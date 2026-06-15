# backend/app/tools/documents/search_document.py
from langchain_core.tools import tool
from typing import Dict, Any, Optional
import logging

# XÓA DÒNG IMPORT TOÀN CỤC Ở ĐÂY ĐỂ TRÁNH LỖI VÒNG LẶP
from app.tools.documents.document_utils import format_document_response, create_error_response

logger = logging.getLogger(__name__)


@tool
def search_document_tool(query: str, filename: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """
    Tìm kiếm thông tin trong tài liệu đã upload bằng Advanced RAG.
    Sử dụng retrieve() + LLM để sinh câu trả lời.
    """
    try:
        logger.info(f"🔍 search_document_tool called - Query: '{query}' | File: {filename}")

        # ĐƯA IMPORT VÀO ĐÂY (GIỮ NGUYÊN TOÀN BỘ LOGIC PHÍA DƯỚI)
        from app.rag.documents.document_rag import DocumentRAG

        doc_rag = DocumentRAG()
        
        # Lấy các chunk liên quan
        retrieved_docs = doc_rag.retrieve(query=query, filename=filename, k=limit)
        
        if not retrieved_docs:
            return format_document_response(
                answer="Không tìm thấy thông tin phù hợp trong tài liệu.",
                sources=[],
                filename=filename or "Tất cả tài liệu"
            )

        # Chuẩn bị context
        context = "\n\n".join(
            f"[Chunk {i+1}]\n{doc['content']}" 
            for i, doc in enumerate(retrieved_docs)
        )

        # Prompt QA
        prompt = f"""
Bạn là trợ lý thông minh chuyên phân tích tài liệu.
Hãy trả lời câu hỏi của người dùng dựa trên nội dung tài liệu dưới đây.

**Tài liệu:** {filename or 'Tài liệu'}
**Câu hỏi:** {query}

**Nội dung tham khảo:**
{context}

Hãy trả lời chính xác, ngắn gọn, bằng tiếng Việt. 
Nếu không có thông tin, hãy nói rõ là không tìm thấy.
"""

        # Gọi LLM
        response = doc_rag.llm.invoke(prompt)
        answer = response.content.strip() if hasattr(response, 'content') else str(response)

        # Chuẩn bị sources
        sources = [
            {
                "content": doc["content"][:300] + "..." if len(doc["content"]) > 300 else doc["content"],
                "metadata": doc.get("metadata", {})
            }
            for doc in retrieved_docs
        ]
        return format_document_response(
            answer=answer,
            sources=sources,
            filename=filename or "Tất cả tài liệu"
        )

    except Exception as e:
        logger.error(f"Search Document Tool Error: {e}", exc_info=True)
        return create_error_response(f"Lỗi khi tìm kiếm tài liệu: {str(e)}")