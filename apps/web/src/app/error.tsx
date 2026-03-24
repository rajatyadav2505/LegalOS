"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { Button, Card } from "@legalos/ui";

export default function GlobalError({
  error,
  reset
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <AppShell>
      <div className="mx-auto max-w-2xl">
        <Card className="space-y-5 text-center">
          <div className="text-xs uppercase tracking-[0.24em] text-slate-400">Application error</div>
          <h1 className="text-3xl font-semibold text-white">The workspace hit an unexpected error.</h1>
          <p className="text-sm leading-6 text-slate-300">
            The page can be retried once the backend or local runtime issue is cleared.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Button onClick={reset}>Try again</Button>
            <Button variant="secondary" asChild>
              <Link href="/">Return home</Link>
            </Button>
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
