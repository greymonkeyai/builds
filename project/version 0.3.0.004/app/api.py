"""HTTP surface — the local web UI + JSON API + SSE event stream.

The SSE stream doubles as the window-presence signal for launch hygiene:
once a window has connected, closing the LAST one stops the program (grace
period) — no orphaned process (S-close-terminate). Headless runs pass
--no-watchdog.
"""
from __future__ import annotations

import json
import os
import queue
import re
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import archive, floor, builtins as B, model
from .connectors import CONNECTORS
from .temporal import classify as temporal_classify


UI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui")


class VantageServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False          # SO_REUSEADDR would re-enable
                                          # sharing on Windows

    def __init__(self, addr, handler, ctx, watchdog=True):
        self.ctx = ctx
        self.sse_clients = []
        self.window_seen = False
        self.watchdog = watchdog
        self.shutdown_timer = None
        super().__init__(addr, handler)

    def sse_add(self, q):
        self.sse_clients.append(q)
        self.window_seen = True
        if self.shutdown_timer:
            self.shutdown_timer.cancel()
            self.shutdown_timer = None

    def sse_drop(self, q):
        if q in self.sse_clients:
            self.sse_clients.remove(q)
        if self.watchdog and self.window_seen and not self.sse_clients:
            self.shutdown_timer = threading.Timer(
                6.0, self._shutdown_for_close)
            self.shutdown_timer.start()

    def _shutdown_for_close(self):
        if not self.sse_clients:
            threading.Thread(target=self.shutdown, daemon=True).start()

    def fanout(self, ev):
        for q in list(self.sse_clients):
            try:
                q.put_nowait(ev)
            except queue.Full:
                pass


def _json_bytes(o):
    return json.dumps(o, ensure_ascii=False).encode("utf-8")


def _roster_entry(ctx, p):
    return {"id": p["id"], "name": p["name"], "traits": p["traits"],
            "interests": p["interests"], "register": p["register"],
            "lens": p["lens"], "voice": p.get("voice"), "color": p["color"],
            "mark": p.get("mark"), "frame": p.get("frame"),
            "art": (p.get("art") or {}),
            "heldConfidence": ctx.personas.held_confidence(p["id"]),
            "characterization": p.get("characterization")}


def state(ctx) -> dict:
    led = ctx.ledger
    floor_state = {"depth": ctx.floor.depth,
                   "played": ctx.floor.played[-10:]}
    emails = [a.value.get("v") for a in led.query(
        predicate="email:message", limit=50)]
    theme = led.resolve("config", "ui:shell-theme")
    frame = led.resolve("config", "user:persona-frame")
    depth = led.resolve("config", "chat:response-depth")
    projects = [{"id": a.subject.split(":", 1)[1],
                 **(a.value.get("v") or {})}
                for a in led.query(predicate="project:profile", limit=50)]
    chat = [e for e in ctx.bus.events if e["kind"] == "persona.speak"][-40:]
    ctxrow = archive.context(led)
    return {
        "version": "0.3.0.004", "app": "Vantage",
        "gate": {"passed": ctx.gate.passed if ctx.gate else None,
                 "timeToGateMs": ctx.gate.time_to_gate_ms if ctx.gate
                 else None},
        "theme": theme.value.get("v") if theme else "light",
        "frame": frame.value.get("v") if frame else "respondent",
        "responseDepth": depth.value.get("v") if depth else 2,
        "roster": [_roster_entry(ctx, p) for p in ctx.personas.roster()],
        "active": ctx.personas.data.get("active"),
        "chat": chat,
        "topic": archive.topic(led),
        "context": ctxrow,
        "focusNeed": floor.focused_need(led),
        "needs": ctx.open_needs(),
        "projects": projects,
        "inbox": emails,
        "speechFloor": floor_state,
        "engines": ctx.engines.honesty(),
        "connectors": {k: v["title"] + (" (declared-absent)"
                       if v["kind"] == "declared-absent" else "")
                       for k, v in CONNECTORS.items()},
        "manifest": ctx.tools.manifest(),
        "steward": {"interval": ctx.steward.interval,
                    "running": ctx.steward.running,
                    "last": ctx.steward.last_run},
        "preloads": sorted(B.PRELOADS),
    }


