# Leszy (cień z porożem) — wideo MiniMax-H3 → paski klatek dla filmu „Leszy”

| Plik | Co |
|---|---|
| `leszy-profil-biel-v1.png` | wzorzec (poza `krok-2` z MathGames `klasa-7/leszy/img/` na bieli, 720×1280, profil w prawo) |
| `manekin-dorosly-stoi-kroczy-siega-cofa-4s.mp4` | manekin dorosłych proporcji, 4 ruchy po 1 s: stoi · ciężki krok · sięga · cofa się (H3 z tekstu, bez dźwięku) |
| `manekin-dorosly-stoi-glowa-szuka-kuca-4s.mp4` | stoi · (głowa ledwo się rusza) · pochyla się · kuca; Leszy w klipie i tak odwrócił głowę — prompt to opisał |
| `leszy-h3-*-4s.mp4` | klipy postaci (wzorzec + manekin), bez dźwięku |
| `prompty/` | m1/m2 = manekiny, c1/c2 = postać |
| `narzedzia/` | `klucz.py` (alfa z luminancji na bieli, tło = mediana brzegu), `sledz.py` (śledzenie głowy → oczy rysowane kodem), `zbuduj.py` (cięcie, krok z odjętym dryfem i przenikaniem szwu, WebP + `leszy-anim.js`) |
| `jobs-leszy.jsonl` | log płatnych wywołań (razem $0.48; trzy odrzucone przez pobieranie referencji — zwrócone) |

Wynik w MathGames: `klasa-7/leszy/leszy-anim/` (paski + JSON + `leszy-anim.js`, `Teledysk.LESZY_ANIM`).
