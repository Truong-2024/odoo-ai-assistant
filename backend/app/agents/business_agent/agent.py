# backend/app/agents/business_agent/agent.py
import logging
import json
from typing import Dict, Any

from langchain_core.messages import AIMessage
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()

from app.agents.state import AgentState
from app.agents.business_agent.prompts import get_business_system_prompt

# Import tools
from app.tools.business.create_invoice import create_invoice_tool
from app.tools.business.confirm_create_invoice import confirm_create_invoice_tool
from app.tools.business.get_sales_report import get_sales_report_tool
from app.tools.business.get_low_stock import get_low_stock_tool
from app.tools.business.get_sale_order_detail import get_sale_order_detail_tool
from app.tools.business.search_products import search_products_tool

logger = logging.getLogger(__name__)

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.0,
    api_key=os.getenv("GROQ_API_KEY"),
    max_tokens=800,           # Giảm để tránh rate limit
)

business_tools = [
    create_invoice_tool,
    confirm_create_invoice_tool,   # ← Đảm bảo có tool này
    get_sales_report_tool,
    get_low_stock_tool,
    get_sale_order_detail_tool,
    search_products_tool,
]

llm_with_tools = llm.bind_tools(business_tools)


def business_node(state: AgentState) -> Dict[str, Any]:
    try:
        messages = state["messages"]
        system_prompt = get_business_system_prompt()

        response = llm_with_tools.invoke([
            ("system", system_prompt),
            *messages[-8:]   # Giảm context để tránh token limit
        ])

        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_names = [t.get('name') for t in response.tool_calls]
            logger.info(f"Business Agent gọi tool: {tool_names}")

            return {
                "messages": [response],
                "current_agent": "business"
            }

        return {
            "messages": [response],
            "current_agent": "business"
        }

    except Exception as e:
        logger.error(f"[Business Agent Error] {e}", exc_info=True)
        return {
            "messages": [AIMessage(
                content="❌ Business Agent đang gặp lỗi. Bạn thử nói rõ hơn một chút nhé!"
            )],
            "current_agent": "business"
        }


business_tools_list = business_tools
print("✅ Business Agent loaded successfully")