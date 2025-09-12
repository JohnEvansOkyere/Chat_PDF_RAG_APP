"""
UI Components Module for VexaAI RAG Chat PDF Application
Handles custom UI elements and styling
Developed by: John Evans Okyere
"""
import streamlit as st
from datetime import datetime
import base64

class UIComponents:
    """Custom UI components for the application"""
    
    def __init__(self):
        """Initialize UI components"""
        self.brand_color = "#1f77b4"
        self.secondary_color = "#ff7f0e"
        self.background_color = "#f8f9fa"
        self.text_color = "#2c3e50"
    
    def load_custom_css(self):
        """Load custom CSS styling"""
        css = """
        <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
        
        /* Main app styling */
        .main {
            font-family: 'Poppins', sans-serif;
        }
        
        /* Header styling */
        .vexaai-header {
            background: linear-gradient(135deg, #1f77b4, #ff7f0e);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .vexaai-title {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .vexaai-subtitle {
            font-size: 1.2rem;
            font-weight: 300;
            margin-top: 0.5rem;
            opacity: 0.9;
        }
        
        .developer-info {
            font-size: 0.9rem;
            margin-top: 1rem;
            opacity: 0.8;
        }
        
        /* Sidebar styling */
        .sidebar-header {
            background: linear-gradient(135deg, #667eea, #764ba2);
            padding: 1.5rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .sidebar-title {
            font-size: 1.5rem;
            font-weight: 600;
            margin: 0;
        }
        
        /* Card styling */
        .info-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            margin-bottom: 1rem;
            border-left: 4px solid #1f77b4;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 0.5rem;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            margin: 0;
        }
        
        .metric-label {
            font-size: 0.9rem;
            opacity: 0.8;
            margin-top: 0.25rem;
        }
        
        /* Welcome screen styling */
        .welcome-container {
            text-align: center;
            padding: 3rem 1rem;
            background: linear-gradient(135deg, #f5f7fa, #c3cfe2);
            border-radius: 15px;
            margin: 2rem 0;
        }
        
        .welcome-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
        }
        
        .welcome-title {
            font-size: 2rem;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 1rem;
        }
        
        .welcome-text {
            font-size: 1.1rem;
            color: #7f8c8d;
            max-width: 600px;
            margin: 0 auto 2rem;
            line-height: 1.6;
        }
        
        /* Feature list styling */
        .feature-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin-top: 2rem;
        }
        
        .feature-item {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }
        
        .feature-item:hover {
            transform: translateY(-5px);
        }
        
        .feature-icon {
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        
        .feature-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #2c3e50;
        }
        
        .feature-description {
            font-size: 0.9rem;
            color: #7f8c8d;
            line-height: 1.5;
        }
        
        /* Chat message styling */
        .chat-message {
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .user-message {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            margin-left: 2rem;
        }
        
        .assistant-message {
            background: #f8f9fa;
            border-left: 4px solid #1f77b4;
            margin-right: 2rem;
        }
        
        /* Footer styling */
        .footer {
            text-align: center;
            padding: 2rem;
            background: linear-gradient(135deg, #2c3e50, #34495e);
            color: white;
            border-radius: 10px;
            margin-top: 3rem;
        }
        
        .footer-content {
            max-width: 800px;
            margin: 0 auto;
        }
        
        .footer-title {
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .footer-text {
            font-size: 0.9rem;
            opacity: 0.8;
            line-height: 1.5;
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        
        /* File uploader styling */
        .uploadedFile {
            border: 2px dashed #1f77b4;
            border-radius: 10px;
            padding: 2rem;
            text-align: center;
            background: #f8f9fa;
            margin: 1rem 0;
        }
        
        /* Progress bar styling */
        .stProgress > div > div > div {
            background: linear-gradient(135deg, #1f77b4, #ff7f0e);
        }
        
        /* Hide streamlit elements */
        .viewerBadge_container__1QSob {
            display: none !important;
        }
        
        #MainMenu {
            visibility: hidden;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .vexaai-title {
                font-size: 2rem;
            }
            
            .welcome-title {
                font-size: 1.5rem;
            }
            
            .feature-list {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    
    def render_header(self):
        """Render main application header"""
        st.markdown("""
        <div class="vexaai-header">
            <h1 class="vexaai-title">🤖 VexaAI</h1>
            <p class="vexaai-subtitle">Intelligent PDF Chat Assistant</p>
            <p class="developer-info">Developed by John Evans Okyere</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_brand_header(self):
        """Render sidebar brand header"""
        st.markdown("""
        <div class="sidebar-header">
            <h2 class="sidebar-title">🤖 VexaAI</h2>
        </div>
        """, unsafe_allow_html=True)
    
    def render_welcome_screen(self):
        """Render welcome screen when no PDF is loaded"""
        st.markdown("""
        <div class="welcome-container">
            <div class="welcome-icon">📄</div>
            <h2 class="welcome-title">Welcome to VexaAI</h2>
            <p class="welcome-text">
                Upload a PDF document to start an intelligent conversation with your content. 
                VexaAI uses advanced AI to understand and answer questions about your documents.
            </p>
            
            <div class="feature-list">
                <div class="feature-item">
                    <div class="feature-icon">📤</div>
                    <h3 class="feature-title">Easy Upload</h3>
                    <p class="feature-description">Simply drag and drop or select your PDF files</p>
                </div>
                
                <div class="feature-item">
                    <div class="feature-icon">🧠</div>
                    <h3 class="feature-title">Smart Analysis</h3>
                    <p class="feature-description">AI-powered document understanding and analysis</p>
                </div>
                
                <div class="feature-item">
                    <div class="feature-icon">💬</div>
                    <h3 class="feature-title">Natural Chat</h3>
                    <p class="feature-description">Ask questions in natural language and get precise answers</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def render_info_card(self, title: str, content: str, icon: str = "ℹ️"):
        """
        Render an information card
        
        Args:
            title: Card title
            content: Card content
            icon: Card icon (emoji)
        """
        st.markdown(f"""
        <div class="info-card">
            <h3>{icon} {title}</h3>
            <p>{content}</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_metric_card(self, value: str, label: str):
        """
        Render a metric card
        
        Args:
            value: Metric value
            label: Metric label
        """
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)
    
    def render_processing_animation(self, text: str = "Processing your PDF..."):
        """
        Render processing animation
        
        Args:
            text: Processing text to display
        """
        with st.spinner(text):
            st.markdown("""
            <div style="text-align: center; padding: 2rem;">
                <div style="font-size: 2rem; margin-bottom: 1rem;">⚡</div>
                <p>Please wait while we analyze your document...</p>
            </div>
            """, unsafe_allow_html=True)
    
    def render_success_message(self, message: str):
        """
        Render success message
        
        Args:
            message: Success message to display
        """
        st.success(f"✅ {message}")
    
    def render_error_message(self, message: str):
        """
        Render error message
        
        Args:
            message: Error message to display
        """
        st.error(f"❌ {message}")
    
    def render_info_message(self, message: str):
        """
        Render info message
        
        Args:
            message: Info message to display
        """
        st.info(f"ℹ️ {message}")
    
    def render_footer(self):
        """Render application footer"""
        st.markdown("""
        <div class="footer">
            <div class="footer-content">
                <h3 class="footer-title">VexaAI - RAG Chat PDF</h3>
                <p class="footer-text">
                    Powered by advanced AI technology for intelligent document interaction.<br>
                    Built with ❤️ by John Evans Okyere using Streamlit, LangChain, and Ollama.
                </p>
                <p class="footer-text">
                    © 2024 VexaAI. All rights reserved.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def render_chat_suggestions(self, suggestions: list):
        """
        Render suggested questions for chat
        
        Args:
            suggestions: List of suggested questions
        """
        if suggestions:
            st.markdown("### 💡 Suggested Questions")
            cols = st.columns(len(suggestions))
            
            for i, suggestion in enumerate(suggestions):
                with cols[i]:
                    if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                        return suggestion
        return None
    
    def render_pdf_preview(self, pdf_name: str, processing_time: float, stats: dict):
        """
        Render PDF processing preview
        
        Args:
            pdf_name: Name of the processed PDF
            processing_time: Time taken to process
            stats: PDF statistics
        """
        st.markdown(f"""
        <div class="info-card">
            <h3>📄 {pdf_name}</h3>
            <p><strong>Processing Time:</strong> {processing_time:.2f} seconds</p>
            <p><strong>Total Chunks:</strong> {stats.get('total_chunks', 0)}</p>
            <p><strong>Total Characters:</strong> {stats.get('total_characters', 0):,}</p>
            <p><strong>Average Chunk Size:</strong> {stats.get('average_chunk_size', 0)} characters</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_chat_stats(self, stats: dict):
        """
        Render chat statistics
        
        Args:
            stats: Chat statistics dictionary
        """
        col1, col2, col3 = st.columns(3)
        
        with col1:
            self.render_metric_card(
                str(stats.get('total_conversations', 0)),
                "Total Questions"
            )
        
        with col2:
            avg_time = stats.get('average_processing_time', 0)
            self.render_metric_card(
                f"{avg_time:.2f}s",
                "Avg Response Time"
            )
        
        with col3:
            model = stats.get('model_used', 'Unknown')
            self.render_metric_card(
                model.split(':')[0],
                "AI Model"
            )
    
    def render_upload_area(self):
        """Render custom upload area"""
        st.markdown("""
        <div class="uploadedFile">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📤</div>
            <h3>Drop your PDF here</h3>
            <p>or click to browse files</p>
        </div>
        """, unsafe_allow_html=True)
    
    def create_download_link(self, data: str, filename: str, text: str):
        """
        Create download link for data
        
        Args:
            data: Data to download
            filename: Filename for download
            text: Link text
        """
        b64 = base64.b64encode(data.encode()).decode()
        href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{text}</a>'
        return href