p = r"C:\builds\harness-ui\version 0.1.0.001\shell\harness.js"
t = open(p, encoding="utf-8").read()

old = '''      var obj = crit.filter(function (c) { return (c.category || 'objective') === 'objective'; });
      var exp = crit.filter(function (c) { return c.category === 'exploratory'; });
      var groups = (obj.length && exp.length) ? [['objective', obj], ['exploratory', exp]] : [['criteria', crit]];
      groups.forEach(function (g) {
        if (g[0] !== 'criteria') m.appendChild(el('h4', null, g[0] + ' (' + g[1].length + ')'));
        var ct = el('table');
        var htr = el('tr');
        var heads = (g[0] === 'objective') ? ['criterion','measure','method','score','owner','evidence'] : ['criterion','score','confidence','owner','evidence'];'''

new = '''      function catOf(c) { var k = c.category || 'measured'; return (k === 'objective') ? 'measured' : (k === 'exploratory') ? 'evaluated' : k; }
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
                  : ['criterion','score','owner','evidence'];'''

assert old in t, "split anchor not found"
t = t.replace(old, new, 1)

old2 = """          if (g[0] === 'objective') {
            tr.appendChild(el('td', 'mono', c.measure || '\\u2014'));
            var mtd = el('td', 'muted'); mtd.textContent = c.method || ''; tr.appendChild(mtd);
          }
          tr.appendChild(el('td', scoreCell(c.score), (c.score === null || c.score === undefined) ? '\\u2014' : c.score));
          if (g[0] !== 'objective') tr.appendChild(el('td', null, (c.confidence === null || c.confidence === undefined) ? '\\u2014' : c.confidence));"""
new2 = """          if (g[0] === 'measured') {
            tr.appendChild(el('td', 'mono', c.measure || '\\u2014'));
            var mtd = el('td', 'muted'); mtd.textContent = c.method || ''; tr.appendChild(mtd);
          }
          tr.appendChild(el('td', scoreCell(c.score), (c.score === null || c.score === undefined) ? '\\u2014' : c.score));
          if (g[0] === 'evaluated') tr.appendChild(el('td', null, (c.confidence === null || c.confidence === undefined) ? '\\u2014' : c.confidence));"""
assert old2 in t, "row anchor not found"
t = t.replace(old2, new2, 1)
open(p, "w", encoding="utf-8").write(t)
print("patched")
