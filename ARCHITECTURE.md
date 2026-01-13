# Fiat Clarity Chat - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                           USER BROWSER                           │
│                      http://localhost:3000                       │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Next.js Frontend (React)                   │    │
│  │                                                          │    │
│  │  • ChatInterface (orchestration)                        │    │
│  │  • MessageBubble (rendering)                            │    │
│  │  • LeadForm (contact capture)                           │    │
│  │  • ChatInput (user input)                               │    │
│  └────────────────────────────────────────────────────────┘    │
└───────────────────────┬─────────────────────────────────────────┘
                        │ HTTP/JSON
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Python)                      │
│                      http://localhost:8000                       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │                  API Endpoints                        │      │
│  │                                                        │      │
│  │  POST /chat           - Message handling             │      │
│  │  POST /lead           - Lead capture + routing       │      │
│  │  GET  /health         - Health check                 │      │
│  │  POST /admin/ingest   - Document ingestion           │      │
│  │  POST /admin/approve  - Document approval            │      │
│  └─────────────┬────────────────────────────────────────┘      │
│                │                                                 │
│  ┌─────────────▼──────────────────────────────────────┐        │
│  │              Business Logic Services                │        │
│  │                                                      │        │
│  │  ┌─────────────────────────────────────────────┐   │        │
│  │  │  AI Provider Service                        │   │        │
│  │  │  • OpenAI integration                       │   │        │
│  │  │  • Dev mode fallback                        │   │        │
│  │  │  • Embedding generation                     │   │        │
│  │  │  • Chat completion                          │   │        │
│  │  └─────────────────────────────────────────────┘   │        │
│  │                                                      │        │
│  │  ┌─────────────────────────────────────────────┐   │        │
│  │  │  RAG Service                                │   │        │
│  │  │  • Vector search (pgvector)                 │   │        │
│  │  │  • Keyword search fallback                  │   │        │
│  │  │  • Top-k retrieval                          │   │        │
│  │  │  • Citation extraction                      │   │        │
│  │  └─────────────────────────────────────────────┘   │        │
│  │                                                      │        │
│  │  ┌─────────────────────────────────────────────┐   │        │
│  │  │  Routing Service                            │   │        │
│  │  │  • Topic classification                     │   │        │
│  │  │  • Bucket assignment                        │   │        │
│  │  │  • Meeting type selection                   │   │        │
│  │  │  • Calendly URL generation                  │   │        │
│  │  └─────────────────────────────────────────────┘   │        │
│  └──────────────────────────────────────────────────┘        │
└───────────────────────┬─────────────────────────────────────────┘
                        │ SQL/Vector Queries
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│           PostgreSQL 15 + pgvector Extension                     │
│                    localhost:5432                                │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  documents   │  │ conversations│  │    leads     │         │
│  │              │  │              │  │              │         │
│  │ • id         │  │ • id         │  │ • id         │         │
│  │ • title      │  │ • session_id │  │ • first_name │         │
│  │ • content    │  │ • lead_id    │  │ • email      │         │
│  │ • status     │  │ • metadata   │  │ • phone      │         │
│  │ • metadata   │  └──────────────┘  │ • bucket     │         │
│  └──────────────┘                     │ • meeting_type│        │
│                                       │ • booking_url│         │
│  ┌──────────────┐  ┌──────────────┐  └──────────────┘         │
│  │   chunks     │  │   messages   │                            │
│  │              │  │              │  ┌──────────────┐         │
│  │ • id         │  │ • id         │  │consent_events│         │
│  │ • document_id│  │ • conv_id    │  │              │         │
│  │ • content    │  │ • role       │  │ • id         │         │
│  │ • embedding  │  │ • content    │  │ • lead_id    │         │
│  │   (vector)   │  │ • metadata   │  │ • ip_address │         │
│  └──────────────┘  └──────────────┘  │ • user_agent │         │
│                                       │ • disclosure │         │
│                                       └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## Request Flow Diagrams

### 1. Initial Chat Message Flow

