# Invoice Chatbot API

A FastAPI backend for the invoice chatbot that can be integrated with Express.ts and React frontend.

## Project Structure

```
Fast/
├── src/
│   ├── api/
│   │   └── routes.py        # API endpoints
│   ├── models/
│   │   └── chat.py         # Data models and schemas
│   ├── services/
│   │   ├── chatbot.py      # Chatbot business logic
│   │   └── database.py     # Database operations
│   ├── utils/
│   │   └── templates.py    # Prompt templates
│   └── main.py             # FastAPI application
└── requirements.txt
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
DATABASE_URL=your_postgresql_url
GOOGLE_API_KEY=your_google_api_key
```

3. Run the server:
```bash
uvicorn src.main:app --reload
```

## API Endpoints

### Authentication
- POST `/api/authenticate`
  - Request: `{ "customer_name": string, "message": "" }`
  - Response: `{ "success": boolean, "message": string, "context": object, "suggestions": string[] }`

### Chat
- POST `/api/chat`
  - Request: `{ "customer_name": string, "message": string }`
  - Response: `{ "response": string, "sql": string, "row_count": number, "data": object[], "suggestions": string[] }`

### History
- GET `/api/history/{customer_name}`
  - Response: `{ "history": [{ "role": string, "content": string }] }`

### Clear History
- POST `/api/clear/{customer_name}`
  - Response: `{ "message": string }`

## Authentication

The API uses API key authentication. Include your API key in requests:
```
X-API-Key: your_api_key
```

## Integration with Express.ts

Example Express.ts proxy endpoint:

```typescript
app.post('/chat', async (req, res) => {
  try {
    const response = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': process.env.CHATBOT_API_KEY
      },
      body: JSON.stringify(req.body)
    });
    
    const data = await response.json();
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
