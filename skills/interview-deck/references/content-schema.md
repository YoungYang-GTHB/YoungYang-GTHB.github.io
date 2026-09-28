# Content schema

The deck source is UTF-8 JSON with a `meta` object and ordered `slides` array.

Required `meta` fields:

- `language`: `zh-CN` or `en-US`.
- `version`, `title`, `author`, `targetRole`, and `durationMinutes`.
- `output`: repository-relative PPTX path.
- `assets`: repository-relative paths for `portrait`, `hero`, and optional images.

Every slide requires:

- `id`: stable lowercase identifier shared by both languages.
- `layout`: one of the layouts implemented by `build-deck.mjs`.
- `title`: a conclusion, not a generic section label.
- `takeaway`: the single sentence the audience should retain.
- `notes`: a spoken script. Keep main-deck notes near 45–75 seconds.

Layouts have layout-specific fields. Use the current Chinese source as the executable
example; validate after editing rather than copying fields speculatively.

Quantitative slide data should include `boundary` or `footnote`. Preserve units and
measurement protocols. Do not convert offline error, intrinsic metrics, or correlations
into task success rates.

Text guidelines:

- Main title: ideally no more than 26 Chinese characters or 12 English words.
- Body: usually no more than 55 Chinese characters per block.
- Use at most three main ideas per slide.
- Put detail in speaker notes or appendix instead of shrinking text.
