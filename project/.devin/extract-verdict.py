import json, re, sys
log = sys.argv[1]
text = []
for line in open(log, encoding='utf-8', errors='replace'):
    try:
        m = json.loads(line)
    except Exception:
        continue
    u = m.get('params', {}).get('update', {})
    if u.get('sessionUpdate') == 'agent_message_chunk':
        text.append(u.get('content', {}).get('text', ''))
full = ''.join(text)
open(log.replace('.acp.log', '.full.txt'), 'w', encoding='utf-8').write(full)
blocks = re.findall(r'```json\s*(\{.*?\})\s*```', full, re.S)
print('chunks:', len(text), 'json blocks:', len(blocks))
if blocks:
    v = blocks[-1]
    open(log.replace('.acp.log', '.verdict.json'), 'w', encoding='utf-8').write(v)
    j = json.loads(v)
    print('overall:', j.get('overall'), '| criteria:', len(j.get('criteria', [])), '| scenarios:', len(j.get('scenarios', [])))
