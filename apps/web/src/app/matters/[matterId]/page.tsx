import { AppShell } from "@/components/app-shell";
import { MatterCockpit } from "@/components/matter-cockpit";

export default async function MatterPage({
  params
}: {
  params: Promise<{ matterId: string }>;
}) {
  const { matterId } = await params;

  return (
    <AppShell>
      <MatterCockpit matterId={matterId} />
    </AppShell>
  );
}
