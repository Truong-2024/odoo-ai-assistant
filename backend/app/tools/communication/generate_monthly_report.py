# backend/app/tools/communication/generate_monthly_report.py
from langchain_core.tools import tool
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from app.repositories.odoo_repository import OdooRepository
from app.tools.communication.send_email import send_email_tool
from app.tools.communication.utils import format_report_summary

logger = logging.getLogger(__name__)


@tool
def generate_monthly_report_tool(
    month: Optional[int] = None,
    year: Optional[int] = None,
    email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tạo báo cáo doanh số theo tháng và có thể gửi qua email
    """
    try:
        repo = OdooRepository()

        if not month:
            month = datetime.now().month
        if not year:
            year = datetime.now().year

        # Xây dựng domain
        start_date = f"{year}-{month:02d}-01"
        if month < 12:
            end_date = f"{year}-{month+1:02d}-01"
        else:
            end_date = f"{year+1}-01-01"

        orders = repo.search_read(
            model="sale.order",
            domain=[
                ["date_order", ">=", start_date],
                ["date_order", "<", end_date]
            ],
            fields=["id", "name", "partner_id", "amount_total", "state", "date_order"],
            limit=500
        )

        total_orders = len(orders)
        total_revenue = sum(o.get("amount_total", 0) for o in orders)
        confirmed_orders = [o for o in orders if o.get("state") in ["sale", "done"]]
        confirmed_revenue = sum(o.get("amount_total", 0) for o in confirmed_orders)

        report = {
            "period": f"{month:02d}/{year}",
            "total_orders": total_orders,
            "total_amount": round(total_revenue, 2),
            "confirmed_orders": len(confirmed_orders),
            "confirmed_amount": round(confirmed_revenue, 2),
            "orders": orders[:50]
        }

        summary = format_report_summary(report)

        # Gửi email nếu có
        if email:
            html_content = f"""
            <h2>Báo cáo doanh số tháng {month:02d}/{year}</h2>
            <p>{summary}</p>
            <hr>
            <p><em>Báo cáo được tạo bởi Odoo AI Assistant</em></p>
            """
            send_email_tool(
                to=email,
                subject=f"Báo cáo doanh số tháng {month:02d}/{year}",
                content=html_content,
                html=True
            )

        return {
            "status": "success",
            "report": report,
            "summary": summary,
            "message": f"✅ Đã tạo báo cáo tháng {month:02d}/{year}"
        }

    except Exception as e:
        logger.error(f"Generate Monthly Report Error: {e}")
        return {"status": "error", "message": str(e)}