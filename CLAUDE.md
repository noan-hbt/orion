# Orion — notes for coding agents

Orion is an always-on, proactive personal agent. Read `docs/architecture/04-architecture.md`
before changing structure, and `docs/DECISIONS.md` for why things are the way they are. The README, `deploy/README.md` and
`docs/REFERENCE.md` are in English; other docs are in French; code, identifiers and comments are in English.

## Commands

- `uv sync` — install
- `uv run pytest -q tests/test_x.py` — tests (only the files touched; a stuck test fails after
  60 s). On Windows, `uv` is in `~/.local/bin` (add it to PATH if not found)
- `uv run ruff format . && uv run ruff check .` — format and lint
- `uv run pyright --pythonplatform Linux` — strict type check (must stay at 0 errors; Linux
  like CI and the server, even from Windows)
- `uv run orion doctor` — check config and storage (`uv tool install --editable .` puts `orion`
  on PATH; without `--config` it reads `./orion.toml`, else `~/.orion/orion.toml`, D180)
- `uv run python -m evals` — behavioural evaluations on the real model (costs cents; `--model`,
  `--case`, `--repeat`, `--offline`). Add a case when Orion gets something wrong for real.

## Rules

- The journal (`orion.core.journal`) is append-only. Never add an update path; corrections are
  new events, forgetting goes through `redact`.
- Projections must be rebuildable from the journal alone.
- Every piece of content carries `Provenance` and `Trust`; derived trust is the minimum of inputs.
- Fail closed. Never swallow an exception: log it with context or let it propagate.
- No secrets in config files or code: use `SecretRef`.
- New capabilities (channels, sources, skills) are modules (`orion.modules`, D24), not code
  wired into `app.py` or `serve.py`. The core stays small.
- Everything that leaves Orion goes through `guardian.outbox.Outbox` (journaled, idempotent).
  Orion speaks first only through the initiative engine, which journals every decision.
- Tests: few, and on behaviour. A new feature gets one or two tests of what the owner would
  notice, not one per branch; a fix gets the test that would have caught it. Never assert exact
  wording, layout or counts that are not the point: they break on every change. Run only the
  test files you touched (`uv run pytest -q tests/test_x.py`), never the whole suite. A test
  that breaks for a reason unrelated to the change is simplified or deleted, not patched again.
- Prompt-cache contract (`tests/test_runtime_cache.py`): each model request must extend the
  previous one byte for byte. Nothing volatile (time, retrieved memory) goes in the system
  message; journaled messages are replayed exactly as sent; the tool registry is fixed and
  sorted; every request carries a stable `session_id`. Never break these tests.
- Parallel sessions: if another coding agent session is already working in this checkout
  (uncommitted changes you did not make, a branch you did not create), do not touch it. Work in
  your own git worktree (`git worktree add ../orion-<topic> -b <branch>`) and remove it once
  merged.

## Merging

When you finish a piece of work, merge its PR yourself without asking the owner (owner's
standing instruction, 09/11/2026): run the checks locally (tests of the touched files, ruff,
pyright), open the PR, then merge it right away (squash, PR title as the commit title). **Do not
wait for CI** (owner's instruction, 09/11/2026): if CI turns red afterwards, the fix comes first
in the next PR. Do not merge if a local check fails, if the PR waits on an owner decision
("Questions ouvertes" in `SUIVI.md`, `a-decider` label), or if it is not your PR. After merging,
start the next work from the up-to-date `main`.

## Refonte v2 (current priority)

Orion is being rebuilt as a multi-agent platform anyone can install (D291–D295). Until the
switch-over, **all new work is the refonte**; v1 (`src/orion`) only gets urgent fixes.

- Start every session by reading `docs/refonte/SUIVI.md` (where we are, next task, handoff,
  open questions), then the task in `docs/refonte/01-feuille-de-route.md`. The why is in
  `docs/refonte/00-cap.md`.
- v2 lives in `next/` (its own uv project, package `orion`, D297). Never import from `src/orion`: a
  reused piece is copied, reread, simplified and tested in `next/`. Run commands from `next/`.
- One task (`R<p>.<n>`) = one branch `refonte/R<p>.<n>-<topic>` = one PR titled `R<p>.<n> ...`.
  Only start a task whose prerequisites are merged and that has no open question in `SUIVI.md`.
  If its "Fait quand" is unclear or contradicts a decision, write the question under
  "Questions ouvertes" in `SUIVI.md` and stop.
- Work continuously, task after task. At the end of each task: update `SUIVI.md` (status
  `fait` with the PR number, next task, handoff notes) in the same PR, commit, push, open the
  PR, merge it without waiting for CI (see "Merging" below), then tell the owner the task is done
  and that the session can be cleared (`/clear`) before the next one. Do the same
  at the end of each part, adding its demonstration to `SUIVI.md`.
- If the conversation grows long (around 150k tokens: many large file reads, long debugging),
  do not start a new step: finish or checkpoint the current one, write the handoff in
  `SUIVI.md`, commit and push, and ask the owner to `/clear`. A fresh session must be able to
  resume from `SUIVI.md` alone.
- Work found along the way that is not in the roadmap goes into `SUIVI.md` ("Passation" or
  "Questions ouvertes"), not into the current PR.
- Never copy OpenBot code (PolyForm Noncommercial): behaviour only, original implementation.
