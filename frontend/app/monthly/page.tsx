import PeriodPage from "@/components/PeriodPage";

export const revalidate = 3600;

export default function MonthlyPage() {
  return (
    <PeriodPage
      period="monthly"
      accentColor="var(--monthly)"
      description="Top 3 most-read articles per source over the past 30 days — excluding articles already featured in Daily or Weekly."
    />
  );
}
