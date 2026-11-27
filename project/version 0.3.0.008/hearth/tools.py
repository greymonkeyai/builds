"""hearth tools — persistently identifiable capabilities.
Minimal set, composition over bespoke minting (S-tool-composition).
Each tool: id, need-expression, input contract (required/optional
slots + thresholds), acceptance tests, exec. Competing realizations
of the same need produce comparable results (S-competing-tools).
"""
import time
# slot spec: name -> {"required":bool, "threshold":float}
def _accept_nonempty(result):
    return bool(result) and result.get("status") != "failed"
TOOLS = [
    {"id": "list.specialized", "need": "list-build",
     "explain": "Geographic/set list builder — specialized retrieval "
                "(C-SpecializedListRetrieval, C-SetBuild). Iterates a "
                "curated source set against declared criteria; records "
                "non-matches for review.",
     "slots": {"criteria": {"required": True, "threshold": 0.5}},
     "accept": _accept_nonempty},
    {"id": "list.general", "need": "list-build",
     "explain": "General-lookup list builder — competing realization of "
                "the same need; generic name recall against criteria.",
     "slots": {"criteria": {"required": True, "threshold": 0.5}},
     "accept": _accept_nonempty},
    {"id": "wiki.lookup", "need": "source-query",
     "explain": "Configured-source reader — mediawiki/api/web fetch "
                "through admitted source rows.",
     "slots": {"sourceKey": {"required": True, "threshold": 0.5},
               "query": {"required": True, "threshold": 0.4}},
     "accept": _accept_nonempty},
    {"id": "weather.read", "need": "env-claim",
     "explain": "Meteorological reader — open-meteo class; results are "
                "claims carrying provenance + freshness.",
     "slots": {"lat": {"required": True, "threshold": 0.5},
               "lon": {"required": True, "threshold": 0.5}},
     "accept": _accept_nonempty},
    {"id": "persona.mint", "need": "persona-create",
     "explain": "Mint a persistent persona from minimal input; opens "
                "portrait/voice/characterization needs.",
     "slots": {"name": {"required": True, "threshold": 0.5}},
     "accept": _accept_nonempty},
    {"id": "art.procedural", "need": "portrait-asset",
     "explain": "Procedural portrait renderer — generated art unique to "
                "each persona (C-PersonalityArt).",
     "slots": {"persona": {"required": True, "threshold": 0.5}},
     "accept": _accept_nonempty},
    {"id": "audio.synth", "need": "channel-asset",
     "explain": "Procedural audio synthesis — ack snippets, ambient "
                "beds, melodies. Real wav artifacts.",
     "slots": {"mood": {"required": True, "threshold": 0.5}},
     "accept": _accept_nonempty},
    {"id": "audio.music", "need": "scene-music",
     "explain": "Procedural music composition — seeded melodic phrases "
                "as wav. The build's music tool-class.",
     "slots": {"seed": {"required": True, "threshold": 0.4}},
     "accept": _accept_nonempty},
    {"id": "tts.sapi", "need": "speech",
     "explain": "SAPI speech composer — text to wav/device.",
     "slots": {"text": {"required": True, "threshold": 0.5},
               "voice": {"required": True, "threshold": 0.5}},
     "accept": _accept_nonempty},
    {"id": "scene.compose", "need": "scene-script",
     "explain": "Scene composer — assembles persona-characterized "
                "enactment scripts (LLM-assisted when live).",
     "slots": {"scene": {"required": True, "threshold": 0.5}},
     "accept": _accept_nonempty},
    {"id": "artifact.codec", "need": "artifact-encode",
     "explain": "Artifact encode/decode — scannable PNG grid + payload "
                "codec; literal-fidelity seam.",
     "slots": {"payload": {"required": True, "threshold": 0.5}},
     "accept": _accept_nonempty},
    {"id": "net.discover", "need": "fleet-discovery",
     "explain": "Local network discovery — ARP/sweep/enrichment across "
                "local transports.",
     "slots": {},
     "accept": _accept_nonempty},
    {"id": "peer.install", "need": "fleet-install",
     "explain": "Join/install driver — invite -> join -> verdict on an "
                "installable target.",
     "slots": {"target": {"required": True, "threshold": 0.5}},
     "accept": _accept_nonempty},
    {"id": "steward.idle", "need": "stewardship",
     "explain": "The Idle Turn Steward as an assignable tool "
                "(C-StewardAsTool): queue drain, asset fulfillment, "
                "background presentation.",
     "slots": {},
     "accept": _accept_nonempty},
    {"id": "mail.read", "need": "source-mail",
     "explain": "Mailbox reader — configured IMAP account or labeled "
                "fixture inbox.",
     "slots": {},
     "accept": _accept_nonempty},
]
class Tools:
    def __init__(self, host):
        self.h = host
    def registry(self):
        return TOOLS
    def for_need(self, template):
        return [t for t in TOOLS if t["need"] == template]
    def register_persist(self):
        """Tools are a privileged persistent class — ids live in the
        index, definitions recorded as ledger rows once."""
        if not self.h.indices["tools"]:
            for t in TOOLS:
                self.h.indices["tools"][t["id"]] = {
                    "id": t["id"], "need": t["need"],
                    "explain": t["explain"]}
            self.h.save_indices()
            self.h.journal.append(
                "tool-registry",
                {"tools": [t["id"] for t in TOOLS]},
                claimant="system", basis="system")
    def compose(self, need, tool_ids, claimant="user"):
        """Composition is a recorded ledger object, decomposable back to
        components."""
        comp = {"need": need, "components": tool_ids,
                "composedAt": time.time()}
        row = self.h.journal.append("tool-composition", comp,
                                    claimant=claimant, basis="claim")
        return row
    def execute(self, tool_id, slots, claimant="steward", need_id=None):
        """Execution evidence is recorded; failure remains recorded and
        leaves the need available."""
        t0 = time.time()
        call = self.h.journal.append(
            "tool-call", {"tool": tool_id, "slots": slots,
                          "need": need_id},
            claimant=claimant, basis="execution-evidence")
        try:
            fn = getattr(self, "_run_" + tool_id.replace(".", "_"), None)
            result = fn(slots) if fn else {"status": "failed",
                                           "reason": "no executor"}
        except Exception as e:
            result = {"status": "failed", "reason": f"{type(e).__name__}: {e}"}
        result.setdefault("seconds", round(time.time() - t0, 1))
        self.h.journal.append(
            "tool-result", {"call": call["id"], "tool": tool_id,
                            "result": result},
            claimant="tool:" + tool_id, basis="execution-evidence",
            refs=[call["id"]] + ([need_id] if need_id else []))
        return result
    # ---- executors (minimal set; module objects call these or are
    # ---- themselves the executor surface)
    def _run_stub(self, slots):
        return {"status": "deferred", "reason": "executor bound by module"}
