"use client";

import { useEffect, useState, useTransition } from "react";
import type {
  SequencingConsoleResponse,
  StrategyWorkspace
} from "@legalos/contracts";
import { Badge, Button, Card, Field, Input, Textarea } from "@legalos/ui";
import { createBrowserApiClient } from "@/lib/api/client";

export function StrategyWorkspace({ matterId }: { matterId: string }) {
  const [workspace, setWorkspace] = useState<StrategyWorkspace | null>(null);
  const [sequencingLabel, setSequencingLabel] = useState("Record gap");
  const [sequencingDetail, setSequencingDetail] = useState(
    "Arrest memo time mismatch needs to be confronted."
  );
  const [sequencing, setSequencing] = useState<SequencingConsoleResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function loadWorkspace() {
    startTransition(() => {
      const api = createBrowserApiClient();
      void api.getStrategyWorkspace(matterId).then((result) => {
        if (result.ok) {
          setWorkspace(result.data);
          setError(null);
          return;
        }
        setError(result.message);
      });
    });
  }

  useEffect(() => {
    loadWorkspace();
  }, [matterId]);

  async function handleSequencingReview() {
    try {
      const api = createBrowserApiClient();
      const response = await api.reviewSequencing(matterId, {
        items: [
          {
            label: sequencingLabel,
            detail: sequencingDetail
          }
        ]
      });
      setSequencing(response);
      setError(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Sequencing review failed");
    }
  }

  if (!workspace && !error) {
    return (
      <Card>
        <div className="text-sm text-slate-300">Loading strategy workspace...</div>
      </Card>
    );
  }

  return (
    <section className="space-y-6">
      <header className="flex flex-col gap-4 border-b border-white/10 pb-5 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-2">
          <div className="text-xs uppercase tracking-[0.24em] text-slate-400">Strategy engine</div>
          <h1 className="text-3xl font-semibold text-white">Bounded hearing strategy</h1>
          <p className="max-w-3xl text-sm leading-6 text-slate-300">
            Issue cards, attack and defense lines, likely bench questions, and a lawful sequencing console.
          </p>
        </div>
        <Button variant="secondary" onClick={loadWorkspace} disabled={isPending}>
          {isPending ? "Refreshing..." : "Refresh strategy"}
        </Button>
      </header>

      {error ? <Card className="text-sm text-red-100">{error}</Card> : null}
      {workspace ? (
        <>
          <Card className="space-y-4">
            <div className="flex flex-wrap gap-3">
              <Badge variant="info">Decision support only</Badge>
              <Badge variant="success">{workspace.issues.length} issues</Badge>
              <Badge variant="warning">{workspace.scenario_tree.length} branches</Badge>
            </div>
            <div className="text-sm leading-6 text-slate-200">
              {workspace.decision_support_label}
            </div>
          </Card>

          <div className="grid gap-4 lg:grid-cols-3">
            {[workspace.best_line, workspace.fallback_line, workspace.risk_line].map((line) => (
              <Card key={line.label} className="space-y-3">
                <div className="text-xs uppercase tracking-[0.22em] text-slate-400">{line.label}</div>
                <div className="text-lg font-semibold text-white">{line.summary}</div>
                <div className="text-sm leading-6 text-slate-200">{line.rationale}</div>
              </Card>
            ))}
          </div>

          <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
            <div className="space-y-6">
              <Card className="space-y-4">
                <div>
                  <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Issue cards</div>
                  <div className="mt-1 text-base font-medium text-white">Attack, defense, and rebuttal</div>
                </div>
                <div className="space-y-4">
                  {workspace.issues.map((issue) => (
                    <article key={issue.issue_label} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                      <div className="text-sm font-semibold text-white">{issue.issue_label}</div>
                      <div className="mt-3 grid gap-3 text-sm text-slate-200">
                        <div>
                          <div className="text-xs uppercase tracking-[0.18em] text-slate-400">Attack</div>
                          <div className="mt-1">{issue.attack}</div>
                        </div>
                        <div>
                          <div className="text-xs uppercase tracking-[0.18em] text-slate-400">Defense</div>
                          <div className="mt-1">{issue.defense}</div>
                        </div>
                        <div>
                          <div className="text-xs uppercase tracking-[0.18em] text-slate-400">Short oral</div>
                          <div className="mt-1">{issue.oral_short}</div>
                        </div>
                        <div>
                          <div className="text-xs uppercase tracking-[0.18em] text-slate-400">Bench questions</div>
                          <ul className="mt-1 space-y-1 text-slate-300">
                            {issue.bench_questions.map((question) => (
                              <li key={question}>{question}</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <div className="text-xs uppercase tracking-[0.18em] text-slate-400">Rebuttal cards</div>
                          <ul className="mt-1 space-y-1 text-slate-300">
                            {issue.rebuttal_cards.map((card) => (
                              <li key={card}>{card}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              </Card>
            </div>

            <div className="space-y-6">
              <Card className="space-y-4">
                <div>
                  <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Scenario tree</div>
                  <div className="mt-1 text-base font-medium text-white">Bounded procedural turns</div>
                </div>
                <div className="space-y-3">
                  {workspace.scenario_tree.map((branch) => (
                    <article key={branch.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                      <div className="text-sm font-semibold text-white">{branch.label}</div>
                      <div className="mt-2 text-sm leading-6 text-slate-200">{branch.path}</div>
                      <div className="mt-3 text-xs text-slate-400">{branch.next_step}</div>
                    </article>
                  ))}
                </div>
              </Card>

              <Card className="space-y-4">
                <div>
                  <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Sequencing console</div>
                  <div className="mt-1 text-base font-medium text-white">Lawful timing guidance</div>
                </div>
                <Field label="Item label">
                  <Input
                    value={sequencingLabel}
                    onChange={(event) => setSequencingLabel(event.target.value)}
                  />
                </Field>
                <Field label="Detail">
                  <Textarea
                    value={sequencingDetail}
                    onChange={(event) => setSequencingDetail(event.target.value)}
                  />
                </Field>
                <Button onClick={() => void handleSequencingReview()} className="w-full">
                  Review sequencing
                </Button>
                {sequencing ? (
                  <div className="space-y-3">
                    <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-200">
                      {sequencing.global_warning}
                    </div>
                    {sequencing.items.map((item) => (
                      <div key={item.label} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                        <div className="flex items-center justify-between gap-3">
                          <div className="text-sm font-semibold text-white">{item.label}</div>
                          <Badge variant={item.mandatory_warning ? "danger" : "info"}>
                            {item.bucket}
                          </Badge>
                        </div>
                        <div className="mt-2 text-sm text-slate-200">{item.recommendation}</div>
                        <div className="mt-2 text-xs text-slate-400">{item.reason}</div>
                      </div>
                    ))}
                  </div>
                ) : null}
              </Card>
            </div>
          </div>
        </>
      ) : null}
    </section>
  );
}
