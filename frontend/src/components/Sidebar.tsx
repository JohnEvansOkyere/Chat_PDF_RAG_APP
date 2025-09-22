import React, { useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useChat } from '../contexts/ChatContext';
import { 
  Bot, 
  Plus, 
  Upload, 
  FileText, 
  MessageCircle, 
  Trash2, 
  User, 
  Settings,
  LogOut,
  X,
  Clock
} from 'lucide-react';
import toast from 'react-hot-toast';

interface SidebarProps {
  onClose?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ onClose }) => {
  const { user, logout } = useAuth();
  const { 
    documents, 
    sessions, 
    currentSession,
    uploadDocument, 
    createSession, 
    selectSession, 
    deleteSession,
    uploadProgress,
    isLoading 
  } = useChat();
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      toast.error('Please select a PDF file');
      return;
    }

    if (file.size > 50 * 1024 * 1024) { // 50MB limit
      toast.error('File size must be less than 50MB');
      return;
    }

    try {
      await uploadDocument(file);
    } catch (error) {
      // Error handled in context
    }

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleCreateSession = async () => {
    try {
      await createSession();
    } catch (error) {
      // Error handled in context
    }
  };

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (window.confirm('Are you sure you want to delete this chat session?')) {
      try {
        await deleteSession(sessionId);
      } catch (error) {
        // Error handled in context
      }
    }
  };

  const handleLogout = async () => {
    if (window.confirm('Are you sure you want to sign out?')) {
      await logout();
    }
  };

  const getDocumentStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'processing':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 24 * 60 * 60 * 1000) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    return date.toLocaleDateString();
  };

  return (
    <div className="h-full bg-white border-r border-gray-200 flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 gradient-bg rounded-xl flex items-center justify-center">
              <Bot className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">VexaAI</h1>
              <p className="text-xs text-gray-500">RAG Chat PDF</p>
            </div>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg md:hidden"
            >
              <X className="h-5 w-5 text-gray-500" />
            </button>
          )}
        </div>

        {/* New Chat Button */}
        <button
          onClick={handleCreateSession}
          disabled={isLoading}
          className="btn-primary w-full flex items-center justify-center space-x-2"
        >
          <Plus className="h-4 w-4" />
          <span>New Chat</span>
        </button>
      </div>

      {/* File Upload */}
      <div className="p-4 border-b border-gray-100">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          accept=".pdf"
          className="hidden"
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading}
          className="w-full flex items-center justify-center space-x-2 py-3 px-4 bg-green-50 hover:bg-green-100 text-green-700 rounded-xl transition-colors disabled:opacity-50"
        >
          <Upload className="h-4 w-4" />
          <span>Upload PDF</span>
        </button>
        
        {uploadProgress > 0 && uploadProgress < 100 && (
          <div className="mt-2">
            <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
              <span>Uploading...</span>
              <span>{uploadProgress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-green-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Content Sections */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {/* Documents Section */}
        <div className="p-4 border-b border-gray-100">
          <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
            <FileText className="h-4 w-4 mr-2" />
            Documents ({documents.length})
          </h3>
          
          <div className="space-y-2 max-h-40 overflow-y-auto scrollbar-thin">
            {documents.length === 0 ? (
              <p className="text-sm text-gray-500 italic">No documents uploaded</p>
            ) : (
              documents.map((doc) => (
                <div 
                  key={doc.id}
                  className="group p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <div className="flex items-start space-x-2">
                    <FileText className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {doc.filename}
                      </p>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className={`text-xs px-2 py-1 rounded-full font-medium ${getDocumentStatusColor(doc.status)}`}>
                          {doc.status}
                        </span>
                        {doc.page_count && (
                          <span className="text-xs text-gray-500">
                            {doc.page_count} pages
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Chat Sessions */}
        <div className="p-4 flex-1">
          <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
            <MessageCircle className="h-4 w-4 mr-2" />
            Recent Chats ({sessions.length})
          </h3>
          
          <div className="space-y-2">
            {sessions.length === 0 ? (
              <p className="text-sm text-gray-500 italic">No chat sessions</p>
            ) : (
              sessions.map((session) => (
                <div
                  key={session.id}
                  onClick={() => selectSession(session.id)}
                  className={`group p-3 rounded-lg cursor-pointer transition-all hover:bg-gray-50 ${
                    currentSession?.id === session.id 
                      ? 'bg-primary-50 border border-primary-200' 
                      : 'hover:shadow-sm'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <MessageCircle className={`h-4 w-4 flex-shrink-0 ${
                          currentSession?.id === session.id 
                            ? 'text-primary-600' 
                            : 'text-gray-400'
                        }`} />
                        <p className={`text-sm font-medium truncate ${
                          currentSession?.id === session.id 
                            ? 'text-primary-900' 
                            : 'text-gray-900'
                        }`}>
                          {session.title}
                        </p>
                      </div>
                      
                      <div className="flex items-center space-x-3 mt-1">
                        <span className="text-xs text-gray-500 flex items-center">
                          <Clock className="h-3 w-3 mr-1" />
                          {formatDate(session.updated_at)}
                        </span>
                        {session.message_count > 0 && (
                          <span className="text-xs text-gray-500">
                            {session.message_count} messages
                          </span>
                        )}
                      </div>
                    </div>
                    
                    <button
                      onClick={(e) => handleDeleteSession(session.id, e)}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 hover:text-red-600 rounded transition-all"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* User Profile */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
          <div className="h-10 w-10 bg-gradient-to-br from-gray-400 to-gray-600 rounded-full flex items-center justify-center">
            <User className="h-5 w-5 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">
              {user?.display_name || user?.email}
            </p>
            <p className="text-xs text-gray-500 truncate">
              {user?.subscription_tier || 'Free Plan'}
            </p>
          </div>
          <div className="flex space-x-1">
            <button className="p-2 hover:bg-gray-200 rounded-lg transition-colors">
              <Settings className="h-4 w-4 text-gray-500" />
            </button>
            <button 
              onClick={handleLogout}
              className="p-2 hover:bg-red-100 hover:text-red-600 rounded-lg transition-colors"
            >
              <LogOut className="h-4 w-4 text-gray-500 hover:text-red-600" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;