"""Publishing lifecycle + exchange packages + account credentialing.
C-PublishOrDefer: select holdings -> choose form/channel -> produce the
artifact and record the exchange — or defer with request + status recorded
where the channel is unconfigured. No silent absence.
C-CredentialDescriptor: external accounts are configurable through an
owner-facing path; a configured account is a configured-source row — the
descriptor recorded, the secret held per local-credential conventions;
secrets never in ledger rows, logs, or exchange media.
"""
import email
import imaplib
import json
import os
from . import artifacts
from .book import fresh_id, now_iso
CRED_DIR = "credentials"
def cred_path(host):
    d = os.path.join(host.runtime_dir, CRED_DIR)
    os.makedirs(d, exist_ok=True)
    return d
def configure_account(host, kind, address, secret, imap_host=None,
                      smtp_host=None):
    """Owner-facing credentialing path: Gmail/iCloud-class account via
    app-password/IMAP. Secret goes to the local credential store — never
    the ledger. The descriptor row IS the configured-source record."""
    account = {"kind": kind, "address": address,
               "imap": imap_host or _default_imap(kind),
               "smtp": smtp_host, "configuredAt": now_iso()}
    cred_file = os.path.join(cred_path(host), f"{kind}-{fresh_id('cred')}.json")
    with open(cred_file, "w", encoding="utf-8") as f:
        json.dump({**account, "secret": secret}, f)
    source_key = f"source-acct-{kind}"
    row = host.book.append("source:configured", {
        "subject": source_key, "kind": "account-imap",
        "name": f"{kind} account {address}",
        "descriptor": "granted_only",
        "credentialDescriptor": {"kind": kind, "address": address,
                                 "imap": account["imap"],
                                 "secretRef": os.path.basename(cred_file)},
        "domains": ["email", "correspondence"], "ceiling": 0.7},
        claimant="principal", certainty=1.0, basis="user-choice")
    host.sources[source_key] = {
        "key": source_key, "kind": "account", "name": f"{kind} account",
        "descriptor": "granted_only", "domains": ["email"],
        "ceiling": 0.7, "credential": os.path.basename(cred_file),
        "admitted": True}
    return row
def _default_imap(kind):
    return {"gmail": "imap.gmail.com", "icloud": "imap.mail.me.com"}.get(kind)
def read_account_mail(host, source_key, limit=10):
    """Once configured, the email path reads the real account."""
    src = host.sources.get(source_key)
    if not src or not src.get("credential"):
        return None
    cf = os.path.join(cred_path(host), src["credential"])
    if not os.path.exists(cf):
        return None
    cred = json.load(open(cf, encoding="utf-8"))
    try:
        m = imaplib.IMAP4_SSL(cred["imap"])
        m.login(cred["address"], cred["secret"])
        m.select("inbox")
        _, data = m.search(None, "ALL")
        ids = data[0].split()[-limit:]
        out = []
        for mid in reversed(ids):
            _, msg = m.fetch(mid, "(RFC822)")
            msgobj = email.message_from_bytes(msg[0][1])
            out.append({"subject": msgobj.get("Subject"),
                        "from": msgobj.get("From"),
                        "date": msgobj.get("Date")})
        m.logout()
        return out
    except Exception as e:
        return {"error": str(e)[:160], "declared": True}
def fixture_inbox(host):
    """Honest fixture basis — labeled, never confused with a live account."""
    inbox = os.path.join(host.root, "fixtures", "inbox")
    out = []
    if os.path.isdir(inbox):
        for name in sorted(os.listdir(inbox)):
            if name.endswith(".eml"):
                msg = email.message_from_binary_file(
                    open(os.path.join(inbox, name), "rb"))
                out.append({"subject": msg.get("Subject"),
                            "from": msg.get("From"),
                            "date": msg.get("Date"),
                            "file": name, "basis": "fixture-directory"})
    return out
