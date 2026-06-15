# backend/app/services/document_service.py
import logging
from typing import Dict, Any, List
from fastapi import UploadFile

from app.rag.documents.document_rag import DocumentRAG
from app.rag.documents.document_loader import DocumentLoader

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Service layer cho Document Agent & Upload
    """

    @staticmethod
    async def upload_and_index(file: UploadFile, current_user: str) -> Dict[str, Any]:
        """Upload file và index vào vector store"""
        try:
            # Load file thành List[Document] (hỗ trợ page-aware)
            docs = await DocumentLoader.load_file_to_documents(file, current_user)

            # Index vào DocumentRAG
            doc_rag = DocumentRAG()
            doc_rag.vector_store.add_documents(docs)   # Sửa thành add_documents (plural)

            logger.info(f"✅ Document indexed: {file.filename} → {len(docs)} chunks")
            return {
                "status": "success",
                "message": f"Đã index file **{file.filename}** thành công",
                "filename": file.filename,
                "doc_id": docs[0].metadata.get("doc_id") if docs else None,
                "pages": len(docs)
            }
        except Exception as e:
            logger.error(f"DocumentService upload error: {e}")
            raise

    @staticmethod
    def search_document(query: str, filename: str = None, k: int = 8) -> Dict[str, Any]:
        """Tìm kiếm và trả lời câu hỏi về tài liệu (thay thế qa_chain cũ)"""
        try:
            doc_rag = DocumentRAG()
            
            # Lấy các chunk liên quan
            docs = doc_rag.retrieve(query=query, filename=filename, k=k)
            
            if not docs:
                return {
                    "answer": "Không tìm thấy thông tin liên quan trong tài liệu.",
                    "sources": [],
                    "method": "no_data"
                }

            context = "\n\n".join([doc["content"] for doc in docs])

            prompt = f"""
Bạn là chuyên gia phân tích tài liệu.
Dựa trên nội dung tài liệu dưới đây, hãy trả lời câu hỏi một cách chính xác, ngắn gọn và bằng tiếng Việt.

**Tài liệu tham khảo:**
{context}

**Câu hỏi:** {query}

Trả lời:
"""

            try:
                result = doc_rag.llm.invoke(prompt)
                answer = result.content.strip()
            except Exception as e:
                logger.error(f"LLM invoke error in search: {e}")
                answer = "Tôi đã tìm thấy thông tin nhưng hiện tại không thể tổng hợp câu trả lời."

            return {
                "answer": answer,
                "sources": docs[:6],
                "method": "document_rag"
            }

        except Exception as e:
            logger.error(f"Document search error: {e}")
            return {
                "answer": "Đã xảy ra lỗi khi tìm kiếm tài liệu.",
                "status": "error"
            }

    @staticmethod
    def summarize_document(filename: str) -> Dict[str, Any]:
        """Tóm tắt tài liệu - sử dụng hàm mới đã tối ưu"""
        try:
            doc_rag = DocumentRAG()
            summary = doc_rag.summarize_full_document(filename)
            
            return {
                "status": "success",
                "summary": summary,
                "filename": filename
            }
        except Exception as e:
            logger.error(f"Summarize error: {e}")
            return {
                "status": "error", 
                "message": str(e),
                "summary": "Không thể tạo tóm tắt lúc này."
            } 