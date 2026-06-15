from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
import psycopg
import os
from dotenv import load_dotenv
import logging
from app.core.security import get_current_user
import re
from pathlib import Path
from app.core.config import settings

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["Chat History"])


# ================= MODELS =================
class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    timestamp: datetime | None = None
    thread_id: str


class UpdateTitleRequest(BaseModel):
    title: str


# ================= DB CONNECTION =================
def get_db_connection():
    conn_string = os.getenv(
        "POSTGRES_CHAT_URI",
        settings.POSTGRES_CHECKPOINT_URI
    )

    if not conn_string:
        raise HTTPException(status_code=500, detail="Database not configured")

    conn_string = conn_string.replace("+psycopg_async", "").replace("+psycopg", "")
    return psycopg.connect(conn_string, autocommit=True)


# ================= SMART TITLE =================
def generate_smart_title(message: str) -> str:
    if not message:
        return "Cuộc trò chuyện mới"

    text = message.strip()

    try:
        import json
        data = json.loads(text)
        if isinstance(data, dict) and data.get("type") == "file":
            filename = data.get("fileName", "file")
            return Path(filename).stem[:80]
    except:
        pass

    file_match = re.search(r"([\w\-\s]+\.pdf|\.docx|\.txt)", text, re.IGNORECASE)
    if file_match:
        return Path(file_match.group(1)).stem[:80]

    return text.replace("\n", " ")[:65]


# ================= THREAD LIST =================
@router.get("/threads")
async def get_all_threads(current_user: str = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:

            # ❗ FIX: KHÔNG dùng timestamp nếu DB không có
            cur.execute("""
                SELECT 
                    t.thread_id,
                    t.title,
                    COUNT(m.message_id) as message_count
                FROM chat_threads t
                LEFT JOIN chat_messages m 
                    ON t.thread_id = m.thread_id
                GROUP BY t.thread_id, t.title
                ORDER BY MAX(m.created_at) DESC NULLS LAST
            """)

            rows = cur.fetchall()

            return [
                {
                    "id": row[0],
                    "title": row[1] or "Cuộc trò chuyện mới",
                    "time": "",
                    "preview": "Xem chi tiết...",
                    "message_count": row[2]
                }
                for row in rows
            ]

    finally:
        conn.close()

# ================= GET MESSAGES =================
@router.get("/thread/{thread_id}")
async def get_thread_messages(
    thread_id: str,
    current_user: str = Depends(get_current_user)
):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:

            # 🛠️ CHUYÊN NGHIỆP FIX: Áp dụng cơ chế bọc lót kép ORDER BY 
            # Nếu thời gian trùng nhau (Mili-giây), ưu tiên sắp xếp theo thứ tự ID hoặc đưa 'user' lên trước AI
            cur.execute("""
                SELECT 
                    message_id, 
                    role, 
                    content,
                    created_at,
                    metadata
                FROM chat_messages
                WHERE thread_id = %s
                ORDER BY created_at ASC, CASE WHEN role = 'user' THEN 0 ELSE 1 END ASC, message_id ASC
            """, (thread_id,))

            rows = cur.fetchall()

            result = []
            for row in rows:
                metadata = row[4] or {}

                if isinstance(metadata, str):
                    import json
                    metadata = json.loads(metadata)

                result.append({
                    "id": row[0],
                    "role": row[1],
                    "content": row[2],
                    "timestamp": row[3],
                    "thread_id": thread_id,

                    "file_name": metadata.get("file_name"),
                    "file_url": metadata.get("file_url"),
                    "is_file_card": metadata.get("is_file_card", False),
                })

            return result

    except psycopg.errors.UndefinedColumn as e:
        # Fallback nếu cột chưa tồn tại (trường hợp migration chưa chạy)
        logger.warning("Cột file_name chưa tồn tại, dùng fallback")
        with conn.cursor() as cur:
            # 🛠️ CHUYÊN NGHIỆP FIX: Áp dụng cơ chế bọc lót tương tự cho khối Fallback
            cur.execute("""
                SELECT message_id, role, content, created_at
                FROM chat_messages
                WHERE thread_id = %s
                ORDER BY created_at ASC, CASE WHEN role = 'user' THEN 0 ELSE 1 END ASC, message_id ASC
            """, (thread_id,))
            
            rows = cur.fetchall()
            result = []
            for row in rows:
                result.append({
                    "id": row[0],
                    "role": row[1],
                    "content": row[2],
                    "timestamp": row[3],
                    "thread_id": thread_id,
                    "file_name": None,
                    "file_url": None,
                    "is_file_card": False,
                })
            return result

    finally:
        conn.close()

# ================= UPDATE TITLE =================
@router.post("/thread/{thread_id}/title")
async def update_thread_title(
    thread_id: str,
    request: UpdateTitleRequest,
    current_user: str = Depends(get_current_user)
):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:

            # ❗ FIX SQL (bạn đang bị duplicate WHERE)
            cur.execute("""
                UPDATE chat_threads
                SET title = %s
                WHERE thread_id = %s
            """, (request.title.strip()[:100], thread_id))

        return {"status": "success", "message": "Đã cập nhật tiêu đề"}

    finally:
        conn.close()


# ================= DELETE THREAD =================
@router.delete("/thread/{thread_id}")
async def delete_thread(
    thread_id: str,
    current_user: str = Depends(get_current_user)
):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:

            # delete messages
            cur.execute("""
                DELETE FROM chat_messages
                WHERE thread_id = %s
            """, (thread_id,))

            # delete thread
            cur.execute("""
                DELETE FROM chat_threads
                WHERE thread_id = %s
            """, (thread_id,))

        return {"status": "success", "message": "Đã xóa cuộc trò chuyện"}

    finally:
        conn.close()