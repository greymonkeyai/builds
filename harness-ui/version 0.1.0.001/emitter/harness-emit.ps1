<#
.SYNOPSIS
  harness-ui emitter — scans a builds root and emits the read-only status display.

.DESCRIPTION
  Discovers project folders (directories carrying `.devin/` + `devlog.md`), derives
  per-project payloads from harness artifacts (devlog.md verdict blocks, .devin/
  state.json, .devin/scenarios.md, .devin/last-*-status.txt, version folders,
  FEATURES.md convention tables), and emits:

    <root>/index.html  <root>/data.js  <root>/harness.js  <root>/styles.css
    <project>/display/index.html|harness.js|styles.css|data.js

  Writes ONLY emitted artifacts plus its own run log. Never modifies devlog.md,
  state.json, or any other project file.

.PARAMETER Root
  Builds root to scan. Default C:\builds.

.PARAMETER Once
  Run a single scan and exit (default when -Watch is not given).

.PARAMETER Watch
  Loop, rescanning every N seconds. `-Watch 0` (or no argument value that parses
  to 0) uses the 30-second default.

.PARAMETER CorpusRoot
  Spec corpus root used to locate CONVENTIONS.md for the current-state live read
  when a project's prompt.md does not name a corpus file. Default C:\Project.

.PARAMETER ShellDir
  Directory holding the shell template files (index.html, harness.js, styles.css).
  Defaults to ..\shell relative to this script.

.PARAMETER LogFile
  Path of the emitter run log. Defaults to a timestamped file next to the script's
  ..\evidence directory when present, else alongside the script.
#>
[CmdletBinding()]
param(
    [string]$Root = 'C:\builds',
    [switch]$Once,
    [int]$Watch = -1,
    [string]$CorpusRoot = 'C:\Project',
    [string]$ShellDir = '',
    [string]$LogFile = ''
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ShellDir) { $ShellDir = Join-Path $scriptDir '..\shell' }
$ShellDir = [IO.Path]::GetFullPath($ShellDir)
$Root = [IO.Path]::GetFullPath($Root)

