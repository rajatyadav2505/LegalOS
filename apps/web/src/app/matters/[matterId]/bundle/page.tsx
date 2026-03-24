import { AppShell } from "@/components/app-shell";
import { BundleWorkspace } from "@/components/bundle-workspace";

export default async function BundlePage({
  params
}: {
  params: Promise<{ matterId: string }>;
}) {
  const { matterId } = await params;

  return (
    <AppShell>
      <BundleWorkspace matterId={matterId} />
    </AppShell>
  );
}
