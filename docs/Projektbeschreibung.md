# Dolphin Selector 3 – Projektbeschreibung

Stand 28.10.2026 · Sketch-Version 13.29 (13.18 auf der Hardware bestätigt, dazu v13.24–v13.27: AUDIO IN, VCO, IN-Kalibrierung, MIDI-Monitor, weiches Umschalten)

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

Eine Datei `sketch.py`, geladen über AMYboard Online. Sie wird **ohne Kommentare** ausgeliefert (~300 KB). Die kommentierte Fassung `sketch_src.py` (~390 KB) läuft inzwischen auch auf dem Board (vom Nutzer bestätigt). Bei v13.11 startete sie noch nicht, weil der Speicher nicht reichte.

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
| `claude/sketch_src.py` | Kommentierte Fassung (aktuell v13.20), zum Lesen |
| `claude/sketch_v13.20.py` | Board-Fassung v13.20 (ohne Kommentare) – diese aufs Board |
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
| 13.20 | 21.10.2026 | Wavefolder für CV LFO und CV ENV (FOLD/DRIVE/MIX in AMY), FOLD MOD über CV IN1/IN2, Vorschau der gefalteten Welle |
| 13.21 | 22.10.2026 | VCO: AMYboard als eigenständiger Oszillator (1 V/Okt an CV IN1/IN2 direkt in AMY, Sub, zweiter Oszillator, Wavefolder, FM/PWM/FOLD per CV, QUANT, Stimmanzeige) |
| 13.22 | 23.10.2026 | AUDIO IN: Stereo-Eingang live durch Gain, Distortion, Filter und die Bus-Effekte (Synths 41/42 mit `AUDIO_IN0/1`), Pegelanzeige, Taster-Funktion, Makros, Statuszeile `IN` |
| 13.23 | 25.10.2026 | I2C-SCAN unter SETUP › ENCODER und INFO › I2C: Adresse, erkannter Typ, Seesaw-Produktnummer (Fehlersuche Quad) |
| 13.24 | 26.10.2026 | Encoder-Menü neu: Übersicht nach Gerät mit Sprung per Drehen, Encoder-Seite mit FUNKTION (AUS/SEITE/PATCH/KANAL/PARAMETER), PATCH für K1–K16 oder AKTUELL mit LISTE und LADEN SOFORT/AUF DRUCK, Parameter in Gruppen, LED-Farbe je Encoder (AUTO/fest), Encoder-Sets A/B/C |
| 13.25 | 26.10.2026 | Kalibrierung der CV-Eingänge (IN1/IN2 OFFSET/SKALA) mit Auto-Abgleich über OUT1, wirkt auch auf VCO und GATE+PITCH im AMY-Weg |
| 13.26 | 27.10.2026 | MIDI-Monitor unter SETUP › MIDI (letzte 8 Ereignisse mit Aktion des Sketches) |
| 13.27 | 27.10.2026 | Weiches Umschalten (Aus-/Einblenden) bei VCO-WELLE und AUDIO-IN-Filter-/Distortion-Typ, VCO › GLAETTUNG für TONHOEHE FREI |
| 13.28 | 27.10.2026 | GLAETTUNG-Stufe LEICHT heißt WENIG (passte nicht in die Zeile). Anleitung DE/EN: Tipps und Tricks, 7 bebilderte Patch-Vorschläge für MODULAR (Bilder unter `docs/img/`) |
| 13.29 | 28.10.2026 | LEDs: Single-LED mit Kanalfarbe, EDIT, TAKT-Blitz, Kanal-Blitz, PANIC-Verlauf und WARNUNG (je Farbe wählbar), Zusatz-Encoder mit ZUSTAND (gedimmt = ohne Wirkung, AUF DRUCK blinkt, Taster-Zustand) und DREH-BLITZ, LED-Farbe KANAL, HELLIGKEIT, IM SCHONER, LED-TEST, INFO › NAV-LED |

## Offene Punkte (auf der Hardware zu prüfen)

