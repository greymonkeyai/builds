"""Governed predicate registry. Namespaces are a closed set; names within a
namespace are extensible but must be registered here before assertions are
authored with them.
"""

PREDICATES = {
    "product":    {"goal", "implementation", "feedback-policy"},
    "project":    {"exists", "title", "kind", "goal", "status", "focus", "member-need",
                   "progress", "created-via"},
    "user":       {"name", "engagement", "mood", "mood-cleared", "editor-proficiency",
                   "ephemeral-cleared", "tool-request", "persona-frame"},
    "persona":    {"exists", "name", "trait", "confidence", "voice", "voice-remote",
                   "interest", "label-color", "roster-priority", "portrait", "role",
                   "style", "usagecredential", "tool-permission", "imitates",
                   "imitation-mark", "admonished", "lens", "responsibility",
                   "display-mode", "art", "temporal-note", "characterization",
                   "mint-refused"},
    "device":     {"input-capture", "speech-transcript", "voice-render", "ambient-pickup"},
    "feedback":   {"sent"},
    "maxim":      {"worldview-anchor", "objection"},
    "gap":        {"research"},
    "tool":       {"exists", "definition", "telemetry", "rank-adjustment", "success-rate",
                   "refusal", "invocation"},
    "chat":       {"user-message", "assistant-response", "response-depth", "topic",
                   "cleared", "idle-turn-variant", "all-chat"},
    "library":    {"acquisition-draft", "acquisition-sent", "recipient", "suggest"},
    "home":       {"routine-suggest", "actuation-draft", "actuation-done", "device"},
    "creator":    {"milestone-suggest", "publish-draft", "published", "target"},
    "study":      {"plan-suggest", "export-draft", "export-sent", "recipient"},
    "travel":     {"prep-suggest", "itinerary-draft", "itinerary-sent", "recipient"},
    "routing":    {"turn-trace", "trace-step", "trace-invoke", "intent-override",
                   "stewardship-assignment", "decision-trace", "surface", "binding",
                   "respondent-rank"},
    "prompt":     {"prep"},
    "source":     {"trust-class", "confidence", "configured", "provenance", "use",
                   "liveness", "model-available", "access-policy", "adequacy"},
    "need":       {"tool-request", "response", "portrait", "countdown", "book-find",
                   "open", "fulfilled", "cancelled", "superseded", "candidate",
                   "deferred", "refined", "list-item", "generic", "set-members",
                   "characterization", "nonmatch"},
    "search":     {"run", "adequacy", "source-adequacy"},
    "idle":       {"drain-fragment", "steward-run"},
    "image":      {"asset", "candidate", "review", "subject"},
    "sound":      {"soundscape-plan", "soundscape-active", "cue"},
    "ui":         {"panel-request", "shell-theme", "card"},
    "avqr":       {"registration"},
    "exchange":   {"bundle-draft", "bundle-sent", "recipient", "imported", "package"},
    "storefront": {"exists", "definition", "status", "confidence"},
    "codebook":   {"entry", "manifest", "source"},
    "set":        {"member", "closure", "criteria", "member-source"},
    "task":       {"plan", "step"},
    "calendar":   {"event", "imported", "linked"},
    "speech":     {"floor-admission", "floor-played", "voice-set"},
    "comparison": {"run", "row"},
    "connector":  {"configured", "run", "item"},
    "temporal":   {"attention", "context"},
    "archive":    {"segment"},
    "ethics":     {"gate"},
    "grant":      {"issued", "consumed", "revoked"},
    "cleanup":    {"run", "compacted", "consolidated", "rule"},
    "studio":     {"document", "export"},
    "contact":    {"exists", "id", "name", "relationship", "status", "ask"},
    "engine":     {"mode", "probe"},
    "launch":     {"report", "honesty"},
    "decision":   {"weights", "score", "churn", "respondent"},
    "seed":       {"loaded"},
}

# Namespaces whose assertions hold *operational* state subject to governed
# cleanup compaction rules (spent rows may be consolidated).
OPERATIONAL_NS = {"need", "idle", "routing"}

ACTION_THRESHOLD = 0.7      # minimum effective confidence for action/acceptance
IMPORT_CEILING = 0.4        # imported assertions capped below ACTION_THRESHOLD


def known(predicate: str) -> bool:
    if ":" not in predicate:
        return False
    ns, name = predicate.split(":", 1)
    return ns in PREDICATES and name in PREDICATES[ns]


def register(predicate: str) -> None:
    """Runtime registration for user-authored predicates (namespaces stay closed)."""
    ns, name = predicate.split(":", 1)
    if ns not in PREDICATES:
        raise ValueError(f"closed namespace set: '{ns}' is not a governed namespace")
    PREDICATES[ns].add(name)
