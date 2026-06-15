# backend/app/tools/documents/compare_documents.py
from langchain_core.tools import tool
from typing import Dict, Any, List
import logging

from app.rag.documents.document_rag import DocumentRAG
from app.tools.documents.document_utils import create_error_response

logger = logging.getLogger(__name__)


@tool
def compare_documents_tool(
    filename1: str,
    filename2: str,
    comparison_focus: str = "nội dung chính, điểm khác biệt và điểm tương đồng"
) -> Dict[str, Any]:
    """
    So sánh hai tài liệu
    """
    try:
        query = f"""
        So sánh hai tài liệu sau:
        1. {filename1}
        2. {filename2}

        Tập trung vào: {comparison_focus}
        Trình bày rõ ràng, có cấu trúc.
        """

        doc_rag = DocumentRAG()
        result = doc_rag.qa_chain(query=query)

        return {
            "status": "success",
            "comparison": result.get("answer"),
            "filename1": filename1,
            "filename2": filename2,
            "message": f"✅ Đã so sánh {filename1} và {filename2}"
        }

    except Exception as e:
        logger.error(f"Compare Documents Tool Error: {e}")
        return create_error_response(f"Lỗi khi so sánh tài liệu: {str(e)}")