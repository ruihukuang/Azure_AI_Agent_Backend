from openai import AsyncAzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from config import Config
from dotenv import load_dotenv
import os

#  Manually load the .env
load_dotenv()

# 2. Pre-flight check: Azure is VERY picky about these exact names
required_vars = ["AZURE_CLIENT_ID", "AZURE_TENANT_ID", "AZURE_CLIENT_SECRET"]
for var in required_vars:
    value = os.getenv(var)
    if not value:
        print(f"❌ CRITICAL: {var} is missing from environment!")
    else:
        # Just print the first few characters to be safe
        print(f"✅ Found {var}: {value[:4]}****")

# Initialize the credential. 
# It will now successfully find AZURE_CLIENT_ID, etc., in the environment.
credential = DefaultAzureCredential()

# 2. Create the token provider function
# This function handles the "calling" that was causing your previous error
token_provider = get_bearer_token_provider(
    credential, 
    "https://cognitiveservices.azure.com/.default" #standard identifier for Azure OpenAI permissions
)

# 3. Pass the provider to the client
openai_client = AsyncAzureOpenAI(
    azure_endpoint=Config.AZURE_ENDPOINT,
    azure_ad_token_provider=token_provider, # Pass the function, not a string!
    api_version="2024-08-01-preview"
)