# Dolphin Selector 3 – Änderungen v13.24

Stand 26.10.2026 · Basis: v13.23

## Neu: Encoder-Menü

Alle Zusatz-Encoder (M5Stack E1–E8, Quad 1 Q1–Q4, Quad 2 Q5–Q8) lassen sich jetzt jeder Funktion zuweisen, auch dem Patch-Wechsel für **jeden** Kanal. Der Single bleibt die Navigation.

### Übersicht (SETUP › ENCODER)
- Oben **GERAETE** (jetzt ungekürzt, z. B. `M5+2QUAD`), **SET** und **DREHRICHTUNG**.
- Darunter alle gefundenen Zusatz-Encoder nach Gerät gruppiert (`= M5STACK =`, `= QUAD 1 =`, `= QUAD 2 =`), rechts die Funktion (`SEITE`, `PATCH K3`, `PATCH AKT`, `KANAL`, `CUTOFF` …).
- **Dreh an einem Zusatz-Encoder: Der Cursor springt auf seine Zeile.** Im Menü lösen die Encoder dabei nichts aus.
- Am Ende **I2C-SCAN**.

### Encoder-Seite
Titel = Encoder (z. B. `E3`), rechts das Gerät. Nach der **FUNKTION** erscheinen nur die passenden Zeilen. Drehen an einem anderen Zusatz-Encoder wechselt direkt zu dessen Seite.

| FUNKTION | Zeilen |
|---|---|
| AUS | – |
| SEITE | – |
| PATCH | KANAL (AKTUELL, K1–K16) · LISTE (ALLE, Kategorien, FAVORITEN, DRUMKITS) · LADEN (SOFORT, AUF DRUCK) · JETZT |
| KANAL | JETZT |
| PARAMETER | GRUPPE (MIXER, KLANG, EFFEKTE, SEQ+SZENE, 303, DRUMS, MODULAR, AUDIO IN) · WERT · JETZT |

Dazu immer **TASTER** und **LED**.

- **PATCH AKTUELL** folgt dem gewählten Kanal – ein einziger Encoder für alle Kanäle.
- **LADEN SOFORT** (ab Werk) wie bisher: nach 120 ms Ruhe.
- **LADEN AUF DRUCK:** Drehen merkt nur vor (`K3 > 045 DRUCK`, in der Übersicht `*`), der Taster (KONTEXT) lädt. Der Taster wird dabei automatisch auf KONTEXT gestellt.
- **KANAL:** Drehen wählt den aktuellen MIDI-Kanal, ein Schritt je Bewegung.
- KONTEXT-Taster bei PATCH/KANAL: kurz = vorgemerkten Patch laden, sonst Kanal stumm/an; lang = Patch-Browser des Kanals.

### LEDs
- Je Zusatz-Encoder wählbar: **AUTO** (Farbe nach Funktion) oder AUS, ROT, ORANGE, GELB, GRUEN, CYAN, BLAU, LILA, WEISS.
- AUTO: SEITE weiß, PATCH blau, KANAL lila, AUS dunkel, PARAMETER nach Gruppe.
- Jetzt auch an den Quads (bisher nur M5Stack, feste Farben). Gesendet wird nur bei Änderung, weil jede Quad-LED zwei I2C-Zugriffe kostet.

### Encoder-Sets A/B/C
- Drei komplette Belegungen (Funktion, Optionen, Taster, LED).
- Umschalten unter SETUP › ENCODER › SET (drehen, Druck aktiviert) oder per Taster-Funktion **ENC-SET >**.
- Ein neues Set startet als Kopie. Das aktive Set wird beim Speichern mitgesichert.

### Sonst
- Ab Werk Q5–Q8 = PATCH K5–K8 (bisher AUS). Gespeicherte Stände behalten ihre Belegung, unbekannte Einträge werden AUS.
- Die bisherige Taster-Unterseite entfällt, der Taster steht jetzt auf der Encoder-Seite.

### Test in der Simulation (26.10.2026)
M5Stack + zwei Quads + Single, beide Sprachen, je 65 Prüfungen: Erkennung, LED-Indizes und -Farben, Übersicht und Sprung per Drehen, alle Funktionen, PATCH K12/AKTUELL/Kategorie/Favoriten/Drumkits, AUF DRUCK mit Vormerken und Laden, KANAL, Parameter-Gruppen, Sets (Taster, Menü, Speichern, Neustart), Übernahme eines v13.23-Stands, ohne Zusatz-Encoder, M5 + ein Quad. Die AUDIO-IN-Tests (v13.22) laufen weiter durch.

## Auf der Hardware zu prüfen
1. Leuchten die Quad-LEDs in der richtigen Farbe am richtigen Encoder?
2. Springt der Cursor beim Drehen in SETUP › ENCODER auf die richtige Zeile?
3. Bleibt der Takt stabil, wenn viele Encoder belegt sind (I2C-Last)?
