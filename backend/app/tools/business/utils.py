# backend/app/tools/business/utils.py

"""
Utilities chung cho Business Tools
"""

import uuid
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# =====================================================
# In-memory storage cho pending confirmations
# =====================================================

PENDING_CONFIRMATIONS: Dict[str, Dict[str, Any]] = {}


# =====================================================
# Confirmation ID
# =====================================================

def generate_confirmation_id() -> str:
    """
    Sinh confirmation_id unique
    """
    return str(uuid.uuid4())


# =====================================================
# Store
# =====================================================

def store_pending_confirmation(
    confirmation_id: str,
    data: Dict[str, Any]
) -> None:
    """
    Lưu đơn hàng đang chờ xác nhận
    """

    PENDING_CONFIRMATIONS[confirmation_id] = data

    logger.info(
        f"🟡 Pending confirmation stored: {confirmation_id}"
    )


# =====================================================
# Get by ID
# =====================================================

def get_pending_confirmation(
    confirmation_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Lấy pending confirmation

    Nếu truyền confirmation_id:
        -> trả về confirmation tương ứng

    Nếu không truyền:
        -> trả về confirmation mới nhất
    """

    if not PENDING_CONFIRMATIONS:
        return None

    if confirmation_id:
        data = PENDING_CONFIRMATIONS.get(confirmation_id)

        if not data:
            return None

        return {
            "confirmation_id": confirmation_id,
            **data
        }

    # Lấy pending cuối cùng
    latest_id = list(PENDING_CONFIRMATIONS.keys())[-1]

    return {
        "confirmation_id": latest_id,
        **PENDING_CONFIRMATIONS[latest_id]
    }


# =====================================================
# Check Exists
# =====================================================

def has_pending_confirmation() -> bool:
    """
    Có confirmation đang chờ hay không
    """
    return len(PENDING_CONFIRMATIONS) > 0


# =====================================================
# Remove
# =====================================================

def remove_pending_confirmation(
    confirmation_id: str
) -> bool:
    """
    Xóa pending confirmation
    """

    if confirmation_id in PENDING_CONFIRMATIONS:
        del PENDING_CONFIRMATIONS[confirmation_id]

        logger.info(
            f"🗑 Removed pending confirmation: {confirmation_id}"
        )

        return True

    return False


# =====================================================
# Get all
# =====================================================

def get_all_pending() -> Dict[str, Dict[str, Any]]:
    """
    Debug: lấy toàn bộ pending confirmations
    """

    return PENDING_CONFIRMATIONS.copy()


# =====================================================
# Clear all
# =====================================================

def clear_all_pending() -> None:
    """
    Xóa toàn bộ pending confirmations
    """

    count = len(PENDING_CONFIRMATIONS)

    PENDING_CONFIRMATIONS.clear()

    logger.warning(
        f"⚠ Cleared all pending confirmations ({count})"
    )