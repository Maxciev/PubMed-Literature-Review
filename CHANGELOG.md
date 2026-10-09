# Changelog

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
