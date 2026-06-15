import logging
import json
from typing import Dict, Any
from datetime import datetime

from app.agents.supervisor import app as langgraph_app
from app.api.routers.history import get_db_connection, generate_smart_title

logger = logging.getLogger(__name__)


class ChatService:
    """
    Service layer cho Chat - Tích hợp Multi-Agent
    """

    @staticmethod
    async def process_message(message: str, thread_id: str | None = None,file_meta: dict | None = None) -> Dict[str, Any]:
        """Xử lý tin nhắn qua Multi-Agent Supervisor"""
        try:
            config = {"configurable": {"thread_id": thread_id}}

            input_state = {
                "messages": [{"role": "user", "content": message}],
                "active_document": file_meta.get("fileName") if file_meta else None,
                "pending_summary": False
            }

            result = langgraph_app.invoke(input_state, config=config)

            ai_response = result["messages"][-1].content
            current_agent = result.get("current_agent", "general")

            await ChatService._save_to_db(thread_id, message, ai_response,file_meta)

            return {
                "response": ai_response,
                "thread_id": thread_id,
                "current_agent": current_agent,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"ChatService Error: {e}", exc_info=True)
            return {
                "response": "❌ Xin lỗi, hệ thống đang gặp lỗi. Bạn thử lại sau nhé!",
                "status": "error"
            }

    # ================= CLEAN PREVIEW =================
    @staticmethod
    def _extract_preview(text: str, file_meta: dict | None = None) -> str:
        if file_meta and isinstance(file_meta, dict):
            if file_meta.get("type") == "file":
                return f"📎 {file_meta.get('fileName', 'file')}"

        return text[:80] if text else ""

    # ================= SAVE DB =================
    @staticmethod
    async def _save_to_db(thread_id: str, user_message: str, ai_message: str,file_meta: dict | None = None):
        """Lưu lịch sử chat vào PostgreSQL"""
        conn = None

        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                now = datetime.now()
                user_id = f"user_{now.timestamp():.0f}"
                ai_id = f"ai_{now.timestamp():.0f}"

                # ================= USER MESSAGE =================
                cur.execute("""
                    INSERT INTO chat_messages (message_id, role, content, thread_id, created_at, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    f"user_{now.timestamp():.0f}",
                    "user",
                    user_message,
                    thread_id,
                    now,
                    json.dumps(file_meta) if file_meta else None
                ))

                # ================= AI MESSAGE =================
                cur.execute("""
                    INSERT INTO chat_messages (message_id, role, content, thread_id, created_at, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    ai_id,
                    "assistant",
                    ai_message,
                    thread_id,
                    now,
                    None
                ))

                # ================= UPDATE THREAD PREVIEW (FIX CHÍNH) =================
                preview_text = ChatService._extract_preview(user_message, file_meta)

                cur.execute("""
                    UPDATE chat_threads
                    SET preview = %s,
                        updated_at = %s
                    WHERE thread_id = %s
                """, (
                    preview_text,
                    now,
                    thread_id
                ))

                conn.commit()

        except Exception as e:
            logger.error(f"Failed to save chat to DB: {e}", exc_info=True)

        finally:
            if conn:
                conn.close() 