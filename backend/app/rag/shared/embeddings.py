# backend/app/rag/shared/embeddings.py
import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
import logging

load_dotenv()
logger = logging.getLogger(__name__)


class EmbeddingManager:
    """
    Quản lý Embedding models - Dễ dàng thay đổi model sau này
    """
    
    _instance = None
    _embeddings = None

    @classmethod
    def get_embeddings(cls):
        """Singleton pattern cho embeddings"""
        if cls._embeddings is None:
            try:
                model_name = os.getenv(
                    "EMBEDDING_MODEL", 
                    "sentence-transformers/all-MiniLM-L6-v2"
                )
                
                cls._embeddings = HuggingFaceEmbeddings(
                    model_name=model_name,
                    model_kwargs={'device': 'cpu'},  # Thay 'cuda' nếu có GPU
                    encode_kwargs={'normalize_embeddings': True}
                )
                logger.info(f"✅ Embeddings loaded: {model_name}")
            except Exception as e:
                logger.error(f"❌ Failed to load embeddings: {e}")
                raise
        return cls._embeddings

    @classmethod
    def get_embedding_function(cls):
        """Trả về embedding function thuần (dùng cho vector store)"""
        return cls.get_embeddings().embed_documents

    @staticmethod
    def embed_query(text: str):
        """Embed một query đơn lẻ"""
        embeddings = EmbeddingManager.get_embeddings()
        return embeddings.embed_query(text)

    @staticmethod
    def embed_documents(texts: list):
        """Embed nhiều documents"""
        embeddings = EmbeddingManager.get_embeddings()
        return embeddings.embed_documents(texts)