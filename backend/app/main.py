# backend/app/main.py
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
from datetime import datetime
from app.core.database import Base, engine
from app.core.config import UPLOADS_DIR
from fastapi.staticfiles import StaticFiles
# Load environment variables
load_dotenv()

# ====================== LOGGING SETUP ======================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ====================== IMPORT ROUTERS ======================
from app.api.routers.auth import router as auth_router
from app.api.routers.chat import router as chat_router
from app.api.routers.history import router as history_router
from app.api.routers.odoo import router as odoo_router
from app.api.routers.tools import router as tools_router
from app.api.routers.upload import router as upload_router

# ====================== FASTAPI APP ======================
app = FastAPI(
    title="Odoo AI Assistant",
    description="""🚀 Odoo AI Assistant v2.0 - Multi-Agent System
    Hỗ trợ: Business Agent, Document Agent, Vision Agent, General Agent""",
    version="2.0.0",
    contact={
        "name": "Odoo AI Assistant",
        "email": "support@odoo-ai.com",
    },
    license_info={
        "name": "MIT License",
    },
    docs_url="/docs",
    redoc_url="/redoc",
)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

os.makedirs(UPLOADS_DIR, exist_ok=True)

print(f"✅ Uploads directory mounted at: {UPLOADS_DIR}")  # Debug

app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
# ====================== CORS MIDDLEWARE ======================
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://odoo-ai-assistant-u84u.vercel.app", # Link Vercel chính chủ hiện tại của bạn
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Chỉ đích danh người nhà, giải quyết triệt để xung đột credentials
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================== INCLUDE ROUTERS ======================
app.include_router(auth_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(history_router, prefix="/api")
app.include_router(odoo_router, prefix="/api")
app.include_router(tools_router, prefix="/api")
app.include_router(upload_router, prefix="/api")

# ====================== ROOT & HEALTH CHECK ======================
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "🚀 Odoo AI Assistant v2.0 - Multi-Agent System is running!",
        "version": "2.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs",
        "features": [
            "Business Agent (Odoo)",
            "Document Agent (RAG)",
            "Vision Agent (OCR + Image QA)",
            "General Agent (Chat đời sống)",
            "Multi-Agent Routing"
        ]
    }


@app.get("/health", tags=["Root"])
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "service": "Odoo AI Assistant",
        "timestamp": datetime.now().isoformat(),
        "agents": ["business", "document", "vision", "general"]
    }


@app.get("/ping", tags=["Root"])
async def ping():
    return {"ping": "pong", "time": datetime.now().isoformat()}


# ====================== STARTUP EVENT ======================
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Odoo AI Assistant v2.0 starting up...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("📍 Database tables checked and created")
    logger.info("📍 Multi-Agent System initialized")
    logger.info("📍 Docs available at: http://localhost:8000/docs")
    
    # TODO: Có thể thêm auto-ingest company data ở đây nếu cần
    # from app.rag.company.company_ingest import CompanyDataIngestor
    # ingestor = CompanyDataIngestor()
    # ingestor.ingest(clear_old=False)


# ====================== SHUTDOWN EVENT ======================
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("⛔ Odoo AI Assistant is shutting down...")


# ====================== RUN DIRECTLY ======================
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
        workers=1
    )
