DeepSeek RAG with Streamlit
This project implements a Retrieval-Augmented Generation (RAG) system using DeepSeek R1 (14B) via Ollama and LangChain. It allows users to upload PDFs, index their content, and retrieve answers based on the document context.

Features
Upload & Process PDFs: Extracts text and splits it into chunks for indexing.
Vector Storage & Retrieval: Uses an in-memory vector store for similarity search.
Chat Interface: Users can ask questions, and the model responds based on document content.
Installation

git clone https://github.com/JohnEvansOkyere/Chat_PDF_RAG_APP 
cd deepseek_rag  
pip install -r requirements.txt  
Usage
Pull the model:

ollama pull deepseek-r1:14b
Run the Streamlit app:

streamlit run app.py
Upload a PDF and start asking questions!
Dependencies
Python
Streamlit
LangChain
Ollama
PDFPlumber

Notes
Ensure Ollama is installed and running before launching the app.