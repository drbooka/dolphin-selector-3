# Dolphin Selector 3 – Änderungen v13.20

Stand 21.10.2026 · Basis: v13.19

## Neu: Wavefolder-LFO am CV-Ausgang

Der Waveshaper aus v13.16 (Clip und Fold) sitzt in AMY an jedem Oszillator. Dazu gehört auch der LFO-Synth 20, den `set_cv_out` auf OUT1/OUT2 legt. Gefaltet wird deshalb direkt in AMY, ohne Rechenlast in Python und ohne Timer-Jitter.

**MODULAR › CV LFO** hat jetzt diese Einträge:

| Eintrag | Wirkung |
|---|---|
| WELLE · RATE · TIEFE | wie bisher |
| **FOLD** | AUS · CLIP · FOLD · CLIP+FOLD |
| **LFO DRIVE** (1–16, log.) | wie weit die Welle zusätzlich in den Folder gefahren wird |
| **FOLD MIX** (0–1) | Anteil der gefalteten Welle (0 = glatt, 1 = voll gefaltet) |
| **FOLD MOD** | AUS · CV IN1 · CV IN2: eine Spannung verschiebt LFO DRIVE |
| **MOD TIEFE** (0–1) | wie stark: 1 = bis ±2 Oktaven (Faktor 4), 5 V = voller Ausschlag |

- **TIEFE liegt vor dem Folder.** Sie bestimmt also auch, wie stark gefaltet wird, ähnlich wie der Eingangspegel eines echten Wavefolders. Beispiel: TIEFE 0.5 × DRIVE 4 → Spitze 2 → die Welle faltet einmal zurück. Die Ausgangsspitze bleibt durch das Falten begrenzt.
- **Vorschau:** Oben auf der Seite zeigt eine Linie eine Periode der Welle nach Tiefe, Drive, Fold und Mix. Rechts oben steht der aktuelle Drive (mit FOLD MOD live). Die Vorschau ist eine Näherung (Dreiecks-Faltung an ±1, harter Clip). AMYs Kennlinien können weicher sein.
- **FOLD MOD** wird alle 30 ms nachgeführt, und nur, wenn FOLD an ist und der LFO wirklich auf einem Ausgang liegt. Der Eingang wird nur gelesen, nicht belegt: CV1>FILTER, Grids usw. können denselben Eingang weiter nutzen. Bei schnellen Drive-Sprüngen kann die Faltung in kleinen Stufen wechseln.
- **LFO DRIVE** lässt sich als Makro und als fester Zusatz-Encoder belegen. Mit dem Encoder in der Hand ist das der klassische „Timbre“-Regler.
- In MODULAR zeigt die Zeile CV LFO den Fold-Typ statt „>“, wenn er an ist.

## Auch für CV ENV

**MODULAR › CV ENV** bekommt **FOLD · ENV DRIVE · FOLD MIX**. Die Hüllkurve wackelt dann beim Anstieg und Abklingen mehrmals hoch und runter. ENV DRIVE ist ebenfalls als Makro/Encoder belegbar.

## Ohne passende Firmware

Ist SETUP › INFO › DISTORTION = NEIN, bleiben alle neuen Einträge ausgeblendet und alles läuft wie in v13.19.

## Werkswerte

FOLD AUS, Drive 4, Mix 1, FOLD MOD AUS, MOD TIEFE 0.5. Ein gespeicherter Stand von v13.19 wird übernommen. Der LFO selbst ist wie bisher nicht Teil der Szenen.

## Auf der Hardware zu prüfen

1. **Faltet AMY auch auf dem CV-Weg?** CV MOD OUT1 = LFO, WELLE SIN, RATE 0.5 Hz, TIEFE 0.5, FOLD = FOLD, LFO DRIVE 4. Am Oszilloskop (oder hörbar über einen VCA/Filter im Rack) müssen pro Periode mehrere Buckel erscheinen. Sieht bzw. klingt alles aus wie vorher, greift `set_cv_out` den Ausgang vor dem Shaper ab. Dann bitte melden, damit ich auf einen anderen Weg umbaue.
2. **Pegel:** Bei TIEFE 1.0 plus Drive: wie hoch sind die Spitzen (bis ±10 V?) Für Eingänge, die nur ±5 V vertragen, TIEFE und DRIVE zurücknehmen.
3. **ENV mit FOLD:** Geht die gefaltete Hüllkurve ins Negative? Das ist bei einer symmetrischen Faltung möglich.
4. **FOLD MOD:** Doepfer-LFO oder Hüllkurve an CV IN1, FOLD MOD = CV IN1: wandert die Faltung mit, ohne hörbares Stufen bei langsamen Raten?
5. **RAM:** `sketch.py` ist rund 4,7 KB größer (264 KB). SETUP › INFO › RAM NACH BOOT mit v13.19 vergleichen.

## Dateien

- `sketch.py` – fürs Board, ohne Kommentare (~264 KB)
- `sketch_en.py` – englische Board-Fassung
- `src/sketch_src.py`, `src/sketch_src_en.py` – kommentierte Fassungen, nicht zum Übertragen
