# Telos — notes for coding agents

Telos is the v2 of Orion: a team of persistent agents serving one person's goals. Why and what:
`../docs/refonte/00-cap.md`. Where we are and what's next: `../docs/refonte/SUIVI.md`. The
tasks: `../docs/refonte/01-feuille-de-route.md`. The root `../CLAUDE.md` rules apply here too.

- Run every command from `next/`: `uv sync`, `uv run pytest -q tests/test_x.py`,
  `uv run ruff format . && uv run ruff check .`, `uv run pyright` (strict, 0 errors).
- Never import from `src/orion`. A reused piece is copied, reread, simplified and tested here;
  its source and invariants are in `../docs/refonte/reprise-v1.md`.
- Layout (audit §6.4): one subpackage per area, created when its first task needs it
  (`core` journal and projections, `host`, `agents`, `conversations`, `queue`, `assignments`,
  `engines`, `workspace`, `computer`, `api`). No empty placeholder modules.
