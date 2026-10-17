# Recenzja R1, runda 2 — FIX  (średnia 4.1)

Wersja strony: `pub/index.html` md5 `265264a1…` (16:52). Cutout przebudowany 16:55–16:58, pozy `i7/jump/j*.png` 17:00.
Wszystko wyrenderowane ponownie:
- `frames.jpg`, `layers.jpg`, `motion.json` (`render_scene.js`, bez błędów strony);
- zbliżenia:
  - `r2_jump_land.jpg` (lądowanie 2.30–3.95 co 0.15);
  - `r2_jump_route.jpg` (skok trasy 4.90–6.90 co 0.125);
  - `r2_exit.jpg` (7.7–10.1);
  - `r2_entry.jpg` (wejście 1.6–2.5);
  - `r2_zoom_mat.jpg`, `r2_zoom_shelf.jpg`, `r2_zoom_exit.jpg`, `r2_zoom_faces_7.00.jpg`, `r2_angel_src_hand.jpg`;
- sondy:
  - `probe.js` (przejście);
  - nowa `probe2.js` → `probe2.json`: pozycja orzesznicy i paciorka co 0.1 s oraz skok jasności między klatkami wokół TIN.

Czasy: TIN = 2.35, lądowanie tLand = 3.88, wyjście tE = 8.67, koniec M = 10.22.

## Weryfikacja poprawek z rundy 1
| # | poprawka | stan | dowód |
|---|---|---|---|
| 1 | Trasa: skok zamiast wspinaczki i „run” | **naprawione** | `R1.json` ma kolejno `stop_sniff` 3.88 → `idle_look` 4.7 → `jump` 5.1 → `groom_wonder` 6.6 → `idle_look` 8.2, bez `climb` i `run`. W `r2_jump_route.jpg` widać po kolei j1_crouch (5.1–5.3), j2_push (5.4), łuk nad dzbanem (5.5–6.3, szczyt y≈305 nad półką y=369), j6_land (6.4) i j7_settle (6.5–6.6) na półce. Patyka nie ma. W `probe2` między klatkami co 0.1 s orzesznica przesuwa się o ≤ 1 px, jeśli nie jest w pozie skoku. |
| 2 | Przejście renderuje scenę do własnego bufora | **naprawione** | Wnętrze widać w rozbłysku od ~1.2 s (`r2_entry.jpg` 1.6/2.0). Przy 2.3 render_vs_scene = 8.2, render_vs_intro = 64. Przy 2.0 render_vs_scene = 48.7, ale to ciepła poświata, nie kosmos. Skok jasności między klatkami 2.30→2.40 wynosi ≤ 3.0, więc cięcia sceny nie ma. |
| 3 | Kolor poz skoku = sprite'y MiniMax | **naprawione na macie, nie na półce** | `r2_zoom_mat.jpg` 3.80 (j7) vs 3.95 (stop_sniff): futro i oczy zgodne. `r2_zoom_shelf.jpg` 6.55 (j7_settle) → 6.65 (groom_wonder): sprite nagle jaśniejszy i bledszy, ok. 1.3× większy, bez przenikania 0.15 s. |
| 4 | Obrót w locie ±0.35 rad | **naprawione** | `jumpAt` l. 680: `clamp(…,-.35,.35)`. Lot 5.6–6.3 bez nurkowania nosem. Stromość przy 9.3 wynika z rysunku pozy j3_rise, nie z obrotu. |
| 5 | Paciorek odchodzi pierwszy | **naprawione** | Odlot zaczyna się przy tE−0.8 = 7.87. Przy 8.6 paciorek jest w (1122,104), orzesznica w (909,369): 340 px. Przy 9.0 jest to 370 px w stronę prawego górnego rogu. |
| 6 | Podpis od pokazania sceny | **naprawione** | Narasta 2.35–2.75 (`r2_entry.jpg` 2.40/2.50). |
| 7 | Światło niesie orzesznicę nad miejsce lądowania | **nie naprawione** | Orzesznica leci do (1114,115), nad matą. Paciorek leci w tym czasie do lampki: przy 2.3 jest w (812,333), ok. 370 px od niej (`probe2.json` 1.0–2.3). Nic jej nie niesie. Co gorsza, przy 2.36 orzesznica znika: patrz Twarde błędy. |
| 8 | Smuga anioła, pasek włosów Marii | **naprawione** | `r2_angel_src_hand.jpg`: dłoń czysta. `angel_review.jpg`: plama nie wraca w żadnym z 7 gestów. `r2_zoom_faces_7.00.jpg`: brak skrawka chusty przy prawej krawędzi anioła, włosy Marii całe. |

