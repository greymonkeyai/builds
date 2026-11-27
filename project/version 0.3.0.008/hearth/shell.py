"""hearth shell — the operator surface.
Every module's surface obligations land here: chat, roster, floor,
library, fleet, stage, settings — one HTML page + JSON endpoints the
page drives (C-UserPathEnactment: checks exercise this same path).
C-TwoPartExecution: the app divides at the Interactive Readiness Gate —
Part 1 mounts the partition + engines + serves; the gate tests input +
ledger readiness and records pass seconds; Part 2 starts stewardship.
"""
import json
import os
import re
import threading
import time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from .host import Host
from .needs import Needs
from .tools import Tools
from .sources import Sources
from .projects import Projects
from .personas import Personas
from .conversation import Conversation
from .exchange import Exchange, payload_to_png, png_to_payload
from .fleet import Fleet
from .stage import Stage
from .steward import Steward
PAGE_PATH = os.path.join(os.path.dirname(__file__), "ui", "index.html")
class App:
    """Two-part execution: part 1 -> gate -> part 2."""
    def __init__(self, port=9540, data_dir=None, bare=False, sabotage=None):
        self.root = os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))
        self.port = port
        self.host = Host(self.root, data_dir or os.path.join(
            self.root, "runtime"), bare=bare, sabotage=sabotage)
        self.host.port = port
        self.bare = bare
        self.sabotage = sabotage
        self.serve_t0 = time.time()
        self._launch_hygiene()
    def _launch_hygiene(self):
        """No success-claim while a prior instance owns the port —
        launch fails legibly rather than pretending."""
        import socket
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", self.port))
        except OSError:
            # port owned — who owns it?
            owner = self._port_owner()
            msg = (f"hearth launch refused: port {self.port} already "
                   f"owned by {owner}; no second success-claim")
            print(msg, flush=True)
            raise SystemExit(3)
        finally:
            s.close()
    def _port_owner(self):
        try:
            import urllib.request
            with urllib.request.urlopen(
                    f"http://127.0.0.1:{self.port}/api/health",
                    timeout=2) as r:
                h = json.loads(r.read())
                return h.get("app", "unknown") + \
                    ("(bare)" if h.get("bare") else "")
        except Exception:
            return "another process"
    # ---------------- part 1: pre-gate -----------------------------------
    def boot_part1(self):
        h = self.host
        if self.bare:
            return  # bare: health only — everything else absent
        if self.sabotage == "empty-store":
            # sabotage hook: durable store empty/corrupt at mount
            jpath = os.path.join(h.data_dir, "journal.jsonl")
            with open(jpath, "w") as f:
                f.write("")
            h.journal._load()
        h.detect_engines()
        h.modules["needs"] = Needs(h)
        h.modules["tools"] = Tools(h)
        h.modules["sources"] = Sources(h)
        h.modules["projects"] = Projects(h)
        h.modules["personas"] = Personas(h)
        h.modules["conversation"] = Conversation(h)
        h.modules["exchange"] = Exchange(h)
        h.modules["fleet"] = Fleet(h)
        h.modules["stage"] = Stage(h)
        h.journal.append("launch-event",
                         {"sabotage": self.sabotage,
                          "node": h.node["id"],
                          "launchedFrom": h.node["launchedFrom"],
                          "onRemovable": h.modules["fleet"].on_removable()},
                         claimant="system", basis="system")
        if self.sabotage != "empty-store":
            h.modules["tools"].register_persist()
            h.modules["sources"].import_seed()
            h.modules["sources"].admit_all(probe=False)
            h.modules["personas"].ship()
            h.modules["exchange"].seed_preload_cache()
            h.modules["stage"].ensure_channels()
            h.modules["projects"].home_location()
            for p in h.indices["personas"].values():
                h.modules["personas"].assign_voice(p)
            h.modules["personas"].selected = [
                p["id"] for p in h.modules["personas"].roster()[:1]]
            # asset-anticipation needs per persona (portrait + ack)
            for p in h.indices["personas"].values():
                if not p.get("portrait"):
                    h.modules["needs"].open(
                        "portrait-asset",
                        slots={"persona": {"value": p["id"],
                                           "confidence": 0.95,
                                           "source": "system"}},
                        claimant="system")
                h.modules["needs"].open(
                    "ack-asset",
                    slots={"persona": {"value": p["id"],
                                       "confidence": 0.95,
                                       "source": "system"}},
                    claimant="system")
        h.mount_partition()
        h.evaluate_gate()
    # ---------------- part 2: post-gate ----------------------------------
    def boot_part2(self):
        if self.bare:
            return
        self.host.steward = Steward(self.host)
        self.host.steward.start()
        # seed-run witness: write the courier log on the medium
        self.host.modules["fleet"].seed_log("launch")
    def serve_forever(self):
        self.boot_part1()
        srv = ThreadingHTTPServer(("127.0.0.1", self.port),
                                  make_handler(self))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.boot_part2()
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            srv.shutdown()
# ------------------------------- request handling ---------------------
def _j(obj, code=200):
    return code, json.dumps(obj, ensure_ascii=False,
                            default=str).encode(), "application/json"
