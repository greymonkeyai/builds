# builds

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/greymonkeyai/builds)

Archive of `C:\builds` — the `project` development-harness line of development:
disposable fresh-from-prompt builds (`project/version 0.3.0.xxx/`) of a local-first,
assertion-ledger persona ecosystem, plus the harness corpus that produces and scores
them.

## Layout

- `project/` — harness workspace
  - `prompt.md`, `devlog.md`, `direction-*.md`, `conventions-*.md`, `shortcomings-*.md`,
    `harness-amendments-*.md`, `prompt-amendments-*.md` — governing corpus; the object
    under refinement is `prompt.md`, builds are disposable evidence
  - `.devin/` — harness gates (direction gate, devlog check), ACP build driver,
    JEV prompts and session logs, scenario suite
  - `version 0.3.0.001/`, `version 0.3.0.002/` — one folder per build:
    `app/` Python source + UI, `evidence/` launch and scenario artifacts,
    `runtime/` ledger/persona state, `scripts/`, `seed-packs/`
- `harness-ui/` — harness line of development for the builds-root status display
  (read-only, file-derived pages over this repo; spec in `harness-ui/prompt.md`)

Related: [greymonkeyai/avatarsDev](https://github.com/greymonkeyai/avatarsDev) is the
reference realization these builds are measured against.

Wiki: https://deepwiki.com/greymonkeyai/builds
