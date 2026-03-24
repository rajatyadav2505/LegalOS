import { AppShell } from "@/components/app-shell";
import { ResearchWorkspace } from "@/components/research-workspace";

export default async function ResearchPage({
  params
}: {
  params: Promise<{ matterId: string }>;
}) {
  const { matterId } = await params;

  return (
    <AppShell>
      <ResearchWorkspace matterId={matterId} />
    </AppShell>
  );
}
