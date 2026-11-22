/* Meridian UI — panels over the assertion ledger. All writes go through the
   API -> append seam; nothing here is a second truth store. */
const $ = s => document.querySelector(s);
const api = async (p, m, b) => {
  const r = await fetch(p, {method: m || "GET",
    headers: {"Content-Type": "application/json"},
    body: b ? JSON.stringify(b) : undefined});
  return r.json();
};
let STATE = {};

async function refresh() {
  STATE = await api("/api/state");
  applyTheme();
  renderHonesty(); renderStatusBar(); renderRoster(); renderChat();
  renderCommand(); renderWorkshops(); renderSettings(); renderAddress();
}

function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));}

// ---- theme (S-color-schemes) ----
function applyTheme(){
  const t = STATE.theme || "light";
  document.body.dataset.theme = t;
  const sel = $("#themeSel");
  if (sel && sel.value !== t) sel.value = t;
}
$("#themeSel") && ($("#themeSel").onchange = async e => {
  await api("/api/config","POST",{predicate:"ui:shell-theme",value:e.target.value});
  document.body.dataset.theme = e.target.value;
});

function renderHonesty(){
  const h = STATE.honesty;
  $("#honesty").innerHTML =
    `<b>meridian ${esc(STATE.version||"")}</b> · ledger: <b>durable</b> (${h.ledger.total} rows / ${h.ledger.live} live)` +
    ` · llm: <b>${h.engines.llm.mode}</b>${h.engines.llm.model?" ("+esc(h.engines.llm.model)+")":""}` +
    ` · tts: local=<b>${h.engines.tts.local}</b> remote=<b>${h.engines.tts.remote}</b>` +
    ` · stt: <b>${esc(h.engines.stt.mode)}</b>` +
    ` · stub declarations: ${esc(Object.entries(h.stubDeclarations).map(([k,v])=>k+": "+v).join(" | "))}` +
    (STATE.admonitions.length? `\nADMONITION: ${esc(STATE.admonitions[STATE.admonitions.length-1])}`:"");
}

// ---- status bar (S-status-bar): version, gate, LLMs, sources, floor, needs
function renderStatusBar(){
  const h = STATE.honesty, g = STATE.gate || {};
  $("#sbVersion").innerHTML = `v<b>${esc(STATE.version||"?")}</b>`;
  $("#sbGate").innerHTML = g.passed
    ? `gate <b>PASS</b> ${g.msToGate!=null?"(t="+g.msToGate+"ms)":""}`
    : `gate <b>FAIL</b>`;
  $("#sbLLM").innerHTML = `llm <b>${h.engines.llm.mode}</b>` +
    (h.engines.llm.model?` [${esc(h.engines.llm.model)}]`:"") +
    ` · tts <b>${h.engines.tts.local}</b>`;
  const cfg = (STATE.connectors&&STATE.connectors.configured)||[];
  const avail = (STATE.connectors&&STATE.connectors.available)||[];
  $("#sbSources").innerHTML = `sources <b>${cfg.length}</b> configured` +
    (cfg.length?` (${esc(cfg.map(c=>c.id).join(", "))})`:"") +
    ` / ${avail.length} known`;
  $("#sbFloor").innerHTML = `floor depth <b>${STATE.speechFloor?STATE.speechFloor.depth:0}</b>`;
  $("#sbNeeds").innerHTML = `open needs <b>${(STATE.needs||[]).length}</b>` +
    ` · emails <b>${STATE.emails||0}</b>`;
}

function portrait(p, size){
  const s = size || 36;
  if (p.art && p.art.dataUrl) {
    return `<img src="${p.art.dataUrl}" width="${s}" height="${s}" style="border-radius:8px" alt="${esc(p.name)}"/>`;
  }
  return `<svg viewBox="0 0 100 100" width="${s}" height="${s}"><rect width="100" height="100" rx="14" fill="${p.color||'#345'}"/><circle cx="50" cy="50" r="34" fill="#00000033"/>${p.imitation?'<polygon points="88,6 96,14 88,22 80,14" fill="#ffbf00"/>':''}<text x="50" y="62" font-size="34" text-anchor="middle" fill="#fff">${esc(p.name[0]||"?")}</text></svg>`;
}

