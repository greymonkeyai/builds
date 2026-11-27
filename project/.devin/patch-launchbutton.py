p = r'C:\builds\harness-ui\version 0.1.0.001\shell\harness.js'
s = open(p, encoding='utf-8').read()
start = s.index('launch service bridge')
start = s.rindex('/*', 0, start)
end = s.index('function renderFleet', start)
new = '''/* ---------- launch bridge ----------
     The page is static; launching a build's own launcher (launch.cmd etc.)
     goes through harness-display.pyw's pywebview API when the display runs
     as its own window, else launch-serve.py on localhost:8358, else a hint. */
  var LAUNCH_SVC = 'http://127.0.0.1:8358';
  function launchButton(projectId, label) {
    var wrap = el('span', 'launchwrap');
    var b = el('button', 'launchbtn', '\\u25B6 ' + (label || 'launch'));
    var note = el('span', 'muted');
    b.addEventListener('click', function (ev) {
      ev.stopPropagation();
      b.disabled = true;
      note.textContent = ' launching\\u2026';
      function done(j) {
        b.disabled = false;
        if (j && j.ok) note.textContent = ' ' + j.build + ' launched \\u2014 ' + String(j.launcher).split(/[\\\\/]/).pop() + ' (pid ' + j.pid + ')';
        else note.textContent = ' ' + ((j && j.error) || 'launch failed');
      }
      function fail() {
        b.disabled = false;
        note.textContent = ' no launch path \\u2014 run the display app (harness-display.pyw) or launch-serve.py on :8358, or run the build\\u2019s launch.cmd manually';
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

  '''
s = s[:start] + new + s[end:]
open(p, 'w', encoding='utf-8').write(s)
print('replaced block, new length', len(s))
