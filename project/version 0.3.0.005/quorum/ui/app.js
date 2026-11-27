/* Quorum 0.3.0.005 — surface behavior. Every control drives its own path
   (S-1: live controls only). */
const $ = s => document.querySelector(s);
const api = async (p, body) => {
  const r = await fetch(p, body === undefined ? {} :
    {method: "POST", headers: {"Content-Type": "application/json"},
     body: JSON.stringify(body)});
  return r.json();
};

/* ---- user-directed jingle (V-E): alerts to the USER are a melodic
   register — machine beeps are never used here (POST /api/tones/* keeps
   the registers separate server-side too). */
function userJingle() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    [[523.25, 0], [659.25, 0.14], [783.99, 0.28]].forEach(([f, t]) => {
      const o = ctx.createOscillator(), g = ctx.createGain();
      o.frequency.value = f; o.type = "sine";
      g.gain.setValueAtTime(0.12, ctx.currentTime + t);
      g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + t + 0.25);
      o.connect(g).connect(ctx.destination);
      o.start(ctx.currentTime + t); o.stop(ctx.currentTime + t + 0.3);
    });
  } catch (e) {}
}

/* ============================ tabs ===================================== */
document.querySelectorAll(".tab").forEach(b => b.onclick = () => {
  document.querySelectorAll(".tab").forEach(x => x.classList.remove("on"));
  document.querySelectorAll(".tabpage").forEach(x => x.classList.remove("on"));
  b.classList.add("on");
  $("#tab-" + b.dataset.tab).classList.add("on");
  if (b.dataset.tab === "log") loadLog();
});
$("#fullscreen").onclick = () => {
  document.fullscreenElement ? document.exitFullscreen()
                             : document.documentElement.requestFullscreen();
};

/* ============================ roster =================================== */
async function loadRoster() {
  const d = await api("/api/roster");
  const el = $("#roster"); el.innerHTML = "";
  const qs = $("#quick-select"); qs.innerHTML = "";
  d.roster.forEach(p => {
    const card = document.createElement("div");
    card.className = "persona-card" + (p.active ? " active" : "");
    card.innerHTML =
      (p.portrait ? `<img src="/api/artifact?path=${encodeURIComponent(p.portrait)}">` : "") +
      `<div class="nm">${p.name} ${p.imitation_mark ? '<span class="mark">◆ IMITATION</span>' : ""}</div>` +
      `<div>${p.register} · <span class="conf">held ${p.heldConfidence.toFixed(2)}</span></div>` +
      `<div class="row">` +
      `<button data-a="up">▲</button><button data-a="dn">▼</button>` +
      `<button data-a="sel">select</button>` +
      `<button data-a="edit" title="Edit this personality (V-F)">edit</button>` +
      `<button data-a="art" title="Re-author portrait">art</button>` +
      `</div>`;
    card.querySelector('[data-a="up"]').onclick = async () => {
      const r = await api("/api/roster/move", {id: p.id, dir: -1});
      if (r.ok) showConfidenceShift(p.name, r.before, r.after);
      loadRoster();
    };
    card.querySelector('[data-a="dn"]').onclick = async () => {
      const r = await api("/api/roster/move", {id: p.id, dir: 1});
      if (r.ok) showConfidenceShift(p.name, r.before, r.after);
      loadRoster();
    };
    card.querySelector('[data-a="sel"]').onclick = async () => {
      await api("/api/roster/select", {id: p.id}); loadRoster();
    };
    card.querySelector('[data-a="edit"]').onclick = () => openEditor(p.id);
    card.querySelector('[data-a="art"]').onclick = async () => {
      await api(`/api/personas/${p.id}/portrait`, {}); loadRoster();
    };
    el.appendChild(card);
    const o = document.createElement("option");
    o.value = p.id; o.textContent = p.name;
    qs.appendChild(o);
  });
}
/* V-D: the reorder's consequence is perceivable — held-confidence change
   is announced, not only recorded. */
function showConfidenceShift(name, before, after) {
  const d = document.createElement("div");
  d.className = "needcard";
  d.textContent = `${name}: held-confidence ${before} → ${after}`;
  $("#chatlog").appendChild(d);
  $("#chatlog").scrollTop = 1e9;
}

$("#new-persona").onclick = async () => {
  const name = prompt("Personality name:");
  if (!name) return;
  const reg = prompt("Register (formal/casual/terse/scholarly/playful):",
                     "casual") || "casual";
  const im = prompt("Imitates a recognizable figure? (name or blank)", "") || "";
  const r = await api("/api/personas",
                      {name, register: reg, imitation_of: im});
  if (r.gate && r.gate.requiresMark) alert(r.gate.admonishment);
  userJingle();
  await api(`/api/personas/${r.persona.id}/portrait`, {});
  loadRoster();
};

