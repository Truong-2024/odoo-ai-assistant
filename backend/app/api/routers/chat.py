from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request 
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from datetime import datetime
import logging
import uuid
import os
import asyncio
from typing import Optional
from app.agents.supervisor import app as langgraph_app
from app.core.security import get_current_user
from app.api.routers.history import get_db_connection, generate_smart_title
from app.rag.documents.document_rag import DocumentRAG
import json
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract
import io
from app.core.config import UPLOADS_DIR

# Import bộ tiện ích Query Rewriter động và thư viện chuẩn hóa chữ tiếng Việt
import unicodedata
# Đảm bảo bạn gọi đúng tên hàm đã cập nhật ở file query_rewriter (hoặc đổi tên hàm tùy ý bạn)
from app.agents.utils.query_rewriter import rewrite_contextual_query_v2 as rewrite_contextual_query
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])

UPLOAD_DIR = UPLOADS_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)


def extract_file_text(file_path: str, file_ext: str) -> str:
    try:
        if file_ext == ".pdf":
            reader = PdfReader(file_path)
            return "\n".join([page.extract_text() or "" for page in reader.pages])
        if file_ext in [".png", ".jpg", ".jpeg", ".webp"]:
            img = Image.open(file_path)
            return pytesseract.image_to_string(img)
    except Exception as e:
        logger.warning(f"File extract error: {e}")
    return ""


