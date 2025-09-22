/ src/components/WelcomeScreen.tsx
import React from 'react';
import { useChat } from '../contexts/ChatContext';
import { Bot, Upload, MessageCircle, Zap, Shield, Clock } from 'lucide-react';

const WelcomeScreen: React.FC = () => {
  const { createSession } = useChat();

  const features = [
    {
      icon: <Zap className="h-6 w-6" />,
      title: "Instant Answers",
      description: "Get immediate responses from your PDF documents"
    },
    {
      icon: <Shield className="h-6 w-6" />,
      title: "Secure & Private",
      description: "Your documents are processed securely and privately"
    },
    {
      icon: <Clock className="h-6 w-6" />,
      title: "Save Time",
      description: "Find information quickly without reading entire documents"
    }
  ];

  const handleStartChat = async () => {
    try {
      await createSession();
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  return (
    <div className="h-full flex items-center justify-center p-8">
      <div className="max-w-4xl mx-auto text-center">
        {/* Hero Section */}
        <div className="mb-12">
          <div className="w-24 h-24 gradient-bg rounded-3xl flex items-center justify-center mx-auto mb-8 animate-float">
            <Bot className="w-12 h-12 text-white" />
          </div>
          
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Chat with Your <span className="text-gradient">PDF Documents</span>
          </h1>
          
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Upload any PDF document and start asking questions. VexaAI uses advanced RAG technology 
            to provide accurate, context-aware answers from your documents.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={handleStartChat}
              className="btn-primary flex items-center justify-center space-x-2 px-8 py-4 text-lg"
            >
              <MessageCircle className="h-5 w-5" />
              <span>Start Chatting</span>
            </button>
            
            <button className="btn-secondary flex items-center justify-center space-x-2 px-8 py-4 text-lg">
              <Upload className="h-5 w-5" />
              <span>Upload PDF</span>
            </button>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-8 mb-12">
          {features.map((feature, index) => (
            <div key={index} className="card-hover p-6 text-center">
              <div className="w-12 h-12 gradient-bg rounded-xl flex items-center justify-center text-white mx-auto mb-4">
                {feature.icon}
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {feature.title}
              </h3>
              <p className="text-gray-600">
                {feature.description}
              </p>
            </div>
          ))}
        </div>

        {/* How it Works */}
        <div className="card p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">How it Works</h2>
          <div className="grid md:grid-cols-3 gap-6 text-left">
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center font-bold">
                1
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-1">Upload PDF</h3>
                <p className="text-gray-600 text-sm">Select and upload your PDF document</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center font-bold">
                2
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-1">AI Processing</h3>
                <p className="text-gray-600 text-sm">AI analyzes and indexes your document</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center font-bold">
                3
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-1">Ask Questions</h3>
                <p className="text-gray-600 text-sm">Chat naturally and get instant answers</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};