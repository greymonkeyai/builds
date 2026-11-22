# Demo 6 — relevant background result through a distinct personality

## steward tick (calendar-scan found the event)
```json
[
 {
  "drain-needs": []
 },
 {
  "countdown": []
 },
 {
  "calendar-scan": 1
 },
 {
  "source-confidence": {
   "adjusted": []
  }
 },
 {
  "compact-check": "under-budget"
 }
]
```

## persona presents it (evidence preserved in ledger)
```json
{
 "kind": "persona",
 "personaId": "persona-5826e68b65be",
 "name": "Cartographer",
 "text": "Herald of the calendar: 'dentist appointment' is within your next day — the ledger holds it as source evidence, not my opinion.",
 "cause": "steward-opportunity",
 "imitation": false,
 "mark": null,
 "color": "#09efe6",
 "at": 1795067899725,
 "engine": "unknown"
}
```

## drain/calendar assertions
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

## composition engine used
```json
{
 "text": "I shall commit the event to cartographic record, noting the location and anticipated timeline of this gathering. As cartographer, I will ensure the ledger's spatial maps accurately reflect the community's events, providing a visual testament to our shared experiences and the ebb and flow of our collective life.",
 "engine": "ollama:llama3.2:latest",
 "stub": false
}
```