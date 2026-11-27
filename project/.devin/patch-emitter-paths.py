p = r"C:\builds\harness-ui\version 0.1.0.001\emitter\harness-emit.ps1"
t = open(p, encoding="utf-8").read()

# 1) add Parse-Paths + Parse-ModuleTable after Parse-ScenarioSuite
anchor1 = """            $exists = $false
            foreach ($s in $out) { if ($s.id -eq $sid) { $exists = $true; break } }
            if (-not $exists) { [void]$out.Add(@{ id = $sid; title = ($title -replace '\\*\\*','') }) }
        }
    }
    return $out
}
"""
add1 = anchor1 + """
function Parse-Paths([string]$path) {
    # '## Paths' rows: | P-foo | journey | a.b -> c.d | S-x, S-y |
    $out = New-Object System.Collections.ArrayList
    if (-not (Test-Path $path)) { return $out }
    $inPaths = $false
    foreach ($line in (Get-Content -LiteralPath $path -Encoding UTF8)) {
        if ($line -match '^##\\s+Paths') { $inPaths = $true; continue }
        if ($inPaths -and $line -match '^##\\s') { break }
        if (-not $inPaths) { continue }
        if ($line -match '^\\|\\s*(P-[A-Za-z0-9_-]+)\\s*\\|\\s*(.*?)\\s*\\|\\s*(.*?)\\s*\\|\\s*(.*?)\\s*\\|') {
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
        if ($line -match '^##\\s+Modules') { $inMod = $true; continue }
        if ($inMod -and $line -match '^##\\s') { break }
        if (-not $inMod) { continue }
        if ($line -match '^\\|\\s*\\*\\*([A-Za-z0-9_-]+)\\*\\*\\s*\\|') {
            $name = $Matches[1]
            $cells = @($line -split '\\|')
            $surface = if ($cells.Count -ge 5) { $cells[4].Trim() } else { '' }
            $hasSurface = ($surface -and $surface -notmatch '^\\s*(none|[\\u2014-])')
            $out[$name] = @{ row_text = $line; surface = $surface; has_surface = $hasSurface }
        }
    }
    return $out
}
"""
assert anchor1 in t, "anchor1 (Parse-ScenarioSuite end) not found"
t = t.replace(anchor1, add1, 1)

# 2) gap-sign computation after suite parse
anchor2 = """    $suite = Parse-ScenarioSuite $scenPath
    Write-Log ("    scenarios.md: {0} ids" -f $(if (Test-Path $scenPath) { $suite.Count } else { 'MISSING -> gap' }))
"""
add2 = anchor2 + """
    # --- pathed scenarios + gap signs (pathed-scenarios.md) ---
    $paths = Parse-Paths $scenPath
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
            $parts = $st -split '\\.', 2
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
"""
assert anchor2 in t, "anchor2 (suite parse) not found"
t = t.replace(anchor2, add2, 1)

# 3) payload field
anchor3 = "            live_scenario_ids = @($suite | ForEach-Object { $_.id })"
assert anchor3 in t, "anchor3 (payload) not found"
t = t.replace(anchor3, anchor3 + "\n            paths = $pathData", 1)

open(p, "w", encoding="utf-8").write(t)
print("emitter patched")
