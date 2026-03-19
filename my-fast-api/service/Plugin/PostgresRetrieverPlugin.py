import logging

from semantic_kernel.functions import kernel_function

from sqlalchemy import text

from service.db_setup import SessionLocal

from service.azure_setup import openai_client

from config import Config



# Get the logger you configured in app.py

logger = logging.getLogger("semantic_kernel")



class PostgresRetrieverPlugin:

    @kernel_function(name="get_context", description="Retrieves info from Postgres")

    async def get_context(self, query: str) -> str:
            logger.info("🔍 RAG: Generating embeddings for query...")
            
            try:
                # 1. Generate the embedding
                embeddings_response = await openai_client.embeddings.create(
                    model=Config.EMBEDDING_MODEL,
                    input=query
                )
                query_vector = embeddings_response.data[0].embedding
                vector_str = f"[{','.join(map(str, query_vector))}]"

                # 2. Database Search
                db = SessionLocal()
                try:
                    search_query = text("""
                        WITH relevant_files AS (
                            SELECT file_name, MAX(1 - (embedding <=> CAST(:vector AS vector))) AS max_similarity
                            FROM doc_vectors 
                            WHERE 1 - (embedding <=> CAST(:vector AS vector)) > 0.6
                            GROUP BY file_name
                            ORDER BY max_similarity DESC
                            LIMIT 3 
                        )
                        SELECT file_name, content 
                        FROM doc_vectors 
                        WHERE file_name IN (SELECT file_name FROM relevant_files)
                        ORDER BY file_name, id;
                    """)
                    
                    results = db.execute(search_query, {"vector": vector_str}).fetchall()
                    
                    # 3. Process results: Using standard dictionary logic
                    file_map = {}
                    for row in results:
                        # row[0] is file_name, row[1] is content
                        fn = str(row[0]) 
                        ct = str(row[1])
                        
                        if fn not in file_map:
                            file_map[fn] = []
                        file_map[fn].append(ct)

                    if not file_map:
                        return "No relevant context found."
                    
                    # Build final context string
                    final_parts = []
                    for fn, chunks in file_map.items():
                        full_text = "\n".join(chunks)
                        # Simple string concatenation to avoid any f-string format code errors
                        header = "--- SOURCE FILE: " + fn + " ---\n"
                        final_parts.append(header + full_text)
                    
                    logger.info("✅ RAG: Successfully retrieved data.")
                    return "\n\n".join(final_parts)
                    
                finally:
                    db.close()

            except Exception as e:
                # Use standard logging to avoid f-string issues in the error handler
                logger.error("❌ RAG Error occurred: %s", str(e))
                return "Error during retrieval."