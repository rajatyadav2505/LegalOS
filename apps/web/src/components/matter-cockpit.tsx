"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { ExternalCaseSummary, MatterDetail } from "@legalos/contracts";
import { Badge, Button, Card } from "@legalos/ui";
import { createBrowserApiClient } from "@/lib/api/client";

function formatDate(value: string | null | undefined) {
  if (!value) {
    return "Not scheduled";
  }
  return new Intl.DateTimeFormat("en-IN", { dateStyle: "medium" }).format(new Date(value));
}

export function MatterCockpit({ matterId }: { matterId: string }) {
  const [matter, setMatter] = useState<MatterDetail | null>(null);
  const [publicCase, setPublicCase] = useState<ExternalCaseSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const api = createBrowserApiClient();
    void Promise.all([api.getMatter(matterId), api.getMatterExternalCases(matterId)]).then(
      ([matterResult, externalCasesResult]) => {
        if (matterResult.ok) {
          setMatter(matterResult.data);
        } else {
          setError(matterResult.message);
          return;
        }

        if (externalCasesResult.ok) {
          setPublicCase(externalCasesResult.data.items[0] ?? null);
        } else {
          setError(externalCasesResult.message);
        }
      }
    );
  }, [matterId]);

  if (error) {
    return (
      <Card>
        <div className="text-sm text-red-100">{error}</div>
      </Card>
    );
  }

  if (!matter) {
    return (
      <Card>
        <div className="text-sm text-slate-300">Loading matter cockpit...</div>
      </Card>
    );
  }

  return (
    <section className="space-y-6">
      <header className="flex flex-col gap-4 border-b border-white/10 pb-5 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-2">
          <div className="text-xs uppercase tracking-[0.24em] text-slate-400">Matter cockpit</div>
          <h1 className="text-3xl font-semibold text-white">{matter.title}</h1>
          <p className="max-w-3xl text-sm leading-6 text-slate-300">
            {matter.reference_code} • {matter.forum} • Stage {matter.stage}
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <Badge variant="success">{matter.status}</Badge>
          <Badge variant="neutral">{matter.document_count} documents</Badge>
          <Badge variant="warning">{matter.saved_authority_count} saved authorities</Badge>
        </div>
      </header>

      <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <Card>
            <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Next hearing</div>
            <div className="mt-2 text-xl font-semibold text-white">
              {formatDate(matter.next_hearing_date)}
            </div>
          </Card>
          <Card>
            <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Forum</div>
            <div className="mt-2 text-xl font-semibold text-white">{matter.forum}</div>
          </Card>
          <Card>
            <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Last updated</div>
            <div className="mt-2 text-xl font-semibold text-white">{formatDate(matter.updated_at)}</div>
          </Card>
        </div>

        <Card>
          <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Matter summary</div>
          <div className="mt-3 text-sm leading-7 text-slate-200">
            {matter.summary ?? "No summary has been recorded yet."}
          </div>
        </Card>

        <Card>
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-xs uppercase tracking-[0.22em] text-slate-400">
                Public docket
              </div>
              <div className="mt-2 text-xl font-semibold text-white">
                {publicCase?.case_number ?? "No linked external case"}
              </div>
              <div className="mt-2 text-sm leading-6 text-slate-300">
                {publicCase
                  ? `${publicCase.court_name ?? "Unknown court"} • ${publicCase.bench_label ?? "Bench pending"} • next date ${formatDate(publicCase.next_listing_date)}`
                  : "Link and import an official court artifact to start chronology, memories, and bench intelligence."}
              </div>
            </div>
            {publicCase ? (
              <Badge variant="success">{publicCase.provenance.verification_status}</Badge>
            ) : (
              <Badge variant="warning">awaiting import</Badge>
            )}
          </div>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_1fr]">
        <Card className="space-y-4">
          <div>
            <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Trust rails</div>
            <div className="mt-1 text-base font-medium text-white">Phase 1 and 2 protections</div>
          </div>
          <div className="grid gap-3 text-sm text-slate-200">
            <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
              Exact quotes render only from stored quote spans and checksums.
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
              Public-law authorities and private matter files share a provenance-aware search surface.
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
              Bundle intelligence surfaces chronology, contradictions, duplicates, and exhibit links with source anchors.
            </div>
          </div>
        </Card>

        <Card className="space-y-4">
          <div>
            <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Quick actions</div>
            <div className="mt-1 text-base font-medium text-white">Open next workflow</div>
          </div>
          <div className="grid gap-3">
            <Button asChild>
              <Link href={`/matters/${matter.id}/upload`}>Upload documents</Link>
            </Button>
            <Button variant="secondary" asChild>
              <Link href={`/matters/${matter.id}/research`}>Research authorities</Link>
            </Button>
            <Button variant="ghost" asChild>
              <Link href={`/matters/${matter.id}/bundle`}>Bundle map</Link>
            </Button>
            <Button variant="secondary" asChild>
              <Link href={`/matters/${matter.id}/intelligence`}>Court intelligence</Link>
            </Button>
            <Button variant="secondary" asChild>
              <Link href={`/matters/${matter.id}/drafting`}>Draft studio</Link>
            </Button>
            <Button variant="ghost" asChild>
              <Link href={`/matters/${matter.id}/strategy`}>Strategy engine</Link>
            </Button>
            <Button variant="ghost" asChild>
              <Link href={`/matters/${matter.id}/institutional`}>Institutional mode</Link>
            </Button>
          </div>
        </Card>
      </div>
    </section>
  );
}
