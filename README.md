# 🚀 Odoo AI Assistant

**Trợ lý AI thông minh tích hợp sâu với Odoo 17** — Hỗ trợ bán hàng, báo cáo, RAG và tạo đơn hàng an toàn.

---

## ✨ Tính năng nổi bật

- **Agent LangGraph** với Supervisor + Human-in-the-Loop
- **Advanced RAG** (HyDE + Cross-Encoder Reranker + PGVector)
- Tạo đơn hàng an toàn (Preview → Xác nhận → Tạo thật)
- Báo cáo doanh số, tồn kho thấp, chi tiết đơn hàng
- Tìm kiếm kiến thức nội bộ thông minh
- Memory dài hạn với PostgreSQL
- Streaming UI + Authentication + PDF Report

---

## 🏗 Architecture

Xem **[ARCHITECTURE.md](./ARCHITECTURE.md)**

![Architecture Diagram](docs/architecture.png)

---

## 📋 Tech Stack

**Backend:** Python 3.10 + FastAPI + LangGraph + Groq (Llama-3.1)  
**AI:** Advanced RAG + Tool Calling  
**Database:** Odoo 17 + PostgreSQL + PGVector  
**Frontend:** Next.js 14 + TypeScript + Tailwind + shadcn/ui  

---

## 🚀 Cài đặt & Chạy

### 1. Khởi động Odoo
```bash
docker-compose up -d