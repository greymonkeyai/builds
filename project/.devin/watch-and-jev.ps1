# Cycle-7 completion watcher — coordinator-side, detached.
# Polls last-cycle-status.txt until the build driver's end-of-session write lands
# (mtime newer than this script's start), then runs the JEV scoring session via
# the same ACP driver. Logs to jev-cycle-007.watch.log.
$ErrorActionPreference = 'Continue'
$proj   = 'C:\builds\project'
$status = Join-Path $proj '.devin\last-cycle-status.txt'
$wlog   = Join-Path $proj '.devin\jev-cycle-007.watch.log'
$driver = Join-Path $proj '.devin\acp-build-driver.py'
$spawned = Get-Date
$deadline = $spawned.AddHours(7)

function W($m) { Add-Content -Path $wlog -Encoding UTF8 -Value ("{0}  {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m) }

W "watcher start — waiting for last-cycle-status.txt mtime > $spawned"
while ((Get-Date) -lt $deadline) {
    if ((Test-Path $status) -and ((Get-Item $status).LastWriteTime -gt $spawned)) {
        W ("build session ended: " + (Get-Content $status -Raw).Trim())
        Start-Sleep -Seconds 10
        $env:ACP_CWD          = $proj
        $env:ACP_PROMPT_FILE  = Join-Path $proj '.devin\jev-cycle-007.md'
        $env:ACP_LOG          = Join-Path $proj '.devin\jev-cycle-007.acp.log'
        $env:ACP_STATUS_FILE  = Join-Path $proj '.devin\last-jev-status.txt'
        $env:ACP_TIMEOUT      = '7200'
        Remove-Item Env:\ACP_SESSION -ErrorAction SilentlyContinue
        W "spawning JEV (jev-cycle-007.md)"
        python $driver *> (Join-Path $proj '.devin\jev-cycle-007.out')
        W "JEV driver exited — verdict output in jev-cycle-007.out"
        exit 0
    }
    Start-Sleep -Seconds 60
}
W "deadline reached without build completion — no JEV spawned"
exit 1
