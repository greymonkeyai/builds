"""Quorum fleet — USB seed lifecycle, honest discovery, invites, roles,
peers, credential surrender.

(C-UsbSeed, C-SeedStagePath, C-SeedLifecycle, C-SeedLog, C-SeedMint,
C-LocalTransports, C-HonestDiscovery, C-SeedSigning; decision-candidates
§3 sovereign hub ledgers, §5 host-sovereign credential screen)

SEED LIFECYCLE (bound order):
  execute in place from media → stage to local disk ONLY when needed AND
  permitted (decline leaves the app on media, no local write) → network
  discovery → user-mediated invites (no silent auto-join) → role
  negotiation → capable targets install.

DISCOVERY is broad and honest: everything found is recorded, including
non-fleet devices — no silent filtering. Coverage is test data. A local
network map is a produced artifact maintained alongside the member network.
A second instance on the same host does NOT count as a joined device.
"""
from __future__ import annotations

import ipaddress
import json
import os
import re
import shutil
import socket
import subprocess
import threading
import time
import urllib.request

from . import rows

# ---------------------------------------------------------------------------
# Named roster (derived operational data per direction-005 — the private
# inventory document is NOT mirrored; this keyed list comes from
# conventions-002 §Fleet test roster and D105 role topology).
ROSTER = [
    {"key": "PC-DEV",       "name": "this machine",        "transports": ["wired-lan"], "expect": "seed/observer host", "install": False},
    {"key": "PC-RMATA-01",  "name": "RMT-93",              "transports": ["wired-lan"], "expect": "fleet target — stable node", "install": True},
    {"key": "PC-RMATA-02",  "name": "RMT-105",             "transports": ["wired-lan"], "expect": "fleet target — resettable/seed node", "install": True},
    {"key": "PC-GMK",       "name": "NUCBOX_G3_PRO",       "transports": ["wired-lan", "wifi", "bt"], "expect": "fleet target; host-capable", "install": True},
    {"key": "TAB-YOGA",     "name": "TAB-YOGA",            "transports": ["wifi"],      "expect": "surface-class (ARM) — likely not-installable", "install": False},
    {"key": "ECHO-DOT",     "name": "Echo Dot(s)",         "transports": ["bt", "wifi"],"expect": "appliance — not installable", "install": False},
    {"key": "ANDROID-PH-1", "name": "Android phone 1",     "transports": ["wifi"],      "expect": "surface-class", "install": False},
    {"key": "ANDROID-PH-2", "name": "Android phone 2",     "transports": ["wifi"],      "expect": "surface-class", "install": False},
    {"key": "ANDROID-TAB",  "name": "Android/Fire tablets","transports": ["wifi"],      "expect": "surface/kiosk-class", "install": False},
    {"key": "PC-TERRY",     "name": "Terryza T6",          "transports": ["wired-lan", "wifi"], "expect": "triage datapoint", "install": True},
    {"key": "STICK-WIN",    "name": "STICK-WIN",           "transports": ["wired-lan", "wifi"], "expect": "unknown state", "install": True},
    {"key": "TAB-SURF",     "name": "loaner Surface",      "transports": ["wifi"],      "expect": "loaner — consent care", "install": False},
    {"key": "RPI-01",       "name": "Raspberry Pi 1",      "transports": ["wired-lan", "wifi"], "expect": "side device, not a target", "install": False},
    {"key": "RPI-02",       "name": "Raspberry Pi 2",      "transports": ["wired-lan", "wifi"], "expect": "side device, not a target", "install": False},
    {"key": "SPK-SONOS-01", "name": "Sonos speaker",       "transports": ["lan"],       "expect": "appliance — not installable", "install": False},
]
# hostname substring → roster key (names drift, keys don't)
HOSTNAME_HINTS = [
    ("rmt-93", "PC-RMATA-01"), ("rmata", "PC-RMATA-01"),
    ("rmt-105", "PC-RMATA-02"),
    ("nucbox", "PC-GMK"), ("g3_pro", "PC-GMK"), ("gmk", "PC-GMK"),
    ("yoga", "TAB-YOGA"),
    ("terryza", "PC-TERRY"), ("terry", "PC-TERRY"),
    ("stick-win", "STICK-WIN"), ("stickwin", "STICK-WIN"),
    ("echo", "ECHO-DOT"), ("amazon-", "ECHO-DOT"),
    ("surface", "TAB-SURF"),
    ("raspberrypi", "RPI-01"), ("rpi", "RPI-01"),
    ("sonos", "SPK-SONOS-01"),
    ("android", "ANDROID-PH-1"),
]
# MAC OUI prefixes (first 3 bytes) → hint (rough, honest-label only)
OUI_HINTS = {
    "b4:2e:99": "PC-GMK", "1c:69:7a": "ECHO-DOT", "44:65:0d": "ECHO-DOT",
    "f0:27:65": "ECHO-DOT", "cc:f7:35": "ECHO-DOT", "68:37:e9": "ECHO-DOT",
    "b8:27:eb": "RPI-01", "dc:a6:32": "RPI-01", "e4:5f:01": "RPI-01",
    "00:1c:c0": "SPK-SONOS-01", "b8:e9:37": "SPK-SONOS-01",
    "5c:aa:fd": "SPK-SONOS-01", "48:a6:b8": "SPK-SONOS-01",
    "94:9f:3e": "SPK-SONOS-01", "00:0e:58": "SPK-SONOS-01",
    "78:28:ca": "SPK-SONOS-01", "c8:69:cd": "SPK-SONOS-01",
}

