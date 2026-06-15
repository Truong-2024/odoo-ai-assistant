'use client';

import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { MessageSquare, Plus, Trash2, Search } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useChat } from '@/hooks/useChat';
import { chatAPI } from '@/lib/api';

export default function Sidebar() {
  const { 
    threads, 
    activeChatId, 
    setActiveChatId, 
    loadChatMessages, 
    createNewChat,
    loadAllThreads 
  } = useChat();

  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadAllThreads();
  }, [loadAllThreads]);

  const filteredThreads = threads.filter(chat =>
    chat.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    chat.preview?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleThreadClick = (threadId: string) => {
    setActiveChatId(threadId);
  };

  const handleDeleteThread = async (threadId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Bạn có chắc chắn muốn xóa cuộc trò chuyện này không?')) return;

    try {
      await chatAPI.deleteThread(threadId);
      await loadAllThreads();

      if (activeChatId === threadId) {
        const remaining = threads.filter(t => t.id !== threadId);
        if (remaining.length > 0) {
          const next = remaining[0];
          setActiveChatId(next.id);
        } else {
          createNewChat();
        }
      }
    } catch (error) {
      console.error("Xóa thread thất bại:", error);
      alert("Không thể xóa cuộc trò chuyện.");
    }
  };

  return (
    <div className="flex h-full flex-col bg-card">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <Button 
          onClick={createNewChat} 
          variant="outline"
          className="w-full justify-start gap-3 h-11 rounded-2xl border-border hover:bg-accent"
        >
          <Plus className="w-5 h-5" />
          Cuộc trò chuyện mới
        </Button>
      </div>

      {/* Search */}
      <div className="px-4 pt-4">
        <div className="relative">
          <Search className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
          <input
            suppressHydrationWarning   // ← Đã thêm để fix hydration error
            type="text"
            placeholder="Tìm cuộc trò chuyện..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-background border border-border pl-10 py-3 rounded-2xl text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/30"
          />
        </div>
      </div>

      {/* Threads List */}
      <div className="flex-1 overflow-auto px-4 py-4">
        <div className="text-xs uppercase tracking-widest text-muted-foreground mb-3 px-2">
          TẤT CẢ CUỘC TRÒ CHUYỆN ({threads.length})
        </div>
        
        <div className="space-y-1">
          {filteredThreads.length > 0 ? (
            filteredThreads.map((chat) => (
              <div
                key={chat.id}
                onClick={() => handleThreadClick(chat.id)}
                className={cn(
                  "group flex items-start gap-3 rounded-2xl px-4 py-3 cursor-pointer transition-all hover:bg-accent",
                  activeChatId === chat.id && "bg-accent border-l-2 border-primary"
                )}
              >
                <MessageSquare className="w-5 h-5 text-muted-foreground mt-0.5 flex-shrink-0" />

                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm text-foreground line-clamp-1">{chat.title}</p>
                  {chat.preview && (
                    <p className="text-xs text-muted-foreground line-clamp-2 mt-1">{chat.preview}</p>
                  )}
                  <p className="text-[10px] text-muted-foreground mt-1.5">
                    {chat.updatedAt ? new Date(chat.updatedAt).toLocaleDateString('vi-VN') : ''}
                  </p>
                </div>

                <button
                  onClick={(e) => handleDeleteThread(chat.id, e)}
                  className="p-1.5 hover:bg-destructive/10 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
                >
                  <Trash2 className="w-4 h-4 text-muted-foreground hover:text-destructive" />
                </button>
              </div>
            ))
          ) : (
            <div className="text-center text-muted-foreground py-12 text-sm">
              Chưa có cuộc trò chuyện nào
            </div>
          )}
        </div>
      </div>

      <div className="p-4 border-t border-border text-xs text-muted-foreground text-center">
        Odoo AI Assistant
      </div>
    </div>
  );
}