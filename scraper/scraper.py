import os
import json
import hashlib
import time
from datetime import datetime, timezone
from typing import Optional
import httpx
from bs4 import BeautifulSoup
from supabase import create_client, Client
from sources import SOURCES

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def article_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def fetch_html(url: str) -> Optional[str]:
    try:
        r = httpx.get(url, headers=HEADERS, timeout=20, follow_redirects=True)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  fetch error {url}: {e}")
        return None


# ── per-source parsers ─────────────────────────────────────────────────────────

def parse_nejm(html: str, limit: int) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    articles = []
    for item in soup.select("li.most-popular__item")[:limit]:
        title_el = item.select_one("a.most-popular__title")
        if not title_el:
            continue
        url = "https://www.nejm.org" + title_el["href"]
        articles.append({
            "title": title_el.get_text(strip=True),
            "url": url,
            "authors": item.select_one(".author-list") and item.select_one(".author-list").get_text(strip=True) or "",
            "abstract": "",
        })
    return articles


def parse_asco_jco(html: str, limit: int) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    articles = []
    for item in soup.select("div.art_title")[:limit]:
        a = item.select_one("a")
        if not a:
            continue
        url = "https://ascopubs.org" + a["href"] if a["href"].startswith("/") else a["href"]
        articles.append({
            "title": a.get_text(strip=True),
            "url": url,
            "authors": "",
            "abstract": "",
        })
    return articles


def parse_lancet(html: str, limit: int) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    articles = []
    for item in soup.select("article.article-item")[:limit]:
        title_el = item.select_one("h3 a, h2 a")
        if not title_el:
            continue
        href = title_el.get("href", "")
        url = "https://www.thelancet.com" + href if href.startswith("/") else href
        articles.append({
            "title": title_el.get_text(strip=True),
            "url": url,
            "authors": "",
            "abstract": "",
        })
    return articles


def parse_nature(html: str, limit: int) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    articles = []
    for item in soup.select("article")[:limit]:
        title_el = item.select_one("h3 a, h2 a")
        if not title_el:
            continue
        href = title_el.get("href", "")
        url = "https://www.nature.com" + href if href.startswith("/") else href
        abstract_el = item.select_one("p.article-item__teaser, div.c-article-teaser-text")
        articles.append({
            "title": title_el.get_text(strip=True),
            "url": url,
            "authors": "",
            "abstract": abstract_el.get_text(strip=True) if abstract_el else "",
        })
    return articles


def parse_asco_news(html: str, limit: int) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    articles = []
    for item in soup.select("div.news-listing__item, article.news-item")[:limit]:
        title_el = item.select_one("h3 a, h2 a, a.news-title")
        if not title_el:
            continue
        href = title_el.get("href", "")
        url = "https://www.asco.org" + href if href.startswith("/") else href
        articles.append({
            "title": title_el.get_text(strip=True),
            "url": url,
            "authors": "",
            "abstract": "",
        })
    return articles


def parse_esmo(html: str, limit: int) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    articles = []
    for item in soup.select("div.news-item, article")[:limit]:
        title_el = item.select_one("h3 a, h2 a, .news-title a")
        if not title_el:
            continue
        href = title_el.get("href", "")
        url = "https://www.esmo.org" + href if href.startswith("/") else href
        articles.append({
            "title": title_el.get_text(strip=True),
            "url": url,
            "authors": "",
            "abstract": "",
        })
    return articles


def parse_aacr(html: str, limit: int) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    articles = []
    for item in soup.select("div.item-page, li.js-widget-item")[:limit]:
        title_el = item.select_one("a")
        if not title_el:
            continue
        href = title_el.get("href", "")
        url = "https://aacrjournals.org" + href if href.startswith("/") else href
        articles.append({
            "title": title_el.get_text(strip=True),
            "url": url,
            "authors": "",
            "abstract": "",
        })
    return articles


PARSERS = {
    "nejm": parse_nejm,
    "jco": parse_asco_jco,
    "lancet_oncology": parse_lancet,
    "nature_cancer": parse_nature,
    "asco": parse_asco_news,
    "esmo": parse_esmo,
    "cancer_discovery": parse_aacr,
}

LIMITS = {"daily": 1, "weekly": 3, "monthly": 3}
PERIOD_URL_KEY = {"daily": "daily_url", "weekly": "weekly_url", "monthly": "monthly_url"}


def scrape_source(source: dict, period: str) -> list[dict]:
    url = source[PERIOD_URL_KEY[period]]
    limit = LIMITS[period]
    print(f"  [{source['id']}] {period} -> {url}")
    html = fetch_html(url)
    if not html:
        return []
    parser = PARSERS.get(source["id"])
    if not parser:
        return []
    raw = parser(html, limit)
    now = datetime.now(timezone.utc).isoformat()
    results = []
    for rank, art in enumerate(raw, start=1):
        if not art["title"] or not art["url"]:
            continue
        results.append({
            "id": article_id(art["url"]),
            "source_id": source["id"],
            "source_name": source["name"],
            "title": art["title"],
            "url": art["url"],
            "authors": art.get("authors", ""),
            "abstract": art.get("abstract", ""),
            "period": period,
            "rank": rank,
            "scraped_at": now,
        })
    return results


def deduplicate(daily: list, weekly: list, monthly: list):
    """Articles in daily are excluded from weekly; daily+weekly excluded from monthly."""
    daily_urls = {a["url"] for a in daily}
    weekly_clean = [a for a in weekly if a["url"] not in daily_urls]
    weekly_monthly_urls = daily_urls | {a["url"] for a in weekly_clean}
    monthly_clean = [a for a in monthly if a["url"] not in weekly_monthly_urls]
    return daily, weekly_clean, monthly_clean


def upsert_articles(articles: list[dict]):
    if not articles:
        return
    # delete today's entries for the same source+period, then insert fresh
    for art in articles:
        supabase.table("articles").upsert(art, on_conflict="id,period").execute()
    print(f"  upserted {len(articles)} articles")


def run():
    print(f"=== scrape run at {datetime.now(timezone.utc).isoformat()} ===")
    for source in SOURCES:
        print(f"\n{source['name']}")
        daily, weekly, monthly = [], [], []
        for period in ("daily", "weekly", "monthly"):
            arts = scrape_source(source, period)
            if period == "daily":
                daily = arts
            elif period == "weekly":
                weekly = arts
            else:
                monthly = arts
            time.sleep(2)

        daily, weekly, monthly = deduplicate(daily, weekly, monthly)
        all_arts = daily + weekly + monthly

        # clear today's records for this source before upserting
        today = datetime.now(timezone.utc).date().isoformat()
        supabase.table("articles").delete().eq("source_id", source["id"]).gte("scraped_at", today).execute()
        upsert_articles(all_arts)

    print("\n=== done ===")


if __name__ == "__main__":
    run()
