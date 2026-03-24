from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class StrategyLineResponse(BaseModel):
    label: str
    summary: str
    rationale: str


class StrategyIssueResponse(BaseModel):
    issue_label: str
    attack: str
    defense: str
    oral_short: str
    oral_detailed: str
    written_note: str
    bench_questions: list[str]
    likely_opponent_attacks: list[str]
    rebuttal_cards: list[str]
    authority_anchors: list[str]


class StrategyScenarioBranchResponse(BaseModel):
    id: str
    label: str
    path: str
    next_step: str


class StrategyWorkspaceResponse(BaseModel):
    matter_id: UUID
    objective: str
    decision_support_label: str
    best_line: StrategyLineResponse
    fallback_line: StrategyLineResponse
    risk_line: StrategyLineResponse
    issues: list[StrategyIssueResponse]
    scenario_tree: list[StrategyScenarioBranchResponse]


class SequencingItemRequest(BaseModel):
    label: str = Field(min_length=2, max_length=255)
    detail: str = Field(min_length=3, max_length=2000)


class SequencingConsoleRequest(BaseModel):
    items: list[SequencingItemRequest] = Field(min_length=1, max_length=25)


class SequencingRecommendationResponse(BaseModel):
    label: str
    bucket: str
    recommendation: str
    reason: str
    mandatory_warning: bool


class SequencingConsoleResponse(BaseModel):
    decision_support_label: str
    global_warning: str
    items: list[SequencingRecommendationResponse]
