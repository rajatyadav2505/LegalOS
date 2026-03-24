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
