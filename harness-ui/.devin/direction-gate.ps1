# Direction gate (UserPromptSubmit): injects the cycle-gate rule into the agent's context.
# Also regenerates .devin/register.json and injects the register digest --
# pending approvals, in-force docs, provisional ids -- so document state is in
# context on every prompt (workflow.md section "Derivative documents").
$gate = 'Cycle gate: clarify the direction sufficiently before building; reject ambiguous directions as inadequate rather than running them.'
$digest = ''
try {
  $scan = Join-Path $PSScriptRoot 'register-scan.ps1'
  if (Test-Path $scan) {
    $digest = (& powershell -NoProfile -File $scan | Select-Object -Last 1)
  }
} catch { $digest = 'register scan failed: ' + $_.Exception.Message }
$ctx = $gate
if ($digest) { $ctx += "`nDocument register digest - " + $digest + "`nRefer to docs by id + status word; statuses: draft | proposed | approved | in-force | discharged | adopted-upstream | superseded | rejected." }
@{
  hookSpecificOutput = @{
    hookEventName    = 'UserPromptSubmit'
    additionalContext = $ctx
  }
} | ConvertTo-Json -Depth 5 -Compress
