# backend/app/agents/confirm_node.py
import logging
from typing import Dict, Any

from langchain_core.messages import AIMessage

from app.agents.state import AgentState
from app.tools.business.confirm_create_invoice import confirm_create_invoice_tool
from app.tools.business.utils import remove_pending_confirmation

logger = logging.getLogger(__name__)


def confirm_node(state: AgentState) -> Dict[str, Any]:
    """Xử lý xác nhận tạo đơn hàng"""
    try:
        pending = state.get("pending_confirmation")
        if not pending or not pending.get("confirmation_id"):
            return {
                "messages": [AIMessage(content="❌ Không tìm thấy đơn hàng chờ xác nhận.")],
                "pending_confirmation": None
            }

        confirmation_id = pending["confirmation_id"]

        # === SỬA LỖI: Gọi tool đúng cách ===
        tool_result = confirm_create_invoice_tool.invoke({"confirmation_id": confirmation_id})

        # Dọn dẹp state
        remove_pending_confirmation(confirmation_id)
        state["pending_confirmation"] = None

        success_message = tool_result.get("message", "✅ Đã tạo đơn hàng thành công!")

        return {
            "messages": [AIMessage(content=success_message)],
            "pending_confirmation": None,
            "current_agent": "business"
        }

    except Exception as e:
        logger.error(f"Confirm Node Error: {e}", exc_info=True)
        state["pending_confirmation"] = None
        return {
            "messages": [AIMessage(content="❌ Xác nhận đơn hàng thất bại. Vui lòng thử lại.")],
            "pending_confirmation": None
        }