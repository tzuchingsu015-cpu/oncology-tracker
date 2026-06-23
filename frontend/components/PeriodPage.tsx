import { getArticlesByPeriod, type Article } from "@/lib/supabase";
import ArticleCard from "./ArticleCard";
import { SOURCES_META } from "@/lib/sourcesMeta";

interface Props {
  period: "daily" | "weekly" | "monthly";
  accentColor: string;
  description: string;
}

export default async function PeriodPage({ period, accentColor, description }: Props) {
  let articles: Article[] = [];
  let fetchError = false;

  if (process.env.NEXT_PUBLIC_SUPABASE_URL) {
    try {
      articles = await getArticlesByPeriod(period);
    } catch {
      fetchError = true;
    }
  }

  const grouped: Record<string, Article[]> = {};
  for (const art of articles) {
    if (!grouped[art.source_id]) grouped[art.source_id] = [];
    grouped[art.source_id].push(art);
  }

  const lastUpdated = articles[0]?.scraped_at
    ? new Date(articles[0].scraped_at).toLocaleDateString("zh-TW", { year: "numeric", month: "long", day: "numeric" })
    : null;

  return (
    <div>
      <div style={{ marginBottom: "2rem" }}>
        <h1 style={{ fontSize: 22, fontWeight: 600, marginBottom: 4, color: accentColor }}>
          {period.charAt(0).toUpperCase() + period.slice(1)} Highlights
        </h1>
        <p style={{ fontSize: 13, color: "var(--text3)" }}>
          {description}
          {lastUpdated && <> &nbsp;·&nbsp; Last updated {lastUpdated}</>}
        </p>
      </div>

      {fetchError && (
        <p style={{ color: "var(--text3)", fontSize: 14 }}>Unable to load articles. Please try again later.</p>
      )}

      {!fetchError && Object.keys(grouped).length === 0 && (
        <p style={{ color: "var(--text3)", fontSize: 14 }}>No articles yet — the scraper will run tonight at 09:00 TST.</p>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "2.5rem" }}>
        {SOURCES_META.map(src => {
          const arts = grouped[src.id];
          if (!arts?.length) return null;
          return (
            <section key={src.id}>
              <h2 style={{ fontSize: 13, fontWeight: 600, letterSpacing: "0.04em", textTransform: "uppercase", color: "var(--text3)", marginBottom: "0.75rem" }}>
                {src.fullName}
              </h2>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {arts.map(art => (
                  <ArticleCard key={art.id + art.rank} article={art} accentColor={accentColor} />
                ))}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
