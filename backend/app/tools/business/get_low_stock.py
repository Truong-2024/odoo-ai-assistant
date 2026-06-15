# backend/app/tools/business/get_low_stock.py
from langchain_core.tools import tool
from typing import Dict, Any
import logging

from app.repositories.odoo_repository import OdooRepository

logger = logging.getLogger(__name__)


@tool
def get_low_stock_tool(threshold: int = 10, limit: int = 20) -> Dict[str, Any]:
    """Lấy danh sách sản phẩm tồn kho thấp"""
    try:
        repo = OdooRepository()
        products = repo.search_read(
            model="product.product",
            domain=[["active", "=", True]],
            fields=["id", "name", "default_code", "list_price", "qty_available"],
            limit=100
        )

        low_stock = [p for p in products if p.get("qty_available", 0) < threshold]

        return {
            "status": "success",
            "threshold": threshold,
            "total_low_stock": len(low_stock),
            "products": low_stock[:limit],
            "message": f"Tìm thấy {len(low_stock)} sản phẩm tồn kho thấp"
        }
    except Exception as e:
        logger.error(f"Get Low Stock Error: {e}")
        return {"status": "error", "message": str(e)}