import styles from "./ArticleCard.module.css";

interface Article {
  id: string;
  source_id: string;
  source_name: string;
  title: string;
  url: string;
  authors: string;
  abstract: string;
  rank: number;
  scraped_at: string;
}

export default function ArticleCard({ article, accentColor }: { article: Article; accentColor: string }) {
  return (
    <div className={styles.card} style={{ borderLeft: `3px solid ${accentColor}` }}>
      <div className={styles.meta}>
        <span className={styles.source}>{article.source_name}</span>
        <span className={styles.rank}>#{article.rank}</span>
      </div>
      <a href={article.url} target="_blank" rel="noopener noreferrer" className={styles.title}>
        {article.title}
      </a>
      {article.authors && <p className={styles.authors}>{article.authors}</p>}
      {article.abstract && <p className={styles.abstract}>{article.abstract}</p>}
    </div>
  );
}
