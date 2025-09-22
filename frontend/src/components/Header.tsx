// src/components/Header.tsx
import React from 'react';
import { useChat } from '../contexts/ChatContext';
import { Menu, FileText } from 'lucide-react';

interface HeaderProps {
  onToggleSidebar: () => void;
  sidebarOpen: boolean;
}

const Header: React.FC<HeaderProps> = ({ onToggleSidebar, sidebarOpen }) => {
  const { currentSession, selectedDocument } = useChat();

  return (
    <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
      <div className="flex items-center space-x-4">
        <button
          onClick={onToggleSidebar}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <Menu className="h-5 w-5 text-gray-600" />
        </button>
        
        <div>
          <h1 className="text-lg font-semibold text-gray-900">
            {currentSession?.title || 'VexaAI Chat'}
          </h1>
          {selectedDocument && (
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <FileText className="h-4 w-4" />
              <span>{selectedDocument.filename}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};