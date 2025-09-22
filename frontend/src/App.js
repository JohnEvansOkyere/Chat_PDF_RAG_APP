import React, { useState, useEffect, useRef } from 'react';
import { Upload, Send, FileText, MessageCircle, User, Bot, Settings, Trash2, Plus, Menu, X } from 'lucide-react';

const VexaAIApp = () => {
  // State management
  const [user, setUser] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentDocument, setCurrentDocument] = useState(null);
  
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // API Base URL
  const API_BASE = 'http://localhost:8000/api';
  
  // Mock authentication for development
  useEffect(() => {
    // Simulate logged in user
    setUser({
      id: 'mock-user-id',
      email: 'demo@vexaai.com',
      display_name: 'Demo User'
    });
    
    // Load initial data
    loadDocuments();
    loadSessions();
  }, []);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // API calls
  const apiCall = async (endpoint, options = {}) => {
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer mock-token',
          ...options.headers
        },
        ...options
      });
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API call failed:', error);
      throw error;
    }
  };

  const loadDocuments = async () => {
    try {
      const docs = await apiCall('/documents');
      setDocuments(docs);
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  const loadSessions = async () => {
    try {
      const sessionList = await apiCall('/chat/sessions');
      setSessions(sessionList);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const loadSessionMessages = async (sessionId) => {
    try {
      const session = await apiCall(`/chat/sessions/${sessionId}`);
      setMessages(session.messages || []);
      setCurrentSession(session);
    } catch (error) {
      console.error('Failed to load session messages:', error);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadingFile(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE}/documents/upload`, {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer mock-token'
        },
        body: formData
      });

      if (!response.ok) throw new Error('Upload failed');
      
      const result = await response.json();
      await loadDocuments();
      
      // Create new chat session with this document
      const newSession = await apiCall('/chat/sessions', {
        method: 'POST',
        body: JSON.stringify({
          title: `Chat with ${file.name}`,
          document_id: result.document_id
        })
      });
      
      setCurrentDocument(result);
      setCurrentSession(newSession);
      setMessages([]);
      await loadSessions();
      
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploadingFile(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;
    
    const userMessage = { role: 'user', content: inputMessage.trim() };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      if (!currentSession) {
        // Create new session if none exists
        const newSession = await apiCall('/chat/sessions', {
          method: 'POST',
          body: JSON.stringify({
            title: 'New Chat',
            document_id: currentDocument?.document_id
          })
        });
        setCurrentSession(newSession);
        await loadSessions();
      }

      const response = await apiCall(`/chat/sessions/${currentSession.id}/messages`, {
        method: 'POST',
        body: JSON.stringify({
          message: userMessage.content,
          document_id: currentDocument?.document_id
        })
      });

      const assistantMessage = {
        role: 'assistant',
        content: response.content,
        sources: response.sources || []
      };

      setMessages(prev => [...prev, assistantMessage]);

    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your message. Please try again.'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const createNewSession = async () => {
    try {
      const newSession = await apiCall('/chat/sessions', {
        method: 'POST',
        body: JSON.stringify({
          title: 'New Chat'
        })
      });
      
      setCurrentSession(newSession);
      setMessages([]);
      setCurrentDocument(null);
      await loadSessions();
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const deleteSession = async (sessionId) => {
    try {
      await apiCall(`/chat/sessions/${sessionId}`, { method: 'DELETE' });
      await loadSessions();
      
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  // Component renders
  const renderMessage = (message, index) => (
    <div key={index} className={`flex gap-3 p-4 ${message.role === 'user' ? 'bg-blue-50' : 'bg-gray-50'}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
        message.role === 'user' ? 'bg-blue-500 text-white' : 'bg-green-500 text-white'
      }`}>
        {message.role === 'user' ? <User size={16} /> : <Bot size={16} />}
      </div>
      <div className="flex-1">
        <div className="font-medium text-sm mb-1">
          {message.role === 'user' ? 'You' : 'VexaAI'}
        </div>
        <div className="text-gray-800 whitespace-pre-wrap">
          {message.content}
        </div>
        {message.sources && message.sources.length > 0 && (
          <div className="mt-2 p-2 bg-white border rounded text-sm">
            <div className="font-medium mb-1">Sources:</div>
            {message.sources.map((source, idx) => (
              <div key={idx} className="text-gray-600">
                • {source.document_name} (Page {source.page_number})
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-80' : 'w-0'} bg-white border-r border-gray-200 transition-all duration-300 overflow-hidden flex flex-col`}>
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg flex items-center justify-center text-white font-bold">
              V
            </div>
            <h1 className="text-xl font-bold text-gray-800">VexaAI</h1>
          </div>
          
          <button
            onClick={createNewSession}
            className="w-full flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus size={16} />
            New Chat
          </button>
        </div>

        {/* File Upload */}
        <div className="p-4 border-b border-gray-200">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".pdf"
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploadingFile}
            className="w-full flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
          >
            <Upload size={16} />
            {uploadingFile ? 'Uploading...' : 'Upload PDF'}
          </button>
        </div>

        {/* Documents */}
        <div className="p-4 border-b border-gray-200">
          <h3 className="font-medium text-gray-800 mb-2">Documents</h3>
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {documents.map(doc => (
              <div key={doc.id} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
                <FileText size={14} />
                <span className="text-sm text-gray-600 truncate">{doc.filename}</span>
                <span className={`text-xs px-2 py-1 rounded ${
                  doc.status === 'completed' ? 'bg-green-100 text-green-600' :
                  doc.status === 'processing' ? 'bg-yellow-100 text-yellow-600' :
                  'bg-red-100 text-red-600'
                }`}>
                  {doc.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Chat Sessions */}
        <div className="flex-1 p-4 overflow-y-auto">
          <h3 className="font-medium text-gray-800 mb-2">Chat Sessions</h3>
          <div className="space-y-2">
            {sessions.map(session => (
              <div key={session.id} className={`flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-gray-100 ${
                currentSession?.id === session.id ? 'bg-blue-100' : ''
              }`}>
                <MessageCircle size={14} />
                <div className="flex-1" onClick={() => loadSessionMessages(session.id)}>
                  <div className="text-sm font-medium truncate">{session.title}</div>
                  <div className="text-xs text-gray-500">{session.message_count} messages</div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteSession(session.id);
                  }}
                  className="text-red-500 hover:text-red-700"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* User Profile */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
              <User size={16} />
            </div>
            <div className="flex-1">
              <div className="text-sm font-medium">{user?.display_name}</div>
              <div className="text-xs text-gray-500">{user?.email}</div>
            </div>
            <Settings size={16} className="text-gray-400" />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 p-4 flex items-center gap-4">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-gray-500 hover:text-gray-700"
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <h2 className="text-lg font-semibold text-gray-800">
            {currentSession ? currentSession.title : 'Welcome to VexaAI'}
          </h2>
          {currentDocument && (
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <FileText size={16} />
              {currentDocument.filename}
            </div>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="w-16 h-16 bg-gradient-to-br from-purple-600 to-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4">
                  V
                </div>
                <h3 className="text-xl font-semibold text-gray-800 mb-2">Welcome to VexaAI</h3>
                <p className="text-gray-600 mb-4">Upload a PDF document and start chatting!</p>
                <div className="space-y-2 text-sm text-gray-500">
                  <p>• Ask questions about your documents</p>
                  <p>• Get AI-powered insights</p>
                  <p>• Search through content intelligently</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-0">
              {messages.map(renderMessage)}
              {isLoading && (
                <div className="flex gap-3 p-4 bg-gray-50">
                  <div className="w-8 h-8 rounded-full bg-green-500 text-white flex items-center justify-center">
                    <Bot size={16} />
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-sm mb-1">VexaAI</div>
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Ask a question about your document..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              disabled={isLoading}
            />
            <button
              onClick={sendMessage}
              disabled={!inputMessage.trim() || isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Send size={16} />
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VexaAIApp;