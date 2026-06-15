'use client';
import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, Paperclip, X, Loader2 } from 'lucide-react';
import { useChat } from '@/hooks/useChat';

interface ChatInputProps {
  onSend: (
    content: string,
    file?: File | null
  ) => Promise<void>;
  isLoading: boolean;
}

export default function ChatInput({ onSend, isLoading }: ChatInputProps) {
  const { input, setInput, cancelUpload, uploadingFile, uploadProgress, uploadFile } = useChat();
  
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [input]);

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();

    const trimmed = input.trim();

    if (isLoading || uploadingFile || isProcessing) return;

    // CASE 1: Có cả text + file -> Gửi chung 1 lượt qua onSend gốc để chạy mượt với Backend
    if (trimmed && selectedFile) {
      setIsProcessing(true);
      try {
        await onSend(trimmed, selectedFile);
        setInput('');
        resetFile();
      } catch (error) {
        console.error(error);
      } finally {
        setIsProcessing(false);
      }
      return;
    }

    // CASE 2: Chỉ có text thông thường
    if (trimmed) {
      onSend(trimmed);
      setInput('');
      if (textareaRef.current) textareaRef.current.style.height = 'auto';
      return;
    }

    // CASE 3: Chỉ có file -> AI tự động nhận diện tóm tắt
    if (selectedFile) {
      setIsProcessing(true);
      try {
        await onSend("", selectedFile);
        resetFile();
      } catch (error) {
        console.error(error);
      } finally {
        setIsProcessing(false);
      }
      return;
    }
  };

  const resetFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 15 * 1024 * 1024) {
      alert("File quá lớn! Vui lòng chọn file dưới 15MB.");
      return;
    }

    setSelectedFile(file);
  };

  const removeSelectedFile = () => {
    cancelUpload();
    resetFile();
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-4xl mx-auto px-4 pb-6">
      <div className="relative bg-background border border-border rounded-3xl focus-within:border-primary focus-within:ring-1 focus-within:ring-primary/30 transition-all shadow-sm">
        
        {/* File Preview + Progress */}
        {selectedFile && (
          <div className="mx-4 mt-3 space-y-3">
            <div className="flex items-center gap-2 bg-muted rounded-xl px-4 py-2.5 text-sm border border-border">
              <Paperclip className="w-4 h-4 text-primary flex-shrink-0" />
              <span className="truncate flex-1 text-foreground font-medium">{selectedFile.name}</span>
              <button
                type="button"
                onClick={removeSelectedFile}
                className="text-destructive hover:text-destructive/80 p-1 rounded-md hover:bg-muted transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Progress/Processing Loading State */}
            {(uploadingFile || isProcessing) && (
              <div className="px-4 pb-1">
                <div className="h-1.5 bg-muted rounded-full overflow-hidden relative">
                  <div className="h-1.5 bg-primary rounded-full absolute top-0 left-0 animate-pulse w-full" />
                </div>
                <p className="text-center text-xs text-muted-foreground mt-1.5 flex items-center justify-center gap-1.5">
                  <Loader2 className="w-3 h-3 animate-spin text-primary" /> Đang tải và xử lý tài liệu ngầm...
                </p>
              </div>
            )}
          </div>
        )}

        <Textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Nhập tin nhắn... (Enter để gửi, Shift+Enter xuống dòng)"
          className="min-h-[68px] max-h-[160px] resize-y py-5 px-6 text-[15.5px] 
                     bg-background border-0 focus-visible:ring-0 
                     text-foreground placeholder:text-muted-foreground rounded-3xl"
          disabled={isLoading || uploadingFile || isProcessing}
        />

        <div className="flex items-center justify-between px-5 pb-4">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            disabled={isLoading || uploadingFile || isProcessing}
            onClick={() => fileInputRef.current?.click()}
          >
            {(uploadingFile || isProcessing) ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Paperclip className="w-5 h-5" />
            )}
          </Button>

          <Button
            type="submit"
            size="icon"
            disabled={(!input.trim() && !selectedFile) || isLoading || uploadingFile || isProcessing}
            className="bg-primary hover:bg-primary/90 text-primary-foreground disabled:bg-muted disabled:text-muted-foreground"
          >
            <Send className="w-5 h-5" />
          </Button>
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        onChange={handleFileSelect}
        accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg,.webp"
      />

      <p className="text-center text-xs text-muted-foreground mt-3">
        Hỗ trợ: PDF, Word, Excel, Ảnh (tối đa 15MB)
      </p>
    </form>
  );
}