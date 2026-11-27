p = r"C:\builds\harness-ui\version 0.1.0.001\shell\harness.js"
t = open(p, encoding="utf-8").read()

old = '''    var crit = v.criteria || [];
    m.appendChild(el('h3', null, 'criteria (' + crit.length + ')'));
    if (!crit.length) m.appendChild(gap('verdict carries no criteria'));
    else {
      var ct = el('table');
      var htr = el('tr');
      ['criterion','score','confidence','owner','evidence'].forEach(function (h) { htr.appendChild(el('th', null, h)); });
      ct.appendChild(htr);
      crit.forEach(function (c) {
        var tr = el('tr');
        tr.appendChild(el('td', null, c.name));
        var sc = el('td', scoreCell(c.score), (c.score === null || c.score === undefined) ? '\\u2014' : c.score);
        tr.appendChild(sc);
        tr.appendChild(el('td', null, (c.confidence === null || c.confidence === undefined) ? '\\u2014' : c.confidence));
        var uo = (c.user_opinion === null || c.user_opinion === undefined) ? '\\u2014' : c.user_opinion;
        var ucell = el('td', (uo !== '\\u2014' && +uo !== +c.score) ? 'cell-reckoned' : null, uo);
        tr.appendChild(ucell);
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
    }'''

new = '''    var crit = v.criteria || [];
    m.appendChild(el('h3', null, 'criteria (' + crit.length + ')'));
    if (!crit.length) m.appendChild(gap('verdict carries no criteria'));
    else {
      var obj = crit.filter(function (c) { return (c.category || 'objective') === 'objective'; });
      var exp = crit.filter(function (c) { return c.category === 'exploratory'; });
      var groups = (obj.length && exp.length) ? [['objective', obj], ['exploratory', exp]] : [['criteria', crit]];
      groups.forEach(function (g) {
        if (g[0] !== 'criteria') m.appendChild(el('h4', null, g[0] + ' (' + g[1].length + ')'));
        var ct = el('table');
        var htr = el('tr');
        var heads = (g[0] === 'objective') ? ['criterion','measure','method','score','owner','evidence'] : ['criterion','score','confidence','owner','evidence'];
        heads.forEach(function (h) { htr.appendChild(el('th', null, h)); });
        ct.appendChild(htr);
        g[1].forEach(function (c) {
          var tr = el('tr');
          tr.appendChild(el('td', null, c.name));
          if (g[0] === 'objective') {
            tr.appendChild(el('td', 'mono', c.measure || '\\u2014'));
            var mtd = el('td', 'muted'); mtd.textContent = c.method || ''; tr.appendChild(mtd);
          }
          tr.appendChild(el('td', scoreCell(c.score), (c.score === null || c.score === undefined) ? '\\u2014' : c.score));
          if (g[0] !== 'objective') tr.appendChild(el('td', null, (c.confidence === null || c.confidence === undefined) ? '\\u2014' : c.confidence));
          var uo = (c.user_opinion === null || c.user_opinion === undefined) ? '\\u2014' : c.user_opinion;
          tr.appendChild(el('td', (uo !== '\\u2014' && +uo !== +c.score) ? 'cell-reckoned' : null, uo));
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
    }'''

assert old in t, "anchor not found"
open(p, "w", encoding="utf-8").write(t.replace(old, new, 1))
print("patched")
