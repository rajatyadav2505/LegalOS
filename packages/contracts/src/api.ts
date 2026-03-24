import { z } from "zod";

export const UserRoleSchema = z.enum(["admin", "member"]);
export const MatterStageSchema = z.enum([
  "pre_filing",
  "filing",
  "notice",
  "evidence",
  "arguments",
  "orders"
]);
export const MatterStatusSchema = z.enum(["active", "hold", "closed"]);
export const DocumentSourceTypeSchema = z.enum([
  "public_law",
  "my_document",
  "opponent_document",
  "court_document",
  "work_product"
]);
export const ProcessingStatusSchema = z.enum(["queued", "processing", "ready", "failed"]);
export const AuthorityKindSchema = z.enum([
  "constitution",
  "statute",
  "judgment",
  "note",
  "matter_document"
]);
export const AuthorityTreatmentSchema = z.enum(["apply", "distinguish", "adverse", "draft"]);
export const EntityTypeSchema = z.enum([
  "person",
  "organization",
  "role",
  "exhibit",
  "issue"
]);
export const RelationSeveritySchema = z.enum(["low", "medium", "high"]);

export const ApiErrorSchema = z.object({
  detail: z.string().optional(),
  message: z.string().optional(),
  code: z.string().optional()
});

export const LoginRequestSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1)
});

export const UserSchema = z.object({
  id: z.string().uuid(),
  organization_id: z.string().uuid(),
  email: z.string().email(),
  full_name: z.string(),
  role: UserRoleSchema
});

export const LoginResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.literal("bearer"),
  user: UserSchema
});

export const MatterSummarySchema = z.object({
  id: z.string().uuid(),
  title: z.string(),
  reference_code: z.string(),
  forum: z.string(),
  stage: MatterStageSchema,
  status: MatterStatusSchema,
  next_hearing_date: z.string().nullable(),
  summary: z.string().nullable(),
  updated_at: z.string(),
  document_count: z.number().int().nonnegative(),
  saved_authority_count: z.number().int().nonnegative()
});

export const MatterDetailSchema = MatterSummarySchema.extend({
  organization_id: z.string().uuid(),
  owner_user_id: z.string().uuid()
});

export const MatterListSchema = z.array(MatterSummarySchema);

export const DocumentResponseSchema = z.object({
  id: z.string().uuid(),
  matter_id: z.string().uuid().nullable(),
  title: z.string(),
  file_name: z.string(),
  content_type: z.string(),
  source_type: DocumentSourceTypeSchema,
  processing_status: ProcessingStatusSchema,
  authority_kind: AuthorityKindSchema,
  citation_text: z.string().nullable(),
  court: z.string().nullable(),
  forum: z.string().nullable(),
  bench: z.string().nullable(),
  decision_date: z.string().nullable(),
  legal_issue: z.string().nullable(),
  processing_stage: z.string().nullable(),
  processing_progress: z.number().int().min(0).max(100).nullable(),
  extraction_method: z.string().nullable(),
  processing_error: z.string().nullable(),
  processing_started_at: z.string().nullable(),
  processing_completed_at: z.string().nullable(),
  created_at: z.string()
});

export const BundleDocumentSummarySchema = z.object({
  id: z.string().uuid(),
  title: z.string(),
  source_type: DocumentSourceTypeSchema,
  processing_status: ProcessingStatusSchema,
  legal_issue: z.string().nullable(),
  processing_stage: z.string().nullable(),
  processing_progress: z.number().int().min(0).max(100).nullable(),
  processing_error: z.string().nullable(),
  created_at: z.string()
});

export const BundleProcessingStageSchema = z.object({
  label: z.string(),
  status: ProcessingStatusSchema,
  count: z.number().int().nonnegative()
});

