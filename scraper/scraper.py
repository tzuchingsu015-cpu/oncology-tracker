"""
Fetches top-cited oncology articles using:
  1. PubMed E-utilities API (free, no key required for low volume)
  2. Crossref API for citation counts
"""

import os
import time
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional
import httpx
from supabase import create_client, Client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

HEADERS = {"User-Agent": "OncologyTracker/1.0 (mailto:tzuchingsu015@gmail.com)"}

# PubMed journal search terms → maps to journal NLM IDs
JOURNALS = [
    {"id": "nejm",             "name": "NEJM",             "full_name": "New England Journal of Medicine", "pubmed_journal": "N Engl J Med"},
    {"id": "jco",              "name": "JCO",              "full_name": "Journal of Clinical Oncology",    "pubmed_journal": "J Clin Oncol"},
    {"id": "lancet_oncology",  "name": "Lancet Oncology",  "full_name": "The Lancet Oncology",            "pubmed_journal": "Lancet Oncol"},
    {"id": "nature_cancer",    "name": "Nature Cancer",    "full_name": "Nature Cancer",                  "pubmed_journal": "Nat Cancer"},
    {"id": "cancer_discovery", "name": "Cancer Discovery", "full_name": "Cancer Discovery (AACR)",        "pubmed_journal": "Cancer Discov"},
    {"id": "jama_oncology",    "name": "JAMA Oncology",    "full_name": "JAMA Oncology",                  "pubmed_journal": "JAMA Oncol"},
    {"id": "annals_oncology",  "name": "Annals of Oncology","full_name":"Annals of Oncology",             "pubmed_journal": "Ann Oncol"},
]

PERIODS = {
    "daily":   (1,  1),   # (days back, articles per source)
    "weekly":  (7,  3),
    "monthly": (30, 3),
}


def article_id(doi_or_pmid: str) -> str:
    return hashlib.sha256(doi_or_pmid.encode()).hexdigest()[:16]


def pubmed_search(journal: str, days: int, max_results: int = 20) -> list[str]:
    """Return list of PMIDs published in the last `days` days."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    date_range = f"{start.strftime('%Y/%m/%d')}:{end.strftime('%Y/%m/%d')}[PDAT]"
    query = f'"{journal}"[Journal] AND {date_range}'

    try:
        r = httpx.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db": "pubmed", "term": query, "retmax": max_results,
                    "retmode": "json", "sort": "pub+date"},
            headers=HEADERS, timeout=15,
        )
        r.raise_for_status()
        ids = r.json()["esearchresult"]["idlist"]
        print(f"    PubMed found {len(ids)} PMIDs")
        return ids
    except Exception as e:
        print(f"    PubMed search error: {e}")
        return []


def pubmed_fetch(pmids: list[str]) -> list[dict]:
    """Fetch article metadata for a list of PMIDs."""
    if not pmids:
        return []
    try:
        r = httpx.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
            params={"db": "pubmed", "id": ",".join(pmids), "retmode": "json"},
            headers=HEADERS, timeout=15,
        )
        r.raise_for_status()
        result = r.json().get("result", {})
        articles = []
        for pmid in pmids:
            item = result.get(pmid, {})
            if not item or item.get("uid") != pmid:
                continue
            doi = next((loc["value"] for loc in item.get("articleids", [])
                        if loc.get("idtype") == "doi"), None)
            authors = ", ".join(
                a.get("name", "") for a in item.get("authors", [])[:3]
            )
            if len(item.get("authors", [])) > 3:
                authors += " et al."
            articles.append({
                "pmid": pmid,
                "doi": doi,
                "title": item.get("title", "").rstrip("."),
                "authors": authors,
                "pub_date": item.get("pubdate", ""),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            })
        return articles
    except Exception as e:
        print(f"    PubMed fetch error: {e}")
        return []


def get_citation_count(doi: str) -> int:
    """Get citation count from Crossref API."""
    if not doi:
        return 0
    try:
        r = httpx.get(
            f"https://api.crossref.org/works/{doi}",
            headers=HEADERS, timeout=10,
        )
        if r.status_code == 200:
            return r.json().get("message", {}).get("is-referenced-by-count", 0)
    except Exception:
        pass
    return 0


def scrape_journal(journal: dict, period: str) -> list[dict]:
    days, limit = PERIODS[period]
    print(f"  [{journal['id']}] {period} (past {days}d)")

    # fetch more candidates than needed so we can sort by citations
    pmids = pubmed_search(journal["pubmed_journal"], days, max_results=30)
    time.sleep(0.4)  # respect NCBI rate limit (3 req/s without API key)

    articles = pubmed_fetch(pmids)
    time.sleep(0.4)

    # get citation counts (Crossref) — only for candidates
    for art in articles:
        art["citations"] = get_citation_count(art["doi"]) if art["doi"] else 0
        time.sleep(0.2)

    # sort by citations descending, take top N
    articles.sort(key=lambda a: a["citations"], reverse=True)
    top = articles[:limit]

    now = datetime.now(timezone.utc).isoformat()
    results = []
    for rank, art in enumerate(top, start=1):
        uid = art["doi"] or art["pmid"]
        results.append({
            "id": article_id(uid),
            "source_id": journal["id"],
            "source_name": journal["name"],
            "title": art["title"],
            "url": art["url"],
            "authors": art["authors"],
            "abstract": "",
            "period": period,
            "rank": rank,
            "scraped_at": now,
        })
        print(f"    #{rank} [{art['citations']} citations] {art['title'][:60]}…")
    return results


def deduplicate(daily: list, weekly: list, monthly: list):
    daily_urls = {a["url"] for a in daily}
    weekly_clean = [a for a in weekly if a["url"] not in daily_urls]
    weekly_monthly_urls = daily_urls | {a["url"] for a in weekly_clean}
    monthly_clean = [a for a in monthly if a["url"] not in weekly_monthly_urls]
    return daily, weekly_clean, monthly_clean


def run():
    print(f"=== scrape run at {datetime.now(timezone.utc).isoformat()} ===")
    today = datetime.now(timezone.utc).date().isoformat()

    for journal in JOURNALS:
        print(f"\n{journal['full_name']}")
        daily, weekly, monthly = [], [], []

        for period in ("daily", "weekly", "monthly"):
            arts = scrape_journal(journal, period)
            if period == "daily":
                daily = arts
            elif period == "weekly":
                weekly = arts
            else:
                monthly = arts

        daily, weekly, monthly = deduplicate(daily, weekly, monthly)
        all_arts = daily + weekly + monthly

        if all_arts:
            supabase.table("articles").delete().eq("source_id", journal["id"]).gte("scraped_at", today).execute()
            supabase.table("articles").upsert(all_arts, on_conflict="id,period").execute()
            print(f"  → saved {len(all_arts)} articles")
        else:
            print(f"  → no articles found")

    print("\n=== done ===")


if __name__ == "__main__":
    run()
