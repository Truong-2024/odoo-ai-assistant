import os
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)

# Định nghĩa cấu trúc JSON bắt buộc LLM phải trả về
class RewrittenOutput(BaseModel):
    reasoning: str = Field(description="Tư duy phân tích ngắn gọn lý do chọn file hoặc giữ nguyên câu hỏi.")
    clean_query: str = Field(description="Câu hỏi hoàn chỉnh, độc lập sau khi đã sửa lỗi chính tả, bù dấu và bổ sung ngữ cảnh file.")
    # 🔥 THÀNH PHẦN MỚI: Tự động phát hiện file đích từ câu hỏi và lịch sử chat
    predicted_file: str = Field(description="Tên chính xác của file từ DANH SÁCH FILE ĐANG CÓ mà câu hỏi này đang hướng tới. Nếu câu hỏi chung chung hoặc tiếp diễn mạch cũ, hãy điền tên file gần nhất được nhắc tới trong lịch sử chat.")

async def rewrite_contextual_query_v2(
    current_query: str, 
    chat_history: List[Dict[str, Any]], 
    active_files: List[str] = None
) -> Dict[str, str]:  # Thay đổi kiểu trả về thành Dict để vừa lấy được query sạch, vừa lấy được file định tuyến
    """
    Tự động sửa lỗi chính tả, chuẩn hóa tiếng Việt và thông minh dự đoán file đích 
    để định tuyến ngữ cảnh linh hoạt như ChatGPT.
    """
    fallback_result = {"clean_query": current_query.replace("\n", " ").strip(), "predicted_file": active_files[0] if active_files else ""}
    
    if not active_files or "[auto_summarize]" in current_query.lower():
        return fallback_result

    try:
        groq_api_key = os.getenv("GROQ_API_KEY")
        
        # Khởi tạo mô hình
        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.0,  # Giữ nguyên độ chính xác cao nhất để kiểm soát cấu trúc output
            api_key=groq_api_key,
            max_tokens=250
        )
        
        # Ép mô hình tuân thủ tuyệt đối cấu trúc Pydantic mới
        structured_llm = llm.with_structured_output(RewrittenOutput)

        # Trích xuất lịch sử trò chuyện gần nhất
        history_str = ""
        for msg in chat_history[-4:]:
            role = "User" if msg.get("role") in ["user", "human"] else "AI"
            content = msg.get("content", "")
            history_str += f"{role}: {content}\n"

        files_list_str = "\n".join([f"- {f}" for f in active_files])

        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "Bạn là bộ tiền xử lý ngôn ngữ và định tuyến ngữ cảnh cấp cao cho hệ thống RAG đa tài liệu.\n"
                "Nhiệm vụ của bạn là tối ưu hóa câu hỏi của người dùng và xác định chính xác tài liệu họ muốn truy vấn.\n\n"
                
                "🔥 CÁC QUY TẮC BẮT BUỘC ĐỂ TRÁNH LỖI HỆ THỐNG:\n"
                "1. TUYỆT ĐỐI GIỮ NGUYÊN Ý ĐỊNH HỎI: Nếu câu hỏi chứa một chủ đề hoàn toàn mới (Ví dụ: 'Thuyết hữu dụng', 'Hàm sản xuất'), KHÔNG ĐƯỢC PHÉP tự ý bẻ lái câu hỏi về chủ đề cũ trong lịch sử chat.\n"
                "2. SỬA LỖI CHÍNH TẢ & BÙ DẤU CHUẨN XÁC: Tự động bổ sung dấu tiếng Việt và sửa lỗi gõ sai cấu trúc từ.\n"
                "   ⚠️ CRITICAL RULE FOR VIETNAMESE VERBS: Không bao giờ được bóp méo, làm sai lệch hoặc đổi tên các động từ hành động cốt lõi của người dùng. "
                "Tuyệt đối KHÔNG ĐƯỢC biến đổi từ 'tóm tắt' thành bất cứ từ sai chính tả nào khác (ví dụ: KHÔNG đổi thành 'tôm tát', 'tôm tắt'). Giữ nguyên dạng chuẩn hóa: 'tóm tắt', 'phân tích', 'kiểm tra'.\n"
                "3. KHÔNG ĐƯỢC NHẠI LẠI LỊCH SỬ: Trường 'clean_query' CHỈ ĐƯỢC CHỨA DUY NHẤT một câu hỏi ngắn gọn độc lập của lượt hỏi hiện tại.\n"
                "4. ĐỊNH TUYẾN NGỮ CẢNH ĐỘNG (QUAN TRỌNG): Dựa vào các từ khóa trong câu hỏi mới và dòng chảy hội thoại trong lịch sử chat, hãy đối chiếu với 'DANH SÁCH FILE ĐANG CÓ' để chọn ra tên file phù hợp nhất điền vào trường 'predicted_file'.\n"
                "   - Nếu câu hỏi hỏi về AI, mạng nơ-ron -> Chọn file liên quan đến trí tuệ nhân tạo.\n"
                "   - Nếu câu hỏi hỏi về cung cầu, giá cả, tiêu dùng -> Chọn file liên quan đến kinh tế vi mô.\n"
                "   - Nếu câu hỏi mập mờ, hãy ưu tiên chọn file gần nhất đang được thảo luận ở cuối lịch sử chat."
            )),
            ("human", (
                "--- DANH SÁCH FILE ĐANG CÓ ---\n"
                "{files_list}\n\n"
                "--- LỊCH SỬ CHAT ---\n"
                "{history}\n\n"
                "--- CÂU HỎI MỚI NHẤT CẦN XỬ LÝ ---\n"
                "'{query}'"
            ))
        ])

        chain = prompt | structured_llm
        
        # Gọi API
        result: RewrittenOutput = await chain.ainvoke({
            "files_list": files_list_str,
            "history": history_str or "Không có lịch sử",
            "query": current_query
        })

        clean_result = result.clean_query.replace("\n", " ").strip()
        
        # Kiểm tra tính hợp lệ của file được dự đoán để tránh lỗi bốc trùng tên lạ
        final_file = result.predicted_file.strip("- ") if result.predicted_file else ""
        if final_file not in active_files:
            # Fallback về file đầu tiên hoặc file cuối cùng hoạt động nếu LLM điền sai tên file
            final_file = active_files[0] if active_files else ""

        logger.info(f"🧠 [REWRITER REASONING]: {result.reasoning}")
        logger.info(f"🔄 [ROUTE ROUTING] File đích được chọn: '{final_file}'")
        logger.info(f"🔄 [QUERY REWRITER] Gốc: '{current_query}' ➔ Sạch: '{clean_result}'")
        
        return {
            "clean_query": clean_result,
            "predicted_file": final_file
        }

    except Exception as e:
        logger.error(f"❌ Lỗi Query Rewriter: {e}")
        return fallback_result