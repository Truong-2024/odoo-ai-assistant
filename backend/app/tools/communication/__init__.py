# backend/app/tools/communication/__init__.py

from .send_email import send_email_tool
from .generate_monthly_report import generate_monthly_report_tool
from .generate_pdf_report import generate_pdf_report_tool

# Danh sách tools của Communication Agent
communication_tools_list = [
    send_email_tool,
    generate_monthly_report_tool,
    generate_pdf_report_tool,
]

__all__ = [
    "send_email_tool",
    "generate_monthly_report_tool",
    "generate_pdf_report_tool",
    "communication_tools_list",
]