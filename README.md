# VexaAI RAG Chat PDF

A full-stack web application that enables intelligent conversations with PDF documents using Retrieval-Augmented Generation (RAG) technology. Upload PDF documents and chat with them naturally using AI-powered responses.

**Developed by:** John Evans Okyere

## Features

### Core Functionality
- **PDF Document Upload**: Upload and manage multiple PDF documents
- **Intelligent Chat Interface**: Natural language conversations with document content
- **User Authentication**: Secure registration and login system with JWT tokens
- **Multi-Session Support**: Create and manage multiple chat sessions
- **Document Management**: View, organize, and delete uploaded documents
- **Real-time Messaging**: Instant message delivery with typing indicators

### Technical Highlights
- **Modern UI/UX**: Beautiful, responsive design with dark mode support
- **RESTful API**: Well-structured FastAPI backend with comprehensive endpoints
- **Database Integration**: PostgreSQL with Supabase for data persistence
- **File Storage**: Supabase Storage for PDF document management
- **Type Safety**: Full TypeScript implementation in frontend
- **Error Handling**: Comprehensive error handling and user feedback

## Technology Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **Python 3.13**: Latest Python features and performance improvements
- **Supabase**: PostgreSQL database and storage
- **JWT**: Secure authentication with JSON Web Tokens
- **Bcrypt**: Password hashing for security
- **Pydantic**: Data validation and serialization
- **Uvicorn**: ASGI server for production deployment

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client for API calls
- **React Hot Toast**: Beautiful notification system
- **Lucide React**: Modern icon library

## Project Structure

```
vexaai-rag-chat-pdf/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── auth.py              # Authentication routes
│   │   ├── services/
│   │   │   ├── auth_service.py      # Authentication logic
│   │   │   ├── chat_service.py      # Chat processing
│   │   │   ├── document_service.py  # Document management
│   │   │   └── vector_service.py    # Vector operations (placeholder)
│   │   │   └── llm_service.py        # LLM logic
│   │   │   └── vector_service.py     # Vector store handling
│   │   ├── middleware/
│   │   │   ├── rate_limiter.py      # Rate limiting
│   │   │   └── logging_middleware.py # Request logging
│   │   │   └── rate_limiter.py       # Request limits
│   │   ├── utils/
│   │   │   └── exceptions.py        # Error handlers
│   │   ├── config.py                # Configuration settings
│   │   ├── database.py              # Database connections
│   │   └── models.py                # Pydantic models
│   ├── main.py                      # FastAPI application
│   ├── requirements.txt             # Python dependencies
│   └── .env                         # Environment variables
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── auth/
│   │   │   │   ├── login/page.tsx   # Login page
│   │   │   │   └── register/page.tsx # Registration page
│   │   │   └── chat/page.tsx        # Main chat interface
│   │   ├── components/
│   │   │   ├── auth/
│   │   │   │   ├── LoginForm.tsx    # Login form
│   │   │   │   └── RegisterForm.tsx # Registration form
│   │   │   └── chat/
│   │   │       ├── ChatInterface.tsx # Chat UI
│   │   │       └── DocumentUpload.tsx # Upload component
│   │   ├── lib/
│   │   │   ├── api.ts               # API client
│   │   │   ├── auth.ts              # Auth utilities
│   │   │   └── utils.ts             # Helper functions
│   │   └── types/
│   │       └── index.ts             # TypeScript types
│   ├── package.json                 # Node dependencies
│   ├── tailwind.config.js           # Tailwind configuration
│   └── .env.local                   # Environment variables
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.13+
- Node.js 18+
- PostgreSQL with pgvector extension
- Supabase account (or local PostgreSQL)

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install fastapi uvicorn supabase python-multipart pydantic pydantic-settings python-jose[cryptography] bcrypt httpx
   ```

4. **Configure environment variables**
   Create `.env` file in backend directory:
   ```env
   # Database
   DATABASE_URL=your_postgres_url
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   
   # Authentication
   JWT_SECRET=your_jwt_secret_key_here
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
   # Application
   ENVIRONMENT=development
   DEBUG=True
   LOG_LEVEL=INFO
   
   # CORS
   CORS_ORIGINS=http://localhost:3000
   
   # LLM Configuration (for future RAG implementation)
   LLM_PROVIDER=Grok
   OPENAI_API_KEY=your_grok_key
   GROK_MODEL=grok-4-fast-reasoning
   ```