## Ocena
| kryterium | ocena | dowód |
|---|---|---|
| 1. Rozpoznawalność | 5 | Już przy 2.0 s świetlisty anioł szepcze do ucha klęczącej dziewczyny przy dzieży. |
| 2. Kierunek artystyczny | 4 | Kells w tle i postaciach. Orzesznica nadal jest gładsza i bardziej „cyfrowa” niż kadr, a groom_wonder (6.65) jest bledszy od reszty jej poz. |
| 3. Bieda, prostota | 5 | Glina, mata, dzieża, łatana suknia, asymetria — bez zmian, wzorcowo. |
| 4. Paleta i pora | 5 | Niski klucz, lampka i zimna smuga z drzwi. Ciepła poświata przejścia gaśnie przed 2.35. |
| 5. Życie postaci | 4 | Maria: mrugnięcie, spojrzenie w górę, uśmiech (7.0 — czuły). Anioł bardzo subtelny. `motion.json`: anioł 16.8–27.5, Maria 23.4–28.8. Bez ghostingu. |
| 6. Życie tła | 4 | Zasłona, płomień, drganie powietrza, kurz w smudze, mąka. Szwów nie widać. |
| 7. Integracja orzesznicy | 4 | Łapy na prawdziwych powierzchniach (mata 3.9–5.1, półka 6.4–8.7), kolor na macie zgodny. Ale: zmiana wyglądu j7→groom_wonder przy 6.6; przy 10.0–10.2 ląduje w powietrzu w górnym prawym rogu (y = 46, `r2_zoom_exit.jpg`); w pozach j1/j6/j7 na ziemi nie ma cienia kontaktowego (`dmLit(…, false, …)`). |
| 8. Ruch orzesznicy | 3 | Skok trasy 5.1–6.6 jest wzorcowy. Wejście zawodzi: przy 2.30→2.40 skacze z y = 115 na y = −119, znika na ~0.3 s i spada z górnej krawędzi. Wyjście kończy się lądowaniem na niczym. |
| 9. Paciorek | 4 | Schodzi do niej przy 5.1–5.4, leci przodem w skoku i świeci na nią na półce 6.6–7.9, a potem odchodzi pierwszy. Na macie (3.9–5.0) wisi jednak ok. 400 px dalej, przy lampce, a w wejściu jej nie niesie. |
| 10. Podpis | 4 | Pojawia się z odsłonięciem sceny i jest czytelny w lewym dolnym rogu. Gaśnie jednak przy 8.87–9.27, czyli ok. 1 s przed końcem tajemnicy. |
| 11. Przejście i ciągłość | 4 | Wejście czyste i na takcie, bez skoku jasności. Ciągłość orzesznicy psują zniknięcie przy 2.36 i lądowanie w powietrzu przy 10.0. |
| 12. Czystość techniczna | 3 | Brud w źródłach usunięty. Zostają dwa „pop”-y orzesznicy: 2.36 (pozycja) i 6.6 (wielkość i barwa). |

**Średnia: 49 / 12 = 4.08.** Mimo średniej ≥ 4.0 wynik to FIX z powodu twardego błędu.

## Twarde błędy
- **HF 7 — pop orzesznicy przy wejściu (nowy, regresja).**
  - Na końcu niesienia (l < TIN) orzesznica jest w (1114,115). W pierwszej klatce po TIN skacze do (1112,−119), czyli 234 px w górę i poza kadr. Wraca z górnej krawędzi dopiero przy ~2.7 s (`probe2.json` 2.3→2.4, `r2_entry.jpg` 2.34 vs 2.36/2.40, `r2_jump_land.jpg` 2.45).
  - Przyczyna: `jumpAt(…, fromAir=true)` zaczyna lot od `uu = 0.5`, czyli od szczytu łuku `A − arcH` (arcH ≈ 210 px), a nie od punktu A. Do tego poza w locie jest rysowana na `Y − h*.35`, a poza niesiona na `cy`.

