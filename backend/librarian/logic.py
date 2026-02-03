import os
import json
import google.generativeai as genai
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import PGVector

# --- CONFIGURATION ---
# Ensure this matches your Docker/Local Postgres setup
CONNECTION_STRING = "postgresql+psycopg2://admin:devpassword@localhost:5432/library_db"
COLLECTION_NAME = "pdf_knowledge"

# --- 1. THE INGESTION ENGINE (The "Reading" Part) ---
def process_pdf_to_vector_db(file_path):
    """Takes a PDF file path and saves its contents to the Vector DB."""
    try:
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        
        # Split into chunks with overlap for context preservation
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(docs)
        
        embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        
        PGVector.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection_name=COLLECTION_NAME,
            connection_string=CONNECTION_STRING,
        )
        return {"status": "success", "message": f"Indexed {len(chunks)} chunks from the PDF."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- 2. THE VERIFICATION ENGINE (The "Answering" Part) ---
def get_verified_answer(query):
    """Searches the DB, generates an answer, and verifies it."""
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        
        # Connect to the existing vector store
        vector_db = PGVector(
            collection_name=COLLECTION_NAME,
            connection_string=CONNECTION_STRING,
            embedding_function=embeddings,
        )

        # RETRIEVAL: Find top 3 relevant context pieces
        docs = vector_db.similarity_search(query, k=3)
        context = "\n---\n".join([doc.page_content for doc in docs])

        # VERIFICATION PROMPT: The core of Project 46
        prompt = f"""
        You are a strictly faithful AI Librarian. Use ONLY the provided context to answer the user's question.
        
        Context from PDF:
        {context}
        
        User Question: {query}
        
        Your response must be in this JSON format:
        {{
            "answer": "Your clear answer here.",
            "faithfulness_score": 0.0 to 1.0,
            "explanation": "Briefly explain why this score was given.",
            "source_citation": "Direct quote or page/paragraph reference."
        }}
        """

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        # Clean the response in case Gemini adds ```json markdown blocks
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)

    except Exception as e:
        return {
            "answer": "I encountered an error while processing your request.",
            "faithfulness_score": 0,
            "explanation": str(e),
            "source_citation": "N/A"
        }