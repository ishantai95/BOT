from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import APIKeyHeader
from typing import List, Dict
import os
from dotenv import load_dotenv
import traceback

from ..models.chat import ChatRequest, ChatResponse, AuthResponse, ConversationHistory, Message
from ..services.chatbot import ChatbotService
from ..services.database import DatabaseService

load_dotenv()

router = APIRouter()
api_key_header = APIKeyHeader(name="X-API-Key")

# Store chatbot instances
chatbot_instances: Dict[str, ChatbotService] = {}

async def verify_api_key(api_key: str = Depends(api_key_header)):
    expected_key = os.getenv("BACKEND_API_KEY")
    print(f"Received API key length: {len(api_key) if api_key else 0}")
    print(f"Expected API key length: {len(expected_key) if expected_key else 0}")
    print(f"Keys match: {api_key == expected_key}")
    
    if not expected_key:
        raise HTTPException(status_code=500, detail="Server API key not configured")
    if api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

async def get_chatbot(api_key: str = Depends(api_key_header)) -> ChatbotService:
    try:
        if api_key not in chatbot_instances:
            db_service = DatabaseService(os.getenv("DATABASE_URL"))
            chatbot_instances[api_key] = ChatbotService(db_service, os.getenv("GOOGLE_API_KEY"))
        return chatbot_instances[api_key]
    except Exception as e:
        print(f"Error creating chatbot service: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error initializing services: {str(e)}")

@router.post("/authenticate", response_model=AuthResponse)
async def authenticate(request: ChatRequest, chatbot: ChatbotService = Depends(get_chatbot)):
    try:
        print(f"Authenticating user: {request.customer_name}")  # Debug log
        success = await chatbot.authenticate(request.customer_name)
        if success:
            suggestions = chatbot.generate_suggestions()
            context = chatbot.session.context if chatbot.session else None
            return AuthResponse(
                success=True,
                message=f"Welcome {request.customer_name}!",
                context=context,
                suggestions=suggestions
            )
        raise HTTPException(status_code=401, detail="Customer not found")
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, chatbot: ChatbotService = Depends(get_chatbot)):
    if not chatbot.session or chatbot.session.customer_name != request.customer_name:
        success = await chatbot.authenticate(request.customer_name)
        if not success:
            raise HTTPException(status_code=401, detail="Customer not found")
    
    response = await chatbot.chat(request.message)
    return response

@router.get("/history/{customer_name}", response_model=ConversationHistory)
async def get_history(
    customer_name: str,
    chatbot: ChatbotService = Depends(get_chatbot)
):
    if not chatbot.session or chatbot.session.customer_name != customer_name:
        success = await chatbot.authenticate(customer_name)
        if not success:
            raise HTTPException(status_code=401, detail="Customer not found")
    
    history = chatbot.get_conversation_history()
    return ConversationHistory(history=[Message(**msg) for msg in history])

@router.post("/clear/{customer_name}")
async def clear_history(
    customer_name: str,
    chatbot: ChatbotService = Depends(get_chatbot)
):
    if not chatbot.session or chatbot.session.customer_name != customer_name:
        success = await chatbot.authenticate(customer_name)
        if not success:
            raise HTTPException(status_code=401, detail="Customer not found")
    
    chatbot.clear_memory()
    return {"message": "Chat history cleared successfully"}
