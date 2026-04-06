import {
  ApprovalCreateRequestSchema,
  ApprovalReviewRequestSchema,
  ApprovalSchema,
  ApiErrorSchema,
  BundleMapSchema,
  CasePartySummarySchema,
  ConnectedMatterSchema,
  DraftDocumentSchema,
  DraftExportResponseSchema,
  DraftGenerateRequestSchema,
  DraftRedlineSchema,
  DocumentResponseSchema,
  ExternalCaseLinkRequestSchema,
  ExternalCaseSummarySchema,
  FilingLineageItemSchema,
  HearingDeltaSchema,
  HybridSearchSchema,
  InstitutionalDashboardSchema,
  JobSchema,
  LoginRequestSchema,
  LoginResponseSchema,
  MatterDetailSchema,
  MatterExternalCaseListSchema,
  MemorySnapshotSchema,
  MergedChronologyItemSchema,
  MatterListSchema,
  ProfileSnapshotSchema,
  ResearchMemoResponseSchema,
  ResearchSaveRequestSchema,
  ResearchSaveResponseSchema,
  ResearchSearchRequestSchema,
  ResearchSearchResponseSchema,
  SequencingConsoleRequestSchema,
  SequencingConsoleResponseSchema,
  StrategyWorkspaceSchema,
  StylePackCreateRequestSchema,
  StylePackSchema,
  UploadDocumentRequestSchema,
  type Approval,
  type ApprovalCreateRequest,
  type ApprovalReviewRequest,
  type BundleMap,
  type CasePartySummary,
  type ConnectedMatter,
  type DraftDocument,
  type DraftExportResponse,
  type DraftGenerateRequest,
  type DraftRedline,
  type DocumentResponse,
  type ExternalCaseLinkRequest,
  type ExternalCaseSummary,
  type FilingLineageItem,
  type HearingDelta,
  type HybridSearch,
  type InstitutionalDashboard,
  type Job,
  type LoginRequest,
  type LoginResponse,
  type MatterDetail,
  type MatterExternalCaseList,
  type MemorySnapshot,
  type MergedChronologyItem,
  type MatterSummary,
  type ProfileSnapshot,
  type ResearchMemoResponse,
  type ResearchSaveRequest,
  type ResearchSaveResponse,
  type ResearchSearchRequest,
  type ResearchSearchResponse,
  type SequencingConsoleRequest,
  type SequencingConsoleResponse,
  type StrategyWorkspace,
  type StylePack,
  type StylePackCreateRequest,
  type UploadDocumentRequest
} from "@legalos/contracts";
import { getBrowserAuthToken } from "@/lib/auth";
import { ApiClientError } from "./errors";

type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; status: number; message: string };

function resolveBaseUrl() {
  if (typeof window === "undefined") {
    return process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
  }

  return process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
}

export class LegalOsApiClient {
  constructor(
    private readonly baseUrl = resolveBaseUrl(),
    private readonly fetchImpl: typeof fetch = fetch,
    private readonly accessToken: string | null = null
  ) {}

  private url(path: string) {
    return new URL(path, this.baseUrl).toString();
  }

  private async request<T>(
    path: string,
    parser: { parse(data: unknown): T },
    init?: RequestInit
  ): Promise<ApiResult<T>> {
    const token = this.accessToken ?? getBrowserAuthToken();
    const headers = new Headers(init?.headers ?? {});
    headers.set("Accept", "application/json");
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    try {
      // Native browser fetch can throw "Illegal invocation" when invoked off its global receiver.
      const response = await this.fetchImpl.call(globalThis, this.url(path), {
        ...init,
        headers
      });

      const text = await response.text();
      const payload = text ? JSON.parse(text) : null;

      if (!response.ok) {
        const error = ApiErrorSchema.safeParse(payload);
        return {
          ok: false,
          status: response.status,
          message:
            error.success
              ? error.data.detail ?? error.data.message ?? response.statusText
              : response.statusText
        };
      }

      return { ok: true, data: parser.parse(payload) };
    } catch (cause) {
      if (cause instanceof SyntaxError) {
        throw new ApiClientError("The API returned invalid JSON.", 502);
      }
      throw cause;
    }
  }

