# Bilingual workflow

Freeze the Chinese deck before producing English. “Frozen” means slide order, slide IDs,
claim selection, chart data, image choices, and major geometry have been approved.

Create the English source by copying the data structure, not the rendered slides.

- Keep slide IDs and quantitative values identical.
- Rewrite for natural interview speech; do not translate word for word.
- Preserve uncertainty and evidence boundaries exactly.
- Allow locale-specific line breaks and a 10–15% typography adjustment.
- Keep product names, model names, units, and experiment protocol labels consistent.
- Write independent English speaker notes and rehearse timing again.

Run validation with peer parity:

```bash
node skills/interview-deck/scripts/validate-deck.mjs slides.en.json --peer slides.zh.json
```

Parity checks cover slide IDs and metric keys. Visual review remains mandatory because
English text expansion and font metrics can change line breaks.
