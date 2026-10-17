# Recenzja R1, runda 3 (weryfikacja końcowa) — PASS  (średnia 4.3)

Wersja strony: `pub/index.html` md5 `20fa5242…` (17:07).
Wszystko wyrenderowane ponownie, bez błędów strony:
- `render_scene.js 0 R1` → `frames.jpg`, `layers.jpg`, `motion.json`;
- `render_jump.js` → kopie `r3_jump_land.jpg`, `r3_jump_route.jpg`, `r3_exit.jpg`. Pliki z rundy 2 przywrócone, kopia w `r2bak/`;
- `probe2.js` → `probe3.json`;
- nowe skrypty:
  - `probe3.js` → `probe3_dm.json`: bbox, piksele i barwa surowego sprite'a orzesznicy oraz po oświetleniu;
  - `render_r3.js` → `r3full/`;
- zbliżenia: `r3_entry.jpg`, `r3_zoom_mat.jpg`, `r3_zoom_shelf.jpg`, `r3_heads.jpg`, `r3_exit_full.jpg`.

Czasy: TIN = 2.35, JIN = 1.53, lądowanie 3.88, wyjście tE = 8.67, M = 10.22.

## Weryfikacja poprawek z rundy 2
| # | poprawka | stan | dowód |
|---|---|---|---|
| 1 | Spadek „z powietrza” startuje w A | **naprawione** | `dm.y`: 2.3 → 115, 2.4 → 116, 2.5 → 122. W 2.3–3.9 nigdy < 0. W `r3_jump_land.jpg` orzesznica jest widoczna w każdej z 12 klatek 2.30–3.95. Skok jasności 2.30→2.40 ≤ 3.0. **Nowa usterka:** przy 2.34→2.36 sprite odwraca się lustrzanie (patrz Poprawki 1). |
| 2 | Wyjście poza kadr | **naprawione** | Cel to B = (1420, 14). Przy h = 100.8 mamy x − h = 1319 ≥ W. Przy 10.0–10.2 orzesznicy nie ma w kadrze (probe3: brak pikseli). Przy 9.3 jest w (1038, 43), 122 px od paciorka (1152, 86), i wylatuje górną krawędzią. Przy 9.9/10.1 brak pozy j6/j7 na krawędzi (`r3_exit_full.jpg`). |
| 3 | Jeden wygląd j7_settle → akcja | **częściowo; kryterium nie spełnione** | Jasność się zgadza: V surowe 201.5 → 199.8. Nasycenie jest teraz *za wysokie*: 0.654 → 0.740 (+13%, kanał B 69 → 52). Po oświetleniu 0.614 → 0.659 (+7%). Wielkość zmieniła kierunek, ale nie jest równa: przy 6.55→6.62 piksele 6934 → 4972 (−28%), wysokość bbox 102 → 81 (−21%). Głowa wyraźnie mniejsza (`r3_zoom_shelf.jpg`, `r3_heads.jpg`). Przenikania nie ma. **Regresja:** skala 0.8 objęła też `idle_look`, więc doszły trzy nowe skoki wielkości (Poprawki 2). |
| 4 | Paciorek niesie orzesznicę | **naprawione** | Odległość paciorek–orzesznica wynosi 68–78 px dla l = 1.0–2.3 (cel < 130). Od 4.3 do 8.2 wynosi 148–183 px (cel < 200). Odchodzi od 8.3 (tE − 0.8 ≈ 7.87 + ease). W `frames.jpg` przy 4.2/5.0 paciorek jest tuż nad nią na macie. |
| 5 | Cień kontaktowy w pozach naziemnych | **naprawione** | Średnia luminancja pasa pod łapami na macie: 3.70 (j6) 44.0, 3.80 (j7) 43.9, 3.95 (stop_sniff) 43.6 — ten sam cień. Na półce: 6.45 (j6) 69.5, 6.70 (groom) 68.8. Cień jest rysowany tylko w kadrze (warunek `G[0]>0&&…`). |
| 6 | Podpis do końca | **naprawione** | `prog(l,M−.35,M)`. W `frames.jpg` 9.9 s podpis pełny, przy 10.10 dopiero gaśnie (`r3_exit_full.jpg`). |

