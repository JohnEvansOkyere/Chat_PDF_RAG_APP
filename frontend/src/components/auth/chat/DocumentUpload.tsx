// frontend/src/components/chat/DocumentUpload.tsx
'use client';

import { useState, useRef } from 'react';
import { Upload, File, X } from 'lucide-react';
import { documentsAPI } from '@/lib/api';
import { formatFileSize } from '@/lib/utils';
import toast from 'react-hot-toast';

interface DocumentUploadProps {
  onUploadSuccess: (documentId: string) => void;
}

export default function DocumentUpload({ onUploadSuccess }: DocumentUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    const pdfFile = files.find(file => file.type === 'application/pdf');
    
    if (pdfFile) {
      setSelectedFile(pdfFile);
    } else {
      toast.error('Please select a PDF file');
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
    } else {
      toast.error('Please select a PDF file');
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    try {
      const response = await documentsAPI.upload(selectedFile);
      toast.success('Document uploaded successfully!');
      onUploadSuccess(response.document_id);
      setSelectedFile(null);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const clearFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Upload PDF Document</h2>
      
      {!selectedFile ? (
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            isDragging
              ? 'border-blue-400 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <Upload className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-4 text-lg text-gray-600">
            Drag and drop your PDF here, or{' '}
            <button
              onClick={() => fileInputRef.current?.click()}
              className="text-blue-600 hover:text-blue-500"
            >
              browse files
            </button>
          </p>
          <p className="text-sm text-gray-500 mt-2">Maximum file size: 50MB</p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>
      ) : (
        <div className="border rounded-lg p-6 bg-gray-50">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <File className="h-8 w-8 text-red-500 mr-3" />
              <div>
                <p className="font-medium text-gray-900">{selectedFile.name}</p>
                <p className="text-sm text-gray-500">{formatFileSize(selectedFile.size)}</p>
              </div>
            </div>
            <button
              onClick={clearFile}
              className="p-1 hover:bg-gray-200 rounded"
            >
              <X className="h-5 w-5 text-gray-500" />
            </button>
          </div>
          
          <button
            onClick={handleUpload}
            disabled={isUploading}
            className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {isUploading ? 'Uploading...' : 'Upload and Process'}
          </button>
        </div>
      )}
    </div>
  );
}
