"""HTTP API + static UI server (stdlib only)."""
from __future__ import annotations

import json
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import builtins as B
from . import needs as N
from . import tools as T


def _json_of(handler) -> dict:
    n = int(handler.headers.get("Content-Length") or 0)
    if not n:
        return {}
    return json.loads(handler.rfile.read(n).decode())


def make_handler(ctx, ui_dir):
    class H(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        # ---------- helpers ----------
        def _send(self, code, body, ctype="application/json"):
            data = body if isinstance(body, (bytes,)) else json.dumps(
                body, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type",
                             ctype if isinstance(body, bytes) else
                             "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _err(self, msg, code=400):
            self._send(code, {"ok": False, "error": msg})

        # ---------- routes ----------
        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            path, q = u.path, urllib.parse.parse_qs(u.query)
            if path in ("/", "/index.html"):
                return self._static("index.html")
            if path.startswith("/ui/"):
                return self._static(path[4:])
            if path == "/api/state":
                return self._send(200, state(ctx))
            if path == "/api/tools":
                return self._send(200, {"tools": ctx.registry.manifest()})
            if path == "/api/needs":
                return self._send(200, {"open": N.open_needs(ctx)})
            if path == "/api/cards":
                return self._send(200, {"events": ctx.bus.recent[-200:]})
            if path == "/api/library":
                rows = ctx.ledger.query(
                    predicate=q.get("predicate", [None])[0],
                    subject=q.get("subject", [None])[0],
                    limit=int(q.get("limit", [200])[0]))
                if q.get("q"):
                    rows = ctx.ledger.search(q["q"][0], 200)
                return self._send(200, {"rows": [r.to_row() for r in rows],
                                        "stats": ctx.ledger.stats()})
            if path == "/api/view":
                return self._send(200, ctx.ledger.render_view(q["subject"][0]))
            if path == "/api/candidates":
                return self._send(200, {"candidates": ctx.ledger.candidates_for(
                    q["subject"][0], q["predicate"][0])})
            if path == "/api/projects":
                return self._send(200, {"projects": projects(ctx)})
            if path == "/api/calendar":
                return self._send(200, {"events": [
                    r.value["v"] | {"assertionId": r.id, "at": r.at}
                    for r in ctx.ledger.query(predicate="calendar:event")]})
            if path == "/api/grants":
                return self._send(200, {"grants": [
                    {"id": a.subjectKey.split(":", 1)[1], **a.value["v"],
                     "at": a.at}
                    for a in ctx.ledger.query(predicate="grant:issued")]})
            if path == "/api/log":
                kind = q.get("kind", [None])[0]
                preds = {"traces": "routing:turn-trace", "decisions": "decision:score",
                         "steward": "idle:steward-run", "telemetry": "tool:telemetry",
                         "churn": "decision:churn"}.get(kind)
                rows = ctx.ledger.query(predicate=preds, limit=int(q.get("limit", [100])[0])) \
                    if preds else []
                return self._send(200, {"rows": [r.to_row() for r in rows]})
            if path == "/api/honesty":
                return self._send(200, ctx.honesty())
            return self._err("not found", 404)

        def do_POST(self):
            u = urllib.parse.urlparse(self.path)
            path = u.path
            body = _json_of(self)
            if path == "/api/chat":
                r = ctx.invoke("run-chat-turn",
                               {"text": body.get("text", ""),
                                "all": bool(body.get("all"))})
                return self._send(200, r)
            if path == "/api/invoke":
                # entry-path callTool: stage the need, then fulfill when gate-ready
                r = ctx.invoke("request-tool",
                               {"toolId": body["toolId"],
                                "slots": body.get("slots") or {},
                                "summary": body.get("summary")})
                nid = (r.get("result") or {}).get("needId") if r.get("ok") else None
                if not nid:
                    return self._send(200, {"ok": False, "error": r.get("error")})
                fr = T.fulfill_need(ctx, nid)
                gate = None
                if fr.get("deferred"):
                    gate = fr.get("missing")
                return self._send(200, {"ok": fr.get("ok"), "needId": nid,
                                        "deferred": fr.get("deferred"),
                                        "missing": gate,
                                        "result": fr.get("result"),
                                        "error": fr.get("error")})
            if path == "/api/grants":
                gid = T.issue_grant(ctx, body["scope"], body.get("lock"))
                return self._send(200, {"ok": True, "grantId": gid})
            if path == "/api/personas":
                r = ctx.invoke("persona.mint", body)
                return self._send(200, r)
            if path == "/api/calendar/import":
                r = ctx.invoke("import-calendar", body)
                return self._send(200, r)
            if path == "/api/exchange/import":
                r = ctx.invoke("import-exchange", body)
                return self._send(200, r)
            if path == "/api/exchange/export":
                r = ctx.invoke("export-exchange", body)
                return self._send(200, r)
            if path == "/api/stt":
                r = ctx.invoke("transcribe-speech", body)
                return self._send(200, r)
            if path == "/api/tts":
                r = ctx.invoke("speak-voice", body)
                return self._send(200, r)
            if path == "/api/steward/wake":
                r = ctx.invoke("steward-tick", {"reason": "manual"})
                return self._send(200, r)
            if path == "/api/config":
                ctx.append("user-settings", body["predicate"], body["value"],
                           "principal", basis={"kind": "config"})
                return self._send(200, {"ok": True})
            if path == "/api/cleanup":
                r = ctx.invoke("cleanup-run", {})
                return self._send(200, r)
            if path.startswith("/api/needs/") and path.endswith("/cancel"):
                nid = path.split("/")[3]
                N.close_need(ctx, nid, "cancelled", {"by": "api"}, "principal")
                return self._send(200, {"ok": True})
            if path.startswith("/api/needs/") and path.endswith("/candidate"):
                nid = path.split("/")[3]
                aid = N.add_candidate(ctx, nid, body["slot"], body["value"],
                                      float(body.get("confidence", 0.8)),
                                      body.get("source", "user"), "principal")
                return self._send(200, {"ok": True, "assertionId": aid})
            if path.startswith("/api/tools/") and path.endswith("/invoke"):
                cid = path.split("/")[3]
                r = ctx.invoke(cid, body.get("input") or {},
                               grant=body.get("grant"))
                return self._send(200, r)
            if path.startswith("/api/tools/") and path.endswith("/inspect"):
                r = ctx.invoke("inspect-tool", {"toolId": path.split("/")[3]})
                return self._send(200, r)
            if path == "/api/library/assert":
                a = ctx.append(body["subject"], body["predicate"], body["value"],
                               "principal",
                               certainty=float(body.get("certainty", 0.9)),
                               basis={"kind": "user-choice"},
                               supersedes=body.get("supersedes"))
                return self._send(200, {"ok": True, "id": a.id})
            return self._err("not found", 404)

        def _static(self, rel):
            fp = os.path.join(ui_dir, rel.replace("/", os.sep))
            if not os.path.isfile(fp):
                return self._err("not found", 404)
            ctype = {"html": "text/html; charset=utf-8",
                     "js": "text/javascript; charset=utf-8",
                     "css": "text/css; charset=utf-8",
                     "svg": "image/svg+xml"}.get(fp.rsplit(".", 1)[-1], "text/plain")
            with open(fp, "rb") as f:
                self._send(200, f.read(), ctype)

    return H


def projects(ctx) -> list[dict]:
    out = []
    for a in ctx.ledger.query(predicate="project:exists"):
        pid = a.subjectKey.split(":", 1)[1]
        subj = a.subjectKey
        goals = [r.value["v"] for r in ctx.ledger.query(subject=subj, predicate="project:goal")]
        linked = [n for n in N.open_needs(ctx) if n["spec"].get("project") == pid]
        closed = [r for r in ctx.ledger.all()
                  if r.subjectKey.startswith("need:")
                  and r.predicate == "need:fulfilled"
                  and (r.value["v"].get("detail") or {}).get("project") == pid]
        out.append({"id": pid, "title": a.value["v"].get("title"),
                    "goals": goals, "openNeeds": linked,
                    "fulfilled": len(closed)})
    return out


def state(ctx) -> dict:
    return {
        "honesty": ctx.honesty(),
        "roster": ctx.personas.roster(),
        "chat": B.chat_history(ctx, 60),
        "topic": B.current_topic(ctx),
        "cards": ctx.bus.recent[-60:],
        "needs": N.open_needs(ctx),
        "projects": projects(ctx),
        "tools": ctx.registry.manifest(),
        "admonitions": ctx.admonitions,
        "frame": ctx.personas.frame(),
        "responseDepth": ctx.response_depth(),
    }


def serve(ctx, port: int, ui_dir: str):
    srv = ThreadingHTTPServer(("127.0.0.1", port), make_handler(ctx, ui_dir))
    return srv
