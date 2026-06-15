# backend/app/agents/general_agent/agent.py
import logging
from typing import Dict, Any

from langchain_core.messages import AIMessage
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()

from app.agents.state import AgentState
from app.agents.general_agent.prompts import get_general_system_prompt, get_general_user_prompt

# Import các tool chung (sẽ mở rộng sau)
from app.tools.general.calculator import calculator_tool
# from app.tools.general.web_search import web_search_tool  # Sẽ thêm sau

logger = logging.getLogger(__name__)

# ========================= LLM =========================
llm = ChatGroq(
    model="llama-3.1-8b-instant",   # Có thể đổi thành llama-3.1-70b sau khi cần chất lượng cao hơn
    temperature=0.7,                # Tăng creativity cho agent đời sống
    api_key=os.getenv("GROQ_API_KEY"),
    max_tokens=1024,
)

# Bind tools cho General Agent
general_tools = [
    calculator_tool,
    # web_search_tool,          # Uncomment khi đã implement
]

llm_with_tools = llm.bind_tools(general_tools)


def general_node(state: AgentState) -> Dict[str, Any]:
    """
    General Agent Node - Xử lý chat đời sống thông thường
    """
    try:
        messages = state["messages"]
        last_message = messages[-1].content

        system_prompt = get_general_system_prompt()

        # Gọi LLM với context gần nhất
        response = llm_with_tools.invoke([
            ("system", system_prompt),
            *messages[-12:]   # Context dài hơn một chút cho hội thoại tự nhiên
        ])

        # Kiểm tra tool calls
        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_names = [t.get('name') for t in response.tool_calls]
            logger.info(f"General Agent gọi tools: {tool_names}")
            
            return {
                "messages": [response],
                "current_agent": "general"
            }

        # Trả lời trực tiếp từ LLM
        return {
            "messages": [response],
            "current_agent": "general"
        }

    except Exception as e:
        logger.error(f"[General Agent Error] {e}", exc_info=True)
        return {
            "messages": [AIMessage(
                content="❌ Xin lỗi, General Agent đang gặp lỗi. Bạn thử lại sau vài giây nhé! "
                        "Nếu bạn đang hỏi về Odoo hoặc tài liệu, hãy nói rõ hơn để tôi chuyển sang agent phù hợp."
            )],
            "current_agent": "general",
            "error_count": state.get("error_count", 0) + 1,
            "last_error": str(e)
        }


# Export tools
general_tools_list = general_tools

print("✅ General Agent initialized successfully with conversational capability")