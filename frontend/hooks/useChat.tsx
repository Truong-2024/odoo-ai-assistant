'use client';

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
  useEffect,
  useRef,
  useMemo
} from 'react';
import { Message } from '@/types';
import { chatAPI } from '@/lib/api';

interface ChatContextType {
  messages: Message[];
  threads: any[];
  activeChatId: string | null;
  currentAgent: string;
  pendingConfirmation: any | null;
  isLoading: boolean;
  isStreaming: boolean;
  error: string | null;
  activeDocument: string | null;
  uploadingFile: boolean;
  uploadProgress: number;
  isPreviewOpen: boolean;

  sendMessage: (content: string, file?: File | null) => Promise<void>;
  uploadFile: (file: File, onProgress?: (progress: number) => void) => Promise<any>;
  cancelUpload: () => void;
  clearError: () => void;
  loadChatMessages: (chatId: string) => Promise<void>;
  loadAllThreads: () => Promise<void>;
  createNewChat: () => void;
  setActiveChatId: (id: string) => void;
  setActiveDocument: (filename: string | null) => void;
  setIsPreviewOpen: (open: boolean) => void;
  input: string;
  setInput: (v: string) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [threads, setThreads] = useState<any[]>([]);
  const [input, setInput] = useState('');
  const [activeChatId, setActiveChatIdState] = useState<string | null>(
    () => crypto.randomUUID()
  );
  