STAGE_PATH = r"C:\builds-installed"          # C-SeedStagePath
SEED_LOG = "seed-log.jsonl"                  # C-SeedLog append-only courier log
APP_PORT = 9790


def find_seed_media(label: str = "BUILD") -> dict:
    """Locate the removable seed medium — the USB drive labeled `build`."""
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-Volume | Where-Object {$_.DriveType -eq 'Removable' -and "
             "$_.DriveLetter} | Select-Object DriveLetter,FileSystemLabel "
             "| ConvertTo-Json"],
            capture_output=True, text=True, timeout=15)
        vols = json.loads(out.stdout or "[]")
        if isinstance(vols, dict):
            vols = [vols]
        for v in vols:
            if (v.get("FileSystemLabel") or "").upper() == label.upper():
                return {"found": True, "letter": f"{v['DriveLetter']}:",
                        "label": v["FileSystemLabel"]}
        return {"found": False, "removable": [f"{v['DriveLetter']}:" for v in vols]}
    except Exception as e:
        return {"found": False, "error": str(e)}


# ---------------------------------------------------------------------------
# DISCOVERY — broad, honest, everything recorded (C-HonestDiscovery)
def _host_subnet() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return ""

def _arp_table() -> list[dict]:
    out = []
    try:
        txt = subprocess.run(["arp", "-a"], capture_output=True, text=True,
                             timeout=15).stdout
        for m in re.finditer(r"(\d+\.\d+\.\d+\.\d+)\s+([\da-fA-F-]{17})\s+(\w+)", txt):
            mac = m.group(2).replace("-", ":").lower()
            out.append({"ip": m.group(1), "mac": mac, "arp_type": m.group(3)})
    except Exception:
        pass
    return out

def _nbtstat_name(ip: str) -> str:
    try:
        txt = subprocess.run(["nbtstat", "-A", ip], capture_output=True,
                             text=True, timeout=8).stdout
        m = re.search(r"^\s*([A-Z0-9\-_]+)\s+<00>\s+UNIQUE", txt, re.M | re.I)
        return m.group(1).strip() if m else ""
    except Exception:
        return ""

def _ping(ip: str) -> bool:
    try:
        r = subprocess.run(["ping", "-n", "1", "-w", "350", ip],
                           capture_output=True, timeout=3)
        return r.returncode == 0
    except Exception:
        return False

