import PeriodPage from "@/components/PeriodPage";

export const revalidate = 3600;

export default function DailyPage() {
  return (
    <PeriodPage
      period="daily"
      accentColor="var(--daily)"
      description="The single most-read article from each source in the past 24 hours."
    />
  );
}
