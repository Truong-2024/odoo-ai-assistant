import os
import logging
from dotenv import load_dotenv
from langgraph.checkpoint.base import BaseCheckpointSaver

load_dotenv()
logger = logging.getLogger(__name__)

# 🛠️ LỚP WRAPPER LAZY ASYNC VỚI CONNECTION POOL TỰ ĐỘNG KHÔI PHỤC KẾT NỐI
class LazyAsyncPostgresSaver(BaseCheckpointSaver):
    def __init__(self, conn_string: str):
        super().__init__()
        self.conn_string = conn_string
        self._saver = None
        self._pool = None  # Thêm biến quản lý Connection Pool

    async def _get_saver(self):
        # Khởi tạo Pool và Saver nếu chưa có hoặc Pool đã bị đóng
        if self._saver is None:
            from psycopg_pool import AsyncConnectionPool
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            
            print("🔄 [LAZY CHECKPOINT] Đang cấu hình Async Connection Pool dẻo dai...")
            
            # Khởi tạo bể kết nối tự duy trì, tự kết nối lại nếu mất mạng
            self._pool = AsyncConnectionPool(
                conninfo=self.conn_string,
                max_size=5,            # Số lượng kết nối tối đa cho phép
                min_size=1,            # Luôn duy trì ít nhất 1 kết nối "sống" để né timeout
                kwargs={"autocommit": True}
            )
            
            # Ép thư viện thế hệ mới của LangGraph sử dụng Pool để tự quản lý vòng đời kết nối
            self._saver = AsyncPostgresSaver(self._pool)
            
            # Tự động đồng bộ cấu trúc bảng hệ thống ban đầu
            await self._saver.setup()
            print("🎉 [LAZY CHECKPOINT] Kích hoạt cấu trúc Connection Pool thành công!")
            
        return self._saver

    # 1. Các hàm Async thực tế phục vụ luồng ainvoke()
    async def aget_tuple(self, config):
        try:
            saver = await self._get_saver()
            return await saver.get_tuple(config)  # Sử dụng thông qua pool an toàn
        except Exception as e:
            logger.error(f"⚠️ [DB RETRY] Lỗi đọc checkpoint: {e}. Đang reset pool...")
            self._saver = None  # Đánh dấu sập để luồng sau tự tạo lại pool mới
            raise e

    async def aput(self, config, checkpoint, metadata, new_versions):
        try:
            saver = await self._get_saver()
            return await saver.put(config, checkpoint, metadata, new_versions)
        except Exception as e:
            logger.error(f"⚠️ [DB RETRY] Lỗi ghi checkpoint: {e}. Đang reset pool...")
            self._saver = None
            raise e

    async def aput_writes(self, config, writes, task_id):
        try:
            saver = await self._get_saver()
            return await saver.put_writes(config, writes, task_id)
        except Exception as e:
            logger.error(f"⚠️ [DB RETRY] Lỗi ghi đè checkpoint: {e}. Đang reset pool...")
            self._saver = None
            raise e

    async def alist(self, config, *, filter=None, before=None, limit=None):
        try:
            saver = await self._get_saver()
            async for item in saver.list(config, filter=filter, before=before, limit=limit):
                yield item
        except Exception as e:
            logger.error(f"⚠️ [DB RETRY] Lỗi lấy danh sách checkpoint: {e}. Đang reset pool...")
            self._saver = None
            raise e

    # 2. Các hàm đồng bộ bắt buộc của BaseCheckpointSaver (Giữ nguyên)
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
        # Làm sạch Connection String chuẩn cho thư viện psycopg
        conn_string = conn_string.replace("+psycopg_async", "").replace("+psycopg", "")
        print(f"🔄 [CHECKPOINT] Đăng ký Lazy Async Context cho: {conn_string[:80]}...")

        # Trả về đối tượng Lazy Wrapper thế hệ mới có Pool bảo vệ
        memory = LazyAsyncPostgresSaver(conn_string)
        
        logger.info("✅ LazyAsyncPostgresSaver registered successfully with Pool mechanism")
        return memory

    except Exception as e:
        logger.error(f"❌ [CHECKPOINT] Postgres connection failed: {e}", exc_info=True)
        print(f"❌ [CHECKPOINT] ERROR: {e}")
        print("→ Fallback to MemorySaver (lịch sử chat chỉ lưu tạm thời)")
        
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()