  async login(payload: LoginRequest): Promise<LoginResponse> {
    const body = LoginRequestSchema.parse(payload);
    const result = await this.request("/api/v1/auth/login", LoginResponseSchema, {
      method: "POST",
      body: JSON.stringify(body),
      headers: {
        "Content-Type": "application/json"
      }
    });

    if (!result.ok) {
      throw new ApiClientError(result.message, result.status);
    }

    return result.data;
  }

  async getMatters(): Promise<ApiResult<MatterSummary[]>> {
    return this.request("/api/v1/matters", MatterListSchema);
  }

  async getMatter(matterId: string): Promise<ApiResult<MatterDetail>> {
    return this.request(`/api/v1/matters/${matterId}`, MatterDetailSchema);
  }

  async getMatterExternalCases(matterId: string): Promise<ApiResult<MatterExternalCaseList>> {
    return this.request(
      `/api/v1/matters/${matterId}/external-cases`,
      MatterExternalCaseListSchema
    );
  }

  async getExternalCaseParties(externalCaseId: string): Promise<ApiResult<CasePartySummary[]>> {
    return this.request(`/api/v1/external-cases/${externalCaseId}/parties`, {
      parse: (data: unknown) => CasePartySummarySchema.array().parse(data)
    });
  }

  async linkExternalCase(
    matterId: string,
    payload: ExternalCaseLinkRequest
  ): Promise<ExternalCaseSummary> {
    const body = ExternalCaseLinkRequestSchema.parse(payload);
    const result = await this.request(
      `/api/v1/matters/${matterId}/external-cases/link`,
      ExternalCaseSummarySchema,
      {
        method: "POST",
        body: JSON.stringify(body),
        headers: {
          "Content-Type": "application/json"
        }
      }
    );

    if (!result.ok) {
      throw new ApiClientError(result.message, result.status);
    }

    return result.data;
  }

  async importExternalCaseArtifact(
    matterId: string,
    payload: {
      sourceSystem: ExternalCaseLinkRequest["source_system"];
      artifactKind: string;
      file: File;
      sourceUrl?: string | null;
      observedAt?: string | null;
      externalCaseId?: string | null;
    }
  ): Promise<ExternalCaseSummary> {
    const formData = new FormData();
    formData.set("source_system", payload.sourceSystem);
    formData.set("artifact_kind", payload.artifactKind);
    if (payload.sourceUrl) {
      formData.set("source_url", payload.sourceUrl);
    }
    if (payload.observedAt) {
      formData.set("observed_at", payload.observedAt);
    }
    if (payload.externalCaseId) {
      formData.set("external_case_id", payload.externalCaseId);
    }
    formData.set("file", payload.file);

    const result = await this.request(
      `/api/v1/matters/${matterId}/external-cases/import`,
      ExternalCaseSummarySchema,
      {
        method: "POST",
        body: formData
      }
    );

    if (!result.ok) {
      throw new ApiClientError(result.message, result.status);
    }

    return result.data;
  }

  async syncExternalCase(matterId: string, externalCaseId: string): Promise<Job> {
    const result = await this.request(
      `/api/v1/external-cases/${externalCaseId}/sync?matter_id=${matterId}`,
      JobSchema,
      {
        method: "POST"
      }
    );

    if (!result.ok) {
      throw new ApiClientError(result.message, result.status);
    }

    return result.data;
  }

  async getMergedChronology(matterId: string): Promise<ApiResult<MergedChronologyItem[]>> {
    return this.request(`/api/v1/matters/${matterId}/chronology`, {
      parse: (data: unknown) => MergedChronologyItemSchema.array().parse(data)
    });
  }

  async getHearingDelta(matterId: string): Promise<ApiResult<HearingDelta>> {
    return this.request(`/api/v1/matters/${matterId}/hearing-delta`, HearingDeltaSchema);
  }

  async getFilingLineage(matterId: string): Promise<ApiResult<FilingLineageItem[]>> {
    return this.request(`/api/v1/matters/${matterId}/filing-lineage`, {
      parse: (data: unknown) => FilingLineageItemSchema.array().parse(data)
    });
  }

