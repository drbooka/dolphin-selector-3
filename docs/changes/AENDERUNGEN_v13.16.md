# Dolphin Selector 3 – Änderungen v13.16

Stand 20.10.2026 · Basis: v13.15

## Neu: Distortion

Grundlage ist das AMY-Update (amy#1116, amy#1134, AMY 1.2.135 → 1.2.166). Jeder Oszillator und jeder Bus hat jetzt einen Waveshaper mit Soft-Clip und Wavefolder. Die beiden lassen sich stapeln und sitzen **nach der Hüllkurve und vor dem Filter**.

| TYP | Wirkung |
|---|---|
| AUS | keine Verzerrung |
| CLIP | weiche Sättigung, warm bis kräftig |
| FOLD | Wavefolder, metallisch, obertonreich |
| CLIP+FOLD | beides nacheinander |

- **DRIVE** (1–20, logarithmisch): wie stark das Signal in die Verzerrung gefahren wird.
- **MIX** (0–1): Anteil des verzerrten Signals (0 = trocken, 1 = voll verzerrt).

### 303
SEQUENCER › 303 ACID bekommt die Einträge **DISTORTION · 303 DRIVE · 303 DIST MIX**, eingereiht nach SLIDE.
- Weil die Verzerrung vor dem Filter sitzt, ergibt das die klassische verzerrte Acid-Linie: Cutoff, Resonanz und ENV MOD formen den verzerrten Klang.
- **DRIVE als Joystick-Ziel:** JOY X oder JOY Y = DRIVE. Die Auslenkung verändert den Drive um bis zu ±2 Oktaven (Faktor 4). Der Joystick-Knopf übernimmt auch den Drive.
- **303 DRIVE** lässt sich als Makro und als fester Zusatz-Encoder belegen.
- MORPH A>B blendet 303 DRIVE und DIST MIX mit. Ältere Szenen ohne diese Werte bleiben beim aktuellen Stand.

### Effekte pro Bus
EFFEKTE › **DISTORTION** (vor MASTER) mit **TYP · BUS DRIVE · DIST MIX**, getrennt für Bus 0–3.
- Gut für die Drums auf Bus 1: CLIP mit Drive 2–4 macht sie dichter und lauter.
- **BUS DRIVE** lässt sich als Makro und als fester Zusatz-Encoder belegen.
- CRUSH gehört in AMY zur selben Stufe. Bei TYP AUS bleibt CRUSH unverändert. Bei TYP CLIP/FOLD wirkt DIST MIX auch auf den Crush-Anteil.
- BUS RESET setzt die Distortion des Busses auf AUS. Szenen speichern sie mit.

### Ohne passende Firmware
Beim Start wird geprüft, ob die Firmware die Distortion-Befehle kennt. Wenn nicht, bleiben alle neuen Einträge ausgeblendet und der Rest läuft wie in v13.15. **SETUP › INFO › DISTORTION** zeigt JA oder NEIN.

## Werkswerte
Alles auf AUS (Drive 4, Mix 1 als Startwerte, sobald ein TYP gewählt wird). Ein gespeicherter Stand von v13.15 wird übernommen.

## Auf der Hardware zu prüfen
- SETUP › INFO › DISTORTION = JA?
- 303 mit CLIP, Drive 4–8: klingt die Verzerrung vor dem Filter (Cutoff-Sweep formt sie)?
- Pegel: Bei hohem Drive kann die 303 deutlich lauter werden, dann 303 LEVEL zurücknehmen.
- Bus-Distortion zusammen mit CRUSH: verhält sich DIST MIX wie beschrieben?
- RAM: `sketch.py` ist rund 3 KB größer (243 KB). SETUP › INFO › RAM NACH BOOT mit v13.15 vergleichen.

## Dateien
- `sketch.py` – fürs Board, ohne Kommentare (~243 KB)
- `sketch_src.py` – kommentierte Fassung (~302 KB), nicht zum Übertragen
