import os
import json
import logging
import google.generativeai as genai
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import PGVector
from ai_engine.models import Document

# Set up logging for debugging
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
# We use the environment variables from your docker-compose.yml
DB_USER = os.environ.get("POSTGRES_USER", "admin")
DB_PASS = os.environ.get("POSTGRES_PASSWORD", "devpassword")
DB_HOST = os.environ.get("POSTGRES_HOST", "postgres") 
DB_PORT = os.environ.get("POSTGRES_PORT", "5432")
DB_NAME = os.environ.get("POSTGRES_DB", "library_db")

# Construct the connection string using the 'postgres' hostname
CONNECTION_STRING = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

COLLECTION_NAME = "rag_collection"

def get_embedding_model():
    """Helper to get the embedding model with the API key."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is missing! Check your .env file.")
    
    return GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004", 
        google_api_key=api_key
    )

# --- 1. THE INGESTION ENGINE ---
def ingest_document(doc_id):
    """Reads a PDF and saves it to the Vector Database."""
    try:
        doc = Document.objects.get(id=doc_id)
        file_path = doc.file.path
        logger.info(f"📄 Processing: {doc.title}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found at {file_path}")

        # Load and Split
        loader = PyPDFLoader(file_path)
        raw_docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(raw_docs)
        
        # Save to Vector DB
        PGVector.from_documents(
            embedding=get_embedding_model(),
            documents=chunks,
            collection_name=COLLECTION_NAME,
            connection_string=CONNECTION_STRING,
            pre_delete_collection=False
        )
        
        doc.processed = True
        doc.save()
        logger.info("✅ Document indexed successfully.")
        return True

    except Exception as e:
        logger.error(f"❌ Ingestion failed: {str(e)}")
        return False

# --- 2. THE VERIFICATION ENGINE ---
def get_verified_answer(query):
    """Retrieves context and generates a verified response using Gemini JSON mode."""
    try:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return {"answer": "System Error: Missing API Key", "faithfulness_score": 0}

        # 1. RETRIEVAL
        vector_db = PGVector(
            collection_name=COLLECTION_NAME,
            connection_string=CONNECTION_STRING,
            embedding_function=get_embedding_model(),
        )
        
        docs = vector_db.similarity_search(query, k=3)
        if not docs:
            return {
                "answer": "I couldn't find any relevant information in the uploaded documents.",
                "faithfulness_score": 0.0,
                "explanation": "No matching vectors found in the database.",
                "source_citation": "None"
            }

        context = "\n\n".join([f"[Source: Page {d.metadata.get('page', 'Unknown')}] {d.page_content}" for d in docs])

        # 2. GENERATION WITH JSON MODE
        genai.configure(api_key=api_key)
        
        # CRITICAL CHANGE: Enforce JSON response type
        generation_config = {
            "temperature": 0.0,
            "response_mime_type": "application/json"
        }
        
        model = genai.GenerativeModel('gemini-1.5-flash', generation_config=generation_config)

        prompt = f"""
        You are VeriRag, a strictly faithful AI Librarian.
        Analyze the following context and answer the user's question.
        
        CONTEXT:
        {context}
        
        QUESTION: 
        {query}
        
        INSTRUCTIONS:
        1. Answer ONLY using the provided context.
        2. If the answer is not in the context, return score 0.
        3. You must provide a "faithfulness_score" between 0.0 and 1.0 (1.0 = perfect evidence).
        4. "source_citation" must be a direct quote from the text.
        
        Output valid JSON with this schema:
        {{
            "answer": "string",
            "faithfulness_score": float,
            "explanation": "string",
            "source_citation": "string"
        }}
        """

        response = model.generate_content(prompt)
        
        # 3. PARSE (No more regex hacking needed)
        return json.loads(response.text)

    except Exception as e:
        logger.error(f"❌ Verification failed: {str(e)}")
        return {
            "answer": "I encountered an error while processing your request.",
            "faithfulness_score": 0,
            "explanation": f"Internal Error: {str(e)}",
            "source_citation": "System Error"
        }