# Dolphin Selector 3 – Änderungen v13.29

Stand 28.10.2026 · Basis: v13.28

## Neu: LEDs

Bisher hat der Sketch nur die LEDs der Zusatz-Encoder in einer festen Farbe je Funktion gesetzt. Die LED des Navigations-Encoders (Single #5880) blieb dunkel. Jetzt zeigen alle LEDs, was gerade los ist. Alles liegt unter **SETUP › ENCODER › LEDS**.

### Navigations-Encoder (Single)
Jede Anzeige hat eine wählbare Farbe. **AUS** schaltet nur diese Anzeige ab.

| Zeile | Ab Werk | Wirkung |
|---|---|---|
| **FARBE** | KANAL | Grundfarbe. KANAL = jeder der 16 Kanäle hat eine eigene Farbe (einmal rund um den Farbkreis), sonst eine feste Farbe |
| **EDIT** | AUTO (weiß) | solange ein Wert bearbeitet wird (großer Ring oder Auswahl in der Zeile) |
| **TAKT** | AUTO | Sequencer läuft: Blitz auf jeden Schlag (erstes Viertel), AUTO = Grundfarbe hell, Takt 1 weiß |
| **KANAL-BLITZ** | AN | beim Kanalwechsel 0,6 s hell in der Farbe des neuen Kanals |
| **PANIC** | AUTO | beim Halten auf SPIELEN von gelb nach rot, bis PANIC auslöst |
| **WARNUNG** | AUTO (rot) | blinkt bei CLIP am AUDIO IN (solange die Seite offen ist), hoher CPU-Last oder Speicherfehler |

Vorrang: PANIC › Kanal-Blitz › Warnung › Takt › EDIT › Grundfarbe.

### Zusatz-Encoder (M5Stack, Quads)
- **ZUSTAND** (ab Werk AN): gedimmt = der Encoder hat gerade keine Wirkung.
  - SEITE: die offene Seite hat für diesen Encoder keinen Wert.
  - PATCH: Kanal stumm oder ohne Patch.
  - PARAMETER: Parameter ausgeblendet, z. B. CUTOFF auf einem Drumkit-Kanal.
  - LADEN AUF DRUCK vorgemerkt: blinkt, bis der Taster lädt.
  - Funktion AUS mit Taster START/STOP, MUTE, AUDIO IN, TAP TEMPO oder ENC-SET: die LED zeigt den Taster.
- **DREH-BLITZ** (ab Werk AN): kurz heller beim Drehen.
- Neue LED-Farbe **KANAL** auf der Encoder-Seite: PATCH K3 leuchtet in der Farbe von Kanal 3, sonst in der des aktuellen Kanals.
- Im Encoder-Menü wird nichts gedimmt, damit man jede Belegung sieht.

### Allgemein
- **HELLIGKEIT** 1–4 für alle LEDs (2 = wie bisher).
- **IM SCHONER** AUS (ab Werk): LEDs dunkel, solange der Bildschirmschoner läuft.
- **LED-TEST:** alle LEDs 2,4 s rot, grün, blau, weiß – zeigt, ob jede LED am richtigen Encoder sitzt.
- **SETUP › INFO › NAV-LED:** Nummer der Single-LED in der Zählung von amyboard, oder KEINE.
- Gesendet wird nur bei Änderung. Während der Wiedergabe gehen höchstens 3 LEDs pro UI-Durchlauf raus (jede Quad-/Single-LED kostet 2 I2C-Zugriffe), die Navigation zuerst.
- Die Einstellungen werden mit dem Zustand gespeichert, nicht in Szenen oder Encoder-Sets. Ältere Stände bekommen die Werkswerte.

## Technik
- `NAV_LED` wird beim Start aus der Gerätereihenfolge bestimmt (amyboard zählt LEDs fortlaufend: M5Stack 8, Quad 4, Single 1).
- Ein Dienst `service_leds()` im UI-Takt berechnet die Wunschfarbe jeder LED. `update_leds()` sendet alles sofort.
- Welche SEITE-Encoder auf der offenen Seite einen Wert haben, wird beim Seitenwechsel und danach alle 300 ms geprüft.
- Board-Datei ca. 317 KB (bisher 308 KB), kommentierte Fassung ca. 403 KB (bisher 391 KB).

## Test in der Simulation (28.10.2026)
Beide Sprachen, kommentierte und Board-Fassung:
- 55 Prüfungen zu allen Anzeigen: Kanalfarbe und -blitz, EDIT auf Ring und Auswahl, TAKT mit Takt 1, PANIC-Verlauf über echtes Halten der Taste, Warnung blinkt, Schoner, Helligkeit, ZUSTAND für SEITE/PATCH/PARAMETER, AUF DRUCK blinkt, Dreh-Blitz, KANAL-Farbe, Taster-Zustände, LED-TEST, I2C-Budget während der Wiedergabe, keine Sendungen in Ruhe, Speichern.
- Gerätekombinationen: nur Single, M5Stack + Single, Quad + Single, ANO + M5Stack (keine Nav-LED), ohne Encoder, alles zusammen mit einem v13.28-Stand.
- Rundgang durch alle 65 Menüseiten ohne Fehler.

## Auf der Hardware zu prüfen
1. Leuchtet die Single-LED? (SETUP › INFO › NAV-LED zeigt die Nummer, LED-TEST lässt alle LEDs gleichzeitig wechseln.)
2. Sitzen alle LEDs am richtigen Encoder (LED-TEST, dann ein Encoder drehen = Dreh-Blitz)?
3. Bleibt der Takt stabil mit TAKT-Blitz und vielen Encodern (SETUP › INFO › BEDIENUNG MAX)?
4. Läuft die kommentierte Fassung (403 KB) noch an? Sonst die Board-Datei `sketch.py` nehmen.
