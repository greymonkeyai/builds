"""shell — launch, readiness gate serving, host runtime, operator
surface, library, status bar, theme, presentation, honesty
declarations, progress/legible outcomes (module: shell).

The operator surface hosts every other module's surface obligations —
each must render. Launch hygiene: probe-before-bind, exclusive bind,
refuse-while-owned, close-terminates. Runtime surfaces declare
capability honestly (C-HonestyBanner, C-DeclaredStubs); outcomes are
user-legible, never raw JSON (C-LegibleOutcome). Presentation decisions
resolve through a declared common choice set recorded as ledger
assertions (C-DeclaredPresentation); named settings preloads are
assertion bundles over that choice set (C-SettingsPreloads,
C-PreloadSuite ≥3).
"""

import json
import os
import re
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

THEMES = {
    "light": {"bg": "#f4f1ea", "ink": "#22201b", "panel": "#fffdf7",
              "edge": "#cfc9b8", "accent": "#6a4d2e"},
    "dark": {"bg": "#17181c", "ink": "#e6e3da", "panel": "#22242a",
             "edge": "#3a3d46", "accent": "#c8a15a"},
    "sepia": {"bg": "#e9ddc4", "ink": "#3d2f1d", "panel": "#f3e9d2",
              "edge": "#b8a073", "accent": "#7a4b1f"},
    "contrast": {"bg": "#000000", "ink": "#ffffff", "panel": "#101010",
                 "edge": "#ffffff", "accent": "#ffff00"},
}
STYLES = {"concise": "one short sentence", "balanced": "1-3 sentences",
          "expansive": "up to 4 sentences with color"}
PRELOADS = {
    "porch-1957": {"theme": "sepia", "response-style": "concise",
                   "response-depth": 1},
    "studio-2012": {"theme": "dark", "response-style": "balanced",
                    "response-depth": 2},
    "signal-2031": {"theme": "contrast", "response-style": "expansive",
                    "response-depth": 3},
}


def _json_body(handler):
    ln = int(handler.headers.get("Content-Length") or 0)
    if not ln:
        return {}
    try:
        return json.loads(handler.rfile.read(ln).decode("utf-8", "replace"))
    except Exception:
        return {}


