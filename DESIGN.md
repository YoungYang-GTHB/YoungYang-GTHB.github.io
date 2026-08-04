# Personal Portfolio Design System

## Subject and job

This is the portfolio of an embodied-AI and robotics engineer. Its first job is to prove, within 30 seconds, that the candidate can take a VLA system from data and training to a real dual-arm robot.

## Direction: Lab Console

The visual language comes from the real workbench: graphite robot hardware, blue grippers, teal telemetry, camera overlays, experiment labels, and engineering field notes. The palette is cool and controlled so the full-color portrait and real-robot video remain the visual evidence. It should feel precise and authored, not futuristic for its own sake.

## Tokens

- Frost: `#F7F9FC`
- Ink: `#111827`
- Servo blue: `#315EFB`
- Signal teal: `#2DD4BF`
- Console: `#0D1418`
- Steel: `#D9E2EC`
- Display: restrained CJK serif stack for research-note headings
- Body: Geist/system CJK sans-serif
- Utility: Geist Mono for labels, metadata, and measurements

## Layout

```text
┌ identity / positioning ───────────────────────────────┐
│ name, focus, contact                    compact photo │
└───────────────────────────────────────────────────────┘
┌ FIELD NOTE 01 / flagship real-robot proof ───────────┐
│                                                      │
│              large calibrated video frame            │
│                                                      │
├ project thesis ───────────────┬ model/task/platform ─┤
├ 01 data → 02 train → 03 eval → 04 infer → 05 robot ─┤
└ measured outcomes / public references ───────────────┘
┌ compact evidence band ────────────────────────────────┐
└ education / skills / supporting projects / history ──┘
```

## Signature

The real-robot video is framed as a calibrated experiment viewport with corner reticles, a live status line, task identity, and measured metadata. This is the only deliberately cinematic element; the rest of the interface stays quiet.

Supporting resume sections use one shared structured-record frame: cool-white surfaces, blue section markers, thin steel dividers, and teal evidence dots. Education, skills, projects, experience, patents, and awards should read as one continuous engineering dossier rather than separate promotional cards.

## Guardrails

- No ambient pulsing gradient blobs.
- No category-by-category rainbow gradients; hierarchy comes from structure and type.
- Avoid nested rounded cards; use dividers and layout hierarchy first.
- Motion is limited to one entrance sequence and purposeful hover feedback.
- Respect `prefers-reduced-motion`.
- Keep the public video click-to-load and strip unrelated workspace details.
