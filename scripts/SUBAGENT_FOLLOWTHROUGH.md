# Subagent result follow-through

Project-local configuration: `.codex/hooks.json`.
Implementation: `scripts/subagent-followthrough.py` (Python standard library only).

## Activate and verify

1. In this repository's Codex session, open `/hooks`, inspect the three command hooks, and trust their exact definitions. Do not bypass hook trust. If the current session does not discover the new file, resume from the repository root and inspect `/hooks` again.
2. Delegate a harmless, bounded read-only task. Wait for it and inspect the hook UI/events. `SubagentStart` records running work; `SubagentStop` records a result requiring review.
3. Before finishing, the synchronous `Stop` hook should ask the coordinator to continue if work/results have not been acknowledged. The coordinator must read the actual collaboration result, explain the outcome, and decide the next action.
4. Inspect and acknowledge the exact receipt:

   ```sh
   python3 scripts/subagent-followthrough.py status --session SESSION_ID
   python3 scripts/subagent-followthrough.py ack --session SESSION_ID --agent AGENT_ID --version VERSION --reason processed
   ```

   Use `waiting_user` only after reporting the actual missing input, `superseded` only for a genuinely replaced task, or `failed_reported` after explaining the failure. Do not acknowledge a result just to silence the hook.
5. Confirm the next Stop permits completion once all receipts are handled. A synthetic test passing is not proof that the live client has loaded/trusted the hook.

## Safety and limits

### Live verification checkpoint (2026-09-09)

The three trust entries exist, but no live hook state database was created after
real subagent completions. Treat hook activation as **unverified**, not repaired.
Completion messages do reach an active coordinator; premature coordinator final
responses have repeatedly left results unattended.

A single `codex queue --thread <exact current thread UUID> --message <probe>`
was accepted by the installed CLI. Acceptance alone is not evidence that an idle
parent resumes. Verify receipt of that exact probe after the current turn ends
before implementing any background relay. Never target a session by guessed name,
send repeated probes, restart the shared daemon, or bypass hook trust to make a
test appear successful. Do not resume recruiting automation on the assumption that
this unverified wake-up mechanism works.

- State is ignored runtime data under `.runtime/subagent-followthrough/`, isolated by parent session. It stores IDs, hashes and dispositions, not messages, transcripts, personal fields or invitation URLs.
- Duplicate events do not reopen handled results. A new result/version requires a fresh acknowledgment; stale acknowledgments are rejected.
- At most three continuation requests are emitted for an unchanged pending set, and at most six across the entire parent session (even if tasks keep changing). After either limit, the hook warns and leaves receipts unresolved. This is a backstop, not an endless work loop; the coordinator must disclose unresolved work rather than claim completion. A new session receives its own budget.
- Different agent turns have separate receipts. Late events cannot hide a newer turn, and a delayed Start cannot overwrite its received Stop. An acknowledgment takes a database write lock and checks the exact version atomically.
- The hook never logs in, submits applications, sends external messages, calls an LLM, invokes `codex queue`, or bypasses user confirmation. Hook prompts do not grant new authority.
- `SubagentStop` does not start an idle parent turn. This design prevents premature stopping while the parent is active; it is not an always-on wake-up service.
- Tasks already running before hooks were activated may not have a Start receipt; inspect live agents separately. Old recruiting queue records are deliberately not imported, avoiding an infinite loop over historical blocked attempts.
- Runtime errors fail open with a visible warning. SQLite transactions serialize event/receipt updates; state remains inspectable for troubleshooting.
- Disable the three hooks through `/hooks` to roll back. This does not alter recruiting data or browser sessions.

Tests: `python3 scripts/test_subagent_followthrough.py`.

Reference: https://learn.chatgpt.com/docs/hooks
