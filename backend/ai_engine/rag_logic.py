import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import PGVector
from ai_engine.models import Document

# Database Connection String
CONNECTION_STRING = "postgresql+psycopg2://admin:devpassword@postgres:5432/ragdb"

def get_embedding_model():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is missing!")
    
    # 004 is the model that works for you
    return GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004", 
        google_api_key=api_key
    )

def ingest_document(doc_id):
    """
    Reads a PDF and saves it to the Vector Database.
    """
    try:
        # 1. Get the Document
        doc = Document.objects.get(id=doc_id)
        file_path = doc.file.path
        print(f"📄 Processing: {doc.title}")

        # 2. Load and Split
        loader = PyPDFLoader(file_path)
        raw_docs = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(raw_docs)
        print(f"✂️  Split into {len(chunks)} chunks.")

        # 3. Embed & Save (The Magic Step)
        print("💾 Saving to Vector Database... (This may take a moment)")
        
        PGVector.from_documents(
            embedding=get_embedding_model(),
            documents=chunks,
            collection_name="rag_collection",
            connection_string=CONNECTION_STRING,
            pre_delete_collection=False
        )
        
        print("✅ Success! Document is now searchable.")
        
    except Exception as e:
        print(f"❌ Error during ingestion: {e}")

# --- Test Function ---
def test_rag():
    # Helper to ingest the latest file
    last_doc = Document.objects.last()
    if last_doc:
        ingest_document(last_doc.id)
    else:
        print("No documents found.")