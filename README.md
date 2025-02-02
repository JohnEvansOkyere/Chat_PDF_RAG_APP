📄 **PDF Question-Answering Assistant** 🤖

This project enables users to upload a PDF file, extract its content, split it into smaller chunks, and leverage the LLama2 
language model to answer questions based on the content of the PDF. Built using LangChain, Streamlit, and Ollama API, this 
tool provides an efficient solution for document-based question answering.

🛠️ **Requirements**

Python 3.x
Streamlit 🖥️
LangChain 🔗
dotenv 🌱
PDFPlumber 📑
Ollama API 🔑

📦 **Installation**

To run this project locally, follow these steps:

Step 1: Install Dependencies

pip install -r requirements.txt

Note: You need to create a requirements.txt file with the following dependencies:

streamlit
langchain
langchain_community
python-dotenv
pdfplumber

Step 2: Set Up Environment Variables

Create a .env file in the project directory and add your Ollama API key:

OLLAMA_API_KEY=your_ollama_api_key

Step 3: Run the Streamlit App

After setting up your environment and dependencies, run the Streamlit app with the following command:

streamlit run app.py

Step 4: Upload PDF and Ask Questions

Open the app in your browser.

Upload a PDF file using the file uploader. 📤

Ask a question related to the content in the PDF. ❓

The app will return a concise answer based on the content of the uploaded PDF. 💬

🧑‍💻 **Code Overview**

app.py

Environment Setup: The .env file loads the Ollama API key for model interaction. 🔑

PDF Upload: Users can upload PDFs using the st.file_uploader() function. 📥

Document Loading: The PDF content is extracted using PDFPlumberLoader for processing. 📃

Text Splitting: The document is split into smaller, manageable chunks using RecursiveCharacterTextSplitter. 🧩

Indexing: Text chunks are indexed using InMemoryVectorStore for efficient retrieval. 📚

Model Interaction: The Ollama LLM is used to generate responses to user queries based on document content. 🧠

Question Answering: The answer_question() function combines relevant document content and provides an answer using a ChatPromptTemplate. 🔍

🚀 **Features**

PDF Upload: Upload PDFs to extract and process content with ease. 📂

Text Splitting: Breaks documents into manageable chunks to improve retrieval and performance. ✂️

Question Answering: Get concise answers based on the PDF's content with LLama2. 🤖

Vector Store: Use vector stores for fast and efficient document content retrieval. 📈

⚙️ **Future Improvements**

Multi-Document Support: Handle multiple PDFs and improve content retrieval. 📄📄

Advanced Error Handling: Enhance user experience by adding better error handling. ⚠️

Customizable Models: Allow users to select between various models for answering questions. ⚙️
