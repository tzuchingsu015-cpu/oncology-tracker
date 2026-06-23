import PeriodPage from "@/components/PeriodPage";

export const revalidate = 3600;

export default function WeeklyPage() {
  return (
    <PeriodPage
      period="weekly"
      accentColor="var(--weekly)"
      description="Top 3 most-read articles per source over the past 7 days — excluding articles already featured in Daily."
    />
  );
}
