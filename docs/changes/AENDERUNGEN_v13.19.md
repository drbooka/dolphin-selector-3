# Dolphin Selector 3 – Änderungen v13.19

Stand 20.10.2026 · Basis: v13.18 (SLICES auf der Hardware bestätigt)

Vier Neuerungen aus der Auswertung der AMYboard-Ankündigungen (Discord #announcements bis 12.09.2026).

## 1. DX7-Bänke von der SD-Karte

**Patch-Browser › DX7 VON SD** (nicht auf Kanal 10):
- listet `.SYX`-Dateien aus `/sd/dx7/` und dem Hauptverzeichnis (32er-Bank oder Einzelstimme),
- zeigt nach dem Öffnen einer Datei die Stimmen mit Namen,
- macht jede Stimme beim Durchdrehen sofort hörbar. Drücken übernimmt, lang drücken stellt den vorherigen Klang wieder her.

Technik: `fm.load_syx(daten, voice, patch=1024+Kanal)` aus AMYs `fm.py` (läuft seit 10.08.2026 auf dem AMYboard) wandelt die Stimme und legt sie als User-Patch ab. Jeder Kanal hat seinen eigenen User-Patch.

- **Gespeichert** werden Datei, Nummer und Name, auch in Szenen. Beim Start wird die Stimme von der Karte neu geladen.
- **Klangformung:** wie bei den eingebauten DX7-Patches (ALGORITHMUS, FEEDBACK, LFO).
- **Fehlt die Datei:** Der Kanal nimmt DX7-Patch 128, Meldung „DX7 Kn · NICHT GELADEN“.
- SD-Stimmen erscheinen nicht unter FAVORITEN/ZULETZT, weil sie zum Kanal gehören.
- **SETUP › INFO › DX7 SD (FM)** zeigt, ob `fm.py` auf dem Board vorhanden ist.

## 2. Taster der Zusatz-Encoder

**SETUP › ENCODER › TASTER:** eine Belegung je angeschlossenem Encoder (E1–E8, Q1–Q8). Kurz = beim Loslassen, lang = ab 0,45 s.

| Belegung | Kurz | Lang |
|---|---|---|
| KONTEXT (ab Werk) | PATCH Kn: Kanal stumm/an · fester Parameter: großer Ring · SEITE auf der Drum-Seite: Step unter dem Encoder setzen | PATCH Kn: Patch-Browser für Kanal n |
| START/STOP · TAP TEMPO | ja | – |
| PANIC (LANG) | – | alle Noten aus |
| MUTE K1–K4 · MUTE 303 · MUTE DRUMS | stumm/an | – |
| AUS | wird nicht abgefragt | |

Gelesen wird über `enc.button(i)`, mit demselben Index wie der Encoder. Kurz und lang erkennt der Sketch selbst. Taster auf AUS werden nicht abgefragt und sparen I2C-Zeit.

## 3. Filter NOTCH und PHASER

SAMPLER › SLOT › FILTER bietet zusätzlich **NOTCH** und **PHASER** (AMY seit 03.08.2026), aber nur, wenn die Firmware `FILTER_NOTCH`/`FILTER_PHASER` kennt. Intern übersetzt eine Tabelle die Auswahl in den AMY-Filtertyp.

## 4. Slices über MIDI

- PAD-KANAL **Noten 44–59** spielen Slice 1–16 des neuen **SLICE-SLOT** (SAMPLER-Seite, sichtbar bei gesetztem PAD-KANAL). Noten 36–43 spielen weiter die ganzen Slots.
- Jedes Stück endet nach seiner Länge, mit TAKT-SYNC im Tempo. Im Modus GATE stoppt Loslassen früher.
- Das Ende wird über ein eigenes AMY-Tag je Slot (210–217) geplant. Ein neuer Anschlag verwirft das alte Ende, damit es das neue Stück nicht abschneidet.
- Auch das Vorhören im SPUR-MENUE › SLICE nutzt jetzt diesen Weg.

## Test (Simulation)

Der ganze Sketch lief mit nachgebauten `amy`/`amyboard`/`fm`/`tulip`-Modulen, kommentierte und Board-Fassung, je 35 Prüfungen bestanden:
- Start; Erkennung von M5Stack + Quad und deren Tastern
- Filterwerte
- DX7 VON SD: Dateien, 32 Stimmen, Vorschau, User-Patch 1026 abgelegt und von Kanal 2 geladen, Speichern in JSON, `sanitize`, Neustart lädt neu, Abbrechen (in der Stimmenliste und im normalen Patch-Browser), fehlende Datei
- Taster: Q1 kurz = Mute K1, Q1 lang = Patch-Browser K1, E3 auf der Drum-Seite setzt Step 3, START/STOP
- MIDI-Slices: Note 46 = Slice 3 mit richtigem Startpunkt, Ende über Tag 210, Note außerhalb ignoriert, Note 37 = ganzer Slot 2
- Übernahme eines gespeicherten v13.18-Stands
- alle neuen Seiten zeichnen

## Auf der Hardware zu prüfen
- SETUP › INFO › DX7 SD (FM) = JA? Wie lange dauert das Laden einer Stimme (hörbare Pause beim Durchdrehen)?
- Klingt eine .SYX-Stimme wie erwartet (z. B. ROM1A-Bank des DX7)?
- Taster: reagieren E- und Q-Taster? Wird die Bedienung mit allen Tastern auf KONTEXT spürbar langsamer (SETUP › INFO › BEDIENUNG MAX)? Wenn ja, ungenutzte auf AUS.
- MIDI-Slices vom KeyStep Pro: Noten 44+ auf dem PAD-KANAL.
- RAM: `sketch.py` ist jetzt ~259 KB (v13.18: 249 KB). Startet das Board sauber? RAM NACH BOOT vergleichen.

## Dateien
- `sketch.py` – fürs Board, ohne Kommentare (~259 KB)
- `sketch_src.py` – kommentierte Fassung (~325 KB), nicht zum Übertragen
- Rückweg: `sketch_v13.18.py` (letzter bestätigter Stand)
