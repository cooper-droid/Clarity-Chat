# Deployment Guide - Render

This guide will help you deploy Clarity Chat to Render with PostgreSQL database.

## Prerequisites

1. GitHub account with your code pushed to repository
2. Render account (sign up at https://render.com)
3. OpenAI API key

## Step 1: Create Render Account

1. Go to https://render.com
2. Sign up with your GitHub account
3. Authorize Render to access your repositories

## Step 2: Deploy Using Blueprint (Automated)

Render will automatically detect the `render.yaml` file and set up all services.

1. Go to your Render Dashboard
2. Click "New +"
3. Select "Blueprint"
4. Connect your GitHub repository: `cooper-droid/Clarity-Chat`
5. Render will detect `render.yaml` and show you:
   - **clarity-db** (PostgreSQL Database)
   - **clarity-api** (FastAPI Backend)
   - **clarity-chat-frontend** (Next.js Frontend)

## Step 3: Set Environment Variables

After blueprint is created, you need to set these environment variables:

### For `clarity-api` service:
- `OPENAI_API_KEY`: Your OpenAI API key
- `DATABASE_URL`: (Auto-populated from database connection)
- `DEV_MODE`: false (already set)

### For `clarity-chat-frontend` service:
- `NEXT_PUBLIC_API_URL`: Your backend URL (e.g., `https://clarity-api.onrender.com`)
- `NODE_ENV`: production (already set)

To set environment variables:
1. Click on each service in your Render dashboard
2. Go to "Environment" tab
3. Add the variables listed above
4. Click "Save Changes"

## Step 4: Initialize Database

Once the database and API are deployed:

1. Go to the `clarity-api` service in Render
2. Click on "Shell" tab
3. Run the database initialization:
   ```bash
   cd apps/api
   python init_db.py
   ```

This will create all necessary tables in PostgreSQL.

## Step 5: Enable pgvector Extension

For RAG functionality, enable the pgvector extension:

1. Go to your `clarity-db` database in Render dashboard
2. Click "Connect" and copy the External Database URL
3. Use a PostgreSQL client (like psql or DBeaver) to connect
4. Run this SQL command:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

Alternatively, Render may have pgvector already enabled.

## Step 6: Seed Production Database

Once your API is deployed and healthy, seed it with your retirement planning documents:

```bash
python scripts/seed_production.py https://clarity-api.onrender.com
```

This will:
1. Upload all markdown files from `data/import/`
2. Create vector embeddings for each document
3. Approve documents for RAG retrieval

**Expected output:**
```
🌱 SEEDING PRODUCTION DATABASE
API URL: https://clarity-api.onrender.com

🔍 Checking API health... ✓ API is healthy

📚 Found 3 document(s) to ingest

📄 Ingesting: Retirement Redefined... ✓ (12 chunks)
📄 Ingesting: Roth Conversions Irmaa... ✓ (18 chunks)
📄 Ingesting: Social Security Timing... ✓ (24 chunks)

✓ 3/3 documents approved and ready for RAG

Your production database is now seeded! 🚀
```

## Step 7: Test Your Deployment

1. **Test API**: Visit `https://clarity-api.onrender.com/health`
   - Should return: `{"status": "healthy", "database": "connected"}`

2. **Test Frontend**: Visit `https://clarity-chat-frontend.onrender.com`
   - Should load the landing page

3. **Test Chat**: Ask a question on the frontend
   - Should receive streaming responses with RAG-powered answers

## Step 8: Custom Domain (Optional)

To use a custom domain:

1. Go to your frontend service in Render
2. Click "Settings" → "Custom Domain"
3. Add your domain (e.g., `chat.fiatclarity.com`)
4. Follow DNS configuration instructions

## Troubleshooting

### API won't start
- Check logs in Render dashboard for `clarity-api`
- Verify `OPENAI_API_KEY` is set correctly
- Ensure database connection is successful

### Frontend can't connect to API
- Verify `NEXT_PUBLIC_API_URL` points to your API service
- Check CORS settings in `main.py` allow your frontend domain
- Check API logs for errors

### Database connection errors
- Verify database service is running
- Check `DATABASE_URL` is correctly set
- Ensure database initialization was completed

### Cold starts (Free Tier)
- Free tier services spin down after 15 minutes of inactivity
- First request after spin-down will be slow (30-60 seconds)
- Upgrade to paid tier ($7/month per service) to eliminate cold starts

## Costs

**Free Tier**:
- Database: 90 days free trial, then $7/month
- API: Free with spin-down after 15 min inactivity
- Frontend: Free with spin-down after 15 min inactivity

**Recommended Production Setup** (~$21/month):
- Database (Starter): $7/month
- API (Starter): $7/month
- Frontend (Starter): $7/month

## Next Steps

1. Set up continuous deployment (auto-deploy on GitHub push)
2. Configure monitoring and alerts
3. Set up backup strategy for database
4. Configure SSL certificates (automatic on Render)
5. Add custom domain

## Support

For issues specific to Render, check:
- Render Docs: https://render.com/docs
- Render Community: https://community.render.com

For application issues, check the GitHub repository issues.
