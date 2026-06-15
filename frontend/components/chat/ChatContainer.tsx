'use client';

import React, { useEffect, useRef, memo } from 'react';
import { Message } from '@/types';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import { useChat } from '@/hooks/useChat';

interface ChatContainerProps {
  messages: Message[];
  isLoading: boolean;
  isStreaming?: boolean;
}

function ChatContainer({
  messages,
  isLoading,
  isStreaming = false,
}: ChatContainerProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const { error, clearError } = useChat();

  // Auto scroll thông minh
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;

    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 150;

    if (isNearBottom || messages.length === 0) {
      el.scrollTo({
        top: el.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [messages, error, isLoading]);

  return (
    <div
      ref={scrollRef}
      className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-6 flex flex-col gap-8 bg-background"
    >
      {messages.map((message) => (
        <MessageBubble 
          key={message.id} 
          message={message} 
        />
      ))}

      {(isLoading || isStreaming) && <TypingIndicator />}

      {error && (
        <div className="mx-auto max-w-md bg-red-950/50 border border-red-800 rounded-2xl p-6 text-center">
          <p className="text-red-400">{error}</p>
          <button
            onClick={clearError}
            className="mt-4 text-sm underline hover:text-red-300"
          >
            Đóng
          </button>
        </div>
      )}
    </div>
  );
}

export default memo(ChatContainer);