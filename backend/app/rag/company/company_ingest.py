# backend/app/rag/company/company_ingest.py
import sys
import os
from datetime import datetime
from typing import List
import logging

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.repositories.odoo_repository import OdooRepository
from app.rag.company.company_vector_store import CompanyVectorStore

logger = logging.getLogger(__name__)


class CompanyDataIngestor:
    """
    Ingestor chuyên biệt cho dữ liệu Odoo (Company Knowledge)
    """
    def __init__(self):
        self.repo = OdooRepository()
        self.vector_store = CompanyVectorStore()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=150,
            separators=["\n\n", "\n", ".", "!", "?", " ", ""]
        )

    def fetch_odoo_data(self) -> List[Document]:
        """Lấy dữ liệu từ Odoo và chuyển thành Document"""
        documents = []

        # 1. Partners (Khách hàng)
        partners = self.repo.search_read(
            model="res.partner",
            domain=[["active", "=", True]],
            fields=["id", "name", "email", "phone", "city", "street", "comment"],
            limit=0
        )
        for p in partners:
            content = f"""Khách hàng: {p.get('name')}
Email: {p.get('email')}
Điện thoại: {p.get('phone')}
Địa chỉ: {p.get('street')} - {p.get('city')}
Ghi chú: {p.get('comment')}"""
            documents.append(Document(
                page_content=content.strip(),
                metadata={
                    "type": "partner",
                    "id": p["id"],
                    "name": p.get("name"),
                    "source": "odoo_res_partner",
                    "last_updated": datetime.now().isoformat()
                }
            ))

        # 2. Products (Sản phẩm)
        products = self.repo.search_read(
            model="product.product",
            domain=[["active", "=", True]],
            fields=["id", "name", "default_code", "list_price", "description_sale"],
            limit=0
        )
        for p in products:
            content = f"""Sản phẩm: {p.get('name')}
Mã SP: {p.get('default_code')}
Giá bán: {p.get('list_price', 0):,} VND
Mô tả: {p.get('description_sale')}"""
            documents.append(Document(
                page_content=content.strip(),
                metadata={
                    "type": "product",
                    "id": p["id"],
                    "name": p.get("name"),
                    "price": float(p.get("list_price") or 0),
                    "source": "odoo_product_product",
                    "last_updated": datetime.now().isoformat()
                }
            ))

        # 3. Sale Orders (Đơn hàng gần đây)
        sales = self.repo.search_read(
            model="sale.order",
            domain=[],
            fields=["id", "name", "partner_id", "amount_total", "state", "date_order", "note"],
            limit=800
        )
        for s in sales:
            partner_name = s.get('partner_id')[1] if isinstance(s.get('partner_id'), list) else "N/A"
            content = f"""Đơn hàng: {s.get('name')}
Khách hàng: {partner_name}
Tổng tiền: {s.get('amount_total', 0):,} VND
Trạng thái: {s.get('state')}
Ngày đặt: {s.get('date_order')}
Ghi chú: {s.get('note')}"""
            documents.append(Document(
                page_content=content.strip(),
                metadata={
                    "type": "sale_order",
                    "id": s["id"],
                    "name": s.get("name"),
                    "partner": partner_name,
                    "amount": float(s.get("amount_total") or 0),
                    "state": s.get("state"),
                    "source": "odoo_sale_order",
                    "last_updated": datetime.now().isoformat()
                }
            ))

        logger.info(f"✅ Extracted {len(documents)} documents from Odoo")
        return documents

    def ingest(self, clear_old: bool = False):
        """Chạy ingestion pipeline"""
        try:
            if clear_old:
                print("🧹 Đang xóa dữ liệu cũ...")
                self.vector_store.delete_collection()

            docs = self.fetch_odoo_data()
            chunks = self.text_splitter.split_documents(docs)

            print(f"📄 Sau chunking: {len(chunks)} chunks")
            print("🔄 Đang nhúng và lưu vào PGVector...")

            self.vector_store.add_documents(chunks)

            print(f"🎉 Company Ingestion HOÀN TẤT! Tổng {len(chunks)} chunks.")
            return {
                "status": "success",
                "total_documents": len(docs),
                "total_chunks": len(chunks),
                "message": "Company knowledge ingested successfully"
            }
        except Exception as e:
            logger.error(f"❌ Company Ingestion failed: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}