```
User                 Frontend              Backend              RAG Service        AI Provider        Database
 │                      │                     │                      │                  │                │
 │  Type message        │                     │                      │                  │                │
 ├─────────────────────>│                     │                      │                  │                │
 │                      │  POST /chat         │                      │                  │                │
 │                      ├────────────────────>│                      │                  │                │
 │                      │                     │  Create/get conv     │                  │                │
 │                      │                     ├─────────────────────────────────────────>│                │
 │                      │                     │                      │                  │  SELECT conv   │
 │                      │                     │<─────────────────────────────────────────┤                │
 │                      │                     │  Save user message   │                  │                │
 │                      │                     ├─────────────────────────────────────────>│                │
 │                      │                     │                      │                  │  INSERT message│
 │                      │                     │  Check if lead gate  │                  │                │
 │                      │                     │  needed              │                  │                │
 │                      │                     ├────┐                 │                  │                │
 │                      │                     │    │ Count assistant │                  │                │
 │                      │                     │<───┘ messages        │                  │                │
 │                      │                     │                      │                  │                │
 │                      │                     │  retrieve_chunks()   │                  │                │
 │                      │                     ├─────────────────────>│                  │                │
 │                      │                     │                      │  generate_embed  │                │
 │                      │                     │                      ├─────────────────>│                │
 │                      │                     │                      │  [1536 floats]   │                │
 │                      │                     │                      │<─────────────────┤                │
 │                      │                     │                      │  Vector search   │                │
 │                      │                     │                      ├──────────────────────────────────>│
 │                      │                     │                      │  Top 3 chunks    │                │
 │                      │                     │                      │<──────────────────────────────────┤
 │                      │                     │  [chunks with meta]  │                  │                │
 │                      │                     │<─────────────────────┤                  │                │
 │                      │                     │  generate_response() │                  │                │
 │                      │                     ├────────────────────────────────────────>│                │
 │                      │                     │                      │  GPT-4 call      │                │
 │                      │                     │                      │  (with context)  │                │
 │                      │                     │  Response text       │                  │                │
 │                      │                     │<────────────────────────────────────────┤                │
 │                      │                     │  Save assistant msg  │                  │                │
 │                      │                     ├─────────────────────────────────────────>│                │
 │                      │                     │                      │                  │  INSERT message│
 │                      │  JSON response      │                      │                  │                │
 │                      │<────────────────────┤                      │                  │                │
 │  Display message     │                     │                      │                  │                │
 │<─────────────────────┤                     │                      │                  │                │
```

### 2. Lead Gate Flow

```
User                 Frontend              Backend              Routing Service      Database
 │                      │                     │                       │                  │
 │  Send 2nd message    │                     │                       │                  │
 ├─────────────────────>│                     │                       │                  │
 │                      │  POST /chat         │                       │                  │
 │                      ├────────────────────>│                       │                  │
 │                      │                     │  Check assistant count│                  │
 │                      │                     ├──────────────────────────────────────────>│
 │                      │                     │  count >= 1           │                  │
 │                      │                     │<──────────────────────────────────────────┤
 │                      │                     │  Check if lead exists │                  │
 │                      │                     ├──────────────────────────────────────────>│
 │                      │                     │  lead_id = null       │                  │
 │                      │                     │<──────────────────────────────────────────┤
 │                      │                     │  ✓ Show lead gate!    │                  │
 │                      │  {show_lead_gate: true}│                    │                  │
 │                      │<────────────────────┤                       │                  │
 │  Show lead form      │                     │                       │                  │
 │<─────────────────────┤                     │                       │                  │
 │                      │                     │                       │                  │
 │  Fill form & submit  │                     │                       │                  │
 ├─────────────────────>│                     │                       │                  │
 │                      │  POST /lead         │                       │                  │
 │                      ├────────────────────>│                       │                  │
 │                      │                     │  route_lead()         │                  │
 │                      │                     ├──────────────────────>│                  │
 │                      │                     │                       │  Get transcript  │
 │                      │                     │                       ├─────────────────>│
 │                      │                     │                       │  messages[]      │
 │                      │                     │                       │<─────────────────┤
 │                      │                     │                       │  Analyze topics  │
 │                      │                     │                       ├────┐             │
 │                      │                     │                       │    │ Apply regex │
 │                      │                     │                       │<───┘ patterns    │
 │                      │                     │                       │  Determine bucket│
 │                      │                     │                       │  & meeting type  │
 │                      │                     │  {bucket, url, ...}   │                  │
 │                      │                     │<──────────────────────┤                  │
 │                      │                     │  Create/update lead   │                  │
 │                      │                     ├──────────────────────────────────────────>│
 │                      │                     │  Create consent event │                  │
 │                      │                     ├──────────────────────────────────────────>│
 │                      │                     │  Link conv to lead    │                  │
 │                      │                     ├──────────────────────────────────────────>│
 │                      │  {booking_url}      │                       │                  │
 │                      │<────────────────────┤                       │                  │
 │  Show "Schedule"     │                     │                       │                  │
 │  button & continue   │                     │                       │                  │
 │<─────────────────────┤                     │                       │                  │
```