## Ocena
| kryterium | ocena | dowód |
|---|---|---|
| 1. Rozpoznawalność | 5 | Przy 2.0 s świetlisty anioł szepcze do ucha klęczącej dziewczyny przy dzieży. |
| 2. Kierunek artystyczny | 4 | Kells w tle i postaciach. Orzesznica nadal jest gładsza i bardziej „cyfrowa” niż kadr. Po filtrze `saturate(1.18)` groom/idle_look (6.7, 8.2) są o ton bardziej pomarańczowe od reszty jej poz. |
| 3. Bieda, prostota | 5 | Glina, mata, dzieża, łatana suknia, asymetria — wzorcowo. |
| 4. Paleta i pora | 5 | Niski klucz, lampka i zimna smuga z drzwi. Poświata przejścia gaśnie przed 2.35. |
| 5. Życie postaci | 4 | Maria: mrugnięcie, spojrzenie, uśmiech. Anioł subtelny. `motion.json`: anioł 16.8–27.5, Maria 23.4–28.8. Bez ghostingu. |
| 6. Życie tła | 4 | Zasłona, płomień, drganie powietrza, kurz w smudze, mąka. Szwów nie widać. |
| 7. Integracja orzesznicy | 4 | Cień kontaktowy w każdej pozie naziemnej, łapy na macie (y = 639) i na półce (y = 369), nie zasłania twarzy. Minusy: skoki wielkości przy zmianie akcji i lekko przesycony groom/idle_look. |
| 8. Ruch orzesznicy | 4 | Wejście ciągłe: spada z łapy światła na matę ze squashem (2.4–3.9). Skok trasy 5.1–6.6 wzorcowy. Wyjście jest wybiciem z półki poza kadr. Minus: lustrzane odwrócenie w locie przy 2.35. |
| 9. Paciorek | 5 | Niesie ją (≤ 78 px), schodzi z nią na matę, prowadzi skok na półkę, świeci na nią i odchodzi pierwszy przy 8.3. |
| 10. Podpis | 5 | Narasta z odsłonięciem sceny, czytelny w lewym dolnym rogu, pełny do 9.9 s. |
| 11. Przejście i ciągłość | 4 | Wejście bez skoku jasności i pozycji. Wyjście czyste: paciorek w (1152, 86) czeka na następną scenę. Ciągłość psuje tylko lustrzane odwrócenie przy TIN. |
| 12. Czystość techniczna | 3 | Źródła czyste, bez fringe'u. Zostaje 5 „pop”-ów orzesznicy: lustrzane odwrócenie 2.35, wielkość 4.7, 5.1, 6.6 i 8.7 (patrz Poprawki 2). |

**Średnia: 52 / 12 = 4.33.** Żadne kryterium nie jest poniżej 3 i nie ma twardego błędu, więc wynik to PASS.

Pop-y wielkości oceniam tak jak w rundzie 2: to nie flicker z HF 7, ale obciążają kryterium 12. Gdyby przy następnej scenie było ich więcej, będą FIX.

## Twarde błędy
Brak. HF 7 z rundy 2 (zniknięcie przy 2.36) usunięty.

## Poprawki (kolejność wg wpływu) — zalecane przed pokazaniem właścicielowi, nie blokują
1. **[krok 5] `pub/index.html`, `mystery` l. 763: kierunek pozy niesionej = kierunek spadku.**
   - Teraz `pose(x,"j4_apex",cx,cy,…,false,…)`, a `jumpAt` od TIN rysuje z `flip = B[0] < A[0]` = true (1077 < 1114). Sprite odwraca się lustrzanie w jednej klatce (`r3_entry.jpg`: 2.34 vs 2.36).
   - Daj w pozie niesionej `flip = landPt[0] < carry[0]`. Alternatywa: w `jumpAt` dla `fromAir` zachowaj flip niesienia.
   - Jak sprawdzić: w `r3_entry.jpg` klatki 2.34 i 2.36 mają ten sam kierunek głowy i ogona.
2. **[krok 5] `pub/index.html` l. 561: `ACTSC` tak, żeby głowa miała stałą wielkość we wszystkich pozach.**
   - Skala 0.8 dla `idle_look` dała nowe skoki:
     - 4.65→4.75 (stop_sniff → idle_look): wysokość bbox 100 → 80. Siedząca orzesznica jest *niższa* od przykucniętej, oko ok. −20%.
     - 5.1 (idle_look → j1): wielkość wraca.
     - 8.65→8.75 (idle_look → j1): oko ok. +25%, `r3_heads.jpg`.
   - Skala 0.8 dla `groom_wonder` przestrzeliła: −21% wysokości przy 6.6.
   - Zacznij od `idle_look: 1.0` (w rundzie 2 nie był problemem) i `groom_wonder: .9`. Potem dostrój tak, żeby średnica oka różniła się o ≤ 10% między stop_sniff, idle_look, groom_wonder i j1/j7.
   - Jak sprawdzić: crop głów jak w `r3_heads.jpg` dla 4.65/4.75, 5.0/5.15, 6.55/6.62 i 8.65/8.75. W `probe3_dm.json` liczba pikseli przy 6.55→6.62 zmienia się o ≤ 15%.
3. **[krok 5] `pub/index.html` l. 561: złagodź `ACTFL` i dodaj krótkie przenikanie.**
   - `saturate(1.18) brightness(.94)` → ok. `saturate(1.05) brightness(.98)`.
   - Jak sprawdzić: w `probe3.js` surowe `sat` dla groom/idle_look ma się mieścić w 0.654 ± 0.03 (teraz 0.74), a `val` w 201 ± 5.
   - Dodatkowo: przenikanie 0.12 s przy wyjściu z `jumping` (u ≥ .92 → akcja) zamaskuje resztę różnicy rysunku.

## Co działa (max 3 punkty)
- Całe życie orzesznicy w jednym ciągu, z mierzalną ciągłością:
  - wejście: niesiona przez światło (≤ 78 px) spada na matę bez przerwy w pozycji;
  - skok na półkę 5.1–6.6 (przykucnięcie, wybicie, łuk nad dzbanem, squash) jest wzorcem dla 19 scen;
  - wyjście: wybicie poza kadr za odchodzącym paciorkiem.
- Paciorek prowadzi orzesznicę przez całą tajemnicę. Ciepłe światło jest na niej od 3.9 do 8.2, a odchodzi pierwszy.
- Przejście i podpis: brak skoku jasności na TIN (≤ 3.0), podpis od odsłonięcia do 9.9 s. Źródła postaci czyste.