def publish(host, holding, form):
    """The publishing workflow (C-PublishOrDefer): select a holding ->
    choose form/channel -> produce + record, or defer + record."""
    request = {"subject": holding, "form": form, "requestedAt": now_iso()}
    configured_channels = {"scancode", "postcard", "file"}
    live_email = any(k.startswith("source-acct-") and
                     host.sources[k].get("credential")
                     for k in host.sources)
    if form in configured_channels:
        out_dir = os.path.join(host.runtime_dir, "artifacts")
        os.makedirs(out_dir, exist_ok=True)
        payload = json.dumps({"holding": holding, "network": host.network_id,
                              "issuedAt": now_iso()}).encode()
        if form == "scancode":
            path = os.path.join(out_dir, f"pub-{fresh_id('x')}.bmp")
            meta = artifacts.encode_rastgrid(payload, path)
            produced = {"kind": "scancode", "file": path,
                        "symbology": meta["symbology"]}
        elif form == "postcard":
            path = os.path.join(out_dir, f"postcard-{fresh_id('x')}.html")
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"<html><body><h2>Postcard</h2><p>{holding}</p>"
                        f"<p>network {host.network_id}</p></body></html>")
            produced = {"kind": "postcard", "file": path}
        else:
            path = os.path.join(out_dir, f"pub-{fresh_id('x')}.json")
            with open(path, "wb") as f:
                f.write(payload)
            produced = {"kind": "file", "file": path}
        row = host.book.append("exchange:published", {
            **request, "state": "produced", "artifact": produced},
            claimant="host", certainty=0.9, basis="execution-evidence")
        return {"state": "produced", "artifact": produced, "row": row["id"]}
    if form in ("email",) and live_email:
        row = host.book.append("exchange:published", {
            **request, "state": "produced",
            "artifact": {"kind": "email-class",
                         "via": "configured account — send deferred to "
                                "operator confirm"}},
            claimant="host", certainty=0.9, basis="execution-evidence")
        return {"state": "produced", "row": row["id"]}
    # deferral — the request and its status are recorded, never silent
    row = host.book.append("exchange:deferred", {
        **request, "state": "deferred",
        "reason": f"channel '{form}' unconfigured on this host",
        "path": "configure the channel on the accounts/settings surface, "
                "then re-issue the publish request"},
        claimant="host", certainty=0.9, basis="execution-evidence")
    return {"state": "deferred", "row": row["id"],
            "reason": f"channel '{form}' unconfigured"}
def export_package(host, what="library-sample"):
    """Exchange package — contents import below the threshold for action
    or acceptance on the receiving host (D9)."""
    personas = [{"name": p["name"], "register": p.get("register"),
                 "domains": p.get("domains")} for p in
                list(host.personas.values())[:3]]
    tools = [{"componentId": k, "purpose": v["purpose"], "inputs": v["inputs"]}
             for k, v in list(host.tool_catalog.items())[:4]]
    pkg = {"schema": "chorus-exchange-1", "from": host.node_id,
           "issuedAt": now_iso(), "what": what,
           "personas": personas, "tools": tools,
           "needs": [n["claim"].get("requirement")
                     for n in host.needs.floor()][:5]}
    path = os.path.join(host.runtime_dir, "artifacts",
                        f"package-{fresh_id('x')}.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pkg, f, indent=1)
    host.book.append("exchange:exported", {
        "subject": what, "file": path, "schema": pkg["schema"]},
        claimant="host", basis="execution-evidence")
    return pkg, path
def import_package(host, pkg, origin="file"):
    """Receiving host records imported assertions below the threshold for
    action or acceptance by default — resolved through its own ledger."""
    imported = 0
    for p in pkg.get("personas", []):
        host.book.append("exchange:imported-persona", {
            "subject": p["name"], **p, "candidate": True,
            "belowThreshold": True, "origin": origin},
            claimant="source:exchange", certainty=0.3, basis="exchange")
        imported += 1
    for t in pkg.get("tools", []):
        host.book.append("tool:candidate", {
            "subject": t["componentId"], "definition": t,
            "status": "candidate", "accepted": False,
            "note": "foreign tool — never live-by-default"},
            claimant="source:exchange", certainty=0.3, basis="exchange")
        imported += 1
    host.book.append("exchange:imported", {
        "subject": pkg.get("what", "package"), "rows": imported,
        "belowThreshold": True, "origin": origin},
        claimant="host", certainty=0.85, basis="execution-evidence")
    return imported
