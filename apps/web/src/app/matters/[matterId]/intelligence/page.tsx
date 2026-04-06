import { AppShell } from "@/components/app-shell";
import { CourtIntelligenceWorkspace } from "@/components/court-intelligence-workspace";

export default async function CourtIntelligencePage({
  params
}: {
  params: Promise<{ matterId: string }>;
}) {
  const { matterId } = await params;

  return (
    <AppShell>
      <CourtIntelligenceWorkspace matterId={matterId} />
    </AppShell>
  );
}
