# Completion gate (Stop): blocks the session from stopping until the cycle entry's
# Result field is filled. Evolved 2026-11-18: the coordinator seeds cycle entries, so
# '### Cycle' presence alone is insufficient. The JEV verdict is recorded afterward by
# a separate session - requiring judge_model here would deadlock the builder.
# Evolved 2026-11-25: also blocks while a top-level *.md lacks a harness-doc
# status header -- unregistered derivative docs surface at creation, not review
# (workflow.md section "Derivative documents").
$devlogOk = (Test-Path devlog.md) -and
    (Select-String -Path devlog.md -Pattern '### Cycle' -Quiet) -and
    -not (Select-String -Path devlog.md -Pattern '\*\*Result:\*\*\s*<pending>' -Quiet)
if (-not $devlogOk) {
  @{ decision = 'block'; reason = 'devlog.md cycle entry still shows Result: <pending> - record what this cycle built (or its failure) before stopping.' } | ConvertTo-Json -Compress
  exit 0
}
$exempt = @('AGENTS.md','README.md')
$missing = @()
foreach ($f in (Get-ChildItem -Path . -Filter '*.md' -File -ErrorAction SilentlyContinue)) {
  if ($exempt -contains $f.Name) { continue }
  $head = (Get-Content -LiteralPath $f.FullName -TotalCount 15 -ErrorAction SilentlyContinue) -join ' '
  if ($head -notmatch 'harness-doc\s+\S') { $missing += $f.Name }
}
if ($missing.Count -gt 0) {
  @{ decision = 'block'; reason = 'unregistered derivative docs - add a <!-- harness-doc kind=... status=... --> header line: ' + ($missing -join ', ') + ' (see C:\Harness\harness\workflow.md, "Derivative documents").' } | ConvertTo-Json -Compress
  exit 0
}
exit 0