// ---- roster (S-personality-roster: persistent panel; click opens editor)
function renderRoster(){
  $("#frameTag").textContent = STATE.frame==="respondent"?"· lenses":"· personas";
  $("#roster").innerHTML = STATE.roster.map(p=>`
    <div class="persona" onclick="openEditor('${p.id}')" title="open personality editor">${portrait(p,44)}
      <div><div class="nm">${p.imitation?"◆ ":""}${esc(p.name)} ${p.imitation?'<span class="imit">IMITATION</span>':""}</div>
      <div class="tag">${esc((p.lens&&p.lens.register)||(p.lens&&p.lens.style)||"")} · ${esc((p.interests||[]).slice(0,3).join(" · "))}</div>
      <div class="tag">${esc(p.displayMode||"respondent")} · conf ${p.confidence}</div></div></div>`).join("")
    || '<div class="small">no personalities — mint one</div>';
}

function renderAddress(){
  const sel = $("#address"), cur = sel.value;
  sel.innerHTML = '<option value="">auto</option>' +
    STATE.roster.map(p=>`<option value="${p.id}" ${p.id===cur?"selected":""}>${esc(p.name)}</option>`).join("");
}

// ---- chat: context display (S-context-display), reset (S-conversation-reset)
function renderChat(){
  $("#chatheadText").textContent = STATE.topic?`Conversation — topic: ${STATE.topic}`:"Conversation";
  const cb = $("#ctxbadge");
  if (STATE.context && STATE.context.label) {
    cb.textContent = "ctx: " + STATE.context.label;
    cb.classList.remove("hidden");
  } else cb.classList.add("hidden");
  const fb = $("#focusbadge");
  if (STATE.focus && STATE.focus.needId) {
    fb.textContent = "focused: " + STATE.focus.needId;
    fb.classList.remove("hidden");
  } else fb.classList.add("hidden");
  const items = [];
  STATE.chat.forEach(m=>{
    const p = STATE.roster.find(x=>"persona:"+x.id===m.claimant);
    items.push(`<div class="bubble ${m.role==='user'?'user':'persona'}">
      ${m.role==='user'?'':`<div class="who" style="color:${p?p.color:'#8af'}">${p?portrait(p,20):""}${p&&p.imitation?"◆ ":""}${esc(p?p.name:m.claimant)}</div>`}
      ${esc(m.text)}</div>`);
  });
  STATE.cards.forEach(ev=>{
    const c = ev.payload||{};
    const cls = c.kind==="witness"?"card witness":c.kind==="workshop"?"card workshop":"card";
    items.push(`<div class="${cls}">${esc(c.kind||"card")} · ${esc(c.summary||c.text||JSON.stringify(c).slice(0,120))}</div>`);
  });
  $("#feed").innerHTML = items.join("");
  $("#feed").scrollTop = $("#feed").scrollHeight;
}

$("#resetBtn").onclick = async ()=>{
  if (!confirm("Reset the conversation? The transcript is sealed into an archive, topic/context/focus cleared.")) return;
  await api("/api/chat/reset","POST",{});
  refresh();
};

// ---- inbox (S-email-commentary) ----
async function loadInbox(){
  const r = await api("/api/emails?limit=50");
  $("#inboxSrc").textContent = r.emails.length?`· ${r.emails.length} messages`:"";
  $("#inboxList").innerHTML = r.emails.map(e=>`
    <div class="email" onclick="selectEmail('${e.id}')">
      <div class="subj">${esc(e.subject)}</div>
      <div class="kv">from ${esc(e.from)} · ${esc(e.date||"")}</div>
      <div class="kv">${esc((e.body||"").slice(0,140))}${(e.body||"").length>140?"…":""}</div>
    </div>`).join("") || '<div class="small">inbox empty</div>';
  const c = await api("/api/context");
  if (c.context && c.context.kind==="email") {
    $("#selctx").innerHTML = `<div class="kv">active context:</div>
      <div class="email"><div class="subj">${esc(c.context.label)}</div>
      <div class="kv">${esc((c.context.detail||"").slice(0,300))}</div></div>`;
  }
}
async function selectEmail(id){
  const r = await api("/api/context/select","POST",{kind:"email",itemId:id});
  if (r.commentary) {
    $("#ctxCommentary").innerHTML = `<div class="commentary">
      <div class="who">${esc(r.commentary.name)} comments <span class="small">${esc(r.commentary.engine||"")}</span></div>
      ${esc(r.commentary.text)}</div>`;
  }
  $("#selctx").innerHTML = r.context?`<div class="kv">active context:</div>
    <div class="email"><div class="subj">${esc(r.context.label)}</div></div>`:$("#selctx").innerHTML;
  refresh();
}
$("#inboxRefresh").onclick = async ()=>{
  await api("/api/connectors/run","POST",{connectorId:"inbox-local"});
  loadInbox(); refresh();
};

