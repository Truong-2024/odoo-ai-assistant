-- =============================================
-- DATABASE SETUP cho Odoo AI Assistant (Đã đồng bộ với Code)
-- =============================================

-- 1. Bảng lưu trữ cuộc hội thoại (Khớp với code Python)
CREATE TABLE IF NOT EXISTS chat_threads (
    thread_id TEXT PRIMARY KEY,
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Bảng lưu trữ tin nhắn (Khớp với code Python)
CREATE TABLE IF NOT EXISTS chat_messages (
    message_id TEXT PRIMARY KEY,
    thread_id TEXT REFERENCES chat_threads(thread_id),
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- 3. Bảng LangGraph Checkpoints (Duy trì để Agent có trí nhớ)
CREATE TABLE IF NOT EXISTS checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    checkpoint JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

-- Tạo Index để truy vấn lịch sử nhanh hơn
CREATE INDEX IF NOT EXISTS idx_messages_thread_id ON chat_messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON chat_messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_threads_updated_at ON chat_threads(updated_at DESC);

-- =============================================
-- Ghi chú: 
-- Sau khi chạy lệnh này, bảng chat_threads và chat_messages đã sẵn sàng.
-- Code Python của bạn sẽ không còn lỗi khi truy vấn nữa.
-- =============================================