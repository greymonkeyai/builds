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
  renderHonesty(); renderRoster(); renderChat(); renderCommand();
  renderWorkshops(); renderSettings();
}

function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));}

function renderHonesty(){
  const h = STATE.honesty;
  $("#honesty").innerHTML =
    `<b>meridian</b> · ledger: <b>durable</b> (${h.ledger.total} rows / ${h.ledger.live} live)` +
    ` · llm: <b>${h.engines.llm.mode}</b>${h.engines.llm.model?" ("+esc(h.engines.llm.model)+")":""}` +
    ` · tts: local=<b>${h.engines.tts.local}</b> remote=<b>${h.engines.tts.remote}</b>` +
    ` · stt: <b>${esc(h.engines.stt.mode)}</b>` +
    ` · stub declarations: ${esc(Object.entries(h.stubDeclarations).map(([k,v])=>k+": "+v).join(" | "))}` +
    (STATE.admonitions.length? `\nADMONITION: ${esc(STATE.admonitions[STATE.admonitions.length-1])}`:"");
}

function portrait(p){
  if (p.art && p.art.dataUrl) {
    // generated persona art (C-PersonalityArt / presentation glass)
    return `<img src="${p.art.dataUrl}" width="36" height="36" style="border-radius:8px" alt="${esc(p.name)}"/>`;
  }
  return `<svg viewBox="0 0 100 100" width="36" height="36"><rect width="100" height="100" rx="14" fill="${p.color||'#345'}"/><circle cx="50" cy="50" r="34" fill="#00000033"/>${p.imitation?'<polygon points="88,6 96,14 88,22 80,14" fill="#ffbf00"/>':''}<text x="50" y="62" font-size="34" text-anchor="middle" fill="#fff">${esc(p.name[0]||"?")}</text></svg>`;
}

function renderRoster(){
  $("#frameTag").textContent = STATE.frame==="respondent"?"· lenses":"· personas";
  $("#roster").innerHTML = STATE.roster.map(p=>`
    <div class="persona">${portrait(p)}
      <div><div class="nm">${p.imitation?"◆ ":""}${esc(p.name)} ${p.imitation?'<span class="imit">IMITATION</span>':""}</div>
      <div class="tag">${esc((p.interests||[]).slice(0,3).join(" · "))}</div>
      <div class="tag">${esc(p.displayMode||"respondent")} · conf ${p.confidence}</div></div></div>`).join("")
    || '<div class="small">no personalities — mint one</div>';
}

function renderChat(){
  $("#chathead").textContent = STATE.topic?`Conversation — topic: ${STATE.topic}`:"Conversation";
  const items = [];
  STATE.chat.forEach(m=>{
    const p = STATE.roster.find(x=>"persona:"+x.id===m.claimant);
    items.push(`<div class="bubble ${m.role==='user'?'user':'persona'}">
      ${m.role==='user'?'':`<div class="who" style="color:${p?p.color:'#8af'}">${p&&p.imitation?"◆ ":""}${esc(p?p.name:m.claimant)}</div>`}
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

function needCard(n){
  const miss = n.deferred && n.deferred.missing ? n.deferred.missing : [];
  const grantMiss = miss.find(m=>m.slot==="__grant__");
  return `<div class="need"><b>${esc(n.kind)}</b> <span class="kv">${esc(n.id)}</span>
    <div class="kv">${esc(n.spec.summary||n.spec.toolId||"")}</div>
    <div class="kv">status: <span class="st">${esc(n.status)}</span>${n.deferred?" — deferred: "+esc(n.deferred.reason):""}</div>
    ${miss.length?`<div class="kv">missing: ${esc(miss.map(m=>m.slot).join(", "))}</div>`:""}
    ${grantMiss?`<button onclick="witnessGrant('${n.id}','${esc(grantMiss.scope||'')}')">witness grant (${esc(grantMiss.scope)})</button>`:""}
    <button onclick="cancelNeed('${n.id}')">cancel</button>
    <button onclick="addCand('${n.id}')">+ candidate</button></div>`;
}

async function witnessGrant(nid, scope){
  // need spec carries lock hint via slot values where applicable
  await api("/api/grants","POST",{scope});
  await api("/api/steward/wake","POST",{});
  refresh();
}
async function cancelNeed(nid){ await api(`/api/needs/${nid}/cancel`,"POST",{}); refresh(); }
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
  const prof = (STATE.honesty && "use") || "use";
  $("#toollist").innerHTML = STATE.tools.filter(t=>t.kind==="tool").map(t=>
    `<div class="tool"><b>${esc(t.id)}</b> <span class="kv">${esc(t.title)}</span>
    <div class="kv">${t.hasSteps?"declarative steps":t.hasFn?"host-backed fn":""}${t.need?` · need:${esc(t.need)}`:""}</div>
    <button onclick="openWorkshop('${t.id}')">open</button>
    <button onclick="inspectTool('${t.id}')">inspect</button></div>`).join("");
  const ns = new Set(STATE.tools.map(t=>t.id));
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

// ---------- events ----------
document.querySelectorAll("#tabs button").forEach(b=>b.onclick=()=>{
  document.querySelectorAll("#tabs button").forEach(x=>x.classList.remove("on"));
  b.classList.add("on");
  document.querySelectorAll("main section").forEach(s=>s.classList.add("hidden"));
  $("#tab-"+b.dataset.tab).classList.remove("hidden");
  if(b.dataset.tab==="library"){ loadNs(); }
  if(b.dataset.tab==="log"){ loadLog(); }
});

let ALL=false;
$("#allChatBtn").onclick=()=>{ALL=!ALL;$("#allChatBtn").textContent=ALL?"ALL CHAT ✓":"ALL CHAT";};
$("#send").onclick=send;
$("#msg").addEventListener("keydown",e=>{if(e.key==="Enter")send();});
async function send(){
  const t=$("#msg").value.trim(); if(!t)return;
  $("#msg").value="";
  await api("/api/chat","POST",{text:t,all:ALL});
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
