# backend/app/rag/shared/reranker.py
import os
import logging
from dotenv import load_dotenv
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain.retrievers import ContextualCompressionRetriever

load_dotenv()
logger = logging.getLogger(__name__)


class RerankerManager:
    """
    Quản lý Reranker (Cross-Encoder) cho RAG
    """
    
    _reranker = None
    _cross_encoder = None

    @classmethod
    def get_cross_encoder(cls):
        """Singleton cho CrossEncoder"""
        if cls._cross_encoder is None:
            try:
                model_name = os.getenv(
                    "RERANKER_MODEL", 
                    "cross-encoder/ms-marco-MiniLM-L6-v2"
                )
                cls._cross_encoder = HuggingFaceCrossEncoder(model_name=model_name)
                logger.info(f"✅ Reranker CrossEncoder loaded: {model_name}")
            except Exception as e:
                logger.warning(f"⚠️ Cannot load reranker: {e}. Will run without reranking.")
                cls._cross_encoder = None
        return cls._cross_encoder

    @classmethod
    def get_reranker(cls, top_n: int = 8):
        """Trả về CrossEncoderReranker"""
        if cls._reranker is None:
            cross_encoder = cls.get_cross_encoder()
            if cross_encoder:
                cls._reranker = CrossEncoderReranker(
                    model=cross_encoder, 
                    top_n=top_n
                )
        return cls._reranker

    @staticmethod
    def get_compression_retriever(base_retriever, top_n: int = 8):
        """Tạo ContextualCompressionRetriever với reranker"""
        reranker = RerankerManager.get_reranker(top_n=top_n)
        if reranker:
            return ContextualCompressionRetriever(
                base_compressor=reranker,
                base_retriever=base_retriever
            )
        else:
            logger.info("Running without reranker")
            return base_retriever