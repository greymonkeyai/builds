"""suite: pathed scenarios — user-journey steps as module.affordance.
Each step names an interface item; the check verifies the affordance is
reachable on the owner-facing surface (rendered or live API) — the
consolidated scenarios carry the enactment detail.
"""
import json
import os
from .checklib import ck, dead
# module.affordance → evidence probe: rendered affordance name and/or
# live API endpoint the affordance calls
STEPS = {
    "shell.launch":      {"aff": "chat", "api": "/api/health"},
    "shell.gate":        {"aff": "status-bar", "api": "/api/gate"},
    "shell.consent":     {"aff": "fleet", "api": "/api/fleet"},
    "shell.status":      {"aff": "status-bar", "api": "/api/state"},
    "shell.library":     {"aff": "library", "api": "/api/library"},
    "shell.close":       {"aff": "chat", "api": "/api/health"},
    "projects.list":     {"aff": "lists", "api": "/api/lists"},
    "personas.roster":   {"aff": "persona-roster", "api": "/api/personas"},
    "personas.create":   {"aff": "persona-create", "api": "/api/personas"},
    "personas.editor":   {"aff": "persona-editor", "api": "/api/personas"},
    "personas.portrait": {"aff": "persona-roster", "api": "/api/personas"},
    "personas.reorder":  {"aff": "roster-up", "api": "/api/personas"},
    "personas.source-match": {"aff": "persona-create", "api": "/api/personas"},
    "personas.voices":   {"aff": "voice-select", "api": "/api/personas"},
    "personas.selector": {"aff": "persona-roster", "api": "/api/personas"},
    "conversation.chat": {"aff": "chat", "api": "/api/conversation"},
    "conversation.speech": {"aff": "chat", "api": "/api/metrics"},
    "conversation.depth": {"aff": "response-depth", "api": "/api/settings"},
    "conversation.context": {"aff": "context-display", "api": "/api/conversation"},
    "conversation.reset": {"aff": "chat-reset", "api": "/api/conversation"},
    "ledger.input":      {"aff": "chat", "api": "/api/ledger"},
    "ledger.recovery":   {"aff": "chat", "api": "/api/ledger"},
    "ledger.candidates": {"aff": "needs-floor", "api": "/api/ledger"},
    "needs.floor":       {"aff": "needs-floor", "api": "/api/needs"},
    "needs.template":    {"aff": "needs-floor", "api": "/api/needs"},
    "needs.focus":       {"aff": "needs-floor", "api": "/api/needs"},
    "needs.candidates":  {"aff": "needs-floor", "api": "/api/needs"},
    "needs.execute":     {"aff": "needs-floor", "api": "/api/needs"},
    "tools.composition": {"aff": "tools", "api": "/api/tools"},
    "tools.registry":    {"aff": "tools", "api": "/api/tools"},
    "sources.seed":      {"aff": "sources", "api": "/api/sources"},
    "sources.gate":      {"aff": "sources", "api": "/api/sources/admissions"},
    "fleet.discovery":   {"aff": "fleet", "api": "/api/fleet/discovery"},
    "fleet.identify":    {"aff": "fleet", "api": "/api/fleet"},
    "fleet.invite":      {"aff": "fleet", "api": "/api/fleet"},
    "fleet.install":     {"aff": "fleet", "api": "/api/fleet"},
    "fleet.roster":      {"aff": "fleet", "api": "/api/fleet"},
    "fleet.map":         {"aff": "map", "api": "/api/fleet/map"},
    "fleet.exchange":    {"aff": "fleet", "api": "/api/fleet"},
    "fleet.negotiate":   {"aff": "fleet", "api": "/api/fleet"},
    "fleet.transports":  {"aff": "fleet", "api": "/api/fleet"},
    "fleet.surrender":   {"aff": "settings", "api": "/api/accounts"},
    "fleet.seed":        {"aff": "fleet", "api": "/api/fleet"},
    "fleet.courier":     {"aff": "fleet", "api": "/api/fleet"},
    "exchange.style":    {"aff": "style-picker", "api": "/api/settings"},
    "exchange.publish":  {"aff": "workshops", "api": "/api/workshops"},
    "exchange.import":   {"aff": "workshops", "api": "/api/workshops"},
    "exchange.republish": {"aff": "workshops", "api": "/api/workshops"},
    "exchange.transmission": {"aff": "tools", "api": "/api/tools"},
    "exchange.cache":    {"aff": "preloads", "api": "/api/preloads"},
    "exchange.scancode": {"aff": "workshops", "api": "/api/workshops"},
    "stage.commentary":  {"aff": "stage", "api": "/api/stage"},
    "stage.background":  {"aff": "stage", "api": "/api/stage"},
    "stage.ack":         {"aff": "stage", "api": "/api/metrics"},
    "stage.present":     {"aff": "stage", "api": "/api/stage"},
    "stage.queue":       {"aff": "stage", "api": "/api/stage"},
    "stage.scene":       {"aff": "stage", "api": "/api/stage"},
    "stage.channels":    {"aff": "stage", "api": "/api/stage"},
}
PATHS = {
    "P-first-run": ["shell.launch", "shell.gate", "projects.list",
                    "personas.roster", "conversation.chat",
                    "conversation.speech", "conversation.depth",
                    "ledger.input", "needs.floor"],
    "P-personality-forge": ["personas.create", "personas.editor",
                            "personas.portrait", "personas.reorder",
                            "personas.source-match", "personas.voices",
                            "personas.selector", "conversation.chat"],
    "P-fleet-adopt": ["fleet.discovery", "fleet.identify",
                      "fleet.invite", "fleet.install", "fleet.roster",
                      "fleet.map"],
    "P-fleet-media": ["exchange.style", "exchange.publish",
                      "fleet.exchange", "fleet.negotiate",
                      "fleet.transports", "fleet.surrender"],
    "P-usb-seed": ["fleet.seed", "shell.consent", "fleet.install",
                   "fleet.courier", "fleet.roster"],
    "P-source-to-voice": ["sources.seed", "sources.gate",
                          "personas.source-match", "conversation.chat",
                          "stage.commentary"],
    "P-artifact-exchange": ["exchange.import", "exchange.style",
                            "exchange.republish", "exchange.transmission",
                            "exchange.cache", "exchange.scancode"],
    "P-session-resume": ["shell.launch", "ledger.recovery",
                         "ledger.candidates", "shell.status",
                         "conversation.context", "conversation.reset",
                         "shell.library", "shell.close"],
    "P-background-service": ["needs.template", "needs.focus",
                             "tools.composition", "tools.registry",
                             "stage.background", "stage.ack",
                             "stage.present"],
    "P-stage-scene": ["stage.queue", "stage.scene", "stage.channels"],
    "P-need-queue": ["needs.floor", "needs.template",
                     "needs.candidates", "needs.execute",
                     "needs.floor"],
}
def _path(ctx, name, steps):
    if not ctx.probe.alive():
        return dead(ctx, [f"{name} step: {s}" for s in steps])
    out = []
    for step in steps:
        spec = STEPS.get(step, {})
        aff, api = spec.get("aff"), spec.get("api")
        rendered = ctx.probe.page()[1] if aff else ""
        aff_ok = bool(aff) and (
            f'id="{aff}"' in rendered or
            f'data-affordance="{aff}"' in rendered or
            f'data-tab="{aff}"' in rendered or
            f'data-action="{aff}"' in rendered)
        code, _ = ctx.probe.get(api) if api else (None, None)
        api_ok = code == 200
        out.append(ck(f"{name} step: {step}",
                      aff_ok or api_ok,
                      f"affordance={aff} rendered={aff_ok} "
                      f"api={api} code={code}",
                      src=("rendered", "user-path")))
    return out
