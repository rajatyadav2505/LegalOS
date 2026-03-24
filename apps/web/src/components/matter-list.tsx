"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { MatterSummary } from "@legalos/contracts";
import { Badge, Button, Card } from "@legalos/ui";
import { clearAuthToken } from "@/lib/auth";
import { createBrowserApiClient } from "@/lib/api/client";

function formatDate(value: string | null) {
  if (!value) {
    return "Not scheduled";
  }
  return new Intl.DateTimeFormat("en-IN", { dateStyle: "medium" }).format(new Date(value));
}

export function MatterList() {
  const [matters, setMatters] = useState<MatterSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const api = createBrowserApiClient();
    void api.getMatters().then((result) => {
      if (result.ok) {
        setMatters(result.data);
        return;
      }
      setError(result.message);
    });
  }, []);

  return (
    <section className="space-y-6">
      <header className="flex flex-col gap-4 border-b border-white/10 pb-5 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-2">
          <div className="text-xs uppercase tracking-[0.24em] text-slate-400">Matter index</div>
          <h1 className="text-3xl font-semibold text-white">Available matter workspaces</h1>
          <p className="max-w-3xl text-sm leading-6 text-slate-300">
            Open a matter cockpit, continue the upload workflow, or move into verified research.
          </p>
        </div>
        <Button
          variant="ghost"
          onClick={() => {
            clearAuthToken();
            window.location.href = "/login";
          }}
        >
          Sign out
        </Button>
      </header>

      {error ? (
        <Card>
          <div className="text-sm text-red-100">{error}</div>
        </Card>
      ) : null}

      <div className="grid gap-4">
        {matters.map((matter) => (
          <Card key={matter.id} className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-2">
              <div className="text-lg font-medium text-white">{matter.title}</div>
              <div className="text-sm text-slate-300">
                {matter.reference_code} • {matter.forum}
              </div>
              <div className="text-sm text-slate-400">{matter.summary ?? "No summary recorded yet."}</div>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <Badge variant="success">{matter.status}</Badge>
              <Badge variant="neutral">{matter.document_count} docs</Badge>
              <Badge variant="warning">Next: {formatDate(matter.next_hearing_date)}</Badge>
              <Button asChild>
                <Link href={`/matters/${matter.id}`}>Open matter</Link>
              </Button>
            </div>
          </Card>
        ))}

        {!matters.length && !error ? (
          <Card>
            <div className="text-sm text-slate-300">Loading matters...</div>
          </Card>
        ) : null}
      </div>
    </section>
  );
}
