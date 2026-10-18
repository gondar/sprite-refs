# Recenzja R1 — FIX  (średnia 3.3)

Wersja strony: `pub/index.html` md5 `58b62c66…` (zmieniona w trakcie recenzji o 16:44 — „jedna orzesznica niesiona przez światło”; wszystkie oceny dotyczą tej wersji, wszystko wyrenderowane ponownie).
Pliki: `frames.jpg`, `layers.jpg`, `motion.json`, zbliżenie skoku `jump_land_half.jpg` (t = 2.30–3.95 co 0.15 s) i `jump_land_dense_half.jpg` (3.80–4.80), skrypty `render_jump.js`, `render_full.js`, `probe.js`, zbliżenia `zoom_*.jpg`.

| kryterium | ocena | dowód |
|---|---|---|
| 1. Rozpoznawalność | 5 | Od 2.6 s: świetlisty anioł szepcze do ucha klęczącej dziewczyny przy dzieży — ośmiolatek od razu powie „Zwiastowanie”. |
| 2. Kierunek artystyczny | 4 | Tło i postacie trzymają Kells (płaskie plamy, spirale w skrzydłach, ołówek); orzesznica w pozach skoku (`i7/jump`) jest gładsza i bardziej „cyfrowa” niż reszta kadru (3.05–3.65 s). |
| 3. Bieda, prostota | 5 | Glina, mata, dzieża, gliniany dzban, łatana suknia, bose stopy, kadr asymetryczny — zero ozdób (wszystkie klatki). |
| 4. Paleta i pora | 5 | Nisko, jedno ciepłe źródło (lampka) + zimne światło z drzwi, głębokie cienie — zgodne z zatwierdzonym R1. |
| 5. Życie postaci | 4 | `mary_review.jpg`: mrugnięcie, spojrzenie w górę, uśmiech, „wonder” — czułe i czytelne; anioł (breath/glow/eyes_open) bardzo subtelny; w `motion.json` obie postacie mają podobny ruch względny (anioł 16.6–27.3, Maria 22.9–28.0). Brud: szara plama pod dłonią anioła (zoom_faces.jpg). |
| 6. Życie tła | 4 | Zasłona, płomień, drganie nad płomieniem, kurz w smudze z drzwi, mąka — 5 detali, szwów nie widać przy amp 0.012. |
| 7. Integracja orzesznicy | 2 | Kolor i cień dobre na macie (3.65) i na półce (5.0–8.0), ale 3.90–4.50 wspina się po patyku, który jest częścią sprite'a „climb” i stoi luzem na podłodze przed zasłoną — łapy nie na prawdziwej powierzchni. |
| 8. Ruch orzesznicy | 1 | Lądowanie na macie OK (3.65 squash, 3.80 settle), ale 3.85→3.90 teleport ~70×120 px na „patyk”, a 4.65–4.80 „run” w powietrzu poziomo z patyka na półkę — sunie bez łuku, bez odbicia; to dokładnie skarga właściciela. |
| 9. Paciorek | 3 | Schodzi do jej głowy (5.0–8.0 tuż nad nią, ciepło na futrze), ale odlatuje dopiero 0.25 s przed skokiem i przy 9.0 s wciąż wisi przy jej ogonie — nie „odchodzi przed nią”. |
| 10. Podpis | 4 | Czytelny, dolny lewy róg na ciemnej podłodze, niczego nie zasłania (4.2–8.0); pojawia się dopiero przy lądowaniu (3.9 s), czyli 1.5 s po pokazaniu sceny. |
| 11. Przejście i ciągłość | 1 | „Rozbłysk” z intra nigdy nie odsłania wnętrza: przy 1.6/2.0/2.3 s wciąż jest kosmos (render vs intro przy 2.3 s: różnica 11.9 — prawie identyczne), a scena wskakuje twardym cięciem przy l = 2.35 s, 0.3 s po takcie (takt = 2.043 s). |
| 12. Czystość techniczna | 2 | Dwa „pop”-y: cała scena przy 2.35 s i orzesznica przy 3.85→3.90 (zmiana pozy, miejsca i wyglądu sprite'a naraz); szara plama na dłoni anioła w każdej klatce. |

## Twarde błędy
- **HF 5 — orzesznica sunie zamiast skakać:** 4.65–4.80 s przelatuje poziomo w pozie biegu z patyka na półkę (`route` t=4.6 „run” → t=4.8), bez przykucnięcia, łuku i lądowania. Do tego teleport 3.85→3.90 s i wspinaczka po nieistniejącym patyku.
- **HF 7 — pop:** twarde wejście sceny przy l = 2.35 s (przejście nie odsłania obrazu) i skok pozycji orzesznicy 3.85→3.90 s.

Przyczyny (sprawdzone w kodzie):
- Trasa w `i6/fx/R1.json` liczy czas od l = 0, a orzesznica ląduje dopiero przy `tLand = TIN + JIN = 3.88 s`. Punkty 2.3 / 2.9 / 3.5 przepadają w locie, więc w chwili lądowania `routeAt` jest już w segmencie 3.5→3.9 (podnóże zasłony). Punkty 8.8 / 9.3 / 10.2 też nigdy nie grają, bo wyjście zaczyna się przy `tE = 8.67`.
- Przejście: `transition()` z czarnym `drawA` odsłania scenę (66% pikseli przy p = 0.9). Z `drawA = intro(q, INTRO-.01)` wynik jest równy intru, więc coś w ścieżce intro → `ofx` gubi warstwę B. Dowód w `review/R1/probe.js`.

## Poprawki (kolejność wg wpływu)
1. **[krok 4 + 5] `pub/i6/fx/R1.json` i `pub/index.html` (`mystery`): trasa po lądowaniu i jeden prawdziwy skok zamiast wspinaczki i „run” w powietrzu.**
   - W silniku dodaj akcję trasy `"jump"`: segment od punktu `jump` do następnego punktu rysuj przez `jumpAt(c, A, B, u, h, false)`, gdzie `u` to postęp segmentu (crouch → push → łuk → land → settle). Długość ok. 1.5 s.
   - Nowa trasa:
     - t=3.9 `stop_sniff` (0.82, 0.86) na macie, facing left;
     - t=4.7 `idle_look` (zauważa Marię);
     - t=5.1 `jump` → (0.708, 0.512);
     - t=6.6 `groom_wonder` na półce;
     - t=8.2 `idle_look` facing right.
   - Usuń `climb`, `run` 4.6 i punkty po 8.67.
   - Jak sprawdzić: `node review/R1/render_jump.js` (zmień T2 na 3.8–6.8 co 0.15). Między dwiema kolejnymi klatkami orzesznica nie może przesunąć się o więcej niż 15 px w pozie innej niż j1–j7. W 5.1–6.6 widać kolejno j1_crouch, j3/j4 nad dzbanem i j6_land na półce. Nie ma klatki z patykiem.
2. **[krok 5] `pub/index.html`, `transition()` (l. 369–372): naprawić odsłonięcie sceny.**
   - Narysuj `drawB` do osobnego bufora normalnie (source-over).
   - Potem na `ofx` maska + `globalCompositeOperation = "source-in"` + `drawImage(buforB)`. Tak scena złożona z wielu wywołań nie zależy od trybu kompozycji ani od stanu po `intro()`.
   - Jak sprawdzić: `node review/R1/probe.js` (wersja porównawcza). Przy l = 2.0 render_vs_scene < 25 i render_vs_intro > 40; w `frames.jpg` klatka 2.0 s pokazuje wnętrze w kręgu rozbłysku. Pełna scena ma być na ekranie przed 2.35 s, bez skoku jasności przy 2.35.
3. **[krok 5] `pub/index.html`, `dmLit`/`jumpAt` i `i7/jump/*.png`: jeden wygląd orzesznicy.**
   - Pozy skoku są bardziej nasycone i mają inne oczy niż akcje MiniMax (3.85 vs 3.95).
   - Wyrównaj średni odcień, nasycenie i jasność futra poz `j1…j7` do sprite'ów `DMS` (np. PIL, dopasowanie średniej HSV na masce futra).
   - Przy przejściu j7_settle → akcja trasy daj 0.15 s przenikania.
   - Jak sprawdzić: zbliżenie 3.80 vs 3.95 — średnia barwa futra różni się < 5%, oczy tej samej wielkości.
4. **[krok 5] `pub/index.html`, `jumpAt`: ogranicz obrót w locie do ±0.35 rad.**
   - Teraz `ang` dochodzi do ~1 rad i przy 3.05 s orzesznica leci nosem w dół jak w nurkowaniu.
   - Jak sprawdzić: w `jump_land_half.jpg` przy 2.9–3.35 tułów pochylony najwyżej ok. 20°.
5. **[krok 5] `pub/index.html`, `mystery`: paciorek odchodzi pierwszy.**
   - Start odlotu przy `tE - 0.8` (zamiast `tE - 0.25`), dolot do `exitFrom` przy `tE + 0.3`.
   - Jak sprawdzić: przy 9.0 s paciorek co najmniej 150 px przed orzesznicą w stronę prawego górnego rogu, a przy 8.6 s już wyraźnie oderwany od jej głowy.
6. **[krok 2–3] `pub/i5/R1_fig_angel.png`, `pub/i7/cut/angel_home.png` i wszystkie `angel_*.webp`: retusz.**
   - Szara plama pod dłonią przy ustach (ok. x 370–425, y 170–230 w płótnie 489×514): zamaluj kremem anioła z linią dłoni. Plama jest już w `R1_full.jpg`, więc to brud źródła, nie ghosting, ale leży w punkcie akcji.
   - Usuń skrawek włosów i chusty Marii przy prawej krawędzi (x ≥ 465, y 150–235).
   - Przebuduj bag cutoutu z poprawionego `home`.
   - Jak sprawdzić: `zoom_faces.jpg` przy t = 6.6 — brak szarej plamy; `angel_review.jpg` — plama nie wraca w żadnym geście.

## Co działa (max 3 punkty)
- Obraz: bieda, niski klucz, jedno ciepłe źródło i świetlisty anioł szepczący do ucha — wzorcowe dla Radosnych.
- Idle Marii (mrugnięcia, spojrzenie w górę, nieśmiały uśmiech) jest czuły i czytelny; zaczyna i kończy na tej samej klatce, bez ghostingu na twarzy.
- Samo lądowanie na macie (3.50–3.85: opadanie, squash j6_land, j7_settle, cień) czyta się jak skok — ten wzorzec trzeba użyć do każdego przemieszczenia.
