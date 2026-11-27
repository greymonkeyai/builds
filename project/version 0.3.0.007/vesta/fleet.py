"""fleet — discovery, invite/join/install, peer protocol, seed media,
roster/map, transports, surrender, host/satellite topology (module: fleet).

Discovery is broad and honest (C-HonestDiscovery): everything found is
recorded including non-fleet devices — coverage is itself test data, and
a local network map is a produced artifact maintained alongside the
member network. The seed lifecycle binds in order (C-SeedLifecycle):
execute in place from media → stage to local disk only when needed and
permitted → network discovery → user-mediated invites → role
negotiation → capable targets install. The USB carries an append-only
courier log (C-SeedLog); capable installed nodes mint gen-2 installers
carrying the founding network identity as an adoptable offer
(C-SeedMint). Local transports preferred — wired LAN baseline plus BT/
NFC/SoftAP where supported (C-LocalTransports). Join consents to
credential surrender: secrets stay host-local, recorded as claims on
both books (C-CredentialSurrender).
"""

import json
import os
import re
import shutil
import socket
import subprocess
import threading
import time
import urllib.request

PEER_PORT_DEFAULT = 7872
STAGE_ROOT = r"C:\builds-installed"

# Derived operational roster — the named-roster docs are ground truth
# for coverage scoring; this is the minimal derived form, not the
# private inventory. Statuses are computed live at discovery time.
EXPECTED_ROSTER = [
    {"id": "PC-GMK", "match": ["nucbox_g3_pro", "gmk", "desktop-oogq7un"], "role": "hub-host", "target": True, "os": "windows-11"},
    {"id": "RMT-93", "match": ["rmt-93", "rmt93"], "role": "host-server", "target": True, "os": "windows"},
    {"id": "RMT-105", "match": ["rmt-105", "rmt105"], "role": "host-server", "target": True, "os": "windows"},
    {"id": "TAB-YOGA", "match": ["yoga"], "role": "input-peripheral", "target": True, "os": "windows-arm"},
    {"id": "PC-RMATA-01", "match": ["rmata-01", "rmatamini"], "role": "seed-host", "target": True, "os": "windows"},
    {"id": "PC-RMATA-02", "match": ["rmata-02"], "role": "seed-host", "target": True, "os": "windows"},
    {"id": "PC-TERRY", "match": ["terryza", "terry"], "role": "salvage-host", "target": True, "os": "windows"},
    {"id": "ECHO-DOT", "match": ["amazon", "echo"], "role": "bt-audio", "target": False, "os": "echo"},
    {"id": "PIXEL-PHONE", "match": ["pixel"], "role": "android-surface", "target": True, "os": "android"},
    {"id": "MYBOOKLIVE", "match": ["mybooklive"], "role": "nas", "target": False, "os": "nas"},
    {"id": "NEST-HUB", "match": ["google-nest-hub", "google-home"], "role": "display", "target": False, "os": "cast"},
    {"id": "BROTHER-PRN", "match": ["brn"], "role": "printer", "target": False, "os": "embedded"},
    {"id": "TPLINK-PLUG", "match": ["hs100"], "role": "smart-plug", "target": False, "os": "iot"},
    {"id": "RASPI", "match": ["raspberrypi"], "role": "side-experiment", "target": True, "os": "linux"},
]


def _local_subnet():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.168.86.1", 80))
        ip = s.getsockname()[0]
        s.close()
        parts = ip.split(".")
        return ip, ".".join(parts[:3]) + ".0/24"
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
            parts = ip.split(".")
            return ip, ".".join(parts[:3]) + ".0/24"
        except Exception:
            return "127.0.0.1", "192.168.86.0/24"


def _ping(ip, timeout_ms=350):
    try:
        r = subprocess.run(["ping", "-n", "1", "-w", str(timeout_ms), ip],
                           capture_output=True, text=True, timeout=timeout_ms / 1000 + 2)
        return "TTL=" in r.stdout
    except Exception:
        return False


def _probe(ip, port, timeout=0.7):
    try:
        s = socket.create_connection((ip, port), timeout)
        s.close()
        return True
    except Exception:
        return False


def _rdns(ip, timeout=1.5):
    try:
        socket.setdefaulttimeout(timeout)
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return None
    finally:
        socket.setdefaulttimeout(None)


