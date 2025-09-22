// supabase/types.ts
// TypeScript types generated from the database schema

export interface Database {
  public: {
    Tables: {
      user_profiles: {
        Row: {
          id: string
          email: string
          display_name: string | null
          avatar_url: string | null
          subscription_tier: 'free' | 'pro' | 'enterprise'
          api_usage_count: number
          created_at: string
          updated_at: string
        }
        Insert: {
          id: string
          email: string
          display_name?: string | null
          avatar_url?: string | null
          subscription_tier?: 'free' | 'pro' | 'enterprise'
          api_usage_count?: number
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          email?: string
          display_name?: string | null
          avatar_url?: string | null
          subscription_tier?: 'free' | 'pro' | 'enterprise'
          api_usage_count?: number
          created_at?: string
          updated_at?: string
        }
      }
      chat_sessions: {
        Row: {
          id: string
          user_id: string
          title: string
          status: 'active' | 'archived' | 'deleted'
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          title?: string
          status?: 'active' | 'archived' | 'deleted'
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          title?: string
          status?: 'active' | 'archived' | 'deleted'
          created_at?: string
          updated_at?: string
        }
      }
      documents: {
        Row: {
          id: string
          user_id: string
          filename: string
          original_filename: string
          file_path: string
          file_size: number
          mime_type: string
          status: 'processing' | 'completed' | 'failed' | 'deleted'
          processing_time: number | null
          page_count: number | null
          total_chunks: number | null
          total_characters: number | null
          total_words: number | null
          preview_text: string | null
          error_message: string | null
          created_at: string
          processed_at: string | null
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          filename: string
          original_filename: string
          file_path: string
          file_size: number
          mime_type?: string
          status?: 'processing' | 'completed' | 'failed' | 'deleted'
          processing_time?: number | null
          page_count?: number | null
          total_chunks?: number | null
          total_characters?: number | null
          total_words?: number | null
          preview_text?: string | null
          error_message?: string | null
          created_at?: string
          processed_at?: string | null
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          filename?: string
          original_filename?: string
          file_path?: string
          file_size?: number
          mime_type?: string
          status?: 'processing' | 'completed' | 'failed' | 'deleted'
          processing_time?: number | null
          page_count?: number | null
          total_chunks?: number | null
          total_characters?: number | null
          total_words?: number | null
          preview_text?: string | null
          error_message?: string | null
          created_at?: string
          processed_at?: string | null
          updated_at?: string
        }
      }
      document_chunks: {
        Row: {
          id: string
          document_id: string
          chunk_index: number
          content: string
          embedding: number[] | null
          metadata: Record<string, any>
          page_number: number | null
          chunk_size: number | null
          start_index: number | null
          created_at: string
        }
        Insert: {
          id?: string
          document_id: string
          chunk_index: number
          content: string
          embedding?: number[] | null
          metadata?: Record<string, any>
          page_number?: number | null
          chunk_size?: number | null
          start_index?: number | null
          created_at?: string
        }
        Update: {
          id?: string
          document_id?: string
          chunk_index?: number
          content?: string
          embedding?: number[] | null
          metadata?: Record<string, any>
          page_number?: number | null
          chunk_size?: number | null
          start_index?: number | null
          created_at?: string
        }
      }
      chat_messages: {
        Row: {
          id: string
          session_id: string
          user_id: string
          role: 'user' | 'assistant' | 'system'
          content: string
          metadata: Record<string, any>
          tokens_used: number | null
          processing_time: number | null
          context_chunks: string[]
          created_at: string
        }
        Insert: {
          id?: string
          session_id: string
          user_id: string
          role: 'user' | 'assistant' | 'system'
          content: string
          metadata?: Record<string, any>
          tokens_used?: number | null
          processing_time?: number | null
          context_chunks?: string[]
          created_at?: string
        }
        Update: {
          id?: string
          session_id?: string
          user_id?: string
          role?: 'user' | 'assistant' | 'system'
          content?: string
          metadata?: Record<string, any>
          tokens_used?: number | null
          processing_time?: number | null
          context_chunks?: string[]
          created_at?: string
        }
      }
      api_usage: {
        Row: {
          id: string
          user_id: string
          endpoint: string
          method: string
          status_code: number | null
          response_time: number | null
          tokens_used: number
          cost: number
          metadata: Record<string, any>
          created_at: string
        }
        Insert: {
          id?: string
          user_id: string
          endpoint: string
          method: string
          status_code?: number | null
          response_time?: number | null
          tokens_used?: number
          cost?: number
          metadata?: Record<string, any>
          created_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          endpoint?: string
          method?: string
          status_code?: number | null
          response_time?: number | null
          tokens_used?: number
          cost?: number
          metadata?: Record<string, any>
          created_at?: string
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      search_document_chunks: {
        Args: {
          query_embedding: number[]
          document_ids?: string[] | null
          similarity_threshold?: number
          match_count?: number
        }
        Returns: {
          id: string
          document_id: string
          content: string
          metadata: Record<string, any>
          similarity: number
        }[]
      }
      get_chat_session_with_messages: {
        Args: {
          session_id: string
          message_limit?: number
        }
        Returns: {
          session: Record<string, any>
          messages: Record<string, any>
        }[]
      }
    }
    Enums: {
      [_ in never]: never
    }
  }
}