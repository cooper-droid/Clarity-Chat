# Fiat Clarity Chat - Quick Start Guide

Get the app running in 5 minutes.

## Prerequisites

- Docker Desktop (running)
- Python 3.11+
- Node.js 18+

## Method 1: Automatic Setup (Recommended)

```bash
cd fiat-clarity-chat
chmod +x scripts/setup.sh
./scripts/setup.sh
```

Then follow the on-screen instructions to start the backend and frontend.

## Method 2: Manual Setup

### Step 1: Start Database

```bash
docker compose up -d
```

Wait 10 seconds for PostgreSQL to initialize.

### Step 2: Setup Backend

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python init_db.py
```

### Step 3: Ingest Sample Data

```bash
# From project root, with backend venv activated
python scripts/ingest.py
python scripts/approve.py
```

### Step 4: Setup Frontend

```bash
cd apps/web
npm install
```

### Step 5: Start Everything

**Terminal 1 - Backend:**
```bash
cd apps/api
source .venv/bin/activate
uvicorn main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd apps/web
npm run dev
```

**Terminal 3 - Open Browser:**
```bash
open http://localhost:3000
```

## Try It Out

1. Type a question: "What is a Roth conversion?"
2. Get an AI-powered response with citations
3. Try to send a second message
4. Fill in the contact form that appears in-chat
5. Continue chatting
6. Click "Schedule a Clarity Call" to see routing in action

## Troubleshooting

### Database connection error
```bash
docker compose down -v
docker compose up -d
# Wait 10 seconds
python apps/api/init_db.py
```

### "Module not found" error
```bash
cd apps/api
source .venv/bin/activate
pip install -r requirements.txt
```

### Frontend won't start
```bash
cd apps/web
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### No responses from AI
Check `apps/api/.env`:
```
DEV_MODE=true
```

This is expected—the app works without OpenAI. To use real AI, add your API key.

## What's Next?

- Read the full [README.md](README.md) for architecture details
- Add your `OPENAI_API_KEY` to use real AI
- Customize the sample content in `data/import/`
- Explore the routing rules in `apps/api/services/routing_service.py`

## Support

Issues? Check:
1. Docker Desktop is running
2. No other services on ports 5432, 8000, or 3000
3. Python venv is activated when running backend commands
4. All dependencies are installed

Still stuck? Check the logs:
- Backend: Look at the uvicorn output
- Frontend: Look at the Next.js terminal
- Database: `docker logs fiat-clarity-db`
