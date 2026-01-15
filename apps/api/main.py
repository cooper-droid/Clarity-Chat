"""
Fiat Clarity Chat - FastAPI Backend
Main application with all endpoints.
Updated: 2026-01-14 - Using OpenAI Prompts API with Clarity Storage
"""
from fastapi import FastAPI, HTTPException, Depends, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os
import uuid
import base64
import json

from dotenv import load_dotenv

# Import PostgreSQL models (for production)
from models import (
    Base, Conversation, Message, Lead, ConsentEvent,
    Document, Chunk, DocumentStatus
)
print("Using PostgreSQL models")

from services.ai_provider import ai_provider
from services.assistants_provider import assistants_provider
from services.rag_service import RAGService
from services.routing_service import RoutingService
from services.web_scraper import web_scraper
from settings_manager import SettingsManager, init_settings_table

load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fiat_clarity.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize settings table
try:
    init_settings_table(DATABASE_URL)
except Exception as e:
    print(f"Settings initialization error: {e}")

# FastAPI app
app = FastAPI(
    title="Fiat Clarity Chat API",
    description="AI-powered conversational interface for retirement planning",
    version="1.0.0"
)

# CORS - Allow localhost for development and production URLs
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://clarity-chat-frontend.onrender.com",  # Production frontend
]

# Add production frontend URL from environment variable if set
FRONTEND_URL = os.getenv("FRONTEND_URL")
if FRONTEND_URL and FRONTEND_URL not in ALLOWED_ORIGINS:
    ALLOWED_ORIGINS.append(FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"\n=== VALIDATION ERROR ===")
    print(f"URL: {request.url}")
    print(f"Method: {request.method}")
    print(f"Errors: {exc.errors()}")
    print("========================\n")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic models
class ChatRequest(BaseModel):
    session_id: str
    message: str
    user_id: Optional[str] = None
    metadata: Optional[Dict] = {}


class ChatResponse(BaseModel):
    response: str
    session_id: str
    show_lead_gate: bool = False
    citations: Optional[List[Dict]] = []
    booking_url: Optional[str] = None


class LeadRequest(BaseModel):
    session_id: str
    first_name: str
    email: EmailStr
    phone: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    page_url: Optional[str] = None


class LeadResponse(BaseModel):
    lead_id: int
    bucket: str
    meeting_type: str
    booking_url: str


class IngestRequest(BaseModel):
    title: str
    content: str
    source_url: Optional[str] = None
    source_type: Optional[str] = "markdown"
    published_date: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    dev_mode: bool
    database: str


# System prompt for Retirement: Redefined framework
SYSTEM_PROMPT = """You are a helpful retirement planning assistant for Fiat Wealth Management.
Your role is to educate prospects using the "Retirement: Redefined" framework.

FRAMEWORK:
For every response, structure your answer using these three parts:

A) WHERE ARE YOU TODAY?
   Ask 1-3 clarifying questions to understand their situation, goals, and constraints.

B) WHAT OPTIONS ALIGN WITH YOUR GOALS?
   Present 2-4 options/approaches with clear tradeoffs. Be educational, not prescriptive.

C) WHAT'S THE NEXT BEST STEP?
   Provide a concrete checklist of 3-5 action items, ending with scheduling a call.

GUARDRAILS:
- Provide educational information only, not personalized investment/tax/legal advice
- Never recommend specific buy/sell/hold actions
- Never suggest exact dollar amounts for conversions or withdrawals
- If asked "what should I do," pivot to education + factors + checklist + scheduling
- Always remind users this is educational and they shouldn't share sensitive info
- End every response with a small CTA to schedule a Clarity Call

TONE:
- Warm, professional, and conversational
- Use plain language, avoid jargon
- Be empathetic to their concerns
- Show expertise without being condescending

Remember: Your goal is to educate and build trust, always nudging toward a human conversation."""


