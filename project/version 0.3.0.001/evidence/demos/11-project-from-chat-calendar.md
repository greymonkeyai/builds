# Demo 11 — project created/advanced from chat, related to calendar

## intents + fulfill
```json
{
 "intents": [
  {
   "toolId": "create-project",
   "score": 0.745,
   "slots": {
    "title": "spring research"
   },
   "features": {
    "keyword": 0.375,
    "pattern": 1.0,
    "slot_fill": 1.0,
    "success_rate": 0.5,
    "rank_mult": 1.0,
    "recency": 0.0,
    "source_conf": 1.0
   }
  }
 ],
 "fulfill": {
  "ok": true,
  "result": {
   "ok": true,
   "projectId": "proj-d6f218567f87",
   "goals": [
    "a-0e429a579509"
   ]
  }
 }
}
```

## goal decomposed into tool work (linked need)
```json
{
 "advanceNeed": "need-14777f946dff",
 "advanceResult": true
}
```

## project view
```json
[
 {
  "id": "proj-d6f218567f87",
  "title": "spring research",
  "goals": [
   {
    "text": "collect spring research notes",
    "status": "open"
   }
  ],
  "openNeeds": [
   {
    "id": "need-fcf32c71afb5",
    "kind": "generic",
    "spec": {
     "summary": "collect spring research notes",
     "project": "proj-d6f218567f87",
     "satisfaction": {}
    },
    "openedAt": 1795067912527,
    "claimant": "principal",
    "assertionId": "a-5f7666ea1fbb"
   }
  ],
  "fulfilled": 0
 }
]
```

## calendar link
```json
"linked"
```

## calendar events remain source evidence
```json
[
 {
  "subjectKey": "calendar",
  "predicate": "calendar:event",
  "value": {
   "type": "map",
   "v": {
    "title": "dentist appointment",
    "startMs": 1795071496685.0,
    "endMs": 0,
    "source": "ics-import"
   }
  },
  "claimant": "pipeline:calendar",
  "certainty": 0.8,
  "context": 1.0,
  "basis": {
   "kind": "source-evidence",
   "ref": "ics-import"
  },
  "at": 1795067896685,
  "supersedes": null,
  "relates": [],
  "tags": [],
  "id": "a-bb525ba9f17c",
  "meta": {}
 }
]
```