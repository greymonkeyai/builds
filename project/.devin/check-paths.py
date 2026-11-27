import json
t = open(r'C:\builds\project\display\data.js', encoding='utf-8').read()
i = t.index('"paths":')
d = 0
for k in range(i + 8, len(t)):
    if t[k] == '{': d += 1
    elif t[k] == '}':
        d -= 1
        if d == 0:
            end = k + 1
            break
obj = json.loads(t[i + 8:end])
print('n_paths:', obj['n_paths'], ' consolidated:', obj['consolidated'], '/', obj['suite_n'])
print('unconsolidated:', obj['unconsolidated'])
print('unknown_refs:', obj['unknown_refs'])
print('undeclared:')
for u in obj['undeclared_items']:
    print('  ', u)
print('unreachable:', obj['unreachable_modules'])
