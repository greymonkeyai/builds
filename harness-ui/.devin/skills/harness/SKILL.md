---
name: harness
description: Operate the development harness — directions, cycles, JEV judging, scenario suite, devlog. Use when the user asks to set up or run the harness in this folder, issues a direction, or mentions cycles, JEV, rubric, scenario suite, coordinator/build sessions, or the development log.
allowed-tools:
  - read
  - grep
  - glob
---

You are a coordinator session for the development harness documented in `C:\Harness`.

Start at `C:\Harness\harness\runbook.md` — it is the operating procedure. Read the model
docs it cites (`workflow.md`, `rubric.md`, `implementation.md`) and `C:\Harness\AGENTS.md`
for boundaries. The docs are authoritative; this skill only orients you.

Load-bearing rules (details live in the docs — do not restate them into other files):

- **Intake first.** Work through `harness/templates/intake.md`: prompt the owner for every
  detail not already stated — project folder, line name, prompt reference, baseline,
  first direction, judge model, scenario suite. Do not guess.
- **The cycle gate.** Clarify each direction sufficiently before cycles run; reject
  ambiguous directions as inadequate. Exhaustive clarification is the discipline for
  spec/doc work; cycles are cheap to discard.
- **Roles stay isolated.** Coordinator (this session), disposable build session(s), and
  the JEV — a separate `devin -p` session per scoring event, pinned to a cheap model
  distinct from the builder's. Judge is never folded into builder.
- **Machinery travels with the project.** Gates, `jev-prompt.md`, `scenarios.md`, and
  `devlog.md` live in the project folder — copy from `harness/templates/` at birth.
- **`C:\Project` is read-only** unless the owner directs otherwise. Cite the spec corpus
  by path and identifier (E-*, D-*, §sections); prompt amendments are drafted here but
  adopted through its own revision process.
- This workspace documents *how* implementations are compared, not *what* they must do.
  Keep harness docs, method docs, and project development logs in their own places.
