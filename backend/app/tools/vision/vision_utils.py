# backend/app/tools/vision/vision_utils.py
import logging
from typing import Dict, Any
from fastapi import UploadFile

logger = logging.getLogger(__name__)


async def process_uploaded_image(file: UploadFile) -> Dict[str, Any]:
    """
    Utility xử lý ảnh upload chung cho các tool Vision
    """
    try:
        from app.rag.documents.document_loader import DocumentLoader
        
        # Extract text qua OCR
        ocr_text = await DocumentLoader.extract_text_from_file(file)
        
        return {
            "status": "success",
            "ocr_text": ocr_text,
            "filename": file.filename,
            "content_length": len(ocr_text)
        }
    except Exception as e:
        logger.error(f"Vision Utils Error: {e}")
        return {
            "status": "error",
            "message": f"Lỗi xử lý ảnh: {str(e)}",
            "ocr_text": ""
        }