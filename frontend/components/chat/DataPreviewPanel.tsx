'use client';
import React, { useState, useEffect, useRef } from 'react';
import { useChat } from '@/hooks/useChat';
import { X } from 'lucide-react';

export default function DataPreviewPanel() {
  const {
    messages, // Lấy danh sách tin nhắn để truy vết tên file gốc
    activeDocument,
    setIsPreviewOpen,
    setActiveDocument
  } = useChat();

  const [loading, setLoading] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Reset loading khi đổi document
  useEffect(() => {
    if (activeDocument) {
      setLoading(true);
    }
  }, [activeDocument]);

  const handleClose = () => {
    setIsPreviewOpen(false);
    // Delay reset để animation mượt
    setTimeout(() => {
      setActiveDocument(null);
      setLoading(false);
    }, 250);
  };

  // ✅ SỬA LỖI ĐƯỜNG DẪN: Tự động tách lấy Base URL từ biến môi trường Render, nếu không có mới dùng localhost
  const backendBaseUrl = process.env.NEXT_PUBLIC_API_URL?.replace('/api', '') || 'http://localhost:8000';
  const iframeSrc = activeDocument
    ? `${backendBaseUrl}${activeDocument}`
    : 'about:blank';

  // ✅ SỬA LỖI TYPESCRIPT: Thêm dấu ? trước .split để bảo vệ an toàn phòng trường hợp activeDocument là null
  const matchedMessage = messages?.find(m => m.fileUrl === activeDocument);
  const originalFileName = matchedMessage?.fileName || activeDocument?.split('/').pop() || 'Tài liệu';

  return (
    <div className="h-full flex flex-col bg-background overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-border flex items-center justify-between flex-shrink-0">
        <div>
          <h2 className="font-semibold text-lg text-foreground">📊 Data Preview</h2>
          <p className="text-xs text-muted-foreground mt-1">Tài liệu đã upload</p>
        </div>
        
        <button
          onClick={handleClose}
          className="p-2 hover:bg-muted rounded-lg transition-colors text-muted-foreground hover:text-foreground"
          title="Đóng preview"
        >
          <X size={20} />
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-auto p-5 relative">
        <div className="h-full flex flex-col">
          {activeDocument && (
            <div className="mb-4 flex items-center justify-between flex-shrink-0">
              <div>
                {/* Hiển thị originalFileName thay vì cắt chuỗi UUID từ URL */}
                <p className="font-medium text-foreground truncate max-w-[280px]">
                  {originalFileName}
                </p>
                <p className="text-xs text-emerald-500">● Đang xem</p>
              </div>
            </div>
          )}

          {/* Iframe Container - Luôn mounted */}
          <div className="flex-1 border border-border rounded-2xl overflow-hidden bg-background relative min-h-[600px]">
            <iframe
              ref={iframeRef}
              src={iframeSrc}
              className="w-full h-full min-h-[700px] will-change-transform"
              title={activeDocument || "Preview"}
              onLoad={() => setLoading(false)}
              style={{ 
                contain: 'strict',
                contentVisibility: activeDocument ? 'visible' : 'hidden' 
              }}
            />

            {/* Loading Overlay */}
            {loading && activeDocument && (
              <div className="absolute inset-0 flex items-center justify-center bg-background/90 backdrop-blur-sm z-10 transition-opacity">
                <div className="flex flex-col items-center gap-3 text-muted-foreground">
                  <div className="w-6 h-6 border-2 border-current border-t-transparent rounded-full animate-spin" />
                  <p className="text-sm">Đang tải tài liệu...</p>
                </div>
              </div>
            )}

            {/* Empty State */}
            {!activeDocument && (
              <div className="h-full flex flex-col items-center justify-center text-center text-muted-foreground py-20">
                <p className="text-5xl mb-6 opacity-50">📂</p>
                <p className="text-lg font-medium text-foreground mb-2">Chưa có tài liệu nào được chọn</p>
                <p className="text-sm max-w-[280px]">Click vào file trong cuộc trò chuyện để xem trước nội dung</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-border text-xs text-muted-foreground text-center flex-shrink-0">
        Multi-Agent System • Connected to Odoo
      </div>
    </div>
  );
}