def make_handler(host):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        # ---------- plumbing ----------
        def _send(self, code, body, ctype="application/json", raw=None):
            data = raw if raw is not None else json.dumps(
                body, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Connection", "close")
            self.end_headers()
            try:
                self.wfile.write(data)
            except Exception:
                pass
            self.close_connection = True

        def _blocked(self, name):
            if host.endpoint_blocked(name):
                self._send(503, {"ok": False,
                                 "declared": f"endpoint '{name}' stubbed by sabotage",
                                 "sabotage": True})
                return True
            return False

        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            path, qs = u.path, urllib.parse.parse_qs(u.query)
            try:
                self._get(path, qs)
            except Exception as e:
                self._send(500, {"ok": False, "error": str(e)})

        def do_POST(self):
            u = urllib.parse.urlparse(self.path)
            body = _json_body(self)
            try:
                self._post(u.path, body)
            except Exception as e:
                self._send(500, {"ok": False, "error": str(e)})

        # ---------- GET ----------
        def _get(self, path, qs):
            if path == "/api/health":
                self._send(200, {"ok": True, "app": "vesta", "bare": False,
                                 "node": host.node_id, "part2": True,
                                 "gate": bool(host.gate_result.get("passed"))})
            elif self._blocked(path):
                return
            elif path == "/":
                self._page()
            elif path == "/api/state":
                self._send(200, self._state())
            elif path == "/api/gate":
                self._send(200, host.gate_result)
            elif path == "/api/roster":
                self._send(200, {"ok": True, "roster": host.personas.roster()})
            elif path == "/api/floor":
                self._send(200, {"ok": True,
                                 "needs": list(host.needs.open_needs().values())})
            elif path == "/api/library":
                self._send(200, {"ok": True, "holdings": self._library()})
            elif path == "/api/sources":
                self._send(200, {"ok": True,
                                 "sources": list(host.ledger.view()["sources"].values())})
            elif path == "/api/voices":
                self._send(200, {"ok": True, "catalog": host.personas.voice_catalog(),
                                 "declared": "thin pool" if len(host.engines.get("voices") or []) < 4 else "ok"})
            elif path == "/api/email":
                self._send(200, host.sources.mail_read())
            elif path == "/api/fleet":
                d = host.fleet.discovery
                transports = d.get("transports") or {}
                order = sorted(transports, key=lambda k: transports[k].get("order", 9))
                self._send(200, {"ok": True,
                                 "discovery": d,
                                 "members": list(host.ledger.view()["members"].values()),
                                 "candidates": d.get("devices", []),
                                 "transportOrder": order,
                                 "network": host.fleet.network,
                                 "map": os.path.join(host.dir, "network-map.json")})
            elif path == "/api/fleet/progress":
                d = host.fleet.discovery
                self._send(200, {"ok": True,
                                 "running": d.get("state") == "running",
                                 "finished": d.get("state") == "finished",
                                 "state": d.get("state"),
                                 "transport": (d.get("progress") or {}).get("transport"),
                                 "progress": d.get("progress"),
                                 "transports": d.get("transports"),
                                 "devices": d.get("devices")})
            elif path == "/api/fleet/roster":
                self._send(200, {"ok": True,
                                 "devices": host.fleet.discovery.get("roster", []),
                                 "expected": [e["id"] for e in host.fleet.EXPECTED_ROSTER]})
            elif path == "/api/stage/channels":
                chans = []
                for c in host.ledger.view()["channels"].values():
                    chans.append({"channel": c.get("channel"),
                                  "name": c.get("name"),
                                  "track": c.get("track"),
                                  "tracks": [c.get("track")] if c.get("track") else [],
                                  "file": c.get("file"),
                                  "state": "playing" if c.get("audioEngine") != "absent-declared"
                                           else "absent-declared"})
                self._send(200, {"ok": True, "channels": chans})
            elif path == "/api/stage":
                self._send(200, {"ok": True, **host.stage.presence(),
                                 "samples": host.stage.ensure_sample_library()})
            elif path == "/api/context":
                self._send(200, {"ok": True,
                                 "context": host.ledger.view()["context"]})
            elif path == "/api/replies":
                self._send(200, {"ok": True,
                                 "replies": host.ledger.view()["replies"][-40:]})
            elif path == "/api/metrics":
                mets = host.ledger.view()["metrics"]
                self._send(200, {"ok": True, "metrics": mets[-60:],
                                 "liveness": host.steward.liveness()})
            elif path == "/api/ledger":
                kind = (qs.get("kind") or [""])[0]
                lim = int((qs.get("limit") or ["80"])[0])
                rows = [r for r in host.ledger.snapshot()
                        if not kind or r.get("kind", "").startswith(kind)]
                self._send(200, {"ok": True, "rows": rows[-lim:],
                                 "total": host.ledger.count()})
            elif re.match(r"^/api/persona/[^/]+/portrait$", path):
                pid = path.split("/")[3]
                p = host.ledger.view()["personas"].get(pid, {})
                f = (p.get("portrait") or {}).get("file")
                if f and os.path.exists(f):
                    with open(f, "rb") as fh:
                        self._send(200, None, "image/svg+xml", raw=fh.read())
                else:
                    self._send(404, {"ok": False, "declared": "no portrait bound"})
            elif re.match(r"^/files/", path):
                self._file(path[len("/files/"):])
            elif path == "/api/preloads":
                cache = host.exchange.preload_cache()
                preloads = [{"kind": "settings-preload", "name": n, "slots": s}
                            for n, s in PRELOADS.items()]
                for k, v in (cache.get("vettedPointers") or {}).items():
                    preloads.append({"kind": "vetted-source", "key": k, "url": v})
                for d in cache.get("decoders") or []:
                    preloads.append({"kind": "decoder", **d})
                for e in cache.get("exemplars") or []:
                    preloads.append({"kind": "exemplar", "name": e.get("name"),
                                     "exemplarKind": e.get("kind"),
                                     "contains": e.get("contains")})
                self._send(200, {"ok": True, "preloads": preloads})
            else:
                self._send(404, {"ok": False, "error": f"no such path {path}"})

        # ---------- POST ----------
        def _post(self, path, b):
            if self._blocked(path):
                return
            if path == "/api/chat":
                self._send(200, {"ok": True, **host.conversation.turn(b.get("text", ""))})
            elif path == "/api/persona/create":
                pid = host.personas.create(
                    b.get("name", "Unnamed"), register=b.get("register"),
                    character=b.get("character"), interests=b.get("interests"),
                    imitate=b.get("imitate"), history=b.get("history"),
                    domains=b.get("domains"))
                sugg = host.personas.suggest_sources(b.get("domains") or b.get("interests") or [])
                self._send(200, {"ok": True, "persona": pid,
                                 "sourceSuggestions": sugg})
            elif path == "/api/persona/select":
                self._send(200, host.personas.select(b.get("id")))
            elif path == "/api/persona/edit":
                self._send(200, host.personas.edit(b.get("id"), b.get("fields") or {}))
            elif path == "/api/persona/voice":
                self._send(200, host.personas.user_assign_voice(b.get("id"), b.get("voiceId")))
            elif path == "/api/persona/source-grant":
                self._send(200, host.personas.grant_source(
                    b.get("id"), b.get("source"), bool(b.get("accept", True))))
            elif path == "/api/roster/move":
                self._send(200, host.personas.move(b.get("id"), b.get("direction", "up")))
            elif path == "/api/need/focus":
                host.needs.focus(b.get("id"))
                self._send(200, {"ok": True})
            elif path == "/api/need/fill":
                host.needs.fill_slot(b.get("id"), b.get("slot"), b.get("value"))
                self._send(200, {"ok": True})
            elif path == "/api/need/cancel":
                host.needs.cancel(b.get("id"))
                self._send(200, {"ok": True})
            elif path == "/api/need/fulfill":
                host.needs.fulfill(b.get("id"), result=b.get("result"), by="user")
                self._send(200, {"ok": True})
            elif path == "/api/need/candidate":
                host.needs.candidate(b.get("id"), b.get("slot"), b.get("value"),
                                     b.get("source"), b.get("confidence", 0.6))
                self._send(200, {"ok": True,
                                 "ranked": host.needs.candidates_for(b.get("id"))})
            elif path == "/api/settings":
                host.ledger.append("settings:set",
                                   {"setting": b.get("setting"), "value": b.get("value")},
                                   claimant="principal", basis="user-set", certainty=1.0)
                self._send(200, {"ok": True})
            elif path == "/api/settings/depth":
                host.conversation.set_depth(b.get("n", 2))
                self._send(200, {"ok": True, "depth": b.get("n")})
            elif path == "/api/settings/selector":
                host.conversation.set_selector(b.get("ids") or [])
                self._send(200, {"ok": True, "selector": host.conversation.selector})
            elif path == "/api/settings/preload":
                self._preload(b.get("name"))
            elif path == "/api/accounts":
                self._send(200, host.sources.configure_account(
                    b.get("name"), b.get("kind", "imap"), b.get("host"),
                    b.get("user"), b.get("secret")))
            elif path == "/api/email/context":
                self._email_context(b.get("id"))
            elif path == "/api/sources/admit":
                if b.get("all"):
                    self._send(200, {"ok": True, "results": host.sources.admit_all(limit=b.get("limit"))})
                else:
                    self._send(200, host.sources.admit(b.get("key")))
            elif path == "/api/sources/import":
                self._send(200, {"ok": True, "sources": list(host.sources.import_seed(force=True).keys())})
            elif path == "/api/fleet/discover":
                d = host.fleet.discovery
                if b.get("background"):
                    if d["state"] != "running":
                        threading.Thread(target=host.fleet.discover, daemon=True).start()
                    self._send(200, {"ok": True, "state": "running",
                                     "progress": d.get("progress")})
                elif d["state"] == "running":
                    self._send(200, {"ok": True, "state": "running",
                                     "progress": d.get("progress")})
                elif d["state"] == "finished" and not b.get("refresh"):
                    devs = d.get("devices", [])
                    tr = d.get("transports") or {}
                    self._send(200, {"ok": True, "state": "finished",
                                     "candidates": devs, "devices": devs,
                                     "transports": [
                                         {"kind": ("wired-lan" if k == "lan" else k),
                                          **v} for k, v in tr.items()]})
                else:
                    result = host.fleet.discover()
                    tr = result.get("transports") or {}
                    devs = result.get("devices", [])
                    self._send(200, {"ok": True, "state": "finished",
                                     "candidates": devs, "devices": devs,
                                     "transports": [
                                         {"kind": ("wired-lan" if k == "lan" else k),
                                          **v} for k, v in tr.items()]})
            elif path == "/api/fleet/invite":
                self._send(200, host.fleet.invite(b.get("ip") or b.get("node")))
            elif path == "/api/fleet/install":
                self._send(200, host.fleet.install(b.get("ip") or b.get("node")))
            elif path == "/api/fleet/delta":
                self._send(200, host.fleet.send_delta(b.get("node") or b.get("ip")))
            elif path == "/api/fleet/map":
                path_m = host.fleet.write_map()
                m = host.fleet.discovery
                members = list(host.ledger.view()["members"].values())
                member_ips = {x.get("ip") for x in members}
                nonmembers = [d2 for d2 in m.get("devices", [])
                              if d2.get("ip") not in member_ips]
                rendered = ("network map — members: "
                            + ", ".join(x.get("node", "?") for x in members)
                            + " | non-members: "
                            + ", ".join(d2.get("ip", "?") for d2 in nonmembers))
                self._send(200, {"ok": True, "file": path_m,
                                 "map": {"node": host.node_id, "members": members,
                                         "nonMembers": nonmembers,
                                         "devices": m.get("devices", []),
                                         "roster": m.get("roster", [])},
                                 "rendered": rendered})
            elif path == "/api/fleet/mint":
                drive = b.get("drive") or b.get("seedDir")
                self._send(200, host.fleet.mint_seed(drive))
            elif path == "/api/fleet/seed-run":
                self._send(200, host.fleet.seed_run(b.get("seedDir")))
            elif path == "/api/fleet/seed-stage" or path == "/api/seed/stage":
                self._send(200, host.fleet.seed_stage(
                    bool(b.get("consent")), b.get("targetDir")))
            elif path == "/api/stage/channel":
                self._send(200, host.stage.open_channel(b.get("name", "ambient"),
                                                        b.get("track")))
            elif path == "/api/stage/interstitial":
                act = b.get("action", "queue")
                iid = b.get("id")
                if act == "queue":
                    iid = host.stage.queue_interstitial(b.get("title", "untitled"),
                                                        b.get("needs"), b.get("style"))
                    self._send(200, {"ok": True, "interstitial": iid})
                elif act == "collect":
                    self._send(200, host.stage.collect_interstitial(iid))
                elif act == "rework":
                    self._send(200, host.stage.rework_interstitial(iid, b.get("changed")))
                elif act == "present":
                    self._send(200, host.stage.present_interstitial(iid))
                else:
                    self._send(400, {"ok": False})
            elif path == "/api/stage/scene":
                self._send(200, host.stage.enact_scene(
                    cast=b.get("cast"), scene=b.get("scene", "knock-knock")))
            elif path == "/api/stage/collect":
                self._send(200, host.stage.collect_for_persona(b.get("persona")))
            elif path == "/api/stage/present":
                self._send(200, host.stage.present_for_persona(b.get("persona")))
            elif path == "/api/conversation/reset":
                self._send(200, host.conversation.reset())
            elif path == "/api/speak":
                self._send(200, host.conversation.speak(b.get("text", ""), b.get("persona")))
            elif path == "/api/publish":
                self._send(200, host.exchange.publish(b.get("holding"), b.get("form")))
            elif path == "/api/exchange/encode":
                if b.get("workshop"):
                    self._send(200, host.exchange.republish(b.get("workshop")))
                else:
                    self._send(200, host.exchange.encode(b.get("holding")))
            elif path == "/api/exchange/encode-tool":
                self._send(200, host.exchange.encode_tool(b.get("composition")))
            elif path == "/api/exchange/decode":
                data = b.get("data")
                if data:
                    import base64
                    self._send(200, host.exchange.decode(base64.b64decode(data)))
                else:
                    self._send(200, host.exchange.decode(b.get("file")))
            elif path == "/api/exchange/republish":
                self._send(200, host.exchange.republish(b.get("workshop")))
            elif path == "/api/tools/compose":
                self._send(200, host.tools.compose(b.get("name"), b.get("steps") or [], b.get("by", "ai")))
            elif path == "/api/tools/run":
                self._send(200, host.tools.run_composition(b.get("composition"), b.get("args") or {}))
            elif path == "/api/tools/invoke":
                self._send(200, host.tools.invoke(b.get("tool"), b.get("args") or {}))
            elif path == "/api/cleanup":
                self._send(200, {"ok": True, **host.ledger.cleanup()})
            else:
                self._send(404, {"ok": False, "error": f"no such path {path}"})

        # ---------- helpers ----------
        def _page(self):
            p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "ui", "index.html")
            with open(p, "rb") as f:
                self._send(200, None, "text/html; charset=utf-8", raw=f.read())

        def _file(self, rel):
            root = os.path.abspath(host.dir)
            p = os.path.abspath(os.path.join(root, rel))
            if not p.startswith(root) or not os.path.exists(p):
                self._send(404, {"ok": False})
                return
            ctype = "audio/wav" if p.endswith(".wav") else \
                "image/png" if p.endswith(".png") else \
                "image/svg+xml" if p.endswith(".svg") else "application/octet-stream"
            with open(p, "rb") as f:
                self._send(200, None, ctype, raw=f.read())

        def _state(self):
            v = host.ledger.view()
            settings = {k: s.get("value") for k, s in v["settings"].items()}
            theme = settings.get("theme", "light")
            return {
                "ok": True, "app": "vesta", "node": host.node_id,
                "uptimeS": round(time.time() - host.booted_at, 1),
                "engines": host.engine_mode(),
                "gate": host.gate_result,
                "settings": settings,
                "theme": THEMES.get(theme, THEMES["light"]),
                "themeName": theme, "themes": list(THEMES),
                "style": settings.get("response-style", "balanced"),
                "styles": STYLES, "preloads": PRELOADS,
                "depth": host.conversation.depth(),
                "selector": host.conversation.selector,
                "roster": host.personas.roster(),
                "needs": list(v["needs_open"].values()),
                "sourceCount": len(v["sources"]),
                "liveness": host.steward.liveness(),
                "context": v["context"],
                "honesty": self._honesty(v),
                "sabotage": sorted(host.sabotage) or None,
            }

        def _honesty(self, v):
            decl = []
            e = host.engines
            if not e["llm"].get("live"):
                decl.append("llm=absent — replies are declared-fallback")
            if not e.get("tts"):
                decl.append("tts=absent — speech floor still serializes")
            if len(e.get("voices") or []) < 4:
                decl.append(f"voice pool thin ({len(e.get('voices') or [])} base voices)")
            if not e.get("bt", {}).get("radio"):
                decl.append("bluetooth=absent or no devices")
            decl.append("stt=absent — no server-side speech input")
            decl.append("ledger=durable (append-only jsonl)")
            return decl

        def _library(self):
            v = host.ledger.view()
            return {
                "personas": [{"id": p["id"], "name": p.get("name"),
                              "register": p.get("register")}
                             for p in host.personas.roster()],
                "tools": [{"id": t.get("tool"), "purpose": t.get("purpose"),
                           "explanation": t.get("explanation")}
                          for t in v["tools"].values()],
                "compositions": [{"id": c.get("composition"), "name": c.get("name"),
                                  "components": c.get("components")}
                                 for c in v["compositions"].values()],
                "lists": [{"id": l["id"], "title": l["title"],
                           "members": len(l["members"]),
                           "nonMatches": len(l["nonMatches"])}
                          for l in v["lists"].values()],
                "workshops": [{"id": w.get("workshop"), "text": (w.get("text") or "")[:80],
                               "imported": w.get("imported")}
                              for w in v["workshops"].values()],
                "sources": [{"key": s.get("source"), "name": s.get("name"),
                             "kind": s.get("kind"),
                             "admitted": (s.get("admission") or {}).get("admitted")}
                            for s in v["sources"].values()],
                "artifacts": [{"id": a.get("artifact"), "holding": a.get("holding"),
                               "symbology": a.get("symbology")}
                              for a in v["artifacts"].values()],
                "projects": [{"id": p["id"], "title": p.get("title"),
                              "state": p.get("state"), "goals": len(p.get("goals", []))}
                             for p in v["projects"].values()],
            }

        def _preload(self, name):
            bundle = PRELOADS.get(name)
            if not bundle:
                self._send(404, {"ok": False, "error": "no such preload"})
                return
            for k, val in bundle.items():
                host.ledger.append("settings:set",
                                   {"setting": k, "value": val, "preload": name},
                                   claimant="principal", basis="user-set",
                                   certainty=1.0)
            host.ledger.append("preload:applied",
                               {"setting": "preload", "value": name,
                                "slots": bundle},
                               claimant="principal", basis="user-set")
            if "response-depth" in bundle:
                host.conversation.set_depth(bundle["response-depth"])
            self._send(200, {"ok": True, "applied": bundle})

        def _email_context(self, mail_id):
            """Select a received email into conversational context; the
            active personality offers commentary."""
            mails = host.sources.mail_read()
            mail = next((m for m in mails.get("mails", [])
                         if m["id"] == mail_id or m.get("subject") == mail_id), None)
            if not mail:
                self._send(404, {"ok": False, "declared": "no such email"})
                return
            host.conversation.set_context(
                f"email: {mail.get('subject')} — from {mail.get('from')}",
                via="email-selection")
            host.ledger.append("email:context",
                               {"email": mail, "basis": mails.get("basis")},
                               claimant="principal", basis="user-set")
            roster = host.personas.roster()
            persona = roster[0] if roster else None
            commentary = None
            if persona:
                r = host.conversation.reply(
                    persona,
                    f"Comment on this email: subject '{mail.get('subject')}', "
                    f"from {mail.get('from')}, body excerpt: "
                    f"{(mail.get('body') or '')[:300]}",
                    {"kind": "chat", "addressed": []})
                commentary = r["text"]
            self._send(200, {"ok": True, "email": mail,
                             "basis": mails.get("basis"),
                             "commentary": commentary})

    return Handler


