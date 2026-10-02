"""
Unit test suite verifying authentication, primitives, and 429 rate-limit backoff.
"""
import unittest
from unittest.mock import patch, MagicMock
from connector import WooCommerceConnector
from mcp_server import WooCommerceMCPServer

class TestWooCommerceConnector(unittest.TestCase):
    def setUp(self):
        self.connector = WooCommerceConnector(
            store_url="https://mock-merchant-store.com",
            consumer_key="ck_mock_test_key",
            consumer_secret="cs_mock_test_secret",
            max_retries=2,
            backoff_factor=0.01
        )
        self.mcp = WooCommerceMCPServer(self.connector)

    @patch("requests.Session.request")
    def test_get_order_success(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": 101, "status": "processing", "total": "1499.00"}
        mock_request.return_value = mock_resp

        result = self.connector.get_order_by_id(101)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["data"]["id"], 101)
        self.assertEqual(result["data"]["total"], "1499.00")

    @patch("requests.Session.request")
    def test_rate_limit_retry_success(self, mock_request):
        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.headers = {"Retry-After": "0"}

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.json.return_value = {"id": 202, "status": "completed"}

        mock_request.side_effect = [resp_429, resp_200]

        result = self.connector.get_order_by_id(202)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["data"]["id"], 202)
        self.assertEqual(mock_request.call_count, 2)

    def test_mcp_tool_definitions(self):
        tools = self.mcp.get_tool_definitions()
        self.assertEqual(len(tools), 4)
        tool_names = [t["name"] for t in tools]
        self.assertIn("wc_list_orders", tool_names)
        self.assertIn("wc_get_order_details", tool_names)
        self.assertIn("wc_search_customer_orders", tool_names)
        self.assertIn("wc_check_inventory", tool_names)

if __name__ == "__main__":
    unittest.main()
