import json
MAP = {'objective': 'measured', 'exploratory': 'evaluated'}
def patch(v):
    for c in v['criteria']:
        cat = c.get('category', 'measured')
        c['category'] = 'user' if c['name'] == 'user score' else MAP.get(cat, cat)
    return v
p = r'C:\builds\project\.devin\jev-cycle-007.verdict.json'
v = patch(json.load(open(p, encoding='utf-8')))
json.dump(v, open(p, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
d = r'C:\builds\project\devlog.md'
t = open(d, encoding='utf-8').read()
s = t.index('```json', t.index('session `iridescent-server`'))
b0 = t.index('\n', s) + 1
e = t.index('```', b0)
v2 = patch(json.loads(t[b0:e]))
open(d, 'w', encoding='utf-8').write(t[:b0] + json.dumps(v2, indent=2, ensure_ascii=False) + '\n' + t[e:])
print([(c['name'], c['category']) for c in v2['criteria']])
