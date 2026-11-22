# Demo 8 — restart recovery + consolidation without losing provenance

before restart: 139 rows; after re-open: 139 rows, 135 live (durable JSONL).

## persona view survives restart
```json
{
 "subjectKey": "persona:persona-5826e68b65be",
 "slots": {
  "persona:exists": {
   "predicate": "persona:exists",
   "value": {
    "type": "map",
    "v": {
     "name": "Cartographer"
    }
   },
   "certainty": 1.0,
   "context": 1.0,
   "effectiveConfidence": 1.0,
   "claimant": "principal",
   "assertionId": "a-0db18af00839",
   "at": 1795067896678,
   "superseded": false
  },
  "persona:name": {
   "predicate": "persona:name",
   "value": {
    "type": "string",
    "v": "Cartographer"
   },
   "certainty": 1.0,
   "context": 1.0,
   "effectiveConfidence": 1.0,
   "claimant": "principal",
   "assertionId": "a-535322e77409",
   "at": 1795067896679,
   "superseded": false
  },
  "persona:interest": {
   "predicate": "persona:interest",
   "value": {
    "type": "string",
    "v": "routes"
   },
   "certainty": 1.0,
   "context": 1.0,
   "effectiveConfidence": 1.0,
   "claimant": "principal",
   "assertionId": "a-dfc60d2c4fe1",
   "at": 1795067896680,
   "superseded": false
  },
  "persona:portrait": {
   "predicate": "persona:portrait",
   "value": {
    "type": "map",
    "v": {
     "artifact": "C:\\builds\\project\\version 0.3.0.001\\runtime\\demo\\artifacts\\persona-5826e68b65be.svg",
     "engine": "inproc-svg"
    }
   },
   "certainty": 1.0,
   "context": 1.0,
   "effectiveConfidence": 1.0,
   "claimant": "engine:portrait",
   "assertionId": "a-251284c20709",
   "at": 1795067896682,
   "superseded": false
  },
  "persona:trait": {
   "predicate": "persona:trait",
   "value": {
    "type": "list",
    "v": [
     "curious",
     "spatial"
    ]
   },
   "certai…
```

## governed consolidation
```json
{
 "ok": true,
 "compacted": {
  "removed": 4,
  "kept": 136
 },
 "confidence": {
  "adjusted": []
 }
}
```

## compaction summary preserves removed ids + superseding rows
```json
[
 {
  "subjectKey": "ledger",
  "predicate": "cleanup:compacted",
  "value": {
   "type": "list",
   "v": [
    {
     "removedId": "a-499322926a98",
     "subject": "need:need-7106ba50b3bb",
     "predicate": "need:open",
     "at": 1795067885539,
     "supersededBy": "a-ecd7c5737c90"
    },
    {
     "removedId": "a-25924a51c4d4",
     "subject": "need:need-7d34427de963",
     "predicate": "need:open",
     "at": 1795067891133,
     "supersededBy": "a-8796aed0d0c8"
    },
    {
     "removedId": "a-da270be8e31c",
     "subject": "need:need-e87e604a89f0",
     "predicate": "need:open",
     "at": 1795067896638,
     "supersededBy": "a-e128003dd9a2"
    },
    {
     "removedId": "a-3fff3383023a",
     "subject": "need:need-f2ea76417a83",
     "predicate": "need:open",
     "at": 1795067896672,
     "supersededBy": "a-b828795f0b7d"
    }
   ]
  },
  "claimant": "steward:cleanup",
  "certainty": 1.0,
  "context": 1.0,
  "basis": {
   "kind": "execution"
  },
  "at": 1795067900785,
  "supersedes": null,
  "relates": [],
  "tags": [],
  "id": "a-ff72ae23a8a8",
  "meta": {}
 }
]
```