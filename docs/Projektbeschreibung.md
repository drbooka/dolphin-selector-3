# Dolphin Selector 3 – Projektbeschreibung

Stand 20.10.2026 · Sketch-Version 13.19 (13.18 auf der Hardware bestätigt)

## Ziel

Aus einem **AMYboard** (ESP32-S3 mit der Synthesizer-Engine AMY, MicroPython) wird eine vollwertige Eurorack-Groovebox, die komplett am Modul bedienbar ist, über OLED, Encoder und Joystick. Sie vereint:

- einen 16-kanaligen Multitimbral-Synth (Juno-60, DX7, Piano, AMYboard-Default, 7 GM-Drumkits, eigene DX7-Bänke von der SD-Karte),
- einen Sequencer mit 4 Spuren (MANUAL/EUCLID/SKALA/ARP), einer 303-Acid-Spur und einer Drum-Spur (8 Instrumente, Grids-Generator, CV-Trigger), tick-genau über AMYs eigenen Sequencer,
- Effekte und Distortion pro Bus, Distortion für die 303, Szenen mit Morph,
- einen Sampler wie eine Groovebox: 8 Slots, WAVs von der SD-Karte, Aufnahme (LINE/MIX) mit Speichern auf SD, zerstörungsfreies Trimmen, Hüllkurve und Filter pro Slot, TAKT-SYNC (Time-Stretch) und SLICES,
- eine Eurorack-Anbindung über CV-Ein- und -Ausgänge (1 V/Okt, Gate, LFO, Hüllkurve, Quantizer, Drum-Trigger).

Einsatz im Studio-Setup mit Doepfer-Modulen, Arturia KeyStep Pro, Roland TR-8S und Tascam Model 12.

## Hardware

| Teil | Funktion |
|---|---|
| AMYboard (ESP32-S3) | Klangerzeugung, MIDI, CV IN 1/2 (−10 … +6,3 V), CV OUT 1/2 (±10 V), SD-Slot |
| Adafruit 1,5" OLED 128×128 #4741 | Anzeige, 16 Graustufen, I2C |
| Adafruit I2C Rotary Encoder #5880 | Navigation (Drehen/Drücken) |
| M5Stack 8-Encoder | optional: E1–E8 frei belegbar |
| Adafruit Quad #5752 (bis zu 2) | optional: Q1–Q4 / Q5–Q8 frei belegbar, auch zusammen mit dem M5Stack |
| M5Stack I2C Joystick U024 (0x52), Adafruit ANO | optional |
| microSD-Karte (FAT32, ≤ 32 GB) | Zustand, Szenen, WAV-Samples, Aufnahmen, WLAN-Zugangsdaten |

Geplant ist eine eigene 3D-gedruckte 22HP-Frontplatte, auf der 8-Encoder und Joystick mit Lego-Pins gesteckt werden.

## Software

Eine Datei `sketch.py`, geladen über AMYboard Online. Sie wird **ohne Kommentare** ausgeliefert (~259 KB). Die kommentierte Fassung `sketch_src.py` (~325 KB) ist zu groß zum Übersetzen auf dem Board (v13.11 startete deshalb nicht).

