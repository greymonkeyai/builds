"""hearth projects — projects, formal lists, temporal + place context.
C-FormalList: a list request creates a formal formatted list as an
assertion-ledger object — iterable, inspectable; the reply presents it.
Environmental grounding (prompt rev 2026-11-27-a): device location is
ledgered; home location canonical; departure/roaming/return handled with
staleness recorded, not hidden.
"""
import json
import os
import time
import urllib.request
class Projects:
    def __init__(self, host):
        self.h = host
    def create(self, name, goal, claimant="user"):
        return self.h.journal.append(
            "project", {"name": name, "goal": goal, "state": "open",
                        "needs": [], "results": []},
            claimant=claimant, basis="claim")
    def advance(self, project_id, note, need_ref=None):
        return self.h.journal.append(
            "project-progress",
            {"project": project_id, "note": note,
             "need": need_ref}, claimant="system", basis="claim",
            refs=[project_id])
    def view(self):
        out = []
        for p in self.h.journal.rows("project"):
            v = dict(p["value"]); v["id"] = p["id"]
            v["progress"] = [r["value"] for r in self.h.journal.rows(
                "project-progress", where={"project": p["id"]})]
            out.append(v)
        return out
    # ---- formal lists -------------------------------------------------
    def new_list(self, criteria, need_id=None, claimant="system"):
        row = self.h.journal.append(
            "list-object",
            {"criteria": criteria, "members": [], "nonMatches": [],
             "need": need_id, "state": "open", "iterable": True},
            claimant=claimant, basis="claim")
        return row
    def list_add(self, list_id, members, non_matches=None):
        return self.h.journal.append(
            "list-members",
            {"list": list_id, "members": members,
             "nonMatches": non_matches or []},
            claimant="tool:list-builder", basis="execution-evidence",
            refs=[list_id])
    def _assembled(self, row):
        """Members re-derived from list-members rows at read time."""
        v = dict(row["value"], id=row["id"])
        v["members"] = []
        v["nonMatches"] = []
        for m in self.h.journal.rows("list-members",
                                     where={"list": row["id"]}):
            v["members"] += m["value"].get("members", [])
            v["nonMatches"] += m["value"].get("nonMatches", [])
        st = self.h.journal.rows("list-state", where={"list": row["id"]})
        if st:
            v["state"] = st[-1]["value"].get("state", v["state"])
        return v
    def list_state(self, list_id, state):
        self.h.journal.append("list-state",
                              {"list": list_id, "state": state},
                              claimant="tool:list-builder",
                              basis="durable-result", refs=[list_id])
    def lists(self):
        return [self._assembled(r)
                for r in self.h.journal.rows("list-object")]
    def get_list(self, list_id):
        row = self.h.journal.get(list_id)
        return self._assembled(row) if row else None
    # ---- temporal context ---------------------------------------------
    def calendar(self):
        """Calendar entries are source evidence — interpreted per the
        same ledger/authority rules."""
        path = os.path.join(self.h.root, "fixtures", "calendar.json")
        items = []
        if os.path.exists(path):
            try:
                items = json.load(open(path))
            except Exception:
                pass
        return items
    # ---- place / environmental grounding ------------------------------
    def home_location(self):
        """Home location is canonical — pinned in config, derived from
        configured values, discovered signals, or user statement."""
        if "homeLocation" not in self.h.config:
            loc = self._geolocate()
            if loc is None:
                loc = {"lat": 0.0, "lon": 0.0,
                       "source": "unconfigured-declared", "stale": True}
            loc["canonical"] = True
            self.h.config["homeLocation"] = loc
            self.h._save_config()
            self.h.journal.append("location-claim",
                                  {"device": "home", **loc},
                                  claimant="system", basis="claim",
                                  provenance=loc.get("source", "config"))
        return self.h.config["homeLocation"]
    def _geolocate(self):
        """Discovered platform/network signal for device placement."""
        try:
            with urllib.request.urlopen(
                    "http://ip-api.com/json/?fields=lat,lon,city,regionName",
                    timeout=6) as r:
                d = json.loads(r.read())
            return {"lat": d.get("lat"), "lon": d.get("lon"),
                    "label": ", ".join(x for x in [d.get("city"),
                                                 d.get("regionName")] if x),
                    "source": "ip-geolocation", "stale": False}
        except Exception:
            return None
    def device_location(self, device, lat=None, lon=None, source="user",
                        label=None):
        """Record an attributed device-location assertion; roaming
        devices carry staleness rather than smoothing it over."""
        home = self.home_location()
        roaming = (lat is not None and home.get("lat") is not None and
                   abs(lat - home["lat"]) > 0.05)
        claim = {"device": device, "lat": lat, "lon": lon,
                 "label": label, "source": source,
                 "atHome": not roaming,
                 "stale": source == "unconfigured-declared"}
        self.h.journal.append("location-claim", claim,
                              claimant="user" if source == "user"
                              else "system",
                              basis="claim", provenance=source)
        return claim
    def environment(self):
        """Grounded environmental view: canonical home + per-device
        claims + freshest weather claim."""
        home = self.home_location()
        locs = {}
        for r in self.h.journal.rows("location-claim"):
            locs[r["value"]["device"]] = r["value"]
        weather = self.h.journal.rows("env-claim")
        w = None
        if weather:
            w = dict(weather[-1]["value"])
            w["freshnessSeconds"] = round(time.time() - weather[-1]["ts"], 0)
        return {"home": home, "devices": locs, "weather": w}
