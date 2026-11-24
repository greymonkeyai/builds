#!/usr/bin/env bash

# Headless DOM dumps for render-check evidence. All file:// — no server.

set -u

EDGE="/c/Program Files/Google/Chrome/Application/chrome.exe"

EV="/c/builds/harness-ui/version 0.1.0.001/evidence"



dump() {  # $1=url $2=outfile $3=extra-flags

  "$EDGE" --headless --disable-gpu --no-first-run ${3:-} --dump-dom "$1" > "$EV/$2" 2>/dev/null

  echo "$2 $(wc -c < "$EV/$2") bytes"

}



# real fleet

dump "file:///C:/builds/index.html" dom-fleet.html

# real project views

dump "file:///C:/builds/project/display/index.html"            dom-proj-summary.html

dump "file:///C:/builds/project/display/index.html#comparison" dom-proj-comparison.html

dump "file:///C:/builds/project/display/index.html#current"    dom-proj-current.html

dump "file:///C:/builds/project/display/index.html#builddetail/6" dom-proj-builddetail.html

# harness-ui own summary (state.json populated)

dump "file:///C:/builds/harness-ui/display/index.html"         dom-harnessui-summary.html

# fixture fleet

FX="file:///C:/builds/harness-ui/version%200.1.0.001/fixtures/fleet"

dump "$FX/index.html"                          dom-fx-fleet.html

dump "$FX/brokenrig/display/index.html"        dom-fx-brokenrig-summary.html

dump "$FX/brokenrig/display/index.html#current" dom-fx-brokenrig-current.html

dump "$FX/stalerig/display/index.html"         dom-fx-stalerig-summary.html

dump "$FX/stalerig/display/index.html#comparison" dom-fx-stalerig-comparison.html

dump "$FX/stalerig/display/index.html#current" dom-fx-stalerig-current.html

