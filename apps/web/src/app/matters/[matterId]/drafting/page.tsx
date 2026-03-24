import { AppShell } from "@/components/app-shell";
import { DraftStudio } from "@/components/draft-studio";

export default async function DraftingPage({
  params
}: {
  params: Promise<{ matterId: string }>;
}) {
  const { matterId } = await params;

  return (
    <AppShell>
      <DraftStudio matterId={matterId} />
    </AppShell>
  );
}
