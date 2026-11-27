# harness-display.pyw — native window for the harness status display.
# Hosts the static shell (C:\builds\index.html fleet index; links down to each
# project's display/) inside Edge WebView2 via pywebview, so the display runs
# as its own executable window instead of a browser tab. Exposes
# window.pywebview.api.launch(project) to the page: resolves the project's
# latest build + emitted launcher artifact from display\data.js and starts it
# in a new console window. Paths validated to stay under the builds root.
#
# Run:  pythonw harness-display.pyw
import json, os, re, subprocess
import webview

ROOT = os.environ.get("HARNESS_BUILD_ROOT", r"C:\builds")
INDEX = os.path.join(ROOT, "index.html")

def resolve(project):
    proj_dir = os.path.normpath(os.path.join(ROOT, project))
    if not proj_dir.startswith(os.path.normpath(ROOT) + os.sep):
        return None, "project escapes root"
    data_js = os.path.join(proj_dir, "display", "data.js")
    if not os.path.isfile(data_js):
        return None, "no display/data.js for project " + project
    raw = open(data_js, encoding="utf-8").read()
    payload = raw.split("=", 1)[1].strip().rstrip(";")
    p = json.loads(payload)["project"]
    build = p.get("latest_build")
    if not build:
        return None, "no latest_build in payload"
    launcher = None
    for b in p.get("builds", []):
        if b.get("folder") == build:
            launcher = b.get("launcher")
    if not launcher:
        return None, "no launcher artifact recorded for " + build
    lpath = os.path.normpath(os.path.join(proj_dir, build, launcher))
    if not lpath.startswith(proj_dir + os.sep) or not re.search(r"\.(cmd|bat|ps1|exe|py)$", lpath, re.I):
        return None, "launcher path rejected: " + lpath
    if not os.path.isfile(lpath):
        return None, "launcher missing on disk: " + lpath
    return (build, lpath), None

class Api:
    def launch(self, project):
        res, err = resolve(project)
        if err:
            return {"ok": False, "error": err}
        build, lpath = res
        flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
        proc = subprocess.Popen([lpath], cwd=os.path.dirname(lpath),
                                creationflags=flags, shell=False)
        return {"ok": True, "project": project, "build": build,
                "launcher": lpath, "pid": proc.pid}

if __name__ == "__main__":
    if not os.path.isfile(INDEX):
        raise SystemExit("no fleet index at " + INDEX + " — run harness-emit.ps1 first")
    api = Api()
    webview.create_window("harness — " + ROOT,
                          "file:///" + INDEX.replace(os.sep, "/"),
                          js_api=api, width=1280, height=860)
    webview.start()
