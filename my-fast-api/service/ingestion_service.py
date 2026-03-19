import os
from sqlalchemy import text
from langchain_text_splitters import CharacterTextSplitter
from service.db_setup import SessionLocal, engine, Base
from service.model import DocVectors
from config import Config
from service.azure_setup import openai_client
from config import Config
import logging

# Get the logger that Semantic Kernel is listening to
sk_logger = logging.getLogger("semantic_kernel")

async def initialize_knowledge_base():
    """
    Handles DB setup and loads new .md files into the vector store using
    configurable chunking parameters.
    """
    # 1. Ensure Extension and Tables Exist
    sk_logger.info("🛠️ [KB_INIT] Step 1: Ensuring PGVector extension and tables exist...")
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 2. Identify already processed files
        sk_logger.info("🔍 [KB_INIT] Step 2: Identifying already processed files in Postgres...")
        existing_files_result = db.execute(text("SELECT DISTINCT file_name FROM doc_vectors")).fetchall()
        existing_files = [f[0] for f in existing_files_result]
        sk_logger.info(f"📁 [KB_INIT] Found {len(existing_files)} files already in database.")
        
        # 3. Initialize Splitter with Config values
        text_splitter = CharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE, 
            chunk_overlap=Config.CHUNK_OVERLAP,
            separator="\n" # Ensures chunks break on new lines where possible
        )
        new_files_count = 0
        for file_name in os.listdir(Config.FOLDER_PATH):
            if file_name.endswith(".md") and file_name not in existing_files:
                new_files_count += 1
                sk_logger.info(f"📥 [KB_INIT] Ingesting New File: {file_name}")
                
                with open(os.path.join(Config.FOLDER_PATH, file_name), 'r', encoding='utf-8') as f:
                    raw_text = f.read()
                
                # split_text is used because raw_text is a string
                chunks = text_splitter.split_text(raw_text)
                sk_logger.info(f"🧩 [KB_INIT] Split {file_name} into {len(chunks)} chunks.")

                for i, chunk in enumerate(chunks):
                    # Get Embedding from Azure (1536-dim) in the 2026 SDK
                    embeddings_response = await openai_client.embeddings.create(
                        model=Config.EMBEDDING_MODEL,
                        input=chunk
                    )
                    vector = embeddings_response.data[0].embedding
                    
                    new_doc = DocVectors(
                        file_name=file_name,
                        content=chunk,
                        embedding=vector
                    )
                    db.add(new_doc)

                    # Log progress for large files every 10 chunks to avoid log flooding
                    if i % 10 == 0:
                        sk_logger.info(f"💾 [KB_INIT] Uploading chunks {i} to database for {file_name}...")
        
        if new_files_count == 0:
            sk_logger.info("✅ [KB_INIT] No new files found. Knowledge base is up to date.")
            print(f"No new files found. Knowledge base is up to date.")
        else:
            db.commit()
            sk_logger.info(f"🚀 [KB_INIT] Ingestion complete. Added {new_files_count} new files.")
            print(f"Ingestion complete. Added {new_files_count} new files.")
        
    except Exception as e:
        sk_logger.error(f"❌ [KB_INIT] Error during ingestion: {str(e)}")
        print(f"Error during ingestion: {e}")
        db.rollback()
    finally:
        db.close()