function needCard(n){
  const miss = n.deferred && n.deferred.missing ? n.deferred.missing : [];
  const grantMiss = miss.find(m=>m.slot==="__grant__");
  const focused = STATE.focus && STATE.focus.needId===n.id;
  return `<div class="need"><b>${esc(n.kind)}</b> <span class="kv">${esc(n.id)}</span>
    <div class="kv">${esc(n.spec.summary||n.spec.toolId||"")}</div>
    <div class="kv">status: <span class="st">${esc(n.status)}</span>${n.deferred?" — deferred: "+esc(n.deferred.reason):""}${focused?' · <b>focused</b>':""}</div>
    ${miss.length?`<div class="kv">missing: ${esc(miss.map(m=>m.slot).join(", "))}</div>`:""}
    ${grantMiss?`<button onclick="witnessGrant('${n.id}','${esc(grantMiss.scope||'')}')">witness grant (${esc(grantMiss.scope)})</button>`:""}
    <button onclick="focusNeed('${n.id}')" title="focus: chat input fills this need's slots conversationally">focus</button>
    <button onclick="cancelNeed('${n.id}')">cancel</button>
    <button onclick="addCand('${n.id}')">+ candidate</button></div>`;
}

async function witnessGrant(nid, scope){
  await api("/api/grants","POST",{scope});
  await api("/api/steward/wake","POST",{});
  refresh();
}
async function cancelNeed(nid){ await api(`/api/needs/${nid}/cancel`,"POST",{}); refresh(); }
async function focusNeed(nid){ await api(`/api/needs/${nid}/focus`,"POST",{}); refresh(); }
async function addCand(nid){
  const slot=prompt("slot name"), value=prompt("value"), conf=prompt("confidence","0.8");
  if(!slot) return;
  await api(`/api/needs/${nid}/candidate`,"POST",{slot,value,confidence:parseFloat(conf||"0.8")});
  refresh();
}

function renderCommand(){
  $("#projects").innerHTML = STATE.projects.map(p=>`
    <div class="proj"><b>${esc(p.title||p.id)}</b> <span class="kv">${esc(p.id)}</span>
    <div class="kv">goals: ${(p.goals||[]).map(g=>esc(g.text||g)).join("; ")||"—"}</div>
    <div class="kv">open needs: ${p.openNeeds.length} · fulfilled: ${p.fulfilled}</div></div>`).join("")
    || '<div class="small">no projects — create one</div>';
  $("#needs").innerHTML = STATE.needs.map(needCard).join("")
    || '<div class="small">queue empty</div>';
  $("#focus").innerHTML = `<div class="kv">topic: ${esc(STATE.topic||"—")} · depth: ${STATE.responseDepth}</div>`;
  api("/api/calendar").then(r=>{
    $("#cal").innerHTML = (r.events||[]).map(e=>{
      const d = e.startMs?new Date(e.startMs).toLocaleString():"?";
      return `<div class="kv">◷ ${d} — ${esc(e.title)}</div>`;}).join("")||'<div class="small">no events</div>';
  });
  api("/api/grants").then(r=>{
    $("#grantReqs").innerHTML = (r.grants||[]).filter(g=>!g.consumed).map(g=>
      `<div class="grant kv">◈ ${esc(g.scope)} ${g.lock?("→ "+esc(g.lock)):""} <span class="small">witnessed, unconsumed</span></div>`).join("")
      || '<div class="small">no live grants</div>';
  });
}

async function renderWorkshops(){
  $("#toollist").innerHTML = STATE.tools.filter(t=>t.kind==="tool").map(t=>
    `<div class="tool"><b>${esc(t.id)}</b> <span class="kv">${esc(t.title)}</span>
    <div class="kv">${t.hasSteps?"declarative steps":t.hasFn?"host-backed fn":""}${t.need?` · need:${esc(t.need)}`:""}</div>
    <button onclick="openWorkshop('${t.id}')">open</button>
    <button onclick="inspectTool('${t.id}')">inspect</button></div>`).join("");
}

