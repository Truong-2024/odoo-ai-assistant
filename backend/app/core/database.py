import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Lấy chuỗi kết nối từ biến môi trường
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://odoo:odoo@localhost:5432/odoo_ai_memory"
)

# 2. Xử lý chuỗi kết nối để phù hợp với driver asyncpg của Python
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Bẻ đôi chuỗi để loại bỏ các tham số dạng ?sslmode=require của Neon gây lỗi cho asyncpg
if "?" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("?")[0]

# 3. Khởi tạo Engine kết nối Async kèm cấu hình SSL chuẩn cho asyncpg
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Tự động kiểm tra kết nối sống/chết trước khi truy vấn
    pool_size=5,         # Giới hạn số lượng kết nối tối đa cho gói Render Free
    max_overflow=10,
    connect_args={"ssl": True} # Ép Neon dùng SSL bảo mật theo đúng chuẩn của asyncpg
)

# 4. Khởi tạo Factory để tạo các phiên làm việc (Session)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 5. Tạo lớp Base cơ sở
Base = declarative_base()

# Dependency dùng cho các API Endpoints cần gọi Database
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()