# backend/app/tools/business/create_invoice.py
from langchain_core.tools import tool
from typing import Dict, Any
import logging
import json

from app.repositories.odoo_repository import OdooRepository
from app.tools.business.utils import generate_confirmation_id, store_pending_confirmation

logger = logging.getLogger(__name__)


@tool
def create_invoice_tool(
    customer: str,
    order_lines: str,
    notes: str = ""
) -> Dict[str, Any]:
    """
    Tạo đơn bán hàng (Sale Order) trong Odoo.

    Args:
        customer (str): Tên khách hàng (phải tồn tại trong Odoo).
        order_lines (str): Chuỗi JSON chứa danh sách sản phẩm.
        notes (str, optional): Ghi chú đơn hàng.

    Ví dụ order_lines:
    [
        {
            "product_name": "Bàn gỗ cao cấp",
            "quantity": 2,
            "price": 4500000
        },
        {
            "product": "Ghế văn phòng", 
            "quantity": 5,
            "price": 1200000
        }
    ]

    Lưu ý: 
    - Tool này chỉ nên được gọi khi người dùng đã cung cấp đầy đủ thông tin sản phẩm.
    - Nếu thiếu thông tin sản phẩm, Business Agent phải hỏi lại người dùng trước.
    """
    try:
        # Parse JSON nếu order_lines là string
        if isinstance(order_lines, str):
            try:
                order_lines = json.loads(order_lines)
            except json.JSONDecodeError as e:
                return {
                    "status": "error", 
                    "message": "❌ order_lines không đúng định dạng JSON. Vui lòng kiểm tra lại."
                }

        if not isinstance(order_lines, list) or len(order_lines) == 0:
            return {
                "status": "error", 
                "message": "❌ order_lines phải là danh sách sản phẩm và không được rỗng."
            }

        repo = OdooRepository()

        # Tìm khách hàng
        partners = repo.search_read(
            model="res.partner",
            domain=[["name", "ilike", customer]],
            fields=["id", "name"],
            limit=1
        )

        if not partners:
            return {
                "status": "error", 
                "message": f"❌ Không tìm thấy khách hàng: {customer}"
            }

        partner = partners[0]

        # Parse order lines
        total_amount = 0.0
        parsed_lines = []

        for line in order_lines:
            if not isinstance(line, dict):
                continue

            qty = float(line.get("quantity", 1))
            price = float(line.get("price", 0))
            
            # Hỗ trợ cả hai key: product_name và product
            product_name = (
                line.get("product_name") 
                or line.get("product") 
                or line.get("name")
                or ""
            ).strip()

            if not product_name:
                continue

            total_amount += qty * price
            parsed_lines.append({
                "product_name": product_name,
                "quantity": qty,
                "price": price
            })

        if not parsed_lines:
            return {
                "status": "error", 
                "message": "❌ Không tìm thấy sản phẩm hợp lệ trong danh sách."
            }

        confirmation_id = generate_confirmation_id()

        preview = {
            "customer": partner,
            "order_lines": parsed_lines,
            "notes": notes,
            "total_amount": total_amount
        }

        store_pending_confirmation(confirmation_id, preview)

        return {
            "status": "pending_confirmation",
            "confirmation_id": confirmation_id,
            "preview": preview,
            "message": "🟡 Đơn hàng đã được chuẩn bị. Vui lòng xác nhận để tạo thực tế."
        }

    except Exception as e:
        logger.error(f"Create Invoice Tool Error: {e}", exc_info=True)
        return {
            "status": "error", 
            "message": f"Lỗi khi tạo đơn hàng: {str(e)}"
        }