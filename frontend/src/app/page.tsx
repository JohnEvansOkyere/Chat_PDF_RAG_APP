// frontend/src/app/page.tsx
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authUtils } from '@/lib/auth';
import { FileText, MessageSquare, Shield, Zap } from 'lucide-react';

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    if (authUtils.isAuthenticated()) {
      router.push('/chat');
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex justify-between items-center py-6">
          <div className="flex items-center">
            <FileText className="h-8 w-8 text-blue-600 mr-2" />
            <h1 className="text-2xl font-bold text-gray-900">VexaAI RAG Chat PDF</h1>
          </div>
          <div className="space-x-4">
            <a
              href="/auth/login"
              className="text-gray-600 hover:text-gray-900"
            >
              Sign In
            </a>
            <a
              href="/auth/register"
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
            >
              Get Started
            </a>
          </div>
        </div>

        {/* Hero Section */}
        <div className="text-center py-20">
          <h2 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Chat with Your
            <span className="text-blue-600"> PDF Documents</span>
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Upload any PDF and ask questions about its content. Get instant, accurate answers powered by advanced AI.
          </p>
          <div className="space-x-4">
            <a
              href="/auth/register"
              className="bg-blue-600 text-white px-8 py-3 rounded-md text-lg hover:bg-blue-700 inline-block"
            >
              Start Chatting
            </a>
            <a
              href="#features"
              className="border border-gray-300 text-gray-700 px-8 py-3 rounded-md text-lg hover:bg-gray-50 inline-block"
            >
              Learn More
            </a>
          </div>
        </div>

        {/* Features Section */}
        <div id="features" className="py-20">
          <div className="text-center mb-16">
            <h3 className="text-3xl font-bold text-gray-900 mb-4">
              Powerful Features
            </h3>
            <p className="text-xl text-gray-600">
              Everything you need to unlock the knowledge in your documents
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center p-6">
              <div className="bg-blue-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <FileText className="h-8 w-8 text-blue-600" />
              </div>
              <h4 className="text-xl font-semibold mb-2">PDF Upload & Processing</h4>
              <p className="text-gray-600">
                Upload PDFs up to 50MB and get them processed instantly with advanced text extraction.
              </p>
            </div>

            <div className="text-center p-6">
              <div className="bg-green-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <MessageSquare className="h-8 w-8 text-green-600" />
              </div>
              <h4 className="text-xl font-semibold mb-2">Intelligent Chat</h4>
              <p className="text-gray-600">
                Ask questions in natural language and get contextual answers based on your document content.
              </p>
            </div>

            <div className="text-center p-6">
              <div className="bg-purple-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <Zap className="h-8 w-8 text-purple-600" />
              </div>
              <h4 className="text-xl font-semibold mb-2">Fast & Accurate</h4>
              <p className="text-gray-600">
                Powered by cutting-edge AI models for quick, accurate responses with source citations.
              </p>
            </div>
          </div>
        </div>

        {/* How it Works */}
        <div className="py-20 bg-white rounded-lg shadow-sm">
          <div className="text-center mb-16">
            <h3 className="text-3xl font-bold text-gray-900 mb-4">
              How It Works
            </h3>
            <p className="text-xl text-gray-600">
              Get started in three simple steps
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 px-8">
            <div className="text-center">
              <div className="bg-blue-600 text-white rounded-full w-10 h-10 flex items-center justify-center mx-auto mb-4 text-lg font-bold">
                1
              </div>
              <h4 className="text-xl font-semibold mb-2">Upload Your PDF</h4>
              <p className="text-gray-600">
                Drag and drop or select your PDF document. We'll process it and extract the content.
              </p>
            </div>

            <div className="text-center">
              <div className="bg-blue-600 text-white rounded-full w-10 h-10 flex items-center justify-center mx-auto mb-4 text-lg font-bold">
                2
              </div>
              <h4 className="text-xl font-semibold mb-2">Ask Questions</h4>
              <p className="text-gray-600">
                Type your questions about the document in natural language.
              </p>
            </div>

            <div className="text-center">
              <div className="bg-blue-600 text-white rounded-full w-10 h-10 flex items-center justify-center mx-auto mb-4 text-lg font-bold">
                3
              </div>
              <h4 className="text-xl font-semibold mb-2">Get Answers</h4>
              <p className="text-gray-600">
                Receive instant, accurate answers based on your document's content.
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="py-8 text-center text-gray-600">
          <p>© 2024 VexaAI RAG Chat PDF. Developed by John Evans Okyere.</p>
        </div>
      </div>
    </div>
  );
}