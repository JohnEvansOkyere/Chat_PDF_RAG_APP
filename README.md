# 🤖 VexaAI - RAG Chat PDF Application

**Intelligent PDF Chat Assistant powered by Advanced AI**

*Developed by John Evans Okyere*

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## 🎯 Overview

VexaAI is a sophisticated Retrieval-Augmented Generation (RAG) application that enables users to have intelligent conversations with PDF documents. Built with cutting-edge AI technologies, it combines document processing, vector search, and natural language generation to provide accurate, context-aware responses.

### 🌟 Key Highlights

- **Advanced RAG Architecture**: Implements state-of-the-art retrieval-augmented generation
- **Ollama Integration**: Leverages local LLM models for privacy and performance
- **Modern UI/UX**: Beautiful, responsive Streamlit interface
- **Production Ready**: Comprehensive error handling, logging, and session management
- **Extensible Design**: Modular architecture for easy customization

---

## ✨ Features

### 📄 Document Processing
- **Multi-format Support**: PDF processing with advanced text extraction
- **Intelligent Chunking**: Smart document segmentation for optimal retrieval
- **Metadata Extraction**: Comprehensive document analysis and statistics
- **Large File Handling**: Efficient processing of documents up to 50MB

### 🧠 AI Capabilities
- **Context-Aware Responses**: Accurate answers based on document content
- **Semantic Search**: Advanced vector similarity matching
- **Conversation Memory**: Maintains context across chat sessions
- **Response Optimization**: Configurable response length and quality

### 🎨 User Interface
- **Modern Design**: Clean, professional interface with custom styling
- **Responsive Layout**: Works seamlessly on desktop and mobile
- **Real-time Processing**: Live feedback during document processing
- **Interactive Chat**: Intuitive conversation interface

### 🛠️ Technical Features
- **Session Management**: Comprehensive user session handling
- **Performance Monitoring**: Response time tracking and optimization
- **Error Handling**: Robust error management and user feedback
- **Data Export**: Chat history and session data export capabilities

---

## 🏗️ Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                           VexaAI RAG System                     │
├─────────────────────────────────────────────────────────────────┤
│  Frontend Layer (Streamlit)                                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │ UI Components│ │ Chat Interface│ │ File Upload │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│  Application Layer                                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │Session Mgmt │ │ Chat Engine │ │PDF Processor│              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│  AI/ML Layer                                                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │ Ollama LLM  │ │ Embeddings  │ │Vector Store │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│  Data Layer                                                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │ PDF Storage │ │    Logs     │ │   Cache     │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | Streamlit | User interface and interaction |
| **Backend** | Python 3.8+ | Core application logic |
| **LLM** | Ollama (DeepSeek-R1) | Language model for responses |
| **Embeddings** | Ollama Embeddings | Text vectorization |
| **Vector Store** | LangChain InMemoryVectorStore | Document retrieval |
| **PDF Processing** | PDFPlumber | Document text extraction |
| **Text Splitting** | LangChain RecursiveCharacterTextSplitter | Document chunking |

---

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- Ollama installed and running
- 4GB+ RAM recommended
- 2GB+ free disk space

### Step 1: Clone Repository

```bash
git clone https://github.com/johnevans/vexaai-rag-chat-pdf.git
cd vexaai-rag-chat-pdf
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install and Setup Ollama

```bash
# Install Ollama (visit https://ollama.ai for platform-specific instructions)
# Pull the required model
ollama pull deepseek-r1:14b
```

### Step 5: Environment Configuration

Create a `.env` file in the project root:

```env
# Model Configuration
MODEL_NAME=deepseek-r1:14b
EMBEDDING_MODEL=deepseek-r1:14b

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# Application Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
SIMILARITY_SEARCH_K=5
MAX_FILE_SIZE_MB=50
TEMPERATURE=0.1
```

---

## ⚙️ Configuration

### Configuration Files

The application uses a centralized configuration system located in `src/config.py`.

#### Key Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `MODEL_NAME` | deepseek-r1:14b | Primary LLM model |
| `EMBEDDING_MODEL` | deepseek-r1:14b | Embedding model |
| `CHUNK_SIZE` | 1000 | Document chunk size |
| `CHUNK_OVERLAP` | 200 | Chunk overlap for context |
| `SIMILARITY_SEARCH_K` | 5 | Number of similar chunks to retrieve |
| `MAX_FILE_SIZE_MB` | 50 | Maximum PDF file size |
| `TEMPERATURE` | 0.1 | LLM response creativity (0-1) |

### Custom Model Configuration

To use different models:

1. Install the desired model with Ollama:
   ```bash
   ollama pull llama2:7b
   ```

2. Update your `.env` file:
   ```env
   MODEL_NAME=llama2:7b
   EMBEDDING_MODEL=llama2:7b
   ```

---

## 🎯 Usage

### Starting the Application

```bash
# Ensure Ollama is running
ollama serve

