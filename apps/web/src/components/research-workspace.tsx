"use client";

import {
  useState,
  useTransition,
  type ChangeEvent,
  type FormEvent
} from "react";
import type {
  AuthorityKind,
  ResearchSearchResponse,
  ResearchSearchResult
} from "@legalos/contracts";
import { Badge, Button, Card, Field, Input, Select, Separator, Textarea } from "@legalos/ui";
import { createBrowserApiClient } from "@/lib/api/client";

const initialFilters: { court: string; issue: string; authorityKind: AuthorityKind } = {
  court: "",
  issue: "",
  authorityKind: "constitution"
};

export function ResearchWorkspace({ matterId }: { matterId: string }) {
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState(initialFilters);
  const [response, setResponse] = useState<ResearchSearchResponse | null>(null);
  const [selected, setSelected] = useState<ResearchSearchResult | null>(null);
  const [issueLabel, setIssueLabel] = useState("Custody without counsel");
  const [selectionNote, setSelectionNote] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  async function runSearch() {
    setFeedback(null);
    const api = createBrowserApiClient();
    const nextResponse = await api.searchAuthorities({
      matterId,
      query,
      filters
    });
    setResponse(nextResponse);
    setSelected(nextResponse.items[0] ?? null);
  }

  function handleSearchSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    startTransition(() => {
      void runSearch().catch((cause) => {
        setFeedback(cause instanceof Error ? cause.message : "Research search failed");
      });
    });
  }

  async function handleSaveSelection(treatment: "apply" | "distinguish" | "adverse" | "draft") {
    if (!selected) {
      return;
    }

    const api = createBrowserApiClient();
    const result = await api.saveResearchSelection(matterId, {
      quoteSpanId: selected.quote_span_id,
      treatment,
      issueLabel,
      note: selectionNote
    });
    setFeedback(`Saved as ${result.treatment} for ${result.issue_label}.`);
  }

  async function handleExportMemo() {
    const api = createBrowserApiClient();
    const result = await api.exportResearchMemo(matterId);
    setFeedback(`Memo export prepared: ${result.file_name}`);
  }

  return (
    <section className="grid gap-6 lg:grid-cols-[1fr_1.05fr]">
      <div className="space-y-4">
        <div className="space-y-2">
          <div className="text-xs uppercase tracking-[0.24em] text-slate-400">Research canvas</div>
          <h1 className="text-3xl font-semibold text-white">Search verified authorities</h1>
          <p className="text-sm leading-6 text-slate-300">
            Every result is backed by a stored quote span, anchor label, and checksum.
          </p>
        </div>

        <Card className="space-y-4">
          <form className="space-y-4" onSubmit={handleSearchSubmit}>
            <Field label="Search query">
                <Input
                  value={query}
                  onChange={(event: ChangeEvent<HTMLInputElement>) => setQuery(event.target.value)}
                  placeholder="e.g. personal liberty legal aid"
                />
            </Field>

            <div className="grid gap-3 sm:grid-cols-3">
              <Field label="Court">
                <Input
                  value={filters.court}
                  onChange={(event: ChangeEvent<HTMLInputElement>) =>
                    setFilters((prev) => ({ ...prev, court: event.target.value }))
                  }
                  placeholder="Constitution of India"
                />
              </Field>
              <Field label="Issue">
                <Input
                  value={filters.issue}
                  onChange={(event: ChangeEvent<HTMLInputElement>) =>
                    setFilters((prev) => ({ ...prev, issue: event.target.value }))
                  }
                  placeholder="legal aid"
                />
              </Field>
              <Field label="Authority kind">
                <Select
                  value={filters.authorityKind}
                  onChange={(event: ChangeEvent<HTMLSelectElement>) =>
                    setFilters((prev) => ({
                      ...prev,
                      authorityKind: event.target.value as AuthorityKind
                    }))
                  }
                  options={[
                    { value: "constitution", label: "Constitution" },
                    { value: "matter_document", label: "Matter document" },
                    { value: "judgment", label: "Judgment" }
                  ]}
                />
              </Field>
            </div>

            <Button type="submit" className="w-full" disabled={isPending}>
              {isPending ? "Searching..." : "Run search"}
            </Button>
          </form>
        </Card>

        <Card className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Result handling</div>
              <div className="mt-1 text-base font-medium text-white">Save, distinguish, or mark adverse</div>
            </div>
            <Badge variant="warning">Source aware</Badge>
          </div>
          <Field label="Issue label">
            <Input
              value={issueLabel}
              onChange={(event: ChangeEvent<HTMLInputElement>) => setIssueLabel(event.target.value)}
            />
          </Field>
          <Textarea
            value={selectionNote}
            onChange={(event: ChangeEvent<HTMLTextAreaElement>) => setSelectionNote(event.target.value)}
            placeholder="Why does this authority matter to the issue?"
          />
          <div className="flex flex-wrap gap-2">
            <Button size="sm" onClick={() => void handleSaveSelection("apply")} disabled={!selected}>
              Apply
            </Button>
            <Button size="sm" variant="secondary" onClick={() => void handleSaveSelection("distinguish")} disabled={!selected}>
              Distinguish
            </Button>
            <Button size="sm" variant="destructive" onClick={() => void handleSaveSelection("adverse")} disabled={!selected}>
              Mark adverse
            </Button>
            <Button size="sm" variant="ghost" onClick={() => void handleSaveSelection("draft")} disabled={!selected}>
              Use in draft
            </Button>
          </div>
        </Card>

        <Card className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Research memo</div>
              <div className="mt-1 text-base font-medium text-white">Export issue pack</div>
            </div>
            <Badge variant="info">Memo ready</Badge>
          </div>
          <Button variant="secondary" onClick={() => void handleExportMemo()} disabled={!response?.items.length}>
            Export memo
          </Button>
        </Card>

        {feedback ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-200">{feedback}</div>
        ) : null}
      </div>

      <div className="space-y-4">
        <Card className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Authorities</div>
              <div className="mt-1 text-base font-medium text-white">Verified results</div>
            </div>
            <Badge variant="neutral">{response?.items.length ?? 0} results</Badge>
          </div>
          <Separator />
          <div className="space-y-3">
            {(response?.items ?? []).map((authority) => (
              <button
                key={authority.quote_span_id}
                className="w-full rounded-2xl border border-white/10 bg-white/5 p-4 text-left transition hover:border-saffron-500/40 hover:bg-white/10"
                onClick={() => setSelected(authority)}
                type="button"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <div className="text-base font-medium text-white">{authority.title}</div>
                    <div className="text-sm text-slate-300">
                      {authority.court ?? "Source document"} • {authority.citation_text ?? "No citation"}
                    </div>
                  </div>
                  <Badge variant={authority.saved_treatment === "adverse" ? "danger" : "success"}>
                    {authority.saved_treatment ?? "verified"}
                  </Badge>
                </div>
                <div className="mt-3 text-sm leading-6 text-slate-300">
                  {authority.legal_issue ?? "Issue metadata pending review"}
                </div>
                <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-400">
                  <span>{authority.anchor_label}</span>
                </div>
              </button>
            ))}
            {response?.items.length ? null : (
              <div className="rounded-2xl border border-dashed border-white/10 px-4 py-8 text-sm text-slate-400">
                Run a search to populate verified authority cards.
              </div>
            )}
          </div>
        </Card>

        <Card className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Quote lock</div>
              <div className="mt-1 text-base font-medium text-white">Source spans only</div>
            </div>
            <Badge variant="warning">{selected ? 1 : 0} span</Badge>
          </div>
          <Separator />
          {selected ? (
            <article className="rounded-2xl border border-white/10 bg-slate-950/30 p-4">
              <div className="text-xs uppercase tracking-[0.2em] text-slate-500">
                {selected.anchor_label}
              </div>
              <blockquote className="mt-2 text-sm leading-7 text-slate-100">
                "{selected.quote_text}"
              </blockquote>
              <div className="mt-3 text-xs text-slate-400">Checksum {selected.quote_checksum}</div>
            </article>
          ) : (
            <div className="rounded-2xl border border-dashed border-white/10 px-4 py-8 text-sm text-slate-400">
              Select a result to inspect its exact stored quote span.
            </div>
          )}
        </Card>
      </div>
    </section>
  );
}
