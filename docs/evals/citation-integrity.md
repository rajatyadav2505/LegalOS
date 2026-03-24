# Citation Integrity Eval

## Goal

Ensure that every authority shown in the research UI is backed by stored citation metadata and a quote span anchor.

## Phase 1 Checks

- Seeded Constitution excerpts preserve their citation text and source URL.
- Search results expose `citation_text`, `anchor_label`, and `quote_checksum`.
- Saved authorities preserve the source `quote_span_id`.
- Memo export includes the anchor and checksum for every saved authority.
- Drafting and strategy flows consume authorities only through saved research records, not freehand citation text.
