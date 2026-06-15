# backend/app/api/routers/tools.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.core.security import get_current_user

router = APIRouter(prefix="/tools", tags=["AI Tools"])


class CreateInvoiceRequest(BaseModel):
    customer: str
    order_lines: List[Dict]
    notes: str = ""


class ConfirmInvoiceRequest(BaseModel):
    confirmation_id: str


class MonthlyReportRequest(BaseModel):
    month: Optional[int] = None
    year: Optional[int] = None
    email: Optional[str] = None


class SendEmailRequest(BaseModel):
    to: str
    subject: str
    content: str
    html: bool = False


# === Backward Compatibility APIs ===
@router.get("/sales-report")
async def api_get_sales_report(
    period: str = "this_month",
    limit: int = 20,
    current_user: str = Depends(get_current_user)
):
    from app.tools.get_sales_report import get_sales_report
    return get_sales_report(period=period, limit=limit)


@router.get("/low-stock")
async def api_get_low_stock(
    threshold: int = 20,
    limit: int = 20,
    current_user: str = Depends(get_current_user)
):
    from app.tools.get_low_stock import get_low_stock
    return get_low_stock(threshold=threshold, limit=limit)


@router.post("/create-invoice")
async def api_create_invoice(
    request: CreateInvoiceRequest,
    current_user: str = Depends(get_current_user)
):
    from app.tools.create_invoice import create_invoice
    return create_invoice(
        customer=request.customer,
        order_lines=request.order_lines,
        notes=request.notes
    )


@router.post("/confirm-invoice")
async def api_confirm_invoice(
    request: ConfirmInvoiceRequest,
    current_user: str = Depends(get_current_user)
):
    from app.tools.create_invoice import confirm_create_invoice
    return confirm_create_invoice(request.confirmation_id)


@router.get("/list")
async def list_all_tools(current_user: str = Depends(get_current_user)):
    """Danh sách tools theo kiến trúc Multi-Agent v2.0"""
    return {
        "version": "Multi-Agent v2.0",
        "agents": [
            {
                "name": "business",
                "description": "Xử lý nghiệp vụ Odoo (đơn hàng, báo cáo, tồn kho...)",
                "capabilities": ["create_invoice", "sales_report", "low_stock", "order_detail"]
            },
            {
                "name": "document",
                "description": "Phân tích tài liệu PDF, Word, Excel, PPT",
                "capabilities": ["search_document", "summarize", "extract_table"]
            },
            {
                "name": "vision",
                "description": "OCR & Phân tích ảnh, hóa đơn scan",
                "capabilities": ["ocr", "image_qa", "describe_image"]
            },
            {
                "name": "general",
                "description": "Chat đời sống, kiến thức chung, tính toán",
                "capabilities": ["conversation", "calculator", "web_search"]
            }
        ],
        "note": "Hệ thống tự động route đến agent phù hợp qua Supervisor"
    }