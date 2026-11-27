# launch-serve.py — tiny local launch service for the harness status display.
# The display is a static page; it cannot spawn processes. This service is the
# bridge: GET /launch?project=<id> reads <root>\<id>\display\data.js, resolves
# the project's latest build + its emitted launcher artifact (launch.cmd), and
# starts it in a new console window. Localhost only; paths validated to stay
# under the builds root. GET /status is a liveness probe for the page.
import json, os, re, subprocess, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

ROOT = os.environ.get("HARNESS_BUILD_ROOT", r"C:\builds")
PORT = int(os.environ.get("HARNESS_LAUNCH_PORT", "8358"))

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

class H(BaseHTTPRequestHandler):
    def _out(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/status":
            self._out(200, {"ok": True, "root": ROOT}); return
        if u.path != "/launch":
            self._out(404, {"ok": False, "error": "unknown path"}); return
        project = (parse_qs(u.query).get("project") or [""])[0]
        res, err = resolve(project)
        if err:
            self._out(400, {"ok": False, "error": err}); return
        build, lpath = res
        flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
        proc = subprocess.Popen([lpath], cwd=os.path.dirname(lpath),
                                creationflags=flags, shell=False)
        self._out(200, {"ok": True, "project": project, "build": build,
                        "launcher": lpath, "pid": proc.pid})

    def log_message(self, *a):
        sys.stderr.write("%s  %s\n" % (self.log_date_time_string(), a[0] % a[1:]))

if __name__ == "__main__":
    print("launch-serve on http://127.0.0.1:%d  root=%s" % (PORT, ROOT))
    HTTPServer(("127.0.0.1", PORT), H).serve_forever()
