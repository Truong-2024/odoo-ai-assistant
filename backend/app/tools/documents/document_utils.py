# backend/app/tools/documents/document_utils.py
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def format_document_response(answer: str, sources: List[Dict], filename: Optional[str] = None) -> Dict[str, Any]:
    """Định dạng response chuẩn cho Document Tools"""
    return {
        "status": "success",
        "answer": answer,
        "sources": sources[:5],  # Giới hạn sources
        "filename": filename,
        "timestamp": datetime.now().isoformat(),
        "message": "✅ Đã xử lý tài liệu thành công"
    }


def create_error_response(message: str, error_type: str = "processing_error") -> Dict[str, Any]:
    """Tạo error response chuẩn"""
    logger.error(f"Document Tool Error: {message}")
    return {
        "status": "error",
        "message": message,
        "error_type": error_type
    }