"""Empress ZOIA patch files (.bin): read one, change it, write it back.

A ZOIA has no patch transfer over MIDI: patches travel on its SD card as 32 KB files
named '012_zoia_Name.bin' (the number is the slot). This module is the file format
only: nothing here talks to hardware or REAPER.

The layout follows the 'ZOIA Patch File binary Format' document written by the
zoia_lib contributors with Empress Effects' help (checked against firmware 2.50 and
2.70), with the two module fields later work corrected (word 2 is the module's
version, word 7 the size of its saved data). Everything is a little-endian 32-bit
word unless noted:

    patch size (words, itself included) | name (16 bytes) | module count | modules
    | connection count | connections (5 words each) | page-name count | names (16
    bytes each) | starred count | starred (1 word each) | one colour per module
    (firmware 1.10 on) | zeros to 32768 bytes

    module: size (words) | type | version | page | old colour | grid position
    | parameter count | saved-data size (bytes) | 8 option bytes | parameters
    | saved data | name (16 bytes; absent in files from firmware before 1.04)

parse() then build() gives back the file byte for byte: whatever this module doesn't
understand (saved data, bytes after the colours) is carried, not interpreted. What a
block number means (which button is a module's audio input) depends on the module's
type and version and is not in the file; that table comes from patches made on the
user's own unit (shapes()).
"""

from __future__ import annotations

import re
import struct
from dataclasses import dataclass, field
from pathlib import Path

PATCH_BYTES = 32768
NAME_BYTES = 16
MODULE_HEAD_WORDS = 10           # 8 header words and 2 of options; then parameters, saved data, the name
PARAM_MAX = 65535                # a parameter's full scale
STRENGTH_MAX = 10000             # a connection at 0 dB; 100 steps a dB, from -100 dB to +12
PAGES = 64
GRID = 40                        # buttons on a page: 5 rows of 8
FILE_NAME = re.compile(r"^(\d{3})_zoia_(.*)\.bin$", re.I)

# Module type -> name, as the ZOIA lists them (the format document's appendix A, and the
# types added since: Euroburo's, Sampler, Logic Gate, Reverse Delay, Univibe).
MODULE_NAMES = {
    0: "SV Filter", 1: "Audio Input", 2: "Audio Output", 3: "Aliaser", 4: "Sequencer", 5: "LFO", 6: "ADSR", 7: "VCA",
    8: "Audio Multiply", 9: "Bit Crusher", 10: "Sample and Hold", 11: "OD & Distortion", 12: "Env Follower",
    13: "Delay Line", 14: "Oscillator", 15: "Pushbutton", 16: "Keyboard", 17: "CV Invert", 18: "Steps",
    19: "Slew Limiter", 20: "MIDI Notes In", 21: "MIDI CC In", 22: "Multiplier", 23: "Compressor", 24: "Multi Filter",
    25: "Plate Reverb", 26: "Buffer Delay", 27: "All Pass Filter", 28: "Quantizer", 29: "Phaser", 30: "Looper",
    31: "In Switch", 32: "Out Switch", 33: "Audio In Switch", 34: "Audio Out Switch", 35: "MIDI Pressure",
    36: "Onset Detector", 37: "Rhythm", 38: "Noise", 39: "Random", 40: "Gate", 41: "Tremolo", 42: "Tone Control",
    43: "Delay w/Mod", 44: "Stompswitch", 45: "Value", 46: "CV Delay", 47: "CV Loop", 48: "CV Filter",
    49: "Clock Divider", 50: "Comparator", 51: "CV Rectify", 52: "Trigger", 53: "Stereo Spread",
    54: "Cport Exp/CV In", 55: "Cport CV Out", 56: "UI Button", 57: "Audio Panner", 58: "Pitch Detector",
    59: "Pitch Shifter", 60: "MIDI Note Out", 61: "MIDI CC Out", 62: "MIDI PC Out", 63: "Bit Modulator",
    64: "Audio Balance", 65: "Inverter", 66: "Fuzz", 67: "Ghostverb", 68: "Cabinet Sim", 69: "Flanger", 70: "Chorus",
    71: "Vibrato", 72: "Env Filter", 73: "Ring Modulator", 74: "Hall Reverb", 75: "Ping Pong Delay",
    76: "Audio Mixer", 77: "CV Flip Flop", 78: "Diffuser", 79: "Reverb Lite", 80: "Room Reverb", 81: "Pixel",
    82: "MIDI Clock In", 83: "Granular", 84: "MIDI Clock Out", 85: "Tap to CV", 86: "MIDI Pitch Bend In",
    87: "Euro CV Out 4", 88: "Euro CV In 1", 89: "Euro CV In 2", 90: "Euro CV In 3", 91: "Euro CV In 4",
    92: "Euro Headphone Amp", 93: "Euro Audio Input 1", 94: "Euro Audio Input 2", 95: "Euro Audio Output 1",
    96: "Euro Audio Output 2", 97: "Euro Pushbutton 1", 98: "Euro Pushbutton 2", 99: "Euro CV Out 1",
    100: "Euro CV Out 2", 101: "Euro CV Out 3", 102: "Sampler", 103: "Device Control", 104: "CV Mixer",
    105: "Logic Gate", 106: "Reverse Delay", 107: "Univibe",
}
COLORS = {1: "blue", 2: "green", 3: "red", 4: "yellow", 5: "aqua", 6: "magenta", 7: "white", 8: "orange", 9: "lime",
          10: "surf", 11: "sky", 12: "purple", 13: "pink", 14: "peach", 15: "mango"}
