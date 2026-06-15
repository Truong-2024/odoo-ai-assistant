# backend/app/tools/vision/extract_invoice_info.py
from langchain_core.tools import tool
from typing import Dict, Any
import logging
from fastapi import UploadFile

from app.tools.vision.vision_utils import process_uploaded_image
from app.rag.documents.document_rag import DocumentRAG

logger = logging.getLogger(__name__)


@tool
async def extract_invoice_info_tool(file: UploadFile) -> Dict[str, Any]:
    """
    Chuyên trích xuất thông tin hóa đơn từ ảnh
    """
    try:
        result = await process_uploaded_image(file)
        if result["status"] == "error":
            return result

        query = """
        Trích xuất thông tin hóa đơn một cách có cấu trúc:
        - Tên công ty / Nhà cung cấp
        - Khách hàng (nếu có)
        - Ngày hóa đơn
        - Tổng tiền (Before tax, Tax, Total)
        - Danh sách sản phẩm/dịch vụ (nếu có)
        """

        doc_rag = DocumentRAG()
        rag_result = doc_rag.qa_chain(query=query, filename=result["filename"])

        return {
            "status": "success",
            "filename": result["filename"],
            "invoice_data": rag_result.get("answer"),
            "ocr_text": result["ocr_text"][:800] + "..." if len(result["ocr_text"]) > 800 else result["ocr_text"],
            "message": "✅ Đã trích xuất thông tin hóa đơn thành công"
        }
    except Exception as e:
        logger.error(f"Extract Invoice Info Tool Error: {e}")
        return {"status": "error", "message": f"Lỗi trích xuất hóa đơn: {str(e)}"}