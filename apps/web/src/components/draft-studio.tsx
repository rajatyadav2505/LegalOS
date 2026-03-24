"use client";

import { useEffect, useState, useTransition } from "react";
import type {
  DraftDocument,
  DraftDocumentType,
  StylePack,
  StylePackCreateRequest
} from "@legalos/contracts";
import { Badge, Button, Card, Field, Input, Select, Textarea } from "@legalos/ui";
import { createBrowserApiClient } from "@/lib/api/client";

const draftTypeOptions: Array<{ value: DraftDocumentType; label: string }> = [
  { value: "petition", label: "Petition" },
  { value: "reply", label: "Reply" },
  { value: "written_submission", label: "Written submission" },
  { value: "affidavit", label: "Affidavit" },
  { value: "application", label: "Application" },
  { value: "synopsis", label: "Synopsis" },
  { value: "list_of_dates", label: "List of dates" },
  { value: "legal_notice", label: "Legal notice" },
  { value: "settlement_note", label: "Settlement note" }
];

export function DraftStudio({ matterId }: { matterId: string }) {
  const [stylePacks, setStylePacks] = useState<StylePack[]>([]);
  const [drafts, setDrafts] = useState<DraftDocument[]>([]);
  const [selectedDraft, setSelectedDraft] = useState<DraftDocument | null>(null);
  const [documentType, setDocumentType] = useState<DraftDocumentType>("petition");
  const [draftTitle, setDraftTitle] = useState("");
  const [stylePackId, setStylePackId] = useState<string>("");
  const [styleName, setStyleName] = useState("Chamber Formal");
  const [styleTone, setStyleTone] = useState("formal and restrained");
  const [styleOpening, setStyleOpening] = useState("It is most respectfully submitted");
  const [stylePrayer, setStylePrayer] = useState("It is therefore most respectfully prayed");
  const [styleNotes, setStyleNotes] = useState("Use short proposition-led paragraphs.");
  const [exportedMarkdown, setExportedMarkdown] = useState<string | null>(null);
  const [redline, setRedline] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function loadWorkspace() {
    startTransition(() => {
      const api = createBrowserApiClient();
      void Promise.all([api.getStylePacks(), api.listDrafts(matterId)]).then(([packs, draftList]) => {
        if (packs.ok) {
          setStylePacks(packs.data);
        }
        if (draftList.ok) {
          setDrafts(draftList.data);
          setSelectedDraft((current) => current ?? draftList.data[0] ?? null);
        }
        if (!packs.ok) {
          setError(packs.message);
        } else if (!draftList.ok) {
          setError(draftList.message);
        } else {
          setError(null);
        }
      });
    });
  }

  useEffect(() => {
    loadWorkspace();
  }, [matterId]);

  async function handleCreateStylePack() {
    setMessage(null);
    setError(null);
    try {
      const api = createBrowserApiClient();
      const payload: StylePackCreateRequest = {
        name: styleName,
        tone: styleTone,
        openingPhrase: styleOpening,
        prayerStyle: stylePrayer,
        citationStyle: "anchor-plus-checksum",
        voiceNotes: styleNotes,
        sourceDocumentIds: []
      };
      const created = await api.createStylePack(payload);
      setStylePacks((current) => [created, ...current]);
      setStylePackId(created.id);
      setMessage(`Created style pack ${created.name}.`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not create style pack");
    }
  }

  async function handleGenerateDraft() {
    setMessage(null);
    setError(null);
    setExportedMarkdown(null);
    setRedline(null);
    try {
      const api = createBrowserApiClient();
      const generated = await api.generateDraft(matterId, {
        documentType,
        title: draftTitle || undefined,
        stylePackId: stylePackId || undefined,
        annexureDocumentIds: [],
        includeSavedAuthorities: true,
        includeBundleIntelligence: true
      });
      setSelectedDraft(generated);
      setDrafts((current) => [generated, ...current]);
      setMessage(`Generated ${generated.document_type.replaceAll("_", " ")} v${generated.version_number}.`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Draft generation failed");
    }
  }

  async function handleExportDraft() {
    if (!selectedDraft) {
      return;
    }
    setMessage(null);
    setError(null);
    try {
      const api = createBrowserApiClient();
      const exported = await api.exportDraft(selectedDraft.id);
      setExportedMarkdown(exported.content);
      setMessage(`Exported ${exported.file_name}.`);
      const refreshed = await api.getDraft(selectedDraft.id);
      if (refreshed.ok) {
        setSelectedDraft(refreshed.data);
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Draft export failed");
    }
  }

  async function handleLoadRedline() {
    if (!selectedDraft) {
      return;
    }
    const previous = drafts.find(
      (item) =>
        item.document_type === selectedDraft.document_type &&
        item.version_number === selectedDraft.version_number - 1
    );
    if (!previous) {
      setRedline("No earlier version is available for comparison.");
      return;
    }
    setMessage(null);
    setError(null);
    try {
      const api = createBrowserApiClient();
      const diff = await api.getDraftRedline(selectedDraft.id, previous.id);
      setRedline(diff.sections.map((section) => `## ${section.label}\n${section.diff}`).join("\n\n"));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Redline generation failed");
    }
  }

  return (
    <section className="space-y-6">
      <header className="flex flex-col gap-4 border-b border-white/10 pb-5 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-2">
          <div className="text-xs uppercase tracking-[0.24em] text-slate-400">Draft studio</div>
          <h1 className="text-3xl font-semibold text-white">Structured drafting</h1>
          <p className="max-w-3xl text-sm leading-6 text-slate-300">
            Drafts are built from matter data, bundle intelligence, and saved verified authorities only. Unresolved facts remain visible as placeholders.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge variant="info">{stylePacks.length} style packs</Badge>
          <Badge variant="warning">{drafts.length} drafts</Badge>
          <Button variant="secondary" onClick={loadWorkspace} disabled={isPending}>
            {isPending ? "Refreshing..." : "Refresh"}
          </Button>
        </div>
      </header>

      {message ? <Card className="text-sm text-emerald-100">{message}</Card> : null}
      {error ? <Card className="text-sm text-red-100">{error}</Card> : null}

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="space-y-6">
          <Card className="space-y-4">
            <div>
              <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Generate draft</div>
              <div className="mt-1 text-base font-medium text-white">Versioned document output</div>
            </div>
            <Field label="Document type">
              <Select
                value={documentType}
                options={draftTypeOptions}
                onChange={(event) => setDocumentType(event.target.value as DraftDocumentType)}
              />
            </Field>
            <Field label="Draft title">
              <Input
                value={draftTitle}
                onChange={(event) => setDraftTitle(event.target.value)}
                placeholder="Optional custom title"
              />
            </Field>
            <Field label="Style pack">
              <Select
                value={stylePackId}
                options={[
                  { value: "", label: "Default chamber-neutral style" },
                  ...stylePacks.map((item) => ({ value: item.id, label: item.name }))
                ]}
                onChange={(event) => setStylePackId(event.target.value)}
              />
            </Field>
            <Button onClick={() => void handleGenerateDraft()} className="w-full">
              Generate structured draft
            </Button>
          </Card>

          <Card className="space-y-4">
            <div>
              <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Style Twin</div>
              <div className="mt-1 text-base font-medium text-white">Create a chamber style pack</div>
            </div>
            <Field label="Pack name">
              <Input value={styleName} onChange={(event) => setStyleName(event.target.value)} />
            </Field>
            <Field label="Tone">
              <Input value={styleTone} onChange={(event) => setStyleTone(event.target.value)} />
            </Field>
            <Field label="Opening phrase">
              <Input
                value={styleOpening}
                onChange={(event) => setStyleOpening(event.target.value)}
              />
            </Field>
            <Field label="Prayer style">
              <Input value={stylePrayer} onChange={(event) => setStylePrayer(event.target.value)} />
            </Field>
            <Field label="Voice notes">
              <Textarea
                value={styleNotes}
                onChange={(event) => setStyleNotes(event.target.value)}
                placeholder="Short chamber voice guidance"
              />
            </Field>
            <Button variant="secondary" onClick={() => void handleCreateStylePack()} className="w-full">
              Save style pack
            </Button>
          </Card>

          <Card className="space-y-4">
            <div>
              <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Draft versions</div>
              <div className="mt-1 text-base font-medium text-white">Select a generated draft</div>
            </div>
            <div className="space-y-3">
              {drafts.length ? (
                drafts.map((draft) => (
                  <button
                    key={draft.id}
                    type="button"
                    onClick={() => {
                      setSelectedDraft(draft);
                      setExportedMarkdown(null);
                      setRedline(null);
                    }}
                    className={[
                      "w-full rounded-2xl border p-4 text-left transition-colors",
                      selectedDraft?.id === draft.id
                        ? "border-saffron-500/40 bg-saffron-500/10"
                        : "border-white/10 bg-white/5 hover:border-white/20"
                    ].join(" ")}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-white">{draft.title}</div>
                        <div className="text-xs text-slate-400">
                          {draft.document_type.replaceAll("_", " ")} • version {draft.version_number}
                        </div>
                      </div>
                      <Badge variant={draft.unresolved_placeholders.length ? "warning" : "success"}>
                        {draft.status}
                      </Badge>
                    </div>
                  </button>
                ))
              ) : (
                <div className="rounded-2xl border border-dashed border-white/10 px-4 py-8 text-sm text-slate-400">
                  No drafts yet. Generate a petition, reply, or written submission.
                </div>
              )}
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Selected draft</div>
                <div className="mt-1 text-base font-medium text-white">
                  {selectedDraft ? selectedDraft.title : "Awaiting generation"}
                </div>
              </div>
              {selectedDraft ? (
                <div className="flex gap-2">
                  <Button size="sm" variant="secondary" onClick={() => void handleExportDraft()}>
                    Export
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => void handleLoadRedline()}>
                    Redline
                  </Button>
                </div>
              ) : null}
            </div>
            {selectedDraft ? (
              <div className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  <Badge variant="info">{selectedDraft.document_type}</Badge>
                  <Badge variant="neutral">v{selectedDraft.version_number}</Badge>
                  <Badge variant={selectedDraft.unresolved_placeholders.length ? "warning" : "success"}>
                    {selectedDraft.unresolved_placeholders.length} placeholders
                  </Badge>
                </div>
                {selectedDraft.style_pack ? (
                  <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-200">
                    Style pack: {selectedDraft.style_pack.name} • {selectedDraft.style_pack.tone}
                  </div>
                ) : null}
                <div className="space-y-3">
                  {selectedDraft.sections.map((section) => (
                    <article key={section.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                      <div className="text-sm font-semibold text-white">{section.label}</div>
                      <pre className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-200">
                        {section.body_text}
                      </pre>
                    </article>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-sm text-slate-400">
                The draft pane will show sections, verified authorities, and annexures after generation.
              </div>
            )}
          </Card>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card className="space-y-4">
              <div>
                <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Verified authorities</div>
                <div className="mt-1 text-base font-medium text-white">Inserted from saved research only</div>
              </div>
              <div className="space-y-3">
                {selectedDraft?.authorities_used.length ? (
                  selectedDraft.authorities_used.map((item) => (
                    <article key={item.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                      <div className="text-sm font-semibold text-white">{item.issue_label}</div>
                      <div className="mt-2 text-xs text-slate-400">
                        {item.treatment} • {item.anchor_label} • checksum {item.checksum}
                      </div>
                      <div className="mt-3 text-sm leading-6 text-slate-200">{item.quote_text}</div>
                    </article>
                  ))
                ) : (
                  <div className="text-sm text-slate-400">
                    Save verified authorities in research first, then regenerate the draft.
                  </div>
                )}
              </div>
            </Card>

            <Card className="space-y-4">
              <div>
                <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Annexures and placeholders</div>
                <div className="mt-1 text-base font-medium text-white">Visible unresolved work</div>
              </div>
              <div className="space-y-3">
                {selectedDraft?.annexures.length ? (
                  selectedDraft.annexures.map((annexure) => (
                    <div key={annexure.id} className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-200">
                      {annexure.label}: {annexure.title}
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-slate-400">No annexures yet.</div>
                )}
                {selectedDraft?.unresolved_placeholders.length ? (
                  selectedDraft.unresolved_placeholders.map((item, index) => (
                    <div key={`${item}-${index}`} className="rounded-2xl border border-amber-500/20 bg-amber-500/10 p-4 text-sm text-amber-50">
                      {item}
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-slate-400">No unresolved placeholders remain in this version.</div>
                )}
              </div>
            </Card>
          </div>

          {exportedMarkdown ? (
            <Card className="space-y-3">
              <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Export preview</div>
              <pre className="max-h-80 overflow-auto whitespace-pre-wrap text-sm leading-6 text-slate-200">
                {exportedMarkdown}
              </pre>
            </Card>
          ) : null}

          {redline ? (
            <Card className="space-y-3">
              <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Redline</div>
              <pre className="max-h-80 overflow-auto whitespace-pre-wrap text-sm leading-6 text-slate-200">
                {redline}
              </pre>
            </Card>
          ) : null}
        </div>
      </div>
    </section>
  );
}
