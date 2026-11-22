# Demo 9 — storefront/exchange package import below action threshold

## import result
```json
{
 "ok": true,
 "result": {
  "ok": true,
  "package": "pkg-demo",
  "counts": {
   "assertions": 1,
   "personas": 1,
   "tools": 1,
   "needs": 1
  },
  "threshold": "below-action (0.4 < 0.7)"
 },
 "ms": 4
}
```

## effective confidence of imported assertions
```json
[
 {
  "id": "a-9326b782c7c4",
  "eff": 0.4,
  "claimant": "exchange:pkg-demo"
 }
]
```

Imported material is recorded but capped below the action threshold (0.4 < 0.7) — resolvable through local ledger, capabilities, and permissions (endorse-source raises trust).