import { z } from "zod";

export const DraftDocumentTypeSchema = z.enum([
  "petition",
  "reply",
  "written_submission",
  "affidavit",
  "application",
  "synopsis",
  "list_of_dates",
  "legal_notice",
  "settlement_note"
]);

export const DraftStatusSchema = z.enum(["draft", "review", "exported"]);
export const ApprovalStatusSchema = z.enum(["pending", "approved", "rejected"]);
export const ApprovalTargetTypeSchema = z.enum(["draft_document", "strategy_workspace"]);

export const StylePackCreateRequestSchema = z.object({
  name: z.string().min(3).max(255),
  description: z.string().optional().nullable(),
  tone: z.string().min(3).max(255).default("formal and restrained"),
  openingPhrase: z
    .string()
    .min(3)
    .max(255)
    .default("It is most respectfully submitted"),
  prayerStyle: z
    .string()
    .min(3)
    .max(255)
    .default("It is therefore most respectfully prayed"),
  citationStyle: z.string().min(3).max(255).default("anchor-plus-checksum"),
  voiceNotes: z.string().optional().nullable(),
  sourceDocumentIds: z.array(z.string().uuid()).optional().default([])
});

export const StylePackSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  description: z.string().nullable(),
  tone: z.string(),
  opening_phrase: z.string(),
  prayer_style: z.string(),
  citation_style: z.string(),
  voice_notes: z.string().nullable(),
  sample_document_titles: z.string().nullable(),
  created_at: z.string()
});

export const DraftGenerateRequestSchema = z.object({
  documentType: DraftDocumentTypeSchema,
  title: z.string().optional().nullable(),
  stylePackId: z.string().uuid().optional().nullable(),
  annexureDocumentIds: z.array(z.string().uuid()).optional().default([]),
  includeSavedAuthorities: z.boolean().optional().default(true),
  includeBundleIntelligence: z.boolean().optional().default(true)
});

export const DraftSectionSchema = z.object({
  id: z.string().uuid(),
  section_key: z.string(),
  label: z.string(),
  body_text: z.string(),
  order_index: z.number().int(),
  is_required: z.boolean(),
  placeholder_count: z.number().int().nonnegative()
});

export const DraftAuthorityUseSchema = z.object({
  id: z.string().uuid(),
  saved_authority_id: z.string().uuid(),
  issue_label: z.string(),
  treatment: z.string(),
  section_key: z.string(),
  anchor_label: z.string(),
  quote_text: z.string(),
  checksum: z.string(),
  citation_text: z.string().nullable()
});

export const DraftAnnexureSchema = z.object({
  id: z.string().uuid(),
  label: z.string(),
  title: z.string(),
  note: z.string().nullable(),
  source_document_id: z.string().uuid().nullable()
});

export const DraftDocumentSchema = z.object({
  id: z.string().uuid(),
  matter_id: z.string().uuid(),
  title: z.string(),
  document_type: DraftDocumentTypeSchema,
  status: DraftStatusSchema,
  version_number: z.number().int().positive(),
  summary: z.string().nullable(),
  export_file_name: z.string().nullable(),
  style_pack: StylePackSchema.nullable(),
  sections: z.array(DraftSectionSchema),
  authorities_used: z.array(DraftAuthorityUseSchema),
  annexures: z.array(DraftAnnexureSchema),
  unresolved_placeholders: z.array(z.string()),
  created_at: z.string()
});

export const DraftExportResponseSchema = z.object({
  file_name: z.string(),
  content: z.string()
});

export const DraftRedlineSectionSchema = z.object({
  section_key: z.string(),
  label: z.string(),
  diff: z.string()
});

export const DraftRedlineSchema = z.object({
  current_draft_id: z.string().uuid(),
  previous_draft_id: z.string().uuid(),
  sections: z.array(DraftRedlineSectionSchema)
});

export const StrategyLineSchema = z.object({
  label: z.string(),
  summary: z.string(),
  rationale: z.string()
});

export const StrategyIssueSchema = z.object({
  issue_label: z.string(),
  attack: z.string(),
  defense: z.string(),
  oral_short: z.string(),
  oral_detailed: z.string(),
  written_note: z.string(),
  bench_questions: z.array(z.string()),
  likely_opponent_attacks: z.array(z.string()),
  rebuttal_cards: z.array(z.string()),
  authority_anchors: z.array(z.string())
});

export const StrategyScenarioBranchSchema = z.object({
  id: z.string(),
  label: z.string(),
  path: z.string(),
  next_step: z.string()
});

