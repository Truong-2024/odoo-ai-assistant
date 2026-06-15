import os
import logging
from typing import List, Optional
import numpy as np 
import json
import asyncio
# Cấu hình OCR Tesseract cục bộ
TESSERACT_DIR = r"C:\Program Files\Tesseract-OCR"
if os.path.exists(TESSERACT_DIR):
    # 1. Bổ sung vào PATH chạy nội bộ của Python
    if TESSERACT_DIR not in os.environ["PATH"]:
        os.environ["PATH"] = TESSERACT_DIR + os.pathsep + os.environ["PATH"]
    
    # 2. Định nghĩa biến môi trường bắt buộc cho bộ thư viện unstructured
    os.environ["OCR_AGENT"] = "tesseract"
    
    # 3. Đề phòng nếu tầng dưới gọi pytesseract thuần
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = os.path.join(TESSERACT_DIR, "tesseract.exe")
    except ImportError:
        pass
else:
    logging.getLogger(__name__).warning(
        f"⚠️ [OCR PATCH] Không tìm thấy thư mục Tesseract tại: {TESSERACT_DIR}. "
        f"Vui lòng kiểm tra lại đường dẫn cài đặt phần mềm!"
    )

# Thư viện LangChain và Tiện ích hỗ trợ
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.pydantic_v1 import BaseModel, Field

# Loaders hệ thống
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredImageLoader

from app.rag.documents.document_vector_store import DocumentVectorStore
from fastapi import Request
from starlette.concurrency import run_in_threadpool
from types import SimpleNamespace

logger = logging.getLogger(__name__)


class Chapter(BaseModel):
    chapter_number: int = Field(description="Số thứ tự chương")
    title: str = Field(description="Tiêu đề chương")
    start_page: int = Field(description="Trang bắt đầu")
    end_page: int = Field(description="Trang kết thúc")


class TableOfContents(BaseModel):
    chapters: list[Chapter]


# ASYNC FUNCTION: Trích xuất mục lục bất đồng bộ
async def extract_toc_with_llm(first_few_pages_text: str, llm, request: Optional[Request] = None) -> SimpleNamespace:
    """
    Trích xuất mục lục từ văn bản thô bằng chế độ JSON thuần của Groq (Hỗ trợ ngắt kết nối)
    """
    try:
        if request and await request.is_disconnected():
            logger.warning("🛑 [TOC] Huỷ bóc tách mục lục do Client ngắt kết nối.")
            return SimpleNamespace(chapters=[])

        llm_json = llm.bind(response_format={"type": "json_object"})

        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "Bạn là chuyên gia phân tích cấu trúc tài liệu.\n"
                "Nhiệm vụ của bạn là trích xuất mục lục các chương từ văn bản được cung cấp.\n"
                "BẮT BUỘC phải trả về một đối tượng JSON hợp lệ có định dạng chính xác như sau:\n"
                "{{\n"
                '  "chapters": [\n'
                '    {{"chapter_number": 1, "title": "Tên chương bằng tiếng Việt", "start_page": 4, "end_page": 22}},\n'
                '    {{"chapter_number": 2, "title": "Tên chương tiếp theo", "start_page": 23, "end_page": 64}}\n'
                '  ]\n'
                "}}\n"
                "Lưu ý: Giữ nguyên văn chữ tiếng Việt, không tự ý sửa đổi từ ngữ."
            )),
            ("human", "Văn bản mục lục thô:\n\n{text}")
        ])

        chain = prompt | llm_json
        response = await chain.ainvoke({"text": first_few_pages_text})
        
        toc_data = json.loads(response.content, object_hook=lambda d: SimpleNamespace(**d))
        return toc_data

    except Exception as e:
        logger.error(f"[TOC EXTRACTION ERROR] Thất bại khi bóc tách mục lục bằng JSON mode: {e}")
        return SimpleNamespace(chapters=[])


