# Product Overview

LegalOS is an India-first litigation operating system for advocates, chambers, senior briefing teams, and DLSA or institutional legal-aid workflows.

The product is not a generic legal chatbot. It is a source-grounded working system for litigation teams that need to research authorities, process matter bundles, draft structured pleadings, analyze weaknesses and contradictions, and prepare bounded strategic options with traceability.

## Current Product Baseline

Phase 0 through Phase 6 are implemented in this repository:

- authenticated matter access via FastAPI JWT login
- matter index and cockpit in Next.js
- document upload, extraction, chunking, and paragraph-level quote spans
- public-law plus matter-document research search
- saved authority handling with treatment labels
- research memo export
- verified quote-lock through stored checksums and exact spans
- bundle map with chronology, contradiction cards, duplicate groups, exhibit links, and cluster summaries
- queued, processing, ready, and failed ingest visibility across bundle documents
- structured draft generation with style packs, annexures, redlines, and unresolved placeholders
- strategy workspace with bounded scenario branches, issue cards, and sequencing guidance
- institutional dashboard with approvals, audit visibility, low-bandwidth mode, and plain-language summaries
- public-court ingestion, canonical dockets, merged chronology, litigant and case memory, judge and court profiles, and hybrid retrieval across public and private records

## Core User Problems

- Research is fragmented across judgments, notes, and uploaded matter files.
- Quote integrity is fragile when teams rely on copied text without span-level provenance.
- Bundle handling is manual, especially for scanned or mixed-format records.
- Drafting is repetitive, but missing facts or unsupported assertions must remain visible.
- Strategy support must be bounded, auditable, and framed as decision support.

## Product Pillars

### Research And Precedent Engine

Natural-language and fielded search across judgments, statutes, notes, and uploaded matters. Results must expose authority strength, citation metadata, relevant paragraphs, and exact quote spans backed by source anchors.

### Document Operating System

Upload and process PDF, DOCX, DOC, RTF, TXT, HTML, images, email exports, and ZIP bundles. Keep document provenance, classify matter context, and support chronology, entity extraction, duplicate detection, exhibit linking, and contradiction mapping.

### Drafting Studio

Generate structured legal documents, not unbounded prose. Surface unresolved facts explicitly, support chamber style packs, annexure scheduling, and redlines, and restrict authority insertion to verified research results.

### Strategy And Arguments

Provide controlled scenario trees, issue cards, and argument sets for attack, defense, oral, written, and hearing preparation. Always label these outputs as decision support, not outcome prediction, and preserve lawful sequencing guardrails.

### Institutional Mode

Support auditability, approval workflows, multilingual/plain-language outputs, low-bandwidth UX, urgency posture, and role-sensitive access control for legal-aid and institutional defense contexts.

### Court Intelligence

Import official public-court artifacts through lawful channels, normalize them into canonical docket records, and expose merged chronology, filing lineage, litigant memory, case memory, connected matters, and descriptive judge/court profiles with visible provenance and freshness.

## Trust Rules

- Every shown proposition needs a source id, citation, and paragraph or page anchor.
- Exact quotes may only come from stored spans.
- “Hide information” requests must be implemented as lawful sequencing guidance with disclosure safeguards.
- Institutional mode must surface more auditability and approval context than private mode.
- No hard dependency on proprietary model vendors in the domain model.
- Public-court connectors must not attempt captcha bypass, covert scraping, or unbounded agent behavior.
- Markdown memory files are generated views, not the source of truth.

## Demo Corpus

The current demo corpus uses verified Constitution excerpts for Articles 14, 21, 22(1)-(2), 32(1), and 39A sourced from the Legislative Department’s published Constitution PDF, plus a synthetic detention-and-legal-aid matter bundle designed to surface chronology, contradiction, duplicate, exhibit-link, drafting, strategy, and institutional workflows. This keeps the baseline demo narrow, traceable, and free of fabricated citations or verbatim quotes while still exercising the full current product surface.
