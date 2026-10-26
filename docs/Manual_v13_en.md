# Dolphin Selector 3 – User Manual

Version 13.24 · 26 Oct 2026 · AMYboard in a Eurorack case · English edition

This manual describes the English edition of the sketch (`sketch_v13.19_en.py`), where all menus are in English. The German edition works the same way. Saved settings and scenes can be used by both.

---

## 1. The four gestures

Everything is operated with the navigation encoder (Adafruit Single #5880). The gestures are the same on every page.

| Gesture | Effect |
|---|---|
| **Turn** | Move the selection or change a value. Turning fast makes bigger steps. |
| **Short press** | Open, edit, confirm |
| **Long press** (> 0.45 s) | One level back. While editing: cancel, the old value is restored. |
| **Hold and turn** | Change MIDI channel 1–16, from any page |
| **Hold 2 s on the HOME page** | PANIC: all notes off, sequencer stops. A ring shows the progress. |

The M5Stack joystick (optional) works like the encoder: left/right is turning, the button is pressing. On the drum page and in lists, up/down changes the row. If **GRIDS › JOYSTICK>XY** or **303 › JOYSTICK>303** is active, the joystick belongs to that instrument and no longer operates the menus.

### Editing values
- **Numeric values** (e.g. cutoff) open a big ring. Turning changes the value and is audible right away. Short press applies, long press cancels.
- **Choice values** (e.g. mode) light up in the row. Turn, then short press to apply, long press to cancel.
- The **Eurorack mode** only becomes active when you press ("OK=ACTIVATE"), so that no voltages jump while you scroll through the options.
- **Switches** (ON/OFF) toggle with a short press.

### Extra encoders E1–E8 and Q1–Q8
Supported are an M5Stack 8-Encoder (**E1–E8**) and up to two Adafruit Quad #5752 (**Q1–Q4**, **Q5–Q8**), also at the same time. The Single #5880 stays the navigation encoder. For a second quad, close the solder jumper **A0** on its back (address 0x4A instead of 0x49).

**SETUP › ENCODER** shows DEVICES at the top (e.g. `M5+2QUAD`), the active **SET** and the DIRECTION. Below it all detected extra encoders are listed by device (`= M5STACK =`, `= QUAD 1 =`, `= QUAD 2 =`) with their function. **Turn an extra encoder and the cursor jumps to its row.** A press opens that encoder's page. There too, turning a different extra encoder switches straight to its settings.

**Encoder page** (title e.g. `E3`, device on the right). After the FUNCTION only the matching rows appear:

| FUNCTION | Further rows | Effect |
|---|---|---|
| **OFF** | – | not read (saves I2C time) |
| **PAGE** | – | controls the first values of the open page (E1–E8 = values 1–8, Q1–Q4 and Q5–Q8 = values 1–4): on HOME the 4 macros, in the MIXER level/pan/porta/reverb, in the SEQUENCER tempo/swing, in the 303 editor note/octave/accent/slide, on the drum page 8 steps, in GRIDS LIVE X/Y/density, in the waveform editor START/END/LOOP A/LOOP B |
| **PATCH** | **CHANNEL** CURRENT or K1–K16 · **LIST** ALL, a category (BASS, LEAD, PAD …), FAVOURITES or DRUM KITS · **LOAD** INSTANT or ON PRESS | turning changes the channel's patch while playing. CURRENT follows the selected channel. A channel with a drum kit always scrolls through the drum kits. |
| **CHANNEL** | – | turning selects the current MIDI channel (like hold-and-turn on the Single) |
| **PARAMETER** | **GROUP** MIXER, SOUND, EFFECTS, SEQ+SCENE, 303, DRUMS, MODULAR, AUDIO IN · **VALUE** | fixed parameter, e.g. master, cutoff, reverb, 303 DRIVE, IN GAIN. The value is shown briefly while turning. |

Every encoder page also has **NOW** (current patch or value), **BUTTON** (see below) and **LED**.

- **LOAD INSTANT** (default): the patch is loaded after 120 ms of rest, and the sequencer keeps running. The overlay shows e.g. `K1 JUNO 012` / `Clock Chimes`. Turning fast jumps in steps of 4.
- **LOAD ON PRESS** (for live use): turning only shows `K3 > 045 PRESS` and the name; the sound stays. The encoder's button loads the patch. The overview then shows a `*` after the assignment. The BUTTON is set to CONTEXT automatically.
- If the channel is the sampler's CHROM. channel, `K1 SAMPLER` appears. If a list is empty (e.g. no favourites yet), `LIST EMPTY` appears.

**LED** (M5Stack and quads): **AUTO** shows the function as a colour – PAGE white, PATCH blue, CHANNEL purple, OFF dark, PARAMETER by group (MIXER and SEQ+SCENE yellow, SOUND and DRUMS orange, EFFECTS green, 303 red, MODULAR cyan, AUDIO IN purple). Or a fixed colour: OFF, RED, ORANGE, YELLOW, GREEN, CYAN, BLUE, PURPLE, WHITE.

**Encoder sets A/B/C:** three complete assignments (function, options, button, LED), e.g. one for live and one for sound design. Switch under SETUP › ENCODER › **SET** (turn, press activates) or with the button function **ENC SET >** (A → B → C → A). A new set starts as a copy of the previous one.

**Buttons** (on the encoder page): every extra encoder has a push button. A short press triggers on release, a long press (> 0.45 s) as soon as the time is reached.

| Assignment | Short | Long |
|---|---|---|
| **CONTEXT** (default) | PATCH: load the pending patch (ON PRESS), otherwise mute/unmute the channel · CHANNEL: mute/unmute the current channel · fixed parameter: big ring for fine adjustment · PAGE on the drum page: set the step under the encoder | PATCH/CHANNEL: patch browser for the channel |
| START/STOP | Start/stop the sequencer | – |
| TAP TEMPO | Tap the tempo | – |
| PANIC (LONG) | – | All notes off |
| MUTE K1–K4 | Mute/unmute the channel | – |
| MUTE 303 / MUTE DRUMS | Mute/unmute the track | – |
| AUDIO IN | Input on/off (MODULAR › AUDIO IN) | – |
| ENC SET > | next encoder set | – |
| OFF | Not read | |

Default: E1–E4 PAGE, E5 master, E6 level, E7 reverb, E8 echo, **Q1–Q8 PATCH K1–K8**. The assignment stays saved even if a device is not connected for a while. Older states keep their assignment (OFF stays OFF).

### Status line (top)
`C1` = current MIDI channel · patch family (JUNO/DX7/DRUM …, `SMP` = sampler channel) · `IN` = AUDIO IN running · tempo · ▶ running / ■ stopped. The thin line below shows the CPU load (bright from 85 %).

---

## 2. Menu tree

```
HOME (start page)
├─ Patch line + info (voices, bus, mute)
├─ MACRO 1–4 (rings) ........ press = edit value
├─ Playhead of the selected track
├─ START / STOP
└─ MENU ─► carousel
    │
    ├─ SOUND  (channel K#)
    │   ├─ PATCH ─► patch browser
    │   │   ├─ FAVORITES · RECENT
    │   │   ├─ BASS · LEAD · PAD · KEYS · BRASS/WIND · PLUCK · BELL/PERC · FX · OTHERS
    │   │   ├─ ALL JUNO · ALL DX7 · DRUMKITS
    │   │   ├─ DX7 FROM SD ─► .SYX file ─► voice 1–32
    │   │   └─ NO PATCH
    │   │   (on channel 10 only DRUMKITS)
    │   ├─ CUTOFF · RESONANCE .................... Juno / AMYB
    │   ├─ ATTACK · DECAY · SUSTAIN · RELEASE ...... Juno / AMYB
    │   ├─ LFO RATE · LFO DEPTH .................. Juno / AMYB / DX7
    │   ├─ ALGORITHM · FEEDBACK .................. DX7
    │   ├─ CHORD · PORTAMENTO · VOICES
    │   ├─ FAVORITE (YES/NO)
    │   ├─ CC-LEARN ─► LEARN TARGET · LEARN · MAPS CHANNEL · DELETE
    │   └─ PATCH VALUES (only after changes: back to the patch sound)
    │
    ├─ MIXER  (16 faders, turn = choose channel)
    │   └─ press ─► CHANNEL n
    │       ├─ PATCH · LEVEL · PAN · MUTE · BUS · VOICES
    │       ├─ CHORD · PORTAMENTO
    │       └─ FAVORITE · REMOVE
    │
    ├─ EFFECTS  (bus of the current channel)
    │   ├─ BUS (0–3) · CHANNELS (who uses the bus) · PATCH-FX (ON/OFF)
    │   ├─ REVERB ─► LEVEL · LIVE · DAMP · XOVER
    │   ├─ CHORUS ─► LEVEL · RATE · DEPTH · DELAY
    │   ├─ ECHO   ─► LEVEL · TIME · FDBK · FILT
    │   ├─ EQ     ─► SOUND PROFILE (MANUAL/NEUTRAL/WARM/PUNCH/BRIGHT) · LOW · MID · HIGH
    │   ├─ DISTORTION ─► TYPE (OFF/CLIP/FOLD/CLIP+FOLD) · BUS DRIVE · DIST MIX
    │   ├─ MASTER · CRUSH BITS · CRUSH RATE
    │   └─ BUS RESET
    │
    ├─ SEQUENCER  (overview: S1–S4, 303, DRM, START/STOP, GLOBAL)
    │   ├─ TRACK 1–4
    │   │   ├─ EDIT STEPS .................. MANUAL mode only
    │   │   ├─ PATTERN (A–D) · MODE (MANUAL/EUCLID/SCALE/ARP)
    │   │   ├─ CHANNEL · STEPS (1–32) · DIVISION (1/32–1/4) · NOTE · GATE
    │   │   ├─ PULSE ....................... EUCLID
    │   │   ├─ SCALE ....................... EUCLID / SCALE
    │   │   ├─ ARP DIRECTION · ARP OCTAVES · ARP IN · LATCH ... ARP
    │   │   ├─ OUTPUT (INT/MIDI/BOTH) · MIDI CHANNEL · MUTE
    │   │   └─ COPY > NEXT · CLEAR
    │   ├─ 303 ACID
    │   │   ├─ EDIT STEPS · PATTERN (A–D)
    │   │   ├─ ACID-GENERATOR · MUTATE
    │   │   ├─ JOYSTICK>303 · JOY X · JOY Y · JOY DEPTH ... only with joystick
    │   │   ├─ WAVE · 303 CUTOFF · RESO · ENV MOD · DECAY · ACCENT · SLIDE
    │   │   ├─ DISTORTION (OFF/CLIP/FOLD/CLIP+FOLD) · 303 DRIVE · 303 DIST MIX
    │   │   ├─ TUNE · ROOT NOTE · 303 LEVEL · STEPS (1–16)
    │   │   ├─ OUTPUT · MIDI CHANNEL · MUTE · CV ACCENT (5V/8V)
    │   │   └─ COPY > NEXT · CLEAR
    │   ├─ DRM ─► drum grid (8 instruments × 16 steps)
    │   │   └─ TRACK MENU (after the last step)
    │   │       ├─ DRUMKIT · INSTRUMENT (1–8) · SAMPLE (KIT/S1–S8) · SLICE · SOUND · NOTE
    │   │       ├─ LENGTH (1–32) · INSTR. MUTE · PULSE · SET EUCLID · CLEAR ROW
    │   │       ├─ GRIDS ─► MODE (PATTERN/LIVE) · GRIDS X · GRIDS Y · RANDOM ·
    │   │       │           INSTRUMENT · DENSITY · CV IN1/2>XY · JOYSTICK>XY · WRITE TO PATTERN
    │   │       ├─ CV TRIGGER ─► TRIG OUT1 · TRIG OUT2 · TRIG LENGTH · TRIG LEVEL
    │   │       ├─ PATTERN (A–D) · DIVISION · CHANNEL
    │   │       ├─ OUTPUT (INT/MIDI/BOTH) · MIDI CHANNEL · TRACK MUTE
    │   │       └─ ALL LENGTHS 16 · COPY > NEXT · CLEAR
    │   └─ GLOBAL
    │       └─ START/STOP · TEMPO · TAP TEMPO · SWING · CLOCK · TRANSPORT · M5 SWITCH
    │
    ├─ MODULAR  (CV monitor IN1/IN2/OUT1/OUT2 at the top)
    │   ├─ MODE (OFF · CV1>FILTER · GATE+PITCH · MIDI>CV · 303>CV · CV1>OUT1 · CV2>OUT2 · QUANTIZE)
    │   ├─ SCALE ...................... QUANTIZE
    │   ├─ CV MOD OUT1 · CV MOD OUT2 (OFF/LFO/ENV)
    │   ├─ CV LFO ─► WAVE · RATE · DEPTH · FOLD · LFO DRIVE · FOLD MIX · FOLD MOD · MOD DEPTH
    │   ├─ CV ENV ─► ATTACK · RELEASE · DEPTH · FOLD · ENV DRIVE · FOLD MIX
    │   ├─ VCO ─► VCO · 1V/OCT IN · PITCH (FREE/QUANT) · SCALE · ROOT AT 0V · VCO FINE · V/OCT
    │   │        WAVE · VCO PW · VCO SUB · SUB OCTAVE · VCO OSC 2 · INTERVAL · VCO DETUNE
    │   │        MOD IN · MOD TARGET (FM/PWM/FOLD) · VCO MOD · FOLD · VCO DRIVE · FOLD MIX
    │   │        VCO LEVEL · PAN · BUS
    │   ├─ AUDIO IN ─► AUDIO IN · MODE (STEREO/MONO/L ONLY/R ONLY) · IN GAIN · IN LEVEL · IN PAN
    │   │             WIDTH · BUS · BUS FX · FILTER · IN CUTOFF · IN RESO
    │   │             DISTORTION · IN DRIVE · DIST MIX
    │   ├─ SCOPE
    │   └─ CALIBRATION ─► OUT1 OFFSET · OUT1 SCALE · OUT2 OFFSET · OUT2 SCALE · TEST VOLTAGE
    │
    ├─ SCENES
    │   ├─ SCENE 1–8 ─► LOAD · SAVE · AS MORPH A · AS MORPH B · DELETE
    │   └─ MORPH A>B · MORPH A · MORPH B
    │
    ├─ SAMPLER
    │   ├─ S1 … S8 ─► SLOT n
    │   │   ├─ FILE ─► WAV selection
    │   │   ├─ WAVEFORM ─► START · END · LOOP A · LOOP B · ZOOM · LISTEN
    │   │   ├─ LISTEN · SAVE TO SD (RAM slots only)
    │   │   ├─ MODE (ONESHOT/GATE/LOOP) · SLICES (OFF/4/8/16) · SPREAD TO DRUMS
    │   │   ├─ TEMPO SYNC · SYNC FROM LEN · GRAIN SEARCH
    │   │   ├─ TUNE · FINE · ROOT NOTE
    │   │   ├─ LEVEL · PAN · BUS
    │   │   ├─ ATTACK · DECAY · SUSTAIN · RELEASE
    │   │   ├─ FILTER (OFF/LP/BP/HP/LP24/NOTCH/PHASER) · CUTOFF · RESONANCE · F-ENV · F-DECAY
    │   │   └─ RELOAD · CLEAR
    │   ├─ RECORDING ─► TARGET SLOT · SOURCE (LINE/MIX) · LENGTH · UNIT (SEC/BARS) ·
    │   │               START (NOW/BAR 1) · DURATION · RECORDING · AUTO SAVE ·
    │   │               SD SAVE · TEST INPUT
    │   ├─ CHROM. CHANNEL · CHROM. SLOT · CHROM. VOICES
    │   ├─ PAD CHANNEL · SLICE-SLOT
    │   └─ SAMPLE-RAM · PADS (displays)
    │
    └─ SETUP
        ├─ MIDI ─► MIDI THRU · MIDI OUT TYP (A/B) · CLOCK · RST ALL MIDI
        ├─ ENCODER ─► DEVICES · SET (A/B/C) · DIRECTION · E1–E8 · Q1–Q8 (connected ones only) · I2C-SCAN
        │   └─ Ex/Qx ─► FUNCTION · CHANNEL · LIST · LOAD · GROUP · VALUE · NOW · BUTTON · LED
        ├─ MACROS ─► MACRO 1–4
        ├─ AUDIO (STEREO/MONO) · VOICES MAX · FAILSAFE
        ├─ DISPLAY ─► BRIGHTNESS · SAVER AFTER · UPDATE (FULL/BANDS)
        ├─ WLAN ─► STATUS · IP · NETWORK · CONNECT · RE-ENTER · DISCONNECT
        ├─ CLOCK ─► SEQ OUTPUT (DIRECT/AHEAD) · LOOKAHEAD · AHEAD TEST · UI CLOCK ·
        │           FALLBACK · TRANSPORT · status displays
        ├─ MOUNT SD · SD STATE NEW · SD TEST
        ├─ INFO ─► VERSION · ENCODER · EXTRAS · JOYSTICK · DISTORTION · TEMPO SYNC · DX7 SD (FM) · I2C · RAM FREE ·
        │          LAST · VOICES · MEMORY · SD · SD REASON · SD CLOCK · SD FREE · SAVE ERROR ·
        │          statistics (BOOT … CONTROLS MAX) · RESET STATS
        └─ FACTORY RESET
```

Rows with a note on the right (e.g. "Juno / AMYB") only appear when they fit the current patch or mode. All DISTORTION entries only appear if the firmware supports them (SETUP › INFO › DISTORTION = YES).

On the display, long names are shortened on the left when a value needs the space on the right (e.g. "SOUND P… MANUAL").

---

## 3. The pages in detail

### HOME (start page)
- Turning selects: macro 1–4 → START/STOP → MENU.
- On a macro, the second line shows the value. Pressing opens the big ring.
- The macros are assigned under SETUP › MACROS. Default: cutoff, resonance, reverb, level.
- The playhead shows the track selected in the SEQUENCER. For DRM each cell shows the loudest hit of that step.

### SOUND
Always applies to the current channel (hold and turn to change the channel).
- **Patch browser:** while scrolling you hear every patch right away (it is loaded after 120 ms of rest). Short press applies, long press restores the old patch. `*` = current patch, `+` = favourite.
- **Sound shaping:** filter, envelope, LFO and DX7 values only apply once you change them. Otherwise the patch sounds as designed. Changing the patch resets these changes.
- **CHORD:** one key plays a chord (MAJ, MIN, MAJ7, … OCTAVE). The voices needed are added automatically.
- **DX7 FROM SD** (in the patch browser, not on channel 10): load your own DX7 banks. Copy `.SYX` files (32-voice bank or single voice, as found in DX7 archives online) into the `dx7` folder of the SD card or into the root folder. First choose the file; pressing shows the voices with their names. While turning you hear every voice, pressing applies it, long press restores the old sound. The voice is saved per channel (file, number, name) and reloaded from the card at startup. ALGORITHM, FEEDBACK and LFO work as with the built-in DX7 patches. If the file is missing at startup, the channel takes the first built-in DX7 patch ("DX7 Kn · NOT LOADED"). SD voices do not appear under FAVORITES/RECENT because they belong to the channel. Scenes save them too.
  - **Where to find banks:** [Dave Benson's DX7 Page](https://homepages.abdn.ac.uk/d.j.benson/pages/html/dx7.html) – `dx7patch.zip` with the original Yamaha ROMs `rom1a`–`rom4b` (a good start), plus large collections (`dx7.zip`, `deckard.zip`, `all-syx.zip`, `DX7EXTRA.ZIP`). Not `raw.tar` (no sysex header). `DX7600.ZIP` contains `.snd` files – rename them to `.syx`. The free DX7 emulator [Dexed](https://www.github.com/asb2m10/dexed) also comes with about 30 cartridges as `.syx`. Better copy a selection than hundreds of files (names are shortened to 14 characters).
- **CC-LEARN:** choose a target (CUT/RES/LEVEL/PORTA), press LEARN, move a knob on the keyboard. Up to 4 assignments per channel.
- Fast patch change for channels 1–4 without the menu: assign an extra encoder to **PATCH K1–K4** (see section 1).

### MIXER
- Turning selects the channel. The faders show the level, the dot below shows the pan, "M" stands for mute.
- At the top right is the voice usage, e.g. `10/24`. Bright means the budget (VOICES MAX) is exceeded.
- Guide values for the CPU load (AMYboard FAQ): a Juno voice ~12 %, a DX7 voice ~8 %, a drum hit ~2 %. So a new patch on channel 1 starts with 4 Juno or 6 DX7 voices, on other channels with 2. A drum kit always needs just 1 voice – it has its own oscillator for every drum, so simultaneous hits still sound.
- **PAN** on a drum kit channel moves all drums of the kit.
- The sampler's CHROM. channel appears here like a normal channel; LEVEL, PAN and BUS apply to it.
- Pressing opens the channel strip.

### EFFECTS
- Effects apply **per bus** (0–3). Every channel is on a bus (MIXER › CHANNEL › BUS), every sample slot has its own BUS (default 1).
- Default: synths on bus 0 with a little reverb, drums (channel 10) and sample pads on bus 1, dry with the PUNCH EQ.
- **PATCH-FX** (default ON on buses 0, 2 and 3): the loaded patch decides chorus and EQ. The Juno patches bring their typical Juno chorus and their high-pass setting as EQ – without them they sound thin. CHORUS and EQ then show "PATCH". As soon as you change chorus, EQ or the sound profile by hand, PATCH-FX switches to OFF for that bus and your values apply. Switching PATCH-FX back ON reloads the patches on the bus. If several channels share a bus, the chorus of the patch loaded last applies – separate buses help.
- **SOUND PROFILE** sets the EQ to presets. Changing the EQ by hand switches to MANUAL.
- **DISTORTION** (per bus): **TYPE** OFF, CLIP (soft saturation), FOLD (wavefolder, metallic) or CLIP+FOLD. **BUS DRIVE** (1–16) sets how hard the signal is driven into the distortion, **DIST MIX** (0–1) the share of the distorted signal. Good for the drums on bus 1: CLIP with a drive of 2–4 makes them denser and louder. BUS DRIVE can be assigned to a macro or a fixed encoder.
- **CRUSH** belongs to the same stage as the distortion in AMY. With TYPE OFF, CRUSH is unaffected. With CLIP/FOLD, DIST MIX also affects the crush share. **CRUSH RATE** also works alone (CRUSH BITS set to OFF): then only sample-rate reduction without bit reduction.
- **MASTER** automatically balances the volume of several channels (headroom).
- **BUS RESET** resets all effects of the bus (including the distortion) to the defaults.

### SEQUENCER
**Overview:** six rows (S1–S4, 303, DRM) with playheads. A bright mark on the right means a pattern change is queued.

**Modes of tracks 1–4:**
| Mode | Function |
|---|---|
| MANUAL | Set steps by hand, with probability |
| EUCLID | PULSE hits spread evenly over STEPS, pitch follows the SCALE |
| SCALE | Each step plays the next degree of the scale |
| ARP | Plays the keys held on "ARP IN" (UP/DOWN/UPDOWN/RANDOM, 1–3 octaves, LATCH) |

A track can also play the sampler's CHROM. channel: track CHANNEL = CHROM. CHANNEL.

**Step editor (MANUAL):** turning selects the step, pressing cycles it: OFF → 100 % → 75 % → 50 % → 25 % → OFF. DONE is at the end.

**303 editor:** turning selects the step. Each press moves one field on: NOTE → OCTAVE → ACCENT → SLIDE → back to the selection. E1–E4 set the four fields directly.

**Patterns A–D:** while the sequencer runs, the pattern only changes at the end of the cycle (for DRM after 16 steps). When stopped, it changes immediately. COPY > NEXT copies e.g. A to B.

**ACID-GENERATOR** builds a new 303 pattern (minor pentatonic, rests, accents, slides). **MUTATE** changes 3 random steps.

**303 distortion:** **DISTORTION** chooses OFF, CLIP, FOLD or CLIP+FOLD, **303 DRIVE** (1–16) the amount, **303 DIST MIX** the share. The distortion sits before the filter – cutoff, resonance and ENV MOD shape the distorted sound, like the classic distorted acid line. With high drive the 303 gets louder: turn down 303 LEVEL. 303 DRIVE can be assigned to a macro or a fixed encoder; MORPH A>B blends DRIVE and MIX as well.

**JOYSTICK>303** (only with a connected joystick): the joystick plays the 303 live.
- **JOY X / JOY Y:** target per axis – CUTOFF, RESO, ENV MOD, DECAY, ACCENT, SLIDE, TRANSP (±12 semitones), DENSITY (down = drop notes) or **DRIVE** (changes 303 DRIVE up or down by up to a factor of 4; only works if DISTORTION is not OFF). Default X = CUTOFF, Y = ENV MOD.
- **JOY DEPTH:** how far the joystick moves the values (10–100 %).
- Releasing jumps back to the saved values. The **joystick button** keeps the current sound as the new base values ("TAKEN OVER").
- While active, the joystick does not operate menus and has priority over JOYSTICK>XY of the drums.

**GLOBAL:**
- **CLOCK:** INTERNAL = own clock, SEND = output MIDI clock, FOLLOW = external clock (MIDI start/stop start and stop the sequencer in time with the master).
- **TAP TEMPO:** press several times in time. A pause of more than 2 s starts over.
- **SWING:** 0–100 %, shifts every second step (also for DRM, for all instruments together).
- **M5 SWITCH:** the switch on the M5Stack starts and stops the sequencer.

### DRUMS (track DRM)
The grid shows 8 instruments below each other (default BD, SD, CH, OH, CP, LT, HT, RS) with 16 steps each. The brightness of a cell is the velocity, a dot means "off". The grey bar is the playhead. It can be in a different place per row if the lengths differ. If an instrument plays a sample slot, `S1` … `S8` is shown on the left instead of the drum name, for a slice e.g. `1c` (slot 1, slice 3; a = 1 … p = 16).

| Control | Effect |
|---|---|
| Turn | Cursor through the steps. At the end of a row it moves to the next instrument, after the last one into the TRACK MENU. |
| Short press | Step: OFF → 100 % → 67 % → 40 % → OFF |
| Joystick up/down | Change the instrument, the step stays |
| E1–E8 (on PAGE) | The 8 steps around the cursor (1–8 or 9–16). Turning sets the velocity in 16 levels, 0 = off. A line under the row shows the range. Q1–Q4 on PAGE: the first 4 of these steps. |
| Long press | Back to the overview (saves) |

- At the bottom: instrument, step/length and velocity, below that pattern and division. `A>B` means a change is queued.
- With lengths above 16 the grid shows the page of the cursor (1–16 or 17–32).

**TRACK MENU:**
- **DRUMKIT** changes the kit on the track's CHANNEL (TR-808, TR-909, LINN 9000, MR-12, TOKYO, 80s POWER, PERCUSSION). While turning you hear every kit right away. This is the same patch as under SOUND › PATCH on that channel. "---" means there is no drum kit on the channel.
- **INSTRUMENT** selects the row that SAMPLE, SOUND, NOTE, LENGTH, INSTR. MUTE, SET EUCLID and CLEAR ROW apply to.
- **SAMPLE:** KIT = sound from the drum kit as before. **S1–S8** = the instrument plays this sample slot instead (it is previewed when selected). Velocity works; MIDI output and CV trigger stay unchanged. Slots in GATE or LOOP mode sound until just before the next step.
- **SLICE** (only if the chosen slot has SLICES): WHOLE = the whole sample, **1–16** = only this piece. The piece is previewed when selected. A piece sounds exactly its own length; a new hit on the same slot cuts the previous one (like a sampler with choke). This lets you rebuild breakbeats – also with Euclid, polymeter and GRIDS.
- **SOUND:** sound of the instrument from the GM list (KICK, SNARE, CLAP, HH CLSD, HH OPEN, TOMs, CRASH, RIDE, COWBELL, CONGAs, CLAVES …). While turning each sound is previewed briefly.
- **NOTE:** the same setting as a number, for notes outside the list (GM mapping, e.g. 36 BD, 38 SD, 42 CH). The TR-8S understands the same notes by default.
- **LENGTH:** 1–32 steps per instrument. Different lengths give polymeter, e.g. hi-hat with 12 against a bass drum with 16.
- **SET EUCLID:** spreads PULSE hits evenly over the instrument's LENGTH (overwrites this row).
- **OUTPUT:** INT = drum kit/samples internally, MIDI = MIDI output only (e.g. TR-8S on MIDI CHANNEL), BOTH = both.
- **TRACK MUTE** mutes the whole track, **INSTR. MUTE** only one instrument.

**GRIDS (pattern generator):**
A map with four corners creates the drum patterns. X and Y blend smoothly between the corners:

| | X = 0 | X = 1 |
|---|---|---|
| **Y = 0** | STRAIGHT (4/4) | BREAKBEAT |
| **Y = 1** | HALFTIME (sparse) | BROKEN (dense) |

- **MODE LIVE:** the grid shows and plays the Grids pattern instead of the pattern. It changes immediately when X, Y or DENSITY change.
- **DENSITY** (0–15, per instrument): how many hits get through. Important hits come first and are played louder.
- **RANDOM** (0–15): small variations on every cycle.
- **E1–E8** on the drum page in LIVE mode: E1 = X, E2 = Y, E3–E8 = density of instruments 1–6.
- **CV IN1/2>XY:** CV IN 1 shifts X, CV IN 2 shifts Y (0–5 V = full range).
- **JOYSTICK>XY:** the deflection shifts X/Y, releasing jumps back.
- **WRITE TO PATTERN** writes the current Grids pattern (with randomness) into the selected pattern and switches to PATTERN. The same happens when you press a step in LIVE mode.
- GRIDS X and GRIDS Y can be assigned to fixed encoders or macros, and MORPH A>B blends them as well.

**CV TRIGGER:**
- **TRIG OUT1 / OUT2:** one instrument per output sends a gate on every hit, e.g. BD → A-140-2v (envelope) for sidechain pumping. The triggers run tick-accurately via AMY, in sync with the sound.
- **TRIG LENGTH:** gate length in 1/32 (1–8).
- **TRIG LEVEL:** 5V, 8V or VELO (0–8 V depending on velocity).
- INSTR. MUTE only mutes the sound, not the trigger. TRACK MUTE stops both.
- If a MODULAR mode, CV MOD or the calibration uses the output, that has priority ("OUT1 IN USE").
- On the drum page, a small bar on the right edge shows which instrument is on OUT1 (left) or OUT2 (right). Dark = output in use.

### MODULAR
| Mode | Function |
|---|---|
| CV1>FILTER | CV IN 1 controls the filter of the current channel |
| GATE+PITCH | IN 1 = gate, IN 2 = pitch (1 V/oct) for the current channel |
| MIDI>CV | Notes of the current channel → OUT 1 pitch, OUT 2 gate (5 V) |
| 303>CV | 303 track → OUT 1 pitch, OUT 2 gate (accent optionally 8 V) |
| CV1>OUT1, CV2>OUT2 | Pass the input straight through |
| QUANTIZE | IN 1 quantized to the selected SCALE → OUT 1 |

- Pitch is always 1 V/octave, 0 V = C1 (MIDI 24).
- **CV MOD:** LFO or envelope (ENV, triggered by notes of the current channel) on OUT 1/2. If a Eurorack mode uses the output, the mode has priority.
- **WAVEFOLDER (v13.20):** CV LFO › FOLD (CLIP/FOLD/CLIP+FOLD) folds the LFO inside AMY. DEPTH acts before the folder (like the input level), LFO DRIVE adds more gain, FOLD MIX blends between smooth and folded. FOLD MOD = CV IN1/IN2 shifts the drive by voltage (MOD DEPTH 1 = ±2 octaves, 5 V = full swing). A preview at the top of the page shows the wave (approximate). LFO DRIVE and ENV DRIVE can be assigned to a macro or encoder. CV ENV also has FOLD, ENV DRIVE and FOLD MIX.
- **CALIBRATION:** set TEST VOLTAGE to 0–4 V, measure it with an oscillator or tuner, then adjust OFFSET/SCALE per output.

#### VCO (v13.21)
**MODULAR › VCO** turns the AMYboard into a standalone oscillator: it sounds continuously (no MIDI, no gate needed), pitch comes in as 1 V/oct at CV IN 1 or IN 2. The output is the AMYboard's normal audio out; level and envelope come from a VCA and ADSR in the rack.

| Item | Effect |
|---|---|
| **VCO** | ON/OFF |
| **1V/OCT IN** | OFF · IN1 · IN2: which input controls pitch |
| **PITCH** | FREE = continuous (AMY tracks the voltage itself, no Python) · QUANT = snapped to SCALE |
| **ROOT AT 0V** | note at 0 V (default C1, as MIDI>CV) |
| **VCO FINE** | ±100 cents |
| **V/OCT** | tracking trim 0.950–1.050 if octaves are off |
| **WAVE** | SIN · TRI · SAW · PULSE; **VCO PW** = pulse width (PULSE only) |
| **VCO SUB** | sub oscillator level (square), **SUB OCTAVE** −1 or −2 |
| **VCO OSC 2** | level of a second oscillator with the same wave; **INTERVAL** ±24 semitones, **VCO DETUNE** 0–50 cents (beating) |
| **MOD IN** | OFF · IN1 · IN2: second CV input for modulation |
| **MOD TARGET** | **FM** (pitch, VCO MOD 1 = 1 oct/V) · **PWM** (VCO MOD 1 = 0.08 per volt) · **FOLD** (shifts VCO DRIVE, 5 V = full swing) |
| **FOLD · VCO DRIVE · FOLD MIX** | wavefolder on the main oscillator (as on the CV LFO) |
| **VCO LEVEL · PAN · BUS** | level and effect bus (the bus reverb, echo, EQ and distortion apply) |

- **Tuning:** the top of the page shows the current note, frequency and deviation in cents (bar centred = in tune). To trim, feed a known voltage, e.g. MODE MIDI>CV, OUT 1 → IN 1 and play C1 and C5 on the keyboard (pitch holds after release). Set ROOT/FINE so C1 reads 0 ct, then V/OCT so C5 reads 0 ct too.
- **FM and PWM** run inside AMY and update every audio block (about 6 ms) – meant for vibrato, pitch envelopes and slow PWM, not audio-rate FM. FOLD modulation updates every 30 ms, QUANT follows the input about every 40 ms.
- Nothing is occupied: CV1>FILTER, GATE+PITCH, Grids etc. can keep reading the same input.
- VCO FINE, VCO PW, VCO SUB, VCO OSC 2, VCO DETUNE, VCO DRIVE, VCO MOD and VCO LEVEL can be assigned to a macro or extra encoder. The VCO state is part of the scenes. PANIC keeps the VCO running.
- If the VCO line in MODULAR shows **MISSING**, the firmware has no free synth (SETUP › INFO › VCO SYNTH).

#### AUDIO IN (v13.22)
**MODULAR › AUDIO IN** routes the stereo input to the output permanently – the AMYboard becomes an effects unit in the rack. The input runs through distortion and filter, then through an effect bus with reverb, chorus, echo, EQ, bus distortion and crush. AMY plays the input itself, so the user interface does not slow it down.

| Item | Function |
|---|---|
| **AUDIO IN** | ON/OFF (OFF by default) |
| **MODE** | **STEREO** (L left, R right) · **MONO** (L+R together at IN PAN, −6 dB each) · **L ONLY** · **R ONLY** |
| **IN GAIN** | input gain −24 … +12 dB, before distortion and filter |
| **IN LEVEL** | output level |
| **IN PAN · WIDTH** | position; WIDTH (STEREO only) 1 = full stereo width, 0 = both sides at IN PAN |
| **BUS** | effect bus (default 2, so synths and drums keep their own effects) |
| **BUS FX** | opens EFFECTS directly for the input's bus |
| **FILTER · IN CUTOFF · IN RESO** | OFF · LP · BP · HP · LP24 (· NOTCH · PHASER), as for sample slots |
| **DISTORTION · IN DRIVE · DIST MIX** | CLIP/FOLD before the filter |

- **Level meter** at the top: L and R of the input (before IN GAIN) with marks at −24/−12/−6 dB, peak value on the right, **CLIP** when clipping. It also runs while OFF, so you can check the level before switching on. Below it: mode (ST/MO/L/R), bus, filter, distortion.
- **Everywhere:** `IN` in the status line shows the input is running. With the button function **AUDIO IN** (SETUP › ENCODER › BUTTONS) an extra encoder switches it on and off from any page. IN GAIN, IN LEVEL, IN PAN, IN CUTOFF, IN RESO and IN DRIVE can be assigned to a macro or extra encoder.
- **Scenes** store all input settings but do not switch it on or off. PANIC keeps it running.
- **Beware of feedback:** do not patch the AMYboard's output into its own input while AUDIO IN is on.
- If the meter does not move: check the DIP switches on the back, cable and level. If MODULAR shows **MISSING**, the firmware has no free synths (SETUP › INFO › AUDIO IN).

### SCENES
- A scene saves sound, mixer, effects (including the bus distortion), the VCO, the AUDIO IN settings (not ON/OFF), tempo, swing and all sequencer patterns (including the drum track with its SAMPLE assignment and the 303 with its distortion). Encoder, MIDI, WLAN and **sampler settings** are not included.
- **MORPH A>B** blends smoothly between two scenes: levels, pan, filter, effects, master, tempo, 303 sound (incl. 303 DRIVE and DIST MIX), Grids X/Y. Patches only change when you LOAD a scene.
- Tip: put MORPH on an extra encoder.

### SAMPLER
The sampler has **8 slots** (S1–S8). A slot points to a WAV file on the SD card or holds a recording in RAM. On the right in the list you see the name, `EMPTY`, `LOADING`, `RAM`, `REC...` (recording) or an error message.

**Getting your own samples onto the card:**
- Copy WAV files on the computer into the `samples` folder of the SD card (or into the root folder).
- Supported: **16-bit PCM, mono or stereo, any sample rate**. Stereo is mixed down to mono when loading. Not supported: 24/32 bit, float, compressed formats (the file selection then reports e.g. `16 BIT ONLY`).
- At most **10 s** per slot are loaded (the range START…END).

**Slot page (S1 … S8):**
- **FILE:** choose a WAV and load it by pressing. The slot is previewed once. Files from the root folder are shown with a leading `/`.
- **WAVEFORM:** the editor (see below). Only for slots with a file.
- **LISTEN:** plays the slot once.
- **MODE:**

| Mode | Behaviour |
|---|---|
| ONESHOT | Always plays to the end (note-off is ignored) – ideal for drums |
| GATE | Stops on release (hard stop, without release) |
| LOOP | Repeats LOOP A…B while held; RELEASE follows afterwards |

- **SLICES** (not in LOOP mode): OFF, 4, 8 or 16 equal pieces of the loaded range. In the waveform editor dashed lines show the borders. The pieces are played via the drum track (TRACK MENU › SLICE). Via MIDI, PAD CHANNEL notes 44–59 play the pieces (see "Playing"). LISTEN plays the whole sample.
  - **SPREAD TO DRUMS** puts slices 1–8 on instruments 1–8 (SAMPLE = this slot, LENGTH 16) and writes the original pattern into the current drum pattern: slice 1 on step 1, the others spread evenly (this assumes the slot is 1 bar long). After that, the drum track plays the loop like the original – now you can rearrange the steps. You are asked first, because rows 1–8 get overwritten. With 16 slices only 1–8 go onto the instruments.
  - **Together with TEMPO SYNC** each piece lasts exactly TEMPO SYNC ÷ SLICES (e.g. 1 BAR / 8 = one eighth) and follows the tempo – the break stays on the grid at any tempo, without a pitch change.
- **TEMPO SYNC** (not in LOOP mode): OFF or 1 beat … 10 bars. The slot then always lasts exactly that long, whatever tempo is running – even with tempo changes during the note – and keeps its pitch (granular time-stretch in AMY). Ideal for loops and phrases: a 2-bar loop stays in time at 90 as at 140 BPM. TUNE, FINE and the CHROM. channel transpose without changing the duration.
  - **SYNC FROM LEN** suggests the matching value from the length and the current tempo (shown on the right) and applies it when pressed.
  - **GRAIN SEARCH** (0–512, default 64): how far the stretcher searches for matching spots. For low sounds (bass) a higher value can sound cleaner; 0 = fixed grains (more stable, comb-like sound).
  - Recordings with UNIT BARS get TEMPO SYNC automatically (e.g. 2 bars → 2 BARS).
  - A slot with TEMPO SYNC needs about 2.5 times as much CPU time when playing – keep an eye on the CPU load when many play at once.
- **TUNE** (±24 semitones) and **FINE** (±50 cents): pitch, applied immediately.
- **ROOT NOTE:** the key on which the sample sounds at its original pitch in the CHROM. channel (default C4 = note 60).
- **LEVEL · PAN · BUS:** apply to the pad (the CHROM. channel uses the mixer values of its channel). Through the BUS a slot also gets the bus distortion.
- **ATTACK · DECAY · SUSTAIN · RELEASE:** volume envelope.
- **FILTER** (OFF/LP/BP/HP/LP24, plus **NOTCH** and **PHASER** if the firmware supports them) with **CUTOFF**, **RESONANCE**, **F-ENV** (filter envelope, ±6 octaves) and **F-DECAY**. NOTCH cuts out a narrow band, PHASER is a classic 3-notch phaser – with F-ENV or CUTOFF on an encoder it moves audibly.
- **RELOAD:** reloads the file, e.g. after it was replaced on the card.
- **CLEAR:** frees the slot. The file stays on the card.

**Waveform editor (non-destructive trimming):**
- At the top the waveform: bright = loaded range, solid lines = START and END, dashed = LOOP A and B (only in LOOP mode).
- **Turning** selects the field: START, END, LOOP A, LOOP B, ZOOM, LISTEN.
- **Pressing** edits the field (then turning changes the value), switches the ZOOM (1x/8x/64x) or plays the sample.
- **Long press** finishes editing; a second one goes back.
- Turning slowly moves the marker by 1 pixel, fast by up to 16 pixels. With zoom 64x it is accurate to the millisecond.
- **E1–E4** (or Q1–Q4) set START, END, LOOP A and LOOP B directly.
- About 0.5 s after the last change the slot is reloaded and played once. The file itself is never changed.

**Playing – three ways:**
1. **Pads via the drum track:** drum track › TRACK MENU › SAMPLE = slot (see DRUMS).
2. **PAD CHANNEL:** choose a MIDI channel. On this channel **MIDI notes 36–43 play slots 1–8** with velocity (C1–G1 or C2–G2 depending on the device). Every slot is monophonic, a new hit cuts the old one. Good for a drum track of the KeyStep Pro.
   - **Notes 44–59 play the slices** of the **SLICE-SLOT** (note 44 = slice 1 … 59 = slice 16, only as many as the slot has SLICES). Each piece sounds for its own length (with TEMPO SYNC in tempo). In GATE mode releasing stops earlier. The list shows the number of slices next to each slot.
3. **Chromatic:** set **CHROM. CHANNEL** to a free MIDI channel (not 10, not the Juno channel – the sampler replaces the patch there). **CHROM. SLOT** selects the slot, **CHROM. VOICES** the polyphony (1–8). The keyboard then plays the slot across all pitches. Sequencer tracks 1–4 can play this channel too.

**RECORDING:**
- **TARGET SLOT:** which slot to record into. An occupied slot is overwritten after confirmation; a file on the card is kept.
- **SOURCE:** LINE = line input, MIX = the board's own output (resampling, e.g. a sequencer loop).
- **LENGTH / UNIT:** 1–10 seconds or 1–10 bars at the current tempo, at most 10 s. **DURATION** shows the result.
- **START:** NOW or **BAR 1** – with the sequencer running, recording starts exactly at the next bar (display `WAITING`).
- Pressing **RECORDING** starts. During the recording the row shows `STOP xx %`; pressing stops early. Controls and sequencer keep running, and the recording has no gaps (AMY records by itself).
- Afterwards the slot is playable immediately. With UNIT BARS, TEMPO SYNC is already set to match – the recording stays in time even with later tempo changes.
- **AUTO SAVE** (default ON): right after the recording it is saved as WAV `/sd/samples/RECnnn.wav` ("Sn SAVED"), and the slot points to that file – then trimming and the waveform work too. While saving, the sound may stutter briefly (the SD card and the sample memory share one bus).
- If AUTO SAVE is OFF, the slot shows `RAM`. With **SLOT › SAVE TO SD** you can save it later, e.g. when nothing is playing. **RAM recordings are lost at power-off.**
- Saving needs a new AMYboard firmware with `tulip.store_sample` (initially from the test editor `amyboard-pr-1399`). **SD SAVE** on the RECORDING page shows YES or FW MISSING. Without suitable firmware, recordings stay in RAM only.
- **TEST INPUT:** measures for 2 s what arrives at the SOURCE: new blocks, bytes per block, **LEVEL**, free RAM and the write time of the SD card. If LINE shows 0 % level, nothing arrives at the input (check cable, level, DIP switches on the back).

**Displays:** **SAMPLE-RAM** = sample memory in use. **PADS** = how many slots can be played as pads (8/8).

### SETUP
- **RST ALL MIDI** removes the patches from all channels.
- **ENCODER:** **DEVICES** shows the detected extra devices (e.g. `M5+2QUAD`). Below that SET, DIRECTION and the overview of all connected encoders E1–E8 and Q1–Q8 (see section 1).
- **FAILSAFE** limits the CPU load. Under overload, voices are switched off instead of crackling.
- **DISPLAY:** **BRIGHTNESS** (contrast), **SAVER AFTER** (dims after 1–30 min without input; the first input only wakes it up), **UPDATE** BANDS = only send changed parts of the image (keeps the timing steady), FULL = always the whole image (if the image looks wrong).
- **CLOCK:**
  - **SEQ OUTPUT AHEAD** (default): notes are computed **LOOKAHEAD** (default 250 ms) in advance and played tick-accurately by AMY – display, encoders and saving cannot shift the timing. **DIRECT** plays immediately (for comparison only).
  - **AHEAD TEST:** one clap now, then two more, 2 beats apart each. If all three sound at once, the firmware does not schedule ahead → set SEQ OUTPUT to DIRECT.
  - **UI CLOCK TIMER** (default): the controls run on their own timer. **FALLBACK** (only with UI CLOCK LOOP) keeps the controls alive when the AMY clock stops. **TRANSPORT** OWN/AMY.
- **WLAN:** save credentials with RE-ENTER (character wheel). They are stored as plain text on the SD card (`wifi_credentials.txt`). After CONNECT, WebREPL runs (password `amyboard`).
- **MOUNT SD** remounts the SD card without a restart – e.g. after swapping cards. It tests with 32 KB; if writing fails, lower clocks and pull-ups are tried. The working setting is remembered and used at the next start. Afterwards the state including scenes is written to the card ("SD OK · SAVED" or e.g. "OK 10M"). If it fails, the message names the reason.
- **SD STATE NEW** deletes `dolphin_state.json` (with `.tmp`/`.bak`) on the card and writes the current state fresh. Settings are kept. Helps with a damaged state file.
- **SD TEST** checks step by step: writing 4 KB / 32 KB / in one go / with flush, the real state, renaming, reading. Each row shows `OK` with a time or an error number (`E5` = I/O error). If writing fails, a list of all clocks follows (20 MHz … 400 kHz) without and with pull-up (`PU`), plus CHOSEN and STATE.
- **INFO:**
  - **DISTORTION:** YES = the firmware knows the distortion commands. With NO all DISTORTION entries are hidden.
  - **DX7 SD (FM):** YES = `fm.py` is on the board, DX7 FROM SD works.
  - **TEMPO SYNC:** YES = the firmware knows the time-stretch (`fit`). With NO, TEMPO SYNC, SYNC FROM LEN and GRAIN SEARCH are hidden.
  - **MEMORY:** where the state is saved (`/sd/` or internally `/user/`).
  - **SD:** OK, REMOUNTED (remounted at startup), SWITCH (saving on the card failed) or the error reason. **SD REASON:** why the sketch last switched away from the card. **SD CLOCK:** STD or e.g. `10M PU`. **SD FREE:** free space.
  - **Statistics** (for troubleshooting): BOOT, RAM AFTER BOOT, DRAW/SEND/SEQ/SAVE/CONTROLS MAX, MISSED, LATE, TICK DEV, CV-TRIGGER. **RESET STATS** clears them.
- **FACTORY RESET** resets everything, deletes the state files in all locations and restarts. Scenes and files on the card are kept.

**Messages from MOUNT SD:**
| Message | Meaning |
|---|---|
| NO FAT32 | No readable file system – format the card as FAT32 (MBR), not exFAT |
| NO RESPONSE / MISSING | No card detected – check the seating or try another card |
| I/O ERROR | The card reports errors (EIO) |
| WRITE ERROR | Writing fails at all clocks – check card, slot or power supply |
| TMP+DIR I/O … | The test file worked, but the state did not – run SD TEST |

---

## 4. Saving

- All settings are saved **automatically**: 2.5 s after the last change, at the latest after 10 s. **While the sequencer is running**, saving waits for STOP (at the latest after 5 min) so that saving does not disturb the timing.
- Files: `dolphin_state.json` (state) and `dolphin_scenes.json` (scenes), preferably on the SD card. The state also includes the sampler's slot settings (file, trim, sound) – but not RAM recordings.
- The file is written safely (`.tmp` → main file, old file → `.bak`). A power failure never destroys the last good state.
- If the SD card reports write errors, the sketch automatically saves internally (`/user/`) and reports "SD ERROR". At startup the newest state from all locations is loaded.
- At startup all sample slots are loaded from the card in the background (display `LOADING`).
- **Before switching off:** press STOP or wait a few seconds.

The English and German editions use the same files and keys, so you can switch between them without losing settings.

---

## 5. Messages and help

| Message | Meaning / remedy |
|---|---|
| PANIC · ALL NOTES OFF | After holding 2 s on HOME |
| HIGH CPU LOAD | Fewer voices, effects or channels. Check FAILSAFE. |
| SD ERROR · SAVING /user/ | The card reports write errors. SETUP › MOUNT SD or SD TEST. |
| SAVE xxx + error text | Saving failed everywhere. Note down the text. |
| STATE · TAKEN OVER | State loaded from another location or a backup |
| NO STATE | Nothing found, starting with defaults |
| STORAGE INTERNAL · SETUP>SD NEW | No SD card was writable at startup – saving internally |
| SD OK / SD ERROR | Result of MOUNT SD (see SETUP) |
| K1 JUNO 012 · Clock Chimes | Patch changed via an extra encoder (PATCH K1–K4) |
| S1 SYNC · 2 BARS | SYNC FROM LEN applied |
| DX7 · FM.PY MISSING | The firmware has no `fm.py` – DX7 FROM SD does not work |
| DX7 · NO VOICES | The .SYX file is not a valid DX7 file |
| DX7 Kn · NOT LOADED | Saved SD voice is missing – the channel uses DX7 patch 1 |
| K1 · MUTE / ON | Channel muted/unmuted via an encoder button |
| DRUMS · 8 SLICES S1 | SPREAD TO DRUMS done |
| K1 SAMPLER · PATCH IN SAMPLER | The channel is the sampler's CHROM. channel – patch change not possible there |
| Sn IN RAM · NOT ON SD! | Recording finished but not saved (AUTO SAVE OFF or firmware without store_sample) – lost at power-off |
| Sn SAVED · RECnnn | Recording saved as WAV on the card |
| SAVE · FIRMWARE TOO OLD | Firmware without tulip.store_sample – flash a new firmware |
| WAIT FOR BAR 1 | Recording starts at the next bar |
| STILL LOADING | The slot is being loaded – wait a moment |
| 16 BIT ONLY · NO WAV · NOT PCM | The file has an unsupported format |
| NO PAD SYNTH | The slot cannot be played as a pad (PADS < 8/8) |
| 303 · TAKEN OVER | Joystick sound of the 303 kept as base values |
| EUCLID · BD 5/16 | SET EUCLID done (instrument, hits/length) |
| GRIDS · > PATTERN | Grids pattern written into the pattern, mode is now PATTERN |
| OUT1 IN USE | The output is used by MODULAR, the trigger is silent |

If a note hangs: hold 2 s on HOME (PANIC).

---

## 6. Notes on the sketch file

- `sketch.py` for the board is delivered **without comments** (~259 KB). With all comments (~323 KB) the memory was no longer enough to compile on the board. The commented English version is in the project as `claude/sketch_src_en.py` – it is meant for reading, not for uploading.
- English edition: upload `sketch_v13.19_en.py` as `sketch.py`. German edition: `sketch_v13.19.py`.
