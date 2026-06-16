import os
from dotenv import load_dotenv
from langchain_postgres import PGVector
from sqlalchemy import text
from langchain_core.documents import Document

load_dotenv()

class DocumentVectorStore:
    def __init__(self):
        # Lấy tên model từ .env (mặc định là all-MiniLM-L6-v2)
        embedding_model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        hf_token = os.getenv("HF_TOKEN")

        # 🔥 SỬA LỖI RAM: Kiểm tra điều kiện môi trường để nạp Embedding phù hợp
        if hf_token:
            # Bản chạy qua API Cloud (Tốn 0MB RAM - Dành cho Render Free)
            from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
            self.embeddings = HuggingFaceInferenceAPIEmbeddings(
                api_key=hf_token,
                model_name=embedding_model
            )
            print(f"🚀 [VectorStore] Đang sử dụng HuggingFace Inference API Cloud (0MB RAM)")
        else:
            # Bản tải cục bộ về máy (Tốn ~400MB RAM - Dành cho Local chạy Offline)
            from langchain_huggingface import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
            print(f"💻 [VectorStore] Đang tải mô hình {embedding_model} trực tiếp vào RAM Local")

        conn_string = os.getenv("POSTGRES_VECTOR_URI")
        if not conn_string:
            raise ValueError("❌ POSTGRES_VECTOR_URI không được tìm thấy trong .env")

        self.vectorstore = PGVector(
            embeddings=self.embeddings,
            collection_name="user_documents",
            connection=conn_string,
            use_jsonb=True,
        )

    # =========================
    # ADD DOCUMENTS
    # =========================
    def add_documents(self, documents, filename=None):
        """
        Add documents + chống duplicate theo filename
        """
        if filename:
            self.delete_document(filename)

        return self.vectorstore.add_documents(documents)

    # =========================
    # DELETE DOCUMENT (SAFE WITH EXPLICIT CAST)
    # =========================
    def delete_document(self, filename: str):
        """
        Xoá toàn bộ chunks theo filename thuộc đúng collection quy định.
        """
        try:
            collection_name = self.vectorstore.collection_name

            sql = text("""
                DELETE FROM langchain_pg_embedding
                WHERE cmetadata->>'filename' = :filename
                  AND collection_id = (
                      SELECT id FROM langchain_pg_collection 
                      WHERE name = :collection_name 
                      LIMIT 1
                  )::uuid
            """)

            with self.vectorstore._engine.connect() as conn:
                conn.execute(sql, {"filename": filename, "collection_name": collection_name})
                conn.commit()
            print(f"[VECTOR DELETE] Đã dọn sạch các chunk cũ của file: {filename}")
        except Exception as e:
            print(f"[VectorStore Error] Không thể xóa document {filename}: {e}")

    # =========================
    # SEARCH
    # =========================
    def similarity_search(self, query: str, k: int = 10, filter: dict = None):
        return self.vectorstore.similarity_search(query, k=k, filter=filter)
        
    def similarity_search_with_score(self, query: str, k: int = 10, filter: dict = None):
        return self.vectorstore.similarity_search_with_score(query=query, k=k, filter=filter)
        
    def as_retriever(self, **kwargs):
        return self.vectorstore.as_retriever(**kwargs)
        
    # =========================
    # GET ALL CHUNKS (ORDERED & SAFE WITH EXPLICIT CAST)
    # =========================
    def get_all_chunks_by_filename(self, filename: str):
        try:
            docs = []
            collection_name = self.vectorstore.collection_name

            sql = text("""
                SELECT document, cmetadata
                FROM langchain_pg_embedding
                WHERE cmetadata->>'filename' = :filename
                  AND cmetadata->>'chunk_id' IS NOT NULL
                  AND collection_id = (
                      SELECT id FROM langchain_pg_collection 
                      WHERE name = :collection_name 
                      LIMIT 1
                  )::uuid
                ORDER BY CAST(cmetadata->>'chunk_id' AS INTEGER) ASC
            """)

            with self.vectorstore._engine.connect() as conn:
                rows = conn.execute(sql, {"filename": filename, "collection_name": collection_name})

                for row in rows:
                    docs.append(
                        Document(
                            page_content=row.document,
                            metadata=row.cmetadata
                        )
                    )

            print(f"[SUMMARY] {filename} -> {len(docs)} chunks")
            return docs

        except Exception as e:
            print(f"[VectorStore Error] get_all_chunks_by_filename: {e}")
            return []

    # =========================
    # GET BY METADATA (SAFE WITH EXPLICIT CAST)
    # =========================
    def get_documents_by_metadata(self, filename: str, doc_type: str):
        try:
            docs = []
            collection_name = self.vectorstore.collection_name

            sql = text("""
                SELECT document, cmetadata
                FROM langchain_pg_embedding
                WHERE cmetadata->>'filename' = :filename
                  AND cmetadata->>'doc_type' = :doc_type
                  AND collection_id = (
                      SELECT id FROM langchain_pg_collection 
                      WHERE name = :collection_name 
                      LIMIT 1
                  )::uuid
                ORDER BY 
                    CAST(cmetadata->>'summary_id' AS INTEGER) NULLS LAST,
                    id ASC
            """)

            with self.vectorstore._engine.connect() as conn:
                rows = conn.execute(sql, {
                    "filename": filename,
                    "doc_type": doc_type,
                    "collection_name": collection_name
                })

                for row in rows:
                    docs.append(
                        Document(
                            page_content=row.document,
                            metadata=row.cmetadata
                        )
                    )

            print(f"[SUMMARY] {filename} -> {len(docs)} {doc_type}")
            return docs

        except Exception as e:
            print(f"[VectorStore Error] get_documents_by_metadata: {e}")
            try:
                return self.similarity_search(
                    query="",
                    k=50,
                    filter={
                        "filename": filename,
                        "doc_type": doc_type
                    }
                )
            except:
                return []