export const StrategyWorkspaceSchema = z.object({
  matter_id: z.string().uuid(),
  objective: z.string(),
  decision_support_label: z.string(),
  best_line: StrategyLineSchema,
  fallback_line: StrategyLineSchema,
  risk_line: StrategyLineSchema,
  issues: z.array(StrategyIssueSchema),
  scenario_tree: z.array(StrategyScenarioBranchSchema)
});

export const SequencingItemRequestSchema = z.object({
  label: z.string().min(2).max(255),
  detail: z.string().min(3).max(2000)
});

export const SequencingConsoleRequestSchema = z.object({
  items: z.array(SequencingItemRequestSchema).min(1).max(25)
});

export const SequencingRecommendationSchema = z.object({
  label: z.string(),
  bucket: z.string(),
  recommendation: z.string(),
  reason: z.string(),
  mandatory_warning: z.boolean()
});

export const SequencingConsoleResponseSchema = z.object({
  decision_support_label: z.string(),
  global_warning: z.string(),
  items: z.array(SequencingRecommendationSchema)
});

export const ApprovalCreateRequestSchema = z.object({
  targetType: ApprovalTargetTypeSchema,
  targetId: z.string().uuid(),
  note: z.string().optional().nullable()
});

export const ApprovalReviewRequestSchema = z.object({
  status: ApprovalStatusSchema,
  reviewNote: z.string().optional().nullable()
});

export const ApprovalSchema = z.object({
  id: z.string().uuid(),
  matter_id: z.string().uuid(),
  target_type: ApprovalTargetTypeSchema,
  target_id: z.string(),
  status: ApprovalStatusSchema,
  note: z.string().nullable(),
  review_note: z.string().nullable(),
  requested_by_user_id: z.string().uuid(),
  reviewed_by_user_id: z.string().uuid().nullable(),
  reviewed_at: z.string().nullable(),
  created_at: z.string()
});

export const AuditEventSchema = z.object({
  id: z.string().uuid(),
  action: z.string(),
  entity_type: z.string(),
  entity_id: z.string(),
  detail: z.string().nullable(),
  created_at: z.string()
});

export const InstitutionalDashboardSchema = z.object({
  matter_id: z.string().uuid(),
  urgency_status: z.string(),
  days_to_hearing: z.number().int().nullable(),
  pending_approvals: z.number().int().nonnegative(),
  latest_draft_id: z.string().uuid().nullable(),
  approvals: z.array(ApprovalSchema),
  recent_audit_events: z.array(AuditEventSchema),
  plain_language_en: z.string(),
  plain_language_hi: z.string(),
  low_bandwidth_brief: z.array(z.string()),
  decision_support_label: z.string()
});

export type Approval = z.infer<typeof ApprovalSchema>;
export type ApprovalCreateRequest = z.infer<typeof ApprovalCreateRequestSchema>;
export type ApprovalReviewRequest = z.infer<typeof ApprovalReviewRequestSchema>;
export type ApprovalStatus = z.infer<typeof ApprovalStatusSchema>;
export type ApprovalTargetType = z.infer<typeof ApprovalTargetTypeSchema>;
export type AuditEvent = z.infer<typeof AuditEventSchema>;
export type DraftAnnexure = z.infer<typeof DraftAnnexureSchema>;
export type DraftAuthorityUse = z.infer<typeof DraftAuthorityUseSchema>;
export type DraftDocument = z.infer<typeof DraftDocumentSchema>;
export type DraftDocumentType = z.infer<typeof DraftDocumentTypeSchema>;
export type DraftExportResponse = z.infer<typeof DraftExportResponseSchema>;
export type DraftGenerateRequest = z.infer<typeof DraftGenerateRequestSchema>;
export type DraftRedline = z.infer<typeof DraftRedlineSchema>;
export type DraftStatus = z.infer<typeof DraftStatusSchema>;
export type DraftSection = z.infer<typeof DraftSectionSchema>;
export type InstitutionalDashboard = z.infer<typeof InstitutionalDashboardSchema>;
export type SequencingConsoleRequest = z.infer<typeof SequencingConsoleRequestSchema>;
export type SequencingConsoleResponse = z.infer<typeof SequencingConsoleResponseSchema>;
export type StrategyWorkspace = z.infer<typeof StrategyWorkspaceSchema>;
export type StylePack = z.infer<typeof StylePackSchema>;
export type StylePackCreateRequest = z.infer<typeof StylePackCreateRequestSchema>;