/* ============================ editor (V-F discoverable) ================= */
async function openEditor(pid) {
  document.querySelector('[data-tab="settings"]').click();
  const ros = (await api("/api/roster")).roster;
  const p = ros.find(x => x.id === pid);
  const voices = (await api("/api/honesty")).tts.voices;
  $("#editor").innerHTML =
    `<div class="editor-form"><h3>Edit ${p.name}</h3>` +
    `<input id="ed-name" value="${p.name}">` +
    `<select id="ed-register">${["formal","casual","terse","scholarly","playful"]
      .map(r => `<option ${r === p.register ? "selected" : ""}>${r}</option>`).join("")}</select>` +
    `<select id="ed-voice"><option value="">(voice)</option>` +
      voices.map(v => `<option ${v === p.voice ? "selected" : ""}>${v}</option>`).join("") +
    `</select>` +
    `<textarea id="ed-traits" placeholder="traits, comma separated"></textarea>` +
    `<textarea id="ed-char" placeholder="characterization"></textarea>` +
    `<button id="ed-save">Save</button></div>`;
  $("#ed-save").onclick = async () => {
    await api(`/api/personas/${pid}/update`, {
      name: $("#ed-name").value, register: $("#ed-register").value,
      voice: $("#ed-voice").value,
      traits: $("#ed-traits").value.split(",").map(s => s.trim()).filter(Boolean),
      characterization: $("#ed-char").value});
    userJingle(); loadRoster();
  };
}

/* ============================ chat ===================================== */
$("#chat-send").onclick = send;
$("#chat-input").addEventListener("keydown", e => {
  if (e.key === "Enter") send();
});
async function send() {
  const t = $("#chat-input").value.trim();
  if (!t) return;
  $("#chat-input").value = "";
  const turn = await api("/api/chat",
                         {text: t, persona: $("#quick-select").value});
  renderTurn(turn);
  loadNeeds(); loadStage();
}
function renderTurn(turn) {
  const el = $("#chatlog");
  const d = document.createElement("div");
  d.className = "turn";
  d.innerHTML = `<div class="user">you: ${turn.input}</div>` +
    (turn.replies || []).map(r =>
      `<div class="reply"><div class="who">${r.name}</div>` +
      `<div>${(r.text || "").replace(/\n/g, "<br>")}</div>` +
      `<div class="fid ${r.fidelity && r.fidelity.verdict === "grounded" ? "ok" : ""}">` +
      `${r.stub ? "declared stub — engine offline" :
         (r.fidelity ? `${r.fidelity.verdict}${r.fidelity.flag ?
           " (" + r.fidelity.flag + ")" : ""}` : "")}</div></div>`).join("") +
    (turn.needs || []).map(n =>
      `<div class="needcard">opened need ${n}</div>`).join("");
  el.appendChild(d);
  el.scrollTop = 1e9;
}
$("#reset-conv").onclick = async () => {
  await api("/api/chat/reset", {});
  $("#chatlog").innerHTML = "";
  $("#topic").textContent = "topic: general";
};

async function loadStage() {
  const d = await api("/api/archive");
  const ros = (await api("/api/roster")).roster;
  const stage = $("#stage");
  const active = ros.filter(p => p.active);
  stage.innerHTML = active.length ?
    active.map(p =>
      `<span class="on-stage">${p.portrait ?
        `<img src="/api/artifact?path=${encodeURIComponent(p.portrait)}">` : ""}
       ${p.name}</span>`).join("") +
    `<span>on stage — ${d.topic || "general"}</span>` :
    "<span>stage empty</span>";
  $("#topic").textContent = "topic: " + (d.topic || "general");
}