export const BundleProcessingOverviewSchema = z.object({
  overall_status: ProcessingStatusSchema,
  total_documents: z.number().int().nonnegative(),
  processed_documents: z.number().int().nonnegative(),
  ready_documents: z.number().int().nonnegative(),
  failed_documents: z.number().int().nonnegative(),
  processing_documents: z.number().int().nonnegative(),
  queued_documents: z.number().int().nonnegative(),
  last_updated_at: z.string(),
  stages: z.array(BundleProcessingStageSchema)
});

export const BundleChronologyItemSchema = z.object({
  id: z.string().uuid(),
  date: z.string(),
  title: z.string(),
  summary: z.string(),
  source_title: z.string(),
  source_type: DocumentSourceTypeSchema,
  anchor_label: z.string(),
  confidence: z.number(),
});

export const BundleClusterSchema = z.object({
  id: z.string(),
  cluster_type: z.string(),
  label: z.string(),
  description: z.string(),
  document_count: z.number().int().nonnegative(),
  dominant_issue: z.string(),
  source_type: DocumentSourceTypeSchema,
  status: z.string()
});

export const BundleContradictionSchema = z.object({
  id: z.string().uuid(),
  issue: z.string(),
  severity: z.string(),
  summary: z.string(),
  contradiction_kind: z.string(),
  source_a: z.string(),
  source_b: z.string(),
  source_a_label: z.string(),
  source_b_label: z.string(),
  source_a_type: DocumentSourceTypeSchema,
  source_b_type: DocumentSourceTypeSchema
});

export const BundleDuplicateMemberSchema = z.object({
  id: z.string().uuid(),
  title: z.string(),
  anchor_label: z.string()
});

export const BundleDuplicateGroupSchema = z.object({
  id: z.string(),
  canonical_title: z.string(),
  duplicate_count: z.number().int().nonnegative(),
  reason: z.string(),
  source_type: DocumentSourceTypeSchema,
  members: z.array(BundleDuplicateMemberSchema)
});

export const BundleExhibitLinkSchema = z.object({
  id: z.string().uuid(),
  exhibit_label: z.string(),
  title: z.string(),
  source_type: DocumentSourceTypeSchema,
  anchor_label: z.string(),
  target_title: z.string(),
  note: z.string()
});

export const BundleMapSchema = z.object({
  matter_id: z.string().uuid(),
  matter_title: z.string(),
  matter_reference_code: z.string(),
  forum: z.string(),
  stage: MatterStageSchema,
  matter_status: MatterStatusSchema,
  ingestion: BundleProcessingOverviewSchema,
  chronology: z.array(BundleChronologyItemSchema),
  contradictions: z.array(BundleContradictionSchema),
  clusters: z.array(BundleClusterSchema),
  duplicate_groups: z.array(BundleDuplicateGroupSchema),
  exhibit_links: z.array(BundleExhibitLinkSchema),
  documents: z.array(BundleDocumentSummarySchema)
});

export const UploadDocumentRequestSchema = z.object({
  matterId: z.string().uuid().optional(),
  sourceType: DocumentSourceTypeSchema,
  title: z.string().optional(),
  authorityKind: AuthorityKindSchema.optional(),
  citationText: z.string().optional(),
  court: z.string().optional(),
  forum: z.string().optional(),
  bench: z.string().optional(),
  legalIssue: z.string().optional(),
  sourceUrl: z.string().url().optional(),
  processInBackground: z.boolean().optional(),
  file: z.custom<File>((value) => typeof File !== "undefined" && value instanceof File, {
    message: "Expected a File instance"
  })
});

export const ResearchSearchRequestSchema = z.object({
  matterId: z.string().uuid(),
  query: z.string().min(2),
  filters: z
    .object({
      court: z.string().optional(),
      issue: z.string().optional(),
      authorityKind: AuthorityKindSchema.optional()
    })
    .optional()
});