5. **Set up database**
   
   Run these SQL commands in your Supabase SQL Editor:
   
   ```sql
   -- Enable extensions
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   
   -- Create user_profiles table
   CREATE TABLE user_profiles (
       id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
       email TEXT UNIQUE NOT NULL,
       display_name TEXT,
       avatar_url TEXT,
       subscription_tier TEXT DEFAULT 'free',
       api_usage_count INTEGER DEFAULT 0,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   
   -- Create documents table
   CREATE TABLE documents (
       id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
       user_id UUID NOT NULL,
       filename TEXT NOT NULL,
       original_filename TEXT NOT NULL,
       file_path TEXT NOT NULL,
       file_size INTEGER NOT NULL,
       mime_type TEXT DEFAULT 'application/pdf',
       status TEXT DEFAULT 'completed',
       error_message TEXT,
       page_count INTEGER,
       chunk_count INTEGER DEFAULT 0,
       metadata JSONB DEFAULT '{}',
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   
   -- Create chat_sessions table
   CREATE TABLE chat_sessions (
       id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
       user_id UUID NOT NULL,
       title TEXT NOT NULL DEFAULT 'New Chat',
       document_id UUID,
       status TEXT DEFAULT 'active',
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   
   -- Create chat_messages table
   CREATE TABLE chat_messages (
       id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
       session_id UUID NOT NULL,
       user_id UUID NOT NULL,
       role TEXT NOT NULL,
       content TEXT NOT NULL,
       metadata JSONB DEFAULT '{}',
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   
   -- Create indexes
   CREATE INDEX idx_documents_user_id ON documents(user_id);
   CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
   CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
   ```


6. **Create Supabase Storage Bucket**
   - Go to Supabase Dashboard → Storage
   - Create a new bucket named `documents`
   - Set it to Public or Private based on your needs

7. **Start the backend server**
   ```bash
   uvicorn main:app --reload
   ```
   
   Backend will run on `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**
   Create `.env.local` file:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000/api
   ```

4. **Start development server**
   ```bash
   npm run dev
   ```
   
   Frontend will run on `http://localhost:3000`

## Usage

### Registration and Login

1. Navigate to `http://localhost:3000`
2. Click "Sign up now" to create a new account
3. Fill in your details and register
4. Login with your credentials

### Uploading Documents

1. After logging in, you'll see the chat dashboard
2. Click "Upload PDF" button
3. Select a PDF file (max 50MB)
4. Wait for upload to complete
5. A new chat session will be created automatically

### Chatting with Documents

1. Type your question in the chat input
2. Press Enter or click Send
3. Receive AI-generated responses (currently placeholder responses)
4. View chat history in the sidebar
5. Create multiple chat sessions for different documents

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/profile` - Get user profile

### Documents
- `POST /api/documents/upload` - Upload PDF document
- `GET /api/documents` - List user documents
- `GET /api/documents/{id}` - Get document details
- `DELETE /api/documents/{id}` - Delete document

### Chat
- `POST /api/chat/sessions` - Create chat session
- `GET /api/chat/sessions` - List user sessions
- `GET /api/chat/sessions/{id}` - Get session with messages
- `POST /api/chat/sessions/{id}/messages` - Send message
- `DELETE /api/chat/sessions/{id}` - Delete session

### System
- `GET /api/health` - Health check endpoint

## Development Notes

### Current Implementation Status

**Completed:**
- User authentication (registration, login, logout)
- JWT token management
- PDF file upload and storage
- Chat interface and messaging
- Session management
- Document management
- Database integration
- Error handling and logging

**In Progress / Placeholder:**
- PDF text extraction and processing
- Vector embeddings generation
- RAG implementation for context retrieval
- LLM integration for intelligent responses


## Deployment

### Backend Deployment

1. **Using Docker**
   ```bash
   docker build -t vexaai-backend .
   docker run -p 8000:8000 vexaai-backend
   ```

2. **Environment Variables**
   - Set all production environment variables
   - Use strong JWT secrets
   - Configure proper CORS origins
   - Set `ENVIRONMENT=production`

### Frontend Deployment

1. **Build for production**
   ```bash
   npm run build
   ```

2. **Deploy to Vercel/Netlify**
   - Connect your repository
   - Set `NEXT_PUBLIC_API_URL` to production backend URL
   - Deploy

## Troubleshooting

### Common Issues

**1. Foreign Key Constraint Errors**
- Remove foreign key constraints from tables that reference `users` table
- Run: `ALTER TABLE table_name DROP CONSTRAINT constraint_name;`

**2. Storage Bucket Not Found**
- Create `documents` bucket in Supabase Storage
- Set appropriate permissions

**3. Authentication Errors (401)**
- Verify token storage key matches (`authToken`)
- Check API interceptor configuration

**4. CORS Errors**
- Verify `CORS_ORIGINS` in backend `.env`
- Ensure frontend URL is allowed


## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Create an issue on GitHub
- Email: johnevansokyere@gmail.com

## Acknowledgments

- Built with FastAPI and Next.js
- Powered by Supabase
- Inspired by modern RAG architectures
- Special thanks to the open-source community

---

**VexaAI RAG Chat PDF** - Making document interaction intelligent and intuitive.

Developed with care by John Evans Okyere