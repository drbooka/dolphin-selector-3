# Dolphin Selector 3 – Änderungen v13.18

Stand 20.10.2026 · Basis: v13.17 (TAKT-SYNC auf der Hardware bestätigt)

## Neu: SLICES (Chopping)

**SAMPLER › SLOT › SLICES** AUS / 4 / 8 / 16 teilt den geladenen Bereich (START…ENDE) in gleich lange Stücke. Im Wellenform-Editor zeigen gestrichelte Linien die Grenzen.

**Drum-Spur › SPUR-MENUE › SLICE** (nach SAMPLE): Hier wählt jedes Instrument GANZ oder ein Stück 1–16. Beim Auswählen wird das Stück angespielt. In der Drum-Zeile steht z. B. `1c` für Slot 1, Slice 3.

**SLOT › AUF DRUMS VERTEILEN** (mit Rückfrage):
- legt Slice 1–8 auf Instrument 1–8 (SAMPLE = Slot, LAENGE 16),
- schreibt das Originalmuster ins aktuelle Pattern: Slice i auf Step i × 16 ÷ SLICES. Das geht von einem 1 Takt langen Slot aus.
- Danach spielt die Drum-Spur den Loop wie das Original, und die Steps lassen sich umstellen, mit Euclid, Polymetrik oder GRIDS.

**Zusammen mit TAKT-SYNC** dauert jedes Stück genau TAKT-SYNC ÷ SLICES und folgt dem Tempo, ohne dass sich die Tonhöhe ändert.

## Technik (nach AMY api.md)
- **Start eines Stücks:** `phase` = Startframe / 2^23. `phase` gilt für die nächste Note und wird von ihr verbraucht. Bei Slots mit SLICES wird der Startpunkt deshalb vor jedem Schlag gesendet, auch 0 für GANZ. So kann ein liegengebliebener Wert nie den nächsten Schlag verschieben.
- **Genauigkeit:** AMY überträgt Zahlen mit 6 Nachkommastellen, das sind rund 8 Frames (0,2 ms). Das reicht.
- **Ende eines Stücks:** Note-Off nach der Slice-Länge, über die Drum-Spur tick-genau geplant. Ein neuer Schlag auf demselben Slot schneidet das vorige Stück ab (ein Pad-Synth pro Slot).
- **Mit TAKT-SYNC:** `fit` = restliche Ticks ab dem Startpunkt. Laut api.md muss `fit` die verbleibende Länge sein, sonst läuft der Rest halb so schnell.
- **Note-Offs:** Slots mit SLICES nehmen sie jetzt auch im Modus EINMAL an. GANZ spielt trotzdem bis zum Ende, weil die Drum-Spur dafür kein Note-Off schickt.
- **`sample_offset`** wird nicht gebraucht. Alle Ereignisse des Sequencers fallen ohnehin auf Block-Grenzen, aufeinanderfolgende Stücke schließen also im selben Raster an.

## Einschränkungen
- Nicht im Modus LOOP.
- Stücke spielt nur die Drum-Spur. PAD-KANAL, ANHOEREN und der CHROM.-Kanal spielen weiter das ganze Sample.
- AUF DRUMS VERTEILEN belegt höchstens 8 Instrumente (bei 16 Slices nur 1–8).

## Auf der Hardware zu prüfen
- Einen 1-Takt-Break auf 8 SLICES stellen, TAKT-SYNC 1 TAKT, AUF DRUMS VERTEILEN, START: klingt es wie das Original?
- Übergänge zwischen den Stücken: Klicks? Falls ja, ATTACK/RELEASE des Slots auf 2–5 ms stellen.
- Tempo ändern: bleibt der Break im Raster?
- SLICE im SPUR-MENUE durchdrehen: wird jeweils nur das Stück angespielt?

## Dateien
- `sketch.py` – fürs Board, ohne Kommentare (~249 KB)
- `sketch_src.py` – kommentierte Fassung (~311 KB), nicht zum Übertragen

Quelle: [AMY api.md](https://raw.githubusercontent.com/shorepine/amy/main/docs/api.md), [amy/__init__.py](https://raw.githubusercontent.com/shorepine/amy/main/amy/__init__.py)
