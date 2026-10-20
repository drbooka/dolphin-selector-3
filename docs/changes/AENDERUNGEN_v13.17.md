# Dolphin Selector 3 – Änderungen v13.17

Stand 20.10.2026 · Basis: v13.16 (Distortion auf der Hardware bestätigt)

## Neu: TAKT-SYNC im Sampler

Grundlage ist AMY `fit` (amy#1129, amy#1131), ein granularer Time-Stretch für PCM-Presets im RAM. Laut AMY-Doku (`docs/api.md`, „Sampler timing and time-stretch (experimental)“):
- `fit=N`: das Sample dauert genau N Sequencer-Ticks, bei gleicher Tonhöhe
- `fit=-1`: aus
- `fit_search`: Suchfenster für die Grain-Ausrichtung (ab Werk 64, 0 = aus)

SAMPLER › SLOT bekommt nach MODUS:
- **TAKT-SYNC:** AUS, 1–3 und 6 Schläge, 1–10 Takte (48 Ticks pro Schlag). Der Slot dauert dann immer genau so lang. Er folgt dem Tempo, auch bei Tempowechseln während der Note, und behält dabei seine Tonhöhe. TUNE, FEIN und der CHROM.-Kanal transponieren, ohne die Dauer zu ändern.
- **SYNC AUS LAENGE:** zeigt rechts den Vorschlag aus Länge und aktuellem Tempo, Drücken übernimmt ihn. Beispiel: 2 s bei 120 BPM ergibt 1 TAKT.
- **GRAIN-SUCHE** (0–512): nur sichtbar, wenn TAKT-SYNC an ist. Höhere Werte können bei Bass sauberer klingen.
- **Aufnahme mit EINHEIT TAKTE** setzt TAKT-SYNC automatisch auf die aufgenommene Länge. Der Loop bleibt so auch bei späteren Tempowechseln im Takt.

Einschränkungen:
- Nicht im Modus LOOP: Das Zusammenspiel von Loop-Punkten und Stretch ist in AMY nicht beschrieben. Bei LOOP wird `fit=-1` gesendet und die Zeile ausgeblendet.
- Rechenzeit: Laut AMY etwa 2,5-mal so viel wie normales Abspielen, je spielendem Slot.
- Kennt die Firmware `fit` nicht, bleiben die Einträge ausgeblendet. **SETUP › INFO › TAKT-SYNC** zeigt JA oder NEIN.

## Korrektur
- **Distortion DRIVE** geht jetzt bis 16 statt 20. AMY begrenzt `dist_drive` laut api.md auf 1/16–16. Werte über 16 aus v13.16 werden beim Laden auf 16 gesetzt.

## Auf der Hardware zu prüfen
- SETUP › INFO › TAKT-SYNC = JA?
- Einen Loop mit 2 TAKTE über die Drum-Spur oder den PAD-KANAL spielen und das Tempo ändern: bleibt er im Takt, behält er die Tonhöhe?
- Klang: Drums, Stimme und Bass mit GRAIN-SUCHE 64, 0 und 256 vergleichen.
- CPU-Last mit mehreren synchronisierten Slots gleichzeitig (Statuszeile, FAILSAFE).
- Wie klingt TAKT-SYNC im Modus GATE (Abbruch beim Loslassen)?

## Dateien
- `sketch.py` – fürs Board, ohne Kommentare (~245 KB)
- `sketch_src.py` – kommentierte Fassung (~306 KB), nicht zum Übertragen

Quelle: [AMY api.md](https://raw.githubusercontent.com/shorepine/amy/main/docs/api.md), [amy PR #1230](https://github.com/shorepine/amy/pull/1230)
