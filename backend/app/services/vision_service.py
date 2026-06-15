# backend/app/services/vision_service.py
import logging
from typing import Dict, Any
from fastapi import UploadFile

from app.rag.documents.document_loader import DocumentLoader

logger = logging.getLogger(__name__)


class VisionService:
    """
    Service layer cho Vision Agent (OCR + Image Analysis)
    """

    @staticmethod
    async def process_image(file: UploadFile, query: str = None) -> Dict[str, Any]:
        """Xử lý ảnh + OCR"""
        try:
            # Extract text từ ảnh
            content = await DocumentLoader.extract_text_from_file(file)

            if not query:
                query = "Mô tả và trích xuất toàn bộ thông tin quan trọng từ ảnh này."

            # Sử dụng DocumentRAG để phân tích (vì ảnh đã được OCR)
            from app.rag.documents.document_rag import DocumentRAG
            doc_rag = DocumentRAG()

            # Tạo document tạm thời
            from langchain_core.documents import Document
            temp_doc = Document(
                page_content=content,
                metadata={"filename": file.filename, "type": "image_ocr"}
            )

            doc_rag.vector_store.add_document(temp_doc)

            result = doc_rag.qa_chain(query=query, filename=file.filename)

            return {
                "status": "success",
                "ocr_text": content[:1000] + "..." if len(content) > 1000 else content,
                "answer": result.get("answer"),
                "filename": file.filename
            }

        except Exception as e:
            logger.error(f"VisionService error: {e}")
            return {
                "status": "error",
                "message": "Không thể phân tích ảnh. Hãy thử upload lại ảnh rõ nét hơn."
            }

    @staticmethod
    async def extract_invoice_info(file: UploadFile) -> Dict[str, Any]:
        """Chuyên trích xuất thông tin hóa đơn"""
        query = "Trích xuất thông tin hóa đơn: tổng tiền, khách hàng, ngày tháng, danh sách sản phẩm."
        return await VisionService.process_image(file, query)