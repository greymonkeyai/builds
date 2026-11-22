# Demo 3 — candidate ranking by contextual confidence + recency

Two 0.6 candidates: principal at same certainty beats an unvetted source (source ceiling caps effective confidence); the 0.9 source candidate still ranks below because the source ceiling binds.

## ranked candidates (slot 'port')
```json
{
 "port": [
  {
   "value": 9760,
   "confidence": 0.6,
   "source": "principal",
   "effectiveConfidence": 0.6,
   "assertionId": "a-c3f28f887243",
   "at": 1795067896658
  },
  {
   "value": 9761,
   "confidence": 0.9,
   "source": "source:old-doc",
   "effectiveConfidence": 0.5,
   "assertionId": "a-7cf231a6fe44",
   "at": 1795067896670
  },
  {
   "value": 9847,
   "confidence": 0.6,
   "source": "source:old-doc",
   "effectiveConfidence": 0.5,
   "assertionId": "a-6f359364f805",
   "at": 1795067896648
  }
 ]
}
```

## failed evidence retained
```json
{
 "invoke": {
  "ok": true,
  "result": {
   "ok": false,
   "error": "not a meridian.exchange/v1 package"
  },
  "ms": 0
 },
 "telemetry": [
  {
   "subjectKey": "tool:import-exchange",
   "predicate": "tool:telemetry",
   "value": {
    "type": "map",
    "v": {
     "status": "ok",
     "ms": 0,
     "needId": null,
     "error": null
    }
   },
   "claimant": "tool:registry",
   "certainty": 1.0,
   "context": 1.0,
   "basis": {
    "kind": "execution"
   },
   "at": 1795067896670,
   "supersedes": null,
   "relates": [],
   "tags": [],
   "id": "a-a6cdd64e4a96",
   "meta": {}
  }
 ]
}
```

Nothing is made true by being recorded — candidates stay inspectable with source and confidence until a tool selects them.