## Poprawki (kolejność wg wpływu)
1. **[krok 5] `pub/index.html`, `jumpAt` (l. 677–679): spadanie „z powietrza” ma startować dokładnie w A.**
   - W gałęzi `fromAir` zamiast paraboli od szczytu licz: `X = lerp(A[0],B[0],u)`, `Y = lerp(A[1],B[1],u*u)` (spadek z zerową prędkością pionową).
   - W `mystery` daj lądowaniu `A = [carry[0], carry[1] + h*.35]`, żeby rysunek w `pose(…, Y − h*.35)` przy u = 0 pokrył się z pozą niesioną.
   - Jak sprawdzić: `node review/R1/probe2.js`. Między 2.3 a 2.4 `dm.y` zmienia się o < 30 px i nigdy nie jest < 0 w 2.3–3.9. W `r2_jump_land.jpg` orzesznica jest widoczna w każdej klatce 2.30–3.95.
2. **[krok 5] `pub/index.html`, `mystery` l. 746: wyjście kończy się poza kadrem, a nie lądowaniem w powietrzu.**
   - Ustaw cel skoku wyjścia na `B = [W + 140, H*.02]` (zgodnie z wejściem następnej sceny, która startuje z `[W*1.04, H*.02]`).
   - Jak sprawdzić: w `probe2.json` przy 10.0–10.2 `dm.x − h ≥ W`. W `r2_exit.jpg` przy 9.9/10.1 nie ma pozy j6/j7 na górnej krawędzi. Przy 9.3 orzesznica leci w stronę paciorka (1152,86).
3. **[krok 5] `pub/index.html` i `i7/…/groom_wonder`: jeden wygląd przy przejściu j7_settle → akcja trasy.**
   - Wyrównaj średni odcień, nasycenie i jasność futra `groom_wonder` do `stop_sniff`, tak jak zrobiono z pozami j (dopasowanie HSV na masce futra). Teraz sprite jest bledszy.
   - Wyrównaj skalę: wysokość tułowia do ramion w `groom_wonder` ≈ w `j7_settle`, a uszy i ogon niech nie rosną.
   - Dodaj przenikanie 0.15 s z ostatniej pozy skoku do pierwszej klatki akcji. Teraz `jumping` dla segmentu `jump` kończy się twardo przy u = 1.
   - Jak sprawdzić: zbliżenie 6.55 vs 6.70 (crop 830,240–1000,400). Barwa futra różni się < 5%, obrys ciała urośnie najwyżej ~10%.
4. **[krok 5] `pub/index.html`, `mystery` l. 733: paciorek naprawdę niesie orzesznicę w wejściu.**
   - Cel lotu paciorka w wejściu: zamiast `light` daj `[carry[0] − h*.3, carry[1] − h*.9]`, tak żeby od p ≈ 0.3 leciał tuż przy jej głowie.
   - Po lądowaniu skróć dolot do niej: `tLand+.2 … tLand+1.0` zamiast `+.4 … +1.8`. Teraz na macie 3.9–5.0 paciorek wisi ok. 400 px dalej, przy lampce.
   - Jak sprawdzić: `probe2.json`. Odległość paciorek–orzesznica < 130 px dla l 1.0–2.3 i < 200 px od 4.3.
5. **[krok 5] `pub/index.html`, `mystery` (rysowanie skoku): cień kontaktowy w pozach naziemnych.**
   - Gdy `jumpAt` zwraca `air:false` (j1/j2 przed wybiciem, j6/j7 po lądowaniu), narysuj ten sam cień co w `dmLit(…, onGround=true)` pod A albo B.
   - Najprościej: wywołaj `jumpAt` dwa razy, albo licz fazę z `p` (`p < fl0 || p ≥ .84`) przed `dmLit`.
   - Jak sprawdzić: `r2_zoom_mat.jpg` — przy 3.80 (j7) cień jak przy 3.95 (stop_sniff); przy 6.45 cień na półce.
6. **[krok 5] `pub/index.html`, `mystery` l. 766: podpis do końca tajemnicy.**
   - Zamiast `1 − prog(l, tE+.2, tE+.6)` daj `1 − prog(l, M−.35, M)`.
   - Jak sprawdzić: w `frames.jpg` klatka 9.9 s ma pełny podpis.

## Co działa (max 3 punkty)
- Skok na półkę 5.1–6.6: przykucnięcie, wybicie, łuk nad dzbanem z lekkim przewyższeniem, lądowanie ze squashem i uspokojenie. To dokładnie to, czego chciał właściciel; wzorzec dla pozostałych 19 scen.
- Przejście z rozbłysku jest teraz miękkie i odsłania wnętrze, bez skoku jasności na TIN.
- Źródła są czyste: dłoń anioła bez plamy we wszystkich gestach, Maria z całymi włosami. Jej uśmiech przy 7.0 jest czuły i nieprzesłodzony.
