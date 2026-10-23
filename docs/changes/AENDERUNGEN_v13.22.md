# Dolphin Selector 3 – Änderungen v13.22

Stand 23.10.2026 · Basis: v13.21

## Neu: AUDIO IN – Eingang live durch Filter und Effekte

**MODULAR › AUDIO IN** schickt den Stereo-Eingang des AMYboards dauerhaft zum Ausgang. Damit arbeitet das Board als Effektgerät im Rack: Signal rein, über Filter, Distortion, Reverb, Chorus, Echo, EQ und Crush, wieder raus. Das funktioniert unabhängig von der gerade offenen Seite, vom Sequencer und vom Sampler.

AMY spielt den Eingang selbst als Oszillator (`wave` `AUDIO_IN0` = links, `AUDIO_IN1` = rechts). Python ist nicht im Signalweg, also keine zusätzliche Latenz durch die Bedienung.

| Eintrag | Wirkung | Werk |
|---|---|---|
| **AUDIO IN** | AN/AUS | AUS |
| **MODUS** | STEREO · MONO (L+R in der Mitte, je −6 dB) · NUR L · NUR R | STEREO |
| **IN GAIN** | Eingangsverstärkung −24 … +12 dB (vor Distortion und Filter) | 0 dB |
| **IN LEVEL** | Ausgangspegel 0–1,5 | 1.00 |
| **IN PAN** | Position im Stereobild | Mitte |
| **BREITE** | nur STEREO: 1 = L ganz links, R ganz rechts; 0 = beide auf IN PAN | 1.00 |
| **BUS** | Effekt-Bus 0–3 | 2 |
| **BUS-EFFEKTE** | öffnet EFFEKTE direkt für diesen Bus | |
| **FILTER** | AUS · TP · BP · HP · TP24 (· NOTCH · PHASER, wenn die Firmware sie kennt) | AUS |
| **IN CUTOFF · IN RESO** | Filterfrequenz und Resonanz (nur bei FILTER ≠ AUS) | 8000 Hz · 0.7 |
| **DISTORTION · IN DRIVE · DIST MIX** | CLIP/FOLD vor dem Filter (nur wenn die Firmware Distortion kennt) | AUS · 4 · 1 |

Ab Werk liegt der Eingang auf **Bus 2**, der sonst frei ist. So bleiben die Effekte des Eingangs getrennt von Synths (Bus 0) und Drums (Bus 1).

### Seite
Oben steht eine **Pegelanzeige L/R** des Eingangs (vor IN GAIN), mit Marken bei −24, −12 und −6 dB, dem Spitzenwert in dB rechts und **CLIP**, wenn ein Kanal übersteuert. Die Anzeige läuft auch bei AUDIO IN = AUS, damit sich der Pegel vorher prüfen lässt. Darunter steht eine Kurzzeile: Modus (ST/MO/L/R), Bus, Filter mit Cutoff, Distortion.

### Überall verfügbar
- **Statuszeile:** `IN` zeigt auf jeder Seite, dass der Eingang läuft.
- **Taster-Funktion AUDIO IN** (SETUP › ENCODER › TASTER): schaltet den Eingang von jeder Seite aus an und aus.
- **Makros und Zusatz-Encoder:** IN GAIN, IN LEVEL, IN PAN, IN CUTOFF, IN RESO, IN DRIVE.
- **Szenen** speichern alle AUDIO-IN-Einstellungen, schalten den Eingang beim Laden aber **nicht** an oder aus. AN/AUS bleibt global. Ältere Szenen ohne AUDIO IN lassen ihn unverändert.
- **PANIC** lässt den Eingang weiterlaufen.
- **EFFEKTE › KANAELE** zeigt `IN`, wenn der Eingang auf dem gewählten Bus liegt.
- **SETUP › AUDIO MONO** legt auch den Eingang in die Mitte.
- **SETUP › INFO › AUDIO IN** zeigt die Synth-Nummern (41/42) oder FEHLT.

### Aufbau in AMY
- Zwei eigene Synths mit je einem Oszillator: **41** = `AUDIO_IN0` (L), **42** = `AUDIO_IN1` (R). Eine `chained_osc`-Kette ginge nicht, weil Filter und Distortion dort auf die ganze Kette wirken; L und R sollen getrennt bleiben.
- Pro Oszillator: `amp const` (aus IN GAIN), `dist_*`, `filter_type`/`filter_freq`/`resonance`, `pan`. Pro Synth: `synth_level` (IN LEVEL) und `bus`.
- Note-on mit Hüllkurve `5,1,60,0` (wie der VCO): 5 ms einblenden, halten, 60 ms ausblenden beim Abschalten, also kein Knacken.
- NUR L / NUR R schalten die andere Seite per Note-off ab.
- Kennt die Firmware keine Synths über 31, zeigt MODULAR „FEHLT“ und AUDIO IN bleibt aus.
- Pegelanzeige: `amy.get_input_buffer()` (letzter Block, jeder zweite Frame), alle 80 ms, nur solange die Seite offen ist.
- Board-Datei ca. 10 KB größer (≈ 288 KB).

### Test in der Simulation (23.10.2026)
Sketch mit nachgebauten `amy`/`amyboard`-Modulen, beide Sprachfassungen, je 75 Prüfungen: Synth-Suche, Einschalten über die Seite, alle gesendeten AMY-Werte (Welle, Bus, amp, Pan, Pegel, Filter, Distortion), alle vier Modi, Breite, Grenzen, BUS-EFFEKTE mit dem richtigen Bus, globales MONO, Statuszeile, Taster, Makros, PANIC, Szenen (AN/AUS bleibt), Speichern und Neustart, alter Zustand ohne AUDIO IN, Firmware ohne Synths über 31, fehlender Eingangspuffer. Alle bestanden.

## Auf der Hardware zu prüfen

1. **Kommt der Eingang an?** Signal an den Eingang, MODULAR › AUDIO IN öffnen: Die Pegelanzeige muss ausschlagen. Wenn nicht: DIP-Schalter auf der Rückseite, Kabel, Pegel (SAMPLER › AUFNAHME › EINGANG TESTEN zeigt dasselbe).
2. **Klingt er?** AUDIO IN = AN. Ist trotz Anzeige nichts zu hören, spielt die Firmware `AUDIO_IN0/1` als Oszillator nicht (dann `audio_in` in der Firmware aus) – bitte melden. SETUP › INFO › AUDIO IN muss 41/42 zeigen.
3. **Stereo:** Signal nur links → nur links zu hören? NUR R → still?
4. **Latenz** spürbar (z. B. Drums durchschicken und mit dem Original vergleichen)?
5. **Rauschen** bei IN GAIN +12 dB, **Knacken** beim Ein-/Ausschalten und bei Filterwechseln.
6. **Rückkopplung:** Nie den Ausgang des AMYboards auf den eigenen Eingang patchen, solange AUDIO IN an ist.
