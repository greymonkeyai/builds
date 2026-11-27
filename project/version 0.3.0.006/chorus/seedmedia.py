"""USB seed lifecycle (C-UsbSeed, C-SeedStagePath, C-SeedLifecycle, C-SeedLog,
C-SeedMint, C-SeedSigning).
A removable medium carries a portable executable that runs in place — no
install required. Staging to local disk only when needed AND permitted;
declining leaves the app running from media with no local write. The medium
carries an append-only local network log (witness courier). Capable
installed nodes mint gen-2 installers carrying the founding network's
identity as an adoptable offer — join-or-found is the user's choice.
"""
import json
import os
import shutil
import sys
import time
from .book import now_iso
STAGE_PATH = r"C:\builds-installed\chorus"
SEED_LOG = "seed-log.jsonl"
def is_removable(path):
    """True when the app is executing from removable media."""
    try:
        drive = os.path.splitdrive(os.path.abspath(path))[0] + "\\"
        import ctypes
        DRIVE_REMOVABLE = 2
        return ctypes.windll.kernel32.GetDriveTypeW(drive) == DRIVE_REMOVABLE
    except Exception:
        return "usb" in path.lower() or os.path.splitdrive(path)[0].upper() \
            not in ("C:",)
def app_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def seed_log_path(root=None):
    return os.path.join(root or app_root(), SEED_LOG)
def append_seed_log(entry, root=None):
    """Witness courier: machine-readable per-node evidence appended on the
    medium itself."""
    entry = dict(entry)
    entry["at"] = now_iso()
    try:
        with open(seed_log_path(root), "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return True
    except Exception:
        return False
def read_seed_log(root=None):
    p = seed_log_path(root)
    if not os.path.exists(p):
        return []
    out = []
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out
def prepare_seed(host, media_root):
    """Build the seed payload onto media at media_root: app + launcher +
    network identity + signing notes (C-SeedSigning — allowlist arrangement
    documented; no Authenticode cert on this machine, declared)."""
    dest = os.path.join(media_root, "chorus-seed")
    os.makedirs(dest, exist_ok=True)
    src = app_root()
    for item in ("chorus", "launch-seed.cmd", "launch.cmd", "LAUNCH.md",
                 "FEATURES.md", "fixtures"):
        s = os.path.join(src, item)
        d = os.path.join(dest, item)
        if os.path.isdir(s):
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.copytree(s, d)
        elif os.path.exists(s):
            shutil.copy2(s, d)
    identity = {"network": host.network_id, "founder": host.node_id,
                "mintedAt": now_iso(),
                "offer": "adoptable — first run may join this network or "
                         "found a new one; the choice is the user's"}
    with open(os.path.join(dest, "network-identity.json"), "w",
              encoding="utf-8") as f:
        json.dump(identity, f, indent=1)
    with open(os.path.join(dest, "SIGNING-NOTES.md"), "w",
              encoding="utf-8") as f:
        f.write("# Signing arrangement (C-SeedSigning)\n\n"
                "This seed is unsigned Python source — no Authenticode cert "
                "on the build host. Lab arrangement: allowlist the seed "
                "folder in AV on lab/target machines (documented, method "
                "free). A killed first run misreports as empty discovery — "
                "treat absence-of-run as a signing/AV finding, not a "
                "discovery result.\n")
    append_seed_log({"event": "seed-prepared", "node": host.node_id,
                     "network": host.network_id, "media": media_root},
                    root=dest)
    return dest
def boot_seed(host):
    """Called when the app detects it's running from removable media.
    Order per C-SeedLifecycle: run in place → log → stage-consent →
    discovery → invites → roles → install."""
    root = app_root()
    append_seed_log({"event": "seed-run", "node": host.node_id,
                     "network": host.network_id,
                     "media": root,
                     "mediaRoot": root,
                     "machine": os.environ.get("COMPUTERNAME", "unknown"),
                     "ranInPlace": True})
    prior = read_seed_log()
    host.book.append("seed:run", {
        "subject": "usb-seed", "ranInPlace": True, "mediaRoot": root,
        "courierEntries": len(prior),
        "machine": os.environ.get("COMPUTERNAME", "unknown")},
        claimant="host", basis="execution-evidence")
    if prior:
        # courier carries accumulated network history into this run
        host.book.append("seed:courier-sync", {
            "subject": "usb-seed", "entries": len(prior),
            "events": [e.get("event") for e in prior][-12:]},
            claimant="host", basis="source-evidence")
    return {"courier": len(prior)}
def stage_consent(host, allowed):
    """Stage to local disk only when needed and permitted; declining leaves
    the app on media with NO local write (S-usb-stage-consent)."""
    if not allowed:
        host.book.append("seed:stage-consent", {
            "subject": "stage", "allowed": False,
            "outcome": "declined — running from media, no local write"},
            claimant="principal", certainty=1.0, basis="user-choice")
        return {"staged": False, "localWrite": False}
    os.makedirs(STAGE_PATH, exist_ok=True)
    src = app_root()
    for item in ("chorus", "launch.cmd", "launch-seed.cmd", "LAUNCH.md",
                 "FEATURES.md", "fixtures"):
        s = os.path.join(src, item)
        d = os.path.join(STAGE_PATH, item)
        if os.path.isdir(s):
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.copytree(s, d)
        elif os.path.exists(s):
            shutil.copy2(s, d)
    host.book.append("seed:stage-consent", {
        "subject": "stage", "allowed": True,
        "outcome": f"staged to {STAGE_PATH}"},
        claimant="principal", certainty=1.0, basis="user-choice")
    return {"staged": True, "path": STAGE_PATH}
def mint_gen2(host, media_root):
    """A capable installed node mints a gen-2 installer carrying the
    founding network's identity as an adoptable offer (C-SeedMint)."""
    dest = prepare_seed(host, media_root)
    host.book.append("seed:mint", {
        "subject": "gen2", "path": dest,
        "carries": host.network_id,
        "joinOrFound": "user choice — carry not enforce"},
        claimant="host", basis="execution-evidence")
    return dest