/* ============================ needs + chit ============================== */
async function loadNeeds() {
  const d = await api("/api/needs");
  const el = $("#needs"); el.innerHTML = "";
  (d.open || []).forEach(n => {
    const v = n.value.v;
    const div = document.createElement("div");
    div.className = "need";
    div.innerHTML =
      `<div class="kind">${n.predicate}</div>` +
      `<div>${(v.slots && (v.slots.ask || v.slots.tool || v.slots.topic)) || n.subject}</div>` +
      `<div class="expl">${v.explain || ""}</div>` +
      `<div class="row" style="margin-top:4px">` +
      `<button data-a="focus">focus</button><button data-a="cancel">cancel</button></div>`;
    div.querySelector('[data-a="focus"]').onclick = async () => {
      await api(`/api/needs/${n.id}/focus`, {});
      $("#topic").textContent = "focus: " +
        ((v.slots && (v.slots.ask || v.slots.tool || v.slots.topic)) || n.id);
    };
    div.querySelector('[data-a="cancel"]').onclick = async () => {
      await api(`/api/needs/${n.id}/cancel`, {}); loadNeeds();
    };
    el.appendChild(div);
  });
  /* decision-candidates §4: steward liveness chit on the first screen */
  const ch = $("#steward-chit");
  const s = d.steward || {};
  ch.textContent = s.ageS == null ? "steward: no pass yet" :
    `steward ${s.ageS < 60 ? Math.round(s.ageS) + "s" :
      Math.round(s.ageS / 60) + "m"} · ${s.escalation}`;
  ch.className = s.escalation || "";
  ch.title = `expected wake ${s.expectedWakeS}s · passes ${s.passes}`;
}

/* ============================ library =================================== */
async function loadLibrary() {
  const d = await api("/api/holdings");
  $("#lib-personas").innerHTML = (d.personas || []).map(p =>
    `<div class="persona-card"><div class="nm">${p.name}</div>` +
    `<div>${p.register} · held ${p.heldConfidence.toFixed(2)}</div>` +
    `<div class="row"><button onclick="openEditor('${p.id}')">edit</button></div></div>`
  ).join("") || "<i>none</i>";
  $("#lib-tools").innerHTML = (d.tools || []).map(t =>
    `<div class="tool-card"><div class="nm">${t.name}</div>` +
    `<div class="purpose">${t.purpose}</div>` +
    `<div class="explain">${t.explain}</div></div>`).join("");
  $("#lib-candidates").innerHTML = (d.candidates || []).map(c =>
    `<div class="tool-card"><div class="nm">candidate: ${c.subject}</div>` +
    `<div class="explain">${(c.value.v.definition || {}).explain ||
      "imported tool definition"}</div>` +
    `<div class="row"><button onclick="acceptCandidate('${c.id}')">accept (mint live)</button></div></div>`
  ).join("") || "<i>none staged</i>";
  $("#lib-workshops").innerHTML = (d.workshops || []).map(w =>
    `<div class="tool-card"><div class="nm">${w.value.v.title}</div>` +
    `<div class="explain">${w.value.v.threshold}</div></div>`).join("") ||
    "<i>none</i>";
}
window.acceptCandidate = async id => {
  await api(`/api/tools/candidate/${id}/accept`, {});
  userJingle(); loadLibrary(); loadWorkshop();
};

/* ============================ workshop ================================== */
async function loadWorkshop() {
  const d = await api("/api/tools");
  $("#workshop-tools").innerHTML = (d.tools || []).map(t =>
    `<div class="tool-card"><div class="nm">${t.name} <code>${t.id}</code></div>` +
    `<div class="purpose">purpose: ${t.purpose}</div>` +
    `<div class="explain">${t.explain}</div>` +
    `<div class="slots">slots: ${JSON.stringify(t.slots)}` +
    `${t.requiresGrant ? " · <b>requires witnessed grant</b>" : ""}</div>` +
    `<div class="row" style="margin-top:6px"><button onclick="invokeTool('${t.id}')">invoke</button></div></div>`
  ).join("");
}
window.invokeTool = async id => {
  const args = prompt("Args as JSON:", '{"topic":"List of municipalities in Pennsylvania","criteria":"incorporated city"}');
  let a = {}; try { a = JSON.parse(args || "{}"); } catch (e) {}
  const r = await api(`/api/tools/${id}/invoke`, {args: a});
  alert(JSON.stringify(r.result || r, null, 1).slice(0, 1800));
};

