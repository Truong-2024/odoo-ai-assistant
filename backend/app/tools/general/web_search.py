# backend/app/tools/general/web_search.py
from langchain_core.tools import tool
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


@tool
def web_search_tool(query: str, num_results: int = 5) -> Dict[str, Any]:
    """
    Tìm kiếm thông tin trên web (Sẽ implement sau khi tích hợp Tavily hoặc SerpAPI)
    """
    # TODO: Implement sau khi có API key (Tavily, DuckDuckGo, SerpAPI...)
    return {
        "status": "pending",
        "message": f"🔍 Tính năng Web Search cho query '{query}' đang được phát triển.",
        "note": "Sẽ hỗ trợ tìm kiếm realtime trong phiên bản sau."
    }