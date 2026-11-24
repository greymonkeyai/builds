window.HARNESS_DATA = {"kind":"project","generated_at":"2026-11-23T23:58:37.7823150Z","emitter":"harness-emit.ps1","project":{"id":"stalerig","path":"C:\\builds\\harness-ui\\version 0.1.0.001\\fixtures\\fleet\\stalerig","state_present":true,"state_error":null,"state":{"line":"stalerig","prompt_ref":"prompt.md (snapshot taken 2026-11-01)","direction_in_force":{"ref":"direction-002.md","clarity":"signed","baseline":"modify-and-measure","budget":{"total":4,"spent":2},"criteria":["clean launch","completeness","scenario suite"]},"builds":["version 0.1.0.001","version 0.1.0.002"],"pending_owner_questions":["Fixture: is C-Beta's recorded challenge acceptable to the owner?"],"revisions":{"prompt":"snapshot 2026-11-01","conventions":"fixture-rev-old (2 ids)","scenarios":"signed 2026-11-12 (2 ids, pre-S-gamma)"}},"suite":[{"id":"S-alpha","title":"Fixture scenario alpha"},{"id":"S-beta","title":"Fixture scenario beta"},{"id":"S-gamma","title":"Fixture scenario gamma — added 2026-11-20, after the last verdict"}],"status_files":{"last-cycle-status.txt":"2026-11-15 09:30:00: fixture session ended prompt=build-prompt-002.md\r\n"},"series":[{"label":"C1","entry":"Cycle 1 — 2026-11-10","kind":"cycle","verdict_kind":"verdict","date":"2026-11-10","direction":"`direction-001.md` — fixture direction","baseline":"fresh — produces `version 0.1.0.001/`","criteria":null,"time_to_implement":"session start 2026-11-10 ~10:00; session end 2026-11-10 ~10:20","result":"built fixture `version 0.1.0.001/` — declared for evidence only","build_folder":"version 0.1.0.001","verdict_ok":true,"verdict_error":null,"verdict":{
  "criteria": [
    { "name": "clean launch", "score": 0.5, "confidence": 0.5, "user_opinion": null },
    { "name": "completeness", "score": 0.4, "confidence": 0.5, "user_opinion": null }
  ],
  "overall": 0.45,
  "judge_model": "fixture",
  "scenarios": [
    { "id": "S-alpha", "score": 0.5, "evidence_class": "repository" },
    { "id": "S-beta", "score": 0.3, "evidence_class": "repository" }
  ],
  "notes": "Fixture verdict."
}},{"label":"C2","entry":"Cycle 2 — 2026-11-15","kind":"cycle","verdict_kind":"verdict","date":"2026-11-15","direction":"`direction-002.md` — second fixture direction","baseline":"modify-and-measure — produces `version 0.1.0.002/`","criteria":null,"time_to_implement":"session start 2026-11-15 ~09:00; session end 2026-11-15 ~09:30","result":"built fixture `version 0.1.0.002/` — declared for evidence only","build_folder":"version 0.1.0.002","verdict_ok":true,"verdict_error":null,"verdict":{
  "criteria": [
    { "name": "clean launch", "score": 0.8, "confidence": 0.6, "user_opinion": null },
    { "name": "completeness", "score": 0.6, "confidence": 0.6, "user_opinion": null }
  ],
  "overall": 0.7,
  "judge_model": "fixture",
  "scenarios": [
    { "id": "S-alpha", "score": 0.7, "evidence_class": "enactment" },
    { "id": "S-beta", "score": 0.6, "evidence_class": "enactment" }
  ],
  "notes": "Fixture verdict — predates S-gamma."
}}],"builds":[{"folder":"version 0.1.0.001","mtime":"2026-11-01T17:00:00.0000000Z","vkey":"0.1.0.1","launcher":null,"conventions":{"C-Alpha":{"status":"conformed","disposition":"conform — fixture record"},"C-Beta":{"status":"reckoned-departure","disposition":"**challenge (recorded)** — fixture departure with stated reason"}}},{"folder":"version 0.1.0.002","mtime":"2026-11-01T17:00:00.0000000Z","vkey":"0.1.0.2","launcher":"launch.cmd","conventions":{"C-Gamma":{"status":"conformed","disposition":"conform — fixture record"},"C-Alpha":{"status":"conformed","disposition":"conform — fixture record"}}}],"latest_build":"version 0.1.0.002","liveness_seconds":1925918,"newest_mtime":"2026-11-01T17:00:00.0000000Z","newest_path":"devlog.md","last_verdict":{"label":"C2","overall":0.7,"judge":"fixture","date":"2026-11-15"},"convention_ids":["C-Alpha","C-Beta","C-Gamma"],"current_state":{"prompt_declared_revision":"snapshot taken 2026-11-01","corpus_prompt_file":"C:\\builds\\harness-ui\\version 0.1.0.001\\fixtures\\corpus\\spec\\Prompt.md","corpus_prompt_mtime":"2026-11-23T23:33:34.8319856Z","corpus_conventions_file":"C:\\builds\\harness-ui\\version 0.1.0.001\\fixtures\\corpus\\spec\\CONVENTIONS.md","corpus_conventions_source":"derived-from-prompt","corpus_convention_ids":["C-Alpha","C-Beta","C-Gamma"],"live_scenario_ids":["S-alpha","S-beta","S-gamma"],"state_revisions":{"prompt":"snapshot 2026-11-01","conventions":"fixture-rev-old (2 ids)","scenarios":"signed 2026-11-12 (2 ids, pre-S-gamma)"}}}};