/* ============================ fleet ===================================== */
$("#fleet-scan").onclick = async () => {
  $("#fleet-status").textContent = "scanning local transports…";
  const d = await api("/api/fleet/discover", {ping: true});
  $("#fleet-status").textContent =
    `${d.found.length} devices · ${d.durationMs}ms · transports: ${d.transports.join(", ")}`;
  renderDiscovery(d);
};
function renderDiscovery(d) {
  $("#fleet-found").innerHTML = (d.found || []).map(f =>
    `<div class="device"><span class="st ${f.reachable ? "found" : "unavailable"}">` +
    `${f.reachable ? "●" : "○"}</span> ` +
    `${f.name || "(unresolved)"} <span style="color:var(--dim)">${f.ip} ${f.mac} ${f.transport}</span>` +
    `${f.roster ? ` · <b>${f.roster}</b>` : ""}${f.self ? " · this host" : ""}</div>`
  ).join("");
  $("#fleet-roster").innerHTML = (d.roster_status || []).map(r =>
    `<div class="device"><span class="st ${r.status}">${r.status}</span> ` +
    `${r.key} — <span style="color:var(--dim)">${r.expect}</span></div>`
  ).join("");
  $("#fleet-invites").innerHTML =
    (d.roster_status || [])
      .filter(r => r.status.startsWith("found"))
      .map(r => `<label class="device"><input type="checkbox" value="${r.key}"> ` +
        `${r.key} <span style="color:var(--dim)">${r.status}</span></label>`).join("") +
    `<div class="row"><button onclick="invite()">invite selected → join</button>` +
    `<button onclick="map()">map</button></div>`;
}
window.invite = async () => {
  const keys = [...document.querySelectorAll("#fleet-invites input:checked")]
    .map(c => c.value);
  if (!keys.length) return alert("select devices to invite");
  const r = await api("/api/fleet/invite", {keys});
  $("#fleet-members").innerHTML =
    `<div class="device">invited: ${r.invited.map(i => i.key).join(", ")}</div>` +
    `<div class="device">NOT invited (never members): ${r.not_invited.join(", ")}</div>` +
    r.invited.map(i =>
      `<div class="device">${i.key} — ` +
      `<button onclick="join('${i.key}')">join → role + credential surrender</button> ` +
      `<button onclick="install('${i.key}')">install push</button></div>`).join("");
};
window.join = async key => {
  const r = await api("/api/fleet/join", {key});
  alert(JSON.stringify(r, null, 1));
};
window.install = async key => alert(JSON.stringify(
  await api("/api/fleet/install", {key}), null, 1));
window.map = async () => {
  const r = await api("/api/fleet/mapbtn".replace("mapbtn", "map"), {});
  alert("map written: " + (r.path || JSON.stringify(r)));
};
$("#fleet-mapbtn").onclick = async () => {
  const r = await api("/api/fleet/map", {});
  alert("map written: " + (r.path || "none"));
};

/* ============================ exchange ================================== */
$("#art-import").onclick = async () => {
  const r = await api("/api/artifact/import",
                      {path: "seed-packs/exemplar-postcard.bmp"});
  $("#artifact-view").innerHTML =
    `<div class="tool-card"><div class="nm">capture layers</div>` +
    `<div class="explain">literal bytes: ${r.capture.literal}<br>` +
    `semantic: ${JSON.stringify(r.capture.semantic)}<br>` +
    `stylistic palette: ${r.capture.stylistic.palette
      .map(p => `rgb(${p.rgb}) ${Math.round(p.share * 100)}%`).join(", ")}</div>` +
    `<img src="/api/artifact?path=${encodeURIComponent("seed-packs/exemplar-postcard.bmp")}" style="max-width:260px">` +
    `</div>`;
  $("#workshops").innerHTML = r.claims.map(c =>
    `<div class="tool-card"><div class="nm">${c.predicate}</div>` +
    `<div class="explain">${JSON.stringify(c.value.v).slice(0, 300)}</div>` +
    `<div class="row"><button onclick="adopt('${c.subject}')">adopt workshop</button></div></div>`
  ).join("");
  loadLibrary(); loadCandidates();
};
window.adopt = async ws => {
  await api(`/api/artifact/${ws}/adopt`, {}); userJingle();
};
$("#art-repub").onclick = async () => {
  const ws = (await api("/api/holdings")).workshops[0];
  if (!ws) return alert("no workshop imported yet");
  const r = await api(`/api/artifact/${ws.subject}/republish`, {});
  alert(JSON.stringify(r, null, 1));
};
async function loadCandidates() {
  const d = await api("/api/tool-candidates");
  $("#candidates").innerHTML = (d.candidates || []).map(c =>
    `<div class="tool-card"><div class="nm">${c.subject}</div>` +
    `<div class="explain">${(c.value.v.definition || {}).explain || ""}</div>` +
    `<div class="row"><button onclick="api('/api/tools/evaluate-tool-candidate/invoke',{args:{candidate:'${c.id}'}}).then(r=>alert(JSON.stringify(r.result,null,1).slice(0,1500)))">evaluate</button>` +
    `<button onclick="acceptCandidate('${c.id}')">accept</button>` +
    `<button onclick="api('/api/tools/${c.subject}/discredit',{note:'rejected'})">discredit</button></div></div>`
  ).join("") || "<i>none</i>";
}
$("#pkg-export").onclick = async () => {
  const r = await api("/api/exchange/export", {});
  alert("exported: " + r.path);
};
$("#pkg-import").onclick = async () => {
  const p = prompt("package path:", "runtime/artifacts/exchange-package.json");
  const r = await api("/api/exchange/import", {path: p});
  alert(JSON.stringify(r, null, 1)); loadLibrary(); loadCandidates();
};

