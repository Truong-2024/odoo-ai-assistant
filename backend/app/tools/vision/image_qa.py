# backend/app/tools/vision/image_qa.py
from langchain_core.tools import tool
from typing import Dict, Any
import logging
from fastapi import UploadFile

from app.tools.vision.vision_utils import process_uploaded_image
from app.rag.documents.document_rag import DocumentRAG

logger = logging.getLogger(__name__)


@tool
async def image_qa_tool(file: UploadFile, query: str) -> Dict[str, Any]:
    """
    Hỏi đáp thông minh trên ảnh (Question Answering on Image)
    """
    try:
        result = await process_uploaded_image(file)
        if result["status"] == "error":
            return result

        doc_rag = DocumentRAG()
        rag_result = doc_rag.qa_chain(query=query, filename=result["filename"])

        return {
            "status": "success",
            "filename": result["filename"],
            "answer": rag_result.get("answer"),
            "ocr_text_preview": result["ocr_text"][:300] + "..." if len(result["ocr_text"]) > 300 else result["ocr_text"],
            "message": f"✅ Đã trả lời câu hỏi về ảnh {result['filename']}"
        }
    except Exception as e:
        logger.error(f"Image QA Tool Error: {e}")
        return {"status": "error", "message": f"Lỗi hỏi đáp trên ảnh: {str(e)}"}