if (-not $LogFile) {
    $evDir = Join-Path $scriptDir '..\evidence'
    if (Test-Path $evDir) {
        $LogFile = Join-Path $evDir ('scan-{0}.log' -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
    } else {
        $LogFile = Join-Path $scriptDir ('scan-{0}.log' -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
    }
}
$LogFile = [IO.Path]::GetFullPath($LogFile)

$script:Log = New-Object System.Collections.ArrayList
function Write-Log([string]$msg) {
    $line = '{0} {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg
    [void]$script:Log.Add($line)
    Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8
    Write-Host $line
}
function Save-Log {
    $script:Log | Out-File -LiteralPath $LogFile -Encoding utf8
}

# ---------------- derivation helpers ----------------

function Get-Field($obj, [string]$name) {
    # StrictMode-safe property read: $null when missing on a PSCustomObject;
    # dictionary keys also resolve through this.
    if ($null -eq $obj) { return $null }
    if ($obj -is [System.Collections.IDictionary]) {
        if ($obj.Contains($name)) { return $obj[$name] }
        return $null
    }
    $prop = $obj.PSObject.Properties[$name]
    if ($prop) { return $prop.Value } else { return $null }
}

function Get-NewestInScopeMtime([string]$dir) {
    # Newest file mtime under $dir, excluding top-level display/, .devin/, .git/.
    $newest = $null; $newestRel = $null
    $stack = New-Object System.Collections.Stack
    $stack.Push($dir)
    while ($stack.Count -gt 0) {
        $d = $stack.Pop()
        $files = @()
        try { $files = [IO.Directory]::EnumerateFiles($d) } catch { }
        foreach ($f in $files) {
            $fi = [IO.FileInfo]$f
            if ($LogFile -and $fi.FullName -eq $LogFile) { continue }
            if ($null -eq $newest -or $fi.LastWriteTimeUtc -gt $newest) {
                $newest = $fi.LastWriteTimeUtc
                $newestRel = $f.Substring($dir.Length).TrimStart('\','/')
            }
        }
        $subs = @()
        try { $subs = [IO.Directory]::EnumerateDirectories($d) } catch { }
        foreach ($s in $subs) {
            $name = [IO.Path]::GetFileName($s)
            if ($d -eq $dir -and ($name -eq 'display' -or $name -eq '.devin' -or $name -eq '.git')) { continue }
            $stack.Push($s)
        }
    }
    return @{ newest = $newest; rel = $newestRel }
}

function Parse-Devlog([string]$path) {
    # Returns entries: heading, kind (cycle|reference), bullets, verdicts[{kind,json,ok,error}]
    $entries = New-Object System.Collections.ArrayList
    $cur = $null
    $inFence = $false; $fenceText = ''
    $pendingKind = 'verdict'
    $lastKey = $null
    $nFencesParsed = 0; $nFencesFailed = 0
    foreach ($line in (Get-Content -LiteralPath $path -Encoding UTF8)) {
        if ($inFence) {
            if ($line -match '^\s*```\s*$') {
                $inFence = $false
                $v = $null; $err = $null
                try { $v = ($fenceText | ConvertFrom-Json) } catch { $err = $_.Exception.Message }
                if ($null -ne $v) { $nFencesParsed++ } else { $nFencesFailed++ }
                if ($null -ne $cur) {
                    [void]$cur.verdicts.Add(@{ kind = $pendingKind; json = $v; raw = $fenceText.TrimEnd(); ok = ($null -ne $v); error = $err })
                }
                continue
            }
            $fenceText += $line + "`n"
            continue
        }
        if ($line -match '^\s*```json\s*$') { $inFence = $true; $fenceText = ''; continue }
        if ($line -match '^##\s') { $cur = $null; $script:section = $line; continue }
        if ($line -match '^###\s+(.+?)\s*$') {
            $headText = $Matches[1]
            $kind = 'cycle'
            if ($headText -match '^version\s') { $kind = 'reference' }
            $cur = [pscustomobject]@{
                heading = $headText; kind = $kind
                bullets = [ordered]@{}; verdicts = (New-Object System.Collections.ArrayList)
            }
            [void]$entries.Add($cur)
            $pendingKind = 'verdict'; $lastKey = $null
            continue
        }
        if ($null -eq $cur) { continue }
        if ($line -match 'Re-score\s+verdict') { $pendingKind = 'rescore' }
        elseif ($line -match '\*\*Verdict') { $pendingKind = 'verdict' }
        if ($line -match '^- \*\*([^:*]+):\*\*\s*(.*)$') {
            $lastKey = $Matches[1].Trim()
            $cur.bullets[$lastKey] = $Matches[2].Trim()
        } elseif ($lastKey -and $line -match '^\s+\S') {
            $cur.bullets[$lastKey] = ($cur.bullets[$lastKey] + ' ' + $line.Trim())
        }
    }
    return @{ entries = $entries; parsed = $nFencesParsed; failed = $nFencesFailed }
}

function Parse-ConventionTable([string]$featuresPath, [System.Collections.ArrayList]$ids) {
    # Rows like: | C-Foo | conform — note | or | C-Foo | challenge (recorded) | note |
    $cells = @{}
    if (-not (Test-Path $featuresPath)) { return $cells }
    foreach ($line in (Get-Content -LiteralPath $featuresPath -Encoding UTF8)) {
        if ($line -match '^\|\s*(C-[A-Za-z0-9_-]+)\s*\|\s*(.+)$') {
            $cid = $Matches[1]
            if ($cid -match '^(C-\\|C-\*)') { continue }
            $rest = $Matches[2]
            $disp = ($rest -split '\|')[0].Trim()
            $d = $disp.ToLower()
            $status = 'recorded'
            if ($d -match 'silent') { $status = 'silent-departure' }
            elseif ($d -match 'challenge|depart|deviat') { $status = 'reckoned-departure' }
            elseif ($d -match '^(conform|conformed)') { $status = 'conformed' }
            if ($cid -match '^C-[A-Z]') {
                $cells[$cid] = @{ status = $status; disposition = $disp }
                if (-not $ids.Contains($cid)) { [void]$ids.Add($cid) }
            }
        }
    }
    return $cells
}

function Parse-ScenarioSuite([string]$path) {
    # | S-foo | text | ... |  -> ordered unique ids + titles
    $out = New-Object System.Collections.ArrayList
    if (-not (Test-Path $path)) { return $out }
    foreach ($line in (Get-Content -LiteralPath $path -Encoding UTF8)) {
        if ($line -match '^\|\s*(S-[A-Za-z0-9_-]+)\s*\|\s*(.+?)\s*\|') {
            $sid = $Matches[1]; $title = $Matches[2]
            $exists = $false
            foreach ($s in $out) { if ($s.id -eq $sid) { $exists = $true; break } }
            if (-not $exists) { [void]$out.Add(@{ id = $sid; title = ($title -replace '\*\*','') }) }
        }
    }
    return $out
}

function Parse-Paths([string]$path) {
    # '## Paths' rows: | P-foo | journey | a.b -> c.d | S-x, S-y |
    $out = New-Object System.Collections.ArrayList
    if (-not (Test-Path $path)) { return $out }
    $inPaths = $false
    foreach ($line in (Get-Content -LiteralPath $path -Encoding UTF8)) {
        if ($line -match '^##\s+Paths') { $inPaths = $true; continue }
        if ($inPaths -and $line -match '^##\s') { break }
        if (-not $inPaths) { continue }
        if ($line -match '^\|\s*(P-[A-Za-z0-9_-]+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|') {
            $steps = @($Matches[3] -split ([char]0x2192) | ForEach-Object { $_.Trim() } | Where-Object { $_ })
            $enacts = @($Matches[4] -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
            [void]$out.Add(@{ id = $Matches[1]; journey = $Matches[2]; steps = $steps; enacts = $enacts })
        }
    }
    return $out
}

function Parse-ModuleTable([string]$projDir) {
    # impl-design-*.md '## Modules' rows: | **name** | owns | scenarios | surface | deps |
    $out = @{}
    $file = Get-ChildItem -LiteralPath $projDir -Filter 'impl-design-*.md' -ErrorAction SilentlyContinue |
            Sort-Object Name | Select-Object -First 1
    if (-not $file) { return $out }
    $inMod = $false
    foreach ($line in (Get-Content -LiteralPath $file.FullName -Encoding UTF8)) {
        if ($line -match '^##\s+Modules') { $inMod = $true; continue }
        if ($inMod -and $line -match '^##\s') { break }
        if (-not $inMod) { continue }
        if ($line -match '^\|\s*\*\*([A-Za-z0-9_-]+)\*\*\s*\|') {
            $name = $Matches[1]
            $cells = @($line -split '\|')
            $surface = if ($cells.Count -ge 5) { $cells[4].Trim() } else { '' }
            $hasSurface = ($surface -and $surface -notmatch '^\s*(none|[\u2014-])')
            $out[$name] = @{ row_text = $line; surface = $surface; has_surface = $hasSurface }
        }
    }
    return $out
}

function Get-ConventionIdsFromFile([string]$path, [System.Collections.ArrayList]$ids) {
    if (-not (Test-Path $path)) { return }
    $text = Get-Content -LiteralPath $path -Raw -Encoding UTF8
    foreach ($m in [regex]::Matches($text, '\|\s*(C-[A-Z][A-Za-z0-9]+)\s*\|')) {
        $cid = $m.Groups[1].Value
        if (-not $ids.Contains($cid)) { [void]$ids.Add($cid) }
    }
}

function Parse-DocRegister([string]$projRoot) {
    # Derivative-doc register: scans top-level *.md for <!-- harness-doc ... -->
    # headers (workflow.md §Derivative documents). Read-only — derives the same
    # shape .devin/register-scan.ps1 emits, without requiring register.json.
    $terminal = @('superseded','rejected','discharged','adopted-upstream')
    $docs = New-Object System.Collections.ArrayList
    $headerless = New-Object System.Collections.ArrayList
    foreach ($f in (Get-ChildItem -LiteralPath $projRoot -Filter '*.md' -File -ErrorAction SilentlyContinue)) {
        if (@('AGENTS.md','README.md') -contains $f.Name) { continue }
        $head = (Get-Content -LiteralPath $f.FullName -TotalCount 15 -ErrorAction SilentlyContinue) -join ' '
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
        # body: full text minus the harness-doc header line, capped — approval
        # review needs the wording, not just the status.
        $body = $head -join "`n"
        $raw = Get-Content -LiteralPath $f.FullName -Raw -Encoding UTF8
        if ($raw) {
            $body = (($raw -split "`r?`n") | Where-Object { $_ -notmatch 'harness-doc' }) -join "`n"
            if ($body.Length -gt 120000) { $body = $body.Substring(0, 120000) + "`n... [truncated at 120KB]" }
        }
        $doc['body'] = $body
        [void]$docs.Add($doc)
    }
    $current = [ordered]@{}
    foreach ($d in $docs) {
        if ($terminal -contains (Get-Field $d 'status')) { continue }
        $n = 0
        if ($d.id -match '(\d+)\s*$') { $n = [int]$Matches[1] }
        $k = Get-Field $d 'kind'
        if (-not $current.Contains($k) -or $n -ge $current[$k].n) { $current[$k] = @{ n = $n; id = $d.id } }
    }
    $currentIds = [ordered]@{}
    foreach ($k in $current.Keys) { $currentIds[$k] = $current[$k].id }
    return [ordered]@{
        docs = @($docs)
        current = $currentIds
        pending = @($docs | Where-Object { @('draft','proposed') -contains (Get-Field $_ 'status') } | ForEach-Object { $_.id })
        in_force = @($docs | Where-Object { (Get-Field $_ 'status') -eq 'in-force' } | ForEach-Object { $_.id })
        provisional_ids = @($docs | Where-Object { (Get-Field $_ 'provisional_ids') -eq $true } | ForEach-Object { $_.id })
        headerless = @($headerless)
    }
}

# ---------------- per-project derivation ----------------

function Build-ProjectData($projDir, $scanUtc) {
    $name = $projDir.Name
    $devlogPath = Join-Path $projDir.FullName 'devlog.md'
    $devinDir = Join-Path $projDir.FullName '.devin'
    Write-Log ("  parsing {0}\devlog.md" -f $name)

    $dev = Parse-Devlog $devlogPath
    Write-Log ("    entries: {0}; verdict json blocks parsed: {1}; failed: {2}" -f $dev.entries.Count, $dev.parsed, $dev.failed)

    # --- state.json ---
    $statePath = Join-Path $devinDir 'state.json'
    $statePresent = Test-Path $statePath
    $state = $null; $stateError = $null
    if ($statePresent) {
        try { $state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json }
        catch { $stateError = ('unparsed: ' + $_.Exception.Message) }
    } else { $stateError = 'missing' }
    Write-Log ("    state.json: {0}" -f $(if ($statePresent) { if ($stateError) { $stateError } else { 'parsed' } } else { 'MISSING -> gap' }))

    # --- scenario suite ---
    $scenPath = Join-Path $devinDir 'scenarios.md'
    if (-not (Test-Path $scenPath)) { $scenPath = Join-Path $projDir.FullName 'scenarios.md' }
    $suite = Parse-ScenarioSuite $scenPath
    Write-Log ("    scenarios.md: {0} ids" -f $(if (Test-Path $scenPath) { $suite.Count } else { 'MISSING -> gap' }))

    # --- pathed scenarios + gap signs (pathed-scenarios.md) ---
    $paths = @(Parse-Paths $scenPath)
    $modules = Parse-ModuleTable $projDir.FullName
    $enacted = @{}
    foreach ($pp in $paths) { foreach ($sid in $pp.enacts) { $enacted[$sid] = $true } }
    $suiteIds = @($suite | ForEach-Object { $_.id })
    $unconsol = @($suiteIds | Where-Object { -not $enacted.ContainsKey($_) })
    $unknownRefs = @($enacted.Keys | Where-Object { $suiteIds -notcontains $_ })
    $undeclared = New-Object System.Collections.ArrayList
    $touchedMods = @{}
    foreach ($pp in $paths) {
        foreach ($st in $pp.steps) {
            $parts = $st -split '\.', 2
            if ($parts.Count -lt 2) { [void]$undeclared.Add(@{ path = $pp.id; item = $st; kind = 'malformed' }); continue }
            $mname = $parts[0]; $aname = $parts[1]
            if (-not $modules.ContainsKey($mname)) { [void]$undeclared.Add(@{ path = $pp.id; item = $st; kind = 'unknown-module' }); continue }
            $touchedMods[$mname] = $true
            if ($modules[$mname].row_text -notmatch [regex]::Escape($aname)) { [void]$undeclared.Add(@{ path = $pp.id; item = $st; kind = 'undeclared-affordance' }) }
        }
    }
    $unreachable = @($modules.Keys | Where-Object { $modules[$_].has_surface -and -not $touchedMods.ContainsKey($_) })
    $pathData = [ordered]@{
        n_paths = $paths.Count
        declared = @($paths)
        consolidated = ($suiteIds.Count - $unconsol.Count)
        suite_n = $suiteIds.Count
        unconsolidated = @($unconsol)
        unknown_refs = @($unknownRefs)
        undeclared_items = @($undeclared)
        unreachable_modules = @($unreachable)
    }
    Write-Log ("    paths: {0}; consolidated {1}/{2}; unconsol {3}; undeclared {4}; unreachable-mods {5}" -f $paths.Count, $pathData.consolidated, $suiteIds.Count, $unconsol.Count, $undeclared.Count, $unreachable.Count)

    # --- last status files ---
    $statusFiles = [ordered]@{}
    foreach ($sf in (Get-ChildItem -LiteralPath $devinDir -Filter 'last-*-status.txt' -File -ErrorAction SilentlyContinue)) {
        $statusFiles[$sf.Name] = (Get-Content -LiteralPath $sf.FullName -Raw -Encoding UTF8)
    }
    Write-Log ("    last-*-status.txt: {0} file(s)" -f $statusFiles.Count)

    # --- derivative doc register (harness-doc headers on top-level *.md) ---
    $register = Parse-DocRegister $projDir.FullName
    Write-Log ("    register: {0} docs; pending {1}; in-force {2}; headerless {3}" -f $register.docs.Count, $register.pending.Count, $register.in_force.Count, $register.headerless.Count)

    # --- raw jev fallback: jev-cycle-*.out verdict blocks not already in devlog ---
    # (devlog is primary; .out files are consulted only when a cycle entry has no parsed verdict)

    # --- builds / version folders ---
    $builds = New-Object System.Collections.ArrayList
    $convIds = New-Object System.Collections.ArrayList
    foreach ($bdir in (Get-ChildItem -LiteralPath $projDir.FullName -Directory -Filter 'version *' -ErrorAction SilentlyContinue)) {
        $launcher = $null
        foreach ($cand in @('launch.cmd','LAUNCH.md','launch.ps1','launch.bat','launch.sh')) {
            $p = Join-Path $bdir.FullName $cand
            if (Test-Path $p) { $launcher = $cand; break }
        }
        $convCells = Parse-ConventionTable (Join-Path $bdir.FullName 'FEATURES.md') $convIds
        $vkey = $null
        $vm = [regex]::Match($bdir.Name, '(\d+\.\d+\.\d+\.\d+)')
        if ($vm.Success) { try { $vkey = [version]$vm.Groups[1].Value } catch { $vkey = $null } }
        [void]$builds.Add([ordered]@{
            folder = $bdir.Name
            mtime  = $bdir.LastWriteTimeUtc.ToString('o')
            vkey   = $(if ($vkey) { $vkey.ToString() } else { $null })
            launcher = $launcher
            conventions = $convCells
        })
    }
    $buildsSorted = @($builds | Sort-Object {
        if ($_.vkey) { [version]$_.vkey } else { [version]'0.0.0.0' }
    }, { $_.mtime })
    $latestBuild = if ($buildsSorted.Count -gt 0) { $buildsSorted[-1] } else { $null }
    Write-Log ("    version folders: {0}; latest: {1}" -f $builds.Count, $(if ($latestBuild) { $latestBuild.folder } else { 'none' }))

    # --- verdicts -> normalized series ---
    $series = New-Object System.Collections.ArrayList
    $cycleIdx = 0
    foreach ($e in $dev.entries) {
        $label = $e.heading
        if ($e.heading -match 'version\s+([0-9][0-9.]*)') { $label = 'v' + $Matches[1] }
        if ($e.heading -match 'Cycle\s+(\d+)') { $cycleIdx = [int]$Matches[1]; $label = 'C' + $cycleIdx }
        $date = $null
        if ($e.heading -match '(\d{4}-\d{2}-\d{2})') { $date = $Matches[1] }
        $vnum = 0
        foreach ($v in $e.verdicts) {
            $vnum++
            $vlabel = $label
            if ($v.kind -eq 'rescore') { $vlabel = $label + '-rescore' }
            elseif ($e.verdicts.Count -gt 1 -and $vnum -gt 1) { $vlabel = "$label.$vnum" }
            $buildFolder = $null
            if ($e.bullets.Contains('Result')) {
                $m = [regex]::Match($e.bullets['Result'], 'version\s+(\d+\.\d+\.\d+\.\d+)')
                if ($m.Success) { $buildFolder = 'version ' + $m.Groups[1].Value }
            }
            [void]$series.Add([ordered]@{
                label = $vlabel; entry = $e.heading; kind = $e.kind; verdict_kind = $v.kind
                date = $date
                direction  = $(if ($e.bullets.Contains('Direction')) { $e.bullets['Direction'] } else { $null })
                baseline   = $(if ($e.bullets.Contains('Baseline')) { $e.bullets['Baseline'] } else { $null })
                criteria   = $(if ($e.bullets.Contains('Criteria')) { $e.bullets['Criteria'] } elseif ($e.bullets.Contains('Criteria (rubric revision)')) { $e.bullets['Criteria (rubric revision)'] } else { $null })
                time_to_implement = $(if ($e.bullets.Contains('Time to implement')) { $e.bullets['Time to implement'] } else { $null })
                calendar_span = $(if ($e.bullets.Contains('Calendar span')) { $e.bullets['Calendar span'] } else { $null })
                llm_build_time = $(if ($e.bullets.Contains('LLM build time')) { $e.bullets['LLM build time'] } else { $null })
                result     = $(if ($e.bullets.Contains('Result')) { $e.bullets['Result'] } else { $null })
                build_folder = $buildFolder
                verdict_ok = $v.ok; verdict_error = $v.error; verdict = $v.json; verdict_raw = $v.raw
            })
        }
        if ($e.verdicts.Count -eq 0) {
            # entry with no parsed verdict: jev-cycle-*.out fallback for cycle entries
            if ($e.kind -eq 'cycle' -and $e.heading -match 'Cycle\s+(\d+)') {
                $outFile = Join-Path $devinDir ('jev-cycle-{0:d3}.out' -f [int]$Matches[1])
                if (Test-Path $outFile) {
                    $raw = Get-Content -LiteralPath $outFile -Raw -Encoding UTF8
                    $jblocks = [regex]::Matches($raw, '(?s)```json\s*(.+?)\s*```')
                    if ($jblocks.Count -gt 0) {
                        $tryJson = $jblocks[$jblocks.Count-1].Groups[1].Value
                        $v = $null
                        try { $v = $tryJson | ConvertFrom-Json } catch { }
                        if ($null -ne $v) {
                            [void]$series.Add([ordered]@{
                                label = $label; entry = $e.heading; kind = 'cycle'; verdict_kind = 'verdict-out'
                                date = $date; direction = $null; baseline = $null; criteria = $null
                                time_to_implement = $null; result = $null; build_folder = $null
                                verdict_ok = $true; verdict_error = $null; verdict = $v; verdict_raw = $tryJson.Trim(); source = ".devin/$([IO.Path]::GetFileName($outFile))"
                            })
                            Write-Log ("    {0}: no devlog verdict -> used {1}" -f $label, [IO.Path]::GetFileName($outFile))
                        }
                    }
                }
            }
        }
    }
    Write-Log ("    verdict series points: {0}" -f $series.Count)

    # --- liveness ---
    $lv = Get-NewestInScopeMtime $projDir.FullName
    $livenessSec = $null
    if ($null -ne $lv.newest) { $livenessSec = [int][math]::Round(($scanUtc - $lv.newest).TotalSeconds) }
    Write-Log ("    liveness: newest in-scope mtime {0} ({1}); age {2}s" -f $(if ($lv.newest) { $lv.newest.ToString('o') } else { 'none' }), $lv.rel, $livenessSec)

    # --- current state: live corpus read ---
    $promptPath = Join-Path $projDir.FullName 'prompt.md'
    $corpusFile = $null; $promptDeclared = $null; $promptRev = $null
    if (Test-Path $promptPath) {
        $promptText = Get-Content -LiteralPath $promptPath -Raw -Encoding UTF8
        $mRev = [regex]::Match($promptText, 'revision\s+(\d{4}-\d{2}-\d{2})')
        if ($mRev.Success) { $promptRev = $mRev.Groups[1].Value }
        $mTk = [regex]::Match($promptText, 'taken\s+(\d{4}-\d{2}-\d{2})')
        if (-not $promptRev -and $mTk.Success) { $promptRev = 'snapshot taken ' + $mTk.Groups[1].Value }
        foreach ($pm in [regex]::Matches($promptText, '([A-Za-z]:\\[^\r\n``"'']+?\.(?:md|txt))')) {
            $cand = $pm.Groups[1].Value.TrimEnd('.,)')
            if (Test-Path $cand) { $corpusFile = $cand; break }
        }
    }
    $corpusConvFile = $null; $corpusConvSource = $null
    if ($corpusFile) {
        $cDir = Split-Path -Parent $corpusFile
        for ($i = 0; $i -lt 3 -and -not $corpusConvFile; $i++) {
            $c1 = Join-Path $cDir 'CONVENTIONS.md'
            if (Test-Path $c1) { $corpusConvFile = $c1; $corpusConvSource = 'derived-from-prompt' }
            $parent = Split-Path -Parent $cDir
            if (-not $parent -or $parent -eq $cDir) { break }
            $cDir = $parent
        }
    }
    if (-not $corpusConvFile -and $PSBoundParameters.ContainsKey('CorpusRoot') -and (Test-Path $CorpusRoot)) {
        $found = Get-ChildItem -LiteralPath $CorpusRoot -Recurse -Depth 3 -Filter 'CONVENTIONS.md' -File -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) { $corpusConvFile = $found.FullName; $corpusConvSource = 'corpusroot-param' }
    }
    $corpusIds = New-Object System.Collections.ArrayList
    if ($corpusConvFile) { Get-ConventionIdsFromFile $corpusConvFile $corpusIds }
    foreach ($cid in $corpusIds) { if (-not $convIds.Contains($cid)) { [void]$convIds.Add($cid) } }
    Write-Log ("    corpus: prompt ref {0}; conventions file {1} -> {2} ids" -f $(if ($corpusFile) { $corpusFile } else { 'none derivable' }), $(if ($corpusConvFile) { $corpusConvFile } else { 'none' }), $corpusIds.Count)

    # verdict-declared conventions ids merge into the id set
    foreach ($sp in $series) {
        $vconv = Get-Field $sp.verdict 'conventions'
        if ($vconv) {
            foreach ($cc in $vconv) {
                $ccid = Get-Field $cc 'id'
                if ($ccid -and -not $convIds.Contains($ccid)) { [void]$convIds.Add($ccid) }
            }
        }
        $vscen = Get-Field $sp.verdict 'scenarios'
        if ($vscen) {
            foreach ($sc in $vscen) {
                $scid = Get-Field $sc 'id'
                $has = $false
                foreach ($sx in $suite) { if ($sx.id -eq $scid) { $has = $true } }
                if (-not $has -and $scid) { [void]$suite.Add(@{ id = $scid; title = '(scored; not in suite file)' }) }
            }
        }
    }

    $lastVerdict = $null
    foreach ($sp in $series) { if ($sp.verdict_ok -and $null -ne (Get-Field $sp.verdict 'overall')) { $lastVerdict = $sp } }
    if (-not $lastVerdict -and $series.Count -gt 0) { $lastVerdict = $series[$series.Count-1] }

    return [ordered]@{
        id = $name
        path = $projDir.FullName
        state_present = $statePresent
        state_error = $stateError
        state = $state
        register = $register
        suite = @($suite)
        status_files = $statusFiles
        series = @($series)
        builds = @($builds)
        latest_build = $(if ($latestBuild) { $latestBuild.folder } else { $null })
        liveness_seconds = $livenessSec
        newest_mtime = $(if ($lv.newest) { $lv.newest.ToString('o') } else { $null })
        newest_path = $lv.rel
        last_verdict = $(if ($lastVerdict) { @{ label = $lastVerdict.label; overall = (Get-Field $lastVerdict.verdict 'overall'); judge = (Get-Field $lastVerdict.verdict 'judge_model'); date = $lastVerdict.date } } else { $null })
        convention_ids = @($convIds | Sort-Object)
        current_state = [ordered]@{
            prompt_declared_revision = $promptRev
            corpus_prompt_file = $corpusFile
            corpus_prompt_mtime = $(if ($corpusFile) { (Get-Item -LiteralPath $corpusFile).LastWriteTimeUtc.ToString('o') } else { $null })
            corpus_conventions_file = $corpusConvFile
            corpus_conventions_source = $corpusConvSource
            corpus_convention_ids = @($corpusIds | Sort-Object)
            live_scenario_ids = @($suite | ForEach-Object { $_.id })
            paths = $pathData
            state_revisions = $(Get-Field $state 'revisions')
        }
    }
}

# ---------------- emit ----------------

$script:Inv = [Globalization.CultureInfo]::InvariantCulture
function ConvertTo-JsonText($v) {
    if ($null -eq $v) { return 'null' }
    if ($v -is [bool]) { if ($v) { return 'true' } else { return 'false' } }
    if ($v -is [datetime]) { return '"' + $v.ToUniversalTime().ToString('o') + '"' }
    if ($v -is [string] -or $v -is [char]) { return '"' + (ConvertTo-JsonEscape ([string]$v)) + '"' }
    if ($v -is [double] -or $v -is [single] -or $v -is [decimal]) {
        return $v.ToString('g17', $script:Inv)
    }
    if ($v -is [enum]) { return ([int]$v).ToString($script:Inv) }
    if ($v -is [ValueType]) { return $v.ToString($script:Inv) }
    if ($v -is [System.Collections.IDictionary]) {
        $parts = New-Object System.Collections.ArrayList
        foreach ($k in $v.Keys) {
            [void]$parts.Add(('"' + (ConvertTo-JsonEscape ([string]$k)) + '":' + (ConvertTo-JsonText $v[$k])))
        }
        return '{' + ($parts -join ',') + '}'
    }
    if ($v -is [System.Collections.IEnumerable]) {
        $parts = New-Object System.Collections.ArrayList
        foreach ($item in $v) { [void]$parts.Add((ConvertTo-JsonText $item)) }
        return '[' + ($parts -join ',') + ']'
    }
    $parts = New-Object System.Collections.ArrayList
    foreach ($pp in $v.PSObject.Properties) {
        [void]$parts.Add(('"' + (ConvertTo-JsonEscape $pp.Name)) + '":' + (ConvertTo-JsonText $pp.Value))
    }
    return '{' + ($parts -join ',') + '}'
}
function ConvertTo-JsonEscape([string]$t) {
        $t = $t.Replace([string]([char]92), [string]([char]92) + [string]([char]92)).Replace('"', [string]([char]92) + '"')
    $t = $t.Replace("`n", '\n').Replace("`r", '\r').Replace("`t", '\t')
    return [regex]::Replace($t, '[\x00-\x08\x0b\x0c\x0e-\x1f]', { param($m) '\u{0:x4}' -f [int][char]$m.Value })
}



function Write-TextFile([string]$path, [string]$content) {
    $dir = Split-Path -Parent $path
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    [IO.File]::WriteAllText($path, $content, (New-Object System.Text.UTF8Encoding($false)))
}

function Invoke-Scan {
    $scanUtc = [DateTime]::UtcNow
    Write-Log ("harness-emit scan — root {0}" -f $Root)
    $shellFiles = @('index.html','harness.js','styles.css')
    foreach ($sf in $shellFiles) {
        if (-not (Test-Path (Join-Path $ShellDir $sf))) { throw "shell template missing: $ShellDir\$sf" }
    }

    $projDirs = Get-ChildItem -LiteralPath $Root -Directory -ErrorAction SilentlyContinue |
        Where-Object { (Test-Path (Join-Path $_.FullName '.devin')) -and (Test-Path (Join-Path $_.FullName 'devlog.md')) }
    Write-Log ("discovered {0} project(s): {1}" -f @($projDirs).Count, (($projDirs | ForEach-Object Name) -join ', '))

    $fleetRows = New-Object System.Collections.ArrayList
    foreach ($pd in $projDirs) {
        Write-Log ("project: {0}" -f $pd.Name)
        $data = Build-ProjectData $pd $scanUtc
        $payload = [ordered]@{
            kind = 'project'
            generated_at = $scanUtc.ToString('o')
            emitter = 'harness-emit.ps1'
            project = $data
        }
        # verdict bodies are injected verbatim (already-valid JSON from the
        # devlog/.out block) — no re-serialization, no lossy round-trip.
        $rawList = New-Object System.Collections.ArrayList
        foreach ($sp in $data.series) {
            if ($sp.Contains('verdict_raw')) {
                if ($sp.verdict_raw) {
                    [void]$rawList.Add($sp.verdict_raw)
                    $sp.verdict = '@@VERDICT_' + $rawList.Count + '@@'
                }
                $sp.Remove('verdict_raw')
            }
        }
        $json = ConvertTo-JsonText $payload
        for ($ri = 0; $ri -lt $rawList.Count; $ri++) {
            $json = $json.Replace('"@@VERDICT_' + ($ri + 1) + '@@"', $rawList[$ri])
        }
        $dispDir = Join-Path $pd.FullName 'display'
        if (-not (Test-Path $dispDir)) { New-Item -ItemType Directory -Path $dispDir -Force | Out-Null }
        foreach ($sf in $shellFiles) {
            Copy-Item -LiteralPath (Join-Path $ShellDir $sf) -Destination (Join-Path $dispDir $sf) -Force
        }
        Write-TextFile (Join-Path $dispDir 'data.js') ('window.HARNESS_DATA = ' + $json + ';')
        Write-Log ("    emitted {0}\display\ (shell + data.js, {1} bytes)" -f $pd.Name, $json.Length)

        [void]$fleetRows.Add([ordered]@{
            id = $pd.Name
            page = ($pd.Name + '/display/index.html')
            line = $(Get-Field $data.state 'line')
            direction = $(Get-Field (Get-Field $data.state 'direction_in_force') 'ref')
            direction_clarity = $(Get-Field (Get-Field $data.state 'direction_in_force') 'clarity')
            budget = $(Get-Field (Get-Field $data.state 'direction_in_force') 'budget')
            docs_pending = $data.register.pending.Count
            docs_pending_ids = @($data.register.pending)
            docs_provisional_ids = @($data.register.provisional_ids)
            docs_in_force = @($data.register.in_force)
            docs_unregistered = @($data.register.headerless)
            last_verdict = $data.last_verdict
            liveness_seconds = $data.liveness_seconds
            newest_mtime = $data.newest_mtime
            last_status = $(if ($data.status_files.Count -gt 0) { ($data.status_files.Values | Select-Object -First 1) } else { $null })
            state_present = $data.state_present
            n_verdicts = $data.series.Count
        })
    }

    $fleet = [ordered]@{
        kind = 'fleet'
        generated_at = $scanUtc.ToString('o')
        emitter = 'harness-emit.ps1'
        root = $Root
        exclusions = 'display/, .devin/ internals, .git/'
        projects = @($fleetRows)
    }
    $fjson = ConvertTo-JsonText $fleet
    foreach ($sf in $shellFiles) {
        Copy-Item -LiteralPath (Join-Path $ShellDir $sf) -Destination (Join-Path $Root $sf) -Force
    }
    Write-TextFile (Join-Path $Root 'data.js') ('window.HARNESS_DATA = ' + $fjson + ';')
    Write-Log ("emitted {0} fleet index + data.js ({1} bytes)" -f $Root, $fjson.Length)
    Save-Log
}

if ($Watch -ge 0) {
    $interval = if ($Watch -eq 0) { 30 } else { $Watch }
    Write-Log ("watch mode: every {0}s (Ctrl+C to stop)" -f $interval)
    while ($true) {
        Invoke-Scan
        Start-Sleep -Seconds $interval
    }
} else {
    Invoke-Scan
}