def holdings(ctx) -> dict:
    """Library holdings (G-D): browsable, inspectable content — personas,
    tools, packages, artifacts — not a raw log view."""
    led = ctx.ledger
    arts = []
    adir = os.path.join(ctx.runtime, "artifacts")
    for dp, _, fns in os.walk(adir):
        for fn in fns:
            p = os.path.join(dp, fn)
            arts.append({"name": fn, "path": p,
                         "kind": os.path.basename(dp),
                         "bytes": os.path.getsize(p)})
    packages = [a.value.get("v") for a in led.query(
        predicate="exchange:package", limit=50)]
    packages += [{"id": (a.value.get("v") or {}).get("id"),
                  "path": (a.value.get("v") or {}).get("path"),
                  "direction": "export"}
                 for a in led.query(predicate="exchange:exported", limit=50)]
    tools = [{"id": t["id"], "title": t["title"], "need": t["need"],
              "authored": t.get("authored"), "kind": "tool",
              "slots": (t.get("template") or {}).get("slots", [])}
             for t in ctx.tools.tools.values()]
    personas = [_roster_entry(ctx, p) for p in ctx.personas.roster()]
    counts = {}
    for a in led.rows:
        ns = a.predicate.split(":", 1)[0]
        counts[ns] = counts.get(ns, 0) + 1
    return {"personas": personas, "tools": tools, "packages": packages,
            "artifacts": arts, "openNeeds": ctx.open_needs(),
            "ledger": {"rows": len(led.rows), "predicates": counts}}


