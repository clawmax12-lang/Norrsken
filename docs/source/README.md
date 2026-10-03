# PRD source provenance

- Original attachment: **Preflight PRD v1.1.pdf**
- Preserved copy: [Preflight-PRD-v1.1.pdf](Preflight-PRD-v1.1.pdf)
- Length: **20 pages**
- Document version/date: **1.1 · 3 Oct 2026, 12:00**
- Canonical editable specification: [../../PRD.md](../../PRD.md)
- SHA-256 of both the attachment and preserved copy:

```text
4abf6eba6d291f9583ce949ad6f97b58e0b09b46bd7cfe846ff0a8c2da460c34
```

The PDF is unchanged. The initial PRD.md import transcribed all sections 0–18, all 15 functional requirements, acceptance criteria, tables, data-contract examples and caveats. Page breaks and wrapping were removed; tables, headings and JSON were formatted for Markdown.

Editorial additions are explicit: the real repository URL replaces its placeholder, the import notice identifies the canonical document, blank owner cells point to TEAM.md, and the open repository question records the observed private visibility. The header labels the technology attribution as the PRD plan so it is not confused with completed implementation.

TEAM.md, AGENTS.md, CLAUDE.md, README.md and the PR template are repository collaboration material added during adoption, not extra product requirements from the PDF. Unspecified implementation questions are tracked as open, without changing the PRD's answers.

Preserve this PDF as the v1.1 baseline. For future approved changes, update PRD.md and its §16 decision log, and retain provenance for any new supplied version. Do not overwrite the original PDF to make it appear that a later decision was in v1.1.

## Revisions after the source import

**v1.2 — 3 Oct 2026:** the product owner explicitly clarified that Preflight is a standard web platform, not an iOS/SwiftUI app. PRD.md now states this in its summary, platform scope, architecture, relevant UI acceptance criteria, agent rules and §16 decision log. README.md, AGENTS.md and TEAM.md reference the updated baseline. No replacement PDF was supplied or created; use PRD.md for the current approved specification.

**v1.3 — 3 Oct 2026:** the product owner adopted all supplied brain images/motion as the visual baseline and clarified that Opus 5.5 builds the core browser brain once, reused across users and A/B views. The originals and provenance are in [../design/README.md](../design/README.md), with the Opus implementation brief. PRD.md §9.1 also distinguishes Gemini's runtime variant/analysis loop from planned Opus final-video composition, Remotion rendering and TRIBE prediction; a changed final video must be re-simulated. Existing requirement IDs, P0/P1 gates and scientific constraints remain. The original PDF is still unchanged.
