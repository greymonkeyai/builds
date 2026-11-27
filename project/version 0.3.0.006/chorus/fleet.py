"""Fleet — discovery, roster, invite/join/install, peer sync, courier.
Discovery is broad and honest (C-HonestDiscovery): everything found is
recorded including non-fleet devices; coverage is itself test data. Join is
user-mediated — no silent auto-join (C-SeedLifecycle). Every host is a
sovereign ledger hub (C-SovereignHubs): pairing = append-only delta
exchange, rejoin correlated by node id + watermark.
"""
import concurrent.futures
import ipaddress
import json
import os
import platform
import re
import socket
import subprocess
import threading
import time
import urllib.request
import urllib.parse
APP_PEER_PORT = int(os.environ.get("CHORUS_PEER_PORT", "7871"))
# Derived operational roster — per direction-006 the named-roster docs are
# ground truth for coverage scoring; this is the minimal derived form,
# NOT the private inventory. Statuses are computed live (found /
# installable / unavailable / not-a-target).
EXPECTED_ROSTER = [
    {"id": "PC-GMK", "match": ["nucbox_g3_pro", "gmk"], "role": "hub-host",
     "target": True, "os": "windows-11"},
    {"id": "RMT-93", "match": ["rmt-93", "rmt93"], "role": "host-server",
     "target": True, "os": "windows"},
    {"id": "RMT-105", "match": ["rmt-105", "rmt105"], "role": "host-server",
     "target": True, "os": "windows"},
    {"id": "TAB-YOGA", "match": ["yoga"], "role": "input-peripheral",
     "target": True, "os": "windows-arm"},
    {"id": "PC-RMATA-01", "match": ["rmata-01", "rmatamini"], "role": "seed-host",
     "target": True, "os": "windows"},
    {"id": "PC-RMATA-02", "match": ["rmata-02"], "role": "seed-host",
     "target": True, "os": "windows"},
    {"id": "PC-TERRY", "match": ["terryza", "terry"], "role": "salvage-host",
     "target": True, "os": "windows"},
    {"id": "ECHO-DOT", "match": ["amazon", "echo"], "role": "bt-audio",
     "target": False, "os": "echo"},
    {"id": "PIXEL-PHONE", "match": ["pixel"], "role": "android-surface",
     "target": True, "os": "android"},
    {"id": "MYBOOKLIVE", "match": ["mybooklive"], "role": "nas",
     "target": False, "os": "nas"},
    {"id": "NEST-HUB", "match": ["google-nest-hub"], "role": "display",
     "target": False, "os": "cast"},
    {"id": "BROTHER-PRN", "match": ["brn"], "role": "printer",
     "target": False, "os": "embedded"},
    {"id": "TPLINK-PLUG", "match": ["hs100"], "role": "smart-plug",
     "target": False, "os": "iot"},
    {"id": "RASPI", "match": ["raspberrypi"], "role": "side-experiment",
     "target": True, "os": "linux"},
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
        return "127.0.0.1", "192.168.86.0/24"
def _ping(ip, timeout_ms=400):
    try:
        r = subprocess.run(["ping", "-n", "1", "-w", str(timeout_ms), ip],
                           capture_output=True, text=True, timeout=timeout_ms/1000 + 2)
        return "TTL=" in r.stdout
    except Exception:
        return False
def _probe(ip, port, timeout=1.0):
    try:
        s = socket.create_connection((ip, port), timeout)
        s.close()
        return True
    except Exception:
        return False
def _rdns(ip, timeout=2.0):
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
        for m in re.finditer(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-f-]{17})", r.stdout):
            out[m.group(1)] = m.group(2)
    except Exception:
        pass
    return out
def _bt_devices():
    """Bluetooth enumeration — local transport coverage."""
    ps = ("Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue |"
          " Where-Object { $_.FriendlyName -and $_.Status -ne 'Unknown' } |"
          " Select-Object -ExpandProperty FriendlyName")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=25)
        return [l.strip() for l in r.stdout.splitlines()
                if l.strip() and "Bluetooth" not in l.strip()[:9]]
    except Exception:
        return []
