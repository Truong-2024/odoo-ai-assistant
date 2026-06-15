# backend/app/tools/vision/ocr_image.py
from langchain_core.tools import tool
from typing import Dict, Any
import logging
from fastapi import UploadFile

from app.tools.vision.vision_utils import process_uploaded_image

logger = logging.getLogger(__name__)


@tool
async def ocr_image_tool(file: UploadFile) -> Dict[str, Any]:
    """
    Thực hiện OCR trên ảnh và trả về text đã trích xuất
    """
    try:
        result = await process_uploaded_image(file)
        
        if result["status"] == "error":
            return result

        return {
            "status": "success",
            "filename": result["filename"],
            "ocr_text": result["ocr_text"],
            "message": f"✅ Đã OCR thành công file {result['filename']}",
            "content_length": result["content_length"]
        }
    except Exception as e:
        logger.error(f"OCR Image Tool Error: {e}")
        return {"status": "error", "message": f"Lỗi OCR: {str(e)}"}