// frontend/lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  timeout: 300000, // 5 phút
});

// Auto attach token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      if (typeof window !== 'undefined') window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

// ====================== CHAT API ======================
export const chatAPI = {
  sendMessage: async (
    message: string, 
    thread_id: string, 
    file?: File | null,
    options?: { 
      signal?: AbortSignal; 
      onProgress?: (progress: number) => void 
    }
  ) => {
    const formData = new FormData();

    formData.append('message', message || "");

    if (thread_id) {
      formData.append('thread_id', thread_id);
    }

    if (file) {
      formData.append('file', file);
    }

    const config: any = {
      signal: options?.signal,
    };

    // Hỗ trợ progress khi có file
    if (options?.onProgress && file) {
      config.onUploadProgress = (progressEvent: any) => {
        if (progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          options.onProgress(percentCompleted);
        }
      };
    }

    const res = await api.post('/chat/message', formData, config);

    return res.data;
  },

  getThreads: async () => {
    const res = await api.get('/history/threads');
    return res.data;
  },

  getThreadMessages: async (threadId: string) => {
    const res = await api.get(`/history/thread/${threadId}`);
    return res.data;
  },

  deleteThread: async (threadId: string) => {
    const res = await api.delete(`/history/thread/${threadId}`);
    return res.data;
  },

  // === UPLOAD FILE (Giữ nguyên, đã tốt) ===
  uploadFile: async (file: File, options?: { 
    signal?: AbortSignal; 
    onProgress?: (progress: number) => void 
  }) => {
    const formData = new FormData();
    formData.append('file', file);

    const config: any = {
      signal: options?.signal,
    };

    if (options?.onProgress) {
      config.onUploadProgress = (progressEvent: any) => {
        if (progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          options.onProgress(percentCompleted);
        }
      };
    }

    const res = await api.post('/upload/', formData, config);

    return res.data;
  },
}; 