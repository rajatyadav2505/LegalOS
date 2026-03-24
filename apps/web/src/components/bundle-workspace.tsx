"use client";

import Link from "next/link";
import { useEffect, useState, useTransition } from "react";
import type { BundleMap as BundleMapPayload } from "@legalos/contracts";
import { Button, Card } from "@legalos/ui";
import { createBrowserApiClient } from "@/lib/api/client";
import { BundleMap } from "@/components/bundle-map";

export function BundleWorkspace({ matterId }: { matterId: string }) {
  const [bundle, setBundle] = useState<BundleMapPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, startTransition] = useTransition();

  function loadBundle() {
    startTransition(() => {
      const api = createBrowserApiClient();
      void api.getBundleMap(matterId).then((result) => {
        if (result.ok) {
          setBundle(result.data);
          setError(null);
          return;
        }
        setError(result.message);
      });
    });
  }

  useEffect(() => {
    loadBundle();
  }, [matterId]);

  if (error) {
    return (
      <Card className="space-y-4">
        <div className="text-sm text-red-100">{error}</div>
        <div className="flex flex-wrap gap-3">
          <Button onClick={loadBundle} disabled={isRefreshing}>
            Retry
          </Button>
          <Button variant="secondary" asChild>
            <Link href={`/matters/${matterId}`}>Back to cockpit</Link>
          </Button>
        </div>
      </Card>
    );
  }

  if (!bundle) {
    return (
      <Card>
        <div className="text-sm text-slate-300">Loading bundle intelligence...</div>
      </Card>
    );
  }

  return <BundleMap bundle={bundle} onRefresh={loadBundle} isRefreshing={isRefreshing} />;
}
