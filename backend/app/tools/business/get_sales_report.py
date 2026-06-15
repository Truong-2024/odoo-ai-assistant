# backend/app/tools/business/get_sales_report.py
from langchain_core.tools import tool
from typing import Dict, Any
from datetime import datetime, timedelta
import logging

from app.repositories.odoo_repository import OdooRepository

logger = logging.getLogger(__name__)


@tool
def get_sales_report_tool(period: str = "this_month", limit: int = 20) -> Dict[str, Any]:
    """Lấy báo cáo doanh số theo kỳ"""
    try:
        repo = OdooRepository()
        domain = []

        today = datetime.now().strftime("%Y-%m-%d")

        if period == "today":
            domain = [["date_order", ">=", today]]
        elif period == "this_week":
            domain = [["date_order", ">=", (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")]]
        elif period == "this_month":
            domain = [["date_order", ">=", datetime.now().strftime("%Y-%m-01")]]
        elif period == "this_year":
            domain = [["date_order", ">=", datetime.now().strftime("%Y-01-01")]]

        sales = repo.search_read(
            model="sale.order",
            domain=domain,
            fields=["id", "name", "partner_id", "amount_total", "date_order", "state"],
            limit=limit
        )

        total_amount = sum(order.get("amount_total", 0) for order in sales)
        confirmed = [s for s in sales if s.get("state") in ["sale", "done"]]

        return {
            "status": "success",
            "period": period,
            "total_orders": len(sales),
            "total_amount": round(total_amount, 2),
            "confirmed_orders": len(confirmed),
            "confirmed_amount": round(sum(o.get("amount_total", 0) for o in confirmed), 2),
            "orders": sales,
            "message": f"Báo cáo doanh số {period}"
        }
    except Exception as e:
        logger.error(f"Get Sales Report Error: {e}")
        return {"status": "error", "message": str(e)}