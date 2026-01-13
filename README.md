# Fiat Clarity Chat

A local-first, ChatGPT-like conversational interface for Fiat Wealth Management prospects. Built with Next.js, FastAPI, PostgreSQL, and pgvector for RAG-powered responses.

## Features

- **ChatGPT-like UI**: Clean chat interface with message bubbles, streaming responses, and scrollable history
- **In-Chat Lead Gate**: After first response, collect contact info inline without breaking the chat flow
- **RAG Knowledge Base**: Vector search over approved marketing content with citations
- **Retirement: Redefined Framework**: Structured responses (Today → Options → Next Steps)
- **Smart Routing**: Automatically route leads to appropriate Calendly links based on conversation topic
- **Consent Audit Trail**: Track all consent events with IP, user agent, timestamp
- **Dev Mode**: Works without OpenAI API key using deterministic responses

## Tech Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15 + pgvector
- **AI**: OpenAI GPT-4 (optional, has dev mode fallback)
- **Infrastructure**: Docker Compose

## Quick Start

### Prerequisites

- Docker Desktop
- Node.js 18+ and npm
- Python 3.11+
- (Optional) OpenAI API key

### 1. Start Infrastructure

```bash
cd fiat-clarity-chat
docker compose up -d
```

This starts PostgreSQL with pgvector on port 5432.

### 2. Start Backend

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python init_db.py  # Run migrations
uvicorn main:app --reload --port 8000
```

Backend runs at http://localhost:8000

### 3. Ingest Sample Data

In a new terminal (from project root):

```bash
cd fiat-clarity-chat
source apps/api/.venv/bin/activate
python scripts/ingest.py
python scripts/approve.py
```

### 4. Start Frontend

In a new terminal:

```bash
cd apps/web
npm install
npm run dev
```

Frontend runs at http://localhost:3000

## Configuration

### Environment Variables

**Backend** (`apps/api/.env`):
```env
DATABASE_URL=postgresql://fiat:fiat123@localhost:5432/fiat_clarity
OPENAI_API_KEY=sk-...  # Optional - runs in DEV MODE without this
DEV_MODE=true  # Set to false when you have OpenAI key
```

**Frontend** (`apps/web/.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Usage

1. Open http://localhost:3000
2. Type a question (e.g., "What is a Roth conversion?")
3. Receive AI-powered response with citations
4. On second message attempt, you'll be prompted for contact info inline
5. Submit contact details to continue chatting
6. Click "Schedule a Clarity Call" to get routed to appropriate Calendly link

## API Endpoints

- `POST /chat` - Send a chat message
- `POST /lead` - Create/update lead with contact info
- `GET /health` - Health check
- `POST /admin/ingest` - Ingest documents
- `POST /admin/approve/{doc_id}` - Approve document for retrieval

## Architecture

### Database Schema

- **documents**: Source content (status: draft/approved/archived)
- **chunks**: Vector embeddings for RAG retrieval
- **conversations**: Chat sessions
- **messages**: Individual messages
- **leads**: Contact information
- **consent_events**: Audit trail for consent capture

### RAG Pipeline

1. Chunk documents semantically (300-800 tokens)
2. Generate embeddings with OpenAI text-embedding-3-small
3. Store in pgvector
4. Retrieve top 3 relevant chunks per query
5. Generate response with GPT-4
6. Include citations (title, date, URL)

### Routing Logic

| Topic Pattern | Bucket | Default Meeting |
|--------------|--------|-----------------|
| Tax, Roth, IRMAA | tax_forward | 15-min Clarity Call |
| Retirement income, Social Security | income | 15-min Clarity Call |
| Business owner, liquidity event | business | 60-min Clarity Visit |
| Estate, legacy | estate | 15-min Clarity Call |
| Retiring within 12 months | (any) | 60-min Clarity Visit |
| Unknown | general | 15-min Clarity Call |

### Dev Mode

When `OPENAI_API_KEY` is missing or `DEV_MODE=true`:
- Uses deterministic placeholder responses
- Falls back to keyword search for retrieval
- Still stores conversations and leads
- Full UI functionality works

## Project Structure

```
fiat-clarity-chat/
├── apps/
│   ├── api/                 # FastAPI backend
│   │   ├── main.py         # Main app & endpoints
│   │   ├── models.py       # SQLAlchemy models
│   │   ├── services/       # Business logic
│   │   ├── init_db.py      # Database initialization
│   │   └── requirements.txt
│   └── web/                # Next.js frontend
│       ├── src/
│       │   ├── app/        # App router
│       │   └── components/ # React components
│       └── package.json
├── infra/
│   └── docker-compose.yml  # PostgreSQL + pgvector
├── data/
│   └── import/             # Sample markdown content
├── scripts/
│   ├── ingest.py          # Document ingestion
│   └── approve.py         # Approve all documents
└── README.md
```

## Guardrails

The bot will NOT:
- Provide personalized investment, tax, or legal advice
- Recommend specific buy/sell/hold actions
- Suggest exact dollar amounts for conversions
- Make decisions for users

Instead, it:
- Educates on factors and tradeoffs
- Asks clarifying questions
- Provides checklists and frameworks
- Always encourages scheduling with an advisor

## Development

### Adding New Content

1. Add markdown files to `data/import/`
2. Run `python scripts/ingest.py`
3. Run `python scripts/approve.py` to make searchable

### Testing Without OpenAI

Set `DEV_MODE=true` in `apps/api/.env` - the system will use placeholder responses and keyword search.

### Database Migrations

Migrations are applied automatically via `init_db.py`. To reset:

```bash
docker compose down -v
docker compose up -d
cd apps/api
python init_db.py
```

## Production Considerations

Before deploying to production:

1. Set strong database password
2. Add `OPENAI_API_KEY`
3. Set `DEV_MODE=false`
4. Configure CORS origins
5. Add rate limiting
6. Enable HTTPS
7. Set up real CRM integration (replace mock)
8. Configure actual Calendly links
9. Add authentication for admin endpoints
10. Set up monitoring and logging

## License

Proprietary - Fiat Wealth Management