1. ~~303: Starten die Hüllkurven beim Slide neu?~~ – am 27.10.2026 bestätigt: Slide gleitet ohne neuen Anschlag.
2. ~~Klingt der Swing bei 1/16 wie erwartet?~~ – am 27.10.2026 bestätigt (60 % und 75 %).
3. MIDI>CV nutzt die Software-Variante; ob die Firmware `note_output` CV_GATE mit dem CV-Hook verbindet, ist offen (`NOTE_OUTPUT_CV_NATIVE`).
4. ~~Joystick: Stimmt die Richtung hoch/runter?~~ – am 27.10.2026 bestätigt (bei JOYSTICK>303 = AN steuert er bewusst die 303 statt der Navigation).
5. ~~Drum-Trigger: Reicht ein Gate von 1/32 für die A-140-2v?~~ – am 27.10.2026 bestätigt, löst zuverlässig aus.
6. ~~Grids per CV: Stimmt die Richtung an CV IN 1/2?~~ – am 27.10.2026 bestätigt (X und Y).
7. ~~**Kalibrierung**~~ – erledigt: Am 26.10.2026 OUT1 mit Multimeter kalibriert (OFFSET −0,312 V, SKALA 0,984 – der Ausgang lag ab Werk 0,3 V zu hoch). Auto-Abgleich (v13.25): IN1 OFFSET +0,169 V / SKALA 1,011, IN2 +0,15 V / 1,010 (gleicher Bauteil-Versatz). OUT2 am 27.10.2026 mit zwei Punkten kalibriert: OFFSET 0,000 V, SKALA 0,942 (gab ab Werk ca. 6 % zu viel aus). Ein defektes Patchkabel hatte zuerst einen toten Eingang vorgetäuscht.
8. ~~**EQ nach Firmware-Update**~~ – am 27.10.2026 geprüft: PUNCH-Profil auf dem Drum-Bus klingt weiterhin passend, keine Änderung nötig.
9. ~~**VCO (v13.21)**~~ – **am 26.10.2026 auf der Hardware bestätigt:** Klang, SUB, OSZ 2, Pegel (sauber auch mit beiden auf 1.0), Tracking nach IN1-Abgleich ohne Steigungsfehler (Rest −12 ct → VCO FEIN +12, Streuung ±8 ct durch Zittern des CV-Eingangs), QUANT mit CHROM/MAJOR sauber und ohne Flattern. Knacken beim Wechsel der WELLE und Zittern im Modus FREI mit v13.27 (Aus-/Einblenden, GLAETTUNG) am 27.10.2026 auf der Hardware behoben. MOD IN mit FM, PWM und FOLD bestätigt.
10. ~~**AUDIO IN (v13.22)**~~ – **am 26.10.2026 auf der Hardware bestätigt** (mit v13.24): Pegelanzeige, Durchlauf, Stereo, Filter, Distortion, Bus-Effekte, Rauschen, Latenz und Ein/Aus in Ordnung. Knacken beim Umschalten von Filter-/Distortion-Typ mit v13.27 am 27.10.2026 auf der Hardware behoben.

11. **Wavefolder CV LFO (v13.20):** am 26.10.2026 bestätigt, dass AMY auch am CV-Ausgang faltet (über VCO-FM hörbar: mehrere Buckel pro Durchgang). FOLD MOD per CV IN1 und ENV mit FOLD ebenfalls bestätigt. Offen (optional): Spitzenpegel bei TIEFE 1.0 + DRIVE mit dem Multimeter.

12. **DX7 VON SD (v13.19):** am 26.10.2026 bestätigt – INFO DX7 SD = JA, Stimmen klingen richtig, Wechsel ohne Stocken, SD-Stimme nach Neustart wieder geladen. Bedienung: kein hörbares Holpern beim schnellen Drehen, BEDIENUNG MAX 132 ms (unter den 250 ms Vorlauf).
13. **Encoder-Menü (v13.24):** am 26.10.2026 mit dem M5Stack bestätigt – Übersicht, Sprung per Drehen, PATCH für beliebigen Kanal, LADEN AUF DRUCK mit Taster, LED-Farben am richtigen Encoder, Sets A/B. Offen: Quad-Teile (LEDs, Q1–Q8), sobald der Ersatz-Quad da ist.
15. **LEDs (v13.29):** Leuchtet die Single-LED (INFO › NAV-LED, LED-TEST)? Alle LEDs am richtigen Encoder? Takt stabil mit TAKT-Blitz (BEDIENUNG MAX)? Läuft die kommentierte Fassung (403 KB) noch an?
14. ~~**Pads/Slices über MIDI (v13.19)**~~ – **am 27.10.2026 bestätigt:** Pads (Noten 36–43) und Slices (44+) auf dem PAD-KANAL funktionieren. Die erste Fehlmeldung lag an der Verkabelung; der MIDI-MONITOR (v13.26) bleibt zur Fehlersuche.