/* ============================ mail ====================================== */
async function loadMail() {
  const d = await api("/api/mail");
  $("#mail-basis").innerHTML =
    `<b>source basis: ${d.basis || "unknown"}</b> — ` +
    `${d.note || ""} · configured account: ${d.configured_account}`;
  $("#inbox").innerHTML = (d.messages || []).map((m, i) =>
    `<div class="device mail-item" onclick="commentary(${i})">` +
    `<div class="subj">${m.subject || m.file}</div>` +
    `<div class="from">${m.from} · ${m.date}</div></div>`).join("");
  window._mail = d.messages || [];
}
window.commentary = async i => {
  const m = window._mail[i];
  await api("/api/chat/context",
            {kind: "email", subject: m.subject, body: m.body});
  const turn = await api("/api/chat",
                         {text: `What do you make of this email — "${m.subject}"?`});
  $("#mail-commentary").innerHTML = turn.replies.map(r =>
    `<div class="reply"><div class="who">${r.name}</div><div>${r.text}</div></div>`
  ).join("");
};

/* ============================ settings ================================== */
document.querySelectorAll("#themes button").forEach(b => b.onclick = async () => {
  document.documentElement.dataset.theme = b.dataset.theme;
  await api("/api/settings", {slot: "theme", value: b.dataset.theme});
});
async function loadSettings() {
  $("#preloads").innerHTML = ["daybreak", "lamplit", "nightwatch"].map(n =>
    `<button onclick="preload('${n}')">${n}</button>`).join(" ");
  const h = await api("/api/honesty");
  $("#cred-role").textContent = `(surface role: ${h.fleet.surface_role})`;
  $("#credentials").innerHTML = h.fleet.surface_role === "host" ?
    `<div class="device">Google/Gmail OAuth — <b>not configured</b> (declared)</div>` +
    `<div class="device">iCloud/IMAP preset — <b>not configured</b> (declared)</div>` +
    `<div class="device">usage credentials — host-local keyring model; ` +
    `secrets never ledgered (§5)</div>` :
    `<div class="device"><b>credential management surrendered to host</b> — ` +
    `status only; secrets stay host-local (§5)</div>`;
}
window.preload = async n => {
  const r = await api("/api/preload", {name: n});
  if (r.ok) {
    document.documentElement.dataset.theme = r.settings.theme || "light";
    userJingle();
  }
};

/* ============================ log / honesty / absences ================== */
async function loadLog() {
  const d = await api("/api/log?n=60");
  $("#log").textContent = (d.tail || []).map(r =>
    `${r.predicate} ${r.subject} ← ${r.claimant} @${r.certainty}`).join("\n");
}
async function loadHonesty() {
  const h = await api("/api/honesty");
  /* V-B: absences are LABELED deferred/not-built — never confusable with
     the feature list. */
  const absent = [];
  if (!h.accounts.email || h.accounts.email.startsWith("absent"))
    absent.push("live mail account connector (fixture .eml basis labeled)");
  absent.push("OAuth account connectors");
  absent.push("server-side STT (browser surface only)");
  absent.push("native desktop shell (browser surface)");
  absent.push("standard QR symbology (qmatrix build-specific layer)");
  absent.push("cross-device fleet joins this session (machinery live; "
              + "no second host joined)");
  $("#absences").innerHTML =
    `<b>not built / deferred — declared absences:</b> ${absent.join(" · ")}`;
  $("#statusbar").innerHTML =
    `<span class="${h.llm.mode.startsWith("live") ? "ok" : "bad"}">llm ${h.llm.mode}</span>` +
    `<span>tts ${h.tts.mode} (${h.tts.voices.length} voices)</span>` +
    `<span>art ${h.art.mode}</span>` +
    `<span>sources: ${Object.entries(h.sources).map(([k, v]) =>
      `${k}=${v}`).join(" · ")}</span>` +
    `<span>role ${h.fleet.surface_role}</span>`;
}

/* ============================ boot ====================================== */
(async function init() {
  loadHonesty(); loadRoster(); loadNeeds(); loadStage();
  loadLibrary(); loadWorkshop(); loadMail(); loadSettings(); loadCandidates();
  setInterval(loadNeeds, 4000);
  setInterval(loadHonesty, 15000);
})();
