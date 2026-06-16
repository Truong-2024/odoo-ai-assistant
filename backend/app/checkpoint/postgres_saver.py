import os
import logging
import asyncio
from dotenv import load_dotenv
from langgraph.checkpoint.base import BaseCheckpointSaver

load_dotenv()
logger = logging.getLogger(__name__)

# 🛠️ LỚP WRAPPER LAZY ASYNC CHUẨN ĐỊNH DẠNG ASYNC INTERFACE
class LazyAsyncPostgresSaver(BaseCheckpointSaver):
    def __init__(self, conn_string: str):
        super().__init__()
        self.conn_string = conn_string
        self._saver = None
        self._pool = None  

    async def _get_saver(self):
        if self._saver is None:
            from psycopg_pool import AsyncConnectionPool
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            
            print("🔄 [LAZY CHECKPOINT] Đang cấu hình Async Connection Pool dẻo dai...")
            
            # Khởi tạo pool nhưng tắt cơ chế tự mở ngầm trong constructor để né Warning
            self._pool = AsyncConnectionPool(
                conninfo=self.conn_string,
                max_size=5,            
                min_size=1,            
                open=False, # Không tự động mở đồng bộ ở đây
                kwargs={"autocommit": True}
            )
            
            # Kích hoạt mở Pool một cách bất đồng bộ (Async) theo đúng chuẩn khuyến nghị
            await self._pool.open()
            
            # Đút Pool vào cho AsyncPostgresSaver quản lý
            self._saver = AsyncPostgresSaver(self._pool)
            
            # Tự động tạo bảng hệ thống một cách bất đồng bộ
            await self._saver.setup()
            print("🎉 [LAZY CHECKPOINT] Kích hoạt cấu trúc Connection Pool thành công!")
            
        return self._saver

    # 1. Định nghĩa chính xác các interface ASYNC (Thêm chữ 'a' vào các hàm của saver)
    async def aget_tuple(self, config):
        try:
            saver = await self._get_saver()
            # 🔥 ĐÃ SỬA: Chuyển từ get_tuple sang aget_tuple (Sửa lỗi Synchronous call)
            return await saver.aget_tuple(config)  
        except Exception as e:
            logger.error(f"⚠️ [DB RETRY] Lỗi đọc checkpoint (aget_tuple): {e}. Đang reset pool...")
            await self._close_pool()
            raise e

    async def aput(self, config, checkpoint, metadata, new_versions):
        try:
            saver = await self._get_saver()
            # 🔥 ĐÃ SỬA: Chuyển từ put sang aput
            return await saver.aput(config, checkpoint, metadata, new_versions)
        except Exception as e:
            logger.error(f"⚠️ [DB RETRY] Lỗi ghi checkpoint (aput): {e}. Đang reset pool...")
            await self._close_pool()
            raise e

    async def aput_writes(self, config, writes, task_id):
        try:
            saver = await self._get_saver()
            # 🔥 ĐÃ SỬA: Chuyển từ put_writes sang aput_writes
            return await saver.aput_writes(config, writes, task_id)
        except Exception as e:
            logger.error(f"⚠️ [DB RETRY] Lỗi ghi đè checkpoint (aput_writes): {e}. Đang reset pool...")
            await self._close_pool()
            raise e

    async def alist(self, config, *, filter=None, before=None, limit=None):
        try:
            saver = await self._get_saver()
            # 🔥 ĐÃ SỬA: Chuyển từ list sang alist
            async for item in saver.alist(config, filter=filter, before=before, limit=limit):
                yield item
        except Exception as e:
            logger.error(f"⚠️ [DB RETRY] Lỗi lấy danh sách checkpoint (alist): {e}. Đang reset pool...")
            await self._close_pool()
            raise e

    async def _close_pool(self):
        """Hàm dọn dẹp pool an toàn khi xảy ra lỗi kết nối"""
        try:
            if self._pool:
                await self._pool.close()
        except:
            pass
        self._pool = None
        self._saver = None

    # 2. Các hàm đồng bộ bắt buộc của BaseCheckpointSaver (Giữ nguyên phương án chặn)
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
        conn_string = conn_string.replace("+psycopg_async", "").replace("+psycopg", "")
        print(f"🔄 [CHECKPOINT] Đăng ký Lazy Async Context cho: {conn_string[:80]}...")

        memory = LazyAsyncPostgresSaver(conn_string)
        logger.info("✅ LazyAsyncPostgresSaver registered successfully with Async Pool Interface")
        return memory

    except Exception as e:
        logger.error(f"❌ [CHECKPOINT] Postgres connection failed: {e}", exc_info=True)
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()