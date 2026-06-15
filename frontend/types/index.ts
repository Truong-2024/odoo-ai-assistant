// frontend/types/index.ts
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;

  agent?: string;

  fileName?: string;
  fileUrl?: string;
  isFileCard?: boolean;
}

export interface Thread {
  id: string;
  title: string;
  preview?: string;
  updatedAt: string | Date;
  message_count?: number;
  time?: string;
}

export interface PendingConfirmation {
  confirmation_id: string;
  preview: {
    customer: { id: number; name: string };
    order_lines: Array<{
      product_name: string;
      quantity: number;
      price: number;
    }>;
    total_amount: number;
    notes?: string;
  };
}

export interface UploadResponse {
  status: string;
  message: string;
  filename: string;
  doc_id: string;
  file_type: string;
  fileUrl?: string;
  fileName?: string;
  isFileCard?: boolean;
}