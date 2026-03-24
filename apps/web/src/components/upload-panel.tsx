"use client";

import Link from "next/link";
import {
  useState,
  useTransition,
  type ChangeEvent,
  type FormEvent
} from "react";
import type { DocumentResponse, DocumentSourceType } from "@legalos/contracts";
import { Badge, Button, Card, Field, Input, Select, Textarea } from "@legalos/ui";
import { createBrowserApiClient } from "@/lib/api/client";

const documentRoles: Array<{ value: DocumentSourceType; label: string }> = [
  { value: "my_document", label: "My docs" },
  { value: "opponent_document", label: "Opponent docs" },
  { value: "court_document", label: "Court docs" },
  { value: "public_law", label: "Public law" },
  { value: "work_product", label: "Work product" }
];

export function UploadPanel({ matterId }: { matterId: string }) {
  const [role, setRole] = useState(documentRoles[0].value);
  const [notes, setNotes] = useState("");
  const [processInBackground, setProcessInBackground] = useState(true);
  const [files, setFiles] = useState<File[]>([]);
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);

    if (!files.length) {
      setMessage("Select at least one file to upload.");
      return;
    }

    startTransition(() => {
      void (async () => {
        const api = createBrowserApiClient();
        const uploaded: DocumentResponse[] = [];
        for (const file of files) {
          const document = await api.uploadMatterDocument({
            matterId,
            file,
            sourceType: role,
            title: file.name,
            legalIssue: notes || undefined,
            processInBackground
          });
          uploaded.push(document);
        }
        setDocuments(uploaded);
        setMessage(
          processInBackground
            ? `Queued ${uploaded.length} document(s). Open the bundle map to watch async processing and bundle-analysis status.`
            : `Uploaded ${uploaded.length} document(s) into the matter pipeline.`
        );
        setFiles([]);
      })().catch((cause) => {
        setMessage(cause instanceof Error ? cause.message : "Upload failed");
      });
    });
  }

  return (
    <section className="grid gap-6 lg:grid-cols-[1fr_0.85fr]">
      <Card className="space-y-5">
        <div className="space-y-2">
          <div className="text-xs uppercase tracking-[0.24em] text-slate-400">Document operating system</div>
          <h1 className="text-3xl font-semibold text-white">Upload matter files</h1>
          <p className="text-sm leading-6 text-slate-300">
            Files are queued into the ingest pipeline with explicit source-role classification, quote-lock extraction, and bundle-analysis rebuilding.
          </p>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <Field label="Document role">
            <Select
              value={role}
              onChange={(event: ChangeEvent<HTMLSelectElement>) =>
                setRole(event.target.value as DocumentSourceType)
              }
              options={documentRoles}
            />
          </Field>

          <Field label="Notes / legal issue">
                <Textarea
              value={notes}
              onChange={(event: ChangeEvent<HTMLTextAreaElement>) => setNotes(event.target.value)}
              placeholder="Optional extraction hints, exhibit links, or issue tags"
            />
          </Field>

          <Field label="Files">
            <Input
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.rtf,.txt,.html,.htm,.png,.jpg,.jpeg,.tif,.tiff,.zip,.eml"
              onChange={(event: ChangeEvent<HTMLInputElement>) =>
                setFiles(Array.from(event.target.files ?? []))
              }
            />
          </Field>

          <label className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-200">
            <input
              type="checkbox"
              checked={processInBackground}
              onChange={(event: ChangeEvent<HTMLInputElement>) =>
                setProcessInBackground(event.target.checked)
              }
              className="mt-1 h-4 w-4 accent-saffron-500"
            />
            <span>
              Process in background for larger bundles. This exposes queued and processing states in
              the Bundle Map before chronology and contradiction analysis finish.
            </span>
          </label>

          <Button type="submit" className="w-full" disabled={isPending}>
            {isPending ? "Uploading..." : processInBackground ? "Upload and enqueue" : "Upload and extract"}
          </Button>
          <Button variant="ghost" asChild className="w-full">
            <Link href={`/matters/${matterId}/bundle`}>Open bundle map</Link>
          </Button>
        </form>

        {message ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-200">{message}</div>
        ) : null}
      </Card>

      <Card className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Uploaded documents</div>
            <div className="mt-1 text-base font-medium text-white">Processing state</div>
          </div>
          <Badge variant="info">Background ingest</Badge>
        </div>

        <div className="space-y-3">
          {documents.length ? (
            documents.map((document) => (
              <article key={document.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="text-sm font-medium text-white">{document.title}</div>
                    <div className="text-xs text-slate-400">{document.source_type}</div>
                  </div>
                  <Badge variant="warning">{document.processing_status}</Badge>
                </div>
                <div className="mt-3 text-sm leading-6 text-slate-300">
                  {document.citation_text ?? document.legal_issue ?? "Stored with paragraph-level quote spans."}
                </div>
                <div className="mt-3 space-y-1 text-xs text-slate-400">
                  <div>Started: {document.processing_started_at ?? "pending"}</div>
                  <div>Completed: {document.processing_completed_at ?? "pending"}</div>
                  <div>Method: {document.extraction_method ?? "pending"}</div>
                  {document.processing_error ? <div>Error: {document.processing_error}</div> : null}
                </div>
              </article>
            ))
          ) : (
            <div className="rounded-2xl border border-dashed border-white/10 px-4 py-8 text-sm text-slate-400">
              Uploaded documents will appear here with extraction and indexing status.
            </div>
          )}
        </div>
      </Card>
    </section>
  );
}
