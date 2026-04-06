"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type {
  CasePartySummary,
  ConnectedMatter,
  ExternalCaseSummary,
  FilingLineageItem,
  HearingDelta,
  HybridSearchItem,
  MatterExternalCaseList,
  MemorySnapshot,
  MergedChronologyItem,
  ProfileSnapshot
} from "@legalos/contracts";
import { Badge, Button, Card, Input } from "@legalos/ui";
import { createBrowserApiClient } from "@/lib/api/client";

type TabKey = "chronology" | "filings" | "party-memory" | "case-memory" | "connected";

function formatDate(value: string | null | undefined) {
  if (!value) {
    return "Unavailable";
  }
  return new Intl.DateTimeFormat("en-IN", { dateStyle: "medium" }).format(new Date(value));
}

function badgeVariant(value: string | undefined) {
  if (!value) {
    return "neutral" as const;
  }
  if (value.includes("verified") || value.includes("succeeded")) {
    return "success" as const;
  }
  if (value.includes("needs") || value.includes("parsed")) {
    return "warning" as const;
  }
  return "neutral" as const;
}

export function CourtIntelligenceWorkspace({ matterId }: { matterId: string }) {
  const [tab, setTab] = useState<TabKey>("chronology");
  const [externalCases, setExternalCases] = useState<MatterExternalCaseList | null>(null);
  const [chronology, setChronology] = useState<MergedChronologyItem[]>([]);
  const [hearingDelta, setHearingDelta] = useState<HearingDelta | null>(null);
  const [filings, setFilings] = useState<FilingLineageItem[]>([]);
  const [connected, setConnected] = useState<ConnectedMatter[]>([]);
  const [parties, setParties] = useState<CasePartySummary[]>([]);
  const [currentPartyId, setCurrentPartyId] = useState<string | null>(null);
  const [partyMemory, setPartyMemory] = useState<MemorySnapshot | null>(null);
  const [caseMemory, setCaseMemory] = useState<MemorySnapshot | null>(null);
  const [judgeProfile, setJudgeProfile] = useState<ProfileSnapshot | null>(null);
  const [courtProfile, setCourtProfile] = useState<ProfileSnapshot | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<HybridSearchItem[]>([]);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importStatus, setImportStatus] = useState<string | null>(null);
  const [importArtifactKind, setImportArtifactKind] = useState("case_history");
  const [error, setError] = useState<string | null>(null);

  const primaryCase = externalCases?.items[0] ?? null;

  async function loadWorkspace() {
    const api = createBrowserApiClient();
    const [casesResult, chronologyResult, deltaResult, filingsResult, connectedResult] =
      await Promise.all([
        api.getMatterExternalCases(matterId),
        api.getMergedChronology(matterId),
        api.getHearingDelta(matterId),
        api.getFilingLineage(matterId),
        api.getConnectedMatters({ matterId })
      ]);

    if (!casesResult.ok) {
      setError(casesResult.message);
      return;
    }

    setExternalCases(casesResult.data);
    if (chronologyResult.ok) {
      setChronology(chronologyResult.data);
    }
    if (deltaResult.ok) {
      setHearingDelta(deltaResult.data);
    }
    if (filingsResult.ok) {
      setFilings(filingsResult.data);
    }
    if (connectedResult.ok) {
      setConnected(connectedResult.data);
    }

    const nextCase = casesResult.data.items[0];
    if (!nextCase) {
      setParties([]);
      setPartyMemory(null);
      setCaseMemory(null);
      setJudgeProfile(null);
      setCourtProfile(null);
      return;
    }

    const [partiesResult, caseMemoryResult] = await Promise.all([
      api.getExternalCaseParties(nextCase.id),
      api.getCaseMemory(nextCase.id)
    ]);

    if (partiesResult.ok) {
      setParties(partiesResult.data);
      if (partiesResult.data[0]) {
        setCurrentPartyId(partiesResult.data[0].party_id);
        const partyMemoryResult = await api.getPartyMemory(partiesResult.data[0].party_id);
        if (partyMemoryResult.ok) {
          setPartyMemory(partyMemoryResult.data);
        }
      }
    }

    if (caseMemoryResult.ok) {
      setCaseMemory(caseMemoryResult.data);
    }

    if (nextCase.judge_id) {
      const judgeProfileResult = await api.getJudgeProfile(nextCase.judge_id);
      if (judgeProfileResult.ok) {
        setJudgeProfile(judgeProfileResult.data);
      }
    }

    if (nextCase.court_id) {
      const courtProfileResult = await api.getCourtProfile(nextCase.court_id);
      if (courtProfileResult.ok) {
        setCourtProfile(courtProfileResult.data);
      }
    }
  }

  useEffect(() => {
    void loadWorkspace();
  }, [matterId]);

  const selectedEvidence = useMemo(() => {
    if (tab === "party-memory") {
      return partyMemory?.source_refs ?? [];
    }
    if (tab === "case-memory") {
      return caseMemory?.source_refs ?? [];
    }
    return judgeProfile?.source_refs ?? courtProfile?.source_refs ?? [];
  }, [caseMemory?.source_refs, courtProfile?.source_refs, judgeProfile?.source_refs, partyMemory?.source_refs, tab]);

  async function runSearch() {
    const api = createBrowserApiClient();
    const result = await api.searchHybrid(searchQuery, { matterId, limit: 8 });
    if (result.ok) {
      setSearchResults(result.data.items);
      setError(null);
      return;
    }
    setError(result.message);
  }

  async function importOfficialArtifact() {
    if (!importFile) {
      return;
    }
    const api = createBrowserApiClient();
    const imported = await api.importExternalCaseArtifact(matterId, {
      sourceSystem: "district_ecourts",
      artifactKind: importArtifactKind,
      file: importFile,
      externalCaseId: primaryCase?.id ?? null
    });
    setImportStatus(`Imported ${imported.case_number} from ${importArtifactKind.replaceAll("_", " ")}.`);
    await loadWorkspace();
  }

  if (error) {
    return (
      <Card className="space-y-4">
        <div className="text-sm text-red-100">{error}</div>
        <Button variant="secondary" asChild>
          <Link href={`/matters/${matterId}`}>Back to cockpit</Link>
        </Button>
      </Card>
    );
  }

  return (
    <section className="space-y-6">
      <header className="space-y-4 border-b border-white/10 pb-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="text-xs uppercase tracking-[0.22em] text-slate-400">
              Court intelligence
            </div>
            <h1 className="mt-1 text-3xl font-semibold text-white">
              Bounded public docket intelligence
            </h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-300">
              Imported official court artifacts, merged chronology, litigant memory, and
              descriptive bench intelligence with visible provenance.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <Badge variant={badgeVariant(primaryCase?.provenance.verification_status)}>
              {primaryCase?.provenance.verification_status ?? "no public case"}
            </Badge>
            <Badge variant="info">
              {primaryCase?.provenance.source_system?.replaceAll("_", " ") ?? "awaiting import"}
            </Badge>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
          <Card className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs uppercase tracking-[0.22em] text-slate-400">
                  Bench brief
                </div>
                <div className="mt-1 text-lg font-semibold text-white">
                  {primaryCase?.court_name ?? "No linked external case"}
                </div>
              </div>
              {primaryCase?.judge_name ? (
                <Badge variant="neutral">{primaryCase.judge_name}</Badge>
              ) : null}
            </div>
            <div className="grid gap-3 text-sm text-slate-200 sm:grid-cols-3">
              <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                <div className="text-xs uppercase tracking-[0.18em] text-slate-400">Bench</div>
                <div className="mt-2 font-medium">{primaryCase?.bench_label ?? "Unspecified"}</div>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                <div className="text-xs uppercase tracking-[0.18em] text-slate-400">Next date</div>
                <div className="mt-2 font-medium">{formatDate(primaryCase?.next_listing_date)}</div>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                <div className="text-xs uppercase tracking-[0.18em] text-slate-400">Status</div>
                <div className="mt-2 font-medium">{primaryCase?.status_text ?? "Unspecified"}</div>
              </div>
            </div>
          </Card>

          <div className="grid gap-4">
            <Card className="space-y-3">
              <div className="text-xs uppercase tracking-[0.22em] text-slate-400">
                Official import
              </div>
              <div className="grid gap-3">
                <select
                  className="h-11 rounded-2xl border border-white/10 bg-slate-950/40 px-4 text-sm text-white"
                  value={importArtifactKind}
                  onChange={(event) => setImportArtifactKind(event.target.value)}
                >
                  <option value="case_history">Case history HTML</option>
                  <option value="cause_list">Cause list HTML</option>
                  <option value="order">Order or judgment artifact</option>
                </select>
                <input
                  aria-label="Official artifact file"
                  className="block w-full text-sm text-slate-300 file:mr-4 file:rounded-2xl file:border-0 file:bg-white/10 file:px-4 file:py-2 file:text-sm file:text-white"
                  type="file"
                  onChange={(event) => setImportFile(event.target.files?.[0] ?? null)}
                />
                <Button onClick={() => void importOfficialArtifact()} disabled={!importFile}>
                  Import official artifact
                </Button>
                {importStatus ? (
                  <div className="text-sm text-emerald-100">{importStatus}</div>
                ) : null}
              </div>
            </Card>

            <Card>
              <div className="text-xs uppercase tracking-[0.22em] text-slate-400">
                Hearing delta
              </div>
              <div className="mt-3 text-sm leading-6 text-slate-200">
                {hearingDelta?.summary ?? "No delta has been computed yet."}
              </div>
              {hearingDelta?.changed_items?.length ? (
                <ul className="mt-3 space-y-2 text-sm text-slate-300">
                  {hearingDelta.changed_items.map((item) => (
                    <li key={item} className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2">
                      {item}
                    </li>
                  ))}
                </ul>
              ) : null}
            </Card>

            <Card>
              <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Data coverage</div>
              <div className="mt-3 flex flex-wrap gap-2">
                <Badge variant={badgeVariant(judgeProfile?.confidence)}>
                  Judge: {judgeProfile?.sample_size ?? 0} samples
                </Badge>
                <Badge variant={badgeVariant(courtProfile?.confidence)}>
                  Court: {courtProfile?.sample_size ?? 0} samples
                </Badge>
              </div>
            </Card>
          </div>
        </div>
      </header>

      <div className="flex flex-wrap gap-2">
        {([
          ["chronology", "Chronology"],
          ["filings", "Filing Diff"],
          ["party-memory", "Party Memory"],
          ["case-memory", "Case Memory"],
          ["connected", "Connected Matters"]
        ] as Array<[TabKey, string]>).map(([key, label]) => (
          <Button
            key={key}
            variant={tab === key ? "primary" : "secondary"}
            onClick={() => setTab(key)}
          >
            {label}
          </Button>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <Card className="space-y-4">
          {tab === "chronology" ? (
            <div className="space-y-3">
              {chronology.map((item) => (
                <div key={item.id} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="neutral">{formatDate(item.event_date)}</Badge>
                    <Badge variant="info">{item.source_kind.replaceAll("_", " ")}</Badge>
                  </div>
                  <div className="mt-3 text-lg font-medium text-white">{item.title}</div>
                  <div className="mt-2 text-sm leading-6 text-slate-300">{item.description}</div>
                  <div className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-500">
                    {item.source_label}
                  </div>
                </div>
              ))}
            </div>
          ) : null}

          {tab === "filings" ? (
            <div className="space-y-3">
              {filings.map((filing) => (
                <div key={filing.id} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="neutral">{filing.filing_side}</Badge>
                    <Badge variant="info">{filing.filing_type}</Badge>
                    <Badge variant="neutral">{formatDate(filing.filing_date)}</Badge>
                  </div>
                  <div className="mt-3 text-lg font-medium text-white">{filing.title}</div>
                  <div className="mt-2 text-sm text-slate-300">{filing.extracted_summary ?? "No summary"}</div>
                  <div className="mt-3 grid gap-3 sm:grid-cols-2">
                    <div className="rounded-2xl border border-white/10 bg-black/10 p-3">
                      <div className="text-xs uppercase tracking-[0.18em] text-slate-400">
                        New Fact Assertions
                      </div>
                      <div className="mt-2 text-sm text-slate-200">
                        {filing.delta.new_fact_assertions.join(", ") || "None"}
                      </div>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-black/10 p-3">
                      <div className="text-xs uppercase tracking-[0.18em] text-slate-400">
                        New Denials
                      </div>
                      <div className="mt-2 text-sm text-slate-200">
                        {filing.delta.new_denials.join(", ") || "None"}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : null}

          {tab === "party-memory" ? (
            <div className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {parties.map((party) => (
                  <Button
                    key={party.party_id}
                    size="sm"
                    variant={currentPartyId === party.party_id ? "primary" : "secondary"}
                    onClick={async () => {
                      const api = createBrowserApiClient();
                      const result = await api.getPartyMemory(party.party_id);
                      if (result.ok) {
                        setCurrentPartyId(party.party_id);
                        setPartyMemory(result.data);
                      }
                    }}
                  >
                    {party.display_name}
                  </Button>
                ))}
              </div>
              <pre className="overflow-x-auto whitespace-pre-wrap rounded-2xl border border-white/10 bg-black/20 p-4 text-sm leading-7 text-slate-200">
                {partyMemory?.markdown_content ?? "No litigant memory has been generated yet."}
              </pre>
            </div>
          ) : null}

          {tab === "case-memory" ? (
            <pre className="overflow-x-auto whitespace-pre-wrap rounded-2xl border border-white/10 bg-black/20 p-4 text-sm leading-7 text-slate-200">
              {caseMemory?.markdown_content ?? "No case memory has been generated yet."}
            </pre>
          ) : null}

          {tab === "connected" ? (
            <div className="space-y-4">
              <div className="flex gap-3">
                <Input
                  placeholder="Search across public and private artifacts"
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                />
                <Button onClick={() => void runSearch()} disabled={searchQuery.trim().length < 2}>
                  Hybrid search
                </Button>
              </div>
              {searchResults.length ? (
                <div className="space-y-3">
                  {searchResults.map((item) => (
                    <div key={`${item.entity_kind}-${item.title}`} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                      <div className="flex flex-wrap gap-2">
                        <Badge variant="info">{item.entity_kind.replaceAll("_", " ")}</Badge>
                        <Badge variant="neutral">score {item.score.toFixed(2)}</Badge>
                      </div>
                      <div className="mt-3 text-base font-medium text-white">{item.title}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-300">
                  Hybrid search covers matter documents, imported public case events, filings, and
                  generated memories once you add a query.
                </div>
              )}

              <div className="space-y-3">
                {connected.map((item) => (
                  <div key={item.id} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                    <div className="text-sm text-slate-300">{item.court_name ?? "Unknown court"}</div>
                    <div className="mt-1 text-lg font-medium text-white">{item.case_number}</div>
                    <div className="mt-2 text-sm text-slate-300">{item.title}</div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </Card>

        <Card className="space-y-4">
          <div>
            <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Source rail</div>
            <div className="mt-1 text-base font-medium text-white">
              Evidence, freshness, and profiles
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="text-xs uppercase tracking-[0.18em] text-slate-400">Judge profile</div>
            <div className="mt-2 text-sm text-slate-200">
              {judgeProfile?.metrics
                ? Object.entries(judgeProfile.metrics)
                    .map(([key, value]) => `${key.replaceAll("_", " ")}: ${String(value ?? "n/a")}`)
                    .join(" | ")
                : "No judge profile snapshot yet."}
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="text-xs uppercase tracking-[0.18em] text-slate-400">Court profile</div>
            <div className="mt-2 text-sm text-slate-200">
              {courtProfile?.metrics
                ? Object.entries(courtProfile.metrics)
                    .map(([key, value]) => `${key.replaceAll("_", " ")}: ${String(value ?? "n/a")}`)
                    .join(" | ")
                : "No court profile snapshot yet."}
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
            <div className="text-xs uppercase tracking-[0.18em] text-slate-400">Source references</div>
            <div className="mt-3 space-y-2 text-sm text-slate-300">
              {selectedEvidence.length ? (
                selectedEvidence.slice(0, 12).map((ref, index) => (
                  <div key={`${index}-${JSON.stringify(ref)}`} className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2">
                    {Object.entries(ref)
                      .map(([key, value]) => `${key}: ${String(value)}`)
                      .join(" | ")}
                  </div>
                ))
              ) : (
                <div>No source references loaded for this panel yet.</div>
              )}
            </div>
          </div>
        </Card>
      </div>
    </section>
  );
}
