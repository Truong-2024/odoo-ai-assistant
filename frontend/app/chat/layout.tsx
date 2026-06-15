'use client';
import { ReactNode } from 'react';
import Header from '@/components/common/Header';
import Sidebar from '@/components/chat/Sidebar';
import { ChatProvider } from '@/hooks/useChat';

export default function ChatLayout({ children }: { children: ReactNode }) {
  return (
    <ChatProvider>
      <div className="flex h-screen overflow-hidden bg-background">   {/* ← Đổi min-h-screen → h-screen */}
        {/* Sidebar */}
        <div className="w-80 border-r border-border flex-shrink-0">
          <Sidebar />
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden h-full">
          <Header />
          <div className="flex-1 flex flex-col min-h-0">
            {children}
          </div>
        </div>
      </div>
    </ChatProvider>
  );
}