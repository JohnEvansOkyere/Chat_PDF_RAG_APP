import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../contexts/ChatContext';
import { Send, Bot, User, FileText, Copy, ThumbsUp, ThumbsDown } from 'lucide-react';
import toast from 'react-hot-toast';

const ChatArea: React.FC = () => {
  const { 
    currentSession, 
    messages, 
    sendMessage, 
    isTyping, 
    selectedDocument 
  } = useChat();
  
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [inputMessage]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    try {
      await sendMessage(inputMessage.trim());
      setInputMessage('');
    } catch (error) {
      // Error handled in context
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  const renderMessage = (message: any, index: number) => {
    const isUser = message.role === 'user';
    
    return (
      <div key={index} className={`flex gap-4 p-6 ${isUser ? 'bg-white' : 'bg-gray-50'}`}>
        {/* Avatar */}
        <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
          isUser 
            ? 'bg-gradient-to-br from-primary-500 to-primary-600 text-white' 
            : 'bg-gradient-to-br from-green-500 to-green-600 text-white'
        }`}>
          {isUser ? <User size={20} /> : <Bot size={20} />}
        </div>

        {/* Message Content */}
        <div className="flex-1 space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-gray-900">
              {isUser ? 'You' : 'VexaAI'}
            </span>
            <span className="text-xs text-gray-500">
              {new Date(message.created_at).toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </span>
          </div>

          {/* Message Text */}
          <div className="prose prose-sm max-w-none">
            <div className="text-gray-800 whitespace-pre-wrap leading-relaxed">
              {message.content}
            </div>
          </div>

          {/* Sources */}
          {message.sources && message.sources.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-4">
              <div className="flex items-center gap-2 text-blue-700 font-medium mb-2">
                <FileText size={16} />
                <span>Sources</span>
              </div>
              <div className="space-y-2">
                {message.sources.map((source: any, idx: number) => (
                  <div key={idx} className="text-sm text-blue-600">
                    • {source.document_name} (Page {source.page_number})
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Message Actions */}
          {!isUser && (
            <div className="flex items-center gap-2 pt-2">
              <button
                onClick={() => copyToClipboard(message.content)}
                className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
                title="Copy message"
              >
                <Copy size={14} />
              </button>
              <button
                className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
                title="Good response"
              >
                <ThumbsUp size={14} />
              </button>
              <button
                className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
                title="Bad response"
              >
                <ThumbsDown size={14} />
              </button>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* Chat Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              {currentSession?.title || 'Chat'}
            </h2>
            {selectedDocument && (
              <div className="flex items-center gap-2 text-sm text-gray-500 mt-1">
                <FileText size={14} />
                <span>Chatting with {selectedDocument.filename}</span>
              </div>
            )}
          </div>
          
          {messages.length > 0 && (
            <div className="text-sm text-gray-500">
              {messages.length} messages
            </div>
          )}
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-md">
              <div className="w-20 h-20 gradient-bg rounded-full flex items-center justify-center mx-auto mb-4">
                <Bot className="w-10 h-10 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Ready to chat!
              </h3>
              <p className="text-gray-600 mb-6">
                {selectedDocument 
                  ? `Ask me anything about ${selectedDocument.filename}`
                  : 'Upload a PDF document and start asking questions'
                }
              </p>
              <div className="grid grid-cols-1 gap-2 text-sm">
                <div className="p-3 bg-gray-50 rounded-lg text-left">
                  <div className="font-medium text-gray-900">Example questions:</div>
                  <div className="text-gray-600 mt-1">
                    • "Summarize the main points"<br/>
                    • "What does this document say about...?"<br/>
                    • "Find information related to..."
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div>
            {messages.map(renderMessage)}
            
            {/* Typing Indicator */}
            {isTyping && (
              <div className="flex gap-4 p-6 bg-gray-50">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-green-500 to-green-600 text-white flex items-center justify-center flex-shrink-0">
                  <Bot size={20} />
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-gray-900 mb-2">VexaAI</div>
                  <div className="flex items-center gap-1">
                    <div className="typing-dot bg-gray-400"></div>
                    <div className="typing-dot bg-gray-400" style={{animationDelay: '0.1s'}}></div>
                    <div className="typing-dot bg-gray-400" style={{animationDelay: '0.2s'}}></div>
                    <span className="ml-2 text-gray-500 text-sm">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <textarea
                ref={textareaRef}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={
                  selectedDocument 
                    ? `Ask anything about ${selectedDocument.filename}...`
                    : "Type your message... (upload a PDF first)"
                }
                className="w-full px-4 py-3 border border-gray-300 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent max-h-32 min-h-[48px]"
                rows={1}
                disabled={isTyping}
              />
            </div>
            
            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isTyping}
              className="btn-primary p-3 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              <Send size={20} />
            </button>
          </div>
          
          <div className="flex justify-between items-center mt-2 text-xs text-gray-500">
            <span>
              Press Enter to send, Shift + Enter for new line
            </span>
            {inputMessage.length > 0 && (
              <span>{inputMessage.length} / 4000</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatArea;