# backend/app/tools/vision/__init__.py

from .ocr_image import ocr_image_tool
from .describe_image import describe_image_tool
from .image_qa import image_qa_tool
from .extract_invoice_info import extract_invoice_info_tool

# Danh sách tools của Vision Agent
vision_tools_list = [
    ocr_image_tool,
    describe_image_tool,
    image_qa_tool,
    extract_invoice_info_tool,
]

__all__ = [
    "ocr_image_tool",
    "describe_image_tool",
    "image_qa_tool",
    "extract_invoice_info_tool",
    "vision_tools_list",
]