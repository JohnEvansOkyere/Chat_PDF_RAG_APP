// frontend/src/types/index.ts
export interface User {
  id: string;
  email: string;
  display_name?: string;
  avatar_url?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface Document {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  status: 'processing' | 'completed' | 'failed' | 'deleted';
  processing_time?: number;
  page_count?: number;
  total_chunks?: number;
  preview_text?: string;
  error_message?: string;
  created_at: string;
  processed_at?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  status: 'active' | 'archived' | 'deleted';
  created_at: string;
  updated_at: string;
  message_count?: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  tokens_used?: number;
  processing_time?: number;
}

export interface ChatRequest {
  message: string;
  document_id?: string;
  stream?: boolean;
}

export interface ChatResponse {
  id: string;
  message: string;
  context_chunks?: string[];
  tokens_used?: number;
  processing_time: number;
  timestamp: string;
}