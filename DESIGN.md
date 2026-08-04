# Personal Portfolio Design System

## Subject and job

This is the portfolio of an embodied-AI and robotics engineer. Its first job is to prove, within 30 seconds, that the candidate can take a VLA system from data and training to a real dual-arm robot.

## Direction: Lab Console

The visual language comes from the real workbench: graphite robot hardware, blue grippers, an olive garment, a muted yellow calibration wall, camera overlays, experiment labels, and engineering field notes. It should feel precise and authored, not futuristic for its own sake.

## Tokens

- Paper: `#F2F5F0`
- Ink: `#101816`
- Servo blue: `#2857E5`
- Garment olive: `#66724C`
- Calibration yellow: `#CBC64C`
- Steel: `#D9E0DA`
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

## Guardrails

- No ambient pulsing gradient blobs.
- Avoid nested rounded cards; use dividers and layout hierarchy first.
- Motion is limited to one entrance sequence and purposeful hover feedback.
- Respect `prefers-reduced-motion`.
- Keep the public video click-to-load and strip unrelated workspace details.
