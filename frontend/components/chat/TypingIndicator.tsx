'use client';

import React, { memo } from 'react';

function TypingIndicator() {
  return (
    <div className="flex gap-4">
      <div className="w-9 h-9 rounded-2xl bg-muted flex-shrink-0 flex items-center justify-center">
        <span className="text-xl">🤖</span>
      </div>
      
      <div className="bg-muted border border-border rounded-3xl rounded-bl-none px-5 py-4 flex items-center">
        <div className="flex gap-1.5">
          <div className="w-2.5 h-2.5 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2.5 h-2.5 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2.5 h-2.5 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
        <span className="ml-4 text-sm text-muted-foreground">Odoo AI đang suy nghĩ...</span>
      </div>
    </div>
  );
}

export default memo(TypingIndicator);