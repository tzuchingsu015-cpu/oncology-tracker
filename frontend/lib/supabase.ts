import { createClient, type SupabaseClient } from "@supabase/supabase-js";

let _client: SupabaseClient | null = null;

function getClient(): SupabaseClient {
  if (!_client) {
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    if (!url || !key) throw new Error("Supabase env vars not set");
    _client = createClient(url, key);
  }
  return _client;
}

export type Article = {
  id: string;
  source_id: string;
  source_name: string;
  title: string;
  url: string;
  authors: string;
  abstract: string;
  period: "daily" | "weekly" | "monthly";
  rank: number;
  scraped_at: string;
};

export async function getArticlesByPeriod(period: "daily" | "weekly" | "monthly"): Promise<Article[]> {
  const supabase = getClient();
  const { data, error } = await supabase
    .from("articles")
    .select("*")
    .eq("period", period)
    .order("source_id", { ascending: true })
    .order("rank", { ascending: true })
    .limit(100);

  if (error) throw error;

  // keep only the most recent scrape per source+period
  const seen = new Set<string>();
  const deduped: Article[] = [];
  for (const art of (data ?? [])) {
    const key = `${art.source_id}:${art.rank}`;
    if (!seen.has(key)) {
      seen.add(key);
      deduped.push(art);
    }
  }
  return deduped;
}
