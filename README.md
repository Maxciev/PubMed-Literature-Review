# PubMed Literature Review

A [Claude](https://claude.ai) skill that turns a research question into a structured, PICO-framed literature review — searched on PubMed, synthesized into a formatted Word document with clickable DOI and PubMed links.

Built for clinicians and researchers who need depth and strategy, not a list of hits.

## What it does

- Reframes your topic into a **PICO** question and builds an explicit search strategy
- Runs **iterative PubMed searches** (MeSH + free-text), refining across rounds
- Tracks **recurring authors and groups** — surfaces who owns the field
- Detects **saturation** — tells you when new searches stop yielding new evidence
- Flags **evidence gaps** worth a real systematic review
- Outputs a **.docx research guide** with a synthesis, an evidence table, and clickable DOI / PubMed links

## Requirements

- Claude with skills support (Claude Desktop or claude.ai)
- The **PubMed connector enabled** in your Claude settings — the skill will not work without it
  - `Settings` → `Connectors` → enable **PubMed**

## Installation

1. Download [`pubmed-literature-review.skill`](https://github.com/Maxciev/PubMed-Literature-Review/raw/main/pubmed-literature-review.skill) — always the current version (see [`CHANGELOG.md`](CHANGELOG.md))
2. In Claude: `Settings` → `Capabilities` → `Skills` → **Upload skill**
3. Select the `.skill` file

## Usage

Invoke it explicitly:

```
/pubmed-literature-review
```

Or just describe what you need — the skill triggers on natural phrasing:

```
I'm writing a paper on scaphoid nonunion — help me map the literature.
```

Claude runs a first reconnaissance search, proposes a PICO breakdown into five sub-areas, then asks you to confirm the search depth (5, 10 or 20 searches), the sub-areas and the output language (English, French or bilingual). It then runs the searches, verifies every cited reference against the PubMed results of the session, and delivers the .docx.

## Example output

See [`examples/`](examples/) for a full generated review.

## What it is not

- **Not a PRISMA systematic review.** No dual screening, no risk-of-bias assessment, no meta-analysis. It is an exploratory evidence map — use it to decide *whether* a systematic review is warranted, not as a substitute for one.
- **Not a substitute for reading the papers.** The synthesis is generated from abstracts and metadata.
- **Verify every reference before citing it.** LLM-generated citations require checking against the source. This is on you.

## Source

The skill's instructions are in [`pubmed-literature-review/SKILL.md`](pubmed-literature-review/SKILL.md). The `.skill` file is the same folder zipped for upload.

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md).

## Citation

If this skill contributes to published work, cite it — see [`CITATION.cff`](CITATION.cff) or use the "Cite this repository" button in the sidebar.

## Author

**Maxime Cievet-Bonfils** — Hand, wrist & elbow surgeon, Lyon, France
[ORCID: 0000-0001-9736-166X](https://orcid.org/0000-0001-9736-166X)

## License

MIT — see [LICENSE](LICENSE).

## Contributing

Issues and pull requests welcome. If you adapt the skill for another specialty or another index (Embase, Scopus), open an issue — I'm interested.
