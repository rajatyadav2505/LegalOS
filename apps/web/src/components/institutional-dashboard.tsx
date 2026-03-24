"use client";

import { useEffect, useState, useTransition } from "react";
import type { Approval, InstitutionalDashboard } from "@legalos/contracts";
import { Badge, Button, Card } from "@legalos/ui";
import { createBrowserApiClient } from "@/lib/api/client";

export function InstitutionalDashboard({
  matterId,
  initialLowBandwidth = false
}: {
  matterId: string;
  initialLowBandwidth?: boolean;
}) {
  const [dashboard, setDashboard] = useState<InstitutionalDashboard | null>(null);
  const [lowBandwidth, setLowBandwidth] = useState(initialLowBandwidth);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function loadDashboard() {
    startTransition(() => {
      const api = createBrowserApiClient();
      void api.getInstitutionalDashboard(matterId).then((result) => {
        if (result.ok) {
          setDashboard(result.data);
          setError(null);
          return;
        }
        setError(result.message);
      });
    });
  }

  useEffect(() => {
    loadDashboard();
  }, [matterId]);

  async function handleRequestApproval() {
    if (!dashboard?.latest_draft_id) {
      setError("Generate a draft before requesting approval.");
      return;
    }
    try {
      const api = createBrowserApiClient();
      const approval = await api.requestApproval(matterId, {
        targetType: "draft_document",
        targetId: dashboard.latest_draft_id,
        note: "Please review the latest generated chamber draft."
      });
      setMessage(`Approval requested: ${approval.id}`);
      loadDashboard();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not request approval");
    }
  }

  async function handleApproveLatest() {
    const pending = dashboard?.approvals.find((item) => item.status === "pending");
    if (!pending) {
      setError("No pending approval is available.");
      return;
    }
    try {
      const api = createBrowserApiClient();
      const reviewed = await api.reviewApproval(pending.id, {
        status: "approved",
        reviewNote: "Approved for supervised institutional circulation."
      });
      setMessage(`Approval reviewed: ${reviewed.status}`);
      loadDashboard();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not review approval");
    }
  }

  if (!dashboard && !error) {
    return (
      <Card>
        <div className="text-sm text-slate-300">Loading institutional dashboard...</div>
      </Card>
    );
  }

  const pendingApproval = dashboard?.approvals.find((item) => item.status === "pending");

  return (
    <section className="space-y-6">
      <header className="flex flex-col gap-4 border-b border-white/10 pb-5 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-2">
          <div className="text-xs uppercase tracking-[0.24em] text-slate-400">Institutional mode</div>
          <h1 className="text-3xl font-semibold text-white">Auditability and approvals</h1>
          <p className="max-w-3xl text-sm leading-6 text-slate-300">
            Approval workflow, audit visibility, urgency posture, and plain-language summaries for institutional legal-aid use.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={loadDashboard} disabled={isPending}>
            {isPending ? "Refreshing..." : "Refresh"}
          </Button>
          <Button variant="ghost" onClick={() => setLowBandwidth((current) => !current)}>
            {lowBandwidth ? "Full view" : "Low-bandwidth view"}
          </Button>
        </div>
      </header>

      {message ? <Card className="text-sm text-emerald-100">{message}</Card> : null}
      {error ? <Card className="text-sm text-red-100">{error}</Card> : null}

      {dashboard ? (
        lowBandwidth ? (
          <Card className="space-y-3">
            <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Low-bandwidth brief</div>
            {dashboard.low_bandwidth_brief.map((item) => (
              <div key={item} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-200">
                {item}
              </div>
            ))}
          </Card>
        ) : (
          <>
            <div className="grid gap-4 lg:grid-cols-4">
              <Card>
                <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Urgency</div>
                <div className="mt-2 text-2xl font-semibold text-white">{dashboard.urgency_status}</div>
              </Card>
              <Card>
                <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Days to hearing</div>
                <div className="mt-2 text-2xl font-semibold text-white">
                  {dashboard.days_to_hearing ?? "Not scheduled"}
                </div>
              </Card>
              <Card>
                <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Pending approvals</div>
                <div className="mt-2 text-2xl font-semibold text-white">{dashboard.pending_approvals}</div>
              </Card>
              <Card>
                <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Latest draft</div>
                <div className="mt-2 text-sm font-semibold text-white">
                  {dashboard.latest_draft_id ?? "Not generated"}
                </div>
              </Card>
            </div>

            <Card className="space-y-4">
              <div className="flex flex-wrap gap-2">
                <Badge variant="info">Higher auditability enabled</Badge>
                <Badge variant="warning">{dashboard.pending_approvals} approvals pending</Badge>
              </div>
              <div className="flex flex-wrap gap-3">
                <Button onClick={() => void handleRequestApproval()}>
                  Request approval for latest draft
                </Button>
                <Button
                  variant="secondary"
                  disabled={!pendingApproval}
                  onClick={() => void handleApproveLatest()}
                >
                  Approve latest pending
                </Button>
              </div>
              <div className="text-sm leading-6 text-slate-200">
                {dashboard.decision_support_label}
              </div>
            </Card>

            <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
              <div className="space-y-6">
                <Card className="space-y-4">
                  <div>
                    <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Approvals</div>
                    <div className="mt-1 text-base font-medium text-white">Review workflow</div>
                  </div>
                  <div className="space-y-3">
                    {dashboard.approvals.length ? (
                      dashboard.approvals.map((approval: Approval) => (
                        <article key={approval.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                          <div className="flex items-center justify-between gap-3">
                            <div className="text-sm font-semibold text-white">{approval.target_type}</div>
                            <Badge
                              variant={
                                approval.status === "approved"
                                  ? "success"
                                  : approval.status === "rejected"
                                    ? "danger"
                                    : "warning"
                              }
                            >
                              {approval.status}
                            </Badge>
                          </div>
                          <div className="mt-2 text-xs text-slate-400">{approval.target_id}</div>
                          <div className="mt-2 text-sm text-slate-200">
                            {approval.review_note ?? approval.note ?? "No note"}
                          </div>
                        </article>
                      ))
                    ) : (
                      <div className="text-sm text-slate-400">No approvals requested yet.</div>
                    )}
                  </div>
                </Card>

                <Card className="space-y-4">
                  <div>
                    <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Audit trail</div>
                    <div className="mt-1 text-base font-medium text-white">Recent sensitive actions</div>
                  </div>
                  <div className="space-y-3">
                    {dashboard.recent_audit_events.map((event) => (
                      <article key={event.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                        <div className="text-sm font-semibold text-white">{event.action}</div>
                        <div className="mt-1 text-xs text-slate-400">
                          {event.entity_type} • {event.entity_id}
                        </div>
                        {event.detail ? (
                          <div className="mt-2 text-sm text-slate-200">{event.detail}</div>
                        ) : null}
                      </article>
                    ))}
                  </div>
                </Card>
              </div>

              <div className="space-y-6">
                <Card className="space-y-4">
                  <div>
                    <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Plain-language summary</div>
                    <div className="mt-1 text-base font-medium text-white">Beneficiary communication</div>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm leading-6 text-slate-200">
                    <div className="text-xs uppercase tracking-[0.18em] text-slate-400">English</div>
                    <div className="mt-2">{dashboard.plain_language_en}</div>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm leading-6 text-slate-200">
                    <div className="text-xs uppercase tracking-[0.18em] text-slate-400">Hindi</div>
                    <div className="mt-2">{dashboard.plain_language_hi}</div>
                  </div>
                </Card>
              </div>
            </div>
          </>
        )
      ) : null}
    </section>
  );
}