### 3. Document Ingestion Flow

```
Admin              Script (ingest.py)    Backend              AI Provider        Database
 │                      │                     │                      │                │
 │  Run ingest.py       │                     │                      │                │
 ├─────────────────────>│                     │                      │                │
 │                      │  Read .md files     │                      │                │
 │                      ├────┐                │                      │                │
 │                      │    │ Parse content  │                      │                │
 │                      │<───┘                │                      │                │
 │                      │  POST /admin/ingest │                      │                │
 │                      ├────────────────────>│                      │                │
 │                      │                     │  Create document     │                │
 │                      │                     ├─────────────────────────────────────>│
 │                      │                     │  (status: draft)     │                │
 │                      │                     │  Chunk content       │                │
 │                      │                     ├────┐                 │                │
 │                      │                     │    │ 300-800 tokens  │                │
 │                      │                     │<───┘ per chunk       │                │
 │                      │                     │  For each chunk:     │                │
 │                      │                     │  generate_embedding()│                │
 │                      │                     ├─────────────────────>│                │
 │                      │                     │  [1536 floats]       │                │
 │                      │                     │<─────────────────────┤                │
 │                      │                     │  Insert chunk        │                │
 │                      │                     ├─────────────────────────────────────>│
 │                      │  {doc_id, chunks}   │  (with embedding)    │                │
 │                      │<────────────────────┤                      │                │
 │  ✓ Ingested          │                     │                      │                │
 │<─────────────────────┤                     │                      │                │
 │                      │                     │                      │                │
 │  Run approve.py      │                     │                      │                │
 ├─────────────────────>│                     │                      │                │
 │                      │  POST /admin/approve│                      │                │
 │                      ├────────────────────>│                      │                │
 │                      │                     │  UPDATE status       │                │
 │                      │                     ├─────────────────────────────────────>│
 │                      │                     │  (draft -> approved) │                │
 │                      │  Success            │                      │                │
 │                      │<────────────────────┤                      │                │
 │  ✓ Approved          │                     │                      │                │
 │<─────────────────────┤                     │                      │                │
```

## Component Responsibilities

### Frontend Components

**ChatInterface.tsx**
- Session management
- Message history state
- Lead gate logic
- API communication
- Booking URL handling

**MessageBubble.tsx**
- Message rendering (user vs assistant)
- Citation display
- Loading animation
- Markdown-like formatting

**LeadForm.tsx**
- Form validation
- Submit handling
- Disclosure text display
- Error handling

**ChatInput.tsx**
- Text input
- Enter/Shift+Enter handling
- Disabled state management
- Send button

### Backend Services

**AI Provider Service**
- OpenAI client initialization
- Embedding generation (text-embedding-3-small)
- Chat completion (GPT-4)
- Dev mode fallback with deterministic responses
- Error handling and retries

**RAG Service**
- Vector similarity search using pgvector
- Keyword search fallback
- Chunk retrieval and ranking
- Citation extraction
- Approved-only filtering