  const [currentAgent, setCurrentAgent] = useState<string>("general");
  const [pendingConfirmation, setPendingConfirmation] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeDocument, setActiveDocumentState] = useState<string | null>(null);
  const [isPreviewOpen, setIsPreviewOpenState] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);

  const abortRef = useRef<AbortController | null>(null);
  const loadedChatRef = useRef<string | null>(null);

  // ================= CLEAN PREVIEW =================
  const cleanPreview = (preview: any) => {
    if (!preview) return '';

    try {
      const parsed =
        typeof preview === 'string'
          ? JSON.parse(preview)
          : preview;

      if (parsed?.type === 'file') {
        return `📎 ${parsed.fileName}`;
      }

      return typeof preview === 'string' ? preview : '';
    } catch {
      return typeof preview === 'string' ? preview : '';
    }
  };

  // ================= THREADS =================
  const loadAllThreads = useCallback(async () => {
    try {
      const data = await chatAPI.getThreads();

      const cleaned = (data || []).map((t: any) => ({
        ...t,
        preview: cleanPreview(t.preview),
      }));

      setThreads(cleaned);
    } catch (err) {
      console.error("Load threads error:", err);
    }
  }, []);

  // ================= LOAD CHAT =================
  const loadChatMessages = useCallback(async (chatId: string) => {
    if (!chatId) return;

    setIsLoading(true);
    setError(null);

    try {
      const data = await chatAPI.getThreadMessages(chatId);

      const formatted = data.map((m: any) => ({
        id: m.id,
        role: m.role as 'user' | 'assistant',
        content: m.content,
        timestamp: new Date(m.timestamp),
        fileName: m.file_name,
        fileUrl: m.file_url,
        isFileCard: m.is_file_card,
        agent: m.agent || 'general',
      }));

      setMessages(formatted);
    } catch (err) {
      setError("Không thể tải lịch sử chat.");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // ================= AUTO LOAD CHAT =================
  useEffect(() => {
    if (!activeChatId) return;
    if (loadedChatRef.current === activeChatId) return;

    loadedChatRef.current = activeChatId;
    loadChatMessages(activeChatId);
  }, [activeChatId, loadChatMessages]);

  // ================= NEW CHAT =================
  const createNewChat = useCallback(() => {
    const newId = crypto.randomUUID();

    setActiveChatIdState(newId);
    setMessages([]);

    setPendingConfirmation(null);
    setCurrentAgent("general");
    setActiveDocumentState(null);
    setIsPreviewOpenState(false);
    setUploadingFile(false);
    setUploadProgress(0);

    loadedChatRef.current = null;

    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }

    loadAllThreads();
  }, [loadAllThreads]);

  const setActiveChatId = useCallback((id: string) => {
    setActiveChatIdState(id);
  }, []);

  const setActiveDocument = useCallback((filename: string | null) => {
    setActiveDocumentState(filename);
  }, []);

  const setIsPreviewOpen = useCallback((open: boolean) => {
    setIsPreviewOpenState(open);
  }, []);

  const clearError = useCallback(() => setError(null), []);

  const cancelUpload = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    setUploadingFile(false);
    setUploadProgress(0);
    setIsLoading(false);
    setError(null);
  }, []);

  // ================= SEND MESSAGE (ĐÃ SỬA) =================
  const sendMessage = useCallback(async (content: string, file?: File | null) => {
    if (!activeChatId) return;

    setIsLoading(true);
    setError(null);

    // Tạo AbortController mới
    const controller = new AbortController();
    abortRef.current = controller;

    let userContent = content.trim();
    const isAutoSummarize = !userContent && !!file;

    if (isAutoSummarize) {
      userContent = "[AUTO_SUMMARIZE]";
    }

    const userMsg: Message = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: isAutoSummarize ? "" : userContent,
      timestamp: new Date(),
      fileName: file?.name,
      isFileCard: !!file && !userContent,
    };

    setMessages(prev => [...prev, userMsg]);

    try {
      let finalContent = userContent;

      const result = await chatAPI.sendMessage(finalContent, activeChatId, file, {
        signal: controller.signal,  
      });

      const aiMsg: Message = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: result.response || (isAutoSummarize ? "Đang tóm tắt tài liệu..." : "Tôi đã nhận tin nhắn của bạn."),
        timestamp: new Date(),
        agent: result.current_agent || 'document',
      };

      setMessages(prev => [...prev, aiMsg]);
      setCurrentAgent(result.current_agent || 'general');

      await loadChatMessages(activeChatId);
      loadAllThreads();

      if (result.pending_confirmation) {
        setPendingConfirmation(result.pending_confirmation);
      }

    } catch (err: any) {
      if (err.name === 'AbortError' || err.code === 'ERR_CANCELED') {
        console.log('Upload / Request đã bị hủy bởi người dùng');
        return;
      }
      setError(err?.response?.data?.detail || err.message || "Lỗi kết nối server");
    } finally {
      setIsLoading(false);
      abortRef.current = null;
    }
  }, [activeChatId, loadChatMessages, loadAllThreads]);

  // ================= UPLOAD FILE (Giữ nguyên) =================
  const uploadFile = useCallback(async (file: File, onProgress?: (progress: number) => void) => {
    if (!file || !activeChatId) return null;

    if (abortRef.current) abortRef.current.abort();

    const controller = new AbortController();
    abortRef.current = controller;

    setIsLoading(true);
    setUploadingFile(true);
    setUploadProgress(0);
    setError(null);

    try {
      const result = await chatAPI.uploadFile(file, {
        signal: controller.signal,
        onProgress: (progress: number) => {
          setUploadProgress(progress);
          if (onProgress) onProgress(progress);
        }
      });

      const fileCardMsg: Message = {
        id: `file_${Date.now()}`,
        role: 'user',
        content: '',
        timestamp: new Date(),
        agent: 'document',
        fileName: file.name,
        fileUrl: result.file_url || result.url,
        isFileCard: true
      };

      setMessages(prev => [...prev, fileCardMsg]);
      
      await loadChatMessages(activeChatId);
      loadAllThreads();

      return { success: true, ...result };

    } catch (err: any) {
      if (err.name === 'AbortError') return null;
      setError(err.message || "Upload file thất bại");
      return { success: false };
    } finally {
      setIsLoading(false);
      setUploadingFile(false);
      setTimeout(() => setUploadProgress(0), 1000);
      abortRef.current = null;
    }
  }, [activeChatId, loadChatMessages, loadAllThreads]);

  // ================= PROVIDER =================
  const contextValue = useMemo(() => ({
    messages,
    threads,
    activeChatId,
    currentAgent,
    pendingConfirmation,
    isLoading,
    isStreaming,
    error,
    activeDocument,
    uploadingFile,
    uploadProgress,
    isPreviewOpen,
    
    input,
    setInput,

    sendMessage,
    uploadFile,
    cancelUpload,
    clearError,
    loadChatMessages,
    loadAllThreads,
    createNewChat,
    setActiveChatId,
    setActiveDocument,
    setIsPreviewOpen,
  }), [
    input,
    messages,
    threads,
    activeChatId,
    currentAgent,
    pendingConfirmation,
    isLoading,
    isStreaming,
    error,
    activeDocument,
    uploadingFile,
    uploadProgress,
    isPreviewOpen,
    sendMessage,
    uploadFile,
    cancelUpload,
    clearError,
    loadChatMessages,
    loadAllThreads,
    createNewChat,
    setActiveChatId,
    setActiveDocument,
    setIsPreviewOpen,
  ]);

  useEffect(() => {
    loadAllThreads();
  }, [loadAllThreads]);

  useEffect(() => {
    return () => {
      if (abortRef.current) abortRef.current.abort();
    };
  }, []);

  return (
    <ChatContext.Provider value={contextValue}>
      {children}
    </ChatContext.Provider>
  );
}

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) throw new Error('useChat must be used within ChatProvider');
  return context;
};