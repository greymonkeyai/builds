# Launch — harness-ui 0.1.0.001

The product is a static status display. To launch it:

1. Run the emitter once (or watch) against the builds root:

       powershell -NoProfile -ExecutionPolicy Bypass -File emitter\harness-emit.ps1 -Root C:uilds -Once

       powershell -NoProfile -ExecutionPolicy Bypass -File emitter\harness-emit.ps1 -Root C:uilds -Watch 30

2. Open the emitted pages from the filesystem — no server:

       file:///C:/builds/index.html                     (fleet index)
       file:///C:/builds/project/display/index.html     (project line)
       file:///C:/builds/harness-ui/display/index.html  (this line)

`launch.cmd` performs step 1 for the default root and opens the fleet index.
