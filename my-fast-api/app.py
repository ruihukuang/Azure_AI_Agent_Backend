import logging
import asyncio
from fastapi import FastAPI, BackgroundTasks
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from contextlib import asynccontextmanager
import uvicorn
from azure.identity import DefaultAzureCredential
from service.agent import get_response
from service.azure_setup import openai_client 
from dotenv import load_dotenv
from config import Config
from service.Plugin.PostgresRetrieverPlugin import PostgresRetrieverPlugin
from typing import Optional

from service.ingestion_service import initialize_knowledge_base

from config import Config
from service.schemas import ChatResponse


kernel = Kernel()

# 1. Global config: This sets the format for EVERY log in your app
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

# 2. Grab the specific Semantic Kernel logger
# Any logs sent to this name will now appear in your console
sk_logger = logging.getLogger("semantic_kernel")
sk_logger.setLevel(logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Everything here runs ON STARTUP
    print("--- Starting up: Initializing Knowledge Base ---")
    await initialize_knowledge_base()
    
    yield  # This is where the app "lives" and handles requests 
    # It defines what happens at the very birth and the very death of the server process.

    # To answer your question directly: The code before the yield must finish running successfully before the FastAPI server is allowed to start handling any user requests.
    
    # 2. Everything here runs ON SHUTDOWN
    print("--- Shutting down ---")

app = FastAPI(lifespan=lifespan)
user_input="Teach me some simple English with less than 1000 characters"
conversation_id =1
use_cache=True

@app.get("/")
async def root():
    return {"status": "Chatbox API is Running"}


# 1. Add Azure OpenAI Service to the Kernel


kernel.add_service(
    AzureChatCompletion(
        service_id="default",              # Matches settings in agent.py
        deployment_name=Config.DEPLOYMENT_MODEL, 
        async_client=openai_client         # Uses your new authenticated client
    )
)

# 2. Register your Plugins
kernel.add_plugin(PostgresRetrieverPlugin(), plugin_name="RetrieverPlugin")

# --- ENDPOINTS ---
@app.post("/chat/{conversation_id}" , response_model=ChatResponse)
async def chat(
    conversation_id: str, 
    user_input: str, 
    use_cache: Optional[str] = "none"
):
    """
    use_cache options:
    - "none": Initial check (Default)
    - "true": User wants the database result
    - "false": User wants a fresh answer (updates DB)
    """
    # Simply await the logic and return the result
    result = await get_response(user_input, conversation_id,kernel, use_cache)
    return result
    




if __name__ == "__main__":
    
    # This actually starts the server
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)