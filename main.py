# main.py
# Full corrected main with persistent managers, vector-store restore, and robust chat flow

import os
import time
import uuid
import tempfile
import streamlit as st
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Import custom modules
from src.config import Config
from src.pdf_processor import PDFProcessor
from src.vector_store import VectorStoreManager
from src.chat_engine import ChatEngine
from src.session_manager import SessionManager
from src.ui_components import UIComponents
from src.utils import create_directories, log_interaction

# Page configuration
st.set_page_config(
    page_title="VexaAI - RAG Chat PDF",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/johnevans/vexaai-rag',
        'Report a bug': 'https://github.com/johnevans/vexaai-rag/issues',
        'About': "VexaAI RAG Chat PDF - Developed by John Evans Okyere"
    }
)


class RAGChatApp:
    """Main RAG Chat Application Class"""

    def __init__(self):
        """Initialize the RAG Chat Application"""
        self.config = Config()
        # If your Config has validate_config, call it; if not, it's fine
        if hasattr(self.config, "validate_config"):
            try:
                self.config.validate_config()
            except Exception:
                # don't fail constructor for minor config validation errors
                pass

        # Persist essential managers in session_state so they survive reruns
        if "pdf_processor" not in st.session_state:
            st.session_state.pdf_processor = PDFProcessor(self.config)
        if "vector_store_manager" not in st.session_state:
            st.session_state.vector_store_manager = VectorStoreManager(self.config)
        if "chat_engine" not in st.session_state:
            # ensure vector_store_manager is passed from session_state
            st.session_state.chat_engine = ChatEngine(self.config, st.session_state.vector_store_manager)
        if "session_manager" not in st.session_state:
            st.session_state.session_manager = SessionManager()
        if "ui_components" not in st.session_state:
            st.session_state.ui_components = UIComponents()

        # Assign instance variables for easier access
        self.pdf_processor: PDFProcessor = st.session_state.pdf_processor
        self.vector_store_manager: VectorStoreManager = st.session_state.vector_store_manager
        self.chat_engine: ChatEngine = st.session_state.chat_engine
        self.session_manager: SessionManager = st.session_state.session_manager
        self.ui_components: UIComponents = st.session_state.ui_components

        # Create necessary directories used by your app
        create_directories()

    def initialize_session_state(self):
        """Initialize Streamlit session state variables via SessionManager"""
        # Use the session manager initializer for consistency
        try:
            self.session_manager.initialize_session()
        except Exception:
            # fallback to basic initialization if session_manager fails
            if "session_id" not in st.session_state:
                st.session_state.session_id = str(uuid.uuid4())
            if "messages" not in st.session_state:
                st.session_state.messages = []
            if "processed_documents" not in st.session_state:
                st.session_state.processed_documents = []
            if "vector_store_ready" not in st.session_state:
                st.session_state.vector_store_ready = False
            if "pdf_processed" not in st.session_state:
                st.session_state.pdf_processed = False
            if "processing_time" not in st.session_state:
                st.session_state.processing_time = 0

        # Ensure keys exist (idempotent)
        if "processed_documents" not in st.session_state:
            st.session_state.processed_documents = []
        if "vector_store_ready" not in st.session_state:
            st.session_state.vector_store_ready = False
        if "pdf_processed" not in st.session_state:
            st.session_state.pdf_processed = False
        if "processing_time" not in st.session_state:
            st.session_state.processing_time = 0
        if "messages" not in st.session_state:
            st.session_state.messages = []

    def restore_vector_store_if_needed(self):
        """
        If session has processed_documents but the in-memory vector store is empty,
        re-index documents into the current VectorStoreManager instance.
        """
        try:
            docs = st.session_state.get("processed_documents", None)
            if docs and not self.vector_store_manager.is_ready():
                # Re-index session documents into the manager
                # index_documents should handle clearing/adding
                ok = self.vector_store_manager.index_documents(docs)
                st.session_state.vector_store_ready = bool(ok and self.vector_store_manager.is_ready())
                st.session_state.pdf_processed = st.session_state.vector_store_ready
                self.vector_store_manager.logger.info("Restored vector store from session documents")
        except Exception as e:
            st.session_state.vector_store_ready = False
            # log error but don't raise
            try:
                self.vector_store_manager.logger.error(f"Failed to restore vector store: {e}")
            except Exception:
                pass

    def handle_pdf_upload(self, uploaded_file):
        """Handle PDF file upload and processing (expects streamlit uploaded_file)"""
        if uploaded_file is None:
            return False

        # If it's the same filename and already processed, skip reprocessing
        is_new_file = st.session_state.get("current_pdf") != uploaded_file.name

        if is_new_file:
            # reset state for new upload
            st.session_state.current_pdf = uploaded_file.name
            st.session_state.pdf_processed = False
            st.session_state.messages = []
            st.session_state.vector_store_ready = False
            st.session_state.processed_documents = []

            with st.spinner(f"🔄 Processing {uploaded_file.name}..."):
                start_time = time.time()
                tmp_file_path = None
                try:
                    # Save uploaded file to a temp file path (pdf_processor expects a path)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(uploaded_file.getbuffer())
                        tmp_file_path = tmp_file.name

                    # validate and load
                    if not self.pdf_processor.validate_pdf_file(tmp_file_path):
                        raise ValueError("Invalid PDF file")

                    # load and split
                    documents = self.pdf_processor.load_pdf(tmp_file_path)
                    chunked_documents = self.pdf_processor.split_documents(documents)
                    if not chunked_documents:
                        raise ValueError("No content could be extracted from the PDF")

                    # test embeddings
                    if not self.vector_store_manager.test_embeddings():
                        raise ValueError("Embeddings test failed - check Ollama connection")

                    # index into vector store
                    index_success = self.vector_store_manager.index_documents(chunked_documents)
                    if not index_success:
                        raise ValueError("Failed to index documents in vector store")

                    # final readiness checks
                    if not self.vector_store_manager.is_ready():
                        raise ValueError("Vector store is not ready after indexing")

                    if not self.chat_engine.test_llm_connection():
                        raise ValueError("LLM connection test failed - check Ollama service")

                    # cleanup tmp file
                    try:
                        os.unlink(tmp_file_path)
                    except Exception:
                        pass

                    # update session state
                    processing_time = time.time() - start_time
                    st.session_state.processing_time = processing_time
                    st.session_state.pdf_processed = True
                    st.session_state.vector_store_ready = True
                    st.session_state.processed_documents = chunked_documents

                    # small extra safety: re-check manager readiness
                    if self.vector_store_manager.is_ready():
                        st.session_state.vector_store_ready = True

                    # feedback to user
                    doc_stats = self.pdf_processor.get_document_stats(chunked_documents)
                    success_msg = f"""✅ **PDF processed successfully!**

📊 **Processing Summary:**
- **Time:** {processing_time:.2f} seconds  
- **Pages:** {doc_stats.get('total_pages', 'N/A')}
- **Chunks:** {doc_stats.get('total_chunks', 0)}
- **Words:** {doc_stats.get('total_words', 0):,}
- **Characters:** {doc_stats.get('total_characters', 0):,}

🎯 **Ready to chat!** Ask me anything about your document."""
                    st.success(success_msg)

                    # show suggested questions
                    with st.expander("💡 Suggested Questions", expanded=False):
                        suggestions = self.chat_engine.get_suggested_questions("")
                        for i, suggestion in enumerate(suggestions, 1):
                            st.write(f"{i}. {suggestion}")

                    return True

                except Exception as e:
                    # cleanup temp file if exists
                    if tmp_file_path and os.path.exists(tmp_file_path):
                        try:
                            os.unlink(tmp_file_path)
                        except Exception:
                            pass

                    # reset session state and show debug info
                    st.session_state.pdf_processed = False
                    st.session_state.vector_store_ready = False
                    st.session_state.processed_documents = []
                    st.error(f"❌ Error processing PDF: {e}")

                    with st.expander("🔍 Debug Information", expanded=False):
                        st.write("**Error Details:**")
                        st.code(str(e))
                        st.write("**Troubleshooting Steps:**")
                        st.write("1. Ensure Ollama is running: `ollama serve`")
                        st.write(f"2. Verify model is installed: `ollama pull {self.config.MODEL_NAME}`")
                        st.write("3. Check PDF file is not corrupted or password-protected")
                        st.write("4. Try a smaller PDF file (< 10MB)")

                    return False

        # return final state
        return bool(st.session_state.get("pdf_processed")) and bool(st.session_state.get("vector_store_ready"))

    def handle_chat_interaction(self, question: str):
        """Handle chat interaction with the PDF"""
        # First, ensure vector store is present (restore if needed)
        self.restore_vector_store_if_needed()

        # Quick readiness check
        vector_store_ready_flag = bool(st.session_state.get("vector_store_ready", False))
        manager_ready = self.vector_store_manager.is_ready()
        processed_docs_len = len(st.session_state.get("processed_documents", []))

        if manager_ready:
            st.session_state.vector_store_ready = True
            vector_store_ready_flag = True

        if not (vector_store_ready_flag and manager_ready and processed_docs_len > 0):
            st.error("❌ Please upload and process a PDF document first before asking questions.")
            return

        if not question or not question.strip():
            st.error("❌ Please enter a question to get started.")
            return

        # Append user message via session manager (keeps logs and metadata)
        try:
            self.session_manager.add_message("user", question)
        except Exception:
            # fallback
            st.session_state.messages.append({"role": "user", "content": question})

        # Display user message immediately
        with st.chat_message("user"):
            st.write(question)

        # Ask LLM / ChatEngine and append assistant message
        with st.spinner("🤔 Thinking..."):
            try:
                # Defensive: ensure get_response returns string
                response = self.chat_engine.get_response(question)
                if response is None:
                    response = "⚠️ No response received from LLM."

            except Exception as e:
                # Ensure error is reported to the user and saved to history
                response = f"❌ Error generating response: {e}"

            # Save assistant message
            try:
                self.session_manager.add_message("assistant", response)
            except Exception:
                st.session_state.messages.append({"role": "assistant", "content": response})

            # Display assistant response
            with st.chat_message("assistant"):
                st.write(response)

            # Log the interaction (try/catch to avoid crashing app on logging errors)
            try:
                log_interaction(
                    session_id=st.session_state.get("session_id", "unknown"),
                    pdf_name=st.session_state.get("current_pdf", "unknown"),
                    question=question,
                    response=response
                )
            except Exception:
                pass

    def render_chat_interface(self):
        """Render the chat interface"""
        # Show previous messages from session state
        messages = self.session_manager.get_messages() if hasattr(self.session_manager, "get_messages") else st.session_state.get("messages", [])
        for msg in messages:
            role = msg.get("role", "assistant")
            content = msg.get("content", "") if isinstance(msg, dict) else str(msg)
            with st.chat_message(role):
                st.write(content)

        # If processed and ready, show active input; otherwise, disabled input
        if st.session_state.get("pdf_processed") and st.session_state.get("vector_store_ready"):
            prompt = st.chat_input("💬 Ask a question about your PDF...")
            if prompt:
                # Do not call st.rerun(); Streamlit will rerun automatically after submission
                self.handle_chat_interaction(prompt)
        else:
            st.chat_input("💬 Upload a PDF first to start chatting...", disabled=True)

    def render_sidebar(self):
        """Render the sidebar with controls and information"""
        with st.sidebar:
            self.ui_components.render_brand_header()

            st.markdown("---")
            st.markdown("### 📄 Upload PDF Document")

            uploaded_file = st.file_uploader(
                "Choose a PDF file",
                type="pdf",
                accept_multiple_files=False,
                help=f"Upload a PDF document (max {getattr(self.config,'MAX_FILE_SIZE_MB', 50)}MB)"
            )

            if uploaded_file:
                self.handle_pdf_upload(uploaded_file)

            st.markdown("---")
            st.markdown("### 🟢 System Status")

            if st.button("🔄 Test Connections", use_container_width=True):
                with st.spinner("Testing..."):
                    embeddings_ok = self.vector_store_manager.test_embeddings()
                    llm_ok = self.chat_engine.test_llm_connection()
                    vs_ok = self.vector_store_manager.is_ready()

                    # Persist status in session state
                    st.session_state.vector_store_ready = bool(vs_ok)
                    st.session_state.pdf_processed = st.session_state.vector_store_ready

                    st.write("**Embeddings:**", "✅ OK" if embeddings_ok else "❌ Failed")
                    st.write("**LLM:**", "✅ OK" if llm_ok else "❌ Failed")
                    st.write("**Vector Store:**", "✅ Ready" if vs_ok else "❌ Not Ready")

            st.markdown("---")
            st.markdown("### 🎛️ Chat Controls")

            if st.button("🗑️ Clear Chat History", use_container_width=True):
                # Clear session messages and engine history
                try:
                    st.session_state.messages = []
                except Exception:
                    st.session_state["messages"] = []
                try:
                    self.chat_engine.clear_conversation_history()
                except Exception:
                    pass
                # let Streamlit rerun naturally

            if st.button("🔄 Reset Session", use_container_width=True):
                try:
                    self.vector_store_manager.clear_index()
                except Exception:
                    pass
                # Clear only keys we manage to avoid losing persisted managers
                keys_to_keep = {"vector_store_manager", "chat_engine", "pdf_processor", "session_manager", "ui_components"}
                for key in list(st.session_state.keys()):
                    if key not in keys_to_keep:
                        del st.session_state[key]
                # ensure flags reset
                st.session_state.vector_store_ready = False
                st.session_state.pdf_processed = False

            st.markdown("---")
            st.markdown("### ⚙️ Model Settings")
            st.info(f"**Model:** {getattr(self.config,'MODEL_NAME','unknown')}")
            st.info(f"**Embedding:** {getattr(self.config,'EMBEDDING_MODEL','unknown')}")
            st.info(f"**Temperature:** {getattr(self.config,'TEMPERATURE','unknown')}")

            # Session stats
            if st.session_state.get("messages"):
                st.markdown("---")
                st.markdown("### 📊 Session Stats")
                user_messages = [m for m in st.session_state.get("messages", []) if m.get("role") == "user"]
                assistant_messages = [m for m in st.session_state.get("messages", []) if m.get("role") == "assistant"]

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total", len(st.session_state.get("messages", [])))
                    st.metric("Questions", len(user_messages))
                with col2:
                    st.metric("Responses", len(assistant_messages))
                    if st.session_state.get("processed_documents"):
                        st.metric("Doc Chunks", len(st.session_state.get("processed_documents", [])))

    def render_main_content(self):
        """Render the main content area"""
        if not st.session_state.get("pdf_processed", False):
            self.ui_components.render_welcome_screen()
        else:
            st.markdown(f"### 💬 Chat with {st.session_state.get('current_pdf','document')}")
            if not st.session_state.get("vector_store_ready", False):
                st.warning("⚠️ Vector store not ready. Please re-upload your PDF.")
                # still render chat interface (input will be disabled)
            self.render_chat_interface()

    def run(self):
        """Main application entry point"""
        try:
            # UI
            self.ui_components.load_custom_css()

            # session state
            self.initialize_session_state()

            # attempt to restore index if necessary
            self.restore_vector_store_if_needed()

            # layout
            self.render_sidebar()
            self.render_main_content()
            self.ui_components.render_footer()

        except Exception as e:
            st.error(f"❌ Application Error: {e}")
            with st.expander("🔍 Debug Information"):
                st.write(str(e))


def main():
    """Application entry point"""
    try:
        app = RAGChatApp()
        app.run()
    except Exception as e:
        # show a non-blocking error so developer can see it
        st.error(f"❌ Critical Application Error: {e}")


if __name__ == "__main__":
    main()
