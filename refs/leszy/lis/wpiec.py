"""wpiec.py DIR [OUT] — paski z buduj.py (DIR/wynik.json + DIR/<nazwa>.png) → klasa-7/leszy/lis: WebP, lis.json, lis.js.
Zostawia z dotychczasowego lis.json pozy patrzy-w-gore, od-tylu, z-gory (rysowane); pozy.stoi = klatka 0 nowego oddechu
(od niej P.lis bierze wysokość odniesienia, więc musi mieć tę samą skalę co paski)."""
import json, sys, os, base64, io
import numpy as np
from PIL import Image

D = sys.argv[1]; OUT = sys.argv[2] if len(sys.argv) > 2 else '/home/user/MathGames/klasa-7/leszy/lis'
Q = int(os.environ.get('Q', 82))
W = json.load(open(f'{D}/wynik.json'))
stary = json.load(open(f'{OUT}/lis.json'))

DODATKI = {   # pola v2 czytane przez P.lis; krok = px drogi na cykl przy stojącym lisie = 300 px (zmierzone z kroku stopy)
 'stoi':             dict(przenikanie=0.3, uwaga='oddech w miejscu, lampka w łapie (wideo H3, ping-pong)'),
 'chod':             dict(krok=174, przenikanie=0, uwaga='spokojny krok w miejscu, lampka trzymana z przodu (wideo H3, pełen cykl 2 kroków, szew przenikany)'),
 'bieg':             dict(krok=421, przenikanie=0, uwaga='ucieczka, płaszcz łopocze; lampka chwilami za ciałem (wtedy lampka = położenie interpolowane)'),
 'obejrzenie-sie':   dict(przenikanie=0.3, uwaga='odwraca głowę ku widzowi / do tyłu i wraca (ok. 0,3–0,7 s = patrzy)'),
 'podnosi-lampke':   dict(przenikanie=0.5, uwaga='lampka od pasa w górę nad głowę; ostatnia klatka = trzymanie (podniesienie 0…1 → klatka)'),
 'pisze-pazurem':    dict(przenikanie=0.5, loopFrom=6, uwaga='sięga łapą (0–5), potem pętla drapania klatek 6–16 (loopFrom 6); lampka w drugiej łapie'),
 'kucniecie':        dict(przenikanie=0.3, nastepna='kucniecie-oddech', uwaga='stanie → skulenie (0,67 s); po końcu graj kucniecie-oddech'),
 'kucniecie-oddech': dict(przenikanie=0.4, uwaga='skulony oddech (pętla), lampka przy ziemi'),
}
PRZYC = {'pisze-pazurem': 17}   # ile klatek zostawić (koniec pętli dobrany po IoU z klatką loopFrom)


def webp(im):
    b = io.BytesIO(); im.save(b, 'WEBP', quality=Q, method=6, alpha_quality=80); return b.getvalue()


anim = {}
for n, e in W.items():
    strip = Image.open(f'{D}/{n}.png').convert('RGBA'); k = e['klatki']; lam = e['lampka']
    if n in PRZYC:
        k = PRZYC[n]; strip = strip.crop((0, 0, k * e['w'], e['h'])); lam = lam[:k]
    data = webp(strip); open(f'{OUT}/{n}.webp', 'wb').write(data)
    anim[n] = dict(plik=f'{n}.webp', klatki=k, fps=e['fps'], w=e['w'], h=e['h'], pivot=[float(v) for v in e['pivot']],
                   petla=e['petla'], lampka=lam, **DODATKI.get(n, {}), zrodlo='MiniMax-H3 ' + e['zrodlo'])
    print(f'{n:17s} {k:3d} kl. {e["fps"]} fps {e["w"]}×{e["h"]}  {len(data) // 1024} KB')

# pozy: stoi = pierwsza klatka oddechu (przycięta), reszta bez zmian
e = W['stoi']; s = Image.open(f'{D}/stoi.png').convert('RGBA').crop((0, 0, e['w'], e['h']))
bb = s.getbbox(); pad = 2
c = Image.new('RGBA', (bb[2] - bb[0] + 2 * pad, e['h'] - bb[1] + pad)); c.alpha_composite(s.crop((bb[0], bb[1], bb[2], e['h'])), (pad, pad))
open(f'{OUT}/stoi-poza.webp', 'wb').write(webp(c))
pozy = dict(stary['pozy'])
pozy['stoi'] = dict(plik='stoi-poza.webp', w=c.width, h=c.height, pivot=[round(e['pivot'][0] - bb[0] + pad, 1), round(e['pivot'][1] - bb[1] + pad, 1)],
                    lampka=[round(e['lampka'][0][0] - bb[0] + pad, 1), round(e['lampka'][0][1] - bb[1] + pad, 1)],
                    uwaga='klatka 0 animacji stoi (wysokość odniesienia dla wszystkich pasków)')
for p in pozy.values(): p.pop('src', None)
man = {'version': 2, 'opis': stary['opis'] + ' v3: animacje z wideo MiniMax-H3 (wzorzec + manekin), 12–24 fps.',
       'animacje': anim, 'pozy': pozy}
json.dump(man, open(f'{OUT}/lis.json', 'w'), ensure_ascii=False, indent=1)
js = json.loads(json.dumps(man))
for grp in ('animacje', 'pozy'):
    for n, x in js[grp].items():
        x['src'] = 'data:image/webp;base64,' + base64.b64encode(open(f"{OUT}/{x['plik']}", 'rb').read()).decode()
body = json.dumps(js, ensure_ascii=False, separators=(',', ':'))
open(f'{OUT}/lis.js', 'w').write('/* Lis-wędrowiec — paski klatek (WebP z alfą jako data URI). Generowane przez narzędzie wpiec.py '
                                 '(sprite-pipeline, wideo MiniMax-H3); nie edytować ręcznie. */\n'
                                 '(function(){var T=window.Teledysk=window.Teledysk||{};T.LIS=' + body + ';})();\n')
print('lis.js', round(os.path.getsize(f'{OUT}/lis.js') / 1024), 'KB')
