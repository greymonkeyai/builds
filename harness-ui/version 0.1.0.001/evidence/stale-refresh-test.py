import re, io, subprocess, threading, time, os, sys

ev = r"C:\builds\harness-ui\version 0.1.0.001\evidence"
datajs = r"C:\builds\harness-ui\version 0.1.0.001\fixtures\fleet\stalerig\display\data.js"
orig = io.open(datajs, encoding='utf-8').read()
marker = "STAMP-BUMPED-20261123"

stop = threading.Event()
def bumper():
    # Continuously rewrite data.js with a bumped generated_at + marker so that
    # whenever the page's 30s poll fires, it sees a newer stamp.
    while not stop.is_set():
        t = io.open(datajs, encoding='utf-8').read()
        t2 = re.sub(r'"generated_at":\s*"[^"]*"', '"generated_at": "2099-01-01T00:00:00Z"', t)
        if marker not in t2:
            t2 = t2.replace('window.HARNESS_DATA = {', 'window.HARNESS_DATA = {"marker": "%s",' % marker, 1)
        if t2 != t:
            io.open(datajs, 'w', encoding='utf-8').write(t2)
        time.sleep(0.2)

th = threading.Thread(target=bumper); th.start()
time.sleep(0.5)

chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
url = "file:///C:/builds/harness-ui/version%200.1.0.001/fixtures/fleet/stalerig/display/index.html"
out = subprocess.run([chrome, "--headless", "--disable-gpu", "--no-first-run",
                      "--user-data-dir=C:/Windows/Temp/chromeprof2",
                      "--virtual-time-budget=90000",
                      "--dump-dom", url],
                     capture_output=True, text=True, timeout=120)
stop.set(); th.join()
io.open(ev + r"\dom-fx-stale-refresh.html", "w", encoding='utf-8').write(out.stdout)

dom = out.stdout
print("dom bytes:", len(dom))
print("marker in dom:", marker in dom)
print("stamp in dom:", "2099-01-01" in dom)
m = re.search(r'data-polls="(\d+)"', dom)
print("polls:", m.group(1) if m else "none")
m = re.search(r'data-stamp="([^"]+)"', dom)
print("rendered stamp:", m.group(1) if m else "none")

# restore original payload
io.open(datajs, 'w', encoding='utf-8').write(orig)
print("data.js restored")