class Fleet:
    def __init__(self, host):
        self.host = host
        self.local_ip, self.subnet = _local_subnet()
        self.discovery = {"state": "idle", "progress": {},
                          "results": [], "map": None}
        self.node_id = host.node_id
    # ---------- discovery ----------
    def run_discovery(self, transports=("lan", "bt")):
        """A discovery run with in-progress + finished states surfaced
        (C-ProgressVisibility / R-F1)."""
        d = self.discovery
        d["state"] = "scanning"
        d["transports"] = list(transports)
        d["progress"] = {"lan": "starting", "bt": "queued"}
        d["results"] = []
        d["startedAt"] = time.time()
        self.host.book.append("fleet:discovery", {
            "subject": "run", "state": "in-progress",
            "transports": list(transports)}, claimant="host",
            basis="execution-evidence")
        self.host.push_event("discovery", {"state": "in-progress",
                                           "transport": "lan"})
        devices = []
        if "lan" in transports:
            net = ipaddress.ip_network(self.subnet, strict=False)
            ips = [str(a) for a in net.hosts()]
            arp = _arp_table()
            found_ips = set(arp.keys())
            done = [0]
            lock = threading.Lock()
            def probe(ip):
                if ip == self.local_ip:
                    host = True
                else:
                    host = _ping(ip) or ip in arp
                rec = None
                if host:
                    name = _rdns(ip)
                    ports = {p: _probe(ip, p, 0.7)
                             for p in (80, 445, 3389, APP_PEER_PORT)}
                    rec = {"ip": ip, "name": name, "mac": arp.get(ip),
                           "ports": {k: v for k, v in ports.items() if v},
                           "peer": ports.get(APP_PEER_PORT, False),
                           "self": ip == self.local_ip,
                           "transport": "lan"}
                with lock:
                    done[0] += 1
                    d["progress"]["lan"] = f"{done[0]}/{len(ips)}"
                    if done[0] % 24 == 0:
                        self.host.push_event("discovery", {
                            "state": "in-progress", "transport": "lan",
                            "progress": d["progress"]["lan"]})
                return rec
            with concurrent.futures.ThreadPoolExecutor(48) as ex:
                for rec in ex.map(probe, ips):
                    if rec:
                        devices.append(rec)
            # ARP-only entries we didn't ping-confirm still get recorded
            for ip, mac in arp.items():
                if ip not in [x["ip"] for x in devices] and \
                        ip.startswith(self.subnet.split(".0/")[0]):
                    devices.append({"ip": ip, "name": _rdns(ip), "mac": mac,
                                    "ports": {}, "peer": False,
                                    "transport": "lan", "arpOnly": True})
        if "bt" in transports:
            d["progress"]["bt"] = "enumerating"
            for name in _bt_devices():
                devices.append({"name": name, "transport": "bluetooth",
                                "ports": {}, "peer": False, "bt": True})
            d["progress"]["bt"] = "done"
        d["results"] = devices
        self._match_roster(devices)
        d["state"] = "finished"
        d["finishedAt"] = time.time()
        d["map"] = self._write_map(devices)
        self.host.book.append("fleet:discovery", {
            "subject": "run", "state": "finished",
            "found": len(devices),
            "elapsedS": round(d["finishedAt"] - d["startedAt"], 1)},
            claimant="host", basis="execution-evidence")
        self.host.push_event("discovery", {"state": "finished",
                                           "found": len(devices)})
        return devices
    def _match_roster(self, devices):
        """Each named-roster device reported with honest status — coverage
        is scored; non-targets recorded too (S-fleet-roster)."""
        report = []
        for exp in EXPECTED_ROSTER:
            hit = None
            for dev in devices:
                nm = (dev.get("name") or "").lower()
                mac = dev.get("mac") or ""
                if any(tok in nm or tok in mac for tok in exp["match"]):
                    hit = dev
                    break
            if not exp["target"]:
                status = "not-a-target" if hit else "not-a-target-absent"
            elif hit is None:
                status = "unavailable"
            elif hit.get("peer"):
                status = "peer-live"
            elif hit["ports"].get("445") or hit["ports"].get("3389") \
                    or hit.get("bt") or exp["os"] == "android":
                status = "installable"
            else:
                status = "found"
            report.append({"id": exp["id"], "role": exp["role"],
                           "expectedOs": exp["os"], "target": exp["target"],
                           "status": status,
                           "ip": hit.get("ip") if hit else None,
                           "name": hit.get("name") if hit else None})
        self.discovery["roster"] = report
        self.host.book.append("fleet:roster-report", {
            "subject": "named-roster", "devices": report,
            "coverage": sum(1 for r in report
                            if r["status"] not in ("unavailable",
                                                   "not-a-target-absent"))},
            claimant="host", basis="execution-evidence")
        return report
    def _write_map(self, devices):
        members = [m for m in self.host.book.current_of("fleet:member")]
        member_ips = {m["claim"].get("ip") for m in members}
        m = {"node": self.node_id, "generatedAt": time.time(),
             "subnet": self.subnet,
             "devices": [{**d,
                          "member": d.get("ip") in member_ips,
                          "kind": ("member" if d.get("ip") in member_ips
                                   else "peer" if d.get("peer")
                                   else "non-member")}
                         for d in devices],
             "members": len(member_ips)}
        path = os.path.join(self.host.runtime_dir, "network-map.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(m, f, indent=1)
        self.host.book.append("fleet:network-map", {
            "subject": "map", "path": path, "devices": len(devices),
            "members": len(member_ips)},
            claimant="host", basis="execution-evidence")
        return m
    # ---------- invite / join / install ----------
    def invite(self, ip, name=None):
        """User selects which candidates join — non-invited devices are NOT
        members. The invite carries the operator through (R-F3): if a peer
        answers, a consent/install surface exists; else explicit inviter-side
        directions — never a dead end."""
        invite_key = f"inv-{int(time.time())}-{os.urandom(3).hex()}"
        rec = {"subject": ip, "ip": ip, "name": name,
               "inviteKey": invite_key, "state": "invited",
               "directions": None}
        # does a peer answer on the app port?
        peer = None
        try:
            with urllib.request.urlopen(
                    f"http://{ip}:{APP_PEER_PORT}/peer/hello", timeout=2) as r:
                peer = json.loads(r.read().decode())
        except Exception:
            peer = None
        if peer:
            rec["peerHello"] = peer
            rec["state"] = "peer-found"
            rec["next"] = ("peer answers — its consent surface is live; "
                           "present the invite key there to complete join")
            # actually attempt join with key
            joined = self._try_join(ip, invite_key)
            rec["joinResult"] = joined
            rec["state"] = "member" if joined.get("joined") else "pending"
        else:
            rec["next"] = (
                "no running peer on this device. To complete the add: "
                "1) carry the seed media (USB labeled BUILD) to the device, "
                "2) run chorus from the media (launch-seed.cmd) — it boots "
                "in place, no install needed, 3) on its fleet screen enter "
                f"invite key {invite_key} — it joins this network and "
                "surrenders credential custody to this host")
            rec["state"] = "pending"
        row = self.host.book.append("fleet:invite", rec, claimant="principal",
                                    certainty=1.0, basis="user-choice")
        self.host.push_event("fleet", {"action": "invite", "ip": ip,
                                       "state": rec["state"]})
        return rec, row
    def _try_join(self, ip, invite_key):
        payload = {"inviteKey": invite_key, "from": self.node_id,
                   "ip": self.local_ip}
        try:
            req = urllib.request.Request(
                f"http://{ip}:{APP_PEER_PORT}/peer/join",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=4) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            return {"joined": False, "error": str(e)[:120]}
    def member_join(self, claim):
        """Called on the peer side when an operator enters an invite key —
        records membership, role negotiation, credential surrender."""
        role = claim.get("role", "surface")
        m = self.host.book.append("fleet:member", {
            "subject": claim["node"], "node": claim["node"],
            "ip": claim["ip"], "role": role, "state": "member",
            "joinedAt": claim.get("at"),
            "credentialSurrender": "consented — credential management "
                                   "surrendered to this host; secrets stay "
                                   "host-local, needs travel, secrets never"},
            claimant="peer:" + claim["node"], certainty=0.9,
            basis="execution-evidence")
        self.host.book.append("fleet:role", {
            "subject": claim["node"], "role": role,
            "negotiated": True,
            "mintRights": role in ("host-server", "hub-host")},
            claimant="host", basis="derived")
        self.host.book.append("fleet:credential-surrender", {
            "subject": claim["node"],
            "surrender": "recorded as a claim on both books"},
            claimant="host", basis="execution-evidence")
        return m
    def install(self, ip):
        """Install attempt on an installable target — honest probe, legible
        outcome, never a dead end."""
        unc = f"\\\\{ip}\\c$"
        rec = {"subject": ip, "ip": ip, "attempted": True}
        try:
            entries = os.listdir(unc)
            rec["adminShare"] = "reachable"
            rec["entries"] = len(entries)
        except Exception as e:
            rec["adminShare"] = f"unreachable: {type(e).__name__}"
            rec["state"] = "pending"
            rec["directions"] = (
                "admin share is not open to this machine. Operator path: "
                "carry the USB seed to the device and run launch-seed.cmd "
                "(runs in place), or sign in on the device and pull the "
                "install from this host's fleet screen")
        self.host.book.append("fleet:install", rec, claimant="principal",
                              certainty=1.0, basis="execution-evidence")
        self.host.push_event("fleet", {"action": "install", "ip": ip,
                                       "state": rec.get("state", "probed")})
        return rec
    # ---------- peer sync (sovereign hubs) ----------
    def export_delta(self, since_id=0):
        """Append-only delta export: rows after a-# watermark."""
        rows = [r for r in self.host.book.rows
                if int(str(r["id"]).split("-")[-1]) > since_id]
        return {"node": self.node_id, "watermark": self.host.book._seq,
                "rows": rows[:2000]}
    def offer_delta(self, payload):
        """Inbound delta — unioned with read-time trust resolution; foreign
        rows are claimant-attributed and quarantined low-certainty."""
        accepted = 0
        for r in payload.get("rows", []):
            row = dict(r)
            row["claimant"] = f"peer:{payload.get('node', 'unknown')}"
            row["certainty"] = min(row.get("certainty", 0.5), 0.5)
            row["id"] = None
            self.host.book.append(
                row["kind"], row["claim"], claimant=row["claimant"],
                certainty=row["certainty"], basis="exchange",
                relates=[f"peer-row:{r.get('id')}"])
            accepted += 1
        return {"accepted": accepted, "node": self.node_id,
                "watermark": self.host.book._seq}
    def sync_with(self, ip):
        """Two-sided real sync: export our delta -> peer offers theirs."""
        since = self.host.state.get(f"peer_watermark:{ip}", 0)
        out = {"peer": ip, "startedAt": time.time()}
        try:
            delta = self.export_delta(since)
            req = urllib.request.Request(
                f"http://{ip}:{APP_PEER_PORT}/peer/offer",
                data=json.dumps(delta).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=6) as r:
                theirs = json.loads(r.read().decode())
            out["sent"] = len(delta["rows"])
            out["ack"] = theirs
            req2 = urllib.request.Request(
                f"http://{ip}:{APP_PEER_PORT}/peer/export?since={theirs.get('watermark', 0)}")
            with urllib.request.urlopen(req2, timeout=6) as r:
                their_delta = json.loads(r.read().decode())
            got = self.offer_delta(their_delta)
            out["received"] = got["accepted"]
            out["rejoin"] = {"correlatedBy": "node+watermark",
                             "theirWatermark": their_delta.get("watermark")}
            out["ok"] = True
            self.host.state[f"peer_watermark:{ip}"] = their_delta.get("watermark", 0)
        except Exception as e:
            out["ok"] = False
            out["error"] = str(e)[:160]
        self.host.book.append("fleet:sync", {"subject": ip, **out},
                              claimant="host", basis="execution-evidence")
        return out
