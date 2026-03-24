"use client";

import type { BundleMap as BundleMapPayload } from "@legalos/contracts";
import { Badge, Button, Card } from "@legalos/ui";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-IN", { dateStyle: "medium" }).format(new Date(value));
}

function sourceLabel(sourceType: BundleMapPayload["documents"][number]["source_type"]) {
  switch (sourceType) {
    case "my_document":
      return "My docs";
    case "opponent_document":
      return "Opponent docs";
    case "court_document":
      return "Court docs";
    case "public_law":
      return "Public law";
    case "work_product":
      return "Work product";
  }
}

function statusVariant(status: string) {
  switch (status) {
    case "ready":
    case "verified":
      return "success";
    case "processing":
    case "needs_review":
    case "medium":
      return "warning";
    case "failed":
    case "blocked":
    case "high":
      return "danger";
    case "queued":
    case "low":
      return "neutral";
    default:
      return "neutral";
  }
}

function EmptyState({ label }: { label: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-white/10 px-4 py-8 text-sm text-slate-400">
      {label}
    </div>
  );
}

export function BundleMap({
  bundle,
  onRefresh,
  isRefreshing
}: {
  bundle: BundleMapPayload;
  onRefresh: () => void;
  isRefreshing: boolean;
}) {
  return (
    <section className="space-y-6">
      <header className="flex flex-col gap-4 border-b border-white/10 pb-5 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-2">
          <div className="text-xs uppercase tracking-[0.24em] text-slate-400">Bundle map</div>
          <h1 className="text-3xl font-semibold text-white">{bundle.matter_title}</h1>
          <p className="max-w-3xl text-sm leading-6 text-slate-300">
            {bundle.matter_reference_code} • {bundle.forum} • chronology, contradictions,
            duplicate detection, and exhibit chains across the matter record.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <Badge variant={statusVariant(bundle.ingestion.overall_status)}>
            {bundle.ingestion.overall_status}
          </Badge>
          <Badge variant="neutral">{bundle.stage}</Badge>
          <Badge variant="info">{bundle.matter_status}</Badge>
          <Button variant="secondary" onClick={onRefresh} disabled={isRefreshing}>
            {isRefreshing ? "Refreshing..." : "Refresh bundle"}
          </Button>
        </div>
      </header>

      <div className="grid gap-4 lg:grid-cols-4">
        <Card>
          <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Ready</div>
          <div className="mt-2 text-2xl font-semibold text-white">
            {bundle.ingestion.ready_documents}
          </div>
        </Card>
        <Card>
          <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Processing</div>
          <div className="mt-2 text-2xl font-semibold text-white">
            {bundle.ingestion.processing_documents}
          </div>
        </Card>
        <Card>
          <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Queued</div>
          <div className="mt-2 text-2xl font-semibold text-white">
            {bundle.ingestion.queued_documents}
          </div>
        </Card>
        <Card>
          <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Failed</div>
          <div className="mt-2 text-2xl font-semibold text-white">
            {bundle.ingestion.failed_documents}
          </div>
          <div className="mt-1 text-xs text-slate-400">
            Updated {formatDate(bundle.ingestion.last_updated_at)}
          </div>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-6">
          <Card className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Chronology</div>
                <div className="mt-1 text-base font-medium text-white">Date-linked events</div>
              </div>
              <Badge variant="neutral">{bundle.chronology.length} events</Badge>
            </div>
            <div className="space-y-3">
              {bundle.chronology.length ? (
                bundle.chronology.map((item) => (
                  <article key={item.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                      <div className="space-y-2">
                        <div className="text-sm font-semibold text-white">{item.title}</div>
                        <div className="text-sm leading-6 text-slate-300">{item.summary}</div>
                      </div>
                      <div className="min-w-[10rem] space-y-1 text-sm text-slate-400">
                        <div>{formatDate(item.date)}</div>
                        <div>{sourceLabel(item.source_type)}</div>
                      </div>
                    </div>
                    <div className="mt-3 text-xs text-slate-400">
                      {item.anchor_label} • {item.source_title}
                    </div>
                  </article>
                ))
              ) : (
                <EmptyState label="Upload matter documents to generate chronology events." />
              )}
            </div>
          </Card>

          <Card className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Contradictions</div>
                <div className="mt-1 text-base font-medium text-white">Conflict lattice</div>
              </div>
              <Badge variant="warning">{bundle.contradictions.length} findings</Badge>
            </div>
            <div className="space-y-3">
              {bundle.contradictions.length ? (
                bundle.contradictions.map((item) => (
                  <article key={item.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-2">
                        <div className="text-sm font-semibold text-white">{item.issue}</div>
                        <div className="text-sm leading-6 text-slate-300">{item.summary}</div>
                      </div>
                      <Badge variant={statusVariant(item.severity)}>{item.severity}</Badge>
                    </div>
                    <div className="mt-3 grid gap-1 text-xs text-slate-400">
                      <div>
                        {sourceLabel(item.source_a_type)}: {item.source_a} • {item.source_a_label}
                      </div>
                      <div>
                        {sourceLabel(item.source_b_type)}: {item.source_b} • {item.source_b_label}
                      </div>
                    </div>
                  </article>
                ))
              ) : (
                <EmptyState label="Contradiction analysis will appear after at least two matter documents are processed." />
              )}
            </div>
          </Card>

          <Card className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Clusters</div>
                <div className="mt-1 text-base font-medium text-white">Issue and entity grouping</div>
              </div>
              <Badge variant="neutral">{bundle.clusters.length} clusters</Badge>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              {bundle.clusters.length ? (
                bundle.clusters.map((item) => (
                  <article key={item.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-semibold text-white">{item.label}</div>
                      <Badge variant={statusVariant(item.status)}>{item.status}</Badge>
                    </div>
                    <div className="mt-2 text-sm leading-6 text-slate-300">{item.description}</div>
                    <div className="mt-3 text-xs text-slate-400">
                      {item.cluster_type} • {item.document_count} docs • {item.dominant_issue}
                    </div>
                  </article>
                ))
              ) : (
                <EmptyState label="Bundle clusters appear once the ingest worker has extracted issue and entity signals." />
              )}
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Documents</div>
                <div className="mt-1 text-base font-medium text-white">Matter records</div>
              </div>
              <Badge variant="neutral">{bundle.documents.length} docs</Badge>
            </div>
            <div className="space-y-3">
              {bundle.documents.length ? (
                bundle.documents.map((item) => (
                  <article key={item.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-white">{item.title}</div>
                        <div className="text-xs text-slate-400">{sourceLabel(item.source_type)}</div>
                      </div>
                      <Badge variant={statusVariant(item.processing_status)}>
                        {item.processing_status}
                      </Badge>
                    </div>
                    <div className="mt-2 text-sm text-slate-300">
                      {item.legal_issue ?? "No issue label recorded."}
                    </div>
                    <div className="mt-3 text-xs text-slate-400">
                      Stage: {item.processing_stage ?? item.processing_status}
                      {typeof item.processing_progress === "number"
                        ? ` • ${item.processing_progress}%`
                        : ""}
                    </div>
                    {item.processing_error ? (
                      <div className="mt-2 text-xs text-red-200">{item.processing_error}</div>
                    ) : null}
                  </article>
                ))
              ) : (
                <EmptyState label="No matter documents have been added to this bundle." />
              )}
            </div>
          </Card>

          <Card className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Duplicates</div>
                <div className="mt-1 text-base font-medium text-white">Canonical records</div>
              </div>
              <Badge variant="warning">{bundle.duplicate_groups.length} groups</Badge>
            </div>
            <div className="space-y-3">
              {bundle.duplicate_groups.length ? (
                bundle.duplicate_groups.map((item) => (
                  <article key={item.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="text-sm font-semibold text-white">{item.canonical_title}</div>
                    <div className="mt-2 text-sm leading-6 text-slate-300">{item.reason}</div>
                    <div className="mt-3 space-y-2">
                      {item.members.map((member) => (
                        <div key={member.id} className="text-xs text-slate-400">
                          {member.title} • {member.anchor_label}
                        </div>
                      ))}
                    </div>
                  </article>
                ))
              ) : (
                <EmptyState label="Duplicate detection runs after multiple similar documents are processed." />
              )}
            </div>
          </Card>

          <Card className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Exhibit links</div>
                <div className="mt-1 text-base font-medium text-white">Reference chain</div>
              </div>
              <Badge variant="info">{bundle.exhibit_links.length} links</Badge>
            </div>
            <div className="space-y-3">
              {bundle.exhibit_links.length ? (
                bundle.exhibit_links.map((item) => (
                  <article key={item.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-semibold text-white">{item.exhibit_label}</div>
                      <Badge variant="neutral">{sourceLabel(item.source_type)}</Badge>
                    </div>
                    <div className="mt-2 text-sm text-slate-300">
                      {item.title} • {item.target_title}
                    </div>
                    <div className="mt-3 text-xs text-slate-400">
                      {item.anchor_label} • {item.note}
                    </div>
                  </article>
                ))
              ) : (
                <EmptyState label="Exhibit links will appear when the parser finds exhibit references in uploaded matter files." />
              )}
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
}
