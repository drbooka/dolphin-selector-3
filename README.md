# Dolphin Selector 3

A MicroPython sketch that turns the [AMYboard](https://amyboard.com) into a full Eurorack groovebox, fully playable on the module via a 128×128 OLED, rotary encoders and an optional joystick.

**Version 13.19** · runs on current AMYboard firmware (AMY 1.2.16x or newer)

## Features

- **Synth:** 16-part multitimbral (Juno-60, DX7, piano, 7 GM drum kits), DX7 banks (`.syx`) loaded from SD, per-channel filter/envelope/LFO, chords, portamento, CC learn
- **Sequencer:** 4 tracks (manual / euclid / scale / arpeggiator), 303 acid track with generator and joystick control, 8-voice drum track with velocity, polymeter, Euclid and a Grids-style X/Y pattern map. Tick-accurate via AMY's own sequencer, MIDI clock in/out
- **Effects:** reverb, chorus, echo, EQ and distortion (clip/fold/drive/mix) per bus, bitcrusher, distortion on the 303
- **Scenes:** 8 slots with A/B morph
- **Sampler:** 8 slots, WAVs from SD, recording (line or resampling) saved to SD, non-destructive trim and loop points, envelope and filter per slot (incl. notch/phaser), tempo sync (time-stretch), slicing to the drum track or MIDI
- **Eurorack:** CV in/out (1 V/oct, gate, LFO, envelope, quantizer, drum triggers), calibration, scope
- **Controls:** navigation encoder, M5Stack 8-encoder and/or up to two Adafruit Quad encoders (freely assignable knobs and buttons, live patch switching), M5Stack joystick

## Hardware

| Part | Role |
|---|---|
| AMYboard (ESP32-S3) | sound engine, MIDI, CV, SD card |
| Adafruit 1.5" 128×128 OLED #4741 | display |
| Adafruit I2C Rotary Encoder #5880 | navigation |
| M5Stack 8-Encoder, Adafruit Quad #5752 | optional extra encoders |
| M5Stack I2C Joystick (0x52) | optional |
| microSD (FAT32) | state, scenes, samples, DX7 banks |

## Installation

1. Update the AMYboard firmware at [amyboard.com/editor](https://amyboard.com/editor).
2. Load **`sketch.py`** from this repository in the editor and send it to the board.

`sketch.py` is shipped **without comments** (~260 KB): the commented version is too larger. For reading, use [`src/sketch_src.py`](src/sketch_src.py), which is the same code with comments.

Optional folders on the SD card: `samples/` for WAV files (16-bit PCM), `dx7/` for DX7 `.syx` banks.

## Documentation (German)

- [Bedienungsanleitung](docs/Bedienungsanleitung.md): user manual with the full menu tree
- [Projektbeschreibung](docs/Projektbeschreibung.md): architecture, version history, open hardware tests
- [Änderungen](docs/changes/): change notes per version

## License

[MIT](LICENSE): free to use, modify and share, including in your own sketches, as long as the copyright notice is kept.
