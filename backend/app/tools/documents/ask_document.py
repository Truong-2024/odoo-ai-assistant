# backend/app/tools/documents/ask_document.py

from langchain_core.tools import tool
from typing import Dict, Any, Optional
import logging

from app.rag.documents.document_rag import DocumentRAG
from app.tools.documents.document_utils import (
    format_document_response,
    create_error_response
)

logger = logging.getLogger(__name__)


@tool
def ask_document_tool(
    query: str,
    filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Hỏi đáp chung về tài liệu (General Document QA)
    """

    try:
        doc_rag = DocumentRAG()

        docs = doc_rag.retrieve(
            query=query,
            filename=filename,
            k=10
        )

        if not docs:
            return format_document_response(
                answer="Không tìm thấy thông tin liên quan trong tài liệu.",
                sources=[],
                filename=filename
            )

        context = "\n\n".join(
            doc["content"]
            for doc in docs
            if doc.get("content")
        )

        if not context.strip():
            return format_document_response(
                answer="Không tìm thấy thông tin liên quan trong tài liệu.",
                sources=[],
                filename=filename
            )

        prompt = f"""
Bạn là trợ lý hỏi đáp tài liệu.

QUY TẮC BẮT BUỘC:

- Chỉ được sử dụng thông tin xuất hiện trong CONTEXT.
- Không được sử dụng kiến thức bên ngoài.
- Không được suy đoán.
- Không được tự bổ sung thông tin.
- Nếu CONTEXT không đủ để trả lời câu hỏi thì phải trả lời chính xác:

Không tìm thấy thông tin này trong tài liệu.

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:
"""

        try:
            result = doc_rag.llm.invoke(prompt)

            answer = (
                result.content.strip()
                if result and hasattr(result, "content")
                else ""
            )

            if not answer:
                answer = "Không tìm thấy thông tin này trong tài liệu."

        except Exception as e:
            logger.error(
                f"LLM invoke error in ask_document: {e}",
                exc_info=True
            )

            answer = (
                "Tôi đã tìm thấy một số thông tin nhưng hiện tại "
                "không thể tổng hợp câu trả lời."
            )

        return format_document_response(
            answer=answer,
            sources=docs[:6],
            filename=filename
        )

    except Exception as e:
        logger.error(
            f"Ask Document Tool Error: {e}",
            exc_info=True
        )

        return create_error_response(
            f"Lỗi khi hỏi đáp tài liệu: {str(e)}"
        )