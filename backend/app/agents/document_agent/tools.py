from langchain_core.tools import tool
from typing import List, Dict, Any, Optional
import logging

from app.rag.documents.document_rag import DocumentRAG

logger = logging.getLogger(__name__)

document_rag = DocumentRAG()


@tool
def search_document_tool(query: str, filename: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """Tìm kiếm thông tin trong tài liệu đã upload bằng Advanced RAG"""
    try:
        result = document_rag.qa_chain(
            query=query,
            filename=filename,
            limit=limit
        )
        return {
            "status": "success",
            "answer": result.get("answer"),
            "sources": result.get("sources", []),
            "method": result.get("method", "rag"),
            "message": f"✅ Đã tìm kiếm trong tài liệu: {filename or 'tất cả file'}"
        }
    except Exception as e:
        logger.error(f"search_document_tool error: {e}")
        return {
            "status": "error",
            "message": f"Lỗi khi tìm kiếm tài liệu: {str(e)}"
        }


# ====================== TOOL CŨ ĐÃ COMMENT ĐỂ TRÁNH XUNG ĐỘT ======================
# @tool
# def summarize_document_tool(filename: str) -> Dict[str, Any]:
#     """Tóm tắt toàn bộ tài liệu (sử dụng summarize_full_document)"""
#     try:
#         logger.info(f"🔧 summarize_document_tool called for: {filename}")
#         summary = document_rag.summarize_full_document(filename)
#         return {
#             "status": "success",
#             "summary": summary,
#             "message": f"✅ Đã tóm tắt tài liệu {filename}"
#         }
#     except Exception as e:
#         logger.error(f"Summarize error for {filename}: {e}")
#         return {"status": "error", "message": str(e)}
# ===============================================================================


@tool
def extract_table_tool(filename: str, table_description: str = "") -> Dict[str, Any]:
    """Trích xuất bảng từ tài liệu"""
    try:
        query = f"Trích xuất và trình bày rõ ràng, đầy đủ tất cả bảng trong tài liệu. {table_description}"
        result = document_rag.qa_chain(
            query=query,
            filename=filename
        )
        return {
            "status": "success",
            "tables": result.get("answer"),
            "message": f"✅ Đã trích xuất bảng từ tài liệu {filename}"
        }
    except Exception as e:
        logger.error(f"Extract table error: {e}")
        return {"status": "error", "message": str(e)}


@tool
def list_uploaded_documents_tool() -> Dict[str, Any]:
    """Liệt kê tất cả tài liệu đã upload"""
    try:
        from app.rag.documents.document_vector_store import DocumentVectorStore
        vector_store = DocumentVectorStore()
        
        docs = vector_store.similarity_search(" ", k=100)
        
        filenames = sorted(list(set(
            doc.metadata.get("filename") 
            for doc in docs 
            if doc.metadata.get("filename")
        )))

        return {
            "status": "success",
            "files": filenames,
            "count": len(filenames),
            "message": f"📋 Tìm thấy {len(filenames)} tài liệu đã upload.",
            "recent_files": filenames[-5:] if filenames else []
        }
    except Exception as e:
        logger.error(f"List documents error: {e}")
        return {
            "status": "success",
            "message": "📋 Danh sách tài liệu sẽ được hiển thị ở Data Preview Panel.",
        }


# Chỉ export các tool còn hoạt động (không bao gồm tool cũ)
document_tools = [
    search_document_tool,
    extract_table_tool,
    list_uploaded_documents_tool,
    # summarize_document_tool đã được chuyển sang app/tools/documents/summarize_document.py
]

print("✅ Document Agent Tools loaded successfully (Old summarize tool has been commented out)") 