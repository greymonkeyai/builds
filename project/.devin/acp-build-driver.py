# ACP build-session driver — harness realization for `devin -p` equivalents.
# Spawns `devin acp`, authenticates with the stored session token via
# authenticate._meta.api_key, opens a session in CWD, sends the prompt file,
# streams all JSON-RPC traffic to LOG, auto-approves permission requests,
# and serves fs read/write callbacks. Exits when the prompt turn completes.
import subprocess, json, threading, time, sys, os

DEVIN = os.environ.get("DEVIN_BIN",
    r"C:\Users\kris_\AppData\Local\Programs\Devin\resources\app\extensions\windsurf\devin\bin\devin.exe")
CWD = os.environ.get("ACP_CWD", r"C:\builds\project")
PROMPT_FILE = os.environ.get("ACP_PROMPT_FILE", os.path.join(CWD, ".devin", "build-prompt-002.md"))
LOG = os.environ.get("ACP_LOG", os.path.join(CWD, ".devin", "build-cycle-002.acp.log"))
MODE = os.environ.get("ACP_MODE", "bypass")   # Bypass Permissions — disposable build session
TIMEOUT = int(os.environ.get("ACP_TIMEOUT", str(6 * 3600)))
STATUS_FILE = os.environ.get("ACP_STATUS_FILE", os.path.join(CWD, ".devin", "last-cycle-status.txt"))
RESUME = os.environ.get("ACP_SESSION")   # session/load this id instead of session/new

def creds_key():
    t = open(r"C:\Users\kris_\AppData\Roaming\devin\credentials.toml", encoding="utf-8").read()
    return t.split('windsurf_api_key = "', 1)[1].split('"', 1)[0]

prompt = open(PROMPT_FILE, encoding="utf-8").read()

proc = subprocess.Popen([DEVIN, "acp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, cwd=CWD, bufsize=0)

log_lock = threading.Lock()
def log(line):
    with log_lock, open(LOG, "ab") as f:
        f.write(line)

lines = []
def reader():
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        lines.append(line)
        log(line)
threading.Thread(target=reader, daemon=True).start()

_id = [0]
def send(method, params=None):
    _id[0] += 1
    msg = {"jsonrpc": "2.0", "id": _id[0], "method": method}
    if params is not None:
        msg["params"] = params
    proc.stdin.write((json.dumps(msg) + "\n").encode())
    proc.stdin.flush()
    return _id[0]

def respond(rid, result):
    proc.stdin.write((json.dumps({"jsonrpc": "2.0", "id": rid, "result": result}) + "\n").encode())
    proc.stdin.flush()

def respond_err(rid, code, message):
    proc.stdin.write((json.dumps({"jsonrpc": "2.0", "id": rid,
                     "error": {"code": code, "message": message}}) + "\n").encode())
    proc.stdin.flush()

def handle_request(msg):
    m, p = msg["method"], msg.get("params", {})
    if m == "session/request_permission":
        opts = p.get("options", [])
        allow = next((o for o in opts if "always" in o.get("optionId", "")),
                next((o for o in opts if "allow" in o.get("optionId", "")),
                     opts[0] if opts else {"optionId": "allow"}))
        respond(msg["id"], {"outcome": {"outcome": "selected", "optionId": allow["optionId"]}})
    elif m == "fs/read_text_file":
        try:
            respond(msg["id"], {"content": open(p["path"], encoding="utf-8",
                    errors="replace").read()})
        except Exception as e:
            respond_err(msg["id"], -32602, str(e))
    elif m == "fs/write_text_file":
        try:
            os.makedirs(os.path.dirname(p["path"]), exist_ok=True)
            open(p["path"], "w", encoding="utf-8").write(p["content"])
            respond(msg["id"], {})
        except Exception as e:
            respond_err(msg["id"], -32602, str(e))
    else:
        respond(msg["id"], {})

init_id = send("initialize", {"protocolVersion": 1,
    "clientCapabilities": {"fs": {"readTextFile": True, "writeTextFile": True}, "terminal": False}})

session_id = None
prompt_id = None
done = False
end_reason = "timeout"
deadline = time.time() + TIMEOUT

while time.time() < deadline and not done:
    if not proc.poll() is None and not lines:
        end_reason = "process-exit"
        break
    time.sleep(0.25)
    while lines:
        line = lines.pop(0)
        try:
            msg = json.loads(line)
        except Exception:
            continue
        if "method" in msg and "id" in msg:
            handle_request(msg)
            continue
        if "id" not in msg:
            continue
        if msg["id"] == init_id:
            if "error" in msg:
                end_reason = "init-error"; done = True; break
            send("authenticate", {"methodId": "devin-browser",
                                  "_meta": {"api_key": creds_key()}})
        elif session_id is None and msg.get("method") is None:
            pass  # handled below
        if "error" in msg:
            log(("RESPONSE-ERROR " + json.dumps(msg) + "\n").encode())
            if msg["id"] == prompt_id or session_id is None:
                end_reason = "rpc-error"; done = True; break
            continue
        res = msg.get("result")
        if res == {} and session_id is None and msg["id"] == init_id + 1:
            if RESUME:
                send("session/load", {"sessionId": RESUME, "cwd": CWD, "mcpServers": []})
            else:
                send("session/new", {"cwd": CWD, "mcpServers": []})
            continue
        if isinstance(res, dict) and session_id is None and (res.get("sessionId") or RESUME):
            session_id = res.get("sessionId") or RESUME
            try:
                send("session/set_mode", {"sessionId": session_id, "modeId": MODE})
            except Exception:
                pass
            prompt_id = send("session/prompt", {"sessionId": session_id,
                             "prompt": [{"type": "text", "text": prompt}]})
            continue
        if msg["id"] == prompt_id:
            end_reason = "turn-complete"
            done = True
            break

log(("DRIVER-END %s session=%s\n" % (end_reason, session_id)).encode())
try:
    proc.terminate()
except Exception:
    pass

# Owner notification: write a status file and sound the terminal bell audibly, so
# a session end (complete OR given-up) is noticeable away from the chat.
try:
    status = "%s: ACP session ended (%s) session=%s prompt=%s\n%s\n" % (
        time.strftime("%Y-%m-%d %H:%M:%S"), end_reason, session_id,
        os.path.basename(PROMPT_FILE), time.asctime())
    open(STATUS_FILE, "w", encoding="utf-8").write(status)
except Exception:
    pass
try:
    import winsound
    for _ in range(3):
        winsound.Beep(880, 220)
        time.sleep(0.18)
    winsound.MessageBeep(winsound.MB_ICONASTERISK)
except Exception:
    pass
print(end_reason, session_id)
