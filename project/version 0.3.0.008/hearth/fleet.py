"""hearth fleet — discovery, identify, join/install, seed, peers.
C-HonestDiscovery: broad + honest — everything found recorded incl.
non-fleet devices; a network map artifact maintained alongside members.
C-OperatorGuidedJoin: no dead ends — target surface or inviter-side
directions. R-F4: install attempts drive to a verdict on an installable
roster device. R-F5: identify action signals the device per capability +
materially richer info. C-SeedLog: append-only courier on the medium.
"""
import json
import os
import re
import socket
import struct
import subprocess
import threading
import time
import urllib.request
STAGE_ROOT = r"C:\builds-installed"
# Derived operational roster — the named roster is coverage ground
# truth; this is the minimal derived form, not the private inventory.
EXPECTED_ROSTER = [
    {"id": "PC-GMK", "match": ["nucbox_g3_pro", "gmk", "desktop-oogq7un"],
     "role": "hub-host", "target": True, "os": "windows-11"},
    {"id": "RMT-93", "match": ["rmt-93", "rmt93"], "role": "host-server",
     "target": True, "os": "windows"},
    {"id": "RMT-105", "match": ["rmt-105", "rmt105"],
     "role": "host-server", "target": True, "os": "windows"},
    {"id": "TAB-YOGA", "match": ["yoga"], "role": "input-peripheral",
     "target": True, "os": "windows-arm"},
    {"id": "PC-RMATA-01", "match": ["rmata-01", "rmatamini"],
     "role": "seed-host", "target": True, "os": "windows"},
    {"id": "PC-RMATA-02", "match": ["rmata-02"], "role": "seed-host",
     "target": True, "os": "windows"},
    {"id": "PC-TERRY", "match": ["terryza", "terry"],
     "role": "salvage-host", "target": True, "os": "windows"},
    {"id": "ECHO-DOT", "match": ["amazon", "echo"], "role": "bt-audio",
     "target": False, "os": "echo"},
    {"id": "PIXEL-PHONE", "match": ["pixel"], "role": "android-surface",
     "target": True, "os": "android"},
    {"id": "MYBOOKLIVE", "match": ["mybooklive"], "role": "nas",
     "target": False, "os": "nas"},
    {"id": "NEST-HUB", "match": ["google-nest-hub", "google-home"],
     "role": "display", "target": False, "os": "cast"},
    {"id": "BROTHER-PRN", "match": ["brn"], "role": "printer",
     "target": False, "os": "embedded"},
    {"id": "TPLINK-PLUG", "match": ["hs100"], "role": "smart-plug",
     "target": False, "os": "iot"},
    {"id": "RASPI", "match": ["raspberrypi"], "role": "side-experiment",
     "target": True, "os": "linux"},
]
# Minimal OUI vendor prefixes (offline inference)
OUI = {"B8:27:EB": "Raspberry Pi", "DC:A6:32": "Raspberry Pi",
       "E4:5F:01": "Raspberry Pi", "00:03:93": "Apple",
       "F0:18:98": "Apple", "AC:BC:32": "Apple",
       "68:54:FD": "Amazon", "74:C2:46": "Amazon",
       "F0:F0:A4": "Google", "54:60:09": "Google",
       "D8:EB:46": "Google", "94:16:25": "Google",
       "30:85:A9": "TP-Link", "50:C7:BF": "TP-Link",
       "3C:52:82": "Brother", "30:05:5C": "Brother",
       "00:90:A9": "Western Digital", "00:0A:E4": "GMK/NucBox"}
SERVICE_PORTS = {21: "ftp", 22: "ssh", 23: "telnet", 53: "dns",
                 80: "http", 139: "netbios-ssn", 443: "https",
                 445: "smb", 554: "rtsp", 1900: "ssdp", 3389: "rdp",
                 5353: "mdns", 62078: "iphone-sync", 8008: "cast",
                 8009: "cast", 8443: "https-alt", 9540: "hearth-peer"}
def _local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.168.86.1", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"
def _ping(ip, timeout_ms=400):
    """Real ICMP ping via system ping; returns RTT seconds or None."""
    try:
        out = subprocess.run(["ping", "-n", "1", "-w", str(timeout_ms),
                              ip], capture_output=True, text=True,
                             timeout=3)
        m = re.search(r"time[=<](\d+(?:\.\d+)?)ms", out.stdout)
        if "TTL=" in out.stdout:
            return round(float(m.group(1)) / 1000, 3) if m else 0.001
    except Exception:
        pass
    return None
