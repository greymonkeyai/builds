# Demo 5 — minimal personality extended by later work

## minted
```json
{
 "personaId": "persona-5826e68b65be",
 "admonished": false
}
```

## portrait artifact
```json
{
 "ok": true,
 "artifact": "C:\\builds\\project\\version 0.3.0.001\\runtime\\demo\\artifacts\\persona-5826e68b65be.svg"
}
```

## edits applied
```json
{
 "ok": true,
 "persona": {
  "id": "persona-5826e68b65be",
  "name": "Cartographer",
  "traits": [
   "curious",
   "spatial"
  ],
  "interests": [
   "maps",
   "routes"
  ],
  "lens": {},
  "voice": {
   "local": "sapi-default"
  },
  "imitates": null,
  "color": "#09efe6",
  "rosterPriority": 0.7,
  "confidence": 0.8,
  "mintedAt": 1795067896.6785715,
  "toolPermissions": [],
  "displayMode": "respondent"
 }
}
```

## computed persona view (slots resolved from ledger)
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