import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Lấy chuỗi kết nối từ biến môi trường (Render sẽ tự cấp khi deploy)
# Nếu chạy ở Local (Docker), nó sẽ tự động dùng URL mặc định ở dưới.
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://odoo:odoo@localhost:5432/odoo_ai_memory"
)

# 2. Render thường cấp link dạng postgresql://, cần convert sang dạng asyncpg cho SQLAlchemy Async
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# 3. Khởi tạo Engine kết nối Async
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Tự động kiểm tra kết nối sống/chết trước khi truy vấn
    pool_size=5,         # Giới hạn số lượng kết nối tối đa cho gói Render Free
    max_overflow=10
)

# 4. Khởi tạo Factory để tạo các phiên làm việc (Session)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 5. Tạo lớp Base cơ sở (Cái mà file main.py đang import)
Base = declarative_base()

# Dependency dùng cho các API Endpoints cần gọi Database
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()