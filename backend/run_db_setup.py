import psycopg
import os
import sys

# Lấy connection string từ biến môi trường trên Render
conn_string = os.getenv("POSTGRES_CHAT_URI")

if not conn_string:
    print("❌ Lỗi: Không tìm thấy biến môi trường POSTGRES_CHAT_URI")
    sys.exit(1)

# Lệnh SQL tạo bảng
sql_commands = """
CREATE TABLE IF NOT EXISTS chat_threads (
    thread_id TEXT PRIMARY KEY,
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    message_id TEXT PRIMARY KEY,
    thread_id TEXT REFERENCES chat_threads(thread_id),
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

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
"""

try:
    with psycopg.connect(conn_string) as conn:
        with conn.cursor() as cur:
            cur.execute(sql_commands)
            conn.commit()
            print("✅ Đã tạo bảng thành công trong Database!")
except Exception as e:
    print(f"❌ Lỗi khi tạo bảng: {e}")
    sys.exit(1)