## Stand der Firmware-Neuerungen (Discord #announcements bis 12.09.2026, GitHub bis v1.2.200)

Bereits genutzt: `ticks=` statt `time=`/`sequence=` (kein Altcode im Sketch), sich sammelnde Sequencer-Tags, Distortion, `fit`/`fit_search`, `phase` als Startpunkt, PCM-Modi, mehrere Encoder-Boards an einem Bus, `store_sample`, Render-Last-Failsafe, Bus-Effekte.

Automatisch mit neuer Firmware (keine Sketch-Änderung nötig): sauberes PCM-Retrigger mit kurzem Crossfade (amy#1223), Sample-Laden ohne Sequencer-Störung (amy#1210), ~15× schnelleres `amy.message()`, CV-IN als Paar gelesen, MIDI-Clock über TRS ohne USB-Host.

**Test 20.10.2026 (v13.19, Simulation):** Der ganze Sketch lief mit nachgebauten `amy`/`amyboard`/`fm`-Modulen (35 Prüfungen, kommentierte und Board-Fassung): Encoder-/Taster-Erkennung M5Stack + Quad, Filter-Werte, DX7 VON SD (Dateien, Stimmen, Vorschau, User-Patch 1026 abgelegt und geladen, Speichern, Neustart, Abbrechen, fehlende Datei), Taster kurz/lang (Mute, Patch-Browser, Drum-Step, START/STOP), MIDI-Slices (Startpunkt, Ende über Tag 210), Übernahme eines v13.18-Stands, alle neuen Seiten zeichnen. Auf der Hardware steht der Test aus.

## Nächste Ideen

- NOTCH/PHASER auch als Filtertyp für Synth-Kanäle (Juno/AMYB).
- Ratchets (2er-Roll pro Step), Wahrscheinlichkeit pro Drum-Instrument, Fill-Modus.
- **Bildschirmschoner mit Delfinen** (Vorschlag 28.10.2026, noch nicht entschieden). Auswahl unter SETUP › DISPLAY › SCHONER-BILD, dazu WECHSEL (alle paar Minuten ein anderer, Einzelne abwählbar; ruhige Bilder bei gestopptem, wilde bei laufendem Sequencer) und TEXT (bisheriger Schoner). Alles bewegt sich gegen Einbrennen, Helligkeit gedimmt, während der Wiedergabe höchstens ca. 4 Bilder/s in Streifen.
  - Ruhig: **1 Sprung** (Delfin springt aus Wellen, im Takt auf die Eins), **2 Schwarm** (drei Delfine unter Wasser, Blasen, Lichtstreifen), **3 Nachtmeer** (Delfin-Silhouette vor dem Mond, funkelnde Sterne).
  - Underground: **Glitch** (Pixel-Delfin zerreißt auf jeden Schlag, Scanlines), **Oszi** (Delfin als Vektorlinie, darunter die echte Ausgangs-Wellenform), **Sonar** (Radarstrahl, Delfine als Echo, jeder Kick ein Ping), **Tunnel** (Delfin fliegt durch einen Rechteck-Tunnel im BPM-Tempo), **Terminal** (fallende echte MIDI-Bytes, ASCII-Delfin, Eingabezeile mit Kanal/BPM), **Flyer** (90er-Rave-Plakat „DOLPHIN soundsystem“, Rasterpunkt-Delfin, Strobo-Invert auf Takt 1).
  - Offen: welche davon rein, Name auf dem Flyer. Schätzung +15–25 KB Sketch.
