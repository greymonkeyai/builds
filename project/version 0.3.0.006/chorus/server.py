"""HTTP surface — the owner-facing operator surface. The UI is a thin
client over these endpoints; every owner-facing control works through
this surface (S-1) and reports legible outcomes (C-LegibleOutcome).
Also serves the peer protocol (/peer/*) for fleet exchange.
"""
import json
import os
import socket
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from . import personas as per
from . import exchange as exch
from . import artifacts as art
from . import stage as stg
from . import seedmedia as seed
from . import chat as chat_mod
from . import needs as nds
from . import sources as src_mod
class Handler(BaseHTTPRequestHandler):
    host = None
    ui_dir = None
    def log_message(self, *a):
        pass
    # ---------- plumbing ----------
    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, default=str).encode("utf-8")
        elif isinstance(body, str):
            body = (json.dumps(body) if ctype == "application/json"
                    else body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass
    def _json(self):
        n = int(self.headers.get("Content-Length", 0))
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return {}
    def _route(self):
        return urllib.parse.urlparse(self.path).path, \
            dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
    # ---------- GET ----------
    def do_GET(self):
        try:
            self._do_GET()
        except Exception:
            import traceback
            try:
                self._send(500, {"error": "internal",
                                 "trace": traceback.format_exc()[-900:]})
            except Exception:
                pass
    def _do_GET(self):
        path, q = self._route()
        h = self.host
        if path in ("/", "/index.html"):
            p = os.path.join(self.ui_dir, "index.html")
            self._send(200, open(p, "rb").read(), "text/html")
            return
        if path == "/api/hello":
            self._send(200, {"ok": True, "app": "chorus",
                             "node": h.node_id,
                             "part2": h.part2_done})
            return
        if path == "/api/state":
            self._send(200, self._state())
            return
        if path == "/api/honesty":
            self._send(200, h.honesty())
            return
        if path == "/api/needs":
            self._send(200, {"open": [self._need_view(n) for n in h.needs.floor()]})
            return
        if path == "/api/library":
            self._send(200, self._library())
            return
        if path == "/api/roster":
            self._send(200, {"roster": [self._persona_view(p)
                                        for p in h.roster_order()]})
            return
        if path == "/api/sources":
            self._send(200, {"sources": [
                {"key": k, "name": v.get("name"), "kind": v.get("kind"),
                 "domains": v.get("domains"), "admitted": v.get("admitted"),
                 "descriptor": v.get("descriptor"), "ceiling": v.get("ceiling")}
                for k, v in h.sources.items()]})
            return
        if path == "/api/fleet":
            self._send(200, {"discovery": h.fleet.discovery,
                             "members": [m["claim"] for m in
                                         h.book.current_of("fleet:member")],
                             "roster": h.fleet.discovery.get("roster", [])})
            return
        if path == "/api/mail":
            mails = exch.fixture_inbox(h)
            live = [k for k in h.sources if k.startswith("source-acct-")]
            self._send(200, {"fixture": mails, "liveAccounts": live,
                             "basis": "fixture-directory (labeled)"
                             if not live else "configured-account"})
            return
        if path == "/api/events":
            self._send(200, {"events": h.events[-100:]})
            return
        if path == "/api/gate":
            gp = os.path.join(h.runtime_dir, "gate.json")
            self._send(200, json.load(open(gp)) if os.path.exists(gp)
                       else {"ok": False})
            return
        if path == "/api/latency":
            rows = h.book.of_kind("speech:latency")
            self._send(200, {"records": [r["claim"] for r in rows],
                             "host": h.node_id})
            return
        if path == "/api/speech-log":
            self._send(200, {"log": h.speech_log[-80:]})
            return
        if path == "/api/stage":
            self._send(200, {"interstitials": h.state.get("interstitials", {}),
                             "channels": h.state.get("channels", {})})
            return
        if path.startswith("/api/audio/"):
            name = os.path.basename(path)
            for base in (os.path.join(h.runtime_dir, "audio"),
                         os.path.join(h.runtime_dir, "personas"),
                         os.path.join(h.runtime_dir, "sample-library"),
                         os.path.join(h.runtime_dir, "assets")):
                p = os.path.join(base, name)
                if os.path.exists(p):
                    self._send(200, open(p, "rb").read(), "audio/wav")
                    return
            self._send(404, {"error": "not found"})
            return
        if path.startswith("/api/art/"):
            pid = path.rsplit("/", 1)[-1]
            p = os.path.join(h.runtime_dir, "personas", pid + ".svg")
            if os.path.exists(p):
                self._send(200, open(p, "rb").read(), "image/svg+xml")
                return
            self._send(404, {"error": "no portrait"})
            return
        # -------- peer protocol (sovereign hubs) --------
        if path == "/peer/hello":
            self._send(200, {"node": h.node_id, "network": h.network_id,
                             "peer": True, "app": "chorus",
                             "consentSurface": "/peer/join — present invite key"})
            return
        if path == "/peer/export":
            since = int(q.get("since", 0))
            self._send(200, h.fleet.export_delta(since))
            return
        if path == "/peer/map":
            mp = os.path.join(h.runtime_dir, "network-map.json")
            self._send(200, json.load(open(mp)) if os.path.exists(mp) else {})
            return
        self._send(404, {"error": "no such route", "path": path})
    def _need_view(self, n):
        return {"id": n["id"], "kind": n["kind"], "needId":
                n["claim"].get("needId"),
                "requirement": n["claim"].get("requirement"),
                "subject": n["claim"].get("subject"),
                "status": n["claim"].get("status"),
                "priority": n["claim"].get("priority"),
                "openedAt": n["claim"].get("openedAt")}
    def _persona_view(self, p):
        return {"id": p["id"], "name": p["name"], "role": p.get("role"),
                "register": p.get("register"), "confidence": p["confidence"],
                "voice": p.get("voice"), "ack": p.get("ack"),
                "portrait": p.get("portrait"), "shipped": p.get("shipped"),
                "imitation": p.get("imitation"), "imitates": p.get("imitates"),
                "sources": p.get("sources"), "domains": p.get("domains"),
                "interests": p.get("interests"),
                "characterization": p.get("characterization")}
    def _state(self):
        h = self.host
        conv = h.state.get("conversation", [])
        return {
            "node": h.node_id, "network": h.network_id,
            "honesty": h.honesty(),
            "roster": [self._persona_view(p) for p in h.roster_order()],
            "selected": h.roster_selected,
            "selector": h.selector_state(),
            "threshold": h.conf_threshold(),
            "depth": h.response_depth(),
            "needs": [self._need_view(n) for n in h.needs.floor()],
            "metCount": len([r for r in h.book.current()
                             if r["kind"].startswith("need:") and
                             r["claim"].get("status") == "fulfilled"]),
            "liveness": h.steward.liveness() if h.steward else None,
            "topic": h.state.get("topic"),
            "conversation": conv[-30:],
            "focusNeed": h.state.get("focus_need"),
            "theme": h.state.get("settings", {}).get("ui:theme", "light"),
            "rows": h.book.count(),
            "discoveryState": h.fleet.discovery["state"],
            "gate": json.load(open(os.path.join(h.runtime_dir, "gate.json")))
            if os.path.exists(os.path.join(h.runtime_dir, "gate.json")) else None,
        }
    def _library(self):
        h = self.host
        lists = [r["claim"] for r in h.book.current_of("list:object")]
        workshops = [r["claim"] for r in h.book.current_of("workshop:imported")] + \
                    [r["claim"] for r in h.book.current_of("workshop:created")]
        return {
            "personas": [self._persona_view(p) for p in h.roster_order()],
            "tools": [{"componentId": k, **v} for k, v in h.tool_catalog.items()],
            "lists": [{"subject": l.get("subject"), "members": l.get("members", []),
                       "memberCount": l.get("memberCount"),
                       "nonMatchCount": l.get("nonMatchCount"),
                       "criteria": l.get("criteria")} for l in lists],
            "workshops": workshops,
            "sources": [{"key": k, "name": v.get("name"),
                         "admitted": v.get("admitted")}
                        for k, v in h.sources.items()],
            "packages": [r["claim"] for r in h.book.current_of("exchange:exported")],
        }
    # ---------- POST ----------
    def do_POST(self):
        try:
            self._do_POST()
        except Exception:
            import traceback
            try:
                self._send(500, {"error": "internal",
                                 "trace": traceback.format_exc()[-900:]})
            except Exception:
                pass
    def _do_POST(self):
        path, q = self._route()
        body = self._json()
        h = self.host
        if path == "/api/chat":
            text = (body.get("text") or "").strip()
            if not text:
                self._send(400, {"error": "empty input"})
                return
            h.turn_in_flight = True
            try:
                result = chat_mod.run_turn(
                    h, text, body.get("selector") or h.selector_state())
            finally:
                h.turn_in_flight = False
            self._send(200, result)
            return
        if path == "/api/roster/select":
            h.roster_selected = body.get("id")
            h.book.append("chat:select", {"subject": body.get("id")},
                          claimant="principal", certainty=1.0,
                          basis="user-choice")
            self._send(200, {"selected": h.roster_selected})
            return
        if path == "/api/roster/move":
            res = per.dyadic_move(h, body.get("id"), body.get("dir", "up"))
            self._send(200, res or {"moved": False, "reason": "unknown id"})
            return
        if path == "/api/persona/mint":
            p, row, accepted, suggestion = per.mint(
                h, body.get("name", "Persona"),
                declared_domains=body.get("domains"),
                interests=body.get("interests"),
                register=body.get("register"),
                accept_source=body.get("accept_source", True))
            if per.is_recognizable(p["name"]):
                per.mark_imitation(h, p, p["name"])
            self._send(200, {"persona": self._persona_view(p),
                             "row": row["id"], "sourceAccepted": accepted,
                             "suggestion": suggestion})
            return
        if path == "/api/persona/source-suggest":
            sugg = h.needs.find_open("need:source-suggest",
                                     subject=body.get("id"))
            if not sugg:
                self._send(200, {"suggestion": None})
                return
            p = h.personas.get(body.get("id"))
            if body.get("accept") and p:
                per.grant_source(h, p, sugg[0]["claim"]["slots"]["source"])
                h.needs.close(sugg[0], "accepted",
                              {"bound": sugg[0]["claim"]["slots"]["source"]})
                self._send(200, {"bound": sugg[0]["claim"]["slots"]["source"]})
            else:
                h.needs.close(sugg[0], "declined",
                              {"declared": "persona source-free by choice"})
                self._send(200, {"declined": True,
                                 "declared": "persona stays source-free"})
            return
        if path == "/api/persona/edit":
            p = h.personas.get(body.get("id"))
            if not p:
                self._send(404, {"error": "no persona"})
                return
            for k in ("name", "register", "interests", "domains", "role"):
                if k in body:
                    p[k] = body[k]
            if "voice" in body:     # user direction only — stable otherwise
                p["voice"] = {"name": body["voice"], "engine": "sapi",
                              "stable": True, "byUser": True}
            per.save_persona(h, p)
            h.book.append("persona:edited", {
                "subject": p["id"], "name": p["name"],
                "fields": [k for k in body if k != "id"]},
                claimant="principal", certainty=1.0, basis="user-choice")
            self._send(200, {"persona": self._persona_view(p)})
            return
        if path == "/api/selector":
            row = h.set_selector(body.get("ids", []))
            self._send(200, {"selector": h.selector_state(), "row": row["id"]})
            return
        if path == "/api/settings":
            key, val = body.get("key"), body.get("value")
            row = h.set_setting(key, val)
            self._send(200, {"set": key, "value": val,
                             "assertion": row["id"],
                             "depth": h.response_depth()})
            return
        if path == "/api/conversation/reset":
            h.reset_conversation()
            self._send(200, {"reset": True})
            return
        if path == "/api/needs/focus":
            target = None
            for n in h.needs.floor():
                if n["claim"].get("needId") == body.get("needId") or \
                        n["id"] == body.get("id"):
                    target = n
            if not target:
                self._send(404, {"error": "need not open"})
                return
            h.needs.focus(target)
            self._send(200, {"focused": target["claim"].get("needId")})
            return
        if path == "/api/needs/fill":
            fid = h.state.get("focus_need")
            tgt = None
            for n in h.needs.floor():
                if n["claim"].get("needId") == fid or \
                        n["claim"].get("needId") == body.get("needId"):
                    tgt = n
            if not tgt:
                self._send(404, {"error": "no focused need"})
                return
            h.needs.fill_slot(tgt, body.get("slot", "value"),
                              body.get("value"))
            self._send(200, {"filled": body.get("slot", "value")})
            return
        if path == "/api/tools/compete":
            tgt = None
            for n in h.needs.floor():
                if n["claim"].get("needId") == body.get("needId") or \
                        n["id"] == body.get("id"):
                    tgt = n
            if not tgt:
                tgt = {"id": "ad-hoc", "claim": {
                    "criteria": body.get("criteria"),
                    "requirement": body.get("requirement", "")}}
            row = h.needs.compete(tgt)
            self._send(200, {"comparison": row["claim"],
                             "row": row["id"]})
            return

        if path == "/api/needs/cancel":
            for n in h.needs.floor():
                if n["claim"].get("needId") == body.get("needId"):
                    h.needs.close(n, "cancelled", {"by": "user"})
                    self._send(200, {"cancelled": True})
                    return
            self._send(404, {"error": "need not open"})
            return
        if path == "/api/sources/admit":
            verdict = src_mod.admit_source(body)
            h.book.append("source:admission", {
                "subject": body["key"], "admitted": verdict["admitted"],
                "checks": verdict["checks"],
                "verdictBasis": verdict["basis"]},
                claimant="host", certainty=0.9, basis="execution-evidence")
            if verdict["quarantined"]:
                h.book.append("source:quarantine", {
                    "subject": body["key"], "basis": verdict["basis"]},
                    claimant="host", basis="execution-evidence")
            self._send(200, verdict)
            return
        if path == "/api/sources/add":
            key = body.get("key") or f"source-{body['name'].lower().replace(' ', '-')}"
            entry = {"key": key, "name": body["name"],
                     "kind": body.get("kind", "web"), "url": body["url"],
                     "api": body.get("api"), "domains": body.get("domains", []),
                     "descriptor": body.get("descriptor", "granted_only"),
                     "ceiling": body.get("ceiling", 0.5)}
            verdict = src_mod.admit_source(entry)
            h.book.append("source:admission", {
                "subject": key, "admitted": verdict["admitted"],
                "checks": verdict["checks"],
                "verdictBasis": verdict["basis"]},
                claimant="host", certainty=0.9, basis="execution-evidence")
            if verdict["admitted"]:
                h.sources[key] = {**entry, "admitted": True}
                h.book.append("source:configured", {
                    "subject": key, "name": entry["name"], "kind": entry["kind"],
                    "endpoint": entry.get("api") or entry["url"],
                    "domains": entry["domains"], "descriptor": entry["descriptor"],
                    "ceiling": entry["ceiling"], "userAdded": True},
                    claimant="principal", certainty=1.0, basis="user-choice")
            else:
                h.book.append("source:quarantine", {
                    "subject": key, "basis": verdict["basis"]},
                    claimant="host", basis="execution-evidence")
            self._send(200, verdict)
            return
        # -------- fleet --------
        if path == "/api/fleet/discover":
            if h.fleet.discovery["state"] == "scanning":
                self._send(200, {"state": "already-scanning"})
                return
            threading.Thread(target=h.fleet.run_discovery,
                             kwargs={"transports": ("lan", "bt")},
                             daemon=True).start()
            self._send(200, {"state": "in-progress", "transports": ["lan", "bt"]})
            return
        if path == "/api/fleet/invite":
            rec, row = h.fleet.invite(body.get("ip"), body.get("name"))
            self._send(200, {"invite": rec, "row": row["id"],
                             "legible": self._legible("invite", rec)})
            return
        if path == "/api/fleet/install":
            rec = h.fleet.install(body.get("ip"))
            self._send(200, {"install": rec,
                             "legible": self._legible("install", rec)})
            return
        if path == "/api/fleet/sync":
            out = h.fleet.sync_with(body.get("ip"))
            self._send(200, out)
            return
        if path == "/api/fleet/map":
            m = h.fleet._write_map(h.fleet.discovery["results"])
            self._send(200, {"map": m, "legible":
                             f"map written — {len(m['devices'])} devices, "
                             f"{m['members']} members"})
            return
        # -------- peer protocol --------
        if path == "/peer/join":
            key = body.get("inviteKey")
            invite = [r for r in h.book.current_of("fleet:invite")
                      if r["claim"].get("inviteKey") == key]
            if not invite:
                self._send(403, {"joined": False,
                                 "reason": "unknown invite key"})
                return
            node = body.get("from")
            m = h.fleet.member_join({"node": node, "ip": body.get("ip"),
                                     "role": body.get("role", "surface"),
                                     "at": body.get("at")})
            self._send(200, {"joined": True, "member": m["id"],
                             "network": h.network_id})
            return
        if path == "/peer/offer":
            out = h.fleet.offer_delta(body)
            self._send(200, out)
            return
        # -------- accounts / mail --------
        if path == "/api/accounts":
            row = exch.configure_account(
                h, body.get("kind", "imap"), body.get("address"),
                body.get("secret"), body.get("imap"), body.get("smtp"))
            self._send(200, {"configured": True, "row": row["id"],
                             "secretHeld": "local credential store only"})
            return
        # -------- publishing / exchange --------
        if path == "/api/publish":
            out = exch.publish(h, body.get("holding"), body.get("form"))
            self._send(200, out)
            return
        if path == "/api/exchange/export":
            pkg, path_ = exch.export_package(h, body.get("what", "library-sample"))
            self._send(200, {"package": pkg, "file": path_})
            return
        if path == "/api/exchange/import":
            n = exch.import_package(h, body.get("package", {}),
                                    body.get("origin", "file"))
            self._send(200, {"imported": n, "belowThreshold": True})
            return
        # -------- artifacts --------
        if path == "/api/artifacts/workshop":
            w = art.make_workshop(h, body.get("name", "workshop"),
                                  persona_id=body.get("persona"),
                                  tool_ids=body.get("tools"),
                                  text=body.get("text", ""),
                                  style=body.get("style"))
            self._send(200, {"workshop": w})
            return
        if path == "/api/artifacts/encode":
            w = body.get("workshop")
            meta = art.encode_workshop(h, w, os.path.join(
                h.runtime_dir, "artifacts"))
            self._send(200, meta)
            return
        if path == "/api/artifacts/capture":
            out = art.capture_artifact(h, body.get("path"))
            self._send(200, out)
            return
        if path == "/api/artifacts/decode":
            dec = art.decode_rastgrid(body.get("path"))
            self._send(200, {"payload": dec["payload"].decode("utf-8", "replace"),
                             "crcOk": dec["crcOk"], "modules": dec["modules"]})
            return
        if path == "/api/artifacts/adopt":
            row = art.adopt_workshop(h, body.get("rowId"))
            self._send(200, {"adopted": bool(row), "row": row["id"] if row else None})
            return
        if path == "/api/artifacts/republish":
            wrow = h.book.get(body.get("rowId"))
            if not wrow:
                self._send(404, {"error": "no workshop row"})
                return
            meta = art.republish(h, wrow, os.path.join(h.runtime_dir, "artifacts"))
            self._send(200, meta)
            return
        # -------- stage --------
        if path == "/api/stage/interstitial":
            iid = stg.request_interstitial(h, body.get("topic", "topic"),
                                           origin=body.get("origin", "user-request"))
            self._send(200, {"interstitial": iid})
            return
        if path == "/api/stage/rework":
            st = stg.rework_interstitial(h, body.get("id"), body.get("topic"))
            self._send(200, st or {"error": "unknown interstitial"})
            return
        if path == "/api/stage/present":
            out = stg.present_interstitial(h, body.get("id"))
            self._send(200, out)
            return
        if path == "/api/stage/scene":
            out = stg.enact_scene(h, body.get("scene", "knock-knock"))
            self._send(200, out)
            return
        if path == "/api/channels":
            ch = stg.open_channel(h, body.get("name", "hum"))
            self._send(200, ch)
            return
        if path == "/api/list":
            # iterate the formal list object (C-FormalList usable as import)
            lid = body.get("listId")
            lst = h.book.get(lid)
            if not lst:
                for r in reversed(h.book.current_of("list:object")):
                    lst = r
                    break
            if not lst:
                self._send(404, {"error": "no list object"})
                return
            c = lst["claim"]
            self._send(200, {"subject": c.get("subject"),
                             "members": c.get("members", []),
                             "memberCount": c.get("memberCount"),
                             "nonMatches": c.get("nonMatches", []),
                             "criteria": c.get("criteria"),
                             "iterable": True})
            return
        if path == "/api/seed/consent":
            out = seed.stage_consent(h, bool(body.get("allowed")))
            self._send(200, out)
            return
        if path == "/api/seed/mint-gen2":
            media = body.get("media") or os.path.splitdrive(h.root)[0] + "\\"
            out = seed.mint_gen2(h, media)
            self._send(200, out)
            return
        if path == "/api/shutdown":
            self._send(200, {"bye": True})
            threading.Timer(0.4, lambda: os._exit(0)).start()
            return
        self._send(404, {"error": "no such route", "path": path})
    def _legible(self, action, rec):
        """Fleet outcomes in user-legible form (C-LegibleOutcome)."""
        if action == "invite":
            st = rec.get("state")
            if st == "member":
                return f"{rec['ip']} joined the network."
            if st == "peer-found":
                return (f"{rec['ip']} runs a peer — finish join on its "
                        f"consent surface with the invite key.")
            return (f"{rec['ip']} invited — pending. {rec.get('next','')}")
        if action == "install":
            if rec.get("adminShare") == "reachable":
                return f"{rec['ip']}: admin share reachable — install path open."
            return f"{rec['ip']}: install pending — {rec.get('directions','')}"
        return str(rec)
def probe_instance(port, timeout=1.5):
    """Launch hygiene: probe the port for a live chorus instance."""
    try:
        import urllib.request
        with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/api/hello", timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None
def port_in_use(port):
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", port))
        s.close()
        return False
    except OSError:
        return True
def serve(host, port, ui_dir):
    Handler.host = host
    Handler.ui_dir = ui_dir
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    httpd.daemon_threads = True
    # peer protocol shares the app port: /peer/* handled above; also bind
    # the peer port for fleet exchange
    peer_port = int(os.environ.get("CHORUS_PEER_PORT", "7871"))
    peerd = None
    if peer_port != port:
        try:
            peerd = ThreadingHTTPServer(("0.0.0.0", peer_port), Handler)
            peerd.daemon_threads = True
            threading.Thread(target=peerd.serve_forever, daemon=True).start()
        except OSError:
            peerd = None
    return httpd, peerd
