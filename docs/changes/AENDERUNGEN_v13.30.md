# Dolphin Selector 3 – Änderungen v13.30

Stand 28.10.2026 · Basis: v13.29

## Neu: Bildschirmschoner mit Delfinen

Der Bildschirmschoner zeigt jetzt acht Bilder, die auf die Musik reagieren. Sie laufen zufällig nacheinander. Nach einer einstellbaren Zeit übernimmt ein ruhiges Leerlauf-Signal. Alles liegt unter **SETUP › DISPLAY › SCHONER-BILD**.

| Bild | Was passiert | Reagiert auf |
|---|---|---|
| **SPRUNG** | Delfin springt aus drei Wellenlinien, mit Spritzern beim Ein- und Auftauchen | läuft: in den ersten 2 Schlägen jedes Takts, sonst alle 6 s |
| **SONAR** | Radarstrahl mit Nachleuchten, Delfine leuchten als Echo auf und verblassen | Bassdrum (Zeile 1 der Drum-Spur) = Ping-Ring; ohne Bassdrum jeder Schlag |
| **TUNNEL** | sechs Rechtecke rasen in die Tiefe, der Delfin schwebt in der Mitte | Tempo, jede Bassdrum gibt einen kurzen Schub |
| **TERMINAL** | fallender Hex-Code, ASCII-Delfin (aus dem Pixelbild erzeugt), Zeile `> K1 120BPM_` | echte MIDI-Bytes (Clock nur jede 24.), sonst Zufallswerte gedimmt |
| **FLYER** | Rave-Plakat mit Name, Raster-Delfin, SOUNDSYSTEM, BPM und Kanal | drei Layouts, neues alle 4 Takte; Strobo-Invert des Namensbalkens auf Takt 1 |
| **ACID-SPUR** | Delfin surft auf dem 303-Pattern: Noten = Höhen, Slides = Rampen, Accents = Wellenberge | 303-Pattern und Takt; steht die 303 oder ist sie stumm, kommt SPRUNG |
| **SPEKTRUM** | 12 Frequenzbalken (Goertzel über den Audio-Ausgang) mit Spitzenmarken, Flosse auf dem lautesten | Audio-Ausgang; ohne Ausgangspuffer Balken nach Schlag und Zufall |
| **WAREHOUSE** | sieben Laserlinien fächern von oben, zwei Delfin-Schatten ziehen durch den Nebel | Ursprung und Richtung wechseln jeden Takt |
| *Leerlauf-Signal* | langsam pulsierender Delfin-Umriss (8 s), jede Minute ein neuer Platz, niedrigster Kontrast | übernimmt nach LEERLAUF |

### Einstellungen (SETUP › DISPLAY › SCHONER-BILD)
- **BILD:** ZUFALL (ab Werk), eines der 8 Bilder fest, oder TEXT (bisheriger Schoner).
- **WECHSEL:** 1, 2 (ab Werk), 5 oder 10 min. Im Zufall nie zweimal dasselbe Bild hintereinander.
- **LEERLAUF:** 30 MIN (ab Werk), 1 STD oder 4 STD seit Start des Schoners.
- **KONTRAST:** DUNKEL, MITTEL (ab Werk), HELL. Das Leerlauf-Signal nutzt immer DUNKEL.
- **FLYER:** Name auf dem Flyer, Zeichenrad, bis 10 Zeichen (ab Werk DOLPHIN).
- **Auswahl** (= IM ZUFALL =): jedes Bild einzeln AN/AUS. Sind alle aus, läuft TEXT.
- **JETZT ZEIGEN:** startet den Schoner sofort.
- **SCHONER NACH** (SETUP › DISPLAY) bestimmt wie bisher, wann er startet.

### Takt und I2C
- Während der Wiedergabe höchstens ein Bild alle 400 ms, gesendet mit dem üblichen Budget von 2 Bändern je UI-Durchlauf. Im Stillstand alle 200 ms mit höchstens 4 Bändern je Durchlauf. Ohne Band-Modus (UPDATE VOLL) 1 s bzw. 400 ms.
- Ein neues Bild wird erst gezeichnet, wenn das vorige ganz draußen ist.
- Ganzzahl-Rechnung mit Sinus-Tabelle, damit MicroPython pro Bild wenig Speicher anlegt.
- Die Zeichenzeit zählt in SETUP › INFO › ZEICHNEN MAX mit.

### Neuer Delfin
Ein neues Pixelbild (32 × 14) mit runder Stirn, Schnabel, nach hinten geneigter Rückenflosse, Brustflosse und Schwanzflosse. Es lässt sich skalieren (1–3×), spiegeln, neigen und als Fläche, Umriss oder Rasterpunkte zeichnen.

## Größe
- Board-Datei `sketch.py`: ca. 334 KB (v13.29: 317 KB, v13.28: 308 KB).
- Kommentierte Fassung: ca. 423 KB (v13.29: 403 KB).
- RAM im Betrieb: Pixelbild, Sinus-Tabelle und Zustand eines Bildes zusammen wenige KB; die Bilder zeichnen in den vorhandenen Bildspeicher.

## Test in der Simulation (28.10.2026)
Beide Sprachen, kommentierte und Board-Fassung, mit nachgebautem Display (Graustufen-Puffer und SSD1327-Bänder):
- Jedes Bild 3 s mit laufendem Sequencer (Bassdrum-Pattern, 303, Audio-Ausgang, MIDI-Bytes): zeichnet ohne Fehler, Band-Budget eingehalten.
- Zufall über 20 Minuten: alle 8 Bilder kamen vor, nie zweimal dasselbe hintereinander; eine eingeschränkte Auswahl wird beachtet.
- Leerlauf-Signal nach 30 min und bleibt; leere Auswahl → TEXT; Start nach SCHONER NACH; Drehen weckt.
- Menü-Zeilen passen, Flyer-Name wird übernommen.
- LED-Tests aus v13.29 und Rundgang durch alle 66 Menüseiten ohne Fehler.

## Auf der Hardware zu prüfen
1. Sehen die Bilder gut aus (Schrift 8×8, Delfin, Kontrast MITTEL)? JETZT ZEIGEN, BILD fest einstellen zum Durchschauen.
2. Bleibt der Takt mit laufendem Schoner stabil? SETUP › INFO › BEDIENUNG MAX und ZEICHNEN MAX notieren, vor allem bei SPEKTRUM.
3. Startet die Board-Datei (334 KB) und die kommentierte Fassung (423 KB)? RAM FREI notieren.
