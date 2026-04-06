from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    MEMBER = "member"


class MatterStatus(StrEnum):
    ACTIVE = "active"
    HOLD = "hold"
    CLOSED = "closed"


class MatterStage(StrEnum):
    PRE_FILING = "pre_filing"
    FILING = "filing"
    NOTICE = "notice"
    EVIDENCE = "evidence"
    ARGUMENTS = "arguments"
    ORDERS = "orders"


class DocumentSourceType(StrEnum):
    PUBLIC_LAW = "public_law"
    MY_DOCUMENT = "my_document"
    OPPONENT_DOCUMENT = "opponent_document"
    COURT_DOCUMENT = "court_document"
    WORK_PRODUCT = "work_product"


class ProcessingStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class AuthorityKind(StrEnum):
    CONSTITUTION = "constitution"
    STATUTE = "statute"
    JUDGMENT = "judgment"
    NOTE = "note"
    MATTER_DOCUMENT = "matter_document"


class AuthorityTreatment(StrEnum):
    APPLY = "apply"
    DISTINGUISH = "distinguish"
    ADVERSE = "adverse"
    DRAFT = "draft"


class EntityType(StrEnum):
    PERSON = "person"
    ORGANIZATION = "organization"
    ROLE = "role"
    EXHIBIT = "exhibit"
    ISSUE = "issue"


class RelationType(StrEnum):
    CONTRADICTION = "contradiction"
    DUPLICATE = "duplicate"


class RelationSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DraftDocumentType(StrEnum):
    PETITION = "petition"
    REPLY = "reply"
    WRITTEN_SUBMISSION = "written_submission"
    AFFIDAVIT = "affidavit"
    APPLICATION = "application"
    SYNOPSIS = "synopsis"
    LIST_OF_DATES = "list_of_dates"
    LEGAL_NOTICE = "legal_notice"
    SETTLEMENT_NOTE = "settlement_note"


class DraftStatus(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    EXPORTED = "exported"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalTargetType(StrEnum):
    DRAFT_DOCUMENT = "draft_document"
    STRATEGY_WORKSPACE = "strategy_workspace"


class SourceSystem(StrEnum):
    DISTRICT_ECOURTS = "district_ecourts"
    HIGH_COURT_SERVICES = "high_court_services"
    ECOURTS_JUDGMENTS = "ecourts_judgments"
    NJDG = "njdg"
    SUPREME_COURT_INDIA = "supreme_court_india"


class EventType(StrEnum):
    FILING_SUBMITTED = "filing_submitted"
    FILING_DEFECT = "filing_defect"
    FILING_CURED = "filing_cured"
    LISTED = "listed"
    HEARD = "heard"
    ADJOURNED = "adjourned"
    ORDER_UPLOADED = "order_uploaded"
    JUDGMENT_UPLOADED = "judgment_uploaded"
    NOTICE_ISSUED = "notice_issued"
    SERVICE_COMPLETED = "service_completed"
    CAVEAT_FOUND = "caveat_found"
    OFFICE_REPORT_ADDED = "office_report_added"
    COMPLIANCE_DUE = "compliance_due"
    COMPLIANCE_FILED = "compliance_filed"
    DISPOSED = "disposed"
    RESTORED = "restored"
    TRANSFERRED = "transferred"


class ArtifactKind(StrEnum):
    CASE_HISTORY = "case_history"
    CAUSE_LIST = "cause_list"
    ORDER = "order"
    JUDGMENT = "judgment"
    FILING = "filing"
    REGISTRY_NOTE = "registry_note"
    SNAPSHOT_HTML = "snapshot_html"
    SNAPSHOT_PDF = "snapshot_pdf"
    SNAPSHOT_JSON = "snapshot_json"


class FilingSide(StrEnum):
    PETITIONER = "petitioner"
    RESPONDENT = "respondent"
    APPELLANT = "appellant"
    APPELLEE = "appellee"
    APPLICANT = "applicant"
    CAVEATOR = "caveator"
    COURT = "court"
    REGISTRY = "registry"
    UNKNOWN = "unknown"


class PartyRole(StrEnum):
    PETITIONER = "petitioner"
    RESPONDENT = "respondent"
    APPELLANT = "appellant"
    APPELLEE = "appellee"
    APPLICANT = "applicant"
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"
    CAVEATOR = "caveator"
    INTERVENOR = "intervenor"
    COUNSEL = "counsel"
    OTHER = "other"


class VerificationStatus(StrEnum):
    IMPORTED = "imported"
    PARSED = "parsed"
    VERIFIED = "verified"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"


class ConfidenceBand(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ProfileWindow(StrEnum):
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    LAST_180_DAYS = "last_180_days"
    LAST_365_DAYS = "last_365_days"
    ALL_TIME = "all_time"


class JobKind(StrEnum):
    EXTERNAL_CASE_SYNC = "external_case_sync"
    RAW_SNAPSHOT_IMPORT = "raw_snapshot_import"
    ARTIFACT_EXTRACT = "artifact_extract"
    CASE_EVENT_REBUILD = "case_event_rebuild"
    FILING_PARSE = "filing_parse"
    PARTY_RESOLUTION = "party_resolution"
    LITIGANT_MEMORY_REFRESH = "litigant_memory_refresh"
    CASE_MEMORY_REFRESH = "case_memory_refresh"
    JUDGE_PROFILE_REFRESH = "judge_profile_refresh"
    COURT_PROFILE_REFRESH = "court_profile_refresh"
    HYBRID_INDEX_REFRESH = "hybrid_index_refresh"
    HEARING_DELTA_REFRESH = "hearing_delta_refresh"


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RETRYABLE = "retryable"
    CANCELLED = "cancelled"


class JobAttemptStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class HybridEntityKind(StrEnum):
    DOCUMENT = "document"
    COURT_ARTIFACT = "court_artifact"
    CASE_EVENT = "case_event"
    CASE_FILING = "case_filing"
    LITIGANT_MEMORY = "litigant_memory"
    CASE_MEMORY = "case_memory"
    JUDGE_PROFILE = "judge_profile"
    COURT_PROFILE = "court_profile"
