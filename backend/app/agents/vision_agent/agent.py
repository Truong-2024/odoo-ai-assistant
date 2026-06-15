# backend/app/agents/vision_agent/agent.py
import logging
from typing import Dict, Any
import re

from langchain_core.messages import AIMessage
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()

from app.agents.state import AgentState
from app.agents.vision_agent.prompts import get_vision_system_prompt, get_vision_user_prompt

# Import Vision Tools - SỬA TÊN MODULE ĐÚNG
from app.tools.vision.ocr_image import ocr_image_tool
from app.tools.vision.describe_image import describe_image_tool
from app.tools.vision.image_qa import image_qa_tool

logger = logging.getLogger(__name__)

# ========================= LLM =========================
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.1,
    api_key=os.getenv("GROQ_API_KEY"),
    max_tokens=1200,
)

# Bind tools cho Vision Agent
vision_tools = [
    ocr_image_tool,
    describe_image_tool,
    image_qa_tool,
]

llm_with_tools = llm.bind_tools(vision_tools)


def vision_node(state: AgentState) -> Dict[str, Any]:
    """
    Vision Agent Node - Chuyên xử lý ảnh và OCR
    """
    try:
        messages = state["messages"]
        last_message = messages[-1].content.strip()

        active_image = state.get("active_document")

        # ====================== BẢO VỆ QUAN TRỌNG: Chuyển PDF sang Document ======================
        if "[Đã tải lên file:" in last_message:
            lower_msg = last_message.lower()
            if any(ext in lower_msg for ext in [".pdf", ".docx", ".xlsx", ".xls", ".doc"]):
                logger.info(f"🔄 Vision Agent redirect → Document Agent (PDF detected)")
                from app.agents.document_agent.agent import document_node
                return document_node(state)

        system_prompt = get_vision_system_prompt()
        user_prompt = get_vision_user_prompt(last_message, active_image)

        # Gọi LLM với tools
        response = llm_with_tools.invoke([
            ("system", system_prompt),
            *messages[-8:]
        ])

        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_names = [t.get('name') for t in response.tool_calls]
            logger.info(f"Vision Agent gọi tools: {tool_names}")
            
            return {
                "messages": [response],
                "current_agent": "vision",
                "active_document": active_image
            }

        return {
            "messages": [response],
            "current_agent": "vision",
            "active_document": active_image
        }

    except Exception as e:
        logger.error(f"[Vision Agent Error] {e}", exc_info=True)
        return {
            "messages": [AIMessage(
                content="❌ Xin lỗi, Vision Agent đang gặp lỗi khi phân tích ảnh. "
                        "Bạn thử upload lại ảnh rõ nét hơn hoặc mô tả chi tiết hơn nhé!"
            )],
            "current_agent": "vision"
        }


# Export cho supervisor
vision_tools_list = vision_tools

print("✅ Vision Agent initialized successfully with OCR & Image Analysis support")