- **Zustand:** Alles Speicherbare liegt in einem Dict `S`. Es wird als JSON gespeichert, mit Werkswerten zusammengeführt (`_merge`) und über `sanitize()` auf gültige Grenzen gebracht. Neue Schlüssel bekommen so bei alten Ständen automatisch ihre Werkswerte.
- **Parameter-System:** Jeder Parameter ist ein `P`-Objekt mit Anzeige, Bereich, Apply-Funktion und Sichtbarkeit. Dieselbe Definition dient der Menüzeile, dem Bearbeitungsring, der Encoder-Zuordnung, den Makros und dem Speichern. Funktionen, die die Firmware nicht kennt (Distortion, `fit`, `store_sample`), werden beim Start geprüft und sonst ausgeblendet.
- **Seiten-Stack:** Startseite → Karussell → Listen-, Bearbeitungs- und Spezialseiten (Patch-Browser, Mixer, Step-Editoren, Drum-Raster, Wellenform-Editor, Modular, Scope).
- **Takt (seit v12.11–12.14):** `tulip.seq_add_callback` ruft den Sequencer alle 2 AMY-Ticks (48 PPQ). Noten werden um VORLAUF (ab Werk 250 ms) im Voraus berechnet und mit `ticks=` auf AMYs Zeitachse gelegt, geplant wird auf `amy.sequencer_ticks()`. Alle Ereignisse liegen auf einem Tag (Tags sammeln sich seit amy#1156), STOP löscht sie auf einmal. CV-Trigger laufen tick-genau über eigene AMY-Synths. Die Bedienung läuft über einen eigenen Timer (40 ms).
- **Display:** Gezeichnet wird nur bei Änderungen. Gesendet werden nur geänderte 8-Zeilen-Bänder, während der Wiedergabe höchstens 2 pro Durchlauf.
- **Encoder (v13.15):** Alle Zusatz-Encoder haben feste Plätze in `S["encf"]` (0–7 = E1–E8, 8–15 = Q1–Q8), damit die Belegung erhalten bleibt, wenn ein Gerät fehlt. Funktionen: SEITE, fester Parameter, PATCH K1–K4 (Live-Patchwechsel), AUS. Die Taster (`S["encb"]`, v13.19) werden über `enc.button(i)` gelesen (gleicher Index wie der Encoder), kurz/lang selbst erkannt.
- **DX7 von SD (v13.19):** `fm.load_syx(daten, voice, patch=1024+Kanal)` legt die Stimme als AMY-User-Patch ab. `S["syx"][Kanal]` = [Datei, Stimme, Name]; beim Start und nach Szenen-Abruf wird neu abgelegt, wenn AMY die Stimme noch nicht kennt.
- **Speichern:** Entprellt (2,5 s, spätestens 10 s), während der Wiedergabe erst bei STOP (spätestens 5 min). Sicheres Schreiben in 512-Byte-Stücken über `.tmp`/`.bak`. Der Speicherort wird beim Start per Schreibtest gewählt (`/sd/` → `/user/` → `/`), die SD-Karte wird selbst eingehängt (Takt/Pull-ups werden bei Fehlern durchprobiert und gemerkt).
- **Drum-Spur (`S["drm"]`):** 8 Instrumente mit eigener Note, Länge (1–32, Polymetrik), Sample-Slot und Slice. Pro Pattern und Instrument ein Text aus 32 Hex-Zeichen (Velocity 0–f).
- **Grids:** Vier Eck-Karten (Gerade, Breakbeat, Halftime, Broken), bilinear per X/Y gemischt, Dichte je Instrument, X/Y per CV IN 1/2 und Joystick.
- **Sampler (v13.0–13.18):** Slots verweisen auf WAVs auf der SD-Karte. Geladen wird nur START…ENDE, mono, in AMYs RAM (Presets 1040–1047), schrittweise im Hintergrund. Aufnahme über AMY `start_sample` direkt in den RAM, danach `tulip.store_sample` auf die Karte. TAKT-SYNC über `fit=N` Ticks (granularer Time-Stretch), SLICES über `phase` (Startframe/2^23) + Note-Off nach der Slice-Länge, mit TAKT-SYNC `fit` = restliche Ticks.

Belegte AMY-Synth-Nummern: 1–16 MIDI-Kanäle, 20/21 CV-LFO/-Hüllkurve, 22–25 Sequencer-MIDI-Ausgabe, 26 303-Stimme, 27 303-MIDI, 28 Drum-MIDI, 29/30 Drum-Trigger OUT1/OUT2, 32–39 Sample-Pads.

## Dateien im Projekt

| Datei | Inhalt |
|---|---|
| `claude/sketch_src.py` | Kommentierte Fassung (aktuell v13.19), zum Lesen |
| `claude/sketch_v13.19.py` | Board-Fassung v13.19 (ohne Kommentare) – diese aufs Board |
| `claude/sketch_v13.15.py` … `v13.18.py` | Sicherungen zum Zurückgehen (v13.18 = letzter bestätigter Stand; ältere Kopien am 20.10.2026 gelöscht) |
| `claude/AENDERUNGEN_v13.15.md` … `v13.19.md`, `v13.0`, `v12.11-12.13` | Änderungslisten |
| `claude/Bedienungsanleitung_v13.md` | Anleitung mit Menübaum (Stand v13.19) |
| `claude/KONZEPT_v12.md` | Bedienkonzept v12 |
| `claude/Projektbeschreibung.md` | Dieses Dokument |
| `claude/Bedienungsanleitung_v12.md` | Alte Anleitung v12.10 (überholt) |

Auf dem Gerät: `dolphin_state.json`, `dolphin_scenes.json` (+ `.tmp`/`.bak`), `/user/sd_freq.txt`, `wifi_credentials.txt`, `/sd/samples/*.wav` (Aufnahmen `RECnnn.wav`), `/sd/dx7/*.syx` (DX7-Bänke).

## Versionsverlauf

| Version | Datum | Änderungen |
|---|---|---|
| v11 | – | Projekt „Selector_2“ / „Amy_Dolphin_CV_9“, Zustand als Textdateien |
| 12.0–12.5 | 24.–25.09.2026 | Neubau: vier Gesten, Karussell, Effekte pro Bus, Szenen/Morph, Patterns, Swing, ARP, Acid-Generator, Kalibrierung; sicheres Speichern mit Ausweichorten |
| 12.6–12.8 | 29.09.2026 | Drum-Spur (8 × bis 32 Steps, Velocity, Polymetrik, Euclid), GRIDS, CV-Trigger, DRUMKIT/SOUND |
| 12.9–12.10 | 29.–30.09.2026 | Review gegen AMY-Doku (Graustufen, PATCH-FX, Drumkits), SD EINBINDEN |
| 12.11–12.14 | 12.–13.10.2026 | Sequencer im Feinraster mit Vorlauf über `ticks=`, Planung auf `amy.sequencer_ticks()`, CV-Trigger über AMY-Synths, Display in Bändern, UI-Timer – **Tempo jetzt stabil (Hardware bestätigt)** |
| 12.15 | 12.10.2026 | JOYSTICK > 303 (Joystick spielt die 303 live) |
| 13.0–13.9 | 13.10.2026 | Sampler als Groovebox (8 Slots, Wellenform-Editor, Pads, chromatisch, Aufnahme); SD-Schreibfehler E5 behoben, SD TEST |
| 13.10–13.14 | 13.–14.10.2026 | Aufnahme über AMY in den RAM (lückenlos), Board-Fassung ohne Kommentare, Speichern der Aufnahme über `tulip.store_sample` |
| 13.15 | 19.10.2026 | M5Stack + Quad #5752 gleichzeitig (E1–E8, Q1–Q8), PATCH K1–K4 per Encoder |
| 13.16 | 20.10.2026 | Distortion (Clip/Fold/Drive/Mix) für 303 und jeden Bus |
| 13.17 | 20.10.2026 | Sampler TAKT-SYNC (`fit`), GRAIN-SUCHE; DRIVE max. 16 |
| 13.18 | 20.10.2026 | Sampler SLICES (4/8/16), SLICE je Drum-Instrument, AUF DRUMS VERTEILEN |
| 13.19 | 20.10.2026 | DX7-Bänke von SD (`fm.load_syx`), Taster der Zusatz-Encoder (kurz/lang), Filter NOTCH/PHASER für Slots, Slices über MIDI (PAD-KANAL Noten 44–59) |

## Offene Punkte (auf der Hardware zu prüfen)

1. 303: Starten die Hüllkurven beim Slide neu?
2. Klingt der Swing bei 1/16 wie erwartet?
3. MIDI>CV nutzt die Software-Variante; ob die Firmware `note_output` CV_GATE mit dem CV-Hook verbindet, ist offen (`NOTE_OUTPUT_CV_NATIVE`).
4. Joystick: Stimmt die Richtung hoch/runter? Sonst `JOY_Y_INVERT = True`.
5. Drum-Trigger: Reicht ein Gate von 1/32 für die A-140-2v?
6. Grids per CV: Stimmt die Richtung an CV IN 1/2?
7. **Kalibrierung nach Firmware-Update prüfen:** Seit dem Update vom 10.08.2026 ist `cv_in` neu kalibriert (ein konstanter Versatz von −0,6 V entfällt) und v1.5-Boards geben den vollen DAC-Bereich aus. Alte OFFSET-/SKALA-Werte unter MODULAR › KALIBRIERUNG können danach falsch sein.
8. **EQ nach Firmware-Update:** Die Firmware hat das Vorzeichen im EQ-Bassband korrigiert. Das PUNCH-Profil auf dem Drum-Bus kann danach bassiger klingen als gewohnt.

## Stand der Firmware-Neuerungen (Discord #announcements bis 12.09.2026, GitHub bis v1.2.200)

Bereits genutzt: `ticks=` statt `time=`/`sequence=` (kein Altcode im Sketch), sich sammelnde Sequencer-Tags, Distortion, `fit`/`fit_search`, `phase` als Startpunkt, PCM-Modi, mehrere Encoder-Boards an einem Bus, `store_sample`, Render-Last-Failsafe, Bus-Effekte.

Automatisch mit neuer Firmware (keine Sketch-Änderung nötig): sauberes PCM-Retrigger mit kurzem Crossfade (amy#1223), Sample-Laden ohne Sequencer-Störung (amy#1210), ~15× schnelleres `amy.message()`, CV-IN als Paar gelesen, MIDI-Clock über TRS ohne USB-Host.

**Test 20.10.2026 (v13.19, Simulation):** Der ganze Sketch lief mit nachgebauten `amy`/`amyboard`/`fm`-Modulen (35 Prüfungen, kommentierte und Board-Fassung): Encoder-/Taster-Erkennung M5Stack + Quad, Filter-Werte, DX7 VON SD (Dateien, Stimmen, Vorschau, User-Patch 1026 abgelegt und geladen, Speichern, Neustart, Abbrechen, fehlende Datei), Taster kurz/lang (Mute, Patch-Browser, Drum-Step, START/STOP), MIDI-Slices (Startpunkt, Ende über Tag 210), Übernahme eines v13.18-Stands, alle neuen Seiten zeichnen. Auf der Hardware steht der Test aus.

## Nächste Ideen

- NOTCH/PHASER auch als Filtertyp für Synth-Kanäle (Juno/AMYB).
- Ratchets (2er-Roll pro Step), Wahrscheinlichkeit pro Drum-Instrument, Fill-Modus.
