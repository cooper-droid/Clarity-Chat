# Fiat Clarity Chat - Project Structure

Complete file tree and description of all components.

```
fiat-clarity-chat/
│
├── README.md                          # Main documentation
├── QUICKSTART.md                      # 5-minute setup guide
├── PROJECT_STRUCTURE.md               # This file
├── .gitignore                         # Git ignore rules
├── docker-compose.yml                 # PostgreSQL + pgvector
│
├── apps/
│   ├── api/                          # FastAPI Backend
│   │   ├── .env                      # Environment variables
│   │   ├── .env.example              # Environment template
│   │   ├── requirements.txt          # Python dependencies
│   │   ├── main.py                   # Main FastAPI app with all endpoints
│   │   ├── models.py                 # SQLAlchemy database models
│   │   ├── init_db.py                # Database initialization script
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── ai_provider.py        # OpenAI abstraction with dev mode
│   │       ├── rag_service.py        # RAG retrieval (vector + keyword search)
│   │       └── routing_service.py    # Lead routing and CRM logic
│   │
│   └── web/                          # Next.js Frontend
│       ├── .env.local                # Environment variables
│       ├── .gitignore                # Next.js specific ignores
│       ├── package.json              # Node dependencies
│       ├── tsconfig.json             # TypeScript config
│       ├── next.config.js            # Next.js config
│       ├── tailwind.config.ts        # Tailwind CSS config
│       ├── postcss.config.js         # PostCSS config
│       └── src/
│           ├── app/
│           │   ├── globals.css       # Global styles
│           │   ├── layout.tsx        # Root layout
│           │   └── page.tsx          # Home page
│           └── components/
│               ├── ChatInterface.tsx  # Main chat component
│               ├── MessageBubble.tsx  # Individual message display
│               ├── LeadForm.tsx       # In-chat contact form
│               └── ChatInput.tsx      # Message input field
│
├── infra/
│   └── docker-compose.yml            # Same as root (for organization)
│
├── data/
│   └── import/                       # Sample marketing content
│       ├── retirement-redefined.md
│       ├── roth-conversions-irmaa.md
│       └── social-security-timing.md
│
└── scripts/
    ├── setup.sh                      # Automated setup script
    ├── ingest.py                     # Document ingestion
    └── approve.py                    # Document approval
```

## Key Components

### Backend (FastAPI)

**main.py**
- POST /chat - Main chat endpoint
- POST /lead - Lead capture with routing
- GET /health - Health check
- POST /admin/ingest - Document ingestion
- POST /admin/approve/{doc_id} - Document approval

**models.py**
- Document: Source content with approval workflow
- Chunk: Vector embeddings for RAG
- Conversation: Chat sessions
- Message: Individual chat messages
- Lead: Contact information and routing
- ConsentEvent: Audit trail for compliance

**services/ai_provider.py**
- OpenAI integration with graceful fallback
- DEV MODE: Works without API key using deterministic responses
- Generates embeddings and chat completions

**services/rag_service.py**
- Vector search using pgvector (production)
- Keyword search fallback (dev mode)
- Retrieves top-k relevant chunks

**services/routing_service.py**
- Routes leads to buckets: tax_forward, income, business, estate, general
- Determines meeting type: 15-min call or 60-min visit
- Returns appropriate Calendly URL

### Frontend (Next.js)

**ChatInterface.tsx**
- Main orchestration component
- Manages conversation state
- Handles lead gate logic
- Shows "Schedule a Clarity Call" button after lead capture

**MessageBubble.tsx**
- Renders user and assistant messages
- ChatGPT-like styling
- Citations display
- Loading animation

**LeadForm.tsx**
- In-chat contact capture form
- First name, email, phone fields
- Disclosure text (no checkboxes)
- Styled to match ChatGPT aesthetic

**ChatInput.tsx**
- Text input with send button
- Enter to send, Shift+Enter for new line
- Disabled state when lead gate active

### Database Schema

**documents**
- id, title, content, status, source_url, published_date, metadata

**chunks**
- id, document_id, content, chunk_index, token_count, embedding (vector)

**conversations**
- id, session_id, lead_id, metadata

**messages**
- id, conversation_id, role, content, metadata

**leads**
- id, first_name, email, phone, bucket, meeting_type, booking_url, metadata

**consent_events**
- id, lead_id, event_type, ip_address, user_agent, disclosure_text, created_at

### Sample Data

**retirement-redefined.md**
- Explains the "Retirement: Redefined" framework
- Three-part structure: Today → Options → Next Steps

**roth-conversions-irmaa.md**
- Deep dive on Roth conversions and Medicare IRMAA surcharges
- Strategic approaches for different scenarios