# Start VexaAI (in a new terminal)
streamlit run main.py
```

The application will be available at `http://localhost:8501`

### Basic Workflow

1. **Upload PDF**: Click on the file upload area and select your PDF
2. **Wait for Processing**: The system will extract and index the content
3. **Start Chatting**: Ask questions about your document
4. **Explore Features**: Use sidebar controls and settings

### Example Interactions

#### Academic Paper Analysis
```
User: "What is the main research question in this paper?"
VexaAI: "Based on the document, the main research question focuses on investigating the impact of machine learning algorithms on predictive accuracy in financial markets, specifically examining how ensemble methods compare to traditional approaches."
```

#### Business Document Review
```
User: "Summarize the key financial metrics mentioned"
VexaAI: "The document highlights several key financial metrics: revenue growth of 15.3% year-over-year, EBITDA margin improvement to 22.1%, and operating cash flow of $2.4M for Q3, indicating strong operational performance."
```

### Advanced Features

#### Conversation Export
- Access chat history export in the sidebar
- Download conversations as JSON files
- Include metadata and timestamps

#### Session Management
- Automatic session tracking
- Performance metrics monitoring
- Error logging and recovery

---

## 📁 Project Structure

```
vexaai-rag-chat-pdf/
│
├── main.py                     # Main application entry point
├── requirements.txt            # Python dependencies
├── README.md                  # Project documentation
├── .env.example               # Environment configuration template
├── .gitignore                 # Git ignore rules
│
├── src/                       # Source code modules
│   ├── __init__.py           # Package initialization
│   ├── config.py             # Configuration management
│   ├── pdf_processor.py      # PDF processing logic
│   ├── vector_store.py       # Vector store management
│   ├── chat_engine.py        # Chat and response logic
│   ├── session_manager.py    # Session state management
│   ├── ui_components.py      # Custom UI components
│   └── utils.py              # Utility functions
│
├── data/                     # Data storage
│   ├── pdfs/                # PDF file storage
│   └── cache/               # Application cache
│
├── logs/                     # Application logs
│   ├── interactions/        # User interaction logs
│   └── errors/              # Error logs
│
├── exports/                  # Data exports
│   ├── chat_history/        # Exported chat sessions
│   └── reports/             # Generated reports
│
├── tests/                    # Unit tests
│   ├── __init__.py
│   ├── test_pdf_processor.py
│   ├── test_vector_store.py
│   ├── test_chat_engine.py
│   └── test_utils.py
│
├── docs/                     # Additional documentation
│   ├── api_reference.md     # API documentation
│   ├── deployment.md        # Deployment guide
│   └── troubleshooting.md   # Troubleshooting guide
│
└── scripts/                  # Utility scripts
    ├── setup.sh             # Setup script
    ├── test.sh              # Testing script
    └── deploy.sh            # Deployment script
```

### Module Descriptions

#### `main.py`
- Application entry point
- Streamlit configuration
- Main application class and workflow

#### `src/config.py`
- Centralized configuration management
- Environment variable handling
- Validation and defaults

#### `src/pdf_processor.py`
- PDF file validation and processing
- Text extraction and cleaning
- Document chunking and metadata

#### `src/vector_store.py`
- Vector store initialization and management
- Document indexing and retrieval
- Similarity search operations

#### `src/chat_engine.py`
- Chat logic and conversation flow
- LLM integration and response generation
- Context management and history

#### `src/session_manager.py`
- User session state management
- Data persistence and cleanup
- Performance tracking

#### `src/ui_components.py`
- Custom Streamlit components
- UI styling and theming
- Interactive elements

#### `src/utils.py`
- Common utility functions
- Logging and error handling
- File operations and validation

---

## 🔧 API Documentation

### Core Classes

#### `RAGChatApp`
Main application class that orchestrates all components.

```python
class RAGChatApp:
    def __init__(self):
        """Initialize the RAG Chat Application"""
        
    def handle_pdf_upload(self, uploaded_file) -> bool:
        """Handle PDF file upload and processing"""
        
    def handle_chat_interaction(self, question: str):
        """Handle chat interaction with the PDF"""
        
    def run(self):
        """Main application entry point"""
```

#### `PDFProcessor`
Handles PDF document processing and text extraction.

```python
class PDFProcessor:
    def load_pdf(self, file_path: str) -> List[Document]:
        """Load PDF document and extract text"""
        
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into smaller chunks"""
        
    def get_document_stats(self, documents: List[Document]) -> dict:
        """Get statistics about processed documents"""
```

#### `VectorStoreManager`
Manages document indexing and retrieval.

