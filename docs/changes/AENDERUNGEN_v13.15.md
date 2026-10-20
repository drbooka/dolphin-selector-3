# Dolphin Selector 3 – Änderungen v13.15

Stand 19.10.2026 · Basis: v13.14

## Neu

**M5Stack 8-Encoder und Adafruit Quad #5752 gleichzeitig**
Bisher wurde nur eines der beiden Geräte genutzt (M5Stack hatte Vorrang). Jetzt werden alle Zusatz-Encoder erkannt und haben feste Plätze:

| Platz | Gerät |
|---|---|
| E1–E8 | M5Stack 8-Encoder |
| Q1–Q4 | erster Adafruit Quad #5752 |
| Q5–Q8 | zweiter Quad (falls vorhanden) |

Der Single #5880 bleibt reine Navigation. Die Zuordnung bleibt gespeichert, auch wenn ein Gerät einmal nicht angeschlossen ist.

**Patch-Wechsel per Encoder: PATCH K1 … PATCH K4**
Neue Funktionen in der Encoder-Zuordnung (direkt nach SEITE). Jeder Zusatz-Encoder kann sie bekommen.
- Drehen wechselt den Patch von Kanal 1–4 im laufenden Betrieb. Geladen wird entprellt wie im Patch-Browser (nach 120 ms Ruhe), der Sequencer läuft weiter.
- Die Einblendung zeigt Kanal, Familie, Nummer und Namen, z. B. `K1 JUNO 012` / `Clock Chimes`.
- Schnelles Drehen springt in 4er-Schritten.
- Normale Kanäle blättern durch Juno, DX7, Piano und AMYB (ohne „kein Patch“). Liegt auf dem Kanal ein Drumkit, wird nur durch die Drumkits geblättert.
- Ist der Kanal der CHROM.-Kanal des Samplers, erscheint `K1 SAMPLER` statt eines Wechsels.
- Ein Kanal ohne Patch beginnt beim ersten Patch der Liste.

**SETUP › ENCODER**
Oben steht **GERAETE** (z. B. `M5+QUAD`), dann DREHRICHTUNG und alle angeschlossenen Encoder E1–E8 und Q1–Q8.

## Werkswerte

- E1–E8 unverändert (E1–E4 SEITE, E5 Master, E6 Level, E7 Reverb, E8 Echo).
- **Q1–Q4 = PATCH K1–K4**, Q5–Q8 = AUS.
- Ein gespeicherter Stand von v13.14 wird übernommen; Q1–Q8 bekommen beim ersten Start die Werkswerte.

## SEITE auf dem Quad

Ein Quad-Encoder auf SEITE steuert wie früher (Quad allein) die ersten vier Werte der Seite: Q1 = 1. Wert … Q4 = 4. Wert (Q5–Q8 ebenso).

## Bedienungsanleitung, Abschnitt „Zusatz-Encoder“ (neu)

> Unterstützt werden ein M5Stack 8-Encoder (E1–E8) und bis zu zwei Adafruit Quad (Q1–Q4, Q5–Q8), auch gleichzeitig. Jeder Encoder ist frei belegbar (SETUP › ENCODER):
> - **SEITE**: steuert die ersten Werte der gerade offenen Seite (E1–E8 bzw. Q1–Q4 = 1.–4. Wert).
> - **PATCH K1–K4**: wechselt den Patch von Kanal 1–4 live.
> - **Fester Parameter**: z. B. Master, Cutoff, Reverb. Beim Drehen erscheint kurz der Wert.
> - **AUS**: wird nicht abgefragt (spart I2C-Zeit).

Menübaum: `ENCODER ─► GERAETE · DREHRICHTUNG · E1–E8 · Q1–Q8`

## Auf der Hardware zu prüfen

- M5Stack und Quad zusammen: erscheinen beide unter GERAETE, drehen E- und Q-Encoder das Richtige?
- Lesezeit: jeder belegte Encoder wird pro Bedienungs-Durchlauf abgefragt. Bei Hängern in der Bedienung unbenutzte Encoder auf AUS stellen; SETUP › INFO › BEDIENUNG MAX zeigt die Zeit.
- Patch-Wechsel während der Wiedergabe: Gibt es beim Laden eines Patches einen hörbaren Aussetzer auf dem Kanal?

## Dateien

- `sketch.py` – fürs Board, ohne Kommentare (~240 KB)
- `sketch_src.py` – kommentierte Fassung (~298 KB), nicht zum Übertragen