async function inspectTool(id){
  const r = await api(`/api/tools/${id}/inspect`,"POST",{});
  $("#workshop").innerHTML = `<pre>${esc(JSON.stringify(r,null,1))}</pre>`;
}

function openWorkshop(id){
  const t = STATE.tools.find(x=>x.id===id);
  if(!t) return;
  const fields = (t.slots||[]).map(s=>`
    <div class="field"><label>${esc(s.name)} ${s.required?'<span class="req">*</span>':''}
    <span class="small">${esc(s.hint||"")}${s.minCertainty?` · minCertainty ${s.minCertainty}`:""}</span></label>
    ${s.widget==="select"?`<select data-slot="${esc(s.name)}">${(s.options||[]).map(o=>`<option>${esc(o)}</option>`).join("")}</select>`
      :s.widget==="textarea"?`<textarea data-slot="${esc(s.name)}" rows="3"></textarea>`
      :`<input data-slot="${esc(s.name)}" placeholder="${esc(s.widget||"text")}">`}</div>`).join("");
  $("#workshop").innerHTML = `<h4>${esc(t.title)} <span class="kv">${esc(t.id)}</span></h4>
    <div class="slotbox">${fields||'<div class="small">no template slots</div>'}</div>
    ${t.grant?`<div class="kv">requires witnessed grant: <b>${esc(t.grant.scope)}</b></div>`:""}
    <button onclick="submitTool('${t.id}')">submit</button><div id="wsmsg"></div>`;
}

async function submitTool(id){
  const slots = {};
  document.querySelectorAll("#workshop [data-slot]").forEach(el=>{
    let v = el.value;
    if(v && v.startsWith("[")||v&&v.startsWith("{")){ try{v=JSON.parse(v);}catch(e){} }
    else if(v && v.includes(",") ) { v = v.split(",").map(x=>x.trim()).filter(Boolean); }
    if(v!==""&&v!=null) slots[el.dataset.slot]=v;
  });
  const r = await api("/api/invoke","POST",{toolId:id,slots});
  $("#wsmsg").innerHTML = `<pre>${esc(JSON.stringify(r,null,1))}</pre>`;
  setTimeout(refresh, 400);
}

function renderSettings(){
  $("#settings").innerHTML = `
    <h3>Conversation</h3>
    <div class="kv">response depth (max respondents)</div>
    <select id="sdepth">${[1,2,3,4].map(n=>`<option ${n===STATE.responseDepth?"selected":""}>${n}</option>`).join("")}</select>
    <div class="kv">persona frame (A12 — non-anthropomorphic option)</div>
    <select id="sframe"><option ${STATE.frame==="respondent"?"selected":""}>respondent</option>
    <option ${STATE.frame==="personified"?"selected":""}>personified</option></select>
    <h3>Stewardship (configurable duties)</h3>
    <div class="kv">duties (comma-separated): drain-needs, countdown, calendar-scan, source-confidence, compact-check</div>
    <input id="sduties" value="drain-needs, countdown, calendar-scan, source-confidence, compact-check">
    <div class="kv">interval seconds</div><input id="sint" value="15">
    <button id="ssave">save settings</button>
    <button id="swake">run steward now</button>
    <button id="sclean">run cleanup</button><pre id="smsg"></pre>`;
  $("#ssave").onclick = async ()=>{
    await api("/api/invoke","POST",{toolId:"set-response-depth",slots:{value:parseInt($("#sdepth").value)}});
    await api("/api/invoke","POST",{toolId:"set-persona-frame",slots:{value:$("#sframe").value}});
    await api("/api/invoke","POST",{toolId:"assign-stewardship",slots:{
      duties:$("#sduties").value.split(",").map(s=>s.trim()).filter(Boolean),
      intervalSec:parseInt($("#sint").value||"15")}});
    refresh();
  };
  $("#swake").onclick = async ()=>{ $("#smsg").textContent = JSON.stringify(await api("/api/steward/wake","POST",{}),null,1); };
  $("#sclean").onclick = async ()=>{ $("#smsg").textContent = JSON.stringify(await api("/api/cleanup","POST",{}),null,1); };
}