export const ResearchSearchResultSchema = z.object({
  document_id: z.string().uuid(),
  quote_span_id: z.string().uuid(),
  title: z.string(),
  citation_text: z.string().nullable(),
  authority_kind: AuthorityKindSchema,
  source_type: DocumentSourceTypeSchema,
  court: z.string().nullable(),
  forum: z.string().nullable(),
  bench: z.string().nullable(),
  decision_date: z.string().nullable(),
  legal_issue: z.string().nullable(),
  anchor_label: z.string(),
  paragraph_start: z.number().int(),
  paragraph_end: z.number().int(),
  page_start: z.number().int().nullable(),
  page_end: z.number().int().nullable(),
  quote_text: z.string(),
  quote_checksum: z.string(),
  score: z.number(),
  saved_treatment: AuthorityTreatmentSchema.nullable().optional()
});

export const ResearchSearchResponseSchema = z.object({
  items: z.array(ResearchSearchResultSchema),
  total: z.number().int().nonnegative()
});

export const ResearchSaveRequestSchema = z.object({
  quoteSpanId: z.string().uuid(),
  citationId: z.string().uuid().nullable().optional(),
  treatment: AuthorityTreatmentSchema,
  issueLabel: z.string().min(3).max(255),
  note: z.string().optional()
});

export const ResearchSaveResponseSchema = z.object({
  id: z.string().uuid(),
  matter_id: z.string().uuid(),
  quote_span_id: z.string().uuid(),
  citation_id: z.string().uuid().nullable(),
  treatment: AuthorityTreatmentSchema,
  issue_label: z.string(),
  note: z.string().nullable()
});

export const QuoteLockResponseSchema = z.object({
  quote_span_id: z.string().uuid(),
  anchor_label: z.string(),
  text: z.string(),
  checksum: z.string()
});

export const ResearchMemoResponseSchema = z.object({
  file_name: z.string(),
  content: z.string()
});

export type AuthorityKind = z.infer<typeof AuthorityKindSchema>;
export type AuthorityTreatment = z.infer<typeof AuthorityTreatmentSchema>;
export type BundleCluster = z.infer<typeof BundleClusterSchema>;
export type BundleChronologyItem = z.infer<typeof BundleChronologyItemSchema>;
export type BundleContradiction = z.infer<typeof BundleContradictionSchema>;
export type BundleDocumentSummary = z.infer<typeof BundleDocumentSummarySchema>;
export type BundleDuplicateGroup = z.infer<typeof BundleDuplicateGroupSchema>;
export type BundleDuplicateMember = z.infer<typeof BundleDuplicateMemberSchema>;
export type BundleExhibitLink = z.infer<typeof BundleExhibitLinkSchema>;
export type BundleMap = z.infer<typeof BundleMapSchema>;
export type BundleProcessingOverview = z.infer<typeof BundleProcessingOverviewSchema>;
export type BundleProcessingStage = z.infer<typeof BundleProcessingStageSchema>;
export type DocumentResponse = z.infer<typeof DocumentResponseSchema>;
export type DocumentSourceType = z.infer<typeof DocumentSourceTypeSchema>;
export type EntityType = z.infer<typeof EntityTypeSchema>;
export type LoginRequest = z.infer<typeof LoginRequestSchema>;
export type LoginResponse = z.infer<typeof LoginResponseSchema>;
export type MatterDetail = z.infer<typeof MatterDetailSchema>;
export type MatterSummary = z.infer<typeof MatterSummarySchema>;
export type ProcessingStatus = z.infer<typeof ProcessingStatusSchema>;
export type RelationSeverity = z.infer<typeof RelationSeveritySchema>;
export type ResearchMemoResponse = z.infer<typeof ResearchMemoResponseSchema>;
export type ResearchSaveRequest = z.infer<typeof ResearchSaveRequestSchema>;
export type ResearchSaveResponse = z.infer<typeof ResearchSaveResponseSchema>;
export type ResearchSearchRequest = z.infer<typeof ResearchSearchRequestSchema>;
export type ResearchSearchResponse = z.infer<typeof ResearchSearchResponseSchema>;
export type ResearchSearchResult = z.infer<typeof ResearchSearchResultSchema>;
export type UploadDocumentRequest = z.infer<typeof UploadDocumentRequestSchema>;
