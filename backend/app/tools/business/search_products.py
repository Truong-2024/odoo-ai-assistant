# backend/app/tools/business/search_products.py
from langchain_core.tools import tool
from typing import Dict, Any
import logging

from app.repositories.odoo_repository import OdooRepository

logger = logging.getLogger(__name__)


@tool
def search_products_tool(query: str, limit: int = 10) -> Dict[str, Any]:
    """Tìm kiếm sản phẩm theo tên hoặc mã"""
    try:
        repo = OdooRepository()
        products = repo.search_read(
            model="product.product",
            domain=[["name", "ilike", query]],
            fields=["id", "name", "default_code", "list_price", "description_sale"],
            limit=limit
        )

        results = []
        for p in products:
            results.append({
                "id": p["id"],
                "name": p["name"],
                "default_code": p.get("default_code", "N/A"),
                "list_price": float(p.get("list_price", 0)),
                "description": (p.get("description_sale") or "")[:300]
            })

        return {
            "status": "success",
            "total": len(results),
            "products": results,
            "message": f"✅ Tìm thấy {len(results)} sản phẩm"
        }
    except Exception as e:
        logger.error(f"Search Products Error: {e}")
        return {"status": "error", "message": str(e)}