import { AppShell } from "@/components/app-shell";
import { StrategyWorkspace } from "@/components/strategy-workspace";

export default async function StrategyPage({
  params
}: {
  params: Promise<{ matterId: string }>;
}) {
  const { matterId } = await params;

  return (
    <AppShell>
      <StrategyWorkspace matterId={matterId} />
    </AppShell>
  );
}
