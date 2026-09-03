# Agent operating guide

This repository is the public code and automation layer for YoungYang's portfolio,
resume builds, job discovery, and application tracking. Personal data and the live
2027 recruiting ledger live in the private `career/` git submodule.

## Start here

1. Run `git submodule update --init --recursive`.
2. Run `./scripts/agent-status.sh` from the repository root.
3. Read `career/AGENT_HANDOFF.md` in full. If the private submodule is unavailable,
   stop before any personalized form filling or application-state edits.
4. Read `career/求职投递/2027届/投递执行规范.md` before opening a new application.
5. Run `python3 skills/job-hunter/scripts/jobctl.py validate` before and after
   changing recruiting data.

## Repository boundary

- Public repository: reusable website, resume templates, skills, scripts, extension,
  and anonymous examples.
- Private `career/` submodule: personal profile fields, resume sources and PDFs,
  interview notes, offers, application ledger, referrals, and recruiting progress.
- Never copy credentials, cookies, access tokens, identity-document numbers, private
  offer terms, or unpublished internship details into the public repository.
- `career/求职投递/2027届/data/applications.yaml` is the canonical application
  ledger. Generated Markdown summaries and browser tabs are not sources of truth.
- `career/求职投递/2027届/data/company_categories.yaml` controls the generated
  state-owned/research, foreign, and private-company views. Do not hand-edit
  `投递汇总.md` or `分类汇总/`.

## Non-negotiable recruiting rules

- Before every application, scan that company's complete current official campus
  job pool, compare exact job IDs, requirements, locations, quotas, and prior history,
  then select the best fit. Do not rely on an old shortlist.
- Run `jobctl.py history` and `jobctl.py preflight` before submission. Never consume
  a company/program quota merely to fill all available choices.
- Never fabricate or upgrade experience. Preserve the exact internship naming and
  capability boundaries documented in the private handoff guide.
- Login, CAPTCHA, identity-sensitive fields, and any final-submit action remain under
  the user's control. A final submit requires explicit user confirmation in the
  current interaction.
- After a verified successful submission, use `jobctl.py record-applied`, validate
  the ledgers, and close that company's browser tabs.
- Prefer Suzhou, then Hangzhou, then other non-Beijing locations when role fit is
  comparable. Beijing is the fallback unless it is the only materially suitable role.

## Editing and delivery

- Preserve unrelated user changes and inspect both `git status` outputs.
- Commit and push `career/` first. Then commit the updated submodule pointer and any
  public-code/documentation changes in the parent repository and push it second.
- Do not commit generated secrets, browser profiles, session exports, or raw mailbox
  data.

The detailed operating model, browser/CDP architecture, truth-source map, recovery
steps, and current checkpoint are in `career/AGENT_HANDOFF.md`.
