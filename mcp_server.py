"""
Model Context Protocol (MCP) Tool Specification for Agent Studio
"""
from typing import Dict, Any, List
import json
from connector import WooCommerceConnector

class WooCommerceMCPServer:
    def __init__(self, connector: WooCommerceConnector):
        self.connector = connector

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "wc_list_orders",
                "description": "List recent merchant orders from WooCommerce. Filter by status to locate failed or processing transactions.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["pending", "processing", "on-hold", "completed", "cancelled", "refunded", "failed"],
                            "description": "Filter orders by current payment/fulfillment state."
                        },
                        "per_page": {
                            "type": "integer",
                            "default": 10,
                            "description": "Number of records to return (max 50)."
                        }
                    }
                }
            },
            {
                "name": "wc_get_order_details",
                "description": "Retrieve line items, shipping status, total amount, and customer details for a given Order ID.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "integer", "description": "The unique numerical WooCommerce Order ID."}
                    },
                    "required": ["order_id"]
                }
            },
            {
                "name": "wc_search_customer_orders",
                "description": "Look up orders associated with a customer email, billing name, or contact number.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "customer_query": {"type": "string", "description": "Customer email, phone, or name."}
                    },
                    "required": ["customer_query"]
                }
            },
            {
                "name": "wc_check_inventory",
                "description": "Check current stock availability and price for a product before processing replacements or upsells.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "product_id": {"type": "integer", "description": "The unique numerical product ID."}
                    },
                    "required": ["product_id"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        try:
            if tool_name == "wc_list_orders":
                res = self.connector.list_orders(
                    status=arguments.get("status"),
                    per_page=arguments.get("per_page", 10)
                )
            elif tool_name == "wc_get_order_details":
                res = self.connector.get_order_by_id(order_id=arguments["order_id"])
            elif tool_name == "wc_search_customer_orders":
                res = self.connector.search_orders_by_customer(customer_query=arguments["customer_query"])
            elif tool_name == "wc_check_inventory":
                res = self.connector.get_product_inventory(product_id=arguments["product_id"])
            else:
                return json.dumps({"error": f"Unknown tool: {tool_name}"})

            return json.dumps(res, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Execution error on {tool_name}: {str(e)}"})
