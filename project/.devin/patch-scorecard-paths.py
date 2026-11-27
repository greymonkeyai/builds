p = r"C:\builds\harness-ui\version 0.1.0.001\shell\harness.js"
t = open(p, encoding="utf-8").read()

old = """    m.appendChild(el('h3', null, 'judge notes'));
    if (v.notes) { var pn = el('p', 'doc-body'); pn.style.whiteSpace = 'pre-wrap'; pn.textContent = v.notes; m.appendChild(pn); }
    else m.appendChild(gap('verdict carries no judge notes'));
    return m;
  }"""
new = """    m.appendChild(el('h3', null, 'judge notes'));
    if (v.notes) { var pn = el('p', 'doc-body'); pn.style.whiteSpace = 'pre-wrap'; pn.textContent = v.notes; m.appendChild(pn); }
    else m.appendChild(gap('verdict carries no judge notes'));

    /* paths — interface coverage (pathed-scenarios.md gap signs) */
    var pd = (p && p.paths) ? p.paths : null;
    m.appendChild(el('h3', null, 'paths \\u2014 interface coverage'));
    if (!pd || !pd.n_paths) { m.appendChild(gap('no pathed scenarios declared')); }
    else {
      m.appendChild(el('p', 'muted',
        pd.n_paths + ' paths \\u00b7 consolidated ' + pd.consolidated + '/' + pd.suite_n +
        ' scenarios \\u00b7 ' + pd.unconsolidated.length + ' unconsolidated \\u00b7 ' +
        pd.undeclared_items.length + ' undeclared items \\u00b7 ' + pd.unreachable_modules.length + ' unreachable modules'));
      var pt = el('table');
      var ph = el('tr');
      ['path','journey','steps','enacts'].forEach(function (h) { ph.appendChild(el('th', null, h)); });
      pt.appendChild(ph);
      pd.declared.forEach(function (pp) {
        var tr = el('tr');
        tr.appendChild(el('td', 'mono', pp.id));
        var jd = el('td', 'muted'); jd.textContent = pp.journey || ''; tr.appendChild(jd);
        var sd = el('td', 'mono'); sd.textContent = (pp.steps || []).join(' \\u2192 '); tr.appendChild(sd);
        tr.appendChild(el('td', null, (pp.enacts || []).length + ''));
        pt.appendChild(tr);
      });
      m.appendChild(pt);
      var gapList = function (title, items, fmt) {
        if (!items.length) return;
        m.appendChild(el('h4', null, title + ' (' + items.length + ')'));
        var ul = el('ul', 'cite');
        items.forEach(function (x) { var li = el('li'); li.textContent = fmt ? fmt(x) : x; ul.appendChild(li); });
        m.appendChild(ul);
      };
      gapList('unconsolidated scenarios (tolerated gap signs)', pd.unconsolidated);
      gapList('undeclared interface items', pd.undeclared_items, function (u) { return u.item + ' in ' + u.path + ' (' + u.kind + ')'; });
      gapList('unknown scenario refs', pd.unknown_refs);
      gapList('unreachable module obligations', pd.unreachable_modules);
    }
    return m;
  }"""
assert old in t, "anchor not found"
open(p, "w", encoding="utf-8").write(t.replace(old, new, 1))
print("patched")
