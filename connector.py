"""
WooCommerce Merchant Connector for Razorpay Agent Studio
Author: Manohar Irigineni
"""
import time
import logging
from typing import Dict, Any, List, Optional
import requests
from requests.auth import HTTPBasicAuth

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("WooCommerceConnector")

class WooCommerceRateLimitException(Exception):
    """Raised when rate limits are exhausted and retries fail."""
    pass

class WooCommerceConnector:
    def __init__(
        self,
        store_url: str,
        consumer_key: str,
        consumer_secret: str,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
        timeout: int = 10
    ):
        self.base_url = store_url.rstrip("/") + "/wp-json/wc/v3"
        self.auth = HTTPBasicAuth(consumer_key, consumer_secret)
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout
        self.session = requests.Session()

    def _execute_request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        params = params or {}
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    auth=self.auth,
                    params=params,
                    timeout=self.timeout
                )

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", self.backoff_factor ** attempt))
                    logger.warning(f"Rate limited (429). Retrying after {retry_after}s... (Attempt {attempt+1}/{self.max_retries})")
                    time.sleep(retry_after)
                    continue

                response.raise_for_status()
                return {
                    "status": "success",
                    "status_code": response.status_code,
                    "data": response.json()
                }

            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP Error on {endpoint}: {e.response.status_code} - {e.response.text}")
                if attempt == self.max_retries:
                    return {"status": "error", "status_code": e.response.status_code, "message": e.response.text}
                time.sleep(self.backoff_factor ** attempt)

            except requests.exceptions.RequestException as e:
                logger.error(f"Network error on {endpoint}: {str(e)}")
                if attempt == self.max_retries:
                    return {"status": "error", "message": f"Connection failed: {str(e)}"}
                time.sleep(self.backoff_factor ** attempt)

        raise WooCommerceRateLimitException("Exceeded maximum retries due to persistent rate limiting.")

    def list_orders(self, status: Optional[str] = None, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        params = {"page": page, "per_page": min(per_page, 50)}
        if status:
            params["status"] = status
        return self._execute_request("GET", "orders", params=params)

    def get_order_by_id(self, order_id: int) -> Dict[str, Any]:
        return self._execute_request("GET", f"orders/{order_id}")

    def search_orders_by_customer(self, customer_query: str, page: int = 1, per_page: int = 5) -> Dict[str, Any]:
        params = {"search": customer_query, "page": page, "per_page": per_page}
        return self._execute_request("GET", "orders", params=params)

    def get_product_inventory(self, product_id: int) -> Dict[str, Any]:
        result = self._execute_request("GET", f"products/{product_id}")
        if result.get("status") == "success":
            data = result["data"]
            return {
                "status": "success",
                "product_id": data.get("id"),
                "name": data.get("name"),
                "sku": data.get("sku"),
                "stock_quantity": data.get("stock_quantity"),
                "stock_status": data.get("stock_status"),
                "price": data.get("price")
            }
        return result
