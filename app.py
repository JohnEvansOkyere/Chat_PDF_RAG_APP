import os
import time
from dotenv import load_dotenv

import streamlit as st
from langchain_ollama.llms import OllamaLLM
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import InMemoryVectorStore
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters.character import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()


template = """
You are an assistant for question-answering tasks. Use only the provided context to answer the question. 
If the context does not contain enough information to answer the question, say "I don't know." Do not make up answers or use external knowledge. 
Keep your response concise and limit it to a maximum of three sentences.

    Question : {question}
    Context : {context}
    Answer: 
"""

pdf_directory = './pdf/'

ollama_API_key = os.getenv("OLLAMA_API_KEY")


model = OllamaLLM(model=ollama_API_key) 
embeddings = OllamaEmbeddings(model = ollama_API_key)  # Embedding is converting text to vectors
vector_store = InMemoryVectorStore(embeddings)


# Uploading PDF
def upload_pdf(file):
    with open(pdf_directory + file.name, "wb") as f:
        f.write(file.getbuffer())
    

# Loading PDF
def load_pdf(file_path):
    loader = PDFPlumberLoader(file_path)
    documents = loader.load()

    return documents


# Splitting into smaller chunks(units)  
def split_text(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1000,
        chunk_overlap = 200,
        add_start_index = True
    )

    return text_splitter.split_documents(documents)


# Index the documents
def index_docs(documents):
    vector_store.add_documents(documents)

# Retrieving data from the vector store(It's like writing a query)
def retrive_doc(query):
    return vector_store.similarity_search(query, K=5)


# Answer the questions asked
def answer_question(question,  documents):
    context = "\n\n".join([doc.page_content for doc in documents])
    prompt = ChatPromptTemplate.from_template(template)

    chain = prompt | model

    return chain.invoke({"question": question, "context": context})


# Streamlit UI
uploaded_file = st.file_uploader("Upload_PDF", 
                                 type="pdf",
                                 accept_multiple_files=False)


# Checking'
if uploaded_file:
    upload_pdf(uploaded_file)     #Upload file
    documents = load_pdf(pdf_directory + uploaded_file.name) # Save file to documents
    chunked_documents = split_text(documents) # Break it into chunks
    index_docs(chunked_documents) # Index the position of the documents


    # Create a chat
    question = st.chat_input()

    if question:
        st.chat_message("user").write(question)
        related_documents = retrive_doc(question)
        answer = answer_question(question, related_documents)
        st.chat_message("assistant").write(answer)


        