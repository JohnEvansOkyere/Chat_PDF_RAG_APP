// frontend/src/app/chat/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authUtils } from '@/lib/auth';
import { documentsAPI, chatAPI } from '@/lib/api';
import { Document, ChatSession, ChatMessage, User } from '@/types';
import DocumentUpload from '@/components/chat/DocumentUpload';
import ChatInterface from '@/components/chat/ChatInterface';
import { FileText, MessageSquare, LogOut, Plus, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';

export default function ChatPage() {
  const [user, setUser] = useState<User | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [currentDocument, setCurrentDocument] = useState<Document | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const { user: authUser } = authUtils.getAuth();
    if (!authUser) {
      router.push('/auth/login');
      return;
    }
    setUser(authUser);
    loadData();
  }, [router]);

  const loadData = async () => {
    try {
      const [docsData, sessionsData] = await Promise.all([
        documentsAPI.list(),
        chatAPI.getSessions()
      ]);
      setDocuments(docsData);
      setSessions(sessionsData);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await authUtils.clearAuth();
      router.push('/');
    } catch (error) {
      toast.error('Logout failed');
    }
  };

  const handleUploadSuccess = async (documentId: string) => {
    // Refresh documents list
    const docsData = await documentsAPI.list();
    setDocuments(docsData);
    
    // Find the uploaded document
    const uploadedDoc = docsData.find(doc => doc.id === documentId);
    if (uploadedDoc) {
      setCurrentDocument(uploadedDoc);
      // Create new chat session for this document
      try {
        const session = await chatAPI.createSession(
          `Chat with ${uploadedDoc.original_filename}`,
          documentId
        );
        setSessions(prev => [session, ...prev]);
        setCurrentSession(session);
        setMessages([]);
      } catch (error) {
        toast.error('Failed to create chat session');
      }
    }
  };

  const handleSessionSelect = async (session: ChatSession) => {
    try {
      const sessionData = await chatAPI.getSession(session.id);
      setCurrentSession(session);
      setMessages(sessionData.messages || []);
    } catch (error) {
      toast.error('Failed to load session');
    }
  };

  const handleNewSession = async () => {
    try {
      const session = await chatAPI.createSession();
      setSessions(prev => [session, ...prev]);
      setCurrentSession(session);
      setMessages([]);
      setCurrentDocument(null);
    } catch (error) {
      toast.error('Failed to create session');
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    try {
      await chatAPI.deleteSession(sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }
      toast.success('Session deleted');
    } catch (error) {
      toast.error('Failed to delete session');
    }
  };

  const handleNewMessage = (message: ChatMessage) => {
    setMessages(prev => [...prev, message]);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-lg font-semibold text-gray-900">VexaAI Chat</h1>
            <button
              onClick={handleLogout}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-md"
            >
              <LogOut size={18} />
            </button>
          </div>
          <div className="text-sm text-gray-600">
            Welcome, {user?.display_name || user?.email}
          </div>
        </div>

        {/* New Session Button */}
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={handleNewSession}
            className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            <Plus size={18} className="mr-2" />
            New Chat
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-4">
            <h2 className="text-sm font-medium text-gray-700 mb-2">Chat Sessions</h2>
            <div className="space-y-2">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className={`group flex items-center justify-between p-2 rounded-md cursor-pointer hover:bg-gray-100 ${
                    currentSession?.id === session.id ? 'bg-blue-50 border border-blue-200' : ''
                  }`}
                  onClick={() => handleSessionSelect(session)}
                >
                  <div className="flex items-center flex-1 min-w-0">
                    <MessageSquare size={16} className="text-gray-400 mr-2 flex-shrink-0" />
                    <span className="text-sm text-gray-900 truncate">{session.title}</span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteSession(session.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-600"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Documents List */}
        <div className="border-t border-gray-200">
          <div className="p-4">
            <h2 className="text-sm font-medium text-gray-700 mb-2">Documents</h2>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className={`flex items-center p-2 rounded-md cursor-pointer hover:bg-gray-100 ${
                    doc.status === 'completed' ? 'text-gray-900' : 'text-gray-500'
                  }`}
                >
                  <FileText size={16} className="text-gray-400 mr-2 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm truncate">{doc.original_filename}</div>
                    <div className="text-xs text-gray-500">{doc.status}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {currentSession ? (
          <ChatInterface
            sessionId={currentSession.id}
            documentId={currentDocument?.id}
            messages={messages}
            onNewMessage={handleNewMessage}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <DocumentUpload onUploadSuccess={handleUploadSuccess} />
          </div>
        )}
      </div>
    </div>
  );
}