OLD_COLOR = {8: 3, 9: 2, 10: 5, 11: 1, 12: 6, 13: 3, 14: 3, 15: 4}    # what a pre-1.10 ZOIA shows instead
_TEXT_OK = re.compile(r"[A-Za-z0-9 .\-]")


def _text(raw: bytes) -> str:
    return raw.split(b"\0", 1)[0].decode("ascii", "replace").rstrip()


def _raw_text(text: str, what: str) -> bytes:
    """A name as the ZOIA stores it: its own characters only (letters, digits, space,
    dash, dot), 16 bytes, zero-filled."""
    bad = sorted({c for c in text if not _TEXT_OK.fullmatch(c)})
    if bad:
        raise ValueError(f"{what} {text!r}: the ZOIA has no {' '.join(repr(c) for c in bad)} (letters, digits, space, - and . only)")
    if len(text) > NAME_BYTES:
        raise ValueError(f"{what} {text!r} is {len(text)} characters: the ZOIA shows {NAME_BYTES}")
    return text.encode("ascii").ljust(NAME_BYTES, b"\0")


@dataclass
class Module:
    type_id: int
    version: int = 0
    page: int = 0
    old_color: int = 7
    position: int = 0
    saved_size: int = 0
    options: list[int] = field(default_factory=lambda: [0] * 8)
    params: list[int] = field(default_factory=list)       # each 0..65535
    saved: bytes = b""                                     # the module's own data (a sequencer's steps...), as found
    name_raw: bytes | None = b"\0" * NAME_BYTES           # None: a file from before module names (1.04)

    @property
    def name(self) -> str:
        return _text(self.name_raw or b"")

    @name.setter
    def name(self, text: str) -> None:
        self.name_raw = _raw_text(text, "module name")

    @property
    def type_name(self) -> str:
        return MODULE_NAMES.get(self.type_id, f"type {self.type_id}")

    @property
    def words(self) -> int:
        return MODULE_HEAD_WORDS + len(self.params) + len(self.saved) // 4 + (0 if self.name_raw is None else 4)


@dataclass
class Connection:
    source: int             # module index
    source_block: int       # block number among ALL the type's blocks, hidden ones counted
    dest: int
    dest_block: int
    strength: int = STRENGTH_MAX

    @property
    def db(self) -> float:
        return (self.strength - STRENGTH_MAX) / 100.0


