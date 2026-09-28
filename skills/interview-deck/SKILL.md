---
name: interview-deck
description: Create or revise editable, evidence-based interview presentations in Chinese and English. Use for interview self-introductions, project deep dives, bilingual deck generation, speaker notes, rendering, or slide QA; keep personal content in the private career submodule.
---

# Interview Deck

Build a presentation that helps an interviewer remember a small number of defensible
claims. Prefer a coherent technical narrative over a slide-shaped resume.

## Repository boundary

- Keep reusable code, layouts, and anonymous examples in this public skill.
- Keep names, contact details, unpublished work, metrics, screenshots, and actual
  deck sources under `career/`.
- Treat `career/面试知识库/核心口径/resume_claim_matrix.md` as the claim boundary.
  Every quantitative claim needs an evidence statement and a limitation.

## Workflow

1. Read the claim matrix, relevant experience files, and only the deep-dive files
   needed for the requested deck.
2. Establish audience, role, talk duration, and language. When unspecified, use a
   10–12 minute, 16:9 technical interview deck.
3. Write one conclusion per slide using `claim -> evidence -> mechanism -> boundary`.
4. Put content in locale-specific JSON with stable slide IDs. Read
   [references/content-schema.md](references/content-schema.md) when authoring data.
5. Generate an editable PPTX with `scripts/build-deck.mjs`.
6. Run `scripts/validate-deck.mjs`, then render with `scripts/render-deck.sh`.
   Inspect the contact sheet and full-size pages for overflow, overlap, font fallback,
   weak contrast, tiny text, and accidental disclosure.
7. Stabilize Chinese first. Before authoring English, read
   [references/bilingual-workflow.md](references/bilingual-workflow.md) and preserve
   slide ID, evidence, visual hierarchy, and metric parity.

Read [references/visual-system.md](references/visual-system.md) when changing theme,
layout, typography, or chart styling.

## Commands

```bash
node skills/interview-deck/scripts/validate-deck.mjs <content.json>
node skills/interview-deck/scripts/build-deck.mjs <content.json>
bash skills/interview-deck/scripts/render-deck.sh <deck.pptx>
```

Never claim that a generated file is visually correct until the rendered pages have
been inspected. Do not translate a deck until the source-language structure is stable.