**Routing Service**
- Transcript analysis
- Regex pattern matching
- Bucket classification (5 buckets)
- Meeting type determination (15-min vs 60-min)
- Calendly URL generation
- Lead upsert logic

## Database Design

### Key Relationships

```
documents 1───┐
              │
              │ has many
              │
              └───> chunks (with vector embeddings)

conversations 1───┐
                  │
                  │ has many
                  │
                  └───> messages

leads 1───┬───> consent_events (audit trail)
          │
          └───> conversations (after capture)
```

### Vector Search Index

```sql
-- pgvector cosine similarity index
CREATE INDEX chunks_embedding_idx
ON chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Query example:
SELECT * FROM chunks
ORDER BY embedding <=> '[query_embedding]'::vector
LIMIT 3;
```

## Security & Compliance

### Consent Audit Trail

Every lead capture creates a consent_event record:

```json
{
  "lead_id": 123,
  "event_type": "lead_capture",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "page_url": "http://localhost:3000",
  "disclosure_text": "By continuing, you agree...",
  "disclosure_version": "v1.0",
  "timestamp": "2024-01-09T10:30:00Z"
}
```

### Guardrails Implementation

System prompt includes:
- "Provide educational information only"
- "Never recommend specific buy/sell/hold actions"
- "Never suggest exact dollar amounts"
- "Always remind users to not share sensitive info"

All responses are filtered through the Retirement: Redefined framework to ensure consistency.

## Performance Considerations

### Chunking Strategy
- Paragraph-based splitting
- Target: 300-800 tokens per chunk
- Overlap: None (simple MVP implementation)
- Upgrade path: Semantic chunking with sentence transformers

### Vector Search
- pgvector with IVFFlat index
- Top-k=3 (configurable)
- Cosine similarity metric
- Fallback to keyword search if no embeddings

### Caching Opportunities (Future)
- Conversation state (Redis)
- Frequent queries (in-memory cache)
- Embedding cache (avoid re-generating)

## Deployment Architecture (Production)

```
┌─────────────────────────────────────────────────────────────┐
│                      Load Balancer (HTTPS)                  │
└────────────────────┬───────────────────┬────────────────────┘
                     │                   │
         ┌───────────▼──────────┐   ┌───▼────────────────┐
         │   Next.js (Vercel)   │   │  FastAPI (Docker)  │
         │   - CDN              │   │  - Multiple pods   │
         │   - Auto-scaling     │   │  - Health checks   │
         └──────────────────────┘   └────┬───────────────┘
                                          │
                          ┌───────────────▼──────────────┐
                          │  PostgreSQL (Managed)        │
                          │  - RDS / Supabase            │
                          │  - pgvector extension        │
                          │  - Automated backups         │
                          └──────────────────────────────┘
```

## Error Handling

### API Errors
- 500: Internal server error → return friendly message
- 404: Not found → guide user back to chat
- 422: Validation error → show field-level errors

### AI Provider Errors
- No API key → Auto-enable dev mode
- Rate limit → Queue and retry
- Timeout → Return cached response or error

### Database Errors
- Connection lost → Retry with exponential backoff
- Constraint violation → Upsert instead of insert

## Monitoring Points

### Key Metrics
- Chat response time (target: <2s)
- Vector search latency (target: <200ms)
- Lead conversion rate
- API error rate
- Database connection pool usage

### Logs to Capture
- All chat messages (for debugging)
- Lead captures (for CRM sync)
- Routing decisions (for optimization)
- AI provider calls (for cost tracking)
- Errors and exceptions (for alerting)

## Future Enhancements

1. **Streaming responses**: SSE or WebSockets
2. **Multi-turn context**: Better conversation memory
3. **Semantic chunking**: Improved retrieval quality
4. **Authentication**: User accounts
5. **Analytics**: Dashboards and reporting
6. **A/B testing**: Routing rules optimization
7. **Real CRM**: Salesforce/HubSpot integration
8. **Email follow-up**: Automated nurture sequences
9. **Calendar embed**: In-app scheduling
10. **Mobile app**: React Native version

---

This architecture is designed to be simple, maintainable, and scalable from local MVP to production deployment.
