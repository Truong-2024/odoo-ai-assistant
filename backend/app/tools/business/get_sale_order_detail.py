# backend/app/tools/business/get_sale_order_detail.py
from langchain_core.tools import tool
from typing import Dict, Any
import logging

from app.repositories.odoo_repository import OdooRepository

logger = logging.getLogger(__name__)


@tool
def get_sale_order_detail_tool(order_name: str) -> Dict[str, Any]:
    """Lấy chi tiết đơn hàng theo mã"""
    try:
        repo = OdooRepository()
        orders = repo.search_read(
            model="sale.order",
            domain=[["name", "=", order_name]],
            fields=["id", "name", "partner_id", "amount_total", "state", "date_order", "note", "order_line"],
            limit=1
        )

        if not orders:
            return {"status": "error", "message": f"❌ Không tìm thấy đơn hàng {order_name}"}

        order = orders[0]
        partner_name = order.get("partner_id")[1] if isinstance(order.get("partner_id"), list) else "N/A"

        return {
            "status": "success",
            "order": {
                "id": order["id"],
                "name": order["name"],
                "customer": partner_name,
                "total_amount": float(order.get("amount_total", 0)),
                "state": order.get("state"),
                "date_order": order.get("date_order"),
                "note": order.get("note"),
            }
        }
    except Exception as e:
        logger.error(f"Get Sale Order Detail Error: {e}")
        return {"status": "error", "message": str(e)}