@router.post("/message")
async def send_message(
    request: Request,                                 
    message: str = Form(""),
    thread_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: str = Depends(get_current_user)
):
    conn = None
    file_path = None
    saved_filename = None

    try:
        thread_id = thread_id or str(uuid.uuid4())
        now = datetime.utcnow()
        config = {"configurable": {"thread_id": thread_id}}

        # Lấy active_document cũ
        old_active_document = None
        try:
            snapshot = await langgraph_app.aget_state(config)
            if snapshot and snapshot.values:
                old_active_document = snapshot.values.get("active_document")
        except Exception as e:
            logger.warning(f"Get state failed: {e}")

        final_message = message.strip()
        file_name = None
        file_url = None
        is_file_card = False
        file_meta = None

        # ================= FILE PROCESSING =================
        if file:
            if await request.is_disconnected():
                logger.warning("🛑 Client disconnected before saving file")
                return {"status": "cancelled", "detail": "Yêu cầu đã bị hủy."}

            ext = os.path.splitext(file.filename)[1].lower()
            saved_filename = f"{uuid.uuid4()}{ext}"
            file_path = os.path.join(UPLOAD_DIR, saved_filename)
            
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            file_name = file.filename
            file_url = f"/uploads/{saved_filename}"
            is_file_card = True

            if await request.is_disconnected():
                logger.warning(f"🛑 Client cancelled after file saved: {file_name}")
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                return {"status": "cancelled", "detail": "Đã hủy sau khi lưu file."}

            # ================= INDEX DOCUMENT =================
            if await request.is_disconnected():
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                return {"status": "cancelled"}

            doc_rag = DocumentRAG()
            try:
                await doc_rag.index_document(
                    file_path=file_path,
                    filename=file_name,
                    request=request  
                )
            except Exception as e:
                logger.error(f"Index document error: {e}")

            file_meta = {
                "type": "file",
                "fileName": file_name,
                "filePath": str(file_path),
                "fileUrl": file_url,
                "doc_id": saved_filename  
            }

        if not final_message and not file:
            raise HTTPException(status_code=400, detail="Vui lòng nhập tin nhắn hoặc upload file")

        # ================= DECIDE MODE =================
        is_auto_summary = (file is not None) and (not final_message)
        user_content = f"[AUTO_SUMMARIZE] File: {file_name}" if is_auto_summary else final_message or f"Phân tích file: {file_name}"
        active_document = file_name or old_active_document

        # ================= DYNAMIC CONTEXT EXTRACTION FOR QUERY REWRITER =================
        active_files_in_thread = []
        chat_history_from_db = []

        if file_name:
            active_files_in_thread.append(file_name)
        if old_active_document and old_active_document not in active_files_in_thread:
            active_files_in_thread.append(old_active_document)

        try:
            context_conn = get_db_connection()
            with context_conn.cursor() as context_cur:
                context_cur.execute("""
                    SELECT metadata FROM chat_messages 
                    WHERE thread_id = %s AND metadata IS NOT NULL
                """, (thread_id,))
                meta_rows = context_cur.fetchall()
                for row in meta_rows:
                    meta_data = row[0]
                    if isinstance(meta_data, str):
                        try:
                            meta_data = json.loads(meta_data)
                        except:
                            continue
                    if meta_data and "file_name" in meta_data and meta_data["file_name"]:
                        f_name = meta_data["file_name"]
                        if f_name not in active_files_in_thread:
                            active_files_in_thread.append(f_name)

                context_cur.execute("""
                    SELECT role, content FROM chat_messages 
                    WHERE thread_id = %s 
                    ORDER BY created_at ASC LIMIT 6
                """, (thread_id,))
                history_rows = context_cur.fetchall()
                for role, content in history_rows:
                    chat_history_from_db.append({"role": role, "content": content})

        except Exception as context_err:
            logger.warning(f"⚠️ [Query Rewriter Context Sync Error]: {context_err}")
        finally:
            if 'context_conn' in locals() and context_conn:
                context_conn.close()

        if not active_document and active_files_in_thread:
            active_document = active_files_in_thread[0]
            logger.info(f"🔄 [THREAD HISTORY RECOVERY] Đã khôi phục hoạt động tài liệu từ DB: {active_document}")

        # 🔥 THAY ĐỔI QUAN TRỌNG: Tích hợp đón nhận cấu trúc dữ liệu mới từ Rewriter Động
        if user_content and not is_auto_summary:
            rewriter_output = await rewrite_contextual_query(
                current_query=user_content,
                chat_history=chat_history_from_db,
                active_files=active_files_in_thread
            )
            # Khai thác dữ liệu từ Dict trả về
            if isinstance(rewriter_output, dict):
                user_content = rewriter_output.get("clean_query", user_content)
                # ChatGPT style: Ép luồng gán file context hoạt động về đúng file được AI dự đoán!
                predicted_file = rewriter_output.get("predicted_file")
                if predicted_file and predicted_file in active_files_in_thread:
                    active_document = predicted_file
                    logger.info(f"🎯 [DYNAMIC ROUTING] Đã chuyển đổi ngữ cảnh tài liệu thông minh sang: {active_document}")
            else:
                # Phương án dự phòng (fallback) nếu rewriter trả về chuỗi thuần túy
                user_content = rewriter_output

        if active_document:
            active_document = unicodedata.normalize('NFC', active_document)

        # ================= 🔥 TIỀN XỬ LÝ ĐỊNH TUYẾN LOGIC THẦN TỐC =================
        query_lower = user_content.lower() if user_content else ""
        
        summary_keywords = ["tóm tắt", "tổng quan", "khái quát nội dung"]
        is_explicit_summary_query = any(kw in query_lower for kw in summary_keywords)
        
        structure_keywords = ["bao nhiêu chương", "bằng nào chương", "có mấy chương", "mục lục", "cấu trúc"]
        is_structure_query = any(kw in query_lower for kw in structure_keywords)

        if is_explicit_summary_query:
            logger.info("🎯 [GLOBAL QUERY DETECTED] Phát hiện yêu cầu tóm tắt tài liệu rõ ràng. Kích hoạt force_summary.")
            is_auto_summary = True
        elif is_structure_query:
            logger.info("🎯 [GLOBAL QUERY DETECTED] Phát hiện câu hỏi cấu trúc tổng thể tài liệu (Số chương/Mục lục). Ép buộc chuyển luồng sang Q&A Query.")
            is_auto_summary = False 

        if await request.is_disconnected():
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            return {"status": "cancelled", "detail": "Hủy trước khi chạy Agent"}

        # ================= LANGGRAPH WITH MONITOR =================
        # Biến active_document ở đây đã được cập nhật động và chính xác theo file cũ/mới người dùng hỏi
        langgraph_task = asyncio.create_task(
            langgraph_app.ainvoke(
                {
                    "messages": [HumanMessage(content=user_content)],
                    "active_document": active_document,  
                    "file_meta": file_meta,
                    "pending_summary": is_auto_summary,
                    "force_summary": is_auto_summary,   
                    "is_auto_summary": is_auto_summary
                },
                config=config
            )
        )

        async def monitor_disconnect():
            try:
                while not langgraph_task.done():
                    if await request.is_disconnected():
                        logger.warning(f"🛑 Monitor detected disconnect - cancelling LangGraph task")
                        langgraph_task.cancel()
                        break
                    await asyncio.sleep(0.25)   
            except asyncio.CancelledError:
                pass

        monitor_task = asyncio.create_task(monitor_disconnect())

        try:
            result = await langgraph_task
        except asyncio.CancelledError:
            logger.warning(f"🛑 LangGraph task cancelled successfully for file: {file_name}")
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as clean_err:
                    logger.error(f"Clean file error: {clean_err}")
            return {"status": "cancelled", "detail": "Đã hủy theo yêu cầu người dùng."}
        finally:
            if not monitor_task.done():
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass

        # ================= SAVE TO DB =================
        if await request.is_disconnected():
            logger.warning("AI finished but client disconnected")
            return {"status": "cancelled"}

        conn = get_db_connection()
        with conn.cursor() as cur:
            user_msg_id = f"user_{uuid.uuid4().hex}"
            ai_msg_id = f"ai_{uuid.uuid4().hex}"

            title = generate_smart_title(file_name or final_message or "Conversation")

            cur.execute("""
                INSERT INTO chat_threads (thread_id, title, created_at, updated_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT(thread_id) DO UPDATE SET updated_at = EXCLUDED.updated_at
            """, (thread_id, title, now, now))

            cur.execute("""
                INSERT INTO chat_messages (thread_id, message_id, role, content, created_at, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                thread_id, user_msg_id, "user",
                final_message if final_message else f"📎 {file_name}",
                now,
                json.dumps({"file_name": file_name, "file_url": file_url, "is_file_card": is_file_card}) if file_name else None
            ))

            cur.execute("""
                INSERT INTO chat_messages (thread_id, message_id, role, content, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (thread_id, ai_msg_id, "assistant", result["messages"][-1].content, now))

        conn.commit()

        return {
            "user_message_id": user_msg_id,
            "ai_message_id": ai_msg_id,
            "response": result["messages"][-1].content,
            "thread_id": thread_id,
            "current_agent": result.get("current_agent", "document"),
            "status": "success"
        }

    except Exception as e:
        logger.error(f"[Chat Error] {e}", exc_info=True)
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            conn.close()