```python
class VectorStoreManager:
    def index_documents(self, documents: List[Document]) -> bool:
        """Index documents in the vector store"""
        
    def similarity_search(self, query: str, k: int = None) -> List[Document]:
        """Perform similarity search for relevant documents"""
        
    def get_relevant_context(self, query: str, max_length: int = 3000) -> str:
        """Get relevant context for a query"""
```

#### `ChatEngine`
Handles conversation logic and response generation.

```python
class ChatEngine:
    def get_response(self, question: str) -> str:
        """Main method to get response for a user question"""
        
    def get_conversation_history(self) -> List[Dict]:
        """Get conversation history"""
        
    def clear_conversation_history(self):
        """Clear conversation history"""
```

---

## 🤝 Contributing

We welcome contributions to VexaAI! Please follow these guidelines:

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `python -m pytest`
6. Submit a pull request

### Code Standards

- Follow PEP 8 style guidelines
- Add docstrings to all functions and classes
- Include type hints where appropriate
- Write comprehensive tests
- Update documentation for new features

### Reporting Issues

Please use the GitHub issue tracker to report bugs or request features. Include:
- Detailed description of the issue
- Steps to reproduce
- System information (OS, Python version, etc.)
- Relevant log files

---

## 🔍 Troubleshooting

### Common Issues

#### 1. Ollama Connection Error
**Problem**: Cannot connect to Ollama service
**Solution**:
```bash
# Check if Ollama is running
ollama list

# Start Ollama service
ollama serve

# Verify model is installed
ollama pull deepseek-r1:14b
```

#### 2. PDF Processing Fails
**Problem**: Error processing PDF files
**Solutions**:
- Ensure PDF is not password-protected
- Check file size (max 50MB)
- Verify PDF is not corrupted
- Try a different PDF file

#### 3. Memory Issues
**Problem**: Application runs out of memory
**Solutions**:
- Reduce `CHUNK_SIZE` in configuration
- Process smaller PDF files
- Restart the application
- Increase system RAM

#### 4. Slow Response Times
**Problem**: AI responses are slow
**Solutions**:
- Use a smaller/faster model
- Reduce `SIMILARITY_SEARCH_K`
- Optimize chunk size
- Check system resources

### Debug Mode

Enable debug logging by setting:
```env
LOG_LEVEL=DEBUG
```

### Performance Optimization

1. **Model Selection**: Use smaller models for faster responses
2. **Chunk Size**: Optimize based on document type
3. **Search Parameters**: Adjust similarity search parameters
4. **Caching**: Enable caching for repeated queries

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Developer

