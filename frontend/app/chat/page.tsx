'use client';

import React from 'react';
import ChatContainer from '@/components/chat/ChatContainer';
import ChatInput from '@/components/chat/ChatInput';
import DataPreviewPanel from '@/components/chat/DataPreviewPanel';
import AgentIndicator from '@/components/chat/AgentIndicator';
import ConfirmationDialog from '@/components/chat/ConfirmationDialog';
import PDFExportButton from '@/components/chat/PDFReportButton';
import { useChat } from '@/hooks/useChat';

export default function ChatPage() {
  const {
    messages,
    isLoading,
    sendMessage,
    currentAgent,
    pendingConfirmation,
    isPreviewOpen,
    setInput,   // ✅ THÊM DÒNG NÀY
  } = useChat();

  const suggestedPrompts = [
    "Tạo đơn hàng cho khách Gemini Furniture",
    "Báo cáo doanh số tháng này",
    "Chi tiết đơn hàng S00076",
    "Tóm tắt file hóa đơn gần nhất",
    "Kiểm tra tồn kho thấp",
  ];

  const handleSendMessage = async (
    content: string,
    file?: File | null
  ) => {
    await sendMessage(content, file);
  };

  // ✅ CHỈ FILL INPUT, KHÔNG SEND
  const handleSuggestedPrompt = (prompt: string) => {
    setInput(prompt);

    setTimeout(() => {
      document.querySelector('textarea')?.focus();
    }, 0);
  };

  return (
    <div className="flex h-full overflow-hidden bg-background">

      {/* CHAT AREA */}
      <div
        className={`flex flex-col border-r border-border min-w-0 h-full transition-all duration-300 ${
          isPreviewOpen ? "w-[calc(100%-420px)]" : "w-full"
        }`}
      >

        {/* HEADER */}
        <div className="flex items-center justify-between border-b border-border bg-background px-6 py-3 flex-shrink-0">
          <AgentIndicator currentAgent={currentAgent} />

          {messages.length >= 2 && (
            <PDFExportButton 
              messages={messages} 
              chatTitle="Cuộc trò chuyện Odoo AI" 
            />
          )}
        </div>

        {/* MAIN */}
        <div className="flex-1 flex flex-col min-h-0">

          {/* MESSAGES */}
          <div className="flex-1 min-h-0 flex flex-col">
            <ChatContainer messages={messages} isLoading={isLoading} />
          </div>

          {/* SUGGESTIONS */}
          {messages?.length === 0 && !isLoading && (
            <div className="px-6 pb-6 flex-shrink-0 border-t border-border bg-background">
              <p className="text-sm text-muted-foreground mb-4">
                Gợi ý nhanh:
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {suggestedPrompts.map((prompt, index) => (
                  <button
                    key={`suggest-${index}`}
                    onClick={() => handleSuggestedPrompt(prompt)}  // ✅ KHÔNG SEND
                    disabled={isLoading}
                    className="text-left border border-border hover:border-primary 
                               bg-background hover:bg-muted p-4 rounded-2xl text-sm 
                               text-foreground transition-all active:scale-[0.985] 
                               disabled:opacity-70 shadow-sm hover:shadow"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* INPUT */}
          <div className="border-t border-border bg-background p-4 flex-shrink-0">
            <ChatInput onSend={handleSendMessage} isLoading={isLoading} />
          </div>

        </div>
      </div>

      {/* PREVIEW PANEL */}
      {isPreviewOpen && (
        <div className="w-[420px] flex-shrink-0 border-l border-border bg-background overflow-hidden flex flex-col">
          <DataPreviewPanel />
          {pendingConfirmation && <ConfirmationDialog />}
        </div>
      )}
    </div>
  );
}