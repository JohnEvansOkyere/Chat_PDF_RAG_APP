// lib/supabase/client.ts
// Supabase client configuration for frontend and backend

import { createClient } from '@supabase/supabase-js'
import type { Database } from './types'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient<Database>(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
})

// Server-side client with service role key (for backend operations)
export const supabaseAdmin = createClient<Database>(
  supabaseUrl,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  {
    auth: {
      autoRefreshToken: false,
      persistSession: false
    }
  }
)

// Storage helpers
export const uploadFile = async (
  bucket: string,
  path: string,
  file: File | Buffer,
  options?: { contentType?: string; metadata?: Record<string, any> }
) => {
  const { data, error } = await supabase.storage
    .from(bucket)
    .upload(path, file, {
      contentType: options?.contentType,
      metadata: options?.metadata,
      upsert: false
    })
  
  if (error) throw error
  return data
}

export const getFileUrl = (bucket: string, path: string) => {
  const { data } = supabase.storage
    .from(bucket)
    .getPublicUrl(path)
  
  return data.publicUrl
}

export const downloadFile = async (bucket: string, path: string) => {
  const { data, error } = await supabase.storage
    .from(bucket)
    .download(path)
  
  if (error) throw error
  return data
}

// Database helpers
export class DocumentService {
  static async createDocument(doc: Database['public']['Tables']['documents']['Insert']) {
    const { data, error } = await supabase
      .from('documents')
      .insert(doc)
      .select()
      .single()
    
    if (error) throw error
    return data
  }

  static async getDocument(id: string) {
    const { data, error } = await supabase
      .from('documents')
      .select('*')
      .eq('id', id)
      .single()
    
    if (error) throw error
    return data
  }

  static async getUserDocuments(userId: string) {
    const { data, error } = await supabase
      .from('documents')
      .select('*')
      .eq('user_id', userId)
      .eq('status', 'completed')
      .order('created_at', { ascending: false })
    
    if (error) throw error
    return data
  }

  static async updateDocumentStatus(
    id: string, 
    status: Database['public']['Tables']['documents']['Update']['status'],
    updates?: Partial<Database['public']['Tables']['documents']['Update']>
  ) {
    const { data, error } = await supabase
      .from('documents')
      .update({ status, ...updates })
      .eq('id', id)
      .select()
      .single()
    
    if (error) throw error
    return data
  }

  static async deleteDocument(id: string) {
    const { error } = await supabase
      .from('documents')
      .delete()
      .eq('id', id)
    
    if (error) throw error
  }
}

export class ChunkService {
  static async createChunks(chunks: Database['public']['Tables']['document_chunks']['Insert'][]) {
    const { data, error } = await supabase
      .from('document_chunks')
      .insert(chunks)
      .select()
    
    if (error) throw error
    return data
  }

  static async searchSimilarChunks(
    queryEmbedding: number[],
    documentIds?: string[],
    similarityThreshold = 0.7,
    matchCount = 10
  ) {
    const { data, error } = await supabase
      .rpc('search_document_chunks', {
        query_embedding: queryEmbedding,
        document_ids: documentIds,
        similarity_threshold: similarityThreshold,
        match_count: matchCount
      })
    
    if (error) throw error
    return data
  }

  static async getDocumentChunks(documentId: string) {
    const { data, error } = await supabase
      .from('document_chunks')
      .select('*')
      .eq('document_id', documentId)
      .order('chunk_index')
    
    if (error) throw error
    return data
  }
}

export class ChatService {
  static async createSession(session: Database['public']['Tables']['chat_sessions']['Insert']) {
    const { data, error } = await supabase
      .from('chat_sessions')
      .insert(session)
      .select()
      .single()
    
    if (error) throw error
    return data
  }

  static async getSession(id: string) {
    const { data, error } = await supabase
      .rpc('get_chat_session_with_messages', {
        session_id: id,
        message_limit: 50
      })
    
    if (error) throw error
    return data[0] // Function returns array with single result
  }

  static async getUserSessions(userId: string) {
    const { data, error } = await supabase
      .from('chat_sessions')
      .select('*')
      .eq('user_id', userId)
      .eq('status', 'active')
      .order('updated_at', { ascending: false })
    
    if (error) throw error
    return data
  }

  static async addMessage(message: Database['public']['Tables']['chat_messages']['Insert']) {
    const { data, error } = await supabase
      .from('chat_messages')
      .insert(message)
      .select()
      .single()
    
    if (error) throw error
    return data
  }

  static async updateSessionTitle(id: string, title: string) {
    const { data, error } = await supabase
      .from('chat_sessions')
      .update({ title })
      .eq('id', id)
      .select()
      .single()
    
    if (error) throw error
    return data
  }

  static async deleteSession(id: string) {
    const { error } = await supabase
      .from('chat_sessions')
      .update({ status: 'deleted' })
      .eq('id', id)
    
    if (error) throw error
  }
}

export class UsageService {
  static async trackUsage(usage: Database['public']['Tables']['api_usage']['Insert']) {
    const { data, error } = await supabaseAdmin
      .from('api_usage')
      .insert(usage)
      .select()
      .single()
    
    if (error) throw error
    return data
  }

  static async getUserUsage(userId: string, days = 30) {
    const startDate = new Date()
    startDate.setDate(startDate.getDate() - days)
    
    const { data, error } = await supabase
      .from('api_usage')
      .select('*')
      .eq('user_id', userId)
      .gte('created_at', startDate.toISOString())
      .order('created_at', { ascending: false })
    
    if (error) throw error
    return data
  }
}

// Authentication helpers
export const auth = {
  signUp: async (email: string, password: string, displayName?: string) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          display_name: displayName
        }
      }
    })
    
    if (error) throw error
    return data
  },

  signIn: async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password
    })
    
    if (error) throw error
    return data
  },

  signOut: async () => {
    const { error } = await supabase.auth.signOut()
    if (error) throw error
  },

  getUser: async () => {
    const { data: { user }, error } = await supabase.auth.getUser()
    if (error) throw error
    return user
  },

  getSession: async () => {
    const { data: { session }, error } = await supabase.auth.getSession()
    if (error) throw error
    return session
  }
}

// Real-time subscriptions
export const subscriptions = {
  chatMessages: (sessionId: string, callback: (payload: any) => void) => {
    return supabase
      .channel(`chat_messages:${sessionId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'chat_messages',
          filter: `session_id=eq.${sessionId}`
        },
        callback
      )
      .subscribe()
  },

  documentStatus: (documentId: string, callback: (payload: any) => void) => {
    return supabase
      .channel(`documents:${documentId}`)
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'documents',
          filter: `id=eq.${documentId}`
        },
        callback
      )
      .subscribe()
  },

  userSessions: (userId: string, callback: (payload: any) => void) => {
    return supabase
      .channel(`user_sessions:${userId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'chat_sessions',
          filter: `user_id=eq.${userId}`
        },
        callback
      )
      .subscribe()
  }
}