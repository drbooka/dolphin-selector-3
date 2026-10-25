# Dolphin Selector 3 – Änderungen v13.23

Stand 25.10.2026 · Basis: v13.22

## Neu: I2C-SCAN zur Fehlersuche

**SETUP › ENCODER › I2C-SCAN** (auch über **SETUP › INFO › I2C**) zeigt jedes Gerät am I2C-Bus mit dem, was die Firmware dort erkennt (`amyboard.scan_i2c`). Damit lässt sich direkt auf dem Display klären, warum ein Zusatz-Encoder nicht im Menü erscheint – ohne Computer und ohne REPL.

- Erste Zeile **SKETCH NUTZT**: welche Zusatz-Encoder der Sketch verwendet (z. B. `M5+QUAD`).
- Danach je Adresse (hexadezimal) der erkannte Typ: SINGLE, QUAD, ANO, M5 8ENC, DISPLAY, AUDIO, CV IN, CV OUT, JOYSTICK oder `?`.
- Rechts bei Seesaw-Boards die Produktnummer, die der Chip meldet: **P5752 = Quad**, P5740/P6310 = ANO, P4991/P5880 = Single.

So liest man das Ergebnis, wenn der Quad fehlt:

| Anzeige | Bedeutung |
|---|---|
| keine Zeile bei 49–50 | Quad antwortet nicht: Kabel, Stromversorgung, Lötbrücken prüfen |
| `49 ANO P5740` | Chip meldet sich als ANO, nicht als Quad (falsches Board oder falsche Seesaw-Firmware) |
| `49 SEESAW? …` | Seesaw-Board antwortet, wird aber keinem Typ zugeordnet |
| `49 QUAD P5752`, aber SKETCH NUTZT ohne QUAD | Erkennung im Sketch prüfen – bitte melden |

Die Liste wird beim Öffnen einmal neu gelesen. Ohne `scan_i2c` (sehr alte Firmware) stehen nur die Adressen da.
