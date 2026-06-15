# backend/app/agents/tools_node.py
import logging
import json
from typing import Dict, Any

from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, ToolMessage

from app.agents.state import AgentState

# Import tools lists
from app.tools.business import business_tools_list
from app.agents.document_agent.agent import document_tools_list
from app.agents.vision_agent.agent import vision_tools_list
from app.tools.communication import communication_tools_list
from app.tools.general import general_tools_list

logger = logging.getLogger(__name__)

# Kết hợp tất cả tools
all_tools = (
    business_tools_list +
    document_tools_list +
    vision_tools_list +
    communication_tools_list +
    general_tools_list
)

tool_node = ToolNode(tools=all_tools)


def tools_node(state: AgentState) -> Dict[str, Any]:
    """Tool Node - Xử lý các tool call với logic đặc biệt cho summarize"""
    try:
        result = tool_node.invoke(state)

        update_state = {}

        # ====================== XỬ LÝ ĐẶC BIỆT CHO SUMMARIZE TOOL ======================
        messages = result.get("messages", [])
        tool_messages = [msg for msg in messages if isinstance(msg, ToolMessage)]

        for tool_msg in tool_messages:
            try:
                content = tool_msg.content
                if isinstance(content, str) and content.startswith("{"):
                    data = json.loads(content)
                    
                    # Xử lý cả 2 định dạng cũ và mới của summarize_document_tool
                    summary_text = None
                    
                    if isinstance(data, dict):
                        if "data" in data and isinstance(data["data"], dict):
                            summary_text = data["data"].get("answer")
                        elif "summary" in data:
                            summary_text = data.get("summary")
                        elif "answer" in data:
                            summary_text = data.get("answer")

                    if summary_text:
                        tool_name = getattr(tool_msg, "name", "") or "summarize_document_tool"
                        
                        logger.info(f"✅ Special handling for {tool_name}: Convert ToolMessage → AIMessage")

                        # Thay ToolMessage bằng AIMessage để graph kết thúc mượt
                        result["messages"] = [
                            msg for msg in result["messages"] 
                            if not isinstance(msg, ToolMessage)
                        ]
                        result["messages"].append(
                            AIMessage(content=summary_text)
                        )
                        
                        update_state["active_document"] = data.get("filename") or state.get("active_document")
                        break

            except (json.JSONDecodeError, KeyError, TypeError):
                continue

        # ====================== XỬ LÝ PENDING CONFIRMATION ======================
        if tool_messages:
            last_tool_msg = tool_messages[-1]
            try:
                content = last_tool_msg.content
                if isinstance(content, str):
                    data = json.loads(content)
                    if data.get("status") == "pending_confirmation":
                        update_state["pending_confirmation"] = {
                            "confirmation_id": data["confirmation_id"]
                        }
                        logger.info(f"🟡 Pending confirmation: {data['confirmation_id']}")
            except Exception:
                pass

        return {**result, **update_state}

    except Exception as e:
        logger.error(f"Tools Node Error: {e}", exc_info=True)
        return {
            "messages": [AIMessage(content="❌ Công cụ đang gặp lỗi tạm thời. Vui lòng thử lại.")]
        } 