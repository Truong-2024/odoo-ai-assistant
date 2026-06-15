from langchain_core.tools import tool
from typing import Dict, Any, Optional
import logging

# XÓA DÒNG IMPORT TOÀN CỤC VÀ KHỞI TẠO INSTANCE SỚM Ở ĐÂY ĐỂ CHẶN LỖI VÒNG LẶP
from app.tools.documents.document_utils import format_document_response, create_error_response

logger = logging.getLogger(__name__)


@tool
async def summarize_document_tool(filename: str, focus: Optional[str] = None) -> Dict[str, Any]:
    """
    Tóm tắt toàn bộ tài liệu theo phong cách chuyên nghiệp cao cấp.
    Tool này hỗ trợ xử lý bất đồng bộ (async/await) mượt mà.
    """
    try:
        logger.info(f"🔧 summarize_document_tool (ASYNC) called for: {filename} | focus: {focus}")
        
        # ====================== FIX 1: VALIDATE FILENAME ======================
        if not filename or filename.strip() == "" or filename.lower().strip() in [
            "tài liệu đã upload",
            "file",
            "document",
            "unknown"
        ]:
            logger.error(f"❌ Invalid filename received: {filename}")
            return create_error_response(
                "Tên file không hợp lệ. Vui lòng chọn lại tài liệu cần tóm tắt."
            )

        # ====================== FIX 2: NORMALIZE FILENAME ======================
        filename = filename.strip()

        # ====================== FIX 3: LAZY SINGLETON RAG ======================
        # Khởi tạo an toàn bên trong hàm để không gây lỗi đứng server lúc khởi động
        from app.rag.documents.document_rag import DocumentRAG
        doc_rag = DocumentRAG()
        
        # 🔥 ĐÃ SỬA: Thêm toán tử await để kích hoạt và lấy dữ liệu thật từ hàm Async RAG
        summary = await doc_rag.summarize_full_document(filename)   
        
        if not summary or "coroutine object" in str(summary).lower():
            summary = "Không thể tạo tóm tắt cho tài liệu này."
            
        # ====================== FIX 4: HARD GUARD OUTPUT ======================
        return {
            "data": {
                "answer": summary or "",
                "filename": filename,
                "method": "full_document_summary",
                "safe_summary": True
            },
            "sources": []
        }

    except Exception as e:
        logger.error(f"Summarize Document Tool Error for {filename}: {e}", exc_info=True)
        return create_error_response(f"Lỗi khi tóm tắt tài liệu **{filename}**: {str(e)}")