def _resolve(ip):
    """Name resolution — reverse DNS then NetBIOS."""
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        pass
    try:
        out = subprocess.run(["nbtstat", "-A", ip], capture_output=True,
                             text=True, timeout=4)
        for line in out.stdout.splitlines():
            if "<00>" in line and "UNIQUE" in line.upper():
                return line.split()[0].lower()
    except Exception:
        pass
    return None
def _scan_ports(ip, ports, timeout=0.25):
    seen = []
    def probe(p):
        try:
            s = socket.create_connection((ip, p), timeout=timeout)
            s.close()
            seen.append(SERVICE_PORTS.get(p, str(p)))
        except Exception:
            pass
    threads = [threading.Thread(target=probe, args=(p,)) for p in ports]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=timeout + 0.2)
    return sorted(set(seen))
class Fleet:
    def __init__(self, host):
        self.h = host
        self.local_ip = _local_ip()
        self.subnet = ".".join(self.local_ip.split(".")[:3])
        self.discovery = {"state": "idle", "progress": {},
                          "devices": [], "roster": [], "finished": None}
        self.members = {}  # id -> member record (remote only)
        self._disc_thread = None
    # ---------------- discovery -----------------------------------------
    def discover(self, async_run=True, probe_ports=True):
        """Start a discovery run; progress observable while running."""
        self.discovery = {"state": "running",
                          "progress": {"arp": "pending", "sweep": "pending",
                                       "enrich": "pending",
                                       "roster": "pending"},
                          "devices": [], "roster": [], "finished": None}
        if async_run:
            self._disc_thread = threading.Thread(
                target=self._discover_work, args=(probe_ports,),
                daemon=True)
            self._disc_thread.start()
            return {"state": "running"}
        self._discover_work(probe_ports)
        return {"state": "finished"}
    def _arp_table(self):
        macs = {}
        try:
            out = subprocess.run(["arp", "-a"], capture_output=True,
                                 text=True, timeout=8)
            for line in out.stdout.splitlines():
                m = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+"
                              r"([0-9a-fA-F-]{17})", line)
                if m and "dynamic" in line.lower():
                    ip, mac = m.group(1), m.group(2).upper().replace("-", ":")
                    if ip.startswith(self.subnet):
                        macs[ip] = mac
        except Exception:
            pass
        return macs
    def _discover_work(self, probe_ports):
        d = self.discovery
        ips = {}
        # wired LAN baseline (C-LocalTransports: wired preferred first)
        try:
            for ip, mac in self._arp_table().items():
                ips[ip] = {"ip": ip, "mac": mac, "via": "arp"}
            d["progress"]["arp"] = f"{len(ips)} arp entries"
        except Exception as e:
            d["progress"]["arp"] = "failed:" + str(e)
        # limited sweep for silent hosts (wired lan, parallel, bounded)
        missing = [i for i in range(1, 61)
                   if f"{self.subnet}.{i}" not in ips]
        hits = []
        def sweep(i):
            ip = f"{self.subnet}.{i}"
            rtt = _ping(ip, 300)
            if rtt is not None:
                hits.append(ip)
        ts = [threading.Thread(target=sweep, args=(i,))
              for i in missing]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        for ip in hits:
            ips.setdefault(ip, {"ip": ip, "mac": None, "via": "sweep"})
        d["progress"]["sweep"] = f"{len(hits)} live"
        devices = []
        for ip, info in sorted(ips.items()):
            dev = dict(info)
            dev["name"] = _resolve(ip)
            dev["rttSeconds"] = _ping(ip, 500)
            if probe_ports:
                dev["services"] = _scan_ports(ip, list(SERVICE_PORTS))
            dev["sameHost"] = ip == self.local_ip
            devices.append(dev)
            d["progress"]["enrich"] = f"{len(devices)}/{len(ips)}"
        d["devices"] = devices
        self._match_roster(devices)
        self._map(devices)
        d["state"] = "finished"
        d["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        self.h.journal.append(
            "discovery-run",
            {"devices": len(devices),
             "live": len([x for x in devices if x["rttSeconds"]]),
             "subnet": self.subnet},
            claimant="tool:net.discover", basis="execution-evidence")
        self.seed_log("discovery", {"devices": len(devices)})
    def _match_roster(self, devices):
        report = []
        hay = " ".join(
            (d.get("name") or "") + " " + (d.get("mac") or "") + " " +
            " ".join(d.get("services", [])) for d in devices).lower()
        for exp in EXPECTED_ROSTER:
            found = next(
                (d for d in devices if any(
                    m in ((d.get("name") or "") + " " +
                          (d.get("mac") or "") + " " +
                          " ".join(d.get("services", []))).lower()
                    for m in exp["match"])), None)
            status = "found" if found else (
                "unavailable" if not exp["target"] else "unavailable")
            if not exp["target"]:
                status = "not-a-target" if found else "unavailable"
            report.append({"id": exp["id"], "role": exp["role"],
                           "target": exp["target"],
                           "status": status,
                           "ip": found["ip"] if found else None,
                           "installable": bool(found and exp["target"]),
                           "name": found.get("name") if found else None})
        # installable = found on lan AND target per roster
        for r in report:
            if r["status"] == "found" and r["target"]:
                r["installable"] = True
        self.discovery["roster"] = report
        self.discovery["progress"]["roster"] = "matched"
        self.h.journal.append("fleet:roster-report",
                              {"devices": report},
                              claimant="tool:net.discover",
                              basis="execution-evidence")
    def _map(self, devices):
        """Network map artifact — members + non-members distinguished."""
        members = {d["ip"]: m for d, m in
                   [(m.get("ip"), m) for m in self.members.values()]
                   if d}
        mapped = []
        for dev in devices:
            mapped.append({"ip": dev["ip"], "name": dev.get("name"),
                           "services": dev.get("services", []),
                           "member": dev["ip"] in members,
                           "sameHost": dev.get("sameHost", False)})
        artifact = {"ts": time.time(), "subnet": self.subnet,
                    "devices": mapped}
        path = os.path.join(self.h.data_dir, "network-map.json")
        with open(path, "w") as f:
            json.dump(artifact, f, indent=1)
        self.h.journal.append("network-map",
                              {"path": path, "devices": len(mapped)},
                              claimant="tool:net.discover",
                              basis="execution-evidence")
    # ---------------- identify / ping (R-F5) ------------------------------
    def identify(self, target):
        """Device-identify action on a discovery result — signal the
        device per its capabilities + materially richer identifying
        info: name resolution, vendor/type inference, services seen."""
        dev = next((d for d in self.discovery["devices"]
                    if d["ip"] == target or d.get("name") == target), None)
        ip = target if re.match(r"^\d+\.\d+\.\d+\.\d+$", target) \
            else (dev or {}).get("ip")
        if not ip:
            try:
                ip = socket.gethostbyname(target)
            except Exception:
                return {"error": "unresolvable"}
        rtt = _ping(ip, 800)
        name = _resolve(ip)
        services = _scan_ports(ip, list(SERVICE_PORTS))
        vendor = None
        mac = (dev or {}).get("mac") or self._arp_table().get(ip)
        if mac:
            vendor = OUI.get(mac[:8])
        # signal the device per capability
        signal = "icmp-echo"
        responded = rtt is not None
        peer = self._peer_probe(ip)
        if peer:
            signal = "hearth-peer-chirp"
            try:
                urllib.request.urlopen(
                    f"http://{ip}:{self.h.port}/api/fleet/chirp",
                    timeout=3)
            except Exception:
                pass
        elif "cast" in services:
            signal = "cast-endpoint-query"
        elif "smb" in services or "netbios-ssn" in services:
            signal = "netbios-query"
        result = {
            "ip": ip, "signalClass": signal,
            "deviceResponded": responded, "rttSeconds": rtt,
            "name": name or (dev or {}).get("name"),
            "vendor": vendor, "services": services,
            "peer": bool(peer),
            "typeInference": self._infer_type(name, vendor, services)}
        self.h.journal.append("device-identify", result,
                              claimant="user", basis="execution-evidence")
        return result
    def _infer_type(self, name, vendor, services):
        s = set(services or [])
        n = (name or "").lower()
        if "cast" in s and (vendor == "Google" or "google" in n):
            return "smart-display/speaker (cast)"
        if "iphone-sync" in s:
            return "ios-device"
        if "smb" in s or "netbios-ssn" in s or "rdp" in s:
            return "windows-host"
        if "ssh" in s and vendor and "Raspberry" in vendor:
            return "raspberry-pi"
        if "hearth-peer" in s:
            return "hearth-peer"
        if vendor:
            return (vendor or "unknown") + " device"
        return "unknown"
    def _peer_probe(self, ip):
        try:
            with urllib.request.urlopen(
                    f"http://{ip}:9540/api/health", timeout=1.5) as r:
                h = json.loads(r.read())
            if h.get("app") == "hearth":
                return h
        except Exception:
            pass
        return None
    # ---------------- invite / join / install (R-F4) ----------------------
    def invite(self, target, installable_hint=None):
        """User-mediated join: candidate -> invite -> attempt driven to
        a verdict on an installable target. No dead ends — directions
        recorded when the path stalls."""
        dev = next((d for d in self.discovery["devices"]
                    if d["ip"] == target or d.get("name") == target), None)
        roster_row = next((r for r in self.discovery["roster"]
                           if r.get("ip") == target), None)
        installable = roster_row.get("installable") if roster_row \
            else bool(installable_hint)
        invite = self.h.journal.append(
            "fleet-invite", {"target": target, "by": "user"},
            claimant="user", basis="user-choice")
        ip = target if re.match(r"^\d+\.\d+\.\d+\.\d+$", target) \
            else (dev or {}).get("ip")
        if not ip:
            verdict = {"verdict": "failed",
                       "reason": "target unresolvable — not an "
                                 "installable device",
                       "installable": bool(installable)}
        else:
            verdict = self._install_attempt(ip, installable)
        self.h.journal.append(
            "install-verdict",
            {"target": target, "ip": ip, **verdict,
             "rosterInstallable": bool(installable)},
            claimant="system", basis="execution-evidence",
            refs=[invite["id"]])
        return {"invite": invite["id"], "verdict": verdict,
                "target": target, "ip": ip}
    def _install_attempt(self, ip, installable):
        """Drive the join/install path to a verdict:
        installed | refused:<reason> | failed:<reason>."""
        steps = []
        # 1. is a hearth peer already there? -> join handshake
        peer = self._peer_probe(ip)
        if peer:
            join = self._peer_join(ip)
            steps.append({"step": "peer-join", "ok": join})
            if join:
                return {"verdict": "installed", "steps": steps,
                        "installable": installable}
        steps.append({"step": "peer-probe", "ok": False})
        # 2. SMB push attempt (Windows target): try opening the share —
        #    an authenticated push is refused without credentials
        services = _scan_ports(ip, [445, 139])
        if "smb" in services or "netbios-ssn" in services:
            steps.append({"step": "smb-probe", "ok": True})
            try:
                out = subprocess.run(
                    ["net", "use", r"\\" + ip + r"\ADMIN$"],
                    capture_output=True, text=True, timeout=8)
                if "successfully" in out.stdout.lower():
                    steps.append({"step": "admin-share", "ok": True})
                    return {"verdict": "installed", "steps": steps,
                            "installable": installable}
                steps.append({"step": "admin-share",
                              "ok": False,
                              "reason": (out.stderr or out.stdout).strip()
                              [:120]})
            except Exception as e:
                steps.append({"step": "admin-share", "ok": False,
                              "reason": str(e)[:120]})
            return {"verdict": "refused",
                    "reason": "SMB reachable; admin-share access denied "
                              "— credentials/consent required on target",
                    "directions": "On the target: run the seed installer "
                                  "from the USB drive, or allow the share "
                                  "and retry invite.",
                    "steps": steps, "installable": installable}
        # 3. nothing listens — failed with reason
        return {"verdict": "failed",
                "reason": "no hearth peer and no reachable install "
                          "channel (smb/admin$) on target",
                "directions": "Carry the USB seed to the device and run "
                              "the installer there; the device joins on "
                              "first run.",
                "steps": steps, "installable": installable}
    def _peer_join(self, ip):
        """Join handshake with a real hearth peer — role negotiation +
        credential surrender recorded on both books."""
        try:
            body = {"node": self.h.node["id"],
                    "network": self.h.node["network"],
                    "consentsToSurrender": True}
            req = urllib.request.Request(
                f"http://{ip}:9540/api/fleet/hello",
                data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=4) as r:
                resp = json.loads(r.read())
            if resp.get("memberId"):
                self.members[resp["memberId"]] = {
                    "id": resp["memberId"], "ip": ip,
                    "role": resp.get("role", "satellite"),
                    "sameHost": False}
                return True
        except Exception:
            pass
        return False
    def peer_hello(self, body):
        """Target side of the join handshake — role negotiation +
        surrender recorded."""
        role = "satellite"
        mid = "mem-" + self.h.node["id"]
        self.members[mid] = {"id": mid, "ip": body.get("addr"),
                             "role": role, "sameHost": False}
        self.h.journal.append("role-grant",
                              {"member": mid, "role": role,
                               "mint": False},
                              claimant="system", basis="claim")
        self.h.journal.append("surrender-claim",
                              {"member": mid,
                               "note": "joining peer consents to "
                                       "surrender credential management; "
                                       "secrets stay host-local"},
                              claimant="system", basis="claim")
        return {"memberId": mid, "role": role,
                "network": self.h.node["network"]}
    def peer_delta(self, body):
        """Sovereign-hub sync — append-only delta exchange unioned with
        read-time trust resolution (C-SovereignHubs)."""
        since = body.get("since", 0)
        delta = [r for r in self.h.journal.rows()
                 if r["ts"] > since][:200]
        return {"rows": delta, "network": self.h.node["network"]}
    def chirp(self):
        """Identify signal landing on a peer — a perceivable response
        within capability: console beep + a wav ping."""
        try:
            import winsound
            winsound.Beep(880, 150)
            winsound.Beep(1180, 150)
        except Exception:
            pass
        path = os.path.join(self.h.audio_dir, "chirp.wav")
        from . import audio
        audio.write_wav(path, audio.tone(880, 0.15) +
                        audio.tone(1180, 0.15))
        return {"chirped": True, "artifact": path}
    # ---------------- USB seed --------------------------------------------
    def medium_root(self):
        """The removable medium this instance runs from / writes to —
        external ground truth: the launched path's drive."""
        exe = os.path.abspath(self.h.root)
        drive = exe.split(os.sep)[0]
        return drive if drive else "C:"
    def on_removable(self):
        """True when launched from removable media — decided by path,
        corroborated by the drive type where checkable."""
        root_drive = os.path.splitdrive(os.path.abspath(self.h.root))[0]
        try:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"(Get-Volume -DriveLetter "
                 f"'{root_drive[0]}').DriveType"],
                capture_output=True, text=True, timeout=10)
            return "Removable" in out.stdout
        except Exception:
            return root_drive.upper() not in ("C:",)
    def seed_log(self, event, extra=None):
        """C-SeedLog: append-only local network log on the medium —
        witness courier accumulating history across visited machines."""
        if self.on_removable():
            path = os.path.join(self.medium_root() + os.sep,
                                "seed-log.jsonl")
        else:
            path = os.path.join(self.h.data_dir, "seed-log.jsonl")
        entry = {"ts": time.time(), "event": event,
                 "node": self.h.node["id"],
                 "network": self.h.node["network"],
                 "host": socket.gethostname(),
                 "medium": self.medium_root()}
        entry.update(extra or {})
        with open(path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return path
    def stage_consent(self, consent):
        """Stage to local disk only when update needed AND permitted;
        decline leaves the app running from media, no local write."""
        if not consent:
            self.h.journal.append("seed-stage",
                                  {"consent": False,
                                   "staged": False,
                                   "note": "declined — stays on media, "
                                           "no local write"},
                                  claimant="user", basis="user-choice")
            return {"staged": False, "declared": True}
        dest = os.path.join(STAGE_ROOT, "hearth")
        os.makedirs(dest, exist_ok=True)
        # stage the package
        import shutil
        src = os.path.join(self.h.root, "hearth")
        dst = os.path.join(dest, "hearth")
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        self.h.journal.append("seed-stage",
                              {"consent": True, "staged": True,
                               "dest": dest},
                              claimant="user", basis="user-choice")
        return {"staged": True, "dest": dest}
    def mint_gen2(self, medium_root=None):
        """C-SeedMint: capable installed node writes a new USB installer
        carrying the founding network identity as an adoptable offer —
        join-or-found is the user's choice."""
        medium = medium_root or self.medium_root()
        dest = os.path.join(medium + os.sep, "hearth-seed")
        import shutil
        src = os.path.join(self.h.root, "hearth")
        os.makedirs(dest, exist_ok=True)
        dst = os.path.join(dest, "hearth")
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
            "__pycache__", "runtime", "evidence"))
        with open(os.path.join(dest, "network-offer.json"), "w") as f:
            json.dump({"offeredNetwork": self.h.node["network"],
                       "choice": "join-or-found",
                       "note": "first run may join the carried network "
                               "identity or found a new one — user's "
                               "choice"}, f, indent=1)
        with open(os.path.join(dest, "launch.cmd"), "w") as f:
            f.write("@echo off\r\n"
                    "cd /d %~dp0\r\n"
                    "python -m hearth --port 9540\r\n")
        self.h.journal.append(
            "seed-mint", {"dest": dest,
                          "carriedNetwork": self.h.node["network"],
                          "choice": "join-or-found"},
            claimant="user", basis="execution-evidence")
        return dest
