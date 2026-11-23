# Completion gate (Stop): blocks the session from stopping until the cycle entry's
# Result field is filled. The coordinator seeds cycle entries with `Result: <pending>`
# at spawn time, so '### Cycle' presence alone is insufficient. The JEV verdict is
# recorded afterward by a separate session - requiring judge_model here would deadlock
# the builder.
if ((Test-Path devlog.md) -and
    (Select-String -Path devlog.md -Pattern '### Cycle' -Quiet) -and
    -not (Select-String -Path devlog.md -Pattern '\*\*Result:\*\*\s*<pending>' -Quiet)) {
  exit 0
}
@{ decision = 'block'; reason = 'devlog.md cycle entry still shows Result: <pending> - record what this cycle built (or its failure) before stopping.' } | ConvertTo-Json -Compress
