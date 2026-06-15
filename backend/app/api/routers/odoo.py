# backend/app/api/routers/odoo.py
from fastapi import APIRouter, Depends, HTTPException
import traceback
from app.repositories.odoo_repository import OdooRepository

router = APIRouter(
    prefix="/odoo",
    tags=["Odoo"]
)


def get_odoo_repo():
    try:
        return OdooRepository()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Odoo connection failed: {str(e)}"
        )


@router.get("/test")
async def test_odoo(repo: OdooRepository = Depends(get_odoo_repo)):
    try:
        return {
            "status": "success",
            "message": "✅ Kết nối Odoo thành công!",
            "database": repo.odoo.env.db,
            "user": repo.odoo.env.user.name
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/partners")
async def get_partners(limit: int = 5, repo: OdooRepository = Depends(get_odoo_repo)):
    try:
        partners = repo.search_read(
            model="res.partner",
            domain=[],
            fields=["id", "name", "email", "phone", "city"],
            limit=limit
        )
        return {
            "status": "success",
            "count": len(partners),
            "partners": partners
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Partners Error: {str(e)}")


@router.get("/products")
async def get_products(limit: int = 5, repo: OdooRepository = Depends(get_odoo_repo)):
    try:
        products = repo.search_read(
            model="product.product",
            domain=[],
            fields=["id", "name", "list_price", "default_code", "active"],
            limit=limit
        )
        return {
            "status": "success",
            "count": len(products),
            "products": products
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Products Error: {str(e)}")


@router.get("/sales")
async def get_sales(limit: int = 5, repo: OdooRepository = Depends(get_odoo_repo)):
    try:
        sales = repo.search_read(
            model="sale.order",
            domain=[],
            fields=["id", "name", "amount_total", "state", "date_order"],
            limit=limit
        )
        return {
            "status": "success",
            "count": len(sales),
            "sales": sales
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Sales Error: {str(e)}")


@router.get("/low-stock")
async def get_low_stock(limit: int = 10, repo: OdooRepository = Depends(get_odoo_repo)):
    try:
        products = repo.search_read(
            model="product.product",
            domain=[["active", "=", True]],
            fields=["id", "name", "qty_available", "default_code"],
            limit=limit
        )
        low_stock = [p for p in products if p.get("qty_available", 0) < 10]
        return {
            "status": "success",
            "count": len(low_stock),
            "products": low_stock
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Low Stock Error: {str(e)}")