**John Evans Okyere**
- Email: [contact@johnevans.dev](mailto:contact@johnevans.dev)
- GitHub: [@johnevans](https://github.com/johnevans)
- LinkedIn: [John Evans Okyere](https://linkedin.com/in/johnevans)

---

## 🙏 Acknowledgments

- **Ollama Team** for the excellent local LLM platform
- **LangChain** for the comprehensive AI framework
- **Streamlit** for the amazing web app framework
- **Open Source Community** for the various libraries and tools

---

## 🔄 Version History

### v1.0.0 (Current)
- Initial release
- Full RAG implementation
- Modern UI/UX
- Comprehensive documentation
- Production-ready features

### Roadmap
- [ ] Multi-document chat support
- [ ] Advanced analytics dashboard
- [ ] API endpoint exposure
- [ ] Docker containerization
- [ ] Cloud deployment guides
- [ ] Mobile app development

---

*For more information, please refer to the [documentation](docs/) or contact the developer.*

























# VexaAI RAG Chat PDF

A modern web application that enables intelligent conversations with PDF documents using Retrieval-Augmented Generation (RAG) technology. Built with FastAPI backend and React frontend, VexaAI allows users to upload PDF documents and chat with them naturally using AI-powered responses.

## Features

### Core Functionality
- **PDF Document Processing**: Upload and parse PDF documents with automatic text extraction
- **Intelligent Chat Interface**: Natural language conversations with document content
- **Vector Search**: Semantic similarity search using embeddings for accurate context retrieval
- **Multi-Document Support**: Manage and chat with multiple PDF documents
- **Session Management**: Persistent chat sessions with message history

### AI Capabilities
- **Multiple LLM Support**: Compatible with OpenAI GPT, Anthropic Claude, and X.AI Grok models
- **Flexible Embedding Providers**: Support for OpenAI and Cohere embeddings
- **Context-Aware Responses**: Answers include source citations from relevant document sections
- **Advanced RAG Pipeline**: Sophisticated retrieval and generation workflow

### User Experience
- **Modern React Frontend**: Beautiful, responsive UI with dark/light theme support
- **Real-time Chat**: Live messaging with typing indicators and smooth animations
- **Authentication System**: Secure user registration and login with JWT tokens
- **File Management**: Easy PDF upload with progress tracking and status monitoring
- **Mobile Responsive**: Works seamlessly across desktop, tablet, and mobile devices

## Technology Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **Supabase**: PostgreSQL database with real-time capabilities
- **Vector Database**: Efficient similarity search with pgvector extension
- **LangChain**: LLM integration and document processing
- **Pydantic**: Data validation and serialization
- **JWT Authentication**: Secure user session management

### Frontend
- **React 18**: Modern React with hooks and context
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client for API communication
- **React Router**: Client-side routing
- **React Hot Toast**: Beautiful notification system

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL with pgvector extension
- Supabase account (or local PostgreSQL setup)

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/vexaai-rag-chat-pdf.git
   cd vexaai-rag-chat-pdf/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Required environment variables**
   ```bash
   # Database
   DATABASE_URL=your_postgres_url
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   
   # Authentication
   JWT_SECRET=your_jwt_secret_key
   
   # AI Configuration
   OPENAI_API_KEY=your_openai_key
   # OR
   CLAUDE_API_KEY=your_claude_key
   # OR  
   GROK_API_KEY=your_grok_key
   
   # CORS
   CORS_ORIGINS=http://localhost:3000
   ```

6. **Start the backend**
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd ../frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Environment configuration**
   ```bash
   echo "REACT_APP_API_URL=http://localhost:8000/api" > .env
   ```

4. **Start the frontend**
   ```bash
   npm start
   ```

### Database Setup

Run the database schema setup SQL (found in `backend/app/database.py`) via Supabase dashboard or your PostgreSQL client.

## Configuration

### LLM Provider Configuration

Choose your preferred LLM provider in the backend `.env` file:

```bash
# OpenAI (default)
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4-turbo-preview

# Anthropic Claude
LLM_PROVIDER=claude
CLAUDE_API_KEY=your_key
CLAUDE_MODEL=claude-3-sonnet-20240229

# X.AI Grok
LLM_PROVIDER=grok
GROK_API_KEY=your_key
GROK_MODEL=grok-beta
```

### Embedding Provider Configuration

```bash
# OpenAI Embeddings (default)
EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# Cohere Embeddings
EMBEDDING_PROVIDER=cohere
COHERE_API_KEY=your_key
COHERE_EMBEDDING_MODEL=embed-english-v3.0
```

## Project Structure

```
vexaai-rag-chat-pdf/
├── backend/
│   ├── app/
│   │   ├── services/          # Business logic services
│   │   ├── models.py          # Pydantic models
│   │   ├── database.py        # Database configuration
│   │   ├── config.py          # Application settings
│   │   └── middleware/        # Custom middleware
│   ├── main.py               # FastAPI application entry point
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── contexts/         # React contexts
│   │   ├── pages/           # Page components
│   │   ├── services/        # API services
│   │   └── App.tsx          # Main React component
│   ├── public/              # Static files
│   └── package.json         # Node.js dependencies
└── README.md
```

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

### Search
- `POST /api/search` - Vector similarity search

## Development

### Backend Development

1. **Install development dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Run tests**
   ```bash
   pytest
   ```

3. **Code formatting**
   ```bash
   black .
   isort .
   ```

4. **Type checking**
   ```bash
   mypy .
   ```

### Frontend Development

1. **Start development server**
   ```bash
   npm start
   ```

2. **Build for production**
   ```bash
   npm run build
   ```

3. **Run tests**
   ```bash
   npm test
   ```

4. **Code formatting**
   ```bash
   npm run format
   ```

## Deployment

### Backend Deployment

1. **Docker deployment**
   ```bash
   docker build -t vexaai-backend .
   docker run -p 8000:8000 vexaai-backend
   ```

2. **Environment setup for production**
   - Set `ENVIRONMENT=production`
   - Use strong JWT secrets
   - Configure proper CORS origins
   - Set up SSL certificates

### Frontend Deployment

1. **Build for production**
   ```bash
   npm run build
   ```

2. **Deploy to hosting provider**
   - Vercel, Netlify, or AWS S3
   - Update `REACT_APP_API_URL` to production backend URL

## Usage

1. **Register/Login**: Create an account or sign in
2. **Upload PDF**: Click "Upload PDF" and select your document
3. **Start Chatting**: Ask questions about your document content
4. **Manage Sessions**: Create multiple chat sessions for different documents
5. **View Sources**: AI responses include citations from relevant document sections

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, email support@vexaai.com or create an issue on GitHub.

## Acknowledgments

- Built with ❤️ by John Evans Okyere
- Powered by modern AI and web technologies
- Special thanks to the open-source community

---

**VexaAI RAG Chat PDF** - Making document interaction intelligent and intuitive.