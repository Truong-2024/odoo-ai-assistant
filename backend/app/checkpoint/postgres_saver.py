import os
import logging
from dotenv import load_dotenv
# 🛠️ ĐÃ SỬA: Sửa thành BaseCheckpointSaver cho đúng chuẩn thư viện LangGraph
from langgraph.checkpoint.base import BaseCheckpointSaver

load_dotenv()

logger = logging.getLogger(__name__)


# 🛠️ LỚP WRAPPER LAZY ASYNC CHUẨN CẤU TRÚC
# Kế thừa BaseCheckpointSaver giúp đồ thị vượt qua vòng kiểm tra lúc compile().
class LazyAsyncPostgresSaver(BaseCheckpointSaver):
    def __init__(self, conn_string: str):
        super().__init__()
        self.conn_string = conn_string
        self._saver = None

    async def _get_saver(self):
        # Kết nối thực tế chỉ được kích hoạt khi tin nhắn đầu tiên đi vào hệ thống
        if self._saver is None:
            import psycopg
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            
            print("🔄 [LAZY CHECKPOINT] Kích hoạt kết nối Async Postgres thực tế...")
            conn = await psycopg.AsyncConnection.connect(self.conn_string, autocommit=True)
            self._saver = AsyncPostgresSaver(conn)
            await self._saver.setup()  # Tự động tạo bảng hệ thống nếu chưa có
            print("🎉 [LAZY CHECKPOINT] Kết nối Async Postgres thành công!")
        return self._saver

    # 1. Định nghĩa các hàm Async thực tế để phục vụ cho luồng ainvoke() của bạn
    async def aget_tuple(self, config):
        saver = await self._get_saver()
        return await saver.aget_tuple(config)

    async def aput(self, config, checkpoint, metadata, new_versions):
        saver = await self._get_saver()
        return await saver.aput(config, checkpoint, metadata, new_versions)

    async def aput_writes(self, config, writes, task_id):
        saver = await self._get_saver()
        return await saver.aput_writes(config, writes, task_id)

    async def alist(self, config, *, filter=None, before=None, limit=None):
        saver = await self._get_saver()
        async for item in saver.alist(config, filter=filter, before=before, limit=limit):
            yield item

    # 2. Khai báo các hàm đồng bộ bắt buộc của BaseCheckpointSaver để tránh lỗi TypeError lúc khởi tạo
    def get_tuple(self, config):
        raise NotImplementedError("Hệ thống đang chạy luồng Async. Hãy sử dụng aget_tuple.")

    def put(self, config, checkpoint, metadata, new_versions):
        raise NotImplementedError("Hệ thống đang chạy luồng Async. Hãy sử dụng aput.")

    def put_writes(self, config, writes, task_id):
        raise NotImplementedError("Hệ thống đang chạy luồng Async. Hãy sử dụng aput_writes.")

    def list(self, config, *, filter=None, before=None, limit=None):
        raise NotImplementedError("Hệ thống đang chạy luồng Async. Hãy sử dụng alist.")


def get_postgres_saver():
    conn_string = os.getenv("POSTGRES_CHECKPOINT_URI")
    print(f"🔍 [CHECKPOINT] Loaded URI: {conn_string}")
    
    if not conn_string:
        print("❌ [CHECKPOINT] Không tìm thấy POSTGRES_CHECKPOINT_URI")
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()

    try:
        # Làm sạch Connection String
        conn_string = conn_string.replace("+psycopg_async", "").replace("+psycopg", "")
        print(f"🔄 [CHECKPOINT] Đăng ký Lazy Async Context cho: {conn_string[:80]}...")

        # Trả về đối tượng Lazy Wrapper (Chạy hoàn toàn mượt mà lúc khởi động)
        memory = LazyAsyncPostgresSaver(conn_string)
        
        logger.info("✅ LazyAsyncPostgresSaver registered successfully")
        return memory

    except Exception as e:
        logger.error(f"❌ [CHECKPOINT] Postgres connection failed: {e}", exc_info=True)
        print(f"❌ [CHECKPOINT] ERROR: {e}")
        print("→ Fallback to MemorySaver (lịch sử chat chỉ lưu tạm thời)")
        
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()