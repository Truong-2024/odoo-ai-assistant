'use client';

import React, { useMemo, useCallback } from 'react';
import { Message } from '@/types';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, Bot, FileText } from 'lucide-react';
import { useChat } from '@/hooks/useChat';

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  const { setActiveDocument, setIsPreviewOpen } = useChat();

  // 🔥 KIỂM TRA XEM TIN NHẮN CÓ PHẢI CHỈ LÀ TOKEN HỆ THỐNG HAY KHÔNG
  const isAutoSummarizeToken = message.content === '[AUTO_SUMMARIZE]';

  // Nếu là tin nhắn thông thường (không phải file card) mà chỉ chứa token hệ thống -> Ẩn toàn bộ
  if (!message.isFileCard && isAutoSummarizeToken) {
    return null;
  }

  // ================= FILE CLICK =================
  const handleFileClick = useCallback(() => {
    if (!message.fileName) return;

    // mở preview panel
    setActiveDocument(message.fileUrl || null);
    setIsPreviewOpen(true);
  }, [message.fileName, setActiveDocument, setIsPreviewOpen]);

  // ================= MARKDOWN =================
  const markdownContent = useMemo(
    () => (
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {message.content}
      </ReactMarkdown>
    ),
    [message.content]
  );

  // ================= FILE CARD =================
  if (message.isFileCard) {
    return (
      <div className="flex flex-col items-end gap-2 justify-end group w-full">
        {/* Khung hiển thị File đính kèm (LUÔN ĐƯỢC GIỮ LẠI) */}
        <div className="flex gap-4 max-w-[80%] min-w-0">
          <div
            onClick={handleFileClick}
            className="cursor-pointer bg-card border border-border hover:border-primary 
                       rounded-3xl px-6 py-4 flex items-center gap-3 transition-all 
                       hover:bg-muted/80 w-full overflow-hidden"
          >
            <FileText className="w-5 h-5 text-primary flex-shrink-0" />

            <div className="min-w-0 flex-1">
              <p className="font-medium text-foreground truncate">
                {message.fileName}
              </p>
              <p className="text-xs text-muted-foreground truncate">
                Nhấp để xem trong Data Preview →
              </p>
            </div>
          </div>
        </div>

        {/* 🛠️ SỬA TẠI ĐÂY: Chỉ hiển thị câu hỏi đi kèm nếu có text VÀ text đó KHÔNG PHẢI là token hệ thống */}
        {message.content && !isAutoSummarizeToken && (
          <div className="flex gap-4 max-w-[80%] min-w-0 flex-row-reverse items-start">
            {/* Avatar của User */}
            <div className="w-9 h-9 rounded-2xl flex items-center justify-center mt-1 flex-shrink-0 bg-accent">
              <User className="w-5 h-5 text-foreground" />
            </div>

            {/* Bong bóng text chứa nội dung câu hỏi */}
            <div className="rounded-3xl px-5 py-4 text-[15.2px] max-w-full break-words min-w-0 bg-accent text-accent-foreground rounded-br-none">
              <div className="markdown-content prose prose-invert max-w-none break-words">
                {markdownContent}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ================= NORMAL MESSAGE =================
  return (
    <div className={cn('flex items-start group', isUser ? 'justify-end' : 'justify-start')}>
      <div className={cn('flex gap-4 max-w-[80%] min-w-0', isUser && 'flex-row-reverse')}>
        
        {/* Avatar */}
        <div
          className={cn(
            'w-9 h-9 rounded-2xl flex items-center justify-center mt-1 flex-shrink-0',
            isUser ? 'bg-accent' : 'bg-muted'
          )}
        >
          {isUser ? (
            <User className="w-5 h-5 text-foreground" />
          ) : (
            <Bot className="w-5 h-5 text-foreground" />
          )}
        </div>

        {/* Message */}
        <div
          className={cn(
            'rounded-3xl px-5 py-4 text-[15.2px] max-w-full break-words min-w-0',
            isUser
              ? 'bg-accent text-accent-foreground rounded-br-none'
              : 'bg-card text-foreground rounded-bl-none'
          )}
        >
          <div className="markdown-content prose prose-invert max-w-none break-words">
            {markdownContent}
          </div>
        </div>
      </div>
    </div>
  );
}

export default React.memo(MessageBubble);