import { AppShell } from "@/components/app-shell";
import { UploadPanel } from "@/components/upload-panel";

export default async function UploadPage({
  params
}: {
  params: Promise<{ matterId: string }>;
}) {
  const { matterId } = await params;

  return (
    <AppShell>
      <UploadPanel matterId={matterId} />
    </AppShell>
  );
}
