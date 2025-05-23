from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from langchain.memory import ConversationBufferWindowMemory

@dataclass
class ChatSession:
    customer_name: str
    memory: ConversationBufferWindowMemory
    context: Dict[str, Any] = field(default_factory=dict)

class CustomerStats(BaseModel):
    total_invoice: int
    total_amount: float
    first_invoice: str
    last_invoice: str
    statuses: str
    currencies: str

class ChatRequest(BaseModel):
    customer_name: str
    message: str

class ChatResponse(BaseModel):
    response: str
    sql: Optional[str] = None
    row_count: Optional[int] = None
    data: Optional[List[Dict[str, Any]]] = None
    suggestions: Optional[List[str]] = None
    error: Optional[str] = None

class AuthResponse(BaseModel):
    success: bool
    message: str
    context: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None

class Message(BaseModel):
    role: str
    content: str

class ConversationHistory(BaseModel):
    history: List[Message]