def serve(host):
    handler = make_handler(host)
    httpd = ThreadingHTTPServer(("127.0.0.1", host.port), handler)
    host._httpd = httpd
    httpd.serve_forever()


def run_bare(port, data):
    """Phase-0 baseline target: an EMPTY system. The port binds and
    /api/health reports bare:true; every other endpoint returns an
    honest 503. No gate passes, no modules mount — every check on the
    corpus goes red."""
    class Bare(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, obj):
            data2 = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data2)))
            self.send_header("Connection", "close")
            self.end_headers()
            try:
                self.wfile.write(data2)
            except Exception:
                pass
            self.close_connection = True

        def do_GET(self):
            if self.path == "/api/health":
                self._send(200, {"ok": True, "app": "vesta", "bare": True,
                                 "node": "bare", "part2": False, "gate": False})
            elif self.path == "/":
                body = "<html><body>vesta bare harness (no modules mounted)</body></html>".encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Connection", "close")
                self.end_headers()
                try:
                    self.wfile.write(body)
                except Exception:
                    pass
            else:
                self._send(503, {"ok": False, "declared": "module not mounted — bare system"})

        do_POST = do_GET

    print(f"vesta BARE harness on :{port} — no modules mounted")
    ThreadingHTTPServer(("127.0.0.1", port), Bare).serve_forever()
    return 0
