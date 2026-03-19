import os
from dotenv import load_dotenv

load_dotenv() # This loads the variables from .env into os.environ

class Config:
    #   azure settings ...

    FOLDER_PATH = os.getenv("FOLDER_PATH")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
    AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
    DEPLOYMENT_MODEL = os.getenv("DEPLOYMENT_MODEL")
    DEPLOYMENT_MODEL_TEMPERATURE = os.getenv("DEPLOYMENT_MODEL_TEMPERATURE")
    DEPLOYMENT_MODEL_MAXTOKEN = os.getenv("DEPLOYMENT_MODEL_MAXTOKEN")

    # New Chunking Configs
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP"))

    # database settings
    DB_DRIVER = os.getenv("DB_DRIVER")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")

    
