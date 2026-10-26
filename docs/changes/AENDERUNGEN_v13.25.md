# Dolphin Selector 3 – Änderungen v13.25

Stand 26.10.2026 · Basis: v13.24

## Neu: Kalibrierung der CV-Eingänge

Anlass: Beim VCO-Test (26.10.2026) lag die Tonhöhe stark daneben. Messungen ergaben, dass OUT1 ab Werk etwa 0,3 V zu hoch ausgab (jetzt mit OFFSET −0,312 / SKALA 0,984 kalibriert) und IN1 etwa 0,19 V zu wenig misst (1,00 → 0,81 V, 3,00 → 2,80 V). Für die Eingänge gab es bisher keine Kalibrierung.

**MODULAR › KALIBRIERUNG** hat jetzt zusätzlich:

| Eintrag | Wirkung |
|---|---|
| **IN1 OFFSET · IN1 SKALA** | gemessen = roh × SKALA + OFFSET (±1 V, 0,8–1,25) |
| **IN2 OFFSET · IN2 SKALA** | dasselbe für IN2 |
| **IN1 ABGLEICH** | Kabel OUT1 → IN1, Druck: Das Board gibt 1 V und 3 V auf OUT1 aus, mittelt je 0,3 s und trägt OFFSET/SKALA ein |
| **IN2 ABGLEICH** | dasselbe mit Kabel OUT1 → IN2 |
| **IN WERKSWERTE** | IN1/IN2 zurück auf 0 / 1.000 (mit Rückfrage) |

Oben auf der Seite stehen IN1, IN2 (kalibriert, drei Nachkommastellen) und OUT1 live.

**Wichtig:** Erst OUT1 kalibrieren (Multimeter, TESTSPANNUNG 0 V / 4 V), dann den Abgleich drücken – der Abgleich nimmt OUT1 als Referenz.

### Wo die Eingangs-Kalibrierung wirkt
- Alles, was der Sketch selbst liest: CV-Monitor, QUANTIZE, Grids per CV, FOLD MOD (CV LFO und VCO), VCO-QUANT, Anzeige auf der VCO-Seite.
- **VCO im Modus FREI:** AMY liest den Eingang roh. Deshalb wird die Kalibrierung in die AMY-Werte eingerechnet: `ext`-Koeffizient × SKALA, OFFSET als Faktor in `const`. Ebenso bei FM und PWM über MOD IN.
- **GATE+PITCH:** Tonhöhen-Skala und -Versatz (IN2) im `freq`-Koeffizienten bzw. `cv_trigger`, die Gate-Schwellen (IN1) umgerechnet.
- Nicht: CV1>FILTER (nur Steuerung der Filterfrequenz, Genauigkeit unkritisch).

### Abgleich-Meldungen
- `IN1 OK +0.186V x1.005` – eingetragen.
- `KEIN SIGNAL?` – zwischen 1 V und 3 V hat sich am Eingang kaum etwas geändert: Kabel prüfen. Nichts wird geändert.
- `WERTE UNPLAUSIBEL` – Ergebnis außerhalb ±1 V / 0,8–1,25: nichts geändert.

### Test in der Simulation (26.10.2026)
Mit nachgebautem Fehler wie gemessen (IN1 = 0,995 × U − 0,185), beide Sprachen: Rohwert 0,81 bei 1 V, Abgleich ergibt OFFSET +0,186 / SKALA 1,005, danach 0–4 V auf ±3 mV genau; ohne Kabel keine Änderung; VCO: ext0 und const korrekt, 3 V ergeben genau 3 Oktaven; PWM; GATE+PITCH (Juno und DX7); Speichern, Neustart, alter Zustand, Werkswerte. Encoder- und AUDIO-IN-Tests laufen weiter durch.

## Auf der Hardware zu prüfen
1. **IN1 ABGLEICH** mit Kabel OUT1 → IN1: Meldung und Werte notieren (erwartet etwa +0,19 V / 1,005).
2. Danach auf der MODULAR-Seite: OUT1 = 1,00 → IN1 ≈ 1,00; OUT1 = 3,00 → IN1 ≈ 3,00.
3. VCO-Tracking erneut (MIDI>CV, OUT1 → IN1, C1 bis C5 auf der VCO-Seite): Cent nahe 0, Rest mit VCO FEIN / V/OKT.
4. IN2 ebenso.