class Handler(BaseHTTPRequestHandler):
    server_version = "Vantage/0.3.0.004"

    def log_message(self, *a):
        pass

    @property
    def ctx(self):
        return self.server.ctx

    def _send(self, body=b"", status=200, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = _json_bytes(body)
            ctype = "application/json"
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        if not n:
            return {}
        raw = self.rfile.read(n)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def _qs(self):
        return urllib.parse.parse_qs(
            urllib.parse.urlparse(self.path).query)

    def _route(self):
        return urllib.parse.urlparse(self.path).path

    # -- static ---------------------------------------------------------------

    def _index(self):
        html = open(os.path.join(UI_DIR, "index.html"),
                    encoding="utf-8").read()
        theme = self.ctx.ledger.resolve("config", "ui:shell-theme")
        t = theme.value.get("v") if theme else "light"
        html = html.replace("<html>", f'<html data-theme="{t}">')
        self._send(html, ctype="text/html; charset=utf-8")

    def _static(self, path):
        rel = path.lstrip("/")
        if ".." in rel:
            return self._send({"error": "no"}, 404)
        full = os.path.join(UI_DIR, rel.split("/", 1)[-1])
        if not os.path.exists(full):
            return self._send({"error": "not found"}, 404)
        ctype = {"js": "text/javascript", "css": "text/css"}.get(
            full.rsplit(".", 1)[-1], "text/plain")
        self._send(open(full, "rb").read(), ctype=ctype)

    def _artifact(self):
        p = (self._qs().get("path") or [""])[0]
        root = os.path.abspath(self.ctx.runtime)
        ap = os.path.abspath(p)
        if not ap.startswith(root) or not os.path.exists(ap):
            return self._send({"error": "no such artifact"}, 404)
        ctype = "image/svg+xml" if ap.endswith(".svg") else \
            "application/octet-stream"
        self._send(open(ap, "rb").read(), ctype=ctype)

    # -- GET ------------------------------------------------------------------

    def do_GET(self):
        path = self._route()
        q = self._qs()
        ctx = self.ctx
        led = ctx.ledger
        if path == "/":
            return self._index()
        if path.startswith("/ui/"):
            return self._static(path)
        if path == "/api/artifact":
            return self._artifact()
        if path == "/api/events":
            return self._sse()
        if path == "/api/state":
            return self._send(state(ctx))
        if path == "/api/honesty":
            return self._send(ctx.engines.honesty())
        if path == "/api/gate":
            return self._send({"passed": ctx.gate.passed if ctx.gate else None,
                               "timeToGateMs": ctx.gate.time_to_gate_ms
                               if ctx.gate else None,
                               "checks": ctx.gate.checks if ctx.gate else {}})
        if path == "/api/roster":
            return self._send({"roster": state(ctx)["roster"],
                               "active": ctx.personas.data.get("active")})
        if path == "/api/library":
            rows = led.query(
                subject=(q.get("subject") or [None])[0],
                predicate=(q.get("predicate") or [None])[0],
                text=(q.get("text") or [None])[0],
                claimant=(q.get("claimant") or [None])[0],
                limit=int((q.get("limit") or [100])[0]))
            return self._send({"rows": [r.row() for r in rows]})
        if path == "/api/predicates":
            return self._send({"predicates": sorted(
                {a.predicate for a in led.rows})})
        if path == "/api/view":
            subj = (q.get("subject") or [""])[0]
            return self._send({"subject": subj, "view": led.view(subj)})
        if path == "/api/candidates":
            return self._send({"candidates": led.candidates(
                (q.get("subject") or [""])[0],
                (q.get("predicate") or [""])[0])})
        if path == "/api/holdings":
            return self._send(holdings(ctx))
        if path == "/api/needs":
            return self._send({"needs": ctx.open_needs()})
        if path in ("/api/calendar", "/api/temporal"):
            return self._send(temporal_classify(led))
        if path == "/api/speech-floor":
            return self._send({"depth": ctx.floor.depth,
                               "played": ctx.floor.played[-20:],
                               "engine": ctx.engines.tts.mode})
        if path == "/api/archive":
            return self._send({"turns": [
                a.value.get("v") for a in led.query(
                    predicate="archive:turn", limit=100)],
                "segments": [a.value.get("v") for a in led.query(
                    predicate="archive:segment", limit=50)]})
        if path == "/api/tools":
            return self._send({"tools": [
                {"id": t["id"], "title": t["title"], "need": t["need"],
                 "template": t["template"], "authored": t.get("authored"),
                 "consequential": t.get("consequential")}
                for t in ctx.tools.tools.values()]})
        if path == "/api/log":
            kind = (q.get("kind") or ["traces"])[0]
            pred = {"traces": "archive:turn", "decisions": "decision:score",
                    "respondents": "decision:respondent",
                    "steward": "idle:steward-run", "churn": "tool:trust",
                    "inference": "inference:commit",
                    "snapshots": "inference:snapshot",
                    "floor": "speech:played",
                    "fidelity": "persona:fidelity-flag"}.get(kind, kind)
            return self._send({"rows": [
                {"predicate": a.predicate, "at": a.at,
                 "value": a.value.get("v"), "claimant": a.claimant}
                for a in led.query(predicate=pred, limit=80)]})
        return self._send({"error": f"no route {path}"}, 404)

    def _sse(self):
        q = queue.Queue(maxsize=300)
        self.server.sse_add(q)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        try:
            self.wfile.write(b": connected\n\n")
            self.wfile.flush()
            while True:
                try:
                    ev = q.get(timeout=25)
                    self.wfile.write(b"data: " + _json_bytes(ev) + b"\n\n")
                    self.wfile.flush()
                except queue.Empty:
                    self.wfile.write(b": tick\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            self.server.sse_drop(q)

    # -- POST -----------------------------------------------------------------

    def do_POST(self):
        path = self._route()
        body = self._body()
        ctx = self.ctx
        led = ctx.ledger

        if path == "/api/chat":
            return self._send(B.run_chat_turn(
                ctx, body.get("text", ""), address=body.get("address"),
                via=body.get("via", "chat")))
        if path == "/api/chat/reset":
            return self._send(archive.reset(ctx))
        if path == "/api/transcribe":
            return self._send(ctx.invoke(
                "transcribe-speech", {"text": body.get("text", "")},
                summary="mic input", via="mic"))
        if path == "/api/invoke":
            return self._send(ctx.invoke(
                body.get("toolId"), body.get("slots", {}),
                summary=body.get("summary", ""), via="api"))
        m = re.match(r"/api/tools/([\w-]+)/invoke$", path)
        if m:
            return self._send(ctx.invoke(
                m.group(1), body.get("input", {}),
                summary=f"api:{m.group(1)}", via="api"))
        if path == "/api/command":
            fn = ctx.tools.commands.get(body.get("name"))
            if not fn:
                return self._send({"ok": False, "error": "no such command"},
                                  404)
            return self._send({"ok": True,
                               "result": _safe(fn(ctx, body.get("args", {})))})
        if path == "/api/personas":
            return self._send(ctx.invoke("persona-mint", body,
                                         summary="mint via api", via="api"))
        m = re.match(r"/api/personas/([\w-]+)/update$", path)
        if m:
            return self._send(ctx.invoke(
                "persona-update",
                {"personaId": m.group(1), "patch": body.get("patch", body)},
                summary="editor save", via="api"))
        if path == "/api/roster/select":
            return self._send(ctx.personas.select(body.get("personaId")))
        if path == "/api/roster/move":
            return self._send(ctx.personas.move(body.get("personaId"),
                                                body.get("direction", 0)))
        m = re.match(r"/api/needs/([\w-]+)/candidate$", path)
        if m or path == "/api/needs/candidate":
            nid = m.group(1) if m else body.get("needId")
            return self._send(floor.supply_candidate(
                ctx, nid, body.get("slot"), body.get("value"),
                source=body.get("source", "user"),
                confidence=body.get("confidence", 0.9)))
        m = re.match(r"/api/needs/([\w-]+)/focus$", path)
        if m:
            return self._send(floor.focus_need(ctx, m.group(1),
                                               body.get("on", True)))
        m = re.match(r"/api/needs/([\w-]+)/cancel$", path)
        if m:
            return self._send(floor.cancel_need(ctx, m.group(1)))
        m = re.match(r"/api/needs/([\w-]+)/retry$", path)
        if m:
            return self._send(ctx.retry(m.group(1)))
        if path == "/api/grants":
            return self._send({"grantId": floor.issue_grant(
                ctx, body.get("scope"), body.get("lock"),
                body.get("consumable", True))})
        if path == "/api/config":
            prev = led.resolve("config", body["predicate"])
            led.say("config", body["predicate"], body.get("value"),
                    claimant="principal", certainty=1.0,
                    basis={"kind": "user-choice"},
                    supersedes=prev.id if prev else None)
            return self._send({"ok": True, "predicate": body["predicate"],
                               "value": body.get("value")})
        if path == "/api/library/assert":
            a = led.say(body["subject"], body["predicate"], body["value"],
                        claimant="principal",
                        certainty=body.get("certainty", 0.9),
                        basis={"kind": "user-choice"},
                        supersedes=body.get("supersedes"))
            return self._send({"ok": True, "id": a.id})
        if path == "/api/calendar/import":
            from . import connectors
            return self._send(connectors.import_ics(
                ctx, body.get("ics", ""), body.get("source", "api")))
        if path == "/api/steward/wake":
            return self._send(ctx.steward.tick(reason="wake"))
        if path == "/api/compare":
            return self._send(ctx.compete(body.get("need"),
                                          body.get("input", {})))
        if path == "/api/exchange/export":
            return self._send(ctx.invoke("export-exchange", body,
                                         summary="export via api", via="api"))
        if path == "/api/exchange/import":
            return self._send(ctx.invoke("import-exchange", body,
                                         summary="import via api", via="api"))
        if path == "/api/context/select":
            return self._send(ctx.invoke("select-context", body,
                                         summary="context select", via="api"))
        return self._send({"error": f"no route {path}"}, 404)


def _safe(v):
    try:
        json.dumps(v)
        return v
    except TypeError:
        return repr(v)
