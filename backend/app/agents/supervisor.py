# backend/app/agents/supervisor.py
import os
import sys
from pathlib import Path
from datetime import datetime
import logging
import inspect 

ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(ROOT_DIR))

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage
from app.checkpoint.postgres_saver import get_postgres_saver
load_dotenv()

from app.agents.state import AgentState
from app.agents.router import classify_intent

# Import Agents
from app.agents.business_agent.agent import business_node
from app.agents.document_agent.agent import document_node
from app.agents.vision_agent.agent import vision_node
from app.agents.general_agent.agent import general_node

# Import Nodes
from app.agents.tools_node import tools_node
from app.agents.confirm_node import confirm_node

logger = logging.getLogger(__name__)


# ========================= SYSTEM PROMPT =========================
system_prompt = f"""Bạn là Odoo AI Assistant v2.0 - Hệ thống Multi-Agent thông minh.

Bạn có 4 Agent chuyên trách:
- Business Agent: Xử lý nghiệp vụ Odoo (tạo đơn, báo cáo, tồn kho...)
- Document Agent: Phân tích tài liệu
- Vision Agent: OCR & phân tích ảnh
- General Agent: Chat đời sống thông thường

Hãy điều phối thông minh và chính xác.

Hôm nay: {datetime.now().strftime("%d/%m/%Y %H:%M")}"""


# ========================= SUPERVISOR NODE (ĐÃ SỬA LỖI ĐỊNH TUYẾN ĐỘNG) =========================
async def supervisor_node(state: AgentState):
    try:
        messages = state["messages"]
        last_message = messages[-1].content.strip() if messages else ""

        print(f"🔍 Supervisor Input: {last_message[:150]}...")

        # ================= CONFIRMATION =================
        if state.get("pending_confirmation"):
            text = last_message.lower()
            if any(word in text for word in ["xác nhận", "có", "ok", "yes", "đồng ý", "tạo đi"]):
                logger.info("✅ User confirmed the order")
                if inspect.iscoroutinefunction(confirm_node):
                    return await confirm_node(state)
                return confirm_node(state)
            elif any(word in text for word in ["hủy", "không", "cancel", "no"]):
                return {
                    "messages": [AIMessage(content="✅ Đã hủy yêu cầu tạo đơn hàng.")],
                    "pending_confirmation": None
                }

        # ================= AUTO SUMMARY =================
        is_auto_summary = state.get("is_auto_summary", False) or "[AUTO_SUMMARIZE]" in last_message
        doc_mode = "summary" if is_auto_summary else "qa"

        # ================= INTENT CLASSIFY =================
        classification = classify_intent(last_message)

        # Lấy file hiện tại lưu trong State (thường do router truyền xuống hoặc lượt chat trước lưu lại)
        active_document = state.get("active_document")
        thread_files = state.get("thread_files", []) or []

        force_document = False
        reason = ""
        mentioned_file = None

        # ================= 🔥 CẢI TIẾN LOGIC ĐỊNH TUYẾN ĐỘNG (CHATGPT STYLE) =================
        # Thay vì check `if active_document:` trước làm khóa cứng luồng, ta ưu tiên phân tích nội dung câu hỏi mới
        
        # 1. Kiểm tra xem trong nội dung câu hỏi vừa được làm sạch (hoặc tin nhắn gốc) có chứa tên file nào trong Thread không
        if thread_files:
            for file_info in thread_files:
                filename = file_info.get("filename") or file_info.get("name", "")
                if filename and filename.lower() in last_message.lower():
                    force_document = True
                    mentioned_file = filename
                    reason = f"🎯 Định tuyến động: Khớp tên tài liệu trong câu hỏi -> {filename}"
                    break

        # 2. Nếu câu hỏi không nhắc trực tiếp tên file, nhưng State đang có active_document (đã được router truyền xuống chính xác)
        if not force_document and active_document:
            force_document = True
            mentioned_file = active_document
            reason = f"Active document context: {active_document}"

        # 3. Từ khóa nhận diện bổ sung
        elif not force_document and any(k in last_message.lower() for k in ["tài liệu", "file", "pdf", "nội dung", "theo bài giảng"]):
            force_document = True
            reason = "Document keyword detected"

        # ================= ĐỊNH HÌNH STATE UPDATES TẬP TRUNG =================
        new_state_updates = {
            "intent_classification": classification,
            "current_agent": classification["agent"]
        }

        # ================= APPLY OVERRIDE =================
        if force_document:
            classification["agent"] = "document"
            classification["confidence"] = 0.99
            classification["reason"] = reason

            new_state_updates["doc_mode"] = doc_mode
            new_state_updates["active_document"] = mentioned_file or active_document

        print("ROUTER RESULT =", classification)

        # ================= CLEAN STATE =================
        if state.get("pending_summary") and is_auto_summary:
            new_state_updates["pending_summary"] = False

        # Cập nhật tập trung vào state trước khi truyền xuống các node con
        state.update(new_state_updates)

        # ================= ROUTING & EXECUTION =================
        if classification["agent"] == "business":
            if inspect.iscoroutinefunction(business_node):
                response = await business_node(state)
            else:
                response = business_node(state)

        elif classification["agent"] == "document":
            if inspect.iscoroutinefunction(document_node):
                response = await document_node(state)
            else:
                response = document_node(state)

        elif classification["agent"] == "vision":
            if inspect.iscoroutinefunction(vision_node):
                response = await vision_node(state)
            else:
                response = vision_node(state)

        else:
            if inspect.iscoroutinefunction(general_node):
                response = await general_node(state)
            else:
                response = general_node(state)

        # ĐẢM BẢO BẮT BUỘC: Ép các cập nhật của Supervisor (đặc biệt là active_document mới) vào response cuối cùng
        if isinstance(response, dict):
            response.update(new_state_updates)
        else:
            response = {**new_state_updates, "messages": [AIMessage(content=str(response))]}

        return response

    except Exception as e:
        logger.error(f"Supervisor Error: {e}", exc_info=True)
        return {
            "messages": [AIMessage(content="❌ Xin lỗi, hệ thống đang gặp lỗi. Bạn thử lại sau nhé!")]
        }


# ========================= ROUTER =========================
def route_after_supervisor(state: AgentState) -> str:
    """Điều hướng sau khi supervisor chạy"""
    if state.get("pending_confirmation"):
        return "confirm"

    if state.get("messages"):
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

    return END


# ========================= BUILD GRAPH =========================
def create_supervisor_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("tools", tools_node)
    workflow.add_node("confirm", confirm_node)

    workflow.set_entry_point("supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "tools": "tools",
            "confirm": "confirm",
            "__end__": END
        }
    )

    workflow.add_edge("tools", "supervisor")
    workflow.add_edge("confirm", "supervisor")

    return workflow


# ====================== COMPILE ======================
checkpointer = get_postgres_saver()
graph = create_supervisor_graph()
app = graph.compile(checkpointer=checkpointer)

print("✅ Multi-Agent Supervisor v2.1 initialized successfully with Dynamic Routing!")
print("📌 Agents: Business | Document | Vision | General")