"""final.py PACKDIR OUT.webp [quality]: the shipped MiniMax atlas — cell 0 = the home, every gesture's cells after it,
identical cells stored once; prints the manifest entry for phone.js."""
import json, sys, os
import numpy as np
from PIL import Image
pk, out = sys.argv[1], sys.argv[2]; q = int(sys.argv[3]) if len(sys.argv) > 3 else 70
m = json.load(open(pk + '/atlas.json')); A = np.asarray(Image.open(pk + '/atlas.png')); W, H = m['cell']
get = lambda i: A[(i // m['cols']) * H:(i // m['cols'] + 1) * H, (i % m['cols']) * W:(i % m['cols'] + 1) * W]
uniq, gs = [get(m['gestures'][0]['at'])], []
for g in m['gestures']:
    seq = []
    for k in range(g['frames']):
        f = get(g['at'] + k)
        j = next((u for u, x in enumerate(uniq) if np.array_equal(x, f)), -1)
        if j < 0: uniq.append(f); j = len(uniq) - 1
        seq.append(j)
    assert seq[0] == 0 and seq[-1] == 0, (g['name'], seq[:2], seq[-2:])
    gs.append({'name': g['name'], 'seq': seq})
cols = 8; rows = (len(uniq) + cols - 1) // cols
at = Image.new('RGBA', (cols * W, rows * H))
for i, f in enumerate(uniq): at.paste(Image.fromarray(f), ((i % cols) * W, (i // cols) * H))
at.save(out, 'WEBP', quality=q, method=6, alpha_quality=90)
at.save(os.path.splitext(out)[0] + '.png')
man = {'cell': [W, H], 'box': m['box'], 'cols': cols, 'count': len(uniq), 'gestures': gs}
json.dump(man, open(os.path.splitext(out)[0] + '.json', 'w'), indent=1)
print(at.size, len(uniq), 'cells', os.path.getsize(out), 'bytes')
for g in gs: print(g['name'], json.dumps(g['seq']).replace(' ', ''))
