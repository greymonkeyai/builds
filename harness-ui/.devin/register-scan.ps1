# register-scan.ps1 -- derives .devin/register.json from harness-doc headers.
#
# Scans top-level *.md files for a header line of the form:
#   <!-- harness-doc kind=shortcomings status=approved since=2026-11-25
#        applies-to=cycle-6 mapped-into=scenarios.md,conventions-004.md -->
# Writes .devin/register.json (docs, current-per-kind, pending, in_force) and
# prints a one-line digest to stdout for the direction gate to inject.
# Read-only except register.json -- never edits the docs it scans.
#
# Usage: powershell -NoProfile -File .devin/register-scan.ps1

$ErrorActionPreference = 'SilentlyContinue'
$root = Split-Path -Parent $PSScriptRoot          # .devin/.. = project folder
$regPath = Join-Path $PSScriptRoot 'register.json'

$terminal = @('superseded','rejected','discharged','adopted-upstream')
$pendingStates = @('draft','proposed')

$docs = New-Object System.Collections.ArrayList
$headerless = New-Object System.Collections.ArrayList
$exempt = @('AGENTS.md','README.md')

foreach ($f in (Get-ChildItem -LiteralPath $root -Filter '*.md' -File)) {
    if ($exempt -contains $f.Name) { continue }
    $head = (Get-Content -LiteralPath $f.FullName -TotalCount 15) -join ' '
    $hdr = $null
    if ($head -match 'harness-doc\s+(.*?)-->') { $hdr = $Matches[1] }
    if ($null -eq $hdr) { [void]$headerless.Add($f.Name); continue }

    $doc = [ordered]@{ id = [IO.Path]::GetFileNameWithoutExtension($f.Name); file = $f.Name }
    foreach ($kv in [regex]::Matches($hdr, '([A-Za-z-]+)=("[^"]*"|\S+)')) {
        $k = $kv.Groups[1].Value -replace '-','_'
        $v = $kv.Groups[2].Value.Trim('"')
        if ($k -eq 'mapped_into' -or $k -eq 'applies_to') {
            $doc[$k] = @($v -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
        } elseif ($v -eq 'true') { $doc[$k] = $true }
        elseif ($v -eq 'false') { $doc[$k] = $false }
        else { $doc[$k] = $v }
    }
    if (-not $doc.Contains('kind'))   { $doc['kind'] = 'unknown' }
    if (-not $doc.Contains('status')) { $doc['status'] = 'unparsed' }
    [void]$docs.Add([pscustomobject]$doc)
}

# current per kind: highest-numbered doc not in a terminal state
$current = [ordered]@{}
foreach ($d in $docs) {
    if ($terminal -contains $d.status) { continue }
    $n = 0
    if ($d.id -match '(\d+)\s*$') { $n = [int]$Matches[1] }
    $k = $d.kind
    if (-not $current.Contains($k) -or $n -ge $current[$k].n) {
        $current[$k] = @{ n = $n; id = $d.id }
    }
}
$currentIds = [ordered]@{}
foreach ($k in $current.Keys) { $currentIds[$k] = $current[$k].id }

$pending  = @($docs | Where-Object { $pendingStates -contains $_.status } | ForEach-Object { $_.id })
$inForce  = @($docs | Where-Object { $_.status -eq 'in-force' } | ForEach-Object { $_.id })
$provisional = @($docs | Where-Object { $_.provisional_ids -eq $true } | ForEach-Object { $_.id })

$register = [ordered]@{
    generated  = (Get-Date).ToUniversalTime().ToString('o')
    root       = $root
    docs       = @($docs)
    current    = $currentIds
    pending    = $pending
    in_force   = $inForce
    provisional_ids = $provisional
    headerless = @($headerless)
}
($register | ConvertTo-Json -Depth 6) | Out-File -LiteralPath $regPath -Encoding utf8

# digest line for the direction gate
$d = 'docs pending approval: ' + $(if ($pending.Count)  { $pending -join ', ' }  else { 'none' })
$d += ' | in force: '           + $(if ($inForce.Count)  { $inForce -join ', ' }  else { 'none' })
if ($provisional.Count) { $d += ' | provisional ids: ' + ($provisional -join ', ') }
if ($headerless.Count)  { $d += ' | UNREGISTERED: '    + ($headerless -join ', ') }
Write-Output $d
