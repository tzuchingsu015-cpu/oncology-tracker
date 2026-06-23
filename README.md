# Oncology Tracker

Aggregates most-read oncology articles from major journals — NEJM, JCO, Lancet Oncology, Nature Cancer, ASCO, ESMO, Cancer Discovery — across three time windows.

## Structure

```
oncology-tracker/
├── scraper/          # Python scraper (runs via GitHub Actions)
│   ├── scraper.py
│   ├── sources.py
│   └── requirements.txt
├── frontend/         # Next.js app (deploy to Vercel)
│   ├── app/
│   │   ├── daily/
│   │   ├── weekly/
│   │   └── monthly/
│   ├── components/
│   └── lib/
├── supabase_schema.sql
└── .github/workflows/scrape.yml
```

## Setup

### 1. Supabase
1. Create a new project at supabase.com
2. Run `supabase_schema.sql` in the SQL editor
3. Copy the Project URL and anon key (for frontend) + service role key (for scraper)

### 2. GitHub repo
1. Push this folder to a new GitHub repo
2. Add secrets: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`

### 3. Vercel (frontend)
1. Import the `frontend/` subfolder to Vercel
2. Set env vars: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
3. Deploy

## Deduplication rule
- **Daily**: 1 article per source (top most-read in past 24h)
- **Weekly**: 3 articles per source (past 7 days) — daily articles excluded
- **Monthly**: 3 articles per source (past 30 days) — daily + weekly articles excluded
