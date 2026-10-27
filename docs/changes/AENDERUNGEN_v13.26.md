# Dolphin Selector 3 – Änderungen v13.26

Stand 27.10.2026 · Basis: v13.25

## Neu: MIDI-Monitor

Anlass: Am 27.10.2026 reagierten die Pads und Slices auf dem PAD-KANAL nicht auf die Noten vom KeyStep, obwohl der Slot spielt und der KeyStep richtig sendet. In der Simulation funktioniert derselbe Weg. Mit dem Monitor sieht man direkt am Board, ob und wie die Noten beim Sketch ankommen.

**SETUP › MIDI › MONITOR** (rechts die Zahl der empfangenen Nachrichten):

- Die letzten 8 Ereignisse, neuestes oben: Kanal (`K11`), Art (`N` Note-on, `CC`, `PC`) und Nummer.
- Rechts, was der Sketch damit gemacht hat:
  - `PAD S1` – Pad ausgelöst
  - `SLICE 3` – Slice ausgelöst
  - `KANAL 1` – normale Note für Kanal 1 (Synth, Arp, MIDI>CV …)
  - `S2 LEER`, `S2 LAEDT` … – Pad- bzw. Slice-Note erkannt, aber der Slot spielt nicht
  - `S1 KEINE SLICE` – Slice-Note erkannt, der SLICE-SLOT hat aber keine bzw. zu wenige SLICES
- Oben rechts zählt alle empfangenen Nachrichten, auch MIDI-Clock. Steht dort 0, kommt gar nichts beim Sketch an.
- Druck leert die Liste und den Zähler.
- Ohne Ereignisse steht dort „WARTE AUF MIDI“ und der eingestellte PAD-KANAL.

Kosten: ein Zähler und eine Liste mit 8 Einträgen, gezeichnet wird nur, solange die Seite offen ist.

## Auf der Hardware zu prüfen
1. Monitor öffnen, KeyStep auf Kanal 11, Noten 36–51 spielen: Was steht links (Kanal, Note) und rechts (Aktion)?