def P_first_run(ctx):
    return _path(ctx, "P-first-run", PATHS["P-first-run"])
def P_personality_forge(ctx):
    return _path(ctx, "P-personality-forge", PATHS["P-personality-forge"])
def P_fleet_adopt(ctx):
    return _path(ctx, "P-fleet-adopt", PATHS["P-fleet-adopt"])
def P_fleet_media(ctx):
    return _path(ctx, "P-fleet-media", PATHS["P-fleet-media"])
def P_usb_seed(ctx):
    return _path(ctx, "P-usb-seed", PATHS["P-usb-seed"])
def P_source_to_voice(ctx):
    return _path(ctx, "P-source-to-voice", PATHS["P-source-to-voice"])
def P_artifact_exchange(ctx):
    return _path(ctx, "P-artifact-exchange", PATHS["P-artifact-exchange"])
def P_session_resume(ctx):
    return _path(ctx, "P-session-resume", PATHS["P-session-resume"])
def P_background_service(ctx):
    return _path(ctx, "P-background-service",
                 PATHS["P-background-service"])
def P_stage_scene(ctx):
    return _path(ctx, "P-stage-scene", PATHS["P-stage-scene"])
def P_need_queue(ctx):
    return _path(ctx, "P-need-queue", PATHS["P-need-queue"])