@app.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "dev_mode": ai_provider.dev_mode,
        "database": db_status
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle chat message.
    Returns response and indicates if lead gate should be shown.
    """
    # Create separate session for settings
    settings_db = SessionLocal()
    try:
        # Load settings with separate session
        settings_mgr = SettingsManager(settings_db)

        # Get or create conversation
        conversation = db.query(Conversation).filter(
            Conversation.session_id == request.session_id
        ).first()

        if not conversation:
            conversation = Conversation(
                session_id=request.session_id,
                extra_data=request.metadata
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        # Save user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.message,
            extra_data=request.metadata
        )
        db.add(user_message)
        db.commit()

        # Check if we should show lead gate
        enable_lead_gate = settings_mgr.get_setting("enable_lead_gate", True)
        assistant_message_count = db.query(Message).filter(
            Message.conversation_id == conversation.id,
            Message.role == "assistant"
        ).count()

        show_lead_gate = enable_lead_gate and assistant_message_count >= 1 and not conversation.lead_id

        if show_lead_gate:
            # Get lead gate message from settings
            lead_gate_msg = settings_mgr.get_setting(
                "lead_gate_message",
                "Before we keep going, where should we send your summary and how can we reach you?"
            )

            gate_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=lead_gate_msg,
                extra_data={"type": "lead_gate"}
            )
            db.add(gate_message)
            db.commit()

            return ChatResponse(
                response=gate_message.content,
                session_id=request.session_id,
                show_lead_gate=True,
                citations=[]
            )

        # Normal response flow - retrieve relevant context
        enable_rag = settings_mgr.get_setting("enable_rag", True)
        rag_chunk_limit = int(settings_mgr.get_setting("rag_chunk_limit", 3))

        # First try to get content from fiatwm.com website
        web_content = []
        try:
            scraped_pages = web_scraper.search_site(request.message)
            web_content = [
                {
                    "title": page["title"],
                    "content": page["content"][:1000],  # Limit content length
                    "source_url": page["url"],
                    "published_date": "Recent"
                }
                for page in scraped_pages
            ]
            if web_content:
                print(f"✓ Found {len(web_content)} relevant pages from fiatwm.com")
        except Exception as e:
            print(f"⚠ Web scraping error: {e}")

        # Then get context from RAG database
        rag_service = RAGService(db)
        context_chunks = rag_service.retrieve_relevant_chunks(request.message, limit=rag_chunk_limit) if enable_rag else []

        # Combine web content and RAG chunks
        all_context = web_content + context_chunks

        # Build message history for context
        recent_messages = db.query(Message).filter(
            Message.conversation_id == conversation.id,
            Message.role.in_(["user", "assistant"])
        ).order_by(Message.created_at.desc()).limit(6).all()

        message_history = [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(recent_messages)
        ]

        # Get AI settings from database
        system_prompt = settings_mgr.get_setting("system_prompt", SYSTEM_PROMPT)
        model = settings_mgr.get_setting("openai_model", "gpt-4-turbo-preview")
        temperature = float(settings_mgr.get_setting("temperature", 0.7))
        max_tokens = int(settings_mgr.get_setting("max_tokens", 1000))
        api_key = settings_mgr.get_setting("openai_api_key", "")

        # Initialize OpenAI client with settings-based API key
        openai_client = None
        use_real_ai = False

        if api_key and api_key.strip():
            try:
                from openai import OpenAI
                openai_client = OpenAI(api_key=api_key.strip())
                use_real_ai = True
                print(f"✓ Using OpenAI with model: {model}")
            except Exception as e:
                print(f"⚠ OpenAI initialization failed: {e}")
                use_real_ai = False

        # Generate response
        if use_real_ai and openai_client:
            # Use real OpenAI
            try:
                # Build context from chunks
                context_text = "\n\n".join([
                    f"[{chunk.get('title', 'Unknown')}]\n{chunk.get('content', '')}"
                    for chunk in all_context
                ])

                # Build messages with context
                augmented_messages = [
                    {"role": "system", "content": system_prompt}
                ]

                if context_text:
                    augmented_messages.append({
                        "role": "system",
                        "content": f"KNOWLEDGE BASE CONTEXT:\n\n{context_text}"
                    })

                augmented_messages.extend(message_history)

                response = openai_client.chat.completions.create(
                    model=model,
                    messages=augmented_messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                response_text = response.choices[0].message.content
                print(f"✓ Generated response using {model}")

            except Exception as e:
                print(f"✗ OpenAI API error: {e}")
                # Fall back to dev mode
                response_text = ai_provider.generate_chat_response(
                    messages=message_history,
                    context_chunks=all_context,
                    system_prompt=system_prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
        else:
            # Use dev mode
            response_text = ai_provider.generate_chat_response(
                messages=message_history,
                context_chunks=all_context,
                system_prompt=system_prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

        # Extract citations
        enable_citations = settings_mgr.get_setting("enable_citations", True)
        citations = []
        if enable_citations:
            citations = [
                {
                    "title": chunk.get("title"),
                    "date": chunk.get("published_date"),
                    "url": chunk.get("source_url")
                }
                for chunk in all_context
                if chunk.get("title")
            ]

        # Save assistant message
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=response_text,
            extra_data={
                "citations": citations,
                "context_chunks": len(all_context),
                "web_content_count": len(web_content)
            }
        )
        db.add(assistant_message)
        db.commit()

        # Get booking URL if lead exists
        booking_url = None
        if conversation.lead_id:
            routing_service = RoutingService(db)
            booking_url = routing_service.get_booking_url(conversation.lead_id)

        return ChatResponse(
            response=response_text,
            session_id=request.session_id,
            show_lead_gate=False,
            citations=citations,
            booking_url=booking_url
        )

    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")
    finally:
        settings_db.close()


@app.post("/chat/stream")
async def chat_stream(
    session_id: str = Form(...),
    message: str = Form(...),
    db: Session = Depends(get_db),
    user_id: Optional[str] = Form(None),
    files: List[UploadFile] = File(default=[])
):
    """
    Handle chat message with streaming response and optional file uploads.
    Returns Server-Sent Events (SSE) stream.
    File size limit: 0.5GB (500MB) per file.
    """

    # Process uploaded files BEFORE the generator (files get closed after request ends)
    file_contents = []
    file_metadata = []
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 0.5GB in bytes

    if files and len(files) > 0:
        for file in files:
            # Skip if no filename (empty file upload)
            if not file.filename:
                continue

            # Store filename and content_type BEFORE reading (file gets closed after read)
            filename = file.filename
            content_type = file.content_type

            # Read file content
            content = await file.read()
            file_size = len(content)

            if file_size > MAX_FILE_SIZE:
                # Return error immediately if file too large
                async def error_stream():
                    yield f"data: {json.dumps({'type': 'error', 'error': f'File {filename} exceeds 0.5GB limit'})}\n\n"
                return StreamingResponse(error_stream(), media_type="text/event-stream")

            # Store file info
            file_info = {
                "filename": filename,
                "content_type": content_type,
                "size": file_size
            }
            file_metadata.append(file_info)

            # For text files, extract content
            if content_type and ('text' in content_type or 'json' in content_type):
                try:
                    text_content = content.decode('utf-8')
                    file_contents.append(f"File: {filename}\n{text_content[:10000]}")  # Limit to 10k chars
                except:
                    file_contents.append(f"File: {filename} (binary file, {file_size} bytes)")
            else:
                # For binary files, just note the file
                file_contents.append(f"File: {filename} ({content_type}, {file_size} bytes)")

    async def generate_stream():
        try:
            print("🔧 Starting generate_stream")
            # Load settings with a separate session to avoid transaction conflicts
            settings_db = SessionLocal()
            print(f"✓ Created settings_db session: {type(settings_db)}")
            settings_mgr = SettingsManager(settings_db)
            print("✓ Created settings_mgr")

            # Get or create conversation
            print(f"🔧 Querying conversation for session: {session_id}")
            conversation = db.query(Conversation).filter(
                Conversation.session_id == session_id
            ).first()
            print(f"✓ Found conversation: {conversation.id if conversation else 'None'}")

            if not conversation:
                conversation = Conversation(
                    session_id=session_id,
                    extra_data={"user_id": user_id} if user_id else {}
                )
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
            elif user_id and not conversation.extra_data.get("user_id"):
                # Update conversation with user_id if it wasn't set
                conversation.extra_data = {**conversation.extra_data, "user_id": user_id}
                db.commit()

            # Prepare message content with file info
            message_content = message
            if file_metadata:
                message_content += "\n\n[Attached files: " + ", ".join([f['filename'] for f in file_metadata]) + "]"

            # Save user message
            user_message = Message(
                conversation_id=conversation.id,
                role="user",
                content=message_content,
                extra_data={"files": file_metadata} if file_metadata else {}
            )
            db.add(user_message)
            db.commit()

            # Check lead gate
            print("🔧 Getting enable_lead_gate setting...")
            enable_lead_gate = settings_mgr.get_setting("enable_lead_gate", True)
            print(f"✓ enable_lead_gate = {enable_lead_gate}")

            print("🔧 Querying assistant message count...")
            assistant_message_count = db.query(Message).filter(
                Message.conversation_id == conversation.id,
                Message.role == "assistant"
            ).count()
            print(f"✓ assistant_message_count = {assistant_message_count}")

            show_lead_gate = enable_lead_gate and assistant_message_count >= 1 and not conversation.lead_id

            if show_lead_gate:
                lead_gate_msg = settings_mgr.get_setting(
                    "lead_gate_message",
                    "Before we keep going, where should we send your summary and how can we reach you?"
                )
                yield f"data: {json.dumps({'type': 'lead_gate', 'content': lead_gate_msg})}\n\n"
                return

            # Check if using your custom Clarity prompt
            prompt_id = os.getenv("OPENAI_PROMPT_ID", "pmpt_6962e013d6d88196b1c3834baa00e88500912c21d3085185")

            # Get API key
            api_key = os.getenv("OPENAI_API_KEY", "")
            if not api_key:
                yield f"data: {json.dumps({'type': 'error', 'error': 'OpenAI API key not configured'})}\n\n"
                return

            from openai import OpenAI
            openai_client = OpenAI(api_key=api_key)

            # Build message with file context if needed
            user_input = message
            if file_contents:
                files_text = "\n\n".join(file_contents)
                user_input += f"\n\n[User uploaded files]:\n{files_text}"

            # Try to use Prompts/Responses API with your Clarity prompt (includes vector store!)
            if prompt_id:
                print(f"✓ Using Clarity prompt (includes Clarity Storage): {prompt_id[:20]}...")
                try:
                    # Check if responses API is available
                    if hasattr(openai_client, 'beta') and hasattr(openai_client.beta, 'responses'):
                        responses_api = openai_client.beta.responses
                    elif hasattr(openai_client, 'responses'):
                        responses_api = openai_client.responses
                    else:
                        raise AttributeError("Responses API not available")

                    # Use your prompt (already includes Clarity Storage + instructions)
                    stream = responses_api.create(
                        prompt={"id": prompt_id, "version": "latest"},
                        input=user_input,
                        stream=True
                    )

                    full_response = ""
                    for event in stream:
                        if hasattr(event, 'delta') and event.delta:
                            content = event.delta
                            full_response += content
                            yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"

                    yield f"data: {json.dumps({'type': 'done'})}\n\n"

                    # Save assistant response
                    assistant_message = Message(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=full_response,
                        extra_data={}
                    )
                    db.add(assistant_message)
                    db.commit()
                    return

                except Exception as e:
                    import traceback
                    print(f"⚠ Responses API error: {e}")
                    print(f"Full error traceback:\n{traceback.format_exc()}")
                    print("Falling back to standard chat...")

            # Fallback to standard chat (if Responses API not available)
            enable_rag = settings_mgr.get_setting("enable_rag", True)
            rag_chunk_limit = int(settings_mgr.get_setting("rag_chunk_limit", 3))

            # Web scraping
            web_content = []
            try:
                scraped_pages = web_scraper.search_site(message)
                web_content = [
                    {
                        "title": page["title"],
                        "content": page["content"][:1000],
                        "source_url": page["url"],
                        "published_date": "Recent"
                    }
                    for page in scraped_pages
                ]
            except Exception as e:
                print(f"⚠ Web scraping error: {e}")

            # RAG
            rag_service = RAGService(db)
            context_chunks = rag_service.retrieve_relevant_chunks(message, limit=rag_chunk_limit) if enable_rag else []
            all_context = web_content + context_chunks

            # Get message history
            recent_messages = db.query(Message).filter(
                Message.conversation_id == conversation.id,
                Message.role.in_(["user", "assistant"])
            ).order_by(Message.created_at.desc()).limit(6).all()

            message_history = [
                {"role": msg.role, "content": msg.content}
                for msg in reversed(recent_messages)
            ]

            # Get AI settings (use environment variables for API key and prompt)
            system_prompt = settings_mgr.get_setting("system_prompt", "You are a helpful assistant.")
            model = settings_mgr.get_setting("openai_model", "gpt-4-turbo-preview")
            temperature = float(settings_mgr.get_setting("temperature", 0.7))
            max_tokens = int(settings_mgr.get_setting("max_tokens", 1000))

            # Use environment variables for API key and prompt (same as above)
            fallback_api_key = os.getenv("OPENAI_API_KEY", "")
            prompt_id = os.getenv("OPENAI_PROMPT_ID", "pmpt_6962e013d6d88196b1c3834baa00e88500912c21d3085185")
            prompt_version = "latest"

            if not fallback_api_key or not fallback_api_key.strip():
                # Dev mode fallback
                yield f"data: {json.dumps({'type': 'content', 'content': 'Running in dev mode. Please configure your OpenAI API key in the admin panel.'})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return

            # Stream from OpenAI
            from openai import OpenAI
            openai_client = OpenAI(api_key=fallback_api_key.strip())

            context_text = "\n\n".join([
                f"[{chunk.get('title', 'Unknown')}]\n{chunk.get('content', '')}"
                for chunk in all_context
            ])

            # Build context for prompt
            additional_context = []
            if context_text:
                additional_context.append(f"KNOWLEDGE BASE CONTEXT:\n\n{context_text}")

            if file_contents:
                files_text = "\n\n".join(file_contents)
                additional_context.append(f"UPLOADED FILES:\n\n{files_text}\n\nThe user has uploaded these files. Please analyze them and incorporate their content into your response.")

            context_string = "\n\n".join(additional_context) if additional_context else ""

            # Debug logging
            print(f"=== PROMPT CONFIGURATION ===")
            print(f"Prompt ID: '{prompt_id}'")
            print(f"Prompt Version: '{prompt_version}'")
            print(f"Has prompt_id: {bool(prompt_id)}")
            print(f"Stripped prompt_id: '{prompt_id.strip() if prompt_id else ''}'")
            print(f"===========================")

            # Check if using Prompt API with prompt_id
            if prompt_id and prompt_id.strip():
                # Use OpenAI Responses API with custom prompt
                try:
                    # Check if responses API is available
                    if not hasattr(openai_client, 'responses'):
                        # Try to access via beta
                        if hasattr(openai_client, 'beta') and hasattr(openai_client.beta, 'responses'):
                            responses_api = openai_client.beta.responses
                        else:
                            raise AttributeError("Responses API not available in this SDK version")
                    else:
                        responses_api = openai_client.responses

                    # Use the Responses API EXACTLY as OpenAI's example
                    prompt_config = {
                        "id": prompt_id.strip(),
                        "version": prompt_version,
                    }

                    # Match OpenAI's example: only prompt and stream parameters
                    stream = responses_api.create(
                        prompt=prompt_config,
                        input=message,  # User message
                        stream=True
                    )
                    print(f"✓ Using OpenAI Responses API with prompt ID: {prompt_id} version {prompt_version}")
                    print(f"  Message: {message[:80]}...")
                except Exception as e:
                    print(f"Error using Responses API: {e}, falling back to standard completion")
                    print(f"Note: Responses API may require SDK update or beta access")
                    # Fallback to standard completion
                    augmented_messages = [
                        {"role": "system", "content": system_prompt}
                    ]
                    if context_string:
                        augmented_messages.append({"role": "system", "content": context_string})
                    augmented_messages.extend(message_history)

                    stream = openai_client.chat.completions.create(
                        model=model,
                        messages=augmented_messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        stream=True
                    )
            else:
                # Standard chat completions
                augmented_messages = [
                    {"role": "system", "content": system_prompt}
                ]
                if context_string:
                    augmented_messages.append({"role": "system", "content": context_string})
                augmented_messages.extend(message_history)

                stream = openai_client.chat.completions.create(
                    model=model,
                    messages=augmented_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True
                )

            full_response = ""

            # Determine if using Responses API or Chat Completions API
            is_responses_api = prompt_id and prompt_id.strip()

            for chunk in stream:
                try:
                    if is_responses_api:
                        # Responses API uses event-based streaming
                        # Check for different event types
                        if hasattr(chunk, 'type'):
                            event_type = chunk.type

                            # Text delta events contain the streaming content
                            if event_type == 'response.output_text.delta':
                                if hasattr(chunk, 'delta') and chunk.delta:
                                    content = chunk.delta
                                    full_response += content
                                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"

                            # Final text event (fallback)
                            elif event_type == 'response.output_text.done':
                                if hasattr(chunk, 'text') and chunk.text:
                                    # If we somehow missed deltas, use the final text
                                    if not full_response or len(chunk.text) > len(full_response):
                                        missing_content = chunk.text[len(full_response):]
                                        if missing_content:
                                            full_response = chunk.text
                                            yield f"data: {json.dumps({'type': 'content', 'content': missing_content})}\n\n"

                        # Fallback: if chunk has content attribute directly
                        elif hasattr(chunk, 'content'):
                            content = str(chunk.content)
                            if content and content not in full_response:
                                full_response += content
                                yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"

                    else:
                        # Standard Chat Completions API streaming
                        if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                            delta = chunk.choices[0].delta
                            if hasattr(delta, 'content') and delta.content:
                                content = delta.content
                                full_response += content
                                yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"

                except Exception as chunk_error:
                    print(f"⚠ Error processing chunk: {chunk_error}")
                    print(f"  Chunk type: {type(chunk)}")
                    if hasattr(chunk, '__dict__'):
                        print(f"  Chunk attributes: {list(chunk.__dict__.keys())}")
                    continue

            # Save assistant message
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=full_response,
                extra_data={
                    "context_chunks": len(all_context),
                    "web_content_count": len(web_content)
                }
            )
            db.add(assistant_message)

            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()
            db.commit()

            # Parse Related Resources from AI response
            # Look for "Related Resources:" section and extract URLs and titles
            import re

            resources = []
            enable_citations = settings_mgr.get_setting("enable_citations", True)

            if enable_citations:
                # Pattern to match "Related Resources:" section
                resources_match = re.search(r'Related Resources?:?\s*\n((?:[-•]\s*.*\n?)+)', full_response, re.IGNORECASE)

                if resources_match:
                    resources_text = resources_match.group(1)

                    # Pattern to match resource lines with optional URLs
                    # Matches: "- Title: URL" or "- Title" or "• Title (URL)"
                    resource_lines = re.findall(r'[-•]\s*([^\n]+)', resources_text)

                    for line in resource_lines:
                        # Try to extract URL from the line
                        url_match = re.search(r'https?://[^\s\)]+', line)
                        url = url_match.group(0) if url_match else None

                        # Extract title (remove URL from title if present)
                        if url:
                            title = re.sub(r'\s*[\(\[]?\s*https?://[^\s\)\]]+[\)\]]?\s*', '', line).strip()
                            # Remove common separators between title and URL
                            title = re.sub(r':\s*$', '', title).strip()
                        else:
                            title = line.strip()

                        # Clean up title
                        title = title.strip('- •:').strip()

                        if title:
                            resources.append({
                                "title": title,
                                "url": url,
                                "date": None
                            })

                # Only send resources if AI provided them - no RAG fallback
                if resources:
                    yield f"data: {json.dumps({'type': 'citations', 'citations': resources})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            import traceback
            print(f"✗ Streaming error: {e}")
            print(f"Full traceback:\n{traceback.format_exc()}")
            db.rollback()  # Rollback failed transaction
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        finally:
            # Close the separate settings session
            settings_db.close()

    return StreamingResponse(generate_stream(), media_type="text/event-stream")


@app.post("/lead", response_model=LeadResponse)
async def create_lead(
    request: LeadRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """
    Create or update lead with contact information.
    Routes to appropriate Calendly link and creates consent audit trail.
    """
    try:
        # Get conversation
        conversation = db.query(Conversation).filter(
            Conversation.session_id == request.session_id
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Route lead
        routing_service = RoutingService(db)
        lead_info = routing_service.route_lead(
            conversation_id=conversation.id,
            first_name=request.first_name,
            email=request.email,
            phone=request.phone
        )

        # Create consent event
        disclosure_text = (
            "By continuing, you agree that Fiat Wealth Management may contact you by phone, "
            "email, or text regarding your request. Message & data rates may apply. "
            "Reply STOP to opt out."
        )

        consent_event = ConsentEvent(
            lead_id=lead_info["lead_id"],
            conversation_id=conversation.id,
            event_type="lead_capture",
            ip_address=request.ip_address or http_request.client.host,
            user_agent=request.user_agent or http_request.headers.get("user-agent"),
            page_url=request.page_url or "http://localhost:3000",
            disclosure_text=disclosure_text,
            disclosure_version="v1.0",
            extra_data={
                "session_id": request.session_id,
                "capture_method": "in_chat_form"
            }
        )
        db.add(consent_event)
        db.commit()

        return LeadResponse(**lead_info)

    except Exception as e:
        print(f"Lead creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating lead: {str(e)}")


@app.post("/admin/ingest")
async def ingest_document(
    request: IngestRequest,
    db: Session = Depends(get_db)
):
    """
    Ingest a document into the knowledge base.
    Creates document and chunks with embeddings.
    """
    try:
        # Parse published_date if provided
        published_date = None
        if request.published_date:
            try:
                published_date = datetime.strptime(request.published_date, "%Y-%m-%d")
            except:
                pass

        # Create document
        document = Document(
            title=request.title,
            content=request.content,
            source_url=request.source_url,
            source_type=request.source_type,
            published_date=published_date,
            status=DocumentStatus.DRAFT
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        # Chunk content (simple paragraph-based chunking)
        chunks = _chunk_content(request.content)

        # Create chunk records with embeddings
        chunk_count = 0
        for idx, chunk_text in enumerate(chunks):
            # Generate embedding
            embedding = ai_provider.generate_embedding(chunk_text)

            # Count tokens (rough estimate)
            token_count = len(chunk_text.split())

            chunk = Chunk(
                document_id=document.id,
                content=chunk_text,
                chunk_index=idx,
                token_count=token_count,
                embedding=str(embedding) if embedding else None
            )
            db.add(chunk)
            chunk_count += 1

        db.commit()

        return {
            "document_id": document.id,
            "title": document.title,
            "chunk_count": chunk_count,
            "status": document.status.value
        }

    except Exception as e:
        print(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=f"Error ingesting document: {str(e)}")


@app.post("/admin/approve/{doc_id}")
async def approve_document(doc_id: int, db: Session = Depends(get_db)):
    """Approve a document for retrieval."""
    try:
        document = db.query(Document).filter(Document.id == doc_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        document.status = DocumentStatus.APPROVED
        document.updated_at = datetime.utcnow()
        db.commit()

        return {
            "document_id": document.id,
            "title": document.title,
            "status": document.status.value
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error approving document: {str(e)}")


def _chunk_content(content: str, min_chunk_size: int = 300, max_chunk_size: int = 800) -> List[str]:
    """
    Chunk content into semantic pieces.
    Simple implementation: split on double newlines (paragraphs) and combine to target size.
    """
    paragraphs = content.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # If adding this paragraph exceeds max size, save current chunk
        if current_chunk and len(current_chunk) + len(para) > max_chunk_size:
            if len(current_chunk) >= min_chunk_size:
                chunks.append(current_chunk)
                current_chunk = para
            else:
                current_chunk += "\n\n" + para
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para

    # Add remaining chunk
    if current_chunk:
        chunks.append(current_chunk)

    return chunks


# ==================== SETTINGS ENDPOINTS ====================

@app.get("/admin/settings")
async def get_settings(db: Session = Depends(get_db)):
    """Get all chatbot settings."""
    try:
        settings_mgr = SettingsManager(db)
        return settings_mgr.get_all_settings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting settings: {str(e)}")


@app.get("/admin/settings/{key}")
async def get_setting(key: str, db: Session = Depends(get_db)):
    """Get a specific setting by key."""
    try:
        settings_mgr = SettingsManager(db)
        value = settings_mgr.get_setting(key)
        if value is None:
            raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
        return {"key": key, "value": value}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting setting: {str(e)}")


@app.put("/admin/settings/{key}")
async def update_setting(
    key: str,
    value: dict,
    db: Session = Depends(get_db)
):
    """
    Update a setting.
    Body: {"value": <any>, "type": "string|number|boolean|json", "description": "..."}
    """
    try:
        settings_mgr = SettingsManager(db)
        setting = settings_mgr.set_setting(
            key,
            value.get("value"),
            value.get("type"),
            value.get("description")
        )
        return {
            "key": key,
            "value": value.get("value"),
            "type": setting.setting_type,
            "updated": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating setting: {str(e)}")


@app.post("/admin/settings/reset")
async def reset_settings(db: Session = Depends(get_db)):
    """Reset all settings to defaults."""
    try:
        settings_mgr = SettingsManager(db)
        settings_mgr.reset_to_defaults()
        return {"message": "Settings reset to defaults", "settings": settings_mgr.get_all_settings()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting settings: {str(e)}")


@app.get("/config")
async def get_public_config(db: Session = Depends(get_db)):
    """Get public configuration for the frontend (non-sensitive settings only)."""
    try:
        settings_mgr = SettingsManager(db)
        all_settings = settings_mgr.get_all_settings()

        # Return only frontend-safe settings
        return {
            "chat_title": all_settings.get("chat_title", {}).get("value"),
            "chat_subtitle": all_settings.get("chat_subtitle", {}).get("value"),
            "welcome_message": all_settings.get("welcome_message", {}).get("value"),
            "schedule_button_text": all_settings.get("schedule_button_text", {}).get("value"),
            "enable_citations": all_settings.get("enable_citations", {}).get("value"),
            "enable_lead_gate": all_settings.get("enable_lead_gate", {}).get("value"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting config: {str(e)}")


# ==================== SESSION MANAGEMENT ENDPOINTS ====================

@app.get("/sessions/{user_id}")
async def get_user_sessions(user_id: str, db: Session = Depends(get_db)):
    """Get all chat sessions for a user."""
    try:
        conversations = db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(Conversation.updated_at.desc()).all()

        return [{
            "session_id": conv.session_id,
            "title": conv.title or "New Chat",
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat(),
            "message_count": len(conv.messages)
        } for conv in conversations]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sessions: {str(e)}")


@app.post("/sessions/create")
async def create_session(
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Create a new chat session."""
    try:
        session_id = str(uuid.uuid4())
        conversation = Conversation(
            session_id=session_id,
            extra_data={"user_id": user_id} if user_id else {}
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        return {
            "session_id": session_id,
            "title": "New Chat",
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")


@app.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    """Get all messages for a specific session."""
    try:
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Session not found")

        messages = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at.asc()).all()

        return [{
            "id": str(msg.id),
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat()
        } for msg in messages]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching messages: {str(e)}")


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a chat session and all its messages."""
    try:
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Session not found")

        db.delete(conversation)
        db.commit()

        return {"message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")


@app.patch("/sessions/{session_id}/title")
async def update_session_title(
    session_id: str,
    title: str,
    db: Session = Depends(get_db)
):
    """Update the title of a chat session."""
    try:
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Session not found")

        # Store title in extra_data since Conversation model doesn't have title field
        conversation.extra_data = {**conversation.extra_data, "title": title}
        conversation.updated_at = datetime.utcnow()
        db.commit()

        return {"message": "Title updated successfully", "title": title}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating title: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
# Force redeploy Wed Jan 14 14:33:03 CST 2026