  async getPartyMemory(partyId: string): Promise<ApiResult<MemorySnapshot>> {
    return this.request(`/api/v1/parties/${partyId}/memory`, MemorySnapshotSchema);
  }

  async refreshPartyMemory(partyId: string): Promise<Job> {
    const result = await this.request(`/api/v1/parties/${partyId}/memory/refresh`, JobSchema, {
      method: "POST"
    });

    if (!result.ok) {
      throw new ApiClientError(result.message, result.status);
    }

    return result.data;
  }

  async getCaseMemory(externalCaseId: string): Promise<ApiResult<MemorySnapshot>> {
    return this.request(`/api/v1/external-cases/${externalCaseId}/memory`, MemorySnapshotSchema);
  }

  async refreshCaseMemory(
    externalCaseId: string,
    matterId?: string | null
  ): Promise<Job> {
    const query = matterId ? `?matter_id=${matterId}` : "";
    const result = await this.request(
      `/api/v1/external-cases/${externalCaseId}/memory/refresh${query}`,
      JobSchema,
      {
        method: "POST"
      }
    );

    if (!result.ok) {
      throw new ApiClientError(result.message, result.status);
    }

    return result.data;
  }

  async getJudgeProfile(judgeId: string): Promise<ApiResult<ProfileSnapshot>> {
    return this.request(`/api/v1/judges/${judgeId}/profile`, ProfileSnapshotSchema);
  }

  async refreshJudgeProfile(judgeId: string): Promise<Job> {
    const result = await this.request(`/api/v1/judges/${judgeId}/profile/refresh`, JobSchema, {
      method: "POST"
    });

    if (!result.ok) {
      throw new ApiClientError(result.message, result.status);
    }

    return result.data;
  }

  async getCourtProfile(courtId: string): Promise<ApiResult<ProfileSnapshot>> {
    return this.request(`/api/v1/courts/${courtId}/profile`, ProfileSnapshotSchema);
  }

  async refreshCourtProfile(courtId: string): Promise<Job> {
    const result = await this.request(`/api/v1/courts/${courtId}/profile/refresh`, JobSchema, {
      method: "POST"
    });

    if (!result.ok) {
      throw new ApiClientError(result.message, result.status);
    }

    return result.data;
  }

  async searchHybrid(
    query: string,
    options?: { matterId?: string | null; limit?: number }
  ): Promise<ApiResult<HybridSearch>> {
    const params = new URLSearchParams({ q: query });
    if (options?.matterId) {
      params.set("matter_id", options.matterId);
    }
    if (options?.limit) {
      params.set("limit", String(options.limit));
    }
    return this.request(`/api/v1/search/hybrid?${params.toString()}`, HybridSearchSchema);
  }

  async getConnectedMatters(
    options?: { matterId?: string | null; externalCaseId?: string | null }
  ): Promise<ApiResult<ConnectedMatter[]>> {
    const params = new URLSearchParams();
    if (options?.matterId) {
      params.set("matter_id", options.matterId);
    }
    if (options?.externalCaseId) {
      params.set("external_case_id", options.externalCaseId);
    }
    const query = params.toString();
    return this.request(`/api/v1/search/connected-matters${query ? `?${query}` : ""}`, {
      parse: (data: unknown) => ConnectedMatterSchema.array().parse(data)
    });
  }

  async getBundleMap(matterId: string): Promise<ApiResult<BundleMap>> {
    return this.request(`/api/v1/matters/${matterId}/bundle`, BundleMapSchema);
  }

  async getStylePacks(): Promise<ApiResult<StylePack[]>> {
    return this.request("/api/v1/drafting/style-packs", {
      parse: (data: unknown) => StylePackSchema.array().parse(data)
    });
  }

