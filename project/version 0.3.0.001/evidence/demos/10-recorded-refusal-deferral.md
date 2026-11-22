# Demo 10 — unconfigured nonlocal effect: deferral recorded

## intents detected
```json
[
 {
  "toolId": "send-mail",
  "score": 0.6711,
  "slots": {
   "to": "kris@example.com",
   "body": "the demo"
  },
  "features": {
   "keyword": 0.1111,
   "pattern": 1.0,
   "slot_fill": 1.0,
   "success_rate": 0.5,
   "rank_mult": 1.0,
   "recency": 0.0,
   "source_conf": 1.0
  }
 }
]
```

## fulfill attempt without grant
```json
{
 "ok": false,
 "deferred": true,
 "missing": [
  {
   "slot": "__grant__",
   "minCertainty": 1.0,
   "scope": "mail.send"
  }
 ]
}
```

## need state — open, deferred with status
```json
{
 "status": "open",
 "deferred": {
  "reason": "grant-required",
  "scope": "mail.send"
 }
}
```

Conversational interpretation alone does not send mail; the request resolves to a recorded deferral, not silent non-action.