@dataclass
class Star:
    """A starred parameter (module, block) or connection (its index), and the MIDI CC
    that moves it, if one was assigned."""
    module: int | None = None
    block: int | None = None
    connection: int | None = None
    cc: int | None = None

    @classmethod
    def from_word(cls, word: int) -> "Star":
        on_connection = bool(word >> 31)
        if on_connection:
            word = ~word & 0xFFFFFFFF
        cc = (word >> 23) & 0xFF
        cc = cc - 1 if cc else None
        if on_connection:
            return cls(connection=word & 0xFFFF, cc=cc)
        return cls(module=word & 0xFFFF, block=(word >> 16) & 0x7F, cc=cc)

    def word(self) -> int:
        cc = 0 if self.cc is None else self.cc + 1
        if self.connection is not None:
            return ~(self.connection | cc << 23) & 0xFFFFFFFF
        return (self.module or 0) | (self.block or 0) << 16 | cc << 23


@dataclass
class Patch:
    name_raw: bytes = b"\0" * NAME_BYTES
    modules: list[Module] = field(default_factory=list)
    connections: list[Connection] = field(default_factory=list)
    page_names: list[bytes] = field(default_factory=list)     # 16 raw bytes each; may be fewer than the pages used
    starred: list[int] = field(default_factory=list)          # raw words: Star.from_word reads one
    colors: list[int] | None = None                           # one per module; None in a file from before 1.10
    extra: bytes = b""                                        # inside the patch size, after the colours: carried as found
    tail: bytes = b""                                         # past the patch size and not zero: carried as found

    @property
    def name(self) -> str:
        return _text(self.name_raw)

    @name.setter
    def name(self, text: str) -> None:
        self.name_raw = _raw_text(text, "patch name")

    @property
    def pages(self) -> int:
        return max((m.page for m in self.modules), default=0) + 1


class _Reader:
    def __init__(self, data: bytes, end: int):
        self.data, self.at, self.end = data, 0, end

    def word(self) -> int:
        if self.at + 4 > self.end:
            raise ValueError(f"not a ZOIA patch: it ends at byte {self.end}, inside a field at {self.at}")
        (v,) = struct.unpack_from("<I", self.data, self.at)
        self.at += 4
        return v

    def take(self, n: int) -> bytes:
        if n < 0 or self.at + n > self.end:
            raise ValueError(f"not a ZOIA patch: {n} bytes asked for at {self.at}, and it ends at {self.end}")
        out = self.data[self.at:self.at + n]
        self.at += n
        return out


def parse(data: bytes) -> Patch:
    """The patch in a .bin file's bytes. ValueError when the bytes aren't one."""
    if len(data) < 28:
        raise ValueError(f"not a ZOIA patch: {len(data)} bytes")
    end = struct.unpack_from("<I", data, 0)[0] * 4
    if not 28 <= end <= len(data):
        raise ValueError(f"not a ZOIA patch: it says it is {end} bytes long, the file is {len(data)}")
    r = _Reader(data, end)
    r.word()
    patch = Patch(name_raw=r.take(NAME_BYTES))
    for _ in range(r.word()):
        start = r.at
        words, type_id, version, page, color, position, n_params, saved_size = (r.word() for _ in range(8))
        spare = words - MODULE_HEAD_WORDS - n_params - (saved_size + 3) // 4
        if spare < 0:
            raise ValueError(f"not a ZOIA patch: module {len(patch.modules)} is {words} words, with {n_params} "
                             f"parameters and {saved_size} bytes of saved data")
        named = spare >= 4
        options = list(r.take(8))
        params = [r.word() for _ in range(n_params)]
        saved = r.take(start + words * 4 - (NAME_BYTES if named else 0) - r.at)
        patch.modules.append(Module(type_id, version, page, color, position, saved_size, options, params, saved,
                                    r.take(NAME_BYTES) if named else None))
    for _ in range(r.word()):
        patch.connections.append(Connection(*(r.word() for _ in range(5))))
    patch.page_names = [r.take(NAME_BYTES) for _ in range(r.word())]
    patch.starred = [r.word() for _ in range(r.word())]
    if end - r.at >= 4 * len(patch.modules) and patch.modules:
        patch.colors = [r.word() for _ in patch.modules]
    patch.extra = r.take(end - r.at)
    patch.tail = data[end:].rstrip(b"\0")
    return patch


