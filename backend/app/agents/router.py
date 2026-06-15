# backend/app/agents/router.py
import os
from typing import Dict, Any

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.0,
    max_tokens=512,
    api_key=os.getenv("GROQ_API_KEY"),
)

class IntentClassification(BaseModel):
    agent: str = Field(..., enum=["business", "document", "vision", "general"])
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str
    mentioned_files: list[str] = Field(default_factory=list)
    is_urgent: bool = False


router_prompt = ChatPromptTemplate.from_template("""
Bạn là **Intent Router** thông minh của Odoo AI Assistant.

Hãy phân loại chính xác query của người dùng vào **một** agent sau:

1. **business**     : Liên quan đến Odoo ERP (tạo đơn hàng, báo cáo, tồn kho, sản phẩm...)
2. **document**     : Hỏi về nội dung file/tài liệu đã upload (PDF, Word, Excel...) hoặc các câu hỏi liên quan đến kiến thức trong file đã upload.
3. **vision**       : Chỉ dành cho ảnh, hình ảnh (PNG, JPG, JPEG, WEBP), hóa đơn scan, OCR ảnh
4. **general**      : Chat đời sống, kiến thức chung, tính toán... (không liên quan đến file đang active)

**Quy tắc quan trọng:**
- Nếu người dùng đang có file đã upload (PDF, bài giảng, giáo trình...) và hỏi về nội dung kiến thức liên quan → ưu tiên **document**.
- Nếu query chứa ".pdf", ".docx", ".xlsx", "tóm tắt file", "nội dung file", "trong file", "theo tài liệu", "theo bài giảng" → **document** (confidence cao).
- Nếu query chứa ".png", ".jpg", ".jpeg", "ảnh", "hình ảnh", "OCR", "hóa đơn scan" → **vision**.
- Không bao giờ nhầm PDF sang Vision.

Query: {query}

Trả về JSON hợp lệ theo schema.
""")

structured_llm = llm.with_structured_output(IntentClassification)


def classify_intent(query: str, state: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Phân loại intent với logic bổ sung mạnh mẽ.
    """
    try:
        chain = router_prompt | structured_llm
        result = chain.invoke({"query": query})

        result_dict = result.model_dump() if hasattr(result, 'model_dump') else dict(result)

        q_lower = query.lower()

        # =========================
        # 🔥 FIX 1: RAG-FIRST POLICY (QUAN TRỌNG NHẤT - CHUYÊN NGHIỆP)
        # =========================
        active_document = None
        thread_files = None
        if state:
            active_document = state.get("active_document")
            thread_files = state.get("thread_files", []) or []

        # Ưu tiên tuyệt đối Document nếu có file active hoặc thread có file
        if active_document or (thread_files and len(thread_files) > 0):
            result_dict["agent"] = "document"
            result_dict["confidence"] = 0.98
            result_dict["reason"] = f"Document context detected → force Document Agent (Active: {active_document})"
            if active_document:
                result_dict["mentioned_files"] = [active_document]
            return result_dict

        # =========================
        # 🔥 FIX 2: FILE KEYWORD BOOST
        # =========================
        if any(keyword in q_lower for keyword in [
            "đã tải lên file", "upload file", ".pdf", ".docx", ".xlsx",
            "tóm tắt file", "nội dung file", "file vừa upload",
            "trong tài liệu", "trong file", "theo tài liệu", "theo bài giảng",
            "file này", "pdf này", "gán nhãn", "nhãn", "bài giảng", "tài liệu"
        ]):
            result_dict["agent"] = "document"
            result_dict["confidence"] = 0.96
            result_dict["reason"] = "Detected document reference"

        # =========================
        # 🔥 FIX 3: VISION RULE (GIỮ NGUYÊN LOGIC)
        # =========================
        elif any(keyword in q_lower for keyword in [
            ".png", ".jpg", ".jpeg", ".webp", "ảnh", "hình ảnh", "ocr", "hóa đơn scan"
        ]):
            result_dict["agent"] = "vision"
            result_dict["confidence"] = 0.92
            result_dict["reason"] = "Image/Vision related query"

        # =========================
        # 🔥 FIX 4: LOW CONFIDENCE FALLBACK
        # =========================
        if result_dict.get("confidence", 0) < 0.65:
            if any(k in q_lower for k in ["file", "tài liệu", "bài giảng", "pdf"]):
                result_dict["agent"] = "document"
                result_dict["reason"] = "Low confidence → document safe fallback"
            else:
                result_dict["agent"] = "general"
                result_dict["reason"] = "Low confidence → general fallback"

        return result_dict

    except Exception as e:
        print(f"[Router Error] {e}")

        # =========================
        # 🔥 FIX 5: FAILSAFE
        # =========================
        return {
            "agent": "document",
            "confidence": 0.80,
            "reason": "Router error → fallback Document Agent",
            "mentioned_files": [],
            "is_urgent": False
        } 