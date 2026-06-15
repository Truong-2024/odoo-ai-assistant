# backend/app/tools/business/__init__.py

from .create_invoice import create_invoice_tool
from .confirm_create_invoice import confirm_create_invoice_tool
from .get_sales_report import get_sales_report_tool
from .get_low_stock import get_low_stock_tool
from .get_sale_order_detail import get_sale_order_detail_tool
from .search_products import search_products_tool

# Danh sách tools của Business Agent
business_tools_list = [
    create_invoice_tool,
    confirm_create_invoice_tool,
    get_sales_report_tool,
    get_low_stock_tool,
    get_sale_order_detail_tool,
    search_products_tool,
]

__all__ = [
    "create_invoice_tool",
    "confirm_create_invoice_tool",
    "get_sales_report_tool",
    "get_low_stock_tool",
    "get_sale_order_detail_tool",
    "search_products_tool",
    "business_tools_list",
]