# Changelog

## 1.2.0 — 2026-11-12

### Added
- **Works without the PubMed connector where code execution can reach NCBI** (e.g. Claude Code on your
  machine; not the claude.ai sandbox, which refused NCBI with HTTP 403 in testing). The bundled
  `scripts/pubmed.py` queries PubMed through NCBI E-utilities (search, metadata, PMID / PMCID / DOI conversion), Python standard library only. The skill
  uses the connector when present and the script otherwise. Compared with the connector on five
  hand-surgery queries: same counts and PMIDs, same DOIs, titles, journals, authors and publication types
  on ten records.
- The script returns the print year and the online-first date separately, which feeds the year check of
  Phase 5.
- Query-craft rules: check the query translation for gene-symbol hijacks ("cast" → POLR1G); check that date
  filters appear in the translation; dedupe by PMID because relevance order is not stable.
- Connector `RATE_LIMIT_EXCEEDED`: wait `retryAfter` and retry, not counted as a failure.

### Fixed
- **Searches are sorted by relevance.** Without `sort`, the connector returns the most recent records first;
  the skill did not set it, so the top 20 of most searches were the newest papers, not the most relevant.
- Removed the claims that date filters never work and that the endpoint has no pagination offset: both
  work on the connector and the script (tested on one query each). The skill now checks the translation
  instead of assuming the filter failed.
- README: skill upload moved to `Customize` → `Skills` on claude.ai.
- When no PubMed access works, the skill stops before Phase 1 and recommends reconnecting the connector and
  starting a new conversation (tools load at conversation start).

## 1.1.0 — 2026-10-09

### Fixed
- **Self-contained skill.** The document template and the docx requirements used to live in
  `references/document-structure.md`. When the skill was re-saved from SKILL.md alone, that file was lost
  and the skill pointed to a file that no longer existed. Everything is now in `SKILL.md`.
- Questions are asked with the multiple-choice tool of the current surface (`AskUserQuestion` in Claude
  Code / Cowork, `ask_user_input_v0` on claude.ai), and files are delivered with `SendUserFile` or
  `present_files` depending on the surface.
- `docx` is required directly; `npm install docx` only runs if that fails.

### Added
- **Output language question** (English · French · bilingual). When the language is already stated in the
  request, it is confirmed in the checkpoint instead of being asked again.
- **Automatic reference verification (Phase 5)**: every cited PMID is checked against the PubMed results
  of the session, along with relevance, audit counts, numerical claims and online-first vs print years.
- Build pattern that generates the bibliography from the citations actually used, so the two cannot
  diverge.
- Optional metadata extraction through subagents to save context on large searches.
- Query-craft rules: avoid over-broad anatomical terms; recover a missing foundational paper with an
  `[Author]` search.
- Audit log: counts of relevant papers and true clinical RCTs (cadaver studies tagged "Randomized
  Controlled Trial" by PubMed are excluded).
- Render check of the .docx (PDF conversion, first, middle and last pages).

## 1.0.0 — 2026-07-14

- Initial release.
