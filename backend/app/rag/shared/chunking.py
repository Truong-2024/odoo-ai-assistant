# backend/app/rag/shared/chunking.py
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
import logging
from typing import List
from langchain_core.documents import Document   # ← Thêm import thiếu

logger = logging.getLogger(__name__)


class DocumentChunker:

    @staticmethod
    def get_semantic_chunker():
        """Semantic Chunking - Tốt hơn rất nhiều cho tài liệu dài"""
        embeddings = OpenAIEmbeddings()  # hoặc embedding model bạn đang dùng
        return SemanticChunker(
            embeddings,
            breakpoint_threshold_type="percentile",  # hoặc "interquartile"
            number_of_chunks= None,  # tự động
        )

    @staticmethod
    def split_documents(documents: List[Document], strategy: str = "recursive"):
        if strategy == "semantic" and len(documents) == 1 and len(documents[0].page_content) > 2000:
            # Dùng semantic cho document dài
            chunker = DocumentChunker.get_semantic_chunker()
            chunks = chunker.split_documents(documents)
        else:
            # Recursive + page aware
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=800,
                chunk_overlap=150,
                separators=["\n\n", "\n", " [BẢNG]", "\n[BẢNG]", ".", "!", "?", " ", ""],
                add_start_index=True,
            )
            chunks = splitter.split_documents(documents)

        # Thêm metadata chunk
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i
            chunk.metadata["chunk_size"] = len(chunk.page_content)

        logger.info(f"Split {len(documents)} docs → {len(chunks)} chunks using {strategy}")
        return chunks 