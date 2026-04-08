# Blog Automation System

AI-powered blog generation pipeline that creates 10–30 SEO-optimised posts daily and distributes them across multiple websites.

## Architecture

```
┌──────────────────────────┐     ┌──────────────────────┐
│  Friend's LLM Server    │     │   Your Machine       │
│  (Ollama + Llama 3.1)   │◄────│   FastAPI Generator  │
│  http://friends-ip:11434 │     │   + Scheduler        │
└──────────────────────────┘     └──────┬───────────────┘
                                       │ inserts posts
                              ┌────────▼────────┐
                              │   Supabase (DB)  │──► Sanity CMS
                              │   per website    │    per website
                              └────────┬────────┘
                                       │ reads content
                              ┌────────▼────────┐
                              │  Next.js 15     │
                              │  (Vercel)       │
                              └─────────────────┘
```

## Quick Start

### 1. Prerequisites

- Docker & Docker Compose
- Node.js 18+
- A Supabase project (per website)
- A Sanity project (per website)
- Access to friend's Ollama API (`http://<ip>:11434`)

### 2. Set Up Supabase

For **each website**, run the migration SQL in the Supabase SQL Editor:

```bash
# Copy the contents of supabase/migrations/001_create_tables.sql
# Paste into: https://supabase.com/dashboard → SQL Editor → New Query → Run
```

This creates the `posts` table with full-text search, pgvector embeddings, and hybrid search functions.

### 3. Configure Sites

```bash
# Edit the sites configuration
cp blog-generator/sites.json blog-generator/sites.json.backup
nano blog-generator/sites.json
```

Fill in each site's:
- `supabase_url`, `supabase_key`, `supabase_service_key`
- `sanity_project_id`, `sanity_dataset`, `sanity_token`
- `topics`, `keywords`, `internal_links`, `external_links`

### 4. Configure Environment

```bash
cp .env.example .env
nano .env
```

Set `LLM_API_URL` to your friend's Ollama server address.

### 5. Start the Blog Generator

```bash
docker compose up -d
```

This starts:
- **blog-generator** — FastAPI on port 8000
- **scheduler** — runs every 2 hours, generates posts for all sites

### 6. Manual Generation (Optional)

```bash
# Generate a single post for a specific site
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"site_id": "site-1", "topic": "React Server Components", "keywords": ["react", "nextjs"]}'

# Batch generate
curl -X POST http://localhost:8000/generate/batch \
  -H "Content-Type: application/json" \
  -d '{"site_id": "site-1", "topics": ["topic1", "topic2", "topic3"]}'

# Check status
curl http://localhost:8000/status
```

### 7. Set Up Next.js Frontend

```bash
cd nextjs-app

# Copy and fill in environment variables
cp .env.local.example .env.local
# Edit .env.local with your Supabase and Sanity credentials

# Install dependencies (already done if you cloned fresh)
npm install

# Run dev server
npm run dev
```

### 8. Deploy to Vercel

```bash
cd nextjs-app

# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variables in Vercel dashboard:
# NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY
# NEXT_PUBLIC_SANITY_PROJECT_ID, NEXT_PUBLIC_SANITY_DATASET
# NEXT_PUBLIC_SITE_URL, REVALIDATION_SECRET
```

### 9. Set Up Sanity Webhook (for ISR)

In your Sanity dashboard → API → Webhooks → Create:
- **URL**: `https://your-site.vercel.app/api/revalidate?secret=YOUR_SECRET`
- **Trigger on**: Create, Update, Delete
- **Filter**: `_type == "post"`

## Project Structure

```
blog-automation/
├── docker-compose.yml          # FastAPI + Scheduler services
├── .env.example                # Global env template
│
├── blog-generator/             # Python FastAPI service
│   ├── main.py                 # API endpoints (/generate, /status, etc.)
│   ├── generator.py            # LLM interaction pipeline
│   ├── post_processor.py       # Anti-AI-detection rewriting
│   ├── link_injector.py        # Auto hyperlink injection
│   ├── embeddings.py           # pgvector embedding generation
│   ├── supabase_client.py      # Multi-site DB operations
│   ├── sanity_sync.py          # Multi-site CMS sync
│   ├── scheduler.py            # Automated generation cron
│   ├── prompts.py              # LLM prompt templates
│   ├── config.py               # Configuration loader
│   └── sites.json              # Per-site credentials & config
│
├── nextjs-app/                 # Next.js 15 frontend
│   ├── src/app/                # App Router pages
│   │   ├── blog/               # Blog listing + [slug] detail
│   │   ├── admin/              # Dashboard
│   │   └── api/                # Revalidation + search endpoints
│   ├── src/components/         # UI components
│   ├── src/lib/                # Supabase, Sanity, SEO utils
│   └── src/sanity/schemas/     # Sanity content schemas
│
└── supabase/migrations/        # Database SQL
```

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/sites` | GET | List configured sites |
| `/generate` | POST | Generate a single post |
| `/generate/batch` | POST | Queue batch generation |
| `/status` | GET | Global stats |
| `/status/{site_id}` | GET | Per-site stats |

## SEO Features

- ✅ Auto-generated `sitemap.xml` and `robots.txt`
- ✅ Open Graph and Twitter Card meta tags
- ✅ JSON-LD structured data (Schema.org BlogPosting)
- ✅ ISR with 1-hour revalidation + on-demand via Sanity webhook
- ✅ Hybrid search (full-text + semantic via pgvector)
- ✅ Automatic internal/external linking
- ✅ Anti-AI-detection post-processing
- ✅ Content quality scoring

## License

Private — for internal use only.
