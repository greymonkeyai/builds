# Demo 1 — typed + spoken input become source-aware assertions

## chat turn result
```json
{
 "ok": true,
 "result": {
  "ok": true,
  "needIds": [],
  "responseNeedId": "need-7106ba50b3bb",
  "drain": {
   "drained": [
    {
     "needId": "need-7106ba50b3bb",
     "ok": true,
     "result": {
      "ok": true,
      "served": true,
      "respondents": [
       {
        "personaId": "persona-f8e7c167f145",
        "name": "Curator",
        "score": 0.2658,
        "engine": "ollama:llama3.2:latest"
       },
       {
        "personaId": "persona-86f2e1acb715",
        "name": "Herald",
        "score": 0.235,
        "engine": "ollama:llama3.2:latest"
       }
      ]
     },
     "ms": 5588
    }
   ]
  },
  "intents": []
 },
 "ms": 5592
}
```

## captured-input assertion
```json
[
 {
  "subjectKey": "chat",
  "predicate": "chat:user-message",
  "value": {
   "type": "map",
   "v": {
    "text": "what does the ledger hold?",
    "all": false
   }
  },
  "claimant": "principal",
  "certainty": 1.0,
  "context": 1.0,
  "basis": {
   "kind": "captured-input"
  },
  "at": 1795067885535,
  "supersedes": null,
  "relates": [],
  "tags": [],
  "id": "a-ab7a7b45bf18",
  "meta": {}
 },
 {
  "subjectKey": "chat",
  "predicate": "chat:user-message",
  "value": {
   "type": "map",
   "v": {
    "text": "note the weather is fine",
    "all": false
   }
  },
  "claimant": "principal",
  "certainty": 1.0,
  "context": 1.0,
  "basis": {
   "kind": "captured-input"
  },
  "at": 1795067891129,
  "supersedes": null,
  "relates": [],
  "tags": [],
  "id": "a-2a9b6170e63d",
  "meta": {}
 }
]
```

## spoken transcript witness
```json
{
 "ok": true,
 "result": {
  "ok": true,
  "result": {
   "ok": true,
   "needIds": [],
   "responseNeedId": "need-7d34427de963",
   "drain": {
    "drained": [
     {
      "needId": "need-7d34427de963",
      "ok": true,
      "result": {
       "ok": true,
       "served": true,
       "respondents": [
        {
         "personaId": "persona-f8e7c167f145",
         "name": "Curator",
         "score": 0.235,
         "engine": "ollama:llama3.2:latest"
        },
        {
         "personaId": "persona-86f2e1acb715",
         "name": "Herald",
         "score": 0.235,
         "engine": "ollama:llama3.2:latest"
        }
       ]
      },
      "ms": 5503
     }
    ]
   },
   "intents": []
  },
  "ms": 5507
 },
 "ms": 5510
}
```

## device:speech-transcript assertion
```json
[
 {
  "subjectKey": "device",
  "predicate": "device:speech-transcript",
  "value": {
   "type": "map",
   "v": {
    "transcript": "note the weather is fine",
    "confidence": 0.82
   }
  },
  "claimant": "engine:stt",
  "certainty": 0.82,
  "context": 1.0,
  "basis": {
   "type": "map",
   "v": {
    "kind": "captured-input"
   }
  },
  "at": 1795067891127,
  "supersedes": null,
  "relates": [],
  "tags": [],
  "id": "a-bbb4dabf3af9",
  "meta": {}
 }
]
```

Each row carries claimant, basis.kind, certainty, time — typed, attributed, provenanced input.