  async createStylePack(payload: StylePackCreateRequest): Promise<StylePack> {
    const body = StylePackCreateRequestSchema.parse(payload);
    const result = await this.request("/api/v1/drafting/style-packs", StylePackSchema, {
      method: "POST",
      body: JSON.stringify({
        name: body.name,
        description: body.description ?? null,
        tone: body.tone,
        opening_phrase: body.openingPhrase,
        prayer_style: body.prayerStyle,
        citation_style: body.citationStyle,
        voice_notes: body.voiceNotes ?? null,
        source_document_ids: body.sourceDocumentIds
      }),
      headers: {
        "Content-Type": "application/json"
      }
    });

    if (!result.ok) {
      throw new ApiClientError(result.message, result.status);
    }

    return result.data;
  }

  async listDrafts(matterId: string): Promise<ApiResult<DraftDocument[]>> {
    return this.request(`/api/v1/drafting/matters/${matterId}/documents`, {
      parse: (data: unknown) => DraftDocumentSchema.array().parse(data)
    });
  }

  async generateDraft(matterId: string, payload: DraftGenerateRequest): Promise<DraftDocument> {
    const body = DraftGenerateRequestSchema.parse(payload);
    const result = await this.request(
      `/api/v1/drafting/matters/${matterId}/documents/generate`,
      DraftDocumentSchema,
      {
        method: "POST",
        body: JSON.stringify({
          document_type: body.documentType,
          title: body.title ?? null,
          style_pack_id: body.stylePackId ?? null,
          annexure_document_ids: body.annexureDocumentIds,
          include_saved_authorities: body.includeSavedAuthorities,
          include_bundle_intelligence: body.includeBundleIntelligence
        }),
        headers: {
          "Content-Type": "application/json"
        }
      }
    );

    if (!result.ok) {
      throw new ApiClientError(result.message, result.status);
    }

    return result.data;
  }

  async getDraft(draftId: string): Promise<ApiResult<DraftDocument>> {
    return this.request(`/api/v1/drafting/documents/${draftId}`, DraftDocumentSchema);
  }

  async exportDraft(draftId: string): Promise<DraftExportResponse> {
    const result = await this.request(
      `/api/v1/drafting/documents/${draftId}/export`,
      DraftExportResponseSchema
    );

    if (!result.ok) {
      throw new ApiClientError(result.message, result.status);
    }

    return result.data;
  }

  async getDraftRedline(
    draftId: string,
    previousVersionId?: string | null
  ): Promise<DraftRedline> {
    const query = previousVersionId ? `?previous_version_id=${previousVersionId}` : "";
    const result = await this.request(
      `/api/v1/drafting/documents/${draftId}/redline${query}`,
      DraftRedlineSchema
    );

    if (!result.ok) {
      throw new ApiClientError(result.message, result.status);
    }

    return result.data;
  }

  async getStrategyWorkspace(matterId: string): Promise<ApiResult<StrategyWorkspace>> {
    return this.request(`/api/v1/strategy/matters/${matterId}/workspace`, StrategyWorkspaceSchema);
  }

  async reviewSequencing(
    matterId: string,
    payload: SequencingConsoleRequest
  ): Promise<SequencingConsoleResponse> {
    const body = SequencingConsoleRequestSchema.parse(payload);
    const result = await this.request(
      `/api/v1/strategy/matters/${matterId}/sequencing-console`,
      SequencingConsoleResponseSchema,
      {
        method: "POST",
        body: JSON.stringify({
          items: body.items
        }),
        headers: {
          "Content-Type": "application/json"
        }
      }
    );

    if (!result.ok) {
      throw new ApiClientError(result.message, result.status);
    }

    return result.data;
  }

  async getInstitutionalDashboard(matterId: string): Promise<ApiResult<InstitutionalDashboard>> {
    return this.request(
      `/api/v1/institutional/matters/${matterId}/dashboard`,
      InstitutionalDashboardSchema
    );
  }

  async requestApproval(matterId: string, payload: ApprovalCreateRequest): Promise<Approval> {
    const body = ApprovalCreateRequestSchema.parse(payload);
    const result = await this.request(
      `/api/v1/institutional/matters/${matterId}/approvals`,
      ApprovalSchema,
      {
        method: "POST",
        body: JSON.stringify({
          target_type: body.targetType,
          target_id: body.targetId,
          note: body.note ?? null
        }),
        headers: {
          "Content-Type": "application/json"
        }
      }
    );

    if (!result.ok) {
      throw new ApiClientError(result.message, result.status);
    }

    return result.data;
  }