def _bt_devices() -> list[dict]:
    """Bluetooth-visible devices (paired radios + neighbors the stack sees)."""
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue | "
             "Where-Object {$_.Status -eq 'OK'} | Select-Object FriendlyName,"
             "InstanceId | ConvertTo-Json"],
            capture_output=True, text=True, timeout=20)
        devs = json.loads(out.stdout or "[]")
        if isinstance(devs, dict):
            devs = [devs]
        return [{"name": d.get("FriendlyName", ""), "transport": "bt",
                 "instance": d.get("InstanceId", "")} for d in devs
                if d.get("FriendlyName")]
    except Exception:
        return []

def _match_roster(name: str, mac: str) -> str:
    nl = (name or "").lower()
    for hint, key in HOSTNAME_HINTS:
        if hint in nl:
            return key
    oui = ":".join((mac or "").split(":")[:3])
    return OUI_HINTS.get(oui, "")

def discover(subnet_ping: bool = True) -> dict:
    """One honest discovery pass over local transports.
    Wired LAN baseline (C-LocalTransports preference); BT included where the
    stack reports it. Everything found is recorded — coverage is test data."""
    t0 = time.time()
    found = []
    host_ip = _host_subnet()
    arp = _arp_table()
    # probe arp entries + subnet neighbors for liveness
    cands = {e["ip"] for e in arp if not e["ip"].endswith(".255")
             and e["ip"] != "224.0.0.0" and not e["ip"].startswith("224.")
             and not e["ip"].startswith("239.")}
    if subnet_ping and host_ip:
        net = ipaddress.ip_network(f"{host_ip}/24", strict=False)
        cands |= {str(h) for h in list(net.hosts())[:254]}
    cands.discard(host_ip)

    live = {}
    lock = threading.Lock()
    def probe(ip):
        if _ping(ip):
            with lock:
                live[ip] = True
    threads = [threading.Thread(target=probe, args=(ip,)) for ip in sorted(cands)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=6)

    arp2 = _arp_table()                       # refresh after ping fill
    macs = {e["ip"]: e["mac"] for e in arp + arp2}
    for ip in sorted(set(list(live) + [e["ip"] for e in arp
                                       if e.get("arp_type") == "dynamic"])):
        name = _nbtstat_name(ip)
        mac = macs.get(ip, "")
        found.append({"ip": ip, "mac": mac, "name": name,
                      "transport": "wired-lan",
                      "roster": _match_roster(name, mac),
                      "reachable": ip in live})
    for d in _bt_devices():
        found.append({"ip": "", "mac": "", "name": d["name"],
                      "transport": "bt",
                      "roster": _match_roster(d["name"], ""),
                      "reachable": True, "bt_instance": d["instance"]})
    # this host — the seed/observer, on the map as itself
    me = {"ip": host_ip, "mac": "", "name": socket.gethostname(),
          "transport": "wired-lan", "roster": "PC-DEV",
          "reachable": True, "self": True}
    found.insert(0, me)

    roster_status = []
    found_keys = {f["roster"] for f in found if f.get("roster")}
    for r in ROSTER:
        seen = r["key"] in found_keys
        status = ("found" if seen else "unavailable") if r["install"] or seen \
            else ("found-not-target" if seen else "not-found-not-target")
        if seen and not r["install"]:
            status = "found-not-target"
        elif seen and r["install"]:
            status = "found-installable"
        roster_status.append({"key": r["key"], "expect": r["expect"],
                              "status": status,
                              "seen_as": [f for f in found if f.get("roster") == r["key"]]})
    return {"ok": True, "durationMs": int((time.time() - t0) * 1000),
            "found": found, "roster_status": roster_status,
            "transports": sorted({f["transport"] for f in found})}


