# Private profile contract

Use this contract only when a form needs fields that do not belong in the public resume.

## Rules

- Keep the populated file inside the private `career/` submodule.
- Never auto-discover or print it. Pass it explicitly with `--private-profile` or
  `JOB_HUNTER_PRIVATE_PROFILE`.
- Give Research and Ranking workers only a redacted capability snapshot. Give the
  Browser Worker only the fields needed by the current form.
- Treat `documents[].allowed_use` as an upload allowlist. Never upload a document
  merely because it exists.
- Record unknown values as absent. Do not invent fallback values unless the user has
  already approved that exact fallback in the private profile.
- A reduced profile or a missing mapping is not evidence that the user's information
  is absent. Before reporting a missing field, consult the explicitly supplied
  authoritative field library, the relevant structured profile section, and any
  referenced document index. Resolve conflicts through the coordinator.
- Existing user authorization applies to later workers within its stated scope.
  Authorized identity/contact fields may be read from explicit private references
  directly into the browser process; do not embed their values in task JSON, tool
  output, messages, screenshots, or artifacts. Never dump a private source before
  redacting it: parse in memory and output field names and presence checks only.
- For attachments, distinguish a missing index entry from a missing file. Follow
  explicit library references, verify the education stage, document type and form
  requirements, then apply the upload authorization. A degree certificate is not an
  enrollment report; a document for one education row must not be reused for another.
- Do not write field values, document contents, access tokens, or complete addresses
  to runtime logs or worker artifacts.

Validate the structure against `schemas/profile-private.schema.json`. A minimal file is:

```yaml
schema_version: 1
resume_overrides: {}
form_profile: {}
documents:
  - type: degree-certificate
    path: /absolute/private/path.pdf
    allowed_use: explicit-form-upload
```

Generate the local form profile explicitly:

```bash
python3 scripts/profile_mapper.py \
  --private-profile career/个人资料/profile.private.yaml \
  --compact
```

The command writes JSON to stdout. Redirect it only to a private, permission-restricted
runtime path and remove it when the browser task finishes.
