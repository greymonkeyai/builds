# Demo 4 — multi-step list preserves criteria; non-matches recorded

## build-list result
```json
{
 "ok": true,
 "result": {
  "criteria": "study techniques",
  "matched": [
   "spaced repetition study techniques",
   "interleaved practice study techniques",
   "retrieval practice study techniques"
  ],
  "headers": [
   "STUDY METHODS:",
   "CHAPTER TWO"
  ],
  "foreignLinks": [
   "https://example.com/unrelated-page"
  ],
  "categoryErrors": [
   "aardvark grooming manual"
  ]
 },
 "ms": 5
}
```

## non-matching candidates retained for review/cleanup
```json
[
 {
  "subjectKey": "need:need-f2ea76417a83",
  "predicate": "need:candidate",
  "value": {
   "type": "map",
   "v": {
    "slot": "header",
    "value": "STUDY METHODS:",
    "confidence": 0.2,
    "source": "list-input",
    "class": "header"
   }
  },
  "claimant": "pipeline:list",
  "certainty": 0.2,
  "context": 1.0,
  "basis": {
   "kind": "source-evidence"
  },
  "at": 1795067896672,
  "supersedes": null,
  "relates": [],
  "tags": [],
  "id": "a-c1079627e010",
  "meta": {}
 },
 {
  "subjectKey": "need:need-f2ea76417a83",
  "predicate": "need:candidate",
  "value": {
   "type": "map",
   "v": {
    "slot": "foreign-link",
    "value": "https://example.com/unrelated-page",
    "confidence": 0.2,
    "source": "list-input",
    "class": "foreign-link"
   }
  },
  "claimant": "pipeline:list",
  "certainty": 0.2,
  "context": 1.0,
  "basis": {
   "kind": "source-evidence"
  },
  "at": 1795067896674,
  "supersedes": null,
  "relates": [],
  "tags": [],
  "id": "a-7319be2f339b",
  "meta": {}
 },
 {
  "subjectKey": "need:need-f2ea76417a83",
  "predicate": "need:candidate",
  "value": {
   "type": "map",
   "v": {
    "slot": "category-error",
    "value": "aardvark grooming manual",
    "confidence": 0.3,
    "source": "list-input",
    "class": "category-error",
    "reason": "does not match requested criteria"
   }
  },
  "claimant": "pipeline:list",
  "certainty": 0.3,
  "context": 1.0,
  "basis": {
   "kind": "source-evidence"
  },
  "at": 1795067896675,
  "supersedes": null,
  "relates": [],
  "tags": [],
  "id": "a-57fc9865a9e7",
  "meta": {}
 },
 {
  "subjectKey": …
```

Headers, foreign links, and category errors are results that do not match the requested criteria — recorded, retained, reviewable.