// ---------- personality editor (S-personality-editor) ----------
let ED_PID = null;
window.openEditor = function(pid){
  const p = STATE.roster.find(x=>x.id===pid);
  if (!p) return;
  ED_PID = pid;
  $("#edTitle").textContent = "personality editor — " + p.name;
  $("#edPortrait").innerHTML = portrait(p, 120);
  $("#peName").value = p.name || "";
  $("#peTraits").value = (p.traits||[]).join(", ");
  $("#peInterests").value = (p.interests||[]).join(", ");
  $("#peRegister").value = (p.lens&&(p.lens.register||p.lens.style)) || "measured";
  $("#peResp").value = ((p.lens||{}).responsibilities||[]).join(", ");
  $("#peVoice").value = (p.voice&&(p.voice.name||p.voice.local)) || "";
  $("#peRate").value = (p.voice&&p.voice.rate)!=null ? p.voice.rate : 0;
  $("#peColor").value = /^#([0-9a-f]{6})$/i.test(p.color||"") ? p.color : "#4ea1d3";
  $("#pePrio").value = p.rosterPriority!=null ? p.rosterPriority : 0.5;
  $("#peMode").value = p.displayMode || "respondent";
  $("#peMsg").textContent = "";
  $("#editor").classList.remove("hidden");
};
$("#peClose").onclick = ()=>{ $("#editor").classList.add("hidden"); ED_PID=null; };
$("#peSave").onclick = async ()=>{
  const csv = s => s.split(",").map(x=>x.trim()).filter(Boolean);
  const body = {personaId: ED_PID,
    name: $("#peName").value.trim() || undefined,
    traits: csv($("#peTraits").value),
    interests: csv($("#peInterests").value),
    lens: {register: $("#peRegister").value, style: $("#peRegister").value,
           responsibilities: csv($("#peResp").value)},
    voice: {name: $("#peVoice").value.trim() || "sapi-default",
            rate: parseInt($("#peRate").value||"0")},
    color: $("#peColor").value,
    rosterPriority: parseFloat($("#pePrio").value||"0.5"),
    displayMode: $("#peMode").value};
  const r = await api("/api/personas/update","POST",body);
  $("#peMsg").textContent = JSON.stringify(r.error||"saved — all editable elements asserted",null,1);
  refresh();
};
$("#peReart").onclick = async ()=>{
  const r = await api("/api/personas/art","POST",{personaId:ED_PID});
  $("#peMsg").textContent = JSON.stringify(r.result||r,null,1);
  refresh();
  setTimeout(()=>openEditor(ED_PID),300);
};
$("#peSpeak").onclick = async ()=>{
  const r = await api("/api/tts","POST",{text:"Hello — this is my voice.",
    personaId:ED_PID});
  $("#peMsg").textContent = JSON.stringify(r.result||r,null,1);
};

// ---------- events ----------
document.querySelectorAll("#tabs button").forEach(b=>b.onclick=()=>{
  document.querySelectorAll("#tabs button").forEach(x=>x.classList.remove("on"));
  b.classList.add("on");
  document.querySelectorAll("main section").forEach(s=>s.classList.add("hidden"));
  $("#tab-"+b.dataset.tab).classList.remove("hidden");
  if(b.dataset.tab==="library"){ loadNs(); }
  if(b.dataset.tab==="log"){ loadLog(); }
  if(b.dataset.tab==="inbox"){ loadInbox(); }
});

let ALL=false;
$("#allChatBtn").onclick=()=>{ALL=!ALL;$("#allChatBtn").textContent=ALL?"ALL CHAT ✓":"ALL CHAT";};
$("#send").onclick=send;
$("#msg").addEventListener("keydown",e=>{if(e.key==="Enter")send();});
async function send(){
  const t=$("#msg").value.trim(); if(!t)return;
  $("#msg").value="";
  await api("/api/chat","POST",{text:t,all:ALL,personaId:$("#address").value||undefined});
  refresh();
}
$("#mintBtn").onclick=async()=>{
  const name=prompt("name?"); if(!name)return;
  const interests=(prompt("interests (comma-separated)?","")||"").split(",").map(s=>s.trim()).filter(Boolean);
  const traits=(prompt("traits (comma-separated)?","")||"").split(",").map(s=>s.trim()).filter(Boolean);
  const imit=prompt("imitates a recognizable person? (name, or blank)","");
  const body={name,interests,traits};
  if(imit){ body.imitates={name:imit,recency:prompt("living | deceased-10y | deceased-older | fictional","living")}; }
  await api("/api/invoke","POST",{toolId:"create-persona",slots:body});
  refresh();
};
$("#newProj").onclick=async()=>{
  const title=prompt("project title?"); if(!title)return;
  const goals=(prompt("goals (comma-separated)?","")||"").split(",").map(s=>s.trim()).filter(Boolean);
  await api("/api/invoke","POST",{toolId:"create-project",slots:{title,goals}});
  refresh();
};
$("#mic").onclick=()=>{
  const SR = window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){ alert("stt: browser Web Speech API unavailable — declared, not faked"); return; }
  const r=new SR(); r.onresult=e=>{
    const res=e.results[0][0];
    api("/api/stt","POST",{transcript:res.transcript,confidence:res.confidence||0.7}).then(refresh);
  }; r.start();
};

