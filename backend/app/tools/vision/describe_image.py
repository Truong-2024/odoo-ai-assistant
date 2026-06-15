# backend/app/tools/vision/describe_image.py
from langchain_core.tools import tool
from typing import Dict, Any
import logging
from fastapi import UploadFile

from app.tools.vision.vision_utils import process_uploaded_image
from app.rag.documents.document_rag import DocumentRAG

logger = logging.getLogger(__name__)


@tool
async def describe_image_tool(file: UploadFile, detailed: bool = False) -> Dict[str, Any]:
    """
    Mô tả chi tiết nội dung ảnh
    """
    try:
        result = await process_uploaded_image(file)
        if result["status"] == "error":
            return result

        query = "Mô tả chi tiết những gì bạn thấy trong ảnh này." if detailed else "Mô tả ngắn gọn nội dung ảnh."

        doc_rag = DocumentRAG()
        rag_result = doc_rag.qa_chain(query=query, filename=result["filename"])

        return {
            "status": "success",
            "filename": result["filename"],
            "description": rag_result.get("answer"),
            "ocr_extracted": result["ocr_text"][:500] + "..." if len(result["ocr_text"]) > 500 else result["ocr_text"],
            "message": "✅ Đã mô tả ảnh thành công"
        }
    except Exception as e:
        logger.error(f"Describe Image Tool Error: {e}")
        return {"status": "error", "message": f"Lỗi mô tả ảnh: {str(e)}"}