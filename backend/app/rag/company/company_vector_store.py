# backend/app/rag/company/company_vector_store.py
import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector

load_dotenv()


class CompanyVectorStore:
    """
    Vector Store chuyên biệt cho dữ liệu nội bộ công ty (Odoo)
    """
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        )
        
        conn_string = os.getenv("POSTGRES_VECTOR_URI")
        if not conn_string:
            raise ValueError("❌ POSTGRES_VECTOR_URI không được tìm thấy trong .env")

        self.vectorstore = PGVector(
            embeddings=self.embeddings,
            collection_name="company_knowledge",   # Collection riêng cho company data
            connection=conn_string,
            use_jsonb=True,
        )

    def add_documents(self, documents):
        """Thêm documents vào vector store"""
        return self.vectorstore.add_documents(documents)

    def similarity_search(self, query: str, k: int = 10, filter: dict = None):
        return self.vectorstore.similarity_search(query, k=k, filter=filter)

    def as_retriever(self, **kwargs):
        return self.vectorstore.as_retriever(**kwargs)

    def delete_collection(self):
        """Xóa toàn bộ collection (dùng khi ingest lại)"""
        self.vectorstore.delete_collection()