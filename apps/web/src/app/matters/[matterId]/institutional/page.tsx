import { AppShell } from "@/components/app-shell";
import { InstitutionalDashboard } from "@/components/institutional-dashboard";

export default async function InstitutionalPage({
  params,
  searchParams
}: {
  params: Promise<{ matterId: string }>;
  searchParams: Promise<{ mode?: string }>;
}) {
  const { matterId } = await params;
  const { mode } = await searchParams;

  return (
    <AppShell>
      <InstitutionalDashboard matterId={matterId} initialLowBandwidth={mode === "lite"} />
    </AppShell>
  );
}