async function loadNs(){
  const r = await api("/api/library?limit=2000");
  const preds=[...new Set(r.rows.map(x=>x.predicate))].sort();
  $("#libns").innerHTML='<option value="">(all predicates)</option>'+preds.map(p=>`<option>${p}</option>`).join("");
  $("#librows").innerHTML = r.rows.slice(-300).reverse().map(row=>
    `<div class="kv">[${row.predicate}] <b>${esc(row.subjectKey)}</b> = ${esc(JSON.stringify(row.value.v)).slice(0,120)}
     <span class="small">${esc(row.claimant)} · c=${row.certainty} · ${new Date(row.at).toLocaleTimeString()} · ${esc(row.id)}</span></div>`).join("");
}
$("#libSearch").onclick=async()=>{
  const r=await api("/api/library?q="+encodeURIComponent($("#libq").value));
  $("#librows").innerHTML = r.rows.map(row=>
    `<div class="kv">[${row.predicate}] <b>${esc(row.subjectKey)}</b> = ${esc(JSON.stringify(row.value.v)).slice(0,140)}
     <span class="small">${esc(row.claimant)} · c=${row.certainty}</span></div>`).join("");
};
$("#libns").onchange=async()=>{
  const r=await api("/api/library?predicate="+encodeURIComponent($("#libns").value));
  $("#librows").innerHTML = r.rows.map(row=>
    `<div class="kv">[${row.predicate}] <b>${esc(row.subjectKey)}</b> = ${esc(JSON.stringify(row.value.v)).slice(0,140)}</div>`).join("");
};
$("#viewGo").onclick=async()=>{
  const r=await api("/api/view?subject="+encodeURIComponent($("#viewsubj").value));
  $("#viewout").textContent=JSON.stringify(r,null,1);
};
$("#edGo").onclick=async()=>{
  let v=$("#edVal").value; try{v=JSON.parse(v);}catch(e){}
  const r=await api("/api/library/assert","POST",{subject:$("#edSubj").value,
    predicate:$("#edPred").value,value:v,certainty:parseFloat($("#edCert").value||"0.9"),
    supersedes:$("#edSup").value||undefined});
  $("#edMsg").textContent=JSON.stringify(r); loadNs();
};
$("#validateSpec").onclick=async()=>{
  let spec; try{spec=JSON.parse($("#newspec").value);}catch(e){$("#specMsg").textContent="bad JSON";return;}
  $("#specMsg").textContent=JSON.stringify(await api("/api/invoke","POST",{toolId:"validate-tool",slots:{spec}}),null,1);
};
$("#mintSpec").onclick=async()=>{
  let spec; try{spec=JSON.parse($("#newspec").value);}catch(e){$("#specMsg").textContent="bad JSON";return;}
  $("#specMsg").textContent=JSON.stringify(await api("/api/invoke","POST",{toolId:"create-tool",slots:{spec}}),null,1);
  refresh();
};
$("#expBtn").onclick=async()=>{
  const r=await api("/api/exchange/export","POST",{});
  $("#expMsg").textContent=" "+JSON.stringify(r.result||r);
};
$("#impBtn").onclick=async()=>{
  let pkg; try{pkg=JSON.parse($("#impPkg").value);}catch(e){$("#impMsg").textContent="bad JSON";return;}
  const r=await api("/api/exchange/import","POST",{package:pkg});
  $("#impMsg").textContent=JSON.stringify(r.result||r,null,1); refresh();
};
async function loadLog(){
  const r=await api("/api/log?kind="+$("#logkind").value+"&limit=80");
  $("#log").textContent=r.rows.map(x=>JSON.stringify(x)).join("\n")||"(none)";
}
$("#loggo").onclick=loadLog;

refresh();
setInterval(()=>{ if(!document.hidden) refresh(); }, 8000);
