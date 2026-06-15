# backend/app/tools/general/general_utils.py
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


def format_general_response(answer: str, source: str = "general_agent") -> Dict[str, Any]:
    """Định dạng response chuẩn cho General Tools"""
    return {
        "status": "success",
        "answer": answer,
        "source": source,
        "timestamp": datetime.now().isoformat(),
        "message": "✅ Đã xử lý thành công"
    }


def create_general_error(message: str) -> Dict[str, Any]:
    """Tạo error response chuẩn"""
    logger.error(f"General Tool Error: {message}")
    return {
        "status": "error",
        "message": message,
        "source": "general_agent"
    }