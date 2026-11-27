"""Quorum HTTP surface — owner-facing API + UI + SSE + launch hygiene.

Launch hygiene (S-4 bar): the port is PROBED before bind; a stale/prior
Quorum instance owning the port fails the launch honestly (ok:false, no
success-claim); the bind is exclusive (no address reuse); closing the
launcher terminates the process (watchdog on parent liveness).
"""
from __future__ import annotations

import json
import os
import re
import socket
import threading
import time
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

from . import rows, connectors, temporal, artifacts, engines

APP_ID = "quorum-0.3.0.005"
UI_DIR = os.path.join(os.path.dirname(__file__), "ui")


def probe_port(port: int) -> dict:
    """Probe before bind: who owns the port?"""
    try:
        with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/api/honesty", timeout=2) as r:
            d = json.loads(r.read())
        if d.get("app") == APP_ID:
            return {"free": False, "owner": "quorum-instance",
                    "note": "prior Quorum instance owns the port — refusing "
                            "to claim clean launch"}
        return {"free": False, "owner": "foreign", "note": "port occupied "
                "by another service"}
    except Exception:
        pass
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=1)
        s.close()
        return {"free": False, "owner": "unknown"}
    except Exception:
        return {"free": True}


def parent_alive() -> bool:
    try:
        import ctypes
        pid = os.getppid()
        out = __import__("subprocess").run(
            ["tasklist", "/FI", f"PID eq {pid}"], capture_output=True,
            text=True, timeout=10).stdout
        return str(pid) in out
    except Exception:
        return True


def _read_json(handler) -> dict:
    n = int(handler.headers.get("Content-Length", 0) or 0)
    try:
        return json.loads(handler.rfile.read(n) or b"{}")
    except Exception:
        return {}


