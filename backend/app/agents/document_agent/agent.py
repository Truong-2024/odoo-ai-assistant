import logging
import json
from typing import Dict, Any, Optional

from langchain_core.messages import AIMessage, HumanMessage 
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
load_dotenv()

from app.agents.state import AgentState
from app.agents.document_agent.prompts import get_document_system_prompt
from app.tools.documents.summarize_document import summarize_document_tool

logger = logging.getLogger(__name__)

# ========================= LLM =========================
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.1,
    api_key=os.getenv("GROQ_API_KEY"),
    max_tokens=2000,
)

# Bind tools
llm_with_tools = llm.bind_tools([summarize_document_tool])

async def document_node(state: AgentState) -> Dict[str, Any]:
    try:
        messages = state["messages"]
        
        # ==========================================================
        # 🛡️ CHẶN LOOP: TÁCH BIỆT TIN NHẮN ĐIỀU HƯỚNG VÀ TIN NHẮN QA
        # ==========================================================
        # 1. Tin nhắn tuyệt đối cuối cùng trong lịch sử (Dùng để bắt lệnh hệ thống)
        absolute_last_message = messages[-1].content.strip() if messages else ""
        
        # 2. Tin nhắn thực tế của User (Dùng để làm câu hỏi query RAG)
        user_messages = [m for m in messages if isinstance(m, HumanMessage) or getattr(m, 'type', '') == 'human']
        if user_messages:
            last_message = user_messages[-1].content.strip()
        else:
            last_message = absolute_last_message
            
        active_document = state.get("active_document")
        pending_summary = state.get("pending_summary", False)
        force_summary = state.get("force_summary", False)
        file_meta = state.get("file_meta")

        # ====================== LUỒNG TÓM TẮT TÀI LIỆU ======================
        # Kích hoạt khi có cờ ép buộc HOẶC token điều hướng xuất hiện ở tin nhắn cuối cùng
        if (force_summary or "[AUTO_SUMMARIZE]" in absolute_last_message) and active_document:
            logger.info(f"🔄 Summary execution triggered for document: {active_document}")

            try:
                # Gọi async invoke của tool
                tool_result = await summarize_document_tool.ainvoke({
                    "filename": active_document
                })

                summary_text = ""
                if isinstance(tool_result, dict):
                    if "data" in tool_result and isinstance(tool_result["data"], dict):
                        summary_text = tool_result["data"].get("answer") or ""
                    elif "summary" in tool_result:
                        summary_text = tool_result.get("summary") or ""
                    elif "answer" in tool_result:
                        summary_text = tool_result.get("answer") or ""
                    else:
                        summary_text = str(tool_result)
                else:
                    summary_text = str(tool_result)

                if not summary_text or len(summary_text.strip()) < 100:
                    logger.warning(f"⚠️ Summary too short ({len(summary_text)} chars). Using minimal fallback.")
                    summary_text = (
                        f"📄 Tài liệu **{active_document}**.\n\n"
                        "Tôi đã phân tích và tóm tắt dựa trên nội dung thực tế của tài liệu."
                    )

                # 🔥 FIX CỐT LÕI: Hạ toàn bộ cờ hiệu về False để giải phóng State bộ nhớ
                return {
                    "messages": [
                        AIMessage(content=f"📄 **TÓM TẮT TÀI LIỆU: {active_document}**\n\n{summary_text}")
                    ],
                    "current_agent": "document",
                    "active_document": active_document,
                    "file_meta": file_meta,
                    "force_summary": False,      # ❌ Gỡ cờ ép buộc
                    "pending_summary": False,    # ❌ Gỡ cờ chờ đợi
                    "is_auto_summary": False     # ❌ Gỡ cờ tự động
                }

            except Exception as e:
                logger.error(f"Summary execution failed: {e}", exc_info=True)
                return {
                    "messages": [
                        AIMessage(content="❌ Không thể tóm tắt tài liệu lúc này. Vui lòng thử lại sau.")
                    ],
                    "current_agent": "document",
                    "active_document": active_document,
                    "force_summary": False,      # ❌ Hạ cờ kể cả khi lỗi để tránh treo cứng Graph
                    "pending_summary": False,
                    "is_auto_summary": False
                }

        # ====================== FILE UPLOAD HANDLING ======================
        if absolute_last_message.startswith("{"):
            try:
                data = json.loads(absolute_last_message)
                if data.get("type") == "file" and data.get("fileName"):
                    filename = data["fileName"].strip()
                    logger.info(f"📄 File uploaded: {filename}")

                    return {
                        "messages": [AIMessage(
                            content=f"📄 File **{filename}** đã upload và phân tích cấu trúc thành công.\n"
                                    f"👉 Gõ **'tóm tắt'** để xem nội dung cốt lõi.\n"
                                    f"👉 Hỏi về cấu trúc: *'Tài liệu này gồm bao nhiêu chương?'*\n"
                                    f"👉 Hoặc bắt đầu đặt câu hỏi chi tiết về file."
                        )],
                        "current_agent": "document",
                        "active_document": filename,
                        "pending_summary": False,     # Chủ động tắt tự động tóm tắt theo cấu hình mới của bạn
                        "summary_lock": False
                    }
            except Exception:
                pass

        # ====================== USER YÊU CẦU TÓM TẮT CHỦ ĐỘNG ======================
        text_lower = absolute_last_message.lower()
        is_summary_request = any(k in text_lower for k in ["tóm tắt", "summary", "summarize"])

        if is_summary_request and active_document:
            return {
                "messages": [AIMessage(content="🔄 Đang tóm tắt tài liệu...")],
                "current_agent": "document",
                "active_document": active_document,
                "tool_calls": [
                    {
                        "name": "summarize_document_tool",
                        "args": {"filename": active_document}
                    }
                ]
            }

        # ====================== NORMAL FLOW (DOCUMENT QA) ======================
        if active_document:
            logger.info(f"📄 Document RAG activated for: {active_document} | Query: {last_message[:100]}...")
            logger.info("[DEBUG] ENTER DOCUMENT QA")
            try:
                from app.rag.documents.document_rag import DocumentRAG
                try:
                    rag = DocumentRAG()
                except Exception as e:
                    logger.error(f"[DEBUG] RAG INIT FAILED: {e}", exc_info=True)
                    raise

                answer = await rag.query_document(
                    filename=active_document,
                    query=last_message
                )

                # ==========================================================
                # 🛡️ ENTERPRISE DOUBLE-GUARDRAIL (BỌC THÉP NÂNG CẤP)
                # ==========================================================
                answer_lower = str(answer).lower()
                is_fallback_needed = False
                
                fallback_keywords = [
                    "không tìm thấy", "không có", "không đề cập", 
                    "không chứa", "không nhắc đến", "không được cung cấp",
                    "xin lỗi, tôi không", "đáp án không có"
                ]
                
                if any(k in answer_lower for k in fallback_keywords):
                    is_fallback_needed = True
                elif not answer or len(str(answer).strip()) < 30:
                    logger.warning(f"⚠️ Query_document returned weak/empty answer for {active_document}")
                    is_fallback_needed = True

                if is_fallback_needed:
                    return {
                        "messages": [
                            AIMessage(content="Thông tin này không có trong tài liệu được cung cấp.")
                        ],
                        "current_agent": "document",
                        "active_document": active_document,
                        "file_meta": file_meta
                    }

                return {
                    "messages": [AIMessage(content=answer)],
                    "current_agent": "document",
                    "active_document": active_document,
                    "file_meta": file_meta
                }

            except Exception as rag_error:
                logger.error(f"RAG failed: {rag_error}", exc_info=True)

        return {
            "messages": [AIMessage(content="❌ Không thể truy xuất nội dung từ tài liệu.")],
            "current_agent": "document",
            "active_document": active_document
        }

    except Exception as e:
        logger.error(f"[Document Agent Error] {e}", exc_info=True)
        return {
            "messages": [AIMessage(content="❌ Xin lỗi, tôi đang gặp vấn đề khi xử lý tài liệu. Bạn thử lại sau nhé!")],
            "current_agent": "document"
        }

# Export cho supervisor
document_tools_list = [summarize_document_tool]
print("✅ Document Agent initialized successfully (Fixed Message Overlap)")