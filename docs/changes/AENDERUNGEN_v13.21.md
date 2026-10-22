# Dolphin Selector 3 – Änderungen v13.21

Stand 22.10.2026 · Basis: v13.20

## Neu: VCO – das AMYboard als eigenständiger Oszillator

**MODULAR › VCO** macht aus dem AMYboard ein Oszillator-Modul fürs Rack. Es klingt dauerhaft, braucht weder MIDI noch Gate und wird per 1 V/Okt über CV IN 1 oder IN 2 gespielt. Hüllkurve und Lautstärke kommen wie bei einem normalen VCO aus dem Rack (A-140-2v, A-130-2v), Filter aus A-120/A-103.

Die Tonhöhe rechnet AMY selbst: Die Spannung am Eingang geht als `ext0`/`ext1`-Koeffizient direkt in `freq` (wie bei GATE+PITCH). Python ist nicht im Signalweg, das Tracking hängt also nicht am UI-Takt.

| Eintrag | Wirkung | Werk |
|---|---|---|
| **VCO** | AN/AUS | AUS |
| **1V/OKT IN** | AUS · IN1 · IN2 | IN1 |
| **TONHOEHE** | FREI (stufenlos, in AMY) · QUANT (auf SKALA gerastet, in Python) | FREI |
| **SKALA** | eigene Skala für QUANT (unabhängig von MODULAR › SKALA) | CHROM |
| **GRUNDTON 0V** | Note bei 0 V | C1 (wie MIDI>CV) |
| **VCO FEIN** | ±100 Cent | 0 |
| **V/OKT** | Tracking-Abgleich 0.950–1.050 | 1.000 |
| **WELLE** | SIN · TRI · SAW · PULS | SAW |
| **VCO PW** | Pulsbreite 0.05–0.95 (nur PULS) | 0.50 |
| **VCO SUB · SUB OKTAVE** | Rechteck-Sub −1/−2 Oktaven | 0 · −1 |
| **VCO OSZ 2 · INTERVALL · VCO DETUNE** | zweiter Oszillator mit gleicher Welle, ±24 HT, 0–50 Cent | 0 · 0 · 7 ct |
| **MOD IN · MOD ZIEL · VCO MOD** | zweiter CV-Eingang auf FM / PWM / FOLD | AUS |
| **FOLD · VCO DRIVE · FOLD MIX** | Wavefolder am Haupt-Oszillator | AUS · 2 · 1 |
| **VCO LEVEL · PAN · BUS** | Ausgang und Effekt-Bus | 0.8 · Mitte · 0 |

### Aufbau in AMY
- Eigener Synth **40** (geprüft wie bei den Pads). Kennt die Firmware keine Synths über 31, nimmt der VCO 31, sofern die Pads ihn nicht brauchen, sonst zeigt MODULAR „FEHLT“.
- Drei Oszillatoren als `chained_osc`-Kette: osc 0 Haupt-Welle (trägt den Wavefolder), osc 1 Sub-Rechteck, osc 2 zweiter Oszillator. Ein `note`-Befehl startet alle drei, danach laufen sie als Dauerton.
- `freq = {const: Hz bei 0 V, note: 0, bend: 0, ext0/ext1: Okt pro Volt}`. Die gespielte Note spielt damit keine Rolle; GRUNDTON, FEIN, INTERVALL und DETUNE stecken in `const`, ohne Neuanschlag.
- Pegel je Oszillator über `amp const`, normiert (`1 / (1 + 0,5 · (SUB + OSZ 2))`), damit beide voll aufgedreht nicht übersteuern.
- **FM** (`ext` auf `freq`, VCO MOD 1 = 1 Okt/V) und **PWM** (`ext` auf `duty`, 0,08 pro Volt) laufen in AMY, pro Audio-Block. **FOLD** verschiebt den Drive alle 30 ms (wie FOLD MOD beim CV LFO).
- **QUANT** liest den Eingang bei jedem UI-Durchlauf (~40 ms), rastet ihn auf die Skala und setzt `const` neu. Eine kleine Hysterese (0,2 Halbtöne) verhindert Flattern an der Grenze zwischen zwei Tönen.

### Seite
Oben stehen die aktuelle Note (groß), die Frequenz und die Abweichung in Cent mit Balken – damit lässt sich der VCO wie mit einem Stimmgerät abgleichen. Darunter zeigt eine Linie zwei Perioden der Welle mit Sub und Fold (Näherung).

### Sonst
- `quantize()` nimmt optional einen Skalen-Index (für den VCO).
- Der VCO gehört zu den Szenen (älter gespeicherte Szenen lassen ihn unverändert). PANIC lässt ihn weiterlaufen.
- AUDIO MONO setzt auch den VCO auf Mitte.
- Neu als Makro/Encoder: VCO FEIN, VCO PW, VCO SUB, VCO OSZ 2, VCO DETUNE, VCO DRIVE, VCO MOD, VCO LEVEL.
- SETUP › INFO › VCO-SYNTH zeigt die verwendete Synth-Nummer.
- Board-Datei ca. 13 KB größer (≈ 278 KB).

## Auf der Hardware zu prüfen

1. **Startet der VCO?** MODULAR › VCO › VCO = AN. Es muss sofort ein Sägezahn auf C1 (ca. 33 Hz) zu hören sein. INFO zeigt VCO-SYNTH 40.
2. **Tracking:** MODUS MIDI>CV, OUT 1 per Kabel auf IN 1, VCO-Seite offen lassen und auf dem KeyStep C1 und C5 spielen. Die Seite muss C1 bzw. C5 zeigen. Weichen die Cent bei C5 ab, V/OKT nachstellen. Bleibt die Tonhöhe trotz Spannung stehen, greift `ext0` hier nicht – dann bitte melden.
3. **Kette:** VCO SUB und VCO OSZ 2 hochdrehen. Sub muss eine Oktave tiefer dazukommen, OSZ 2 schweben (DETUNE 7 ct). Ist nur die Haupt-Welle zu hören, wird `chained_osc` im Synth-Modus nicht übernommen.
4. **Pegel:** SUB und OSZ 2 auf 1.0, VCO LEVEL 0.8 – verzerrt es am Ausgang?
5. **Knacken:** beim Wechsel der WELLE oder beim Ändern von GRUNDTON.
6. **QUANT:** langsame Rampe (z. B. CV LFO SAW auf OUT1 → IN1) muss als Tonleiter laufen, ohne Flattern an den Übergängen.
