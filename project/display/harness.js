/* harness-ui static shell \u2014 renders window.HARNESS_DATA (emitted by harness-emit.ps1).
   file:// only: data.js arrives via <script> tag; polling re-injects a cache-busted
   script tag every 30s while visible; refocus reloads and re-renders ONLY when the
   payload's generated_at stamp is newer than what is rendered. */
(function () {
  'use strict';
  var app = document.getElementById('app');
  var state = {
    data: window.HARNESS_DATA || null,
    stamp: (window.HARNESS_DATA && window.HARNESS_DATA.generated_at) || null,
    polls: 0,
    tab: 'summary',
    selPoint: -1,      // series index chosen for build detail
    depth: 0           // 0 = all
  };
  var loadUtc = Date.now();
  // deep link: #comparison / #current / #builddetail[/<series-index>]
  (function () {
    var h = (window.location.hash || '').replace(/^#/, '');
    if (!h) return;
    var parts = h.split('/');
    if (['summary','direction','documents','comparison','scorecard','current','builddetail'].indexOf(parts[0]) >= 0) state.tab = parts[0];
    if (parts[1] !== undefined && !isNaN(+parts[1])) state.selPoint = +parts[1];
  })();

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined && text !== null) e.textContent = String(text);
    return e;
  }
  function age(sec) {
    if (sec === null || sec === undefined) return null;
    var s = Math.max(0, Math.round(sec)), out;
    if (s < 90) out = s + 's';
    else if (s < 5400) out = Math.round(s / 60) + 'm';
    else if (s < 172800) out = (s / 3600).toFixed(1) + 'h';
    else out = Math.round(s / 86400) + 'd';
    return out;
  }
  function absent(why) { var d = el('span', 'absent', '\u2014 ' + (why || 'absent')); return d; }
  function gap(msg) { var d = el('div', 'gap'); d.appendChild(document.createTextNode(msg)); return d; }

  /* ---------- owner cues — things that need the owner ---------- */
  // Reads both payload shapes: the fleet row fields (docs_*, direction) and the
  // project payload (register.pending/provisional_ids/headerless,
  // state.direction_in_force.ref).
  function computeCues(p) {
    var cues = [];
    var reg = p.register || {};
    var pendIds = p.docs_pending_ids || reg.pending || [];
    var pend = (p.docs_pending != null) ? p.docs_pending : pendIds.length;
    var provIds = p.docs_provisional_ids || reg.provisional_ids || [];
    var unregIds = p.docs_unregistered || reg.headerless || [];
    var dir = p.direction || (p.state && p.state.direction_in_force && p.state.direction_in_force.ref);
    var qs = (p.state && p.state.pending_owner_questions) ? p.state.pending_owner_questions.length : 0;
    if (pend > 0) cues.push({ sev: 'action', text: pend + ' doc' + (pend > 1 ? 's' : '') + ' pending approval: ' + pendIds.join(', '), do: 'documents tab — read and approve or amend' });
    if (provIds.length > 0) cues.push({ sev: 'warn', text: provIds.length + ' doc' + (provIds.length > 1 ? 's' : '') + ' carrying provisional ids', do: 'review wording; corpus adoption assigns real ids' });
    if (unregIds.length > 0) cues.push({ sev: 'warn', text: unregIds.length + ' unregistered doc' + (unregIds.length > 1 ? 's' : '') + ': ' + unregIds.join(', '), do: 'stamp a harness-doc header or remove' });
    if (!dir) cues.push({ sev: 'action', text: 'no direction in force', do: 'scope and approve the next direction' });
    if (qs > 0) cues.push({ sev: 'action', text: qs + ' question' + (qs > 1 ? 's' : '') + ' awaiting you', do: 'answer in .devin/state.json' });
    return cues;
  }
  function cueStrip(p) {
    var cues = computeCues(p);
    var d = el('div', 'cue-strip');
    if (!cues.length) { d.appendChild(el('span', 'cue ok', '\u2713 nothing needs you — harness is clear')); return d; }
    cues.forEach(function (c) {
      var s = el('span', 'cue ' + c.sev, (c.sev === 'action' ? '\u25B2 ' : '\u25CB ') + c.text);
      s.title = c.do;
      d.appendChild(s);
    });
    d.appendChild(el('span', 'cue-do', 'next: ' + cues[0].do));
    return d;
  }
  function kvTable(obj, order) {
    var t = el('table', 'kv');
    var keys = order || Object.keys(obj);
    keys.forEach(function (k) {
      var tr = el('tr');
      tr.appendChild(el('th', null, k));
      var td = el('td');
      var v = obj ? obj[k] : undefined;
      if (v === undefined || v === null) td.appendChild(absent('not recorded'));
      else td.appendChild(renderAny(v));
      tr.appendChild(td); t.appendChild(tr);
    });
    return t;
  }
  function renderAny(v) {
    if (v === null || v === undefined) return absent();
    if (typeof v !== 'object') return el('span', null, String(v));
    if (Array.isArray(v)) {
      if (v.length === 0) return el('span', 'muted', '[] (empty \u2014 none recorded)');
      var ul = el('ul', 'cite');
      v.forEach(function (x) {
        var li = el('li');
        li.appendChild(renderAny(x));
        ul.appendChild(li);
      });
      return ul;
    }
    var keys = Object.keys(v);
    if (keys.length === 0) return el('span', 'muted', '{} (empty \u2014 none recorded)');
    return kvTable(v);
  }

  /* ---------- refresh ---------- */
  function pollData() {
    var s = document.createElement('script');
    s.src = 'data.js?ts=' + Date.now();
    s.onload = function () {
      state.polls++;
      var d = window.HARNESS_DATA;
      if (d && d.generated_at && d.generated_at !== state.stamp) {
        state.data = d; state.stamp = d.generated_at;
        render();
      }
      updateBadge();
      s.remove();
    };
    s.onerror = function () { updateBadge('data.js reload failed'); s.remove(); };
    document.head.appendChild(s);
  }
  function updateBadge(err) {
    var b = document.getElementById('refresh-badge');
    if (!b) return;
    b.textContent = 'data ' + (state.stamp || 'none') + ' \u00b7 polls ' + state.polls +
      (err ? ' \u00b7 ' + err : '');
    document.body.setAttribute('data-polls', String(state.polls));
    document.body.setAttribute('data-stamp', state.stamp || '');
  }
  setInterval(function () { if (!document.hidden) pollData(); }, 30000);
  document.addEventListener('visibilitychange', function () {
    if (!document.hidden) pollData();
  });
  window.addEventListener('focus', function () { pollData(); });
  setInterval(function () { // liveness tick, derived locally from the emitted age
    var d = state.data;
    var p = d && (d.kind === 'project' ? d.project : null);
    var secs = p ? p.liveness_seconds : null;
    var nodes = document.querySelectorAll('[data-age]');
    for (var i = 0; i < nodes.length; i++) {
      var base = secs;
      if (nodes[i].getAttribute('data-age') === 'fleet') base = +nodes[i].getAttribute('data-sec');
      if (base === null || base === undefined || isNaN(base)) { nodes[i].textContent = '\u2014'; continue; }
      nodes[i].textContent = age(base + (Date.now() - loadUtc) / 1000);
    }
  }, 1000);

  /* ---------- header ---------- */
  function header(sub) {
    var h = el('header', 'top');
    h.appendChild(el('h1', null, 'harness status'));
    h.appendChild(el('span', 'meta', sub));
    var b = el('span', 'meta'); b.id = 'refresh-badge';
    h.appendChild(b);
    var note = el('span', 'refresh-note', 'polls data.js every 30s while visible; refocus re-renders only on a newer generated-at');
    h.appendChild(note);
    return h;
  }

  /* ---------- fleet ---------- */
  /* ---------- launch bridge ----------
     The page is static; launching a build's own launcher (launch.cmd etc.)
     goes through harness-display.pyw's pywebview API when the display runs
     as its own window, else launch-serve.py on localhost:8358, else a hint. */
  var LAUNCH_SVC = 'http://127.0.0.1:8358';
  function launchButton(projectId, label) {
    var wrap = el('span', 'launchwrap');
    var b = el('button', 'launchbtn', '\u25B6 ' + (label || 'launch'));
    var note = el('span', 'muted');
    b.addEventListener('click', function (ev) {
      ev.stopPropagation();
      b.disabled = true;
      note.textContent = ' launching\u2026';
      function done(j) {
        b.disabled = false;
        if (j && j.ok) note.textContent = ' ' + j.build + ' launched \u2014 ' + String(j.launcher).split(/[\\/]/).pop() + ' (pid ' + j.pid + ')';
        else note.textContent = ' ' + ((j && j.error) || 'launch failed');
      }
      function fail() {
        b.disabled = false;
        note.textContent = ' no launch path \u2014 run the display app (harness-display.pyw) or launch-serve.py on :8358, or run the build\u2019s launch.cmd manually';
      }
      try {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.launch) {
          window.pywebview.api.launch(projectId).then(done).catch(fail);
        } else {
          fetch(LAUNCH_SVC + '/launch?project=' + encodeURIComponent(projectId))
            .then(function (r) { return r.json(); })
            .then(done).catch(fail);
        }
      } catch (e) { fail(); }
    });
    wrap.appendChild(b); wrap.appendChild(note);
    return wrap;
  }

  function renderFleet(d) {
    var m = el('main'); m.id = 'view-fleet';
    m.appendChild(el('p', 'meta',
      'root ' + d.root + ' \u00b7 generated ' + d.generated_at + ' \u00b7 liveness excludes ' + (d.exclusions || 'display/, .devin/, .git/')));
    if (!d.projects || d.projects.length === 0) {
      m.appendChild(gap('no machinery-carrying projects discovered under ' + d.root));
      return m;
    }
    var t = el('table');
    t.setAttribute('data-rows', String(d.projects.length));
    var tr = el('tr');
    ['line', 'direction in force', 'budget spent', 'docs', 'last verdict', 'liveness age', 'last status', 'page', 'launch'].forEach(function (x) { tr.appendChild(el('th', null, x)); });
    t.appendChild(tr);
    d.projects.forEach(function (p) {
      var r = el('tr', 'fleet-row');
      r.appendChild(el('td', null, p.line || p.id));
      var td = el('td');
      if (p.direction) td.appendChild(el('span', null, p.direction + (p.direction_clarity ? ' (' + p.direction_clarity + ')' : '')));
      else td.appendChild(absent(p.state_present ? 'state.json parsed; direction absent' : 'no state.json'));
      r.appendChild(td);
      td = el('td');
      if (p.budget && (p.budget.spent !== undefined || p.budget.total !== undefined))
        td.appendChild(el('span', null, (p.budget.spent === null || p.budget.spent === undefined ? '\u2014' : p.budget.spent) + ' / ' + (p.budget.total === null || p.budget.total === undefined ? '\u2014' : p.budget.total)));
      else td.appendChild(absent());
      r.appendChild(td);
      td = el('td');
      var pend = p.docs_pending || 0;
      var inf = (p.docs_in_force || []).length;
      var unreg = (p.docs_unregistered || []).length;
      var cues = computeCues(p);
      if (cues.some(function (c) { return c.sev === 'action'; })) {
        var ny = el('span', 'needs-you', '\u25B2 needs you');
        ny.title = cues.map(function (c) { return c.text + ' — ' + c.do; }).join('\n');
        td.appendChild(ny); td.appendChild(el('span', 'muted', ' · '));
      }
      if (pend === 0 && inf === 0 && unreg === 0) td.appendChild(absent('no register'));
      else {
        if (pend > 0) { var w = el('span', 'doc-pending', pend + ' pending'); w.title = (p.docs_pending_ids || []).join(', '); td.appendChild(w); td.appendChild(el('span', 'muted', ' · ')); }
        td.appendChild(el('span', inf > 0 ? 'doc-inforce' : 'muted', inf + ' in force'));
        if (unreg > 0) { td.appendChild(el('span', 'muted', ' · ')); var u = el('span', 'doc-unreg', unreg + ' unregistered'); u.title = p.docs_unregistered.join(', '); td.appendChild(u); }
      }
      r.appendChild(td);
      td = el('td');
      if (p.last_verdict)
        td.appendChild(el('span', null,
          (p.last_verdict.overall === null || p.last_verdict.overall === undefined ? '\u2014' : p.last_verdict.overall) +
          ' @ ' + p.last_verdict.label + (p.last_verdict.judge ? ' \u00b7 ' + p.last_verdict.judge : '')));
      else if (p.n_verdicts === 0) td.appendChild(absent('no parsed verdict'));
      else td.appendChild(absent());
      r.appendChild(td);
      td = el('td');
      var a = el('span'); a.setAttribute('data-age', 'fleet'); a.setAttribute('data-sec', String(p.liveness_seconds));
      a.textContent = age(p.liveness_seconds) || '\u2014';
      td.appendChild(a);
      if (p.newest_mtime) { td.appendChild(el('span', 'muted', ' \u00b7 ')); td.title = 'newest in-scope mtime ' + p.newest_mtime; }
      r.appendChild(td);
      td = el('td', 'mono'); td.appendChild(el('span', null, p.last_status ? String(p.last_status).split('\n')[0].slice(0, 80) : '\u2014'));
      r.appendChild(td);
      td = el('td');
      var link = el('a', null, 'open');
      link.href = encodeURI(p.page);
      td.appendChild(link);
      r.appendChild(td);
      td = el('td');
      td.appendChild(launchButton(p.id, 'launch'));
      r.appendChild(td);
      r.addEventListener('click', function (ev) {
        if (ev.target.tagName !== 'A' && ev.target.tagName !== 'BUTTON') window.location.href = encodeURI(p.page);
      });
      t.appendChild(r);
    });
    m.appendChild(t);
    return m;
  }

  /* ---------- project: summary ---------- */
  function viewSummary(p) {
    var m = el('div'); m.id = 'view-summary';
    m.appendChild(el('h2', null, 'project summary \u2014 .devin/state.json'));
    m.appendChild(cueStrip(p));
    if (!p.state_present) { m.appendChild(gap('.devin/state.json is missing \u2014 every state-derived field below is a gap, not a default')); }
    else if (p.state_error) { m.appendChild(gap('.devin/state.json present but unparsed: ' + p.state_error)); }
    if (p.state) {
      var keys = ['line', 'prompt_ref', 'direction_in_force', 'builds', 'pending_owner_questions', 'revisions'];
      Object.keys(p.state).forEach(function (k) { if (keys.indexOf(k) < 0) keys.push(k); });
      m.appendChild(kvTable(p.state, keys));
      if (!('pending_owner_questions' in p.state)) m.appendChild(gap('pending_owner_questions key absent from state.json'));
    } else {
      m.appendChild(el('h3', null, 'fields that would render from state.json'));
      m.appendChild(kvTable({ line: null, prompt_ref: null, direction_in_force: null, builds: null, pending_owner_questions: null, revisions: null }));
    }
    if (p.status_files && Object.keys(p.status_files).length) {
      m.appendChild(el('h2', null, '.devin/last-*-status.txt (verbatim)'));
      Object.keys(p.status_files).forEach(function (n) {
        m.appendChild(el('h3', null, n));
        var d = el('div', 'status-file'); d.textContent = p.status_files[n];
        m.appendChild(d);
      });
    }
    return m;
  }

  /* ---------- project: direction ---------- */
  function viewDirection(p) {
    var m = el('div'); m.id = 'view-direction';
    m.appendChild(el('h2', null, 'direction — what governs the current cycle'));
    m.appendChild(cueStrip(p));
    var dif = (p.state && p.state.direction_in_force) || null;
    var docs = (p.register && p.register.docs) || [];
    var dirs = docs.filter(function (d) { return d.kind === 'direction'; }).sort(function (a, b) {
      return (+(/\d+/.exec(b.id) || [0])[0]) - (+(/\d+/.exec(a.id) || [0])[0]);
    });
    if (dif) {
      m.appendChild(kvTable({
        'in force': dif.ref || '— none (awaiting next direction)',
        clarity: dif.clarity, baseline: dif.baseline,
        'budget spent / total': dif.budget ? (dif.budget.spent + ' / ' + dif.budget.total) : null,
        criteria: dif.criteria,
        'last direction': dif.last_direction ? (dif.last_direction.ref + ' — ' + (dif.last_direction.clarity || '')) : null
      }));
    } else {
      m.appendChild(gap('no direction_in_force block in state.json'));
    }
    if (!dirs.length) { m.appendChild(gap('no direction docs in the register')); return m; }
    var featured = null;
    if (dif && dif.ref) featured = dirs.filter(function (d) { return d.file === dif.ref || d.id === String(dif.ref).replace(/\.md$/, ''); })[0];
    if (!featured) featured = dirs.filter(function (d) { return ['proposed', 'draft', 'approved'].indexOf(d.status) >= 0; })[0];
    if (!featured) featured = dirs[0];
    var banner = 'featured: ' + featured.id + ' — status ' + featured.status;
    if (featured.status === 'proposed' || featured.status === 'draft') banner += ' — AWAITING OWNER APPROVAL';
    else if (featured.status === 'in-force') banner += ' — actively steering this cycle';
    var b = el('div', 'dir-banner ' + (featured.status === 'in-force' ? 'ok' : 'warn'), banner);
    m.appendChild(b);
    if (featured.body) { var body = el('div', 'doc-body'); body.innerHTML = mdToHtml(featured.body); m.appendChild(body); }
    if (dirs.length > 1) {
      m.appendChild(el('h3', null, 'all directions'));
      var t = el('table'), tr = el('tr');
      ['id', 'status', 'applies to', 'mapped into'].forEach(function (x) { tr.appendChild(el('th', null, x)); });
      t.appendChild(tr);
      dirs.forEach(function (d) {
        var r = el('tr');
        r.appendChild(el('td', 'mono', d.id));
        r.appendChild(el('td', null, d.status));
        r.appendChild(el('td', null, (d.applies_to || []).join(', ')));
        r.appendChild(el('td', null, (d.mapped_into || []).join(', ')));
        t.appendChild(r);
      });
      m.appendChild(t);
    }
    return m;
  }

  /* ---------- project: documents ---------- */
  function docStatusClass(s) {
    if (s === 'in-force') return 'ds-inforce';
    if (s === 'approved') return 'ds-approved';
    if (s === 'draft' || s === 'proposed') return 'ds-pending';
    if (s === 'unparsed') return 'ds-bad';
    return 'ds-terminal';
  }
  /* minimal markdown -> html: headings, tables, fences, lists, bold/code */
  function mdToHtml(md) {
    function esc(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
    function inline(s) {
      return esc(s).replace(/\*\*([^*]+)\*\*/g,'<b>$1</b>').replace(/`([^`]+)`/g,'<code>$1</code>');
    }
    var lines = String(md || '').split(/\r?\n/), html = '', i = 0;
    while (i < lines.length) {
      var ln = lines[i];
      if (/^\s*```/.test(ln)) {
        var buf = []; i++;
        while (i < lines.length && !/^\s*```/.test(lines[i])) { buf.push(lines[i]); i++; }
        i++;
        html += '<pre>' + esc(buf.join('\n')) + '</pre>';
        continue;
      }
      if (/^\s*\|/.test(ln)) {
        var rows = [];
        while (i < lines.length && /^\s*\|/.test(lines[i])) { rows.push(lines[i]); i++; }
        var t = '<table class="mdt">', headDone = false;
        rows.forEach(function (r) {
          var cells = r.replace(/^\s*\|/, '').replace(/\|\s*$/, '').split('|');
          var sep = cells.every(function (c) { return /^\s*:?-{2,}:?\s*$/.test(c); });
          if (sep) return;
          var tag = headDone ? 'td' : 'th';
          t += '<tr>' + cells.map(function (c) { return '<' + tag + '>' + inline(c.trim()) + '</' + tag + '>'; }).join('') + '</tr>';
          headDone = true;
        });
        html += t + '</table>';
        continue;
      }
      var mm = ln.match(/^(#{1,4})\s+(.*)/);
      if (mm) { var lv = Math.min(4, mm[1].length + 1); html += '<h' + lv + '>' + inline(mm[2]) + '</h' + lv + '>'; }
      else if (/^\s*---+\s*$/.test(ln)) html += '<hr>';
      else if (/^\s*$/.test(ln)) { /* spacing */ }
      else if (/^\s*[-*]\s+/.test(ln)) html += '<div class="mdli">&bull; ' + inline(ln.replace(/^\s*[-*]\s+/, '')) + '</div>';
      else if (/^\s*\d+\.\s+/.test(ln)) html += '<div class="mdli">' + inline(ln) + '</div>';
      else html += '<p>' + inline(ln) + '</p>';
      i++;
    }
    return html;
  }
  function docView(doc, open) {
    var det = el('details', 'doc-view');
    if (open) det.setAttribute('open', '');
    var sum = el('summary');
    sum.appendChild(el('span', 'mono', doc.id));
    sum.appendChild(document.createTextNode(' '));
    sum.appendChild(el('span', 'doc-status ' + docStatusClass(doc.status), doc.status || '?'));
    if (doc.provisional_ids) sum.appendChild(el('span', 'muted', ' · provisional ids'));
    if (doc.applies_to && doc.applies_to.length) sum.appendChild(el('span', 'muted', ' · ' + doc.applies_to.join(',')));
    sum.appendChild(el('span', 'muted', '  ' + doc.file));
    det.appendChild(sum);
    var body = el('div', 'doc-body');
    if (doc.body) body.innerHTML = mdToHtml(doc.body);
    else body.appendChild(absent('no body emitted'));
    det.appendChild(body);
    return det;
  }
  function viewDocuments(p) {
    var m = el('div'); m.id = 'view-documents';
    var reg = p.register || null;
    m.appendChild(el('h2', null, 'derivative documents — harness-doc register'));
    if (!reg || !reg.docs || !reg.docs.length) {
      m.appendChild(gap('no harness-doc headers found on top-level *.md — the register is empty (see workflow.md §Derivative documents)'));
      return m;
    }
    var docs = reg.docs;
    var pend = reg.pending || [], prov = reg.provisional_ids || [], inf = reg.in_force || [];

    // review queue — docs whose wording needs eyes: pending approval or provisional ids
    var queue = docs.filter(function (d) { return pend.indexOf(d.id) >= 0 || prov.indexOf(d.id) >= 0; });
    m.appendChild(el('h3', null, 'review queue — wording needs eyes (' + queue.length + ')'));
    if (!queue.length) m.appendChild(el('p', 'muted', 'empty — nothing awaiting approval or adoption review'));
    queue.forEach(function (d) {
      var open = pend.indexOf(d.id) >= 0;   // pending docs open expanded; provisional collapsed
      var v = docView(d, open);
      if (prov.indexOf(d.id) >= 0) {
        var tag = el('div', 'muted', 'provisional ids — approve wording before corpus adoption assigns real C-ids');
        v.insertBefore(tag, v.lastChild);
      }
      m.appendChild(v);
    });

    // in force
    m.appendChild(el('h3', null, 'in force (' + inf.length + ')'));
    if (inf.length) {
      var d = el('div', 'mono'); d.textContent = inf.join('  ');
      m.appendChild(d);
    } else m.appendChild(el('p', 'muted', 'nothing steering right now'));

    // current per kind
    if (reg.current && Object.keys(reg.current).length) {
      m.appendChild(el('h3', null, 'current per kind'));
      m.appendChild(kvTable(reg.current));
    }

    // full register — click a row to read the doc inline
    m.appendChild(el('h3', null, 'register (' + docs.length + ' docs) — click a row to read the doc'));
    var t = el('table', 'matrix');
    var tr = el('tr');
    ['id', 'kind', 'status', 'applies-to', 'mapped-into', 'file'].forEach(function (x) { tr.appendChild(el('th', null, x)); });
    t.appendChild(tr);
    var sorted = docs.slice().sort(function (a, b) {
      return (a.kind === b.kind ? String(a.id).localeCompare(String(b.id)) : String(a.kind).localeCompare(String(b.kind)));
    });
    sorted.forEach(function (doc) {
      var r = el('tr', 'doc-row');
      r.appendChild(el('td', 'rowh', doc.id));
      r.appendChild(el('td', null, doc.kind || '—'));
      var st = el('td', 'doc-status ' + docStatusClass(doc.status), doc.status || '?');
      if (doc.provisional_ids) st.title = 'provisional ids — pending corpus adoption';
      r.appendChild(st);
      r.appendChild(el('td', null, (doc.applies_to || []).join(', ') || '—'));
      r.appendChild(el('td', null, (doc.mapped_into || []).join(', ') || '—'));
      r.appendChild(el('td', 'mono', doc.file));
      r.addEventListener('click', function () {
        var next = r.nextSibling;
        if (next && next.className === 'doc-detail') { next.parentNode.removeChild(next); return; }
        var dr = el('tr', 'doc-detail');
        var td = el('td'); td.colSpan = 6;
        var body = el('div', 'doc-body');
        if (doc.body) body.innerHTML = mdToHtml(doc.body);
        else body.appendChild(absent('no body emitted'));
        td.appendChild(body);
        dr.appendChild(td);
        r.parentNode.insertBefore(dr, r.nextSibling);
      });
      t.appendChild(r);
    });
    m.appendChild(t);

    // unregistered
    var un = reg.headerless || [];
    if (un.length) {
      m.appendChild(gap(un.length + ' top-level *.md file(s) without a harness-doc header — unregistered: ' + un.join(', ')));
    }
    return m;
  }

  /* ---------- project: comparison ---------- */
  var PALETTE = ['#295d8f', '#b26a00', '#2e7d32', '#7b3294', '#b3261e', '#00838f', '#5d4037', '#c2185b', '#455a64', '#6d4c41', '#33691e', '#283593'];
  function critSeries(subset) {
    var names = [];
    subset.forEach(function (sp) {
      if (sp.verdict && sp.verdict.criteria) sp.verdict.criteria.forEach(function (c) {
        if (names.indexOf(c.name) < 0) names.push(c.name);
      });
    });
    return names;
  }
  function scoreOf(sp, name) {
    if (!sp.verdict || !sp.verdict.criteria) return null;
    for (var i = 0; i < sp.verdict.criteria.length; i++)
      if (sp.verdict.criteria[i].name === name) return sp.verdict.criteria[i];
    return null;
  }
  function scenCell(sp, id) {
    if (!sp.verdict || !sp.verdict.scenarios) return null;
    for (var i = 0; i < sp.verdict.scenarios.length; i++)
      if (sp.verdict.scenarios[i].id === id) return sp.verdict.scenarios[i];
    return null;
  }
  function viewComparison(p) {
    var m = el('div'); m.id = 'view-comparison';
    var series = p.series || [];
    m.appendChild(el('h2', null, 'criteria over cycles'));
    if (!series.length) { m.appendChild(gap('no verdict JSON parsed from devlog.md or .devin/jev-*.out \u2014 nothing to chart')); }
    else {
      // depth picker anchored at the latest run
      var bar = el('div', 'depthbar');
      bar.appendChild(el('span', null, 'show last '));
      var sel = el('select');
      var opts = [3, 5, 10, series.length].filter(function (v, i, a) { return v > 0 && v <= series.length && a.indexOf(v) === i; });
      opts.sort(function (a, b) { return a - b; });
      opts.forEach(function (n) { var o = el('option', null, n === series.length ? n + ' (all)' : String(n)); o.value = String(n); sel.appendChild(o); });
      sel.value = String(state.depth || series.length);
      sel.addEventListener('change', function () { state.depth = +sel.value; render(); });
      bar.appendChild(sel);
      bar.appendChild(el('span', 'muted', ' of ' + series.length + ' verdicts \u2014 anchored at the latest run'));
      m.appendChild(bar);
      var n = +sel.value, subset = series.slice(Math.max(0, series.length - n));
      m.appendChild(chart(subset));
      m.appendChild(legend(critSeries(subset)));
      m.appendChild(el('h2', null, 'scenarios \u2014 id \u00d7 cycle (score \u00b7 evidence class)'));
      m.appendChild(matrixScenarios(p, subset));
      m.appendChild(el('h2', null, 'conventions \u2014 id \u00d7 build (disposition on record)'));
      m.appendChild(matrixConventions(p));
    }
    return m;
  }
  function chart(subset) {
    var W = 780, H = 260, PL = 36, PB = 46, PT = 10, PR = 8;
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', W); svg.setAttribute('height', H);
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    svg.id = 'criteria-chart';
    var iw = W - PL - PR, ih = H - PT - PB;
    var names = critSeries(subset);
    function X(i) { return PL + (subset.length <= 1 ? iw / 2 : (i / (subset.length - 1)) * iw); }
    function Y(v) { return PT + (1 - v) * ih; }
    for (var g = 0; g <= 4; g++) {
      var y = PT + g * ih / 4;
      var ln = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      ln.setAttribute('x1', PL); ln.setAttribute('x2', W - PR);
      ln.setAttribute('y1', y); ln.setAttribute('y2', y);
      ln.setAttribute('stroke', '#d8d8d0');
      svg.appendChild(ln);
      var lbl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      lbl.setAttribute('x', 4); lbl.setAttribute('y', y + 4);
      lbl.setAttribute('font-size', '10'); lbl.setAttribute('fill', '#6b6b64');
      lbl.textContent = (1 - g / 4).toFixed(2);
      svg.appendChild(lbl);
    }
    names.forEach(function (nm, ci) {
      var pts = [];
      subset.forEach(function (sp, i) {
        var c = scoreOf(sp, nm);
        if (c && c.score !== null && c.score !== undefined) pts.push({ i: i, v: c.score, sp: sp, c: c });
      });
      var color = PALETTE[ci % PALETTE.length];
      var prev = null;
      pts.forEach(function (pt) {
        if (prev) { // sparse: connect consecutive *present* points only if adjacent columns? spec: sparse line \u2014 connect across gaps is fine per "one colored line per criterion, sparse (no point where a cycle wasn't scored)"
          var pl = document.createElementNS('http://www.w3.org/2000/svg', 'line');
          pl.setAttribute('x1', X(prev.i)); pl.setAttribute('x2', X(pt.i));
          pl.setAttribute('y1', Y(prev.v)); pl.setAttribute('y2', Y(pt.v));
          pl.setAttribute('stroke', color); pl.setAttribute('stroke-width', '1.6');
          svg.appendChild(pl);
        }
        prev = pt;
      });
      pts.forEach(function (pt) {
        var c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        c.setAttribute('cx', X(pt.i)); c.setAttribute('cy', Y(pt.v));
        c.setAttribute('r', '4.5'); c.setAttribute('fill', color);
        c.setAttribute('class', 'point');
        c.setAttribute('data-label', pt.sp.label);
        var ti = document.createElementNS('http://www.w3.org/2000/svg', 'title');
        ti.textContent = pt.sp.label + ' \u00b7 ' + nm + ' = ' + pt.v +
          (pt.c.user_opinion !== null && pt.c.user_opinion !== undefined ? ' (owner ' + pt.c.user_opinion + ')' : '');
        c.appendChild(ti);
        c.addEventListener('click', (function (sp) { return function () { openBuildDetail(sp); }; })(pt.sp));
        svg.appendChild(c);
      });
    });
    subset.forEach(function (sp, i) {
      var lbl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      lbl.setAttribute('x', X(i)); lbl.setAttribute('y', H - PB + 14);
      lbl.setAttribute('font-size', '10'); lbl.setAttribute('fill', '#1c1c1a');
      lbl.setAttribute('text-anchor', 'end');
      lbl.setAttribute('transform', 'rotate(-35 ' + X(i) + ' ' + (H - PB + 14) + ')');
      lbl.textContent = sp.label;
      svg.appendChild(lbl);
    });
    return svg;
  }
  function legend(names) {
    var d = el('div', 'legend');
    names.forEach(function (nm, i) {
      var s = el('span');
      var sw = el('span', 'sw'); sw.style.background = PALETTE[i % PALETTE.length];
      s.appendChild(sw); s.appendChild(document.createTextNode(nm));
      d.appendChild(s);
    });
    return d;
  }
  function matrixScenarios(p, subset) {
    var t = el('table', 'matrix'); t.id = 'matrix-scenarios';
    var tr = el('tr'); tr.appendChild(el('th', 'rowh', 'scenario'));
    subset.forEach(function (sp) { tr.appendChild(el('th', null, sp.label)); });
    t.appendChild(tr);
    if (!p.suite || !p.suite.length) {
      var e = el('tr'); var td = el('td'); td.colSpan = subset.length + 1;
      td.appendChild(gap('no scenario suite parsed (.devin/scenarios.md missing or empty)'));
      e.appendChild(td); t.appendChild(e); return t;
    }
    var cells = 0, filled = 0;
    p.suite.forEach(function (s) {
      var r = el('tr');
      var h = el('td', 'rowh', s.id); h.title = s.title || '';
      r.appendChild(h);
      subset.forEach(function (sp) {
        cells++;
        var td = el('td');
        var sc = scenCell(sp, s.id);
        if (!sc || sc.score === null || sc.score === undefined) {
          td.className = 'cell-gap'; td.textContent = '\u2014';
          td.title = 'not assessed in ' + sp.label + ' \u2014 visible gap';
        } else {
          filled++;
          var v = sc.score;
          td.style.background = 'rgba(46,125,50,' + (0.15 + 0.75 * v) + ')';
          td.textContent = v.toFixed(2).replace(/0+$/, '').replace(/\.$/, '') +
            (sc.evidence_class === 'enactment' ? ' E' : sc.evidence_class === 'repository' ? ' R' : '');
          td.title = (sc.evidence_class || 'unclassed') + (sc.notes ? ' \u2014 ' + sc.notes : '');
        }
        r.appendChild(td);
      });
      t.appendChild(r);
    });
    t.setAttribute('data-cells', String(cells));
    t.setAttribute('data-filled', String(filled));
    return t;
  }
  function matrixConventions(p) {
    var t = el('table', 'matrix'); t.id = 'matrix-conventions';
    var tr = el('tr'); tr.appendChild(el('th', 'rowh', 'convention'));
    var builds = p.builds || [];
    builds.forEach(function (b) { tr.appendChild(el('th', null, b.folder.replace(/^version /, 'v'))); });
    t.appendChild(tr);
    if (!p.convention_ids || !p.convention_ids.length) {
      var e = el('tr'); var td = el('td'); td.colSpan = builds.length + 1;
      td.appendChild(gap('no convention id set derivable (no corpus CONVENTIONS.md, no FEATURES.md tables, no verdict conventions arrays)'));
      e.appendChild(td); t.appendChild(e); return t;
    }
    if (!builds.length) {
      var e2 = el('tr'); var td2 = el('td'); td2.colSpan = 1;
      td2.appendChild(gap('no version folders \u2014 conventions cannot be assessed per build'));
      e2.appendChild(td2); t.appendChild(e2);
    }
    var cells = 0, gaps = 0;
    p.convention_ids.forEach(function (cid) {
      var r = el('tr');
      r.appendChild(el('td', 'rowh', cid));
      builds.forEach(function (b) {
        cells++;
        var td = el('td');
        var rec = b.conventions && b.conventions[cid];
        if (!rec) { td.className = 'cell-gap'; td.textContent = '\u2014'; td.title = 'not assessed in ' + b.folder + ' \u2014 visible gap'; gaps++; }
        else if (rec.status === 'conformed') { td.className = 'cell-conformed'; td.textContent = 'conform'; }
        else if (rec.status === 'reckoned-departure') { td.className = 'cell-reckoned'; td.textContent = 'departure\u00b7recorded'; }
        else if (rec.status === 'silent-departure') { td.className = 'cell-silent'; td.textContent = 'silent departure'; }
        else { td.className = 'cell-na'; td.textContent = rec.disposition || 'recorded'; }
        td.title = b.folder + ': ' + (rec ? rec.disposition : 'not assessed');
        r.appendChild(td);
      });
      t.appendChild(r);
    });
    t.setAttribute('data-cells', String(cells));
    t.setAttribute('data-gaps', String(gaps));
    return t;
  }

  /* ---------- project: current state ---------- */
  function viewCurrent(p) {
    var m = el('div'); m.id = 'view-current';
    var cs = p.current_state || {};
    m.appendChild(el('h2', null, 'current state \u2014 live read, what the next cycle would be judged under'));
    var t = el('table', 'kv');
    function row(k, node) { var tr = el('tr'); tr.appendChild(el('th', null, k)); var td = el('td'); td.appendChild(node); tr.appendChild(td); t.appendChild(tr); }
    row('prompt.md declared revision', cs.prompt_declared_revision ? el('span', null, cs.prompt_declared_revision) : absent('no revision marker in prompt.md'));
    row('corpus prompt file', cs.corpus_prompt_file ? el('span', 'mono', cs.corpus_prompt_file) : absent('no corpus path derivable from prompt.md'));
    row('corpus prompt mtime (live)', cs.corpus_prompt_mtime ? el('span', null, cs.corpus_prompt_mtime) : absent());
    var rev = cs.state_revisions || null;
    row('state.json revisions (snapshot)', rev ? renderAny(rev) : absent(p.state_present ? 'revisions key absent' : 'no state.json'));
    m.appendChild(t);

    m.appendChild(el('h3', null, 'live scenario id set \u2014 .devin/scenarios.md (' + (cs.live_scenario_ids ? cs.live_scenario_ids.length : 0) + ' ids)'));
    if (cs.live_scenario_ids && cs.live_scenario_ids.length) {
      var d = el('div', 'mono'); d.textContent = cs.live_scenario_ids.join('  ');
      m.appendChild(d);
    } else m.appendChild(gap('no live scenario suite parsed'));

    m.appendChild(el('h3', null, 'pathed scenarios \u2014 build guidance (live read of scenarios.md ## Paths; not scored)'));
    m.appendChild(pathsBlock(p));

    m.appendChild(el('h3', null, 'live convention id set' + (cs.corpus_conventions_file ? ' \u2014 ' + cs.corpus_conventions_file + ' (' + (cs.corpus_convention_ids || []).length + ' ids)' : '')));
    if (cs.corpus_convention_ids && cs.corpus_convention_ids.length) {
      var d2 = el('div', 'mono'); d2.textContent = cs.corpus_convention_ids.join('  ');
      m.appendChild(d2);
      if (cs.corpus_conventions_source === 'corpusroot-param')
        m.appendChild(el('p', 'muted', 'located via -CorpusRoot parameter (not derived from prompt.md)'));
    } else {
      m.appendChild(gap('no conventions corpus derivable \u2014 this line has no live convention id set'));
    }

    m.appendChild(el('h3', null, 'coverage \u2014 live ids vs last verdict'));
    var lastSp = null;
    (p.series || []).forEach(function (sp) { if (sp.verdict_ok) lastSp = sp; });
    if (!lastSp) m.appendChild(gap('no parsed verdict \u2014 nothing assessed'));
    else {
      var scored = {};
      (lastSp.verdict.scenarios || []).forEach(function (s) { scored[s.id] = true; });
      var unassessed = (cs.live_scenario_ids || []).filter(function (id) { return !scored[id]; });
      var tx = el('p');
      tx.appendChild(el('span', null, 'last verdict ' + lastSp.label + ' assessed ' + Object.keys(scored).length + ' scenario id(s); '));
      if (unassessed.length)
        tx.appendChild(el('span', 'absent', unassessed.length + ' live id(s) not yet assessed: ' + unassessed.join(', ')));
      else tx.appendChild(el('span', null, 'every live scenario id was assessed'));
      m.appendChild(tx);
    }
    return m;
  }

  /* ---------- project: build detail ---------- */
  function viewBuildDetail(p) {
    var m = el('div'); m.id = 'view-builddetail';
    m.appendChild(el('h2', null, 'build detail'));
    var series = p.series || [];
    if (!series.length && !(p.builds || []).length) { m.appendChild(gap('no builds and no verdicts recorded')); return m; }
    var bar = el('div', 'depthbar');
    bar.appendChild(el('span', null, 'verdict: '));
    var sel = el('select');
    if (!series.length) { var o0 = el('option', null, '(none parsed)'); sel.appendChild(o0); sel.disabled = true; }
    series.forEach(function (sp, i) {
      var o = el('option', null, sp.label + ' \u2014 ' + sp.entry + (sp.verdict_ok ? '' : ' (unparsed block)'));
      o.value = String(i); sel.appendChild(o);
    });
    if (state.selPoint >= 0 && state.selPoint < series.length) sel.value = String(state.selPoint);
    sel.addEventListener('change', function () { state.selPoint = +sel.value; render(); });
    bar.appendChild(sel);
    m.appendChild(bar);
    if (!series.length) return m;
    var i = sel.selectedIndex >= 0 ? +sel.value : series.length - 1;
    var sp = series[i];
    state.selPoint = i;

    var t = el('table', 'kv');
    function row(k, node) { var tr = el('tr'); tr.appendChild(el('th', null, k)); var td = el('td'); td.appendChild(node); tr.appendChild(td); t.appendChild(tr); }
    row('entry', el('span', null, sp.entry));
    row('date', sp.date ? el('span', null, sp.date) : absent('no date in entry heading'));
    row('time to implement', sp.time_to_implement ? el('span', null, sp.time_to_implement) : absent());
    row('direction', sp.direction ? el('span', null, sp.direction) : absent());
    row('baseline', sp.baseline ? el('span', null, sp.baseline) : absent());
    row('criteria', sp.criteria ? el('span', null, sp.criteria) : absent());
    row('build folder', sp.build_folder ? el('span', 'mono', sp.build_folder) : absent('no version folder named in Result'));
    // launch pointer \u2014 wired only for the most recent run
    var lp = el('td');
    var b = null;
    (p.builds || []).forEach(function (x) { if (x.folder === sp.build_folder) b = x; });
    if (!sp.build_folder) lp.appendChild(absent('no build associated with this verdict'));
    else if (!b) lp.appendChild(absent('build folder ' + sp.build_folder + ' not found on disk'));
    else if (sp.build_folder !== p.latest_build) lp.appendChild(absent('stale \u2014 launch pointer wired only for the most recent run (' + p.latest_build + ')'));
    else if (!b.launcher) lp.appendChild(absent('latest build, but no launcher artifact found inside it'));
    else {
      var a = el('a', null, '../' + sp.build_folder + '/' + b.launcher);
      a.href = encodeURI('../' + sp.build_folder + '/' + b.launcher);
      lp.appendChild(a);
      lp.appendChild(el('span', 'muted', '  (resolves \u2014 most recent run)'));
    }
    var ltr = el('tr'); ltr.appendChild(el('th', null, 'launch pointer')); ltr.appendChild(lp); t.appendChild(ltr);
    m.appendChild(t);

    m.appendChild(el('h3', null, 'verdict JSON (' + (sp.source || 'devlog.md') + (sp.verdict_ok ? '' : ' \u2014 UNPARSED') + ')'));
    if (sp.verdict_ok && sp.verdict) {
      var pre = el('pre'); pre.textContent = JSON.stringify(sp.verdict, null, 2);
      m.appendChild(pre);
    } else {
      m.appendChild(gap('verdict block present but could not be parsed as JSON' + (sp.verdict_error ? ': ' + sp.verdict_error : '')));
    }

    var cites = [];
    if (sp.verdict && sp.verdict.criteria) sp.verdict.criteria.forEach(function (c) {
      (c.evidence || []).forEach(function (e) { cites.push(c.name + ' \u2192 ' + e); });
    });
    if (sp.verdict && sp.verdict.scenarios) sp.verdict.scenarios.forEach(function (s) {
      (s.evidence || []).forEach(function (e) { cites.push(s.id + ' \u2192 ' + e); });
    });
    m.appendChild(el('h3', null, 'evidence citations (' + cites.length + ')'));
    if (cites.length) {
      var ul = el('ul', 'cite');
      cites.forEach(function (c) { var li = el('li'); li.textContent = c; ul.appendChild(li); });
      m.appendChild(ul);
    } else m.appendChild(gap('this verdict carries no evidence citations'));
    if (sp.result) {
      m.appendChild(el('h3', null, 'result (devlog excerpt)'));
      var d = el('p', 'muted'); d.textContent = sp.result;
      m.appendChild(d);
    }
    return m;
  }

  /* ---------- pathed scenarios (P-*) — build guidance, not scored ---------- */
  function pathsData(p) { return (p && p.paths) || (p && p.current_state && p.current_state.paths) || null; }
  function pathsBlock(p) {
    var wrap = el('div');
    var pd = pathsData(p);
    if (!pd || !pd.n_paths) { wrap.appendChild(gap('no pathed scenarios declared')); return wrap; }
    wrap.appendChild(el('p', 'muted',
      pd.n_paths + ' paths \u00b7 consolidated ' + pd.consolidated + '/' + pd.suite_n +
      ' scenarios \u00b7 ' + pd.unconsolidated.length + ' unconsolidated \u00b7 ' +
      pd.undeclared_items.length + ' undeclared items \u00b7 ' + pd.unreachable_modules.length + ' unreachable modules'));
    var pt = el('table');
    var ph = el('tr');
    ['path','journey','steps','enacts'].forEach(function (h) { ph.appendChild(el('th', null, h)); });
    pt.appendChild(ph);
    pd.declared.forEach(function (pp) {
      var tr = el('tr');
      tr.appendChild(el('td', 'mono', pp.id));
      var jd = el('td', 'muted'); jd.textContent = pp.journey || ''; tr.appendChild(jd);
      var sd = el('td', 'mono'); sd.textContent = (pp.steps || []).join(' \u2192 '); tr.appendChild(sd);
      var en = el('td', 'mono'); en.textContent = (pp.enacts || []).join(', '); tr.appendChild(en);
      pt.appendChild(tr);
    });
    wrap.appendChild(pt);
    var gapList = function (title, items, fmt) {
      if (!items.length) return;
      wrap.appendChild(el('h4', null, title + ' (' + items.length + ')'));
      var ul = el('ul', 'cite');
      items.forEach(function (x) { var li = el('li'); li.textContent = fmt ? fmt(x) : x; ul.appendChild(li); });
      wrap.appendChild(ul);
    };
    gapList('unconsolidated scenarios (tolerated gap signs)', pd.unconsolidated);
    gapList('undeclared interface items', pd.undeclared_items, function (u) { return u.item + ' in ' + u.path + ' (' + u.kind + ')'; });
    gapList('unknown scenario refs', pd.unknown_refs);
    gapList('unreachable module obligations', pd.unreachable_modules);
    return wrap;
  }

  /* ---------- project: scorecard (latest JEV verdict) ---------- */
  function scoreCell(v) {
    if (v === null || v === undefined || isNaN(+v)) return 'cell-na';
    var n = +v;
    if (n >= 0.8) return 'cell-conformed';
    if (n >= 0.5) return 'cell-reckoned';
    return 'cell-silent';
  }
  function viewScorecard(p) {
    var m = el('div'); m.id = 'view-scorecard';
    var lastSp = null, series = p.series || [];
    series.forEach(function (sp) { if (sp.verdict_ok) lastSp = sp; });
    if (!lastSp) { m.appendChild(el('h2', null, 'scorecard')); m.appendChild(gap('no parsed verdict yet')); return m; }
    var v = lastSp.verdict || {};

    m.appendChild(el('h2', null, 'scorecard \u2014 ' + lastSp.label + ' (' + (lastSp.entry || '') + ')'));
    var hdr = el('table', 'kv');
    function row(t, k, node) { var tr = el('tr'); tr.appendChild(el('th', null, k)); var td = el('td'); td.appendChild(node); tr.appendChild(td); t.appendChild(tr); }
    var ov = el('span'); ov.className = scoreCell(v.overall); ov.style.fontWeight = '700'; ov.style.padding = '1px 6px';
    ov.textContent = (v.overall !== null && v.overall !== undefined) ? v.overall : '\u2014';
    row(hdr, 'overall', ov);
    row(hdr, 'judge', el('span', null, (v.judge_model || '\u2014') + (lastSp.verdict_kind ? ' \u00b7 ' + lastSp.verdict_kind : '')));
    row(hdr, 'date', lastSp.date ? el('span', null, lastSp.date) : absent());
    row(hdr, 'direction', lastSp.direction ? el('span', null, lastSp.direction) : absent());
    row(hdr, 'build folder', lastSp.build_folder ? el('span', 'mono', lastSp.build_folder) : absent());
    var met = v.metrics || {}, mk = Object.keys(met);
    row(hdr, 'metrics', mk.length ? renderAny(met) : absent());
    m.appendChild(hdr);

    var crit = v.criteria || [];
    m.appendChild(el('h3', null, 'criteria (' + crit.length + ')'));
    if (!crit.length) m.appendChild(gap('verdict carries no criteria'));
    else {
      function catOf(c) { var k = c.category || 'measured'; return (k === 'objective') ? 'measured' : (k === 'exploratory') ? 'evaluated' : k; }
      var kinds = ['measured', 'evaluated', 'user'];
      var groups = kinds.map(function (k) { return [k, crit.filter(function (c) { return catOf(c) === k; })]; })
                        .filter(function (g) { return g[1].length; });
      if (!groups.length) groups = [['criteria', crit]];
      groups.forEach(function (g) {
        m.appendChild(el('h4', null, g[0] + ' (' + g[1].length + ')'));
        var ct = el('table');
        var htr = el('tr');
        var heads = (g[0] === 'measured') ? ['criterion','measure','method','score','owner','evidence']
                  : (g[0] === 'evaluated') ? ['criterion','score','confidence','owner','evidence']
                  : ['criterion','score','owner','evidence'];
        heads.forEach(function (h) { htr.appendChild(el('th', null, h)); });
        ct.appendChild(htr);
        g[1].forEach(function (c) {
          var tr = el('tr');
          tr.appendChild(el('td', null, c.name));
          if (g[0] === 'measured') {
            tr.appendChild(el('td', 'mono', c.measure || '\u2014'));
            var mtd = el('td', 'muted'); mtd.textContent = c.method || ''; tr.appendChild(mtd);
          }
          tr.appendChild(el('td', scoreCell(c.score), (c.score === null || c.score === undefined) ? '\u2014' : c.score));
          if (g[0] === 'evaluated') tr.appendChild(el('td', null, (c.confidence === null || c.confidence === undefined) ? '\u2014' : c.confidence));
          var uo = (c.user_opinion === null || c.user_opinion === undefined) ? '\u2014' : c.user_opinion;
          tr.appendChild(el('td', (uo !== '\u2014' && +uo !== +c.score) ? 'cell-reckoned' : null, uo));
          var ev = el('td');
          var evs = c.evidence || [];
          if (!evs.length) { ev.appendChild(absent('no citations')); }
          else {
            var det = el('details'); var sum = el('summary', null, evs.length + ' citation(s)');
            det.appendChild(sum);
            var ul = el('ul', 'cite'); evs.forEach(function (e) { var li = el('li'); li.textContent = e; ul.appendChild(li); });
            det.appendChild(ul); ev.appendChild(det);
          }
          tr.appendChild(ev);
          ct.appendChild(tr);
        });
        m.appendChild(ct);
      });
    }

    var scen = v.scenarios || [];
    m.appendChild(el('h3', null, 'scenarios (' + scen.length + ')'));
    if (!scen.length) m.appendChild(gap('verdict carries no scenario scores'));
    else {
      var en = 0; scen.forEach(function (s) { if (s.evidence_class === 'enactment') en++; });
      m.appendChild(el('p', 'muted', en + '/' + scen.length + ' enactment-class'));
      var st = el('table');
      var shr = el('tr');
      ['id','score','class','notes','evidence'].forEach(function (h) { shr.appendChild(el('th', null, h)); });
      st.appendChild(shr);
      scen.forEach(function (s) {
        var tr = el('tr');
        tr.appendChild(el('td', 'mono', s.id));
        tr.appendChild(el('td', scoreCell(s.score), (s.score === null || s.score === undefined) ? '\u2014' : s.score));
        tr.appendChild(el('td', s.evidence_class === 'enactment' ? 'doc-inforce' : 'doc-pending', s.evidence_class || '\u2014'));
        var nt = el('td', 'muted'); nt.textContent = s.notes || ''; tr.appendChild(nt);
        var ev = el('td');
        var evs = s.evidence || [];
        if (!evs.length) { ev.appendChild(absent('none')); }
        else {
          var det = el('details'); det.appendChild(el('summary', null, evs.length + ''));
          var ul = el('ul', 'cite'); evs.forEach(function (e) { var li = el('li'); li.textContent = e; ul.appendChild(li); });
          det.appendChild(ul); ev.appendChild(det);
        }
        tr.appendChild(ev);
        st.appendChild(tr);
      });
      m.appendChild(st);
    }

    var uc = v.user_commentary || [];
    if (uc.length) {
      m.appendChild(el('h3', null, 'owner commentary (' + uc.length + ')'));
      var uul = el('ul', 'cite'); uc.forEach(function (c) { var li = el('li'); li.textContent = (typeof c === 'string') ? c : JSON.stringify(c); uul.appendChild(li); });
      m.appendChild(uul);
    }
    m.appendChild(el('h3', null, 'judge notes'));
    if (v.notes) { var pn = el('p', 'doc-body'); pn.style.whiteSpace = 'pre-wrap'; pn.textContent = v.notes; m.appendChild(pn); }
    else m.appendChild(gap('verdict carries no judge notes'));

    /* paths — pathed scenarios (P-*): build guidance, not scored rows */
    m.appendChild(el('h3', null, 'pathed scenarios \u2014 build guidance (interface coverage, gap signs)'));
    m.appendChild(pathsBlock(p));
    return m;
  }

  /* ---------- project shell ---------- */
  function renderProject(d) {
    var p = d.project;
    var m = el('main'); m.id = 'view-project';
    m.appendChild(el('p', 'meta',
      p.id + ' \u2014 ' + p.path + ' \u00b7 generated ' + d.generated_at + ' \u00b7 liveness age '));
    var ageSpan = el('span', 'mono'); ageSpan.setAttribute('data-age', 'project');
    ageSpan.textContent = age(p.liveness_seconds) || '\u2014';
    m.lastChild.appendChild(ageSpan);
    m.lastChild.appendChild(el('span', 'muted', ' (newest in-scope ' + (p.newest_path || 'none') + ')'));

    if (p.latest_build) {
      var lb = el('div', 'launchbar');
      lb.appendChild(launchButton(p.id, 'launch ' + p.latest_build));
      m.appendChild(lb);
    }

    var tabs = el('div', 'tabs');
    [['summary', 'project summary'], ['direction', 'direction'], ['documents', 'documents'], ['comparison', 'comparison'], ['scorecard', 'scorecard'], ['current', 'current state'], ['builddetail', 'build detail']].forEach(function (pair) {
      var b = el('button', state.tab === pair[0] ? 'active' : '', pair[1]);
      b.addEventListener('click', function () { state.tab = pair[0]; render(); });
      tabs.appendChild(b);
    });
    m.appendChild(tabs);
    var pane = el('div', 'pane');
    if (state.tab === 'direction') pane.appendChild(viewDirection(p));
    else if (state.tab === 'documents') pane.appendChild(viewDocuments(p));
    else if (state.tab === 'comparison') pane.appendChild(viewComparison(p));
    else if (state.tab === 'scorecard') pane.appendChild(viewScorecard(p));
    else if (state.tab === 'current') pane.appendChild(viewCurrent(p));
    else if (state.tab === 'builddetail') pane.appendChild(viewBuildDetail(p));
    else pane.appendChild(viewSummary(p));
    m.appendChild(pane);
    return m;
  }
  function openBuildDetail(sp) {
    var idx = (state.data.project.series || []).indexOf(sp);
    state.selPoint = idx;
    state.tab = 'builddetail';
    render();
  }

  function render() {
    var d = state.data;
    app.textContent = '';
    if (!d) {
      app.appendChild(header('no data'));
      var mn = el('main'); mn.appendChild(gap('window.HARNESS_DATA missing \u2014 data.js did not load or is empty'));
      app.appendChild(mn); return;
    }
    document.body.setAttribute('data-kind', d.kind);
    if (d.kind === 'fleet') {
      app.appendChild(header('fleet \u2014 ' + (d.root || '?')));
      app.appendChild(renderFleet(d));
    } else {
      app.appendChild(header('line \u2014 ' + (d.project ? d.project.id : '?')));
      app.appendChild(renderProject(d));
    }
    updateBadge();
  }
  render();
})();
