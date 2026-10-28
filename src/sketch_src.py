# ================================================================
# DOLPHIN SELECTOR 3  -  AMYboard Eurorack Synth  -  sketch.py
# Version 13.30 (28.10.2026) - BILDSCHIRMSCHONER
# ================================================================
#
# Hardware (unveraendert):
#   AMYboard (ESP32-S3, MicroPython), Adafruit 1.5" 128x128 OLED
#   #4741 (16 Graustufen), Adafruit I2C Rotary Encoder #5880 als
#   Navigation. Optional: M5Stack 8-Encoder (E1-E8) UND/ODER bis zu
#   zwei Adafruit Quad #5752 (Q1-Q4, Q5-Q8), M5Stack I2C Joystick,
#   Adafruit ANO.
#   Encoder-Reihenfolge wie gehabt (amyboard.encoder(): M5Stack,
#   Quads, ANOs, Singles, je nach I2C-Adresse).
#
# ----------------------------------------------------------------
# BEDIENUNG - vier Gesten, ueberall gleich
# ----------------------------------------------------------------
#   DREHEN              Auswahl bewegen / Wert aendern
#   KURZ DRUECKEN       oeffnen, bearbeiten, bestaetigen
#   LANG DRUECKEN       eine Ebene zurueck; waehrend einer
#                       Bearbeitung: ABBRECHEN (alter Wert zurueck)
#   GEDRUECKT + DREHEN  MIDI-Kanal wechseln - von jeder Seite aus
#   Auf SPIELEN 2 s halten = PANIC (Ring zeigt den Fortschritt)
#
#   Beim Bearbeiten beschleunigt schnelles Drehen die Schritte.
#   Joystick hoch/runter: auf der Drum-Seite Instrument wechseln.
#
# ----------------------------------------------------------------
# AUFBAU
# ----------------------------------------------------------------
#   SPIELEN (Start)  Patch, 4 Makros, Sequencer, Start/Stop, MENUE
#   MENUE-Karussell:
#     KLANG      Patch-Browser (Kategorien, Favoriten, Zuletzt),
#                Filter, Huellkurve, LFO, DX7, Akkord, Portamento
#     MIXER      16 Kanaele als Fader, Kanalzug pro Kanal
#     EFFEKTE    pro Bus: Reverb, Chorus, Echo, EQ + Klangprofil,
#                Crush, Master
#     SEQUENCER  4 Spuren + 303 + DRUMS, Live-Abspielpunkt, Swing,
#                Wahrscheinlichkeit, 4 Patterns/Spur, ARP live,
#                Acid-Generator, Tap-Tempo
#                DRUMS: 8 Instrumente x bis 32 Steps, Velocity in
#                16 Stufen, Laenge pro Instrument (Polymetrik),
#                Euclid pro Instrument, E1-E8 = 8 Steps direkt,
#                GRIDS (X/Y-Karte, Dichte je Instrument, live per
#                CV IN / Joystick), CV-TRIGGER (Instrument -> OUT1/2),
#                DRUMKIT und SOUND je Instrument (mit Vorhoeren)
#     MODULAR    CV-Monitor, CV-Modi, Quantizer, CV MOD,
#                Kalibrierung, Scope, VCO, AUDIO IN
#     SZENEN     8 Speicherplaetze, Morph A <-> B
#     SAMPLER    8 Slots (Pads + chromatisch), Wellenform-Editor,
#                Aufnahme auf SD, WAVs von SD
#     SETUP      MIDI, Encoder, Makros, Audio, Display, WLAN,
#                Takt, Info, Werksreset
#
# ----------------------------------------------------------------
# LEISTUNG UND KLANG
# ----------------------------------------------------------------
#   - Zeichnen nur bei Aenderung, max. ca. 22 Bilder/s, im
#     Leerlauf kein Display-Verkehr (ein Vollbild = 8 KB I2C).
#   - Encoder E1-E8 nur lesen, wenn belegt; CV nur bei Aenderung.
#   - Stimmenbudget begrenzt die Summe aller Stimmen.
#   - Effekte pro Bus; ab Werk Drums auf Bus 1 (trocken, PUNCH-EQ),
#     Synths auf Bus 0 mit etwas Reverb.
#   - Headroom-Ausgleich pro Bus, Render-Last-Warnung, Failsafe.
#
# ZUSTAND: /sd/dolphin_state.json (sonst Flash). Beim ersten Start
# werden die Dateien von v11 (amyboard_state*.txt) uebernommen und
# NICHT geloescht. Szenen: dolphin_scenes.json.
#
# NEU IN v13.30:
#   - Bildschirmschoner mit Delfinen: SPRUNG, SONAR, TUNNEL, TERMINAL,
#     FLYER, ACID-SPUR, SPEKTRUM, WAREHOUSE. Sie laufen zufaellig nacheinander
#     (WECHSEL nach 1/2/5/10 min), nach 30 min/1 h/4 h (LEERLAUF) uebernimmt ein
#     langsam pulsierender Delfin-Umriss. Takt, Kick (Bassdrum der Drum-Spur),
#     303-Pattern, MIDI-Bytes und der Audio-Ausgang treiben die Bilder.
#   - SETUP > DISPLAY > SCHONER-BILD: BILD (ZUFALL, ein festes Bild, TEXT =
#     bisheriger Schoner), WECHSEL, LEERLAUF, KONTRAST, FLYER-Text, Auswahl
#     fuer den Zufall, JETZT ZEIGEN.
#   - Waehrend der Wiedergabe hoechstens ein Bild alle 400 ms, gesendet in
#     Baendern mit dem ueblichen Budget - der Takt hat Vorrang.
#   HW-TEST: Bilder auf dem Display, BEDIENUNG/ZEICHNEN MAX mit laufendem
#            Sequencer (SPEKTRUM rechnet am meisten), Startspeicher.
#
# NEU IN v13.29:
#   - LED des Navigations-Encoders (Single #5880) wird genutzt: FARBE
#     (ab Werk die Farbe des aktuellen Kanals), EDIT (anders, solange ein
#     Wert bearbeitet wird), TAKT (Blitz auf jeden Schlag, Takt 1 weiss),
#     KANAL-BLITZ beim Kanalwechsel, PANIC (gelb nach rot beim Halten),
#     WARNUNG (blinkt bei CLIP am AUDIO IN, hoher CPU-Last, Speicherfehler).
#     Jede Anzeige hat eine waehlbare Farbe oder AUS.
#   - Zusatz-Encoder: ZUSTAND (gedimmt = ohne Wirkung: SEITE ohne Wert auf
#     dieser Seite, Kanal stumm oder leer, Parameter ausgeblendet; AUF DRUCK
#     vorgemerkt = blinkt; Funktion AUS mit Taster START/MUTE/AUDIO IN/TAP/
#     ENC-SET zeigt den Taster-Zustand), DREH-BLITZ, neue LED-Farbe KANAL.
#   - SETUP > ENCODER > LEDS: alle Einstellungen, HELLIGKEIT (4 Stufen fuer
#     alle LEDs), IM SCHONER (LEDs aus/an), LED-TEST. SETUP > INFO > NAV-LED.
#   - Gesendet wird nur bei Aenderung, waehrend der Wiedergabe hoechstens
#     3 LEDs pro UI-Durchlauf (I2C-Last).
#   HW-TEST: Leuchtet die LED des Single (Index NAV-LED in SETUP > INFO)?
#            Richtige LED am richtigen Encoder (LED-TEST)? Takt stabil?
#
# NEU IN v13.28:
#   - VCO > GLAETTUNG: Stufe LEICHT heisst jetzt WENIG. "GLAETTUNG LEICHT"
#     war fuer die Zeile zu lang und wurde abgeschnitten.
#
# NEU IN v13.27:
#   - Kein Knacken mehr beim Wechsel der VCO-WELLE und beim Wechsel von
#     FILTER- bzw. DISTORTION-Typ bei AUDIO IN: kurz ausblenden (Huellkurve,
#     60 ms), umschalten, wieder einblenden (5 ms). Schnelles Durchdrehen
#     blendet nur einmal aus.
#   - VCO > GLAETTUNG (AUS/WENIG/STARK, nur Modus FREI): der 1V/Okt-
#     Eingang wird in Python gelesen und geglaettet (gleitender Mittelwert,
#     Zeitkonstante ca. 60 / 200 ms) statt direkt in AMY. Ruhigerer Ton,
#     folgt schnellen Spruengen aber etwas verzoegert.
#   HW-TEST 26.10.2026: Knacken bei WELLE und AUDIO-IN-Filtertyp, Zittern
#            im Modus FREI (ca. +-8 ct).
#
# NEU IN v13.26:
#   - SETUP > MIDI > MONITOR: die letzten 8 MIDI-Ereignisse, die beim
#     Sketch ankommen (Kanal, Note/CC/PC, Wert) und was der Sketch damit
#     gemacht hat (PAD S1, SLICE 3, KANAL, KEINE SLICES, SLOT AUS ...).
#     Dazu die Zahl aller empfangenen Nachrichten (auch Clock). Zur
#     Fehlersuche, z. B. wenn Pads oder Slices nicht reagieren.
#
# NEU IN v13.25:
#   - KALIBRIERUNG fuer CV IN1/IN2: IN1/IN2 OFFSET und SKALA (gemessen =
#     roh x SKALA + OFFSET), wie bei den Ausgaengen. Gilt fuer alles, was
#     den Eingang liest: CV-Monitor, QUANTIZE, Grids per CV, FOLD MOD, VCO
#     (auch der AMY-Weg: ext-Koeffizient x SKALA, Versatz in const) und
#     GATE+PITCH (Tonhoehe und Gate-Schwellen).
#   - IN1/IN2 ABGLEICH: Kabel OUT1 -> INx, Druck. Das Board gibt 1 V und
#     3 V auf OUT1 aus, mittelt je 0,3 s und traegt OFFSET/SKALA ein.
#     Voraussetzung: OUT1 vorher kalibriert (Multimeter, TESTSPANNUNG).
#   - Kopf der KALIBRIERUNG-Seite zeigt IN1/IN2 kalibriert und OUT1 live.
#   HW-TEST 26.10.2026: OUT1 brauchte OFFSET -0.312 / SKALA 0.984, IN1
#            misst ca. 0.19 V zu wenig (1.00 -> 0.81, 3.00 -> 2.80).
#
# NEU IN v13.24:
#   - SETUP > ENCODER neu: Uebersicht aller Zusatz-Encoder nach Geraet
#     (M5STACK, QUAD 1, QUAD 2) mit ihrer Funktion. Drehen an einem
#     Zusatz-Encoder springt auf seine Zeile. Druecken oeffnet die Seite
#     des Encoders: FUNKTION (AUS/SEITE/PATCH/KANAL/PARAMETER), danach nur
#     die passenden Eintraege, dazu TASTER und LED.
#   - PATCH fuer alle 16 Kanaele oder AKTUELL (folgt dem gewaehlten
#     Kanal). LISTE: ALLE, eine Kategorie, FAVORITEN oder DRUMKITS. LADEN:
#     SOFORT (wie bisher) oder AUF DRUCK (Drehen zeigt nur den Namen, der
#     Taster laedt). KANAL: Drehen waehlt den aktuellen MIDI-Kanal.
#   - PARAMETER in Gruppen (MIXER, KLANG, EFFEKTE, SEQ+SZENE, 303, DRUMS,
#     MODULAR, AUDIO IN) statt einer langen Liste.
#   - LED je Encoder (M5Stack und Quads): AUTO = Farbe nach Funktion, AUS
#     oder eine feste Farbe.
#   - ENCODER-SETS A/B/C: drei komplette Belegungen (Funktion, Taster,
#     LED), umschaltbar unter SETUP > ENCODER > SET oder per Taster
#     ENC-SET >. Q5-Q8 ab Werk PATCH K5-K8.
#
# NEU IN v13.23:
#   - SETUP > ENCODER > I2C-SCAN (auch SETUP > INFO > I2C): jede Adresse am
#     Bus mit dem erkannten Geraet und der Seesaw-Produktnummer, dazu was
#     der Sketch davon als Zusatz-Encoder nutzt. Zur Fehlersuche, wenn z. B.
#     der Quad nicht erscheint.
#
# NEU IN v13.22:
#   - AUDIO IN: MODULAR > AUDIO IN schickt den Stereo-Eingang dauerhaft
#     zum Ausgang - das AMYboard arbeitet als Effektgeraet im Rack. AMY
#     spielt den Eingang als Oszillator (wave AUDIO_IN0/AUDIO_IN1), je
#     Seite ein eigener Synth (41 = L, 42 = R). Python ist nicht im
#     Signalweg.
#   - Pro Seite: IN GAIN (-24..+12 dB), Distortion (vor dem Filter),
#     Filter (TP/BP/HP/TP24, NOTCH/PHASER wenn vorhanden), Pan; dazu
#     IN LEVEL, MODUS STEREO (mit BREITE) / MONO / NUR L / NUR R und BUS.
#     Ueber den Bus wirken Reverb, Chorus, Echo, EQ, Bus-Distortion und
#     Crush aus EFFEKTE - BUS-EFFEKTE oeffnet direkt den richtigen Bus.
#   - Pegelanzeige L/R mit CLIP oben auf der Seite (amy.get_input_buffer,
#     nur solange die Seite offen ist).
#   - AN/AUS gilt ueberall: Szenen speichern die Einstellungen, schalten
#     den Eingang aber nicht ab; PANIC laesst ihn laufen. Statuszeile
#     zeigt "IN". Taster-Funktion AUDIO IN (an/aus), IN GAIN, IN LEVEL,
#     IN PAN, IN CUTOFF, IN RESO, IN DRIVE als Makro/Encoder.
#   HW-TEST: Kommt der Eingang an (Pegelanzeige)? Klingt er ueber
#            AUDIO_IN0/1 (sonst ist audio_in in der Firmware aus)? Latenz,
#            Rauschen bei IN GAIN +12 dB, Rueckkopplung bei Kabel OUT>IN.
#
# NEU IN v13.21:
#   - VCO: MODULAR > VCO macht das AMYboard zu einem eigenstaendigen
#     Oszillator-Modul (Dauerton, kein MIDI noetig). Tonhoehe per 1 V/Okt
#     an CV IN1 oder IN2 - ausgewertet direkt in AMY (freq-Koeffizient
#     ext0/ext1), also ohne Python im Signalweg. Kette aus drei
#     Oszillatoren (chained_osc): Haupt-Welle SIN/TRI/SAW/PULS mit
#     Pulsbreite, Sub-Oszillator (Rechteck -1/-2 Okt) und ein zweiter,
#     verstimmbarer Oszillator (Intervall + Cent). Wavefolder (CLIP/FOLD
#     aus v13.16) am Haupt-Oszillator.
#   - MOD-EINGANG (IN1/IN2) wirkt auf TONHOEHE (exp. FM, in AMY),
#     PULSBREITE (PWM, in AMY) oder FOLD (Drive, alle 30 ms).
#   - TONHOEHE FREI (stufenlos) oder QUANT (auf eine eigene Skala
#     gerastet, alle 40 ms). V/OKT-Abgleich je Eingang (0.950-1.050).
#   - Kopf der VCO-Seite: Note, Frequenz und Cent-Abweichung live (zum
#     Stimmen) plus Vorschau der Welle.
#   - VCO FEIN, PULSBREITE, SUB, OSZ 2, VERSTIMMUNG, DRIVE, MOD TIEFE und
#     LEVEL als Makro/Encoder; der VCO-Zustand gehoert zu den Szenen.
#   HW-TEST: Tracking ueber 5 Oktaven (V/OKT-Abgleich), Synth 40 vorhanden
#            (sonst 31), Pegel mit SUB + OSZ 2, Knacken beim Wellenwechsel.
#
# NEU IN v13.20:
#   - WAVEFOLDER-LFO: MODULAR > CV LFO hat jetzt FOLD (AUS/CLIP/FOLD/
#     CLIP+FOLD), LFO DRIVE und FOLD MIX. Der Waveshaper aus v13.16 sitzt in
#     AMY an jedem Oszillator, also auch am LFO-Synth 20, der per set_cv_out
#     auf OUT1/OUT2 liegt - gefaltet wird in AMY, ohne Python-Rechenlast.
#     TIEFE liegt vor dem Folder (wie der Eingangspegel eines echten
#     Wavefolders), LFO DRIVE verstaerkt zusaetzlich.
#   - FOLD MOD: CV IN1 oder IN2 verschiebt LFO DRIVE um bis zu +-2 Oktaven
#     (MOD TIEFE, 5 V = voller Ausschlag), alle 30 ms nachgefuehrt.
#   - LFO DRIVE als Makro und fester Encoder (wie 303 DRIVE).
#   - Vorschau der gefalteten Welle oben auf der CV-LFO-Seite (Naeherung).
#   - CV ENV bekommt ebenfalls FOLD, ENV DRIVE und FOLD MIX.
#   HW-TEST: Faltet AMY auch auf dem CV-Weg (Scope an OUT1)? Pegel bei
#            TIEFE 1.0 + Drive (Spitzen bis +-10 V?), ENV-Fold negativ?
#
# NEU IN v13.19:
#   - DX7-BAENKE VON SD: Patch-Browser > DX7 VON SD listet .SYX-Dateien aus
#     /sd/dx7/ und dem Hauptverzeichnis, dann die (bis zu 32) Stimmen. Beim
#     Durchdrehen hoerbar; die Stimme wird mit fm.load_syx als AMY-User-
#     Patch 1024+Kanal abgelegt, gespeichert (Datei, Nummer, Name) und beim
#     Start neu geladen. Klangformung wie bei DX7 (ALGORITHMUS, FEEDBACK, LFO).
#   - TASTER der Zusatz-Encoder (SETUP > ENCODER > TASTER), kurz/lang:
#     KONTEXT (PATCH Kn: kurz Mute, lang Patch-Browser; fester Parameter:
#     grosser Ring; SEITE auf der Drum-Seite: Step setzen), START/STOP, TAP
#     TEMPO, PANIC (lang), MUTE K1-K4, MUTE 303, MUTE DRUMS, AUS.
#   - FILTER NOTCH und PHASER fuer Sample-Slots (wenn die Firmware
#     FILTER_NOTCH/FILTER_PHASER kennt).
#   - SLICES UEBER MIDI: PAD-KANAL Noten 44-59 spielen die Slices des
#     SLICE-SLOT (Ende nach Slice-Laenge, eigenes AMY-Tag je Slot).
#   HW-TEST: fm.load_syx auf dem Board (Import, Dauer), Taster-Lesezeit.
#
# NEU IN v13.18:
#   - SLICES: SAMPLER > SLOT > SLICES AUS/4/8/16 teilt den Slot in gleich
#     lange Stuecke (Linien im Wellenform-Editor). Drum-Spur > SPUR-MENUE >
#     SLICE waehlt je Instrument ein Stueck (GANZ = wie bisher). Gestartet
#     wird ueber phase (Startframe/2^23), beendet per Note-Off nach der
#     Slice-Laenge; ein neuer Schlag auf demselben Slot schneidet ab.
#     Mit TAKT-SYNC dauert jedes Stueck genau TAKT-SYNC/SLICES (fit =
#     restliche Ticks, wie in api.md verlangt) - Breakbeats im Tempo.
#     SLOT > AUF DRUMS VERTEILEN legt Slice 1-8 auf Instrument 1-8 und
#     schreibt das Original-Muster ins Pattern (geht von 1 Takt aus).
#     Nicht im Modus LOOP. Drum-Zeile zeigt z. B. "1c" = Slot 1, Slice 3.
#   HW-TEST: Uebergaenge zwischen Slices (Klicks?), phase bei Dateien >
#            8 Mio. Frames (nicht moeglich, max. 10 s), fit + phase.
#
# NEU IN v13.17:
#   - SAMPLER > SLOT > TAKT-SYNC: der Slot dauert immer genau 1 Schlag ...
#     10 Takte, folgt dem Tempo (auch waehrend der Note) und behaelt dabei
#     seine Tonhoehe (AMY fit=N, granularer Time-Stretch; fit=-1 = aus).
#     TUNE/FEIN und der CHROM.-Kanal transponieren ohne die Dauer zu
#     aendern. SYNC AUS LAENGE schlaegt den Wert aus Laenge und Tempo vor.
#     GRAIN-SUCHE (fit_search, ab Werk 64, 0 = aus) fuer tiefe Klaenge.
#     Aufnahmen mit EINHEIT TAKTE bekommen TAKT-SYNC automatisch.
#     Nicht im Modus LOOP. Kostet ca. 2,5x Rechenzeit je spielendem Slot.
#   - Distortion DRIVE bis 16 (AMY-Grenze laut api.md, vorher 20).
#   HW-TEST: Loop bei Tempowechsel synchron? Klang bei Drums/Bass?
#
# NEU IN v13.16:
#   - DISTORTION (AMY 1.2.16x: Waveshaper pro Oszillator und pro Bus -
#     Soft-Clip, Wavefolder, stapelbar, nach der Huellkurve und vor dem
#     Filter).
#     303: TYP AUS/CLIP/FOLD/CLIP+FOLD, DRIVE, MIX - die klassisch
#       verzerrte Acid-Linie, weil das Filter danach kommt. DRIVE als
#       Joystick-Ziel, Makro und fester Encoder (303 DRIVE).
#     EFFEKTE > DISTORTION pro Bus: TYP, DRIVE, MIX (BUS DRIVE als Makro/
#       Encoder). Arbeitet mit CRUSH zusammen (gleiche Stufe in AMY).
#     Kennt die Firmware die Befehle nicht, bleiben die Eintraege
#     ausgeblendet (SETUP > INFO > DISTORTION zeigt JA/NEIN).
#   HW-TEST: Klang/Pegel bei DRIVE 4-16, MIX < 1 zusammen mit CRUSH.
#
# NEU IN v13.15:
#   - M5Stack 8-Encoder und Adafruit Quad #5752 gleichzeitig: bisher galt
#     "M5Stack hat Vorrang, sonst Quad". Jetzt erscheinen alle Zusatz-
#     Encoder unter SETUP > ENCODER: E1-E8 (M5Stack), Q1-Q4 (Quad), ein
#     zweiter Quad als Q5-Q8. Nur der Single (Navigation) bleibt aussen vor.
#   - Neue Encoder-Funktionen PATCH K1 - PATCH K4: Drehen wechselt den
#     Patch von Kanal 1-4 im laufenden Betrieb (entprellt geladen wie im
#     Patch-Browser, Sequencer laeuft weiter). Schnelles Drehen = 4er-
#     Schritte. Drumkit-Kanaele blaettern nur durch die Drumkits. Ab Werk
#     Q1-Q4 = PATCH K1-K4. Jeder Zusatz-Encoder kann jede Funktion haben.
#   HW-TEST: M5Stack + Quad zusammen an amyboard.encoder() (Reihenfolge,
#            Lesezeit pro Durchlauf), SETUP > ENCODER zeigt die Geraete.
#
# NEU IN v13.14:
#   - Aufnahmen auf die SD-Karte speichern ueber tulip.store_sample()
#     (neue AMYboard-Firmware, PR 1399). AUFNAHME > AUTO-SPEICHERN (ab
#     Werk AN) schreibt nach jeder Aufnahme /sd/samples/RECnnn.wav und
#     stellt den Slot auf die Datei um (dann auch Trimmen/Wellenform).
#     SLOT > AUF SD SPEICHERN fuer RAM-Slots von Hand. Ohne passende
#     Firmware bleibt alles wie in v13.13 (nur RAM).
#
# NEU IN v13.13:
#   - AUFNAHME-Seite: tote Zeilen LETZTE/LUECKEN/PEGEL entfernt (gehoerten
#     zum entfernten SD-Datei-Weg).
#
# NEU IN v13.12:
#   - v13.11 startete nicht (vermutlich zu wenig Speicher beim Uebersetzen
#     der ~300 KB grossen Datei). sketch.py wird jetzt OHNE Kommentare
#     ausgeliefert (~240 KB); dies hier ist die kommentierte Fassung.
#   - Aufnahme nur noch in den RAM von AMY (der Weg ueber Python/SD-Datei
#     funktionierte auf dem Board nicht und ist entfernt).
#   - Pegelmessung (EINGANG TESTEN) korrigiert: a[::step] gibt es in
#     MicroPython nicht, der Pegel war dadurch immer 0.
#
# NEU IN v13.11:
#   - AUFNAHME > ZIEL: RAM (neu, ab Werk) laesst AMY selbst aufnehmen -
#     lueckenlos, Bedienung und Sequencer laufen weiter, START TAKT 1
#     tick-genau. Die Aufnahme liegt nur im RAM (Slot zeigt "RAM") und
#     ist nach dem Ausschalten weg. SD-DATEI = bisheriger Weg (Python
#     holt Bloecke ab, blockiert, Luecken jetzt als Stille statt Dauerton).
#
# NEU IN v13.10:
#   - Aufnahme wieder in den RAM (Stuecke a 32 KB statt eines grossen
#     Puffers), die SD-Karte wird erst danach beschrieben. v13.3 schrieb
#     waehrend der Aufnahme - jeder SD-Zugriff kostete Bloecke (3060
#     LUECKEN bei 10 s). Reicht der RAM nicht, wird kuerzer aufgenommen.
#   - Blocklaenge aus den Daten statt angenommen; PEGEL der Aufnahme.
#   - AUFNAHME > EINGANG TESTEN: 2 s messen, was die Firmware liefert
#     (Bloecke/s, Pegel, RAM, SD-Schreibzeit).
#
# NEU IN v13.9:
#   - SD-Schreibfehler E5 behoben (vermutlich): verwaiste SDCard-Objekte
#     wurden von der Speicherbereinigung freigegeben und schalteten dabei
#     den SPI-Slot der eingehaengten Karte ab. Jetzt: vor dem Einhaengen
#     aufraeumen, eigenes Kartenobjekt behalten, beim Start immer selbst
#     einhaengen, Schreibtest unter denselben Bedingungen wie Speichern.
#
# NEU IN v13.8:
#   - SD TEST: scheitert das Schreiben, werden alle Takte (20 MHz bis
#     400 kHz) jeweils ohne und mit internen Pull-ups durchprobiert und
#     als Liste gezeigt; eine funktionierende Einstellung wird gemerkt.
#   - Neu-Einhaengen gibt die alte Karte vorher frei (deinit).
#
# NEU IN v13.7:
#   - SETUP > SD TEST: prueft Schreiben/Lesen Schritt fuer Schritt (4K,
#     32K, am Stueck, mit flush, der echte Zustand, Umbenennen) und zeigt
#     je Schritt OK + Zeit oder die Fehlernummer.
#   - SD-GRUND wird nach erfolgreichem Speichern auf der Karte geloescht.
#
# NEU IN v13.6:
#   - SD-Schreibfehler (E/A) bei groesseren Dateien trotz frischer Karte:
#     SD EINBINDEN prueft jetzt mit 32 KB und senkt bei Fehlern den
#     SPI-Takt (20 > 10 > 5 > 2 > 1 MHz). Der funktionierende Takt wird
#     in /user/sd_freq.txt gemerkt und beim Start verwendet.
#     SETUP > INFO > SD-TAKT zeigt ihn.
#
# NEU IN v13.5:
#   - SETUP > SD ZUSTAND NEU: loescht dolphin_state.json (+ .tmp/.bak) auf
#     der Karte und schreibt den aktuellen Zustand frisch dorthin. Die
#     Einstellungen bleiben erhalten (sie liegen im Speicher).
#   - WERKSRESET loescht die Zustandsdateien jetzt an allen Orten.
#
# NEU IN v13.4:
#   - SD EINBINDEN meldete OK, obwohl das Speichern des Zustands auf der
#     Karte scheiterte und still nach /user/ gewechselt wurde. Jetzt:
#     Meldung mit Grund, SETUP > INFO zeigt SD-GRUND und SD FREI.
#
# NEU IN v13.3:
#   - Aufnahme direkt auf die SD-Karte statt erst komplett in den RAM
#     ("ZU WENIG RAM" bei mehr als ~2 s): kleiner Ringpuffer (48 KB),
#     Datei wird vorab in voller Laenge angelegt ("BEREITE VOR").
#
# NEU IN v13.2:
#   - Ist /sd beim Start nicht beschreibbar, haengt der Sketch die Karte
#     selbst neu ein und prueft erneut, bevor er nach /user/ ausweicht.
#     SETUP > INFO > SD zeigt dann "NEU EINGEH.".
#
# NEU IN v13.1:
#   - v13.0 lief nicht an ("RuntimeError: asm overflow"): die zwei
#     @micropython.viper-Funktionen entfernt, Stereo->Mono und Spitzen
#     jetzt in array("h") bzw. ueber max()/min().
#
# NEU IN v13.0 - SAMPLER ALS GROOVEBOX:
#   - 8 SAMPLE-SLOTS. Jeder Slot verweist auf eine WAV auf der SD-Karte
#     (/sd/samples/ oder Hauptverzeichnis; 16 Bit, mono/stereo, jede
#     Samplerate). Eigene Dateien einfach auf die Karte kopieren.
#   - Zerstoerungsfrei trimmen: START/ENDE und LOOP A/B im WELLENFORM-
#     Editor (Zoom 1x/8x/64x, E1-E4 direkt). Geladen wird nur der
#     Bereich START..ENDE (hoechstens 10 s), mono, in den RAM von AMY.
#   - Pro Slot: MODUS EINMAL/GATE/LOOP, TUNE/FEIN, GRUNDTON, LEVEL, PAN,
#     BUS, Huellkurve ADSR, FILTER TP/BP/HP/TP24 mit RESONANZ, F-ENV und
#     F-DECAY.
#   - PADS: Drum-Spur > Instrument > SAMPLE = Slot statt Drumkit-Klang.
#     PAD-KANAL: MIDI-Noten 36-43 spielen Slot 1-8.
#   - CHROMATISCH: CHROM. KANAL spielt CHROM. SLOT ueber die Tastatur
#     (auch Sequencer-Spuren 1-4 auf diesem Kanal).
#   - AUFNAHME: LINE oder MIX (Resampling), Laenge in SEK oder TAKTEN,
#     Start SOFORT oder auf TAKT 1 des laufenden Sequencers. Gespeichert
#     als Stereo-WAV /sd/samples/RECnnn.wav und in den Ziel-Slot geladen.
#   - Laden im Hintergrund: Bedienung und Sequencer laufen weiter.
#   HW-TEST: Aufnahme ohne LUECKEN? Pads auf Synth 32-39 (INFO PADS)?
#            Laden mit _send_transfer_chunk (sonst haelt der Seq kurz)?
#
# NEU IN v12.15:
#   - JOYSTICK > 303 (Menue der 303-Spur): der Joystick spielt die 303
#     live. X und Y frei belegbar (ab Werk X = CUTOFF, Y = ENV MOD),
#     weitere Ziele RESO, DECAY, ACCENT, SLIDE, TRANSP (+-12 Halbtoene),
#     DICHTE (nach unten = Noten weglassen). Loslassen = zurueck auf die
#     gespeicherten Werte. Joystick-Knopf = aktuellen Klang uebernehmen.
#     TIEFE regelt, wie weit der Joystick die Werte verschiebt.
#     Solange aktiv, bedient der Joystick nicht mehr die Menues (wie
#     bei Grids); hat Vorrang vor JOYSTICK>XY der Drums.
#
# NEU IN v12.14:
#   - Geplant wird auf amy.sequencer_ticks() (genau der Zaehler, mit dem
#     AMY ticks= vergleicht) statt auf dem Tick, den der Callback
#     mitbringt. Weichen beide ab, landeten geplante Noten sofort statt
#     zum Tick (= Holpern in Schueben). SETUP > INFO > TICK-ABW zeigt
#     die Abweichung (min/max).
#   - SETUP > TAKT > VORAUS-TEST: Clap sofort, dann 2 und 4 Schlaege
#     spaeter ueber ticks= - hoert man alle drei auf einmal, plant die
#     Firmware nicht -> SEQ-AUSGABE auf DIREKT stellen.
#
# NEU IN v12.13:
#   - Drum-Trigger auf CV OUT laufen ueber eigene AMY-Synths (29/30),
#     die per set_cv_out auf den Ausgang gelegt und wie die Noten mit
#     ticks= geplant werden - tick-genau zum Ton statt ueber Python/I2C
#     (in v12.12 kamen die Trigger je nach Python-Last bis zu ~100 ms
#     zu spaet -> Rack-Drums und interne Drums liefen auseinander).
#   - Zu spaet berechnete Noten werden NICHT mehr nachgespielt (sie
#     klangen ausserhalb des Rasters), sondern ausgelassen (INFO: SPAET).
#   - Fester Startpunkt: alle Spuren zaehlen von einem gemeinsamen
#     Start-Tick; MIDI-Start/-Stop (FA/FC) startet und stoppt bei
#     CLOCK = FOLGEN den Sequencer im Takt des Masters.
#   - VORLAUF ab Werk 250 ms; Speichern waehrend der Wiedergabe erst
#     nach 5 min (sonst bei STOP).
#
# NEU IN v12.12:
#   - Sequencer mit VORLAUF: Noten werden ca. 150 ms im Voraus berechnet
#     und mit ticks= auf AMYs eigene Zeitachse gelegt. AMY spielt sie
#     tick-genau - Display, Encoder, Speicherbereinigung und I2C koennen
#     den Takt nicht mehr verschieben (v12.11 spielte jede Note in dem
#     Moment, in dem Python dazu kam -> schwankendes Tempo).
#     MIDI ueber tulip.midi_out, CV-Ausgaenge und die Anzeige folgen
#     ueber eine Warteschlange zum richtigen Tick.
#   - SETUP > TAKT: SEQ-AUSGABE VORAUS/DIREKT, VORLAUF in ms
#   - SETUP > INFO: SPAET (Steps, die erst nach ihrem Tick berechnet wurden)
#
# NEU IN v12.11:
#   - Sequencer im Feinraster (tulip.seq_add_callback alle 2 AMY-Ticks,
#     3 Subs pro 32tel): Swing in 1/3-32tel-Stufen, START beginnt bei
#     Step 1, verpasste Steps werden nicht mehr gebuendelt nachgespielt
#   - Display nur in geaenderten 8-Zeilen-Baendern, waehrend der
#     Wiedergabe hoechstens 2 Baender (1 KB) pro Durchlauf
#   - Bedienung ueber eigenen Timer (40 ms) statt im Sequencer-Takt
#   - Speichern und gc.collect waehrend der Wiedergabe zurueckgestellt
#   - Mute veraendert den Headroom nicht mehr (kein Pegelsprung)
#   - Drum-Pan gedrosselt, CV-Trigger mit 1-ms-Luecke beim Neuausloesen,
#     Morph robust bei alten Szenen, Patchnamen kompakt im RAM
#   - SETUP > INFO: Messwerte (Zeichnen, Display, Seq, Speichern,
#     verpasste Steps, Bootzeit, RAM nach Boot)
#
# AUF HARDWARE ZU PRUEFEN (im Code markiert mit "HW-TEST"):
#   - (geklaert v12.9: Display hat line, kein ellipse -> Ersatz,
#     contrast ueber den Treiber; Synth-Nummern bis 31 sind erlaubt)
#   - v12.11 Display-Baender: Bild sauber? Sonst SETUP > DISPLAY >
#     UPDATE: VOLL
#   - v12.11 UI-TAKT TIMER / SEQ-TAKT FEIN (SETUP > TAKT zeigt den Stand)
#   - 303: Huellkurven bei gebundenem (Slide-)Ton
#   - Joystick: Richtung hoch/runter (JOY_Y_INVERT)
#   - Drum-Trigger: reicht ein 1/32-Gate fuer die A-140-2v? (TRIG LAENGE)
# ================================================================

import amy
import amyboard
import time
import os
import gc
import math

try:
    import json
except ImportError:
    import ujson as json

try:
    import tulip
except Exception:
    tulip = None

try:
    import midi
except Exception:
    midi = None

try:
    import framebuf
except Exception:
    framebuf = None

try:
    import random as _random
except Exception:
    _random = None

VERSION = "13.30"


# ================================================================
# KLEINE HELFER
# ================================================================

def clamp(v, lo, hi):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def clamp_int(v, lo, hi):
    v = int(v)
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def now():
    return time.ticks_ms()


def since(t):
    return time.ticks_diff(time.ticks_ms(), t)


def rnd(n):
    # Zufallszahl 0..n-1 (urandom, sonst Zeit-basiert)
    if n <= 1:
        return 0
    try:
        return _random.getrandbits(16) % n
    except Exception:
        return (time.ticks_us() // 7) % n


# Messwerte (SETUP > INFO): Hoechstwerte in Mikrosekunden, verpasste Steps
MEAS = {"draw": 0, "flush": 0, "seq": 0, "save": 0, "miss": 0, "late": 0,
        "ui": 0, "drop": 0}
TDIFF = [None, None]     # Abweichung amy.sequencer_ticks() - Callback-Tick


def meas(k, t0):
    d = time.ticks_diff(time.ticks_us(), t0)
    if d > MEAS[k]:
        MEAS[k] = d


def meas_reset():
    for k in MEAS:
        MEAS[k] = 0
    TDIFF[0] = TDIFF[1] = None


def deep_copy(obj):
    # Listen/Dicts aus Zahlen und Texten - schnell genug fuer Szenen.
    return json.loads(json.dumps(obj))


# ================================================================
# DISPLAY UND STARTBILD
# ================================================================

amyboard.init_display()

# set_display_rotation() speichert dauerhaft - nur bei Abweichung.
try:
    if amyboard.display_rotation() != 0:
        amyboard.set_display_rotation(0)
except Exception:
    pass

display = amyboard.display
_boot_ms = now()
SPLASH_MIN_MS = 1000

# Faehigkeiten des Display-Objekts (amyboard.Display: line ja,
# ellipse nein -> eigener Ersatz; contrast liegt beim SSD1327-Treiber)
HAS_LINE = hasattr(display, "line")
HAS_ELLIPSE = hasattr(display, "ellipse")
_disp_hw = getattr(display, "_hw", None)
HAS_CONTRAST = hasattr(display, "contrast") or hasattr(_disp_hw, "contrast")


def display_contrast(v):
    try:
        if hasattr(display, "contrast"):
            display.contrast(v)
        elif _disp_hw is not None:
            _disp_hw.contrast(v)
    except Exception as e:
        print("CONTRAST", e)


# Graustufen 0-15: amyboard.display ist ein GS4-Framebuffer, MicroPython
# nimmt nur die unteren 4 Bit der Farbe (bis v12.8 wurden 0-255-Werte
# benutzt - 200 wurde so zu 8, 208 zu 0 = unsichtbar).
W = 15       # hell / aktiv
HI = 12
MID = 10     # Werte
LO = 7
DIM = 5      # Beschriftungen zweiter Ordnung
GH = 2       # Hintergrund-Spuren
SEL = 8      # Auswahlbalken (schwarze Schrift darauf)


def _refresh_fw():
    try:
        amyboard.display_refresh()
    except Exception:
        try:
            display.show()
        except Exception:
            pass


# ---------------- Display in Baendern (v12.11) ----------------
# Der SSD1327-Treiber der Firmware (ssd1327.py) haelt eine Kopie des
# Panel-Inhalts (_shadow) und schickt bei show() den EINEN Block von
# der ersten bis zur letzten geaenderten Zeile - Statuszeile oben plus
# Abspielpunkt unten = fast das ganze Bild (8 KB, ~200 ms bei 400 kHz).
# Hier: 16 Baender a 8 Zeilen (512 Byte), nur geaenderte senden, und
# waehrend der Wiedergabe hoechstens FLUSH_BANDS_RUN pro Durchlauf.
# Voraussetzung: amyboard.display zeichnet in den Puffer des Treibers
# (wird beim Start mit einem Pixel geprueft), sonst wie bisher.

BAND_ROWS = 8
BAND_BYTES = 512          # 8 Zeilen x 64 Byte (GS4, 128 px)
BANDS = 16
FLUSH_BANDS_RUN = 2       # ~23 ms I2C pro Durchlauf waehrend der Wiedergabe
_fast_ok = False
_fb_mv = None
_sh_mv = None


def _fast_setup():
    global _fast_ok, _fb_mv, _sh_mv
    hw = _disp_hw
    if hw is None:
        return
    for a in ("buffer", "_shadow", "write_cmd", "write_data", "col_addr", "row_addr"):
        if not hasattr(hw, a):
            return
    if getattr(hw, "width", 0) != 128 or getattr(hw, "height", 0) != 128:
        return
    if len(hw.buffer) != BANDS * BAND_BYTES or len(hw._shadow) != BANDS * BAND_BYTES:
        return
    try:
        display.fill(0)
        display.pixel(0, 0, 15)
        shared = hw.buffer[0] != 0
        display.fill(0)
        shared = shared and hw.buffer[0] == 0
    except Exception:
        shared = False
    if shared:
        _fb_mv = memoryview(hw.buffer)
        _sh_mv = memoryview(hw._shadow)
        _fast_ok = True
    print("DISPLAY BAENDER", "JA" if _fast_ok else "NEIN")


def _send_band(hw, b, e):
    a = b * BAND_BYTES
    z = e * BAND_BYTES
    r0 = hw.row_addr[0] + b * BAND_ROWS
    hw.write_cmd(0x15)
    hw.write_cmd(hw.col_addr[0])
    hw.write_cmd(hw.col_addr[1])
    hw.write_cmd(0x75)
    hw.write_cmd(r0)
    hw.write_cmd(r0 + (e - b) * BAND_ROWS - 1)
    hw.write_data(_fb_mv[a:z])
    _sh_mv[a:z] = _fb_mv[a:z]


def flush_display(max_bands=0):
    # -> True, wenn das Panel jetzt dem Puffer entspricht
    global _fast_ok
    if not (_fast_ok and S["dfast"]):
        _refresh_fw()
        return True
    hw = _disp_hw
    try:
        if not hw._shadow_valid:
            hw.show(True)
            return True
        mb = _fb_mv
        ms = _sh_mv
        sent = 0
        b = 0
        while b < BANDS:
            a = b * BAND_BYTES
            if mb[a:a + BAND_BYTES] == ms[a:a + BAND_BYTES]:
                b += 1
                continue
            if max_bands and sent >= max_bands:
                return False
            e = b + 1
            while e < BANDS and not (max_bands and sent + (e - b) >= max_bands):
                a2 = e * BAND_BYTES
                if mb[a2:a2 + BAND_BYTES] == ms[a2:a2 + BAND_BYTES]:
                    break
                e += 1
            _send_band(hw, b, e)
            sent += e - b
            b = e
        return True
    except Exception as e:
        print("DISPLAY BAND", e)
        _fast_ok = False
        _refresh_fw()
        return True


def refresh():
    # Vollstaendig senden (Startbild, Schoner, Werksreset)
    if _fast_ok:
        flush_display(0)
    else:
        _refresh_fw()


def _splash():
    display.fill(0)
    display.text("DOLPHIN", 36, 34, W)
    display.text("SELECTOR 3", 24, 46, DIM)
    x = 22
    for h in (4, 9, 14, 20, 14, 9, 4, 9, 14, 20, 14):
        display.fill_rect(x, 84 - h, 4, h, HI if h > 12 else LO)
        x += 8
    display.text("v" + VERSION, 48, 100, GH + 3)
    refresh()


try:
    _splash()
except Exception as e:
    print("SPLASH", e)

try:
    _fast_setup()
except Exception as e:
    print("DISPLAY SETUP", e)


# ================================================================
# ENCODER
# ================================================================
#
# amyboard.encoder() legt alle Geraete in einen flachen Indexraum
# (accessories.md: M5Stack, Quads, ANOs, Singles). enc.devices
# liefert sie in genau dieser Reihenfolge.

try:
    enc = amyboard.encoder(invert=False)
except Exception:
    enc = None

ENC_PER_DEV = {"m5stack": 8, "adafruit_quad": 4,
               "adafruit_single": 1, "adafruit_ano": 1}
BTN_PER_DEV = {"adafruit_ano": 5}


def _device_blocks():
    blocks = []
    if enc is None:
        return blocks
    try:
        devices = enc.devices
    except Exception:
        return blocks
    off = 0
    for typ, addr in devices:
        blocks.append((typ, addr, off))
        off += ENC_PER_DEV.get(typ, 0)
    return blocks


_blocks = _device_blocks()

NAV_ENCODER = 0
NAV_BUTTON = 0
_nav_found = None
_boff = 0
for _t, _a, _s in _blocks:
    if _t == "adafruit_single" and _nav_found != "adafruit_single":
        NAV_ENCODER, NAV_BUTTON, _nav_found = _s, _boff, _t
    elif _t == "adafruit_ano" and _nav_found is None:
        NAV_ENCODER, NAV_BUTTON, _nav_found = _s, _boff, _t
    _boff += BTN_PER_DEV.get(_t, ENC_PER_DEV.get(_t, 0))

# Zusatz-Encoder (v13.15): M5Stack UND Quads gleichzeitig. Jeder
# Encoder hat einen festen Platz (Slot) in S["encf"]:
#   0-7   E1-E8   erster M5Stack 8-Encoder
#   8-11  Q1-Q4   erster Adafruit Quad #5752
#   12-15 Q5-Q8   zweiter Quad
# So bleibt die Zuordnung erhalten, auch wenn ein Geraet mal fehlt.
# PARAM_ENCODERS[i] = Encoder-Index fuer amyboard, ENC_SLOT[i] = Slot.
ENC_SLOTS = 16
ENC_SLOT_NAMES = (["E%d" % (i + 1) for i in range(8)]
                  + ["Q%d" % (i + 1) for i in range(8)])
PARAM_ENCODERS = []
ENC_SLOT = []
PARAM_BUTTONS = []       # v13.19: Taster-Index je Zusatz-Encoder
ENC_DEVS = []            # erkannte Geraete fuer SETUP > ENCODER
_nq = 0
_nm = 0
_bb = 0                  # Taster-Versatz (ANO belegt 5 Taster)
for _t, _a, _s in _blocks:
    if _t == "m5stack" and _nm == 0:
        _nm = 1
        ENC_DEVS.append("M5")
        for _i in range(8):
            PARAM_ENCODERS.append(_s + _i)
            PARAM_BUTTONS.append(_bb + _i)
            ENC_SLOT.append(_i)
    elif _t == "adafruit_quad" and _nq < 2:
        ENC_DEVS.append("QUAD")
        for _i in range(4):
            PARAM_ENCODERS.append(_s + _i)
            PARAM_BUTTONS.append(_bb + _i)
            ENC_SLOT.append(8 + 4 * _nq + _i)
        _nq += 1
    _bb += BTN_PER_DEV.get(_t, ENC_PER_DEV.get(_t, 0))
del _nq, _nm, _bb

# v13.24: LED-Index (amyboard zaehlt LEDs fortlaufend ueber alle Geraete)
# und Geraete-Nummer (0 = M5Stack, 1/2 = Quad 1/2) je Zusatz-Encoder
LED_PER_DEV = {"m5stack": 8, "adafruit_quad": 4, "adafruit_single": 1}
ENC_LED = []
ENC_DEVNO = []
NAV_LED = None           # v13.29: LED des Navigations-Encoders (Single)
_lo = 0
_nq = 0
_nm = 0
for _t, _a, _s in _blocks:
    if _t == "m5stack" and _nm == 0:
        _nm = 1
        for _i in range(8):
            ENC_LED.append(_lo + _i)
            ENC_DEVNO.append(0)
    elif _t == "adafruit_quad" and _nq < 2:
        _nq += 1
        for _i in range(4):
            ENC_LED.append(_lo + _i)
            ENC_DEVNO.append(_nq)
    elif _t == "adafruit_single" and _s == NAV_ENCODER and NAV_LED is None:
        NAV_LED = _lo
    _lo += LED_PER_DEV.get(_t, 0)
del _lo, _nq, _nm


def enc_page_index(slot):
    # Welcher Seiten-Regler (enc_param) gehoert zu einem Slot bei SEITE:
    # E1-E8 -> 0-7, Q1-Q4 und Q5-Q8 -> 0-3 (wie frueher ein Quad allein)
    return slot if slot < 8 else (slot - 8) % 4

try:
    encoder_count = enc.encoders if enc is not None else 0
except Exception:
    encoder_count = 0


# ================================================================
# JOYSTICK (M5Stack, Adresse 0x52 - wie m5joy.py, eigener Bus
# wird nicht angelegt)
# ================================================================

JOY_ADDR = 0x52
JOY_DEADZONE = 0.15
JOY_Y_DEADZONE = 0.3     # hoch/runter nur bei deutlicher Auslenkung
JOY_Y_INVERT = False     # HW-TEST: Richtung hoch/runter
_JOY_REG = bytes([3])

try:
    _i2c = amyboard.get_i2c()
    joystick_available = JOY_ADDR in _i2c.scan()
except Exception:
    _i2c = None
    joystick_available = False


def joystick_read():
    try:
        _i2c.writeto(JOY_ADDR, _JOY_REG)
        b = _i2c.readfrom(JOY_ADDR, 3)
        return (b[0] / 255.0, b[1] / 255.0, b[2])
    except Exception:
        return None


# ================================================================
# SPEICHERORT: SD-KARTE ODER FLASH
# ================================================================

def sd_present():
    try:
        os.stat("/sd")
        return True
    except Exception:
        return False


# Speicherort per Schreibtest waehlen. Frueher: schlug mount_sd()
# fehl (z.B. weil die Karte schon eingehaengt war), landete alles in
# /user/current/ - beim naechsten Start evtl. woanders gesucht.
try:
    amyboard.mount_sd()
except Exception as e:
    print("MOUNT SD", e)

STORE_DIRS = ("/sd/", "/user/", "/")


def _dir_writable(d, kb=4):
    probe = d + ".dolphin_probe"
    gc.collect()         # wie beim Speichern (siehe _sd_mount_fresh)
    try:
        # Stuecke a 512 Byte - ein Mini-Test uebersah Fehler bei
        # groesseren Dateien (EIO beim Speichern). Fuer die SD-Karte
        # 32 KB (v13.6: 4 KB gingen, 10 KB Zustand nicht)
        blk = b"0123456789abcdef" * 32
        n = kb * 2
        f = open(probe, "wb")
        for _ in range(n):
            f.write(blk)
        f.close()
        f = open(probe, "rb")
        ok = True
        for _ in range(n):
            if f.read(512) != blk:
                ok = False
                break
        f.close()
        try:
            os.remove(probe)
        except Exception:
            pass
        return ok
    except Exception as e:
        print("NICHT BESCHREIBBAR", d, e)
        return False


SD_PINS = dict(sck=12, miso=13, mosi=11, cs=10, slot=2)


# SPI-Takt der Karte: Schreibfehler (EIO) bei groesseren Dateien trotz
# frisch formatierter Karte deuten auf zu schnellen Takt / Leitungen.
# Getestet wird von schnell nach langsam; der passende Takt wird im
# internen Flash gemerkt (/user/sd_freq.txt), weil der Zustand selbst
# ja auf der Karte liegt.
SD_FREQS = (20000000, 10000000, 5000000, 2000000, 1000000, 400000)
SD_FREQ_FILE = "/user/sd_freq.txt"
sd_freq = 0              # 0 = Standard-Takt
sd_pull = False          # v13.8: interne Pull-ups auf den SD-Leitungen
_sd_card = None          # eigenes SDCard-Objekt (fuer deinit)


def _sd_freq_load():
    # -> (takt, pullup) oder None
    try:
        f = open(SD_FREQ_FILE)
        t = f.read().strip().split(",")
        f.close()
        v = int(t[0])
        p = len(t) > 1 and t[1] == "1"
        if v == 0 or v in SD_FREQS:
            return (v, p)
    except Exception:
        pass
    return None


def _sd_freq_save(v, p=False):
    try:
        f = open(SD_FREQ_FILE, "w")
        f.write("%d,%d" % (v, 1 if p else 0))
        f.close()
    except Exception as e:
        print("SD FREQ SAVE", e)


def _sd_pullups():
    # Pull-ups vor dem Anlegen der Karte setzen (MISO, MOSI, CS, SCK).
    # Ohne Pull-up auf MISO lesen manche Aufbauten, scheitern aber beim
    # Schreiben (Karte meldet "busy" nicht sauber) -> E5.
    try:
        from machine import Pin
        for p in (SD_PINS["miso"], SD_PINS["mosi"], SD_PINS["cs"]):
            Pin(p, Pin.IN, Pin.PULL_UP)
    except Exception as e:
        print("SD PULLUP", e)


def _sd_mount_fresh(freq=0, pull=False):
    # Aushaengen und selbst neu einhaengen (Pins wie in amyboard.py).
    # -> None bei Erfolg, sonst die Ausnahme
    global sd_freq, sd_pull, _sd_card
    try:
        os.umount("/sd")
    except Exception:
        pass
    if _sd_card is not None:
        try:
            _sd_card.deinit()
        except Exception:
            pass
        _sd_card = None
    # v13.9: verwaiste SDCard-Objekte JETZT aufraeumen. Sonst gibt die
    # Speicherbereinigung sie irgendwann spaeter frei - ihr Finalizer
    # schaltet dabei den gemeinsamen SPI-Slot ab, und die gerade
    # eingehaengte Karte liefert ab da E5 beim Schreiben (genau das
    # Bild aus SD TEST: Test direkt nach dem Einhaengen OK, Speichern
    # danach - mit gc.collect() - E5).
    gc.collect()
    err = None
    try:
        import machine
        if pull:
            _sd_pullups()
        if freq:
            card = machine.SDCard(freq=freq, **SD_PINS)
        else:
            card = machine.SDCard(**SD_PINS)
        os.mount(os.VfsFat(card), "/sd")
        _sd_card = card
        sd_freq = freq
        sd_pull = pull
    except Exception as e:
        err = e
        sd_freq = 0
        sd_pull = False
        print("SD MOUNT", repr(e))
        try:                              # Weg der Firmware versuchen
            amyboard.mount_sd()
        except Exception:
            pass
    return err


def _sd_cfg_txt(f, p):
    t = ("%dK" % (f // 1000)) if f and f < 1000000 else (("%dM" % (f // 1000000)) if f else "STD")
    return t + (" PU" if p else "")


# v13.2: Ist /sd beim Start nicht beschreibbar, die Karte einmal selbst
# neu einhaengen und erneut pruefen (vorher landete der Stand in /user/,
# obwohl SD EINBINDEN danach funktionierte).
_sd_boot = "OK"
_f = _sd_freq_load()
# v13.9: immer selbst einhaengen (das Einhaengen der Firmware konnte nach
# einer Speicherbereinigung nicht mehr schreiben)
if _f is None:
    _f = (0, False)
_sd_mount_fresh(_f[0], _f[1])
time.sleep_ms(20)
if not _dir_writable("/sd/", 4):
    print("SD BEIM START NICHT BESCHREIBBAR - HAENGE NEU EIN")
    _sd_boot = "FEHLT"
    _sd_mount_fresh(0, False)
    time.sleep_ms(20)
    if _dir_writable("/sd/", 4):
        _sd_boot = "NEU EINGEH."

BASE = None
for _d in STORE_DIRS:
    if _dir_writable(_d):
        BASE = _d
        break
if BASE is None:
    BASE = "/sd/"
    print("KEIN BESCHREIBBARER ORT GEFUNDEN")

STATE_FILE = BASE + "dolphin_state.json"
SCENE_FILE = BASE + "dolphin_scenes.json"
STATE_TMP = STATE_FILE + ".tmp"
STATE_BAK = STATE_FILE + ".bak"
# Alte Orte (v12.0-v12.2), falls dort noch ein Stand liegt
LEGACY_STATE = [d + "dolphin_state.json" for d in ("/sd/", "/user/current/", "/user/", "/")
                if d != BASE]
WLAN_CRED_FILE = "/sd/wifi_credentials.txt"
print("STATE ->", STATE_FILE)


# ================================================================
# PATCHES
# ================================================================
#
# amy/docs/api.md "K": 0-127 Juno, 128-255 DX7, 256 Piano,
# 257 AMYboard Default, 384-390 Gamma9001 GM-Drumkits.
# (258 gibt es auf GAMMA9001-Geraeten nicht.)

PIANO_PATCH = 256
AMYB_PATCH = 257
DRUM_PATCH = 384
DRUM_CHANNEL = 10
DRUM_KITS = list(range(384, 391))
ALL_PATCHES = list(range(0, 256)) + [PIANO_PATCH, AMYB_PATCH] + DRUM_KITS
PATCH_POS = {}
for _i, _p in enumerate(ALL_PATCHES):
    PATCH_POS[_p] = _i

# Namen als je EIN Text mit "|" statt 2 x 128 Einzeltexten (v12.11):
# spart internierte Texte und zwei Listen im RAM.
_JUNO_TXT = "Brass Set 1|Brass Swell|Trumpet|Flutes|Moving Strings|Brass & Strings|Choir|Piano I|Organ I|Organ II|Combo Organ|Calliope|Donald Pluck|Celeste|Elect Piano I|Elect Piano II|Clock Chimes|Steel Drums|Xylophone|Brass III|Fanfare|String III|Pizzicato|High Strings|Bass Clarinet|English Horn|Brass Ensemble|Guitar|Koto|Dark Pluck|Funky I|Synth Bass I|Lead I|Lead II|Lead III|Funky II|Synth Bass II|Funky III|Thud Wah|Going Up|Piano II|Clav|Frontier Organ|Snare Drum|Tom Toms|Timpani|Shaker|Synth Pad|Sweep I|Pluck Sweep|Repeater|Sweep II|Pluck Bell|Dark Synth Piano|Sustainer|Wah Release|Gong|Resonance Funk|Drum Booms|Dust Storm|Rocket Men|Hand Claps|FX Sweep|Caverns|Strings|Violin|Chorus Vibes|Organ 1|Harpsichord 1|Recorder|Perc. Pluck|Noise Sweep|Space Chimes|Nylon Guitar|Orchestral Pad|Bright Pluck|Organ Bell|Accordion|FX Rise 1|FX Rise 2|Brass|Helicopter|Lute|Chorus Funk|Tomita|FX Sweep 1|Sharp Reed|Bass Pluck|Resonant Rise|Harpsichord 2|Dark Ensemble|Contact Wah|Noise Sweep 2|Glassy Wah|Phase Ensemble|Chorused Bell|Clav|Organ 2|Bassoon|Auto Release Noise|Brass Ensemble|Ethereal|Chorus Bell 2|Blizzard|E Piano Tremolo|Clarinet|Thunder|Reedy Organ|Flute / Horn|Toy Rhodes|Surf's Up|OW Bass|Piccolo|Melodic Taps|Meow Brass|Violin High|High Bells|Rolling Wah|Ping Bell|Brassy Organ|Low Dark Strings|Piccolo Trumpet|Cello|High Strings|Rocket Men|Forbidden Planet|Froggy|Owgan"
_DX7_TXT = "BRASS 1|BRASS 2|BRASS 3|STRINGS 1|STRINGS 2|STRINGS 3|ORCHESTRA|PIANO 1|PIANO 2|PIANO 3|E.PIANO 1|GUITAR 1|GUITAR 2|SYN-LEAD 1|BASS 1|BASS 2|E.ORGAN 1|PIPES 1|HARPSICH 1|CLAV 1|VIBE 1|MARIMBA|KOTO|FLUTE 1|ORCH-CHIME|TUB BELLS|STEEL DRUM|TIMPANI|REFS WHISL|VOICE 1|TRAIN|TAKE OFF|PIANO 4|PIANO 5|E.PIANO 2|E.PIANO 3|E.PIANO 4|PIANO 5THS|CELESTE|TOY PIANO|HARPSICH 2|HARPSICH 3|CLAV 2|CLAV 3|E.ORGAN 2|E.ORGAN 3|E.ORGAN 4|E.ORGAN 5|PIPES 2|PIPES 3|PIPES 4|CALIOPE|ACCORDION|SITAR|GUITAR 3|GUITAR 4|GUITAR 5|GUITAR 6|LUTE|BANJO|HARP 1|HARP 2|BASS 3|BASS 4|PICCOLO|FLUTE 2|OBOE|CLARINET|SAX BC|BASSOON|STRINGS 4|STRINGS 5|STRINGS 6|STRINGS 7|STRINGS 8|BRASS 4|BRASS 5|BRASS 6 BC|BRASS 7|BRASS 8|RECORDER|HARMONICA1|HRMNCA2 BC|VOICE 2|VOICE 3|GLOKENSPL|VIBE 2|XYLOPHONE|CHIMES|GONG 1|GONG 2|BELLS|COW BELL|BLOCK|FLEXATONE|LOG DRUM|SYN-LEAD 2|SYN-LEAD 3|SYN-LEAD 4|SYN-LEAD 5|SYN-CLAV 1|SYN-CLAV 2|SYN-CLAV 3|SYN-PIANO|SYNBRASS 1|SYNBRASS 2|SYNORGAN 1|SYNORGAN 2|SYN-VOX|SYN-ORCH|SYN-BASS 1|SYN-BASS 2|HARP-FLUTE|BELL-FLUTE|E.P-BRS BC|T.BL-EXPA|CHIME-STRG|B.DRM-SNAR|SHIMMER|EVOLUTION|WATER GDN|WASP STING|LASER GUN|DESCENT|OCTAVE WAR|GRAND PRIX|ST.HELENS|EXPLOSION"


def _name_index(txt):
    offs = [0]
    i = txt.find("|")
    while i >= 0:
        offs.append(i + 1)
        i = txt.find("|", i + 1)
    offs.append(len(txt) + 1)
    try:
        from array import array
        return array("H", offs)
    except Exception:
        return offs


_JUNO_OFF = _name_index(_JUNO_TXT)
_DX7_OFF = _name_index(_DX7_TXT)
DRUM_KIT_NAMES = ("TR-808", "TR-909", "LINN 9000", "MR-12", "TOKYO",
                  "80s POWER", "PERCUSSION")


def chan_patch_name(ch):
    # Patchname eines Kanals; der CHROM.-Kanal zeigt seinen Sample-Slot
    try:
        if chrom_owns(ch):
            k = S["sb"]["cs"]
            return "SMP S%d %s" % (k + 1, slot_name(k))
    except Exception:
        pass
    return patch_name(S["pat"][ch])


def patch_name(p):
    if p == -1:
        return "---"
    if 0 <= p <= 127:
        return _JUNO_TXT[_JUNO_OFF[p]:_JUNO_OFF[p + 1] - 1]
    if 128 <= p <= 255:
        q = p - 128
        return _DX7_TXT[_DX7_OFF[q]:_DX7_OFF[q + 1] - 1]
    if p == PIANO_PATCH:
        return "PIANO"
    if p == AMYB_PATCH:
        return "AMYBOARD DEF"
    if 384 <= p <= 390:
        return DRUM_KIT_NAMES[p - 384]
    if USER_BASE < p <= USER_BASE + 16:
        e = S["syx"][p - USER_BASE]
        return e[2] if e else "SD DX7"
    return "PATCH %d" % p


def family(p):
    if p == -1:
        return "NONE"
    if 0 <= p <= 127:
        return "JUNO"
    if 128 <= p <= 255:
        return "DX7"
    if p == PIANO_PATCH:
        return "PIANO"
    if p == AMYB_PATCH:
        return "AMYB"
    if 384 <= p <= 390:
        return "DRUM"
    if USER_BASE < p <= USER_BASE + 16:
        return "DX7"              # DX7-Stimme von der SD-Karte (v13.19)
    return "OTHER"


FAMILY_SHORT = {"NONE": "---", "JUNO": "JUNO", "DX7": "DX7", "PIANO": "PNO",
                "AMYB": "AMYB", "DRUM": "DRUM", "OTHER": "?"}


def is_drum(p):
    return 384 <= p <= 390


# Kategorien fuer den Patch-Browser - aus den Namen abgeleitet,
# erster Treffer gewinnt.
CAT_DEFS = (
    ("BASS", ("BASS", "BOOM", "THUD")),
    ("LEAD", ("LEAD", "FUNK", "WAH", "TOMITA")),
    ("PAD", ("STRING", "PAD", "CHOIR", "ENSEMBLE", "SWEEP", "ETHEREAL",
             "ORCH", "VOICE", "VOX", "SUSTAIN", "CAVERN", "VIOLIN", "CELLO")),
    ("KEYS", ("PIANO", "ORGAN", "CLAV", "HARPSI", "CELESTE", "RHODES",
              "CALIOPE", "CALLIOPE", "ACCORDION", "OWGAN", "E.P")),
    ("BRASS/WIND", ("BRASS", "TRUMPET", "HORN", "FANFARE", "FLUTE", "CLARINET",
                    "OBOE", "BASSOON", "SAX", "RECORDER", "PICCOLO", "REED",
                    "HARMONICA", "HRMNCA", "PIPES")),
    ("PLUCK", ("PLUCK", "GUITAR", "KOTO", "LUTE", "SITAR", "BANJO", "HARP",
               "PIZZ", "NYLON")),
    ("BELL/PERC", ("BELL", "CHIME", "VIBE", "MARIMBA", "XYLO", "GLOKEN",
                   "STEEL", "GONG", "BLOCK", "TIMPANI", "DRUM", "TOM", "SNARE",
                   "SHAKER", "CLAP", "LOG", "COW", "TAPS", "FLEXATONE", "B.DRM")),
    ("FX", ("FX", "RISE", "NOISE", "HELICOPTER", "ROCKET", "THUNDER", "LASER",
            "EXPLOSION", "TRAIN", "TAKE OFF", "WASP", "DESCENT", "GRAND PRIX",
            "ST.HELENS", "BLIZZARD", "DUST", "SURF", "FROGGY", "FORBIDDEN",
            "WHISL", "WAR", "SPACE", "WATER", "EVOLUTION", "SHIMMER",
            "REPEATER", "GOING UP", "MEOW")),
)


def _build_categories():
    cats = [[] for _ in CAT_DEFS]
    other = []
    for p in range(256):
        nm = patch_name(p).upper()
        hit = -1
        for ci in range(len(CAT_DEFS)):
            for k in CAT_DEFS[ci][1]:
                if k in nm:
                    hit = ci
                    break
            if hit >= 0:
                break
        if hit >= 0:
            cats[hit].append(p)
        else:
            other.append(p)
    cats[3].append(PIANO_PATCH)
    cats[3].append(AMYB_PATCH)
    return cats, other


PATCH_CATS, PATCH_OTHER = _build_categories()


# ================================================================
# MUSIK-TABELLEN
# ================================================================

CHORD_NAMES = ["AUS", "DUR", "MOLL", "DUR7", "MOLL7", "DOM7",
               "DUR9", "MOLL9", "ADD9", "SUS4", "QUINT", "OKTAVE"]
CHORD_INTERVALS = [[], [4, 7], [3, 7], [4, 7, 11], [3, 7, 10], [4, 7, 10],
                   [4, 7, 11, 14], [3, 7, 10, 14], [4, 7, 14], [5, 7], [7], [12]]

SCALE_NAMES = ("CHROM", "MAJOR", "MINOR", "DORIAN", "PHRYG", "LYDIAN",
               "MIXOLY", "MAJ PENT", "MIN PENT", "BLUES", "HARM MIN",
               "MELOD MIN", "WHOLE")
SCALES = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11),
    (0, 2, 4, 5, 7, 9, 11), (0, 2, 3, 5, 7, 8, 10), (0, 2, 3, 5, 7, 9, 10),
    (0, 1, 3, 5, 7, 8, 10), (0, 2, 4, 6, 7, 9, 11), (0, 2, 4, 5, 7, 9, 10),
    (0, 2, 4, 7, 9), (0, 3, 5, 7, 10), (0, 3, 5, 6, 7, 10),
    (0, 2, 3, 5, 7, 8, 11), (0, 2, 3, 5, 7, 9, 11), (0, 2, 4, 6, 8, 10),
)
NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


def note_name(n):
    n = int(n)
    return "%s%d" % (NOTE_NAMES[n % 12], n // 12 - 1)


def scale_note(root, degree, scale_index):
    sc = SCALES[scale_index % len(SCALES)]
    degree = int(degree)
    return clamp_int(int(root) + sc[degree % len(sc)] + 12 * (degree // len(sc)), 0, 127)


# GM-Drumnoten -> Kurzname fuer das Drum-Raster (2 Zeichen).
# Die TR-8S nutzt ab Werk dieselben Noten fuer BD/SD/RS/CP/CH/OH/Toms.
GM_DRUM_LABELS = {35: "BD", 36: "BD", 37: "RS", 38: "SD", 39: "CP", 40: "SD",
                  41: "LF", 42: "CH", 43: "FT", 44: "PH", 45: "LT", 46: "OH",
                  47: "MT", 48: "HT", 49: "CC", 50: "HT", 51: "RC", 52: "CN",
                  53: "RB", 54: "TB", 55: "SC", 56: "CB", 57: "CC", 59: "RC",
                  60: "BO", 61: "BO", 62: "CO", 63: "CO", 64: "CO", 69: "CA",
                  70: "MA", 75: "CL", 76: "WB", 77: "WB", 58: "VS", 65: "TI",
                  66: "TI", 67: "AG", 68: "AG", 71: "WH", 72: "WH", 73: "GU",
                  74: "GU", 78: "CU", 79: "CU", 80: "TR", 81: "TR"}

# Klangliste fuer DRUMS > SOUND: GM-Drumnoten mit Namen. Belegt sind
# in allen Gamma9001-Kits (patches.h) 35-57, 59-72, 75-77, 80, 81;
# dem TR-808-Kit (384) fehlen 71, 72, 80 und 81.
GM_DRUM_NAME = {35: "KICK 2", 36: "KICK", 37: "RIM", 38: "SNARE", 39: "CLAP",
                40: "SNARE 2", 41: "TOM LF", 42: "HH ZU", 43: "TOM FT",
                44: "HH PED", 45: "TOM LO", 46: "HH OFFN", 47: "TOM LM",
                48: "TOM HM", 49: "CRASH", 50: "TOM HI", 51: "RIDE", 52: "CHINA",
                53: "RIDE BL", 54: "TAMB", 55: "SPLASH", 56: "COWBELL",
                57: "CRASH 2", 59: "RIDE 2", 60: "BONGO H", 61: "BONGO L",
                62: "CONGA HM", 63: "CONGA HO", 64: "CONGA L", 65: "TIMBAL H",
                66: "TIMBAL L", 67: "AGOGO H", 68: "AGOGO L", 69: "CABASA",
                70: "MARACAS", 71: "PFEIFE K", 72: "PFEIFE L", 75: "CLAVES",
                76: "WOOD H", 77: "WOOD L", 80: "TRIANG Z", 81: "TRIANG O"}
KIT_NOTES_ALL = sorted(GM_DRUM_NAME)
KIT_NOTES_808 = [n for n in KIT_NOTES_ALL if n not in (71, 72, 80, 81)]


def drum_row_label(k):
    # Kurzname einer Drum-Zeile: Sample-Slot oder GM-Drum
    try:
        sk = S["drm"]["smp"][k]
        if sk >= 0:
            pc = S["drm"]["sli"][k]
            if pc and slot_chops(sk):
                return "%d%s" % (sk + 1, "abcdefghijklmnop"[pc - 1])
            return "S%d" % (sk + 1)
    except Exception:
        pass
    return drum_label(S["drm"]["notes"][k])


def drum_label(n):
    return GM_DRUM_LABELS.get(n, "%02d" % (n % 100))


# Klangprofile (EQ low/mid/high in dB) je Bus
PROFILES = (("MANUELL", None), ("NEUTRAL", (0.0, 0.0, 0.0)),
            ("WARM", (2.0, 0.0, -2.0)), ("PUNCH", (3.0, -1.5, 2.0)),
            ("HELL", (-1.0, 0.0, 3.0)))
PROFILE_NAMES = [p[0] for p in PROFILES]


# ================================================================
# ZUSTAND  (alles Speicherbare liegt in EINEM Dict S)
# ================================================================

CHORUS_MAX_DELAY = 512.0
ECHO_MAX_DELAY_MS = 1000
ACID_STEPS_MAX = 16
SEQ_MAX_STEPS = 32
NUM_PATTERNS = 4

TONE_DEF = (("cut", 8000.0), ("res", 0.7), ("att", 30), ("dec", 250),
            ("sus", 0.7), ("rel", 400), ("lfr", 2.0), ("lfd", 0.2),
            ("alg", 1), ("fb", 0))

ACID_DEFAULT_PATTERN = [
    [0, 0, 1, 0], [0, 0, 0, 1], [12, 0, 0, 0], [0, 0, 1, 0],
    [-1, 0, 0, 0], [3, 0, 0, 0], [0, 0, 1, 0], [7, 0, 0, 1],
    [0, 0, 0, 0], [-1, 0, 0, 0], [10, 0, 1, 0], [0, 0, 0, 1],
    [12, 0, 0, 0], [0, 0, 1, 0], [3, 0, 0, 1], [5, 0, 0, 0],
]

# Drum-Spur: 8 Instrumente, pro Pattern und Instrument ein Text mit
# 32 Hex-Zeichen (ein Zeichen = ein Step, 0 = aus, 1-f = Velocity).
# Kompakt im JSON (~1 KB fuer 4 Patterns).
DRUM_ROWS = 8
DRUM_DEFAULT_NOTES = (36, 38, 42, 46, 39, 45, 50, 37)   # BD SD CH OH CP LT HT RS
DRUM_EMPTY = "0" * SEQ_MAX_STEPS
DRUM_START = ("f000f000f000f000", "0000f0000000f000",
              "a0a0a0a0a0a0a0a0", "00000000000000c0")
HEX_DIGITS = "0123456789abcdef"


DRUM_GRID_DENS = (10, 9, 10, 7, 6, 6, 6, 6)   # Grids-Dichte ab Werk je Instrument


def new_drums():
    return {"ch": DRUM_CHANNEL, "mute": 0, "pat": 0, "div": 1, "out": 0,
            "mch": DRUM_CHANNEL, "lens": [16] * DRUM_ROWS,
            "notes": list(DRUM_DEFAULT_NOTES), "mutes": [0] * DRUM_ROWS,
            "pats": [[DRUM_EMPTY] * DRUM_ROWS for _ in range(NUM_PATTERNS)],
            # CV-Trigger: Instrument (-1 = aus) fuer OUT1/OUT2, Laenge in
            # 1/32, Pegel 0 = 5 V, 1 = 8 V, 2 = Velocity (0-8 V)
            "trg": [-1, -1], "tlen": 1, "tlv": 0,
            # Grids: Modus 0 = PATTERN, 1 = LIVE; X/Y 0-1; Zufall 0-15;
            # Dichte je Instrument 0-15; CV IN1/2 -> X/Y; Joystick -> X/Y
            "gm": 0, "gx": 0.0, "gy": 0.0, "gz": 0,
            "gd": list(DRUM_GRID_DENS), "gcv": 0, "gj": 0,
            # v13.0: Sample-Slot je Instrument (-1 = Drumkit-Klang)
            "smp": [-1] * DRUM_ROWS,
            # v13.18: Slice je Instrument (0 = ganzes Sample, 1-16)
            "sli": [0] * DRUM_ROWS}


def _hex_row(s):
    if not isinstance(s, str):
        s = ""
    s = "".join([c if c in HEX_DIGITS else "0" for c in s.lower()[:SEQ_MAX_STEPS]])
    return s + "0" * (SEQ_MAX_STEPS - len(s))


def new_track(ch, note):
    return {"ch": ch, "steps": 8, "div": 1, "mode": 0, "note": note,
            "gate": 6, "pul": 4, "scale": 1, "mute": 0, "out": 0,
            "mch": ch, "pat": 0,
            "pats": [[0] * SEQ_MAX_STEPS for _ in range(NUM_PATTERNS)],
            "adir": 0, "aoct": 1, "ain": 1, "latch": 0}


# ---------------- Sampler-Slots (v13.0) ----------------
SMP_SLOTS = 8


def new_slot():
    # Zeiten in ms ab Dateianfang; en = 0 heisst "bis zum Ende",
    # le = 0 heisst "Loop bis ENDE"
    return {"f": "", "st": 0, "en": 0, "ls": 0, "le": 0, "pm": 0,
            "tu": 0, "fi": 0, "rt": 60, "lv": 1.0, "pan": 0.5, "bus": 1,
            "at": 0, "de": 300, "su": 1.0, "re": 80,
            "ft": 0, "cu": 8000.0, "rs": 0.7, "fe": 0.0, "fd": 300,
            # v13.17: TAKT-SYNC in Schlaegen (0 = aus), Grain-Suche
            "sy": 0, "fs": 64,
            # v13.18: Anzahl Slices (0 = aus)
            "nc": 0}


def new_sampler():
    return {"sl": [new_slot() for _ in range(SMP_SLOTS)],
            "ch": 0, "cs": 0, "pch": 0, "cv": 4,
            "src": 0, "len": 4, "unit": 0, "rst": 0, "rs": 0,
            # v13.14: Aufnahme danach automatisch auf SD speichern
            "asv": 1,
            # v13.19: Slot, dessen Slices der PAD-KANAL ab Note 44 spielt
            "ss": 0}


# Zusatz-Encoder ab Werk: E1-E4 Seite, E5-E8 Master/Level/Reverb/Echo,
# Q1-Q4 Patch Kanal 1-4, Q5-Q8 aus (v13.15)
ENCB_DEFAULT = ("KONTEXT",) * 16      # Taster je Zusatz-Encoder (v13.19)


def new_vco():
    # v13.21: on, Tonhoehe-Eingang (0 AUS, 1 IN1, 2 IN2), Welle, Grundton
    # (Note bei 0 V), Fein (Cent), V/Okt-Abgleich, Pulsbreite, Sub-Pegel,
    # Sub-Oktave (1/2), Osz-2-Pegel, Osz-2-Intervall (HT), Verstimmung
    # (Cent), Pitch-Modus (0 FREI, 1 QUANT), Skala, Mod-Eingang, Mod-Ziel,
    # Mod-Tiefe, Fold-Typ/Drive/Mix, Level, Pan, Bus
    return {"on": 0, "src": 1, "wav": 2, "root": 24, "fine": 0, "trk": 1.0,
            "pw": 0.5, "sub": 0.0, "so": 1, "o2": 0.0, "iv": 0, "det": 7,
            "pm": 0, "sc": 0, "msrc": 0, "mt": 0, "md": 0.3,
            "ft": 0, "fd": 2.0, "fm": 1.0, "lvl": 0.8, "pan": 0.5, "bus": 0,
            "sm": 0}


def new_sv():
    # v13.30 Schoner: bild 0 = ZUFALL, 1-8 festes Bild, 9 = TEXT; pool = Bits
    # der Bilder im Zufall; wz/lz/hl = Index WECHSEL/LEERLAUF/KONTRAST
    return {"bild": 0, "pool": 255, "wz": 1, "lz": 0, "hl": 1, "fly": "DOLPHIN"}


def new_led():
    # v13.29 LEDs: hl Helligkeit 0-3, nav Farbe der Navigation (0 = Kanal,
    # sonst Index in LED_RGB), ed/bt/pn/wn Farbe fuer EDIT/TAKT/PANIC/
    # WARNUNG (0 AUTO, 1 AUS = Anzeige aus), cf Kanal-Blitz, st Zustand der
    # Zusatz-Encoder, fl Dreh-Blitz, sv im Schoner (0 = LEDs aus)
    return {"hl": 1, "nav": 0, "ed": 0, "bt": 0, "pn": 0, "wn": 0,
            "cf": 1, "st": 1, "fl": 1, "sv": 0}


def new_ain():
    # v13.22 AUDIO IN: an/aus, Modus (0 STEREO, 1 MONO, 2 NUR L, 3 NUR R),
    # Eingangsverstaerkung (dB), Ausgangspegel, Pan, Breite (STEREO), Bus,
    # Filter (Typ wie Sample-Slots, Cutoff, Resonanz), Distortion (Typ,
    # Drive, Mix). Ab Werk aus, eigener Bus 2 (trocken).
    return {"on": 0, "mode": 0, "gain": 0.0, "lvl": 1.0, "pan": 0.5, "wid": 1.0,
            "bus": 2, "ft": 0, "cu": 8000.0, "rs": 0.7,
            "dt": 0, "dd": 4.0, "dm": 1.0}


USER_BASE = 1024         # AMY-User-Patches: 1024 + Kanal = DX7 von SD
ENCF_DEFAULT = ("SCREEN", "SCREEN", "SCREEN", "SCREEN",
                "master", "lvl", "rvL", "ecL",
                "pk1", "pk2", "pk3", "pk4",
                "pk5", "pk6", "pk7", "pk8")


def new_encx():
    # v13.24: pl = Patch-Liste, ld = Laden (0 SOFORT, 1 AUF DRUCK),
    # led = LED-Farbe (0 AUTO, 1 AUS, 2.. feste Farbe)
    return {"pl": 0, "ld": 0, "led": 0}


def default_state():
    s = {
        "v": 12, "n": 0,
        # Kanaele (Index 0 unbenutzt, 1-16 = MIDI-Kanal)
        "pat": [-1] * 17, "vo": [1] * 17, "bus": [0] * 17,
        "lvl": [1.0] * 17, "pan": [0.5] * 17, "mute": [0] * 17,
        "chord": [0] * 17, "porta": [0] * 17,
        "ccmap": [[] for _ in range(17)],
        # Klangformung pro Kanal; "tch" = welche Gruppen der Nutzer
        # veraendert hat (sonst gelten die Patch-eigenen Werte)
        "tch": [0] * 17,
        # Effekte pro Bus 0-3
        "fx": [{"rv": [0.0, 0.5, 0.5, 1000.0],       # level, live, damp, xover
                "cho": [0.0, 0.5, 0.5, CHORUS_MAX_DELAY],  # level, rate, depth, delay
                "ech": [0.0, 250, 0.35, 0.0],           # level, ms, feedback, filter
                "eq": [0.0, 0.0, 0.0], "prof": 1,
                # pfx = 1: Chorus und EQ bestimmt der geladene Patch
                # (Juno-Patches bringen ihren Chorus + HPF-EQ mit)
                "pfx": 0 if b == 1 else 1,
                # v13.16 Distortion: Typ (0 AUS, 1 CLIP, 2 FOLD, 3 BEIDE),
                # Drive, Mix
                "dst": [0, 4.0, 1.0]} for b in range(4)],
        "master": 1.0, "crush": 0, "crate": 0, "audio": 0,
        "cur": 1, "thru": 0, "mtype": 0, "inv": 0,
        "encf": list(ENCF_DEFAULT),
        "macro": ["cut", "res", "rvL", "lvl"],
        # Eurorack
        "eur": 0, "qscale": 1, "cvsrc": [0, 0], "lfo": [0, 0.5, 0.5],
        # v13.20 Wavefolder: LFO [Typ, Drive, Mix, Mod-Quelle, Mod-Tiefe],
        # ENV [Typ, Drive, Mix]
        "lfof": [0, 4.0, 1.0, 0, 0.5], "envf": [0, 4.0, 1.0],
        "env": [10, 300, 0.5], "cal": [[0.0, 1.0], [0.0, 1.0]],
        "calin": [[0.0, 1.0], [0.0, 1.0]],
        # Sequencer
        "tempo": 108, "run": 0, "clock": 0, "swing": 0, "sel": 0,
        "trk": [new_track(1, 60), new_track(2, 60), new_track(3, 60),
                new_track(DRUM_CHANNEL, 36)],
        "acid": {"steps": 16, "mute": 0, "out": 0, "mch": 1, "pat": 0,
                 "pats": [deep_copy(ACID_DEFAULT_PATTERN) for _ in range(NUM_PATTERNS)],
                 "wave": 0, "cut": 400.0, "reso": 3.0, "env": 3.0, "dec": 300,
                 "acc": 0.6, "tune": 0, "lvl": 0.6, "slide": 60, "root": 36,
                 "cvacc": 0,
                 # v12.15: Joystick > 303 (an/aus, Ziel X, Ziel Y, Tiefe %)
                 "joy": 0, "jx": 1, "jy": 3, "jd": 100,
                 # v13.16: Distortion Typ / Drive / Mix
                 "dt": 0, "dd": 4.0, "dm": 1.0},
        "drm": new_drums(),
        # Extras / System
        "sb": new_sampler(), "notlauf": 1, "transport": 0,
        "m5": 0, "fail": 4, "vbud": 24, "dim": 5, "bright": 255,
        # v13.19: DX7 von SD je Kanal [Datei, Stimme, Name] oder None;
        # Taster der Zusatz-Encoder
        "syx": [None] * 17, "encb": list(ENCB_DEFAULT),
        # v13.24: Encoder-Optionen, aktives Set, gespeicherte Sets A/B/C
        "encx": [new_encx() for _ in range(16)], "eset": 0, "esets": [None, None, None],
        "fav": [], "rec": [], "mA": 0, "mB": 1, "mx": 0.0, "cct": 0,
        # v12.11: UI-Takt 1 = Timer, 0 = loop(); Display 1 = Baender
        "uit": 1, "dfast": 1,
        # v12.12: Sequencer-Ausgabe 1 = VORAUS (ticks=), 0 = DIREKT; Vorlauf ms
        "sqm": 1, "vlf": 250,
        # v13.21: VCO
        "vco": new_vco(),
        # v13.22: AUDIO IN
        "ain": new_ain(),
        # v13.29: LEDs
        "led": new_led(),
        # v13.30: Bildschirmschoner
        "sv": new_sv(),
    }
    for k, v in TONE_DEF:
        s[k] = [v] * 17
    # Werk: Kanal 1 Juno, Kanal 10 Drums auf eigenem, trockenem Bus
    s["pat"][1] = 0
    s["vo"][1] = 4
    s["pat"][10] = DRUM_PATCH
    s["bus"][10] = 1
    s["fx"][0]["rv"][0] = 0.12
    s["fx"][1]["prof"] = 3
    s["fx"][1]["eq"] = list(PROFILES[3][1])
    # Drum-Spur Pattern A: Grundbeat (v12.6 - vorher Viertel-Bassdrum
    # auf Spur 4; Spur 4 bleibt ab Werk leer)
    a = s["drm"]["pats"][0]
    for k in range(len(DRUM_START)):
        a[k] = DRUM_START[k] + "0" * (SEQ_MAX_STEPS - len(DRUM_START[k]))
    return s


S = default_state()


# ---------------------------------------------------------------
# Zusammenfuehren geladener Daten mit den Werkswerten
# ---------------------------------------------------------------

def _merge(d, src):
    if isinstance(d, dict):
        if not isinstance(src, dict):
            return d
        for k in d:
            if k in src:
                d[k] = _merge(d[k], src[k])
        return d
    if isinstance(d, list):
        if not isinstance(src, list):
            return d
        if len(d) == len(src):
            return [_merge(d[i], src[i]) for i in range(len(d))]
        if len(d) == 0 or not isinstance(d[0], (list, dict)):
            return src
        return d
    if isinstance(d, float):
        try:
            return float(src)
        except Exception:
            return d
    if isinstance(d, int):
        try:
            return int(src)
        except Exception:
            return d
    if isinstance(d, str):
        return src if isinstance(src, str) else d
    return src


def _sanitize_drums():
    d = S["drm"]
    dd = new_drums()
    for k in ("lens", "notes", "mutes", "smp", "sli"):
        if not isinstance(d[k], list) or len(d[k]) != DRUM_ROWS:
            d[k] = dd[k]
    d["smp"] = [clamp_int(v, -1, SMP_SLOTS - 1) for v in d["smp"]]
    d["sli"] = [clamp_int(v, 0, 16) for v in d["sli"]]
    d["ch"] = clamp_int(d["ch"], 1, 16)
    d["mch"] = clamp_int(d["mch"], 1, 16)
    d["div"] %= 4
    d["out"] = clamp_int(d["out"], 0, 2)
    d["pat"] %= NUM_PATTERNS
    d["mute"] = 1 if d["mute"] else 0
    if not isinstance(d["gd"], list) or len(d["gd"]) != DRUM_ROWS:
        d["gd"] = dd["gd"]
    if not isinstance(d["trg"], list) or len(d["trg"]) != 2:
        d["trg"] = dd["trg"]
    d["trg"] = [clamp_int(v, -1, DRUM_ROWS - 1) for v in d["trg"]]
    d["tlen"] = clamp_int(d["tlen"], 1, 8)
    d["tlv"] %= 3
    d["gm"] %= 2
    d["gx"] = clamp(d["gx"], 0.0, 1.0)
    d["gy"] = clamp(d["gy"], 0.0, 1.0)
    d["gz"] = clamp_int(d["gz"], 0, 15)
    d["gd"] = [clamp_int(v, 0, 15) for v in d["gd"]]
    d["gcv"] = 1 if d["gcv"] else 0
    d["gj"] = 1 if d["gj"] else 0
    for k in range(DRUM_ROWS):
        d["lens"][k] = clamp_int(d["lens"][k], 1, SEQ_MAX_STEPS)
        d["notes"][k] = clamp_int(d["notes"][k], 0, 127)
        d["mutes"][k] = 1 if d["mutes"][k] else 0
    for pat in d["pats"]:
        for k in range(DRUM_ROWS):
            pat[k] = _hex_row(pat[k])


def sanitize():
    # Grenzen erzwingen - nach Laden, Migration und Szenen-Abruf.
    if not isinstance(S.get("syx"), list) or len(S["syx"]) != 17:
        S["syx"] = [None] * 17
    for ch in range(17):
        p = S["pat"][ch]
        if p == 258:
            p = 384
        if p != -1 and p not in PATCH_POS:
            e = S["syx"][ch]
            if not (p == USER_BASE + ch and isinstance(e, list) and len(e) == 3):
                p = 0
        if p != USER_BASE + ch:
            S["syx"][ch] = None
        S["pat"][ch] = p
        S["vo"][ch] = clamp_int(S["vo"][ch], 1, 8)
        S["bus"][ch] = clamp_int(S["bus"][ch], 0, 3)
        S["lvl"][ch] = clamp(S["lvl"][ch], 0.0, 2.0)
        S["pan"][ch] = clamp(S["pan"][ch], 0.0, 1.0)
        S["mute"][ch] = 1 if S["mute"][ch] else 0
        if not (0 <= S["chord"][ch] < len(CHORD_NAMES)) or is_drum(p):
            S["chord"][ch] = 0
        S["porta"][ch] = clamp_int(S["porta"][ch], 0, 2000)
        maps = []
        for m in S["ccmap"][ch]:
            try:
                if 0 <= m[0] <= 127 and 0 <= m[1] < len(CC_TARGETS):
                    maps.append([int(m[0]), int(m[1])])
            except Exception:
                pass
        S["ccmap"][ch] = maps[-4:]
    S["cur"] = clamp_int(S["cur"], 1, 16)
    if S["eur"] not in EUR_MODE_VALUES:
        S["eur"] = 0
    S["qscale"] %= len(SCALES)
    S["tempo"] = clamp_int(S["tempo"], 20, 300)
    S["swing"] = clamp_int(S["swing"], 0, 100)
    S["clock"] %= 3
    S["sel"] %= 6
    for t in S["trk"]:
        t["ch"] = clamp_int(t["ch"], 1, 16)
        t["steps"] = clamp_int(t["steps"], 1, SEQ_MAX_STEPS)
        t["div"] %= 4
        t["mode"] %= len(SEQ_MODES)
        t["note"] = clamp_int(t["note"], 0, 127)
        t["gate"] = clamp_int(t["gate"], 1, 48)
        t["pul"] = clamp_int(t["pul"], 0, t["steps"])
        t["scale"] %= len(SCALES)
        t["out"] = clamp_int(t["out"], 0, 2)
        t["mch"] = clamp_int(t["mch"], 1, 16)
        t["pat"] %= NUM_PATTERNS
        t["adir"] %= 4
        t["aoct"] = clamp_int(t["aoct"], 1, 3)
        t["ain"] = clamp_int(t["ain"], 1, 16)
        for pat in t["pats"]:
            for i in range(SEQ_MAX_STEPS):
                pat[i] = clamp_int(pat[i], 0, 4)
    a = S["acid"]
    a["steps"] = clamp_int(a["steps"], 1, ACID_STEPS_MAX)
    a["pat"] %= NUM_PATTERNS
    a["out"] = clamp_int(a["out"], 0, 2)
    a["mch"] = clamp_int(a["mch"], 1, 16)
    a["cut"] = clamp(a["cut"], ACID_CUT_MIN, ACID_CUT_MAX)
    a["reso"] = clamp(a["reso"], 0.5, 8.0)
    a["env"] = clamp(a["env"], 0.0, 7.0)
    a["dec"] = clamp_int(a["dec"], 30, 2500)
    a["acc"] = clamp(a["acc"], 0.0, 1.0)
    a["tune"] = clamp_int(a["tune"], -12, 12)
    a["joy"] = 1 if a["joy"] else 0
    a["jx"] %= len(ACID_JOY_TARGETS)
    a["jy"] %= len(ACID_JOY_TARGETS)
    a["jd"] = clamp_int(a["jd"], 10, 100)
    a["dt"] %= len(DIST_TYPES)
    a["dd"] = clamp(a["dd"], DIST_DRIVE_MIN, DIST_DRIVE_MAX)
    a["dm"] = clamp(a["dm"], 0.0, 1.0)
    a["lvl"] = clamp(a["lvl"], 0.0, 1.5)
    a["slide"] = clamp_int(a["slide"], 10, 500)
    a["root"] = clamp_int(a["root"], 24, 72)
    for pat in a["pats"]:
        for st in pat:
            st[0] = clamp_int(st[0], -1, 12)
            st[1] = clamp_int(st[1], -1, 1)
            st[2] = 1 if st[2] else 0
            st[3] = 1 if st[3] else 0
    _sanitize_drums()
    for b in range(4):
        f = S["fx"][b]
        f["cho"][3] = clamp(f["cho"][3], 50.0, CHORUS_MAX_DELAY)
        f["ech"][1] = clamp_int(f["ech"][1], 10, ECHO_MAX_DELAY_MS)
        f["prof"] %= len(PROFILES)
        f["pfx"] = 1 if f["pfx"] else 0
        ds = f["dst"]
        ds[0] = clamp_int(ds[0], 0, len(DIST_TYPES) - 1)
        ds[1] = clamp(ds[1], DIST_DRIVE_MIN, DIST_DRIVE_MAX)
        ds[2] = clamp(ds[2], 0.0, 1.0)
    S["crush"] %= len(CRUSH_BITS)
    S["crate"] %= len(CRUSH_RATES)
    S["fail"] %= len(FAILSAFE_VALUES)
    S["vbud"] = clamp_int(S["vbud"], 8, 64)
    S["mA"] %= 8
    S["mB"] %= 8
    S["mx"] = clamp(S["mx"], 0.0, 1.0)
    S["fav"] = [p for p in S["fav"] if p in PATCH_POS][:32]
    S["rec"] = [p for p in S["rec"] if p in PATCH_POS][:8]
    # Staende vor v13.15 haben 8 Eintraege: Q1-Q8 mit Werkswerten ergaenzen
    while len(S["encf"]) < ENC_SLOTS:
        S["encf"].append(ENCF_DEFAULT[len(S["encf"])])
    S["encf"] = S["encf"][:ENC_SLOTS]
    while len(S["encb"]) < ENC_SLOTS:
        S["encb"].append(ENCB_DEFAULT[len(S["encb"])])
    S["encb"] = [b if b in ENCB_KEYS else "AUS" for b in S["encb"][:ENC_SLOTS]]
    S["encf"] = [f if f in ENC_KEYS else "AUS" for f in S["encf"]]
    S["encx"] = _sanitize_encx(S["encx"])
    S["eset"] = clamp_int(S["eset"], 0, 2)
    if not isinstance(S["esets"], list) or len(S["esets"]) != 3:
        S["esets"] = [None, None, None]
    for i in range(3):
        e = S["esets"][i]
        try:
            S["esets"][i] = {
                "f": [f if f in ENC_KEYS else "AUS" for f in e["f"]][:ENC_SLOTS],
                "b": [b if b in ENCB_KEYS else "AUS" for b in e["b"]][:ENC_SLOTS],
                "x": _sanitize_encx(e["x"])}
            if len(S["esets"][i]["f"]) != ENC_SLOTS or len(S["esets"][i]["b"]) != ENC_SLOTS:
                S["esets"][i] = None
        except Exception:
            S["esets"][i] = None
    S["uit"] = 1 if S["uit"] else 0
    S["dfast"] = 1 if S["dfast"] else 0
    S["sqm"] = 1 if S["sqm"] else 0
    S["vlf"] = clamp_int(S["vlf"], 50, 400)
    for key in ("lfof", "envf"):
        ff = S[key]
        ff[0] = clamp_int(ff[0], 0, len(DIST_TYPES) - 1)
        ff[1] = clamp(ff[1], DIST_DRIVE_MIN, DIST_DRIVE_MAX)
        ff[2] = clamp(ff[2], 0.0, 1.0)
    S["lfof"][3] = clamp_int(S["lfof"][3], 0, 2)
    S["lfof"][4] = clamp(S["lfof"][4], 0.0, 1.0)
    for key, lo, hi in (("cal", 0.9, 1.1), ("calin", 0.8, 1.25)):
        if not isinstance(S[key], list) or len(S[key]) != 2:
            S[key] = [[0.0, 1.0], [0.0, 1.0]]
        for c in S[key]:
            c[0] = clamp(c[0], -1.0, 1.0)
            c[1] = clamp(c[1], lo, hi)
    _sanitize_vco()
    _sanitize_led()
    _sanitize_sv()
    _sanitize_ain()
    _sanitize_sampler()


def _sanitize_encx(lst):
    out = []
    for i in range(ENC_SLOTS):
        try:
            x = lst[i]
            out.append({"pl": clamp_int(x["pl"], 0, len(PL_NAMES) - 1),
                        "ld": 1 if x["ld"] else 0,
                        "led": clamp_int(x["led"], 0, len(LED_NAMES) - 1)})
        except Exception:
            out.append(new_encx())
    return out


def _sanitize_sv():
    x = S["sv"]
    x["bild"] = clamp_int(x["bild"], 0, 9)
    x["pool"] = clamp_int(x["pool"], 0, 255)
    x["wz"] = clamp_int(x["wz"], 0, 3)
    x["lz"] = clamp_int(x["lz"], 0, 2)
    x["hl"] = clamp_int(x["hl"], 0, 2)
    if not isinstance(x["fly"], str):
        x["fly"] = "DOLPHIN"
    x["fly"] = x["fly"][:10]


def _sanitize_led():
    x = S["led"]
    x["hl"] = clamp_int(x["hl"], 0, 3)
    for k in ("nav", "ed", "bt", "pn", "wn"):
        x[k] = clamp_int(x[k], 0, 9)
    for k in ("cf", "st", "fl", "sv"):
        x[k] = 1 if x[k] else 0


def _sanitize_ain():
    a = S["ain"]
    a["on"] = 1 if a["on"] else 0
    a["mode"] %= len(AIN_MODE_NAMES)
    a["gain"] = clamp(a["gain"], AIN_GAIN_MIN, AIN_GAIN_MAX)
    a["lvl"] = clamp(a["lvl"], 0.0, 1.5)
    a["pan"] = clamp(a["pan"], 0.0, 1.0)
    a["wid"] = clamp(a["wid"], 0.0, 1.0)
    a["bus"] = clamp_int(a["bus"], 0, 3)
    a["ft"] %= len(SMP_FILT_NAMES)
    a["cu"] = clamp(a["cu"], 40.0, 16000.0)
    a["rs"] = clamp(a["rs"], 0.5, 16.0)
    a["dt"] = clamp_int(a["dt"], 0, len(DIST_TYPES) - 1)
    a["dd"] = clamp(a["dd"], DIST_DRIVE_MIN, DIST_DRIVE_MAX)
    a["dm"] = clamp(a["dm"], 0.0, 1.0)


def _sanitize_vco():
    v = S["vco"]
    v["on"] = 1 if v["on"] else 0
    v["src"] = clamp_int(v["src"], 0, 2)
    v["wav"] %= len(VCO_WAVE_NAMES)
    v["root"] = clamp_int(v["root"], 12, 96)
    v["fine"] = clamp_int(v["fine"], -100, 100)
    v["trk"] = clamp(v["trk"], 0.95, 1.05)
    v["pw"] = clamp(v["pw"], 0.05, 0.95)
    v["sub"] = clamp(v["sub"], 0.0, 1.0)
    v["so"] = clamp_int(v["so"], 1, 2)
    v["o2"] = clamp(v["o2"], 0.0, 1.0)
    v["iv"] = clamp_int(v["iv"], -24, 24)
    v["det"] = clamp_int(v["det"], 0, 50)
    v["pm"] = 1 if v["pm"] else 0
    v["sc"] %= len(SCALES)
    v["msrc"] = clamp_int(v["msrc"], 0, 2)
    v["mt"] %= len(VCO_MOD_NAMES)
    v["md"] = clamp(v["md"], 0.0, 1.0)
    v["ft"] = clamp_int(v["ft"], 0, len(DIST_TYPES) - 1)
    v["fd"] = clamp(v["fd"], DIST_DRIVE_MIN, DIST_DRIVE_MAX)
    v["fm"] = clamp(v["fm"], 0.0, 1.0)
    v["lvl"] = clamp(v["lvl"], 0.0, 1.5)
    v["pan"] = clamp(v["pan"], 0.0, 1.0)
    v["bus"] = clamp_int(v["bus"], 0, 3)
    v["sm"] = clamp_int(v["sm"], 0, 2)


def _sanitize_sampler():
    b = S["sb"]
    if not isinstance(b.get("sl"), list) or len(b["sl"]) != SMP_SLOTS:
        b["sl"] = [new_slot() for _ in range(SMP_SLOTS)]
    for sl in b["sl"]:
        if not isinstance(sl.get("f"), str):
            sl["f"] = ""
        for key in ("st", "en", "ls", "le"):
            sl[key] = max(0, int(sl[key]))
        sl["pm"] %= len(SMP_MODE_NAMES)
        sl["tu"] = clamp_int(sl["tu"], -24, 24)
        sl["fi"] = clamp_int(sl["fi"], -50, 50)
        sl["rt"] = clamp_int(sl["rt"], 24, 96)
        sl["lv"] = clamp(sl["lv"], 0.0, 1.5)
        sl["pan"] = clamp(sl["pan"], 0.0, 1.0)
        sl["bus"] = clamp_int(sl["bus"], 0, 3)
        for key in ("at", "de", "re"):
            sl[key] = clamp_int(sl[key], 0, 5000)
        sl["su"] = clamp(sl["su"], 0.0, 1.0)
        sl["ft"] %= len(SMP_FILT_NAMES)
        sl["cu"] = clamp(sl["cu"], 40.0, 16000.0)
        sl["rs"] = clamp(sl["rs"], 0.5, 16.0)
        sl["fe"] = clamp(sl["fe"], -6.0, 6.0)
        sl["fd"] = clamp_int(sl["fd"], 10, 5000)
        if sl["sy"] not in SYNC_BEATS:
            sl["sy"] = 0
        sl["fs"] = clamp_int(sl["fs"], 0, 512)
        if sl["nc"] not in SLICE_COUNTS:
            sl["nc"] = 0
    for key, hi in (("ch", 16), ("pch", 16), ("cs", SMP_SLOTS - 1), ("rs", SMP_SLOTS - 1)):
        b[key] = clamp_int(b[key], 0, hi)
    b["cv"] = clamp_int(b["cv"], 1, 8)
    b["src"] %= len(SMP_SRC_NAMES)
    b["len"] = clamp_int(b["len"], 1, 10)
    b["unit"] %= len(SMP_REC_UNITS)
    b["rst"] %= len(SMP_REC_STARTS)
    b["asv"] = 1 if b["asv"] else 0
    b["ss"] = clamp_int(b["ss"], 0, SMP_SLOTS - 1)


# ---------------------------------------------------------------
# Speichern (entprellt, nur bei Aenderung)
# ---------------------------------------------------------------

_last_saved = None
_save_due = None
_save_first = None
SAVE_DELAY_MS = 2500
SAVE_MAX_MS = 10000      # spaetestens 10 s nach der ersten Aenderung


def request_save():
    # Entprellt, aber nie endlos verschoben: auch bei Dauer-Aenderungen
    # wird spaetestens SAVE_MAX_MS nach der ersten Aenderung gespeichert.
    global _save_due, _save_first
    t = now()
    if _save_first is None:
        _save_first = t
    due = time.ticks_add(t, SAVE_DELAY_MS)
    hard = time.ticks_add(_save_first, SAVE_MAX_MS)
    if time.ticks_diff(due, hard) > 0:
        due = hard
    _save_due = due


def _replace(src, dst):
    try:
        os.rename(src, dst)
    except OSError:
        try:
            os.remove(dst)
        except OSError:
            pass
        os.rename(src, dst)


_save_err = ""


def _save_failed(stage, e):
    global _save_err
    _save_err = ("%s %s" % (stage, e))[:40]
    print("SAVE FEHLER", stage, repr(e), "->", STATE_FILE)
    try:
        toast("SPEICH." + stage, (BASE + " " + str(e))[:14], 3000)
    except Exception:
        pass


WRITE_CHUNK = 512


def _write_file(path, txt):
    # In kleinen Stuecken schreiben: grosse Einzel-Writes loesen auf
    # manchen Karten/Flash-Treibern EIO aus.
    gc.collect()
    data = txt.encode()
    f = open(path, "wb")
    try:
        for i in range(0, len(data), WRITE_CHUNK):
            f.write(data[i:i + WRITE_CHUNK])
        try:
            f.flush()
        except Exception:
            pass
    finally:
        f.close()


def _write_direct(txt):
    try:
        _write_file(STATE_FILE, txt)
    except OSError:
        time.sleep_ms(50)
        _write_file(STATE_FILE, txt)     # ein zweiter Versuch


def _write_safe(txt):
    # "" bei Erfolg, sonst der Schritt, der gescheitert ist.
    step = "TMP"
    try:
        _write_file(STATE_TMP, txt)
        step = "BAK"
        try:
            os.stat(STATE_FILE)
            have_old = True
        except OSError:
            have_old = False
        if have_old:
            _replace(STATE_FILE, STATE_BAK)
        step = "MOVE"
        _replace(STATE_TMP, STATE_FILE)
        return ""
    except Exception as e:
        print("SAVE SICHER", step, repr(e))
        return step


def _set_base(d):
    global BASE, STATE_FILE, SCENE_FILE, STATE_TMP, STATE_BAK
    BASE = d
    STATE_FILE = d + "dolphin_state.json"
    SCENE_FILE = d + "dolphin_scenes.json"
    STATE_TMP = STATE_FILE + ".tmp"
    STATE_BAK = STATE_FILE + ".bak"


# ---------------------------------------------------------------
# SD-Karte neu einbinden (SETUP > SD NEU EINBINDEN)
# ---------------------------------------------------------------
# amyboard.mount_sd() bindet die Karte nur beim Start ein und verschluckt
# Fehler. Wird die Karte im Betrieb getauscht, bleibt /sd an der alten
# haengen. Hier: aushaengen, selbst neu einhaengen (Pins wie in
# amyboard.py), Schreibtest, dann den Stand sofort auf die Karte legen.

_ERRNO_TXT = {1: "BELEGT", 2: "FEHLT", 5: "E/A-FEHLER", 19: "KEIN FAT32",
              110: "KEINE ANTWORT", 116: "KEINE ANTWORT", 12: "SPEICHER"}
sd_status = _sd_boot if BASE == "/sd/" else "NICHT AKTIV"   # SETUP > INFO > SD
sd_switch_err = ""       # warum zuletzt von /sd/ weggewechselt wurde


def sd_free_kb():
    try:
        v = os.statvfs("/sd")
        return v[0] * v[3] // 1024
    except Exception:
        return -1


def _err_txt(e):
    try:
        n = e.args[0]
        if isinstance(n, int):
            return _ERRNO_TXT.get(n, "FEHLER %d" % n)
    except Exception:
        pass
    return str(e)[:12] or "FEHLER"


STATE_NAMES = ("dolphin_state.json", "dolphin_state.json.tmp",
               "dolphin_state.json.bak", ".dolphin_probe")


def sd_remount(clean=False):
    # -> (ok, text fuer die Anzeige). clean=True (SD ZUSTAND NEU): vorher
    # die Zustandsdateien auf der Karte loeschen - eine beschaedigte
    # dolphin_state.json laesst sonst jedes Speichern scheitern.
    global sd_status
    err = _sd_mount_fresh(sd_freq, sd_pull)
    try:
        os.listdir("/sd")
    except Exception as e:
        sd_status = _err_txt(err or e)
        return False, sd_status
    if clean:
        for n in STATE_NAMES:
            try:
                os.remove("/sd/" + n)
                print("GELOESCHT /sd/" + n)
            except OSError as e:
                if e.args and e.args[0] != 2:      # 2 = gibt es nicht
                    sd_status = "LOESCHEN " + _err_txt(e)
                    return False, ("LOESCHEN " + _err_txt(e))[:14]
    # Takt suchen: erst der aktuelle, dann von schnell nach langsam,
    # bis 32 KB sicher geschrieben und gelesen werden
    good = _dir_writable("/sd/", 32)
    if not good:
        cfg = sd_find_cfg()
        good = cfg is not None
    if not good:
        sd_status = "NICHT BESCHR."
        return False, "SCHREIBFEHLER"
    _set_base("/sd/")
    ok = save_state(force=True)
    if BASE != "/sd/":
        # Testdatei ging, der Zustand liess sich aber nicht schreiben ->
        # save_state ist auf /user/ ausgewichen. Ehrlich melden.
        return False, (sd_switch_err or "SPEICH.FEHLER")[:14]
    try:
        scenes_save()
    except Exception:
        pass
    sd_status = "OK" if ok else "SPEICH.FEHLER"
    if ok and (sd_freq or sd_pull):
        return ok, "OK " + _sd_cfg_txt(sd_freq, sd_pull)
    return ok, "GESPEICHERT" if ok else sd_status


def _sd_cfgs():
    out = [(0, False)]
    for p in (False, True):
        for f in SD_FREQS:
            out.append((f, p))
    out.append((0, True))
    return out


def sd_find_cfg(matrix=None):
    # Alle Einstellungen (Takt x Pull-up) durchprobieren, bis 32 KB sicher
    # geschrieben und gelesen werden. Die erste (schnellste) passende wird
    # gemerkt. matrix: Liste, in die jedes Ergebnis eingetragen wird.
    found = None
    for f, p in _sd_cfgs():
        e = _sd_mount_fresh(f, p)
        if e is not None:
            r = "MOUNT " + _err_txt(e)[:5]
        else:
            time.sleep_ms(20)
            r = "OK" if _dir_writable("/sd/", 32) else "E5"
        if matrix is not None:
            matrix.append((_sd_cfg_txt(f, p), r))
        if r == "OK" and found is None:
            found = (f, p)
            if matrix is None:
                break
    if found is not None:
        _sd_mount_fresh(found[0], found[1])
        time.sleep_ms(20)
        _sd_freq_save(found[0], found[1])
    else:
        _sd_mount_fresh(0, False)
    return found


def _next_store():
    # Wechselt auf den naechsten beschreibbaren Ort nach BASE.
    try:
        i = STORE_DIRS.index(BASE) + 1
    except ValueError:
        i = 0
    while i < len(STORE_DIRS):
        d = STORE_DIRS[i]
        i += 1
        if _dir_writable(d):
            print("SPEICHERORT GEWECHSELT", BASE, "->", d)
            _set_base(d)
            try:
                toast("SD-FEHLER", "SPEICHERE " + d[:6], 2500)
            except Exception:
                pass
            return True
    return False


def save_state(force=False):
    # Erst sicher (.tmp -> Hauptdatei, alte -> .bak). Klappt das auf
    # diesem Dateisystem nicht, direkt schreiben wie in v12.0.
    global _last_saved, _save_due, _save_first, _save_err, sd_switch_err, sd_status
    _save_due = None
    _save_first = None
    try:
        eset_snapshot()          # v13.24: aktives Encoder-Set mitspeichern
    except Exception:
        pass
    try:
        txt = json.dumps(S)
    except Exception as e:
        _save_failed("JSON", e)
        return False
    if txt == _last_saved and not force:
        return True
    S["n"] = S.get("n", 0) + 1
    txt = json.dumps(S)       # mit neuem Zaehler - wird nach Erfolg _last_saved
    ok = False
    err = None
    while True:
        step = _write_safe(txt)
        if not step:
            ok = True
            print("GESPEICHERT", len(txt), "Bytes ->", STATE_FILE)
            break
        try:
            _write_direct(txt)
            ok = True
            print("GESPEICHERT direkt (sicher scheiterte bei %s)" % step)
            break
        except Exception as e:
            err = (step + "+DIR", e)
        if BASE == "/sd/":
            # v13.4: Grund merken - sonst sieht man nur, dass der
            # Speicherort still nach /user/ gewechselt ist
            sd_switch_err = ("%s %s" % (err[0], _err_txt(err[1])))[:24]
            sd_status = "WECHSEL"
            print("SD SPEICHERN SCHEITERT:", err[0], repr(err[1]))
        # Ort defekt (z.B. EIO auf der SD) -> naechsten Ort versuchen
        if not _next_store():
            break
    if not ok:
        _save_failed(err[0], err[1])
        return False
    _save_err = ""
    if BASE == "/sd/":
        sd_switch_err = ""
    _last_saved = txt
    return True


SAVE_RUN_MAX_MS = 300000  # waehrend der Wiedergabe spaetestens nach 5 min


def service_save():
    # Waehrend der Wiedergabe warten (JSON + SD-Zugriff blockieren den
    # Takt) - STOP speichert sofort, sonst spaetestens nach 60 s.
    if _save_due is None or time.ticks_diff(now(), _save_due) < 0:
        return
    if S["run"] and _save_first is not None and since(_save_first) < SAVE_RUN_MAX_MS:
        return
    t0 = time.ticks_us()
    save_state()
    meas("save", t0)


def _read_kv(path):
    try:
        f = open(path, "r")
    except Exception:
        return None
    vals = {}
    try:
        for line in f:
            line = line.strip()
            if line and ":" in line:
                k, _, v = line.partition(":")
                vals[k] = v
    except Exception:
        pass
    try:
        f.close()
    except Exception:
        pass
    return vals


def _ints(s, n=None):
    try:
        r = [int(float(x)) for x in s.split(",")]
    except Exception:
        return None
    if n is not None and len(r) != n:
        return None
    return r


def _floats(s, n=None):
    try:
        r = [float(x) for x in s.split(",")]
    except Exception:
        return None
    if n is not None and len(r) != n:
        return None
    return r


# Alte Encoder-Funktions-IDs (v8-v11) -> neue Parameter-Schluessel
_OLD_ENC = {0: "AUS", 1: "master", 2: "lvl", 3: "cut", 4: "res", 5: "pan",
            6: "att", 7: "dec", 8: "sus", 9: "rel", 10: "rvL", 11: "chL",
            12: "ecL", 13: "eqL", 14: "eqM", 15: "eqH", 16: "tempo",
            17: "SCREEN", 18: "rvV", 19: "rvD", 20: "rvX", 21: "chR",
            22: "chD", 23: "chM", 24: "ecT", 25: "ecF", 26: "ecC",
            27: "porta", 28: "acut", 29: "ares", 30: "aenv", 31: "adec",
            32: "aacc"}


def migrate_v11():
    # Uebernimmt amyboard_state.txt (+ _extras.txt) von v11. Die alten
    # Dateien bleiben unangetastet. -> True, wenn etwas gefunden wurde.
    v = None
    ex = None
    for base in ("/sd/", "/user/current/"):
        v = _read_kv(base + "amyboard_state.txt")
        if v is not None:
            ex = _read_kv(base + "amyboard_state_extras.txt") or {}
            break
    if v is None:
        return False
    print("MIGRATION v11")
    for key, dst in (("channel_patch", "pat"), ("channel_voices", "vo"),
                     ("channel_bus", "bus"), ("channel_chord", "chord")):
        r = _ints(v.get(key, ""), 17)
        if r:
            S[dst] = r
    for key, dst in (("channel_level", "lvl"), ("channel_pan", "pan")):
        r = _floats(v.get(key, ""), 17)
        if r:
            S[dst] = r
    dxp = _floats(v.get("channel_dx_pan", ""), 17)
    if dxp:
        for ch in range(17):
            if family(S["pat"][ch]) == "DX7":
                S["pan"][ch] = dxp[ch]
    for key, dst in (("eurorack_mode", "eur"), ("eurorack_quantize_scale", "qscale"),
                     ("audio_mode", "audio"), ("current_channel", "cur"),
                     ("encoder_invert", "inv"), ("midi_thru", "thru")):
        r = _ints(v.get(key, ""), 1)
        if r:
            S[dst] = r[0]
    r = _ints(v.get("encoder_function", ""), 8)
    if r:
        S["encf"] = [_OLD_ENC.get(x, "AUS") for x in r]
    r = _floats(v.get("fx_values", ""), 16)
    if r:
        f = S["fx"][0]
        f["rv"] = r[0:4]
        f["cho"] = [r[4], r[5], r[6], r[7]]
        f["ech"] = [r[8], int(r[9]), r[10], r[11]]
        f["eq"] = r[12:15]
        f["prof"] = 0 if (r[12] or r[13] or r[14]) else 1
        S["master"] = r[15]
    g = _ints(v.get("seq_global", ""), 4)
    if g:
        S["run"], S["tempo"], S["clock"], S["sel"] = g
    for i in range(4):
        r = _ints(v.get("seq_t%d" % (i + 1), ""), 11)
        t = S["trk"][i]
        if r:
            (t["ch"], t["steps"], t["div"], t["mode"], t["note"], t["gate"],
             t["pul"], t["scale"], t["mute"], t["out"], t["mch"]) = r
        pat = v.get("seq_p%d" % (i + 1), "")
        if len(pat) == SEQ_MAX_STEPS:
            t["pats"][0] = [4 if c == "1" else 0 for c in pat]
    a = S["acid"]
    r = _ints(v.get("acid_i", ""), 10)
    if r:
        (a["steps"], a["mute"], a["out"], a["mch"], a["wave"], a["dec"],
         a["tune"], a["root"], a["slide"], a["cvacc"]) = r
    r = _floats(v.get("acid_f", ""), 5)
    if r:
        a["cut"], a["reso"], a["env"], a["acc"], a["lvl"] = r
    steps = v.get("acid_p", "").split(";")
    if len(steps) == ACID_STEPS_MAX:
        pat = []
        for st in steps:
            try:
                pat.append([int(x) for x in st.split("/")])
            except Exception:
                pat.append([-1, 0, 0, 0])
        a["pats"][0] = pat
    # Extras
    r = _ints(ex.get("midi_type", ""), 1)
    if r:
        S["mtype"] = r[0]
    r = _ints(ex.get("m5_switch", ""), 1)
    if r:
        S["m5"] = r[0]
    r = _ints(ex.get("failsafe", ""), 1)
    if r:
        S["fail"] = r[0]
    r = _ints(ex.get("porta", ""), 17)
    if r:
        S["porta"] = r
    for item in ex.get("ccmap", "").split(";"):
        try:
            ch, cc, t = [int(x) for x in item.split("/")]
            S["ccmap"][ch].append([cc, t])
        except Exception:
            pass
    r = _ints(ex.get("cv_src", ""), 2)
    if r:
        S["cvsrc"] = r
    r = _floats(ex.get("lfo", ""), 3)
    if r:
        S["lfo"] = [int(r[0]), r[1], r[2]]
    r = _floats(ex.get("env", ""), 3)
    if r:
        S["env"] = [int(r[0]), int(r[1]), r[2]]
    r = _ints(ex.get("crush", ""))
    if r:
        S["crush"] = r[0]
        if len(r) > 1:
            S["crate"] = r[1]
    r = _ints(ex.get("takt", ""), 2)
    if r:
        S["notlauf"], S["transport"] = r
    return True


def _load_json(path):
    f = open(path, "r")
    try:
        return json.loads(f.read())
    finally:
        f.close()


def _migrate_pfx(src):
    # Staende vor v12.9 kennen "pfx" nicht. Hat der Nutzer Chorus oder EQ
    # des Busses nie angefasst (Chorus 0, Profil NEUTRAL), bestimmt ab
    # jetzt der Patch; sonst bleiben seine Einstellungen.
    try:
        for b in range(4):
            if "pfx" in src["fx"][b]:
                continue
            f = S["fx"][b]
            f["pfx"] = 1 if (b != 1 and not f["cho"][0] and f["prof"] == 1) else 0
    except Exception as e:
        print("PFX MIGRATION", e)


def load_state():
    global S, _last_saved
    best = None
    best_n = -1
    best_path = None
    for path in [STATE_FILE, STATE_TMP, STATE_BAK] + LEGACY_STATE:
        try:
            data = _load_json(path)
            if not isinstance(data, dict):
                raise ValueError("kein Objekt")
        except Exception as e:
            print("LOAD", path, e)
            continue
        n = data.get("n", 0)
        try:
            n = int(n)
        except Exception:
            n = 0
        print("GEFUNDEN", path, "Stand", n)
        if n > best_n:
            best, best_n, best_path = data, n, path
    if best is not None:
        try:
            S = _merge(default_state(), best)
            _migrate_pfx(best)
            sanitize()
            print("ZUSTAND AUS", best_path)
            if best_path == STATE_FILE:
                _last_saved = json.dumps(S)
                return "json"
            _last_saved = None          # naechstes Speichern schreibt an BASE
            request_save()
            return "backup"
        except Exception as e:
            print("LOAD MERGE", e)
    S = default_state()
    try:
        if migrate_v11():
            sanitize()
            save_state(force=True)
            return "v11"
    except Exception as e:
        print("MIGRATION", e)
        S = default_state()
    sanitize()
    return "neu"


# ================================================================
# KLANG-ENGINE: KANAELE
# ================================================================

# Stimmen ab Werk je Patch-Familie auf Kanal 1 (andere Kanaele: 2).
# CPU laut AMYboard-FAQ: Juno-Stimme ~12 %, DX7 ~8 %, Drum-Schlag ~2 %.
DEFAULT_VOICES = {"JUNO": 4, "DX7": 6, "PIANO": 4, "AMYB": 4}
# synth_flags (amy.h): 1 Noten ueber die MIDI-Notenbefehle (Drumkits),
# 2 Note-Offs ignorieren, 8 keine Noten-Warnungen auf der seriellen
# Schnittstelle (die liegt im Audiopfad - ein Sequencer, der mitten im
# Takt einsteigt, erzeugt sonst viele davon).
DRUM_SYNTH_FLAGS = 1 | 2 | 8
SYNTH_QUIET_FLAGS = 8
DRUM_KIT_OSCS = 42       # Oszillatoren eines Gamma9001-Kits (TR-808: 38)

FILTER_FAM = ("JUNO", "AMYB")
ENV_FAM = ("JUNO", "AMYB")
LFO_FAM = ("JUNO", "AMYB", "DX7")
PITCH_OSCS = {"JUNO": (2, 3, 4), "AMYB": (2, 3), "DX7": (0,)}
LFO_OSC = 1
LFO_DEPTH_OCT = 0.25

T_FILTER = 1
T_ENV = 2
T_LFO = 4
T_DX = 8

_flags_sent = [0] * 17
_configured = set()       # Synths, die AMY schon kennt


def cur():
    return S["cur"]


def cur_patch():
    return S["pat"][S["cur"]]


def cur_family():
    return family(S["pat"][S["cur"]])


def kit_voices():
    # Ein Drumkit ist eine Stimme mit einem Osc pro Drum - gleichzeitige
    # Schlaege gehen trotzdem (patches.h "iv1in42", AMYboard-FAQ).
    return 1


def default_voices(p, ch):
    if is_drum(p):
        return kit_voices()
    return DEFAULT_VOICES.get(family(p), 4) if ch == 1 else 2


def eff_voices(ch):
    # Tatsaechlich an AMY gesendete Stimmen (Akkord braucht mehr).
    p = S["pat"][ch]
    if p == -1:
        return 1
    if is_drum(p):
        return kit_voices()
    need = len(CHORD_INTERVALS[S["chord"][ch]]) + 1
    return max(S["vo"][ch], need)


def voices_total(skip=0):
    n = 0
    for ch in range(1, 17):
        if ch != skip and S["pat"][ch] != -1:
            n += eff_voices(ch)
    return n


def voices_allowed(ch):
    return max(1, S["vbud"] - voices_total(skip=ch))


# ---------------- Klangformung ----------------

def apply_filter(ch):
    if family(S["pat"][ch]) in FILTER_FAM:
        amy.send(synth=ch, osc=0, filter_freq=S["cut"][ch], resonance=S["res"][ch])


def apply_env(ch):
    # bp0 auf osc 0 ist nur bei Juno/AMYB die Lautstaerke
    if family(S["pat"][ch]) in ENV_FAM:
        amy.send(synth=ch, osc=0, bp0="%d,1.0,%d,%.3f,%d,0" % (
            S["att"][ch], S["dec"][ch], S["sus"][ch], S["rel"][ch]))


def apply_lfo(ch):
    fam = family(S["pat"][ch])
    if fam not in LFO_FAM:
        return
    amy.send(synth=ch, osc=LFO_OSC, freq=S["lfr"][ch])
    depth = S["lfd"][ch] * LFO_DEPTH_OCT
    for o in PITCH_OSCS[fam]:
        amy.send(synth=ch, osc=o, freq={"mod0": depth})


def dx_feedback_value(fb):
    return 0.00125 * (2 ** fb)   # wie amy/fm.py


def apply_dx(ch):
    if family(S["pat"][ch]) == "DX7":
        amy.send(synth=ch, osc=0, algorithm=S["alg"][ch])
        amy.send(synth=ch, osc=0, feedback=dx_feedback_value(S["fb"][ch]))


def tone_touch(ch, bit):
    S["tch"][ch] |= bit


def reapply_tone(ch):
    t = S["tch"][ch]
    try:
        if t & T_FILTER:
            apply_filter(ch)
        if t & T_ENV:
            apply_env(ch)
        if t & T_LFO:
            apply_lfo(ch)
        if t & T_DX:
            apply_dx(ch)
    except Exception as e:
        print("TONE", ch, e)


def reset_tone(ch):
    for k, v in TONE_DEF:
        S[k][ch] = v
    S["tch"][ch] = 0


# ---------------- Pegel / Pan ----------------

def apply_level(ch):
    off = (S["pat"][ch] == -1 and not chrom_owns(ch)) or S["mute"][ch]
    lv = 0.0 if off else S["lvl"][ch]
    try:
        amy.send(synth=ch, synth_level=lv)
    except Exception:
        pass


_pan_sent = {}
_pan_time = {}
_pan_pending = {}
PAN_DRUM_MS = 150


def apply_pan(ch, force=False):
    # Juno/DX7: osc 0 ist der Kopf der Kette, sein Pan gilt fuer alle.
    # Drumkit: jeder Drum ist ein eigener Osc - alle setzen (nur bei
    # Aenderung, der Patch startet mittig). Das sind ~40 Befehle, daher
    # hoechstens alle 150 ms; der Rest kommt ueber service_pan().
    p = 0.5 if S["audio"] == 1 else S["pan"][ch]
    try:
        if is_drum(S["pat"][ch]):
            if _pan_sent.get(ch, 0.5) == p:
                _pan_pending.pop(ch, None)
                return
            last = _pan_time.get(ch)
            if not force and last is not None and since(last) < PAN_DRUM_MS:
                _pan_pending[ch] = 1
                return
            n = 38 if S["pat"][ch] == DRUM_PATCH else DRUM_KIT_OSCS
            for o in range(n):
                amy.send(synth=ch, osc=o, pan=p)
            _pan_sent[ch] = p
            _pan_time[ch] = now()
            _pan_pending.pop(ch, None)
        else:
            amy.send(synth=ch, osc=0, pan=p)
    except Exception:
        pass


def service_pan():
    for ch in list(_pan_pending):
        if since(_pan_time.get(ch, 0)) >= PAN_DRUM_MS:
            apply_pan(ch)


def apply_porta(ch):
    try:
        amy.send(synth=ch, portamento=int(S["porta"][ch]))
    except Exception as e:
        print("PORTA", e)


# ---------------- Kanal komplett einrichten ----------------

def configure_channel(ch):
    try:
        if chrom_owns(ch):
            chrom_configure()
            return
    except Exception as e:
        print("CHROM", e)

    real = S["pat"][ch]
    un = real == -1
    patch = 0 if un else real
    voices = 1 if un else S["vo"][ch]

    if ch == DRUM_CHANNEL and not un and not is_drum(patch):
        patch = DRUM_PATCH
        S["pat"][ch] = patch
    drum = is_drum(patch)
    if drum:
        voices = kit_voices()
        S["vo"][ch] = voices
    elif not un:
        voices = eff_voices(ch)

    # Bus zuerst: die Chorus/EQ-Zeile eines Patches landet auf dem Bus
    # seines Synths (patches.c) - der muss beim Laden schon stimmen.
    if ch in _configured:
        amy.send(synth=ch, bus=S["bus"][ch])
    _configured.add(ch)
    if patch > USER_BASE:
        # DX7-Stimme von SD: erst als User-Patch ablegen (v13.19)
        e = S["syx"][ch]
        if not e or _syx_done.get(ch) != (e[0], e[1]):
            if not syx_install(ch):
                patch = S["pat"][ch]
                voices = eff_voices(ch)
    amy.send(synth=ch, patch=patch, num_voices=voices, bus=S["bus"][ch])
    # Flags nach dem Patch: das Kit bringt eigene ("if3") mit
    flags = DRUM_SYNTH_FLAGS if drum else SYNTH_QUIET_FLAGS
    amy.send(synth=ch, synth_flags=flags)
    _flags_sent[ch] = flags
    _pan_sent.pop(ch, None)       # Patch startet mit Pan 0.5

    apply_level(ch)
    apply_pan(ch, True)
    if not un:
        reapply_tone(ch)
        if S["porta"][ch]:
            apply_porta(ch)
        if S["ccmap"][ch]:
            apply_ccmap(ch)
    try:
        eur_after_configure(ch)
    except Exception:
        pass
    if ch == S["sb"]["pch"]:
        # PAD-KANAL: Noten gehen an die Pads, nicht an den Kanal-Synth
        try:
            amy.send(synth=ch, grab_midi_notes=0)
        except Exception:
            pass


# Entprelltes Laden beim Durchblaettern: geladen wird erst, wenn
# der Encoder PATCH_SETTLE_MS ruht.
PATCH_SETTLE_MS = 120
_pending_cfg = {}


def request_configure(ch):
    _pending_cfg[ch] = now()


def flush_configure(force=False):
    if not _pending_cfg:
        return
    t = now()
    done = False
    for ch in list(_pending_cfg):
        if force or time.ticks_diff(t, _pending_cfg[ch]) >= PATCH_SETTLE_MS:
            del _pending_cfg[ch]
            try:
                configure_channel(ch)
            except Exception as e:
                print("CFG", ch, e)
            done = True
    if done:
        try:
            refresh_buses()
        except Exception as e:
            print("BUS", e)


def set_patch(ch, p):
    if p != USER_BASE + ch:
        S["syx"][ch] = None
    # Patch zuweisen (Vorschau), Klangformung gehoert zum neuen Patch.
    if S["pat"][ch] != p:
        reset_tone(ch)
    S["pat"][ch] = p
    if p != -1:
        S["vo"][ch] = clamp_int(default_voices(p, ch), 1, voices_allowed(ch))
    request_configure(ch)


def commit_patch(ch):
    flush_configure(True)
    p = S["pat"][ch]
    if p != -1 and p < USER_BASE:     # SD-Stimmen gehoeren zum Kanal
        rec = [x for x in S["rec"] if x != p]
        rec.insert(0, p)
        S["rec"] = rec[:8]
    request_save()


def toggle_favorite(p):
    if p == -1 or p >= USER_BASE:
        return
    if p in S["fav"]:
        S["fav"].remove(p)
    else:
        S["fav"].append(p)
    request_save()


# ================================================================
# EFFEKTE PRO BUS  (api.md "Per-bus Effects")
# ================================================================

_fx_bus_override = None


def fx_bus():
    if _fx_bus_override is not None:
        return _fx_bus_override
    return S["bus"][S["cur"]]


# ---------------- Distortion (v13.16) ----------------
# AMY (amy#1116/#1134): Waveshaper je Oszillator und je Bus, nach der
# Huellkurve und vor dem Filter. dist_clip / dist_fold schalten die
# Stufen (stapelbar), dist_drive verstaerkt davor, dist_mix blendet
# trocken/verzerrt. dist_crush gehoert zur selben Stufe (CRUSH).
# AUS = beide Stufen aus, Drive 1, Mix 1 (Crush bleibt so unberuehrt).

DIST_TYPES = ["AUS", "CLIP", "FOLD", "CLIP+FOLD"]
DIST_DRIVE_MIN = 1.0
DIST_DRIVE_MAX = 16.0


def dist_args(typ, drive, mix):
    if not typ:
        return {"dist_clip": 0, "dist_fold": 0, "dist_drive": 1, "dist_mix": 1}
    return {"dist_clip": 1 if typ in (1, 3) else 0,
            "dist_fold": 1 if typ in (2, 3) else 0,
            "dist_drive": round(drive, 3), "dist_mix": round(mix, 3)}


def _dist_probe():
    # Kennt amy.send die Distortion-Schluessel? (neutral an Bus 0)
    try:
        amy.send(bus=0, **dist_args(0, 1.0, 1.0))
        return True
    except Exception as e:
        print("DISTORTION FEHLT", e)
        return False


DIST_OK = _dist_probe()


def fx_send(bus, what, force=False):
    f = S["fx"][bus]
    if what in ("cho", "eq") and f["pfx"] and not force:
        return            # Chorus/EQ kommen vom Patch (PATCH-FX)
    try:
        if what == "rv":
            r = f["rv"]
            amy.send(bus=bus, reverb="%.3f,%.3f,%.3f,%.1f" % (r[0], r[1], r[2], r[3]))
        elif what == "cho":
            c = f["cho"]
            amy.send(bus=bus, chorus="%.3f,%.1f,%.3f,%.3f" % (c[0], c[3], c[1], c[2]))
        elif what == "ech":
            e = f["ech"]
            amy.send(bus=bus, echo="%.3f,%d,%d,%.3f,%.3f" % (
                e[0], int(e[1]), ECHO_MAX_DELAY_MS, e[2], e[3]))
        elif what == "eq":
            q = f["eq"]
            amy.send(bus=bus, eq="%.2f,%.2f,%.2f" % (q[0], q[1], q[2]))
        elif what == "dst":
            if DIST_OK:
                d = f["dst"]
                amy.send(bus=bus, **dist_args(d[0], d[1], d[2]))
    except Exception as e:
        print("FX", bus, what, e)


def apply_bus_fx(bus):
    for w in ("rv", "cho", "ech", "eq", "dst"):
        fx_send(bus, w)


def set_profile(bus, idx):
    if S["fx"][bus]["pfx"]:
        S["fx"][bus]["pfx"] = 0
        fx_send(bus, "cho")       # eigener Chorus statt Patch-Chorus
    S["fx"][bus]["prof"] = idx
    pr = PROFILES[idx][1]
    if pr is not None:
        S["fx"][bus]["eq"] = list(pr)
        fx_send(bus, "eq")


def reset_bus_fx(bus):
    d = default_state()["fx"][bus]
    S["fx"][bus] = d
    apply_bus_fx(bus)
    if d["pfx"]:
        reload_bus_patches(bus)
    request_save()


def reload_bus_patches(bus):
    # PATCH-FX wieder an: Patches auf dem Bus neu laden, damit ihr
    # Chorus/EQ wieder gilt (kurz haengende Noten werden beendet)
    for ch in range(1, 17):
        if S["pat"][ch] != -1 and S["bus"][ch] == bus:
            try:
                configure_channel(ch)
            except Exception as e:
                print("RELOAD", ch, e)


# ---------------- Master, Headroom ----------------

def active_buses():
    buses = {0}
    for ch in range(1, 17):
        if S["pat"][ch] != -1 or chrom_owns(ch):
            buses.add(S["bus"][ch])
    for sl in S["sb"]["sl"]:
        if sl["f"]:
            buses.add(sl["bus"])        # Pads (v13.0)
    if S["vco"]["on"]:
        buses.add(S["vco"]["bus"])      # VCO (v13.21)
    if S["ain"]["on"]:
        buses.add(S["ain"]["bus"])      # AUDIO IN (v13.22)
    return buses


def headroom_scale():
    # Summe mehrerer Kanaele -> 1/sqrt(n), mind. 0.35. Gezaehlt werden
    # belegte Kanaele, NICHT nur ungemutete - sonst springt der Pegel der
    # anderen beim Muten (v12.11).
    n = 0
    for ch in range(1, 17):
        if S["pat"][ch] != -1:
            n += 1
    if n <= 1:
        return 1.0
    return max(0.35, 1.0 / (n ** 0.5))


_last_volume = {}
_fx_touched = set()


def apply_master_volume():
    # api.md "V": Lautstaerke pro Bus. Nur belegte Busse ansprechen.
    v = round(S["master"] * headroom_scale(), 3)
    for b in active_buses():
        if _last_volume.get(b) == v:
            continue
        try:
            amy.send(bus=b, volume=v)
            _last_volume[b] = v
        except Exception as e:
            print("VOL", e)


def refresh_buses():
    # Nach Bus-/Patchwechsel: neue Busse bekommen ihre Effekte,
    # Lautstaerke und Crush.
    for b in active_buses():
        if b not in _fx_touched:
            _fx_touched.add(b)
            apply_bus_fx(b)
    apply_master_volume()
    apply_crush()


# ---------------- Crush (api.md "GH": dist_crush) ----------------

CRUSH_BITS = [0, 12, 10, 8, 6, 4, 3, 2]
CRUSH_RATES = [1, 2, 3, 4, 6, 8, 12, 16]
_crush_applied = {}


def apply_crush():
    bits = CRUSH_BITS[S["crush"]]
    rate = CRUSH_RATES[S["crate"]]
    # Nur Sample-Rate reduzieren geht auch: Bits 24 = unveraendert (api.md)
    if not bits and rate > 1:
        bits = 24
    want = (bits, rate) if bits else None
    buses = active_buses()
    for b in set(buses) | set(_crush_applied):
        target = want if b in buses else None
        if _crush_applied.get(b) == target:
            continue
        try:
            if target is None:
                amy.send(bus=b, dist_crush=0)
            else:
                amy.send(bus=b, dist_crush=[bits, rate])
            _crush_applied[b] = target
        except Exception as e:
            print("CRUSH", e)


def apply_audio_mode():
    for ch in range(1, 17):
        apply_pan(ch)
    if _vco_running:
        try:
            _vco_send_out()       # VCO-Pan folgt MONO/STEREO (v13.21)
        except Exception as e:
            print("VCO PAN", e)
    if _ain_running:
        try:
            _ain_send_out()       # AUDIO IN: Pan folgt MONO/STEREO (v13.22)
        except Exception as e:
            print("AUDIO IN PAN", e)


# ---------------- CC-Mapping (api.md "ic"/midi_cc) ----------------

CC_TARGETS = [
    ("CUT", 1, 100.0, 8000.0, 0.0, "i%iv0F%v"),
    ("RES", 0, 0.5, 8.0, 0.0, "i%iv0R%v"),
    ("LEVEL", 0, 0.0, 1.0, 0.0, "i%iiV%v"),
    ("PORTA", 0, 0.0, 1000.0, 0.0, "i%im%v"),
]
CC_TARGET_NAMES = [c[0] for c in CC_TARGETS]
_learn_armed = False
_learned = None


def apply_ccmap(ch):
    try:
        amy.send(synth=ch, midi_cc="255")
    except Exception as e:
        print("CC CLEAR", e)
        return
    for cc, t in S["ccmap"][ch]:
        name, log, lo, hi, off, cmd = CC_TARGETS[t]
        try:
            amy.send(synth=ch, midi_cc="%d,%d,%s,%s,%s,%s" % (cc, log, lo, hi, off, cmd))
        except Exception as e:
            print("CC", e)


def bind_cc(ch, cc, target):
    maps = [m for m in S["ccmap"][ch] if m[0] != cc]
    maps.append([cc, target])
    S["ccmap"][ch] = maps[-4:]
    apply_ccmap(ch)
    request_save()


# ---------------- MIDI-Typ, Failsafe ----------------

FAILSAFE_VALUES = [0.0, 0.80, 0.85, 0.90, 0.95, 1.00]


def apply_midi_type():
    try:
        amyboard.set_midi_type("B" if S["mtype"] else "A")
    except Exception as e:
        print("MIDI TYPE", e)


def apply_failsafe():
    try:
        amy.set_render_load_threshold(FAILSAFE_VALUES[S["fail"]])
    except Exception as e:
        print("FAILSAFE", e)


def apply_all_sound():
    # Kompletter Abgleich (Boot, Szene laden).
    for ch in range(1, 17):
        try:
            configure_channel(ch)
        except Exception as e:
            print("INIT CH", ch, e)
    _fx_touched.clear()
    _last_volume.clear()
    _crush_applied.clear()
    refresh_buses()
    apply_audio_mode()


# ================================================================
# EURORACK
# ================================================================
#
# CV IN 1/2: ADC misst -10..ca. +6.3 V. CV OUT 1/2: -10..+10 V.
# Pitch ueberall 1 V/Okt, 0 V = MIDI-Note 24 (C1) - wie der
# note_output-Default.

CV_IN_MIN = -10.0
CV_IN_MAX = 6.3
CV_ZERO_NOTE = 24
CV_GATE_VOLTS = 5.0
GATE_HIGH = 3.0
GATE_LOW = 2.0

EUR_OFF = 0
EUR_CV1_FILTER = 1
EUR_GATE_PITCH = 2
EUR_CV1_OUT1 = 3
EUR_CV2_OUT2 = 4
EUR_QUANTIZE = 5
EUR_MIDI_CV = 7
EUR_ACID_CV = 8
# (6 war in v11 die SCOPE-Ansicht - jetzt eigene Seite)

EUR_MODE_VALUES = [EUR_OFF, EUR_CV1_FILTER, EUR_GATE_PITCH, EUR_MIDI_CV,
                   EUR_ACID_CV, EUR_CV1_OUT1, EUR_CV2_OUT2, EUR_QUANTIZE]
EUR_MODE_NAMES = ["AUS", "CV1>FILTER", "GATE+PITCH", "MIDI>CV",
                  "303>CV", "CV1>OUT1", "CV2>OUT2", "QUANTIZE"]

NOTE_OUTPUT_CV_NATIVE = False   # Firmware verbindet den Hook (noch) nicht
NOTE_OUTPUT_OFF = getattr(amy, "NOTE_OUTPUT_OFF", 0)
NOTE_OUTPUT_CV_GATE = getattr(amy, "NOTE_OUTPUT_CV_GATE", 1)
NOTE_OUTPUT_MIDI_OUT = getattr(amy, "NOTE_OUTPUT_MIDI_OUT", 2)

_eur_mode = EUR_OFF
_eur_ch = None
_last_cv = [None, None]        # zuletzt geschriebene Spannung (nach Kalibrierung)
cv_out_v = [0.0, 0.0]          # logischer Wert fuer den Monitor
cv_in_v = [0.0, 0.0]           # zuletzt gelesene Eingaenge
cal_test = None                # Testspannung der Kalibrierseite


def cv_write(ch, volts, min_step=0.0):
    # Schreibt nur bei Aenderung (blockierender I2C-Zugriff), mit
    # Kalibrierung (Offset, Skalierung) pro Ausgang.
    cv_out_v[ch] = volts
    c = S["cal"][ch]
    v = clamp(volts * c[1] + c[0], -10.0, 10.0)
    last = _last_cv[ch]
    if last is not None and -min_step <= v - last <= min_step:
        return
    try:
        amyboard.cv_out(v, channel=ch)
        _last_cv[ch] = v
    except Exception:
        pass


def cv_in_cal(ch):
    # v13.25: (Versatz, Skala) des Eingangs: gemessen = roh * Skala + Versatz
    c = S["calin"][ch]
    return c[0], c[1]


def cv_read(ch):
    try:
        o, s = cv_in_cal(ch)
        v = clamp(amyboard.cv_in(channel=ch) * s + o, CV_IN_MIN, CV_IN_MAX)
    except Exception:
        return cv_in_v[ch]
    cv_in_v[ch] = v
    return v


def clear_cv():
    try:
        amy.send(cv_trigger="0")
        amy.send(cv_trigger="1")
    except Exception:
        pass
    _last_cv[0] = None
    _last_cv[1] = None
    cv_write(0, 0.0)
    cv_write(1, 0.0)


def _cv_trigger_offset():
    return (CV_ZERO_NOTE - 69) / 12.0


def _eur_apply_to_channel(mode, ch):
    fam = family(S["pat"][ch])
    if mode == EUR_CV1_FILTER:
        amy.send(synth=ch, osc=0, filter_freq={"const": 500, "ext0": 0.33})
        amy.send(synth=ch, osc=0, filter_type=getattr(amy, "FILTER_LPF24", 4))
    elif mode == EUR_GATE_PITCH:
        if fam not in ("JUNO", "AMYB", "DX7", "PIANO"):
            return
        amy.send(synth=ch, num_voices=1)
        # v13.25: AMY liest die Eingaenge roh - Kalibrierung hier einrechnen
        go, gs = cv_in_cal(0)
        po, ps = cv_in_cal(1)
        hi = round((GATE_HIGH - go) / gs, 3)
        lo = round((GATE_LOW - go) / gs, 3)
        if fam in ("JUNO", "AMYB"):
            for o in PITCH_OSCS[fam]:
                amy.send(synth=ch, osc=o, freq={"ext1": round(ps, 4)})
            amy.send(cv_trigger="0,%s,%s,i%dl1n%.3f" % (hi, lo, ch, CV_ZERO_NOTE + 12.0 * po))
        else:
            amy.send(cv_trigger="0,%s,%s,1,%.4f,%.4f,i%dl1n%%v" % (
                hi, lo, ps, _cv_trigger_offset() + po, ch))
        amy.send(cv_trigger="0,%s,%s,i%dl0" % (lo, hi, ch))
    elif mode == EUR_MIDI_CV and NOTE_OUTPUT_CV_NATIVE:
        amy.send(synth=ch, note_output="%d,0,1,,12,%d,%s" % (
            NOTE_OUTPUT_CV_GATE, CV_ZERO_NOTE, CV_GATE_VOLTS))


def eur_after_configure(ch):
    if ch == _eur_ch and _eur_mode in (EUR_CV1_FILTER, EUR_GATE_PITCH, EUR_MIDI_CV):
        try:
            _eur_apply_to_channel(_eur_mode, ch)
        except Exception as e:
            print("EUR REAPPLY", e)


def apply_eurorack_mode():
    global _eur_mode, _eur_ch, _last_q
    prev_mode, prev_ch = _eur_mode, _eur_ch
    _eur_mode = EUR_OFF
    _eur_ch = None
    clear_cv()
    midicv_reset()
    acid_cv_reset()
    _last_q = None
    if prev_ch is not None:
        if prev_mode == EUR_MIDI_CV and NOTE_OUTPUT_CV_NATIVE:
            try:
                amy.send(synth=prev_ch, note_output="%d" % NOTE_OUTPUT_OFF)
            except Exception:
                pass
        if prev_mode in (EUR_CV1_FILTER, EUR_GATE_PITCH):
            try:
                configure_channel(prev_ch)
            except Exception as e:
                print("EUR UNDO", e)
    mode = S["eur"]
    if mode == EUR_OFF:
        return
    _eur_mode = mode
    if mode in (EUR_CV1_FILTER, EUR_GATE_PITCH, EUR_MIDI_CV):
        _eur_ch = S["cur"]
        try:
            _eur_apply_to_channel(mode, _eur_ch)
        except Exception as e:
            print("EUR", mode, e)
    try:
        cvmod_service(force=True)
    except Exception:
        pass


# ---------------- MIDI -> CV (wie note_output CV_GATE) ----------------

_midicv_held = []
_midicv_gate = False


def midicv_reset():
    global _midicv_gate
    del _midicv_held[:]
    _midicv_gate = False


def cv_pitch(note):
    return clamp((note - CV_ZERO_NOTE) / 12.0, -10.0, 10.0)


def midicv_note(note, on):
    global _midicv_gate
    if on:
        if note in _midicv_held:
            _midicv_held.remove(note)
        _midicv_held.append(note)
        cv_write(0, cv_pitch(note))
        if not _midicv_gate:
            cv_write(1, CV_GATE_VOLTS)
            _midicv_gate = True
    else:
        if note not in _midicv_held:
            return
        _midicv_held.remove(note)
        if _midicv_held:
            cv_write(0, cv_pitch(_midicv_held[-1]))
        elif _midicv_gate:
            cv_write(1, 0.0)
            _midicv_gate = False


def midicv_active_for(ch):
    return _eur_mode == EUR_MIDI_CV and not NOTE_OUTPUT_CV_NATIVE and ch == _eur_ch


# ---------------- Quantizer, Durchreichen ----------------

_last_q = None


def quantize(v, si=None):
    # si: Skalen-Index (None = MODULAR > SKALA); v13.21 auch fuer den VCO
    semis = int(round(clamp(v, CV_IN_MIN, CV_IN_MAX) * 12.0))
    sc = SCALES[(S["qscale"] if si is None else si) % len(SCALES)]
    base = semis // 12
    best = semis
    bd = None
    for oo in (-1, 0, 1):
        for d in sc:
            c = (base + oo) * 12 + d
            dist = abs(c - semis)
            if bd is None or dist < bd:
                best, bd = c, dist
    return best / 12.0


def service_eurorack():
    global _last_q
    if cal_test is not None:
        return
    m = _eur_mode
    if m == EUR_CV1_OUT1:
        cv_write(0, cv_read(0), 0.005)
    elif m == EUR_CV2_OUT2:
        cv_write(1, cv_read(1), 0.005)
    elif m == EUR_QUANTIZE:
        q = quantize(cv_read(0))
        if _last_q is None or abs(q - _last_q) > 0.001:
            cv_write(0, q)
            _last_q = q


def set_cal_test(volts):
    # Kalibrierseite: feste Spannung auf OUT1, Gate 5 V auf OUT2.
    global cal_test
    cal_test = volts
    if volts is None:
        apply_eurorack_mode()
    else:
        _last_cv[0] = None
        _last_cv[1] = None
        cv_write(0, volts)
        cv_write(1, CV_GATE_VOLTS)


# ================================================================
# CV MOD: LFO / Huellkurve als Quelle fuer OUT1/OUT2
# (amyboard.set_cv_out, modular.md)
# ================================================================

CVMOD_LFO_SYNTH = 20
CVMOD_ENV_SYNTH = 21
CVMOD_SOURCE_NAMES = ["AUS", "LFO", "ENV"]
CVMOD_WAVE_NAMES = ["SIN", "TRI", "SAW", "PUL"]
CVMOD_WAVE_ATTR = [("SINE", 0), ("TRIANGLE", 4), ("SAW_DOWN", 2), ("PULSE", 1)]
_cv_applied = [None, None]     # Synth, der gerade auf OUT1/OUT2 liegt (0 = keiner)
_cv_synths_ready = False
TRIG_SYNTHS = (29, 30)         # Drum-Trigger OUT1/OUT2 (v12.13)
TRIG_FULL_V = 10.0             # Synth-Ausgang 1.0 = +10 V (modular.md: -10..+10 V)
TRIG_AMP = 0.8                 # Grundpegel 8 V, 5 V/VELO ueber die Velocity
_trig_native = hasattr(amyboard, "set_cv_out")
_trig_ready = [False, False]
_env_held = 0


def _cv_conflict(out):
    if out == 0:
        return _eur_mode in (EUR_CV1_OUT1, EUR_QUANTIZE, EUR_MIDI_CV, EUR_ACID_CV) or cal_test is not None
    return _eur_mode in (EUR_CV2_OUT2, EUR_MIDI_CV, EUR_ACID_CV) or cal_test is not None


def _wave_const(i):
    n, dflt = CVMOD_WAVE_ATTR[i]
    return getattr(amy, n, dflt)


def cvmod_setup():
    global _cv_synths_ready
    lf = S["lfo"]
    en = S["env"]
    try:
        # ohne vel: ein LFO, der auf keinen Ausgang geht, laeuft sonst als
        # tieffrequentes Signal in den Audio-Mix (set_cv_out nimmt ihn
        # erst beim Zuweisen heraus)
        amy.send(synth=CVMOD_LFO_SYNTH, num_voices=1, oscs_per_voice=1,
                 wave=_wave_const(lf[0]), freq=lf[1], amp=lf[2])
        amy.send(synth=CVMOD_ENV_SYNTH, num_voices=1, oscs_per_voice=1,
                 wave=_wave_const(0), freq=0, phase=0.25,
                 bp0="%d,1,%d,0" % (en[0], en[1]), amp=en[2])
        _cv_synths_ready = True
        cvfold_apply(True)        # v13.20: Wavefolder der CV-Synths
    except Exception as e:
        print("CVMOD SETUP", e)


def cvmod_update_lfo():
    if not _cv_synths_ready:
        return
    lf = S["lfo"]
    try:
        amy.send(synth=CVMOD_LFO_SYNTH, wave=_wave_const(lf[0]), freq=lf[1], amp=lf[2])
    except Exception as e:
        print("CVMOD LFO", e)


def cvmod_update_env():
    if not _cv_synths_ready:
        return
    en = S["env"]
    try:
        amy.send(synth=CVMOD_ENV_SYNTH, bp0="%d,1,%d,0" % (en[0], en[1]), amp=en[2])
    except Exception as e:
        print("CVMOD ENV", e)


# ---------------- Wavefolder fuer CV LFO / CV ENV (v13.20) ----------------
# Der Waveshaper aus v13.16 (dist_clip/dist_fold/dist_drive/dist_mix) sitzt
# in AMY an jedem Oszillator - also auch an den Synths 20 (LFO) und 21 (ENV),
# die per set_cv_out auf OUT1/OUT2 liegen. Gefaltet wird in AMY selbst.
# Die Amplitude (TIEFE) wirkt VOR dem Shaper: sie bestimmt, wie weit die
# Welle in den Folder laeuft (wie der Eingangspegel eines echten Wavefolders),
# DRIVE verstaerkt zusaetzlich. MIX blendet zwischen glatt und gefaltet.
# FOLD MOD: CV IN1/IN2 verschiebt den LFO-Drive um bis zu +-2 Oktaven
# (Faktor 4 bei MOD TIEFE 1, 5 V = voller Ausschlag), alle FOLD_MOD_MS.

FOLD_MOD_NAMES = ["AUS", "CV IN1", "CV IN2"]
FOLD_MOD_MS = 30
_fold_sent = [None, None]      # zuletzt gesendet (Typ, Drive, Mix): LFO, ENV
_fold_mod = 0.0                # aktuelle Auslenkung aus CV IN, -1..+1
_fold_next = 0


def fold_drive_lfo():
    # LFO DRIVE inklusive FOLD MOD
    ff = S["lfof"]
    d = ff[1]
    if ff[3] and _fold_mod:
        d = d * (2 ** (2.0 * _fold_mod * ff[4]))
    return clamp(d, DIST_DRIVE_MIN, DIST_DRIVE_MAX)


def _fold_send(i, synth, typ, drive, mix, force):
    want = (typ, round(drive, 2), round(mix, 3))
    if not force and _fold_sent[i] == want:
        return
    try:
        amy.send(synth=synth, osc=0, **dist_args(typ, drive, mix))
        _fold_sent[i] = want
    except Exception as e:
        print("CV FOLD", e)


def cvfold_apply(force=False):
    if not (DIST_OK and _cv_synths_ready):
        return
    ff = S["lfof"]
    ef = S["envf"]
    _fold_send(0, CVMOD_LFO_SYNTH, ff[0], fold_drive_lfo(), ff[2], force)
    _fold_send(1, CVMOD_ENV_SYNTH, ef[0], ef[1], ef[2], force)


def cvfold_service():
    # FOLD MOD nachfuehren - nur wenn FOLD an, eine Quelle gewaehlt ist und
    # der LFO wirklich auf einem Ausgang liegt
    global _fold_mod, _fold_next
    ff = S["lfof"]
    if not (DIST_OK and ff[0] and ff[3] and CVMOD_LFO_SYNTH in _cv_applied):
        if _fold_mod:
            _fold_mod = 0.0
            cvfold_apply()
        return
    if since(_fold_next) < 0:
        return
    _fold_next = time.ticks_add(now(), FOLD_MOD_MS)
    o = clamp(cv_read(ff[3] - 1) / 5.0, -1.0, 1.0)
    if abs(o - _fold_mod) > 0.01:
        _fold_mod = o
        cvfold_apply()


def _lfo_wave(i, p):
    # eine Periode der LFO-Welle fuer die Vorschau (p = 0..1)
    if i == 0:
        return math.sin(6.2832 * p)
    if i == 1:
        return 1.0 - 4.0 * abs(p - 0.5)
    if i == 2:
        return 1.0 - 2.0 * p
    return 1.0 if p < 0.5 else -1.0


def fold_shape(x, typ):
    # Naeherung fuer die Anzeige: Dreiecks-Faltung an +-1, Clip hart.
    # AMYs Kennlinien koennen weicher sein - nur zur Orientierung.
    if typ in (2, 3):
        t = math.fmod(x + 1.0, 4.0)
        if t < 0:
            t += 4.0
        x = t - 1.0 if t <= 2.0 else 3.0 - t
    if typ in (1, 3):
        x = clamp(x, -1.0, 1.0)
    return x


def trig_synth_setup(out):
    # Gleichspannung (Sinus bei freq 0, Phase 0.25 = 1.0) mit
    # Rechteck-Huellkurve: Note an = Gate high, Note aus = 0 V. Ohne vel
    # angelegt - erst nach set_cv_out wird gespielt (sonst Audio-Mix).
    if _trig_ready[out]:
        return True
    try:
        amy.send(synth=TRIG_SYNTHS[out], num_voices=1, oscs_per_voice=1,
                 wave=_wave_const(0), freq=0, phase=0.25, bp0="1,1,1,0",
                 amp=TRIG_AMP)
        _trig_ready[out] = True
    except Exception as e:
        print("TRIG SETUP", e)
    return _trig_ready[out]


def trig_native(out):
    return _cv_applied[out] == TRIG_SYNTHS[out]


def _cv_want(out):
    want = S["cvsrc"][out]
    if want and not _cv_conflict(out):
        return (0, CVMOD_LFO_SYNTH, CVMOD_ENV_SYNTH)[want]
    if (_trig_native and S["drm"]["trg"][out] >= 0 and not _cv_conflict(out)
            and not S["cvsrc"][out] and trig_synth_setup(out)):
        return TRIG_SYNTHS[out]
    return 0


def cvmod_service(force=False):
    if force:
        _cv_applied[0] = None
        _cv_applied[1] = None
    changed = False
    for out in (0, 1):
        synth = _cv_want(out)
        if synth == _cv_applied[out]:
            continue
        old = _cv_applied[out]
        if old in TRIG_SYNTHS:
            try:
                amy.send(synth=old, vel=0)
            except Exception:
                pass
        if synth in (CVMOD_LFO_SYNTH, CVMOD_ENV_SYNTH) and not _cv_synths_ready:
            cvmod_setup()
        try:
            amyboard.set_cv_out(channel=out, synth=synth)
        except Exception as e:
            print("CVMOD OUT", e)
        _cv_applied[out] = synth
        if old in TRIG_SYNTHS and synth == 0 and not _cv_conflict(out):
            _last_cv[out] = None
            cv_write(out, 0.0)
        changed = True
    if changed:
        _lfo_gate()


def _lfo_gate():
    # LFO erst NACH dem Zuweisen starten und stoppen, sobald kein
    # Ausgang ihn mehr nutzt - sonst landet er im Audio-Mix.
    if not _cv_synths_ready:
        return
    on = CVMOD_LFO_SYNTH in _cv_applied
    try:
        amy.send(synth=CVMOD_LFO_SYNTH, vel=1 if on else 0)
    except Exception as e:
        print("CVMOD LFO GATE", e)


def cvmod_env_note(on):
    global _env_held
    try:
        if on:
            _env_held += 1
            amy.send(synth=CVMOD_ENV_SYNTH, note=60, vel=1)
        else:
            _env_held = max(0, _env_held - 1)
            if _env_held == 0:
                amy.send(synth=CVMOD_ENV_SYNTH, vel=0)
    except Exception:
        pass


# ================================================================
# VCO (v13.21): AMYboard als eigenstaendiger Oszillator
# ================================================================
#
# Ein eigener Synth (VCO_SYNTH) klingt dauerhaft, solange VCO = AN.
# Tonhoehe: 1 V/Okt an CV IN1 (ext0) oder IN2 (ext1). AMY rechnet den
# freq-Koeffizienten selbst pro Block nach - Python ist nicht im
# Signalweg. Die gespielte Note spielt keine Rolle (Koeffizient note = 0),
# die Grundfrequenz steckt komplett in const (Hz bei 0 V).
#
# Kette (chained_osc, synth.md): ein note-on startet alle drei.
#   osc 0  Haupt-Welle, traegt den Wavefolder (dist_*, wie v13.16)
#   osc 1  Sub: Rechteck 1 oder 2 Oktaven tiefer
#   osc 2  zweiter Oszillator: Intervall (HT) + Verstimmung (Cent)
# Pegel je Oszillator ueber amp const (amp wird im dB-Bereich mit vel
# und eg0 verrechnet, wirkt also als Faktor), gesamt ueber synth_level.
#
# MOD IN: FM (Tonhoehe) und PWM laufen als ext-Koeffizient in AMY,
# FOLD (Drive) wird wie FOLD MOD des CV LFO alle 30 ms nachgefuehrt.
# QUANT: Python liest den 1V/Okt-Eingang, rastet ihn auf die Skala und
# setzt const neu (bei jedem UI-Durchlauf, ~40 ms) - dann ohne ext.

VCO_WAVE_NAMES = ["SIN", "TRI", "SAW", "PULS"]   # Reihenfolge wie CVMOD_WAVE_ATTR
VCO_MOD_NAMES = ["FM", "PWM", "FOLD"]
VCO_IN_NAMES = ["AUS", "IN1", "IN2"]
VCO_PM_NAMES = ["FREI", "QUANT"]
VCO_OSCS = 3
VCO_BP0 = "5,1,60,0"       # 5 ms Einschwingen, halten, 60 ms Ausklingen
VCO_FM_OCT = 1.0           # MOD TIEFE 1 = 1 Oktave pro Volt
VCO_PWM_PER_V = 0.08       # MOD TIEFE 1 = 0.08 Pulsbreite pro Volt (5 V = 0.4)
VCO_FOLD_MS = 30
VCO_Q_HYST = 0.2           # Quant: neue Stufe erst, wenn sie 0.2 HT naeher ist
VCO_SYNTH = None
_vco_running = False
_vco_q = None              # aktuelle Quant-Stufe in Halbtoenen ueber dem Grundton
_vco_fold_mod = 0.0        # Auslenkung FOLD-Modulation, -1..+1
_vco_fold_next = 0
_vco_fold_sent = None
VCO_XFADE_MS = 65         # Umschalten: 60 ms ausblenden, dann wechseln
VCO_SM_ALPHA = (0.0, 0.4, 0.15)   # Glaettung je UI-Durchlauf (~30 ms)
_vco_wave_due = None      # Zeitpunkt fuer den verzoegerten Wellenwechsel
_vco_sm = None            # geglaettete Tonhoehe in Halbtoenen ueber dem Grundton
_vco_sm_sent = None


def vco_init():
    # Synth-Nummer suchen: 40, wenn die Firmware Synths ueber 31 kennt
    # (wie bei den Pads), sonst 31 - aber nur, wenn die Pads 31 nicht
    # selbst brauchen.
    global VCO_SYNTH
    VCO_SYNTH = None
    try:
        amy.send(synth=40, num_voices=1, oscs_per_voice=VCO_OSCS)
        if amy.get_synth_commands(40).strip():
            VCO_SYNTH = 40
    except Exception as e:
        print("VCO PROBE", e)
    if VCO_SYNTH is None and 31 not in PAD_SYNTHS:
        VCO_SYNTH = 31
    print("VCO-SYNTH", VCO_SYNTH)
    if S["vco"]["on"]:
        vco_start()


def vco_hz(semis=0.0):
    # Frequenz bei 0 V (plus semis Halbtoene): Grundton + Fein
    v = S["vco"]
    return 440.0 * 2 ** ((v["root"] + semis - 69) / 12.0 + v["fine"] / 1200.0)


def _vco_ext(v):
    # ext-Koeffizienten (ext0 = IN1, ext1 = IN2) fuer freq in Okt/V und der
    # Versatz in Oktaven, den die Eingangs-Kalibrierung dazu beitraegt
    # (AMY liest die Eingaenge roh: Okt = k * (roh * Skala + Versatz)).
    e = [0.0, 0.0]
    sh = 0.0
    for c, k in ((v["src"], v["trk"] if (v["src"] and not v["pm"] and not v["sm"]) else 0.0),
                 (v["msrc"], v["md"] * VCO_FM_OCT if (v["msrc"] and v["mt"] == 0) else 0.0)):
        if c and k:
            o, s = cv_in_cal(c - 1)
            e[c - 1] += k * s
            sh += k * o
    return e, sh


def _vco_send_freq():
    v = S["vco"]
    global _vco_sm_sent
    semis = _vco_q if (v["pm"] and v["src"] and _vco_q is not None) else 0
    if v["src"] and not v["pm"] and v["sm"] and _vco_sm is not None:
        semis = _vco_sm
        _vco_sm_sent = _vco_sm
    e, sh = _vco_ext(v)
    f0 = vco_hz(semis) * 2 ** sh
    f2 = f0 * 2 ** (v["iv"] / 12.0 + v["det"] / 1200.0)
    for o, f in ((0, f0), (1, f0 / (2 ** v["so"])), (2, f2)):
        amy.send(synth=VCO_SYNTH, osc=o,
                 freq={"const": round(f, 4), "note": 0, "bend": 0,
                       "ext0": round(e[0], 4), "ext1": round(e[1], 4)})


def _vco_send_duty():
    v = S["vco"]
    d = [0.0, 0.0]
    pw = v["pw"]
    if v["msrc"] and v["mt"] == 1:
        o, s = cv_in_cal(v["msrc"] - 1)
        k = v["md"] * VCO_PWM_PER_V
        d[v["msrc"] - 1] = round(k * s, 4)
        pw = clamp(pw + k * o, 0.02, 0.98)
    for o in (0, 2):
        amy.send(synth=VCO_SYNTH, osc=o,
                 duty={"const": round(pw, 3), "ext0": d[0], "ext1": d[1]})


def _vco_send_wave():
    w = _wave_const(S["vco"]["wav"])
    for o in (0, 2):
        amy.send(synth=VCO_SYNTH, osc=o, wave=w)


def _vco_send_mix():
    # Summe normieren, damit SUB + OSZ 2 nicht uebersteuern
    v = S["vco"]
    norm = 1.0 / (1.0 + 0.5 * (v["sub"] + v["o2"]))
    for o, g in ((0, 1.0), (1, v["sub"]), (2, v["o2"])):
        amy.send(synth=VCO_SYNTH, osc=o, amp={"const": round(g * norm, 3)})


def _vco_send_out():
    v = S["vco"]
    p = 0.5 if S["audio"] == 1 else v["pan"]
    for o in range(VCO_OSCS):
        amy.send(synth=VCO_SYNTH, osc=o, pan=p)
    amy.send(synth=VCO_SYNTH, synth_level=v["lvl"])


def vco_fold_drive():
    v = S["vco"]
    d = v["fd"]
    if _vco_fold_mod:
        d = d * (2 ** (2.0 * _vco_fold_mod * v["md"]))
    return clamp(d, DIST_DRIVE_MIN, DIST_DRIVE_MAX)


def _vco_send_fold(force=False):
    global _vco_fold_sent
    if not DIST_OK:
        return
    v = S["vco"]
    want = (v["ft"], round(vco_fold_drive(), 2), round(v["fm"], 3))
    if not force and want == _vco_fold_sent:
        return
    amy.send(synth=VCO_SYNTH, osc=0, **dist_args(want[0], want[1], want[2]))
    _vco_fold_sent = want


def _vco_quant(force=False):
    # Quant-Stufe aus dem 1V/Okt-Eingang; True, wenn sie sich geaendert hat
    global _vco_q
    v = S["vco"]
    if not (v["pm"] and v["src"]):
        return False
    r = cv_read(v["src"] - 1) * v["trk"] * 12.0
    q = int(round(quantize(r / 12.0, v["sc"]) * 12.0))
    if (not force and _vco_q is not None and q != _vco_q
            and abs(r - _vco_q) < abs(r - q) + VCO_Q_HYST):
        q = _vco_q
    if q == _vco_q and not force:
        return False
    _vco_q = q
    return True


def vco_start():
    global _vco_running, _vco_q, _vco_fold_sent, _vco_fold_mod, _vco_wave_due, _vco_sm
    _vco_wave_due = None
    _vco_sm = None
    if VCO_SYNTH is None:
        S["vco"]["on"] = 0
        toast("VCO", "KEIN SYNTH FREI", 1800)
        return False
    s = VCO_SYNTH
    v = S["vco"]
    try:
        amy.send(synth=s, num_voices=1, oscs_per_voice=VCO_OSCS, bus=v["bus"])
        amy.send(synth=s, osc=0, chained_osc=1)
        amy.send(synth=s, osc=1, chained_osc=2, wave=_wave_const(3), duty=0.5)
        for o in range(VCO_OSCS):
            amy.send(synth=s, osc=o, bp0=VCO_BP0)
        _vco_q = None
        _vco_fold_sent = None
        _vco_fold_mod = 0.0
        _vco_quant(True)
        _vco_send_wave()
        _vco_send_freq()
        _vco_send_duty()
        _vco_send_mix()
        _vco_send_out()
        _vco_send_fold(True)
        amy.send(synth=s, note=69, vel=1)
        _vco_running = True
    except Exception as e:
        print("VCO START", e)
        toast("VCO", "FEHLER", 1500)
        return False
    refresh_buses()
    return True


def vco_stop():
    global _vco_running, _vco_wave_due
    _vco_wave_due = None
    if VCO_SYNTH is not None:
        try:
            amy.send(synth=VCO_SYNTH, vel=0)
        except Exception as e:
            print("VCO STOP", e)
    _vco_running = False
    refresh_buses()


def vco_apply_all():
    if S["vco"]["on"]:
        vco_start()
    elif _vco_running:
        vco_stop()


def vco_service():
    # Quant nachfuehren, FOLD per CV modulieren
    global _vco_fold_mod, _vco_fold_next, _vco_wave_due, _vco_sm
    if not _vco_running:
        return
    v = S["vco"]
    try:
        if _vco_wave_due is not None and since(_vco_wave_due) >= 0:
            _vco_wave_due = None
            _vco_send_wave()
            amy.send(synth=VCO_SYNTH, note=69, vel=1)
        if _vco_quant():
            _vco_send_freq()
        if v["src"] and not v["pm"] and v["sm"]:
            r = cv_read(v["src"] - 1) * v["trk"] * 12.0
            _vco_sm = r if _vco_sm is None else _vco_sm + VCO_SM_ALPHA[v["sm"]] * (r - _vco_sm)
            if _vco_sm_sent is None or abs(_vco_sm - _vco_sm_sent) > 0.01:
                _vco_send_freq()
        if v["mt"] == 2 and v["msrc"] and v["ft"] and DIST_OK:
            if since(_vco_fold_next) >= 0:
                _vco_fold_next = time.ticks_add(now(), VCO_FOLD_MS)
                o = clamp(cv_read(v["msrc"] - 1) / 5.0, -1.0, 1.0)
                if abs(o - _vco_fold_mod) > 0.01:
                    _vco_fold_mod = o
                    _vco_send_fold()
        elif _vco_fold_mod:
            _vco_fold_mod = 0.0
            _vco_send_fold()
    except Exception as e:
        print("VCO SERVICE", e)


def vco_pitch_now():
    # aktuelle Tonhoehe als MIDI-Notenzahl mit Nachkommastellen (Anzeige)
    v = S["vco"]
    n = v["root"] + v["fine"] / 100.0
    if v["src"]:
        if v["pm"]:
            n += _vco_q or 0
        elif v["sm"] and _vco_sm is not None:
            n += _vco_sm
        else:
            n += cv_in_v[v["src"] - 1] * 12.0 * v["trk"]
    if v["msrc"] and v["mt"] == 0:
        n += cv_in_v[v["msrc"] - 1] * 12.0 * v["md"] * VCO_FM_OCT
    return n


# ================================================================
# AUDIO IN (v13.22): Eingang live durch Filter und Effekte
# ================================================================
#
# AMY spielt den Stereo-Eingang als Oszillator (api.md: wave AUDIO_IN0 =
# links, AUDIO_IN1 = rechts). Zwei eigene Synths mit je einem
# Oszillator, solange AUDIO IN = AN als Dauerton gestartet (wie der VCO):
#   AIN_SYNTHS[0]  AUDIO_IN0 (L)
#   AIN_SYNTHS[1]  AUDIO_IN1 (R)
# Zwei Synths statt einer chained_osc-Kette, weil Filter und Distortion
# bei einer Kette auf die ganze Kette wirken - L und R sollen getrennt
# bleiben (Panorama, Stereo-Filter).
# Pro Oszillator: IN GAIN (amp const, aus dB), Distortion (dist_*, vor
# dem Filter), Filter (wie die Sample-Slots), Pan. Pro Synth:
# synth_level (IN LEVEL) und Bus. Ueber den Bus wirken Reverb, Chorus,
# Echo, EQ, Bus-Distortion und Crush aus EFFEKTE. Python ist nicht im
# Signalweg.
#
# MODUS: STEREO (L links, R rechts, BREITE 0..1 um PAN herum), MONO (L+R
#        auf PAN, je -6 dB, damit gleiche Signale nicht lauter werden),
#        NUR L, NUR R (die andere Seite schweigt).
# Pegelanzeige: amy.get_input_buffer() liefert den letzten Eingangsblock
# (bis 256 Frames int16, L/R verschraenkt). Gelesen wird nur, solange die
# AUDIO-IN-Seite offen ist (jeder zweite Frame reicht fuer die Spitze).

AIN_MODE_NAMES = ["STEREO", "MONO", "NUR L", "NUR R"]
AIN_WAVES = (getattr(amy, "AUDIO_IN0", 12), getattr(amy, "AUDIO_IN1", 13))
AIN_BP0 = "5,1,60,0"        # wie VCO: 5 ms einblenden, halten, 60 ms aus
AIN_GAIN_MIN = -24.0
AIN_GAIN_MAX = 12.0
AIN_METER_FLOOR = -48.0     # dB am linken Rand der Pegelanzeige
AIN_CLIP = 32000            # ab hier gilt ein Sample als Uebersteuerung
AIN_CLIP_MS = 1500          # CLIP so lange anzeigen
AIN_SYNTHS = None
_ain_running = False
_ain_gate = [False, False]  # klingt L / R gerade?
_ain_meter = [0.0, 0.0]     # Spitze 0..1 mit Abfall
_ain_fade_due = None      # v13.27: Umschalten mit Aus-/Einblenden
_ain_fade_fns = []
_ain_clip = [None, None]    # Zeitpunkt der letzten Uebersteuerung


def ain_init():
    # Synths 41/42 gibt es nur, wenn die Firmware Synths ueber 31 kennt
    # (wie Pads und VCO). Sonst bleibt AUDIO IN aus ("FEHLT").
    global AIN_SYNTHS
    AIN_SYNTHS = None
    try:
        amy.send(synth=42, num_voices=1, oscs_per_voice=1)
        if amy.get_synth_commands(42).strip():
            AIN_SYNTHS = (41, 42)
    except Exception as e:
        print("AUDIO IN PROBE", e)
    print("AUDIO-IN-SYNTHS", AIN_SYNTHS)
    if S["ain"]["on"]:
        ain_start()


def _ain_want():
    # welche Seiten klingen sollen: (L, R)
    m = S["ain"]["mode"]
    return (m != 3, m != 2)


def _ain_pans():
    a = S["ain"]
    if S["audio"] == 1:
        return (0.5, 0.5)
    p = a["pan"]
    if a["mode"] == 0:
        h = a["wid"] / 2.0
        return (clamp(p - h, 0.0, 1.0), clamp(p + h, 0.0, 1.0))
    return (p, p)


def ain_gain_factor():
    a = S["ain"]
    g = 10 ** (a["gain"] / 20.0)
    if a["mode"] == 1:
        g *= 0.5            # MONO: L+R auf einer Position
    return g


def _ain_send_gain():
    g = round(ain_gain_factor(), 4)
    for s in AIN_SYNTHS:
        amy.send(synth=s, osc=0, amp={"const": g})


def _ain_send_out():
    a = S["ain"]
    pl = _ain_pans()
    for i in (0, 1):
        amy.send(synth=AIN_SYNTHS[i], osc=0, pan=round(pl[i], 3))
        amy.send(synth=AIN_SYNTHS[i], synth_level=a["lvl"])


def _ain_send_filter():
    a = S["ain"]
    ft = a["ft"]
    for s in AIN_SYNTHS:
        amy.send(synth=s, osc=0, filter_type=SMP_FILT_VALS[ft])
        if ft:
            amy.send(synth=s, osc=0, filter_freq={"const": round(a["cu"], 1)},
                     resonance=a["rs"])


def _ain_send_dist():
    if not DIST_OK:
        return
    a = S["ain"]
    for s in AIN_SYNTHS:
        amy.send(synth=s, osc=0, **dist_args(a["dt"], a["dd"], a["dm"]))


def _ain_send_gate():
    # Note-on fuer jede Seite, die klingen soll; die andere aus
    w = _ain_want()
    for i in (0, 1):
        if w[i] and not _ain_gate[i]:
            amy.send(synth=AIN_SYNTHS[i], note=60, vel=1)
            _ain_gate[i] = True
        elif not w[i] and _ain_gate[i]:
            amy.send(synth=AIN_SYNTHS[i], vel=0)
            _ain_gate[i] = False


def ain_start():
    global _ain_running
    if AIN_SYNTHS is None:
        S["ain"]["on"] = 0
        toast("AUDIO IN", "KEIN SYNTH FREI", 1800)
        return False
    a = S["ain"]
    try:
        for i in (0, 1):
            s = AIN_SYNTHS[i]
            amy.send(synth=s, num_voices=1, oscs_per_voice=1, bus=a["bus"])
            amy.send(synth=s, osc=0, wave=AIN_WAVES[i], bp0=AIN_BP0)
            _ain_gate[i] = False
        _ain_send_gain()
        _ain_send_dist()
        _ain_send_filter()
        _ain_send_out()
        _ain_send_gate()
        _ain_running = True
    except Exception as e:
        print("AUDIO IN START", e)
        toast("AUDIO IN", "FEHLER", 1500)
        return False
    refresh_buses()
    return True


def ain_fade(fn):
    # Filter-/Distortion-Typ wechseln, ohne zu knacken: beide Seiten kurz
    # ausblenden (Huellkurve), nach VCO_XFADE_MS umschalten und wieder an
    global _ain_fade_due
    if not _ain_running:
        return
    if _ain_fade_due is None:
        for i in (0, 1):
            if _ain_gate[i]:
                amy.send(synth=AIN_SYNTHS[i], vel=0)
    if fn not in _ain_fade_fns:
        _ain_fade_fns.append(fn)
    _ain_fade_due = time.ticks_add(now(), VCO_XFADE_MS)


def ain_service():
    global _ain_fade_due
    if _ain_fade_due is None or since(_ain_fade_due) < 0:
        return
    _ain_fade_due = None
    try:
        for fn in _ain_fade_fns:
            fn()
        del _ain_fade_fns[:]
        if _ain_running:
            for i in (0, 1):
                if _ain_gate[i]:
                    amy.send(synth=AIN_SYNTHS[i], note=60, vel=1)
    except Exception as e:
        print("AUDIO IN FADE", e)


def ain_stop():
    global _ain_running, _ain_fade_due
    _ain_fade_due = None
    del _ain_fade_fns[:]
    if AIN_SYNTHS is not None:
        for i in (0, 1):
            try:
                amy.send(synth=AIN_SYNTHS[i], vel=0)
            except Exception as e:
                print("AUDIO IN STOP", e)
            _ain_gate[i] = False
    _ain_running = False
    refresh_buses()


def ain_apply_all():
    if S["ain"]["on"]:
        ain_start()
    elif _ain_running:
        ain_stop()


def ain_toggle():
    # Taster-Funktion AUDIO IN (v13.22)
    S["ain"]["on"] = 0 if S["ain"]["on"] else 1
    ain_apply_all()
    toast("AUDIO IN", "AN" if _ain_running else "AUS", 700)
    request_save()


def ain_meter_read():
    # Spitzenwerte des letzten Eingangsblocks nach _ain_meter (0..1),
    # mit Abfall, damit die Anzeige nicht flackert.
    getbuf = getattr(amy, "get_input_buffer", None)
    if getbuf is None:
        return False
    try:
        b = getbuf()
    except Exception:
        return False
    pk = [0, 0]
    if b:
        a = array("h", bytes(b))
        for i in range(0, len(a) - 1, 4):
            v = a[i]
            if v < 0:
                v = -v
            if v > pk[0]:
                pk[0] = v
            v = a[i + 1]
            if v < 0:
                v = -v
            if v > pk[1]:
                pk[1] = v
    t = now()
    for i in (0, 1):
        if pk[i] >= AIN_CLIP:
            _ain_clip[i] = t
        p = pk[i] / 32767.0
        _ain_meter[i] = p if p > _ain_meter[i] else _ain_meter[i] * 0.7
    return True


def ain_clipping(i):
    c = _ain_clip[i]
    return c is not None and since(c) < AIN_CLIP_MS


def ain_db(i):
    p = _ain_meter[i]
    if p <= 0.00001:
        return AIN_METER_FLOOR
    return max(AIN_METER_FLOOR, 20.0 * math.log10(p))


# ================================================================
# SAMPLER / GROOVEBOX (v13.0)
# ================================================================
#
# 8 Sample-Slots. Jeder Slot verweist auf eine WAV auf der SD-Karte
# (eigene Aufnahme oder manuell kopiert). Geladen wird nur der
# getrimmte Bereich START..ENDE, und zwar mono in den RAM von AMY
# (load_sample, api.md "PCM sampling"). Die Datei selbst bleibt
# unveraendert - Trimmen ist zerstoerungsfrei.
#
# Gespielt wird ein Slot
#   - als PAD: von der Drum-Spur (Instrument > SAMPLE) oder ueber den
#     PAD-KANAL (MIDI-Noten 36-43 = Slot 1-8), je Slot ein eigener Synth
#   - CHROMATISCH: ein MIDI-Kanal spielt einen Slot ueber die Tastatur
#     (auch Sequencer-Spuren 1-4 koennen diesen Kanal spielen)
#
# Pro Slot: Modus EINMAL / GATE / LOOP, Loop-Punkte, Tune/Fein,
# Grundton, Level/Pan/Bus, Huellkurve (ADSR), Filter (TP/BP/HP/TP24)
# mit Resonanz und Filter-Huellkurve.
#
# Aufnahme: LINE (Audio-Eingang) oder MIX (Resampling) als Stereo-WAV
# nach /sd/samples/RECnnn.wav, danach automatisch in den Ziel-Slot.
# Die Bloecke kommen ueber amy.get_input_buffer()/get_output_buffer();
# waehrend der Aufnahme steht die Bedienung. HW-TEST: LUECKEN-Anzeige.

SMP_SLOTS = 8
SMP_PRESET_BASE = 1040          # PCM-Presets 1040-1047 im RAM von AMY
SMP_MAX_MS = 10000              # hoechstens 10 s pro Slot
SMP_ROOT = 60                   # Preset-Grundton (Pads spielen Note 60)
SMP_CHUNK = 94                  # Frames pro Uebertragungsnachricht (188 Byte)
SD_ROOT = "/sd"
SMP_DIR = SD_ROOT + "/samples"
SMP_MODE_NAMES = ["EINMAL", "GATE", "LOOP"]
SMP_FILT_NAMES = ["AUS", "TP", "BP", "HP", "TP24"]
SMP_FILT_VALS = [0, 1, 2, 3, 4]           # AMY filter_type
# v13.19: Notch und Phaser (AMY seit 03.08.2026), nur wenn bekannt
for _fn, _fc in (("NOTCH", "FILTER_NOTCH"), ("PHASER", "FILTER_PHASER")):
    _fv = getattr(amy, _fc, None)
    if _fv is not None:
        SMP_FILT_NAMES.append(_fn)
        SMP_FILT_VALS.append(_fv)
SMP_SRC_NAMES = ["LINE", "MIX"]
SMP_REC_UNITS = ["SEK", "TAKTE"]
SMP_REC_STARTS = ["SOFORT", "TAKT 1"]
SMP_PAD_NOTE0 = 36              # PAD-KANAL: Note 36 = Slot 1 ... 43 = Slot 8
SMP_BLOCK_FRAMES = 256
SMP_BLOCK_US = 1000000.0 * SMP_BLOCK_FRAMES / 44100
ZERO_HZ = 440.0                 # AMY: logfreq 0 = 440 Hz (constants.py)
PCM_WAVE = getattr(amy, "PCM", 7)
PCM_PLAY_STOP = 0
PCM_LOOP_FOREVER = 4


# ---------------- Hilfen ----------------
# Kein viper/native: der Compiler der Firmware bricht damit beim Laden
# des Sketches ab ("asm overflow", v13.0). Gerechnet wird in array("h"),
# Spitzenwerte ueber die eingebauten max()/min().

from array import array


try:
    import ubinascii as _b64m

    def _b64(b):
        return _b64m.b2a_base64(b)[:-1].decode()
except ImportError:
    import binascii as _b64m

    def _b64(b):
        return _b64m.b2a_base64(b)[:-1].decode()


# Uebertragungs-Nutzdaten: ueber den sysex-markierten Weg, damit AMY
# sie nicht mit normalen Befehlen (Sequencer!) verwechselt (amy/__init__.py)
_xfer_send = getattr(amy, "_send_transfer_chunk", None)
SMP_XFER_SAFE = _xfer_send is not None
if _xfer_send is None:
    def _xfer_send(m):
        amy.send_raw(m)
_xfer_lock = False       # True: Sequencer haelt an (nur ohne sicheren Weg)


# ---------------- WAV-Dateien ----------------

def wav_info(path):
    # -> dict(ch, sr, bits, off, frames) oder Text mit dem Fehler
    try:
        f = open(path, "rb")
    except Exception:
        return "FEHLT"
    try:
        h = f.read(12)
        if len(h) < 12 or h[0:4] != b"RIFF" or h[8:12] != b"WAVE":
            return "KEIN WAV"
        fmt = None
        pos = 12
        while True:
            c = f.read(8)
            if len(c) < 8:
                return "KEINE DATEN"
            cid = c[0:4]
            size = c[4] | (c[5] << 8) | (c[6] << 16) | (c[7] << 24)
            pos += 8
            if cid == b"fmt ":
                d = f.read(size)
                tag = d[0] | (d[1] << 8)
                ch = d[2] | (d[3] << 8)
                sr = d[4] | (d[5] << 8) | (d[6] << 16) | (d[7] << 24)
                bits = d[14] | (d[15] << 8)
                if tag == 0xFFFE and size >= 26:
                    tag = d[24] | (d[25] << 8)
                fmt = (tag, ch, sr, bits)
            elif cid == b"data":
                if fmt is None:
                    return "KEIN FORMAT"
                tag, ch, sr, bits = fmt
                if tag != 1:
                    return "NICHT PCM"
                if bits != 16:
                    return "NUR 16 BIT"
                if ch not in (1, 2):
                    return "KANAELE?"
                return {"ch": ch, "sr": sr, "off": pos,
                        "frames": size // (2 * ch)}
            else:
                f.seek(pos + size + (size & 1))
            pos += size + (size & 1)
            if cid == b"fmt ":
                f.seek(pos)
    except Exception as e:
        return str(e)[:10] or "FEHLER"
    finally:
        f.close()


def smp_list_files():
    # WAVs aus /sd/samples und dem Hauptverzeichnis der Karte
    out = []
    for d in (SMP_DIR, SD_ROOT):
        try:
            names = os.listdir(d)
        except Exception:
            continue
        for n in names:
            if n.lower().endswith(".wav") and not n.startswith("."):
                out.append(n if d == SD_ROOT else d[len(SD_ROOT) + 1:] + "/" + n)
    out.sort()
    return out


def smp_path(rel):
    return SD_ROOT + "/" + rel


def smp_short(rel, n=8):
    nm = rel.split("/")[-1]
    if nm.lower().endswith(".wav"):
        nm = nm[:-4]
    return nm[:n].upper()


# ---------------- Laufzeit je Slot ----------------
# info: wav_info der Datei, ok: Sample geladen, frames: geladene Frames,
# err: Fehlertext, peaks: Wellenform-Cache (fuer den Editor)

class SlotRT:
    def __init__(self):
        self.info = None
        self.ok = False
        self.frames = 0
        self.err = ""
        self.peaks = None
        self.pkey = None
        self.ram = False      # v13.11: Aufnahme nur im RAM von AMY


SRT = [SlotRT() for _ in range(SMP_SLOTS)]


def sb():
    return S["sb"]


def slot(k):
    return S["sb"]["sl"][k]


def slot_len_ms(k):
    i = SRT[k].info
    if not isinstance(i, dict) or not i["sr"]:
        return 0
    return i["frames"] * 1000 // i["sr"]


def slot_region(k):
    # -> (start_ms, ende_ms) gueltig und hoechstens SMP_MAX_MS lang
    sl = slot(k)
    total = slot_len_ms(k)
    st = clamp_int(sl["st"], 0, max(0, total - 1))
    en = sl["en"] if sl["en"] else total
    en = clamp_int(en, st + 1, total) if total else 0
    if en - st > SMP_MAX_MS:
        en = st + SMP_MAX_MS
    return st, en


def slot_name(k):
    sl = slot(k)
    if not sl["f"]:
        return "RAM-REC" if SRT[k].ram else "LEER"
    return smp_short(sl["f"])


# ---------------- TAKT-SYNC (v13.17) ----------------
# AMY fit=N: das Sample dauert genau N Sequencer-Ticks (48 pro Schlag),
# granularer Time-Stretch, folgt dem Tempo; fit=-1 schaltet ab. Nur fuer
# PCM-Presets im RAM - also genau unsere Slots. fit_search = Suchfenster
# fuer die Grain-Ausrichtung (Frames, 0 = feste Grains).

SYNC_BEATS = [0, 1, 2, 3, 4, 6, 8, 12, 16, 20, 24, 28, 32, 36, 40]
TICKS_PER_BEAT = 48
FIT_OK = True            # wird in pad_synths_init geprueft


def sync_label(b):
    if not b:
        return "AUS"
    if b % 4:
        return "%d SCHL." % b
    n = b // 4
    return "1 TAKT" if n == 1 else "%d TAKTE" % n


SYNC_NAMES = [sync_label(b) for b in SYNC_BEATS]


def slot_play_ms(k):
    # Laenge des geladenen Bereichs (Datei oder RAM-Aufnahme) in ms
    rt = SRT[k]
    if not rt.frames:
        return 0
    i = rt.info
    sr = i["sr"] if isinstance(i, dict) and i["sr"] else 44100
    return rt.frames * 1000 // sr


def sync_suggest(k):
    # Naechster SYNC-Wert zur Laenge beim aktuellen Tempo
    ms = slot_play_ms(k)
    if not ms:
        return 0
    beats = ms * S["tempo"] / 60000.0
    best = 1
    for b in SYNC_BEATS[1:]:
        if abs(b - beats) < abs(best - beats):
            best = b
    return best


# ---------------- SLICES (v13.18) ----------------
# Ein Slot wird in nc gleich lange Stuecke geteilt. Start eines Stuecks
# ueber phase (PCM: Startframe / 2^23, gilt fuer die naechste Note und
# wird von ihr verbraucht), Ende per Note-Off. Mit TAKT-SYNC: fit =
# restliche Ticks ab dem Startpunkt (api.md: "fit has to be the
# REMAINING ticks").

SLICE_COUNTS = [0, 4, 8, 16]
SLICE_NAMES = ["AUS", "4", "8", "16"]
PHASE_FRAMES = 8388608.0  # 2^23


def slot_chops(k):
    sl = slot(k)
    return sl["nc"] if sl["pm"] != 2 else 0


def slot_sync_ticks(k):
    sl = slot(k)
    if FIT_OK and sl["sy"] and sl["pm"] != 2:
        return sl["sy"] * TICKS_PER_BEAT
    return 0


def slice_subs(k):
    # Laenge eines Stuecks in Sequencer-Subs (1 Sub = 2 Ticks)
    nc = slot_chops(k) or 1
    t = slot_sync_ticks(k)
    if t:
        return max(1, t // nc // SUB_TICKS)
    ms = slot_play_ms(k) / nc
    return max(1, int(ms * S["tempo"] / 2500.0))


def _fit_probe(synth):
    global FIT_OK
    try:
        amy.send(synth=synth, osc=0, fit=-1)
        FIT_OK = True
    except Exception as e:
        FIT_OK = False
        print("FIT FEHLT", e)


# ---------------- Synths fuer Pads ----------------
# Je Slot ein Synth (1 Stimme, Neuausloesen schneidet ab = "Choke").
# Bevorzugt 32-39; kennt die Firmware keine Synths ueber 31, bleiben
# 0, 17, 18, 19, 31 (dann haben nur Slot 1-5 Pads).

PAD_SYNTHS = []


def pad_synths_init():
    global PAD_SYNTHS
    hi = list(range(32, 32 + SMP_SLOTS))
    ok = False
    try:
        amy.send(synth=hi[-1], num_voices=1, oscs_per_voice=1)
        ok = bool(amy.get_synth_commands(hi[-1]).strip())
    except Exception as e:
        print("PAD PROBE", e)
    PAD_SYNTHS = hi if ok else [0, 17, 18, 19, 31]
    print("PAD-SYNTHS", PAD_SYNTHS)
    _fit_probe(PAD_SYNTHS[-1])


def pad_synth(k):
    return PAD_SYNTHS[k] if k < len(PAD_SYNTHS) else None


def chrom_ch():
    return S["sb"]["ch"]


def chrom_owns(ch):
    return ch and ch == S["sb"]["ch"]


def _tune_freq(semis):
    # Tonhoehen-Versatz ueber den const-Koeffizienten der Frequenz
    # (in Hz, 0 = kein Versatz): 440 Hz * 2^(st/12) = +st Halbtoene
    if -0.001 < semis < 0.001:
        return 0
    return ZERO_HZ * (2 ** (semis / 12.0))


def _slot_send(synth, k, chrom):
    # Klangparameter eines Slots an einen Synth (ohne Neuladen)
    sl = slot(k)
    semis = sl["tu"] + sl["fi"] / 100.0
    if chrom:
        semis += SMP_ROOT - sl["rt"]
    pm = sl["pm"]
    amy.send(synth=synth, osc=0, wave=PCM_WAVE, preset=SMP_PRESET_BASE + k,
             mode=(PCM_LOOP_FOREVER if pm == 2 else PCM_PLAY_STOP))
    amy.send(synth=synth, osc=0, freq={"const": _tune_freq(semis)})
    amy.send(synth=synth, osc=0, bp0="%d,1,%d,%.3f,%d,0" % (
        sl["at"], sl["de"], sl["su"], sl["re"]))
    ft = sl["ft"]
    amy.send(synth=synth, osc=0, filter_type=SMP_FILT_VALS[ft])
    if ft:
        amy.send(synth=synth, osc=0,
                 filter_freq={"const": sl["cu"], "eg1": sl["fe"]},
                 resonance=sl["rs"], bp1="0,1,%d,0,%d,0" % (sl["fd"], sl["re"]))
    # EINMAL: Note-Offs ignorieren (spielt bis zum Ende)
    amy.send(synth=synth, synth_flags=(2 | 8) if (pm == 0 and not slot_chops(k)) else 8)
    if FIT_OK:
        # TAKT-SYNC: nicht im LOOP-Modus (Loop-Punkte + Stretch ungeklaert)
        sy = sl["sy"] if pm != 2 else 0
        try:
            if sy:
                amy.send(synth=synth, osc=0, fit=sy * TICKS_PER_BEAT,
                         fit_search=sl["fs"])
            else:
                amy.send(synth=synth, osc=0, fit=-1)
        except Exception as e:
            print("FIT", e)


def pad_configure(k, full=True):
    # full: Synth neu anlegen (Bus, Start); sonst nur Klang nachfuehren
    ps = pad_synth(k)
    if ps is None:
        return
    sl = slot(k)
    try:
        if not sl["f"]:
            amy.send(synth=ps, vel=0)
            return
        if full:
            amy.send(synth=ps, num_voices=1, oscs_per_voice=1, bus=sl["bus"])
        _slot_send(ps, k, False)
        amy.send(synth=ps, osc=0, pan=0.5 if S["audio"] == 1 else sl["pan"])
        amy.send(synth=ps, synth_level=sl["lv"])
    except Exception as e:
        print("PAD CFG", k, e)


def chrom_configure(full=True):
    # Wird von configure_channel() fuer den CHROM.-Kanal aufgerufen
    ch = chrom_ch()
    if not ch:
        return
    k = S["sb"]["cs"]
    try:
        if full:
            amy.send(synth=ch, num_voices=S["sb"]["cv"], oscs_per_voice=1, bus=S["bus"][ch])
            _configured.add(ch)
        _slot_send(ch, k, True)
        p = 0.5 if S["audio"] == 1 else S["pan"][ch]
        amy.send(synth=ch, osc=0, pan=p)
        apply_level(ch)
    except Exception as e:
        print("CHROM CFG", e)


def chrom_set(ch):
    # CHROM.-Kanal wechseln: alter Kanal bekommt seinen Patch zurueck
    old = S["sb"]["ch"]
    S["sb"]["ch"] = ch
    if old and old != ch:
        try:
            configure_channel(old)
        except Exception as e:
            print("CHROM REL", e)
    if ch:
        configure_channel(ch)
    refresh_buses()


def slot_refresh(k, full=False):
    # Klangparameter geaendert: Pad und ggf. CHROM.-Kanal neu setzen
    pad_configure(k, full)
    if chrom_ch() and S["sb"]["cs"] == k:
        chrom_configure(full)


def slot_play(k, vel=0.8, sched=False, part=-1):
    # Pad ausloesen (sched=True: im Sequencer-Vorlauf, ueber snd).
    # part >= 0: nur dieses Stueck (SLICES)
    ps = pad_synth(k)
    if ps is None or not SRT[k].ok:
        return False
    send = snd if sched else amy.send
    nc = slot_chops(k)
    if nc:
        # Startpunkt immer mitschicken (auch 0) - eine verbrauchte oder
        # liegengebliebene phase soll nie die naechste Note verschieben
        i = part if 0 <= part < nc else 0
        kw = {"phase": (i * SRT[k].frames // nc) / PHASE_FRAMES}
        t = slot_sync_ticks(k)
        if t:
            kw["fit"] = t * (nc - i) // nc
        send(synth=ps, osc=0, **kw)
    send(synth=ps, note=SMP_ROOT, vel=vel)
    return True


SLICE_TAG0 = 210          # AMY-Tag je Slot fuer das Slice-Ende (v13.19)
SMP_SLICE_NOTE0 = 44      # PAD-KANAL: Note 44 = Slice 1 ... 59 = Slice 16


def slice_play_now(k, pc, vel=0.8):
    # Ein Stueck sofort spielen und nach seiner Laenge beenden (MIDI,
    # Vorhoeren). Ein frueher geplantes Ende desselben Slots wird
    # verworfen, damit es das neue Stueck nicht abschneidet.
    if not slot_play(k, vel, False, pc):
        return False
    t = _seq_ticks()
    ps = pad_synth(k)
    tag = SLICE_TAG0 + k
    try:
        amy.send(ticks="0,0,%d" % tag)
        if t is not None:
            amy.send(synth=ps, note=SMP_ROOT, vel=0,
                     ticks="%d,0,%d" % (t + slice_subs(k) * SUB_TICKS, tag))
    except Exception as e:
        print("SLICE OFF", e)
    return True


def slot_stop(k, sched=False):
    ps = pad_synth(k)
    if ps is None:
        return
    if sched:
        snd(synth=ps, note=SMP_ROOT, vel=0)
    else:
        amy.send(synth=ps, note=SMP_ROOT, vel=0)


def pads_all_off():
    for ps in PAD_SYNTHS:
        try:
            amy.send(synth=ps, vel=0)
        except Exception:
            pass


# ---------------- Laden (schrittweise im Hintergrund) ----------------
#
# Ein Ladeauftrag schickt den Kopf (load_sample) und dann pro
# ui_service()-Durchlauf so viele 94-Frame-Pakete, wie in LOAD_BUDGET_US
# passen - Bedienung und Sequencer laufen weiter. Stereo-Dateien werden
# zu mono gemischt.

LOAD_BUDGET_US = 12000
_load_q = []             # Slots, die (neu) geladen werden sollen
_load_job = None
_load_after = {}         # Slot -> Zeitpunkt (entprelltes Neuladen)
_peek_after_load = None  # Slot, der nach dem Laden vorgehoert wird
RELOAD_SETTLE_MS = 450


def slot_request_load(k, delay=0, audition=False):
    global _peek_after_load
    if delay:
        _load_after[k] = time.ticks_add(now(), delay)
    elif k not in _load_q:
        _load_q.append(k)
    if audition:
        _peek_after_load = k


def slot_loading(k=None):
    if _load_job is None:
        return False
    return k is None or _load_job["k"] == k


def _load_start(k):
    global _load_job
    sl = slot(k)
    rt = SRT[k]
    rt.ok = False
    rt.err = ""
    if not sl["f"]:
        rt.info = None
        try:
            amy.send(load_sample="%d,0" % (SMP_PRESET_BASE + k))
        except Exception:
            pass
        pad_configure(k)
        return
    info = wav_info(smp_path(sl["f"]))
    rt.info = info
    if not isinstance(info, dict):
        rt.err = info
        print("SLOT", k + 1, sl["f"], info)
        return
    st, en = slot_region(k)
    sr = info["sr"]
    f0 = st * sr // 1000
    f1 = min(info["frames"], en * sr // 1000)
    n = max(1, f1 - f0)
    ls = le = 0
    if sl["pm"] == 2:
        a = clamp_int(sl["ls"], st, en) if sl["ls"] else st
        b = clamp_int(sl["le"], a + 1, en) if sl["le"] else en
        ls = max(0, a * sr // 1000 - f0)
        le = min(n - 1, b * sr // 1000 - f0)
        if le <= ls:
            ls, le = 0, 0
    try:
        fh = open(smp_path(sl["f"]), "rb")
        fh.seek(info["off"] + f0 * 2 * info["ch"])
    except Exception as e:
        rt.err = "LESEFEHLER"
        print("SLOT OPEN", e)
        return
    try:
        amy.send(load_sample="%d,%d,%d,%g,%d,%d" % (
            SMP_PRESET_BASE + k, n, sr, SMP_ROOT, ls, le))
    except Exception as e:
        fh.close()
        rt.err = "AMY"
        print("LOAD HEAD", e)
        return
    ch = info["ch"]
    _load_job = {"k": k, "fh": fh, "left": n, "ch": ch, "n": n,
                 "raw": array("h", bytes(SMP_CHUNK * 2 * ch)),
                 "mono": array("h", bytes(SMP_CHUNK * 2))}
    rt.frames = n


def _load_step(budget_us):
    global _load_job, _xfer_lock, _peek_after_load
    j = _load_job
    t0 = time.ticks_us()
    fh = j["fh"]
    raw = j["raw"]
    mono = j["mono"]
    ch = j["ch"]
    try:
        while j["left"] > 0:
            m = SMP_CHUNK if j["left"] > SMP_CHUNK else j["left"]
            ni = m * ch                     # Werte (int16) in diesem Paket
            got = (fh.readinto(memoryview(raw)[:ni]) or 0) // 2
            if got < ni:
                # Datei kuerzer als gedacht: mit Stille auffuellen
                for i in range(got, ni):
                    raw[i] = 0
            if ch == 2:
                for i in range(m):
                    mono[i] = (raw[2 * i] + raw[2 * i + 1]) >> 1
                _xfer_send(_b64(memoryview(mono)[:m]))
            else:
                _xfer_send(_b64(memoryview(raw)[:m]))
            j["left"] -= m
            if budget_us and time.ticks_diff(time.ticks_us(), t0) > budget_us:
                return
    except Exception as e:
        print("LOAD STEP", e)
        SRT[j["k"]].err = "LADEFEHLER"
        j["left"] = 0
    try:
        fh.close()
    except Exception:
        pass
    k = j["k"]
    _load_job = None
    _xfer_lock = False
    if not SRT[k].err:
        SRT[k].ok = True
    slot_refresh(k, True)
    try:
        refresh_buses()
    except Exception:
        pass
    mark_dirty()
    if _peek_after_load == k:
        _peek_after_load = None
        slot_play(k)


def smp_service():
    # Entprelltes Neuladen, Warteschlange, laufende Uebertragung
    global _xfer_lock
    if _nrec["on"] or _nrec["at"] is not None:
        nrec_service()
    if _load_after:
        t = now()
        for k in list(_load_after):
            if time.ticks_diff(t, _load_after[k]) >= 0:
                del _load_after[k]
                if k not in _load_q:
                    _load_q.append(k)
    if _load_job is None and _load_q:
        k = _load_q.pop(0)
        _load_start(k)
        mark_dirty()
    if _load_job is not None:
        if SMP_XFER_SAFE:
            _load_step(LOAD_BUDGET_US)
        else:
            # Ohne markierten Weg darf zwischendurch kein anderer Befehl
            # an AMY gehen: am Stueck laden, Sequencer haelt kurz an
            _xfer_lock = True
            _load_step(0)


def smp_load_all():
    for k in range(SMP_SLOTS):
        if slot(k)["f"]:
            slot_request_load(k)
        else:
            SRT[k].info = None


def slot_assign(k, rel):
    SRT[k].ram = False
    sl = slot(k)
    keep = {key: sl[key] for key in ("bus", "lv", "pan")}
    sl.clear()
    sl.update(new_slot())
    sl.update(keep)
    sl["f"] = rel
    SRT[k].peaks = None
    slot_request_load(k, audition=True)
    request_save()


def slot_clear(k):
    SRT[k].ram = False
    S["sb"]["sl"][k] = new_slot()
    SRT[k].peaks = None
    SRT[k].ok = False
    slot_request_load(k)
    request_save()


def smp_ram_kb():
    return sum([SRT[k].frames * 2 for k in range(SMP_SLOTS) if SRT[k].ok]) // 1024


# ---------------- Wellenform fuer den Editor ----------------
# Je Spalte ein kurzes Fenster aus der Datei lesen (128 Lesezugriffe),
# Spitzenwert 0-1000. Reicht fuer die Uebersicht und ist schnell.

PEAK_COLS = 120


def slot_peaks(k, v0, v1):
    # Spitzen fuer den Ausschnitt v0..v1 (ms) - mit Cache
    rt = SRT[k]
    key = (slot(k)["f"], v0, v1)
    if rt.pkey == key and rt.peaks is not None:
        return rt.peaks
    info = rt.info
    pk = bytearray(PEAK_COLS)
    if isinstance(info, dict):
        sr = info["sr"]
        ch = info["ch"]
        f0 = v0 * sr // 1000
        f1 = max(f0 + PEAK_COLS, v1 * sr // 1000)
        span = (f1 - f0) / PEAK_COLS
        win = int(min(512, max(16, span)))
        buf = array("h", bytes(win * 2 * ch))
        try:
            fh = open(smp_path(slot(k)["f"]), "rb")
            for c in range(PEAK_COLS):
                fr = f0 + int(c * span)
                if fr >= info["frames"]:
                    break
                fh.seek(info["off"] + fr * 2 * ch)
                got = (fh.readinto(buf) or 0) // 2
                if got <= 0:
                    break
                for i in range(got, len(buf)):
                    buf[i] = 0
                # Spitze ueber beide Kanaele (eingebaut, schnell)
                p = max(max(buf), -min(buf))
                pk[c] = min(255, p >> 7)
            fh.close()
        except Exception as e:
            print("PEAKS", e)
    rt.peaks = pk
    rt.pkey = key
    return pk


# ---------------- Aufnahme ----------------

_rec_state = {"run": False, "gaps": 0, "last": "", "peak": -1, "blk": 0}


def _rec_frames():
    s = S["sb"]
    if s["unit"] == 1:
        # Takte (4/4) beim aktuellen Tempo
        ms = s["len"] * 4 * 60000 // max(20, S["tempo"])
    else:
        ms = s["len"] * 1000
    return min(SMP_MAX_MS, ms) * 44100 // 1000


SMP_SRC_AMY = (2, 1)     # LINE -> AUDIO_IN, MIX -> Ausgang
_nrec = {"on": False, "k": 0, "until": 0, "at": None, "frames": 0, "t0": 0}


def nrec_start():
    s = S["sb"]
    k = s["rs"]
    if _nrec["on"] or _nrec["at"] is not None:
        nrec_stop()
        return
    if _load_job is not None and _load_job["k"] == k:
        toast("AUFNAHME", "LAEDT NOCH", 1500)
        return
    _load_after.pop(k, None)
    if k in _load_q:
        _load_q.remove(k)
    _nrec["k"] = k
    _nrec["frames"] = _rec_frames()
    if s["rst"] and S["run"] and _origin is not None:
        t = _seq_ticks()
        if t is not None:
            bar = 192
            _nrec["at"] = _origin + ((t - _origin) // bar + 1) * bar
            toast("AUFNAHME", "WARTE AUF TAKT 1", 1500)
            mark_dirty()
            return
    _nrec_go()


def _nrec_go():
    s = S["sb"]
    k = _nrec["k"]
    _nrec["at"] = None
    frames = _nrec["frames"]
    try:
        slot_stop(k)
        amy.send(start_sample="%d,%d,%d,%d,0,0" % (
            SMP_PRESET_BASE + k, SMP_SRC_AMY[s["src"]], frames, SMP_ROOT))
    except Exception as e:
        print("NREC", e)
        toast("AUFNAHME", "AMY FEHLER", 2000)
        return
    sl = slot(k)
    keep = {key: sl[key] for key in ("bus", "lv", "pan")}
    sl.clear()
    sl.update(new_slot())
    sl.update(keep)
    if s["unit"] == 1 and s["len"] * 4 in SYNC_BEATS:
        sl["sy"] = s["len"] * 4          # Takt-Aufnahme bleibt im Takt
    rt = SRT[k]
    rt.info = None
    rt.peaks = None
    rt.err = ""
    rt.ok = False
    rt.ram = True
    rt.frames = frames
    _nrec["on"] = True
    _nrec["t0"] = now()
    _nrec["until"] = time.ticks_add(now(), frames * 1000 // 44100 + 150)
    request_save()
    mark_dirty()


def nrec_stop():
    if _nrec["at"] is not None:
        _nrec["at"] = None
        toast("AUFNAHME", "ABGEBROCHEN")
        mark_dirty()
        return
    if not _nrec["on"]:
        return
    try:
        amy.send(stop_sample=1)
    except Exception as e:
        print("NREC STOP", e)
    _nrec_done(True)


def _nrec_done(early=False):
    k = _nrec["k"]
    _nrec["on"] = False
    rt = SRT[k]
    rt.ok = True
    # tatsaechlich aufgenommene Frames (bei vorzeitigem Stopp kuerzer)
    fr = _nrec["frames"]
    if early:
        fr = min(fr, since(_nrec["t0"]) * 44100 // 1000)
    rt.frames = max(1, fr)
    slot_refresh(k, True)
    try:
        refresh_buses()
    except Exception:
        pass
    if S["sb"]["asv"] and smp_can_store():
        slot_store(k)
    else:
        toast("S%d IN RAM" % (k + 1), "NICHT AUF SD!", 2500)
    mark_dirty()


# ---------------- Aufnahme auf SD speichern (v13.14) ----------------
# tulip.store_sample(preset, pfad, frames=n) schreibt ein PCM-Preset als
# WAV (ab AMYboard-Firmware PR 1399, Hinweis von bwhitman im Discord).
# Waehrend des Schreibens teilen sich SD-Karte und Sample-RAM einen
# SPI-Bus - der Ton kann kurz stocken. Darum erst NACH der Aufnahme.

def _store_fn():
    return getattr(tulip, "store_sample", None) if tulip is not None else None


def smp_can_store():
    return _store_fn() is not None and sd_present()


def _rec_next_name():
    try:
        os.mkdir(SMP_DIR)
    except Exception:
        pass
    try:
        names = os.listdir(SMP_DIR)
    except Exception:
        names = []
    n = 1
    for nm in names:
        u = nm.upper()
        if u.startswith("REC") and u.endswith(".WAV"):
            try:
                n = max(n, int(u[3:-4]) + 1)
            except Exception:
                pass
    return "samples/REC%03d.wav" % n


def slot_store(k):
    # RAM-Aufnahme eines Slots als WAV auf die Karte schreiben
    fn = _store_fn()
    rt = SRT[k]
    if fn is None:
        toast("SPEICHERN", "FIRMWARE ZU ALT", 2500)
        return False
    if not rt.ram or not rt.ok:
        return False
    rel = _rec_next_name()
    toast("SPEICHERE S%d" % (k + 1), rel[-10:], 8000)
    render(force=True)
    gc.collect()
    try:
        fn(SMP_PRESET_BASE + k, smp_path(rel), frames=rt.frames)
    except TypeError:
        try:
            fn(SMP_PRESET_BASE + k, smp_path(rel))
        except Exception as e:
            print("STORE", repr(e))
            toast("SPEICHERN", "FEHLER " + _err_txt(e)[:6], 2500)
            return False
    except Exception as e:
        print("STORE", repr(e))
        toast("SPEICHERN", "FEHLER " + _err_txt(e)[:6], 2500)
        return False
    info = wav_info(smp_path(rel))
    if not isinstance(info, dict):
        toast("SPEICHERN", "DATEI " + str(info)[:8], 2500)
        return False
    # Slot zeigt jetzt auf die Datei. Das Preset bleibt geladen (kein
    # Neuladen noetig); Trimmen laedt spaeter aus der Datei.
    slot(k)["f"] = rel
    rt.ram = False
    rt.info = info
    rt.peaks = None
    request_save()
    toast("S%d GESPEICHERT" % (k + 1), smp_short(rel), 2500)
    mark_dirty()
    return True


def nrec_service(tick=None):
    # Start auf Takt 1 (aus dem Sequencer-Takt) und Ende der Aufnahme
    if _nrec["at"] is not None:
        t = tick if tick is not None else _seq_ticks()
        if t is not None and t >= _nrec["at"]:
            _nrec_go()
        elif not S["run"]:
            _nrec_go()
    if _nrec["on"]:
        if time.ticks_diff(now(), _nrec["until"]) >= 0:
            _nrec_done()
        else:
            mark_dirty()                  # Fortschritt anzeigen


def nrec_progress():
    if not _nrec["on"]:
        return 0.0
    tot = _nrec["frames"] * 1000 // 44100 or 1
    return clamp(since(_nrec["t0"]) / tot, 0.0, 1.0)


def _peak16(b, step=8):
    # Spitzenpegel 0-32767 eines Blocks. MicroPython kann bei array kein
    # a[::step] - daher max()/min() ueber das ganze array (v13.12)
    try:
        a = array("h", bytes(b))
        return max(max(a), -min(a))
    except Exception:
        return 0


# ---------------- Aufnahme-Test (v13.10) ----------------

def rec_test():
    # 2 s nur abholen und zaehlen - zeigt, was die Firmware liefert
    s = S["sb"]
    name = "get_output_buffer" if s["src"] == 1 else "get_input_buffer"
    getbuf = getattr(amy, name, None)
    res = [("QUELLE", SMP_SRC_NAMES[s["src"]])]
    if getbuf is None:
        res.append(("FUNKTION", "FEHLT"))
        return res
    calls = nones = new = same = 0
    size = 0
    peak = 0
    last = None
    t0 = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < 2000:
        b = getbuf()
        calls += 1
        if b is None:
            nones += 1
            continue
        if b != last:
            new += 1
            size = len(b)
            if not (new & 3):
                p = _peak16(b, 2)
                if p > peak:
                    peak = p
            last = b
        else:
            same += 1
    blk_frames = size // 4 if size else 0
    expect = 2 * 44100 // blk_frames if blk_frames else 0
    res += [("AUFRUFE", "%d" % calls), ("NONE", "%d" % nones),
            ("NEUE BLOECKE", "%d" % new), ("ERWARTET", "%d" % expect),
            ("GLEICHE", "%d" % same), ("BYTES/BLOCK", "%d" % size),
            ("PEGEL", "%d%%" % (peak * 100 // 32767)),
            ("RAM FREI", _free_mem())]
    # SD-Schreibzeit fuer 1 KB (die verliert die Aufnahme sonst)
    t1 = time.ticks_ms()
    try:
        f = open(SD_ROOT + "/.rectest", "wb")
        for _ in range(16):
            f.write(bytes(1024))
        f.close()
        os.remove(SD_ROOT + "/.rectest")
        res.append(("SD 16KB", "%dms" % time.ticks_diff(time.ticks_ms(), t1)))
    except Exception as e:
        res.append(("SD 16KB", _err_txt(e)[:8]))
    return res

# ================================================================
# DX7-BAENKE VON SD (v13.19)
# ================================================================
# .SYX-Dateien (32er-Bank oder Einzelstimme) aus /sd/dx7/ oder dem
# Hauptverzeichnis. fm.load_syx(daten, voice, patch=n) wandelt eine
# Stimme und legt sie als AMY-User-Patch n ab (fm.py, AMY seit 08/2026).
# Jeder Kanal hat seinen eigenen User-Patch 1024 + Kanal.

SYX_DIR = SD_ROOT + "/dx7"
_fm_mod = None
_syx_done = {}           # Kanal -> (Datei, Stimme), die AMY gerade kennt
_syx_names = [None, None]


def fm_mod():
    global _fm_mod
    if _fm_mod is None:
        m = False
        try:
            from amy import fm as m
        except Exception:
            try:
                import fm as m
            except Exception as e:
                print("FM FEHLT", e)
        _fm_mod = m
    return _fm_mod or None


def syx_list_files():
    out = []
    for d in (SYX_DIR, SD_ROOT):
        try:
            names = os.listdir(d)
        except Exception:
            continue
        for n in names:
            if n.lower().endswith(".syx") and not n.startswith("."):
                out.append(n if d == SD_ROOT else "dx7/" + n)
    out.sort()
    return out


def _syx_read(rel):
    f = open(smp_path(rel), "rb")
    try:
        return f.read()
    finally:
        f.close()


def syx_names(rel):
    if _syx_names[0] == rel:
        return _syx_names[1]
    fm = fm_mod()
    names = []
    if fm is not None:
        try:
            names = [str(n).strip() or "?" for n in fm.syx_names(_syx_read(rel))]
        except Exception as e:
            print("SYX NAMEN", e)
    gc.collect()
    _syx_names[0] = rel
    _syx_names[1] = names
    return names


def syx_install(ch):
    # Stimme des Kanals als User-Patch ablegen. Scheitert es: DX7-Patch 128
    e = S["syx"][ch]
    fm = fm_mod()
    try:
        if fm is None:
            raise OSError("fm.py fehlt")
        fm.load_syx(_syx_read(e[0]), voice=e[1], patch=USER_BASE + ch)
        _syx_done[ch] = (e[0], e[1])
        gc.collect()
        return True
    except Exception as ex:
        print("SYX LADEN", ch, ex)
        toast("DX7 K%d" % ch, "NICHT GELADEN", 1800)
        S["syx"][ch] = None
        S["pat"][ch] = 128
        _syx_done.pop(ch, None)
        return False


def set_syx_patch(ch, rel, voice, name):
    reset_tone(ch)
    if S["pat"][ch] != USER_BASE + ch:
        S["vo"][ch] = clamp_int(default_voices(128, ch), 1, voices_allowed(ch))
    S["syx"][ch] = [rel, voice, name]
    S["pat"][ch] = USER_BASE + ch
    _syx_done.pop(ch, None)
    request_configure(ch)


# ================================================================
# WLAN (Zugangsdaten nur auf der SD-Karte, Klartext)
# ================================================================

WEBREPL_PASSWORD = "amyboard"
wlan_connected = False
wlan_ip = None


def wifi_save(ssid, pw):
    if not sd_present():
        return False
    try:
        f = open(WLAN_CRED_FILE, "w")
        f.write("ssid:%s\npassword:%s\n" % (ssid, pw))
        f.close()
        return True
    except Exception as e:
        print("WLAN SAVE", e)
        return False


def wifi_load():
    if not sd_present():
        return None, None
    ssid = pw = None
    try:
        f = open(WLAN_CRED_FILE, "r")
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("ssid:"):
                ssid = line[5:]
            elif line.startswith("password:"):
                pw = line[9:]
        f.close()
    except Exception:
        pass
    return ssid, pw


def wifi_connect():
    global wlan_connected, wlan_ip
    ssid, pw = wifi_load()
    if not ssid:
        return False
    try:
        ip = amyboard.wifi(ssid, pw)
    except Exception as e:
        print("WLAN", e)
        ip = None
    wlan_ip = ip
    wlan_connected = bool(ip)
    if wlan_connected:
        try:
            import webrepl
            webrepl.start(password=WEBREPL_PASSWORD)
        except Exception as e:
            print("WEBREPL", e)
    return wlan_connected


def wifi_disconnect():
    global wlan_connected, wlan_ip
    try:
        import network
        network.WLAN(network.STA_IF).disconnect()
    except Exception as e:
        print("WLAN OFF", e)
    wlan_connected = False
    wlan_ip = None


# ================================================================
# SEQUENCER: 4 Spuren + 303-Spur + Drum-Spur
# ================================================================
#
# Takt (v12.11): tulip.seq_add_callback ruft _seq_cb alle 2 AMY-Ticks
# (48 PPQ) - ein "Sub" = 2 Ticks, 3 Subs = eine 32tel. Ohne diese
# Funktion laeuft der Sequencer wie bisher in loop(tick) (jede 32tel).
# Gezaehlt wird ab START (Ursprung), nicht ab Boot - START beginnt also
# immer bei Step 1. Noten werden direkt mit amy.send(synth=, note=,
# vel=) ausgeloest (AMYs Scheduler mit synth= brachte in v2 keinen Ton).
#
# Neu in v12:
#   - 4 Patterns (A-D) pro Spur, Wechsel am Ende des Durchlaufs
#   - Wahrscheinlichkeit pro Step (Werte 1-4 = 25-100 %)
#   - Swing (0-100) fuer ungerade Steps - wirkt im 32tel-Raster:
#     bei 1/16 ab 50 als starker Shuffle, bei 1/8 und 1/4 feiner
#   - Modus ARP: spielt die auf "ARP EIN" gehaltenen Tasten,
#     AUF/AB/AUFAB/ZUFALL, 1-3 Oktaven, LATCH
#   - Acid-Generator und Mutation fuer die 303
# Neu in v12.6:
#   - Drum-Spur: 8 Instrumente, Velocity 1-15 pro Step, eigene
#     Laenge pro Instrument, Pattern-Wechsel nach 16 Steps

SEQ_DIV_NAMES = ["1/32", "1/16", "1/8", "1/4"]
SUB_TICKS = 2            # 1 Sub = 2 AMY-Ticks
SUB_PER_32 = 3
SEQ_DIV_SUB = [3, 6, 12, 24]   # Step-Laenge in Subs (1/32 .. 1/4)
SEQ_MODES = ["MANUAL", "EUCLID", "SKALA", "ARP"]
ARP_DIRS = ["AUF", "AB", "AUFAB", "ZUFALL"]
SEQ_OUT_NAMES = ["INTRN", "MIDI", "BEIDE"]
SEQ_CLOCK_NAMES = ["INTERN", "SENDEN", "FOLGEN"]
PATTERN_NAMES = ["A", "B", "C", "D"]
SEQ_MIDI_SYNTH_BASE = 22
ACID_SYNTH = 26
ACID_MIDI_SYNTH = 27
DRUM_MIDI_SYNTH = 28     # HW-TEST: MIDI-Ausgabe der Drum-Spur
SEQ_MIDI_VEL = 100 / 127.0
_seq_midi_native = hasattr(amy, "NOTE_OUTPUT_MIDI_OUT")

ACID_NOTE_LABELS = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#",
                    "A", "A#", "B", "C'")
ACID_WAVE_NAMES = ["SAW", "SQR"]
ACID_VEL = 0.7
ACID_ACC_OCT = 2.5
ACID_CUT_MIN = 60.0
ACID_CUT_MAX = 8000.0
ACID_GATE_ACC_VOLTS = 8.0
ACID_BP0 = "2,1,20,0"
ACID_FILTER_TYPE = getattr(amy, "FILTER_LPF24", 4)

DRUM_BAR = 16            # Pattern-Wechsel alle 16 Steps (1 Takt bei 1/16)
DRUM_GATE_SUB = 6        # Note-Off nach 2 x 1/32
TRIG_GAP_US = 1000       # Low-Luecke beim Neuausloesen eines CV-Triggers
DRUM_VEL_CYCLE = (0, 15, 10, 6)   # Druecken: AUS -> 100 -> 67 -> 40 % -> AUS


class RT:
    # Laufzeitzustand einer Spur (wird nicht gespeichert)
    def __init__(self, idx, midi_synth):
        self.idx = idx
        self.midi_synth = midi_synth
        self.active = None
        self.active_ch = None
        self.off_at = 0
        self.midi_open = None
        self.midi_ready = None
        self.arp_i = 0
        self.pending = None
        self.step = -1
        self.rows = None      # Drum-Spur: aktueller Step je Instrument
        self.offs = []        # Drum-Spur: offene Noten (kanal, note, midi)
        self.trig_off = [0, 0]      # Drum-Trigger: Ende je CV OUT (Sub)
        self.poffs = []       # Drum-Spur: offene Pads (Slot, Ende-Sub)
        self.trig_hi = [False, False]


ACID = 4
DRUM = 5
RTS = ([RT(i, SEQ_MIDI_SYNTH_BASE + i) for i in range(4)]
       + [RT(ACID, ACID_MIDI_SYNTH), RT(DRUM, DRUM_MIDI_SYNTH)])


def trk_cfg(i):
    if i == ACID:
        return S["acid"]
    if i == DRUM:
        return S["drm"]
    return S["trk"][i]


def euclid_hit(i, steps, pulses):
    if pulses <= 0:
        return False
    if pulses >= steps:
        return True
    return ((i + 1) * pulses) // steps != (i * pulses) // steps


# ---------------- ARP: gehaltene Tasten ----------------

_held = {}
_latched = {}


def arp_note(ch, note, on):
    use = False
    latch = False
    for t in S["trk"]:
        if t["mode"] == 3 and t["ain"] == ch:
            use = True
            if t["latch"]:
                latch = True
    if not use:
        return
    h = _held.setdefault(ch, [])
    if on:
        if latch:
            lt = _latched.setdefault(ch, [])
            if not h:
                del lt[:]      # neue Handhaltung ersetzt die gelatchten Noten
            if note not in lt:
                lt.append(note)
        if note not in h:
            h.append(note)
    elif note in h:
        h.remove(note)


def arp_clear(ch=None):
    if ch is None:
        _held.clear()
        _latched.clear()
    else:
        _latched.pop(ch, None)


def arp_pick(t, rt):
    src = _latched.get(t["ain"]) if t["latch"] else _held.get(t["ain"])
    if not src:
        return None
    base = sorted(src)
    seq = []
    for o in range(t["aoct"]):
        for n in base:
            seq.append(n + 12 * o)
    n_ = len(seq)
    i = rt.arp_i
    rt.arp_i += 1
    d = t["adir"]
    if d == 0:
        n = seq[i % n_]
    elif d == 1:
        n = seq[n_ - 1 - (i % n_)]
    elif d == 2:
        if n_ < 2:
            n = seq[0]
        else:
            per = 2 * n_ - 2
            k = i % per
            n = seq[k] if k < n_ else seq[per - k]
    else:
        n = seq[rnd(n_)]
    return clamp_int(n, 0, 127)


def step_note(t, rt, i):
    m = t["mode"]
    if m == 0:
        v = t["pats"][t["pat"]][i]
        if v <= 0:
            return None
        if v < 4 and rnd(4) >= v:
            return None
        return t["note"]
    if m == 1:
        if not euclid_hit(i, t["steps"], t["pul"]):
            return None
        return scale_note(t["note"], i, t["scale"])
    if m == 2:
        return scale_note(t["note"], i, t["scale"])
    return arp_pick(t, rt)


# ---------------- Zeitplanung (v12.12) ----------------
#
# Die Spuren werden VORLAUF ms im Voraus berechnet. Alles, was AMY
# spielt, bekommt ticks="<Tick>,0,SEQ_TAG": AMY speichert die Nachricht
# und spielt sie, sobald ihr Sequencer diesen Tick erreicht (im
# Audio-Block, unabhaengig von Python). Mit eigenem Tag, damit STOP alle
# noch offenen Ereignisse auf einmal loeschen kann. Was AMY nicht planen
# kann (tulip.midi_out, CV per I2C, Anzeige), kommt in _defer und wird
# im Sequencer-Callback ausgefuehrt, sobald der Tick erreicht ist.

SEQ_TAG = 201
_sched = None            # AMY-Tick des gerade berechneten Subs (None = sofort)
_late_tick = -1          # Noten mit Tick < diesem Wert sind zu spaet
_defer = []              # [Tick, Funktion, Argumente] in Zeitfolge


def snd(**kw):
    if _sched is not None:
        if _sched < _late_tick and kw.get("vel"):
            # zu spaet berechnet: lieber auslassen als neben dem Raster
            # spielen (Note-Offs gehen immer raus)
            MEAS["drop"] += 1
            return
        kw["ticks"] = "%d,0,%d" % (_sched, SEQ_TAG)
    amy.send(**kw)


def snd_at(tick, **kw):
    if tick is not None:
        kw["ticks"] = "%d,0,%d" % (tick, SEQ_TAG)
    amy.send(**kw)


def later(fn, *args):
    if _sched is None:
        fn(*args)
    else:
        _defer.append((_sched, fn, args))


def run_deferred(tick):
    n = 0
    for e in _defer:
        if e[0] > tick:
            break
        n += 1
        try:
            e[1](*e[2])
        except Exception as ex:
            print("DEFER", ex)
    if n:
        del _defer[:n]


def _midi_raw(msg):
    if tulip is not None:
        tulip.midi_out(msg)


def _set_step(rt, i):
    rt.step = i


def _set_rows(rt, b, rows):
    rt.step = b
    rt.rows = rows


# ---------------- Ausgabe MIDI ----------------

def _midi_setup(t, rt):
    global _seq_midi_native
    if not _seq_midi_native or rt.midi_ready == t["mch"]:
        return
    try:
        amy.send(synth=rt.midi_synth, note_output="%d,%d" % (NOTE_OUTPUT_MIDI_OUT, t["mch"]))
        rt.midi_ready = t["mch"]
    except Exception as e:
        print("SEQ MIDI", e)
        _seq_midi_native = False


def _midi_off_raw(rt, target, note):
    if target is None or note is None:
        return
    if target == rt.midi_synth:
        snd(synth=rt.midi_synth, note=note, vel=0)
    elif tulip is not None:
        later(_midi_raw, [0x80 | (target - 1), note, 0])


def seq_midi(t, rt, note, on, vel=SEQ_MIDI_VEL):
    if on:
        if t["out"] not in (1, 2):
            return
        if _seq_midi_native:
            _midi_setup(t, rt)
            snd(synth=rt.midi_synth, note=note, vel=vel)
            rt.midi_open = rt.midi_synth
        elif tulip is not None:
            later(_midi_raw, [0x90 | (t["mch"] - 1), note, clamp_int(vel * 127, 1, 127)])
            rt.midi_open = t["mch"]
    else:
        _midi_off_raw(rt, rt.midi_open, note)
        rt.midi_open = None


# ---------------- Spuren 1-4 ----------------

def _note_out(t, rt, ch, note, on):
    if on:
        if t["out"] in (0, 2):
            snd(synth=ch, note=note, vel=1)
    else:
        snd(synth=ch, note=note, vel=0)
    seq_midi(t, rt, note, on)
    if midicv_active_for(ch):
        later(midicv_note, note, on)


def _track_off(t, rt):
    if rt.active is None:
        return
    try:
        _note_out(t, rt, rt.active_ch, rt.active, False)
    except Exception as e:
        print("SEQ OFF", e)
    rt.active = None
    rt.active_ch = None


def _swing_off(L, i):
    # L = Step-Laenge in Subs. Ungerade Steps rutschen um bis zu L/2
    # nach hinten (100 % = eine halbe Step-Laenge, wie bisher).
    if not (i & 1):
        return 0
    return (S["swing"] * (L // 2) + 50) // 100


def _track_tick(t, rt, s):
    if rt.active is not None and s >= rt.off_at:
        _track_off(t, rt)
    L = SEQ_DIV_SUB[t["div"]]
    pos = s % (t["steps"] * L)
    i = pos // L
    if pos - i * L != _swing_off(L, i):
        return
    if i == 0 and rt.pending is not None:
        t["pat"] = rt.pending
        rt.pending = None
    later(_set_step, rt, i)
    if t["mute"]:
        return
    note = step_note(t, rt, i)
    if note is None:
        return
    if rt.active is not None:
        _track_off(t, rt)
    try:
        _note_out(t, rt, t["ch"], note, True)
    except Exception as e:
        print("SEQ ON", e)
        return
    rt.active = note
    rt.active_ch = t["ch"]
    g = t["gate"] // SUB_TICKS          # Gate in AMY-Ticks -> Subs
    rt.off_at = s + (g if g > 0 else 1)


# ---------------- 303-Spur ----------------

_acid_ready = False
_acid_acc_applied = None
_acid_gate_v = 0.0


def acid_wave_const():
    if S["acid"]["wave"] == 1:
        return getattr(amy, "PULSE", 1)
    return getattr(amy, "SAW_DOWN", 2)


# ---------------- Joystick > 303 (v12.15) ----------------
ACID_JOY_TARGETS = ["AUS", "CUTOFF", "RESO", "ENV MOD", "DECAY", "ACCENT",
                    "SLIDE", "TRANSP", "DICHTE", "DRIVE"]
_acid_mod = {}           # Ziel-Index -> Auslenkung -1..+1 (0 = Ruhe)
_acid_joy_next = 0
ACID_JOY_DEAD = 0.08


def _jm(t):
    return _acid_mod.get(t, 0.0)


def acid_val(k):
    # gespeicherter Wert + Joystick-Auslenkung
    a = S["acid"]
    v = a[k]
    if not _acid_mod:
        return v
    if k == "cut":
        o = _jm(1)
        return clamp(v * (2 ** (3.0 * o)), ACID_CUT_MIN, ACID_CUT_MAX) if o else v
    if k == "reso":
        return clamp(v + 3.0 * _jm(2), 0.5, 8.0)
    if k == "env":
        return clamp(v + 3.5 * _jm(3), 0.0, 7.0)
    if k == "dec":
        o = _jm(4)
        return clamp_int(v * (2 ** (1.5 * o)), 30, 2500) if o else v
    if k == "acc":
        return clamp(v + 0.6 * _jm(5), 0.0, 1.0)
    if k == "slide":
        o = _jm(6)
        return clamp_int(v * (2 ** (1.5 * o)), 10, 500) if o else v
    if k == "tune":
        return clamp_int(v + int(round(12 * _jm(7))), -24, 24)
    if k == "dd":
        o = _jm(9)
        return clamp(v * (2 ** (2.0 * o)), DIST_DRIVE_MIN, DIST_DRIVE_MAX) if o else v
    return v


def acid_density_skip(acc):
    # DICHTE nach unten: Noten ohne Accent zuerst weglassen
    o = _jm(8)
    if o >= 0:
        return False
    p = int(-o * 100)
    if acc:
        p = p // 2
    return rnd(100) < p


def acid_bp1():
    return "0,1,%d,0,10,0" % int(acid_val("dec"))


def acid_eg(acc):
    return acid_val("env") + (ACID_ACC_OCT * acid_val("acc") if acc else 0.0)


def acid_apply_filter():
    global _acid_acc_applied
    if not _acid_ready:
        return
    a = S["acid"]
    try:
        amy.send(synth=ACID_SYNTH, osc=0,
                 filter_freq="%.1f,0,0,0,%.3f" % (acid_val("cut"), acid_eg(False)),
                 resonance=acid_val("reso"))
        _acid_acc_applied = False
    except Exception as e:
        print("ACID FILTER", e)


def _acid_set_accent(acc):
    global _acid_acc_applied
    if acc == _acid_acc_applied:
        return
    try:
        snd(synth=ACID_SYNTH, osc=0, filter_freq=",,,,%.3f" % acid_eg(acc))
        _acid_acc_applied = acc
    except Exception as e:
        print("ACID ACC", e)


def acid_apply(what):
    if not _acid_ready:
        return
    a = S["acid"]
    try:
        if what == "filter":
            acid_apply_filter()
        elif what == "dec":
            amy.send(synth=ACID_SYNTH, osc=0, bp1=acid_bp1())
        elif what == "wave":
            amy.send(synth=ACID_SYNTH, osc=0, wave=acid_wave_const())
        elif what == "lvl":
            amy.send(synth=ACID_SYNTH, synth_level=a["lvl"])
        elif what == "slide":
            amy.send(synth=ACID_SYNTH, portamento=int(acid_val("slide")))
        elif what == "dist":
            if DIST_OK:
                # Joystick DRIVE wirkt auch bei TYP AUS nicht (bewusst)
                amy.send(synth=ACID_SYNTH, osc=0,
                         **dist_args(a["dt"], acid_val("dd"), a["dm"]))
    except Exception as e:
        print("ACID", what, e)


def acid_setup():
    global _acid_ready
    try:
        amy.send(synth=ACID_SYNTH, num_voices=1, oscs_per_voice=1, wave=acid_wave_const())
        _acid_ready = True
        amy.send(synth=ACID_SYNTH, osc=0, filter_type=ACID_FILTER_TYPE)
        acid_apply_filter()
        amy.send(synth=ACID_SYNTH, osc=0, bp0=ACID_BP0)
        amy.send(synth=ACID_SYNTH, osc=0, bp1=acid_bp1())
        acid_apply("slide")
        acid_apply("lvl")
        acid_apply("dist")
    except Exception as e:
        print("ACID SETUP", e)


def acid_cv_active():
    return _eur_mode == EUR_ACID_CV


def acid_cv_reset():
    global _acid_gate_v
    _acid_gate_v = 0.0


def _acid_gate(v):
    global _acid_gate_v
    if v != _acid_gate_v:
        cv_write(1, v)
        _acid_gate_v = v


def _acid_on(rt, note, acc, legato):
    a = S["acid"]
    old = rt.active
    if legato and old == note:
        if acid_cv_active() and a["cvacc"]:
            later(_acid_gate, ACID_GATE_ACC_VOLTS if acc else CV_GATE_VOLTS)
        return
    vel = ACID_VEL + (1.0 - ACID_VEL) * a["acc"] if acc else ACID_VEL
    if a["out"] in (0, 2) and _acid_ready:
        _acid_set_accent(acc)
        snd(synth=ACID_SYNTH, note=note, vel=vel)
    if a["out"] in (1, 2):
        prev = rt.midi_open if legato else None
        if legato:
            rt.midi_open = None
        seq_midi(a, rt, note, True, vel)
        if prev is not None:
            _midi_off_raw(rt, prev, old)
    if acid_cv_active():
        later(cv_write, 0, cv_pitch(note))
        later(_acid_gate, ACID_GATE_ACC_VOLTS if (acc and a["cvacc"]) else CV_GATE_VOLTS)


def _acid_off(rt):
    note = rt.active
    rt.active = None
    rt.off_at = 0
    if note is None:
        return
    try:
        if _acid_ready:
            snd(synth=ACID_SYNTH, note=note, vel=0)
        seq_midi(S["acid"], rt, note, False)
    except Exception as e:
        print("ACID OFF", e)
    if acid_cv_active():
        later(_acid_gate, 0.0)


def _acid_tick(rt, s):
    a = S["acid"]
    if rt.active is not None and rt.off_at and s >= rt.off_at:
        _acid_off(rt)
    L = SEQ_DIV_SUB[1]
    pos = s % (a["steps"] * L)
    i = pos // L
    if pos - i * L != _swing_off(L, i):
        return
    if i == 0 and rt.pending is not None:
        a["pat"] = rt.pending
        rt.pending = None
    later(_set_step, rt, i)
    if a["mute"]:
        return
    st = a["pats"][a["pat"]][i]
    if st[0] < 0:
        if rt.active is not None:
            _acid_off(rt)
        return
    if _acid_mod and acid_density_skip(st[2]):
        if rt.active is not None:
            _acid_off(rt)
        return
    note = clamp_int(a["root"] + st[0] + 12 * st[1] + acid_val("tune"), 0, 127)
    legato = rt.active is not None
    try:
        _acid_on(rt, note, st[2], legato)
    except Exception as e:
        print("ACID ON", e)
        return
    rt.active = note
    rt.off_at = 0 if st[3] else s + SUB_PER_32


# Acid-Generator: Moll-Pentatonik + Oktave, Pausen, Accent, Slide
_GEN_DEGREES = (0, 0, 0, 3, 5, 7, 7, 10, 12)


def _gen_step():
    if rnd(100) < 18:
        return [-1, 0, 0, 0]
    o = 0
    r = rnd(10)
    if r == 0:
        o = -1
    elif r == 9:
        o = 1
    return [_GEN_DEGREES[rnd(len(_GEN_DEGREES))], o,
            1 if rnd(100) < 28 else 0, 1 if rnd(100) < 20 else 0]


def acid_generate():
    a = S["acid"]
    a["pats"][a["pat"]] = [_gen_step() for _ in range(ACID_STEPS_MAX)]
    request_save()


def acid_mutate():
    a = S["acid"]
    pat = a["pats"][a["pat"]]
    for _ in range(3):
        pat[rnd(a["steps"])] = _gen_step()
    request_save()


# ---------------- Drum-Spur ----------------
#
# Jedes Instrument laeuft mit eigener Laenge ueber denselben Takt
# (Polymetrik: HiHat mit 12 Steps gegen Bassdrum mit 16). Swing
# folgt dem gemeinsamen Raster, damit alle Instrumente zusammen
# swingen. Intern spielt die Spur auf ihrem Kanal (ab Werk 10,
# Drumkit), per MIDI z.B. die TR-8S.

def drm_get(k, s):
    d = S["drm"]
    return int(d["pats"][d["pat"]][k][s], 16)


def drm_set(k, s, v):
    d = S["drm"]
    pat = d["pats"][d["pat"]]
    row = pat[k]
    pat[k] = row[:s] + HEX_DIGITS[clamp_int(v, 0, 15)] + row[s + 1:]
    request_save()


def drum_euclid(k, pulses):
    d = S["drm"]
    n = d["lens"][k]
    pat = d["pats"][d["pat"]]
    new = "".join(["f" if euclid_hit(i, n, pulses) else "0" for i in range(n)])
    pat[k] = new + pat[k][n:]
    request_save()


def drum_clear_row(k):
    d = S["drm"]
    d["pats"][d["pat"]][k] = DRUM_EMPTY
    request_save()


def _drum_midi(d, rt, note, vel127):
    # vel127 = 0 -> Note-Off
    if _seq_midi_native:
        _midi_setup(d, rt)
    if _seq_midi_native:
        snd(synth=rt.midi_synth, note=note, vel=vel127 / 127.0)
    elif tulip is not None:
        if vel127:
            later(_midi_raw, [0x90 | (d["mch"] - 1), note, vel127])
        else:
            later(_midi_raw, [0x80 | (d["mch"] - 1), note, 0])


def _drum_offs(d, rt):
    offs = rt.offs
    rt.offs = []
    rt.off_at = 0
    for ch, note, ext in offs:
        try:
            if ch:
                snd(synth=ch, note=note, vel=0)
            if ext:
                _drum_midi(d, rt, note, 0)
        except Exception as e:
            print("DRUM OFF", e)


# ---------------- Drum-Trigger auf CV OUT ----------------
#
# Ein Instrument pro Ausgang loest ein Gate aus (z.B. Bassdrum ->
# Doepfer A-140-2v). Belegt ein Eurorack-Modus, CV MOD oder die
# Kalibrierung den Ausgang, hat das Vorrang - der Trigger schweigt.
# INSTR. MUTE schaltet nur den Klang stumm, nicht den Trigger (so
# kann ein Instrument nur ins Rack gehen). SPUR MUTE stoppt beides.

DRUM_TRIG_NAMES = ["5V", "8V", "VELO"]


def drum_out_free(out):
    return not _cv_conflict(out) and not S["cvsrc"][out]


def _trig_io(out, volts, gap):
    # Ausfuehrung zum richtigen Tick (ueber later)
    if not drum_out_free(out):
        return
    if gap:
        # Low muss lang genug sein, damit das Modul eine neue Flanke sieht
        cv_write(out, 0.0)
        time.sleep_us(TRIG_GAP_US)
    cv_write(out, volts)


def _trig_low(rt, out):
    if rt.trig_hi[out]:
        rt.trig_hi[out] = False
        if trig_native(out):
            snd_at(_sched, synth=TRIG_SYNTHS[out], vel=0)
        else:
            later(_trig_io, out, 0.0, False)
        return True
    return False


def drum_trig_all_off(rt=None):
    rt = rt or RTS[DRUM]
    for out in (0, 1):
        _trig_low(rt, out)


def _trig_fire(rt, out, v, s, just_low=False):
    if not drum_out_free(out):
        return
    d = S["drm"]
    lv = d["tlv"]
    volts = CV_GATE_VOLTS if lv == 0 else (8.0 if lv == 1 else 8.0 * v / 15.0)
    gap = rt.trig_hi[out] or just_low
    if trig_native(out):
        # tick-genau ueber AMY. Neu ausloesen: 1 Tick vorher auf 0 V.
        ts = TRIG_SYNTHS[out]
        vel = clamp(volts / (TRIG_AMP * TRIG_FULL_V), 0.0, 1.0)
        if _sched is not None and _sched < _late_tick:
            MEAS["drop"] += 1
        else:
            if gap:
                snd_at(None if _sched is None else _sched - 1, synth=ts, vel=0)
            snd_at(_sched, synth=ts, note=60, vel=vel)
    else:
        # noch high (oder gerade erst runter): mit Luecke neu ausloesen
        later(_trig_io, out, volts, gap)
    rt.trig_hi[out] = True
    rt.trig_off[out] = s + d["tlen"] * SUB_PER_32


# ---------------- Grids: X/Y-Karte ----------------
#
# Vier Eck-Karten (je Instrument 16 Gewichte 0-f): hohe Werte spielen
# schon bei wenig Dichte, niedrige erst bei viel Dichte. X/Y mischt
# die Ecken stufenlos (bilinear), DICHTE je Instrument ist die
# Schwelle, ZUFALL wackelt an den Gewichten. Wichtige Steps (hohes
# Gewicht) werden lauter gespielt.
#
#   X=0 Y=0  GERADE (4/4)      X=1 Y=0  BREAKBEAT
#   X=0 Y=1  HALFTIME (duenn)  X=1 Y=1  BROKEN (dicht)
#
# Reihenfolge je Ecke: BD SD CH OH CP LT HT RS (Zeilen 1-8).

_GRID_SRC = (
    ("f003e002f004e015", "0002a0030001a042", "35e635d735e635c8", "00a0005000900060",
     "0000f0000000e000", "0000000300000060", "0000000000300050", "0020000400200030"),
    ("f020003a00e01002", "0020f0030060f050", "c4a5c4a6c4a5c4a7", "0000000c0000000a",
     "000000000000a000", "0000000000000a06", "0000000000060000", "00300004000300a0"),
    ("f000000200a00003", "00000000f0000000", "b030a040b030a050", "0000000c00000000",
     "000000000000000a", "0000000000000c0a", "000000000000a0c0", "00a000000a000000"),
    ("f00a00c00af0000c", "0080f0a60c50f0a6", "ebdcebdcebdcebdc", "000a000c000a000d",
     "000000c00000000a", "0000000c0000a000", "00000a000000000c", "0c00a00c00a00c00"),
)
GRID = [[[int(c, 16) for c in row] for row in corner] for corner in _GRID_SRC]
GRID_MODE_NAMES = ["PATTERN", "LIVE"]
_grid_mod = [0.0, 0.0]      # Versatz aus CV IN / Joystick


def grid_xy():
    d = S["drm"]
    return (clamp(d["gx"] + _grid_mod[0], 0.0, 1.0),
            clamp(d["gy"] + _grid_mod[1], 0.0, 1.0))


def grid_vel(k, s, z=0, xy=None):
    # Velocity 0-15 des Grids an Instrument k, Step s
    d = S["drm"]
    dens = d["gd"][k]
    if dens <= 0:
        return 0
    x, y = xy or grid_xy()
    s %= 16
    top = GRID[0][k][s] + (GRID[1][k][s] - GRID[0][k][s]) * x
    bot = GRID[2][k][s] + (GRID[3][k][s] - GRID[2][k][s]) * x
    w = top + (bot - top) * y
    if z:
        w += (rnd(2 * z + 1) - z) * 0.5
    if w <= 15 - dens:
        return 0
    return clamp_int(4 + w * 11 / 15, 1, 15)


def drum_cell(k, s, xy=None):
    # Was an Step s von Instrument k klingt (Anzeige, ohne Zufall)
    d = S["drm"]
    if d["gm"]:
        return grid_vel(k, s, 0, xy)
    return int(d["pats"][d["pat"]][k][s], 16)


def grid_freeze():
    # Aktuelle Grids-Karte ins Pattern schreiben und auf PATTERN schalten
    d = S["drm"]
    pat = d["pats"][d["pat"]]
    xy = grid_xy()
    for k in range(DRUM_ROWS):
        n = d["lens"][k]
        row = "".join([HEX_DIGITS[grid_vel(k, s, d["gz"], xy)] for s in range(n)])
        pat[k] = row + pat[k][n:]
    d["gm"] = 0
    request_save()


_grid_next = 0


def service_grid_mod():
    # CV IN1/IN2 (0-5 V = +0..1) und Joystick (Auslenkung +-0.5)
    # verschieben X/Y. Nur im LIVE-Modus, ca. alle 40 ms.
    global _grid_next
    d = S["drm"]
    if not d["gm"] or not (d["gcv"] or d["gj"]):
        if _grid_mod[0] or _grid_mod[1]:
            _grid_mod[0] = _grid_mod[1] = 0.0
            mark_dirty()
        return
    if since(_grid_next) < 0:
        return
    _grid_next = time.ticks_add(now(), 40)
    mx = my = 0.0
    if d["gcv"]:
        mx += cv_read(0) / 5.0
        my += cv_read(1) / 5.0
    if d["gj"] and _joy is not None and not acid_joy_active():
        mx += _joy[0] - 0.5
        jy = _joy[1] - 0.5
        my += -jy if JOY_Y_INVERT else jy
    if abs(mx - _grid_mod[0]) > 0.01 or abs(my - _grid_mod[1]) > 0.01:
        _grid_mod[0] = mx
        _grid_mod[1] = my


def acid_joy_active():
    return bool(S["acid"]["joy"]) and joystick_available


def grid_joy_active():
    # Joystick steuert Grids statt die Drum-Seite zu bedienen
    # (die 303 hat Vorrang)
    d = S["drm"]
    return d["gm"] and d["gj"] and not acid_joy_active()


def joy_owned():
    # Joystick gehoert einem Instrument statt der Menue-Bedienung
    return acid_joy_active() or grid_joy_active()


def _acid_joy_axis(raw):
    o = (raw - 0.5) * 2.0
    if -ACID_JOY_DEAD < o < ACID_JOY_DEAD:
        return 0.0
    o = (o - ACID_JOY_DEAD if o > 0 else o + ACID_JOY_DEAD) / (1.0 - ACID_JOY_DEAD)
    return clamp(o * S["acid"]["jd"] / 100.0, -1.0, 1.0)


def _acid_mod_apply(new):
    # neue Auslenkungen uebernehmen und nur Geaendertes an AMY schicken
    global _acid_mod
    old = _acid_mod
    _acid_mod = new
    touched = set(new) | set(old)
    if touched & {1, 2, 3, 5}:
        acid_apply("filter")
    if 4 in touched:
        acid_apply("dec")
    if 6 in touched:
        acid_apply("slide")
    if 9 in touched:
        acid_apply("dist")
    mark_dirty()


def service_acid_joy():
    global _acid_joy_next
    if not acid_joy_active() or _joy is None:
        if _acid_mod:
            _acid_mod_apply({})
        return
    if since(_acid_joy_next) < 0:
        return
    _acid_joy_next = time.ticks_add(now(), 30)
    a = S["acid"]
    ox = _acid_joy_axis(_joy[0])
    # Rohwert Y waechst nach unten (wie bei der Menue-Bedienung):
    # hoch = mehr, runter = weniger
    oy = _acid_joy_axis(_joy[1])
    if not JOY_Y_INVERT:
        oy = -oy
    new = {}
    for t, o in ((a["jx"], ox), (a["jy"], oy)):
        if t and o:
            new[t] = clamp(new.get(t, 0.0) + o, -1.0, 1.0)
    changed = set(new) != set(_acid_mod)
    if not changed:
        for t in new:
            if abs(new[t] - _acid_mod[t]) > 0.02:
                changed = True
                break
    if changed:
        _acid_mod_apply(new)


def acid_joy_latch():
    # Joystick-Knopf: aktuellen Klang als neue Grundwerte uebernehmen
    if not _acid_mod:
        toast("303", "JOYSTICK IN RUHE")
        return
    a = S["acid"]
    for k in ("cut", "reso", "env", "dec", "acc", "slide", "tune", "dd"):
        a[k] = acid_val(k)
    a["tune"] = clamp_int(a["tune"], -12, 12)
    _acid_mod_apply({})
    request_save()
    toast("303", "UEBERNOMMEN")


def _drum_tick(rt, s):
    d = S["drm"]
    if rt.offs and s >= rt.off_at:
        _drum_offs(d, rt)
    if rt.poffs:
        keep = []
        for sk, t in rt.poffs:
            if s >= t:
                slot_stop(sk, True)
            else:
                keep.append((sk, t))
        rt.poffs = keep
    low0 = low1 = False
    if rt.trig_hi[0] and s >= rt.trig_off[0]:
        low0 = _trig_low(rt, 0)
    if rt.trig_hi[1] and s >= rt.trig_off[1]:
        low1 = _trig_low(rt, 1)
    L = SEQ_DIV_SUB[d["div"]]
    g = s // L
    if s - g * L != _swing_off(L, g):
        return
    b = g % DRUM_BAR
    if b == 0 and rt.pending is not None:
        d["pat"] = rt.pending
        rt.pending = None
    lens = d["lens"]
    rows = [g % lens[k] for k in range(DRUM_ROWS)]
    later(_set_rows, rt, b, rows)      # Anzeige zum richtigen Zeitpunkt
    if d["mute"]:
        return
    if rt.offs:
        _drum_offs(d, rt)
    pat = d["pats"][d["pat"]]
    inner = d["out"] in (0, 2)
    ext = d["out"] in (1, 2)
    ch = d["ch"]
    live = d["gm"]
    xy = grid_xy() if live else None
    trg = d["trg"]
    # Ein Drumkit ignoriert Note-Offs (synth_flags 2) - dann keine senden
    # (spart pro Schlag einen amy.send)
    inner_off = inner and not is_drum(S["pat"][ch])
    smp = d["smp"]
    for k in range(DRUM_ROWS):
        if live:
            v = grid_vel(k, rows[k], d["gz"], xy)
        else:
            v = int(pat[k][rows[k]], 16)
        if not v:
            continue
        if trg[0] == k or trg[1] == k:
            try:
                for out in (0, 1):
                    if trg[out] == k:
                        _trig_fire(rt, out, v, s, low0 if out == 0 else low1)
            except Exception as e:
                print("DRUM TRIG", e)
        if d["mutes"][k]:
            continue
        note = d["notes"][k]
        sk = smp[k]
        pad = False
        try:
            if inner:
                pc = d["sli"][k] - 1 if sk >= 0 else -1
                if pc >= 0 and not slot_chops(sk):
                    pc = -1
                if sk >= 0 and slot_play(sk, v / 15.0, True, pc):
                    pad = True
                    if pc >= 0:
                        # SLICE: nach der Stueck-Laenge beenden
                        rt.poffs = [e for e in rt.poffs if e[0] != sk]
                        rt.poffs.append((sk, s + slice_subs(sk)))
                    elif slot(sk)["pm"]:
                        # GATE/LOOP: bis kurz vor den naechsten Step halten
                        rt.poffs = [e for e in rt.poffs if e[0] != sk]
                        rt.poffs.append((sk, s + max(1, L - 1)))
                elif sk < 0:
                    snd(synth=ch, note=note, vel=v / 15.0)
            if ext:
                _drum_midi(d, rt, note, (v * 127 + 7) // 15)
        except Exception as e:
            print("DRUM ON", e)
            continue
        if (inner_off and not pad and sk < 0) or ext:
            rt.offs.append((ch if (inner_off and sk < 0) else 0, note, ext))
    if rt.offs:
        rt.off_at = s + DRUM_GATE_SUB


# ---------------- Patterns ----------------

def track_clear_pattern(i):
    t = trk_cfg(i)
    if i == ACID:
        t["pats"][t["pat"]] = [[-1, 0, 0, 0] for _ in range(ACID_STEPS_MAX)]
    elif i == DRUM:
        t["pats"][t["pat"]] = [DRUM_EMPTY] * DRUM_ROWS
    else:
        t["pats"][t["pat"]] = [0] * SEQ_MAX_STEPS
    request_save()


def track_copy_pattern(i, dst):
    t = trk_cfg(i)
    t["pats"][dst] = deep_copy(t["pats"][t["pat"]])
    request_save()


def track_set_pattern(i, p):
    # laufend: Wechsel am Ende des Durchlaufs, gestoppt: sofort
    if S["run"]:
        RTS[i].pending = p
    else:
        trk_cfg(i)["pat"] = p


# ---------------- Transport ----------------

def seq_release(i):
    rt = RTS[i]
    if i == ACID:
        _acid_off(rt)
    elif i == DRUM:
        _drum_offs(S["drm"], rt)
        drum_trig_all_off(rt)
        for sk, t in rt.poffs:
            try:
                slot_stop(sk)
            except Exception:
                pass
        rt.poffs = []
    else:
        _track_off(S["trk"][i], rt)


_next_sub = None         # naechster zu berechnender Sub (relativ zum Start)
_origin = None           # AMY-Tick, an dem Step 1 aller Spuren liegt
_req_origin = None       # vorgegebener Start-Tick (MIDI-Start bei FOLGEN)
_seq_slot = None         # tulip.seq_add_callback-Slot (None = loop())
_last_tick = 0


def lookahead_subs():
    # VORLAUF in ms -> Subs (1 Sub = 2 Ticks = 2500/Tempo ms). Mindestens
    # 4 Subs, damit auch der Takt ueber loop() (alle 6 Ticks) reicht.
    if not S["sqm"]:
        return 0
    ms_per_sub = 2500.0 / max(20, S["tempo"])
    return clamp_int(S["vlf"] / ms_per_sub + 0.5, 4, 32)


def _process(s):
    for i in range(4):
        try:
            _track_tick(S["trk"][i], RTS[i], s)
        except Exception as e:
            print("SEQ TICK", i, e)
    try:
        _acid_tick(RTS[ACID], s)
    except Exception as e:
        print("ACID TICK", e)
    try:
        _drum_tick(RTS[DRUM], s)
    except Exception as e:
        print("DRUM TICK", e)


def seq_process_tick(tick):
    # VORAUS: alle Subs bis "jetzt + Vorlauf" berechnen und auf AMYs
    # Zeitachse legen. DIREKT (wie v12.11): nur bis "jetzt", sofort
    # spielen. Alle Spuren zaehlen ab demselben Start-Tick (_origin).
    # Zu spaet berechnete Noten werden ausgelassen, laengere Aussetzer
    # uebersprungen (MEAS "drop"/"miss").
    global _next_sub, _origin, _sched, _last_tick, _late_tick, _req_origin
    jumped = tick < _last_tick - 8          # Tick-Zaehler neu (Reset)
    _last_tick = tick
    if _nrec["at"] is not None:
        try:
            nrec_service(tick)            # Aufnahme auf Takt 1
        except Exception as e:
            print("NREC TICK", e)
    run_deferred(tick)
    if not S["run"]:
        _next_sub = None
        _origin = None
        return
    la = lookahead_subs()
    if _origin is None or _next_sub is None or jumped:
        if _req_origin is not None and tick - 2 <= _req_origin <= tick + 96:
            _origin = _req_origin
        else:
            # Mit Vorlauf etwas spaeter beginnen, damit Step 1 schon
            # geplant ist, wenn AMY ihn erreicht.
            _origin = tick + (2 * SUB_TICKS if la else 0)
        _req_origin = None
        _next_sub = 0
    now_rel = (tick - _origin) // SUB_TICKS
    if la:
        _late_tick = tick - 1
        if _next_sub < now_rel - 2:
            MEAS["miss"] += 1
            _next_sub = now_rel
        elif _next_sub < now_rel:
            MEAS["late"] += 1
    else:
        _late_tick = -1
        catch = SUB_PER_32 if _seq_slot is not None else 2 * SUB_PER_32
        if now_rel - _next_sub + 1 > catch:
            MEAS["miss"] += 1
            _next_sub = now_rel
    end = now_rel + la
    try:
        while _next_sub <= end:
            if _next_sub >= 0:
                _sched = (_origin + _next_sub * SUB_TICKS) if la else None
                _process(_next_sub)
            _next_sub += 1
    finally:
        _sched = None


def amy_tick(tick):
    # Basis fuer die Planung: AMYs eigener Sequencer-Zaehler (damit
    # vergleicht AMY die ticks=). Faellt auf den Callback-Tick zurueck.
    t = _seq_ticks()
    if t is None:
        return tick
    d = t - tick
    if TDIFF[0] is None or d < TDIFF[0]:
        TDIFF[0] = d
    if TDIFF[1] is None or d > TDIFF[1]:
        TDIFF[1] = d
    return t


def _seq_cb(tick):
    if _xfer_lock:
        return            # Sample-Uebertragung am Stueck (alte Firmware)
    t0 = time.ticks_us()
    try:
        seq_process_tick(amy_tick(tick))
    except Exception as e:
        print("SEQ", e)
    meas("seq", t0)


def seq_cb_start():
    # Feinraster: alle 2 AMY-Ticks. Ein alter Slot (Sketch neu geladen
    # ohne Neustart) wird vorher entfernt.
    global _seq_slot
    if tulip is None or not hasattr(tulip, "seq_add_callback"):
        return False
    try:
        import builtins
        old = getattr(builtins, "_dolphin_seq_slot", None)
    except Exception:
        builtins = None
        old = None
    if old is not None:
        try:
            tulip.seq_remove_callback(old)
        except Exception:
            pass
    try:
        _seq_slot = tulip.seq_add_callback(_seq_cb, 0, SUB_TICKS)
    except Exception as e:
        print("SEQ CB", e)
        _seq_slot = None
        return False
    try:
        builtins._dolphin_seq_slot = _seq_slot
    except Exception:
        pass
    return True


def seq_cb_stop():
    global _seq_slot
    if _seq_slot is not None and tulip is not None:
        try:
            tulip.seq_remove_callback(_seq_slot)
        except Exception:
            pass
    _seq_slot = None


def seq_send_transport(byte):
    if S["clock"] != 1 or tulip is None:
        return
    try:
        tulip.midi_out([byte])
    except Exception as e:
        print("TRANSPORT", e)


def seq_cancel_scheduled():
    # Noch nicht gespielte, bereits geplante Ereignisse verwerfen und
    # alles abschalten, was dadurch haengen koennte.
    del _defer[:]
    try:
        amy.send(ticks="0,0,%d" % SEQ_TAG)
    except Exception as e:
        print("SEQ CLEAR", e)
    chans = set()
    midi_chs = set()
    for t in S["trk"]:
        chans.add(t["ch"])
        if t["out"] in (1, 2):
            midi_chs.add(t["mch"])
    if S["drm"]["out"] in (0, 2):
        chans.add(S["drm"]["ch"])
    for t in (S["acid"], S["drm"]):
        if t["out"] in (1, 2):
            midi_chs.add(t["mch"])
    for ch in chans:
        try:
            amy.send(synth=ch, vel=0)
        except Exception:
            pass
    try:
        amy.send(synth=ACID_SYNTH, vel=0)
    except Exception:
        pass
    for rt in RTS:
        try:
            if rt.midi_ready is not None:
                amy.send(synth=rt.midi_synth, vel=0)
        except Exception:
            pass
        rt.midi_open = None
    if tulip is not None:
        for mch in midi_chs:
            try:
                tulip.midi_out([0xB0 | (mch - 1), 123, 0])
            except Exception:
                pass
    pads_all_off()
    RTS[DRUM].poffs = []
    # CV: Trigger, 303-Gate und MIDI>CV-Gate sicher auf 0
    rtd = RTS[DRUM]
    for ts in TRIG_SYNTHS:
        try:
            amy.send(synth=ts, vel=0)
        except Exception:
            pass
    for out in (0, 1):
        rtd.trig_hi[out] = False
        if trig_native(out):
            continue
        if S["drm"]["trg"][out] >= 0 and drum_out_free(out):
            cv_write(out, 0.0)
    if acid_cv_active():
        _acid_gate(0.0)
    if _midicv_gate:
        midicv_reset()
        cv_write(1, 0.0)


def seq_start():
    global _origin
    _origin = None           # naechster Tick = Step 1
    S["run"] = 1
    for rt in RTS:
        rt.arp_i = 0
    if not transport_hook(True):
        seq_send_transport(0xFA)
    request_save()


def seq_stop():
    S["run"] = 0
    if not transport_hook(False):
        seq_send_transport(0xFC)
    seq_cancel_scheduled()
    for i in range(len(RTS)):
        try:
            seq_release(i)
        except Exception:
            pass
        RTS[i].step = -1
        RTS[i].rows = None
        if RTS[i].pending is not None:
            trk_cfg(i)["pat"] = RTS[i].pending
            RTS[i].pending = None
    save_state()


def seq_toggle():
    if S["run"]:
        seq_stop()
    else:
        seq_start()


def apply_tempo():
    try:
        amy.send(tempo=S["tempo"])
    except Exception as e:
        print("TEMPO", e)
    try:
        import sequencer
        sequencer.tempo(S["tempo"])
    except Exception:
        pass


# 0 INTERN -> AMY 0, 1 SENDEN -> AMY 2 (Master), 2 FOLGEN -> AMY 1
_CLOCK_TO_AMY = (0, 2, 1)


def apply_clock():
    try:
        amy.send(external_midi_sync=_CLOCK_TO_AMY[S["clock"]])
    except Exception as e:
        print("CLOCK", e)
    if S["clock"] == 1 and S["run"] and tulip is not None:
        try:
            tulip.midi_out([0xFA])
        except Exception:
            pass
    try:
        apply_transport()
    except Exception:
        pass


# Tap-Tempo: Mittel der letzten Abstaende, Pause > 2 s = neu
_taps = []


def tap_tempo():
    t = now()
    if _taps and time.ticks_diff(t, _taps[-1]) > 2000:
        del _taps[:]
    _taps.append(t)
    if len(_taps) > 5:
        _taps.pop(0)
    if len(_taps) >= 2:
        span = time.ticks_diff(_taps[-1], _taps[0]) / (len(_taps) - 1)
        if span > 0:
            S["tempo"] = clamp_int(60000.0 / span + 0.5, 20, 300)
            apply_tempo()
            request_save()


# ================================================================
# MIDI-EINGANG: ein gemeinsamer Callback
# ================================================================

_bank_msb = [None] * 17


def pc_sync(ch, program):
    old = S["pat"][ch]
    if old == -1:
        return
    bank = _bank_msb[ch]
    if bank is None:
        bank = old >> 7
        if bank == 2:
            bank = 0
    p = program + 128 * bank
    if p in PATCH_POS:
        if p != old:
            reset_tone(ch)
        S["pat"][ch] = p
        mark_dirty()


def chord_notes(ch, note, vel, on):
    v = vel / 127.0 if on else 0
    for iv in CHORD_INTERVALS[S["chord"][ch]]:
        n = note + iv
        if n <= 127:
            amy.send(synth=ch, note=n, vel=v)


MIDI_LOG_N = 8
_midi_log = []            # (Kanal, Art, Nummer, Wert, Aktion), neuestes zuletzt
_midi_count = [0]


def _mlog(ch, kind, num, val, act):
    _midi_log.append((ch, kind, num, val, act))
    if len(_midi_log) > MIDI_LOG_N:
        _midi_log.pop(0)
    if STACK and isinstance(STACK[-1], MidiMonitorPage):
        mark_dirty()


def midi_dispatch(m):
    global _learned, _learn_armed
    _midi_count[0] += 1
    try:
        if _saver and _sv["cur"] == SV_TERM:
            sv_midi(m)
        if S["thru"] and tulip is not None:
            tulip.midi_out(m)
        if len(m) and m[0] in (0xFA, 0xFB, 0xFC):
            if S["clock"] == 2:
                ext_transport(m[0])
            return
        if len(m) < 2:
            return
        st = m[0]
        typ = st & 0xF0
        if typ == 0xF0:
            return
        ch = (st & 0x0F) + 1
        if typ == 0x90 or typ == 0x80:
            if len(m) < 3:
                return
            note = m[1]
            on = typ == 0x90 and m[2] > 0
            if ch == S["sb"]["pch"] and SMP_PAD_NOTE0 <= note < SMP_PAD_NOTE0 + SMP_SLOTS:
                pk = note - SMP_PAD_NOTE0
                if on:
                    ok = slot_play(pk, m[2] / 127.0)
                    _mlog(ch, "N", note, m[2], ("PAD S%d" % (pk + 1)) if ok else
                          ("S%d %s" % (pk + 1, _slot_state(pk)[:6])))
                elif slot(pk)["pm"]:
                    slot_stop(pk)
                return
            if (ch == S["sb"]["pch"] and SMP_SLICE_NOTE0 <= note < SMP_SLICE_NOTE0 + 16):
                k = S["sb"]["ss"]
                pc = note - SMP_SLICE_NOTE0
                if on and pc >= slot_chops(k):
                    _mlog(ch, "N", note, m[2], "S%d KEINE SLICE" % (k + 1))
                if pc < slot_chops(k):
                    if on:
                        ok = slice_play_now(k, pc, m[2] / 127.0)
                        _mlog(ch, "N", note, m[2], ("SLICE %d" % (pc + 1)) if ok else
                              ("S%d %s" % (k + 1, _slot_state(k)[:6])))
                    elif slot(k)["pm"] == 1:
                        slot_stop(k)              # GATE: Loslassen stoppt
                return
            if on:
                _mlog(ch, "N", note, m[2], "%s %d" % ("KANAL", ch))
            if S["chord"][ch]:
                chord_notes(ch, note, m[2], on)
            if midicv_active_for(ch):
                midicv_note(note, on)
            arp_note(ch, note, on)
            if ch == S["cur"] and 2 in S["cvsrc"]:
                cvmod_env_note(on)
        elif typ == 0xB0:
            _mlog(ch, "CC", m[1], m[2] if len(m) > 2 else 0, "")
            if m[1] == 0 and len(m) > 2:
                _bank_msb[ch] = m[2]
            if _learn_armed:
                _learn_armed = False
                _learned = (ch, m[1], S["cct"])
        elif typ == 0xC0:
            _mlog(ch, "PC", m[1], 0, "")
            pc_sync(ch, m[1])
    except Exception as e:
        print("MIDI", e)


def _seq_ticks():
    try:
        return amy.sequencer_ticks()
    except Exception:
        return None


def ext_transport(b):
    # CLOCK = FOLGEN: MIDI-Start/-Stop des Masters (z.B. KeyStep Pro).
    # Step 1 liegt auf dem naechsten Clock-Tick nach dem Start-Byte.
    global _req_origin
    if b == 0xFC:
        if S["run"]:
            seq_stop()
        return
    if b == 0xFA and S["run"]:
        seq_stop()
    if not S["run"]:
        t = _seq_ticks()
        _req_origin = None if t is None else t + 1
        seq_start()
        if t is not None:
            try:
                seq_process_tick(t)       # Step 1 sofort planen
            except Exception as e:
                print("EXT START", e)


def register_midi():
    if midi is None:
        return
    try:
        midi.remove_callback(midi_dispatch)
    except Exception:
        pass
    try:
        midi.add_callback(midi_dispatch)
    except Exception as e:
        print("MIDI CB", e)


# ================================================================
# PANIC
# ================================================================

def panic():
    for ch in range(1, 17):
        try:
            amy.send(synth=ch, vel=0)
        except Exception:
            pass
    if S["run"]:
        seq_stop()
    arp_clear()
    if _midicv_gate:
        cv_write(1, 0.0)
    midicv_reset()
    try:
        amy.send(synth=ACID_SYNTH, vel=0)
    except Exception:
        pass
    pads_all_off()
    if acid_cv_active():
        _acid_gate(0.0)
    sent = []
    for t in S["trk"] + [S["acid"], S["drm"]]:
        if t["out"] in (1, 2) and t["mch"] not in sent and tulip is not None:
            sent.append(t["mch"])
            try:
                tulip.midi_out([0xB0 | (t["mch"] - 1), 123, 0])
            except Exception:
                pass
    toast("PANIC", "ALLE NOTEN AUS")


def reset_all_midi():
    for ch in range(1, 17):
        S["pat"][ch] = -1
        try:
            configure_channel(ch)
            amy.send(synth=ch, vel=0)
        except Exception as e:
            print("RST", ch, e)
    refresh_buses()
    save_state()


# ================================================================
# SZENEN + MORPH
# ================================================================
#
# Eine Szene ist ein Schnappschuss aller Klang-, Mixer-, Effekt- und
# Sequencer-Werte (nicht: Encoder, WLAN, MIDI-Setup). Morph blendet
# alle stufenlosen Werte zwischen Szene A und B; Patches wechseln
# nur beim LADEN einer Szene.

SCENE_KEYS = ("pat", "vo", "bus", "lvl", "pan", "mute", "chord", "porta",
              "cut", "res", "att", "dec", "sus", "rel", "lfr", "lfd", "alg",
              "fb", "tch", "fx", "master", "crush", "crate", "tempo", "swing",
              "trk", "acid", "drm", "syx", "vco", "ain")
scenes = [None] * 8


def scenes_load():
    global scenes
    for path in [SCENE_FILE] + [d + "dolphin_scenes.json" for d in
                                ("/sd/", "/user/current/", "/user/", "/")]:
        try:
            f = open(path, "r")
            data = json.loads(f.read())
            f.close()
        except Exception:
            continue
        if isinstance(data, list) and len(data) == 8:
            scenes = data
            print("SZENEN AUS", path)
            return


def scenes_save():
    try:
        _write_file(SCENE_FILE, json.dumps(scenes))
        return True
    except Exception as e:
        print("SCENES", e)
        return False


def scene_store(i):
    scenes[i] = deep_copy(dict((k, S[k]) for k in SCENE_KEYS))
    ok = scenes_save()
    toast("SZENE %d" % (i + 1), "GESPEICHERT" if ok else "FEHLER")


def scene_recall(i):
    sc = scenes[i]
    if sc is None:
        toast("SZENE %d" % (i + 1), "LEER")
        return
    ain_on = S["ain"]["on"]          # v13.22: AN/AUS bleibt global
    dflt = default_state()           # einmal statt pro Schluessel
    for k in SCENE_KEYS:
        if k in sc:
            S[k] = _merge(dflt[k], deep_copy(sc[k]))
    S["ain"]["on"] = ain_on
    sanitize()
    for rt in RTS:
        rt.pending = None
    apply_all_sound()
    apply_tempo()
    acid_setup()
    apply_eurorack_mode()
    vco_apply_all()
    ain_apply_all()
    request_save()
    toast("SZENE %d" % (i + 1), "GELADEN")


def scene_delete(i):
    scenes[i] = None
    scenes_save()


_MORPH_CH = ("lvl", "pan", "cut", "res")
_MORPH_FX = ("rv", "cho", "ech", "eq")
_MORPH_ACID = ("cut", "reso", "env", "acc", "lvl", "dec", "dd", "dm")
_morph_pending = False


def request_morph():
    global _morph_pending
    _morph_pending = True


def _lerp(a, b, x):
    return a + (b - a) * x


def morph_apply():
    global _morph_pending
    _morph_pending = False
    A = scenes[S["mA"]]
    B = scenes[S["mB"]]
    if A is None or B is None:
        return
    x = S["mx"]
    # Jeder Abschnitt einzeln abgesichert: fehlt einer alten Szene ein
    # Schluessel, wird nur dieser Teil uebersprungen (v12.11).
    try:
        z17 = [0] * 17
        ta = A.get("tch", z17)
        tb = B.get("tch", z17)
        for ch in range(1, 17):
            lv = (_lerp(A["lvl"][ch], B["lvl"][ch], x))
            if abs(lv - S["lvl"][ch]) > 0.004:
                S["lvl"][ch] = lv
                apply_level(ch)
            pn = _lerp(A["pan"][ch], B["pan"][ch], x)
            if abs(pn - S["pan"][ch]) > 0.004:
                S["pan"][ch] = pn
                apply_pan(ch)
            if (ta[ch] | tb[ch]) & T_FILTER and "cut" in A and "cut" in B:
                cu = _lerp(A["cut"][ch], B["cut"][ch], x)
                rs = _lerp(A["res"][ch], B["res"][ch], x)
                if abs(cu - S["cut"][ch]) > 1 or abs(rs - S["res"][ch]) > 0.01:
                    S["cut"][ch] = cu
                    S["res"][ch] = rs
                    tone_touch(ch, T_FILTER)
                    apply_filter(ch)
    except Exception as e:
        print("MORPH KANAL", e)
    try:
        for b in range(4):
            for w in _MORPH_FX:
                va = A["fx"][b][w]
                vb = B["fx"][b][w]
                cur_l = S["fx"][b][w]
                changed = False
                for k in range(len(cur_l)):
                    nv = _lerp(va[k], vb[k], x)
                    if isinstance(cur_l[k], int):
                        nv = int(nv)
                    if abs(nv - cur_l[k]) > 0.002:
                        cur_l[k] = nv
                        changed = True
                if changed and b in active_buses():
                    fx_send(b, w)
    except Exception as e:
        print("MORPH FX", e)
    try:
        m = _lerp(A["master"], B["master"], x)
        if abs(m - S["master"]) > 0.004:
            S["master"] = m
            apply_master_volume()
        t = int(_lerp(A["tempo"], B["tempo"], x) + 0.5)
        if t != S["tempo"]:
            S["tempo"] = t
            apply_tempo()
    except Exception as e:
        print("MORPH MASTER", e)
    try:
        ac = S["acid"]
        chg = False
        for k in _MORPH_ACID:
            # .get: aeltere Szenen kennen dd/dm nicht
            nv = _lerp(A["acid"].get(k, ac[k]), B["acid"].get(k, ac[k]), x)
            if isinstance(ac[k], int):
                nv = int(nv)
            if abs(nv - ac[k]) > 0.002:
                ac[k] = nv
                chg = True
        if chg:
            acid_apply("filter")
            acid_apply("dec")
            acid_apply("lvl")
            acid_apply("dist")
    except Exception as e:
        print("MORPH 303", e)
    try:
        # Grids X/Y (aeltere Szenen ohne Drum-Spur: nichts tun)
        if "drm" in A and "drm" in B:
            dr = S["drm"]
            for k in ("gx", "gy"):
                dr[k] = clamp(_lerp(A["drm"].get(k, dr[k]), B["drm"].get(k, dr[k]), x), 0.0, 1.0)
    except Exception as e:
        print("MORPH", e)


# ================================================================
# GRAFIK
# ================================================================
#
# Kein try/except pro Zeichenbefehl (kostet Zeit) - der Renderer
# faengt Fehler einmal pro Bild ab.

fb = display


def R(x, y, w, h, c):
    fb.fill_rect(x, y, w, h, c)


def T(s, x, y, c=W):
    fb.text(s, x, y, c)


def TC(s, cx, y, c=W):
    fb.text(s, cx - 4 * len(s), y, c)


def TR(s, rx, y, c=W):
    fb.text(s, rx - 8 * len(s), y, c)


def HL(x, y, w, c):
    fb.hline(x, y, w, c)


def VL(x, y, h, c):
    fb.vline(x, y, h, c)


def FR(x, y, w, h, c):
    fb.hline(x, y, w, c)
    fb.hline(x, y + h - 1, w, c)
    fb.vline(x, y, h, c)
    fb.vline(x + w - 1, y, h, c)


def LN(x0, y0, x1, y1, c):
    if HAS_LINE:
        fb.line(x0, y0, x1, y1, c)
        return
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        fb.pixel(x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def CIRC(x, y, r, c, fill=False):
    if HAS_ELLIPSE:
        fb.ellipse(x, y, r, r, c, fill)
        return
    if fill:
        for yy in range(-r, r + 1):
            w = int((r * r - yy * yy) ** 0.5)
            fb.hline(x - w, y + yy, 2 * w + 1, c)
        return
    n = max(12, r * 6)
    for k in range(n):
        a = 6.2832 * k / n
        fb.pixel(x + int(round(r * math.cos(a))), y + int(round(r * math.sin(a))), c)


def bar(x, y, w, h, frac, fg=HI, bg=GH):
    fb.fill_rect(x, y, w, h, bg)
    fw = int(w * clamp(frac, 0.0, 1.0))
    if fw > 0:
        fb.fill_rect(x, y, fw, h, fg)


def bipbar(x, y, w, h, frac, fg=HI, bg=GH):
    # Balken von der Mitte aus (Pan, EQ, Spannungen)
    fb.fill_rect(x, y, w, h, bg)
    mid = x + w // 2
    p = x + int(w * clamp(frac, 0.0, 1.0))
    if p >= mid:
        fb.fill_rect(mid, y, max(1, p - mid), h, fg)
    else:
        fb.fill_rect(p, y, mid - p, h, fg)
    fb.vline(mid, y - 1, h + 2, MID)


# ---------------- Grosse Schrift (2x/3x aus der 8x8-Schrift) ----------------

_big_cache = {}


def _big_runs(s):
    runs = _big_cache.get(s)
    if runs is not None:
        return runs
    runs = []
    if framebuf is not None:
        w = 8 * len(s)
        buf = bytearray(w)
        f = framebuf.FrameBuffer(buf, w, 8, framebuf.MONO_HLSB)
        f.fill(0)
        f.text(s, 0, 0, 1)
        for yy in range(8):
            xx = 0
            while xx < w:
                if f.pixel(xx, yy):
                    st = xx
                    while xx < w and f.pixel(xx, yy):
                        xx += 1
                    runs.append((st, yy, xx - st))
                else:
                    xx += 1
    if len(_big_cache) > 40:
        _big_cache.clear()
    _big_cache[s] = runs
    return runs


def BIG(s, x, y, sc=2, c=W):
    if framebuf is None:
        fb.text(s, x, y + 4 * (sc - 1), c)
        return
    for st, yy, ln in _big_runs(s):
        fb.fill_rect(x + st * sc, y + yy * sc, ln * sc, sc, c)


def BIGC(s, cx, y, sc=2, c=W):
    BIG(s, cx - 4 * sc * len(s), y, sc, c)


# ---------------- Ringe (270 Grad, vorberechnet) ----------------

_RING_N = 36
_RING = []
for _k in range(_RING_N + 1):
    _a = math.radians(135 + 270.0 * _k / _RING_N)
    _RING.append((math.cos(_a), math.sin(_a)))


def ring(cx, cy, r, frac, sz=3, step=1, bip=False, fg=W, bg=GH):
    k_val = int(clamp(frac, 0.0, 1.0) * _RING_N + 0.5)
    k_mid = _RING_N // 2
    half = sz // 2
    for k in range(0, _RING_N + 1, step):
        c, s = _RING[k]
        if bip:
            on = (k_mid <= k <= k_val) or (k_val <= k <= k_mid)
        else:
            on = k <= k_val and k_val > 0
        fb.fill_rect(cx + int(r * c) - half, cy + int(r * s) - half, sz, sz, fg if on else bg)


# ---------------- Symbole fuer das Menue (24x24) ----------------

def icon(i, x, y, c):
    if i == 0:      # KLANG - Welle
        px, py = x, y + 12
        for k in range(1, 13):
            nx = x + 2 * k
            ny = y + 12 - int(9 * math.sin(k * 0.5236))
            LN(px, py, nx, ny, c)
            px, py = nx, ny
    elif i == 1:    # MIXER - Fader
        for j, h in ((0, 13), (1, 5), (2, 16)):
            VL(x + 3 + 9 * j, y + 1, 22, c)
            R(x + 9 * j, y + h, 7, 4, c)
    elif i == 2:    # EFFEKTE - Stern
        cx, cy = x + 12, y + 12
        for dx, dy in ((10, 0), (7, 7), (0, 10), (-7, 7), (-10, 0), (-7, -7), (0, -10), (7, -7)):
            LN(cx + dx // 3, cy + dy // 3, cx + dx, cy + dy, c)
        R(cx - 1, cy - 1, 3, 3, c)
    elif i == 3:    # SEQUENCER - Raster
        on = (1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1)
        for j in range(12):
            xx = x + (j % 4) * 6
            yy = y + 3 + (j // 4) * 7
            if on[j]:
                R(xx, yy, 5, 5, c)
            else:
                FR(xx, yy, 5, 5, c)
    elif i == 4:    # MODULAR - Buchse mit Kabel
        CIRC(x + 8, y + 8, 7, c)
        CIRC(x + 8, y + 8, 2, c, True)
        LN(x + 13, y + 13, x + 17, y + 20, c)
        LN(x + 17, y + 20, x + 23, y + 23, c)
    elif i == 5:    # SZENEN - Kartenstapel
        FR(x + 8, y + 1, 15, 11, c)
        R(x + 4, y + 6, 15, 11, 0)
        FR(x + 4, y + 6, 15, 11, c)
        R(x, y + 11, 15, 12, 0)
        FR(x, y + 11, 15, 12, c)
        R(x + 3, y + 16, 9, 2, c)
    elif i == 6:    # SAMPLER - Wellenform
        FR(x, y + 3, 24, 18, c)
        for k, h in enumerate((2, 6, 3, 8, 5, 2, 7, 4, 2, 5)):
            VL(x + 2 + 2 * k, y + 11 - h // 2, h + 1, c)
    elif i == 7:    # SETUP - Zahnrad
        CIRC(x + 12, y + 12, 7, c)
        CIRC(x + 12, y + 12, 3, c)
        for dx, dy in ((0, -10), (7, -7), (10, 0), (7, 7), (0, 10), (-7, 7), (-10, 0), (-7, -7)):
            R(x + 11 + dx, y + 11 + dy, 3, 3, c)


# ================================================================
# BILDSCHIRM-VERWALTUNG
# ================================================================

_dirty = True
_toast = None     # (titel, text, bis_ms)
cpu_load = 0.0


def mark_dirty():
    global _dirty
    _dirty = True


def toast(title, line="", ms=1100):
    global _toast
    _toast = (title, line, time.ticks_add(now(), ms))
    mark_dirty()


def draw_toast():
    title, line, _ = _toast
    R(6, 46, 116, 36, 0)
    R(6, 46, 116, 12, SEL)
    TC(title[:14], 64, 48, 0)
    FR(6, 46, 116, 36, W)
    TC(line[:14], 64, 66, W)


def draw_acid_joy(y=None):
    # kleine Anzeige der Joystick-Ziele (nur wenn ausgelenkt)
    if not _acid_mod:
        return
    a = S["acid"]
    parts = []
    for t in (a["jx"], a["jy"]):
        if t in _acid_mod:
            parts.append("%s%+d" % (ACID_JOY_TARGETS[t][:3], int(_acid_mod[t] * 99)))
    if parts:
        txt = " ".join(parts)[:16]
        yy = 117 if y is None else y
        R(0, yy - 1, 128, 10, 0)
        T(txt, 1, yy, HI)


def draw_status():
    ch = S["cur"]
    R(0, 0, 26, 9, HI)
    TC("C%d" % ch, 13, 1, 0)
    T("SMP" if chrom_owns(ch) else FAMILY_SHORT[family(S["pat"][ch])], 30, 1,
      MID if not S["mute"][ch] else DIM)
    if _ain_running:
        T("IN", 66, 1, LO)                # AUDIO IN laeuft (v13.22)
    TR("%d" % S["tempo"], 110, 1, LO)
    if S["run"]:
        for k in range(4):
            VL(116 + k, 1 + k, 8 - 2 * k, W)
    else:
        R(116, 2, 6, 6, DIM)
    HL(0, 10, 128, GH)
    w = int(128 * clamp(cpu_load, 0.0, 1.0))
    if w:
        HL(0, 10, w, W if cpu_load > 0.85 else LO)


def draw_rows(rows, sel, y0=28, n=7, rh=12, edit=False, maxlen=15):
    # rows: Liste (label, value). Zeichnet ein Scroll-Fenster um sel.
    total = len(rows)
    start = clamp_int(sel - n // 2, 0, max(0, total - n))
    for r in range(n):
        i = start + r
        if i >= total:
            break
        y = y0 + r * rh
        label, val = rows[i]
        val = str(val)
        room = maxlen - len(val) - (1 if val else 0)
        label = label[:max(1, room)]
        if i == sel:
            R(0, y - 2, 124, rh - 1, W if edit else SEL)
            T(label, 3, y, 0)
            if val:
                TR(val, 123, y, 0)
        else:
            T(label, 3, y, MID)
            if val:
                TR(val, 123, y, HI)
    if total > n:
        h = max(4, (n * rh) * n // total)
        span = n * rh - h
        yy = y0 - 2 + (span * start // max(1, total - n))
        VL(126, y0 - 2, n * rh, GH)
        R(125, yy, 3, h, LO)


def draw_title(t, right=""):
    T(t[:15], 3, 14, HI)
    if right:
        TR(right, 125, 14, DIM)
    HL(0, 24, 128, GH)


# ================================================================
# PARAMETER
# ================================================================

NUM = 0
ENUM = 1
BOOL = 2
ACT = 3
LINK = 4
INFO = 5

REG = {}


class P:
    def __init__(self, label, ref=None, lo=0.0, hi=1.0, step=0.01, fmt="%.2f",
                 kind=NUM, opts=None, vals=None, apply=None, vis=None, unit="",
                 log=False, bip=False, confirm=False, act=None, page=None,
                 info=None, short=None, key=None, getter=None, setter=None,
                 fmtf=None):
        self.label = label
        self.ref = ref
        self.lo = lo
        self.hi = hi
        self.step = step
        self.fmt = fmt
        self.kind = kind
        self.opts = opts
        self.vals = vals
        self.apply = apply
        self.vis = vis
        self.unit = unit
        self.log = log
        self.bip = bip
        self.confirm = confirm
        self.act = act
        self.page = page
        self.info = info
        self.short = short or label[:4]
        self.getter = getter
        self.setter = setter
        self.fmtf = fmtf
        self.integer = isinstance(lo, int) and isinstance(hi, int) and isinstance(step, int)
        if key:
            REG[key] = self

    def get(self):
        if self.getter:
            return self.getter()
        c, i = self.ref()
        return c[i]

    def set(self, v):
        if self.kind == NUM:
            v = clamp(v, self.lo, self.hi)
            if self.integer:
                v = int(round(v))
        if self.setter:
            self.setter(v)
        else:
            c, i = self.ref()
            c[i] = v
        if self.apply:
            try:
                self.apply()
            except Exception as e:
                print("APPLY", self.label, e)
        request_save()
        mark_dirty()

    def options(self):
        o = self.opts
        return o() if callable(o) else o

    def values(self):
        v = self.vals
        return v() if callable(v) else v

    def index(self):
        v = self.get()
        vals = self.values()
        if vals is not None:
            return vals.index(v) if v in vals else 0
        return int(v)

    def value_at(self, idx):
        vals = self.values()
        return vals[idx] if vals is not None else idx

    def nudge(self, d, acc=1):
        if self.kind == NUM:
            v = self.get()
            if self.log:
                v = v * (2 ** (d * acc * self.step / 12.0))
            else:
                v = v + d * acc * self.step
            self.set(v)
        elif self.kind == ENUM:
            n = len(self.options())
            if n:
                self.set(self.value_at((self.index() + d) % n))
        elif self.kind == BOOL:
            if d % 2:
                self.set(0 if self.get() else 1)

    def num_text(self):
        v = self.get()
        if self.fmtf:
            return self.fmtf(v)
        return self.fmt % v

    def text(self, idx=None):
        k = self.kind
        if k == NUM:
            return self.num_text() + self.unit
        if k == ENUM:
            o = self.options()
            if not o:
                return "-"
            i = self.index() if idx is None else idx
            return o[i % len(o)]
        if k == BOOL:
            return "AN" if self.get() else "AUS"
        if self.info:
            return self.info()
        return ">" if k == LINK else ""

    def frac(self):
        if self.kind != NUM:
            return 0.0
        v = self.get()
        if self.log:
            return math.log(max(v, self.lo) / self.lo) / math.log(self.hi / self.lo)
        return (v - self.lo) / float(self.hi - self.lo)


# Referenz-Helfer: (Container, Index)
def rS(k):
    return lambda: (S, k)


def rCH(k):
    return lambda: (S[k], S["cur"])


def rFX(name, i):
    return lambda: (S["fx"][fx_bus()][name], i)


def rT(k):
    return lambda: (S["trk"][S["sel"] % 4], k)


def rA(k):
    return lambda: (S["acid"], k)


def rD(k):
    return lambda: (S["drm"], k)


def rL(k, i):
    return lambda: (S[k], i)


# ================================================================
# PARAMETER-DEFINITIONEN (eine Stelle fuer Anzeige, Bedienung,
# Encoder-Zuordnung, Makros und Speichern)
# ================================================================

def _tone(bit, fn):
    def f():
        ch = S["cur"]
        tone_touch(ch, bit)
        fn(ch)
    return f


def _fam_in(fams):
    return lambda: cur_family() in fams


def _hz(v):
    return "%d" % int(v)


def _bus_changed():
    configure_channel(S["cur"])
    refresh_buses()


def _vo_changed():
    ch = S["cur"]
    S["vo"][ch] = min(S["vo"][ch], voices_allowed(ch))
    configure_channel(ch)


def _mute_changed():
    apply_level(S["cur"])
    apply_master_volume()


def _eq_changed():
    b = fx_bus()
    S["fx"][b]["prof"] = 0
    if S["fx"][b]["pfx"]:
        S["fx"][b]["pfx"] = 0     # Hand-EQ uebernimmt vom Patch
        fx_send(b, "cho")
    fx_send(b, "eq")


def _fx(name):
    def f():
        b = fx_bus()
        if name in ("cho", "eq") and S["fx"][b]["pfx"]:
            S["fx"][b]["pfx"] = 0     # Hand-Einstellung uebernimmt vom Patch
            fx_send(b, "eq" if name == "cho" else "cho")
        fx_send(b, name)
    return f


# ---------------- Kanal ----------------
P_LVL = P("LEVEL", rCH("lvl"), 0.0, 2.0, 0.02, apply=lambda: apply_level(S["cur"]), key="lvl", short="LVL")
P_PAN = P("PAN", rCH("pan"), 0.0, 1.0, 0.02, bip=True, apply=lambda: apply_pan(S["cur"]), key="pan", short="PAN")
P_MUTE = P("MUTE", rCH("mute"), kind=BOOL, apply=_mute_changed)
P_BUS = P("BUS", rCH("bus"), 0, 3, 1, "%d", apply=_bus_changed)
P_VO = P("STIMMEN", rCH("vo"), 1, 8, 1, "%d", apply=_vo_changed,
         vis=lambda: cur_patch() != -1 and not is_drum(cur_patch()))
P_CHORD = P("AKKORD", rCH("chord"), kind=ENUM, opts=CHORD_NAMES,
            apply=lambda: configure_channel(S["cur"]),
            vis=lambda: not is_drum(cur_patch()))
P_PORTA = P("PORTAMENTO", rCH("porta"), 0, 2000, 10, "%d", unit="ms",
            apply=lambda: apply_porta(S["cur"]), key="porta", short="PORT")

# ---------------- Klangformung ----------------
P_CUT = P("CUTOFF", rCH("cut"), 40.0, 16000.0, 1, fmtf=_hz, unit="Hz", log=True,
          apply=_tone(T_FILTER, apply_filter), key="cut", short="CUT", vis=_fam_in(FILTER_FAM))
P_RES = P("RESONANZ", rCH("res"), 0.5, 16.0, 0.1, "%.1f",
          apply=_tone(T_FILTER, apply_filter), key="res", short="RES", vis=_fam_in(FILTER_FAM))
P_ATT = P("ATTACK", rCH("att"), 0, 5000, 5, "%d", unit="ms",
          apply=_tone(T_ENV, apply_env), key="att", short="ATT", vis=_fam_in(ENV_FAM))
P_DEC = P("DECAY", rCH("dec"), 0, 10000, 10, "%d", unit="ms",
          apply=_tone(T_ENV, apply_env), key="dec", short="DEC", vis=_fam_in(ENV_FAM))
P_SUS = P("SUSTAIN", rCH("sus"), 0.0, 1.0, 0.02,
          apply=_tone(T_ENV, apply_env), key="sus", short="SUS", vis=_fam_in(ENV_FAM))
P_REL = P("RELEASE", rCH("rel"), 0, 10000, 10, "%d", unit="ms",
          apply=_tone(T_ENV, apply_env), key="rel", short="REL", vis=_fam_in(ENV_FAM))
P_LFR = P("LFO RATE", rCH("lfr"), 0.05, 20.0, 1, "%.2f", unit="Hz", log=True,
          apply=_tone(T_LFO, apply_lfo), key="lfr", short="LFOR", vis=_fam_in(LFO_FAM))
P_LFD = P("LFO TIEFE", rCH("lfd"), 0.0, 1.0, 0.02,
          apply=_tone(T_LFO, apply_lfo), key="lfd", short="LFOD", vis=_fam_in(LFO_FAM))
P_ALG = P("ALGORITHMUS", rCH("alg"), 1, 32, 1, "%d",
          apply=_tone(T_DX, apply_dx), vis=_fam_in(("DX7",)))
P_FB = P("FEEDBACK", rCH("fb"), 0, 7, 1, "%d",
         apply=_tone(T_DX, apply_dx), vis=_fam_in(("DX7",)))

# ---------------- Effekte (Bus aus fx_bus()) ----------------
P_RVL = P("REV LEVEL", rFX("rv", 0), 0.0, 1.0, 0.02, apply=_fx("rv"), key="rvL", short="REV")
P_RVV = P("REV LIVE", rFX("rv", 1), 0.0, 1.0, 0.02, apply=_fx("rv"), key="rvV", short="LIVE")
P_RVD = P("REV DAMP", rFX("rv", 2), 0.0, 1.0, 0.02, apply=_fx("rv"), key="rvD", short="DAMP")
P_RVX = P("REV XOVER", rFX("rv", 3), 200.0, 8000.0, 50, fmtf=_hz, unit="Hz",
          apply=_fx("rv"), key="rvX", short="XOVR")
P_CHL = P("CHO LEVEL", rFX("cho", 0), 0.0, 1.0, 0.02, apply=_fx("cho"), key="chL", short="CHO")
P_CHR = P("CHO RATE", rFX("cho", 1), 0.05, 10.0, 0.05, "%.2f", unit="Hz", apply=_fx("cho"), key="chR", short="CRAT")
P_CHD = P("CHO DEPTH", rFX("cho", 2), 0.0, 1.0, 0.02, apply=_fx("cho"), key="chD", short="CDEP")
P_CHM = P("CHO DELAY", rFX("cho", 3), 50.0, CHORUS_MAX_DELAY, 8, fmtf=_hz, apply=_fx("cho"), key="chM", short="CDEL")
P_ECL = P("ECHO LEVEL", rFX("ech", 0), 0.0, 1.0, 0.02, apply=_fx("ech"), key="ecL", short="ECHO")
P_ECT = P("ECHO ZEIT", rFX("ech", 1), 10, ECHO_MAX_DELAY_MS, 10, "%d", unit="ms", apply=_fx("ech"), key="ecT", short="ETIM")
P_ECF = P("ECHO FDBK", rFX("ech", 2), 0.0, 0.95, 0.02, apply=_fx("ech"), key="ecF", short="EFB")
P_ECC = P("ECHO FILT", rFX("ech", 3), -1.0, 1.0, 0.05, bip=True, apply=_fx("ech"), key="ecC", short="EFLT")
P_EQL = P("EQ LOW", rFX("eq", 0), -15.0, 15.0, 0.5, "%+.1f", unit="dB", bip=True, apply=_eq_changed, key="eqL", short="LOW")
P_EQM = P("EQ MID", rFX("eq", 1), -15.0, 15.0, 0.5, "%+.1f", unit="dB", bip=True, apply=_eq_changed, key="eqM", short="MID")
P_EQH = P("EQ HIGH", rFX("eq", 2), -15.0, 15.0, 0.5, "%+.1f", unit="dB", bip=True, apply=_eq_changed, key="eqH", short="HIGH")
P_PROF = P("KLANGPROFIL", kind=ENUM, opts=PROFILE_NAMES,
           getter=lambda: S["fx"][fx_bus()]["prof"],
           setter=lambda v: set_profile(fx_bus(), v))
def _pfx_changed():
    b = fx_bus()
    if S["fx"][b]["pfx"]:
        reload_bus_patches(b)
    else:
        fx_send(b, "cho")
        fx_send(b, "eq")


P_PFX = P("PATCH-FX", lambda: (S["fx"][fx_bus()], "pfx"), kind=BOOL, apply=_pfx_changed)
P_DST = P("TYP", rFX("dst", 0), kind=ENUM, opts=DIST_TYPES, apply=_fx("dst"))
P_DSD = P("BUS DRIVE", rFX("dst", 1), DIST_DRIVE_MIN, DIST_DRIVE_MAX, 1, "%.1f", log=True,
          apply=_fx("dst"), key="dsD", short="DRV",
          vis=lambda: DIST_OK and S["fx"][fx_bus()]["dst"][0] != 0)
P_DSM = P("DIST MIX", rFX("dst", 2), 0.0, 1.0, 0.05, apply=_fx("dst"),
          vis=lambda: S["fx"][fx_bus()]["dst"][0] != 0)
P_MASTER = P("MASTER", rS("master"), 0.0, 2.0, 0.02, apply=apply_master_volume, key="master", short="MAST")
P_CRUSH = P("CRUSH BITS", rS("crush"), kind=ENUM,
            opts=["AUS", "12", "10", "8", "6", "4", "3", "2"], apply=apply_crush)
P_CRATE = P("CRUSH RATE", rS("crate"), kind=ENUM,
            opts=["1x", "2x", "3x", "4x", "6x", "8x", "12x", "16x"], apply=apply_crush)

# ---------------- Sequencer global ----------------
P_TEMPO = P("TEMPO", rS("tempo"), 20, 300, 1, "%d", unit="BPM", apply=apply_tempo, key="tempo", short="BPM")
P_SWING = P("SWING", rS("swing"), 0, 100, 5, "%d", unit="%", key="swing", short="SWNG")
P_CLOCK = P("CLOCK", rS("clock"), kind=ENUM, opts=SEQ_CLOCK_NAMES, apply=apply_clock)
P_TRANSPORT = P("TRANSPORT", rS("transport"), kind=ENUM, opts=["EIGEN", "AMY"],
                apply=lambda: apply_transport())
P_M5 = P("M5 SCHALTER", rS("m5"), kind=ENUM, opts=["AUS", "SEQ"])


# ---------------- Spur 1-4 ----------------
def _sel():
    return S["sel"] % 4


def _trk_release():
    seq_release(_sel())


def _steps_changed():
    t = S["trk"][_sel()]
    t["pul"] = min(t["pul"], t["steps"])


def _latch_changed():
    t = S["trk"][_sel()]
    if not t["latch"]:
        arp_clear(t["ain"])


def _pat_get(i):
    # zeigt ein vorgemerktes Pattern (Wechsel am Durchlaufende) an
    def g():
        k = _sel() if i is None else i
        rt = RTS[k]
        return rt.pending if rt.pending is not None else trk_cfg(k)["pat"]
    return g


TP_MODE = P("MODUS", rT("mode"), kind=ENUM, opts=SEQ_MODES, apply=_trk_release)
TP_PAT = P("PATTERN", kind=ENUM, opts=PATTERN_NAMES, getter=_pat_get(None),
           setter=lambda v: track_set_pattern(_sel(), v))
TP_CH = P("KANAL", rT("ch"), 1, 16, 1, "%d", apply=_trk_release)
TP_STEPS = P("STEPS", rT("steps"), 1, SEQ_MAX_STEPS, 1, "%d", apply=_steps_changed)
TP_DIV = P("TEILUNG", rT("div"), kind=ENUM, opts=SEQ_DIV_NAMES)
TP_NOTE = P("NOTE", rT("note"), 0, 127, 1, fmtf=note_name)
TP_GATE = P("GATE", rT("gate"), 1, 48, 1, "%d", unit="t")
TP_PUL = P("PULSE", rT("pul"), 0, SEQ_MAX_STEPS, 1, "%d",
           vis=lambda: S["trk"][_sel()]["mode"] == 1, apply=_steps_changed)
TP_SCALE = P("SKALA", rT("scale"), kind=ENUM, opts=SCALE_NAMES,
             vis=lambda: S["trk"][_sel()]["mode"] in (1, 2))
TP_ADIR = P("ARP RICHTUNG", rT("adir"), kind=ENUM, opts=ARP_DIRS,
            vis=lambda: S["trk"][_sel()]["mode"] == 3)
TP_AOCT = P("ARP OKTAVEN", rT("aoct"), 1, 3, 1, "%d", vis=lambda: S["trk"][_sel()]["mode"] == 3)
TP_AIN = P("ARP EIN", rT("ain"), 1, 16, 1, "K%d", vis=lambda: S["trk"][_sel()]["mode"] == 3)
TP_LATCH = P("LATCH", rT("latch"), kind=BOOL, apply=_latch_changed,
             vis=lambda: S["trk"][_sel()]["mode"] == 3)
TP_OUT = P("AUSGANG", rT("out"), kind=ENUM, opts=SEQ_OUT_NAMES, apply=_trk_release)
TP_MCH = P("MIDI-KANAL", rT("mch"), 1, 16, 1, "%d", apply=_trk_release,
           vis=lambda: S["trk"][_sel()]["out"] > 0)
TP_MUTE = P("MUTE", rT("mute"), kind=BOOL, apply=_trk_release)


# ---------------- 303 ----------------
AP_PAT = P("PATTERN", kind=ENUM, opts=PATTERN_NAMES, getter=_pat_get(ACID),
           setter=lambda v: track_set_pattern(ACID, v))
AP_WAVE = P("WELLE", rA("wave"), kind=ENUM, opts=ACID_WAVE_NAMES, apply=lambda: acid_apply("wave"))
AP_CUT = P("303 CUTOFF", rA("cut"), ACID_CUT_MIN, ACID_CUT_MAX, 1, fmtf=_hz, unit="Hz",
           log=True, apply=lambda: acid_apply("filter"), key="acut", short="303C")
AP_RESO = P("303 RESO", rA("reso"), 0.5, 8.0, 0.1, "%.1f", apply=lambda: acid_apply("filter"), key="ares", short="303R")
AP_ENV = P("303 ENV MOD", rA("env"), 0.0, 7.0, 0.1, "%.1f", apply=lambda: acid_apply("filter"), key="aenv", short="303E")
AP_DEC = P("303 DECAY", rA("dec"), 30, 2500, 10, "%d", unit="ms", apply=lambda: acid_apply("dec"), key="adec", short="303D")
AP_ACC = P("303 ACCENT", rA("acc"), 0.0, 1.0, 0.05, apply=lambda: acid_apply("filter"), key="aacc", short="303A")
AP_SLIDE = P("SLIDE", rA("slide"), 10, 500, 5, "%d", unit="ms", apply=lambda: acid_apply("slide"))
AP_TUNE = P("TUNE", rA("tune"), -12, 12, 1, "%+d")
AP_ROOT = P("GRUNDTON", rA("root"), 24, 72, 1, fmtf=note_name)
AP_LVL = P("303 LEVEL", rA("lvl"), 0.0, 1.5, 0.02, apply=lambda: acid_apply("lvl"), key="alvl", short="303L")
AP_STEPS = P("STEPS", rA("steps"), 1, ACID_STEPS_MAX, 1, "%d")
AP_OUT = P("AUSGANG", rA("out"), kind=ENUM, opts=SEQ_OUT_NAMES, apply=lambda: seq_release(ACID))
AP_MCH = P("MIDI-KANAL", rA("mch"), 1, 16, 1, "%d", apply=lambda: seq_release(ACID),
           vis=lambda: S["acid"]["out"] > 0)
AP_MUTE = P("MUTE", rA("mute"), kind=BOOL, apply=lambda: seq_release(ACID))
AP_CVACC = P("CV ACCENT", rA("cvacc"), kind=ENUM, opts=["5V", "8V"])
AP_DT = P("DISTORTION", rA("dt"), kind=ENUM, opts=DIST_TYPES,
          apply=lambda: acid_apply("dist"), vis=lambda: DIST_OK)
AP_DD = P("303 DRIVE", rA("dd"), DIST_DRIVE_MIN, DIST_DRIVE_MAX, 1, "%.1f", log=True,
          apply=lambda: acid_apply("dist"), key="adrv", short="303X",
          vis=lambda: DIST_OK and S["acid"]["dt"] != 0)
AP_DM = P("303 DIST MIX", rA("dm"), 0.0, 1.0, 0.05,
          apply=lambda: acid_apply("dist"), vis=lambda: DIST_OK and S["acid"]["dt"] != 0)


def _acid_joy_changed():
    if S["acid"]["joy"]:
        toast("303 JOYSTICK", "KNOPF=UEBERNEHM.", 1800)
    else:
        _acid_mod_apply({})


AP_JOY = P("JOYSTICK>303", rA("joy"), kind=BOOL, apply=_acid_joy_changed,
           vis=lambda: joystick_available)
AP_JX = P("JOY X", rA("jx"), kind=ENUM, opts=ACID_JOY_TARGETS,
          vis=lambda: joystick_available and S["acid"]["joy"])
AP_JY = P("JOY Y", rA("jy"), kind=ENUM, opts=ACID_JOY_TARGETS,
          vis=lambda: joystick_available and S["acid"]["joy"])
AP_JD = P("JOY TIEFE", rA("jd"), 10, 100, 5, "%d", unit="%",
          vis=lambda: joystick_available and S["acid"]["joy"])


# ---------------- Drums ----------------
# DRM_UI: [gewaehltes Instrument, PULSE fuer EUCLID SETZEN]
# (Bedienzustand, wird nicht gespeichert)
DRM_UI = [0, 4]


def _drm_release():
    seq_release(DRUM)


def _drm_ins_ref(key):
    return lambda: (S["drm"][key], DRM_UI[0])


def _drm_note_txt(n):
    return "%d %s" % (n, drum_label(n))


def _drm_ins_names():
    return ["%d %s" % (k + 1, drum_row_label(k)) for k in range(DRUM_ROWS)]


DP_INS = P("INSTRUMENT", lambda: (DRM_UI, 0), kind=ENUM, opts=_drm_ins_names)


# Drumkit der Spur = Patch auf ihrem KANAL
def _kit_get():
    p = S["pat"][S["drm"]["ch"]]
    return p if is_drum(p) else -1


def _kit_set(p):
    if p != -1:
        set_patch(S["drm"]["ch"], p)     # entprellt: laedt nach 120 ms Ruhe


DP_KIT = P("DRUMKIT", kind=ENUM, opts=["---"] + list(DRUM_KIT_NAMES),
           vals=[-1] + DRUM_KITS, getter=_kit_get, setter=_kit_set)


# Klang eines Instruments: GM-Note aus der Liste, mit Vorhoeren
_audition = [None, 0]     # (kanal, note), Note-Off-Zeit


def drum_audition(note):
    d = S["drm"]
    if d["out"] == 1:
        return            # nur MIDI - intern nichts vorhoeren
    ch = d["ch"]
    try:
        if _audition[0] is not None and not is_drum(S["pat"][_audition[0][0]]):
            amy.send(synth=_audition[0][0], note=_audition[0][1], vel=0)
        amy.send(synth=ch, note=note, vel=0.8)
        _audition[0] = (ch, note)
        _audition[1] = time.ticks_add(now(), 150)
    except Exception as e:
        print("AUDITION", e)


def service_audition():
    if _audition[0] is not None and since(_audition[1]) >= 0:
        ch, note = _audition[0]
        _audition[0] = None
        if is_drum(S["pat"][ch]):
            return        # Kit ignoriert Note-Offs
        try:
            amy.send(synth=ch, note=note, vel=0)
        except Exception:
            pass


def _sound_set(n):
    S["drm"]["notes"][DRM_UI[0]] = n
    _drm_release()
    drum_audition(n)


def _sound_vals():
    # nur Noten, die das Kit auf dem Spur-Kanal wirklich belegt; eine
    # andere (per NOTE eingestellte) Note bleibt in der Liste sichtbar
    kit = S["pat"][S["drm"]["ch"]]
    vals = list(KIT_NOTES_808 if kit == DRUM_PATCH else KIT_NOTES_ALL)
    n = S["drm"]["notes"][DRM_UI[0]]
    if n not in vals:
        vals.append(n)
        vals.sort()
    return vals


def _sound_opts():
    return [GM_DRUM_NAME.get(n, "NOTE %d" % n) for n in _sound_vals()]


DP_SOUND = P("SOUND", kind=ENUM, opts=_sound_opts, vals=_sound_vals,
             getter=lambda: S["drm"]["notes"][DRM_UI[0]], setter=_sound_set)
DP_NOTE = P("NOTE", _drm_ins_ref("notes"), 0, 127, 1, fmtf=_drm_note_txt, apply=_drm_release)
DP_LEN = P("LAENGE", _drm_ins_ref("lens"), 1, SEQ_MAX_STEPS, 1, "%d")
DP_IMUTE = P("INSTR. MUTE", _drm_ins_ref("mutes"), kind=BOOL)
DP_PUL = P("PULSE", lambda: (DRM_UI, 1), 0, SEQ_MAX_STEPS, 1, "%d")
DP_PAT = P("PATTERN", kind=ENUM, opts=PATTERN_NAMES, getter=_pat_get(DRUM),
           setter=lambda v: track_set_pattern(DRUM, v))
DP_DIV = P("TEILUNG", rD("div"), kind=ENUM, opts=SEQ_DIV_NAMES)
DP_CH = P("KANAL", rD("ch"), 1, 16, 1, "%d", apply=_drm_release)
DP_OUT = P("AUSGANG", rD("out"), kind=ENUM, opts=SEQ_OUT_NAMES, apply=_drm_release)
DP_MCH = P("MIDI-KANAL", rD("mch"), 1, 16, 1, "%d", apply=_drm_release,
           vis=lambda: S["drm"]["out"] > 0)
DP_MUTE = P("SPUR MUTE", rD("mute"), kind=BOOL, apply=_drm_release)


# CV-Trigger
def _trig_opts():
    return ["AUS"] + _drm_ins_names()


def _trig_changed(out):
    def f():
        drum_trig_all_off()
        cvmod_service()
        if S["drm"]["trg"][out] >= 0 and not drum_out_free(out):
            toast("OUT%d BELEGT" % (out + 1), "MODULAR PRUEFEN", 1800)
    return f


DP_TRG = [P("TRIG OUT%d" % (o + 1), (lambda o=o: (S["drm"]["trg"], o)), kind=ENUM,
            opts=_trig_opts, vals=list(range(-1, DRUM_ROWS)), apply=_trig_changed(o))
          for o in range(2)]
DP_TLEN = P("TRIG LAENGE", rD("tlen"), 1, 8, 1, "%d", unit="/32")
DP_TLV = P("TRIG PEGEL", rD("tlv"), kind=ENUM, opts=DRUM_TRIG_NAMES)

# Grids
DP_GM = P("GRIDS", rD("gm"), kind=ENUM, opts=GRID_MODE_NAMES)
DP_GX = P("GRIDS X", rD("gx"), 0.0, 1.0, 0.02, key="gx", short="GRDX")
DP_GY = P("GRIDS Y", rD("gy"), 0.0, 1.0, 0.02, key="gy", short="GRDY")
DP_GZ = P("ZUFALL", rD("gz"), 0, 15, 1, "%d")
DP_GDEN = P("DICHTE", _drm_ins_ref("gd"), 0, 15, 1, "%d")
DP_GD = [P("DICHTE %d" % (k + 1), (lambda k=k: (S["drm"]["gd"], k)), 0, 15, 1, "%d")
         for k in range(DRUM_ROWS)]
DP_GCV = P("CV IN1/2>XY", rD("gcv"), kind=BOOL)
DP_GJ = P("JOYSTICK>XY", rD("gj"), kind=BOOL, vis=lambda: joystick_available)

# ---------------- Modular ----------------
P_EUR = P("MODUS", rS("eur"), kind=ENUM, opts=EUR_MODE_NAMES, vals=EUR_MODE_VALUES,
          confirm=True, apply=apply_eurorack_mode)
P_QSCALE = P("SKALA", rS("qscale"), kind=ENUM, opts=SCALE_NAMES,
             vis=lambda: S["eur"] == EUR_QUANTIZE)
P_CV1 = P("CV MOD OUT1", rL("cvsrc", 0), kind=ENUM, opts=CVMOD_SOURCE_NAMES,
          apply=lambda: cvmod_service(True))
P_CV2 = P("CV MOD OUT2", rL("cvsrc", 1), kind=ENUM, opts=CVMOD_SOURCE_NAMES,
          apply=lambda: cvmod_service(True))
P_LFOW = P("LFO WELLE", rL("lfo", 0), kind=ENUM, opts=CVMOD_WAVE_NAMES, apply=cvmod_update_lfo)
P_LFOR = P("CV LFO RATE", rL("lfo", 1), 0.05, 20.0, 1, "%.2f", unit="Hz", log=True,
           apply=cvmod_update_lfo, key="lfoR", short="CVLR")
P_LFOD = P("CV LFO TIEFE", rL("lfo", 2), 0.0, 1.0, 0.05, apply=cvmod_update_lfo, key="lfoD", short="CVLD")
P_ENVA = P("ENV ATTACK", rL("env", 0), 1, 5000, 5, "%d", unit="ms", apply=cvmod_update_env)
P_ENVR = P("ENV RELEASE", rL("env", 1), 1, 5000, 5, "%d", unit="ms", apply=cvmod_update_env)
P_ENVD = P("ENV TIEFE", rL("env", 2), 0.0, 1.0, 0.05, apply=cvmod_update_env)

# Wavefolder CV LFO / CV ENV (v13.20)
def _lfof_on():
    return DIST_OK and S["lfof"][0] != 0


def _envf_on():
    return DIST_OK and S["envf"][0] != 0


P_LFFT = P("FOLD", rL("lfof", 0), kind=ENUM, opts=DIST_TYPES, apply=cvfold_apply,
           vis=lambda: DIST_OK)
P_LFFD = P("LFO DRIVE", rL("lfof", 1), DIST_DRIVE_MIN, DIST_DRIVE_MAX, 1, "%.1f", log=True,
           apply=cvfold_apply, key="lfoF", short="CVLF", vis=_lfof_on)
P_LFFM = P("FOLD MIX", rL("lfof", 2), 0.0, 1.0, 0.05, apply=cvfold_apply, vis=_lfof_on)
P_LFFS = P("FOLD MOD", rL("lfof", 3), kind=ENUM, opts=FOLD_MOD_NAMES, apply=cvfold_apply,
           vis=_lfof_on)
P_LFFA = P("MOD TIEFE", rL("lfof", 4), 0.0, 1.0, 0.05,
           vis=lambda: _lfof_on() and S["lfof"][3] != 0)
P_ENFT = P("FOLD", rL("envf", 0), kind=ENUM, opts=DIST_TYPES, apply=cvfold_apply,
           vis=lambda: DIST_OK)
P_ENFD = P("ENV DRIVE", rL("envf", 1), DIST_DRIVE_MIN, DIST_DRIVE_MAX, 1, "%.1f", log=True,
           apply=cvfold_apply, key="envF", short="CVEF", vis=_envf_on)
P_ENFM = P("FOLD MIX", rL("envf", 2), 0.0, 1.0, 0.05, apply=cvfold_apply, vis=_envf_on)


def _cal_changed():
    _last_cv[0] = None
    _last_cv[1] = None
    cv_write(0, cv_out_v[0])
    cv_write(1, cv_out_v[1])


_CAL_TEST_V = [None, 0.0, 1.0, 2.0, 3.0, 4.0]
_cal_ui = [0]


def _calin_changed():
    # Eingangs-Kalibrierung geaendert: AMY-Wege neu setzen (VCO, GATE+PITCH)
    if _vco_running:
        try:
            _vco_send_freq()
            _vco_send_duty()
        except Exception as e:
            print("CALIN VCO", e)
    if _eur_mode == EUR_GATE_PITCH and cal_test is None:
        apply_eurorack_mode()


def _cv_mean(ch, ms=300):
    acc = 0.0
    n = 0
    t0 = now()
    while since(t0) < ms:
        try:
            acc += amyboard.cv_in(channel=ch)
            n += 1
        except Exception:
            pass
        time.sleep_ms(6)
    return acc / n if n else None


def cal_in_auto(ch):
    # OUT1 gibt 1 V und 3 V aus, INx misst roh; daraus Skala und Versatz
    name = "IN%d" % (ch + 1)
    toast(name + " ABGLEICH", "MISST...", 4000)
    render(force=True)
    r = []
    for v in (1.0, 3.0):
        set_cal_test(v)
        time.sleep_ms(250)
        r.append(_cv_mean(ch))
    set_cal_test(_CAL_TEST_V[_cal_ui[0]])
    if r[0] is None or r[1] is None or r[1] - r[0] < 1.2:
        toast(name + " ABGLEICH", "KEIN SIGNAL?", 2500)
        return
    s = 2.0 / (r[1] - r[0])
    o = 1.0 - s * r[0]
    if not (0.8 <= s <= 1.25 and -1.0 <= o <= 1.0):
        toast(name + " ABGLEICH", "WERTE UNPLAUSIBEL", 2500)
        return
    S["calin"][ch] = [round(o, 3), round(s, 4)]
    _calin_changed()
    request_save()
    toast(name + " OK", "%+.3fV x%.3f" % (o, s), 2500)


def _cal_test_changed():
    set_cal_test(_CAL_TEST_V[_cal_ui[0]])


P_CAL = [
    P("OUT1 OFFSET", lambda: (S["cal"][0], 0), -0.5, 0.5, 0.002, "%+.3f", unit="V", bip=True, apply=_cal_changed),
    P("OUT1 SKALA", lambda: (S["cal"][0], 1), 0.9, 1.1, 0.001, "%.3f", apply=_cal_changed),
    P("OUT2 OFFSET", lambda: (S["cal"][1], 0), -0.5, 0.5, 0.002, "%+.3f", unit="V", bip=True, apply=_cal_changed),
    P("OUT2 SKALA", lambda: (S["cal"][1], 1), 0.9, 1.1, 0.001, "%.3f", apply=_cal_changed),
    P("TESTSPANNUNG", lambda: (_cal_ui, 0), kind=ENUM,
      opts=["AUS", "0V C1", "1V C2", "2V C3", "3V C4", "4V C5"], apply=_cal_test_changed),
    P("IN1 OFFSET", lambda: (S["calin"][0], 0), -1.0, 1.0, 0.002, "%+.3f", unit="V", bip=True,
      apply=_calin_changed),
    P("IN1 SKALA", lambda: (S["calin"][0], 1), 0.8, 1.25, 0.001, "%.3f", apply=_calin_changed),
    P("IN2 OFFSET", lambda: (S["calin"][1], 0), -1.0, 1.0, 0.002, "%+.3f", unit="V", bip=True,
      apply=_calin_changed),
    P("IN2 SKALA", lambda: (S["calin"][1], 1), 0.8, 1.25, 0.001, "%.3f", apply=_calin_changed),
]

# ---------------- Szenen ----------------
P_MORPH = P("MORPH A>B", rS("mx"), 0.0, 1.0, 0.02, apply=request_morph, key="morph", short="MRPH")
P_MA = P("MORPH A", rS("mA"), kind=ENUM, opts=["1", "2", "3", "4", "5", "6", "7", "8"], apply=request_morph)
P_MB = P("MORPH B", rS("mB"), kind=ENUM, opts=["1", "2", "3", "4", "5", "6", "7", "8"], apply=request_morph)

# ---------------- System ----------------
P_AUDIO = P("AUDIO", rS("audio"), kind=ENUM, opts=["STEREO", "MONO"], apply=apply_audio_mode)
P_VBUD = P("STIMMEN MAX", rS("vbud"), 8, 64, 1, "%d")
P_FAIL = P("FAILSAFE", rS("fail"), kind=ENUM,
           opts=["AUS", "0.80", "0.85", "0.90", "0.95", "1.00"], apply=apply_failsafe)
P_INV = P("DREHRICHTUNG", rS("inv"), kind=ENUM, opts=["NORMAL", "INVERT"])
P_THRU = P("MIDI THRU", rS("thru"), kind=BOOL)
P_MTYPE = P("MIDI OUT TYP", rS("mtype"), kind=ENUM, opts=["A", "B"], apply=apply_midi_type)
P_CCT = P("LERN-ZIEL", rS("cct"), kind=ENUM, opts=CC_TARGET_NAMES)


def apply_bright():
    # SSD1327-Kontrast (0-255) ueber den Treiber von amyboard.display
    if HAS_CONTRAST:
        display_contrast(S["bright"])


P_BRIGHT = P("HELLIGKEIT", rS("bright"), 30, 255, 15, "%d", apply=apply_bright,
             vis=lambda: HAS_CONTRAST)
P_DIM = P("SCHONER NACH", rS("dim"), kind=ENUM, vals=[0, 1, 2, 5, 10, 30],
          opts=["AUS", "1 MIN", "2 MIN", "5 MIN", "10 MIN", "30 MIN"])


def _timer_update():
    if timer_wanted():
        notlauf_start()
        apply_transport()
    else:
        apply_transport()
        notlauf_stop()


P_NOTLAUF = P("NOTLAUF", rS("notlauf"), kind=ENUM, opts=["AUS", "AN"], apply=_timer_update,
              vis=lambda: not S["uit"])
P_UIT = P("UI-TAKT", rS("uit"), kind=ENUM, opts=["LOOP", "TIMER"], apply=_timer_update)
def voraus_test():
    # Clap jetzt, dann 2 und 4 Schlaege spaeter ueber ticks=. Klingen alle
    # drei gleichzeitig, spielt die Firmware geplante Noten sofort.
    t = _seq_ticks()
    ch = S["drm"]["ch"]
    if t is None:
        toast("VORAUS-TEST", "KEINE TICKS")
        return
    try:
        amy.send(synth=ch, note=39, vel=1)
        amy.send(synth=ch, note=39, vel=1, ticks="%d,0,%d" % (t + 96, SEQ_TAG + 1))
        amy.send(synth=ch, note=39, vel=1, ticks="%d,0,%d" % (t + 192, SEQ_TAG + 1))
        toast("VORAUS-TEST", "3 CLAPS IM TAKT?", 2500)
    except Exception as e:
        toast("VORAUS-TEST", str(e)[:14], 2500)


def _sqm_changed():
    if S["run"]:
        seq_stop()
        seq_start()


P_SQM = P("SEQ-AUSGABE", rS("sqm"), kind=ENUM, opts=["DIREKT", "VORAUS"], apply=_sqm_changed)
P_VMS = P("VORLAUF", rS("vlf"), 50, 400, 25, "%d", unit="ms", vis=lambda: S["sqm"])
P_DFAST = P("UPDATE", rS("dfast"), kind=ENUM, opts=["VOLL", "BAENDER"],
            vis=lambda: _fast_ok)



# ---------------- VCO (v13.21) ----------------

def rV(k):
    return lambda: (S["vco"], k)


def _vco_do(fn):
    # Aenderung nur senden, wenn der VCO laeuft (sonst beim Start)
    def f():
        if _vco_running:
            fn()
    return f


def _vco_pitch_changed():
    global _vco_q
    _vco_q = None
    if _vco_running:
        _vco_quant(True)
        _vco_send_freq()


def _vco_mod_changed():
    global _vco_fold_mod
    v = S["vco"]
    if not (v["mt"] == 2 and v["msrc"]):
        _vco_fold_mod = 0.0
    if _vco_running:
        _vco_send_freq()
        _vco_send_duty()
        _vco_send_fold()


def _vco_bus_changed():
    if _vco_running:
        amy.send(synth=VCO_SYNTH, bus=S["vco"]["bus"])
    refresh_buses()


def _vco_o2():
    return S["vco"]["o2"] > 0


def _vco_mod():
    return S["vco"]["msrc"] != 0


def _vco_fold_on():
    return DIST_OK and S["vco"]["ft"] != 0


P_VON = P("VCO", rV("on"), kind=BOOL, apply=vco_apply_all)
P_VSRC = P("1V/OKT IN", rV("src"), kind=ENUM, opts=VCO_IN_NAMES, apply=_vco_pitch_changed)
P_VPM = P("TONHOEHE", rV("pm"), kind=ENUM, opts=VCO_PM_NAMES, apply=_vco_pitch_changed,
          vis=lambda: S["vco"]["src"] != 0)
P_VSC = P("SKALA", rV("sc"), kind=ENUM, opts=SCALE_NAMES, apply=_vco_pitch_changed,
          vis=lambda: S["vco"]["src"] != 0 and S["vco"]["pm"] != 0)
P_VROOT = P("GRUNDTON 0V", rV("root"), 12, 96, 1, fmtf=note_name,
            apply=_vco_do(_vco_send_freq))
P_VFIN = P("VCO FEIN", rV("fine"), -100, 100, 1, "%+d", unit="ct", bip=True,
           apply=_vco_do(_vco_send_freq), key="vfin", short="VFIN")
P_VTRK = P("V/OKT", rV("trk"), 0.95, 1.05, 0.001, "%.3f", apply=_vco_pitch_changed,
           vis=lambda: S["vco"]["src"] != 0)
def _vco_wave_changed():
    # v13.27: ausblenden, Welle spaeter in vco_service wechseln
    global _vco_wave_due
    if not _vco_running:
        return
    if _vco_wave_due is None:
        amy.send(synth=VCO_SYNTH, vel=0)
    _vco_wave_due = time.ticks_add(now(), VCO_XFADE_MS)


def _vco_sm_changed():
    global _vco_sm, _vco_sm_sent
    _vco_sm = None
    _vco_sm_sent = None
    _vco_pitch_changed()


P_VWAV = P("WELLE", rV("wav"), kind=ENUM, opts=VCO_WAVE_NAMES, apply=_vco_wave_changed)
P_VSM = P("GLAETTUNG", rV("sm"), kind=ENUM, opts=["AUS", "WENIG", "STARK"], apply=_vco_sm_changed,
          vis=lambda: S["vco"]["src"] != 0 and S["vco"]["pm"] == 0)
P_VPW = P("VCO PW", rV("pw"), 0.05, 0.95, 0.01, apply=_vco_do(_vco_send_duty),
          key="vpw", short="VPW", vis=lambda: S["vco"]["wav"] == 3)
P_VSUB = P("VCO SUB", rV("sub"), 0.0, 1.0, 0.02, apply=_vco_do(_vco_send_mix),
           key="vsub", short="VSUB")
P_VSO = P("SUB OKTAVE", rV("so"), kind=ENUM, opts=["-1", "-2"], vals=[1, 2],
          apply=_vco_do(_vco_send_freq), vis=lambda: S["vco"]["sub"] > 0)
P_VO2 = P("VCO OSZ 2", rV("o2"), 0.0, 1.0, 0.02, apply=_vco_do(_vco_send_mix),
          key="vo2", short="VO2")
P_VIV = P("INTERVALL", rV("iv"), -24, 24, 1, "%+d", unit="HT",
          apply=_vco_do(_vco_send_freq), vis=_vco_o2)
P_VDET = P("VCO DETUNE", rV("det"), 0, 50, 1, "%d", unit="ct",
           apply=_vco_do(_vco_send_freq), key="vdet", short="VDET", vis=_vco_o2)
P_VMSRC = P("MOD IN", rV("msrc"), kind=ENUM, opts=VCO_IN_NAMES, apply=_vco_mod_changed)
P_VMT = P("MOD ZIEL", rV("mt"), kind=ENUM, opts=VCO_MOD_NAMES, apply=_vco_mod_changed,
          vis=_vco_mod)
P_VMD = P("VCO MOD", rV("md"), 0.0, 1.0, 0.02, apply=_vco_mod_changed,
          key="vmd", short="VMOD", vis=_vco_mod)
P_VFT = P("FOLD", rV("ft"), kind=ENUM, opts=DIST_TYPES,
          apply=_vco_do(lambda: _vco_send_fold(True)), vis=lambda: DIST_OK)
P_VFD = P("VCO DRIVE", rV("fd"), DIST_DRIVE_MIN, DIST_DRIVE_MAX, 1, "%.1f", log=True,
          apply=_vco_do(_vco_send_fold), key="vdrv", short="VDRV", vis=_vco_fold_on)
P_VFM = P("FOLD MIX", rV("fm"), 0.0, 1.0, 0.05, apply=_vco_do(_vco_send_fold),
          vis=_vco_fold_on)
P_VLVL = P("VCO LEVEL", rV("lvl"), 0.0, 1.5, 0.02, apply=_vco_do(_vco_send_out),
           key="vlvl", short="VLVL")
P_VPAN = P("PAN", rV("pan"), 0.0, 1.0, 0.02, bip=True, apply=_vco_do(_vco_send_out))
P_VBUS = P("BUS", rV("bus"), 0, 3, 1, "%d", apply=_vco_bus_changed)

# ---------------- AUDIO IN (v13.22) ----------------

def rI(k):
    return lambda: (S["ain"], k)


def _ain_do(fn):
    # Aenderung nur senden, wenn der Eingang laeuft (sonst beim Start)
    def f():
        if _ain_running:
            fn()
    return f


def _ain_mode_changed():
    if _ain_running:
        _ain_send_gain()
        _ain_send_out()
        _ain_send_gate()


def _ain_bus_changed():
    if _ain_running:
        for s in AIN_SYNTHS:
            amy.send(synth=s, bus=S["ain"]["bus"])
    refresh_buses()


def _ain_filt_on():
    return S["ain"]["ft"] != 0


def _ain_dist_on():
    return DIST_OK and S["ain"]["dt"] != 0


P_AON = P("AUDIO IN", rI("on"), kind=BOOL, apply=ain_apply_all)
P_AMODE = P("MODUS", rI("mode"), kind=ENUM, opts=AIN_MODE_NAMES, apply=_ain_mode_changed)
P_AGAIN = P("IN GAIN", rI("gain"), AIN_GAIN_MIN, AIN_GAIN_MAX, 0.5, "%+.1f", unit="dB",
            apply=_ain_do(_ain_send_gain), key="igain", short="IGN")
P_ALVL = P("IN LEVEL", rI("lvl"), 0.0, 1.5, 0.02, apply=_ain_do(_ain_send_out),
           key="ilvl", short="ILVL")
P_APAN = P("IN PAN", rI("pan"), 0.0, 1.0, 0.02, bip=True, apply=_ain_do(_ain_send_out),
           key="ipan", short="IPAN")
P_AWID = P("BREITE", rI("wid"), 0.0, 1.0, 0.05, apply=_ain_do(_ain_send_out),
           vis=lambda: S["ain"]["mode"] == 0)
P_ABUS = P("BUS", rI("bus"), 0, 3, 1, "%d", apply=_ain_bus_changed)
P_AFT = P("FILTER", rI("ft"), kind=ENUM, opts=SMP_FILT_NAMES,
          apply=lambda: ain_fade(_ain_send_filter))
P_ACU = P("IN CUTOFF", rI("cu"), 40.0, 16000.0, 1, fmtf=_hz, unit="Hz", log=True,
          apply=_ain_do(_ain_send_filter), key="icut", short="ICUT", vis=_ain_filt_on)
P_ARS = P("IN RESO", rI("rs"), 0.5, 16.0, 0.1, "%.1f", apply=_ain_do(_ain_send_filter),
          key="ires", short="IRES", vis=_ain_filt_on)
P_ADT = P("DISTORTION", rI("dt"), kind=ENUM, opts=DIST_TYPES,
          apply=lambda: ain_fade(_ain_send_dist), vis=lambda: DIST_OK)
P_ADD = P("IN DRIVE", rI("dd"), DIST_DRIVE_MIN, DIST_DRIVE_MAX, 1, "%.1f", log=True,
          apply=_ain_do(_ain_send_dist), key="idrv", short="IDRV", vis=_ain_dist_on)
P_ADM = P("DIST MIX", rI("dm"), 0.0, 1.0, 0.05, apply=_ain_do(_ain_send_dist),
          vis=_ain_dist_on)

# ---------------- Zuordnung E1-E8 und Makros ----------------
ASSIGN_KEYS = ["master", "lvl", "pan", "cut", "res", "att", "dec", "sus", "rel",
               "lfr", "lfd", "porta", "rvL", "rvV", "rvD", "rvX", "chL", "chR",
               "chD", "chM", "ecL", "ecT", "ecF", "ecC", "eqL", "eqM", "eqH",
               "tempo", "swing", "morph", "acut", "ares", "aenv", "adec", "aacc",
               "alvl", "lfoR", "lfoD", "gx", "gy", "adrv", "dsD", "lfoF", "envF",
               "vfin", "vpw", "vsub", "vo2", "vdet", "vdrv", "vmd", "vlvl",
               "igain", "ilvl", "ipan", "icut", "ires", "idrv"]
ASSIGN_NAMES = [REG[k].label for k in ASSIGN_KEYS]


# ---------------- Patch-Wechsel per Encoder (v13.15) ----------------
# PATCH K1-K4: Drehen blaettert den Patch eines Kanals durch - im
# laufenden Betrieb. Geladen wird entprellt (set_patch: erst wenn der
# Encoder PATCH_SETTLE_MS ruht), der Sequencer laeuft weiter.

PATCH_ENC_CHANNELS = tuple(range(1, 17))
MELODIC_PATCHES = [p for p in ALL_PATCHES if not is_drum(p)]

# Patch-Listen (v13.24): 0 ALLE, 1.. Kategorien, dann FAVORITEN, DRUMKITS
PL_NAMES = ["ALLE"] + [c[0] for c in CAT_DEFS] + ["FAVORITEN", "DRUMKITS"]
PL_FAV = len(CAT_DEFS) + 1
PL_DRUM = len(CAT_DEFS) + 2
LD_NAMES = ["SOFORT", "AUF DRUCK"]
_enc_pend = {}           # Slot -> (Kanal, Patch), wartet auf den Taster


def patch_list(ch, pl):
    p = S["pat"][ch]
    if ch == DRUM_CHANNEL or is_drum(p) or pl == PL_DRUM:
        return DRUM_KITS
    if pl == 0:
        return MELODIC_PATCHES
    if pl == PL_FAV:
        return [x for x in S["fav"] if not is_drum(x)]
    return PATCH_CATS[pl - 1]


def enc_patch_ch(f):
    # Kanal einer PATCH-Funktion: pk1..pk16, pkc = aktueller Kanal
    return S["cur"] if f == "pkc" else int(f[2:])


class PatchEnc:
    own_toast = True     # zeigt selbst Kanal + Patchname
    vis = None

    def __init__(self, ch):
        self.ch = ch     # 0 = AKTUELL
        self.label = ("PATCH K%d" % ch) if ch else "PATCH AKT"
        self.short = ("PK%d" % ch) if ch else "PKA"

    def nudge(self, d, acc=1):
        self.nudge_slot(None, d, acc)

    def nudge_slot(self, sl, d, acc=1):
        ch = self.ch or S["cur"]
        if chrom_owns(ch):
            toast("K%d SAMPLER" % ch, "PATCH IM SAMPLER", 900)
            return
        x = S["encx"][sl] if sl is not None else new_encx()
        lst = patch_list(ch, x["pl"])
        if not lst:
            toast("K%d %s" % (ch, PL_NAMES[x["pl"]][:9]), "LISTE LEER", 900)
            return
        pend = _enc_pend.get(sl)
        p = pend[1] if (pend and pend[0] == ch) else S["pat"][ch]
        step = d * (4 if acc > 1 else 1)
        if p in lst:
            i = (lst.index(p) + step) % len(lst)
        else:
            # Kanal ohne Patch oder Patch nicht in der Liste: am Anfang
            i = 0 if d > 0 else len(lst) - 1
        np = lst[i]
        if x["ld"] and sl is not None:
            _enc_pend[sl] = (ch, np)
            toast("K%d > %03d DRUCK" % (ch, np), patch_name(np)[:14], 2500)
            return
        set_patch(ch, np)
        request_save()
        mark_dirty()
        toast("K%d %s %03d" % (ch, FAMILY_SHORT[family(np)], np),
              patch_name(np)[:14], 900)

    def text(self):
        return patch_name(S["pat"][self.ch or S["cur"]])[:14]


def enc_pend_load(sl):
    # AUF DRUCK: vorgemerkten Patch laden. True, wenn etwas geladen wurde.
    pend = _enc_pend.pop(sl, None)
    if pend is None:
        return False
    ch, p = pend
    set_patch(ch, p)
    commit_patch(ch)
    toast("K%d GELADEN" % ch, patch_name(p)[:14], 900)
    return True


class ChanEnc:
    # KANAL: Drehen waehlt den aktuellen MIDI-Kanal
    own_toast = True
    vis = None
    label = "KANAL"
    short = "KAN"

    def nudge(self, d, acc=1):
        on_hold_turn(1 if d > 0 else -1)

    def text(self):
        return "K%d" % S["cur"]


PATCH_ENC_KEYS = ["pkc"]
REG["pkc"] = PatchEnc(0)
for _c in PATCH_ENC_CHANNELS:
    REG["pk%d" % _c] = PatchEnc(_c)
    PATCH_ENC_KEYS.append("pk%d" % _c)
REG["chan"] = ChanEnc()

ENC_KEYS = ["AUS", "SCREEN", "chan"] + PATCH_ENC_KEYS + ASSIGN_KEYS
ENC_NAMES = (["AUS", "SEITE", "KANAL"] + [REG[k].label for k in PATCH_ENC_KEYS]
             + ASSIGN_NAMES)

# Parameter-Gruppen (v13.24) mit AUTO-LED-Farbe (Index in LED_RGB)
ENC_GROUPS = (
    ("MIXER", 4, ("master", "lvl", "pan", "porta")),
    ("KLANG", 3, ("cut", "res", "att", "dec", "sus", "rel", "lfr", "lfd")),
    ("EFFEKTE", 5, ("rvL", "rvV", "rvD", "rvX", "chL", "chR", "chD", "chM",
                    "ecL", "ecT", "ecF", "ecC", "eqL", "eqM", "eqH", "dsD")),
    ("SEQ+SZENE", 4, ("tempo", "swing", "morph")),
    ("303", 2, ("acut", "ares", "aenv", "adec", "aacc", "alvl", "adrv")),
    ("DRUMS", 3, ("gx", "gy")),
    ("MODULAR", 6, ("lfoR", "lfoD", "lfoF", "envF", "vfin", "vpw", "vsub", "vo2",
                    "vdet", "vdrv", "vmd", "vlvl")),
    ("AUDIO IN", 8, ("igain", "ilvl", "ipan", "icut", "ires", "idrv")),
)
ENC_GROUP_NAMES = [g[0] for g in ENC_GROUPS]
ENC_GROUP_OF = {}
for _gi, _g in enumerate(ENC_GROUPS):
    for _k in _g[2]:
        ENC_GROUP_OF[_k] = _gi
for _k in ASSIGN_KEYS:
    if _k not in ENC_GROUP_OF:          # neue Parameter landen sicher irgendwo
        ENC_GROUP_OF[_k] = 0

FUNC_NAMES = ["AUS", "SEITE", "PATCH", "KANAL", "PARAMETER"]
LED_NAMES = ["AUTO", "AUS", "ROT", "ORANGE", "GELB", "GRUEN", "CYAN", "BLAU",
             "LILA", "WEISS", "KANAL"]
LED_RGB = (None, (0, 0, 0), (40, 0, 0), (40, 12, 0), (32, 26, 0), (0, 36, 0),
           (0, 26, 26), (0, 0, 40), (24, 0, 34), (22, 22, 22), None)
LED_KANAL = 10           # v13.29: LED-Farbe = Farbe des Kanals
LED_IND_NAMES = LED_NAMES[:10]               # Anzeigen: AUTO, AUS, Farben
LED_NAV_NAMES = ["KANAL"] + LED_NAMES[1:10]  # Navigation: 0 = Kanalfarbe
LED_HELL = (0.5, 1.0, 2.0, 3.5)              # HELLIGKEIT 1-4 (2 = wie bisher)
SV_NAMES = ["SPRUNG", "SONAR", "TUNNEL", "TERMINAL", "FLYER", "ACID-SPUR", "SPEKTRUM", "WAREHOUSE"]   # v13.30: Schoner-Bilder


def _hue40(h):
    # Farbkreis mit Hoechstwert 40 (wie LED_RGB), h = 0..1
    k = h * 6.0
    i = int(k) % 6
    f = k - int(k)
    u = int(40 * f)
    d = int(40 * (1.0 - f))
    return ((40, u, 0), (d, 40, 0), (0, 40, u), (0, d, 40), (u, 0, 40), (40, 0, d))[i]


# Kanalfarben 1-16 einmal rund um den Farbkreis (Kanal 1 orange)
CH_RGB = [None] + [_hue40((c - 1) / 16.0 + 0.06) for c in range(1, 17)]
_led_flash = {}          # Slot -> Zeit des letzten Drehens (DREH-BLITZ)



def enc_func(f):
    if f == "AUS":
        return 0
    if f == "SCREEN":
        return 1
    if f.startswith("pk"):
        return 2
    if f == "chan":
        return 3
    return 4


def enc_group_keys(gi):
    return [k for k in ASSIGN_KEYS if ENC_GROUP_OF.get(k) == gi]


def enc_func_text(sl):
    # Kurztext der Belegung fuer die Uebersicht
    f = S["encf"][sl]
    fn = enc_func(f)
    if fn == 2:
        return ("PATCH AKT" if f == "pkc" else "PATCH K%s" % f[2:]) + (
            "*" if sl in _enc_pend else "")
    if fn == 4:
        prm = REG.get(f)
        return prm.label[:12] if prm is not None else "?"
    return FUNC_NAMES[fn]


def enc_led_index(sl):
    x = S["encx"][sl]
    if x["led"]:
        return x["led"]
    f = S["encf"][sl]
    fn = enc_func(f)
    if fn == 4:
        return ENC_GROUPS[ENC_GROUP_OF.get(f, 0)][1]
    return (1, 9, 7, 8)[fn]


# ---------------- Encoder-Sets A/B/C (v13.24) ----------------
ESET_NAMES = ["A", "B", "C"]


def eset_snapshot():
    S["esets"][S["eset"]] = {"f": list(S["encf"]), "b": list(S["encb"]),
                             "x": deep_copy(S["encx"])}


def eset_switch(n):
    eset_snapshot()
    S["eset"] = n
    sn = S["esets"][n]
    if sn:
        S["encf"] = list(sn["f"])
        S["encb"] = list(sn["b"])
        S["encx"] = deep_copy(sn["x"])
    _enc_pend.clear()
    _encf_changed()
    request_save()
    toast("ENCODER-SET", ESET_NAMES[n], 900)


def eset_next():
    eset_switch((S["eset"] + 1) % 3)


def _encf_changed():
    resync_param_encoders()
    update_leds()


P_ENCF = [P(ENC_SLOT_NAMES[i], rL("encf", i), kind=ENUM, opts=ENC_NAMES, vals=ENC_KEYS,
            apply=_encf_changed) for i in range(ENC_SLOTS)]

# Taster der Zusatz-Encoder (v13.19)
ENCB_KEYS = ["AUS", "KONTEXT", "START", "TAP", "PANIC", "MUTE1", "MUTE2", "MUTE3",
             "MUTE4", "M303", "MDRM", "AIN", "ESET"]
ENCB_NAMES = ["AUS", "KONTEXT", "START/STOP", "TAP TEMPO", "PANIC (LANG)", "MUTE K1",
              "MUTE K2", "MUTE K3", "MUTE K4", "MUTE 303", "MUTE DRUMS",
              "AUDIO IN", "ENC-SET >"]
P_ENCB = [P(ENC_SLOT_NAMES[i] + " TASTER", rL("encb", i), kind=ENUM, opts=ENCB_NAMES,
            vals=ENCB_KEYS) for i in range(ENC_SLOTS)]
P_MACRO = [P("MAKRO %d" % (i + 1), rL("macro", i), kind=ENUM, opts=ASSIGN_NAMES,
             vals=ASSIGN_KEYS) for i in range(4)]


# ================================================================
# SEITEN
# ================================================================

STACK = []
_accel = 1


def turn_accel():
    return _accel


def top():
    return STACK[-1]


def push(p):
    STACK.append(p)
    p.enter()
    mark_dirty()


def pop():
    if len(STACK) > 1:
        p = STACK.pop()
        p.leave()
        STACK[-1].resume()
        mark_dirty()


def go_home():
    while len(STACK) > 1:
        pop()


class Page:
    status = True
    custom = False

    def enter(self):
        pass

    def resume(self):
        pass

    def leave(self):
        pass

    def turn(self, d):
        pass

    def vturn(self, d):
        # Joystick hoch/runter - nur Seiten mit Zeilen nutzen es
        pass

    def press(self):
        pass

    def back(self):
        return False

    def draw(self):
        pass

    def tick(self):
        return False

    def enc_param(self, i):
        return None


# ---------------------------------------------------------------
# Liste mit Parametern
# ---------------------------------------------------------------

class ListPage(Page):
    def __init__(self, title, items, on_enter=None, on_leave=None, right=None):
        self.title = title
        self._items = items
        self.cur = 0
        self.edit = False
        self.start = None
        self.tmp = 0
        self.on_enter = on_enter
        self.on_leave = on_leave
        self.right = right
        self.y0 = 28
        self.n = 7
        self.rh = 12

    def items(self):
        its = self._items() if callable(self._items) else self._items
        return [it for it in its if it.vis is None or it.vis()]

    def ttl(self):
        return self.title() if callable(self.title) else self.title

    def enter(self):
        if self.on_enter:
            self.on_enter()

    def leave(self):
        if self.on_leave:
            self.on_leave()

    def _sel(self, its):
        if not its:
            return None
        if self.cur >= len(its):
            self.cur = len(its) - 1
        return its[self.cur]

    def turn(self, d):
        its = self.items()
        it = self._sel(its)
        if it is None:
            return
        if self.edit:
            if it.confirm:
                self.tmp = (self.tmp + d) % len(it.options())
            else:
                it.nudge(d)
        else:
            self.cur = (self.cur + d) % len(its)

    def press(self):
        it = self._sel(self.items())
        if it is None:
            return
        k = it.kind
        if k == NUM:
            push(EditPage(it, self.ttl()))
        elif k == ENUM:
            if not self.edit:
                self.edit = True
                self.start = it.get()
                self.tmp = it.index()
            else:
                if it.confirm:
                    it.set(it.value_at(self.tmp))
                self.edit = False
        elif k == BOOL:
            it.nudge(1)
        elif k == ACT:
            it.act()
        elif k == LINK:
            push(it.page())

    def back(self):
        if self.edit:
            it = self._sel(self.items())
            if it is not None and not it.confirm and it.get() != self.start:
                it.set(self.start)
            self.edit = False
            return True
        return False

    def enc_param(self, i):
        nums = [it for it in self.items() if it.kind == NUM]
        return nums[i] if i < len(nums) else None

    def draw_head(self):
        draw_title(self.ttl(), self.right() if self.right else "")

    def draw(self):
        its = self.items()
        self.draw_head()
        rows = []
        for j in range(len(its)):
            it = its[j]
            if self.edit and j == self.cur and it.confirm:
                rows.append((it.label, it.text(self.tmp)))
            else:
                rows.append((it.label, it.text()))
        if not rows:
            TC("LEER", 64, 60, DIM)
            return
        draw_rows(rows, self.cur, self.y0, self.n, self.rh, self.edit)
        self.draw_foot(self._sel(its))

    def draw_foot(self, it):
        y = 118
        if self.edit:
            TC("OK=AKTIVIEREN" if it.confirm else "DREHEN, OK", 64, y, DIM)
        elif it.kind == NUM:
            if it.bip:
                bipbar(3, y + 2, 120, 3, it.frac(), MID)
            else:
                bar(3, y + 2, 120, 3, it.frac(), MID)
        elif it.kind == ACT:
            TC("DRUECKEN", 64, y, DIM)


def link(label, factory, info=None, vis=None):
    return P(label, kind=LINK, page=factory, info=info, vis=vis)


def action(label, fn, info=None, vis=None):
    return P(label, kind=ACT, act=fn, info=info, vis=vis)


def infoline(label, fn, vis=None):
    return P(label, kind=INFO, info=fn, vis=vis)


# ---------------------------------------------------------------
# Wert bearbeiten: grosser Ring
# ---------------------------------------------------------------

class EditPage(Page):
    def __init__(self, item, crumb):
        self.item = item
        self.crumb = crumb
        self.start = None

    def enter(self):
        self.start = self.item.get()

    def turn(self, d):
        self.item.nudge(d, turn_accel())

    def press(self):
        pop()

    def back(self):
        if self.item.get() != self.start:
            self.item.set(self.start)
        return False

    def enc_param(self, i):
        return self.item if i == 0 else None

    def draw(self):
        it = self.item
        T(self.crumb[:15], 3, 14, DIM)
        ring(64, 68, 36, it.frac(), 4, 1, it.bip)
        s = it.num_text()
        if len(s) * 16 <= 64:
            BIGC(s, 64, 58, 2, W)
        else:
            TC(s, 64, 62, W)
        if it.unit:
            TC(it.unit, 64, 80, MID)
        TC(it.label[:14], 64, 104, HI)
        TC("LANG = ABBRUCH", 64, 118, DIM)


# ---------------------------------------------------------------
# Bestaetigen / Texteingabe
# ---------------------------------------------------------------

class Confirm(Page):
    def __init__(self, title, line1, line2, fn):
        self.title = title
        self.l1 = line1
        self.l2 = line2
        self.fn = fn

    def press(self):
        pop()
        self.fn()

    def draw(self):
        draw_title(self.title)
        TC(self.l1, 64, 44, W)
        TC(self.l2, 64, 58, MID)
        R(14, 80, 100, 14, SEL)
        TC("DRUECKEN = JA", 64, 83, 0)
        TC("LANG = NEIN", 64, 104, DIM)


WLAN_CHARSET = " ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.!@#*"


class TextEntry(Page):
    def __init__(self, title, cb, masked=False):
        self.title = title
        self.cb = cb
        self.masked = masked
        self.buf = ""
        self.wheel = 1

    def turn(self, d):
        self.wheel = (self.wheel + d) % (len(WLAN_CHARSET) + 3)

    def _label(self, i):
        n = len(WLAN_CHARSET)
        i %= n + 3
        if i < n:
            c = WLAN_CHARSET[i]
            return "SPC" if c == " " else c
        return ("FERTIG", "LOESCHEN", "ABBRUCH")[i - n]

    def press(self):
        n = len(WLAN_CHARSET)
        i = self.wheel
        if i < n:
            if len(self.buf) < 32:
                self.buf += WLAN_CHARSET[i]
        elif i == n:
            if self.buf:
                txt = self.buf
                pop()
                self.cb(txt)
        elif i == n + 1:
            self.buf = self.buf[:-1]
        else:
            pop()

    def draw(self):
        draw_title(self.title, "%d" % len(self.buf))
        shown = "*" * len(self.buf) if self.masked else self.buf
        T(shown[-15:] + "_", 3, 32, W)
        HL(0, 44, 128, GH)
        for k in (-2, -1, 1, 2):
            TC(self._label(self.wheel + k), 64 + k * 26, 66, DIM if abs(k) == 2 else MID)
        lab = self._label(self.wheel)
        R(64 - 4 * len(lab) - 6, 58, 8 * len(lab) + 12, 22, W)
        TC(lab, 64, 65, 0)
        TC("DREHEN, DRUECKEN", 64, 118, DIM)


# ---------------------------------------------------------------
# SPIELEN (Start)
# ---------------------------------------------------------------

_hold_progress = 0.0     # PANIC-Fortschritt beim Halten (0..1)


def track_label(i):
    if i == ACID:
        return "303"
    if i == DRUM:
        return "DRM"
    return "S%d" % (i + 1)


def _draw_drum_strip(x, y, n, w, h, gap):
    # Kurzansicht der Drum-Spur: pro Step der lauteste Schlag
    d = S["drm"]
    lens = d["lens"]
    play = RTS[DRUM].step if S["run"] else -1
    xy = grid_xy() if d["gm"] else None
    for s in range(n):
        mv = 0
        for k in range(DRUM_ROWS):
            if s < lens[k] and not d["mutes"][k]:
                v = drum_cell(k, s, xy)
                if v > mv:
                    mv = v
        if s == play:
            c = W
        elif mv == 0:
            c = GH
        elif mv < 8:
            c = LO
        elif mv < 12:
            c = MID
        else:
            c = HI
        R(x + s * (w + gap), y, w, h, c)


def draw_steps_strip(i, x, y, n, w, h, gap):
    # Kurzansicht einer Spur: n Zellen, Abspielpunkt hell
    if i == DRUM:
        _draw_drum_strip(x, y, n, w, h, gap)
        return
    t = trk_cfg(i)
    rt = RTS[i]
    steps = t["steps"]
    block = (rt.step // n) if (S["run"] and rt.step >= 0) else 0
    base = block * n
    for k in range(n):
        s = base + k
        xx = x + k * (w + gap)
        if s >= steps:
            R(xx + w // 2, y + h // 2, 1, 1, GH)
            continue
        if i == ACID:
            st = t["pats"][t["pat"]][s]
            c = GH if st[0] < 0 else (HI if st[2] else LO)
        else:
            m = t["mode"]
            if m == 0:
                v = t["pats"][t["pat"]][s]
                c = (GH, DIM, LO, MID, HI)[v]
            elif m == 1:
                c = MID if euclid_hit(s, steps, t["pul"]) else GH
            else:
                c = LO
        if s == rt.step and S["run"]:
            c = W
        R(xx, y, w, h, c)


class HomePage(Page):
    def __init__(self):
        self.cur = 5
        self.last_step = None

    def turn(self, d):
        self.cur = (self.cur + d) % 6

    def press(self):
        if self.cur < 4:
            p = REG.get(S["macro"][self.cur])
            if p is not None:
                push(EditPage(p, "MAKRO %d" % (self.cur + 1)))
        elif self.cur == 4:
            seq_toggle()
        else:
            push(Carousel())

    def enc_param(self, i):
        return REG.get(S["macro"][i]) if i < 4 else None

    def tick(self):
        if not S["run"]:
            return False
        st = RTS[S["sel"]].step
        if st != self.last_step:
            self.last_step = st
            return True
        return False

    def draw(self):
        ch = S["cur"]
        p = S["pat"][ch]
        T(chan_patch_name(ch)[:16], 3, 15, W if not S["mute"][ch] else DIM)
        if chrom_owns(ch):
            info = "SAMPLER %dST B%d" % (S["sb"]["cv"], S["bus"][ch])
        elif p == -1:
            info = "KEIN PATCH"
        else:
            info = "%03d %dST B%d" % (p, eff_voices(ch), S["bus"][ch])
            if S["mute"][ch]:
                info += " MUTE"
        if self.cur < 4:
            pr = REG.get(S["macro"][self.cur])
            if pr is not None and (pr.vis is None or pr.vis()):
                info = (pr.label[:7] + " " + pr.text())[:15]
                T(info, 3, 26, HI)
            else:
                T("NICHT AKTIV", 3, 26, DIM)
        else:
            T(info, 3, 26, DIM)
        for i in range(4):
            cx = 16 + 32 * i
            pr = REG.get(S["macro"][i])
            if pr is None or (pr.vis is not None and not pr.vis()):
                ring(cx, 54, 11, 0.0, 2, 2, False, GH, GH)
                TC("--", cx, 70, DIM)
                continue
            ring(cx, 54, 11, pr.frac(), 3 if self.cur == i else 2, 1, pr.bip,
                 W if self.cur == i else HI)
            lab = pr.short[:4]
            if self.cur == i:
                R(cx - 16, 68, 32, 11, SEL)
                TC(lab, cx, 70, 0)
            else:
                TC(lab, cx, 70, MID)
        sel = S["sel"]
        T(track_label(sel), 3, 86, DIM)
        draw_steps_strip(sel, 28, 86, 16, 5, 7, 1)
        for j, lab in ((4, "STOP" if S["run"] else "START"), (5, "MENUE")):
            x = 4 if j == 4 else 68
            if self.cur == j:
                R(x, 102, 56, 15, SEL)
                TC(lab, x + 28, 106, 0)
            else:
                FR(x, 102, 56, 15, DIM)
                TC(lab, x + 28, 106, MID)
        if _hold_progress > 0:
            R(24, 30, 80, 70, 0)
            ring(64, 64, 26, _hold_progress, 4, 1, False, W, GH)
            TC("PANIC", 64, 60, W)


# ---------------------------------------------------------------
# MENUE-Karussell
# ---------------------------------------------------------------

class Carousel(Page):
    idx = 0

    def turn(self, d):
        Carousel.idx = (Carousel.idx + d) % len(CARDS)

    def press(self):
        push(CARDS[Carousel.idx][3]())

    def draw(self):
        n = len(CARDS)
        i = Carousel.idx
        for side, x in ((-1, 2), (1, 100)):
            j = (i + side) % n
            R(x, 30, 26, 34, GH)
            icon(CARDS[j][2], x + 1, 35, DIM)
        R(36, 18, 56, 56, GH)
        FR(36, 18, 56, 56, HI)
        icon(CARDS[i][2], 52, 34, W)
        TC(CARDS[i][0], 64, 82, W)
        TC(CARDS[i][1], 64, 96, DIM)
        x0 = 64 - (n * 8) // 2 + 2
        for k in range(n):
            if k == i:
                R(x0 + k * 8 - 1, 110, 5, 5, W)
            else:
                R(x0 + k * 8, 111, 3, 3, LO)


# ---------------------------------------------------------------
# Patch-Browser
# ---------------------------------------------------------------

class PatchBrowser(Page):
    def __init__(self):
        self.ch = S["cur"]
        self.orig = S["pat"][self.ch]
        e = S["syx"][self.ch]
        self.orig_syx = list(e) if e else None
        self.level = 0
        self.rcur = 0
        self.pcur = 0
        self.plist = []
        if self.ch == DRUM_CHANNEL:
            self.roots = [("DRUMKITS", lambda: DRUM_KITS)]
        else:
            self.roots = [("FAVORITEN", lambda: S["fav"]), ("ZULETZT", lambda: S["rec"])]
            for ci in range(len(CAT_DEFS)):
                self.roots.append((CAT_DEFS[ci][0], (lambda c=ci: PATCH_CATS[c])))
            self.roots += [("SONSTIGE", lambda: PATCH_OTHER),
                           ("ALLE JUNO", lambda: list(range(0, 128))),
                           ("ALLE DX7", lambda: list(range(128, 256))),
                           ("DRUMKITS", lambda: DRUM_KITS),
                           ("DX7 VON SD", "syx"),
                           ("KEIN PATCH", None)]

    def enter(self):
        if len(self.roots) == 1:
            self._open(0)

    def _open(self, r):
        fn = self.roots[r][1]
        if fn == "syx":
            push(SyxBrowser(self.ch))
            return
        if fn is None:
            set_patch(self.ch, -1)
            commit_patch(self.ch)
            pop()
            return
        lst = list(fn())
        if not lst:
            toast("LEER", "")
            return
        self.plist = lst
        self.pcur = lst.index(self.orig) if self.orig in lst else 0
        self.level = 1

    def turn(self, d):
        if self.level == 0:
            self.rcur = (self.rcur + d) % len(self.roots)
        else:
            self.pcur = (self.pcur + d) % len(self.plist)
            set_patch(self.ch, self.plist[self.pcur])

    def press(self):
        if self.level == 0:
            self._open(self.rcur)
        else:
            if S["pat"][self.ch] != self.plist[self.pcur]:
                set_patch(self.ch, self.plist[self.pcur])
            commit_patch(self.ch)
            pop()

    def back(self):
        if self.level == 1:
            if self.orig_syx:
                set_syx_patch(self.ch, *self.orig_syx)
                flush_configure(True)
            elif S["pat"][self.ch] != self.orig:
                set_patch(self.ch, self.orig)
                flush_configure(True)
            self.level = 0
            if len(self.roots) == 1:
                return False
            return True
        return False

    def draw(self):
        if self.level == 0:
            draw_title("PATCH K%d" % self.ch)
            rows = []
            for name, fn in self.roots:
                rows.append((name, "%d" % len(fn()) if callable(fn) else ""))
            draw_rows(rows, self.rcur)
            TC("AKTUELL " + patch_name(self.orig)[:8], 64, 118, DIM)
        else:
            draw_title(self.roots[self.rcur][0], "%d/%d" % (self.pcur + 1, len(self.plist)))
            rows = []
            for p in self.plist:
                mark = "*" if p == self.orig else ("+" if p in S["fav"] else "")
                rows.append(("%03d %s" % (p, patch_name(p)), mark))
            draw_rows(rows, self.pcur)
            TC("OK=NEHMEN LANG=Z", 64, 118, DIM)


class SyxBrowser(Page):
    # DX7 VON SD: Datei waehlen, dann Stimme (beim Drehen hoerbar)
    def __init__(self, ch):
        self.ch = ch
        self.files = []
        self.names = []
        self.level = 0
        self.fcur = 0
        self.vcur = 0
        self.orig_pat = S["pat"][ch]
        e = S["syx"][ch]
        self.orig_syx = list(e) if e else None

    def enter(self):
        if fm_mod() is None:
            toast("DX7", "FM.PY FEHLT", 2000)
        self.files = syx_list_files()
        e = S["syx"][self.ch]
        if e and e[0] in self.files:
            self.fcur = self.files.index(e[0])

    def _restore(self):
        if self.orig_syx:
            set_syx_patch(self.ch, *self.orig_syx)
        else:
            set_patch(self.ch, self.orig_pat)
        flush_configure(True)

    def _preview(self):
        set_syx_patch(self.ch, self.files[self.fcur], self.vcur, self.names[self.vcur])

    def turn(self, d):
        if self.level == 0:
            if self.files:
                self.fcur = (self.fcur + d) % len(self.files)
        elif self.names:
            self.vcur = (self.vcur + d) % len(self.names)
            self._preview()

    def vturn(self, d):
        self.turn(d)

    def press(self):
        if self.level == 0:
            if not self.files or fm_mod() is None:
                return
            names = syx_names(self.files[self.fcur])
            if not names:
                toast("DX7", "KEINE STIMMEN", 1500)
                return
            self.names = names
            self.level = 1
            e = S["syx"][self.ch]
            ok = e and e[0] == self.files[self.fcur] and e[1] < len(names)
            self.vcur = e[1] if ok else 0
            self._preview()
        else:
            commit_patch(self.ch)
            pop()
            if isinstance(top(), PatchBrowser):
                pop()

    def back(self):
        if self.level == 1:
            self._restore()
            self.level = 0
            return True
        return False

    def draw(self):
        if self.level == 0:
            draw_title("DX7 SD K%d" % self.ch,
                       "%d/%d" % (self.fcur + 1, len(self.files)) if self.files else "")
            if not self.files:
                TC("KEINE .SYX", 64, 56, MID)
                TC("/sd/dx7/", 64, 72, DIM)
                return
            draw_rows([(f.split("/")[-1][:-4][:14], "") for f in self.files], self.fcur)
            TC("OK=OEFFNEN", 64, 118, DIM)
        else:
            draw_title(self.files[self.fcur].split("/")[-1][:-4][:10],
                       "%d/%d" % (self.vcur + 1, len(self.names)))
            draw_rows([("%02d %s" % (i + 1, n), "") for i, n in enumerate(self.names)],
                      self.vcur)
            TC("OK=NEHMEN LANG=Z", 64, 118, DIM)


# ---------------------------------------------------------------
# MIXER
# ---------------------------------------------------------------

def _fav_text():
    return "JA" if cur_patch() in S["fav"] else "NEIN"


def _unassign():
    set_patch(S["cur"], -1)
    commit_patch(S["cur"])


def channel_items():
    return [link("PATCH", PatchBrowser, info=lambda: patch_name(cur_patch())[:7]),
            P_LVL, P_PAN, P_MUTE, P_BUS, P_VO, P_CHORD, P_PORTA,
            action("FAVORIT", lambda: toggle_favorite(cur_patch()), info=_fav_text,
                   vis=lambda: -1 < cur_patch() < USER_BASE),
            action("ENTFERNEN", _unassign, vis=lambda: cur_patch() != -1)]


def channel_page():
    return ListPage(lambda: "KANAL %d" % S["cur"], channel_items)


class MixerPage(Page):
    def turn(self, d):
        on_channel_select(1 + (S["cur"] - 1 + d) % 16)

    def press(self):
        push(channel_page())

    def enc_param(self, i):
        return (P_LVL, P_PAN, P_PORTA, P_RVL)[i] if i < 4 else None

    def draw(self):
        c = S["cur"] - 1
        bank = c // 8
        T("MIXER %s" % ("1-8" if bank == 0 else "9-16"), 3, 14, HI)
        TR("%d/%d" % (voices_total(), S["vbud"]), 125, 14,
           W if voices_total() > S["vbud"] else DIM)
        for i in range(8):
            ch = bank * 8 + i + 1
            x = 7 + i * 15
            sel = (ch == S["cur"])
            R(x, 27, 7, 60, GH)
            if S["pat"][ch] != -1:
                h = int(60 * clamp(S["lvl"][ch] / 2.0, 0.0, 1.0))
                col = DIM if S["mute"][ch] else (W if sel else MID)
                if h:
                    R(x, 87 - h, 7, h, col)
                R(x + int(S["pan"][ch] * 6), 89, 1, 3, MID)
                if S["mute"][ch]:
                    T("M", x, 45, W)
            if sel:
                FR(x - 3, 24, 13, 70, W)
            lab = "%d" % ch
            TC(lab, x + 3, 96, W if sel else DIM)
        p = S["pat"][S["cur"]]
        T(("C%d " % S["cur"] + chan_patch_name(S["cur"]))[:16], 3, 107, HI)
        T("L%.2f P%.2f B%d" % (S["lvl"][S["cur"]], S["pan"][S["cur"]], S["bus"][S["cur"]]),
          3, 118, DIM)


# ---------------------------------------------------------------
# KLANG
# ---------------------------------------------------------------

def _tone_reset():
    ch = S["cur"]
    reset_tone(ch)
    configure_channel(ch)
    request_save()
    toast("KLANG", "PATCH-WERTE")


def _learn():
    global _learn_armed
    _learn_armed = not _learn_armed
    mark_dirty()


def _cc_clear():
    S["ccmap"][S["cur"]] = []
    apply_ccmap(S["cur"])
    request_save()


def cc_page():
    return ListPage("CC-LEARN", [
        P_CCT,
        action("LERNEN", _learn, info=lambda: "WARTE" if _learn_armed else "START"),
        infoline("MAPS KANAL", lambda: "%d" % len(S["ccmap"][S["cur"]])),
        action("LOESCHEN", _cc_clear)])


def klang_items():
    return [link("PATCH", PatchBrowser, info=lambda: patch_name(cur_patch())[:7]),
            P_CUT, P_RES, P_ATT, P_DEC, P_SUS, P_REL, P_LFR, P_LFD, P_ALG, P_FB,
            P_CHORD, P_PORTA, P_VO,
            action("FAVORIT", lambda: toggle_favorite(cur_patch()), info=_fav_text,
                   vis=lambda: -1 < cur_patch() < USER_BASE),
            link("CC-LEARN", cc_page),
            action("PATCH-WERTE", _tone_reset, vis=lambda: S["tch"][S["cur"]] != 0)]


def klang_page():
    return ListPage(lambda: "KLANG K%d" % S["cur"], klang_items,
                    right=lambda: FAMILY_SHORT[cur_family()])


# ---------------------------------------------------------------
# EFFEKTE
# ---------------------------------------------------------------

_fxb_ui = [0]


def _fx_enter(bus=None):
    # bus: fester Bus (z. B. von AUDIO IN), sonst der des aktuellen Kanals
    global _fx_bus_override
    _fxb_ui[0] = S["bus"][S["cur"]] if bus is None else bus
    _fx_bus_override = _fxb_ui[0]


def _fx_leave():
    global _fx_bus_override
    _fx_bus_override = None


def _fxb_changed():
    global _fx_bus_override
    _fx_bus_override = _fxb_ui[0]


P_FXBUS = P("BUS", lambda: (_fxb_ui, 0), 0, 3, 1, "%d", kind=ENUM,
            opts=["0", "1", "2", "3"], apply=_fxb_changed)


def _bus_users():
    b = fx_bus()
    chs = [str(ch) for ch in range(1, 17) if S["pat"][ch] != -1 and S["bus"][ch] == b]
    if S["ain"]["on"] and S["ain"]["bus"] == b:
        chs.insert(0, "IN")               # AUDIO IN (v13.22)
    return ",".join(chs)[:6] if chs else "-"


def fx_page(bus=None):
    return ListPage(lambda: "EFFEKTE BUS %d" % fx_bus(), [
        P_FXBUS,
        infoline("KANAELE", _bus_users),
        link("REVERB", lambda: ListPage("REVERB", [P_RVL, P_RVV, P_RVD, P_RVX]),
             info=lambda: "%.2f" % S["fx"][fx_bus()]["rv"][0]),
        P_PFX,
        link("CHORUS", lambda: ListPage("CHORUS", [P_CHL, P_CHR, P_CHD, P_CHM]),
             info=lambda: "PATCH" if S["fx"][fx_bus()]["pfx"] else "%.2f" % S["fx"][fx_bus()]["cho"][0]),
        link("ECHO", lambda: ListPage("ECHO", [P_ECL, P_ECT, P_ECF, P_ECC]),
             info=lambda: "%.2f" % S["fx"][fx_bus()]["ech"][0]),
        link("EQ", lambda: ListPage("EQ", [P_PROF, P_EQL, P_EQM, P_EQH]),
             info=lambda: "PATCH" if S["fx"][fx_bus()]["pfx"] else PROFILE_NAMES[S["fx"][fx_bus()]["prof"]][:6]),
        link("DISTORTION", lambda: ListPage("DISTORTION", [P_DST, P_DSD, P_DSM]),
             info=lambda: DIST_TYPES[S["fx"][fx_bus()]["dst"][0]][:6],
             vis=lambda: DIST_OK),
        P_MASTER, P_CRUSH, P_CRATE,
        action("BUS RESET", lambda: push(Confirm("BUS RESET", "EFFEKTE BUS %d" % fx_bus(),
                                                 "AUF WERK?", lambda: reset_bus_fx(fx_bus()))))],
        on_enter=lambda: _fx_enter(bus), on_leave=_fx_leave)


# ---------------------------------------------------------------
# SEQUENCER
# ---------------------------------------------------------------

class SeqPage(Page):
    # Uebersicht: 6 Spuren (S1-S4, 303, DRM) mit Abspielpunkt, darunter
    # START/STOP und GLOBAL. Cursor 0-5 = Spuren, 6 = Start/Stop,
    # 7 = Global.
    def __init__(self):
        self.cur = S["sel"]
        self.last = None

    def turn(self, d):
        self.cur = (self.cur + d) % 8
        if self.cur < 6:
            S["sel"] = self.cur

    def press(self):
        if self.cur < 6:
            S["sel"] = self.cur
            if self.cur == DRUM:
                push(DrumPage())
            else:
                push(track_page())
        elif self.cur == 6:
            seq_toggle()
        else:
            push(seq_global_page())

    def enc_param(self, i):
        return (P_TEMPO, P_SWING)[i] if i < 2 else None

    def tick(self):
        if not S["run"]:
            return False
        st = [rt.step for rt in RTS]
        if st != self.last:
            self.last = st
            return True
        return False

    def draw(self):
        for i in range(6):
            y = 14 + i * 12
            t = trk_cfg(i)
            sel = (i == self.cur)
            lab = track_label(i)
            if sel:
                R(0, y - 2, 25, 11, SEL)
                T(lab, 1, y, 0)
            else:
                T(lab, 1, y, DIM if t["mute"] else MID)
            draw_steps_strip(i, 27, y, 16, 5, 7, 1)
            if t["mute"]:
                HL(27, y + 3, 95, DIM)
            if RTS[i].pending is not None:
                R(124, y, 3, 7, W)
        for j, y, lab in ((6, 88, ("STOP " if S["run"] else "START ") + "%dBPM" % S["tempo"]),
                          (7, 101, "GLOBAL")):
            if self.cur == j:
                R(0, y - 2, 124, 12, SEL)
                T(lab, 4, y, 0)
                if j == 7:
                    TR(">", 122, y, 0)
            else:
                T(lab, 4, y, MID)
                if j == 7:
                    TR(">", 122, y, DIM)
        if self.cur < 6:
            t = trk_cfg(self.cur)
            pat = PATTERN_NAMES[t["pat"]]
            if self.cur == ACID:
                info = "303 PAT %s %dST" % (pat, t["steps"])
            elif self.cur == DRUM:
                info = "K%d DRUMS %s" % (t["ch"], pat)
            else:
                info = "K%d %s %s" % (t["ch"], SEQ_MODES[t["mode"]][:6], pat)
            T(info[:16], 3, 117, DIM)
        elif S["swing"]:
            T("SWING %d%%" % S["swing"], 3, 117, DIM)


def _copy_next(i=None):
    i = S["sel"] if i is None else i
    t = trk_cfg(i)
    dst = (t["pat"] + 1) % NUM_PATTERNS
    track_copy_pattern(i, dst)
    toast("KOPIERT", "%s > %s" % (PATTERN_NAMES[t["pat"]], PATTERN_NAMES[dst]))


def _clear_pat(i=None):
    i = S["sel"] if i is None else i
    push(Confirm("LEEREN", "PATTERN %s" % PATTERN_NAMES[trk_cfg(i)["pat"]],
                 "ALLE STEPS AUS?", lambda: track_clear_pattern(i)))


def track_items():
    if S["sel"] == ACID:
        return [link("STEPS BEARBEITEN", lambda: AcidEditor()),
                AP_PAT,
                action("ACID-GENERATOR", lambda: (acid_generate(), toast("303", "NEUES PATTERN"))),
                action("MUTIEREN", lambda: (acid_mutate(), toast("303", "3 STEPS NEU"))),
                AP_JOY, AP_JX, AP_JY, AP_JD,
                AP_WAVE, AP_CUT, AP_RESO, AP_ENV, AP_DEC, AP_ACC, AP_SLIDE,
                AP_DT, AP_DD, AP_DM,
                AP_TUNE, AP_ROOT, AP_LVL, AP_STEPS, AP_OUT, AP_MCH, AP_MUTE,
                AP_CVACC,
                action("KOPIE > NAECHST.", _copy_next),
                action("LEEREN", _clear_pat)]
    return [link("STEPS BEARBEITEN", lambda: StepEditor(),
                 vis=lambda: S["trk"][S["sel"] % 4]["mode"] == 0),
            TP_PAT, TP_MODE, TP_CH, TP_STEPS, TP_DIV, TP_NOTE, TP_GATE, TP_PUL,
            TP_SCALE, TP_ADIR, TP_AOCT, TP_AIN, TP_LATCH, TP_OUT, TP_MCH, TP_MUTE,
            action("KOPIE > NAECHST.", _copy_next,
                   vis=lambda: S["trk"][S["sel"] % 4]["mode"] == 0),
            action("LEEREN", _clear_pat, vis=lambda: S["trk"][S["sel"] % 4]["mode"] == 0)]


def track_page():
    return ListPage(lambda: "303 ACID" if S["sel"] == ACID else "SPUR %d" % (S["sel"] + 1),
                    track_items)


def seq_global_page():
    return ListPage("SEQ GLOBAL", [
        action("START/STOP", seq_toggle, info=lambda: "LAEUFT" if S["run"] else "STEHT"),
        P_TEMPO,
        action("TAP TEMPO", tap_tempo, info=lambda: "%d" % S["tempo"]),
        P_SWING, P_CLOCK, P_TRANSPORT, P_M5])


class StepEditor(Page):
    # Spur 1-4 im Modus MANUAL. Druecken schaltet einen Step durch:
    # AUS -> 100% -> 75% -> 50% -> 25% -> AUS.
    def __init__(self):
        self.i = S["sel"] % 4
        self.cur = 0
        self.last = None

    def turn(self, d):
        t = S["trk"][self.i]
        self.cur = (self.cur + d) % (t["steps"] + 1)

    def press(self):
        t = S["trk"][self.i]
        if self.cur >= t["steps"]:
            request_save()
            pop()
            return
        pat = t["pats"][t["pat"]]
        v = pat[self.cur]
        pat[self.cur] = 4 if v == 0 else v - 1
        request_save()

    def tick(self):
        st = RTS[self.i].step if S["run"] else -1
        if st != self.last:
            self.last = st
            return True
        return False

    def draw(self):
        t = S["trk"][self.i]
        pat = t["pats"][t["pat"]]
        draw_title("S%d PAT %s" % (self.i + 1, PATTERN_NAMES[t["pat"]]),
                   "%d/%d" % (min(self.cur + 1, t["steps"]), t["steps"]))
        play = RTS[self.i].step if S["run"] else -1
        for s in range(t["steps"]):
            x = (s % 8) * 16 + 1
            y = 28 + (s // 8) * 16
            v = pat[s]
            if v:
                R(x, y, 14, 12, (0, LO, MID, HI, W)[v])
            else:
                FR(x, y, 14, 12, GH + 2)
            if s == self.cur:
                FR(x - 1, y - 1, 16, 14, W)
                if v:
                    R(x + 4, y + 3, 6, 6, 0)
            if s == play:
                R(x, y + 13, 14, 2, W)
        yb = 28 + ((t["steps"] + 7) // 8) * 16 + 2
        if self.cur >= t["steps"]:
            R(0, yb - 2, 124, 12, SEL)
            TC("FERTIG", 64, yb, 0)
        else:
            TC("FERTIG", 64, yb, DIM)
            v = pat[self.cur]
            T("STEP %d: %s" % (self.cur + 1, ("AUS", "25%", "50%", "75%", "100%")[v]), 3, 118, MID)


class AcidEditor(Page):
    # 303-Steps: Druecken geht NOTE -> OKTAVE -> ACCENT -> SLIDE -> Auswahl
    FIELDS = ("NOTE", "OKTAVE", "ACCENT", "SLIDE")

    def __init__(self):
        self.cur = 0
        self.field = None
        self.last = None

    def _step(self):
        a = S["acid"]
        return a["pats"][a["pat"]][self.cur]

    def _change(self, k, d):
        st = self._step()
        if k == 0:
            st[0] = clamp_int(st[0] + d, -1, 12)
        elif k == 1:
            st[1] = clamp_int(st[1] + d, -1, 1)
        elif d % 2:
            st[k] = 0 if st[k] else 1
        request_save()

    def turn(self, d):
        a = S["acid"]
        if self.field is None:
            self.cur = (self.cur + d) % (a["steps"] + 1)
        elif self.cur < a["steps"]:
            self._change(self.field, d)

    def press(self):
        a = S["acid"]
        if self.cur >= a["steps"]:
            pop()
            return
        if self.field is None:
            self.field = 0
        elif self.field >= 3:
            self.field = None
        else:
            self.field += 1

    def back(self):
        if self.field is not None:
            self.field = None
            return True
        return False

    def enc_param(self, i):
        # E1-E4 = NOTE/OKTAVE/ACCENT/SLIDE des markierten Steps
        if i < 4 and self.cur < S["acid"]["steps"]:
            return _AcidEncProxy(self, i)
        return None

    def tick(self):
        st = RTS[ACID].step if S["run"] else -1
        if st != self.last:
            self.last = st
            return True
        return False

    def draw(self):
        a = S["acid"]
        pat = a["pats"][a["pat"]]
        draw_title("303 PAT %s" % PATTERN_NAMES[a["pat"]],
                   "%d/%d" % (min(self.cur + 1, a["steps"]), a["steps"]))
        play = RTS[ACID].step if S["run"] else -1
        for s in range(ACID_STEPS_MAX):
            x = (s % 8) * 16
            y = 28 + (s // 8) * 16
            if s >= a["steps"]:
                R(x + 7, y + 6, 2, 2, GH)
                continue
            st = pat[s]
            rest = st[0] < 0
            if s == self.cur:
                bg, fg = W, 0
            elif rest:
                bg, fg = GH, DIM
            else:
                bg, fg = (SEL if st[2] else GH + 2), W
            R(x + 1, y, 14, 13, bg)
            T("--" if rest else ACID_NOTE_LABELS[st[0]][:2], x, y + 3, fg)
            if st[3] and not rest:
                R(x + 1, y + 11, 14, 2, 0 if s == self.cur else W)
            if s == play:
                R(x + 1, y + 14, 14, 1, W)
        if self.cur >= a["steps"]:
            R(0, 68, 124, 12, SEL)
            TC("FERTIG", 64, 70, 0)
            return
        st = pat[self.cur]
        vals = ("--" if st[0] < 0 else ACID_NOTE_LABELS[st[0]],
                "%+d" % st[1] if st[1] else "0",
                "AN" if st[2] else "AUS", "AN" if st[3] else "AUS")
        for k in range(4):
            y = 66 + k * 12
            if self.field == k:
                R(0, y - 2, 124, 11, W)
                T(self.FIELDS[k], 3, y, 0)
                TR(vals[k], 123, y, 0)
            else:
                T(self.FIELDS[k], 3, y, MID)
                TR(vals[k], 123, y, HI)
        TC("OK=FELD LANG=ZUR", 64, 118, DIM)


class _AcidEncProxy:
    # Minimal-Parameter fuer E1-E4 im 303-Step-Editor
    def __init__(self, page, k):
        self.page = page
        self.k = k
        self.label = AcidEditor.FIELDS[k]

    def nudge(self, d, acc=1):
        self.page._change(self.k, d)
        mark_dirty()

    def text(self):
        v = self.page._step()[self.k]
        return str(v)


# ---------------------------------------------------------------
# DRUMS: Raster 8 Instrumente x 16 Steps (Seite 1-16 / 17-32)
# ---------------------------------------------------------------
#
#   DREHEN        Cursor durch die Steps, am Zeilenende ins naechste
#                 Instrument; nach dem letzten: SPUR-MENUE
#   DRUECKEN      Step: AUS -> 100 % -> 67 % -> 40 % -> AUS
#                 SPUR-MENUE: Einstellungen oeffnen
#   JOYSTICK      hoch/runter = Instrument, links/rechts = Step
#   E1-E8 (SEITE) die 8 Steps rund um den Cursor (1-8 oder 9-16 der
#                 aktuellen Seite), Drehen = Velocity 0-15

DRUM_X0 = 19      # erste Spalte des Rasters
DRUM_Y0 = 13      # erste Zeile
DRUM_RH = 11      # Zeilenhoehe


def _drum_x(c):
    # 6 px pro Step, nach je 4 Steps 1 px Luecke
    return DRUM_X0 + c * 6 + c // 4


class DrumPage(Page):
    def __init__(self):
        self.row = DRM_UI[0]
        self.step = 0
        self.menu = False
        self.last = None

    def _len(self):
        return S["drm"]["lens"][self.row]

    def resume(self):
        # Im Menue kann Instrument oder Laenge geaendert worden sein
        self.row = DRM_UI[0]
        self.step = min(self.step, self._len() - 1)

    def leave(self):
        request_save()           # nicht synchron - der Sequencer laeuft evtl.

    def _move(self, d):
        if self.menu:
            self.menu = False
            if d > 0:
                self.row, self.step = 0, 0
            else:
                self.row = DRUM_ROWS - 1
                self.step = self._len() - 1
            return
        self.step += d
        if self.step >= self._len():
            if self.row == DRUM_ROWS - 1:
                self.menu = True
                self.step = self._len() - 1
            else:
                self.row += 1
                self.step = 0
        elif self.step < 0:
            if self.row == 0:
                self.menu = True
                self.step = 0
            else:
                self.row -= 1
                self.step = self._len() - 1

    def turn(self, d):
        n = abs(d) * (2 if turn_accel() >= 3 else 1)
        s = 1 if d > 0 else -1
        for _ in range(n):
            self._move(s)
            if self.menu:
                break
        DRM_UI[0] = self.row

    def vturn(self, d):
        self.menu = False
        self.row = (self.row + d) % DRUM_ROWS
        self.step = min(self.step, self._len() - 1)
        DRM_UI[0] = self.row

    def press(self):
        if self.menu:
            push(drum_menu_page())
            return
        if S["drm"]["gm"]:
            # Im LIVE-Modus zuerst das Grids-Muster ins Pattern holen,
            # dann wie gewohnt bearbeiten
            grid_freeze()
            toast("GRIDS", "> PATTERN")
        v = drm_get(self.row, self.step)
        cyc = DRUM_VEL_CYCLE
        nv = cyc[(cyc.index(v) + 1) % len(cyc)] if v in cyc else 0
        drm_set(self.row, self.step, nv)

    def enc_param(self, i):
        if i >= 8:
            return None
        if S["drm"]["gm"]:
            # LIVE: E1 = X, E2 = Y, E3-E8 = Dichte Instrument 1-6
            if i == 0:
                return DP_GX
            if i == 1:
                return DP_GY
            return DP_GD[i - 2]
        if self.menu:
            return None
        s = (self.step // 8) * 8 + i
        if s >= self._len():
            return None
        return _DrumEncProxy(self.row, s)

    def enc_press(self, i, long):
        # Taster eines Zusatz-Encoders (KONTEXT): Step wie Druecken setzen
        if long or self.menu or S["drm"]["gm"]:
            return
        s = (self.step // 8) * 8 + i
        if s < self._len():
            v = drm_get(self.row, s)
            cyc = DRUM_VEL_CYCLE
            drm_set(self.row, s, cyc[(cyc.index(v) + 1) % len(cyc)] if v in cyc else 0)

    def tick(self):
        rt = RTS[DRUM]
        st = tuple(rt.rows) if (S["run"] and rt.rows) else None
        if S["drm"]["gm"]:
            x, y = grid_xy()
            st = (st, int(x * 50), int(y * 50))
        if st != self.last:
            self.last = st
            return True
        return False

    def draw(self):
        d = S["drm"]
        rt = RTS[DRUM]
        live = d["gm"]
        xy = grid_xy() if live else None
        rows = rt.rows if S["run"] else None
        page = self.step // 16
        trg = d["trg"]
        for r in range(DRUM_ROWS):
            y = DRUM_Y0 + r * DRUM_RH
            n = d["lens"][r]
            here = (r == self.row and not self.menu)
            muted = d["mutes"][r] or d["mute"]
            T(drum_row_label(r), 1, y, W if here else (DIM if muted else MID))
            play = rows[r] if rows is not None else -1
            for c in range(16):
                s = page * 16 + c
                if s >= n:
                    break
                x = _drum_x(c)
                if s == play:
                    R(x - 1, y - 1, 7, 10, GH)
                v = drum_cell(r, s, xy)
                if v:
                    R(x, y, 5, 8, 3 + (v * 12) // 15)   # Velocity 1-15 -> Grau 3-15
                else:
                    R(x + 2, y + 3, 1, 2, GH + 2)
                if here and s == self.step:
                    FR(x - 1, y - 1, 7, 10, W)
            if muted:
                HL(DRUM_X0, y + 4, 97, DIM)
            # Trigger-Ausgang dieses Instruments (1/2) rechts am Rand
            for out in (0, 1):
                if trg[out] == r:
                    R(119 + 4 * out, y + 1, 3, 6, HI if drum_out_free(out) else GH)
            if here and PARAM_ENCODERS and not live:
                # Bereich, den E1-E8 gerade bearbeiten
                c0 = (self.step // 8) * 8 - page * 16
                HL(_drum_x(c0), y + 9, 8 * 6 + 1, LO)
        HL(0, 102, 128, GH)
        if self.menu:
            R(0, 105, 124, 11, SEL)
            T("SPUR-MENUE", 3, 107, 0)
            TR(">", 122, 107, 0)
        elif live:
            T("%s %d/%d" % (drum_row_label(self.row), self.step + 1, self._len()),
              1, 106, HI)
            TR("D%d" % d["gd"][self.row], 127, 106, MID)
        else:
            v = drm_get(self.row, self.step)
            T("%s %d/%d" % (drum_row_label(self.row), self.step + 1, self._len()),
              1, 106, HI)
            TR("%d%%" % ((v * 100 + 7) // 15) if v else "AUS", 127, 106, MID)
        if live:
            T("GRIDS X%02d Y%02d" % (int(xy[0] * 99), int(xy[1] * 99)), 1, 117, LO)
            return
        pn = PATTERN_NAMES[d["pat"]]
        if rt.pending is not None:
            pn += ">" + PATTERN_NAMES[rt.pending]
        T("PAT %s %s" % (pn, SEQ_DIV_NAMES[d["div"]]), 1, 117, DIM)
        if max(d["lens"]) > 16 and rt.pending is None:
            TR("%d-%d" % (page * 16 + 1, page * 16 + 16), 127, 117, DIM)


class _DrumEncProxy:
    # E1-E8 auf der Drum-Seite: Velocity eines Steps (0 = aus)
    def __init__(self, k, s):
        self.k = k
        self.s = s
        self.label = "%s %d" % (drum_row_label(k), s + 1)

    def nudge(self, d, acc=1):
        drm_set(self.k, self.s, drm_get(self.k, self.s) + d)
        mark_dirty()

    def text(self):
        return "%d" % drm_get(self.k, self.s)


def _drm_euclid():
    k = DRM_UI[0]
    n = S["drm"]["lens"][k]
    p = min(DRM_UI[1], n)
    drum_euclid(k, p)
    toast("EUCLID", "%s %d/%d" % (drum_row_label(k), p, n))


def _drm_clear_row():
    k = DRM_UI[0]
    drum_clear_row(k)
    toast("GELEERT", drum_row_label(k))


def _drm_len16():
    S["drm"]["lens"] = [16] * DRUM_ROWS
    request_save()
    toast("LAENGEN", "ALLE 16")


def _grid_freeze_act():
    grid_freeze()
    toast("GRIDS", "> PATTERN %s" % PATTERN_NAMES[S["drm"]["pat"]])


def _grid_mode_changed():
    if S["drm"]["gm"]:
        toast("GRIDS LIVE", "E1=X E2=Y", 1500)


def grids_page():
    return ListPage("GRIDS", [
        P("MODUS", rD("gm"), kind=ENUM, opts=GRID_MODE_NAMES, apply=_grid_mode_changed),
        DP_GX, DP_GY, DP_GZ, DP_INS, DP_GDEN, DP_GCV, DP_GJ,
        action("IN PATTERN SCHR.", _grid_freeze_act)],
        right=lambda: "X%02d Y%02d" % (int(grid_xy()[0] * 99), int(grid_xy()[1] * 99)))


def _trig_info():
    t = S["drm"]["trg"]
    return "%s/%s" % ("-" if t[0] < 0 else t[0] + 1, "-" if t[1] < 0 else t[1] + 1)


def trig_page():
    return ListPage("CV TRIGGER", DP_TRG + [DP_TLEN, DP_TLV])


def _drm_smp_changed():
    _drm_release()
    sk = S["drm"]["smp"][DRM_UI[0]]
    if sk >= 0:
        if not slot_play(sk):
            toast("S%d" % (sk + 1), "LEER" if not slot(sk)["f"] else
                  ("KEIN PAD" if pad_synth(sk) is None else _slot_state(sk)), 1500)


def _drm_sli_changed():
    _drm_release()
    k = DRM_UI[0]
    sk = S["drm"]["smp"][k]
    if sk >= 0:
        pc = S["drm"]["sli"][k] - 1
        if pc >= 0:
            slice_play_now(sk, pc)
        else:
            slot_play(sk)


DP_SLI = P("SLICE", _drm_ins_ref("sli"), kind=ENUM,
           opts=lambda: ["GANZ"] + ["%d" % (i + 1) for i in range(16)],
           vals=list(range(17)), apply=_drm_sli_changed,
           vis=lambda: S["drm"]["smp"][DRM_UI[0]] >= 0
           and slot_chops(S["drm"]["smp"][DRM_UI[0]]) > 0)
DP_SMP = P("SAMPLE", _drm_ins_ref("smp"), kind=ENUM,
           opts=lambda: ["KIT"] + ["S%d %s" % (i + 1, slot_name(i)[:5]) for i in range(SMP_SLOTS)],
           vals=list(range(-1, SMP_SLOTS)), apply=_drm_smp_changed)


def drum_menu_page():
    return ListPage(lambda: "DRUMS K%d" % S["drm"]["ch"], [
        DP_KIT, DP_INS, DP_SMP, DP_SLI, DP_SOUND, DP_NOTE, DP_LEN, DP_IMUTE, DP_PUL,
        action("EUCLID SETZEN", _drm_euclid),
        action("ZEILE LEEREN", _drm_clear_row),
        link("GRIDS", grids_page, info=lambda: GRID_MODE_NAMES[S["drm"]["gm"]][:5]),
        link("CV TRIGGER", trig_page, info=_trig_info),
        DP_PAT, DP_DIV, DP_CH, DP_OUT, DP_MCH, DP_MUTE,
        action("ALLE LAENGEN 16", _drm_len16),
        action("KOPIE > NAECHST.", lambda: _copy_next(DRUM)),
        action("LEEREN", lambda: _clear_pat(DRUM))])


# ---------------------------------------------------------------
# MODULAR
# ---------------------------------------------------------------

def _vco_info():
    if VCO_SYNTH is None:
        return "FEHLT"
    return "AN" if _vco_running else "AUS"


def vco_items():
    return [P_VON, P_VSRC, P_VPM, P_VSC, P_VSM, P_VROOT, P_VFIN, P_VTRK,
            P_VWAV, P_VPW, P_VSUB, P_VSO, P_VO2, P_VIV, P_VDET,
            P_VMSRC, P_VMT, P_VMD, P_VFT, P_VFD, P_VFM,
            P_VLVL, P_VPAN, P_VBUS]


def _vco_wave(i, p, pw):
    # eine Periode der Haupt-Welle fuer die Vorschau
    if i == 3:
        return 1.0 if p < pw else -1.0
    return _lfo_wave(i, p)


class VcoPage(ListPage):
    # Kopf: Note gross, Cent-Abweichung (zum Stimmen), Frequenz und eine
    # Vorschau von zwei Perioden (Haupt + Sub, gefaltet - Naeherung)
    def __init__(self):
        ListPage.__init__(self, "VCO", vco_items)
        self.y0 = 66
        self.n = 4
        self._next = 0
        self._shown = None

    def tick(self):
        if since(self._next) < 0:
            return False
        self._next = time.ticks_add(now(), 120)
        v = S["vco"]
        for i in (v["src"], v["msrc"]):
            if i:
                cv_read(i - 1)
        k = (int(vco_pitch_now() * 20), round(vco_fold_drive(), 1), _vco_running)
        if k != self._shown:
            self._shown = k
            return True
        return False

    def draw_head(self):
        v = S["vco"]
        n = vco_pitch_now()
        hz = 440.0 * 2 ** ((n - 69) / 12.0)
        near = clamp_int(int(round(n)), 0, 127)
        ct = int(round((n - near) * 100))
        draw_title("VCO " + ("AN" if _vco_running else "AUS"),
                   ("%dHz" % hz) if hz < 10000 else ("%.1fk" % (hz / 1000.0)))
        on = _vco_running
        BIG(note_name(near), 3, 27, 2, W if on else DIM)
        TR("%+dct" % ct, 125, 27, HI if abs(ct) <= 5 else MID)
        bipbar(72, 38, 52, 4, (ct + 50) / 100.0, HI if abs(ct) <= 5 else LO)
        cy = 53
        a = 6
        typ = v["ft"] if DIST_OK else 0
        drive = vco_fold_drive()
        norm = 1.0 / (1.0 + 0.5 * v["sub"])
        px = py = None
        for k in range(61):
            p = k / 30.0
            y = _vco_wave(v["wav"], p % 1.0, v["pw"])
            if v["sub"]:
                y += v["sub"] * (1.0 if (p / (2 ** v["so"])) % 1.0 < 0.5 else -1.0)
            y *= norm
            if typ:
                y = y * (1.0 - v["fm"]) + fold_shape(y * drive, typ) * v["fm"]
            xx = 4 + 2 * k
            yy = cy - int(clamp(y, -1.0, 1.0) * a)
            if px is not None:
                LN(px, py, xx, yy, W if on else LO)
            px, py = xx, yy
        HL(0, 62, 128, GH)


# ---------------- AUDIO IN (v13.22) ----------------

def _ain_info():
    if AIN_SYNTHS is None:
        return "FEHLT"
    return "AN" if _ain_running else "AUS"


def ain_items():
    return [P_AON, P_AMODE, P_AGAIN, P_ALVL, P_APAN, P_AWID, P_ABUS,
            link("BUS-EFFEKTE", lambda: fx_page(S["ain"]["bus"]),
                 info=lambda: "BUS %d" % S["ain"]["bus"]),
            P_AFT, P_ACU, P_ARS, P_ADT, P_ADD, P_ADM]


class AinPage(ListPage):
    # Kopf: Pegelanzeige L/R (Eingang vor IN GAIN) mit CLIP, darunter
    # Modus, Bus, Filter und Distortion in Kurzform
    def __init__(self):
        ListPage.__init__(self, "AUDIO IN", ain_items)
        self.y0 = 66
        self.n = 4
        self._next = 0
        self._shown = None

    def tick(self):
        if since(self._next) < 0:
            return False
        self._next = time.ticks_add(now(), 80)
        ok = ain_meter_read()
        k = (int(ain_db(0)), int(ain_db(1)), ain_clipping(0), ain_clipping(1),
             _ain_running, ok)
        if k != self._shown:
            self._shown = k
            return True
        return False

    def draw_head(self):
        a = S["ain"]
        draw_title("AUDIO IN", "AN" if _ain_running else "AUS")
        want = _ain_want()
        span = -AIN_METER_FLOOR
        for i in (0, 1):
            y = 28 + i * 11
            T("LR"[i], 1, y, MID if want[i] else DIM)
            db = ain_db(i)
            clip = ain_clipping(i)
            bar(12, y + 1, 78, 6, (db - AIN_METER_FLOOR) / span,
                W if clip else (HI if _ain_running else LO))
            for m in (-24, -12, -6):
                VL(12 + int(78 * (m - AIN_METER_FLOOR) / span), y, 8, GH + 2)
            if clip:
                TR("CLIP", 128, y, W)
            elif db <= AIN_METER_FLOOR:
                TR("--", 128, y, DIM)
            else:
                TR("%d" % int(db), 128, y, MID)
        info = ("ST", "MO", "L", "R")[a["mode"]] + " B%d" % a["bus"]
        if a["ft"]:
            info += " " + SMP_FILT_NAMES[a["ft"]] + " " + _hz(a["cu"])
        if DIST_OK and a["dt"]:
            info += " " + DIST_TYPES[a["dt"]][:4]
        T(info[:16], 1, 51, DIM)
        HL(0, 62, 128, GH)


class ModularPage(ListPage):
    def __init__(self):
        ListPage.__init__(self, "MODULAR", [
            P_EUR, P_QSCALE, P_CV1, P_CV2,
            link("CV LFO", lambda: CvLfoPage(),
                 info=lambda: DIST_TYPES[S["lfof"][0]] if (DIST_OK and S["lfof"][0]) else ">"),
            link("CV ENV", lambda: ListPage("CV ENV", [P_ENVA, P_ENVR, P_ENVD,
                                                         P_ENFT, P_ENFD, P_ENFM])),
            link("VCO", lambda: VcoPage(), info=_vco_info),
            link("AUDIO IN", lambda: AinPage(), info=_ain_info),
            link("SCOPE", lambda: ScopePage()),
            link("KALIBRIERUNG", calib_page)])
        self.y0 = 72
        self.n = 4
        self.rh = 12
        self._next = 0
        self._shown = None

    def tick(self):
        if since(self._next) < 0:
            return False
        self._next = time.ticks_add(now(), 120)
        v = (round(cv_read(0), 2), round(cv_read(1), 2),
             round(cv_out_v[0], 2), round(cv_out_v[1], 2))
        if v != self._shown:
            self._shown = v
            return True
        return False

    def draw_head(self):
        vals = (cv_in_v[0], cv_in_v[1], cv_out_v[0], cv_out_v[1])
        labs = ("IN1", "IN2", "OUT1", "OUT2")
        for k in range(4):
            y = 14 + k * 11
            T(labs[k], 1, y, MID if k < 2 else W)
            bipbar(36, y + 2, 46, 4, (vals[k] + 10.0) / 20.0, HI if k > 1 else LO)
            TR("%+.2f" % vals[k], 128, y, HI)
        m = S["eur"]
        txt = EUR_MODE_NAMES[EUR_MODE_VALUES.index(m)] if m in EUR_MODE_VALUES else "?"
        if _eur_ch:
            txt += " K%d" % _eur_ch
        if cal_test is not None:
            txt = "TEST %.0fV" % cal_test
        T(txt[:16], 1, 59, DIM)
        HL(0, 68, 128, GH)

    def draw_foot(self, it):
        pass


class CvLfoPage(ListPage):
    # CV LFO mit Vorschau der (gefalteten) Welle oben (v13.20)
    def __init__(self):
        ListPage.__init__(self, "CV LFO", [P_LFOW, P_LFOR, P_LFOD, P_LFFT, P_LFFD,
                                           P_LFFM, P_LFFS, P_LFFA])
        self.y0 = 66
        self.n = 4
        self._shown = None

    def tick(self):
        # nur bei FOLD MOD aendert sich die Vorschau von selbst
        ff = S["lfof"]
        if not (ff[0] and ff[3]):
            return False
        d = round(fold_drive_lfo(), 1)
        if d != self._shown:
            self._shown = d
            return True
        return False

    def draw_head(self):
        lf = S["lfo"]
        ff = S["lfof"]
        typ = ff[0] if DIST_OK else 0
        drive = fold_drive_lfo()
        draw_title("CV LFO", ("D%.1f" % drive) if typ else "")
        cy = 42
        a = 14
        HL(4, cy - a, 120, GH)
        HL(4, cy + a, 120, GH)
        px = py = None
        for k in range(61):
            w = _lfo_wave(lf[0], k / 60.0) * lf[2]
            y = w
            if typ:
                y = w * (1.0 - ff[2]) + fold_shape(w * drive, typ) * ff[2]
            xx = 4 + 2 * k
            yy = cy - int(clamp(y, -1.0, 1.0) * a)
            if px is not None:
                LN(px, py, xx, yy, W)
            px, py = xx, yy
        HL(0, 62, 128, GH)


def _calib_leave():
    if cal_test is not None:
        _cal_ui[0] = 0
        set_cal_test(None)


def _cal_reset_in():
    S["calin"] = [[0.0, 1.0], [0.0, 1.0]]
    _calin_changed()
    request_save()
    toast("IN1/IN2", "WERKSWERTE", 1200)


class CalibPage(ListPage):
    # v13.25: oben IN1/IN2 (kalibriert) und OUT1 live
    def __init__(self):
        ListPage.__init__(self, "KALIBRIERUNG", P_CAL + [
            action("IN1 ABGLEICH", lambda: cal_in_auto(0)),
            action("IN2 ABGLEICH", lambda: cal_in_auto(1)),
            action("IN WERKSWERTE", lambda: push(Confirm("IN1/IN2", "KALIBRIERUNG", "ZURUECKSETZEN?", _cal_reset_in)))],
            on_leave=_calib_leave)
        self.y0 = 50
        self.n = 6
        self._next = 0
        self._shown = None

    def tick(self):
        if since(self._next) < 0:
            return False
        self._next = time.ticks_add(now(), 150)
        k = (round(cv_read(0), 3), round(cv_read(1), 3), round(cv_out_v[0], 3))
        if k != self._shown:
            self._shown = k
            return True
        return False

    def draw_head(self):
        draw_title(self.ttl())
        T("IN1 %+.3f" % cv_in_v[0], 0, 27, HI)
        T("IN2 %+.3f" % cv_in_v[1], 0, 37, HI)
        TR("OUT1", 128, 27, DIM)
        TR("%+.3f" % cv_out_v[0], 128, 37, MID)
        HL(0, 46, 128, GH)


def calib_page():
    return CalibPage()


class ScopePage(Page):
    custom = True

    def __init__(self):
        self._next = 0

    def enter(self):
        display.fill(0)
        TC("SCOPE", 64, 56, DIM)
        refresh()

    def leave(self):
        mark_dirty()

    def tick(self):
        if since(self._next) >= 0:
            self._next = time.ticks_add(now(), 150)
            try:
                amyboard.draw_waveform()
            except Exception as e:
                print("SCOPE", e)
        return False


# ---------------------------------------------------------------
# SZENEN
# ---------------------------------------------------------------

def _scene_slot_page(i):
    def store():
        if scenes[i] is not None:
            push(Confirm("SZENE %d" % (i + 1), "UEBERSCHREIBEN?", "", lambda: scene_store(i)))
        else:
            scene_store(i)

    def as_a():
        S["mA"] = i
        request_morph()
        request_save()

    def as_b():
        S["mB"] = i
        request_morph()
        request_save()

    def delete():
        push(Confirm("SZENE %d" % (i + 1), "LOESCHEN?", "", lambda: scene_delete(i)))

    return ListPage("SZENE %d" % (i + 1), [
        action("LADEN", lambda: (scene_recall(i), go_home()),
               vis=lambda: scenes[i] is not None),
        action("SPEICHERN", store),
        action("ALS MORPH A", as_a, vis=lambda: scenes[i] is not None),
        action("ALS MORPH B", as_b, vis=lambda: scenes[i] is not None),
        action("LOESCHEN", delete, vis=lambda: scenes[i] is not None)])


def _slot_info(i):
    def f():
        s = "BELEGT" if scenes[i] is not None else "LEER"
        if S["mA"] == i:
            s = "A " + s[:4]
        elif S["mB"] == i:
            s = "B " + s[:4]
        return s
    return f


def scenes_page():
    items = [link("SZENE %d" % (i + 1), (lambda i=i: _scene_slot_page(i)), info=_slot_info(i))
             for i in range(8)]
    items += [P_MORPH, P_MA, P_MB]
    return ListPage("SZENEN", items)


# ---------------------------------------------------------------
# SAMPLER (v13.0): Slots, Wellenform-Editor, Dateien, Aufnahme
# ---------------------------------------------------------------

SMP_UI = [0]             # gerade bearbeiteter Slot


def _sk():
    return SMP_UI[0]


def _rs(key):
    return lambda: (slot(SMP_UI[0]), key)


def _snd_changed():
    slot_refresh(_sk())


def _full_changed():
    slot_refresh(_sk(), True)


def _trim_changed():
    slot_request_load(_sk(), RELOAD_SETTLE_MS, audition=True)


def _mode_changed():
    _trim_changed()
    slot_refresh(_sk())


def _ms_txt(ms):
    ms = int(ms)
    if ms >= 1000:
        return "%d.%02ds" % (ms // 1000, (ms % 1000) // 10)
    return "%dms" % ms


SP_MODE = P("MODUS", _rs("pm"), kind=ENUM, opts=SMP_MODE_NAMES, apply=_mode_changed)
SP_NC = P("SLICES", _rs("nc"), kind=ENUM, opts=SLICE_NAMES, vals=SLICE_COUNTS,
          apply=_full_changed, vis=lambda: slot(_sk())["pm"] != 2)


def slices_to_drums(k):
    # Slice 1..n auf Instrument 1..n, Original-Muster ins Pattern
    nc = slot_chops(k)
    d = S["drm"]
    n = min(DRUM_ROWS, nc)
    pat = d["pats"][d["pat"]]
    for r in range(n):
        d["smp"][r] = k
        d["sli"][r] = r + 1
        d["lens"][r] = 16
        step = r * 16 // nc
        row = ["0"] * SEQ_MAX_STEPS
        row[step] = "f"
        pat[r] = "".join(row)
    seq_release(DRUM)
    request_save()
    toast("DRUMS", "%d SLICES S%d" % (n, k + 1), 1500)


def _slices_to_drums_act():
    k = _sk()
    n = min(DRUM_ROWS, slot_chops(k))
    push(Confirm("AUF DRUMS", "INSTR. 1-%d UND" % n, "PATTERN %s NEU?"
                 % PATTERN_NAMES[S["drm"]["pat"]], lambda: slices_to_drums(k)))


SP_SY = P("TAKT-SYNC", _rs("sy"), kind=ENUM, opts=SYNC_NAMES, vals=SYNC_BEATS,
          apply=_snd_changed, vis=lambda: FIT_OK and slot(_sk())["pm"] != 2)
SP_FS = P("GRAIN-SUCHE", _rs("fs"), 0, 512, 8, "%d",
          apply=_snd_changed, vis=lambda: FIT_OK and slot(_sk())["sy"] != 0
          and slot(_sk())["pm"] != 2)


def _sync_from_len():
    k = _sk()
    b = sync_suggest(k)
    if not b:
        toast("S%d" % (k + 1), "NICHT GELADEN")
        return
    slot(k)["sy"] = b
    slot_refresh(k)
    request_save()
    toast("S%d SYNC" % (k + 1), sync_label(b))
SP_TU = P("TUNE", _rs("tu"), -24, 24, 1, "%+d", unit="HT", apply=_snd_changed)
SP_FI = P("FEIN", _rs("fi"), -50, 50, 1, "%+d", unit="ct", apply=_snd_changed)
SP_RT = P("GRUNDTON", _rs("rt"), 24, 96, 1, fmtf=note_name, apply=_snd_changed)
SP_LV = P("LEVEL", _rs("lv"), 0.0, 1.5, 0.02, apply=_snd_changed)
SP_PAN = P("PAN", _rs("pan"), 0.0, 1.0, 0.02, bip=True, apply=_snd_changed)
SP_BUS = P("BUS", _rs("bus"), 0, 3, 1, "%d", apply=lambda: (_full_changed(), refresh_buses()))
SP_AT = P("ATTACK", _rs("at"), 0, 5000, 5, "%d", unit="ms", apply=_snd_changed)
SP_DE = P("DECAY", _rs("de"), 0, 5000, 10, "%d", unit="ms", apply=_snd_changed)
SP_SU = P("SUSTAIN", _rs("su"), 0.0, 1.0, 0.02, apply=_snd_changed)
SP_RE = P("RELEASE", _rs("re"), 0, 5000, 10, "%d", unit="ms", apply=_snd_changed)
SP_FT = P("FILTER", _rs("ft"), kind=ENUM, opts=SMP_FILT_NAMES, apply=_snd_changed)
SP_CU = P("CUTOFF", _rs("cu"), 40.0, 16000.0, 1, fmtf=_hz, unit="Hz", log=True,
          apply=_snd_changed, vis=lambda: slot(_sk())["ft"] != 0)
SP_RS = P("RESONANZ", _rs("rs"), 0.5, 16.0, 0.1, "%.1f", apply=_snd_changed,
          vis=lambda: slot(_sk())["ft"] != 0)
SP_FE = P("F-ENV", _rs("fe"), -6.0, 6.0, 0.1, "%+.1f", unit="Okt", bip=True,
          apply=_snd_changed, vis=lambda: slot(_sk())["ft"] != 0)
SP_FD = P("F-DECAY", _rs("fd"), 10, 5000, 10, "%d", unit="ms", apply=_snd_changed,
          vis=lambda: slot(_sk())["ft"] != 0)


def _slot_state(k):
    rt = SRT[k]
    if slot_loading(k) or k in _load_q or k in _load_after:
        return "LAEDT"
    if _nrec["on"] and _nrec["k"] == k:
        return "REC..."
    if _nrec["at"] is not None and _nrec["k"] == k:
        return "WARTE"
    if rt.err:
        return rt.err[:7]
    if not slot(k)["f"]:
        return "RAM" if rt.ram else "LEER"
    return smp_short(slot(k)["f"], 7)


def _slot_play_act():
    k = _sk()
    if not SRT[k].ok:
        toast("S%d" % (k + 1), _slot_state(k))
    elif not slot_play(k):
        toast("S%d" % (k + 1), "KEIN PAD-SYNTH")


def _slot_clear_act():
    k = _sk()
    push(Confirm("SLOT %d" % (k + 1), "LEEREN?", "DATEI BLEIBT", lambda: slot_clear(k)))


def slot_page(k):
    def enter():
        SMP_UI[0] = k
    return ListPage(lambda: "SLOT %d" % (SMP_UI[0] + 1), [
        link("DATEI", lambda: FileBrowser(SMP_UI[0]), info=lambda: _slot_state(SMP_UI[0])),
        link("WELLENFORM", lambda: SampleEditPage(SMP_UI[0]),
             vis=lambda: isinstance(SRT[SMP_UI[0]].info, dict)),
        action("ANHOEREN", _slot_play_act),
        action("AUF SD SPEICHERN", lambda: slot_store(SMP_UI[0]),
               vis=lambda: SRT[SMP_UI[0]].ram and SRT[SMP_UI[0]].ok),
        SP_MODE, SP_NC,
        action("AUF DRUMS VERTEILEN", _slices_to_drums_act,
               vis=lambda: slot_chops(SMP_UI[0]) > 0),
        SP_SY,
        action("SYNC AUS LAENGE", _sync_from_len,
               info=lambda: sync_label(sync_suggest(SMP_UI[0])),
               vis=lambda: FIT_OK and slot(SMP_UI[0])["pm"] != 2 and SRT[SMP_UI[0]].ok),
        SP_FS, SP_TU, SP_FI, SP_RT, SP_LV, SP_PAN, SP_BUS,
        SP_AT, SP_DE, SP_SU, SP_RE,
        SP_FT, SP_CU, SP_RS, SP_FE, SP_FD,
        action("NEU LADEN", lambda: slot_request_load(SMP_UI[0], audition=True),
               vis=lambda: bool(slot(SMP_UI[0])["f"])),
        action("LEEREN", _slot_clear_act,
               vis=lambda: bool(slot(SMP_UI[0])["f"]) or SRT[SMP_UI[0]].ram)],
        on_enter=enter,
        right=lambda: _ms_txt(slot_region(SMP_UI[0])[1] - slot_region(SMP_UI[0])[0])
        if SRT[SMP_UI[0]].ok else "")


# ---------------- Dateiauswahl ----------------

class FileBrowser(Page):
    def __init__(self, k):
        self.k = k
        self.files = []
        self.cur = 0

    def enter(self):
        self.files = smp_list_files()
        f = slot(self.k)["f"]
        self.cur = self.files.index(f) if f in self.files else 0

    def turn(self, d):
        if self.files:
            self.cur = (self.cur + d) % len(self.files)

    def vturn(self, d):
        self.turn(d)

    def press(self):
        if not self.files:
            return
        rel = self.files[self.cur]
        info = wav_info(smp_path(rel))
        if not isinstance(info, dict):
            toast(smp_short(rel), info, 1800)
            return
        slot_assign(self.k, rel)
        pop()

    def draw(self):
        draw_title("DATEI S%d" % (self.k + 1),
                   "%d/%d" % (self.cur + 1, len(self.files)) if self.files else "")
        if not self.files:
            TC("KEINE WAV", 64, 56, MID)
            TC("/sd/samples/", 64, 72, DIM)
            return
        cur = slot(self.k)["f"]
        rows = []
        for rel in self.files:
            nm = rel.split("/")[-1][:-4]
            if rel.startswith("samples/"):
                nm = nm
            else:
                nm = "/" + nm
            rows.append((nm[:13], "*" if rel == cur else ""))
        draw_rows(rows, self.cur)
        TC("OK=LADEN LANG=Z", 64, 118, DIM)


# ---------------- Wellenform-Editor ----------------
#
#   DREHEN        Feld waehlen (START, ENDE, LOOP A, LOOP B, ZOOM, ANHOEREN)
#   DRUECKEN      Feld bearbeiten / Zoom wechseln / anhoeren
#   LANG          Bearbeitung beenden, sonst zurueck
#   E1-E4         START, ENDE, LOOP A, LOOP B direkt
# Schnelles Drehen macht groessere Schritte (1 Pixel = ein Schritt
# bei langsamem Drehen). Nach dem Loslassen wird neu geladen und
# einmal vorgehoert.

SE_FIELDS = ("START", "ENDE", "LOOP A", "LOOP B", "ZOOM", "ANHOEREN")
SE_ZOOMS = (1, 8, 64)
_ACC_MUL = {1: 1, 2: 2, 3: 4, 6: 16}
WX0 = 4                  # Wellenform: x 4..123, y 26..72
WY0 = 26
WH = 46


def se_get(k, f):
    sl = slot(k)
    st, en = slot_region(k)
    if f == 0:
        return st
    if f == 1:
        return en
    if f == 2:
        return clamp_int(sl["ls"], st, en - 1) if sl["ls"] else st
    lb = clamp_int(sl["le"], st + 1, en) if sl["le"] else en
    return lb


def se_set(k, f, v):
    sl = slot(k)
    total = slot_len_ms(k)
    st, en = slot_region(k)
    if f == 0:
        v = clamp_int(v, 0, en - 1)
        sl["st"] = v
        if sl["en"] and sl["en"] - v > SMP_MAX_MS:
            sl["en"] = v + SMP_MAX_MS
    elif f == 1:
        v = clamp_int(v, st + 1, min(total, st + SMP_MAX_MS))
        sl["en"] = 0 if v >= total else v
    elif f == 2:
        sl["ls"] = clamp_int(v, st, se_get(k, 3) - 1)
    else:
        v = clamp_int(v, se_get(k, 2) + 1, en)
        sl["le"] = 0 if v >= en else v
    request_save()
    slot_request_load(k, RELOAD_SETTLE_MS, audition=True)
    mark_dirty()


class _SeProxy:
    def __init__(self, page, f):
        self.page = page
        self.f = f
        self.label = SE_FIELDS[f]

    def nudge(self, d, acc=1):
        self.page.nudge(self.f, d, 3 if acc > 1 else 1)

    def text(self):
        return _ms_txt(se_get(self.page.k, self.f))


class SampleEditPage(Page):
    def __init__(self, k):
        self.k = k
        self.cur = 0
        self.edit = False
        self.zoom = 0
        self.view = None
        self.last = None

    def _total(self):
        return max(1, slot_len_ms(self.k))

    def _focus(self):
        f = self.cur if self.cur < 4 else 0
        if f >= 2 and slot(self.k)["pm"] != 2:
            f = 0
        return se_get(self.k, f)

    def _update_view(self, force=False):
        total = self._total()
        w = max(20, total // SE_ZOOMS[self.zoom])
        c = self._focus()
        if (not force and self.view is not None
                and self.view[1] - self.view[0] == min(w, total)):
            v0, v1 = self.view
            m = (v1 - v0) // 10
            if v0 + m <= c <= v1 - m or (v0 == 0 and c < v1) or (v1 == total and c > v0):
                return
        v0 = clamp_int(c - w // 2, 0, max(0, total - w))
        self.view = (v0, min(total, v0 + w))

    def nudge(self, f, d, acc):
        v0, v1 = self.view or (0, self._total())
        step = max(1, (v1 - v0) // PEAK_COLS) * _ACC_MUL.get(acc, 16 if acc > 6 else 4)
        se_set(self.k, f, se_get(self.k, f) + d * step)
        self._update_view()

    def turn(self, d):
        if self.edit:
            self.nudge(self.cur, d, turn_accel())
        else:
            n = len(SE_FIELDS)
            self.cur = (self.cur + d) % n
            if slot(self.k)["pm"] != 2 and self.cur in (2, 3):
                self.cur = 4 if d > 0 else 1
            self._update_view()

    def vturn(self, d):
        self.edit = False
        self.turn(d)

    def press(self):
        if self.cur < 4:
            self.edit = not self.edit
        elif self.cur == 4:
            self.zoom = (self.zoom + 1) % len(SE_ZOOMS)
            self._update_view(True)
        else:
            _slot_play_k(self.k)

    def back(self):
        if self.edit:
            self.edit = False
            return True
        return False

    def enc_param(self, i):
        if i < 2 or (i < 4 and slot(self.k)["pm"] == 2):
            return _SeProxy(self, i)
        return None

    def tick(self):
        st = (slot_loading(self.k), self.k in _load_after, SRT[self.k].ok)
        if st != self.last:
            self.last = st
            return True
        return False

    def _x(self, ms):
        v0, v1 = self.view
        return WX0 + (ms - v0) * PEAK_COLS // max(1, v1 - v0)

    def draw(self):
        k = self.k
        if self.view is None:
            self._update_view(True)
        v0, v1 = self.view
        st, en = slot_region(k)
        loop = slot(k)["pm"] == 2
        draw_title("S%d %s" % (k + 1, slot_name(k)), "%dx" % SE_ZOOMS[self.zoom])
        pk = slot_peaks(k, v0, v1)
        mid = WY0 + WH // 2
        HL(WX0, mid, PEAK_COLS, GH)
        for c in range(PEAK_COLS):
            ms = v0 + (v1 - v0) * c // PEAK_COLS
            h = pk[c] * (WH // 2) // 255
            if h:
                VL(WX0 + c, mid - h, 2 * h + 1, HI if st <= ms < en else GH + 1)
        for f, col in ((0, W), (1, W), (2, MID), (3, MID)):
            if f >= 2 and not loop:
                continue
            ms = se_get(k, f)
            if v0 <= ms <= v1:
                x = self._x(ms)
                if f < 2:
                    VL(x, WY0 - 1, WH + 2, col)
                    R(x - 1 if f == 1 else x, WY0 - 1, 2, 3, col)
                else:
                    for yy in range(WY0, WY0 + WH, 3):
                        VL(x, yy, 2, col)
                if f == self.cur:
                    R(x - 1, WY0 + WH + 1, 3, 2, W)
        nc = slot_chops(k)
        for i in range(1, nc):
            ms = st + (en - st) * i // nc
            if v0 <= ms <= v1:
                x = self._x(ms)
                for yy in range(WY0 + 1, WY0 + WH, 6):
                    R(x, yy, 1, 2, LO)
        HL(0, WY0 + WH + 4, 128, GH)
        rows = []
        for f in range(len(SE_FIELDS)):
            if f in (2, 3) and not loop:
                val = "-"
            elif f < 4:
                val = _ms_txt(se_get(k, f))
            elif f == 4:
                val = "%dx" % SE_ZOOMS[self.zoom]
            else:
                val = ""
            rows.append((SE_FIELDS[f], val))
        draw_rows(rows, self.cur, 80, 3, 11, self.edit)
        if slot_loading(k) or k in _load_after or k in _load_q:
            T("LAEDT", 3, 118, DIM)
        else:
            T("LEN " + _ms_txt(en - st), 3, 118, DIM)
        TR("OK=EDIT" if self.cur < 4 and not self.edit else "", 125, 118, DIM)


def _slot_play_k(k):
    SMP_UI[0] = k
    _slot_play_act()


# ---------------- Aufnahme ----------------

def _sb_ref(key):
    return lambda: (S["sb"], key)


SR_SLOT = P("ZIEL-SLOT", _sb_ref("rs"), kind=ENUM,
            opts=lambda: ["S%d %s" % (i + 1, slot_name(i)[:5]) for i in range(SMP_SLOTS)])
SR_SRC = P("QUELLE", _sb_ref("src"), kind=ENUM, opts=SMP_SRC_NAMES)
SR_LEN = P("LAENGE", _sb_ref("len"), 1, 10, 1, "%d")
SR_UNIT = P("EINHEIT", _sb_ref("unit"), kind=ENUM, opts=SMP_REC_UNITS)
SR_START = P("START", _sb_ref("rst"), kind=ENUM, opts=SMP_REC_STARTS)


def _rec_act():
    k = S["sb"]["rs"]
    if _nrec["on"] or _nrec["at"] is not None:
        nrec_stop()
    elif slot(k)["f"] or SRT[k].ram:
        push(Confirm("SLOT %d" % (k + 1), "UEBERSCHREIBEN?", "(DATEI BLEIBT)", nrec_start))
    else:
        nrec_start()


def _rec_info():
    if _nrec["at"] is not None:
        return "WARTE"
    if _nrec["on"]:
        return "STOP %d%%" % int(nrec_progress() * 100)
    return "REC"


def rec_page():
    return ListPage("AUFNAHME", [
        SR_SLOT, SR_SRC, SR_LEN, SR_UNIT, SR_START,
        infoline("DAUER", lambda: _ms_txt(_rec_frames() * 1000 // 44100)),
        action("AUFNAHME", _rec_act, info=_rec_info),
        P("AUTO-SPEICHERN", _sb_ref("asv"), kind=BOOL),
        infoline("SD-SPEICHERN", lambda: "JA" if _store_fn() else "FIRMWARE FEHLT"),
        action("EINGANG TESTEN", _rec_test_act)])


def _rec_test_act():
    toast("EINGANG", "2 S MESSEN...", 4000)
    render(force=True)
    res = rec_test()
    toast("EINGANG", "FERTIG", 500)
    push(ListPage("EINGANG TEST", [infoline(n, (lambda r=r: r)) for n, r in res]))


# ---------------- Sampler-Hauptseite ----------------

def _ch_opts():
    return ["AUS"] + ["%d" % c for c in range(1, 17)]


def _pch_set(v):
    old = S["sb"]["pch"]
    S["sb"]["pch"] = v
    try:
        if old and old != v:
            amy.send(synth=old, grab_midi_notes=1)
        if v:
            amy.send(synth=v, grab_midi_notes=0)
    except Exception as e:
        print("PAD-KANAL", e)


SM_CH = P("CHROM. KANAL", kind=ENUM, opts=_ch_opts, getter=lambda: S["sb"]["ch"],
          setter=chrom_set)
SM_CS = P("CHROM. SLOT", _sb_ref("cs"), kind=ENUM,
          opts=lambda: ["S%d %s" % (i + 1, slot_name(i)[:5]) for i in range(SMP_SLOTS)],
          apply=lambda: chrom_configure(), vis=lambda: bool(S["sb"]["ch"]))
SM_CV = P("CHROM. STIMMEN", _sb_ref("cv"), 1, 8, 1, "%d",
          apply=lambda: chrom_configure(), vis=lambda: bool(S["sb"]["ch"]))
SM_PCH = P("PAD-KANAL", kind=ENUM, opts=_ch_opts, getter=lambda: S["sb"]["pch"],
           setter=_pch_set)
SM_SS = P("SLICE-SLOT", _sb_ref("ss"), kind=ENUM,
          opts=lambda: ["S%d %s" % (i + 1, ("%d" % slot_chops(i)) if slot_chops(i) else "-")
                        for i in range(SMP_SLOTS)],
          vis=lambda: bool(S["sb"]["pch"]))


def sampler_page():
    items = [link("S%d" % (i + 1), (lambda i=i: slot_page(i)),
                  info=(lambda i=i: _slot_state(i))) for i in range(SMP_SLOTS)]
    items += [link("AUFNAHME", rec_page),
              SM_CH, SM_CS, SM_CV, SM_PCH, SM_SS,
              infoline("SAMPLE-RAM", lambda: "%dK" % smp_ram_kb()),
              infoline("PADS", lambda: "%d/%d" % (len(PAD_SYNTHS), SMP_SLOTS))]
    return ListPage("SAMPLER", items)


# ---------------------------------------------------------------
# SETUP
# ---------------------------------------------------------------

def _rst_midi():
    push(Confirm("RST ALL MIDI", "ALLE PATCHES", "ENTFERNEN?",
                 lambda: (reset_all_midi(), toast("MIDI", "ALLE ENTFERNT"))))


class MidiMonitorPage(Page):
    # v13.26: letzte MIDI-Ereignisse, neuestes oben
    def __init__(self):
        self._n = None

    def tick(self):
        k = (_midi_count[0], len(_midi_log))
        if k != self._n:
            self._n = k
            return True
        return False

    def press(self):
        del _midi_log[:]
        _midi_count[0] = 0
        mark_dirty()

    def draw(self):
        draw_title("MIDI MONITOR", "%d" % min(_midi_count[0], 99999))
        if not _midi_log:
            TC("WARTE AUF MIDI", 64, 56, MID)
            TC("PAD-KANAL %s" % (("%d" % S["sb"]["pch"]) if S["sb"]["pch"] else "AUS"), 64, 72, DIM)
        y = 28
        for ch, kind, num, val, act in reversed(_midi_log):
            T("K%-2d%s%-3d" % (ch, kind, num), 1, y, W if y == 28 else MID)
            TR(act[:8], 127, y, HI if y == 28 else LO)
            y += 11
        TC("DRUECKEN=LEEREN", 64, 118, DIM)


def midi_setup_page():
    return ListPage("MIDI", [P_THRU, P_MTYPE, P_CLOCK,
                             link("MONITOR", lambda: MidiMonitorPage(),
                                  info=lambda: "%d" % min(_midi_count[0], 9999)),
                             action("RST ALL MIDI", _rst_midi)])


def encb_page():
    return ListPage("TASTER", [P_ENCB[sl] for sl in ENC_SLOT])


# ---------------- I2C-SCAN (v13.23) ----------------
# Zeigt jede Adresse am Bus und was die Firmware dort erkennt
# (amyboard.scan_i2c, ab Firmware 19.08.2026). Fuer Seesaw-Boards (Single,
# Quad, ANO) steht rechts die Produktnummer, die der Chip meldet: 5752 =
# Quad, 5740/6310 = ANO, 4991/5880 = Single.

I2C_TYPE_SHORT = {"adafruit_single": "SINGLE", "adafruit_quad": "QUAD",
                  "adafruit_ano": "ANO", "m5stack": "M5 8ENC"}
I2C_KNOWN_SHORT = {0x3C: "DISPLAY", 0x3D: "DISPLAY", 0x40: "AUDIO",
                   0x41: "M5 8ENC", 0x48: "CV IN", 0x52: "JOYSTICK",
                   0x58: "CV OUT"}


def i2c_scan_rows():
    rows = []
    fn = getattr(amyboard, "scan_i2c", None)
    res = None
    if fn is not None:
        try:
            res = fn(verbose=False)
        except Exception as e:
            print("SCAN_I2C", e)
    if res is None:
        try:
            res = [(a, None, "") for a in sorted(amyboard.get_i2c().scan())]
        except Exception as e:
            return [("I2C FEHLER", str(e)[:7])]
    for addr, typ, desc in res:
        name = I2C_TYPE_SHORT.get(typ) if typ else None
        val = ""
        if "product" in desc:
            val = "P" + desc.split()[-1][:6]
            name = name or "SEESAW?"
        if not name:
            name = I2C_KNOWN_SHORT.get(addr, "?")
        rows.append(("%02X %s" % (addr, name), val))
    if not rows:
        rows.append(("KEINE GERAETE", ""))
    return rows


def i2c_scan_page():
    toast("I2C", "SUCHE...", 3000)
    render(force=True)
    rows = i2c_scan_rows()
    items = [infoline("SKETCH NUTZT", lambda: "+".join(ENC_DEVS)[:7] if ENC_DEVS else "-")]
    items += [infoline(n, (lambda v=v: v)) for n, v in rows]
    toast("I2C", "%d GERAETE" % len(rows), 600)
    return ListPage("I2C-SCAN", items)



# ---------------- Encoder-Menue (v13.24) ----------------
# Uebersicht nach Geraet; Drehen an einem Zusatz-Encoder springt auf
# seine Zeile. Die Encoder-Seite zeigt nach FUNKTION nur passende Zeilen.

ENC_UI = [0]
ENC_DEV_TITLES = ("M5STACK", "QUAD 1", "QUAD 2")


def _eu():
    return ENC_UI[0]


def _enc_set_f(f):
    sl = _eu()
    if S["encf"][sl] != f:
        _enc_pend.pop(sl, None)
        S["encf"][sl] = f
        _encf_changed()


def _func_set(fn):
    sl = _eu()
    f = S["encf"][sl]
    if enc_func(f) == fn:
        return
    if fn == 2:
        f = "pkc"
    elif fn == 4:
        f = enc_group_keys(0)[0]
    else:
        f = ("AUS", "SCREEN", None, "chan")[fn]
    _enc_set_f(f)


def _grp_set(gi):
    _enc_set_f(enc_group_keys(gi)[0])


def _ld_changed():
    sl = _eu()
    if S["encx"][sl]["ld"] and S["encb"][sl] != "KONTEXT":
        S["encb"][sl] = "KONTEXT"
        toast("TASTER", "JETZT KONTEXT", 1200)
    if not S["encx"][sl]["ld"]:
        _enc_pend.pop(sl, None)


def _is_fn(fn):
    return lambda: enc_func(S["encf"][_eu()]) == fn


EP_FUNC = P("FUNKTION", kind=ENUM, opts=FUNC_NAMES, vals=list(range(5)),
            getter=lambda: enc_func(S["encf"][_eu()]), setter=_func_set)
EP_CH = P("KANAL", kind=ENUM, opts=["AKTUELL"] + ["K%d" % c for c in PATCH_ENC_CHANNELS],
          vals=PATCH_ENC_KEYS, getter=lambda: S["encf"][_eu()], setter=_enc_set_f,
          vis=_is_fn(2))
EP_PL = P("LISTE", lambda: (S["encx"][_eu()], "pl"), kind=ENUM, opts=PL_NAMES,
          apply=lambda: _enc_pend.pop(_eu(), None), vis=_is_fn(2))
EP_LD = P("LADEN", lambda: (S["encx"][_eu()], "ld"), kind=ENUM, opts=LD_NAMES,
          apply=_ld_changed, vis=_is_fn(2))
EP_GRP = P("GRUPPE", kind=ENUM, opts=ENC_GROUP_NAMES, vals=list(range(len(ENC_GROUPS))),
           getter=lambda: ENC_GROUP_OF.get(S["encf"][_eu()], 0), setter=_grp_set,
           vis=_is_fn(4))
EP_PAR = P("WERT", kind=ENUM,
           opts=lambda: [REG[k].label for k in
                         enc_group_keys(ENC_GROUP_OF.get(S["encf"][_eu()], 0))],
           vals=lambda: enc_group_keys(ENC_GROUP_OF.get(S["encf"][_eu()], 0)),
           getter=lambda: S["encf"][_eu()], setter=_enc_set_f, vis=_is_fn(4))
EP_BTN = P("TASTER", lambda: (S["encb"], _eu()), kind=ENUM, opts=ENCB_NAMES,
           vals=ENCB_KEYS)
EP_LED = P("LED", lambda: (S["encx"][_eu()], "led"), kind=ENUM, opts=LED_NAMES,
           apply=lambda: update_leds(), vis=lambda: bool(ENC_LED))


def _enc_now():
    f = S["encf"][_eu()]
    prm = REG.get(f)
    return prm.text()[:9] if prm is not None and hasattr(prm, "text") else "-"


def enc_items():
    return [EP_FUNC, EP_CH, EP_PL, EP_LD, EP_GRP, EP_PAR,
            infoline("JETZT", _enc_now, vis=lambda: enc_func(S["encf"][_eu()]) >= 2),
            EP_BTN, EP_LED]


def _slot_dev(sl):
    try:
        return ENC_DEV_TITLES[ENC_DEVNO[ENC_SLOT.index(sl)]]
    except Exception:
        return ""


class EncEditPage(ListPage):
    def __init__(self, sl):
        ENC_UI[0] = sl
        ListPage.__init__(self, lambda: ENC_SLOT_NAMES[_eu()], enc_items,
                          right=lambda: _slot_dev(_eu()))

    def enc_jump(self, sl):
        # anderen Zusatz-Encoder drehen = dessen Einstellungen zeigen
        if sl != ENC_UI[0]:
            self.edit = False
            ENC_UI[0] = sl
            toast("ENCODER", ENC_SLOT_NAMES[sl], 500)

    def leave(self):
        request_save()


def _eset_info():
    return ESET_NAMES[S["eset"]]


P_ESET = P("SET", kind=ENUM, opts=ESET_NAMES, vals=[0, 1, 2], confirm=True,
           getter=lambda: S["eset"], setter=eset_switch)


class EncOverviewPage(ListPage):
    def __init__(self):
        items = [infoline("GERAETE", _devs_text), P_ESET, P_INV,
                 link("LEDS", led_page, vis=lambda: _leds_n() > 0)]
        self._row = {}
        last = None
        for i in range(len(ENC_SLOT)):
            sl = ENC_SLOT[i]
            dv = ENC_DEVNO[i] if i < len(ENC_DEVNO) else 0
            if dv != last:
                last = dv
                items.append(infoline("= " + ENC_DEV_TITLES[dv] + " =", lambda: ""))
            self._row[sl] = len(items)
            items.append(link(ENC_SLOT_NAMES[sl], (lambda s=sl: EncEditPage(s)),
                              info=(lambda s=sl: enc_func_text(s))))
        if not ENC_SLOT:
            items.append(infoline("KEINE ZUSATZ-ENC", lambda: ""))
        items.append(link("I2C-SCAN", i2c_scan_page))
        ListPage.__init__(self, "ENCODER", items)

    def enc_jump(self, sl):
        if sl in self._row and not self.edit:
            self.cur = self._row[sl]


def _devs_text():
    if not ENC_DEVS:
        return "KEINE"
    nq = ENC_DEVS.count("QUAD")
    t = "M5" if "M5" in ENC_DEVS else ""
    if nq:
        t += ("+" if t else "") + ("%dQUAD" % nq if nq > 1 else "QUAD")
    return t


def encoder_page():
    return EncOverviewPage()


# ---------------- SCHONER-BILD (v13.30) ----------------

def rSV(k):
    return lambda: (S["sv"], k)


def _sv_rnd():
    return S["sv"]["bild"] == 0


def _pool_p(i):
    def g():
        return (S["sv"]["pool"] >> i) & 1

    def s(v):
        if v:
            S["sv"]["pool"] |= 1 << i
        else:
            S["sv"]["pool"] &= 255 ^ (1 << i)
    return P(SV_NAMES[i], kind=BOOL, getter=g, setter=s, vis=_sv_rnd)


SP_BILD = P("BILD", rSV("bild"), kind=ENUM, opts=["ZUFALL"] + SV_NAMES + ["TEXT"])
SP_WZ = P("WECHSEL", rSV("wz"), kind=ENUM, opts=["1 MIN", "2 MIN", "5 MIN", "10 MIN"],
          vis=_sv_rnd)
SP_LZ = P("LEERLAUF", rSV("lz"), kind=ENUM, opts=["30 MIN", "1 STD", "4 STD"])
SP_HL = P("KONTRAST", rSV("hl"), kind=ENUM, opts=["DUNKEL", "MITTEL", "HELL"])
SP_POOL = [_pool_p(i) for i in range(len(SV_NAMES))]


def _fly_set(s):
    S["sv"]["fly"] = s.upper()[:10]
    request_save()


def saver_page():
    return ListPage("SCHONER", [SP_BILD, SP_WZ, SP_LZ, SP_HL,
                                    action("FLYER", lambda: push(TextEntry("FLYER", _fly_set)),
                                           info=lambda: S["sv"]["fly"][:8]),
                                    infoline("= IM ZUFALL =", lambda: "", vis=_sv_rnd)]
                    + SP_POOL + [action("JETZT ZEIGEN", sv_start)])


# ---------------- LEDS (v13.29) ----------------

def rLED(k):
    return lambda: (S["led"], k)


def _leds_n():
    try:
        return enc.leds if enc is not None else 0
    except Exception:
        return 0


def _nav_led_ok():
    return NAV_LED is not None and NAV_LED < _leds_n()


def _led_upd():
    update_leds()


LP_HELL = P("HELLIGKEIT", rLED("hl"), kind=ENUM, opts=["1", "2", "3", "4"], apply=_led_upd)
LP_NAV = P("FARBE", rLED("nav"), kind=ENUM, opts=LED_NAV_NAMES, apply=_led_upd,
           vis=_nav_led_ok)
LP_ED = P("EDIT", rLED("ed"), kind=ENUM, opts=LED_IND_NAMES, apply=_led_upd, vis=_nav_led_ok)
LP_BT = P("TAKT", rLED("bt"), kind=ENUM, opts=LED_IND_NAMES, apply=_led_upd, vis=_nav_led_ok)
LP_CF = P("KANAL-BLITZ", rLED("cf"), kind=BOOL, vis=_nav_led_ok)
LP_PN = P("PANIC", rLED("pn"), kind=ENUM, opts=LED_IND_NAMES, vis=_nav_led_ok)
LP_WN = P("WARNUNG", rLED("wn"), kind=ENUM, opts=LED_IND_NAMES, apply=_led_upd,
          vis=_nav_led_ok)
LP_ST = P("ZUSTAND", rLED("st"), kind=BOOL, apply=_led_upd, vis=lambda: bool(ENC_LED))
LP_FL = P("DREH-BLITZ", rLED("fl"), kind=BOOL, vis=lambda: bool(ENC_LED))
LP_SV = P("IM SCHONER", rLED("sv"), kind=ENUM, opts=["AUS", "AN"])


def led_page():
    return ListPage("LEDS", [
        infoline("SINGLE", lambda: "JA" if _nav_led_ok() else "FEHLT"),
        LP_HELL,
        infoline("= NAVIGATION =", lambda: "", vis=_nav_led_ok),
        LP_NAV, LP_ED, LP_BT, LP_CF, LP_PN, LP_WN,
        infoline("= ZUSATZ-ENC =", lambda: "", vis=lambda: bool(ENC_LED)),
        LP_ST, LP_FL,
        infoline("= ALLGEMEIN =", lambda: ""),
        LP_SV,
        action("LED-TEST", led_test)])


def _wifi_new():
    if not sd_present():
        toast("WLAN", "SD-KARTE FEHLT")
        return

    def got_pw(ssid):
        def f(pw):
            toast("WLAN", "GESPEICHERT" if wifi_save(ssid, pw) else "FEHLER")
        return f

    push(TextEntry("SSID", lambda ssid: push(TextEntry("PASSWORT", got_pw(ssid), True))))


def _wifi_conn():
    toast("WLAN", "VERBINDE...", 3000)
    render(force=True)
    ok = wifi_connect()
    toast("WLAN", str(wlan_ip) if ok else "FEHLER")


def wlan_page():
    return ListPage("WLAN", [
        infoline("STATUS", lambda: "VERB." if wlan_connected else "GETR."),
        infoline("IP", lambda: str(wlan_ip)[:12] if wlan_ip else "-", vis=lambda: wlan_connected),
        infoline("NETZ", lambda: (wifi_load()[0] or "-")[:7]),
        action("VERBINDEN", _wifi_conn),
        action("NEU EINGEBEN", _wifi_new),
        action("TRENNEN", lambda: (wifi_disconnect(), toast("WLAN", "GETRENNT")))])


def takt_page():
    return ListPage("TAKT", [
        P_SQM, P_VMS,
        action("VORAUS-TEST", voraus_test, info=lambda: "CLAP"),
        infoline("VORLAUF STEPS", lambda: "%d/32" % (lookahead_subs() // SUB_PER_32),
                 vis=lambda: S["sqm"]),
        P_UIT, P_NOTLAUF, P_TRANSPORT,
        infoline("UI LAEUFT", lambda: "TIMER" if ui_timer_mode() else "LOOP"),
        infoline("SEQ-TAKT", lambda: "FEIN" if _seq_slot is not None else "LOOP"),
        infoline("NOTLAUF", lambda: ("AN" if _notlauf_timer is not None else
                                     ("FEHLT" if S["notlauf"] else "AUS")),
                 vis=lambda: not S["uit"]),
        infoline("LOOP", lambda: "STEHT" if _notlauf_active else "OK",
                 vis=lambda: not S["uit"]),
        infoline("UEBERNAHMEN", lambda: "%d" % min(_notlauf_count, 99999),
                 vis=lambda: not S["uit"])])


def _free_mem():
    try:
        return "%dK" % (gc.mem_free() // 1024)
    except Exception:
        return "?"


def _i2c_count():
    try:
        return "%d" % len(amyboard.get_i2c().scan())
    except Exception:
        return "?"


def info_page():
    return ListPage("INFO", [
        infoline("VERSION", lambda: VERSION),
        infoline("ENCODER", lambda: "%d" % encoder_count),
        infoline("ZUSATZ", lambda: "%d" % len(PARAM_ENCODERS)),
        infoline("JOYSTICK", lambda: "JA" if joystick_available else "NEIN"),
        infoline("DISTORTION", lambda: "JA" if DIST_OK else "NEIN"),
        infoline("TAKT-SYNC", lambda: "JA" if FIT_OK else "NEIN"),
        infoline("VCO-SYNTH", lambda: "%d" % VCO_SYNTH if VCO_SYNTH else "FEHLT"),
        infoline("AUDIO IN", lambda: "%d/%d" % AIN_SYNTHS if AIN_SYNTHS else "FEHLT"),
        infoline("DX7 SD (FM)", lambda: "JA" if fm_mod() else "NEIN"),
        infoline("NAV-LED", lambda: ("%d" % NAV_LED) if _nav_led_ok() else "KEINE"),
        link("I2C", i2c_scan_page, info=_i2c_count),
        infoline("RAM FREI", _free_mem),
        infoline("LAST", lambda: "%d%%" % int(cpu_load * 100)),
        infoline("STIMMEN", lambda: "%d/%d" % (voices_total(), S["vbud"])),
        infoline("SPEICHER", lambda: BASE),
        infoline("SD", lambda: sd_status[:10]),
        infoline("SD-GRUND", lambda: sd_switch_err[:9], vis=lambda: bool(sd_switch_err)),
        infoline("SD-TAKT", lambda: _sd_cfg_txt(sd_freq, sd_pull)),
        infoline("SD FREI", lambda: ("%dM" % (sd_free_kb() // 1024)) if sd_free_kb() >= 0 else "?"),
        infoline("SPEICH.FEHLER", lambda: _save_err[:6] if _save_err else "KEINER"),
        infoline("LINE/ELL", lambda: "%s/%s" % ("J" if HAS_LINE else "N", "J" if HAS_ELLIPSE else "N")),
        infoline("BOOT", lambda: "%.1fs" % (_boot_dur_ms / 1000.0)),
        infoline("RAM NACH BOOT", lambda: "%dK" % (_ram_boot // 1024)),
        infoline("DISPLAY", lambda: ("BAENDER" if (_fast_ok and S["dfast"]) else "VOLL")),
        infoline("ZEICHNEN MAX", lambda: "%dms" % (MEAS["draw"] // 1000)),
        infoline("SENDEN MAX", lambda: "%dms" % (MEAS["flush"] // 1000)),
        infoline("SEQ MAX", lambda: "%dms" % (MEAS["seq"] // 1000)),
        infoline("SPEICHERN MAX", lambda: "%dms" % (MEAS["save"] // 1000)),
        infoline("VERPASST", lambda: "%d" % min(MEAS["miss"], 99999)),
        infoline("SPAET", lambda: "%d/%d" % (min(MEAS["late"], 9999), min(MEAS["drop"], 9999))),
        infoline("TICK-ABW", lambda: ("-" if TDIFF[0] is None else
                                      "%d/%d" % (TDIFF[0], TDIFF[1]))[:7]),
        infoline("CV-TRIGGER", lambda: "/".join(["AMY" if trig_native(o) else
                                                  ("PY" if S["drm"]["trg"][o] >= 0 else "-")
                                                  for o in (0, 1)])),
        infoline("BEDIENUNG MAX", lambda: "%dms" % (MEAS["ui"] // 1000)),
        action("MESSUNG RESET", lambda: (meas_reset(), toast("MESSUNG", "ZURUECKGESETZT")))])


def factory_reset():
    try:
        notlauf_stop()
        seq_cb_stop()
    except Exception:
        pass
    # v13.5: alte Zustandsdateien ueberall loeschen (auch eine
    # beschaedigte auf der SD-Karte)
    for base in ("/sd/", "/user/current/", "/user/", "/"):
        for n in STATE_NAMES:
            try:
                os.remove(base + n)
            except Exception:
                pass
    try:
        d = default_state()
        d["n"] = S.get("n", 0) + 1     # neuer als alle Backups
        f = open(STATE_FILE, "w")
        f.write(json.dumps(d))
        f.close()
    except Exception as e:
        print("RESET", e)
    display.fill(0)
    TC("WERKSRESET", 64, 56, W)
    refresh()
    time.sleep_ms(800)
    try:
        import machine
        machine.reset()
    except Exception as e:
        print("RESET", e)


def _sd_remount_act(clean=False):
    toast("SD-KARTE", "PRUEFE...", 5000)
    render(force=True)
    ok, txt = sd_remount(clean)
    toast("SD OK" if ok else "SD FEHLER", txt, 2500 if ok else 4000)


# ---------------- SD TEST (v13.7): jeden Schritt einzeln pruefen ----------------

def _sd_step(res, name, fn):
    t0 = time.ticks_ms()
    try:
        fn()
        r = "OK %dms" % time.ticks_diff(time.ticks_ms(), t0)
    except Exception as e:
        n = e.args[0] if (e.args and isinstance(e.args[0], int)) else None
        r = ("E%d" % n) if n is not None else str(e)[:8]
        print("SD TEST", name, repr(e))
    res.append((name, r))


def _w_chunks(path, data, chunk=512, flush=False):
    f = open(path, "wb")
    try:
        for i in range(0, len(data), chunk):
            f.write(data[i:i + chunk])
        if flush:
            f.flush()
    finally:
        f.close()


def sd_test():
    res = []
    d = "/sd/"
    blk = b"0123456789abcdef" * 32
    try:
        js = json.dumps(S).encode()
    except Exception:
        js = blk * 20
    res.append(("TAKT", ("%dMHZ" % (sd_freq // 1000000)) if sd_freq else "STANDARD"))
    res.append(("JSON KB", "%d" % (len(js) // 1024)))
    _sd_step(res, "LISTDIR", lambda: os.listdir("/sd"))
    _sd_step(res, "W 4K", lambda: _w_chunks(d + "t_4k.bin", blk * 8))
    _sd_step(res, "W 32K", lambda: _w_chunks(d + "t_32k.bin", blk * 64))
    _sd_step(res, "W 32K AM STUECK", lambda: _w_chunks(d + "t_32k1.bin", blk * 64, 32768))
    _sd_step(res, "W 4K+FLUSH", lambda: _w_chunks(d + "t_4kf.bin", blk * 8, 512, True))
    _sd_step(res, "W JSON", lambda: _w_chunks(d + "t_state.json", js))
    _sd_step(res, "W JSON+FLUSH", lambda: _w_chunks(d + "t_statf.json", js, 512, True))
    _sd_step(res, "W ZUSTAND.TMP", lambda: _w_chunks(STATE_TMP if BASE == d else d + "dolphin_state.json.tmp", js))

    def _ren():
        _w_chunks(d + "t_a.bin", blk)
        try:
            os.remove(d + "t_b.bin")
        except Exception:
            pass
        os.rename(d + "t_a.bin", d + "t_b.bin")
    _sd_step(res, "RENAME", _ren)

    def _rd():
        f = open(d + "t_32k.bin", "rb")
        ok = f.read() == blk * 64
        f.close()
        if not ok:
            raise Exception("DATEN FALSCH")
    _sd_step(res, "LESEN 32K", _rd)
    for n in ("t_4k.bin", "t_32k.bin", "t_32k1.bin", "t_4kf.bin", "t_state.json",
              "t_statf.json", "t_a.bin", "t_b.bin"):
        try:
            os.remove(d + n)
        except Exception:
            pass
    res.append(("FREI", ("%dM" % (sd_free_kb() // 1024)) if sd_free_kb() >= 0 else "?"))
    gc.collect()
    return res


def _sd_test_act():
    toast("SD TEST", "LAEUFT...", 20000)
    render(force=True)
    res = sd_test()
    if any(r[1].startswith("E") for r in res):
        # Schreiben scheitert: alle Einstellungen durchprobieren
        toast("SD TEST", "PROBIERE TAKTE", 20000)
        render(force=True)
        m = []
        found = sd_find_cfg(m)
        res.append(("-- TAKT/PULLUP --", ""))
        res += m
        res.append(("GEWAEHLT", _sd_cfg_txt(found[0], found[1]) if found else "KEINE"))
        if found is not None:
            ok, txt = sd_remount()
            res.append(("ZUSTAND", txt[:9]))
    toast("SD TEST", "FERTIG", 600)
    push(ListPage("SD TEST", [infoline(n, (lambda r=r: r)) for n, r in res]))


def _sd_clean_act():
    push(Confirm("SD ZUSTAND NEU", "ZUSTANDSDATEI", "AUF SD NEU?", lambda: _sd_remount_act(True)))


def setup_page():
    return ListPage("SETUP", [
        link("MIDI", midi_setup_page),
        link("ENCODER", encoder_page),
        link("MAKROS", lambda: ListPage("MAKROS", P_MACRO)),
        P_AUDIO, P_VBUD, P_FAIL,
        link("DISPLAY", lambda: ListPage("DISPLAY", [P_BRIGHT, P_DIM,
                                                    link("SCHONER-BILD", saver_page),
                                                    P_DFAST])),
        link("WLAN", wlan_page),
        link("TAKT", takt_page),
        action("SD EINBINDEN", _sd_remount_act, info=lambda: "OK" if BASE == "/sd/" else "-"),
        action("SD ZUSTAND NEU", _sd_clean_act),
        action("SD TEST", _sd_test_act),
        link("INFO", info_page),
        action("WERKSRESET", lambda: push(Confirm("WERKSRESET", "ALLE EINSTELL.",
                                                  "ZURUECKSETZEN?", factory_reset)))])


# Karussell-Karten: (Name, Hinweis, Symbol, Seite)
CARDS = [
    ("KLANG", "PATCH FILTER ENV", 0, klang_page),
    ("MIXER", "16 KANAELE", 1, MixerPage),
    ("EFFEKTE", "REVERB CHORUS EQ", 2, fx_page),
    ("SEQUENCER", "SPUREN 303 DRUMS", 3, SeqPage),
    ("MODULAR", "CV VCO AUDIO IN", 4, ModularPage),
    ("SZENEN", "8 PLAETZE MORPH", 5, scenes_page),
    ("SAMPLER", "8 SLOTS + REC", 6, sampler_page),
    ("SETUP", "MIDI ENC WLAN", 7, setup_page),
]


# ================================================================
# EINGABE
# ================================================================

LONG_MS = 450
PANIC_MS = 2000

_btn_down = False
_btn_t0 = 0
_btn_turned = False
_btn_fired = False
_last_nav = 0
_last_turn_ms = 0
_last_input = 0
_saver = False
_joy = None
_joy_armed = True
_joy_varmed = True


def _nav_delta():
    global _last_nav
    if enc is None:
        return 0
    try:
        pos = enc.read(NAV_ENCODER)
    except Exception:
        return 0
    d = pos - _last_nav
    if d:
        _last_nav = pos
    return -d if S["inv"] else d


def _nav_button():
    if enc is None:
        return False
    try:
        return bool(enc.button(NAV_BUTTON))
    except Exception:
        return False


def _joy_delta():
    # Joystick X: einmal deutlich auslenken = ein Schritt
    global _joy_armed
    if _joy is None:
        return 0
    x = _joy[0]
    if x > 0.5 + JOY_DEADZONE or x < 0.5 - JOY_DEADZONE:
        if _joy_armed:
            _joy_armed = False
            return 1 if x > 0.5 else -1
        return 0
    _joy_armed = True
    return 0


def _joy_vdelta():
    # Joystick Y: einmal deutlich auslenken = eine Zeile (+1 = runter)
    global _joy_varmed
    if _joy is None:
        return 0
    y = _joy[1]
    if y > 0.5 + JOY_Y_DEADZONE or y < 0.5 - JOY_Y_DEADZONE:
        if _joy_varmed:
            _joy_varmed = False
            d = 1 if y > 0.5 else -1
            return -d if JOY_Y_INVERT else d
        return 0
    _joy_varmed = True
    return 0


def _update_accel(d):
    global _accel, _last_turn_ms
    dt = since(_last_turn_ms)
    _last_turn_ms = now()
    if dt < 30 or abs(d) >= 3:
        _accel = 6
    elif dt < 60:
        _accel = 3
    elif dt < 110:
        _accel = 2
    else:
        _accel = 1


def wake():
    # -> True, wenn der Bildschirmschoner lief (Eingabe wird verschluckt)
    global _last_input, _saver
    _last_input = now()
    if _saver:
        _saver = False
        apply_bright()
        mark_dirty()
        return True
    return False


def on_channel_select(ch):
    S["cur"] = ch
    request_save()
    mark_dirty()


def on_hold_turn(d):
    ch = 1 + (S["cur"] - 1 + d) % 16
    on_channel_select(ch)
    toast("KANAL %d" % ch, chan_patch_name(ch)[:14], 700)


_joy_btn_prev = False


def poll_input():
    global _btn_down, _btn_t0, _btn_turned, _btn_fired, _hold_progress
    global _joy_btn_prev
    if joy_owned():
        # Joystick gehoert Grids X/Y oder der 303
        d = _nav_delta()
        vd = 0
    else:
        d = _nav_delta() + _joy_delta()
        vd = _joy_vdelta()
    jb = _joy is not None and bool(_joy[2])
    if acid_joy_active():
        # Joystick-Knopf = Klang uebernehmen (nicht Menue-Druecken)
        if jb and not _joy_btn_prev:
            acid_joy_latch()
        _joy_btn_prev = jb
        jb = False
    pressed = _nav_button() or jb

    if d or vd or (pressed and not _btn_down):
        if wake():
            if pressed:
                _btn_down = True
                _btn_fired = True
                _btn_t0 = now()
            return

    if d:
        _update_accel(d)
        if _btn_down:
            _btn_turned = True
            _hold_progress = 0.0
            on_hold_turn(d)
        else:
            top().turn(d)
            mark_dirty()

    if vd and not _btn_down:
        top().vturn(vd)
        mark_dirty()

    if pressed and not _btn_down:
        _btn_down = True
        _btn_t0 = now()
        _btn_turned = False
        _btn_fired = False
    elif pressed and _btn_down:
        if not _btn_turned and not _btn_fired and isinstance(top(), HomePage):
            held = since(_btn_t0)
            if held >= LONG_MS:
                prog = clamp((held - LONG_MS) / float(PANIC_MS - LONG_MS), 0.0, 1.0)
                if prog - _hold_progress > 0.04 or prog >= 1.0:
                    _hold_progress = prog
                    mark_dirty()
                if held >= PANIC_MS:
                    _btn_fired = True
                    _hold_progress = 0.0
                    panic()
    elif not pressed and _btn_down:
        _btn_down = False
        if _hold_progress:
            _hold_progress = 0.0
            mark_dirty()
        if _btn_turned or _btn_fired:
            return
        wake()
        if since(_btn_t0) < LONG_MS:
            top().press()
        else:
            p = top()
            if not p.back():
                pop()
        mark_dirty()


# ---------------- Zusatz-Encoder E1-E8, Q1-Q8 ----------------

_last_param = [0] * len(PARAM_ENCODERS)
_enc_page_seen = None


def resync_param_encoders():
    for i in range(len(PARAM_ENCODERS)):
        try:
            _last_param[i] = enc.read(PARAM_ENCODERS[i])
        except Exception:
            pass


def read_param_encoders():
    global _enc_page_seen
    if enc is None or not PARAM_ENCODERS:
        return
    p = top()
    if p is not _enc_page_seen:
        # Seitenwechsel: Positionen uebernehmen, ohne auszuloesen
        _enc_page_seen = p
        resync_param_encoders()
        return
    jump = getattr(p, "enc_jump", None)     # v13.24: Encoder-Menue
    for i in range(len(PARAM_ENCODERS)):
        sl = ENC_SLOT[i]
        f = S["encf"][sl]
        if f == "AUS" and jump is None:
            continue          # nicht lesen = kein I2C-Verkehr
        try:
            pos = enc.read(PARAM_ENCODERS[i])
        except Exception:
            continue
        d = pos - _last_param[i]
        if not d:
            continue
        _last_param[i] = pos
        _led_flash[sl] = now()          # v13.29: DREH-BLITZ
        if S["inv"]:
            d = -d
        if wake():
            continue
        if jump is not None:
            jump(sl)
            mark_dirty()
            continue
        if f == "SCREEN":
            prm = p.enc_param(enc_page_index(sl))
            quiet = True
        else:
            prm = REG.get(f)
            quiet = getattr(prm, "own_toast", False)
        if prm is None:
            continue
        vis = getattr(prm, "vis", None)
        if vis is not None and not vis():
            continue
        if hasattr(prm, "nudge_slot"):
            prm.nudge_slot(sl, d, 2 if abs(d) >= 3 else 1)
        else:
            prm.nudge(d, 2 if abs(d) >= 3 else 1)
        mark_dirty()
        if not quiet:
            toast(prm.label[:14], prm.text(), 700)


# ---------------- Taster der Zusatz-Encoder (v13.19) ----------------

_pb_t0 = [None] * len(PARAM_BUTTONS)
_pb_long = [False] * len(PARAM_BUTTONS)


def _mute_toggle(ch):
    S["mute"][ch] ^= 1
    apply_level(ch)
    apply_master_volume()
    toast("K%d" % ch, "MUTE" if S["mute"][ch] else "AN", 700)


def enc_button_action(sl, long):
    a = S["encb"][sl]
    if a == "KONTEXT":
        f = S["encf"][sl]
        if f == "SCREEN":
            fn = getattr(top(), "enc_press", None)
            if fn is not None:
                fn(enc_page_index(sl), long)
        elif f.startswith("pk") or f == "chan":
            ch = S["cur"] if f == "chan" else enc_patch_ch(f)
            if long:
                _enc_pend.pop(sl, None)
                S["cur"] = ch
                push(PatchBrowser())
            elif not enc_pend_load(sl):
                _mute_toggle(ch)
        elif f != "AUS":
            prm = REG.get(f)
            if isinstance(prm, P) and prm.kind == NUM and (prm.vis is None or prm.vis()):
                push(EditPage(prm, ENC_SLOT_NAMES[sl]))
    elif long:
        if a == "PANIC":
            panic()
    elif a == "START":
        seq_toggle()
    elif a == "TAP":
        tap_tempo()
        toast("TAP", "%d BPM" % S["tempo"], 700)
    elif a.startswith("MUTE"):
        _mute_toggle(int(a[4:]))
    elif a == "AIN":
        ain_toggle()
    elif a == "ESET":
        eset_next()
    elif a in ("M303", "MDRM"):
        i = ACID if a == "M303" else DRUM
        t = trk_cfg(i)
        t["mute"] = 0 if t["mute"] else 1
        seq_release(i)
        toast(track_label(i), "MUTE" if t["mute"] else "AN", 700)
    request_save()
    mark_dirty()


def read_param_buttons():
    # Kurz = beim Loslassen, lang = sobald LONG_MS erreicht (einmal)
    if enc is None:
        return
    for i in range(len(PARAM_BUTTONS)):
        sl = ENC_SLOT[i]
        if S["encb"][sl] == "AUS":
            continue              # nicht lesen = kein I2C-Verkehr
        try:
            down = bool(enc.button(PARAM_BUTTONS[i]))
        except Exception:
            continue
        t0 = _pb_t0[i]
        if down:
            if t0 is None:
                _pb_t0[i] = now()
                _pb_long[i] = False
            elif not _pb_long[i] and since(t0) >= LONG_MS:
                _pb_long[i] = True
                if not wake():
                    enc_button_action(sl, True)
        elif t0 is not None:
            _pb_t0[i] = None
            if not _pb_long[i] and not wake():
                enc_button_action(sl, False)


# ---------------- LEDs (v13.29) ----------------
# Ein Dienst fuer alle LEDs. Je UI-Durchlauf bekommt jede LED eine
# Wunschfarbe; gesendet wird nur bei Aenderung (jede LED kostet 1-2
# I2C-Zugriffe), waehrend der Wiedergabe hoechstens LED_SENDS_RUN.
#
# Navigation (Single), Vorrang von oben nach unten:
#   IM SCHONER AUS + Schoner     -> dunkel
#   PANIC halten (SPIELEN)       -> gelb nach rot
#   Kanalwechsel                 -> Kanalfarbe hell, CHFLASH_MS
#   Warnung                      -> blinkt
#   Schlag (Sequencer laeuft)    -> Blitz, Takt 1 weiss
#   Bearbeiten                   -> EDIT-Farbe statt FARBE
#   sonst                        -> FARBE
# Zusatz-Encoder: Farbe wie bisher (AUTO, fest, neu KANAL), dazu ZUSTAND
# (gedimmt = ohne Wirkung, AUF DRUCK vorgemerkt = blinkt) und DREH-BLITZ.

_led_sent = {}           # LED-Index -> zuletzt gesendete Farbe
_led_ch_prev = [None]
_led_ch_t = [0]          # Zeit des letzten Kanalwechsels
_led_test = [None]       # Startzeit des LED-TESTS
_led_page = [None, 0, {}]  # Seite, naechste Pruefung, Slot -> SEITE hat Wert
LED_SENDS_RUN = 3
LED_DIM = 0.18           # gedimmt = ohne Wirkung
LED_FLASH = 2.5          # Blitz-Faktor
LED_FLASH_MS = 150
LED_CHFLASH_MS = 600
LED_BEAT_TICKS = 12      # Schlag-Blitz: erstes Viertel des Schlags
LED_TEST_MS = 2400
LED_TEST_COL = (2, 5, 7, 9)   # ROT GRUEN BLAU WEISS


def _lsc(rgb, f=1.0):
    # Farbe mal Faktor mal HELLIGKEIT; was leuchten soll, bleibt sichtbar
    if rgb is None:
        return (0, 0, 0)
    f *= LED_HELL[S["led"]["hl"]]
    out = []
    for v in rgb:
        if v:
            v = int(v * f)
            v = 1 if v < 1 else (255 if v > 255 else v)
        out.append(v)
    return (out[0], out[1], out[2])


def led_beat():
    # 0 = kein Schlag, 1 = Schlag, 2 = Takt 1 (aus AMYs Sequencer-Zaehler)
    if not S["run"] or _origin is None:
        return 0
    t = _seq_ticks()
    if t is None:
        return 0
    r = t - _origin
    if r < 0 or r % TICKS_PER_BEAT >= LED_BEAT_TICKS:
        return 0
    return 2 if (r // TICKS_PER_BEAT) % 4 == 0 else 1


def led_warning():
    return (ain_clipping(0) or ain_clipping(1) or _load_warned or bool(_save_err))


def nav_editing():
    if not STACK:
        return False
    p = STACK[-1]
    return isinstance(p, EditPage) or bool(getattr(p, "edit", False))


def _nav_rgb(t):
    x = S["led"]
    if _saver and not x["sv"]:
        return (0, 0, 0)
    if _hold_progress and x["pn"] != 1:
        h = _hold_progress
        if x["pn"] == 0:
            return _lsc((40, int(30 * (1.0 - h)), 0), 1.0 + h)
        return _lsc(LED_RGB[x["pn"]], 0.5 + 1.5 * h)
    if x["cf"] and time.ticks_diff(t, _led_ch_t[0]) < LED_CHFLASH_MS:
        return _lsc(CH_RGB[S["cur"]], LED_FLASH)
    if x["wn"] != 1 and led_warning():
        if (t // 125) % 2:
            return (0, 0, 0)
        return _lsc(LED_RGB[2 if x["wn"] == 0 else x["wn"]], 1.5)
    base = CH_RGB[S["cur"]] if x["nav"] == 0 else LED_RGB[x["nav"]]
    if x["ed"] != 1 and nav_editing():
        base = LED_RGB[9 if x["ed"] == 0 else x["ed"]]
    if x["bt"] != 1:
        b = led_beat()
        if b:
            if x["bt"] == 0:
                if b == 2 or not any(base):
                    return _lsc(LED_RGB[9], 2.0)
                return _lsc(base, LED_FLASH)
            return _lsc(LED_RGB[x["bt"]], 2.0 if b == 2 else 1.2)
    return _lsc(base)


def _btn_state(a):
    # Funktion AUS: die LED zeigt den Zustand des Tasters
    if a == "START":
        on, c = S["run"], 5
    elif a.startswith("MUTE"):
        on, c = S["mute"][int(a[4:])], 2
    elif a == "M303":
        on, c = S["acid"]["mute"], 2
    elif a == "MDRM":
        on, c = S["drm"]["mute"], 2
    elif a == "AIN":
        on, c = S["ain"]["on"], 6
    elif a == "TAP":
        return _lsc(LED_RGB[9], LED_FLASH if led_beat() else LED_DIM)
    elif a == "ESET":
        return _lsc(LED_RGB[(9, 4, 8)[S["eset"]]])
    else:
        return None
    return _lsc(LED_RGB[c], 1.0 if on else LED_DIM)


def _led_page_scan(p, t):
    # Welche SEITE-Encoder haben auf der offenen Seite einen Wert?
    # Bei Seitenwechsel sofort, sonst alle 300 ms.
    if p is _led_page[0] and time.ticks_diff(t, _led_page[1]) < 0:
        return
    _led_page[0] = p
    _led_page[1] = time.ticks_add(t, 300)
    d = {}
    seen = {}
    get = p.enc_param
    if isinstance(p, ListPage):
        # ListPage: Zeilen nur einmal auswerten (enc_param filtert sonst je Wert)
        nums = [it for it in p.items() if it.kind == NUM]
        get = lambda k: nums[k] if k < len(nums) else None
    for sl in ENC_SLOT:
        if S["encf"][sl] != "SCREEN":
            continue
        k = enc_page_index(sl)
        if k not in seen:
            try:
                prm = get(k)
                vis = getattr(prm, "vis", None)
                seen[k] = prm is not None and (vis is None or bool(vis()))
            except Exception:
                seen[k] = False
        d[sl] = seen[k]
    _led_page[2] = d


def _slot_rgb(sl, t, jump):
    x = S["led"]
    if _saver and not x["sv"]:
        return (0, 0, 0)
    ex = S["encx"][sl]
    f = S["encf"][sl]
    fn = enc_func(f)
    li = ex["led"]
    if li == LED_KANAL:
        rgb = CH_RGB[enc_patch_ch(f) if fn == 2 else S["cur"]]
    elif li:
        rgb = LED_RGB[li]
    else:
        if fn == 0 and x["st"]:
            bs = _btn_state(S["encb"][sl])
            if bs is not None:
                return bs
        rgb = LED_RGB[enc_led_index(sl)]
    fac = 1.0
    if x["st"] and not jump:
        if fn == 1:
            if not _led_page[2].get(sl, True):
                fac = LED_DIM
        elif fn == 2:
            ch = enc_patch_ch(f)
            if sl in _enc_pend:
                if (t // 250) % 2:
                    fac = LED_DIM
            elif S["mute"][ch] or (S["pat"][ch] == -1 and not chrom_owns(ch)):
                fac = LED_DIM
        elif fn == 4:
            vis = getattr(REG.get(f), "vis", None)
            if vis is not None and not vis():
                fac = LED_DIM
    if x["fl"] and sl in _led_flash and time.ticks_diff(t, _led_flash[sl]) < LED_FLASH_MS:
        fac = LED_FLASH
    return _lsc(rgb, fac)


def led_test():
    _led_test[0] = now()
    toast("LED-TEST", "R G B W", LED_TEST_MS)


def service_leds(force=False):
    if enc is None:
        return
    try:
        n = enc.leds
    except Exception:
        return
    if not n:
        return
    t = now()
    want = []
    try:
        if S["cur"] != _led_ch_prev[0]:
            if _led_ch_prev[0] is not None:
                _led_ch_t[0] = t
            _led_ch_prev[0] = S["cur"]
        if _led_test[0] is not None and time.ticks_diff(t, _led_test[0]) >= LED_TEST_MS:
            _led_test[0] = None
        tst = None
        if _led_test[0] is not None:
            k = time.ticks_diff(t, _led_test[0]) * len(LED_TEST_COL) // LED_TEST_MS
            tst = _lsc(LED_RGB[LED_TEST_COL[k % len(LED_TEST_COL)]], 1.5)
        if NAV_LED is not None and NAV_LED < n:
            want.append((NAV_LED, tst or _nav_rgb(t)))
        p = STACK[-1] if STACK else None
        jump = getattr(p, "enc_jump", None) is not None
        if p is not None and S["led"]["st"] and tst is None:
            _led_page_scan(p, t)
        for i in range(len(ENC_SLOT)):
            li = ENC_LED[i] if i < len(ENC_LED) else None
            if li is None or li >= n:
                continue
            want.append((li, tst or _slot_rgb(ENC_SLOT[i], t, jump)))
    except Exception as e:
        print("LED", e)
        return
    budget = 0 if (force or not S["run"]) else LED_SENDS_RUN
    sent = 0
    for li, rgb in want:
        if _led_sent.get(li) == rgb:
            continue
        if budget and sent >= budget:
            break
        try:
            enc.led(li, *rgb)
        except Exception as e:
            print("LED", e)
            return
        _led_sent[li] = rgb
        sent += 1


def update_leds():
    # alle LEDs sofort neu berechnen und senden (Name seit v13.24)
    service_leds(True)



# ================================================================
# BILDSCHIRM: Takt, Schoner
# ================================================================
#
# Eingaben zeichnen sofort (max. alle FRAME_MS). Reine Live-
# Anzeigen (Abspielpunkt, CV-Monitor) hoechstens alle LIVE_MS -
# ein Vollbild kostet ~8 KB I2C, das darf den Ton nicht bremsen.

FRAME_MS = 45
LIVE_MS = 240
_last_frame = 0
_live = False


_flush_pending = False


def render(force=False):
    # Zeichnen und Senden getrennt (v12.11): gezeichnet wird bei
    # Aenderung, gesendet werden nur geaenderte Baender - waehrend der
    # Wiedergabe hoechstens FLUSH_BANDS_RUN pro Durchlauf, der Rest im
    # naechsten. Live-Anzeigen warten, bis das letzte Bild draussen ist.
    global _dirty, _last_frame, _toast, _live, _flush_pending
    if _saver:
        return
    if _toast is not None and time.ticks_diff(now(), _toast[2]) >= 0:
        _toast = None
        _dirty = True
    p = top()
    if p.custom:
        return
    el = since(_last_frame)
    draw = force
    if not draw:
        if _dirty:
            draw = el >= FRAME_MS
        elif _live and not _flush_pending:
            draw = el >= LIVE_MS
    if draw:
        _dirty = False
        _live = False
        _last_frame = now()
        t0 = time.ticks_us()
        try:
            fb.fill(0)
            p.draw()
            if p.status:
                draw_status()
            if _acid_mod:
                draw_acid_joy()
            if _toast is not None:
                draw_toast()
        except Exception as e:
            print("DRAW", e)
        meas("draw", t0)
        _flush_pending = True
    if _flush_pending:
        t0 = time.ticks_us()
        budget = 0 if (force or not S["run"]) else FLUSH_BANDS_RUN
        _flush_pending = not flush_display(budget)
        meas("flush", t0)


# ---------------- Bildschirmschoner (v13.30) ----------------
# Acht Bilder laufen zufaellig nacheinander, nach LEERLAUF uebernimmt ein
# langsam pulsierender Delfin-Umriss. Jedes Bild zeichnet das ganze Bild
# neu; gesendet werden nur geaenderte Baender (flush_display). Waehrend
# der Wiedergabe hoechstens ein Bild alle SV_RUN_MS mit dem Band-Budget,
# damit der Takt Vorrang hat. Ganzzahl-Rechnung, damit in MicroPython
# moeglichst wenig Speicher pro Bild angelegt wird.

SV_TERM = 3
SV_IDLE = 8
SV_TEXT = 9
SV_WZ = (1, 2, 5, 10)            # WECHSEL nach Minuten
SV_LZ = (30, 60, 240)            # LEERLAUF nach Minuten
SV_KONTRAST = (20, 60, 120)
SV_RUN_MS = 400                  # Bildabstand waehrend der Wiedergabe
SV_IDLE_MS = 200                 # Bildabstand im Stillstand
SV_BANDS = 12                    # SPEKTRUM-Baender
SV_BANDS_STOP = 4                # Baender je Durchlauf bei gestopptem Sequencer

_SIN = [int(127 * math.sin(6.2832 * i / 64)) for i in range(64)]


def _sn(i):
    return _SIN[i & 63]


def _cs(i):
    return _SIN[(i + 16) & 63]


# Delfin als Pixelbild (nach rechts, "#" = an), gezeichnet in Spalten-
# Stuecken - so laesst er sich skalieren, spiegeln und neigen.
_SV_DOL = (
    ".............##.................",
    "..............###...............",
    "..............####..............",
    ".............#########..........",
    "#........###############........",
    "##....####################......",
    ".##########################.....",
    ".###########################....",
    ".#########################.###..",
    "##......#######################.",
    "............###########.........",
    "....................##..........",
    "...................##...........",
    "..................##............",
)


def _sv_prep():
    h = len(_SV_DOL)
    w = max([len(r) for r in _SV_DOL])

    def on(x, y):
        return 0 <= y < h and 0 <= x < len(_SV_DOL[y]) and _SV_DOL[y][x] == "#"

    cols = []
    for x in range(w):
        y = 0
        while y < h:
            if on(x, y):
                y0 = y
                while on(x, y):
                    y += 1
                cols.append((x, y0, y - y0))
            else:
                y += 1
    out = []
    for y in range(h):
        for x in range(w):
            if on(x, y) and not (on(x - 1, y) and on(x + 1, y) and on(x, y - 1) and on(x, y + 1)):
                out.append((x, y))
    return w, h, tuple(cols), tuple(out)


SV_DW, SV_DH, _SV_COLS, _SV_OUT = _sv_prep()
# ASCII-Delfin fuer TERMINAL: je 2x2 Pixel ein Zeichen nach Dichte


def _sv_ascii():
    out = []
    for y in range(0, SV_DH, 2):
        ln = ""
        for x in range(0, SV_DW, 2):
            n = 0
            for yy in (y, y + 1):
                r = _SV_DOL[yy] if yy < SV_DH else ""
                n += (r[x:x + 2]).count("#")
            ln += " .:%#"[n]
        out.append(ln.rstrip())
    return tuple(out)


_SV_ASC = _sv_ascii()


def sv_dol(x, y, s=2, c=W, k=0, flip=False, mode=0):
    # k = Neigung in 1/16 Pixel je Spalte (+ = Nase runter);
    # mode 0 voll, 1 Umriss, 2 Rasterpunkte
    w1 = SV_DW - 1
    mid = SV_DW // 2
    if mode == 1:
        for px, py in _SV_OUT:
            xx = w1 - px if flip else px
            fb.fill_rect(x + xx * s, y + py * s + ((k * (px - mid) * s) >> 4), s, s, c)
        return
    d = s - 1 if s > 1 else 1
    for px, py, n in _SV_COLS:
        xx = w1 - px if flip else px
        yy = y + py * s + ((k * (px - mid) * s) >> 4)
        if mode == 2:
            for j in range(n):
                fb.fill_rect(x + xx * s, yy + j * s, d, d, c)
        else:
            fb.fill_rect(x + xx * s, yy, s, n * s, c)


def sv_clock(t):
    # (Position in 1/16 Schlag, laeuft). Steht der Sequencer: ein Schlag
    # alle 2 s, damit sich die Bilder trotzdem ruhig bewegen.
    if S["run"] and _origin is not None:
        tk = _seq_ticks()
        if tk is not None and tk >= _origin:
            return (tk - _origin) * 16 // TICKS_PER_BEAT, True
    return t * 16 // 2000, False


_sv_pl = [None, None]    # letzter Schlag, letzter Drum-Step


def sv_pulse(b16, run):
    # True, wenn seit dem letzten Bild eine Bassdrum (Zeile 1 der Drum-Spur)
    # kam - ohne Bassdrum im Pattern: jeder Schlag.
    beat = b16 >> 4
    d = S["drm"]
    rt = RTS[DRUM]
    if run and not d["mute"] and rt.step >= 0:
        n0 = d["lens"][0]
        has = False
        for i in range(n0):
            if drum_cell(0, i):
                has = True
                break
        if has:
            st = rt.step
            last = _sv_pl[1]
            _sv_pl[1] = st
            _sv_pl[0] = beat
            if last is None or st == last:
                return False
            for i in range(1, (st - last) % DRUM_BAR + 1):
                if drum_cell(0, ((last + i) % DRUM_BAR) % n0):
                    return True
            return False
    hit = _sv_pl[0] is not None and beat != _sv_pl[0]
    _sv_pl[0] = beat
    return hit


_sv = {"cur": SV_TEXT, "t0": 0, "sw": 0, "next": 0, "flush": False, "idle": False}
_svd = {}                # Zustand des laufenden Bildes
_sv_mq = []              # MIDI-Bytes fuer TERMINAL
_sv_clk = [0]
_sv_gc = []              # Goertzel-Koeffizienten (x4096) fuer SPEKTRUM


def sv_midi(m):
    # aus midi_dispatch, nur solange TERMINAL laeuft; Clock nur jede 24.
    if not len(m):
        return
    if m[0] == 0xF8:
        _sv_clk[0] += 1
        if _sv_clk[0] % 24:
            return
    if len(_sv_mq) < 16:
        _sv_mq.append(" ".join(["%02X" % v for v in m[:3]]))


def _sv_rise(d, t):
    lt = d.get("lt", t)
    d["lt"] = t
    dt = time.ticks_diff(t, lt)
    return 500 if dt > 500 else dt


def sv_jump(el):
    b16, run = sv_clock(now())
    d = _svd
    if run:
        bar = b16 >> 6
        p = b16 & 63
        if d.get("bar") != bar:
            d["bar"] = bar
            d["x0"] = rnd(24)
            d["fl"] = rnd(2)
        p = p * 2 if p < 32 else -1         # springt in den ersten 2 Schlaegen
    else:
        cyc = el // 6000
        if d.get("bar") != cyc:
            d["bar"] = cyc
            d["x0"] = rnd(24)
            d["fl"] = rnd(2)
        p = (el % 6000) * 64 // 2500
        if p >= 64:
            p = -1
    if p >= 0:
        w = SV_DW * 2
        x = d["x0"] + p * 5 // 8
        if d["fl"]:
            x = 128 - w - x
        y = 92 - ((_sn(p >> 1) * 64) >> 7)
        sv_dol(x, y, 2, 13, (p - 32) >> 2, bool(d["fl"]))
        if p < 8 or p > 54:
            sx = x + (w - 8 if (p < 8) == bool(d["fl"]) else 0)
            for _ in range(4):
                fb.fill_rect(sx + rnd(14), 98 - rnd(10), 2, 2, 6 + rnd(6))
    ph = el // 60
    for i, yb, am, c in ((0, 108, 4, 8), (1, 116, 3, 5), (2, 123, 2, 3)):
        for xx in range(0, 128, 2):
            fb.fill_rect(xx, yb + ((_sn(xx + ph * (i + 1) + i * 20) * am) >> 7), 2, 1, c)


def sv_sonar(el):
    b16, run = sv_clock(now())
    t = now()
    d = _svd
    cx = cy = 64
    for r in (20, 40, 60):
        for i in range(0, 64, 2):
            fb.pixel(cx + ((_cs(i) * r) >> 7), cy + ((_sn(i) * r) >> 7), 2)
    fb.hline(4, cy, 120, 1)
    fb.vline(cx, 4, 120, 1)
    a = (b16 if run else el * 64 // 4000) & 63     # laeuft: eine Umdrehung pro Takt
    for j, c in ((3, 2), (2, 3), (1, 5), (0, 11)):
        aa = (a - j) & 63
        LN(cx, cy, cx + ((_cs(aa) * 60) >> 7), cy + ((_sn(aa) * 60) >> 7), c)
    bl = d.get("bl")
    if bl is None:
        bl = d["bl"] = [[rnd(64), 18 + rnd(38), time.ticks_add(t, -9999)] for _ in range(3)]
        d["a"] = a
    la = d["a"]
    d["a"] = a
    sweep = (a - la) & 63
    for b in bl:
        if 0 < ((b[0] - la) & 63) <= sweep:
            b[2] = t                         # vom Strahl getroffen
        age = time.ticks_diff(t, b[2])
        c = 13 - age // 250
        if c > 0:
            sv_dol(cx + ((_cs(b[0]) * b[1]) >> 7) - SV_DW // 2,
                   cy + ((_sn(b[0]) * b[1]) >> 7) - SV_DH // 2, 1, c, 0, 16 < b[0] < 48)
        elif age > 8000:
            b[0] = rnd(64)
            b[1] = 18 + rnd(38)
            b[2] = time.ticks_add(t, -4000)
    pg = d.get("pg") or []
    if sv_pulse(b16, run):
        pg.append(t)
    keep = []
    for p0 in pg:
        age = time.ticks_diff(t, p0)
        if age < 900:
            keep.append(p0)
            r = age * 64 // 900
            c = 9 - age // 110
            for i in range(64):
                fb.pixel(cx + ((_cs(i) * r) >> 7), cy + ((_sn(i) * r) >> 7), c)
    d["pg"] = keep


def sv_tunnel(el):
    b16, run = sv_clock(now())
    t = now()
    d = _svd
    dt = _sv_rise(d, t)
    bo = d.get("bo", 0)
    if sv_pulse(b16, run):
        bo = 40                              # Kick: kurzer Schub
    d["bo"] = bo * 3 // 4
    sp = (S["tempo"] if run else 30) * (10 + bo) // 10
    ph = (d.get("ph", 0) + dt * sp // 60) % 1000
    d["ph"] = ph
    cx = 64 + ((_sn(el // 40) * 8) >> 7)
    cy = 64 + ((_cs(el // 55) * 6) >> 7)
    for k in ((0, 0), (127, 0), (0, 127), (127, 127)):
        LN(cx, cy, k[0], k[1], 1)
    for i in range(6):
        q = (i * 1000 + ph) // 60           # Tiefe 0..100
        s = 4 + 124 * q * q // 10000
        FR(cx - s // 2, cy - s // 2, s, s, 1 + q * 11 // 100)
    sv_dol(cx - SV_DW, cy - SV_DH + ((_sn(el // 30) * 4) >> 7), 2, 14, (_sn(el // 50) * 4) >> 7)


def sv_term(el):
    t = now()
    run = S["run"]
    d = _svd
    ln = d.get("ln")
    if ln is None:
        ln = d["ln"] = []
    dt = _sv_rise(d, t)
    v = dt * (40 if run else 15) // 1000 or 1
    for e in ln:
        e[1] += v
    while ln and ln[0][1] > 127:
        ln.pop(0)
    if not ln or ln[-1][1] >= 11:
        s = None
        if _sv_mq:
            s, c = _sv_mq.pop(0), 10
        elif rnd(3) == 0:
            s, c = "%02X %02X" % (rnd(256), rnd(128)), 3
        if s:
            ln.append([4 + rnd(2) * 64, 0, s, c])
    for x, y, s, c in ln:
        T(s, x, y, max(1, c - y // 32))
    R(0, 36, 128, 8 * len(_SV_ASC) + 4, 0)
    for i in range(len(_SV_ASC)):
        T(_SV_ASC[i], 0, 38 + 8 * i, 12)
    R(0, 96, 128, 12, 0)
    T("> K%d %dBPM%s" % (S["cur"], S["tempo"], "_" if (el // 500) & 1 else ""), 4, 98, 10)


def sv_flyer(el):
    b16, run = sv_clock(now())
    d = _svd
    lay = ((b16 >> 8) if run else el // 10000) % 3      # alle 4 Takte / 10 s
    bar = b16 >> 6
    strobe = run and d.get("bar") is not None and bar != d["bar"]
    d["bar"] = bar
    name = S["sv"]["fly"] or "DOLPHIN"
    sc = 2 if len(name) <= 7 else 1
    nw = 8 * sc * len(name)
    if lay == 0:
        sv_dol(16, 4, 3, 9, -2, False, 2)
        ty, sy = 52, 78
        for i in range(4):
            for j in range(4 - i):
                fb.fill_rect(104 + j * 6, 4 + i * 6, 2, 2, 4)
    elif lay == 1:
        sv_dol(16, 46, 3, 9, 2, True, 2)
        ty, sy = 6, 30
    else:
        sv_dol(90, 8, 1, 11, 0, False)
        sv_dol(6, 76, 1, 11, 0, True)
        ty, sy = 36, 62
    if strobe:
        R(4, ty, 120, 20, 0)
        FR(4, ty, 120, 20, 15)
        BIG(name, 64 - nw // 2, ty + (2 if sc == 2 else 6), sc, 15)
    else:
        R(4, ty, 120, 20, 12)
        BIG(name, 64 - nw // 2, ty + (2 if sc == 2 else 6), sc, 0)
    TC("SOUNDSYSTEM", 64, sy, 7)
    HL(4, 100, 120, 4)
    T("%d BPM" % S["tempo"], 4, 108, 8)
    TR("K%d" % S["cur"], 124, 108, 8)


def sv_acid(el):
    a = S["acid"]
    n = a["steps"]
    if not S["run"] or a["mute"] or n < 1:
        sv_jump(el)                          # 303 steht: SPRUNG
        return
    b16, run = sv_clock(now())
    pat = a["pats"][a["pat"]]
    ys = [None if st[0] < 0 else 100 - (st[0] + 12 * st[1] + 12) * 2 for st in pat[:n]]
    px = b16 * 10 // 4 - 36                  # 10 Pixel je Step, Delfin bei x=36
    i0 = px // 10
    for k in range(-1, 15):
        i = i0 + k
        x = i * 10 - px
        y = ys[i % n]
        if y is None:
            continue
        st = pat[i % n]
        ny = ys[(i + 1) % n]
        if st[3] and ny is not None:
            fb.hline(x, y, 5, 9)
            LN(x + 4, y, x + 10, ny, 9)        # Slide = Rampe
        else:
            fb.hline(x, y, 10, 9)
            if ny is not None and ny != y:
                fb.vline(x + 10, min(y, ny), abs(ny - y) + 1, 5)
        if st[2]:
            R(x + 3, y - 4, 4, 3, 15)            # Accent = Wellenberg
    i = (px + 36) // 10
    y = ys[i % n]
    k = 0
    if y is None:
        y = 70
        for j in range(1, n):
            if ys[(i - j) % n] is not None:
                y = ys[(i - j) % n] - 8
                break
    else:
        ny = ys[(i + 1) % n]
        if pat[i % n][3] and ny is not None:
            k = max(-8, min(8, (ny - y) // 2))
    sv_dol(36 - SV_DW // 2, y - SV_DH - 1, 1, 14, k)


def _sv_coef():
    out = []
    for i in range(SV_BANDS):
        f = 150.0 * (2 ** (i * 6.3 / (SV_BANDS - 1)))     # 150 Hz bis ca. 12 kHz
        out.append(int(2 * math.cos(6.2832 * f / 44100) * 4096))
    return out


def sv_spec(el):
    b16, run = sv_clock(now())
    d = _svd
    mags = None
    gb = getattr(amy, "get_output_buffer", None)
    if gb is not None:
        try:
            buf = gb()
            if buf:
                smp = array("h", bytes(buf))
                if not _sv_gc:
                    _sv_gc.extend(_sv_coef())
                n2 = 2 * min(len(smp) // 2, 96)
                mags = []
                for c in _sv_gc:
                    s1 = s2 = 0
                    for j in range(0, n2, 2):         # Goertzel, linker Kanal
                        s0 = (smp[j] >> 6) + ((c * s1) >> 12) - s2
                        s2 = s1
                        s1 = s0
                    mags.append(abs(s1) + abs(s2))
        except Exception:
            mags = None
    if not mags or not max(mags):
        # ohne Ausgangspuffer: Balken nach Schlag und Zufall
        ph = b16 & 15
        mags = [(16 - ph) * (40 + rnd(60)) * (SV_BANDS - i) // SV_BANDS for i in range(SV_BANDS)]
    mx = max(d.get("mx", 1) * 9 // 10, max(mags), 1)
    d["mx"] = mx
    pk = d.get("pk") or [0] * SV_BANDS
    best = 0
    bh = -1
    for i in range(SV_BANDS):
        h = mags[i] * 90 // mx
        pk[i] = max(h, pk[i] - 4)
        x = 4 + i * 10
        if h:
            R(x, 112 - h, 9, h, 4 + h // 18)
        HL(x, 110 - pk[i], 9, 9)
        if h > bh:
            bh = h
            best = i
    d["pk"] = pk
    HL(0, 113, 128, 3)
    xb = 4 + best * 10
    for j in range(12):                      # Flosse auf dem lautesten Balken
        HL(xb + 1, 112 - bh - 12 + j, j * 2 // 3 + 1, 14)


def sv_ware(el):
    b16, run = sv_clock(now())
    bar = b16 >> 6
    for k, sp, yy, s, c, fl in ((0, 25, 70, 2, 3, False), (1, 40, 34, 1, 2, True)):
        w = SV_DW * s
        x = (el // sp) % (128 + w) - w
        if fl:
            x = 128 - x - w
        sv_dol(x, yy + ((_sn(el // 40 + k * 20) * 3) >> 7), s, c, 0, fl)
    ox = (20, 64, 108)[bar % 3]
    sw = (_sn(el // 25) * 30) >> 7
    dr = 1 if bar & 1 else -1                # Richtung wechselt jeden Takt
    for i in range(7):
        LN(ox, 0, ox + dr * ((i - 3) * 28 + sw), 127, (6, 9, 5, 11, 5, 9, 6)[i])
    for _ in range(12):
        fb.pixel(rnd(128), 20 + rnd(100), 1 + rnd(2))


def sv_idle(el):
    d = _svd
    p = el // 60000                          # jede Minute ein neuer Platz
    if d.get("p") != p:
        d["p"] = p
        d["x"] = rnd(128 - 2 * SV_DW)
        d["y"] = 8 + rnd(112 - 2 * SV_DH)
        d["fl"] = rnd(2)
    c = 1 + (((_sn(el // 125) + 127) * 5) >> 8)    # 1..5, Periode 8 s
    sv_dol(d["x"], d["y"], 2, c, 0, bool(d["fl"]), 1)


def sv_text(el):
    p = (el // 5000 * 37) % 90
    T("DOLPHIN", 8 + p // 2, 20 + p, GH + 1)
    if S["run"]:
        T("%d BPM" % S["tempo"], 8 + p // 2, 32 + p, GH)


SV_DRAW = (sv_jump, sv_sonar, sv_tunnel, sv_term, sv_flyer, sv_acid, sv_spec, sv_ware,
           sv_idle, sv_text)


def sv_pick(t):
    x = S["sv"]
    b = x["bild"]
    if b == 0:
        pool = [i for i in range(len(SV_NAMES)) if (x["pool"] >> i) & 1]
        if len(pool) > 1 and _sv["cur"] in pool:
            pool.remove(_sv["cur"])
        c = pool[rnd(len(pool))] if pool else SV_TEXT
    else:
        c = b - 1 if b <= len(SV_NAMES) else SV_TEXT
    _sv["cur"] = c
    _sv["sw"] = t
    _sv["next"] = t
    _svd.clear()
    del _sv_mq[:]


def sv_start():
    global _saver
    _saver = True
    t = now()
    _sv["t0"] = t
    _sv["idle"] = False
    _sv["flush"] = False
    _sv["cur"] = -1
    _sv_pl[0] = _sv_pl[1] = None
    sv_pick(t)
    if HAS_CONTRAST:
        display_contrast(SV_KONTRAST[S["sv"]["hl"]])


def sv_service():
    t = now()
    x = S["sv"]
    budget = FLUSH_BANDS_RUN if S["run"] else SV_BANDS_STOP
    if _sv["flush"]:
        _sv["flush"] = not flush_display(budget)
        return
    if time.ticks_diff(t, _sv["next"]) < 0:
        return
    if not _sv["idle"] and time.ticks_diff(t, _sv["t0"]) >= SV_LZ[x["lz"]] * 60000:
        _sv["idle"] = True
        sv_pick(t)
        _sv["cur"] = SV_IDLE
        if HAS_CONTRAST:
            display_contrast(SV_KONTRAST[0])
    elif (not _sv["idle"] and x["bild"] == 0
          and time.ticks_diff(t, _sv["sw"]) >= SV_WZ[x["wz"]] * 60000):
        sv_pick(t)
    c = _sv["cur"]
    fast = _fast_ok and S["dfast"]
    if c == SV_TEXT:
        iv = 5000
    elif c == SV_IDLE:
        iv = 400
    elif S["run"]:
        iv = SV_RUN_MS if fast else 1000
    else:
        iv = SV_IDLE_MS if fast else 400
    _sv["next"] = time.ticks_add(t, iv)
    t0 = time.ticks_us()
    try:
        fb.fill(0)
        SV_DRAW[c](time.ticks_diff(t, _sv["sw"]))
    except Exception as e:
        print("SCHONER", c, e)
    meas("draw", t0)
    _sv["flush"] = not flush_display(budget)


def service_saver():
    if _saver:
        sv_service()
        return
    m = S["dim"]
    if not m or top().custom or _btn_down:
        return
    if since(_last_input) > m * 60000:
        sv_start()


# ================================================================
# LAUFENDE DIENSTE
# ================================================================

RENDER_LOAD_WARN = 0.85
RENDER_LOAD_CLEAR = 0.75
_load_next = 0
_load_warned = False
_morph_next = 0
_m5_prev = None
_gc_next = 0


def service_load():
    global _load_next, _load_warned, cpu_load
    if since(_load_next) < 0:
        return
    _load_next = time.ticks_add(now(), 1000)
    try:
        ld = amy.render_load()
    except Exception:
        return
    if abs(ld - cpu_load) > 0.06:
        mark_dirty()
    cpu_load = ld
    if ld >= RENDER_LOAD_WARN and not _load_warned:
        _load_warned = True
        toast("HOHE CPU-LAST", "%d%%" % int(ld * 100), 1500)
    elif ld < RENDER_LOAD_CLEAR:
        _load_warned = False


def service_misc():
    global _learned, _morph_next, _m5_prev
    if _learned is not None:
        ch, cc, t = _learned
        _learned = None
        bind_cc(ch, cc, t)
        toast("CC%d > %s" % (cc, CC_TARGETS[t][0]), "KANAL %d" % ch)
    if _morph_pending and since(_morph_next) >= 0:
        _morph_next = time.ticks_add(now(), 60)
        morph_apply()
    cvmod_service()
    cvfold_service()
    vco_service()
    ain_service()
    smp_service()
    if S["m5"] and enc is not None:
        try:
            st = bool(enc.switch())
        except Exception:
            return
        if _m5_prev is None:
            _m5_prev = st
        elif st != _m5_prev:
            _m5_prev = st
            seq_toggle()
            mark_dirty()


GC_IDLE_MS = 4000
GC_RUN_MS = 20000        # waehrend der Wiedergabe seltener (v12.11)


def service_gc():
    # Speicherbereinigung nur in Ruhephasen, damit sie nicht
    # mitten in einen Sequencer-Step faellt
    global _gc_next
    if since(_gc_next) >= 0 and since(_last_input) > 700:
        _gc_next = time.ticks_add(now(), GC_RUN_MS if S["run"] else GC_IDLE_MS)
        gc.collect()


# ================================================================
# TAKT: UI-NOTLAUF + AMY-TRANSPORT (sequencer_run)
# ================================================================
#
# v12.11: Ab Werk (UI-TAKT = TIMER) ruft ein machine.Timer alle 40 ms
# ui_service() - unabhaengig von Tempo und Transport; loop() macht dann
# nichts mehr fuer die Bedienung. Bei UI-TAKT = LOOP gilt das Verhalten
# von v12.10: loop(tick) bedient, der Timer springt nur als NOTLAUF ein,
# wenn loop() steht (sequencer_run=0 oder MIDI FOLGEN ohne Clock).

UI_TIMER_MS = 40
NOTLAUF_PERIOD_MS = 100
NOTLAUF_MIN_MS = 300
NOTLAUF_TIMER_IDS = (3, 2, 1, 0)

_ui_busy = False
_last_loop_ms = None
_notlauf_timer = None
_notlauf_active = False
_notlauf_count = 0
_transport_stopped = False


def _notlauf_threshold():
    normal = 7500 // max(20, int(S["tempo"]))
    return max(NOTLAUF_MIN_MS, 2 * normal + NOTLAUF_PERIOD_MS)


def timer_wanted():
    return bool(S["uit"] or S["notlauf"])


def ui_timer_mode():
    return bool(S["uit"]) and _notlauf_timer is not None


def _notlauf_cb(t):
    global _notlauf_active, _notlauf_count
    if _ui_busy or not STACK:
        return
    if S["uit"]:
        try:
            ui_service()
        except Exception as e:
            print("UI TIMER", e)
        return
    if not S["notlauf"]:
        return
    if not _transport_stopped:
        if _last_loop_ms is not None and since(_last_loop_ms) < _notlauf_threshold():
            return
    try:
        if not _notlauf_active:
            _notlauf_active = True
            _notlauf_count += 1
        ui_service()
    except Exception as e:
        print("NOTLAUF", e)


def loop_heartbeat():
    global _last_loop_ms, _notlauf_active
    _last_loop_ms = now()
    _notlauf_active = False


def notlauf_start():
    global _notlauf_timer, _last_loop_ms
    if _notlauf_timer is not None:
        return True
    try:
        import machine
    except Exception:
        return False
    _last_loop_ms = now()
    for tid in NOTLAUF_TIMER_IDS:
        try:
            t = machine.Timer(tid)
            t.init(period=UI_TIMER_MS, mode=machine.Timer.PERIODIC, callback=_notlauf_cb)
        except Exception as e:
            print("NOTLAUF TIMER", tid, e)
            continue
        _notlauf_timer = t
        return True
    return False


def notlauf_stop():
    global _notlauf_timer, _notlauf_active
    if _notlauf_timer is not None:
        try:
            _notlauf_timer.deinit()
        except Exception:
            pass
    _notlauf_timer = None
    _notlauf_active = False


def transport_effective():
    # Transport AMY nur, wenn die Bedienung auch ohne loop() weiterlaeuft
    return (S["transport"] == 1 and timer_wanted()
            and _notlauf_timer is not None and S["clock"] != 2)


def _send_seq_run(on):
    global _transport_stopped
    try:
        amy.send(sequencer_run=(1 if on else 0))
        _transport_stopped = not on
    except Exception as e:
        print("SEQ RUN", e)


def apply_transport():
    if transport_effective():
        if S["run"] and _transport_stopped:
            _send_seq_run(True)
        elif not S["run"] and not _transport_stopped:
            _send_seq_run(False)
    elif _transport_stopped:
        _send_seq_run(True)


def transport_hook(start):
    if not transport_effective():
        return False
    _send_seq_run(start)
    return True


# ================================================================
# HAUPTSCHLEIFE
# ================================================================

def ui_service():
    global _ui_busy, _joy, _live
    if _ui_busy:
        return False
    _ui_busy = True
    _ui_t0 = time.ticks_us()
    try:
        _joy = joystick_read() if joystick_available else None
        try:
            poll_input()
        except Exception as e:
            print("INPUT", e)
        try:
            read_param_encoders()
        except Exception as e:
            print("ENC", e)
        try:
            read_param_buttons()
        except Exception as e:
            print("TASTER", e)
        flush_configure()
        try:
            service_eurorack()
        except Exception as e:
            print("EUR", e)
        try:
            service_grid_mod()
        except Exception as e:
            print("GRID", e)
        try:
            service_acid_joy()
        except Exception as e:
            print("303 JOY", e)
        service_audition()
        service_pan()
        try:
            if top().tick():
                _live = True
        except Exception as e:
            print("TICK", e)
        try:
            service_misc()
        except Exception as e:
            print("MISC", e)
        service_load()
        service_save()
        service_saver()
        try:
            service_leds()
        except Exception as e:
            print("LED", e)
        service_gc()
        render()
    finally:
        _ui_busy = False
        meas("ui", _ui_t0)
    return True


def loop(tick):
    # Sequencer: im Feinraster ueber _seq_cb, sonst hier (jede 32tel).
    # Bedienung: im TIMER-Modus ueber den Timer, sonst hier.
    loop_heartbeat()
    if _seq_slot is None:
        _seq_cb(tick)
    elif _defer:
        t = amy_tick(tick)
        if t - _last_tick > 2 * SUB_TICKS:
            run_deferred(t)
    if not ui_timer_mode():
        try:
            ui_service()
        except Exception as e:
            print("UI", e)


# ================================================================
# START
# ================================================================

_state_src = load_state()
print("ZUSTAND:", _state_src)
scenes_load()
apply_midi_type()
apply_failsafe()
apply_all_sound()
try:
    apply_eurorack_mode()
except Exception as e:
    print("EUR INIT", e)
register_midi()
try:
    apply_tempo()
    apply_clock()
except Exception as e:
    print("SEQ INIT", e)
acid_setup()
try:
    pad_synths_init()
    smp_load_all()           # laedt im Hintergrund (ui_service)
except Exception as e:
    print("SAMPLER INIT", e)
try:
    cvmod_service(True)
except Exception as e:
    print("CVMOD INIT", e)
try:
    vco_init()               # v13.21: nach den Pads (Synth-Nummer)
except Exception as e:
    print("VCO INIT", e)
try:
    ain_init()               # v13.22: nach dem VCO (Synth-Nummern)
except Exception as e:
    print("AUDIO IN INIT", e)
if S["run"]:
    S["run"] = 0
    try:
        seq_start()
    except Exception as e:
        print("SEQ AUTOSTART", e)
update_leds()
apply_bright()
resync_param_encoders()
try:
    _last_nav = enc.read(NAV_ENCODER) if enc is not None else 0
except Exception:
    _last_nav = 0
_last_input = now()

# Boot-Zwischenwerte freigeben, RAM und Bootzeit fuer SETUP > INFO
for _n in ("_i", "_p", "_t", "_a", "_s", "_k", "_d", "_boff", "_nav_found", "_blocks"):
    try:
        del globals()[_n]
    except Exception:
        pass
gc.collect()
try:
    _ram_boot = gc.mem_free()
except Exception:
    _ram_boot = 0
_boot_dur_ms = since(_boot_ms)

try:
    _rest = SPLASH_MIN_MS - since(_boot_ms)
    if _rest > 0:
        time.sleep_ms(_rest)
except Exception:
    pass

STACK.append(HomePage())
if _state_src == "v11":
    toast("V11 IMPORT", "EINSTELLUNGEN", 2500)
elif _state_src == "backup":
    toast("ZUSTAND", "UEBERNOMMEN", 2500)
elif _state_src == "neu":
    toast("KEIN ZUSTAND", STATE_FILE[-24:], 2500)
elif BASE != "/sd/":
    # Hinweis beim Start: es wird intern gespeichert
    toast("SPEICHER INTERN", "SETUP>SD NEU", 2500)
mark_dirty()
render(force=True)

try:
    seq_cb_start()
except Exception as e:
    print("SEQ CB INIT", e)
try:
    if timer_wanted():
        notlauf_start()
    apply_transport()
except Exception as e:
    print("TAKT INIT", e)

print("================================")
print("DOLPHIN SELECTOR 3 v" + VERSION)
print("Encoder:", encoder_count, "Zusatz:", len(PARAM_ENCODERS))
print("Speicher:", STATE_FILE)
print("Seq:", "FEIN" if _seq_slot is not None else "LOOP",
      "VORAUS %dms" % S["vlf"] if S["sqm"] else "DIREKT",
      "UI:", "TIMER" if ui_timer_mode() else "LOOP",
      "Display:", "BAENDER" if _fast_ok else "VOLL",
      "RAM:", _ram_boot, "Boot ms:", _boot_dur_ms)
print("================================")

# Do not edit. Set automatically by the knobs on AMYboard Online.
_auto_generated_knobs = """

"""