def build(patch: Patch) -> bytes:
    """The 32768 bytes of a .bin file. ValueError when the patch can't be one (too big,
    a connection or star naming a module that isn't there)."""
    n = len(patch.modules)
    for i, c in enumerate(patch.connections):
        if not (0 <= c.source < n and 0 <= c.dest < n):
            raise ValueError(f"connection {i} joins modules {c.source} and {c.dest}: the patch has {n}")
    if patch.colors is not None and len(patch.colors) != n:
        raise ValueError(f"{len(patch.colors)} colours for {n} modules")
    out = bytearray(patch.name_raw.ljust(NAME_BYTES, b"\0")[:NAME_BYTES])
    out += struct.pack("<I", n)
    for i, m in enumerate(patch.modules):
        if len(m.saved) % 4 or len(m.options) != 8 or (m.name_raw is not None and len(m.name_raw) != NAME_BYTES):
            raise ValueError(f"module {i} ({m.type_name}): saved data must be whole words, options 8 bytes, the name 16")
        out += struct.pack("<8I", m.words, m.type_id, m.version, m.page, m.old_color, m.position, len(m.params), m.saved_size)
        out += bytes(m.options) + struct.pack(f"<{len(m.params)}I", *m.params) + m.saved + (m.name_raw or b"")
    out += struct.pack("<I", len(patch.connections))
    for c in patch.connections:
        out += struct.pack("<5I", c.source, c.source_block, c.dest, c.dest_block, c.strength)
    out += struct.pack("<I", len(patch.page_names)) + b"".join(p.ljust(NAME_BYTES, b"\0")[:NAME_BYTES] for p in patch.page_names)
    out += struct.pack(f"<I{len(patch.starred)}I", len(patch.starred), *patch.starred)
    if patch.colors is not None:
        out += struct.pack(f"<{n}I", *patch.colors)
    out += patch.extra
    if len(out) % 4:
        raise ValueError("the patch is not a whole number of words")
    size = len(out) + 4
    whole = struct.pack("<I", size // 4) + bytes(out) + patch.tail
    if len(whole) > PATCH_BYTES:
        raise ValueError(f"the patch is {len(whole)} bytes: a ZOIA patch holds {PATCH_BYTES}")
    return whole.ljust(PATCH_BYTES, b"\0")


def read(path: str | Path) -> Patch:
    return parse(Path(path).read_bytes())


def file_name(slot: int, name: str) -> str:
    """The name the ZOIA looks for on its card: '012_zoia_Name.bin' loads into slot 12."""
    if not 0 <= slot <= 63:
        raise ValueError(f"slot {slot}: a ZOIA has slots 0 to 63")
    return f"{slot:03d}_zoia_{re.sub(r'[^A-Za-z0-9.-]+', '_', name).strip('_') or 'patch'}.bin"


def card_patches(folder: str | Path) -> list[dict]:
    """The patch files in a card folder (the ZOIA writes its own to 'from_zoia' and loads
    from 'to_zoia'), by slot. A file that isn't a patch is listed with its error."""
    out = []
    for f in sorted(Path(folder).glob("*.bin")):
        m = FILE_NAME.match(f.name)
        row: dict = {"file": str(f), "slot": int(m.group(1)) if m else None}
        try:
            p = read(f)
            row.update(name=p.name or (m.group(2) if m else f.stem), modules=len(p.modules), pages=p.pages)
        except (ValueError, OSError) as e:
            row["error"] = str(e)
        out.append(row)
    return out


def describe(patch: Patch) -> dict:
    """The patch as plain data: its modules (type, page, grid position, parameters as
    0..1 of full scale), connections (in dB) and stars (with their MIDI CCs)."""
    used = [0] * max(patch.pages, 1)
    modules = []
    for i, m in enumerate(patch.modules):
        color = (patch.colors[i] if patch.colors else None) or m.old_color
        modules.append({
            "index": i, "type": m.type_name, **({"name": m.name} if m.name else {}), "page": m.page, "position": m.position,
            "color": COLORS.get(color, color), "version": m.version, "options": list(m.options),
            "params": [round(v / PARAM_MAX, 4) for v in m.params],
            **({"saved_bytes": len(m.saved)} if m.saved else {})})
        if m.page < len(used):
            used[m.page] += 1
    names = [_text(p) for p in patch.page_names]
    stars = []
    for w in patch.starred:
        s = Star.from_word(w)
        row: dict = {"connection": s.connection} if s.connection is not None else {"module": s.module, "block": s.block}
        if s.module is not None and s.module < len(patch.modules):
            row["type"] = patch.modules[s.module].type_name
        if s.cc is not None:
            row["midi_cc"] = s.cc
        stars.append(row)
    return {"name": patch.name, "modules": modules,
            "connections": [{"from": [c.source, c.source_block], "to": [c.dest, c.dest_block], "db": c.db}
                            for c in patch.connections],
            "pages": [{"page": i, **({"name": names[i]} if i < len(names) and names[i] else {}), "modules": n}
                      for i, n in enumerate(used)],
            "starred": stars,
            "bytes": struct.unpack_from("<I", build(patch), 0)[0] * 4}


# ------------------------------------------------------------------- changing a patch

def set_param(patch: Patch, module: int, param: int, value: float) -> None:
    """One module parameter, 0..1 of its full scale (what the value means, ms or Hz,
    depends on the module type)."""
    m = _module(patch, module)
    if not 0 <= param < len(m.params):
        raise ValueError(f"module {module} ({m.type_name}) has {len(m.params)} parameters: no parameter {param}")
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"a parameter is 0 to 1 of its range, not {value}")
    m.params[param] = round(value * PARAM_MAX)