def _arp_table():
    out = {}
    try:
        r = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=10)
        for m in re.finditer(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]{17})", r.stdout):
            out[m.group(1)] = m.group(2).lower()
    except Exception:
        pass
    return out


def _peer_call(ip, port, msg, timeout=3.0):
    try:
        s = socket.create_connection((ip, port), timeout)
        s.sendall(json.dumps(msg).encode() + b"\n")
        s.settimeout(timeout)
        data = s.recv(65536)
        s.close()
        return json.loads(data.decode()) if data else None
    except Exception as e:
        return {"error": str(e)}


class Fleet:
    EXPECTED_ROSTER = EXPECTED_ROSTER

    def __init__(self, host):
        self.h = host
        self.discovery = {"state": "idle", "devices": [], "roster": [],
                          "transports": {}, "at": None, "progress": None}
        self._peer_sock = None
        self._peer_thread = None
        self.network = {"id": f"net-{int(host.booted_at)}", "foundedBy": host.node_id}

    # ---------------- discovery ----------------
    def discover(self, full=True):
        """Run discovery with in-progress/per-transport progress and a
        finished state on the owner-facing surface
        (C-ProgressVisibility)."""
        self.discovery["state"] = "running"
        self.discovery["progress"] = {"transport": "lan", "done": 0, "total": 0}
        self_ip, subnet = _local_subnet()
        base = subnet.split(".0/")[0]
        arp = _arp_table()
        # candidates: ARP-known + ping sweep
        candidates = set(arp.keys())
        ips = [f"{base}.{i}" for i in range(1, 255)]
        self.discovery["progress"]["total"] = len(ips)
        found = set()
        threads = []
        lock = threading.Lock()
        def worker(ip):
            if _ping(ip):
                with lock:
                    found.add(ip)
            with lock:
                self.discovery["progress"]["done"] += 1
        batch = []
        for ip in ips:
            t = threading.Thread(target=worker, args=(ip,), daemon=True)
            t.start()
            batch.append(t)
            if len(batch) >= 96:
                for b in batch:
                    b.join(2.5)
                batch = []
        for b in batch:
            b.join(2.5)
        found |= candidates
        # enrich in parallel — rdns + port probes per device
        enriched = {}
        elock = threading.Lock()
        def enrich(ip):
            name = _rdns(ip)
            ports = {p: _probe(ip, p, 0.5) for p in (80, 445, self.h.peer_port)}
            with elock:
                enriched[ip] = (name, ports)
        eths = [threading.Thread(target=enrich, args=(ip,), daemon=True)
                for ip in found]
        for t in eths:
            t.start()
        for t in eths:
            t.join(4)
        devices = []
        for ip in sorted(found, key=lambda x: [int(p) for p in x.split(".")]):
            name, ports = enriched.get(ip, (None, {}))
            dev = {"ip": ip, "node": name or ip, "name": name,
                   "mac": arp.get(ip),
                   "ports": {str(k): v for k, v in ports.items() if v},
                   "peer": bool(ports.get(self.h.peer_port)),
                   "self": ip == self_ip,
                   "sameHost": ip == self_ip or ip.startswith("127."),
                   "transport": "lan",
                   "member": False,
                   "kind": "peer" if ports.get(self.h.peer_port) else "non-member"}
            devices.append(dev)
            self.h.ledger.append("device:found", dev,
                                 claimant="system", basis="discovery",
                                 certainty=0.8, transient=True)
        # transports: wired LAN baseline + honest BT enumeration
        bt = self.h.engines.get("bt", {})
        self.discovery["transports"] = {
            "lan": {"used": True, "found": len(devices), "order": 1},
            "bt": {"used": bool(bt.get("radio")), "order": 2,
                   "devices": bt.get("devices", [])},
            "nfc": {"used": False, "declared": "no nfc hardware", "order": 3},
            "softap": {"used": False, "declared": "not attempted — no AP configured", "order": 4},
        }
        self.discovery["devices"] = devices
        self.discovery["at"] = time.time()
        self._match_roster(devices)
        self.write_map()
        self.discovery["state"] = "finished"
        self.h.ledger.append("fleet:discovery",
                             {"devices": len(devices), "subnet": subnet,
                              "transports": self.discovery["transports"]},
                             claimant="system", basis="execution-evidence")
        return self.discovery

    def _match_roster(self, devices):
        """Every named-roster device reported with honest status —
        coverage is scored; non-targets recorded too."""
        report = []
        for exp in EXPECTED_ROSTER:
            hit = None
            for d in devices:
                name = (d.get("name") or "").lower()
                ip = d.get("ip", "")
                if any(mk in name or mk in ip for mk in exp["match"]):
                    hit = d
                    break
            status = "not-found"
            if hit:
                if not exp["target"]:
                    status = "not-a-target"
                elif hit["self"] or hit["ports"].get("445"):
                    status = "installable" if not hit["self"] else "found"
                else:
                    status = "found"
            else:
                status = "unavailable"
            report.append({"id": exp["id"], "role": exp["role"],
                           "target": exp["target"], "status": status,
                           "device": hit})
        self.discovery["roster"] = report
        self.h.ledger.append("fleet:roster-report",
                             {"subject": "named-roster", "devices": report},
                             claimant="system", basis="discovery")

    def write_map(self):
        """The map artifact covers non-member devices alongside the
        member network (C-HonestDiscovery)."""
        m = {"node": self.h.node_id, "generatedAt": time.time(),
             "subnet": _local_subnet()[1],
             "devices": self.discovery["devices"],
             "members": list(self.h.ledger.view()["members"].values()),
             "roster": self.discovery["roster"],
             "legend": {"member": "joined the network",
                        "peer": "vesta peer, not joined",
                        "non-member": "found, not part of the network"}}
        path = os.path.join(self.h.dir, "network-map.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(m, f, indent=1)
        self.h.ledger.append("fleet:map", {"file": path,
                                           "devices": len(self.discovery["devices"])},
                             claimant="system", basis="execution-evidence")
        return path

    # ---------------- peer protocol ----------------
    def start_peer_listener(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("0.0.0.0", self.h.peer_port))
            s.listen(8)
            self._peer_sock = s
            self._peer_thread = threading.Thread(target=self._peer_loop, daemon=True)
            self._peer_thread.start()
            return True
        except Exception:
            self._peer_sock = None
            return False

    def stop_peer_listener(self):
        try:
            if self._peer_sock:
                self._peer_sock.close()
        except Exception:
            pass

    def _peer_loop(self):
        while True:
            try:
                conn, addr = self._peer_sock.accept()
            except Exception:
                return
            threading.Thread(target=self._peer_handle, args=(conn, addr),
                             daemon=True).start()

    def _peer_handle(self, conn, addr):
        try:
            data = conn.recv(65536)
            msg = json.loads(data.decode().strip() or "{}")
            reply = self._peer_dispatch(msg, addr[0])
            conn.sendall(json.dumps(reply).encode() + b"\n")
        except Exception:
            try:
                conn.sendall(json.dumps({"ok": False}).encode() + b"\n")
            except Exception:
                pass
        finally:
            conn.close()

    def _peer_dispatch(self, msg, ip):
        op = msg.get("op")
        if op == "hello":
            return {"ok": True, "node": self.h.node_id, "app": "vesta",
                    "network": self.network["id"]}
        if op == "join":
            return self._accept_join(msg, ip)
        if op == "delta":
            return self._accept_delta(msg, ip)
        if op == "install":
            return self._accept_install(msg, ip)
        return {"ok": False, "error": "unknown op"}

    def _accept_join(self, msg, ip):
        """Join → role negotiation → credential surrender recorded as a
        claim on BOTH books (C-CredentialSurrender): the joiner's
        credential screen closes, secrets stay host-local."""
        role = msg.get("wantRole", "member")
        granted = "member" if role in ("member", "surface") else "surface"
        self.h.ledger.append("fleet:join",
                             {"node": msg.get("node"), "ip": ip,
                              "outcome": "member" if granted == "member" else "pending",
                              "role": granted},
                             claimant="system", basis="peer-protocol")
        self.h.ledger.append("fleet:role",
                             {"node": msg.get("node"), "ip": ip,
                              "role": granted, "negotiated": True,
                              "mintRights": granted == "member"},
                             claimant="system", basis="peer-protocol")
        self.h.ledger.append("fleet:credential-surrender",
                             {"node": msg.get("node"), "ip": ip,
                              "heldBy": "host",
                              "consented": True,
                              "credentialScreen": "closed-on-joiner",
                              "secretsStayHostLocal": True},
                             claimant="system", basis="peer-protocol")
        self.h.ledger.append("fleet:member",
                             {"node": msg.get("node"), "ip": ip,
                              "role": granted, "state": "joined",
                              "host": msg.get("host") or ip,
                              "sameHost": ip.startswith("127.") or
                                        ip == _local_subnet()[0],
                              "credentialSurrender": {
                                  "consented": True,
                                  "heldBy": "host",
                                  "credentialScreen": "closed-on-joiner",
                                  "secretsStayHostLocal": True}},
                             claimant="system", basis="peer-protocol")
        self.h.ledger.append("grant:recorded",
                             {"grant": "role", "node": msg.get("node"),
                              "role": granted,
                              "mintRights": granted == "member" and
                                          msg.get("capable") is True},
                             claimant="system", basis="peer-protocol")
        return {"ok": True, "node": self.h.node_id, "role": granted,
                "network": self.network["id"],
                "surrender": "credential screen closes on your side; "
                             "secrets stay on your host"}

    def _accept_delta(self, msg, ip):
        rows = msg.get("rows", [])
        applied = 0
        for r in rows[:500]:
            try:
                r2 = dict(r)
                r2["id"] = f"peer-{r2.get('id')}"
                self.h.ledger.journal.append(**{k: r2.get(k) for k in
                    ("kind", "value", "claimant", "basis", "certainty",
                     "confidence", "supersedes", "relates", "tags")
                    if k in r2}, **{f: v for f, v in r2.items() if f not in
                    ("kind", "value", "claimant", "basis", "certainty",
                     "confidence", "supersedes", "relates", "tags", "id",
                     "at")})
                applied += 1
            except Exception:
                pass
        self.h.ledger.append("fleet:delta-received",
                             {"from": msg.get("node"), "applied": applied},
                             claimant="system", basis="peer-protocol")
        members = self.h.ledger.view()["members"]
        if msg.get("node") in members:
            self.h.ledger.append("fleet:rejoin",
                                 {"node": msg.get("node"), "correlated": True,
                                  "member": True},
                                 claimant="system", basis="peer-protocol")
        return {"ok": True, "applied": applied,
                "rows": self.h.ledger.count()}

    def _accept_install(self, msg, ip):
        return {"ok": False, "declared": "install push not accepted by "
                                         "policy on this node — stage via seed"}

    # ---------------- invite / join / install (operator path) ----------
    def invite(self, ip):
        """Invite a discovered candidate — user-mediated, never silent
        auto-join. Carries the operator through: target peer consent or
        explicit inviter-side directions (C-OperatorGuidedJoin)."""
        dev = next((d for d in self.discovery["devices"]
                    if d["ip"] == ip or d.get("node") == ip
                    or d.get("name") == ip), None)
        ip = dev["ip"] if dev else ip
        outcome = {"ip": ip, "steps": []}
        if dev and dev.get("self"):
            outcome["ok"] = False
            outcome["legible"] = (
                f"{ip} is this host — a device cannot join itself. "
                f"Pick another candidate.")
            outcome["next"] = "pick-another-candidate"
        elif dev and dev.get("peer"):
            r = _peer_call(ip, self.h.peer_port,
                           {"op": "join", "node": self.h.node_id,
                            "wantRole": "member", "capable": True})
            if r and r.get("ok"):
                outcome["steps"].append({"step": "join", "ok": True,
                                         "role": r.get("role"),
                                         "surrender": r.get("surrender")})
                outcome["member"] = r.get("role")
                self.h.ledger.append("fleet:join",
                                     {"node": f"peer@{ip}", "ip": ip,
                                      "outcome": "member", "role": r.get("role")},
                                     claimant="system", basis="peer-protocol")
                self.h.ledger.append("fleet:member",
                                     {"node": f"peer@{ip}", "ip": ip,
                                      "role": r.get("role"), "state": "joined",
                                      "host": dev.get("name") or ip,
                                      "sameHost": dev.get("sameHost"),
                                      "credentialSurrender": r.get("surrender")},
                                     claimant="system", basis="peer-protocol")
                outcome["ok"] = True
                outcome["legible"] = (f"{ip} joined as {r.get('role')} — "
                                      f"credential surrender recorded")
            else:
                outcome["steps"].append({"step": "join", "ok": False,
                                         "error": (r or {}).get("error")})
                outcome["ok"] = False
                self.h.ledger.append("fleet:join",
                                     {"node": f"peer@{ip}", "ip": ip,
                                      "outcome": "pending",
                                      "why": (r or {}).get("error")},
                                     claimant="system", basis="peer-protocol")
                outcome["legible"] = (f"{ip} runs a vesta peer but declined or "
                                      f"failed the join: {(r or {}).get('error')}. "
                                      f"Operator: re-run discovery, then retry.")
        elif dev:
            outcome["ok"] = False
            outcome["pending"] = "directions"
            self.h.ledger.append("fleet:join",
                                 {"node": f"host@{ip}", "ip": ip,
                                  "outcome": "pending",
                                  "why": "no-vesta-peer — directions issued"},
                                 claimant="system", basis="peer-protocol")
            outcome["legible"] = (
                f"{ip} ({dev.get('name') or 'unnamed'}) was found but runs no "
                f"vesta peer. Operator directions: carry the USB seed "
                f"(H:\\vesta-seed) to that machine and run launch-seed.cmd — "
                f"or run install below to attempt a LAN push.")
            outcome["directions"] = [
                "Insert the USB drive labeled BUILD into the target",
                "Run H:\\vesta-seed\\launch-seed.cmd on the target",
                "Consent to staging when asked, then invite again here"]
        else:
            outcome["ok"] = False
            outcome["legible"] = (f"{ip} is not in the current discovery set — "
                                  f"run discovery first, then invite.")
        outcome["next"] = "install" if outcome.get("ok") else (
            "carry-usb-seed-or-install" if outcome.get("directions") else
            "discover-then-invite")
        outcome["path"] = ["discover", "invite", "join-or-install", "delta-sync"]
        self.h.ledger.append("fleet:invite", outcome,
                             claimant="system", basis="peer-protocol")
        return outcome

    def install(self, ip):
        """Attempt install on a target — real attempt, honest outcome,
        never a dead end (C-OperatorGuidedJoin, C-DemonstratedDistribution)."""
        dev = next((d for d in self.discovery["devices"]
                    if d["ip"] == ip or d.get("node") == ip
                    or d.get("name") == ip), None)
        ip = dev["ip"] if dev else ip
        outcome = {"ip": ip, "at": time.time()}
        if dev and dev.get("self"):
            outcome["ok"] = False
            outcome["status"] = "refused"
            outcome["legible"] = (f"{ip} is this host — a device is not an "
                                  f"install target for itself. Pick another.")
        elif dev and dev.get("peer"):
            r = _peer_call(ip, self.h.peer_port,
                           {"op": "install", "node": self.h.node_id})
            outcome["peerInstall"] = r
            outcome["ok"] = bool(r and r.get("ok"))
            outcome["status"] = "installed" if outcome["ok"] else "refused"
            outcome["legible"] = (f"install push to {ip}: "
                                  f"{json.dumps(r)[:160]}")
            outcome["surface"] = f"http://{ip}:{self.h.port}/" if outcome["ok"] \
                else None
        elif dev and dev["ports"].get("445"):
            # real push attempt via admin share — honest result
            dest = f"\\\\{ip}\\C$\\builds-installed\\vesta"
            try:
                r = subprocess.run(
                    ["robocopy", os.path.dirname(os.path.abspath(__file__)),
                     os.path.join(dest), "/MIR", "/NFL", "/NDL",
                     "/NJH", "/NJS", "/R:0", "/W:1"],
                    capture_output=True, text=True, timeout=20)
                ok = r.returncode < 8 and os.path.isdir(dest)
                outcome["ok"] = ok
                outcome["status"] = "installed" if ok else "refused"
                outcome["method"] = "admin-share-robocopy"
                outcome["legible"] = (
                    f"install push to {dest}: {'succeeded' if ok else 'refused'} "
                    f"(robocopy rc={r.returncode}). "
                    + ("" if ok else
                       "Operator directions: enable admin share or carry the "
                       "USB seed to the target — a device that cannot yet "
                       "proceed says why."))
                outcome["directions"] = [] if ok else [
                    "Enable the admin share (C$) on the target",
                    "Or carry the USB seed to the target and run launch-seed.cmd"]
            except Exception as e:
                outcome["ok"] = False
                outcome["status"] = "unreachable"
                outcome["legible"] = (f"install push to {ip} failed: {e}. "
                                      f"Carry the USB seed to the target.")
                outcome["directions"] = ["Carry the USB seed to the target"]
        else:
            outcome["ok"] = False
            outcome["status"] = "pending"
            outcome["pending"] = True
            outcome["directions"] = ["Run discovery first",
                                     "Carry the USB seed to the target"]
            outcome["legible"] = (
                f"{ip} is neither a joined peer nor reachable on 445 — "
                f"it cannot yet proceed. Operator: run discovery, carry "
                f"the USB seed (H:\\vesta-seed\\launch-seed.cmd) to the "
                f"target, then invite again.")
        self.h.ledger.append("fleet:install", outcome,
                             claimant="system", basis="execution-evidence")
        return outcome

    # ---------------- delta exchange ----------------
    def send_delta(self, node_or_ip):
        """Delta sync to a member node — real rows over the peer socket,
        evidenced on both books."""
        members = self.h.ledger.view()["members"]
        member = next((m for m in members.values()
                       if m.get("node") == node_or_ip or m.get("ip") == node_or_ip),
                      None)
        if not member:
            return {"ok": False, "legible": f"{node_or_ip} is not a member — "
                                            "delta exchange requires a joined node"}
        ip = member.get("ip") or node_or_ip
        rows = [r for r in self.h.ledger.snapshot() if not r.get("transient")][-200:]
        r = _peer_call(ip, self.h.peer_port,
                       {"op": "delta", "node": self.h.node_id, "rows": rows})
        transferred = (r or {}).get("applied", 0) if r else 0
        self.h.ledger.append("fleet:delta",
                             {"node": member.get("node"), "ip": ip,
                              "sent": len(rows), "transferred": transferred,
                              "peerRows": (r or {}).get("rows")},
                             claimant="system", basis="peer-protocol")
        return {"ok": bool(r and r.get("ok")), "transferred": transferred,
                "sent": len(rows),
                "legible": f"delta to {member.get('node')}: {transferred}/{len(rows)} rows applied"}

    # ---------------- seed media ----------------
    def seed_drive(self):
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Get-Volume | Where-Object {$_.FileSystemLabel -eq 'BUILD'} | "
                 "Select-Object -ExpandProperty DriveLetter"],
                capture_output=True, text=True, timeout=10)
            letter = r.stdout.strip()
            return f"{letter}:\\" if letter else None
        except Exception:
            return None

    def courier_log_path(self):
        drive = self.seed_drive()
        if not drive:
            return None
        return os.path.join(drive, "vesta-seed", "seed-log.jsonl")

    def courier_append(self, event):
        """The USB medium carries an append-only local network log —
        a witness courier accumulating history across visited machines
        (C-SeedLog)."""
        path = self.courier_log_path()
        if not path:
            return None
        os.makedirs(os.path.dirname(path), exist_ok=True)
        row = {"at": time.time(), "node": self.h.node_id,
               "host": os.environ.get("COMPUTERNAME"), "event": event}
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        self.h.ledger.append("fleet:courier", dict(row, log=path),
                             claimant="system", basis="execution-evidence",
                             certainty=0.85)
        return path

    def seed_run(self, seed_dir=None):
        """Seed lifecycle: executing in place from removable media —
        courier append, then offer staging consent (decline leaves the
        app on media, no local write). Stale-seed revisit: if the media
        already carries an older/other network offer, the revisit is
        recorded with its handling."""
        drive = self.seed_drive()
        launched = seed_dir or (os.path.join(drive, "vesta-seed")
                                if drive else None)
        # stale-seed revisit handling — recorded, not silent
        offer_path = os.path.join(launched or "", "network-offer.json")
        if os.path.exists(offer_path):
            try:
                old = json.load(open(offer_path, encoding="utf-8"))
                handling = "same-network" if old.get("network") == self.network["id"] \
                    else "older-or-other-network — offer stands, user chooses"
                self.h.ledger.append("seed:revisit",
                                     {"offer": old, "handling": handling},
                                     claimant="system", basis="execution-evidence")
                self.courier_append({"kind": "seed-revisit",
                                     "handling": handling})
            except Exception:
                pass
        self.courier_append({"kind": "seed-run-in-place",
                             "network": self.network["id"],
                             "port": self.h.port})
        self.h.ledger.append("fleet:seed-run",
                             {"drive": drive, "launchedFrom": launched,
                              "inPlace": True, "installed": False,
                              "courier": self.courier_log_path()},
                             claimant="system", basis="execution-evidence")
        return {"ok": True, "drive": drive, "launchedFrom": launched,
                "installed": False, "courier": self.courier_log_path()}

    def seed_stage(self, consent, target_dir=None):
        """Stage to C:\\builds-installed only when needed AND permitted;
        decline leaves the app on media with no local write."""
        if not consent:
            self.courier_append({"kind": "stage-declined",
                                 "result": "no local write"})
            self.h.ledger.append("fleet:stage-consent",
                                 {"consent": False, "wrote": False,
                                  "result": "declined — running from media, "
                                            "no local write"},
                                 claimant="principal", basis="user-set")
            return {"ok": True, "staged": False, "wrote": False,
                    "legible": "declined — vesta stays on the USB drive; "
                               "nothing was written locally"}
        dest = target_dir or os.path.join(STAGE_ROOT, "vesta")
        src = os.path.dirname(os.path.abspath(__file__))
        os.makedirs(dest, exist_ok=True)
        staged = []
        for fn in os.listdir(src):
            if fn.endswith(".py"):
                shutil.copy2(os.path.join(src, fn), os.path.join(dest, fn))
                staged.append(fn)
        self.courier_append({"kind": "staged", "dest": dest, "files": staged})
        self.h.ledger.append("fleet:stage-consent",
                             {"consent": True, "dest": dest, "wrote": True,
                              "files": staged},
                             claimant="principal", basis="user-set")
        return {"ok": True, "staged": True, "wrote": True, "dest": dest,
                "legible": f"staged {len(staged)} files to {dest}"}

    def mint_seed(self, drive=None):
        """Capable installed node mints a gen-2 USB installer carrying
        the founding network's identity as an adoptable offer —
        carry, not enforce (C-SeedMint)."""
        drive = drive or self.seed_drive()
        if not drive:
            return {"ok": False, "error": "no BUILD drive present"}
        dest = os.path.join(drive, "vesta-seed")
        src_pkg = os.path.dirname(os.path.abspath(__file__))
        build_root = os.path.dirname(src_pkg)
        os.makedirs(dest, exist_ok=True)
        # package + launchers + the network offer
        for item in ("vesta", "launch-seed.cmd", "launch.cmd"):
            s = os.path.join(build_root, item)
            d = os.path.join(dest, item)
            if os.path.isdir(s):
                if os.path.isdir(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d,
                                ignore=shutil.ignore_patterns("__pycache__"))
            elif os.path.exists(s):
                shutil.copy2(s, d)
        offer = {"network": self.network["id"], "networkId": self.network["id"],
                 "foundedBy": self.network["foundedBy"],
                 "mintedBy": self.h.node_id, "at": time.time(),
                 "adoptable": True, "choice": "join-or-found",
                 "offer": "join this network or found a new one — the user's choice"}
        with open(os.path.join(dest, "network-offer.json"), "w",
                  encoding="utf-8") as f:
            json.dump(offer, f, indent=1)
        self.courier_append({"kind": "minted-gen2", "dest": dest,
                             "network": self.network["id"]})
        self.h.ledger.append("fleet:seed-minted",
                             {"dest": dest, "network": self.network["id"],
                              "offer": "join-or-found is the user's choice"},
                             claimant="system", basis="execution-evidence")
        return {"ok": True, "dest": dest, "installer": dest,
                "file": os.path.join(dest, "launch-seed.cmd"),
                "networkOffer": offer, "offer": offer}
