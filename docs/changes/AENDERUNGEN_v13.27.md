# Dolphin Selector 3 – Änderungen v13.27

Stand 27.10.2026 · Basis: v13.26

Anlass: Beim Hardware-Test am 26.10.2026 knackte es leicht beim Wechsel der VCO-WELLE und beim Umschalten des Filtertyps unter AUDIO IN. Im VCO-Modus FREI zitterte die Tonhöhe um etwa ±8 ct, weil der CV-Eingang selbst leicht schwankt.

## Weiches Umschalten

- **VCO › WELLE:** Läuft der VCO, wird er beim Wechsel zuerst über die Hüllkurve ausgeblendet (60 ms Release). Nach ca. 65 ms wechselt die Welle, dann blendet er in 5 ms wieder ein.
- **AUDIO IN › FILTER und DISTORTION:** Beim Wechsel des Typs gilt dasselbe für beide Seiten (L/R), die gerade klingen. Cutoff, Reso, Drive und Mix ändern sich weiter sofort, denn sie knacken nicht.
- Dreht man schnell durch die Liste, wird nur einmal ausgeblendet. Umgeschaltet wird erst 65 ms nach der letzten Änderung, und zwar auf den zuletzt gewählten Wert.
- Wird der VCO oder AUDIO IN während des Ausblendens ausgeschaltet, bleibt er aus.

## VCO › GLAETTUNG (nur TONHOEHE FREI)

- **AUS** (Werk): wie bisher. AMY liest den Eingang direkt, folgt ohne Verzögerung und zittert ein wenig.
- **LEICHT / STARK:** Python liest den Eingang bei jedem Durchlauf der Bedienschleife (ca. 30 ms) und glättet ihn mit einem gleitenden Mittelwert.
  - Zeitkonstante ca. 60 ms (LEICHT) bzw. 200 ms (STARK).
  - Neu gesendet wird nur, wenn sich die Tonhöhe um mehr als 0,01 Halbton ändert.
  - Die Eingangs-Kalibrierung und V/OKT wirken wie gewohnt.
- FM und PWM über MOD IN laufen weiter in AMY.
- Für schnelle Sequenzen AUS oder LEICHT, für gehaltene Töne und Drones STARK. Mit STARK gleiten Tonsprünge hörbar, ähnlich wie ein kurzes Portamento.
- Der Wert wird mit dem Zustand gespeichert. Ein alter Zustand ohne den Wert lädt mit AUS.

## Tests (Simulation)

- Neue Tests für Ausblenden, Verzögerung, einmaliges Ausblenden beim schnellen Drehen, Stopp während des Ausblendens, Glättung (Zeitkonstanten, Schwelle, Anzeige, Speichern).
- Die bisherigen Tests (AUDIO IN, Encoder, Kalibrierung) laufen in beiden Sprachfassungen fehlerfrei.

## Hardware-Test 27.10.2026

Bestätigt: WELLE und AUDIO-IN-Filter-/Distortion-Typ wechseln ohne Knacken, GLAETTUNG beruhigt die Tonhöhe im Modus FREI.

## Geprüft wurde

1. VCO läuft, WELLE durchdrehen: Knackt es noch? Ist die kurze Lücke störend?
2. AUDIO IN mit Signal, FILTER-Typ und DISTORTION-Typ wechseln: knackfrei?
3. VCO FREI mit fester Spannung (z. B. MIDI>CV, gehaltene Note): Anzeige und Ton mit GLAETTUNG AUS, LEICHT und STARK vergleichen. Wird die Streuung von ±8 ct kleiner?
4. Mit STARK eine Sequenz spielen: Ist das Nachgleiten wie beschrieben?
