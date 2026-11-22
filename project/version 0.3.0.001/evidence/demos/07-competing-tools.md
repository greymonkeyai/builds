# Demo 7 — locally competing tools expressing the same need

render-speech-sapi and render-speech-remote both express need 'speech.render'. speak-voice ranks them; results are interpretable under a shared local understanding (ok / rendered artifact).

## speak-voice outcome
```json
{
 "ok": true,
 "renderedBy": "render-speech-sapi",
 "result": {
  "ok": true,
  "engine": "sapi",
  "artifact": null
 }
}
```

## remote renderer invoked directly — honest unconfigured failure
```json
{
 "ok": true,
 "result": {
  "ok": false,
  "error": "remote TTS not configured — no source grant",
  "unconfigured": true
 },
 "ms": 0
}
```

rank multipliers: sapi 1.0->1.0, remote 1.0->0.9

## churn rows (remote's unconfigured failure lowers its rank, not its eligibility)
```json
[
 {
  "subjectKey": "decision:churn",
  "predicate": "decision:churn",
  "value": {
   "type": "map",
   "v": {
    "toolId": "render-speech-remote",
    "needId": null,
    "from": 1.0,
    "to": 0.9
   }
  },
  "claimant": "model:decision",
  "certainty": 1.0,
  "context": 1.0,
  "basis": {
   "kind": "execution"
  },
  "at": 1795067899741,
  "supersedes": null,
  "relates": [],
  "tags": [],
  "id": "a-1b2740573164",
  "meta": {}
 }
]
```