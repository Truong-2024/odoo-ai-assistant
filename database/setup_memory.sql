-- =============================================
-- DATABASE SETUP cho Odoo AI Assistant
-- =============================================

-- Tạo database (chạy thủ công nếu chưa có)
-- CREATE DATABASE odoo_ai_memory;

-- Kết nối vào database
\c odoo_ai_memory

-- =============================================
-- 1. Bảng LangGraph Checkpoints (đã có)
-- =============================================
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

CREATE INDEX IF NOT EXISTS idx_checkpoints_thread_id ON checkpoints(thread_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_created_at ON checkpoints(created_at DESC);

-- =============================================
-- 2. Bảng Thread Metadata (đã có)
-- =============================================
CREATE TABLE IF NOT EXISTS thread_metadata (
    thread_id TEXT PRIMARY KEY,
    user_id TEXT,
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- 3. Bảng Chat Messages (MỚI - Quan trọng cho History)
-- =============================================
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    thread_id TEXT NOT NULL,
    message_id TEXT NOT NULL UNIQUE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Index tối ưu cho History Chat
CREATE INDEX IF NOT EXISTS idx_chat_messages_thread_id ON chat_messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp ON chat_messages(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_thread_time ON chat_messages(thread_id, timestamp);

-- =============================================
-- COMMENT
-- =============================================
COMMENT ON TABLE checkpoints IS 'LangGraph persistent memory cho Agent';
COMMENT ON TABLE thread_metadata IS 'Thông tin bổ sung của từng cuộc trò chuyện';
COMMENT ON TABLE chat_messages IS 'Lưu lịch sử tin nhắn để hiển thị trên Frontend';

-- =============================================
-- SAMPLE DATA (tùy chọn)
-- =============================================
-- INSERT INTO thread_metadata (thread_id, title, user_id) 
-- VALUES ('default', 'Cuộc trò chuyện đầu tiên', 'admin@odoo.ai');