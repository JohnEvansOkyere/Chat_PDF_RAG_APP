PDF Question-Answering Assistant
This project allows users to upload a PDF file, extract its content, break it into smaller chunks, and use a language model (LLama2) to answer questions based on the content of the PDF. It leverages LangChain for integration with various LLMs and vector stores.

Requirements
Python 3.x
Streamlit
LangChain
dotenv
PDFPlumber
Ollama API
Installation
To run this project locally, follow these steps:

Step 1: Install Dependencies
bash
Copy
Edit
pip install -r requirements.txt
Note: You need to create a requirements.txt file with the following dependencies:

text
Copy
Edit
streamlit
langchain
langchain_community
python-dotenv
pdfplumber
Step 2: Set Up Environment Variables
Create a .env file in the project directory and add your Ollama API key:

env
Copy
Edit
OLLAMA_API_KEY=your_ollama_api_key
Step 3: Run the Streamlit App
After setting up your environment and dependencies, run the Streamlit app with the following command:

bash
Copy
Edit
streamlit run app.py
Step 4: Upload PDF and Ask Questions
Open the app in your browser.
Upload a PDF file using the file uploader.
Ask a question related to the content in the PDF.
The app will return a concise answer based on the content of the uploaded PDF.
Code Explanation
app.py
Environment Setup: The dotenv library loads the Ollama API key from a .env file.
PDF Upload: Users can upload a PDF using st.file_uploader().
Document Loading: The PDF is loaded and processed using PDFPlumberLoader to extract the text.
Text Splitting: The document is split into smaller chunks using RecursiveCharacterTextSplitter to improve context retrieval for the LLM.
Indexing: Chunks of the document are indexed using InMemoryVectorStore to make similarity searches efficient.
Model Interaction: The Ollama LLM is used to generate responses to user queries based on the context from the PDF.
Question Answering: The answer_question() function retrieves relevant content from the document chunks and provides an answer using the ChatPromptTemplate.
Streamlit UI
File Upload: Users upload a PDF file.
Chat Input: Users enter questions that are answered based on the content of the PDF.
Features
PDF Upload: Allows users to upload PDFs to extract content.
Text Splitting: Divides the content into manageable chunks for efficient retrieval.
Question Answering: Users can ask questions, and the assistant will provide concise answers based on the PDF content.
Vector Store: Efficient search and retrieval of relevant document sections using vector stores.
Future Improvements
Multi-Document Support: Extend the functionality to handle multiple PDFs.
Advanced Error Handling: Improve handling of edge cases and user input errors.
Customizable Models: Allow users to choose between different models for question answering.

Build by John Evans Okyere
Data Scientist/ ML Engineer