**social-security-timing.md**
- Comprehensive guide to Social Security claiming strategies
- Break-even analysis and decision framework

## Data Flow

### Chat Flow
1. User sends message via ChatInput
2. ChatInterface calls POST /chat
3. Backend checks if lead gate needed (after 1st assistant response)
4. If lead gate: Return lead gate message, show LeadForm
5. If normal: RAG retrieval → AI response → return with citations
6. Frontend renders MessageBubble with response

### Lead Capture Flow
1. User fills LeadForm (first_name, email, phone)
2. Frontend calls POST /lead
3. Backend routes lead based on conversation content
4. Creates/updates Lead record
5. Creates ConsentEvent audit trail
6. Returns booking_url
7. Frontend shows "Schedule a Clarity Call" button
8. User can continue chatting

### Ingestion Flow
1. Run `python scripts/ingest.py`
2. Reads .md files from data/import/
3. Calls POST /admin/ingest for each file
4. Backend chunks content (300-800 tokens)
5. Generates embeddings (or skips in dev mode)
6. Stores Document + Chunks (status: draft)
7. Run `python scripts/approve.py`
8. Calls POST /admin/approve/{doc_id}
9. Sets status: approved
10. Now retrievable in chat

## Environment Variables

**Backend (.env)**
```
DATABASE_URL=postgresql://fiat:fiat123@localhost:5432/fiat_clarity
OPENAI_API_KEY=                      # Optional - runs in DEV MODE without it
DEV_MODE=true                        # Set false to use OpenAI
```

**Frontend (.env.local)**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Development Workflow

1. Start database: `docker compose up -d`
2. Initialize DB: `python apps/api/init_db.py`
3. Ingest content: `python scripts/ingest.py && python scripts/approve.py`
4. Start backend: `cd apps/api && uvicorn main:app --reload`
5. Start frontend: `cd apps/web && npm run dev`
6. Open http://localhost:3000

## Production Checklist

Before deploying:
- [ ] Add real OPENAI_API_KEY
- [ ] Set DEV_MODE=false
- [ ] Change database password
- [ ] Configure CORS origins
- [ ] Add rate limiting
- [ ] Enable HTTPS
- [ ] Add authentication for admin endpoints
- [ ] Replace mock Calendly URLs with real ones
- [ ] Integrate with real CRM
- [ ] Set up monitoring
- [ ] Configure logging
- [ ] Add error tracking (Sentry, etc.)
- [ ] Set up backup strategy
- [ ] Review and test guardrails

## Testing the Lead Gate

1. Open app, send first message: "What is a Roth conversion?"
2. Receive response with framework + citations
3. Try to send second message
4. See lead gate: "Before we keep going..."
5. Fill in contact form
6. Submit
7. See confirmation: "Thank you, [name]!"
8. Your pending message is sent automatically
9. "Schedule a Clarity Call" button appears
10. Continue chatting normally

## Testing Routing

Different topics route to different buckets:

**Tax/Roth/IRMAA** → tax_forward bucket
- Try: "How do Roth conversions affect Medicare premiums?"

**Retirement Income/Social Security** → income bucket
- Try: "When should I claim Social Security?"

**Business Owner** → business bucket
- Try: "I'm selling my business, how do I plan for taxes?"

**Estate/Legacy** → estate bucket
- Try: "How do I set up a trust for my grandchildren?"

**Urgency triggers** → 60-min Clarity Visit
- Try: "I'm retiring in 3 months and need help planning"

**Default** → general bucket
- Try: "Tell me about retirement planning"

Check the booking_url in the response to see routing in action.

## Extending the System

### Add New Content
1. Create .md file in data/import/
2. Run `python scripts/ingest.py`
3. Run `python scripts/approve.py`

### Customize Routing Rules
Edit `apps/api/services/routing_service.py`:
- ROUTING_RULES: Add patterns for new buckets
- URGENCY_PATTERNS: Add triggers for 60-min meetings
- CALENDLY_URLS: Update URLs for your Calendly account

### Customize System Prompt
Edit SYSTEM_PROMPT in `apps/api/main.py` to change:
- Tone and style
- Framework structure
- Guardrails
- CTAs

### Add New Endpoints
Add routes to `apps/api/main.py`:
```python
@app.post("/your-endpoint")
async def your_endpoint(...):
    # Your logic
    pass
```

### Modify UI
Edit components in `apps/web/src/components/`:
- ChatInterface.tsx: Overall layout and flow
- MessageBubble.tsx: Message styling
- LeadForm.tsx: Contact form fields
- ChatInput.tsx: Input behavior

## Troubleshooting

See QUICKSTART.md for common issues and solutions.
