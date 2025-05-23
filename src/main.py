from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
from dotenv import load_dotenv
from .api.routes import router

# Load environment variables from project root
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(env_path)

# Debug print
print("Environment Variables Loaded From:", env_path)
print(f"BACKEND_API_KEY: {os.getenv('BACKEND_API_KEY')}")
print(f"DATABASE_URL exists: {'DATABASE_URL' in os.environ}")
print(f"GOOGLE_API_KEY exists: {'GOOGLE_API_KEY' in os.environ}")

app = FastAPI(
    title="Invoice Chatbot API",
    description="API for interacting with the invoice chatbot",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
