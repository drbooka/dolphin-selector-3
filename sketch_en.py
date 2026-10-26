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
VERSION = "13.24"
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
    if n <= 1:
        return 0
    try:
        return _random.getrandbits(16) % n
    except Exception:
        return (time.ticks_us() // 7) % n
MEAS = {"draw": 0, "flush": 0, "seq": 0, "save": 0, "miss": 0, "late": 0,
        "ui": 0, "drop": 0}
TDIFF = [None, None]
def meas(k, t0):
    d = time.ticks_diff(time.ticks_us(), t0)
    if d > MEAS[k]:
        MEAS[k] = d
def meas_reset():
    for k in MEAS:
        MEAS[k] = 0
    TDIFF[0] = TDIFF[1] = None
def deep_copy(obj):
    return json.loads(json.dumps(obj))
amyboard.init_display()
try:
    if amyboard.display_rotation() != 0:
        amyboard.set_display_rotation(0)
except Exception:
    pass
display = amyboard.display
_boot_ms = now()
SPLASH_MIN_MS = 1000
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
W = 15
HI = 12
MID = 10
LO = 7
DIM = 5
GH = 2
SEL = 8
def _refresh_fw():
    try:
        amyboard.display_refresh()
    except Exception:
        try:
            display.show()
        except Exception:
            pass
BAND_ROWS = 8
BAND_BYTES = 512
BANDS = 16
FLUSH_BANDS_RUN = 2
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
    print("DISPLAY BANDS", "YES" if _fast_ok else "NO")
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
ENC_SLOTS = 16
ENC_SLOT_NAMES = (["E%d" % (i + 1) for i in range(8)]
                  + ["Q%d" % (i + 1) for i in range(8)])
PARAM_ENCODERS = []
ENC_SLOT = []
PARAM_BUTTONS = []
ENC_DEVS = []
_nq = 0
_nm = 0
_bb = 0
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
LED_PER_DEV = {"m5stack": 8, "adafruit_quad": 4, "adafruit_single": 1}
ENC_LED = []
ENC_DEVNO = []
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
    _lo += LED_PER_DEV.get(_t, 0)
del _lo, _nq, _nm
def enc_page_index(slot):
    return slot if slot < 8 else (slot - 8) % 4
try:
    encoder_count = enc.encoders if enc is not None else 0
except Exception:
    encoder_count = 0
JOY_ADDR = 0x52
JOY_DEADZONE = 0.15
JOY_Y_DEADZONE = 0.3
JOY_Y_INVERT = False
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
def sd_present():
    try:
        os.stat("/sd")
        return True
    except Exception:
        return False
try:
    amyboard.mount_sd()
except Exception as e:
    print("MOUNT SD", e)
STORE_DIRS = ("/sd/", "/user/", "/")
def _dir_writable(d, kb=4):
    probe = d + ".dolphin_probe"
    gc.collect()
    try:
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
        print("NOT WRITABLE", d, e)
        return False
SD_PINS = dict(sck=12, miso=13, mosi=11, cs=10, slot=2)
SD_FREQS = (20000000, 10000000, 5000000, 2000000, 1000000, 400000)
SD_FREQ_FILE = "/user/sd_freq.txt"
sd_freq = 0
sd_pull = False
_sd_card = None
def _sd_freq_load():
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
    try:
        from machine import Pin
        for p in (SD_PINS["miso"], SD_PINS["mosi"], SD_PINS["cs"]):
            Pin(p, Pin.IN, Pin.PULL_UP)
    except Exception as e:
        print("SD PULLUP", e)
def _sd_mount_fresh(freq=0, pull=False):
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
        try:
            amyboard.mount_sd()
        except Exception:
            pass
    return err
def _sd_cfg_txt(f, p):
    t = ("%dK" % (f // 1000)) if f and f < 1000000 else (("%dM" % (f // 1000000)) if f else "STD")
    return t + (" PU" if p else "")
_sd_boot = "OK"
_f = _sd_freq_load()
if _f is None:
    _f = (0, False)
_sd_mount_fresh(_f[0], _f[1])
time.sleep_ms(20)
if not _dir_writable("/sd/", 4):
    print("SD NOT WRITABLE AT BOOT - REMOUNTING")
    _sd_boot = "MISSING"
    _sd_mount_fresh(0, False)
    time.sleep_ms(20)
    if _dir_writable("/sd/", 4):
        _sd_boot = "REMOUNTED"
BASE = None
for _d in STORE_DIRS:
    if _dir_writable(_d):
        BASE = _d
        break
if BASE is None:
    BASE = "/sd/"
    print("NO WRITABLE LOCATION FOUND")
STATE_FILE = BASE + "dolphin_state.json"
SCENE_FILE = BASE + "dolphin_scenes.json"
STATE_TMP = STATE_FILE + ".tmp"
STATE_BAK = STATE_FILE + ".bak"
LEGACY_STATE = [d + "dolphin_state.json" for d in ("/sd/", "/user/current/", "/user/", "/")
                if d != BASE]
WLAN_CRED_FILE = "/sd/wifi_credentials.txt"
print("STATE ->", STATE_FILE)
PIANO_PATCH = 256
AMYB_PATCH = 257
DRUM_PATCH = 384
DRUM_CHANNEL = 10
DRUM_KITS = list(range(384, 391))
ALL_PATCHES = list(range(0, 256)) + [PIANO_PATCH, AMYB_PATCH] + DRUM_KITS
PATCH_POS = {}
for _i, _p in enumerate(ALL_PATCHES):
    PATCH_POS[_p] = _i
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
        return "DX7"
    return "OTHER"
FAMILY_SHORT = {"NONE": "---", "JUNO": "JUNO", "DX7": "DX7", "PIANO": "PNO",
                "AMYB": "AMYB", "DRUM": "DRUM", "OTHER": "?"}
def is_drum(p):
    return 384 <= p <= 390
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
CHORD_NAMES = ["OFF", "MAJ", "MIN", "MAJ7", "MIN7", "DOM7",
               "MAJ9", "MIN9", "ADD9", "SUS4", "FIFTH", "OCTAVE"]
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
GM_DRUM_LABELS = {35: "BD", 36: "BD", 37: "RS", 38: "SD", 39: "CP", 40: "SD",
                  41: "LF", 42: "CH", 43: "FT", 44: "PH", 45: "LT", 46: "OH",
                  47: "MT", 48: "HT", 49: "CC", 50: "HT", 51: "RC", 52: "CN",
                  53: "RB", 54: "TB", 55: "SC", 56: "CB", 57: "CC", 59: "RC",
                  60: "BO", 61: "BO", 62: "CO", 63: "CO", 64: "CO", 69: "CA",
                  70: "MA", 75: "CL", 76: "WB", 77: "WB", 58: "VS", 65: "TI",
                  66: "TI", 67: "AG", 68: "AG", 71: "WH", 72: "WH", 73: "GU",
                  74: "GU", 78: "CU", 79: "CU", 80: "TR", 81: "TR"}
GM_DRUM_NAME = {35: "KICK 2", 36: "KICK", 37: "RIM", 38: "SNARE", 39: "CLAP",
                40: "SNARE 2", 41: "TOM LF", 42: "HH CLSD", 43: "TOM FT",
                44: "HH PED", 45: "TOM LO", 46: "HH OPEN", 47: "TOM LM",
                48: "TOM HM", 49: "CRASH", 50: "TOM HI", 51: "RIDE", 52: "CHINA",
                53: "RIDE BL", 54: "TAMB", 55: "SPLASH", 56: "COWBELL",
                57: "CRASH 2", 59: "RIDE 2", 60: "BONGO H", 61: "BONGO L",
                62: "CONGA HM", 63: "CONGA HO", 64: "CONGA L", 65: "TIMBAL H",
                66: "TIMBAL L", 67: "AGOGO H", 68: "AGOGO L", 69: "CABASA",
                70: "MARACAS", 71: "WHISTL S", 72: "WHISTL L", 75: "CLAVES",
                76: "WOOD H", 77: "WOOD L", 80: "TRIANG M", 81: "TRIANG O"}
KIT_NOTES_ALL = sorted(GM_DRUM_NAME)
KIT_NOTES_808 = [n for n in KIT_NOTES_ALL if n not in (71, 72, 80, 81)]
def drum_row_label(k):
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
PROFILES = (("MANUAL", None), ("NEUTRAL", (0.0, 0.0, 0.0)),
            ("WARM", (2.0, 0.0, -2.0)), ("PUNCH", (3.0, -1.5, 2.0)),
            ("BRIGHT", (-1.0, 0.0, 3.0)))
PROFILE_NAMES = [p[0] for p in PROFILES]
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
DRUM_ROWS = 8
DRUM_DEFAULT_NOTES = (36, 38, 42, 46, 39, 45, 50, 37)
DRUM_EMPTY = "0" * SEQ_MAX_STEPS
DRUM_START = ("f000f000f000f000", "0000f0000000f000",
              "a0a0a0a0a0a0a0a0", "00000000000000c0")
HEX_DIGITS = "0123456789abcdef"
DRUM_GRID_DENS = (10, 9, 10, 7, 6, 6, 6, 6)
def new_drums():
    return {"ch": DRUM_CHANNEL, "mute": 0, "pat": 0, "div": 1, "out": 0,
            "mch": DRUM_CHANNEL, "lens": [16] * DRUM_ROWS,
            "notes": list(DRUM_DEFAULT_NOTES), "mutes": [0] * DRUM_ROWS,
            "pats": [[DRUM_EMPTY] * DRUM_ROWS for _ in range(NUM_PATTERNS)],
            "trg": [-1, -1], "tlen": 1, "tlv": 0,
            "gm": 0, "gx": 0.0, "gy": 0.0, "gz": 0,
            "gd": list(DRUM_GRID_DENS), "gcv": 0, "gj": 0,
            "smp": [-1] * DRUM_ROWS,
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
SMP_SLOTS = 8
def new_slot():
    return {"f": "", "st": 0, "en": 0, "ls": 0, "le": 0, "pm": 0,
            "tu": 0, "fi": 0, "rt": 60, "lv": 1.0, "pan": 0.5, "bus": 1,
            "at": 0, "de": 300, "su": 1.0, "re": 80,
            "ft": 0, "cu": 8000.0, "rs": 0.7, "fe": 0.0, "fd": 300,
            "sy": 0, "fs": 64,
            "nc": 0}
def new_sampler():
    return {"sl": [new_slot() for _ in range(SMP_SLOTS)],
            "ch": 0, "cs": 0, "pch": 0, "cv": 4,
            "src": 0, "len": 4, "unit": 0, "rst": 0, "rs": 0,
            "asv": 1,
            "ss": 0}
ENCB_DEFAULT = ("KONTEXT",) * 16
def new_vco():
    return {"on": 0, "src": 1, "wav": 2, "root": 24, "fine": 0, "trk": 1.0,
            "pw": 0.5, "sub": 0.0, "so": 1, "o2": 0.0, "iv": 0, "det": 7,
            "pm": 0, "sc": 0, "msrc": 0, "mt": 0, "md": 0.3,
            "ft": 0, "fd": 2.0, "fm": 1.0, "lvl": 0.8, "pan": 0.5, "bus": 0}
def new_ain():
    return {"on": 0, "mode": 0, "gain": 0.0, "lvl": 1.0, "pan": 0.5, "wid": 1.0,
            "bus": 2, "ft": 0, "cu": 8000.0, "rs": 0.7,
            "dt": 0, "dd": 4.0, "dm": 1.0}
USER_BASE = 1024
ENCF_DEFAULT = ("SCREEN", "SCREEN", "SCREEN", "SCREEN",
                "master", "lvl", "rvL", "ecL",
                "pk1", "pk2", "pk3", "pk4",
                "pk5", "pk6", "pk7", "pk8")
def new_encx():
    return {"pl": 0, "ld": 0, "led": 0}
def default_state():
    s = {
        "v": 12, "n": 0,
        "pat": [-1] * 17, "vo": [1] * 17, "bus": [0] * 17,
        "lvl": [1.0] * 17, "pan": [0.5] * 17, "mute": [0] * 17,
        "chord": [0] * 17, "porta": [0] * 17,
        "ccmap": [[] for _ in range(17)],
        "tch": [0] * 17,
        "fx": [{"rv": [0.0, 0.5, 0.5, 1000.0],
                "cho": [0.0, 0.5, 0.5, CHORUS_MAX_DELAY],
                "ech": [0.0, 250, 0.35, 0.0],
                "eq": [0.0, 0.0, 0.0], "prof": 1,
                "pfx": 0 if b == 1 else 1,
                "dst": [0, 4.0, 1.0]} for b in range(4)],
        "master": 1.0, "crush": 0, "crate": 0, "audio": 0,
        "cur": 1, "thru": 0, "mtype": 0, "inv": 0,
        "encf": list(ENCF_DEFAULT),
        "macro": ["cut", "res", "rvL", "lvl"],
        "eur": 0, "qscale": 1, "cvsrc": [0, 0], "lfo": [0, 0.5, 0.5],
        "lfof": [0, 4.0, 1.0, 0, 0.5], "envf": [0, 4.0, 1.0],
        "env": [10, 300, 0.5], "cal": [[0.0, 1.0], [0.0, 1.0]],
        "tempo": 108, "run": 0, "clock": 0, "swing": 0, "sel": 0,
        "trk": [new_track(1, 60), new_track(2, 60), new_track(3, 60),
                new_track(DRUM_CHANNEL, 36)],
        "acid": {"steps": 16, "mute": 0, "out": 0, "mch": 1, "pat": 0,
                 "pats": [deep_copy(ACID_DEFAULT_PATTERN) for _ in range(NUM_PATTERNS)],
                 "wave": 0, "cut": 400.0, "reso": 3.0, "env": 3.0, "dec": 300,
                 "acc": 0.6, "tune": 0, "lvl": 0.6, "slide": 60, "root": 36,
                 "cvacc": 0,
                 "joy": 0, "jx": 1, "jy": 3, "jd": 100,
                 "dt": 0, "dd": 4.0, "dm": 1.0},
        "drm": new_drums(),
        "sb": new_sampler(), "notlauf": 1, "transport": 0,
        "m5": 0, "fail": 4, "vbud": 24, "dim": 5, "bright": 255,
        "syx": [None] * 17, "encb": list(ENCB_DEFAULT),
        "encx": [new_encx() for _ in range(16)], "eset": 0, "esets": [None, None, None],
        "fav": [], "rec": [], "mA": 0, "mB": 1, "mx": 0.0, "cct": 0,
        "uit": 1, "dfast": 1,
        "sqm": 1, "vlf": 250,
        "vco": new_vco(),
        "ain": new_ain(),
    }
    for k, v in TONE_DEF:
        s[k] = [v] * 17
    s["pat"][1] = 0
    s["vo"][1] = 4
    s["pat"][10] = DRUM_PATCH
    s["bus"][10] = 1
    s["fx"][0]["rv"][0] = 0.12
    s["fx"][1]["prof"] = 3
    s["fx"][1]["eq"] = list(PROFILES[3][1])
    a = s["drm"]["pats"][0]
    for k in range(len(DRUM_START)):
        a[k] = DRUM_START[k] + "0" * (SEQ_MAX_STEPS - len(DRUM_START[k]))
    return s
S = default_state()
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
    _sanitize_vco()
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
_last_saved = None
_save_due = None
_save_first = None
SAVE_DELAY_MS = 2500
SAVE_MAX_MS = 10000
def request_save():
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
    print("SAVE ERROR", stage, repr(e), "->", STATE_FILE)
    try:
        toast("SAVE " + stage, (BASE + " " + str(e))[:14], 3000)
    except Exception:
        pass
WRITE_CHUNK = 512
def _write_file(path, txt):
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
        _write_file(STATE_FILE, txt)
def _write_safe(txt):
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
        print("SAVE SAFE", step, repr(e))
        return step
def _set_base(d):
    global BASE, STATE_FILE, SCENE_FILE, STATE_TMP, STATE_BAK
    BASE = d
    STATE_FILE = d + "dolphin_state.json"
    SCENE_FILE = d + "dolphin_scenes.json"
    STATE_TMP = STATE_FILE + ".tmp"
    STATE_BAK = STATE_FILE + ".bak"
_ERRNO_TXT = {1: "BUSY", 2: "MISSING", 5: "I/O ERROR", 19: "NO FAT32",
              110: "NO RESPONSE", 116: "NO RESPONSE", 12: "MEMORY"}
sd_status = _sd_boot if BASE == "/sd/" else "NOT ACTIVE"
sd_switch_err = ""
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
            return _ERRNO_TXT.get(n, "ERROR %d" % n)
    except Exception:
        pass
    return str(e)[:12] or "ERROR"
STATE_NAMES = ("dolphin_state.json", "dolphin_state.json.tmp",
               "dolphin_state.json.bak", ".dolphin_probe")
def sd_remount(clean=False):
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
                print("DELETED /sd/" + n)
            except OSError as e:
                if e.args and e.args[0] != 2:
                    sd_status = "DELETE " + _err_txt(e)
                    return False, ("DELETE " + _err_txt(e))[:14]
    good = _dir_writable("/sd/", 32)
    if not good:
        cfg = sd_find_cfg()
        good = cfg is not None
    if not good:
        sd_status = "NOT WRITABLE"
        return False, "WRITE ERROR"
    _set_base("/sd/")
    ok = save_state(force=True)
    if BASE != "/sd/":
        return False, (sd_switch_err or "SAVE ERROR")[:14]
    try:
        scenes_save()
    except Exception:
        pass
    sd_status = "OK" if ok else "SAVE ERROR"
    if ok and (sd_freq or sd_pull):
        return ok, "OK " + _sd_cfg_txt(sd_freq, sd_pull)
    return ok, "SAVED" if ok else sd_status
def _sd_cfgs():
    out = [(0, False)]
    for p in (False, True):
        for f in SD_FREQS:
            out.append((f, p))
    out.append((0, True))
    return out
def sd_find_cfg(matrix=None):
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
    try:
        i = STORE_DIRS.index(BASE) + 1
    except ValueError:
        i = 0
    while i < len(STORE_DIRS):
        d = STORE_DIRS[i]
        i += 1
        if _dir_writable(d):
            print("STORAGE CHANGED", BASE, "->", d)
            _set_base(d)
            try:
                toast("SD ERROR", "SAVING " + d[:6], 2500)
            except Exception:
                pass
            return True
    return False
def save_state(force=False):
    global _last_saved, _save_due, _save_first, _save_err, sd_switch_err, sd_status
    _save_due = None
    _save_first = None
    try:
        eset_snapshot()
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
    txt = json.dumps(S)
    ok = False
    err = None
    while True:
        step = _write_safe(txt)
        if not step:
            ok = True
            print("SAVED", len(txt), "Bytes ->", STATE_FILE)
            break
        try:
            _write_direct(txt)
            ok = True
            print("SAVED directly (safe save failed at %s)" % step)
            break
        except Exception as e:
            err = (step + "+DIR", e)
        if BASE == "/sd/":
            sd_switch_err = ("%s %s" % (err[0], _err_txt(err[1])))[:24]
            sd_status = "SWITCH"
            print("SD SAVE FAILS:", err[0], repr(err[1]))
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
SAVE_RUN_MAX_MS = 300000
def service_save():
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
_OLD_ENC = {0: "AUS", 1: "master", 2: "lvl", 3: "cut", 4: "res", 5: "pan",
            6: "att", 7: "dec", 8: "sus", 9: "rel", 10: "rvL", 11: "chL",
            12: "ecL", 13: "eqL", 14: "eqM", 15: "eqH", 16: "tempo",
            17: "SCREEN", 18: "rvV", 19: "rvD", 20: "rvX", 21: "chR",
            22: "chD", 23: "chM", 24: "ecT", 25: "ecF", 26: "ecC",
            27: "porta", 28: "acut", 29: "ares", 30: "aenv", 31: "adec",
            32: "aacc"}
def migrate_v11():
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
                raise ValueError("not an object")
        except Exception as e:
            print("LOAD", path, e)
            continue
        n = data.get("n", 0)
        try:
            n = int(n)
        except Exception:
            n = 0
        print("FOUND", path, "saved", n)
        if n > best_n:
            best, best_n, best_path = data, n, path
    if best is not None:
        try:
            S = _merge(default_state(), best)
            _migrate_pfx(best)
            sanitize()
            print("STATE FROM", best_path)
            if best_path == STATE_FILE:
                _last_saved = json.dumps(S)
                return "json"
            _last_saved = None
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
DEFAULT_VOICES = {"JUNO": 4, "DX7": 6, "PIANO": 4, "AMYB": 4}
DRUM_SYNTH_FLAGS = 1 | 2 | 8
SYNTH_QUIET_FLAGS = 8
DRUM_KIT_OSCS = 42
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
_configured = set()
def cur():
    return S["cur"]
def cur_patch():
    return S["pat"][S["cur"]]
def cur_family():
    return family(S["pat"][S["cur"]])
def kit_voices():
    return 1
def default_voices(p, ch):
    if is_drum(p):
        return kit_voices()
    return DEFAULT_VOICES.get(family(p), 4) if ch == 1 else 2
def eff_voices(ch):
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
def apply_filter(ch):
    if family(S["pat"][ch]) in FILTER_FAM:
        amy.send(synth=ch, osc=0, filter_freq=S["cut"][ch], resonance=S["res"][ch])
def apply_env(ch):
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
    return 0.00125 * (2 ** fb)
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
    if ch in _configured:
        amy.send(synth=ch, bus=S["bus"][ch])
    _configured.add(ch)
    if patch > USER_BASE:
        e = S["syx"][ch]
        if not e or _syx_done.get(ch) != (e[0], e[1]):
            if not syx_install(ch):
                patch = S["pat"][ch]
                voices = eff_voices(ch)
    amy.send(synth=ch, patch=patch, num_voices=voices, bus=S["bus"][ch])
    flags = DRUM_SYNTH_FLAGS if drum else SYNTH_QUIET_FLAGS
    amy.send(synth=ch, synth_flags=flags)
    _flags_sent[ch] = flags
    _pan_sent.pop(ch, None)
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
        try:
            amy.send(synth=ch, grab_midi_notes=0)
        except Exception:
            pass
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
    if S["pat"][ch] != p:
        reset_tone(ch)
    S["pat"][ch] = p
    if p != -1:
        S["vo"][ch] = clamp_int(default_voices(p, ch), 1, voices_allowed(ch))
    request_configure(ch)
def commit_patch(ch):
    flush_configure(True)
    p = S["pat"][ch]
    if p != -1 and p < USER_BASE:
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
_fx_bus_override = None
def fx_bus():
    if _fx_bus_override is not None:
        return _fx_bus_override
    return S["bus"][S["cur"]]
DIST_TYPES = ["OFF", "CLIP", "FOLD", "CLIP+FOLD"]
DIST_DRIVE_MIN = 1.0
DIST_DRIVE_MAX = 16.0
def dist_args(typ, drive, mix):
    if not typ:
        return {"dist_clip": 0, "dist_fold": 0, "dist_drive": 1, "dist_mix": 1}
    return {"dist_clip": 1 if typ in (1, 3) else 0,
            "dist_fold": 1 if typ in (2, 3) else 0,
            "dist_drive": round(drive, 3), "dist_mix": round(mix, 3)}
def _dist_probe():
    try:
        amy.send(bus=0, **dist_args(0, 1.0, 1.0))
        return True
    except Exception as e:
        print("DISTORTION MISSING", e)
        return False
DIST_OK = _dist_probe()
def fx_send(bus, what, force=False):
    f = S["fx"][bus]
    if what in ("cho", "eq") and f["pfx"] and not force:
        return
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
        fx_send(bus, "cho")
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
    for ch in range(1, 17):
        if S["pat"][ch] != -1 and S["bus"][ch] == bus:
            try:
                configure_channel(ch)
            except Exception as e:
                print("RELOAD", ch, e)
def active_buses():
    buses = {0}
    for ch in range(1, 17):
        if S["pat"][ch] != -1 or chrom_owns(ch):
            buses.add(S["bus"][ch])
    for sl in S["sb"]["sl"]:
        if sl["f"]:
            buses.add(sl["bus"])
    if S["vco"]["on"]:
        buses.add(S["vco"]["bus"])
    if S["ain"]["on"]:
        buses.add(S["ain"]["bus"])
    return buses
def headroom_scale():
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
    for b in active_buses():
        if b not in _fx_touched:
            _fx_touched.add(b)
            apply_bus_fx(b)
    apply_master_volume()
    apply_crush()
CRUSH_BITS = [0, 12, 10, 8, 6, 4, 3, 2]
CRUSH_RATES = [1, 2, 3, 4, 6, 8, 12, 16]
_crush_applied = {}
def apply_crush():
    bits = CRUSH_BITS[S["crush"]]
    rate = CRUSH_RATES[S["crate"]]
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
            _vco_send_out()
        except Exception as e:
            print("VCO PAN", e)
    if _ain_running:
        try:
            _ain_send_out()
        except Exception as e:
            print("AUDIO IN PAN", e)
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
EUR_MODE_VALUES = [EUR_OFF, EUR_CV1_FILTER, EUR_GATE_PITCH, EUR_MIDI_CV,
                   EUR_ACID_CV, EUR_CV1_OUT1, EUR_CV2_OUT2, EUR_QUANTIZE]
EUR_MODE_NAMES = ["OFF", "CV1>FILTER", "GATE+PITCH", "MIDI>CV",
                  "303>CV", "CV1>OUT1", "CV2>OUT2", "QUANTIZE"]
NOTE_OUTPUT_CV_NATIVE = False
NOTE_OUTPUT_OFF = getattr(amy, "NOTE_OUTPUT_OFF", 0)
NOTE_OUTPUT_CV_GATE = getattr(amy, "NOTE_OUTPUT_CV_GATE", 1)
NOTE_OUTPUT_MIDI_OUT = getattr(amy, "NOTE_OUTPUT_MIDI_OUT", 2)
_eur_mode = EUR_OFF
_eur_ch = None
_last_cv = [None, None]
cv_out_v = [0.0, 0.0]
cv_in_v = [0.0, 0.0]
cal_test = None
def cv_write(ch, volts, min_step=0.0):
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
def cv_read(ch):
    try:
        v = clamp(amyboard.cv_in(channel=ch), CV_IN_MIN, CV_IN_MAX)
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
        if fam in ("JUNO", "AMYB"):
            for o in PITCH_OSCS[fam]:
                amy.send(synth=ch, osc=o, freq={"ext1": 1})
            amy.send(cv_trigger="0,%s,%s,i%dl1n%d" % (GATE_HIGH, GATE_LOW, ch, CV_ZERO_NOTE))
        else:
            amy.send(cv_trigger="0,%s,%s,1,1.0,%.4f,i%dl1n%%v" % (
                GATE_HIGH, GATE_LOW, _cv_trigger_offset(), ch))
        amy.send(cv_trigger="0,%s,%s,i%dl0" % (GATE_LOW, GATE_HIGH, ch))
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
_last_q = None
def quantize(v, si=None):
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
    global cal_test
    cal_test = volts
    if volts is None:
        apply_eurorack_mode()
    else:
        _last_cv[0] = None
        _last_cv[1] = None
        cv_write(0, volts)
        cv_write(1, CV_GATE_VOLTS)
CVMOD_LFO_SYNTH = 20
CVMOD_ENV_SYNTH = 21
CVMOD_SOURCE_NAMES = ["OFF", "LFO", "ENV"]
CVMOD_WAVE_NAMES = ["SIN", "TRI", "SAW", "PUL"]
CVMOD_WAVE_ATTR = [("SINE", 0), ("TRIANGLE", 4), ("SAW_DOWN", 2), ("PULSE", 1)]
_cv_applied = [None, None]
_cv_synths_ready = False
TRIG_SYNTHS = (29, 30)
TRIG_FULL_V = 10.0
TRIG_AMP = 0.8
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
        amy.send(synth=CVMOD_LFO_SYNTH, num_voices=1, oscs_per_voice=1,
                 wave=_wave_const(lf[0]), freq=lf[1], amp=lf[2])
        amy.send(synth=CVMOD_ENV_SYNTH, num_voices=1, oscs_per_voice=1,
                 wave=_wave_const(0), freq=0, phase=0.25,
                 bp0="%d,1,%d,0" % (en[0], en[1]), amp=en[2])
        _cv_synths_ready = True
        cvfold_apply(True)
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
FOLD_MOD_NAMES = ["OFF", "CV IN1", "CV IN2"]
FOLD_MOD_MS = 30
_fold_sent = [None, None]
_fold_mod = 0.0
_fold_next = 0
def fold_drive_lfo():
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
    if i == 0:
        return math.sin(6.2832 * p)
    if i == 1:
        return 1.0 - 4.0 * abs(p - 0.5)
    if i == 2:
        return 1.0 - 2.0 * p
    return 1.0 if p < 0.5 else -1.0
def fold_shape(x, typ):
    if typ in (2, 3):
        t = math.fmod(x + 1.0, 4.0)
        if t < 0:
            t += 4.0
        x = t - 1.0 if t <= 2.0 else 3.0 - t
    if typ in (1, 3):
        x = clamp(x, -1.0, 1.0)
    return x
def trig_synth_setup(out):
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
VCO_WAVE_NAMES = ["SIN", "TRI", "SAW", "PULSE"]
VCO_MOD_NAMES = ["FM", "PWM", "FOLD"]
VCO_IN_NAMES = ["OFF", "IN1", "IN2"]
VCO_PM_NAMES = ["FREE", "QUANT"]
VCO_OSCS = 3
VCO_BP0 = "5,1,60,0"
VCO_FM_OCT = 1.0
VCO_PWM_PER_V = 0.08
VCO_FOLD_MS = 30
VCO_Q_HYST = 0.2
VCO_SYNTH = None
_vco_running = False
_vco_q = None
_vco_fold_mod = 0.0
_vco_fold_next = 0
_vco_fold_sent = None
def vco_init():
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
    v = S["vco"]
    return 440.0 * 2 ** ((v["root"] + semis - 69) / 12.0 + v["fine"] / 1200.0)
def _vco_ext(v):
    e = [0.0, 0.0]
    if v["src"] and not v["pm"]:
        e[v["src"] - 1] += v["trk"]
    if v["msrc"] and v["mt"] == 0:
        e[v["msrc"] - 1] += v["md"] * VCO_FM_OCT
    return e
def _vco_send_freq():
    v = S["vco"]
    semis = _vco_q if (v["pm"] and v["src"] and _vco_q is not None) else 0
    f0 = vco_hz(semis)
    e = _vco_ext(v)
    f2 = f0 * 2 ** (v["iv"] / 12.0 + v["det"] / 1200.0)
    for o, f in ((0, f0), (1, f0 / (2 ** v["so"])), (2, f2)):
        amy.send(synth=VCO_SYNTH, osc=o,
                 freq={"const": round(f, 4), "note": 0, "bend": 0,
                       "ext0": round(e[0], 4), "ext1": round(e[1], 4)})
def _vco_send_duty():
    v = S["vco"]
    d = [0.0, 0.0]
    if v["msrc"] and v["mt"] == 1:
        d[v["msrc"] - 1] = round(v["md"] * VCO_PWM_PER_V, 4)
    for o in (0, 2):
        amy.send(synth=VCO_SYNTH, osc=o,
                 duty={"const": round(v["pw"], 3), "ext0": d[0], "ext1": d[1]})
def _vco_send_wave():
    w = _wave_const(S["vco"]["wav"])
    for o in (0, 2):
        amy.send(synth=VCO_SYNTH, osc=o, wave=w)
def _vco_send_mix():
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
    global _vco_running, _vco_q, _vco_fold_sent, _vco_fold_mod
    if VCO_SYNTH is None:
        S["vco"]["on"] = 0
        toast("VCO", "NO FREE SYNTH", 1800)
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
        toast("VCO", "ERROR", 1500)
        return False
    refresh_buses()
    return True
def vco_stop():
    global _vco_running
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
    global _vco_fold_mod, _vco_fold_next
    if not _vco_running:
        return
    v = S["vco"]
    try:
        if _vco_quant():
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
    v = S["vco"]
    n = v["root"] + v["fine"] / 100.0
    if v["src"]:
        if v["pm"]:
            n += _vco_q or 0
        else:
            n += cv_in_v[v["src"] - 1] * 12.0 * v["trk"]
    if v["msrc"] and v["mt"] == 0:
        n += cv_in_v[v["msrc"] - 1] * 12.0 * v["md"] * VCO_FM_OCT
    return n
AIN_MODE_NAMES = ["STEREO", "MONO", "L ONLY", "R ONLY"]
AIN_WAVES = (getattr(amy, "AUDIO_IN0", 12), getattr(amy, "AUDIO_IN1", 13))
AIN_BP0 = "5,1,60,0"
AIN_GAIN_MIN = -24.0
AIN_GAIN_MAX = 12.0
AIN_METER_FLOOR = -48.0
AIN_CLIP = 32000
AIN_CLIP_MS = 1500
AIN_SYNTHS = None
_ain_running = False
_ain_gate = [False, False]
_ain_meter = [0.0, 0.0]
_ain_clip = [None, None]
def ain_init():
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
        g *= 0.5
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
        toast("AUDIO IN", "NO FREE SYNTH", 1800)
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
        toast("AUDIO IN", "ERROR", 1500)
        return False
    refresh_buses()
    return True
def ain_stop():
    global _ain_running
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
    S["ain"]["on"] = 0 if S["ain"]["on"] else 1
    ain_apply_all()
    toast("AUDIO IN", "ON" if _ain_running else "OFF", 700)
    request_save()
def ain_meter_read():
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
SMP_SLOTS = 8
SMP_PRESET_BASE = 1040
SMP_MAX_MS = 10000
SMP_ROOT = 60
SMP_CHUNK = 94
SD_ROOT = "/sd"
SMP_DIR = SD_ROOT + "/samples"
SMP_MODE_NAMES = ["ONESHOT", "GATE", "LOOP"]
SMP_FILT_NAMES = ["OFF", "LP", "BP", "HP", "LP24"]
SMP_FILT_VALS = [0, 1, 2, 3, 4]
for _fn, _fc in (("NOTCH", "FILTER_NOTCH"), ("PHASER", "FILTER_PHASER")):
    _fv = getattr(amy, _fc, None)
    if _fv is not None:
        SMP_FILT_NAMES.append(_fn)
        SMP_FILT_VALS.append(_fv)
SMP_SRC_NAMES = ["LINE", "MIX"]
SMP_REC_UNITS = ["SEC", "BARS"]
SMP_REC_STARTS = ["NOW", "BAR 1"]
SMP_PAD_NOTE0 = 36
SMP_BLOCK_FRAMES = 256
SMP_BLOCK_US = 1000000.0 * SMP_BLOCK_FRAMES / 44100
ZERO_HZ = 440.0
PCM_WAVE = getattr(amy, "PCM", 7)
PCM_PLAY_STOP = 0
PCM_LOOP_FOREVER = 4
from array import array
try:
    import ubinascii as _b64m
    def _b64(b):
        return _b64m.b2a_base64(b)[:-1].decode()
except ImportError:
    import binascii as _b64m
    def _b64(b):
        return _b64m.b2a_base64(b)[:-1].decode()
_xfer_send = getattr(amy, "_send_transfer_chunk", None)
SMP_XFER_SAFE = _xfer_send is not None
if _xfer_send is None:
    def _xfer_send(m):
        amy.send_raw(m)
_xfer_lock = False
def wav_info(path):
    try:
        f = open(path, "rb")
    except Exception:
        return "MISSING"
    try:
        h = f.read(12)
        if len(h) < 12 or h[0:4] != b"RIFF" or h[8:12] != b"WAVE":
            return "NO WAV"
        fmt = None
        pos = 12
        while True:
            c = f.read(8)
            if len(c) < 8:
                return "NO DATA"
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
                    return "NO FORMAT"
                tag, ch, sr, bits = fmt
                if tag != 1:
                    return "NOT PCM"
                if bits != 16:
                    return "16 BIT ONLY"
                if ch not in (1, 2):
                    return "CHANNELS?"
                return {"ch": ch, "sr": sr, "off": pos,
                        "frames": size // (2 * ch)}
            else:
                f.seek(pos + size + (size & 1))
            pos += size + (size & 1)
            if cid == b"fmt ":
                f.seek(pos)
    except Exception as e:
        return str(e)[:10] or "ERROR"
    finally:
        f.close()
def smp_list_files():
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
class SlotRT:
    def __init__(self):
        self.info = None
        self.ok = False
        self.frames = 0
        self.err = ""
        self.peaks = None
        self.pkey = None
        self.ram = False
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
        return "RAM-REC" if SRT[k].ram else "EMPTY"
    return smp_short(sl["f"])
SYNC_BEATS = [0, 1, 2, 3, 4, 6, 8, 12, 16, 20, 24, 28, 32, 36, 40]
TICKS_PER_BEAT = 48
FIT_OK = True
def sync_label(b):
    if not b:
        return "OFF"
    if b % 4:
        return "%d BEATS" % b
    n = b // 4
    return "1 BAR" if n == 1 else "%d BARS" % n
SYNC_NAMES = [sync_label(b) for b in SYNC_BEATS]
def slot_play_ms(k):
    rt = SRT[k]
    if not rt.frames:
        return 0
    i = rt.info
    sr = i["sr"] if isinstance(i, dict) and i["sr"] else 44100
    return rt.frames * 1000 // sr
def sync_suggest(k):
    ms = slot_play_ms(k)
    if not ms:
        return 0
    beats = ms * S["tempo"] / 60000.0
    best = 1
    for b in SYNC_BEATS[1:]:
        if abs(b - beats) < abs(best - beats):
            best = b
    return best
SLICE_COUNTS = [0, 4, 8, 16]
SLICE_NAMES = ["OFF", "4", "8", "16"]
PHASE_FRAMES = 8388608.0
def slot_chops(k):
    sl = slot(k)
    return sl["nc"] if sl["pm"] != 2 else 0
def slot_sync_ticks(k):
    sl = slot(k)
    if FIT_OK and sl["sy"] and sl["pm"] != 2:
        return sl["sy"] * TICKS_PER_BEAT
    return 0
def slice_subs(k):
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
        print("FIT MISSING", e)
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
    if -0.001 < semis < 0.001:
        return 0
    return ZERO_HZ * (2 ** (semis / 12.0))
def _slot_send(synth, k, chrom):
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
    amy.send(synth=synth, synth_flags=(2 | 8) if (pm == 0 and not slot_chops(k)) else 8)
    if FIT_OK:
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
    pad_configure(k, full)
    if chrom_ch() and S["sb"]["cs"] == k:
        chrom_configure(full)
def slot_play(k, vel=0.8, sched=False, part=-1):
    ps = pad_synth(k)
    if ps is None or not SRT[k].ok:
        return False
    send = snd if sched else amy.send
    nc = slot_chops(k)
    if nc:
        i = part if 0 <= part < nc else 0
        kw = {"phase": (i * SRT[k].frames // nc) / PHASE_FRAMES}
        t = slot_sync_ticks(k)
        if t:
            kw["fit"] = t * (nc - i) // nc
        send(synth=ps, osc=0, **kw)
    send(synth=ps, note=SMP_ROOT, vel=vel)
    return True
SLICE_TAG0 = 210
SMP_SLICE_NOTE0 = 44
def slice_play_now(k, pc, vel=0.8):
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
LOAD_BUDGET_US = 12000
_load_q = []
_load_job = None
_load_after = {}
_peek_after_load = None
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
        rt.err = "READ ERROR"
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
            ni = m * ch
            got = (fh.readinto(memoryview(raw)[:ni]) or 0) // 2
            if got < ni:
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
        SRT[j["k"]].err = "LOAD ERROR"
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
PEAK_COLS = 120
def slot_peaks(k, v0, v1):
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
                p = max(max(buf), -min(buf))
                pk[c] = min(255, p >> 7)
            fh.close()
        except Exception as e:
            print("PEAKS", e)
    rt.peaks = pk
    rt.pkey = key
    return pk
_rec_state = {"run": False, "gaps": 0, "last": "", "peak": -1, "blk": 0}
def _rec_frames():
    s = S["sb"]
    if s["unit"] == 1:
        ms = s["len"] * 4 * 60000 // max(20, S["tempo"])
    else:
        ms = s["len"] * 1000
    return min(SMP_MAX_MS, ms) * 44100 // 1000
SMP_SRC_AMY = (2, 1)
_nrec = {"on": False, "k": 0, "until": 0, "at": None, "frames": 0, "t0": 0}
def nrec_start():
    s = S["sb"]
    k = s["rs"]
    if _nrec["on"] or _nrec["at"] is not None:
        nrec_stop()
        return
    if _load_job is not None and _load_job["k"] == k:
        toast("RECORDING", "STILL LOADING", 1500)
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
            toast("RECORDING", "WAIT FOR BAR 1", 1500)
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
        toast("RECORDING", "AMY ERROR", 2000)
        return
    sl = slot(k)
    keep = {key: sl[key] for key in ("bus", "lv", "pan")}
    sl.clear()
    sl.update(new_slot())
    sl.update(keep)
    if s["unit"] == 1 and s["len"] * 4 in SYNC_BEATS:
        sl["sy"] = s["len"] * 4
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
        toast("RECORDING", "CANCELLED")
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
        toast("S%d IN RAM" % (k + 1), "NOT ON SD!", 2500)
    mark_dirty()
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
    fn = _store_fn()
    rt = SRT[k]
    if fn is None:
        toast("SAVE", "FIRMWARE TOO OLD", 2500)
        return False
    if not rt.ram or not rt.ok:
        return False
    rel = _rec_next_name()
    toast("SAVING S%d" % (k + 1), rel[-10:], 8000)
    render(force=True)
    gc.collect()
    try:
        fn(SMP_PRESET_BASE + k, smp_path(rel), frames=rt.frames)
    except TypeError:
        try:
            fn(SMP_PRESET_BASE + k, smp_path(rel))
        except Exception as e:
            print("STORE", repr(e))
            toast("SAVE", "ERROR " + _err_txt(e)[:6], 2500)
            return False
    except Exception as e:
        print("STORE", repr(e))
        toast("SAVE", "ERROR " + _err_txt(e)[:6], 2500)
        return False
    info = wav_info(smp_path(rel))
    if not isinstance(info, dict):
        toast("SAVE", "FILE " + str(info)[:8], 2500)
        return False
    slot(k)["f"] = rel
    rt.ram = False
    rt.info = info
    rt.peaks = None
    request_save()
    toast("S%d SAVED" % (k + 1), smp_short(rel), 2500)
    mark_dirty()
    return True
def nrec_service(tick=None):
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
            mark_dirty()
def nrec_progress():
    if not _nrec["on"]:
        return 0.0
    tot = _nrec["frames"] * 1000 // 44100 or 1
    return clamp(since(_nrec["t0"]) / tot, 0.0, 1.0)
def _peak16(b, step=8):
    try:
        a = array("h", bytes(b))
        return max(max(a), -min(a))
    except Exception:
        return 0
def rec_test():
    s = S["sb"]
    name = "get_output_buffer" if s["src"] == 1 else "get_input_buffer"
    getbuf = getattr(amy, name, None)
    res = [("SOURCE", SMP_SRC_NAMES[s["src"]])]
    if getbuf is None:
        res.append(("FUNCTION", "MISSING"))
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
    res += [("CALLS", "%d" % calls), ("NONE", "%d" % nones),
            ("NEW BLOCKS", "%d" % new), ("EXPECTED", "%d" % expect),
            ("SAME", "%d" % same), ("BYTES/BLOCK", "%d" % size),
            ("LEVEL", "%d%%" % (peak * 100 // 32767)),
            ("RAM FREE", _free_mem())]
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
SYX_DIR = SD_ROOT + "/dx7"
_fm_mod = None
_syx_done = {}
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
                print("FM MISSING", e)
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
            print("SYX NAMES", e)
    gc.collect()
    _syx_names[0] = rel
    _syx_names[1] = names
    return names
def syx_install(ch):
    e = S["syx"][ch]
    fm = fm_mod()
    try:
        if fm is None:
            raise OSError("fm.py missing")
        fm.load_syx(_syx_read(e[0]), voice=e[1], patch=USER_BASE + ch)
        _syx_done[ch] = (e[0], e[1])
        gc.collect()
        return True
    except Exception as ex:
        print("SYX LOAD", ch, ex)
        toast("DX7 K%d" % ch, "NOT LOADED", 1800)
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
SEQ_DIV_NAMES = ["1/32", "1/16", "1/8", "1/4"]
SUB_TICKS = 2
SUB_PER_32 = 3
SEQ_DIV_SUB = [3, 6, 12, 24]
SEQ_MODES = ["MANUAL", "EUCLID", "SCALE", "ARP"]
ARP_DIRS = ["UP", "DOWN", "UPDOWN", "RANDOM"]
SEQ_OUT_NAMES = ["INT", "MIDI", "BOTH"]
SEQ_CLOCK_NAMES = ["INTERNAL", "SEND", "FOLLOW"]
PATTERN_NAMES = ["A", "B", "C", "D"]
SEQ_MIDI_SYNTH_BASE = 22
ACID_SYNTH = 26
ACID_MIDI_SYNTH = 27
DRUM_MIDI_SYNTH = 28
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
DRUM_BAR = 16
DRUM_GATE_SUB = 6
TRIG_GAP_US = 1000
DRUM_VEL_CYCLE = (0, 15, 10, 6)
class RT:
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
        self.rows = None
        self.offs = []
        self.trig_off = [0, 0]
        self.poffs = []
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
                del lt[:]
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
SEQ_TAG = 201
_sched = None
_late_tick = -1
_defer = []
def snd(**kw):
    if _sched is not None:
        if _sched < _late_tick and kw.get("vel"):
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
    g = t["gate"] // SUB_TICKS
    rt.off_at = s + (g if g > 0 else 1)
_acid_ready = False
_acid_acc_applied = None
_acid_gate_v = 0.0
def acid_wave_const():
    if S["acid"]["wave"] == 1:
        return getattr(amy, "PULSE", 1)
    return getattr(amy, "SAW_DOWN", 2)
ACID_JOY_TARGETS = ["OFF", "CUTOFF", "RESO", "ENV MOD", "DECAY", "ACCENT",
                    "SLIDE", "TRANSP", "DENSITY", "DRIVE"]
_acid_mod = {}
_acid_joy_next = 0
ACID_JOY_DEAD = 0.08
def _jm(t):
    return _acid_mod.get(t, 0.0)
def acid_val(k):
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
DRUM_TRIG_NAMES = ["5V", "8V", "VELO"]
def drum_out_free(out):
    return not _cv_conflict(out) and not S["cvsrc"][out]
def _trig_io(out, volts, gap):
    if not drum_out_free(out):
        return
    if gap:
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
        ts = TRIG_SYNTHS[out]
        vel = clamp(volts / (TRIG_AMP * TRIG_FULL_V), 0.0, 1.0)
        if _sched is not None and _sched < _late_tick:
            MEAS["drop"] += 1
        else:
            if gap:
                snd_at(None if _sched is None else _sched - 1, synth=ts, vel=0)
            snd_at(_sched, synth=ts, note=60, vel=vel)
    else:
        later(_trig_io, out, volts, gap)
    rt.trig_hi[out] = True
    rt.trig_off[out] = s + d["tlen"] * SUB_PER_32
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
_grid_mod = [0.0, 0.0]
def grid_xy():
    d = S["drm"]
    return (clamp(d["gx"] + _grid_mod[0], 0.0, 1.0),
            clamp(d["gy"] + _grid_mod[1], 0.0, 1.0))
def grid_vel(k, s, z=0, xy=None):
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
    d = S["drm"]
    if d["gm"]:
        return grid_vel(k, s, 0, xy)
    return int(d["pats"][d["pat"]][k][s], 16)
def grid_freeze():
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
    d = S["drm"]
    return d["gm"] and d["gj"] and not acid_joy_active()
def joy_owned():
    return acid_joy_active() or grid_joy_active()
def _acid_joy_axis(raw):
    o = (raw - 0.5) * 2.0
    if -ACID_JOY_DEAD < o < ACID_JOY_DEAD:
        return 0.0
    o = (o - ACID_JOY_DEAD if o > 0 else o + ACID_JOY_DEAD) / (1.0 - ACID_JOY_DEAD)
    return clamp(o * S["acid"]["jd"] / 100.0, -1.0, 1.0)
def _acid_mod_apply(new):
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
    if not _acid_mod:
        toast("303", "JOYSTICK AT REST")
        return
    a = S["acid"]
    for k in ("cut", "reso", "env", "dec", "acc", "slide", "tune", "dd"):
        a[k] = acid_val(k)
    a["tune"] = clamp_int(a["tune"], -12, 12)
    _acid_mod_apply({})
    request_save()
    toast("303", "TAKEN OVER")
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
    later(_set_rows, rt, b, rows)
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
                        rt.poffs = [e for e in rt.poffs if e[0] != sk]
                        rt.poffs.append((sk, s + slice_subs(sk)))
                    elif slot(sk)["pm"]:
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
    if S["run"]:
        RTS[i].pending = p
    else:
        trk_cfg(i)["pat"] = p
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
_next_sub = None
_origin = None
_req_origin = None
_seq_slot = None
_last_tick = 0
def lookahead_subs():
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
    global _next_sub, _origin, _sched, _last_tick, _late_tick, _req_origin
    jumped = tick < _last_tick - 8
    _last_tick = tick
    if _nrec["at"] is not None:
        try:
            nrec_service(tick)
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
        return
    t0 = time.ticks_us()
    try:
        seq_process_tick(amy_tick(tick))
    except Exception as e:
        print("SEQ", e)
    meas("seq", t0)
def seq_cb_start():
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
    _origin = None
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
def midi_dispatch(m):
    global _learned, _learn_armed
    try:
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
                    slot_play(pk, m[2] / 127.0)
                elif slot(pk)["pm"]:
                    slot_stop(pk)
                return
            if (ch == S["sb"]["pch"] and SMP_SLICE_NOTE0 <= note < SMP_SLICE_NOTE0 + 16):
                k = S["sb"]["ss"]
                pc = note - SMP_SLICE_NOTE0
                if pc < slot_chops(k):
                    if on:
                        slice_play_now(k, pc, m[2] / 127.0)
                    elif slot(k)["pm"] == 1:
                        slot_stop(k)
                return
            if S["chord"][ch]:
                chord_notes(ch, note, m[2], on)
            if midicv_active_for(ch):
                midicv_note(note, on)
            arp_note(ch, note, on)
            if ch == S["cur"] and 2 in S["cvsrc"]:
                cvmod_env_note(on)
        elif typ == 0xB0:
            if m[1] == 0 and len(m) > 2:
                _bank_msb[ch] = m[2]
            if _learn_armed:
                _learn_armed = False
                _learned = (ch, m[1], S["cct"])
        elif typ == 0xC0:
            pc_sync(ch, m[1])
    except Exception as e:
        print("MIDI", e)
def _seq_ticks():
    try:
        return amy.sequencer_ticks()
    except Exception:
        return None
def ext_transport(b):
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
                seq_process_tick(t)
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
    toast("PANIC", "ALL NOTES OFF")
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
            print("SCENES FROM", path)
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
    toast("SCENE %d" % (i + 1), "SAVED" if ok else "ERROR")
def scene_recall(i):
    sc = scenes[i]
    if sc is None:
        toast("SCENE %d" % (i + 1), "EMPTY")
        return
    ain_on = S["ain"]["on"]
    dflt = default_state()
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
    toast("SCENE %d" % (i + 1), "LOADED")
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
        print("MORPH CHANNEL", e)
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
        if "drm" in A and "drm" in B:
            dr = S["drm"]
            for k in ("gx", "gy"):
                dr[k] = clamp(_lerp(A["drm"].get(k, dr[k]), B["drm"].get(k, dr[k]), x), 0.0, 1.0)
    except Exception as e:
        print("MORPH", e)
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
    fb.fill_rect(x, y, w, h, bg)
    mid = x + w // 2
    p = x + int(w * clamp(frac, 0.0, 1.0))
    if p >= mid:
        fb.fill_rect(mid, y, max(1, p - mid), h, fg)
    else:
        fb.fill_rect(p, y, mid - p, h, fg)
    fb.vline(mid, y - 1, h + 2, MID)
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
def icon(i, x, y, c):
    if i == 0:
        px, py = x, y + 12
        for k in range(1, 13):
            nx = x + 2 * k
            ny = y + 12 - int(9 * math.sin(k * 0.5236))
            LN(px, py, nx, ny, c)
            px, py = nx, ny
    elif i == 1:
        for j, h in ((0, 13), (1, 5), (2, 16)):
            VL(x + 3 + 9 * j, y + 1, 22, c)
            R(x + 9 * j, y + h, 7, 4, c)
    elif i == 2:
        cx, cy = x + 12, y + 12
        for dx, dy in ((10, 0), (7, 7), (0, 10), (-7, 7), (-10, 0), (-7, -7), (0, -10), (7, -7)):
            LN(cx + dx // 3, cy + dy // 3, cx + dx, cy + dy, c)
        R(cx - 1, cy - 1, 3, 3, c)
    elif i == 3:
        on = (1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1)
        for j in range(12):
            xx = x + (j % 4) * 6
            yy = y + 3 + (j // 4) * 7
            if on[j]:
                R(xx, yy, 5, 5, c)
            else:
                FR(xx, yy, 5, 5, c)
    elif i == 4:
        CIRC(x + 8, y + 8, 7, c)
        CIRC(x + 8, y + 8, 2, c, True)
        LN(x + 13, y + 13, x + 17, y + 20, c)
        LN(x + 17, y + 20, x + 23, y + 23, c)
    elif i == 5:
        FR(x + 8, y + 1, 15, 11, c)
        R(x + 4, y + 6, 15, 11, 0)
        FR(x + 4, y + 6, 15, 11, c)
        R(x, y + 11, 15, 12, 0)
        FR(x, y + 11, 15, 12, c)
        R(x + 3, y + 16, 9, 2, c)
    elif i == 6:
        FR(x, y + 3, 24, 18, c)
        for k, h in enumerate((2, 6, 3, 8, 5, 2, 7, 4, 2, 5)):
            VL(x + 2 + 2 * k, y + 11 - h // 2, h + 1, c)
    elif i == 7:
        CIRC(x + 12, y + 12, 7, c)
        CIRC(x + 12, y + 12, 3, c)
        for dx, dy in ((0, -10), (7, -7), (10, 0), (7, 7), (0, 10), (-7, 7), (-10, 0), (-7, -7)):
            R(x + 11 + dx, y + 11 + dy, 3, 3, c)
_dirty = True
_toast = None
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
        T("IN", 66, 1, LO)
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
            return "ON" if self.get() else "OFF"
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
        S["fx"][b]["pfx"] = 0
        fx_send(b, "cho")
    fx_send(b, "eq")
def _fx(name):
    def f():
        b = fx_bus()
        if name in ("cho", "eq") and S["fx"][b]["pfx"]:
            S["fx"][b]["pfx"] = 0
            fx_send(b, "eq" if name == "cho" else "cho")
        fx_send(b, name)
    return f
P_LVL = P("LEVEL", rCH("lvl"), 0.0, 2.0, 0.02, apply=lambda: apply_level(S["cur"]), key="lvl", short="LVL")
P_PAN = P("PAN", rCH("pan"), 0.0, 1.0, 0.02, bip=True, apply=lambda: apply_pan(S["cur"]), key="pan", short="PAN")
P_MUTE = P("MUTE", rCH("mute"), kind=BOOL, apply=_mute_changed)
P_BUS = P("BUS", rCH("bus"), 0, 3, 1, "%d", apply=_bus_changed)
P_VO = P("VOICES", rCH("vo"), 1, 8, 1, "%d", apply=_vo_changed,
         vis=lambda: cur_patch() != -1 and not is_drum(cur_patch()))
P_CHORD = P("CHORD", rCH("chord"), kind=ENUM, opts=CHORD_NAMES,
            apply=lambda: configure_channel(S["cur"]),
            vis=lambda: not is_drum(cur_patch()))
P_PORTA = P("PORTAMENTO", rCH("porta"), 0, 2000, 10, "%d", unit="ms",
            apply=lambda: apply_porta(S["cur"]), key="porta", short="PORT")
P_CUT = P("CUTOFF", rCH("cut"), 40.0, 16000.0, 1, fmtf=_hz, unit="Hz", log=True,
          apply=_tone(T_FILTER, apply_filter), key="cut", short="CUT", vis=_fam_in(FILTER_FAM))
P_RES = P("RESONANCE", rCH("res"), 0.5, 16.0, 0.1, "%.1f",
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
P_LFD = P("LFO DEPTH", rCH("lfd"), 0.0, 1.0, 0.02,
          apply=_tone(T_LFO, apply_lfo), key="lfd", short="LFOD", vis=_fam_in(LFO_FAM))
P_ALG = P("ALGORITHM", rCH("alg"), 1, 32, 1, "%d",
          apply=_tone(T_DX, apply_dx), vis=_fam_in(("DX7",)))
P_FB = P("FEEDBACK", rCH("fb"), 0, 7, 1, "%d",
         apply=_tone(T_DX, apply_dx), vis=_fam_in(("DX7",)))
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
P_ECT = P("ECHO TIME", rFX("ech", 1), 10, ECHO_MAX_DELAY_MS, 10, "%d", unit="ms", apply=_fx("ech"), key="ecT", short="ETIM")
P_ECF = P("ECHO FDBK", rFX("ech", 2), 0.0, 0.95, 0.02, apply=_fx("ech"), key="ecF", short="EFB")
P_ECC = P("ECHO FILT", rFX("ech", 3), -1.0, 1.0, 0.05, bip=True, apply=_fx("ech"), key="ecC", short="EFLT")
P_EQL = P("EQ LOW", rFX("eq", 0), -15.0, 15.0, 0.5, "%+.1f", unit="dB", bip=True, apply=_eq_changed, key="eqL", short="LOW")
P_EQM = P("EQ MID", rFX("eq", 1), -15.0, 15.0, 0.5, "%+.1f", unit="dB", bip=True, apply=_eq_changed, key="eqM", short="MID")
P_EQH = P("EQ HIGH", rFX("eq", 2), -15.0, 15.0, 0.5, "%+.1f", unit="dB", bip=True, apply=_eq_changed, key="eqH", short="HIGH")
P_PROF = P("SOUND PROFILE", kind=ENUM, opts=PROFILE_NAMES,
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
P_DST = P("TYPE", rFX("dst", 0), kind=ENUM, opts=DIST_TYPES, apply=_fx("dst"))
P_DSD = P("BUS DRIVE", rFX("dst", 1), DIST_DRIVE_MIN, DIST_DRIVE_MAX, 1, "%.1f", log=True,
          apply=_fx("dst"), key="dsD", short="DRV",
          vis=lambda: DIST_OK and S["fx"][fx_bus()]["dst"][0] != 0)
P_DSM = P("DIST MIX", rFX("dst", 2), 0.0, 1.0, 0.05, apply=_fx("dst"),
          vis=lambda: S["fx"][fx_bus()]["dst"][0] != 0)
P_MASTER = P("MASTER", rS("master"), 0.0, 2.0, 0.02, apply=apply_master_volume, key="master", short="MAST")
P_CRUSH = P("CRUSH BITS", rS("crush"), kind=ENUM,
            opts=["OFF", "12", "10", "8", "6", "4", "3", "2"], apply=apply_crush)
P_CRATE = P("CRUSH RATE", rS("crate"), kind=ENUM,
            opts=["1x", "2x", "3x", "4x", "6x", "8x", "12x", "16x"], apply=apply_crush)
P_TEMPO = P("TEMPO", rS("tempo"), 20, 300, 1, "%d", unit="BPM", apply=apply_tempo, key="tempo", short="BPM")
P_SWING = P("SWING", rS("swing"), 0, 100, 5, "%d", unit="%", key="swing", short="SWNG")
P_CLOCK = P("CLOCK", rS("clock"), kind=ENUM, opts=SEQ_CLOCK_NAMES, apply=apply_clock)
P_TRANSPORT = P("TRANSPORT", rS("transport"), kind=ENUM, opts=["OWN", "AMY"],
                apply=lambda: apply_transport())
P_M5 = P("M5 SWITCH", rS("m5"), kind=ENUM, opts=["OFF", "SEQ"])
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
    def g():
        k = _sel() if i is None else i
        rt = RTS[k]
        return rt.pending if rt.pending is not None else trk_cfg(k)["pat"]
    return g
TP_MODE = P("MODE", rT("mode"), kind=ENUM, opts=SEQ_MODES, apply=_trk_release)
TP_PAT = P("PATTERN", kind=ENUM, opts=PATTERN_NAMES, getter=_pat_get(None),
           setter=lambda v: track_set_pattern(_sel(), v))
TP_CH = P("CHANNEL", rT("ch"), 1, 16, 1, "%d", apply=_trk_release)
TP_STEPS = P("STEPS", rT("steps"), 1, SEQ_MAX_STEPS, 1, "%d", apply=_steps_changed)
TP_DIV = P("DIVISION", rT("div"), kind=ENUM, opts=SEQ_DIV_NAMES)
TP_NOTE = P("NOTE", rT("note"), 0, 127, 1, fmtf=note_name)
TP_GATE = P("GATE", rT("gate"), 1, 48, 1, "%d", unit="t")
TP_PUL = P("PULSE", rT("pul"), 0, SEQ_MAX_STEPS, 1, "%d",
           vis=lambda: S["trk"][_sel()]["mode"] == 1, apply=_steps_changed)
TP_SCALE = P("SCALE", rT("scale"), kind=ENUM, opts=SCALE_NAMES,
             vis=lambda: S["trk"][_sel()]["mode"] in (1, 2))
TP_ADIR = P("ARP DIRECTION", rT("adir"), kind=ENUM, opts=ARP_DIRS,
            vis=lambda: S["trk"][_sel()]["mode"] == 3)
TP_AOCT = P("ARP OCTAVES", rT("aoct"), 1, 3, 1, "%d", vis=lambda: S["trk"][_sel()]["mode"] == 3)
TP_AIN = P("ARP IN", rT("ain"), 1, 16, 1, "K%d", vis=lambda: S["trk"][_sel()]["mode"] == 3)
TP_LATCH = P("LATCH", rT("latch"), kind=BOOL, apply=_latch_changed,
             vis=lambda: S["trk"][_sel()]["mode"] == 3)
TP_OUT = P("OUTPUT", rT("out"), kind=ENUM, opts=SEQ_OUT_NAMES, apply=_trk_release)
TP_MCH = P("MIDI CHANNEL", rT("mch"), 1, 16, 1, "%d", apply=_trk_release,
           vis=lambda: S["trk"][_sel()]["out"] > 0)
TP_MUTE = P("MUTE", rT("mute"), kind=BOOL, apply=_trk_release)
AP_PAT = P("PATTERN", kind=ENUM, opts=PATTERN_NAMES, getter=_pat_get(ACID),
           setter=lambda v: track_set_pattern(ACID, v))
AP_WAVE = P("WAVE", rA("wave"), kind=ENUM, opts=ACID_WAVE_NAMES, apply=lambda: acid_apply("wave"))
AP_CUT = P("303 CUTOFF", rA("cut"), ACID_CUT_MIN, ACID_CUT_MAX, 1, fmtf=_hz, unit="Hz",
           log=True, apply=lambda: acid_apply("filter"), key="acut", short="303C")
AP_RESO = P("303 RESO", rA("reso"), 0.5, 8.0, 0.1, "%.1f", apply=lambda: acid_apply("filter"), key="ares", short="303R")
AP_ENV = P("303 ENV MOD", rA("env"), 0.0, 7.0, 0.1, "%.1f", apply=lambda: acid_apply("filter"), key="aenv", short="303E")
AP_DEC = P("303 DECAY", rA("dec"), 30, 2500, 10, "%d", unit="ms", apply=lambda: acid_apply("dec"), key="adec", short="303D")
AP_ACC = P("303 ACCENT", rA("acc"), 0.0, 1.0, 0.05, apply=lambda: acid_apply("filter"), key="aacc", short="303A")
AP_SLIDE = P("SLIDE", rA("slide"), 10, 500, 5, "%d", unit="ms", apply=lambda: acid_apply("slide"))
AP_TUNE = P("TUNE", rA("tune"), -12, 12, 1, "%+d")
AP_ROOT = P("ROOT NOTE", rA("root"), 24, 72, 1, fmtf=note_name)
AP_LVL = P("303 LEVEL", rA("lvl"), 0.0, 1.5, 0.02, apply=lambda: acid_apply("lvl"), key="alvl", short="303L")
AP_STEPS = P("STEPS", rA("steps"), 1, ACID_STEPS_MAX, 1, "%d")
AP_OUT = P("OUTPUT", rA("out"), kind=ENUM, opts=SEQ_OUT_NAMES, apply=lambda: seq_release(ACID))
AP_MCH = P("MIDI CHANNEL", rA("mch"), 1, 16, 1, "%d", apply=lambda: seq_release(ACID),
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
        toast("303 JOYSTICK", "BUTTON=KEEP", 1800)
    else:
        _acid_mod_apply({})
AP_JOY = P("JOYSTICK>303", rA("joy"), kind=BOOL, apply=_acid_joy_changed,
           vis=lambda: joystick_available)
AP_JX = P("JOY X", rA("jx"), kind=ENUM, opts=ACID_JOY_TARGETS,
          vis=lambda: joystick_available and S["acid"]["joy"])
AP_JY = P("JOY Y", rA("jy"), kind=ENUM, opts=ACID_JOY_TARGETS,
          vis=lambda: joystick_available and S["acid"]["joy"])
AP_JD = P("JOY DEPTH", rA("jd"), 10, 100, 5, "%d", unit="%",
          vis=lambda: joystick_available and S["acid"]["joy"])
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
def _kit_get():
    p = S["pat"][S["drm"]["ch"]]
    return p if is_drum(p) else -1
def _kit_set(p):
    if p != -1:
        set_patch(S["drm"]["ch"], p)
DP_KIT = P("DRUMKIT", kind=ENUM, opts=["---"] + list(DRUM_KIT_NAMES),
           vals=[-1] + DRUM_KITS, getter=_kit_get, setter=_kit_set)
_audition = [None, 0]
def drum_audition(note):
    d = S["drm"]
    if d["out"] == 1:
        return
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
            return
        try:
            amy.send(synth=ch, note=note, vel=0)
        except Exception:
            pass
def _sound_set(n):
    S["drm"]["notes"][DRM_UI[0]] = n
    _drm_release()
    drum_audition(n)
def _sound_vals():
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
DP_LEN = P("LENGTH", _drm_ins_ref("lens"), 1, SEQ_MAX_STEPS, 1, "%d")
DP_IMUTE = P("INSTR. MUTE", _drm_ins_ref("mutes"), kind=BOOL)
DP_PUL = P("PULSE", lambda: (DRM_UI, 1), 0, SEQ_MAX_STEPS, 1, "%d")
DP_PAT = P("PATTERN", kind=ENUM, opts=PATTERN_NAMES, getter=_pat_get(DRUM),
           setter=lambda v: track_set_pattern(DRUM, v))
DP_DIV = P("DIVISION", rD("div"), kind=ENUM, opts=SEQ_DIV_NAMES)
DP_CH = P("CHANNEL", rD("ch"), 1, 16, 1, "%d", apply=_drm_release)
DP_OUT = P("OUTPUT", rD("out"), kind=ENUM, opts=SEQ_OUT_NAMES, apply=_drm_release)
DP_MCH = P("MIDI CHANNEL", rD("mch"), 1, 16, 1, "%d", apply=_drm_release,
           vis=lambda: S["drm"]["out"] > 0)
DP_MUTE = P("TRACK MUTE", rD("mute"), kind=BOOL, apply=_drm_release)
def _trig_opts():
    return ["OFF"] + _drm_ins_names()
def _trig_changed(out):
    def f():
        drum_trig_all_off()
        cvmod_service()
        if S["drm"]["trg"][out] >= 0 and not drum_out_free(out):
            toast("OUT%d IN USE" % (out + 1), "CHECK MODULAR", 1800)
    return f
DP_TRG = [P("TRIG OUT%d" % (o + 1), (lambda o=o: (S["drm"]["trg"], o)), kind=ENUM,
            opts=_trig_opts, vals=list(range(-1, DRUM_ROWS)), apply=_trig_changed(o))
          for o in range(2)]
DP_TLEN = P("TRIG LENGTH", rD("tlen"), 1, 8, 1, "%d", unit="/32")
DP_TLV = P("TRIG LEVEL", rD("tlv"), kind=ENUM, opts=DRUM_TRIG_NAMES)
DP_GM = P("GRIDS", rD("gm"), kind=ENUM, opts=GRID_MODE_NAMES)
DP_GX = P("GRIDS X", rD("gx"), 0.0, 1.0, 0.02, key="gx", short="GRDX")
DP_GY = P("GRIDS Y", rD("gy"), 0.0, 1.0, 0.02, key="gy", short="GRDY")
DP_GZ = P("RANDOM", rD("gz"), 0, 15, 1, "%d")
DP_GDEN = P("DENSITY", _drm_ins_ref("gd"), 0, 15, 1, "%d")
DP_GD = [P("DENSITY %d" % (k + 1), (lambda k=k: (S["drm"]["gd"], k)), 0, 15, 1, "%d")
         for k in range(DRUM_ROWS)]
DP_GCV = P("CV IN1/2>XY", rD("gcv"), kind=BOOL)
DP_GJ = P("JOYSTICK>XY", rD("gj"), kind=BOOL, vis=lambda: joystick_available)
P_EUR = P("MODE", rS("eur"), kind=ENUM, opts=EUR_MODE_NAMES, vals=EUR_MODE_VALUES,
          confirm=True, apply=apply_eurorack_mode)
P_QSCALE = P("SCALE", rS("qscale"), kind=ENUM, opts=SCALE_NAMES,
             vis=lambda: S["eur"] == EUR_QUANTIZE)
P_CV1 = P("CV MOD OUT1", rL("cvsrc", 0), kind=ENUM, opts=CVMOD_SOURCE_NAMES,
          apply=lambda: cvmod_service(True))
P_CV2 = P("CV MOD OUT2", rL("cvsrc", 1), kind=ENUM, opts=CVMOD_SOURCE_NAMES,
          apply=lambda: cvmod_service(True))
P_LFOW = P("LFO WAVE", rL("lfo", 0), kind=ENUM, opts=CVMOD_WAVE_NAMES, apply=cvmod_update_lfo)
P_LFOR = P("CV LFO RATE", rL("lfo", 1), 0.05, 20.0, 1, "%.2f", unit="Hz", log=True,
           apply=cvmod_update_lfo, key="lfoR", short="CVLR")
P_LFOD = P("CV LFO DEPTH", rL("lfo", 2), 0.0, 1.0, 0.05, apply=cvmod_update_lfo, key="lfoD", short="CVLD")
P_ENVA = P("ENV ATTACK", rL("env", 0), 1, 5000, 5, "%d", unit="ms", apply=cvmod_update_env)
P_ENVR = P("ENV RELEASE", rL("env", 1), 1, 5000, 5, "%d", unit="ms", apply=cvmod_update_env)
P_ENVD = P("ENV DEPTH", rL("env", 2), 0.0, 1.0, 0.05, apply=cvmod_update_env)
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
P_LFFA = P("MOD DEPTH", rL("lfof", 4), 0.0, 1.0, 0.05,
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
def _cal_test_changed():
    set_cal_test(_CAL_TEST_V[_cal_ui[0]])
P_CAL = [
    P("OUT1 OFFSET", lambda: (S["cal"][0], 0), -0.5, 0.5, 0.002, "%+.3f", unit="V", bip=True, apply=_cal_changed),
    P("OUT1 SCALE", lambda: (S["cal"][0], 1), 0.9, 1.1, 0.001, "%.3f", apply=_cal_changed),
    P("OUT2 OFFSET", lambda: (S["cal"][1], 0), -0.5, 0.5, 0.002, "%+.3f", unit="V", bip=True, apply=_cal_changed),
    P("OUT2 SCALE", lambda: (S["cal"][1], 1), 0.9, 1.1, 0.001, "%.3f", apply=_cal_changed),
    P("TEST VOLTAGE", lambda: (_cal_ui, 0), kind=ENUM,
      opts=["OFF", "0V C1", "1V C2", "2V C3", "3V C4", "4V C5"], apply=_cal_test_changed),
]
P_MORPH = P("MORPH A>B", rS("mx"), 0.0, 1.0, 0.02, apply=request_morph, key="morph", short="MRPH")
P_MA = P("MORPH A", rS("mA"), kind=ENUM, opts=["1", "2", "3", "4", "5", "6", "7", "8"], apply=request_morph)
P_MB = P("MORPH B", rS("mB"), kind=ENUM, opts=["1", "2", "3", "4", "5", "6", "7", "8"], apply=request_morph)
P_AUDIO = P("AUDIO", rS("audio"), kind=ENUM, opts=["STEREO", "MONO"], apply=apply_audio_mode)
P_VBUD = P("VOICES MAX", rS("vbud"), 8, 64, 1, "%d")
P_FAIL = P("FAILSAFE", rS("fail"), kind=ENUM,
           opts=["OFF", "0.80", "0.85", "0.90", "0.95", "1.00"], apply=apply_failsafe)
P_INV = P("DIRECTION", rS("inv"), kind=ENUM, opts=["NORMAL", "INVERT"])
P_THRU = P("MIDI THRU", rS("thru"), kind=BOOL)
P_MTYPE = P("MIDI OUT TYP", rS("mtype"), kind=ENUM, opts=["A", "B"], apply=apply_midi_type)
P_CCT = P("LEARN TARGET", rS("cct"), kind=ENUM, opts=CC_TARGET_NAMES)
def apply_bright():
    if HAS_CONTRAST:
        display_contrast(S["bright"])
P_BRIGHT = P("BRIGHTNESS", rS("bright"), 30, 255, 15, "%d", apply=apply_bright,
             vis=lambda: HAS_CONTRAST)
P_DIM = P("SAVER AFTER", rS("dim"), kind=ENUM, vals=[0, 1, 2, 5, 10, 30],
          opts=["OFF", "1 MIN", "2 MIN", "5 MIN", "10 MIN", "30 MIN"])
def _timer_update():
    if timer_wanted():
        notlauf_start()
        apply_transport()
    else:
        apply_transport()
        notlauf_stop()
P_NOTLAUF = P("FALLBACK", rS("notlauf"), kind=ENUM, opts=["OFF", "ON"], apply=_timer_update,
              vis=lambda: not S["uit"])
P_UIT = P("UI CLOCK", rS("uit"), kind=ENUM, opts=["LOOP", "TIMER"], apply=_timer_update)
def voraus_test():
    t = _seq_ticks()
    ch = S["drm"]["ch"]
    if t is None:
        toast("AHEAD TEST", "NO TICKS")
        return
    try:
        amy.send(synth=ch, note=39, vel=1)
        amy.send(synth=ch, note=39, vel=1, ticks="%d,0,%d" % (t + 96, SEQ_TAG + 1))
        amy.send(synth=ch, note=39, vel=1, ticks="%d,0,%d" % (t + 192, SEQ_TAG + 1))
        toast("AHEAD TEST", "3 CLAPS IN TIME?", 2500)
    except Exception as e:
        toast("AHEAD TEST", str(e)[:14], 2500)
def _sqm_changed():
    if S["run"]:
        seq_stop()
        seq_start()
P_SQM = P("SEQ OUTPUT", rS("sqm"), kind=ENUM, opts=["DIRECT", "AHEAD"], apply=_sqm_changed)
P_VMS = P("LOOKAHEAD", rS("vlf"), 50, 400, 25, "%d", unit="ms", vis=lambda: S["sqm"])
P_DFAST = P("UPDATE", rS("dfast"), kind=ENUM, opts=["FULL", "BANDS"],
            vis=lambda: _fast_ok)
def rV(k):
    return lambda: (S["vco"], k)
def _vco_do(fn):
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
P_VSRC = P("1V/OCT IN", rV("src"), kind=ENUM, opts=VCO_IN_NAMES, apply=_vco_pitch_changed)
P_VPM = P("PITCH", rV("pm"), kind=ENUM, opts=VCO_PM_NAMES, apply=_vco_pitch_changed,
          vis=lambda: S["vco"]["src"] != 0)
P_VSC = P("SCALE", rV("sc"), kind=ENUM, opts=SCALE_NAMES, apply=_vco_pitch_changed,
          vis=lambda: S["vco"]["src"] != 0 and S["vco"]["pm"] != 0)
P_VROOT = P("ROOT AT 0V", rV("root"), 12, 96, 1, fmtf=note_name,
            apply=_vco_do(_vco_send_freq))
P_VFIN = P("VCO FINE", rV("fine"), -100, 100, 1, "%+d", unit="ct", bip=True,
           apply=_vco_do(_vco_send_freq), key="vfin", short="VFIN")
P_VTRK = P("V/OCT", rV("trk"), 0.95, 1.05, 0.001, "%.3f", apply=_vco_pitch_changed,
           vis=lambda: S["vco"]["src"] != 0)
P_VWAV = P("WAVE", rV("wav"), kind=ENUM, opts=VCO_WAVE_NAMES, apply=_vco_do(_vco_send_wave))
P_VPW = P("VCO PW", rV("pw"), 0.05, 0.95, 0.01, apply=_vco_do(_vco_send_duty),
          key="vpw", short="VPW", vis=lambda: S["vco"]["wav"] == 3)
P_VSUB = P("VCO SUB", rV("sub"), 0.0, 1.0, 0.02, apply=_vco_do(_vco_send_mix),
           key="vsub", short="VSUB")
P_VSO = P("SUB OCTAVE", rV("so"), kind=ENUM, opts=["-1", "-2"], vals=[1, 2],
          apply=_vco_do(_vco_send_freq), vis=lambda: S["vco"]["sub"] > 0)
P_VO2 = P("VCO OSC 2", rV("o2"), 0.0, 1.0, 0.02, apply=_vco_do(_vco_send_mix),
          key="vo2", short="VO2")
P_VIV = P("INTERVAL", rV("iv"), -24, 24, 1, "%+d", unit="st",
          apply=_vco_do(_vco_send_freq), vis=_vco_o2)
P_VDET = P("VCO DETUNE", rV("det"), 0, 50, 1, "%d", unit="ct",
           apply=_vco_do(_vco_send_freq), key="vdet", short="VDET", vis=_vco_o2)
P_VMSRC = P("MOD IN", rV("msrc"), kind=ENUM, opts=VCO_IN_NAMES, apply=_vco_mod_changed)
P_VMT = P("MOD TARGET", rV("mt"), kind=ENUM, opts=VCO_MOD_NAMES, apply=_vco_mod_changed,
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
def rI(k):
    return lambda: (S["ain"], k)
def _ain_do(fn):
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
P_AMODE = P("MODE", rI("mode"), kind=ENUM, opts=AIN_MODE_NAMES, apply=_ain_mode_changed)
P_AGAIN = P("IN GAIN", rI("gain"), AIN_GAIN_MIN, AIN_GAIN_MAX, 0.5, "%+.1f", unit="dB",
            apply=_ain_do(_ain_send_gain), key="igain", short="IGN")
P_ALVL = P("IN LEVEL", rI("lvl"), 0.0, 1.5, 0.02, apply=_ain_do(_ain_send_out),
           key="ilvl", short="ILVL")
P_APAN = P("IN PAN", rI("pan"), 0.0, 1.0, 0.02, bip=True, apply=_ain_do(_ain_send_out),
           key="ipan", short="IPAN")
P_AWID = P("WIDTH", rI("wid"), 0.0, 1.0, 0.05, apply=_ain_do(_ain_send_out),
           vis=lambda: S["ain"]["mode"] == 0)
P_ABUS = P("BUS", rI("bus"), 0, 3, 1, "%d", apply=_ain_bus_changed)
P_AFT = P("FILTER", rI("ft"), kind=ENUM, opts=SMP_FILT_NAMES, apply=_ain_do(_ain_send_filter))
P_ACU = P("IN CUTOFF", rI("cu"), 40.0, 16000.0, 1, fmtf=_hz, unit="Hz", log=True,
          apply=_ain_do(_ain_send_filter), key="icut", short="ICUT", vis=_ain_filt_on)
P_ARS = P("IN RESO", rI("rs"), 0.5, 16.0, 0.1, "%.1f", apply=_ain_do(_ain_send_filter),
          key="ires", short="IRES", vis=_ain_filt_on)
P_ADT = P("DISTORTION", rI("dt"), kind=ENUM, opts=DIST_TYPES,
          apply=_ain_do(_ain_send_dist), vis=lambda: DIST_OK)
P_ADD = P("IN DRIVE", rI("dd"), DIST_DRIVE_MIN, DIST_DRIVE_MAX, 1, "%.1f", log=True,
          apply=_ain_do(_ain_send_dist), key="idrv", short="IDRV", vis=_ain_dist_on)
P_ADM = P("DIST MIX", rI("dm"), 0.0, 1.0, 0.05, apply=_ain_do(_ain_send_dist),
          vis=_ain_dist_on)
ASSIGN_KEYS = ["master", "lvl", "pan", "cut", "res", "att", "dec", "sus", "rel",
               "lfr", "lfd", "porta", "rvL", "rvV", "rvD", "rvX", "chL", "chR",
               "chD", "chM", "ecL", "ecT", "ecF", "ecC", "eqL", "eqM", "eqH",
               "tempo", "swing", "morph", "acut", "ares", "aenv", "adec", "aacc",
               "alvl", "lfoR", "lfoD", "gx", "gy", "adrv", "dsD", "lfoF", "envF",
               "vfin", "vpw", "vsub", "vo2", "vdet", "vdrv", "vmd", "vlvl",
               "igain", "ilvl", "ipan", "icut", "ires", "idrv"]
ASSIGN_NAMES = [REG[k].label for k in ASSIGN_KEYS]
PATCH_ENC_CHANNELS = tuple(range(1, 17))
MELODIC_PATCHES = [p for p in ALL_PATCHES if not is_drum(p)]
PL_NAMES = ["ALL"] + [c[0] for c in CAT_DEFS] + ["FAVOURITES", "DRUM KITS"]
PL_FAV = len(CAT_DEFS) + 1
PL_DRUM = len(CAT_DEFS) + 2
LD_NAMES = ["INSTANT", "ON PRESS"]
_enc_pend = {}
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
    return S["cur"] if f == "pkc" else int(f[2:])
class PatchEnc:
    own_toast = True
    vis = None
    def __init__(self, ch):
        self.ch = ch
        self.label = ("PATCH K%d" % ch) if ch else "PATCH CUR"
        self.short = ("PK%d" % ch) if ch else "PKA"
    def nudge(self, d, acc=1):
        self.nudge_slot(None, d, acc)
    def nudge_slot(self, sl, d, acc=1):
        ch = self.ch or S["cur"]
        if chrom_owns(ch):
            toast("K%d SAMPLER" % ch, "PATCH IN SAMPLER", 900)
            return
        x = S["encx"][sl] if sl is not None else new_encx()
        lst = patch_list(ch, x["pl"])
        if not lst:
            toast("K%d %s" % (ch, PL_NAMES[x["pl"]][:9]), "LIST EMPTY", 900)
            return
        pend = _enc_pend.get(sl)
        p = pend[1] if (pend and pend[0] == ch) else S["pat"][ch]
        step = d * (4 if acc > 1 else 1)
        if p in lst:
            i = (lst.index(p) + step) % len(lst)
        else:
            i = 0 if d > 0 else len(lst) - 1
        np = lst[i]
        if x["ld"] and sl is not None:
            _enc_pend[sl] = (ch, np)
            toast("K%d > %03d PRESS" % (ch, np), patch_name(np)[:14], 2500)
            return
        set_patch(ch, np)
        request_save()
        mark_dirty()
        toast("K%d %s %03d" % (ch, FAMILY_SHORT[family(np)], np),
              patch_name(np)[:14], 900)
    def text(self):
        return patch_name(S["pat"][self.ch or S["cur"]])[:14]
def enc_pend_load(sl):
    pend = _enc_pend.pop(sl, None)
    if pend is None:
        return False
    ch, p = pend
    set_patch(ch, p)
    commit_patch(ch)
    toast("K%d LOADED" % ch, patch_name(p)[:14], 900)
    return True
class ChanEnc:
    own_toast = True
    vis = None
    label = "CHANNEL"
    short = "CHN"
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
ENC_NAMES = (["OFF", "PAGE", "CHANNEL"] + [REG[k].label for k in PATCH_ENC_KEYS]
             + ASSIGN_NAMES)
ENC_GROUPS = (
    ("MIXER", 4, ("master", "lvl", "pan", "porta")),
    ("SOUND", 3, ("cut", "res", "att", "dec", "sus", "rel", "lfr", "lfd")),
    ("EFFECTS", 5, ("rvL", "rvV", "rvD", "rvX", "chL", "chR", "chD", "chM",
                    "ecL", "ecT", "ecF", "ecC", "eqL", "eqM", "eqH", "dsD")),
    ("SEQ+SCENE", 4, ("tempo", "swing", "morph")),
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
    if _k not in ENC_GROUP_OF:
        ENC_GROUP_OF[_k] = 0
FUNC_NAMES = ["OFF", "PAGE", "PATCH", "CHANNEL", "PARAMETER"]
LED_NAMES = ["AUTO", "OFF", "RED", "ORANGE", "YELLOW", "GREEN", "CYAN", "BLUE",
             "PURPLE", "WHITE"]
LED_RGB = (None, (0, 0, 0), (40, 0, 0), (40, 12, 0), (32, 26, 0), (0, 36, 0),
           (0, 26, 26), (0, 0, 40), (24, 0, 34), (22, 22, 22))
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
    f = S["encf"][sl]
    fn = enc_func(f)
    if fn == 2:
        return ("PATCH CUR" if f == "pkc" else "PATCH K%s" % f[2:]) + (
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
    toast("ENCODER SET", ESET_NAMES[n], 900)
def eset_next():
    eset_switch((S["eset"] + 1) % 3)
def _encf_changed():
    resync_param_encoders()
    update_leds()
P_ENCF = [P(ENC_SLOT_NAMES[i], rL("encf", i), kind=ENUM, opts=ENC_NAMES, vals=ENC_KEYS,
            apply=_encf_changed) for i in range(ENC_SLOTS)]
ENCB_KEYS = ["AUS", "KONTEXT", "START", "TAP", "PANIC", "MUTE1", "MUTE2", "MUTE3",
             "MUTE4", "M303", "MDRM", "AIN", "ESET"]
ENCB_NAMES = ["OFF", "CONTEXT", "START/STOP", "TAP TEMPO", "PANIC (LONG)", "MUTE K1",
              "MUTE K2", "MUTE K3", "MUTE K4", "MUTE 303", "MUTE DRUMS",
              "AUDIO IN", "ENC SET >"]
P_ENCB = [P(ENC_SLOT_NAMES[i] + " BUTTON", rL("encb", i), kind=ENUM, opts=ENCB_NAMES,
            vals=ENCB_KEYS) for i in range(ENC_SLOTS)]
P_MACRO = [P("MACRO %d" % (i + 1), rL("macro", i), kind=ENUM, opts=ASSIGN_NAMES,
             vals=ASSIGN_KEYS) for i in range(4)]
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
            TC("EMPTY", 64, 60, DIM)
            return
        draw_rows(rows, self.cur, self.y0, self.n, self.rh, self.edit)
        self.draw_foot(self._sel(its))
    def draw_foot(self, it):
        y = 118
        if self.edit:
            TC("OK=ACTIVATE" if it.confirm else "TURN, OK", 64, y, DIM)
        elif it.kind == NUM:
            if it.bip:
                bipbar(3, y + 2, 120, 3, it.frac(), MID)
            else:
                bar(3, y + 2, 120, 3, it.frac(), MID)
        elif it.kind == ACT:
            TC("PRESS", 64, y, DIM)
def link(label, factory, info=None, vis=None):
    return P(label, kind=LINK, page=factory, info=info, vis=vis)
def action(label, fn, info=None, vis=None):
    return P(label, kind=ACT, act=fn, info=info, vis=vis)
def infoline(label, fn, vis=None):
    return P(label, kind=INFO, info=fn, vis=vis)
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
        TC("LONG = CANCEL", 64, 118, DIM)
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
        TC("PRESS = YES", 64, 83, 0)
        TC("LONG = NO", 64, 104, DIM)
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
        return ("DONE", "DELETE", "CANCEL")[i - n]
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
        TC("TURN, PRESS", 64, 118, DIM)
_hold_progress = 0.0
def track_label(i):
    if i == ACID:
        return "303"
    if i == DRUM:
        return "DRM"
    return "S%d" % (i + 1)
def _draw_drum_strip(x, y, n, w, h, gap):
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
                push(EditPage(p, "MACRO %d" % (self.cur + 1)))
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
            info = "NO PATCH"
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
                T("NOT ACTIVE", 3, 26, DIM)
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
        for j, lab in ((4, "STOP" if S["run"] else "START"), (5, "MENU")):
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
            self.roots = [("FAVORITES", lambda: S["fav"]), ("RECENT", lambda: S["rec"])]
            for ci in range(len(CAT_DEFS)):
                self.roots.append((CAT_DEFS[ci][0], (lambda c=ci: PATCH_CATS[c])))
            self.roots += [("OTHERS", lambda: PATCH_OTHER),
                           ("ALL JUNO", lambda: list(range(0, 128))),
                           ("ALL DX7", lambda: list(range(128, 256))),
                           ("DRUMKITS", lambda: DRUM_KITS),
                           ("DX7 FROM SD", "syx"),
                           ("NO PATCH", None)]
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
            toast("EMPTY", "")
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
            TC("CURRENT " + patch_name(self.orig)[:8], 64, 118, DIM)
        else:
            draw_title(self.roots[self.rcur][0], "%d/%d" % (self.pcur + 1, len(self.plist)))
            rows = []
            for p in self.plist:
                mark = "*" if p == self.orig else ("+" if p in S["fav"] else "")
                rows.append(("%03d %s" % (p, patch_name(p)), mark))
            draw_rows(rows, self.pcur)
            TC("OK=TAKE LONG=BK", 64, 118, DIM)
class SyxBrowser(Page):
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
            toast("DX7", "FM.PY MISSING", 2000)
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
                toast("DX7", "NO VOICES", 1500)
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
                TC("NO .SYX", 64, 56, MID)
                TC("/sd/dx7/", 64, 72, DIM)
                return
            draw_rows([(f.split("/")[-1][:-4][:14], "") for f in self.files], self.fcur)
            TC("OK=OPEN", 64, 118, DIM)
        else:
            draw_title(self.files[self.fcur].split("/")[-1][:-4][:10],
                       "%d/%d" % (self.vcur + 1, len(self.names)))
            draw_rows([("%02d %s" % (i + 1, n), "") for i, n in enumerate(self.names)],
                      self.vcur)
            TC("OK=TAKE LONG=BK", 64, 118, DIM)
def _fav_text():
    return "YES" if cur_patch() in S["fav"] else "NO"
def _unassign():
    set_patch(S["cur"], -1)
    commit_patch(S["cur"])
def channel_items():
    return [link("PATCH", PatchBrowser, info=lambda: patch_name(cur_patch())[:7]),
            P_LVL, P_PAN, P_MUTE, P_BUS, P_VO, P_CHORD, P_PORTA,
            action("FAVORITE", lambda: toggle_favorite(cur_patch()), info=_fav_text,
                   vis=lambda: -1 < cur_patch() < USER_BASE),
            action("REMOVE", _unassign, vis=lambda: cur_patch() != -1)]
def channel_page():
    return ListPage(lambda: "CHANNEL %d" % S["cur"], channel_items)
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
def _tone_reset():
    ch = S["cur"]
    reset_tone(ch)
    configure_channel(ch)
    request_save()
    toast("SOUND", "PATCH VALUES")
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
        action("LEARN", _learn, info=lambda: "WAITING" if _learn_armed else "START"),
        infoline("MAPS CHANNEL", lambda: "%d" % len(S["ccmap"][S["cur"]])),
        action("DELETE", _cc_clear)])
def klang_items():
    return [link("PATCH", PatchBrowser, info=lambda: patch_name(cur_patch())[:7]),
            P_CUT, P_RES, P_ATT, P_DEC, P_SUS, P_REL, P_LFR, P_LFD, P_ALG, P_FB,
            P_CHORD, P_PORTA, P_VO,
            action("FAVORITE", lambda: toggle_favorite(cur_patch()), info=_fav_text,
                   vis=lambda: -1 < cur_patch() < USER_BASE),
            link("CC-LEARN", cc_page),
            action("PATCH VALUES", _tone_reset, vis=lambda: S["tch"][S["cur"]] != 0)]
def klang_page():
    return ListPage(lambda: "SOUND K%d" % S["cur"], klang_items,
                    right=lambda: FAMILY_SHORT[cur_family()])
_fxb_ui = [0]
def _fx_enter(bus=None):
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
        chs.insert(0, "IN")
    return ",".join(chs)[:6] if chs else "-"
def fx_page(bus=None):
    return ListPage(lambda: "EFFECTS BUS %d" % fx_bus(), [
        P_FXBUS,
        infoline("CHANNELS", _bus_users),
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
        action("BUS RESET", lambda: push(Confirm("BUS RESET", "EFFECTS BUS %d" % fx_bus(),
                                                 "TO DEFAULT?", lambda: reset_bus_fx(fx_bus()))))],
        on_enter=lambda: _fx_enter(bus), on_leave=_fx_leave)
class SeqPage(Page):
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
    toast("COPIED", "%s > %s" % (PATTERN_NAMES[t["pat"]], PATTERN_NAMES[dst]))
def _clear_pat(i=None):
    i = S["sel"] if i is None else i
    push(Confirm("CLEAR", "PATTERN %s" % PATTERN_NAMES[trk_cfg(i)["pat"]],
                 "ALL STEPS OFF?", lambda: track_clear_pattern(i)))
def track_items():
    if S["sel"] == ACID:
        return [link("EDIT STEPS", lambda: AcidEditor()),
                AP_PAT,
                action("ACID-GENERATOR", lambda: (acid_generate(), toast("303", "NEW PATTERN"))),
                action("MUTATE", lambda: (acid_mutate(), toast("303", "3 NEW STEPS"))),
                AP_JOY, AP_JX, AP_JY, AP_JD,
                AP_WAVE, AP_CUT, AP_RESO, AP_ENV, AP_DEC, AP_ACC, AP_SLIDE,
                AP_DT, AP_DD, AP_DM,
                AP_TUNE, AP_ROOT, AP_LVL, AP_STEPS, AP_OUT, AP_MCH, AP_MUTE,
                AP_CVACC,
                action("COPY > NEXT", _copy_next),
                action("CLEAR", _clear_pat)]
    return [link("EDIT STEPS", lambda: StepEditor(),
                 vis=lambda: S["trk"][S["sel"] % 4]["mode"] == 0),
            TP_PAT, TP_MODE, TP_CH, TP_STEPS, TP_DIV, TP_NOTE, TP_GATE, TP_PUL,
            TP_SCALE, TP_ADIR, TP_AOCT, TP_AIN, TP_LATCH, TP_OUT, TP_MCH, TP_MUTE,
            action("COPY > NEXT", _copy_next,
                   vis=lambda: S["trk"][S["sel"] % 4]["mode"] == 0),
            action("CLEAR", _clear_pat, vis=lambda: S["trk"][S["sel"] % 4]["mode"] == 0)]
def track_page():
    return ListPage(lambda: "303 ACID" if S["sel"] == ACID else "TRACK %d" % (S["sel"] + 1),
                    track_items)
def seq_global_page():
    return ListPage("SEQ GLOBAL", [
        action("START/STOP", seq_toggle, info=lambda: "RUNNING" if S["run"] else "STOPPED"),
        P_TEMPO,
        action("TAP TEMPO", tap_tempo, info=lambda: "%d" % S["tempo"]),
        P_SWING, P_CLOCK, P_TRANSPORT, P_M5])
class StepEditor(Page):
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
            TC("DONE", 64, yb, 0)
        else:
            TC("DONE", 64, yb, DIM)
            v = pat[self.cur]
            T("STEP %d: %s" % (self.cur + 1, ("OFF", "25%", "50%", "75%", "100%")[v]), 3, 118, MID)
class AcidEditor(Page):
    FIELDS = ("NOTE", "OCTAVE", "ACCENT", "SLIDE")
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
            TC("DONE", 64, 70, 0)
            return
        st = pat[self.cur]
        vals = ("--" if st[0] < 0 else ACID_NOTE_LABELS[st[0]],
                "%+d" % st[1] if st[1] else "0",
                "ON" if st[2] else "OFF", "ON" if st[3] else "OFF")
        for k in range(4):
            y = 66 + k * 12
            if self.field == k:
                R(0, y - 2, 124, 11, W)
                T(self.FIELDS[k], 3, y, 0)
                TR(vals[k], 123, y, 0)
            else:
                T(self.FIELDS[k], 3, y, MID)
                TR(vals[k], 123, y, HI)
        TC("OK=FIELD LONG=BK", 64, 118, DIM)
class _AcidEncProxy:
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
DRUM_X0 = 19
DRUM_Y0 = 13
DRUM_RH = 11
def _drum_x(c):
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
        self.row = DRM_UI[0]
        self.step = min(self.step, self._len() - 1)
    def leave(self):
        request_save()
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
                    R(x, y, 5, 8, 3 + (v * 12) // 15)
                else:
                    R(x + 2, y + 3, 1, 2, GH + 2)
                if here and s == self.step:
                    FR(x - 1, y - 1, 7, 10, W)
            if muted:
                HL(DRUM_X0, y + 4, 97, DIM)
            for out in (0, 1):
                if trg[out] == r:
                    R(119 + 4 * out, y + 1, 3, 6, HI if drum_out_free(out) else GH)
            if here and PARAM_ENCODERS and not live:
                c0 = (self.step // 8) * 8 - page * 16
                HL(_drum_x(c0), y + 9, 8 * 6 + 1, LO)
        HL(0, 102, 128, GH)
        if self.menu:
            R(0, 105, 124, 11, SEL)
            T("TRACK MENU", 3, 107, 0)
            TR(">", 122, 107, 0)
        elif live:
            T("%s %d/%d" % (drum_row_label(self.row), self.step + 1, self._len()),
              1, 106, HI)
            TR("D%d" % d["gd"][self.row], 127, 106, MID)
        else:
            v = drm_get(self.row, self.step)
            T("%s %d/%d" % (drum_row_label(self.row), self.step + 1, self._len()),
              1, 106, HI)
            TR("%d%%" % ((v * 100 + 7) // 15) if v else "OFF", 127, 106, MID)
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
    toast("CLEARED", drum_row_label(k))
def _drm_len16():
    S["drm"]["lens"] = [16] * DRUM_ROWS
    request_save()
    toast("LENGTHS", "ALL 16")
def _grid_freeze_act():
    grid_freeze()
    toast("GRIDS", "> PATTERN %s" % PATTERN_NAMES[S["drm"]["pat"]])
def _grid_mode_changed():
    if S["drm"]["gm"]:
        toast("GRIDS LIVE", "E1=X E2=Y", 1500)
def grids_page():
    return ListPage("GRIDS", [
        P("MODE", rD("gm"), kind=ENUM, opts=GRID_MODE_NAMES, apply=_grid_mode_changed),
        DP_GX, DP_GY, DP_GZ, DP_INS, DP_GDEN, DP_GCV, DP_GJ,
        action("WRITE TO PATTERN", _grid_freeze_act)],
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
            toast("S%d" % (sk + 1), "EMPTY" if not slot(sk)["f"] else
                  ("NO PAD" if pad_synth(sk) is None else _slot_state(sk)), 1500)
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
           opts=lambda: ["WHOLE"] + ["%d" % (i + 1) for i in range(16)],
           vals=list(range(17)), apply=_drm_sli_changed,
           vis=lambda: S["drm"]["smp"][DRM_UI[0]] >= 0
           and slot_chops(S["drm"]["smp"][DRM_UI[0]]) > 0)
DP_SMP = P("SAMPLE", _drm_ins_ref("smp"), kind=ENUM,
           opts=lambda: ["KIT"] + ["S%d %s" % (i + 1, slot_name(i)[:5]) for i in range(SMP_SLOTS)],
           vals=list(range(-1, SMP_SLOTS)), apply=_drm_smp_changed)
def drum_menu_page():
    return ListPage(lambda: "DRUMS K%d" % S["drm"]["ch"], [
        DP_KIT, DP_INS, DP_SMP, DP_SLI, DP_SOUND, DP_NOTE, DP_LEN, DP_IMUTE, DP_PUL,
        action("SET EUCLID", _drm_euclid),
        action("CLEAR ROW", _drm_clear_row),
        link("GRIDS", grids_page, info=lambda: GRID_MODE_NAMES[S["drm"]["gm"]][:5]),
        link("CV TRIGGER", trig_page, info=_trig_info),
        DP_PAT, DP_DIV, DP_CH, DP_OUT, DP_MCH, DP_MUTE,
        action("ALL LENGTHS 16", _drm_len16),
        action("COPY > NEXT", lambda: _copy_next(DRUM)),
        action("CLEAR", lambda: _clear_pat(DRUM))])
def _vco_info():
    if VCO_SYNTH is None:
        return "MISSING"
    return "ON" if _vco_running else "OFF"
def vco_items():
    return [P_VON, P_VSRC, P_VPM, P_VSC, P_VROOT, P_VFIN, P_VTRK,
            P_VWAV, P_VPW, P_VSUB, P_VSO, P_VO2, P_VIV, P_VDET,
            P_VMSRC, P_VMT, P_VMD, P_VFT, P_VFD, P_VFM,
            P_VLVL, P_VPAN, P_VBUS]
def _vco_wave(i, p, pw):
    if i == 3:
        return 1.0 if p < pw else -1.0
    return _lfo_wave(i, p)
class VcoPage(ListPage):
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
        draw_title("VCO " + ("ON" if _vco_running else "OFF"),
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
def _ain_info():
    if AIN_SYNTHS is None:
        return "MISSING"
    return "ON" if _ain_running else "OFF"
def ain_items():
    return [P_AON, P_AMODE, P_AGAIN, P_ALVL, P_APAN, P_AWID, P_ABUS,
            link("BUS FX", lambda: fx_page(S["ain"]["bus"]),
                 info=lambda: "BUS %d" % S["ain"]["bus"]),
            P_AFT, P_ACU, P_ARS, P_ADT, P_ADD, P_ADM]
class AinPage(ListPage):
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
        draw_title("AUDIO IN", "ON" if _ain_running else "OFF")
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
            link("CALIBRATION", calib_page)])
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
    def __init__(self):
        ListPage.__init__(self, "CV LFO", [P_LFOW, P_LFOR, P_LFOD, P_LFFT, P_LFFD,
                                           P_LFFM, P_LFFS, P_LFFA])
        self.y0 = 66
        self.n = 4
        self._shown = None
    def tick(self):
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
def calib_page():
    return ListPage("CALIBRATION", P_CAL, on_leave=_calib_leave)
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
def _scene_slot_page(i):
    def store():
        if scenes[i] is not None:
            push(Confirm("SCENE %d" % (i + 1), "OVERWRITE?", "", lambda: scene_store(i)))
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
        push(Confirm("SCENE %d" % (i + 1), "DELETE?", "", lambda: scene_delete(i)))
    return ListPage("SCENE %d" % (i + 1), [
        action("LOAD", lambda: (scene_recall(i), go_home()),
               vis=lambda: scenes[i] is not None),
        action("SAVE", store),
        action("AS MORPH A", as_a, vis=lambda: scenes[i] is not None),
        action("AS MORPH B", as_b, vis=lambda: scenes[i] is not None),
        action("DELETE", delete, vis=lambda: scenes[i] is not None)])
def _slot_info(i):
    def f():
        s = "BUSY" if scenes[i] is not None else "EMPTY"
        if S["mA"] == i:
            s = "A " + s[:4]
        elif S["mB"] == i:
            s = "B " + s[:4]
        return s
    return f
def scenes_page():
    items = [link("SCENE %d" % (i + 1), (lambda i=i: _scene_slot_page(i)), info=_slot_info(i))
             for i in range(8)]
    items += [P_MORPH, P_MA, P_MB]
    return ListPage("SCENES", items)
SMP_UI = [0]
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
SP_MODE = P("MODE", _rs("pm"), kind=ENUM, opts=SMP_MODE_NAMES, apply=_mode_changed)
SP_NC = P("SLICES", _rs("nc"), kind=ENUM, opts=SLICE_NAMES, vals=SLICE_COUNTS,
          apply=_full_changed, vis=lambda: slot(_sk())["pm"] != 2)
def slices_to_drums(k):
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
    push(Confirm("TO DRUMS", "INSTR. 1-%d AND" % n, "PATTERN %s NEW?"
                 % PATTERN_NAMES[S["drm"]["pat"]], lambda: slices_to_drums(k)))
SP_SY = P("TEMPO SYNC", _rs("sy"), kind=ENUM, opts=SYNC_NAMES, vals=SYNC_BEATS,
          apply=_snd_changed, vis=lambda: FIT_OK and slot(_sk())["pm"] != 2)
SP_FS = P("GRAIN SEARCH", _rs("fs"), 0, 512, 8, "%d",
          apply=_snd_changed, vis=lambda: FIT_OK and slot(_sk())["sy"] != 0
          and slot(_sk())["pm"] != 2)
def _sync_from_len():
    k = _sk()
    b = sync_suggest(k)
    if not b:
        toast("S%d" % (k + 1), "NOT LOADED")
        return
    slot(k)["sy"] = b
    slot_refresh(k)
    request_save()
    toast("S%d SYNC" % (k + 1), sync_label(b))
SP_TU = P("TUNE", _rs("tu"), -24, 24, 1, "%+d", unit="HT", apply=_snd_changed)
SP_FI = P("FINE", _rs("fi"), -50, 50, 1, "%+d", unit="ct", apply=_snd_changed)
SP_RT = P("ROOT NOTE", _rs("rt"), 24, 96, 1, fmtf=note_name, apply=_snd_changed)
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
SP_RS = P("RESONANCE", _rs("rs"), 0.5, 16.0, 0.1, "%.1f", apply=_snd_changed,
          vis=lambda: slot(_sk())["ft"] != 0)
SP_FE = P("F-ENV", _rs("fe"), -6.0, 6.0, 0.1, "%+.1f", unit="oct", bip=True,
          apply=_snd_changed, vis=lambda: slot(_sk())["ft"] != 0)
SP_FD = P("F-DECAY", _rs("fd"), 10, 5000, 10, "%d", unit="ms", apply=_snd_changed,
          vis=lambda: slot(_sk())["ft"] != 0)
def _slot_state(k):
    rt = SRT[k]
    if slot_loading(k) or k in _load_q or k in _load_after:
        return "LOADING"
    if _nrec["on"] and _nrec["k"] == k:
        return "REC..."
    if _nrec["at"] is not None and _nrec["k"] == k:
        return "WAITING"
    if rt.err:
        return rt.err[:7]
    if not slot(k)["f"]:
        return "RAM" if rt.ram else "EMPTY"
    return smp_short(slot(k)["f"], 7)
def _slot_play_act():
    k = _sk()
    if not SRT[k].ok:
        toast("S%d" % (k + 1), _slot_state(k))
    elif not slot_play(k):
        toast("S%d" % (k + 1), "NO PAD SYNTH")
def _slot_clear_act():
    k = _sk()
    push(Confirm("SLOT %d" % (k + 1), "CLEAR?", "FILE IS KEPT", lambda: slot_clear(k)))
def slot_page(k):
    def enter():
        SMP_UI[0] = k
    return ListPage(lambda: "SLOT %d" % (SMP_UI[0] + 1), [
        link("FILE", lambda: FileBrowser(SMP_UI[0]), info=lambda: _slot_state(SMP_UI[0])),
        link("WAVEFORM", lambda: SampleEditPage(SMP_UI[0]),
             vis=lambda: isinstance(SRT[SMP_UI[0]].info, dict)),
        action("LISTEN", _slot_play_act),
        action("SAVE TO SD", lambda: slot_store(SMP_UI[0]),
               vis=lambda: SRT[SMP_UI[0]].ram and SRT[SMP_UI[0]].ok),
        SP_MODE, SP_NC,
        action("SPREAD TO DRUMS", _slices_to_drums_act,
               vis=lambda: slot_chops(SMP_UI[0]) > 0),
        SP_SY,
        action("SYNC FROM LEN", _sync_from_len,
               info=lambda: sync_label(sync_suggest(SMP_UI[0])),
               vis=lambda: FIT_OK and slot(SMP_UI[0])["pm"] != 2 and SRT[SMP_UI[0]].ok),
        SP_FS, SP_TU, SP_FI, SP_RT, SP_LV, SP_PAN, SP_BUS,
        SP_AT, SP_DE, SP_SU, SP_RE,
        SP_FT, SP_CU, SP_RS, SP_FE, SP_FD,
        action("RELOAD", lambda: slot_request_load(SMP_UI[0], audition=True),
               vis=lambda: bool(slot(SMP_UI[0])["f"])),
        action("CLEAR", _slot_clear_act,
               vis=lambda: bool(slot(SMP_UI[0])["f"]) or SRT[SMP_UI[0]].ram)],
        on_enter=enter,
        right=lambda: _ms_txt(slot_region(SMP_UI[0])[1] - slot_region(SMP_UI[0])[0])
        if SRT[SMP_UI[0]].ok else "")
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
        draw_title("FILE S%d" % (self.k + 1),
                   "%d/%d" % (self.cur + 1, len(self.files)) if self.files else "")
        if not self.files:
            TC("NO WAV", 64, 56, MID)
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
        TC("OK=LOAD LONG=BK", 64, 118, DIM)
SE_FIELDS = ("START", "END", "LOOP A", "LOOP B", "ZOOM", "LISTEN")
SE_ZOOMS = (1, 8, 64)
_ACC_MUL = {1: 1, 2: 2, 3: 4, 6: 16}
WX0 = 4
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
            T("LOADING", 3, 118, DIM)
        else:
            T("LEN " + _ms_txt(en - st), 3, 118, DIM)
        TR("OK=EDIT" if self.cur < 4 and not self.edit else "", 125, 118, DIM)
def _slot_play_k(k):
    SMP_UI[0] = k
    _slot_play_act()
def _sb_ref(key):
    return lambda: (S["sb"], key)
SR_SLOT = P("TARGET SLOT", _sb_ref("rs"), kind=ENUM,
            opts=lambda: ["S%d %s" % (i + 1, slot_name(i)[:5]) for i in range(SMP_SLOTS)])
SR_SRC = P("SOURCE", _sb_ref("src"), kind=ENUM, opts=SMP_SRC_NAMES)
SR_LEN = P("LENGTH", _sb_ref("len"), 1, 10, 1, "%d")
SR_UNIT = P("UNIT", _sb_ref("unit"), kind=ENUM, opts=SMP_REC_UNITS)
SR_START = P("START", _sb_ref("rst"), kind=ENUM, opts=SMP_REC_STARTS)
def _rec_act():
    k = S["sb"]["rs"]
    if _nrec["on"] or _nrec["at"] is not None:
        nrec_stop()
    elif slot(k)["f"] or SRT[k].ram:
        push(Confirm("SLOT %d" % (k + 1), "OVERWRITE?", "(FILE IS KEPT)", nrec_start))
    else:
        nrec_start()
def _rec_info():
    if _nrec["at"] is not None:
        return "WAITING"
    if _nrec["on"]:
        return "STOP %d%%" % int(nrec_progress() * 100)
    return "REC"
def rec_page():
    return ListPage("RECORDING", [
        SR_SLOT, SR_SRC, SR_LEN, SR_UNIT, SR_START,
        infoline("DURATION", lambda: _ms_txt(_rec_frames() * 1000 // 44100)),
        action("RECORDING", _rec_act, info=_rec_info),
        P("AUTO SAVE", _sb_ref("asv"), kind=BOOL),
        infoline("SD SAVE", lambda: "YES" if _store_fn() else "FW MISSING"),
        action("TEST INPUT", _rec_test_act)])
def _rec_test_act():
    toast("INPUT", "MEASURING 2 S...", 4000)
    render(force=True)
    res = rec_test()
    toast("INPUT", "DONE", 500)
    push(ListPage("INPUT TEST", [infoline(n, (lambda r=r: r)) for n, r in res]))
def _ch_opts():
    return ["OFF"] + ["%d" % c for c in range(1, 17)]
def _pch_set(v):
    old = S["sb"]["pch"]
    S["sb"]["pch"] = v
    try:
        if old and old != v:
            amy.send(synth=old, grab_midi_notes=1)
        if v:
            amy.send(synth=v, grab_midi_notes=0)
    except Exception as e:
        print("PAD CHANNEL", e)
SM_CH = P("CHROM. CHANNEL", kind=ENUM, opts=_ch_opts, getter=lambda: S["sb"]["ch"],
          setter=chrom_set)
SM_CS = P("CHROM. SLOT", _sb_ref("cs"), kind=ENUM,
          opts=lambda: ["S%d %s" % (i + 1, slot_name(i)[:5]) for i in range(SMP_SLOTS)],
          apply=lambda: chrom_configure(), vis=lambda: bool(S["sb"]["ch"]))
SM_CV = P("CHROM. VOICES", _sb_ref("cv"), 1, 8, 1, "%d",
          apply=lambda: chrom_configure(), vis=lambda: bool(S["sb"]["ch"]))
SM_PCH = P("PAD CHANNEL", kind=ENUM, opts=_ch_opts, getter=lambda: S["sb"]["pch"],
           setter=_pch_set)
SM_SS = P("SLICE-SLOT", _sb_ref("ss"), kind=ENUM,
          opts=lambda: ["S%d %s" % (i + 1, ("%d" % slot_chops(i)) if slot_chops(i) else "-")
                        for i in range(SMP_SLOTS)],
          vis=lambda: bool(S["sb"]["pch"]))
def sampler_page():
    items = [link("S%d" % (i + 1), (lambda i=i: slot_page(i)),
                  info=(lambda i=i: _slot_state(i))) for i in range(SMP_SLOTS)]
    items += [link("RECORDING", rec_page),
              SM_CH, SM_CS, SM_CV, SM_PCH, SM_SS,
              infoline("SAMPLE-RAM", lambda: "%dK" % smp_ram_kb()),
              infoline("PADS", lambda: "%d/%d" % (len(PAD_SYNTHS), SMP_SLOTS))]
    return ListPage("SAMPLER", items)
def _rst_midi():
    push(Confirm("RST ALL MIDI", "ALL PATCHES", "REMOVE?",
                 lambda: (reset_all_midi(), toast("MIDI", "ALL REMOVED"))))
def midi_setup_page():
    return ListPage("MIDI", [P_THRU, P_MTYPE, P_CLOCK, action("RST ALL MIDI", _rst_midi)])
def encb_page():
    return ListPage("BUTTONS", [P_ENCB[sl] for sl in ENC_SLOT])
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
            return [("I2C ERROR", str(e)[:7])]
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
        rows.append(("NO DEVICES", ""))
    return rows
def i2c_scan_page():
    toast("I2C", "SCANNING...", 3000)
    render(force=True)
    rows = i2c_scan_rows()
    items = [infoline("SKETCH USES", lambda: "+".join(ENC_DEVS)[:7] if ENC_DEVS else "-")]
    items += [infoline(n, (lambda v=v: v)) for n, v in rows]
    toast("I2C", "%d DEVICES" % len(rows), 600)
    return ListPage("I2C-SCAN", items)
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
        toast("BUTTON", "NOW CONTEXT", 1200)
    if not S["encx"][sl]["ld"]:
        _enc_pend.pop(sl, None)
def _is_fn(fn):
    return lambda: enc_func(S["encf"][_eu()]) == fn
EP_FUNC = P("FUNCTION", kind=ENUM, opts=FUNC_NAMES, vals=list(range(5)),
            getter=lambda: enc_func(S["encf"][_eu()]), setter=_func_set)
EP_CH = P("CHANNEL", kind=ENUM, opts=["CURRENT"] + ["K%d" % c for c in PATCH_ENC_CHANNELS],
          vals=PATCH_ENC_KEYS, getter=lambda: S["encf"][_eu()], setter=_enc_set_f,
          vis=_is_fn(2))
EP_PL = P("LIST", lambda: (S["encx"][_eu()], "pl"), kind=ENUM, opts=PL_NAMES,
          apply=lambda: _enc_pend.pop(_eu(), None), vis=_is_fn(2))
EP_LD = P("LOAD", lambda: (S["encx"][_eu()], "ld"), kind=ENUM, opts=LD_NAMES,
          apply=_ld_changed, vis=_is_fn(2))
EP_GRP = P("GROUP", kind=ENUM, opts=ENC_GROUP_NAMES, vals=list(range(len(ENC_GROUPS))),
           getter=lambda: ENC_GROUP_OF.get(S["encf"][_eu()], 0), setter=_grp_set,
           vis=_is_fn(4))
EP_PAR = P("VALUE", kind=ENUM,
           opts=lambda: [REG[k].label for k in
                         enc_group_keys(ENC_GROUP_OF.get(S["encf"][_eu()], 0))],
           vals=lambda: enc_group_keys(ENC_GROUP_OF.get(S["encf"][_eu()], 0)),
           getter=lambda: S["encf"][_eu()], setter=_enc_set_f, vis=_is_fn(4))
EP_BTN = P("BUTTON", lambda: (S["encb"], _eu()), kind=ENUM, opts=ENCB_NAMES,
           vals=ENCB_KEYS)
EP_LED = P("LED", lambda: (S["encx"][_eu()], "led"), kind=ENUM, opts=LED_NAMES,
           apply=lambda: update_leds(), vis=lambda: bool(ENC_LED))
def _enc_now():
    f = S["encf"][_eu()]
    prm = REG.get(f)
    return prm.text()[:9] if prm is not None and hasattr(prm, "text") else "-"
def enc_items():
    return [EP_FUNC, EP_CH, EP_PL, EP_LD, EP_GRP, EP_PAR,
            infoline("NOW", _enc_now, vis=lambda: enc_func(S["encf"][_eu()]) >= 2),
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
        items = [infoline("DEVICES", _devs_text), P_ESET, P_INV]
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
            items.append(infoline("NO EXTRA ENC", lambda: ""))
        items.append(link("I2C-SCAN", i2c_scan_page))
        ListPage.__init__(self, "ENCODER", items)
    def enc_jump(self, sl):
        if sl in self._row and not self.edit:
            self.cur = self._row[sl]
def _devs_text():
    if not ENC_DEVS:
        return "NONE"
    nq = ENC_DEVS.count("QUAD")
    t = "M5" if "M5" in ENC_DEVS else ""
    if nq:
        t += ("+" if t else "") + ("%dQUAD" % nq if nq > 1 else "QUAD")
    return t
def encoder_page():
    return EncOverviewPage()
def _wifi_new():
    if not sd_present():
        toast("WLAN", "SD CARD MISSING")
        return
    def got_pw(ssid):
        def f(pw):
            toast("WLAN", "SAVED" if wifi_save(ssid, pw) else "ERROR")
        return f
    push(TextEntry("SSID", lambda ssid: push(TextEntry("PASSWORD", got_pw(ssid), True))))
def _wifi_conn():
    toast("WLAN", "CONNECTING...", 3000)
    render(force=True)
    ok = wifi_connect()
    toast("WLAN", str(wlan_ip) if ok else "ERROR")
def wlan_page():
    return ListPage("WLAN", [
        infoline("STATUS", lambda: "CONN." if wlan_connected else "DISC."),
        infoline("IP", lambda: str(wlan_ip)[:12] if wlan_ip else "-", vis=lambda: wlan_connected),
        infoline("NETWORK", lambda: (wifi_load()[0] or "-")[:7]),
        action("CONNECT", _wifi_conn),
        action("RE-ENTER", _wifi_new),
        action("DISCONNECT", lambda: (wifi_disconnect(), toast("WLAN", "DISCONNECTED")))])
def takt_page():
    return ListPage("CLOCK", [
        P_SQM, P_VMS,
        action("AHEAD TEST", voraus_test, info=lambda: "CLAP"),
        infoline("LOOKAHEAD STEPS", lambda: "%d/32" % (lookahead_subs() // SUB_PER_32),
                 vis=lambda: S["sqm"]),
        P_UIT, P_NOTLAUF, P_TRANSPORT,
        infoline("UI RUNS", lambda: "TIMER" if ui_timer_mode() else "LOOP"),
        infoline("SEQ CLOCK", lambda: "FINE" if _seq_slot is not None else "LOOP"),
        infoline("FALLBACK", lambda: ("ON" if _notlauf_timer is not None else
                                     ("MISSING" if S["notlauf"] else "OFF")),
                 vis=lambda: not S["uit"]),
        infoline("LOOP", lambda: "STOPPED" if _notlauf_active else "OK",
                 vis=lambda: not S["uit"]),
        infoline("APPLY", lambda: "%d" % min(_notlauf_count, 99999),
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
        infoline("EXTRAS", lambda: "%d" % len(PARAM_ENCODERS)),
        infoline("JOYSTICK", lambda: "YES" if joystick_available else "NO"),
        infoline("DISTORTION", lambda: "YES" if DIST_OK else "NO"),
        infoline("TEMPO SYNC", lambda: "YES" if FIT_OK else "NO"),
        infoline("VCO SYNTH", lambda: "%d" % VCO_SYNTH if VCO_SYNTH else "MISSING"),
        infoline("AUDIO IN", lambda: "%d/%d" % AIN_SYNTHS if AIN_SYNTHS else "MISSING"),
        infoline("DX7 SD (FM)", lambda: "YES" if fm_mod() else "NO"),
        link("I2C", i2c_scan_page, info=_i2c_count),
        infoline("RAM FREE", _free_mem),
        infoline("LAST", lambda: "%d%%" % int(cpu_load * 100)),
        infoline("VOICES", lambda: "%d/%d" % (voices_total(), S["vbud"])),
        infoline("MEMORY", lambda: BASE),
        infoline("SD", lambda: sd_status[:10]),
        infoline("SD REASON", lambda: sd_switch_err[:9], vis=lambda: bool(sd_switch_err)),
        infoline("SD CLOCK", lambda: _sd_cfg_txt(sd_freq, sd_pull)),
        infoline("SD FREE", lambda: ("%dM" % (sd_free_kb() // 1024)) if sd_free_kb() >= 0 else "?"),
        infoline("SAVE ERROR", lambda: _save_err[:6] if _save_err else "NONE"),
        infoline("LINE/ELL", lambda: "%s/%s" % ("J" if HAS_LINE else "N", "J" if HAS_ELLIPSE else "N")),
        infoline("BOOT", lambda: "%.1fs" % (_boot_dur_ms / 1000.0)),
        infoline("RAM AFTER BOOT", lambda: "%dK" % (_ram_boot // 1024)),
        infoline("DISPLAY", lambda: ("BANDS" if (_fast_ok and S["dfast"]) else "FULL")),
        infoline("DRAW MAX", lambda: "%dms" % (MEAS["draw"] // 1000)),
        infoline("SEND MAX", lambda: "%dms" % (MEAS["flush"] // 1000)),
        infoline("SEQ MAX", lambda: "%dms" % (MEAS["seq"] // 1000)),
        infoline("SAVE MAX", lambda: "%dms" % (MEAS["save"] // 1000)),
        infoline("MISSED", lambda: "%d" % min(MEAS["miss"], 99999)),
        infoline("LATE", lambda: "%d/%d" % (min(MEAS["late"], 9999), min(MEAS["drop"], 9999))),
        infoline("TICK DEV", lambda: ("-" if TDIFF[0] is None else
                                      "%d/%d" % (TDIFF[0], TDIFF[1]))[:7]),
        infoline("CV-TRIGGER", lambda: "/".join(["AMY" if trig_native(o) else
                                                  ("PY" if S["drm"]["trg"][o] >= 0 else "-")
                                                  for o in (0, 1)])),
        infoline("CONTROLS MAX", lambda: "%dms" % (MEAS["ui"] // 1000)),
        action("RESET STATS", lambda: (meas_reset(), toast("STATS", "RESET")))])
def factory_reset():
    try:
        notlauf_stop()
        seq_cb_stop()
    except Exception:
        pass
    for base in ("/sd/", "/user/current/", "/user/", "/"):
        for n in STATE_NAMES:
            try:
                os.remove(base + n)
            except Exception:
                pass
    try:
        d = default_state()
        d["n"] = S.get("n", 0) + 1
        f = open(STATE_FILE, "w")
        f.write(json.dumps(d))
        f.close()
    except Exception as e:
        print("RESET", e)
    display.fill(0)
    TC("FACTORY RESET", 64, 56, W)
    refresh()
    time.sleep_ms(800)
    try:
        import machine
        machine.reset()
    except Exception as e:
        print("RESET", e)
def _sd_remount_act(clean=False):
    toast("SD CARD", "CHECKING...", 5000)
    render(force=True)
    ok, txt = sd_remount(clean)
    toast("SD OK" if ok else "SD ERROR", txt, 2500 if ok else 4000)
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
    res.append(("CLOCK", ("%dMHZ" % (sd_freq // 1000000)) if sd_freq else "STANDARD"))
    res.append(("JSON KB", "%d" % (len(js) // 1024)))
    _sd_step(res, "LISTDIR", lambda: os.listdir("/sd"))
    _sd_step(res, "W 4K", lambda: _w_chunks(d + "t_4k.bin", blk * 8))
    _sd_step(res, "W 32K", lambda: _w_chunks(d + "t_32k.bin", blk * 64))
    _sd_step(res, "W 32K IN ONE", lambda: _w_chunks(d + "t_32k1.bin", blk * 64, 32768))
    _sd_step(res, "W 4K+FLUSH", lambda: _w_chunks(d + "t_4kf.bin", blk * 8, 512, True))
    _sd_step(res, "W JSON", lambda: _w_chunks(d + "t_state.json", js))
    _sd_step(res, "W JSON+FLUSH", lambda: _w_chunks(d + "t_statf.json", js, 512, True))
    _sd_step(res, "W STATE.TMP", lambda: _w_chunks(STATE_TMP if BASE == d else d + "dolphin_state.json.tmp", js))
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
            raise Exception("DATA WRONG")
    _sd_step(res, "READ 32K", _rd)
    for n in ("t_4k.bin", "t_32k.bin", "t_32k1.bin", "t_4kf.bin", "t_state.json",
              "t_statf.json", "t_a.bin", "t_b.bin"):
        try:
            os.remove(d + n)
        except Exception:
            pass
    res.append(("FREE", ("%dM" % (sd_free_kb() // 1024)) if sd_free_kb() >= 0 else "?"))
    gc.collect()
    return res
def _sd_test_act():
    toast("SD TEST", "RUNNING...", 20000)
    render(force=True)
    res = sd_test()
    if any(r[1].startswith("E") for r in res):
        toast("SD TEST", "TRY CLOCKS", 20000)
        render(force=True)
        m = []
        found = sd_find_cfg(m)
        res.append(("-- CLK/PULLUP --", ""))
        res += m
        res.append(("CHOSEN", _sd_cfg_txt(found[0], found[1]) if found else "NONE"))
        if found is not None:
            ok, txt = sd_remount()
            res.append(("STATE", txt[:9]))
    toast("SD TEST", "DONE", 600)
    push(ListPage("SD TEST", [infoline(n, (lambda r=r: r)) for n, r in res]))
def _sd_clean_act():
    push(Confirm("SD STATE NEW", "STATE FILE", "NEW ON SD?", lambda: _sd_remount_act(True)))
def setup_page():
    return ListPage("SETUP", [
        link("MIDI", midi_setup_page),
        link("ENCODER", encoder_page),
        link("MACROS", lambda: ListPage("MACROS", P_MACRO)),
        P_AUDIO, P_VBUD, P_FAIL,
        link("DISPLAY", lambda: ListPage("DISPLAY", [P_BRIGHT, P_DIM, P_DFAST])),
        link("WLAN", wlan_page),
        link("CLOCK", takt_page),
        action("MOUNT SD", _sd_remount_act, info=lambda: "OK" if BASE == "/sd/" else "-"),
        action("SD STATE NEW", _sd_clean_act),
        action("SD TEST", _sd_test_act),
        link("INFO", info_page),
        action("FACTORY RESET", lambda: push(Confirm("FACTORY RESET", "ALL SETTINGS",
                                                  "RESET?", factory_reset)))])
CARDS = [
    ("SOUND", "PATCH FILTER ENV", 0, klang_page),
    ("MIXER", "16 CHANNELS", 1, MixerPage),
    ("EFFECTS", "REVERB CHORUS EQ", 2, fx_page),
    ("SEQUENCER", "TRACKS 303 DRUMS", 3, SeqPage),
    ("MODULAR", "CV VCO AUDIO IN", 4, ModularPage),
    ("SCENES", "8 SLOTS MORPH", 5, scenes_page),
    ("SAMPLER", "8 SLOTS + REC", 6, sampler_page),
    ("SETUP", "MIDI ENC WLAN", 7, setup_page),
]
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
    toast("CHANNEL %d" % ch, chan_patch_name(ch)[:14], 700)
_joy_btn_prev = False
def poll_input():
    global _btn_down, _btn_t0, _btn_turned, _btn_fired, _hold_progress
    global _joy_btn_prev
    if joy_owned():
        d = _nav_delta()
        vd = 0
    else:
        d = _nav_delta() + _joy_delta()
        vd = _joy_vdelta()
    jb = _joy is not None and bool(_joy[2])
    if acid_joy_active():
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
        _enc_page_seen = p
        resync_param_encoders()
        return
    jump = getattr(p, "enc_jump", None)
    for i in range(len(PARAM_ENCODERS)):
        sl = ENC_SLOT[i]
        f = S["encf"][sl]
        if f == "AUS" and jump is None:
            continue
        try:
            pos = enc.read(PARAM_ENCODERS[i])
        except Exception:
            continue
        d = pos - _last_param[i]
        if not d:
            continue
        _last_param[i] = pos
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
_pb_t0 = [None] * len(PARAM_BUTTONS)
_pb_long = [False] * len(PARAM_BUTTONS)
def _mute_toggle(ch):
    S["mute"][ch] ^= 1
    apply_level(ch)
    apply_master_volume()
    toast("K%d" % ch, "MUTE" if S["mute"][ch] else "ON", 700)
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
        toast(track_label(i), "MUTE" if t["mute"] else "ON", 700)
    request_save()
    mark_dirty()
def read_param_buttons():
    if enc is None:
        return
    for i in range(len(PARAM_BUTTONS)):
        sl = ENC_SLOT[i]
        if S["encb"][sl] == "AUS":
            continue
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
_led_sent = {}
def update_leds():
    if enc is None:
        return
    try:
        if not enc.leds:
            return
        for i in range(len(ENC_SLOT)):
            li = ENC_LED[i] if i < len(ENC_LED) else None
            if li is None or li >= enc.leds:
                continue
            rgb = LED_RGB[enc_led_index(ENC_SLOT[i])]
            if _led_sent.get(li) == rgb:
                continue
            enc.led(li, *rgb)
            _led_sent[li] = rgb
    except Exception as e:
        print("LED", e)
FRAME_MS = 45
LIVE_MS = 240
_last_frame = 0
_live = False
_flush_pending = False
def render(force=False):
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
_saver_next = 0
_saver_pos = 0
def service_saver():
    global _saver, _saver_next, _saver_pos
    if _saver:
        if since(_saver_next) >= 0:
            _saver_next = time.ticks_add(now(), 5000)
            _saver_pos = (_saver_pos + 37) % 90
            try:
                fb.fill(0)
                T("DOLPHIN", 8 + _saver_pos // 2, 20 + _saver_pos, GH + 1)
                if S["run"]:
                    T("%d BPM" % S["tempo"], 8 + _saver_pos // 2, 32 + _saver_pos, GH)
            except Exception:
                pass
            refresh()
        return
    m = S["dim"]
    if not m or top().custom or _btn_down:
        return
    if since(_last_input) > m * 60000:
        _saver = True
        _saver_next = 0
        if HAS_CONTRAST:
            display_contrast(20)
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
        toast("HIGH CPU LOAD", "%d%%" % int(ld * 100), 1500)
    elif ld < RENDER_LOAD_CLEAR:
        _load_warned = False
def service_misc():
    global _learned, _morph_next, _m5_prev
    if _learned is not None:
        ch, cc, t = _learned
        _learned = None
        bind_cc(ch, cc, t)
        toast("CC%d > %s" % (cc, CC_TARGETS[t][0]), "CHANNEL %d" % ch)
    if _morph_pending and since(_morph_next) >= 0:
        _morph_next = time.ticks_add(now(), 60)
        morph_apply()
    cvmod_service()
    cvfold_service()
    vco_service()
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
GC_RUN_MS = 20000
def service_gc():
    global _gc_next
    if since(_gc_next) >= 0 and since(_last_input) > 700:
        _gc_next = time.ticks_add(now(), GC_RUN_MS if S["run"] else GC_IDLE_MS)
        gc.collect()
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
        print("FALLBACK", e)
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
            print("BUTTONS", e)
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
        service_gc()
        render()
    finally:
        _ui_busy = False
        meas("ui", _ui_t0)
    return True
def loop(tick):
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
_state_src = load_state()
print("STATE:", _state_src)
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
    smp_load_all()
except Exception as e:
    print("SAMPLER INIT", e)
try:
    cvmod_service(True)
except Exception as e:
    print("CVMOD INIT", e)
try:
    vco_init()
except Exception as e:
    print("VCO INIT", e)
try:
    ain_init()
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
    toast("V11 IMPORT", "SETTINGS", 2500)
elif _state_src == "backup":
    toast("STATE", "TAKEN OVER", 2500)
elif _state_src == "neu":
    toast("NO STATE", STATE_FILE[-24:], 2500)
elif BASE != "/sd/":
    toast("STORAGE INTERNAL", "SETUP>SD NEW", 2500)
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
    print("CLOCK INIT", e)
print("================================")
print("DOLPHIN SELECTOR 3 v" + VERSION)
print("Encoder:", encoder_count, "Extras:", len(PARAM_ENCODERS))
print("Storage:", STATE_FILE)
print("Seq:", "FINE" if _seq_slot is not None else "LOOP",
      "AHEAD %dms" % S["vlf"] if S["sqm"] else "DIRECT",
      "UI:", "TIMER" if ui_timer_mode() else "LOOP",
      "Display:", "BANDS" if _fast_ok else "FULL",
      "RAM:", _ram_boot, "Boot ms:", _boot_dur_ms)
print("================================")
_auto_generated_knobs = """
"""
# Do not edit. Set automatically by the knobs on AMYboard Online.
_auto_generated_knobs = """

"""
