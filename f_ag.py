import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder
from typing import List, Dict
from uuid import uuid4
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Azure AI Agent Backend")

# Environment variables for Azure configuration
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT", "https://foundry1234.services.ai.azure.com/api/projects/AI-Hackathon")
AGENT_ID = os.getenv("AGENT_ID", "asst_H4LMeHPk2gsDJql4ZCIj3pWw")

# Initialize Azure AI Project Client
credential = DefaultAzureCredential()
project_client = AIProjectClient(credential=credential, endpoint=AZURE_ENDPOINT)

# In-memory store for thread IDs (use a database like Redis or PostgreSQL for production)
thread_store: Dict[str, str] = {}

class MessageRequest(BaseModel):
    thread_id: str | None = None
    content: str

class MessageResponse(BaseModel):
    role: str
    content: str

class ThreadResponse(BaseModel):
    thread_id: str

class ChatHistoryResponse(BaseModel):
    messages: List[MessageResponse]

@app.post("/api/thread", response_model=ThreadResponse)
async def create_thread():
    try:
        thread = project_client.agents.threads.create()
        thread_id = str(uuid4())  # Generate a unique session ID for the frontend
        thread_store[thread_id] = thread.id  # Map session ID to Azure thread ID
        logger.info(f"Created thread with session ID {thread_id} and Azure thread ID {thread.id}")
        return ThreadResponse(thread_id=thread_id)
    except Exception as e:
        logger.error(f"Failed to create thread: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create thread: {str(e)}")

@app.post("/api/message", response_model=MessageResponse)
async def send_message(request: MessageRequest):
    try:
        # If no thread_id provided, create a new thread
        if not request.thread_id or request.thread_id not in thread_store:
            thread = project_client.agents.threads.create()
            thread_id = str(uuid4())
            thread_store[thread_id] = thread.id
            request.thread_id = thread_id
            logger.info(f"Created new thread for message with session ID {thread_id}")
        else:
            thread_id = thread_store[request.thread_id]

        # Create and send user message
        message = project_client.agents.messages.create(
            thread_id=thread_store[request.thread_id],
            role="user",
            content=request.content
        )

        # Process the message with the agent
        run = project_client.agents.runs.create_and_process(
            thread_id=thread_store[request.thread_id],
            agent_id=AGENT_ID
        )

        if run.status == "failed":
            logger.error(f"Run failed: {run.last_error}")
            raise HTTPException(status_code=500, detail=f"Run failed: {run.last_error}")

        # Retrieve the latest assistant message
        messages = project_client.agents.messages.list(
            thread_id=thread_store[request.thread_id],
            order=ListSortOrder.DESCENDING
        )
        for msg in messages:
            if msg.role == "assistant" and msg.text_messages:
                logger.info(f"Assistant response retrieved for thread {request.thread_id}")
                return MessageResponse(
                    role=msg.role,
                    content=msg.text_messages[-1].text.value
                )

        logger.warning(f"No assistant response found for thread {request.thread_id}")
        raise HTTPException(status_code=404, detail="No assistant response found")
    except Exception as e:
        logger.error(f"Failed to process message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@app.get("/api/history/{thread_id}", response_model=ChatHistoryResponse)
async def get_chat_history(thread_id: str):
    if thread_id not in thread_store:
        logger.warning(f"Thread ID {thread_id} not found")
        raise HTTPException(status_code=404, detail="Thread not found")
    
    try:
        messages = project_client.agents.messages.list(
            thread_id=thread_store[thread_id],
            order=ListSortOrder.ASCENDING
        )
        chat_history = [
            MessageResponse(
                role=msg.role,
                content=msg.text_messages[-1].text.value if msg.text_messages else ""
            )
            for msg in messages if msg.text_messages
        ]
        logger.info(f"Retrieved chat history for thread {thread_id}")
        return ChatHistoryResponse(messages=chat_history)
    except Exception as e:
        logger.error(f"Failed to retrieve chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chat history: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)