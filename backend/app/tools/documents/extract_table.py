# backend/app/tools/documents/extract_table.py
from langchain_core.tools import tool
from typing import Dict, Any, Optional
import logging

from app.rag.documents.document_rag import DocumentRAG
from app.tools.documents.document_utils import format_document_response, create_error_response

logger = logging.getLogger(__name__)


@tool
def extract_table_tool(filename: str, table_description: Optional[str] = None) -> Dict[str, Any]:
    """
    Trích xuất và trình bày bảng từ tài liệu
    """
    try:
        query = "Trích xuất tất cả bảng trong tài liệu một cách rõ ràng, có cấu trúc."
        if table_description:
            query += f" {table_description}"

        doc_rag = DocumentRAG()
        result = doc_rag.qa_chain(query=query, filename=filename)

        return format_document_response(
            answer=result.get("answer", "Không tìm thấy bảng nào trong tài liệu."),
            sources=result.get("sources", []),
            filename=filename
        )

    except Exception as e:
        logger.error(f"Extract Table Tool Error: {e}")
        return create_error_response(f"Lỗi khi trích xuất bảng: {str(e)}")