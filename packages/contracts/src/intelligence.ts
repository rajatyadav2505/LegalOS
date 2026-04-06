import { z } from "zod";

export const SourceSystemSchema = z.enum([
  "district_ecourts",
  "high_court_services",
  "ecourts_judgments",
  "njdg",
  "supreme_court_india"
]);

export const ArtifactKindSchema = z.enum([
  "case_history",
  "cause_list",
  "order",
  "judgment",
  "filing",
  "registry_note",
  "snapshot_html",
  "snapshot_pdf",
  "snapshot_json"
]);

export const ConfidenceBandSchema = z.enum(["low", "medium", "high"]);
export const VerificationStatusSchema = z.enum([
  "imported",
  "parsed",
  "verified",
  "needs_review",
  "rejected"
]);

export const JobKindSchema = z.enum([
  "external_case_sync",
  "raw_snapshot_import",
  "artifact_extract",
  "case_event_rebuild",
  "filing_parse",
  "party_resolution",
  "litigant_memory_refresh",
  "case_memory_refresh",
  "judge_profile_refresh",
  "court_profile_refresh",
  "hybrid_index_refresh",
  "hearing_delta_refresh"
]);

export const JobStatusSchema = z.enum([
  "pending",
  "running",
  "succeeded",
  "failed",
  "retryable",
  "cancelled"
]);

export const HybridEntityKindSchema = z.enum([
  "document",
  "court_artifact",
  "case_event",
  "case_filing",
  "litigant_memory",
  "case_memory",
  "judge_profile",
  "court_profile"
]);

export const ProvenanceSchema = z.object({
  source_system: SourceSystemSchema,
  source_url: z.string().nullable(),
  raw_snapshot_id: z.string().uuid().nullable(),
  observed_at: z.string().nullable(),
  fetched_at: z.string().nullable(),
  content_hash: z.string().nullable(),
  parser_version: z.string().nullable(),
  confidence: ConfidenceBandSchema,
  verification_status: VerificationStatusSchema
});

export const JobSchema = z.object({
  id: z.string().uuid(),
  kind: JobKindSchema,
  status: JobStatusSchema,
  idempotency_key: z.string(),
  attempt_count: z.number().int().nonnegative(),
  max_attempts: z.number().int().positive(),
  last_error: z.string().nullable(),
  created_at: z.string(),
  completed_at: z.string().nullable()
});

export const ExternalCaseLinkRequestSchema = z.object({
  source_system: SourceSystemSchema,
  case_title: z.string().min(3),
  case_number: z.string().min(2),
  court_name: z.string().min(3),
  cnr_number: z.string().optional().nullable(),
  source_url: z.string().url().optional().nullable(),
  relationship_label: z.string().default("primary")
});

export const ExternalCaseSummarySchema = z.object({
  id: z.string().uuid(),
  matter_link_id: z.string().uuid().nullable(),
  court_id: z.string().uuid().nullable(),
  judge_id: z.string().uuid().nullable(),
  title: z.string(),
  case_number: z.string(),
  cnr_number: z.string().nullable(),
  case_type: z.string().nullable(),
  court_name: z.string().nullable(),
  bench_label: z.string().nullable(),
  judge_name: z.string().nullable(),
  status_text: z.string().nullable(),
  neutral_citation: z.string().nullable(),
  latest_stage: z.string().nullable(),
  next_listing_date: z.string().nullable(),
  relationship_label: z.string().nullable(),
  is_primary: z.boolean(),
  provenance: ProvenanceSchema
});

export const CasePartySummarySchema = z.object({
  party_id: z.string().uuid(),
  display_name: z.string(),
  role: z.string()
});

export const MatterExternalCaseListSchema = z.object({
  items: z.array(ExternalCaseSummarySchema),
  total: z.number().int().nonnegative()
});

export const MergedChronologyItemSchema = z.object({
  id: z.string(),
  event_date: z.string(),
  title: z.string(),
  description: z.string(),
  source_kind: z.string(),
  source_label: z.string(),
  confidence: z.union([z.number(), z.string()]),
  provenance: z.record(z.string()).nullable().optional()
});

export const HearingDeltaSchema = z.object({
  summary: z.string(),
  changed_items: z.array(z.string()),
  latest_event_date: z.string().nullable()
});

export const FilingLineageDeltaSchema = z.object({
  new_fact_assertions: z.array(z.string()),
  new_denials: z.array(z.string())
});

export const FilingLineageItemSchema = z.object({
  id: z.string(),
  external_case_id: z.string(),
  case_number: z.string(),
  filing_side: z.string(),
  filing_type: z.string(),
  title: z.string(),
  filing_date: z.string().nullable(),
  reliefs_sought: z.array(z.string()),
  fact_assertions: z.array(z.string()),
  admissions: z.array(z.string()),
  denials: z.array(z.string()),
  annexures_relied: z.array(z.string()),
  statutes_cited: z.array(z.string()),
  precedents_cited: z.array(z.string()),
  extracted_summary: z.string().nullable(),
  delta: FilingLineageDeltaSchema
});

export const MemorySnapshotSchema = z.object({
  id: z.string().uuid(),
  storage_path: z.string(),
  markdown_content: z.string(),
  source_refs: z.array(z.record(z.unknown())),
  confidence: ConfidenceBandSchema,
  verification_status: VerificationStatusSchema,
  created_at: z.string()
});

export const ProfileSnapshotSchema = z.object({
  id: z.string().uuid(),
  storage_path: z.string(),
  markdown_content: z.string(),
  source_refs: z.array(z.record(z.unknown())),
  confidence: ConfidenceBandSchema,
  sample_size: z.number().int().nonnegative(),
  freshness_timestamp: z.string().nullable(),
  metrics: z.record(z.unknown()),
  created_at: z.string()
});

export const HybridSearchItemSchema = z.object({
  title: z.string(),
  entity_kind: HybridEntityKindSchema,
  score: z.number(),
  metadata: z.record(z.unknown())
});

export const HybridSearchSchema = z.object({
  items: z.array(HybridSearchItemSchema),
  total: z.number().int().nonnegative()
});

export const ConnectedMatterSchema = z.object({
  id: z.string().uuid(),
  title: z.string(),
  case_number: z.string(),
  cnr_number: z.string().nullable(),
  court_name: z.string().nullable(),
  next_listing_date: z.string().nullable()
});

export type ConnectedMatter = z.infer<typeof ConnectedMatterSchema>;
export type CasePartySummary = z.infer<typeof CasePartySummarySchema>;
export type ExternalCaseLinkRequest = z.infer<typeof ExternalCaseLinkRequestSchema>;
export type ExternalCaseSummary = z.infer<typeof ExternalCaseSummarySchema>;
export type FilingLineageItem = z.infer<typeof FilingLineageItemSchema>;
export type HearingDelta = z.infer<typeof HearingDeltaSchema>;
export type HybridSearch = z.infer<typeof HybridSearchSchema>;
export type HybridSearchItem = z.infer<typeof HybridSearchItemSchema>;
export type Job = z.infer<typeof JobSchema>;
export type MatterExternalCaseList = z.infer<typeof MatterExternalCaseListSchema>;
export type MemorySnapshot = z.infer<typeof MemorySnapshotSchema>;
export type MergedChronologyItem = z.infer<typeof MergedChronologyItemSchema>;
export type ProfileSnapshot = z.infer<typeof ProfileSnapshotSchema>;