def make_handler(host, launch_report):
    H = host

    class Q(BaseHTTPRequestHandler):
        def log_message(self, *a):
            launch_report.setdefault("log", []).append(
                " ".join(str(x) for x in a))

        def _send(self, code, body, ctype="application/json"):
            data = body if isinstance(body, bytes) else \
                json.dumps(body, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)

        def _params(self):
            return dict(urllib.parse.parse_qsl(
                urllib.parse.urlparse(self.path).query))

        # ============================================================ GET ==
        def do_GET(self):
            path = urllib.parse.urlparse(self.path).path
            p = self._params()
            if path == "/" or path == "/index.html":
                return self._send(200, open(os.path.join(UI_DIR, "index.html"),
                                            "rb").read(), "text/html")
            if path.startswith("/ui/"):
                ap = os.path.abspath(os.path.join(UI_DIR, path[4:]))
                if not ap.startswith(os.path.abspath(UI_DIR)) \
                        or not os.path.exists(ap):
                    return self._send(404, {"error": "not found"})
                ct = {".js": "text/javascript", ".css": "text/css",
                      ".svg": "image/svg+xml", ".html": "text/html"}.get(
                    os.path.splitext(ap)[1], "application/octet-stream")
                return self._send(200, open(ap, "rb").read(), ct)
            if path == "/api/artifact":
                ap = os.path.abspath(p.get("path", ""))
                if os.path.exists(ap):
                    ext = os.path.splitext(ap)[1].lower()
                    ct = {".bmp": "image/bmp", ".svg": "image/svg+xml",
                          ".json": "application/json"}.get(ext, "text/plain")
                    return self._send(200, open(ap, "rb").read(), ct)
                return self._send(404, {"error": "not found"})
            if path == "/api/honesty":
                return self._send(200, {"app": APP_ID, **H.honesty()})
            if path == "/api/gate":
                g = json.load(open(H.gate_path)) if os.path.exists(H.gate_path) \
                    else {"passed": False}
                return self._send(200, g)
            if path == "/api/state":
                return self._send(200, H.honesty() | {
                    "roster": H.personas.roster(),
                    "needs": H.floor.open_needs(),
                    "topic": H.topic,
                    "surface_role": H.surface_role,
                    "turns": len(H.turns)})
            if path == "/api/roster":
                return self._send(200, {"roster": H.personas.roster(),
                                        "active": H.personas.active})
            if path == "/api/needs":
                return self._send(200, {"open": H.floor.open_needs(),
                                        "count": H.floor.count_open(),
                                        "idlePassAt": H.steward.last_pass_at,
                                        "steward": H.steward.liveness()})
            if path == "/api/holdings":
                return self._send(200, {
                    "personas": H.personas.roster(),
                    "tools": [H.tools.describe(t) for t in H.tools.live],
                    "candidates": H.tools.candidates(),
                    "workshops": H.book.find(predicate="workshop:entry"),
                    "packages": H.book.find(predicate="exchange:imported")})
            if path == "/api/tools":
                return self._send(200, {"tools": [H.tools.describe(t)
                                                  for t in H.tools.live]})
            if path == "/api/tool-candidates":
                return self._send(200, {"candidates": H.tools.candidates()})
            if path == "/api/view":
                return self._send(200, {"view": H.book.view(p.get("subject", ""))})
            if path == "/api/candidates":
                return self._send(200, {"rows": H.book.find(
                    predicate="need:list", subject=p.get("subject"),
                    include_superseded=True)})
            if path in ("/api/calendar", "/api/temporal"):
                cal = connectors.ics_events(os.path.join(
                    os.path.dirname(H.runtime), "fixtures", "calendar.ics"))
                return self._send(200, {"ok": cal.get("ok"),
                                        "buckets": temporal.bucket(
                                            cal.get("events", [])),
                                        "raw": cal.get("events", [])})
            if path == "/api/archive":
                return self._send(200, {"turns": H.turns[-50:],
                                        "topic": H.topic,
                                        "segments": _segments(H.turns)})
            if path == "/api/speech-floor":
                return self._send(200, H.speech.status())
            if path == "/api/mail":
                inbox = connectors.eml_inbox(os.path.join(
                    os.path.dirname(H.runtime), "fixtures", "inbox"))
                inbox["configured_account"] = H.configured_accounts["email"] or \
                    "absent — declared; fixture basis labeled"
                return self._send(200, inbox)
            if path == "/api/fleet/discovery":
                d = launch_report.get("discovery") or {}
                return self._send(200, d or {"ok": False,
                                             "note": "no scan yet — POST "
                                                     "/api/fleet/discover"})
            if path == "/api/fleet/map":
                mp = os.path.join(H.runtime, "network-map.json")
                return self._send(200, json.load(open(mp))
                                  if os.path.exists(mp) else {"ok": False})
            if path == "/api/fleet/roster":
                return self._send(200, {"roster": __import__("quorum.fleet",
                                        fromlist=["ROSTER"]).ROSTER})
            if path == "/api/library":
                return self._send(200, {"rows": H.book.find(
                    predicate=p.get("predicate"), subject=p.get("subject"),
                    text=p.get("text"), limit=int(p.get("limit", 100)),
                    include_superseded=p.get("include_superseded")
                    in ("1", "true", "True"))})
            if path == "/api/log":
                return self._send(200, {"tail": H.book.rows and
                                        [a.to_row() for a in
                                         H.book.rows[-int(p.get("n", 40)):]] or []})
            if path == "/api/predicates":
                return self._send(200, {"predicates": sorted(
                    {a.predicate for a in H.book.rows})})
            if path == "/api/seed/log":
                return self._send(200, {"entries": H.seed.courier_log()
                                        if H.seed else []})
            if path == "/events":
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                q = __import__("queue").Queue()
                H.book.listeners.append(q.put)
                try:
                    while True:
                        try:
                            d = q.get(timeout=15)
                            self.wfile.write(
                                f"data: {json.dumps(d, ensure_ascii=False)}\n\n"
                                .encode())
                            self.wfile.flush()
                        except Exception:
                            self.wfile.write(b": ping\n\n")
                            self.wfile.flush()
                except Exception:
                    return
            return self._send(404, {"error": f"unknown {path}"})

        # ============================================================ POST ==
        def do_POST(self):
            try:
                return self._do_POST()
            except Exception:
                import traceback
                tb = traceback.format_exc()
                try:
                    with open(os.path.join(H.runtime,
                                           "handler-errors.log"), "a",
                              encoding="utf-8") as f:
                        f.write(f"--- POST {self.path}\n{tb}\n")
                except Exception:
                    pass
                try:
                    return self._send(500, {"ok": False,
                                            "error": tb.splitlines()[-1]})
                except Exception:
                    return

        def _do_POST(self):
            path = urllib.parse.urlparse(self.path).path
            b = _read_json(self)
            if path == "/api/shutdown":
                self._send(200, {"ok": True})
                threading.Thread(target=self.server.shutdown,
                                 daemon=True).start()
                return
            if path == "/api/chat":
                return self._send(200, H.chat(b.get("text", ""),
                                              b.get("persona", "")))
            if path == "/api/chat/reset":
                H.topic = ""
                H.turns = []
                H.context_stack = []
                return self._send(200, {"ok": True, "topic": ""})
            if path == "/api/chat/context":
                sel = {"kind": b.get("kind"), "subject": b.get("subject", ""),
                       "body": b.get("body", "")}
                H.context_stack.append(sel)
                H.topic = b.get("subject", H.topic)
                return self._send(200, {"ok": True,
                                        "context": H.context_stack,
                                        "topic": H.topic})
            if path == "/api/invoke" or path == "/api/command":
                comp, _, verb = (b.get("step", "") or "").partition(".")
                args = b.get("args") or {k: v for k, v in b.items()
                                         if k != "step"}
                r = H.primitives.run(comp, verb, args, {}, H.ctx)
                return self._send(200, r)
            m = re.match(r"/api/tools/([\w-]+)/invoke$", path)
            if m:
                need = H.floor.open("tool-request",
                                    f"call:{m.group(1)}:{rows.new_id('c')[2:]}",
                                    {"tool": m.group(1),
                                     "args": b.get("args", b)})
                res = H.tools.invoke(m.group(1), b.get("args", b), H.ctx)
                if res.get("ok"):
                    H.floor.fulfill(need["id"], res.get("result") or res,
                                    claimant=f"tool:{m.group(1)}")
                return self._send(200, {"need": need["id"], **res})
            if path == "/api/tools/mint":
                return self._send(200, H.tools.mint(
                    b.get("definition", {}), accepted_from=b.get("acceptedFrom", "")))
            m = re.match(r"/api/tools/([\w-]+)/(endorse|discredit)$", path)
            if m:
                return self._send(200, H.tools.endorse(
                    m.group(1), m.group(2) == "endorse",
                    note=b.get("note", "")))
            m = re.match(r"/api/tools/candidate/([\w-]+)/accept$", path)
            if m:
                cand = H.book.get(m.group(1))
                if not cand:
                    return self._send(404, {"error": "no such candidate"})
                dfn = cand["value"]["v"]["definition"]
                return self._send(200, H.tools.mint(dfn,
                                                    accepted_from=m.group(1)))
            if path == "/api/personas":
                g = H.personas.gate(b.get("name", ""),
                                    b.get("imitation_of", ""))
                p = H.personas.mint(b.get("name", "unnamed"),
                                    register=b.get("register", "casual"),
                                    traits=b.get("traits", []),
                                    imitation_of=b.get("imitation_of", ""))
                # portrait/voice/characterization are generated NEEDS —
                # the persona exists minimal, then extends
                H.floor.open("tool-request",
                             f"extend:{p['id']}:portrait",
                             {"tool": "_persona-extend", "args": {
                                 "persona": p["id"], "aspect": "portrait"}},
                             claimant="system", certainty=0.9)
                return self._send(200, {"persona": p, "gate": g})
            m = re.match(r"/api/personas/([\w-]+)/update$", path)
            if m:
                return self._send(200, H.personas.update(m.group(1), b))
            m = re.match(r"/api/personas/([\w-]+)/portrait$", path)
            if m:
                p = H.personas.personas.get(m.group(1))
                if not p:
                    return self._send(404, {"error": "no persona"})
                r = __import__("quorum.art", fromlist=["generate"]).generate(
                    H.llm, p, os.path.join(H.artifacts_dir, "persona-art"))
                p["portrait"] = r["path"]
                H.personas._save()
                H.book.claim(p["id"], "persona:portrait",
                             {"path": r["path"], "generator": r["generator"]},
                             claimant="engine:art", certainty=0.8,
                             basis="generated")
                return self._send(200, r)
            m = re.match(r"/api/personas/([\w-]+)/voice$", path)
            if m:
                return self._send(200, H.personas.update(
                    m.group(1), {"voice": b.get("voice", "")}))
            if path == "/api/roster/select":
                return self._send(200, H.personas.select(b.get("id", "")))
            if path == "/api/roster/move":
                return self._send(200, H.personas.move(
                    b.get("id", ""), int(b.get("dir", -1))))
            m = re.match(r"/api/needs/([\w-]+)/focus$", path)
            if m:
                H.book.claim(m.group(1), "need:focus", {"focused": True},
                             claimant="principal", certainty=1.0,
                             basis="user-choice")
                return self._send(200, {"ok": True})
            m = re.match(r"/api/needs/([\w-]+)/candidate$", path)
            if m or path == "/api/needs/candidate":
                nid = m.group(1) if m else b.get("need", "")
                return self._send(200, H.floor.add_candidate(
                    nid, b.get("slot", ""), b.get("value"),
                    b.get("source", "principal"), float(b.get("confidence", 1.0)),
                    b.get("evidence", "")))
            m = re.match(r"/api/needs/([\w-]+)/slot$", path)
            if m:
                return self._send(200, H.floor.set_slot(
                    m.group(1), b.get("slot", ""), b.get("value")))
            m = re.match(r"/api/needs/([\w-]+)/cancel$", path)
            if m:
                return self._send(200, H.floor.cancel(m.group(1)) or {})
            m = re.match(r"/api/needs/([\w-]+)/retry$", path)
            if m:
                need = H.book.get(m.group(1))
                return self._send(200, {"retried": bool(need)})
            if path == "/api/grants":
                return self._send(200, H.grants.grant(b.get("scope", "")))
            if path == "/api/settings":
                return self._send(200, H.book.claim(
                    "settings", f"settings:{b.get('slot')}", b.get("value"),
                    claimant="principal", certainty=1.0, basis="user-choice"))
            if path == "/api/preload":
                return self._send(200, H.apply_preload(b.get("name", "")))
            if path == "/api/mail/ingest":
                inbox = connectors.eml_inbox(os.path.join(
                    os.path.dirname(H.runtime), "fixtures", "inbox"))
                n = 0
                for msg in inbox.get("messages", []):
                    if msg.get("subject"):
                        H.book.claim(f"mail:{msg['file']}", "email:received",
                                     msg, claimant="source:eml-inbox",
                                     certainty=0.8, basis="source-evidence",
                                     meta={"basis": "fixture"})
                        n += 1
                return self._send(200, {"ingested": n, "basis": inbox["basis"],
                                        "note": inbox.get("note", "")})
            if path == "/api/steward/wake":
                return self._send(200, H.steward.pass_())
            if path == "/api/compare":
                """Competing tools on the same need (prompt §Tools; C-
                DeterministicMatchReview) — run both legs, score comparably."""
                topic = b.get("topic", "")
                crit = b.get("criteria", "incorporated city")
                legs = []
                for tid in ("list-members", "retrieve-table"):
                    r = H.tools.invoke(tid, {"topic": topic, "criteria": crit},
                                       H.ctx)
                    res = r.get("env") or {}
                    legs.append({"tool": tid,
                                 "members": len(res.get("members") or []),
                                 "nonmatches": len(res.get("nonmatches") or []),
                                 "ok": r.get("ok")})
                H.book.claim(f"compare:{topic}", "compare:result", legs,
                             claimant="tool:compare", certainty=0.8,
                             basis="execution")
                return self._send(200, {"topic": topic, "legs": legs})
            if path == "/api/exchange/export":
                pkg = {"kind": "quorum-exchange", "v": 1,
                       "personas": [H.personas.personas[i]
                                    for i in H.personas.order],
                       "tools": list(H.tools.live.values()),
                       "assertions": [a.to_row() for a in H.book.rows[-200:]]}
                os.makedirs(H.artifacts_dir, exist_ok=True)
                out = b.get("path") or os.path.join(
                    H.artifacts_dir, "exchange-package.json")
                json.dump(pkg, open(out, "w", encoding="utf-8"), indent=2)
                H.book.claim("exchange", "exchange:exported",
                             {"path": out}, claimant="system", certainty=0.9,
                             basis="execution")
                return self._send(200, {"path": out})
            if path == "/api/exchange/import":
                try:
                    pkg = json.load(open(b.get("path", ""), encoding="utf-8"))
                except Exception as e:
                    return self._send(200, {"ok": False, "error": str(e)})
                n = 0
                for a in pkg.get("assertions", [])[:200]:
                    H.book.claim(a.get("subject", "import"),
                                 a.get("predicate", "exchange:imported"),
                                 a.get("value", {}).get("v", a.get("value")),
                                 claimant="exchange:package",
                                 certainty=min(float(a.get("certainty", 0.4)),
                                               0.4), basis="import",
                                 meta={"origin": {"kind": "import",
                                                  "sourceKey": b.get("path")}})
                    n += 1
                for t in pkg.get("tools", []):
                    if t.get("id") and t["id"] not in H.tools.live:
                        H.tools.stage_candidate(
                            t, {"kind": "import",
                                "sourceKey": b.get("path", "package")})
                H.book.claim("exchange", "exchange:imported",
                             {"path": b.get("path"), "rows": n,
                              "threshold": "below-action"},
                             claimant="exchange:package", certainty=0.4,
                             basis="import")
                return self._send(200, {"ok": True, "imported": n,
                                        "candidates_staged": True})
            # ---------------- fleet ----------------
            if path == "/api/fleet/discover":
                d = __import__("quorum.fleet", fromlist=["discover"]).discover(
                    subnet_ping=b.get("ping", True))
                launch_report["discovery"] = d
                H.book.claim("fleet", "fleet:discovery",
                             {"found": len(d["found"]),
                              "transports": d["transports"],
                              "durationMs": d["durationMs"]},
                             claimant="engine:discovery", certainty=0.85,
                             basis="execution")
                if H.seed:
                    H.seed.courier({"event": "discovery",
                                    "found": len(d["found"])})
                return self._send(200, d)
            if path == "/api/fleet/invite":
                d = launch_report.get("discovery") or {"found": []}
                return self._send(200, H.fleet.invite(d, b.get("keys", [])))
            if path == "/api/fleet/join":
                dev = b.get("device") or {}
                return self._send(200, H.fleet.join(
                    b.get("key", ""), dev, same_host=bool(b.get("same_host"))))
            if path == "/api/fleet/install":
                return self._send(200, H.fleet.install(b.get("key", "")))
            if path == "/api/fleet/map":
                d = launch_report.get("discovery") or {"found": []}
                return self._send(200, H.fleet.network_map(d, H.runtime))
            if path == "/api/seed/mount":
                media = b.get("media", "")
                H.seed = __import__("quorum.fleet", fromlist=["Seed"]).Seed(
                    H.book, media)
                return self._send(200, {"mounted": media})
            if path == "/api/seed/stage":
                return self._send(200, (H.seed or _noseed()).stage(
                    bool(b.get("consent")), b.get("app_src",
                                                 os.path.dirname(UI_DIR))))
            if path == "/api/seed/mint":
                if not H.seed:
                    return self._send(200, {"ok": False,
                                            "error": "no seed mounted"})
                return self._send(200, H.seed.mint(
                    b.get("app_src", os.path.dirname(UI_DIR)),
                    H.fleet.network_id, b.get("label", "gen2")))
            # ---------------- artifacts ----------------
            if path == "/api/artifact/import":
                return self._send(200, H.exchange.import_artifact(
                    b.get("path", "")))
            m = re.match(r"/api/artifact/([\w-]+)/adopt$", path)
            if m:
                return self._send(200, H.exchange.adopt(m.group(1)))
            m = re.match(r"/api/artifact/([\w-]+)/republish$", path)
            if m:
                out = b.get("path") or os.path.join(
                    H.artifacts_dir, f"republished-{m.group(1)}.bmp")
                return self._send(200, H.exchange.republish(m.group(1), out))
            if path == "/api/artifact/encode":
                enc = artifacts.matrix_encode(
                    json.dumps(b.get("payload", {})).encode(),
                    b.get("path", os.path.join(H.artifacts_dir, "out.bmp")))
                return self._send(200, enc)
            if path == "/api/artifact/decode":
                try:
                    d = artifacts.matrix_decode(b.get("path", ""))
                    payload = d.get("payload", b"")
                    d["payload"] = payload.decode("utf-8", errors="replace") \
                        if isinstance(payload, bytes) else str(payload)
                    return self._send(200, d | {"ok": True})
                except Exception as e:
                    return self._send(200, {"ok": False, "error": str(e)})
            if path == "/api/peer/pair":
                return self._send(200, H.fleet.pair_peer(
                    b.get("peer_id", ""), b.get("endpoint", "")))
            if path == "/api/peer/sever":
                return self._send(200, H.fleet.sever(b.get("peer_id", "")))
            if path == "/api/peer/rejoin-offer":
                return self._send(200, H.fleet.rejoin_offer(
                    b.get("peer_id", "")))
            if path == "/api/peer/delta":
                """Same-host peer exercise — honestly labeled: does NOT count
                as a joined device (owner ruling). Exercises the sovereign-hub
                delta exchange between two Books."""
                import quorum.book as qbook
                peer_path = os.path.join(H.runtime, "peer-ledger.jsonl")
                pb = qbook.Book(peer_path)
                pb.mount()
                sent = H.fleet.peer_delta(pb, b.get("peer_id", "peer-local"))
                their = pb.rows_after(0)
                n = H.book.import_rows(their, b.get("peer_id", "peer-local"))
                return self._send(200, {"same_host_exercise": True,
                                        "not_a_device_join": True,
                                        "sent": sent, "imported": n})
            if path == "/api/voice/spec":
                return self._send(200, artifacts.voice_spec(
                    b.get("families", []), b.get("traits", {})))
            if path == "/api/voice/map":
                spec = artifacts.voice_spec(b.get("families", []),
                                            b.get("traits", {}))
                return self._send(200, artifacts.map_voice(
                    spec, H.speech.voices()))
            if path == "/api/speak":
                return self._send(200, H.speech.admit(
                    b.get("text", ""), b.get("voice", ""),
                    b.get("persona", "")))
            if path == "/api/tones/machine":
                engines.machine_beep()
                return self._send(200, {"ok": True, "register": "machine-beep"})
            if path == "/api/tones/user":
                engines.user_jingle()
                return self._send(200, {"ok": True, "register": "user-jingle"})
            m = re.match(r"/api/personas/([\w-]+)/assign$", path)
            if m:
                """C-SurfaceAssignment — bind a persona to a named surface."""
                r = H.personas.update(m.group(1),
                                      {"surface": b.get("surface", "")})
                H.book.claim(m.group(1), "persona:surface-assign",
                             {"surface": b.get("surface", "")},
                             claimant="principal", certainty=1.0,
                             basis="user-choice")
                return self._send(200, r)
            if path == "/api/cleanup":
                return self._send(200, H.book.cleanup())
            if path == "/api/email/commentary":
                """S-email-commentary — persona commentary on a selected
                message, recorded as its own claim (evidence preserved)."""
                m2 = {"subject": b.get("subject", ""), "body": b.get("body", "")}
                H.context_stack.append({"kind": "email", **m2})
                H.topic = m2["subject"]
                turn = H.chat(b.get("prompt",
                                    f"Commentary on the email '{m2['subject']}'?"))
                H.book.claim(f"mail:{m2['subject']}", "email:commentary",
                             {"subject": m2["subject"],
                              "replies": [r["name"] for r in
                                          turn.get("replies", [])],
                              "basis": "fixture-directory"},
                             claimant="system", certainty=0.9,
                             basis="execution")
                return self._send(200, turn)
            return self._send(404, {"error": f"unknown {path}"})

    return Q


def _noseed():
    class _NS:
        def stage(self, *a, **k):
            return {"staged": False, "error": "no seed mounted"}
        def mint(self, *a, **k):
            return {"ok": False, "error": "no seed mounted"}
    return _NS()


def _segments(turns):
    """Topic segments for the archive (C-ConversationArchive)."""
    segs, cur = [], None
    for t in turns:
        topic = t.get("topic") or "general"
        if topic != cur:
            segs.append({"topic": topic, "at": t.get("id")})
            cur = topic
    return segs


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False          # exclusive bind (S-4)


def serve(host, launch_report, open_browser=True):
    probe = probe_port(host.port)
    launch_report["port_probe"] = probe
    if not probe["free"]:
        launch_report["ok"] = False
        launch_report["error"] = (f"port {host.port} owned by "
                                  f"{probe['owner']} — {probe.get('note')}")
        return None
    srv = Server(("127.0.0.1", host.port), make_handler(host, launch_report))
    launch_report["ok"] = True
    launch_report["bound"] = host.port
    if open_browser:
        try:
            import webbrowser
            webbrowser.open(f"http://127.0.0.1:{host.port}/")
        except Exception:
            pass
    return srv