  async reviewApproval(approvalId: string, payload: ApprovalReviewRequest): Promise<Approval> {
    const body = ApprovalReviewRequestSchema.parse(payload);
    const result = await this.request(
      `/api/v1/institutional/approvals/${approvalId}/review`,
      ApprovalSchema,
      {
        method: "POST",
        body: JSON.stringify({
          status: body.status,
          review_note: body.reviewNote ?? null
        }),
        headers: {
          "Content-Type": "application/json"
        }
      }
    );

    if (!result.ok) {
      throw new ApiClientError(result.message, result.status);
    }

    return result.data;
  }

  async searchAuthorities(payload: ResearchSearchRequest): Promise<ResearchSearchResponse> {
    const body = ResearchSearchRequestSchema.parse(payload);
    const params = new URLSearchParams({
      matter_id: body.matterId,
      q: body.query
    });
    if (body.filters?.court) {
      params.set("court", body.filters.court);
    }
    if (body.filters?.issue) {
      params.set("issue", body.filters.issue);
    }
    if (body.filters?.authorityKind) {
      params.set("authority_kind", body.filters.authorityKind);
    }

    const result = await this.request(
      `/api/v1/research/search?${params.toString()}`,
      ResearchSearchResponseSchema
    );

    if (!result.ok) {
      throw new ApiClientError(result.message, result.status);
    }

    return result.data;
  }

  async saveResearchSelection(
    matterId: string,
    payload: ResearchSaveRequest
  ): Promise<ResearchSaveResponse> {
    const body = ResearchSaveRequestSchema.parse(payload);
    const result = await this.request(
      `/api/v1/research/matters/${matterId}/saved-authorities`,
      ResearchSaveResponseSchema,
      {
        method: "POST",
        body: JSON.stringify({
          quote_span_id: body.quoteSpanId,
          citation_id: body.citationId ?? null,
          treatment: body.treatment,
          issue_label: body.issueLabel,
          note: body.note ?? null
        }),
        headers: {
          "Content-Type": "application/json"
        }
      }
    );

    if (!result.ok) {
      throw new ApiClientError(result.message, result.status);
    }

    return result.data;
  }

  async exportResearchMemo(matterId: string): Promise<ResearchMemoResponse> {
    const result = await this.request(
      `/api/v1/research/matters/${matterId}/export`,
      ResearchMemoResponseSchema
    );

    if (!result.ok) {
      throw new ApiClientError(result.message, result.status);
    }

    return result.data;
  }

  async uploadMatterDocument(payload: UploadDocumentRequest): Promise<DocumentResponse> {
    const body = UploadDocumentRequestSchema.parse(payload);
    const formData = new FormData();
    if (body.matterId) {
      formData.set("matter_id", body.matterId);
    }
    formData.set("source_type", body.sourceType);
    formData.set("title", body.title ?? body.file.name);
    formData.set("authority_kind", body.authorityKind ?? "matter_document");
    if (body.citationText) {
      formData.set("citation_text", body.citationText);
    }
    if (body.court) {
      formData.set("court", body.court);
    }
    if (body.forum) {
      formData.set("forum", body.forum);
    }
    if (body.bench) {
      formData.set("bench", body.bench);
    }
    if (body.legalIssue) {
      formData.set("legal_issue", body.legalIssue);
    }
    if (body.sourceUrl) {
      formData.set("source_url", body.sourceUrl);
    }
    if (body.processInBackground !== undefined) {
      formData.set("process_in_background", String(body.processInBackground));
    }
    formData.set("file", body.file);

    const result = await this.request("/api/v1/documents/upload", DocumentResponseSchema, {
      method: "POST",
      body: formData
    });

    if (!result.ok) {
      throw new ApiClientError(result.message, result.status);
    }

    return result.data;
  }
}

export function createBrowserApiClient(accessToken?: string | null) {
  return new LegalOsApiClient(resolveBaseUrl(), fetch, accessToken ?? null);
}
