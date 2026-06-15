# backend/app/tools/business/confirm_create_invoice.py
from langchain_core.tools import tool
from typing import Dict, Any
import logging

from app.repositories.odoo_repository import OdooRepository
from app.tools.business.utils import get_pending_confirmation, remove_pending_confirmation

logger = logging.getLogger(__name__)


@tool
def confirm_create_invoice_tool(confirmation_id: str) -> Dict[str, Any]:
    """
    Xác nhận và tạo đơn hàng thật trong Odoo.
    Tool này được gọi sau khi người dùng xác nhận.
    """
    try:
        pending_data = get_pending_confirmation(confirmation_id)
        if not pending_data:
            return {
                "status": "error",
                "message": "❌ Không tìm thấy đơn hàng chờ xác nhận hoặc đã hết hạn."
            }

        repo = OdooRepository()
        order_lines = []

        for line in pending_data.get("order_lines", []):
            product_name = line.get("product_name", "").strip()
            products = repo.search_read(
                model="product.product",
                domain=[["name", "ilike", product_name]],
                fields=["id", "name"],
                limit=1
            )
            if products:
                product = products[0]
                order_lines.append((0, 0, {
                    "product_id": product["id"],
                    "product_uom_qty": line.get("quantity", 1),
                    "price_unit": line.get("price", 0)
                }))

        sale_order_vals = {
            "partner_id": pending_data["customer"]["id"],
            "note": pending_data.get("notes", ""),
            "order_line": order_lines
        }

        sale_order_id = repo.create(model="sale.order", vals=sale_order_vals)
        order_info = repo.read(
            model="sale.order", 
            ids=[sale_order_id], 
            fields=["name"]
        )[0]

        # Xóa khỏi pending
        remove_pending_confirmation(confirmation_id)

        return {
            "status": "success",
            "sale_order_id": sale_order_id,
            "sale_order_name": order_info["name"],
            "message": f"✅ Đã tạo đơn hàng thành công!\nMã đơn hàng: **{order_info['name']}**"
        }

    except Exception as e:
        logger.error(f"Confirm Create Invoice Tool Error: {e}", exc_info=True)
        return {
            "status": "error", 
            "message": f"Lỗi khi xác nhận đơn hàng: {str(e)}"
        }