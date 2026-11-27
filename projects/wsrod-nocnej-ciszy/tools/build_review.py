"""build_review.py: MusicGames docs/wsrod-nocnej-ciszy/anim-review/index.html (+ an artifact copy in OUT_ART) from the template and anim/manifest.json."""
import json, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MG = "/home/user/MusicGames"
man = json.load(open(MG + "/fingerpick-warmup/art/wsrod-nocnej-ciszy/anim/manifest.json"))
jobs = [json.loads(l) for l in open(os.path.join(HERE, "jobs.jsonl"))]
cost = sum(j.get("est_cost_usd") or 0 for j in jobs if j.get("state") == "ok")
PL = {
 "fox-sit": ("brzdąka dwa razy, lekko kiwa głową, koniec szalika i czubek ogona się kołyszą", "ta sama poza co fox.webp"),
 "fox-sing": ("śpiewa (pyszczek otwarty i półotwarty), kołysze głową, brzdąka", "ta sama poza co fox-sing.webp"),
 "fox-tiptoe": ("idzie na palcach, wysoko unosząc kolana, w miejscu (dwa kroki na pętlę); po ścieżce przesuwa go gra", "nowa poza: stoi na tylnych łapach"),
 "fox-stand": ("oddycha, mruga raz (klatka 6), raz delikatnie brzdąka", "nowa poza: stoi, stopy razem"),
 "dog-sit": ("macha ogonem dwa razy, mruga raz (klatka 6)", "ta sama poza co dog.webp"),
 "dog-bark": ("szczeka dwa razy (pysk otwarty w klatkach 2–3 i 6–7), przednie łapy lekko podskakują", "poza z dog.webp, oba uszy w górze"),
 "dog-sleep": ("powoli oddycha, czubek ogona drgnie", "nowa poza: leży, pysk na łapach"),
 "hen-idle": ("mruga, kiwa głową", "ta sama poza co hen.webp"),
 "duck-idle": ("mruga, kiwa głową", "ta sama poza co duck.webp"),
 "rabbit-idle": ("mruga, ucho lekko drga", "ta sama poza co rabbit.webp"),
}
for k, (m, p) in PL.items():
    man["clips"][k]["motion"], man["clips"][k]["pose"] = m, p
missing = {
 "Pies wstaje z leżenia (poziom 13, takt 15)": "zamówienie wysłane, ale bramka APIYI odrzuciła klucz (401 „Invalid token”, dwa razy, nic nie zostało policzone). Prompt czeka gotowy. Do tego czasu pies przeskakuje z leżenia od razu do szczekania na siedząco.",
 "Lis śpiewa na stojąco": "przy kurniku (takty 15–16, drugie przejście) lis śpiewa stojąc; teraz gra pokazałaby siedzący śpiew. To następna animacja do zrobienia.",
 "Pozostałe stany": "pies: przechyla głowę, uszy, merdanie, opada, kładzie się, ziewa, śpiewa; lis: stroi, zachwyt, przestrach; kura wygląda z kurnika, kaczka idzie, królik uszy i serce, śpiew całej trójki. Na razie zostają stillki z ruchem z kodu (do „merdania” pasuje animacja siedzącego psa).",
}
foot = (f"Zrobione narzędziem generate-game-gifs (gpt-image-2.6-flare, GIF przez APIYI, wysoka jakość, zatwierdzony rysunek jako wzór): "
        f"10 animacji z 10 udanych zamówień, koszt szacunkowy ${cost:.2f}. Obwódka z papieru odtworzona w tej samej szerokości co na stillkach. "
        f"Paski WebP, manifest i wyniki kontroli: <code>fingerpick-warmup/art/wsrod-nocnej-ciszy/anim/</code>. Surowe GIF-y, prompty i dziennik zamówień: "
        f"<code>gondar/sprite-refs</code> → <code>projects/wsrod-nocnej-ciszy/</code>.")
data = {"clips": man["clips"], "states": man["states"], "missing": missing, "foot": foot}
tpl = open(os.path.join(HERE, "tools", "review_template.html")).read()
def page(art):
    return tpl.replace("__ART__", art).replace("__DATA__", json.dumps(data, ensure_ascii=False))
out = MG + "/docs/wsrod-nocnej-ciszy/anim-review/index.html"
os.makedirs(os.path.dirname(out), exist_ok=True)
head = '<!doctype html>\n<html lang="pl">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
body = page("../../../fingerpick-warmup/art/wsrod-nocnej-ciszy/")
t_end = body.index("</style>") + len("</style>")
open(out, "w").write(head + body[:t_end] + "\n<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n</head>\n<body>\n" + body[t_end:] + "\n</body>\n</html>\n")
if len(sys.argv) > 1:
    open(sys.argv[1], "w").write(page("art/"))
print("wrote", out, "cost est", round(cost, 3))
