from pydantic import BaseModel
from typing import Optional

class ChatResponse(BaseModel):
    status: str
    content: str
    source: str
    conversation_id: str
    message: Optional[str] = None  # For things like "Previous answer found"