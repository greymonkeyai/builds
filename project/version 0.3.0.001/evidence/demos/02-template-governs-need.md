# Demo 2 — template governs an unfulfilled requirement

## need opened (missing required slot 'query')
```json
{
 "toolId": "run-search",
 "summary": "demo2: governed requirement",
 "slots": {},
 "satisfaction": {},
 "project": null
}
```

## candidate supplied -> gate ready
```json
{
 "ready": true,
 "missing": [],
 "filled": {
  "query": {
   "value": "confidence",
   "confidence": 0.85,
   "source": "user",
   "effectiveConfidence": 0.85,
   "assertionId": "a-6c18c2721a53",
   "at": 1795067896639
  }
 },
 "grant": null
}
```

## fulfillment
```json
{
 "ok": true
}
```
## need after
```json
{
 "status": "fulfilled",
 "detail": {
  "toolId": "run-search",
  "result": {
   "ok": true,
   "query": "confidence",
   "hits": [
    {
     "subjectKey": "need:need-e87e604a89f0",
     "predicate": "need:candidate",
     "value": {
      "type": "map",
      "v": {
       "slot": "query",
       "value": "confidence",
       "confidence": 0.85,
       "source": "user"
      }
     },
     "claimant": "principal",
     "certainty": 0.85,
     "context": 1.0,
     "basis": {
      "kind": "source-evidence",
      "ref": "user"
     },
     "at": 1795067896639,
     "supersedes": null,
     "relates": [],
     "tags": [],
     "id": "a-6c18c2721a53",
     "meta": {}
    },
    {
     "subjectKey": "decision:persona",
     "predicate": "decision:respondent",
     "value": {
      "type": "map",
      "v": {
       "input": "note the weather is fine",
       "ranking": [
        {
         "personaId": "persona-f8e7c167f145",
         "score": 0.235,
         "features": {
          "lens_overlap": 0.0,
          "topic_link": 0.0,
          "confidence": 0.8,
          "priority": 0.5
         }
        },
        {
         "personaId": "persona-86f2e1acb715",
         "score": 0.235,
         "features": {
          "lens_overlap": 0.0,
          "topic_link": 0.0,
          "confidence": 0.8,
          "priority": 0.5
         }
        },
        {
         "personaId": "persona-75757f70538f",
         "score": 0.235,
         "features": {
          "lens_overlap": 0.0,
          "topic_link": 0.0,
          "confidence": 0.8,
          "priority": 0.5
         }
     …
```

Creation did not imply execution: the need waited on the floor until required slots met their certainty threshold.