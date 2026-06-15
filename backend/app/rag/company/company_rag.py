# backend/app/rag/company/company_rag.py
import logging
from typing import List, Dict, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.retrievers.document_compressors import CrossEncoderReranker

from app.rag.company.company_vector_store import CompanyVectorStore

logger = logging.getLogger(__name__)


class CompanyRAG:
    """
    Advanced RAG chuyên biệt cho dữ liệu công ty / Odoo
    """
    def __init__(self):
        self.vector_store = CompanyVectorStore()
        self.llm = None
        self.reranker = None

        # LLM
        try:
            self.llm = ChatGroq(
                model="llama-3.1-8b-instant",
                temperature=0.1,
                max_tokens=800,
            )
        except Exception as e:
            logger.warning(f"LLM init warning: {e}")

        # Reranker
        try:
            cross_encoder = HuggingFaceCrossEncoder(
                model_name="cross-encoder/ms-marco-MiniLM-L6-v2"
            )
            self.reranker = CrossEncoderReranker(model=cross_encoder, top_n=8)
        except Exception as e:
            logger.warning(f"Reranker init failed: {e}")

        base_retriever = self.vector_store.as_retriever(search_kwargs={"k": 12})

        if self.reranker:
            self.compression_retriever = ContextualCompressionRetriever(
                base_compressor=self.reranker,
                base_retriever=base_retriever
            )
        else:
            self.compression_retriever = base_retriever

    def retrieve(self, query: str, k: int = 10) -> List[Dict]:
        """Retrieve documents với reranking"""
        docs = self.compression_retriever.invoke(query)
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": getattr(doc, "score", None)
            }
            for doc in docs[:k]
        ]

    def qa_chain(self, query: str) -> Dict:
        """Main QA cho Company Knowledge"""
        docs = self.retrieve(query)
        context = "\n\n".join([doc["content"] for doc in docs])

        if not docs or len(context) < 50:
            return {
                "answer": "Không tìm thấy thông tin liên quan trong kiến thức công ty.",
                "sources": [],
                "method": "no_data"
            }

        try:
            prompt = ChatPromptTemplate.from_template("""
Bạn là chuyên gia tư vấn Odoo ERP.

**Thông tin tham khảo từ cơ sở dữ liệu công ty:**
{context}

**Câu hỏi:** {question}

Trả lời chính xác, ngắn gọn bằng tiếng Việt:
""")
            chain = prompt | self.llm | StrOutputParser()
            answer = chain.invoke({"context": context, "question": query})

            return {
                "answer": answer.strip(),
                "sources": docs[:6],
                "method": "company_rag"
            }
        except Exception as e:
            logger.error(f"CompanyRAG QA error: {e}")
            return {
                "answer": "Tôi đã tìm nhưng gặp lỗi khi tổng hợp câu trả lời.",
                "sources": docs[:6],
                "method": "error"
            }