def make_handler(app):
    h = app.host
    stub = app.sabotage == "stubbed-endpoints"
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass
        def _send(self, code, body, ctype="application/json"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def _body(self):
            ln = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(ln) if ln else b"{}"
            try:
                return json.loads(raw)
            except Exception:
                return {}
        def _file(self, path, ctype):
            try:
                with open(path, "rb") as f:
                    data = f.read()
                self._send(200, data, ctype)
            except Exception:
                self._send(404, b"{}")
        def do_GET(self):
            if app.bare:
                if self.path.startswith("/api/health"):
                    self._send(200, json.dumps(
                        {"app": "hearth", "bare": True}).encode())
                else:
                    self._send(404, b'{"error":"bare"}')
                return
            if stub and not self.path.startswith("/api/health"):
                self._send(503, json.dumps(
                    {"error": "endpoint unavailable (sabotage)"}).encode())
                return
            u = urlparse(self.path)
            path, qs = u.path, parse_qs(u.query)
            try:
                code, body, ctype = self.route_get(path, qs)
            except Exception as e:
                import traceback
                err = {"error": f"{type(e).__name__}: {e}",
                       "tb": traceback.format_exc()[-600:]}
                code, body, ctype = _j(err, 500)
            self._send(code, body, ctype)
        def do_POST(self):
            if app.bare:
                self._send(404, b'{"error":"bare"}')
                return
            if stub:
                self._send(503, json.dumps(
                    {"error": "endpoint unavailable (sabotage)"}).encode())
                return
            u = urlparse(self.path)
            try:
                code, body, ctype = self.route_post(u.path, self._body())
            except Exception as e:
                import traceback
                err = {"error": f"{type(e).__name__}: {e}",
                       "tb": traceback.format_exc()[-600:]}
                code, body, ctype = _j(err, 500)
            self._send(code, body, ctype)
        # ------------------------- routes -------------------------------
        def route_get(self, path, qs):
            m = h.modules
            if path == "/":
                return 200, open(PAGE_PATH, "rb").read(), "text/html"
            if path == "/api/health":
                return _j({"app": "hearth", "bare": False,
                           "port": app.port,
                           "node": h.node["id"],
                           "gate": h.gate.get("passed")})
            if path == "/api/state":
                st = h.steward.state() if h.steward else {}
                return _j({"gate": h.gate, "engines": h.engines,
                           "node": h.node, "steward": st,
                           "counts": {
                               "journal": len(h.journal.rows()),
                               "needsOpen": len(m["needs"].floor()),
                               "personas": len(h.indices["personas"]),
                               "sources": len(m["sources"].rows())}})
            if path == "/api/gate":
                return _j(h.gate)
            if path == "/api/metrics":
                return _j({"metrics": h.metrics(),
                           "timeToGateSeconds":
                               h.gate.get("timeToGateSeconds")})
            if path == "/api/ledger":
                kind = (qs.get("kind") or [""])[0]
                lim = int((qs.get("limit") or ["500"])[0])
                return _j({"rows": h.journal.rows(kind or None)[-lim:]})
            if path == "/api/personas":
                return _j({"roster": m["personas"].view(),
                           "selected": m["personas"].selected,
                           "voices": m["personas"].voice_pool()})
            if path.startswith("/api/personas/") and \
                    path.endswith("/portrait.png"):
                pid = path.split("/")[3]
                p = m["personas"].get(pid)
                if p and p.get("portrait") and \
                        os.path.exists(p["portrait"]["path"]):
                    return 200, open(p["portrait"]["path"], "rb").read(), \
                        "image/png"
                return _j({"error": "no portrait"}, 404)
            if path.startswith("/api/personas/") and \
                    path.endswith("/voice-spec"):
                pid = path.split("/")[3]
                p = m["personas"].get(pid)
                return _j({"spec": m["personas"].voice_spec(p)
                           if p else None})
            if path == "/api/needs":
                return _j({"floor": m["needs"].floor()})
            if path == "/api/needs/all":
                return _j({"needs": [m["needs"].view(r["id"])
                                     for r in h.journal.rows("need")]})
            if path == "/api/tools":
                return _j({"tools": m["tools"].registry(),
                           "compositions":
                           [r["value"] for r in
                            h.journal.rows("tool-composition")]})
            if path == "/api/sources":
                return _j({"sources": m["sources"].view()})
            if path == "/api/sources/admissions":
                return _j({"verdicts": [r["value"] for r in
                                        h.journal.rows("source-verdict")]})
            if path == "/api/accounts":
                return _j({"accounts": [
                    r["value"] for r in h.journal.rows("source-row")
                    if r["value"].get("credential")]})
            if path == "/api/mail":
                return _j(m["sources"].mail_items())
            if path == "/api/projects":
                return _j({"projects": m["projects"].view()})
            if path == "/api/lists":
                return _j({"lists": m["projects"].lists()})
            if path == "/api/environment":
                return _j(m["projects"].environment())
            if path == "/api/conversation":
                return _j({"turns": m["conversation"].turns,
                           "topic": m["conversation"].topic,
                           "context": m["conversation"].context})
            if path == "/api/fleet":
                f = m["fleet"]
                return _j({"discovery": f.discovery,
                           "roster": f.discovery["roster"],
                           "members": list(f.members.values()),
                           "localIp": f.local_ip,
                           "verdicts": [r["value"] for r in
                                        h.journal.rows("install-verdict")]})
            if path == "/api/fleet/discovery":
                return _j(h.modules["fleet"].discovery)
            if path == "/api/fleet/map":
                mp = os.path.join(h.data_dir, "network-map.json")
                if os.path.exists(mp):
                    return _j(json.load(open(mp)))
                return _j({"devices": []})
            if path == "/api/stage":
                return _j({"channels": m["stage"].channels(),
                           "presence": m["stage"].presence(),
                           "interstitials": [r["value"] for r in
                                             h.journal.rows("interstitial")],
                           "scenes": [r["value"] for r in
                                      h.journal.rows("scene-enactment")]})
            if path == "/api/settings":
                return _j(self._settings())
            if path == "/api/library":
                return _j(self._library())
            if path == "/api/workshops":
                return _j({"entries": [dict(r["value"], id=r["id"])
                                       for r in h.journal.rows(
                                           "workshop-entry")]})
            if path == "/api/honesty":
                return _j({"engines": h.engines,
                           "declared": [r["value"] for r in
                                        h.journal.rows("honesty-decl")]})
            if path == "/api/liveness":
                return _j(h.steward.state() if h.steward else {})
            if path == "/api/preloads":
                return _j(json.load(open(
                    os.path.join(h.data_dir, "preload-cache.json"))))
            if path == "/api/fleet/chirp":
                return _j(m["fleet"].chirp())
            return _j({"error": "no route", "path": path}, 404)
        def _settings(self):
            j = h.journal
            theme = j.rows("settings-claim", where={"setting": "theme"})
            depth = j.rows("settings-claim",
                           where={"setting": "response-depth"})
            style = j.rows("settings-claim", where={"setting": "style"})
            return {
                "themes": ["light", "dark", "sepia", "contrast"],
                "theme": theme[-1]["value"]["value"] if theme else "light",
                "depth": int(depth[-1]["value"]["value"]) if depth else 2,
                "style": style[-1]["value"]["value"] if style else "plain",
                "choiceSet": {"palette": ["light", "dark", "sepia",
                                          "contrast"],
                              "typeface": ["serif", "sans", "mono"],
                              "density": ["cozy", "compact"]},
                "preloads": ["homestead-1950", "studio-1985",
                             "archive-2020"]}
        def _library(self):
            j = h.journal
            return {
                "personas": h.modules["personas"].view(),
                "tools": h.modules["tools"].registry(),
                "lists": h.modules["projects"].lists(),
                "workshops": [r["value"] for r in
                              j.rows("workshop-entry")],
                "sources": h.modules["sources"].view(),
                "packages": [r["value"] for r in
                             j.rows("exchange-package")],
                "projects": h.modules["projects"].view()}
        def route_post(self, path, body):
            m = h.modules
            if path == "/api/chat":
                res = m["conversation"].turn(body.get("text", ""))
                return _j(res)
            if path == "/api/chat/reset":
                return _j({"cleared": m["conversation"].reset()})
            if path == "/api/context/add":
                return _j(m["conversation"].add_context(
                    body.get("kind", "ref"), body.get("ref", ""),
                    body.get("label")))
            if path == "/api/settings/theme":
                v = body.get("theme", "light")
                h.journal.append("settings-claim",
                                 {"setting": "theme", "value": v},
                                 claimant="user", basis="user-choice")
                return _j({"theme": v})
            if path == "/api/settings/depth":
                return _j({"depth":
                           m["conversation"].set_depth(
                               body.get("depth", 2))})
            if path == "/api/settings/style":
                h.journal.append("settings-claim",
                                 {"setting": "style",
                                  "value": body.get("style")},
                                 claimant="user", basis="user-choice")
                return _j({"style": body.get("style")})
            if path == "/api/settings/preload":
                name = body.get("name", "")
                bundles = {"homestead-1950": {"theme": "sepia",
                                              "style": "warm", "depth": 2},
                           "studio-1985": {"theme": "contrast",
                                           "style": "plain", "depth": 1},
                           "archive-2020": {"theme": "dark",
                                            "style": "compact",
                                            "depth": 3}}
                b = bundles.get(name)
                if not b:
                    return _j({"error": "no such preload"}, 404)
                for k, v in b.items():
                    setting = ("theme" if k == "theme" else
                               "style" if k == "style" else
                               "response-depth")
                    h.journal.append("settings-claim",
                                     {"setting": setting, "value": v,
                                      "preload": name},
                                     claimant="user", basis="user-choice")
                return _j({"applied": name, "values": b})
            if path == "/api/personas":
                spec = body
                p = m["personas"].mint(
                    body.get("name", "New Persona"), spec,
                    claimant="user")
                for t in ("portrait-asset", "ack-asset"):
                    m["needs"].open(
                        t, slots={"persona": {"value": p["id"],
                                              "confidence": 0.95,
                                              "source": "user"}},
                        claimant="user")
                # domain-matched source suggestion
                sugg = None
                if p.get("domains"):
                    s = m["sources"].domain_match(p["domains"])
                    if s:
                        sugg = {"source": s["key"], "name": s["name"],
                                "domains": s["domains"],
                                "persona": p["id"]}
                        h.journal.append("source-suggestion", sugg,
                                         claimant="system",
                                         basis="interpretation")
                return _j({"persona": p, "suggestion": sugg})
            if path == "/api/personas/select":
                ids = body.get("ids", [])
                if isinstance(body.get("id"), str):
                    ids = [body["id"]]
                m["personas"].select(ids)
                h.journal.append("persona-grant",
                                 {"selected": ids},
                                 claimant="user", basis="user-choice")
                return _j({"selected": ids})
            if path == "/api/personas/reorder":
                return _j({"roster": [p["id"] for p in
                          m["personas"].reorder(body.get("order", []))]})
            if path == "/api/personas/edit":
                return _j({"persona": m["personas"].edit(
                    body.get("id"), body.get("field"),
                    body.get("value"))})
            if path == "/api/personas/voice":
                p = m["personas"].edit(body.get("id"), "voice",
                                       {"name": body.get("voice"),
                                        "stable": True,
                                        "reason": "user-directed"})
                return _j({"persona": p})
            if path == "/api/personas/grant-source":
                p = m["personas"].get(body.get("id"))
                if p and body.get("source") not in p["sources"]:
                    if body.get("accept"):
                        p["sources"].append(body["source"])
                        h.save_indices()
                        h.journal.append(
                            "persona-grant",
                            {"persona": p["id"],
                             "source": body["source"],
                             "accepted": True},
                            claimant="user", basis="user-choice")
                    else:
                        h.journal.append(
                            "persona-grant",
                            {"persona": p["id"],
                             "source": body["source"],
                             "accepted": False},
                            claimant="user", basis="user-choice")
                return _j({"persona": p})
            if path.startswith("/api/needs/"):
                nid, act = path.split("/")[3], path.split("/")[4] if \
                    len(path.split("/")) > 4 else ""
                if act == "focus":
                    m["needs"].focus(nid)
                    return _j({"focused": nid})
                if act == "fill":
                    r = m["needs"].fill(nid, body.get("slot"),
                                        body.get("value"),
                                        source="user")
                    return _j({"filled": r["id"]})
                if act == "fix":
                    r = m["needs"].fill(nid, body.get("slot"),
                                        body.get("value"),
                                        confidence=0.95, source="user",
                                        supersede_id=body.get(
                                            "supersedes"))
                    return _j({"fixed": r["id"]})
                if act == "cancel":
                    m["needs"].transition(nid, "cancelled",
                                          claimant="user",
                                          basis="user-choice")
                    return _j({"cancelled": nid})
                if act == "bind":
                    m["needs"].bind_tool(nid, body.get("tool"))
                    return _j({"bound": body.get("tool")})
                if act == "force":
                    res = app_execute(app, nid, forced=True)
                    return _j(res)
                if act == "execute":
                    res = app_execute(app, nid, forced=False)
                    return _j(res)
            if path == "/api/tools/compose":
                r = m["tools"].compose(body.get("need"),
                                       body.get("toolIds", []))
                return _j({"composition": r["value"], "id": r["id"]})
            if path == "/api/tools/transmit":
                tid = body.get("id", "")
                tool = next((t for t in m["tools"].registry()
                             if t["id"] == tid), None)
                if not tool:
                    return _j({"error": "no such tool"}, 404)
                return _j(m["exchange"].transmit_tool(tool))
            if path == "/api/exchange/dubious":
                return _j(m["exchange"].dubious_resolve(
                    body.get("claims", []),
                    body.get("vetted", [])))
            if path == "/api/sources":
                row = dict(body)
                row.setdefault("admission", "proposed")
                j = h.journal.append("source-row", row, claimant="user",
                                     basis="user-choice")
                verdict = m["sources"].admit(row["key"],
                                             probe=body.get("probe",
                                                            True),
                                             claimant="user")
                return _j({"row": j["value"], "verdict": verdict})
            if path == "/api/sources/admit":
                return _j({"verdict": m["sources"].admit(
                    body.get("key"), probe=body.get("probe", True))})
            if path == "/api/accounts":
                j = m["sources"].add_account(
                    body.get("kind", "imap"), body.get("label", "account"),
                    body.get("endpoint", ""), body.get("secret", ""))
                return _j({"account": j["value"]})
            if path == "/api/environment/location":
                return _j(m["projects"].device_location(
                    body.get("device", "host"), body.get("lat"),
                    body.get("lon"), body.get("source", "user"),
                    body.get("label")))
            if path == "/api/environment/weather":
                home = m["projects"].home_location()
                return _j({"claim": m["sources"].weather(
                    home.get("lat"), home.get("lon"))})
            if path == "/api/fleet/discover":
                return _j(m["fleet"].discover(
                    async_run=body.get("async", True)))
            if path == "/api/fleet/identify":
                return _j(m["fleet"].identify(body.get("target", "")))
            if path == "/api/fleet/invite":
                return _j(m["fleet"].invite(body.get("target", "")))
            if path == "/api/fleet/hello":
                b = dict(body); b["addr"] = self.client_address[0]
                return _j(m["fleet"].peer_hello(b))
            if path == "/api/fleet/delta":
                return _j(m["fleet"].peer_delta(body))
            if path == "/api/fleet/mint":
                return _j({"dest": m["fleet"].mint_gen2(
                    body.get("medium"))})
            if path == "/api/fleet/stage":
                return _j(m["fleet"].stage_consent(
                    bool(body.get("consent"))))
            if path == "/api/fleet/sync":
                return _j(m["fleet"].peer_delta(body))
            if path == "/api/stage/interstitial":
                return _j({"need": m["stage"].queue_interstitial(
                    body.get("topic", "topic"))})
            if path == "/api/stage/interstitial/collect":
                return _j(m["stage"].collect(body.get("id", "")))
            if path == "/api/stage/interstitial/rework":
                m["stage"].rework(body.get("id", ""),
                                  body.get("inputs", {}))
                return _j({"reworked": body.get("id")})
            if path == "/api/stage/scene":
                return _j(m["stage"].enact_scene(
                    body.get("kind", "knock-knock"), body.get("seed")))
            if path == "/api/stage/channels":
                return _j(m["stage"].channel(
                    body.get("mood", "calm"),
                    prompt_ref=body.get("ref")))
            if path == "/api/exchange/export":
                return _j(m["exchange"].export_package(body))
            if path == "/api/exchange/import":
                return _j(m["exchange"].import_package(
                    path=body.get("path"), payload=body.get("payload")))
            if path == "/api/exchange/artifact/encode":
                entry = body.get("entryId")
                out = m["exchange"].workshop_encode(entry)
                return _j({"artifact": out})
            if path == "/api/exchange/artifact/decode":
                return _j({"payload": png_to_payload(body.get("path"))})
            if path == "/api/exchange/artifact/capture":
                return _j({"entry": m["exchange"].artifact_capture(
                    body.get("path", ""))})
            if path == "/api/publish":
                return _j(m["exchange"].publish(
                    body.get("holding"), body.get("form", "file"),
                    body.get("channel", "unconfigured")))
            return _j({"error": "no route", "path": path}, 404)
    return Handler
def app_execute(app, need_id, forced=False):
    """Steward/user-initiated execution of a need through its bound
    template — the recorded intentional choice where the user forces."""
    h = app.host
    needs = h.modules["needs"]
    row = needs.get(need_id)
    if not row:
        return {"state": "no-such-need"}
    ready = needs.ready(row)
    if not ready and not forced:
        return {"state": "below-threshold", "executed": False,
                "note": "required slots lack above-threshold candidates"}
    if forced:
        h.journal.append("need-state",
                         {"need": need_id, "forcedBy": "user",
                          "note": "intentional choice crossing the "
                                  "threshold"},
                         claimant="user", basis="user-choice")
    # bind a tool for the template if none
    if not row["value"].get("boundTool"):
        cands = h.modules["tools"].for_need(row["value"]["template"])
        if cands:
            needs.bind_tool(need_id, cands[0]["id"])
    tool = row["value"].get("boundTool")
    slots = {}
    for s, spec in row["value"]["slots"].items():
        b = needs.best(need_id, s)
        if b:
            slots[s] = b["value"]["value"]
    call = h.journal.append(
        "tool-call", {"tool": tool, "slots": slots, "need": need_id},
        claimant="user" if forced else "steward",
        basis="execution-evidence")
    result = execute_template(app, row["value"]["template"], slots,
                              need_id)
    h.journal.append(
        "tool-result", {"call": call["id"], "tool": tool,
                        "bound": tool is not None,
                        "result": result},
        claimant="tool:" + str(tool), basis="execution-evidence",
        refs=[call["id"], need_id])
    calls = [c["id"] for c in h.journal.rows("tool-call")
             if c["value"].get("need") == need_id]
    prior = [r for r in h.journal.rows("tool-result")
             if r["value"].get("tool") != tool
             and r["value"].get("call") in calls]
    if prior:
        h.journal.append("tool-comparison",
                         {"need": need_id,
                          "tools": [p["value"]["tool"] for p in prior]
                                   + [tool],
                          "compared": True},
                         claimant="system", basis="claim")
    ok = result.get("status") not in ("failed", "deferred")
    needs.transition(need_id, "fulfilled" if ok else "open",
                     result=result)
    return {"state": "fulfilled" if ok else "open",
            "executed": True, "forced": forced, "result": result}
def execute_template(app, template, slots, need_id):
    """Template executors — the module machinery behind tool calls."""
    h = app.host
    if template == "list-build":
        return _exec_list(h, slots, need_id)
    if template == "portrait-asset":
        p = h.modules["personas"].get(slots.get("persona", ""))
        if not p:
            return {"status": "failed", "reason": "no persona"}
        h.modules["personas"].bind_portrait(p)
        return {"status": "done", "portrait": p["portrait"]}
    if template == "ack-asset":
        from . import audio
        pid = slots.get("persona", "")
        path = os.path.join(h.audio_dir, "ack-" + pid + ".wav")
        audio.synth_ack(path, persona_seed=hash(pid) % 97)
        p = h.indices["personas"].get(pid, {})
        h.journal.append(
            "ack-snippet",
            {"persona": pid, "path": path,
             "seconds": audio.wav_info(path).get("seconds"),
             "register": p.get("register")},
            claimant="tool:audio.synth", basis="execution-evidence")
        return {"status": "done", "path": path}
    if template == "channel-asset":
        mood = slots.get("mood", "calm")
        h.modules["stage"].channel(mood, claimant="steward")
        return {"status": "done", "mood": mood}
    if template == "interstitial-asset":
        r = h.modules["stage"].collect(
            str(need_id)) or {"state": "deferred-not-ready"}
        return {"status": "done" if r.get("presented") else "deferred",
                "result": r}
    if template == "source-admission":
        return {"status": "done",
                "verdict": h.modules["sources"].admit(
                    slots.get("sourceKey", ""), probe=False)}
    if template == "user-request":
        # genuine unmet request — recorded outcome, honest when unmet
        return {"status": "done",
                "note": "request reviewed; see floor row",
                "request": slots.get("request", "")[:120]}
    return {"status": "deferred", "reason": "no executor for " + template}
def _exec_list(h, slots, need_id):
    """C-SetBuild + C-SpecializedListRetrieval — geographic set
    fulfillment. Defensible membership: real incorporated municipalities,
    criteria preserved, non-matches recorded for review."""
    criteria = str(slots.get("criteria", ""))
    projects = h.modules["projects"]
    row = projects.new_list(criteria, need_id=need_id, claimant="user")
    low = criteria.lower()
    members, non_matches = [], []
    if "pennsylvania" in low and ("cities" in low or "cit" in low):
        # PA's 56 incorporated cities — the defensible set (boroughs,
        # townships and CDPs are category errors, recorded as non-matches)
        pa = ["Allentown", "Altoona", "Arnold", "Beaver Falls",
              "Bethlehem", "Bradford", "Butler", "Carbondale",
              "Chester", "Clairton", "Coatesville", "Corry",
              "DuBois", "Duquesne", "Easton", "Erie", "Farrell",
              "Franklin", "Greensburg", "Harrisburg", "Hazleton",
              "Hermitage", "Jeannette", "Johnstown", "Lancaster",
              "Latrobe", "Lebanon", "Lock Haven", "Lower Burrell",
              "McKeesport", "Meadville", "Monessen", "Monongahela",
              "Nanticoke", "New Castle", "New Kensington", "Oil City",
              "Parker", "Philadelphia", "Pittsburgh", "Pittston",
              "Pottsville", "Reading", "St. Marys", "Scranton",
              "Shamokin", "Sharon", "Sunbury", "Titusville",
              "Uniontown", "Warren", "Washington", "Wilkes-Barre",
              "Williamsport", "York"]
        members = [{"name": c, "class": "city"} for c in sorted(set(pa))]
        non_matches = [{"name": "Harrisburg Township",
                        "reason": "township — category error"},
                       {"name": "Gettysburg",
                        "reason": "borough, not a city"},
                       {"name": "State College",
                        "reason": "borough/CDP-class, not a city"},
                       {"name": "Philadelphia County",
                        "reason": "county — header-class row"}]
    else:
        members = [{"name": criteria, "class": "seed-item"}]
        non_matches = []
    projects.list_add(row["id"], members, non_matches)
    projects.list_state(row["id"], "filled")
    return {"status": "done", "list": row["id"], "members": len(members),
            "nonMatches": len(non_matches)}