class DocumentRAG:
    def __init__(self):
        self.vector_store = DocumentVectorStore()
        self.llm = None
        self.reranker = None
        self.compression_retriever = None

        self._init_llm()
        self._init_reranker()

    def _init_llm(self):
        try:
            logger.info("[LLM INIT] Đang cấu hình chuỗi Model Dự phòng tự động (LLM Fallbacks)...")
            fallback_models = [
                "llama-3.3-70b-versatile",  
                "mixtral-8x7b-32768",      
                "llama-3.1-8b-instant",    
                "gemma2-9b-it",            
                "llama3-70b-8192"          
            ]
            
            groq_api_key = os.getenv("GROQ_API_KEY")
            llm_objects = []
            
            for model_name in fallback_models:
                llm_objects.append(
                    ChatGroq(
                        model=model_name,
                        temperature=0.0,
                        api_key=groq_api_key,
                        max_tokens=1000,
                    )
                )
            
            primary_llm = llm_objects[0]
            backup_llms = llm_objects[1:]
            
            self.llm = primary_llm.with_fallbacks(backup_llms)
            logger.info(f"[LLM INIT] Kích hoạt thành công lá chắn 5 lớp: {', '.join(fallback_models)}")
            
        except Exception as e:
            logger.error(f"Failed to init LLM with Fallbacks: {e}")
            self.llm = None

    def _init_reranker(self):
        try:
            cross_encoder = HuggingFaceCrossEncoder(
                model_name=os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L6-v2")
            )
            self.reranker = CrossEncoderReranker(model=cross_encoder, top_n=15)
        except Exception as e:
            logger.warning(f"Reranker init failed: {e}")
            self.reranker = None

        base_retriever = self.vector_store.as_retriever(search_kwargs={"k": 25})
        if self.reranker:
            self.compression_retriever = ContextualCompressionRetriever(
                base_compressor=self.reranker,
                base_retriever=base_retriever
            )
        else:
            self.compression_retriever = base_retriever

    # ====================== INDEX DOCUMENT ======================
    async def index_document(self, file_path: str, filename: str, request: Optional[Request] = None) -> int:
        """Chỉ index chunks (Hỗ trợ ngắt kết nối an toàn + cleanup file)"""
        try:
            if request and await request.is_disconnected():
                logger.warning(f"🛑 [INDEX] Huỷ ngay khi vào index_document: {filename}")
                self._cleanup_file(file_path)
                return 0

            # Load document qua threadpool tránh block event loop
            docs = await run_in_threadpool(self._load_document, file_path, filename)
            
            if not docs:
                raise ValueError("Không trích xuất được nội dung văn bản.")

            if request and await request.is_disconnected():
                logger.warning(f"🛑 [INDEX] Huỷ tiến trình sau khi load document: {filename}")
                self._cleanup_file(file_path)
                return 0

            # --- THỰC HIỆN BÓC TÁCH MỤC LỤC TRƯỚC KHI CẮT CHUNK ---
            toc_json = None
            if filename.lower().endswith('.pdf') and self.llm:
                try:
                    # Tăng từ docs[:5] lên docs[:12] để bao phủ hết mục lục bài giảng/slide nằm ở các trang sau
                    first_pages = docs[:12]
                    first_pages_text = "\n".join([d.page_content for d in first_pages])
                    if len(first_pages_text.strip()) > 50:
                        logger.info(f"[LAYOUT INGESTION] Đang phân tích mục lục tự động cho: {filename}")
                        toc_json = await extract_toc_with_llm(first_pages_text, self.llm, request)
                except Exception as toc_err:
                    logger.warning(f"[LAYOUT INGESTION] Bỏ qua bóc tách mục lục do: {toc_err}")

            if request and await request.is_disconnected():
                logger.warning(f"🛑 [INDEX] Huỷ tiến trình trước khi cắt nhỏ văn bản (splitting): {filename}")
                self._cleanup_file(file_path)
                return 0

            chunks = self._split_documents(docs)
            logger.info(f"[INDEX START] {filename} -> {len(chunks)} chunks")

            # Tiêm siêu dữ liệu vào từng mảnh văn bản nhỏ
            for idx, chunk in enumerate(chunks):
                if request and idx % 10 == 0 and await request.is_disconnected():
                    logger.warning(f"🛑 [INDEX] Huỷ tiến trình khi đang cấu trúc metadata chunk thứ {idx}")
                    self._cleanup_file(file_path)
                    return 0

                chunk.metadata.update({
                    "filename": filename,
                    "doc_type": "chunk",
                    "source": file_path,
                    "chunk_id": idx
                })
                
                if toc_json and hasattr(toc_json, 'chapters') and toc_json.chapters:
                    try:
                        current_page = int(chunk.metadata.get("page", 0)) + 1 
                        for ch in toc_json.chapters:
                            if ch.start_page <= current_page <= ch.end_page:
                                chunk.metadata.update({
                                    "chapter_belong": f"Chương {ch.chapter_number}",
                                    "chapter_title": ch.title
                                })
                                break
                    except Exception:
                        pass

            # TẠO CHUNK ĐẶC BIỆT CHỨA TOÀN BỘ MỤC LỤC ĐỂ LƯU VÀO VECTOR STORE
            if toc_json and hasattr(toc_json, 'chapters') and toc_json.chapters:
                try:
                    toc_lines = [f"Mục lục và cấu trúc tổng thể của tài liệu {filename}:"]
                    toc_lines.append(f"Tổng số chương: {len(toc_json.chapters)} chương.")
                    for ch in toc_json.chapters:
                        toc_lines.append(f"- Chương {ch.chapter_number}: {ch.title} (Trang {ch.start_page} đến {ch.end_page})")
                    
                    toc_string_content = "\n".join(toc_lines)
                    
                    # Tạo một Document độc lập đại diện cho cấu trúc tổng quát của file
                    toc_document = Document(
                        page_content=toc_string_content,
                        metadata={
                            "filename": filename,
                            "doc_type": "table_of_contents",  # Đánh dấu tag đặc biệt để truy xuất thẳng khi đếm chương
                            "source": file_path,
                            "page": 0,
                            "chunk_id": 9999
                        }
                    )
                    chunks.append(toc_document)
                    logger.info(f"✨ [LAYOUT INGESTION] Đã tích hợp chunk Mục lục đặc biệt ({len(toc_json.chapters)} chương) vào danh sách index.")
                except Exception as toc_append_err:
                    logger.error(f"Lỗi khi đóng gói chunk mục lục: {toc_append_err}")

            if request and await request.is_disconnected():
                logger.warning(f"🛑 [INDEX] Huỷ tiến trình ngay trước khi lưu dữ liệu vào Vector Store: {filename}")
                self._cleanup_file(file_path)
                return 0

            # Ghi dữ liệu vào Vector Store qua threadpool
            await run_in_threadpool(self.vector_store.add_documents, chunks, filename=filename)

            logger.info(f"Indexed {len(chunks)} chunks from {filename}")
            return len(chunks)

        except Exception as e:
            logger.error(f"Failed to index {filename}: {e}")
            self._cleanup_file(file_path)
            raise

    def _cleanup_file(self, file_path: str):
        """Dọn dẹp file tạm an toàn khi tiến trình bị hủy dọc đường"""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🗑️ Đã xóa file tạm thành công: {os.path.basename(file_path)}")
        except Exception as e:
            logger.error(f"Lỗi xóa file tạm {file_path}: {e}")

    def _load_document(self, file_path: str, filename: str) -> List[Document]:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            
            # Kiểm tra nếu PDF quét ảnh (Độ dài chuỗi text bóc ra quá ít) thì chuyển hướng qua OCR
            total_text_len = sum(len(d.page_content.strip()) for d in docs)
            if total_text_len < 100:
                logger.warning(f"⚠️ [PDF DETECT] Phát hiện {filename} là PDF scan/ảnh. Ép chạy bằng Unstructured OCR...")
                loader = UnstructuredImageLoader(
                    file_path, 
                    mode="elements",
                    strategy="hi_res",
                    ocr_languages=["vie"]
                )
                docs = loader.load()
            return docs
            
        elif ext == ".docx":
            loader = Docx2txtLoader(file_path)
        elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".webp"]:
            loader = UnstructuredImageLoader(
                file_path, 
                mode="elements",
                strategy="hi_res",       # Bắt buộc hi_res để kích hoạt OCR chất lượng cao
                ocr_languages=["vie"]    # Ép Tesseract OCR bóc tách văn bản tiếng Việt
            )
        else:
            raise ValueError(f"Unsupported file type: {ext}")
        return loader.load()
    
    def _split_documents(self, docs: List[Document]) -> List[Document]:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=150,
            separators=["\n\n", "\n", ".", " ", ""],
        )
        return text_splitter.split_documents(docs)

    # ====================== SUMMARIZE FULL DOCUMENT ======================
    async def summarize_full_document(self, filename: str, request: Optional[Request] = None) -> str:
        """
        Bộ tóm tắt thích ứng đa góc nhìn (Chuẩn ChatGPT Chuyên nghiệp)
        Tự động nhận diện loại tài liệu và sinh cấu trúc đầu ra cá nhân hóa,
        đồng thời tích hợp chặt chẽ cấu trúc mục lục tổng thể để chống sót chương.
        """
        try:
            logger.info(f"[PRO SUMMARY] Khởi động bộ tóm tắt thích ứng cao cấp cho: {filename}")
            
            if request and await request.is_disconnected():
                logger.warning("🛑 [PRO SUMMARY] Huỷ ngay khi vừa gọi hàm.")
                return f"Yêu cầu tóm tắt {filename} đã bị hủy."

            # 1. TRUY VẤN SONG SCAN: Lấy cả chunk mục lục đặc biệt và các đoạn nội dung cốt lõi
            logger.info(f"🔍 [PRO SUMMARY] Đang gom ngữ cảnh nội dung và cấu trúc mục lục tổng thể...")
            
            # Chạy đồng thời 2 câu truy vấn lên Vector Store để tiết kiệm thời gian (Giảm Latency)
            async def _get_toc():
                return await run_in_threadpool(
                    self.vector_store.similarity_search_with_score,
                    query="Mục lục tổng thể cấu trúc danh sách tất cả các chương tài liệu số lượng",
                    k=1,
                    filter={"filename": filename, "doc_type": "table_of_contents"}
                )
                
            async def _get_content():
                return await run_in_threadpool(
                    self.vector_store.similarity_search_with_score,
                    query="Nội dung cốt lõi, khái niệm luận điểm, số liệu trọng tâm, định lý, kết luận thực nghiệm",
                    k=25,  
                    filter={"filename": filename}
                )

            toc_results, content_results = await asyncio.gather(_get_toc(), _get_content())
            
            if not content_results and not toc_results:
                return f"Không tìm thấy dữ liệu của tài liệu {filename} trong hệ thống."

            # 2. XỬ LÝ VÀ ĐỒNG BỘ MẠCH NGỮ CẢNH (CONTEXT)
            toc_string = "Không tìm thấy dữ liệu mục lục cấu trúc sẵn có."
            if toc_results:
                toc_string = toc_results[0][0].page_content.strip()

            # Lọc trùng và sắp xếp các đoạn nội dung theo mạch trang tăng dần
            max_chunks = [doc for doc, score in content_results if doc.metadata.get("doc_type") != "table_of_contents"][:18]
            try:
                max_chunks.sort(key=lambda x: (
                    int(x.metadata.get('page', 0)), 
                    int(x.metadata.get('chunk_id', x.metadata.get('index', 0)))
                ))
            except Exception:
                pass

            context_parts = []
            for i, doc in enumerate(max_chunks):
                content = doc.page_content.strip()
                compressed_content = " ".join(content.split())[:1200] # Giới hạn 1200 từ sâu cho mỗi chunk
                page_info = f"Trang {doc.metadata.get('page', '?')}"
                if "chapter_belong" in doc.metadata:
                    page_info += f" - {doc.metadata['chapter_belong']}"
                context_parts.append(f"[Đoạn {i+1} ({page_info})]: {compressed_content}")
                
            context = "\n\n".join(context_parts)
            
            # 3. SIÊU PROMPT TƯ DUY 2 BƯỚC (CHUYÊN NGHIỆP CẤP ENTERPRISE)
            dynamic_prompt = f"""
Bạn là một AI phân tích thông tin cấp cao sở hữu tư duy phân loại của ChatGPT Plus và Claude 3.5 Sonnet.
Nhiệm vụ của bạn là đọc cấu trúc mục lục (TOC) và các chuỗi dữ liệu (CONTEXT) trích xuất từ file **{filename}** để lập một bản tóm tắt cá nhân hóa, cô đọng nhưng bao phủ toàn bộ nội dung trọng tâm.

[BƯỚC 1: NHẬN DIỆN VÀ PHÂN LOẠI BIẾN THỂ TÀI LIỆU]
Trước khi viết, hãy phân tích xem dữ liệu thực tế thuộc nhóm nào sau đây để kích hoạt tư duy chuyên biệt:
- Nhóm 1: VĂN BẢN PHÁP LUẬT / QUY ĐỊNH HÀNH CHÍNH. (Cần cấu trúc: Cơ quan ban hành, Điều khoản cốt lõi, Trách nhiệm, Hiệu lực).
- Nhóm 2: GIÁO TRÌNH / TÀI LIỆU HỌC THUẬT / SÁCH NGHIÊN CỨU. (Cần cấu trúc: Tổng quan bài toán, Các trường phái/phương pháp tiếp cận, Kết quả thực nghiệm).
- Nhóm 3: BÁO CÁO TÀI CHÍNH / SỐ LIỆU KINH DOANH. (Cần cấu trúc: Chỉ số tăng trưởng, Bảng so sánh, Khuyến nghị kỹ thuật).
- Nhóm 4: ẢNH CHỤP OCR / INFOGRAPHIC / THÔNG TIN SỰ KIỆN. (Cần cấu trúc: Chuỗi sự kiện tuyến tính, Thông điệp scannable cốt lõi).

[BƯỚC 2: RÀNG BUỘC KIẾN TRÚC ĐẦU RA (QUY TẮC TỐI CAO)]
1. TUYỆT ĐỐI KHÔNG ÁP DỤNG KHUÔN MẪU RẬP KHUÔN CỐ ĐỊNH. Bạn được toàn quyền tự sinh từ 3-4 tiêu đề lớn (##) kèm icon emoji thích hợp, tên tiêu đề phải phản ánh trực tiếp bản chất nội dung file (Ví dụ: ## 🎲 TIẾP CẬN GÁN NHÃN DỰA TRÊN XÁC SUẤT).
2. BAO PHỦ TOÀN DIỆN: Dựa vào cấu trúc Mục lục để phân bổ nội dung tóm tắt đều khắp các chương. Nghiêm cấm việc chỉ tóm tắt chương cuối và bỏ quên các chương giữa.
3. LỌC BỎ CẶN OCR: Loại bỏ hoàn toàn các thông tin trùng lặp, lỗi lặp từ, lỗi xuống dòng ngắt quang do Tesseract OCR quét ảnh gây ra.
4. KHÔNG VIẾT CÂU LƯỜI BIẾNG: Không viết các câu vô nghĩa như "Tài liệu không đề cập chi tiết". Hãy đi thẳng vào bản chất hành vi, công thức hoặc lý thuyết được mô tả trong ngữ cảnh.
5. ĐỘ SÂU THÔNG TIN: Giữ lại các mốc thời gian, con số phần trăm (%), tên thuật toán hoặc thực thể chính. Viết đậm (**bold**) từ khóa quan trọng.

---
[CẤU TRÚC MỤC LỤC TỔNG THỂ CỦA FILE]:
{toc_string}

---
[NGỮ CẢNH DỮ LIỆU NGUYÊN BẢN (ĐỒNG BỘ THEO MẠCH FILE)]:
{context}

---
BẢN TÓM TẮT THÍCH ỨNG CAO CẤP (Định dạng Markdown chuyên nghiệp, scannable, ngắn gọn nhưng đầy đủ):
"""
            
            if request and await request.is_disconnected():
                logger.warning("🛑 [PRO SUMMARY] Ngắt kết nối trước khi gọi API Groq.")
                return "Yêu cầu đã bị hủy."

            # 4. KÍCH HOẠT CHUỖI LLM FALLBACKS
            result = await self.llm.ainvoke(dynamic_prompt)
            logger.info(f"[PRO SUMMARY] Đã xuất bản bản tóm tắt cá nhân hóa thành công cho file: {filename}")
            return result.content.strip()

        except Exception as e:
            logger.error(f"[PRO SUMMARY ERROR] Thất bại hệ thống: {str(e)}", exc_info=True)
            return f"❌ Lỗi hệ thống khi tóm tắt thích ứng: {str(e)[:100]}"

    # ====================== QUERY DOCUMENT (Q&A) ======================
    async def query_document(self, filename: str, query: str, k: int = 10, request: Optional[Request] = None) -> str:
        """
        Truy vấn chuẩn Enterprise Chatbot (Async Version có tính năng huỷ kết nối nhanh)
        """
        try:
            logger.info(f"[ENTERPRISE QA] Tiếp nhận câu hỏi gốc: '{query}' cho tài liệu: {filename}")

            if request and await request.is_disconnected():
                logger.warning("🛑 [ENTERPRISE QA] Huỷ ngay khi tiếp nhận câu hỏi.")
                return "Yêu cầu đã bị hủy."

            # ĐÁNH CHẶN CÂU HỎI MỤC LỤC/SỐ CHƯƠNG TOÀN CỤC
            query_lower = query.lower()
            is_global_query = any(w in query_lower for w in ["chương", "mục lục", "tổng số", "bao nhiêu phần", "tổng quan"])
            
            all_raw_results = []

            if is_global_query:
                logger.info(f"🔍 [GLOBAL RETRIEVAL] Đang ưu tiên bốc chunk cấu trúc tổng thể (table_of_contents) cho file: {filename}")
                # Truy vấn thẳng chunk đặc biệt chứa toàn bộ mục lục cấu trúc qua bộ lọc metadata
                toc_results = await run_in_threadpool(
                    self.vector_store.similarity_search_with_score,
                    query="Mục lục tổng thể cấu trúc danh sách tất cả các chương tài liệu số lượng",
                    k=3,
                    filter={"filename": filename, "doc_type": "table_of_contents"}
                )
                if toc_results:
                    for doc, score in toc_results:
                        all_raw_results.append(doc)
                    logger.info("🎯 [GLOBAL RETRIEVAL] Đã lấy thành công chunk cấu trúc đặc biệt đưa vào ngữ cảnh LLM.")
                else:
                    # FALLBACK DỰ PHÒNG KHI KHÔNG CÓ CHUNK TOC: Quét diện rộng lấy các chunk chứa từ khóa "Chương"
                    logger.warning("🎯 [GLOBAL RETRIEVAL] Không tìm thấy chunk TOC! Kích hoạt quét từ khóa 'Chương' toàn file làm fallback...")
                    backup_results = await run_in_threadpool(
                        self.vector_store.similarity_search_with_score,
                        query="Danh sách cấu trúc gồm các Chương 1 Chương 2 Chương 3 Chương 4 Chương 5 Chương 6 Chương 7 Chương 8 Chương 9 Chương 10",
                        k=25,
                        filter={"filename": filename}
                    )
                    for doc, score in backup_results:
                        all_raw_results.append(doc)

            # Nếu không phải câu hỏi cấu trúc hoặc không thấy chunk đặc biệt/dự phòng nào, chạy luồng Multi-Query mở rộng ngữ nghĩa
            if not all_raw_results:
                expanded_queries = [query] 
                mq_prompt = f"""
Bạn là chuyên gia phân tích ngôn ngữ độc lập. Hãy đọc câu hỏi gốc dưới đây và tự động sinh ra ĐÚNG 3 câu hỏi phụ (biến thể) có cùng bản chất ý nghĩa bằng tiếng Việt.
QUY TẮC: Trả về đúng 3 câu hỏi, mỗi câu một dòng. KHÔNG kèm số thứ tự, KHÔNG viết lời dẫn rườm rà.

CÂU HỎI GỐC: "{query}"

3 BIẾN THỂ NGỮ NGHĨA CHUẨN:
"""
                try:
                    mq_result = await self.llm.ainvoke(mq_prompt)
                    if mq_result and hasattr(mq_result, "content"):
                        raw_lines = mq_result.content.strip().split("\n")
                        cleaned_queries = [line.strip() for line in raw_lines if line.strip() and len(line.strip()) > 5]
                        expanded_queries.extend(cleaned_queries[:3]) 
                except Exception:
                    pass

                if request and await request.is_disconnected():
                    logger.warning("🛑 [ENTERPRISE QA] Huỷ trước bước tìm kiếm Vector.")
                    return "Yêu cầu đã bị hủy."

                seen_contents = set() 
                scan_k = 35 if is_global_query else 25  

                for sub_query in expanded_queries:
                    if request and await request.is_disconnected():
                        logger.warning("🛑 [ENTERPRISE QA] Huỷ vòng lặp tìm kiếm vector giữa chừng.")
                        return "Yêu cầu đã bị hủy."

                    sub_results = await run_in_threadpool(
                        self.vector_store.similarity_search_with_score,
                        query=sub_query,
                        k=scan_k, 
                        filter={"filename": filename}
                    )
                    
                    for doc, score in sub_results:
                        if doc.page_content not in seen_contents:
                            seen_contents.add(doc.page_content)
                            all_raw_results.append(doc)

            if not all_raw_results:
                return "Tôi không tìm thấy thông tin này trong tài liệu."

            if request and await request.is_disconnected():
                logger.warning("🛑 [ENTERPRISE QA] Huỷ trước bước chạy Cross-Encoder Reranker.")
                return "Yêu cầu đã bị hủy."

            # Phân tách luồng xử lý Reranker để tránh cắt ngắn mất chunk mục lục cấu trúc gốc
            if is_global_query and any(d.metadata.get("doc_type") == "table_of_contents" for d in all_raw_results):
                selected_chunks = all_raw_results[:5]
            else:
                if hasattr(self, 'reranker') and self.reranker:
                    all_reranked = await run_in_threadpool(self.reranker.compress_documents, all_raw_results, query)
                    top_slice = 18 if is_global_query else 6
                    selected_chunks = all_reranked[:top_slice] 
                else:
                    top_slice = 18 if is_global_query else 6
                    selected_chunks = all_raw_results[:top_slice]

            try:
                selected_chunks.sort(key=lambda x: (
                    int(x.metadata.get('page', 0)), 
                    int(x.metadata.get('chunk_id', x.metadata.get('index', 0)))
                ))
            except Exception:
                pass

            if request and await request.is_disconnected():
                logger.warning("🛑 [ENTERPRISE QA] Huỷ trước giây gọi LLM chính trả lời câu hỏi.")
                return "Yêu cầu đã bị hủy."

            context_parts = []
            for idx, doc in enumerate(selected_chunks):
                page_num = doc.metadata.get('page', '?')
                chapter_info = ""
                if "chapter_belong" in doc.metadata:
                    chapter_info = f" ({doc.metadata['chapter_belong']} - {doc.metadata.get('chapter_title', '')})"
                
                raw_content = doc.page_content.strip()
                # Đối với chunk mục lục đặc biệt, giữ nguyên độ dài toàn vẹn cấu trúc
                if doc.metadata.get("doc_type") == "table_of_contents":
                    clean_content = raw_content
                else:
                    clean_content = " ".join(raw_content.split())[:800] # Mở rộng giới hạn đọc của đoạn văn lên 800 từ chuyên sâu
                
                context_parts.append(f"[Đoạn dữ liệu {idx+1} - Trang {page_num}{chapter_info}]:\n{clean_content}")

            context = "\n\n".join(context_parts)

            qa_prompt = f"""
Bạn là chuyên gia phân tích dữ liệu và giải đáp tài liệu cấp cao. Hãy trả lời câu hỏi của người dùng một cách chính xác, sâu sắc và chuyên nghiệp dựa trên chuỗi dữ liệu (CONTEXT) đã được trích xuất và đồng bộ theo thứ tự trang dưới đây.

QUY TẮC ĐÁNH GIÁ VÀ ĐỊNH DẠNG ĐẦU RA (BẮT BUỘC):
1. **Tính chính xác tối cao**: Chỉ trả lời dựa vào dữ liệu có trong CONTEXT. Tuyệt đối không tự suy đoán.
2. **Quy tắc từ chối**: Nếu CONTEXT hoàn toàn không chứa thông tin, hãy trả lời đúng nguyên văn câu dưới đây:
"Tôi không tìm thấy thông tin này trong tài liệu."
3. **QUY TẮC ĐỊNH DẠNG (QUAN TRỌNG NHẤT)**: 
   - KHÔNG LIỆT KÊ hoặc hiển thị lại các tiêu đề nhãn dạng "[Đoạn dữ liệu 1 - Trang...]", "[Đoạn dữ liệu 2]..." từ phần ngữ cảnh vào câu trả lời.
   - Hãy tổng hợp thông tin một cách tự nhiên. Nếu nhiều đoạn dữ liệu cùng nói về một nội dung (ví dụ: cùng xác nhận tài liệu có 10 chương), hãy gộp lại thành MỘT kết luận duy nhất, ngắn gọn và trực tiếp.
   - Không viết câu trả lời theo kiểu lặp đi lặp lại cấu trúc ngữ cảnh.

NGỮ CẢNH TÀI LIỆU (CONTEXT):
{context}

CÂU HỎI CỦA NGƯỜI DÙNG:
{query}

CÂU TRẢ LỜI KHÁCH QUAN VÀ MẠCH LẠC (Sử dụng Markdown, gạch đầu dòng, viết đậm từ khóa quan trọng):
"""

            result = await self.llm.ainvoke(qa_prompt)
            answer = result.content.strip() if result and hasattr(result, "content") else ""

            if not answer:
                return "Tôi không tìm thấy thông tin này trong tài liệu."

            suspicious_phrases = ["theo kiến thức bên ngoài", "ngoài tài liệu", "tôi đoán là", "thực tế ngoài đời"]
            if any(phrase in answer.lower() for phrase in suspicious_phrases):
                return "Tôi không tìm thấy thông tin này trong tài liệu."

            logger.info(f"[ENTERPRISE QA] Xuất bản câu trả lời thành công!")
            return answer

        except Exception as e:
            logger.error(f"[ENTERPRISE QA ERROR] Thất bại: {e}", exc_info=True)
            return f"❌ Lỗi hệ thống khi truy vấn tài liệu chuẩn Enterprise: {str(e)[:100]}"
            
    def _has_query_overlap(self, query, context):
        query_words = {w.lower() for w in query.split() if len(w) > 2}
        context_lower = context.lower()
        hits = sum(1 for w in query_words if w in context_lower)
        return hits >= 1