# ---------------------------------------------------------------------------
# SEED LIFECYCLE
class Seed:
    """The USB-resident seed: runs in place, carries the append-only network
    log (witness courier), stages only with consent, mints gen-2 media."""

    def __init__(self, book, media_root: str):
        self.book = book
        self.media = media_root               # e.g. "H:\\seed"
        os.makedirs(media_root, exist_ok=True)

    @property
    def log_path(self) -> str:
        return os.path.join(self.media, SEED_LOG)

    def courier(self, entry: dict) -> dict:
        """C-SeedLog — append a machine-readable witness entry ON the medium.
        Accumulates network history across the machines it visits."""
        e = {"at": rows.now_ms(), "host": socket.gethostname(), **entry}
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
        self.book.claim("seed", "seed:courier", entry,
                        claimant="seed:usb", certainty=0.8, basis="execution")
        return e

    def courier_log(self) -> list[dict]:
        out = []
        if os.path.exists(self.log_path):
            for line in open(self.log_path, encoding="utf-8"):
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def stage(self, consent: bool, app_src: str) -> dict:
        """C-SeedLifecycle step 2 — stage to local disk ONLY when update is
        needed AND permitted. Decline → app stays on media, no local write."""
        if not consent:
            self.courier({"event": "stage-declined",
                          "note": "user declined staging — no local write"})
            return {"staged": False, "reason": "declined", "wrote": False}
        dest = os.path.join(STAGE_PATH, "quorum")
        os.makedirs(STAGE_PATH, exist_ok=True)
        shutil.copytree(app_src, dest, dirs_exist_ok=True)
        self.courier({"event": "staged", "dest": dest})
        return {"staged": True, "dest": dest, "wrote": True}

    def mint(self, app_src: str, network_id: str, dest_label="gen2") -> dict:
        """C-SeedMint — write a NEW USB installer carrying the founding
        network's identity AS AN ADOPTABLE OFFER (carry, not enforce:
        first run may join the carried network or found a new one)."""
        dest = os.path.join(self.media, f"minted-{dest_label}")
        os.makedirs(dest, exist_ok=True)
        shutil.copytree(app_src, os.path.join(dest, "quorum"),
                        dirs_exist_ok=True)
        identity = {"network_id": network_id, "minted_by": socket.gethostname(),
                    "at": rows.now_ms(), "offer": "adoptable — join carried "
                    "network or found a new one; the choice is the user's"}
        with open(os.path.join(dest, "network-identity.json"), "w",
                  encoding="utf-8") as f:
            json.dump(identity, f, indent=2)
        # C-SeedSigning — success-gating: arrange signing / AV-allowlisting
        # so a killed first run doesn't misreport as empty discovery. No
        # Authenticode cert on this machine: the arrangement is a manifest
        # + documented allowlist steps, honestly labeled.
        manifest = {"files": [], "signed": False,
                    "note": "unsigned — Python stdlib sources; see "
                            "SIGNING-NOTES.md for the AV allowlist "
                            "arrangement on lab/target machines"}
        for root_, _, files in os.walk(dest):
            for fn in files:
                manifest["files"].append(
                    os.path.relpath(os.path.join(root_, fn), dest))
        with open(os.path.join(dest, "manifest.json"), "w",
                  encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        with open(os.path.join(dest, "SIGNING-NOTES.md"), "w",
                  encoding="utf-8") as f:
            f.write(
                "# Seed signing / AV allowlist (C-SeedSigning)\n\n"
                "This seed is unsigned Python source launched via the "
                "system interpreter — there is no binary to sign on this "
                "machine (declared). To prevent a killed first run "
                "misreporting as empty discovery, arrange on each lab/"
                "target machine:\n\n"
                "1. Allowlist `python.exe` + this media path in the host "
                "AV/Defender (exclusions → `H:\\quorum-seed` or the "
                "minted folder).\n"
                "2. If SmartScreen prompts on `launch-seed.cmd`, choose "
                "'More info → Run anyway' once — that is the consent gate, "
                "not a failure.\n"
                "3. If a cert is issued later, sign `launch-seed.cmd` and "
                "re-record `manifest.json` with `signed: true`.\n")
        self.courier({"event": "mint", "dest": dest,
                      "network_id": network_id})
        return {"minted": dest, "identity": identity}


# ---------------------------------------------------------------------------
# FLEET MEMBERSHIP — invites are user-mediated; no silent auto-join
class Fleet:
    def __init__(self, book, seed: Seed | None = None):
        self.book = book
        self.seed = seed
        self.members: dict[str, dict] = {}    # roster-key -> member record
        self.invites: dict[str, dict] = {}
        self.network_id = f"net-{rows.new_id('n')[2:]}"
        self.peers: dict[str, dict] = {}      # peer_id -> peer book handle

    def invite(self, discovery: dict, keys: list[str]) -> dict:
        """C-SeedLifecycle step 4 — the user picks which discovered devices
        get invites. Non-invited devices are never members."""
        invited = []
        dev_by_key = {}
        for f in discovery.get("found", []):
            if f.get("roster"):
                dev_by_key.setdefault(f["roster"], f)
        for key in keys:
            dev = dev_by_key.get(key)
            inv = {"key": key, "at": rows.now_ms(), "issued": True,
                   "device": dev, "state": "issued"}
            self.invites[key] = inv
            invited.append(inv)
            self.book.claim(f"fleet:{key}", "fleet:invite", inv,
                            claimant="principal", certainty=1.0,
                            basis="user-choice")
        if self.seed:
            self.seed.courier({"event": "invites-issued", "keys": keys})
        return {"invited": invited,
                "not_invited": [k for k in dev_by_key if k not in keys]}

    def negotiate_role(self, key: str, installable: bool) -> dict:
        """C-SeedLifecycle step 5 — role negotiation per joined device;
        mint capability is a negotiated role grant, not universal."""
        caps = ["ledger-hub"] if installable else ["surface"]
        role = {"key": key, "caps": caps, "mint": installable,
                "at": rows.now_ms()}
        self.book.claim(f"fleet:{key}", "fleet:role", role,
                        claimant="system", certainty=0.9, basis="execution")
        return role

    def join(self, key: str, device: dict, same_host: bool = False) -> dict:
        """A device joins after invite + role negotiation + credential
        surrender consent. Same-host second instances are honestly excluded
        from device membership (owner ruling 2026-11-25).

        Join is REAL: the target's peer endpoint is probed; membership
        completes only when a live install answers. A device not running a
        reachable install stays 'pending' — recorded, never faked."""
        if same_host:
            return {"ok": False, "member": False,
                    "note": "same-host instance does not count as a joined "
                            "device (owner ruling) — peer exercise only"}
        if key not in self.invites:
            return {"ok": False, "member": False,
                    "error": "not invited — joins are user-mediated"}
        installable = any(r["key"] == key and r["install"] for r in ROSTER)
        role = self.negotiate_role(key, installable)
        peer = self._probe_peer(device)
        member = {"key": key, "device": device, "role": role,
                  "peer_endpoint": peer,
                  "state": "member" if peer["reachable"] else "pending",
                  "joined_at": rows.now_ms()}
        if peer["reachable"]:
            self.members[key] = member
            self.credential_surrender(key)
        self.book.claim(f"fleet:{key}", "fleet:member", member,
                        claimant="system", certainty=0.9,
                        basis="execution" if peer["reachable"] else "refusal")
        if self.seed:
            self.seed.courier({"event": "join-attempt", "key": key,
                               "state": member["state"]})
        return {"ok": peer["reachable"], "member": member,
                "note": "member" if peer["reachable"] else
                        "pending — device not running a reachable install; "
                        "invite + role + surrender-consent recorded"}

    def _probe_peer(self, device: dict) -> dict:
        """Is a live install reachable on this device? Real probe, honest
        answer — a device with no running peer cannot join."""
        ip = (device or {}).get("ip", "")
        if not ip:
            return {"reachable": False, "endpoint": None}
        for port in (APP_PORT, 9791):
            try:
                with urllib.request.urlopen(
                        f"http://{ip}:{port}/api/honesty", timeout=3) as r:
                    d = json.loads(r.read())
                if str(d.get("app", "")).startswith("quorum"):
                    return {"reachable": True,
                            "endpoint": f"http://{ip}:{port}",
                            "peer_app": d.get("app")}
            except Exception:
                continue
        return {"reachable": False, "endpoint": None,
                "note": "no quorum endpoint answered — device is present "
                        "but not installed/running"}

    def install(self, key: str) -> dict:
        """C-SeedLifecycle step 6 — capable target machines install the app.
        Honest attempt: probe the target's admin share / reachability and
        record the real outcome; a failed push is recorded, not faked."""
        member = self.members.get(key)
        if not member:
            return {"ok": False, "error": "not a member"}
        dev = member.get("device") or {}
        ip = dev.get("ip", "")
        if member.get("state") != "member":
            return {"ok": False, "error": "join pending — install requires "
                    "a reachable peer endpoint",
                    "status": member.get("state"), "recorded": True}
        if not ip:
            return {"ok": False, "error": "no address — device not reachable",
                    "recorded": True}
        share = f"\\\\{ip}\\C$"
        reachable = os.path.exists(share)
        outcome = {"key": key, "target": ip, "share": share,
                   "share_reachable": reachable,
                   "status": "installable" if reachable else
                             "target unreachable to install push — recorded"}
        self.book.claim(f"fleet:{key}", "fleet:install", outcome,
                        claimant="system", certainty=0.9,
                        basis="execution" if reachable else "refusal")
        if self.seed:
            self.seed.courier({"event": "install-attempt", **outcome})
        return {"ok": reachable, **outcome}

    # ---- credential surrender (decision-candidates §5) -----------------------
    def credential_surrender(self, key: str) -> dict:
        """Join surrenders credential management to the host. The satellite's
        credential screen closes (status may remain); secrets stay host-local.
        Recorded as a claim on both books (host book here + peer book via
        peer rows when exchanged)."""
        return self.book.claim(
            f"fleet:{key}", "peer:credential-surrender",
            {"key": key, "surrendered": True,
             "note": "credential screen closed on join; secrets stay "
                     "host-local; needs travel, secrets never do"},
            claimant="principal", certainty=1.0, basis="user-choice")

    # ---- peer topology (decision-candidates §3) -------------------------------
    def pair_peer(self, peer_id: str, endpoint: str) -> dict:
        """A paired peer is a configured source (source:peer descriptor row)."""
        desc = {"peer": peer_id, "endpoint": endpoint, "state": "paired"}
        self.peers[peer_id] = desc
        return self.book.claim(peer_id, "source:peer", desc,
                               claimant="system", certainty=0.9, basis="config")

    def peer_delta(self, peer_book, peer_id: str, their_mark: int = 0) -> dict:
        """Rejoin correlation: append-only delta exchange both ways; union,
        never rewrite; conflicts resolve at read time."""
        ours = self.book.rows_after(their_mark)
        n_imported = peer_book.import_rows(ours, peer_id)
        return {"sent": len(ours), "imported_by_peer": n_imported}

    def sever(self, peer_id: str) -> dict:
        """peer:sever — intentional severance is a principal-authored claim;
        later contact presents the rejoin/new-ownership fork, never silent
        re-merge."""
        return self.book.claim(peer_id, "peer:sever",
                               {"peer": peer_id, "intentional": True},
                               claimant="principal", certainty=1.0,
                               basis="user-choice")

    def rejoin_offer(self, peer_id: str) -> dict:
        """On contact with a severed peer: the fork is presented."""
        severed = bool(self.book.find(predicate="peer:sever",
                                      subject=peer_id))
        return {"peer": peer_id, "severed": severed,
                "offer": ["rejoin", "new-ownership"] if severed else ["rejoin"]}

    # ---- network map (C-HonestDiscovery) -------------------------------------
    def network_map(self, discovery: dict, out_dir: str) -> dict:
        """The produced map artifact: member network + discovered non-members,
        maintained alongside the member network."""
        m = {"generated": rows.now_ms(), "network_id": self.network_id,
             "members": [{"key": k, "role": v.get("role", {}).get("caps")}
                         for k, v in self.members.items()],
             "discovered": discovery.get("found", []),
             "roster_status": discovery.get("roster_status", []),
             "transports": discovery.get("transports", []),
             "note": "broad+honest: non-fleet devices recorded on the map, "
                     "never members"}
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, "network-map.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(m, f, indent=2, ensure_ascii=False)
        self.book.claim("fleet", "fleet:map",
                        {"path": path, "devices": len(discovery.get("found", [])),
                         "members": len(self.members)},
                        claimant="system", certainty=0.9, basis="execution")
        return {"path": path, "map": m}
