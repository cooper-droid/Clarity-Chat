"""
Streaming chat endpoint for real-time response generation
"""
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict
from sqlalchemy.orm import Session
import json
import asyncio

from main import get_db, SettingsManager, Conversation, Message, RAGService, web_scraper


class StreamChatRequest(BaseModel):
    session_id: str
    message: str
    metadata: Optional[Dict] = {}


async def generate_stream(
    request: StreamChatRequest,
    db: Session,
    settings_mgr: SettingsManager
):
    """Generate streaming response from OpenAI"""
    try:
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

        # Check lead gate
        enable_lead_gate = settings_mgr.get_setting("enable_lead_gate", True)
        assistant_message_count = db.query(Message).filter(
            Message.conversation_id == conversation.id,
            Message.role == "assistant"
        ).count()

        show_lead_gate = enable_lead_gate and assistant_message_count >= 1 and not conversation.lead_id

        if show_lead_gate:
            lead_gate_msg = settings_mgr.get_setting(
                "lead_gate_message",
                "Before we keep going, where should we send your summary and how can we reach you?"
            )
            yield f"data: {json.dumps({'type': 'lead_gate', 'content': lead_gate_msg})}\n\n"
            return

        # Get context
        enable_rag = settings_mgr.get_setting("enable_rag", True)
        rag_chunk_limit = int(settings_mgr.get_setting("rag_chunk_limit", 3))

        # Web scraping
        web_content = []
        try:
            scraped_pages = web_scraper.search_site(request.message)
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
        context_chunks = rag_service.retrieve_relevant_chunks(request.message, limit=rag_chunk_limit) if enable_rag else []
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

        # Get AI settings
        system_prompt = settings_mgr.get_setting("system_prompt", "You are a helpful assistant.")
        model = settings_mgr.get_setting("openai_model", "gpt-4-turbo-preview")
        temperature = float(settings_mgr.get_setting("temperature", 0.7))
        max_tokens = int(settings_mgr.get_setting("max_tokens", 1000))
        api_key = settings_mgr.get_setting("openai_api_key", "")

        if not api_key or not api_key.strip():
            # Dev mode fallback
            yield f"data: {json.dumps({'type': 'content', 'content': 'Dev mode: No API key configured'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return

        # Stream from OpenAI
        from openai import OpenAI
        openai_client = OpenAI(api_key=api_key.strip())

        context_text = "\n\n".join([
            f"[{chunk.get('title', 'Unknown')}]\n{chunk.get('content', '')}"
            for chunk in all_context
        ])

        augmented_messages = [
            {"role": "system", "content": system_prompt}
        ]

        if context_text:
            augmented_messages.append({
                "role": "system",
                "content": f"KNOWLEDGE BASE CONTEXT:\n\n{context_text}"
            })

        augmented_messages.extend(message_history)

        stream = openai_client.chat.completions.create(
            model=model,
            messages=augmented_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )

        full_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"

        # Save assistant message
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=full_response,
            metadata={
                "context_chunks": len(all_context),
                "web_content_count": len(web_content)
            }
        )
        db.add(assistant_message)
        db.commit()

        # Send citations
        enable_citations = settings_mgr.get_setting("enable_citations", True)
        if enable_citations and all_context:
            citations = [
                {
                    "title": chunk.get("title"),
                    "date": chunk.get("published_date"),
                    "url": chunk.get("source_url")
                }
                for chunk in all_context
                if chunk.get("title")
            ]
            yield f"data: {json.dumps({'type': 'citations', 'citations': citations})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        print(f"✗ Streaming error: {e}")
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
