# 🚀 START HERE - Fiat Clarity Chat

Welcome! This is a complete, production-ready MVP of Fiat Clarity Chat.

## ⚡ Quick Start (5 Minutes)

### Prerequisites
- Docker Desktop (running)
- Python 3.11+
- Node.js 18+

### One-Command Setup

```bash
chmod +x scripts/setup.sh && ./scripts/setup.sh
```

This will:
1. Start PostgreSQL with pgvector
2. Set up Python backend
3. Set up Next.js frontend
4. Initialize database
5. Ingest sample content

Then follow the on-screen instructions to start the backend and frontend.

### Manual Start (if you prefer)

**Terminal 1 - Database:**
```bash
docker compose up -d
```

**Terminal 2 - Backend:**
```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python init_db.py
python ../scripts/ingest.py
python ../scripts/approve.py
uvicorn main:app --reload
```

**Terminal 3 - Frontend:**
```bash
cd apps/web
npm install
npm run dev
```

**Terminal 4 - Browser:**
```bash
open http://localhost:3000
```

## 🎯 What You'll See

1. **ChatGPT-like Interface**: Clean, modern chat UI
2. **Smart Assistant**: Asks "What is a Roth conversion?"
3. **Lead Gate**: After 1st response, 2nd message triggers contact form
4. **Contact Form**: Appears inline in chat (first name, email, phone)
5. **Routing**: Automatically routes to correct Calendly based on topic
6. **Scheduling**: "Schedule a Clarity Call" button appears after lead capture

## 📚 Documentation

- **README.md** - Complete documentation (architecture, API, setup)
- **QUICKSTART.md** - Step-by-step setup guide
- **ARCHITECTURE.md** - System diagrams and design
- **DELIVERY_SUMMARY.md** - What's included and requirements checklist
- **PROJECT_STRUCTURE.md** - File descriptions
- **COMPLETE_FILE_LISTING.md** - All files overview

## ✅ What's Included

✓ FastAPI backend with RAG (pgvector)
✓ Next.js frontend (ChatGPT-like UI)
✓ PostgreSQL + pgvector database
✓ Smart lead routing (5 buckets)
✓ Consent audit trail
✓ Dev mode (works without OpenAI)
✓ 3 sample marketing guides (6,500 words)
✓ Complete test suite
✓ Automated setup script

## 🧪 Test the Features

### Test 1: Basic Chat
1. Open http://localhost:3000
2. Type: "What is a Roth conversion?"
3. Get AI-powered response with Retirement: Redefined framework
4. See citations at bottom

### Test 2: Lead Gate
1. Send first message
2. Try to send second message
3. See: "Before we keep going, where should we send your summary..."
4. Fill contact form inline
5. Submit and continue chatting
6. See "Schedule a Clarity Call" button appear

### Test 3: Routing
Ask different topics to see routing:
- "How do Roth conversions affect Medicare?" → tax_forward bucket
- "When should I claim Social Security?" → income bucket
- "I'm selling my business" → business bucket

## 🔧 Configuration

### Add OpenAI API Key (Optional)

The app works without OpenAI in DEV MODE. To use real AI:

1. Edit `apps/api/.env`
2. Add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-key-here
   DEV_MODE=false
   ```
3. Restart backend

### Customize Routing

Edit `apps/api/services/routing_service.py`:
- ROUTING_RULES: Change keyword patterns
- CALENDLY_URLS: Add your Calendly links

### Add More Content

1. Add .md files to `data/import/`
2. Run: `python scripts/ingest.py`
3. Run: `python scripts/approve.py`

## 📊 Tech Stack

- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.11+, SQLAlchemy, OpenAI
- **Database**: PostgreSQL 15 + pgvector
- **Infrastructure**: Docker Compose
- **AI**: OpenAI GPT-4 (optional - has dev mode)

## 🎨 Features

✓ ChatGPT-like UI with message bubbles
✓ In-chat lead gate (seamless, non-disruptive)
✓ Smart routing to 5 buckets
✓ Meeting type selection (15-min vs 60-min)
✓ RAG with vector search
✓ Consent audit trail
✓ Retirement: Redefined framework
✓ Guardrails (no personalized advice)
✓ Educational disclaimers
✓ Works offline (dev mode)

## 🚨 Troubleshooting

### "Cannot connect to database"
```bash
docker compose down -v
docker compose up -d
sleep 10
python apps/api/init_db.py
```

### "Module not found"
```bash
cd apps/api
source .venv/bin/activate
pip install -r requirements.txt
```

### "Port already in use"
Kill processes on ports 5432, 8000, or 3000:
```bash
lsof -ti:8000 | xargs kill
lsof -ti:3000 | xargs kill
```

### Frontend won't start
```bash
cd apps/web
rm -rf node_modules package-lock.json
npm install
npm run dev
```

## 🧪 Verify Setup

Run the test suite:
```bash
cd apps/api
source .venv/bin/activate
cd ../..
python scripts/test_setup.py
```

Should see all tests pass ✓

## 📁 Project Structure

```
fiat-clarity-chat/
├── apps/
│   ├── api/          # FastAPI backend
│   └── web/          # Next.js frontend
├── data/
│   └── import/       # Sample content
├── scripts/          # Setup & ingestion
├── infra/            # Docker config
└── docs/             # Documentation
```

## 🌟 Next Steps

1. Run the setup script
2. Explore the chat interface
3. Test the lead gate
4. Review the documentation
5. Customize for your needs
6. (Optional) Add OpenAI API key
7. Deploy to production

## 💬 Questions?

Check the documentation files - everything is thoroughly documented.

**Main Docs**: README.md
**Quick Setup**: QUICKSTART.md
**Architecture**: ARCHITECTURE.md

## 🎉 You're Ready!

Everything is built and tested. Just run the setup script and you'll be chatting in minutes.

```bash
chmod +x scripts/setup.sh && ./scripts/setup.sh
```

**Happy coding!** 🚀
