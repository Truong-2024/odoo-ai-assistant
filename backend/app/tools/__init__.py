# backend/app/tools/__init__.py
"""
Central tools export for Odoo AI Assistant
"""

# ==================== BUSINESS TOOLS ====================
from .business.create_invoice import create_invoice_tool
from .business.get_sales_report import get_sales_report_tool
from .business.get_low_stock import get_low_stock_tool
from .business.get_sale_order_detail import get_sale_order_detail_tool
from .business.search_products import search_products_tool
from .business.confirm_create_invoice import confirm_create_invoice_tool

# ==================== VISION TOOLS ====================
from .vision.ocr_image import ocr_image_tool
from .vision.describe_image import describe_image_tool
from .vision.image_qa import image_qa_tool

# ==================== DOCUMENT TOOLS ====================
from .documents.search_document import search_document_tool
from .documents.summarize_document import summarize_document_tool
from .documents.extract_table import extract_table_tool

# ==================== GENERAL TOOLS ====================
from .general.calculator import calculator_tool

# ==================== EXPORT LISTS ====================
business_tools_list = [
    create_invoice_tool,
    get_sales_report_tool,
    get_low_stock_tool,
    get_sale_order_detail_tool,
    search_products_tool,
    confirm_create_invoice_tool,
]

vision_tools_list = [
    ocr_image_tool,
    describe_image_tool,
    image_qa_tool,
]

documents_tools_list = [
    search_document_tool,
    summarize_document_tool,
    extract_table_tool,
]

general_tools_list = [
    calculator_tool,
]

communication_tools_list = []

# For tools_node.py
all_tools = (
    business_tools_list +
    vision_tools_list +
    documents_tools_list +
    general_tools_list +
    communication_tools_list
)

print("✅ Tools initialized successfully - All modules imported")

__all__ = [
    'business_tools_list',
    'vision_tools_list',
    'documents_tools_list',
    'general_tools_list',
    'communication_tools_list',
    'all_tools'
]