def set_strength(patch: Patch, connection: int, db: float) -> None:
    """A connection's strength, -100 to +12 dB (0 dB is what a new connection has)."""
    if not 0 <= connection < len(patch.connections):
        raise ValueError(f"the patch has {len(patch.connections)} connections: no connection {connection}")
    if not -100.0 <= db <= 12.0:
        raise ValueError(f"connection strength is -100 to +12 dB, not {db}")
    patch.connections[connection].strength = round(STRENGTH_MAX + db * 100)


def star(patch: Patch, module: int, block: int, cc: int | None = None) -> None:
    """Stars a module's parameter block, with a MIDI CC to move it from REAPER (None: a
    star alone). Starring it again changes its CC."""
    _module(patch, module)
    if not 0 <= block <= 0x7F:
        raise ValueError(f"block {block}: 0 to 127")
    if cc is not None and not 0 <= cc <= 127:
        raise ValueError(f"MIDI CC {cc}: 0 to 127")
    word = Star(module=module, block=block, cc=cc).word()
    for i, w in enumerate(patch.starred):
        s = Star.from_word(w)
        if (s.module, s.block) == (module, block):
            patch.starred[i] = word
            return
    patch.starred.append(word)


def _module(patch: Patch, index: int) -> Module:
    if not 0 <= index < len(patch.modules):
        raise ValueError(f"the patch has {len(patch.modules)} modules: no module {index}")
    return patch.modules[index]


# ------------------------------------------------- what real patches say about modules

def shapes(patches: list[Patch]) -> dict[int, list[dict]]:
    """What each module type looks like in real patches, per version: how many
    parameters, how much saved data, which option bytes were seen. A new module of a
    type is safe to write only in a shape the user's own ZOIA has saved."""
    seen: dict[tuple[int, int, int, int, int], dict] = {}
    for p in patches:
        for m in p.modules:
            key = (m.type_id, m.version, len(m.params), len(m.saved), m.saved_size)
            row = seen.setdefault(key, {"type": m.type_name, "version": m.version, "params": len(m.params),
                                        "saved_bytes": len(m.saved), "saved_size": m.saved_size, "count": 0,
                                        "options": set()})
            row["count"] += 1
            row["options"].add(tuple(m.options))
    out: dict[int, list[dict]] = {}
    for key in sorted(seen):
        row = seen[key]
        row["options"] = sorted(row["options"])
        out.setdefault(key[0], []).append(row)
    return out
