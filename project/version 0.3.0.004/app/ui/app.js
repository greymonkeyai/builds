/* Vantage UI — every control works through the control itself (G-A). */
"use strict";
const $ = id => document.getElementById(id);
let STATE = null;
let holdTab = "personas";
async function api(path, body) {
  if (body === undefined) {
    const r = await fetch(path);
    return r.json();
  }
  const r = await fetch(path, {method:"POST",
    headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)});
  return r.json();
}
function esc(s){ return String(s??"").replace(/[&<>"]/g,
  c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }
function artUrl(p){ return p.art && p.art.file ?
  "/api/artifact?path="+encodeURIComponent(p.art.file) : null; }
// ---- theme control: drive the selector, observe the restyle ----------
async function applyTheme(t, persist=true) {
  document.documentElement.setAttribute("data-theme", t);
  if (persist) {
    // the same path the tool gate uses — a real config assertion, not a
    // visual-only tweak
    await api("/api/invoke", {toolId:"set-theme", slots:{theme:t},
      summary:"theme selector"});
  }
}
// ---- tabs -------------------------------------------------------------
document.querySelectorAll("#tabs button").forEach(b => {
  b.onclick = () => {
    document.querySelectorAll("#tabs button").forEach(x=>x.classList.remove("on"));
    b.classList.add("on");
    document.querySelectorAll("main > section").forEach(s=>s.classList.add("hidden"));
    $("tab-"+b.dataset.tab).classList.remove("hidden");
    if (b.dataset.tab==="library") loadHoldings();
    if (b.dataset.tab==="settings") renderSettings();
    if (b.dataset.tab==="workshops") renderTools();
    if (b.dataset.tab==="command") renderCommand();
    if (b.dataset.tab==="inbox") renderInbox();
  };
});
// ---- roster (operable: select + reorder, all personas reachable) ------
function renderRoster() {
  const r = $("roster");
  r.innerHTML = "";
  (STATE.roster||[]).forEach((p, i) => {
    const d = document.createElement("div");
    d.className = "pcard" + (p.id===STATE.active ? " active":"");
    const img = artUrl(p);
    d.innerHTML =
      (img?`<img src="${img}">`:`<img src="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'><rect width='40' height='40' fill='${encodeURIComponent(p.color)}'/></svg>">`)+
      `<div style="flex:1"><div class="nm">${esc(p.name)}${p.mark?' <span class="mark">◆</span>':''}</div>`+
      `<div class="reg">${esc(p.register)} · conf ${p.heldConfidence}</div></div>`+
      `<div class="mv"><button data-mv="-1" title="up">▲</button><button data-mv="1" title="down">▼</button></div>`;
    d.onclick = async e => {
      const mv = e.target.dataset.mv;
      if (mv !== undefined) {
        await api("/api/roster/move", {personaId:p.id, direction:+mv});
      } else {
        await api("/api/roster/select", {personaId:p.id});
      }
      refresh();
    };
    d.ondblclick = () => openEditor(p.id);
    r.appendChild(d);
  });
}
// ---- stage strip (C-PresenceStage: current-discussion participants) ---
function renderStage() {
  const s = $("stage");
  const recent = (STATE.chat||[]).slice(-6).map(c=>c.persona||c.name);
  const parts = [...new Set(recent)];
  s.innerHTML = parts.length
    ? "<span class='small'>stage:</span> " + parts.map(nm=>{
        const p = (STATE.roster||[]).find(x=>x.name===nm)||{};
        const img = artUrl(p);
        return `<span class="stage-chip">${img?`<img src="${img}">`:""}${esc(nm)}</span>`;
      }).join("")
    : "<span class='small'>stage: —</span>";
}
// ---- chat feed --------------------------------------------------------
function renderFeed() {
  const f = $("feed");
  f.innerHTML = "";
  (STATE.chat||[]).forEach(c => {
    const d = document.createElement("div");
    d.className = "msg";
    const p = (STATE.roster||[]).find(x=>x.id===c.persona) || {};
    const img = artUrl(p);
    d.innerHTML = `<div class="who">${img?`<img class="art" src="${img}">`:""}${esc(c.name)}`+
      ` <span class="small">${esc(c.register||"")}${c.reaction?" · reaction":""}`+
      `${c.contextCommentary?" · on your selection":""}</span></div>`+
      `<div class="txt">${esc(c.text)}</div>`;
    f.appendChild(d);
  });
  f.scrollTop = f.scrollHeight;
}
// ---- composer ----------------------------------------------------------
async function send() {
  const text = $("msg").value.trim();
  if (!text) return;
  $("msg").value = "";
  const feed = $("feed");
  const u = document.createElement("div");
  u.className = "msg user";
  u.innerHTML = `<div class="who">you</div><div class="txt">${esc(text)}</div>`;
  feed.appendChild(u); feed.scrollTop = feed.scrollHeight;
  await api("/api/chat", {text, address:$("address").value||null});
  refresh();
}
// ---- badges -------------------------------------------------------------
function renderBadges() {
  $("topicbadge").classList.toggle("hidden", !STATE.topic);
  if (STATE.topic) $("topicbadge").textContent = "topic: "+STATE.topic;
  $("ctxbadge").classList.toggle("hidden", !STATE.context);
  if (STATE.context) $("ctxbadge").textContent = "ctx: "+STATE.context.label;
  $("focusbadge").classList.toggle("hidden", !STATE.focusNeed);
  if (STATE.focusNeed) $("focusbadge").textContent = "focus: "+STATE.focusNeed;
}
// ---- inbox ---------------------------------------------------------------
async function renderInbox() {
  const list = $("inboxList");
  list.innerHTML = "";
  (STATE.inbox||[]).forEach((m, i) => {
    const d = document.createElement("div");
    d.className = "mailrow";
    d.innerHTML = `<b>${esc(m.subject)}</b><div class="meta">${esc(m.from)} · ${esc(m.date||"")}</div>`;
    d.onclick = async () => {
      $("selctx").textContent = m.subject+" — "+(m.body||"").slice(0,300);
      const r = await api("/api/context/select",
        {kind:"email", ref:m.file||m.subject, label:m.subject,
         excerpt:(m.body||"")});
      if (r.result && r.result.commentary) {
        $("ctxCommentary").innerHTML =
          `<div class="msg"><div class="who">${esc(r.result.commentary.persona)} `+
          `<span class="small">${esc(r.result.commentary.register)}</span></div>`+
          `<div class="txt">${esc(r.result.commentary.text)}</div></div>`;
      }
      refresh();
    };
    list.appendChild(d);
  });
  if (!list.children.length)
    list.innerHTML = "<div class='small'>no mail — drop .eml files into fixtures/inbox and re-scan</div>";
}
// ---- command ---------------------------------------------------------------
async function renderCommand() {
  const np = $("needs"); np.innerHTML = "";
  (STATE.needs||[]).forEach(n => {
    const d = document.createElement("div");
    d.className = "needrow";
    d.innerHTML = `<b>${esc(n.summary||n.toolId)}</b>
      <div class="meta">${n.toolId} · ${n.status}${n.missing&&n.missing.length?
        " · missing: "+n.missing.join(", "):""}</div>
      <button data-f="focus">focus</button>
      <button data-f="retry">retry</button>
      <button data-f="cancel">cancel</button>`;
    d.querySelectorAll("button").forEach(b=>{
      b.onclick = async () => {
        if (b.dataset.f==="focus") await api(`/api/needs/${n.id}/focus`,{});
        if (b.dataset.f==="retry") await api(`/api/needs/${n.id}/retry`,{});
        if (b.dataset.f==="cancel") await api(`/api/needs/${n.id}/cancel`,{});
        refresh();
      };
    });
    np.appendChild(d);
  });
  if (!np.children.length) np.innerHTML = "<div class='small'>queue empty</div>";
  const pj = $("projects"); pj.innerHTML = "";
  (STATE.projects||[]).forEach(p => {
    const d = document.createElement("div");
    d.className = "projrow";
    d.innerHTML = `<b>${esc(p.title)}</b><div class="meta">${esc(p.status||"")} · ${(p.goals||[]).join("; ")}</div>`;
    pj.appendChild(d);
  });
  if (!pj.children.length) pj.innerHTML = "<div class='small'>no projects</div>";
  const cal = await api("/api/calendar");
  const cc = $("cal");
  cc.innerHTML = ["current","upcoming"].map(b =>
    `<div class="small"><b>${b}:</b> ` +
    (cal[b]||[]).map(e=>esc(e.summary)).join("; ") + "</div>").join("");
  // grant requests: deferred needs awaiting authority
  const gr = $("grantReqs"); gr.innerHTML = "";
  (STATE.needs||[]).filter(n=>n.status==="deferred").forEach(n=>{
    const d = document.createElement("div");
    d.className = "grant";
    d.innerHTML = `<b>${esc(n.summary)}</b> awaits a witnessed grant `+
      `<button data-scope="publish.creator">grant publish.creator</button> `+
      `<button data-scope="mail.send">grant mail.send</button>`;
    d.querySelectorAll("button").forEach(b=>{
      b.onclick = async ()=>{
        await api("/api/grants",{scope:b.dataset.scope});
        await api(`/api/needs/${n.id}/retry`,{});
        refresh();
      };
    });
    gr.appendChild(d);
  });
  if (!gr.children.length) gr.innerHTML="<div class='small'>none pending</div>";
}
// ---- library (holdings — G-D) ----------------------------------------------
async function loadHoldings() {
  const h = await api("/api/holdings");
  const nav = document.querySelectorAll("#libnav button");
  nav.forEach(b=>{ b.onclick = ()=>{
    nav.forEach(x=>x.classList.remove("on")); b.classList.add("on");
    holdTab = b.dataset.hold;
    $("ledgerpane").classList.toggle("hidden", holdTab!=="ledger");
    renderHoldings(h);
  };});
  renderHoldings(h);
}
function renderHoldings(h) {
  const list = $("liblist"), det = $("libdetail");
  list.innerHTML = ""; det.textContent = "select a holding to inspect it";
  const add = (html, detail) => {
    const d = document.createElement("div");
    d.className = "hrow"; d.innerHTML = html;
    d.onclick = () => {
      det.innerHTML = "";
      const pre = document.createElement("div");
      pre.innerHTML = detail;
      det.appendChild(pre);
    };
    list.appendChild(d);
  };
  if (holdTab==="personas") h.personas.forEach(p=>{
    const img = artUrl(p);
    add(`${img?`<img src="${img}">`:""}<b>${esc(p.name)}</b>
      <div class="meta">${esc(p.register)} · held-conf ${p.heldConfidence}${p.mark?" · ◆ IMITATION":""}</div>`,
      `<b>${esc(p.name)}</b>${img?`<img src="${img}">`:""}
      register: ${esc(p.register)}\ntraits: ${(p.traits||[]).join(", ")}
      interests: ${(p.interests||[]).join(", ")}\nvoice: ${JSON.stringify(p.voice)}
      held-confidence: ${p.heldConfidence}\ncharacterization:
      ${esc(p.characterization||"(none yet)")}`);
  });
  if (holdTab==="tools") h.tools.forEach(t=>{
    add(`<b>${esc(t.title)}</b><div class="meta">${t.id} · need:${t.need||"—"}${t.authored?" · authored":""}</div>`,
      `<b>${esc(t.id)}</b>\n${esc(t.title)}\nneed: ${t.need||"—"}\nslots: `+
      (t.slots||[]).map(s=>s.name+(s.required?"*":"")).join(", "));
  });
  if (holdTab==="packages") h.packages.forEach(p=>{
    add(`<b>${esc(p.id||"pkg")}</b><div class="meta">${esc(p.schema||"export")} · ${JSON.stringify(p.counts||{})}</div>`,
      JSON.stringify(p,null,2));
  });
  if (holdTab==="artifacts") h.artifacts.forEach(a=>{
    add(`<b>${esc(a.name)}</b><div class="meta">${a.kind} · ${a.bytes}b</div>`,
      a.name.endsWith(".svg")?`<img src="/api/artifact?path=${encodeURIComponent(a.path)}">`+esc(a.path):esc(a.path));
  });
  if (holdTab==="needs") h.openNeeds.forEach(n=>{
    add(`<b>${esc(n.summary)}</b><div class="meta">${n.toolId} · ${n.status}</div>`,
      JSON.stringify(n,null,2));
  });
  if (holdTab==="ledger") {
    det.textContent = `rows: ${h.ledger.rows}\n\nnamespaces:\n`+
      Object.entries(h.ledger.predicates).map(([k,v])=>`  ${k}: ${v}`).join("\n");
    loadLedgerRows();
  }
}
async function loadLedgerRows() {
  const ns = $("libns");
  const preds = await api("/api/predicates");
  ns.innerHTML = "<option value=''>(all predicates)</option>" +
    preds.predicates.map(p=>`<option>${p}</option>`).join("");
  $("libSearch").onclick = async ()=>{
    const r = await api("/api/library?limit=60"+
      (ns.value?"&predicate="+ns.value:"")+
      ($("libq").value?"&text="+encodeURIComponent($("libq").value):""));
    $("librows").innerHTML = r.rows.map(a=>
      `<div class="lrow"><b>${a.predicate}</b> ${esc(a.subject)} `+
      `<span class="small">${a.claimant} · c=${a.certainty}</span><br>`+
      `<span class="small">${esc(JSON.stringify(a.value&&a.value.v)).slice(0,140)}</span></div>`).join("");
  };
  $("libSearch").onclick();
  $("edGo").onclick = async ()=>{
    const r = await api("/api/library/assert",
      {subject:$("edSubj").value, predicate:$("edPred").value,
       value:$("edVal").value, certainty:+$("edCert").value,
       supersedes:$("edSup").value||null});
    $("edMsg").textContent = JSON.stringify(r);
    $("libSearch").onclick();
  };
}
// ---- workshops ---------------------------------------------------------------
async function renderTools() {
  const t = await api("/api/tools");
  const list = $("toollist"); list.innerHTML = "";
  t.tools.forEach(tool=>{
    const d = document.createElement("div");
    d.className = "toolrow";
    d.innerHTML = `<b>${esc(tool.title)}</b><div class="meta">${tool.id} · need:${tool.need||"—"}</div>`;
    d.onclick = ()=>openWorkshop(tool);
    list.appendChild(d);
  });
}
function openWorkshop(tool) {
  const w = $("workshop");
  w.innerHTML = `<h4>${esc(tool.title)}</h4>`;
  const slots = (tool.template&&tool.template.slots)||[];
  slots.forEach(s=>{
    const row = document.createElement("div");
    row.className = "slot";
    row.innerHTML = `<label>${s.name}${s.required?"*":""}</label>
      <input data-slot="${s.name}" placeholder="${s.required?"required":"optional"}">`;
    w.appendChild(row);
  });
  const btn = document.createElement("button");
  btn.textContent = "invoke";
  btn.onclick = async ()=>{
    const slotsIn = {};
    w.querySelectorAll("input[data-slot]").forEach(i=>{
      if (i.value) { try{slotsIn[i.dataset.slot]=JSON.parse(i.value);}
        catch{slotsIn[i.dataset.slot]=i.value;} }
    });
    const r = await api("/api/invoke",{toolId:tool.id,slots:slotsIn,
      summary:"workshop invoke"});
    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(r,null,2);
    w.appendChild(pre);
    refresh();
  };
  w.appendChild(btn);
}
// ---- settings --------------------------------------------------------------
async function renderSettings() {
  const s = $("settings");
  s.innerHTML = `<h3>Preloads (named assertion bundles)</h3>`;
  (STATE.preloads||[]).forEach(name=>{
    const b = document.createElement("button");
    b.textContent = "apply "+name; b.style.marginRight="6px";
    b.onclick = async ()=>{
      await api("/api/invoke",{toolId:"apply-preload",slots:{name},
        summary:"settings preload"});
      refresh();
    };
    s.appendChild(b);
  });
  const st = document.createElement("div");
  st.innerHTML = `<h3>Runtime</h3>
    <div class="slot"><label>response depth</label>
      <input id="setDepth" type="number" min="1" max="4" value="${STATE.responseDepth||2}">
      <button id="depthGo">set</button></div>
    <div class="slot"><label>persona frame</label>
      <select id="setFrame"><option>respondent</option><option>personified</option></select>
      <button id="frameGo">set</button></div>
    <h3>Steward duties</h3><div id="duties"></div>
    <h3>Declarations</h3>
    <div class="small">${(STATE.engines.declaredAbsences||[]).map(esc).join(" · ")}</div>`;
  s.appendChild(st);
  $("setFrame").value = STATE.frame||"respondent";
  $("depthGo").onclick = async ()=>{
    await api("/api/invoke",{toolId:"set-response-depth",
      slots:{depth:+$("setDepth").value},summary:"settings"});
    refresh();};
  $("frameGo").onclick = async ()=>{
    await api("/api/config",{predicate:"user:persona-frame",
      value:$("setFrame").value}); refresh();};
  ["drain-needs","temporal-attention","inbox-scan",
   "confidence-review","compact-check"].forEach(d=>{
    const row = document.createElement("div");
    row.className = "slot";
    row.innerHTML = `<label>${d}</label>
      <button data-on="1">on</button><button data-on="0">off</button>`;
    row.querySelectorAll("button").forEach(b=>{
      b.onclick = async ()=>{
        await api("/api/invoke",{toolId:"assign-stewardship",
          slots:{duty:d,on:b.dataset.on==="1"},summary:"settings"});
      };});
    $("duties").appendChild(row);
  });
}
// ---- editor -------------------------------------------------------------------
function openEditor(pid) {
  const p = (STATE.roster||[]).find(x=>x.id===pid);
  if (!p) return;
  $("editor").classList.remove("hidden");
  $("edTitle").textContent = "personality editor — "+p.name;
  const img = artUrl(p);
  $("edPortrait").innerHTML = img?`<img src="${img}">`:"(no portrait yet)";
  $("peName").value = p.name;
  $("peTraits").value = (p.traits||[]).join(", ");
  $("peInterests").value = (p.interests||[]).join(", ");
  $("peRegister").value = p.register||"measured";
  $("peResp").value = ""; // filled below if present
  $("peVoice").value = (p.voice&&p.voice.name)||"";
  $("peRate").value = (p.voice&&p.voice.rate)||0;
  $("peColor").value = p.color||"#457b9d";
  $("peConf").value = p.heldConfidence;
  $("peMode").value = p.frame||"respondent";
  $("peSave").onclick = async ()=>{
    const patch = {name:$("peName").value,
      traits:$("peTraits").value.split(",").map(x=>x.trim()).filter(Boolean),
      interests:$("peInterests").value.split(",").map(x=>x.trim()).filter(Boolean),
      register:$("peRegister").value,
      voice:{name:$("peVoice").value||null,rate:+$("peRate").value},
      color:$("peColor").value, frame:$("peMode").value};
    const r = await api(`/api/personas/${pid}/update`,{patch});
    $("peMsg").textContent = JSON.stringify(r.result||r,null,2).slice(0,600);
    refresh();
  };
  $("peReart").onclick = async ()=>{
    const r = await api("/api/invoke",{toolId:"generate-portrait",
      slots:{personaId:pid},summary:"editor reart"});
    $("peMsg").textContent = JSON.stringify(r.result||r);
    refresh();
  };
  $("peSpeak").onclick = async ()=>{
    await api("/api/invoke",{toolId:"speak-voice",
      slots:{text:"This is "+p.name+" speaking.",persona:p.name},
      summary:"editor speak"});
  };
  $("peClose").onclick = ()=>$("editor").classList.add("hidden");
}
// ---- exchange ------------------------------------------------------------------
$("expBtn").onclick = async ()=>{
  const r = await api("/api/exchange/export",{});
  $("expMsg").textContent = JSON.stringify(r.result||r);
};
$("impBtn").onclick = async ()=>{
  let pkg;
  try { pkg = JSON.parse($("impPkg").value); }
  catch(e){ $("impMsg").textContent = "bad JSON: "+e; return; }
  const r = await api("/api/exchange/import",{package:pkg});
  $("impMsg").textContent = JSON.stringify(r.result||r,null,2);
};
// ---- log ------------------------------------------------------------------------
$("loggo").onclick = async ()=>{
  const r = await api("/api/log?kind="+$("logkind").value);
  $("log").textContent = r.rows.map(a=>
    `${a.predicate} [${a.claimant}] ${JSON.stringify(a.value).slice(0,220)}`)
    .join("\n");
};
// ---- misc controls -----------------------------------------------------------------
$("send").onclick = send;
$("msg").addEventListener("keydown", e=>{ if(e.key==="Enter") send(); });
$("resetBtn").onclick = async ()=>{ await api("/api/chat/reset",{}); refresh(); };
$("newProj").onclick = async ()=>{
  const title = prompt("project title:"); if(!title) return;
  const goals = prompt("goals (comma separated):","")||"";
  await api("/api/invoke",{toolId:"create-project",
    slots:{title, goals:goals.split(",").map(x=>x.trim()).filter(Boolean)},
    summary:"ui create-project"});
  refresh();
};
$("mintBtn").onclick = async ()=>{
  const name = prompt("personality name:"); if(!name) return;
  const figure = prompt("modeled on a recognizable figure? (blank = original):","")||null;
  const r = await api("/api/personas",{name, figure});
  const res = r.result||r;
  if (res.admonishment) alert("Admonishment: "+res.admonishment);
  if (res.personaId)
    await api("/api/invoke",{toolId:"persona-onboard",
      slots:{personaId:res.personaId},summary:"ui onboard"});
  refresh();
};
$("allChatBtn").onclick = async ()=>{
  await api("/api/config",{predicate:"chat:all-chat",value:true});
  $("chatheadText").textContent = "Conversation (all respondents)";
};
$("inboxRefresh").onclick = async ()=>{
  await api("/api/invoke",{toolId:"steward-tick",slots:{},summary:"inbox rescan"});
  refresh();
};
$("fsBtn").onclick = ()=>{
  if (document.fullscreenElement) document.exitFullscreen();
  else document.documentElement.requestFullscreen();
};
$("themeSel").onchange = e => applyTheme(e.target.value);
let rec = null;
$("mic").onclick = ()=>{
  const SR = window.SpeechRecognition||window.webkitSpeechRecognition;
  if (!SR) { alert("speech input: none declared on this browser"); return; }
  if (rec) { rec.stop(); rec=null; return; }
  rec = new SR(); rec.lang="en-US";
  rec.onresult = async e=>{
    const text = e.results[0][0].transcript;
    await api("/api/transcribe",{text});
    refresh();
  };
  rec.onend = ()=>{ rec=null; };
  rec.start();
};
// ---- refresh loop + SSE ------------------------------------------------------
async function refresh() {
  try {
    STATE = await api("/api/state");
  } catch(e) { return; }
  renderRoster(); renderStage(); renderFeed(); renderBadges();
  // status bar
  $("sbVersion").textContent = "Vantage "+STATE.version;
  $("sbGate").textContent = STATE.gate.passed ?
    `gate PASS ${(STATE.gate.timeToGateMs/1000).toFixed(1)}s` : "gate —";
  $("sbLLM").textContent = "llm: "+(STATE.engines.llm&&STATE.engines.llm.mode);
  $("sbSources").textContent = "sources: "+
    Object.keys(STATE.connectors||{}).join(", ");
  $("sbFloor").textContent = "floor: "+STATE.speechFloor.depth+" queued";
  $("sbNeeds").textContent = "needs: "+STATE.needs.length+" open";
  $("themeSel").value = STATE.theme;
  $("honesty").textContent =
    `llm ${STATE.engines.llm.mode} · tts ${STATE.engines.tts.mode}`+
    ` · portrait ${STATE.engines.portrait.mode} · declared: `+
    (STATE.engines.declaredAbsences||[]).join(", ");
  // quick-select options
  const sel = $("address");
  const cur = sel.value;
  sel.innerHTML = `<option value="">auto</option>`+
    (STATE.roster||[]).map(p=>`<option value="${p.id}">${esc(p.name)}</option>`).join("");
  sel.value = cur;
}
try {
  const es = new EventSource("/api/events");
  es.onmessage = e => {
    const ev = JSON.parse(e.data);
    if (ev.kind==="persona.speak") refresh();
    if (ev.kind==="offer") {
      const f=$("feed"), d=document.createElement("div");
      d.className="msg"; d.innerHTML =
        `<div class="who">${esc(ev.payload.persona||"steward")} · offer</div>`+
        `<div class="txt">${esc(ev.payload.text)}</div>`;
      f.appendChild(d); f.scrollTop=f.scrollHeight;
    }
  };
} catch(e) {}
refresh();
setInterval(refresh, 5000);
