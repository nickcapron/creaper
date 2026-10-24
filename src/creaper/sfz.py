"""SFZ multisample instruments and the sample details a sampler needs: an SFZ file's
regions (with <control>/<global>/<master>/<group> opcodes inherited, #define and
#include, note names), WAV loop points from the 'smpl' chunk (so sustained samples
loop instead of dying), and velocity layers and round robins from file names
('Violin_C4_pp_rr2.wav'). zones() turns regions into what the sampler builds: one
zone per key and velocity range, its round-robin takes together. Pure: no REAPER."""

from __future__ import annotations

import re
import struct
from pathlib import Path

HEADERS = ("control", "global", "master", "group", "region")
NOTE = re.compile(r"^([a-gA-G])([#b]?)(-?\d+)$")
SEMITONE = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
LOOP_MODES = ("loop_continuous", "loop_sustain")
MAX_ZONES = 128


def _int(v) -> int:
    return int(round(float(v)))


def note_value(value: str | int) -> int:
    """A key opcode's value: a MIDI number or an SFZ note name (c4 = 60, c#4, db4)."""
    if isinstance(value, int):
        return value
    v = str(value).strip()
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    m = NOTE.match(v)
    if not m:
        raise ValueError(f"'{v}' isn't a note")
    pc = SEMITONE[m.group(1).lower()] + {"#": 1, "b": -1, "": 0}[m.group(2)]
    return 12 * (int(m.group(3)) + 1) + pc


def _strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


MAX_INCLUDES = 4096   # include expansions in all: a library includes one note file per key


def _expand(text: str, base: Path, depth: int = 0, defines: dict[str, str] | None = None,
            count: list | None = None) -> str:
    """#include (relative to the root .sfz's folder, as sfizz and ARIA read it) and
    #define $NAME value (seen by the files included after it). Included files must be
    .sfz/.sfzh files within two folders of the root (a library's Programs/ and its
    shared folder); the same file may be included again (with other defines), up to
    MAX_INCLUDES expansions in all, 8 deep."""
    if depth > 8:
        raise ValueError("#include nests too deep")
    defines = {} if defines is None else defines
    count = [0] if count is None else count
    out = []
    for line in _strip_comments(text).splitlines():
        m = re.match(r'\s*#include\s+"([^"]+)"', line)
        if m:
            inc = (base / m.group(1).replace("\\", "/")).resolve()
            if inc.suffix.lower() not in (".sfz", ".sfzh", ".txt"):
                raise ValueError(f"#include of a non-SFZ file: {inc.name}")
            try:
                inc.relative_to(base.resolve().parent.parent)
            except ValueError:
                raise ValueError(f"#include outside the instrument's library: {inc}") from None
            count[0] += 1
            if count[0] > MAX_INCLUDES:
                raise ValueError(f"more than {MAX_INCLUDES} #include expansions")
            out.append(_expand(inc.read_text(encoding="utf-8", errors="replace"), base, depth + 1, defines, count))
            continue
        m = re.match(r"\s*#define\s+(\$\w+)\s+(\S+)", line)
        if m:
            defines[m.group(1)] = m.group(2)
            continue
        for k in sorted(defines, key=len, reverse=True):
            line = line.replace(k, defines[k])
        out.append(line)
    return "\n".join(out)


def _opcodes(body: str) -> dict[str, str]:
    """key=value pairs; a value runs to the next 'key=' (sample paths can hold spaces)."""
    out = {}
    for m in re.finditer(r"(\w+)=(.*?)(?=\s+\w+=|\s*$)", body.strip(), flags=re.S):
        out[m.group(1)] = m.group(2).strip()
    return out


def parse(text: str, base: Path) -> list[dict]:
    """The regions of an SFZ text, each with every opcode it inherits; 'path' is the
    sample's absolute path (default_path from <control> applied)."""
    text = _expand(text, base)
    scopes: dict[str, dict] = {h: {} for h in HEADERS}
    regions = []
    parts = re.split(r"<(\w+)>", text)
    for header, body in zip(parts[1::2], parts[2::2]):
        header = header.lower()
        ops = _opcodes(body)
        if header not in HEADERS:
            continue
        # A new header resets the ones under it; <control> stands apart from the rest.
        if header != "control":
            for h in HEADERS[HEADERS.index(header):]:
                scopes[h] = {}
        scopes[header] = ops
        if header == "region":
            merged: dict = {}
            for h in HEADERS:
                merged.update(scopes[h])
            merged["_own"] = set(ops)
            if "sample" in merged:
                regions.append(merged)
    for r in regions:
        rel = (r.get("default_path", "") + r["sample"]).replace("\\", "/")
        r["path"] = str((base / rel).resolve())
    return regions


def wav_loop(path: str) -> dict | None:
    """A WAV's first sampler loop and unity note from its 'smpl' chunk:
    {'start', 'end' (frames, end inclusive), 'unity_note'}; None without one."""
    try:
        with open(path, "rb") as f:
            head = f.read(12)
            if head[:4] != b"RIFF" or head[8:12] != b"WAVE":
                return None
            while True:
                chunk = f.read(8)
                if len(chunk) < 8:
                    return None
                kind, size = chunk[:4], struct.unpack("<I", chunk[4:])[0]
                if kind == b"smpl":
                    data = f.read(size)
                    if len(data) < 36:
                        return None
                    unity = struct.unpack("<I", data[12:16])[0]
                    loops = struct.unpack("<I", data[28:32])[0]
                    if loops < 1 or len(data) < 36 + 24:
                        return {"unity_note": unity} if unity else None
                    _, _, start, end, _, _ = struct.unpack("<6I", data[36:60])
                    return {"start": start, "end": end, "unity_note": unity}
                f.seek(size + (size & 1), 1)
    except OSError:
        return None


# ------------------------------------------------------- names: velocity, rr

DYNAMICS = ["ppp", "pp", "p", "mp", "mf", "f", "ff", "fff"]
SOFT_LOUD = {"soft": 2, "light": 2, "medium": 4, "med": 4, "hard": 6, "loud": 6, "strong": 6}
RR = re.compile(r"(?:^|[ _\-.])(?:rr|roundrobin|round_robin|take|alt)[ _\-]?(\d+)(?=$|[ _\-.])", re.I)
VEL = re.compile(r"(?:^|[ _\-.])(?:v|vel|velocity|layer)[ _\-]?(\d{1,3})(?=$|[ _\-.])", re.I)


def name_layers(name: str) -> tuple[str, int | None, int | None]:
    """(the name without its velocity and round-robin marks, a loudness rank or None,
    the round-robin number or None) from a sample's file stem."""
    stem = Path(name).stem
    rr = RR.search(stem)
    rr_n = int(rr.group(1)) if rr else None
    if rr:
        stem = stem[: rr.start()] + stem[rr.end():]
    rank = None
    tokens = re.split(r"[ _\-.]+", stem)
    kept = []
    for t in tokens:
        low = t.lower()
        if rank is None and t in DYNAMICS:          # case-sensitive: 'F' and 'P' are notes or words
            rank = DYNAMICS.index(t)
            continue
        if rank is None and low in SOFT_LOUD:
            rank = SOFT_LOUD[low]
            continue
        m = VEL.fullmatch("_" + t)
        if rank is None and m:
            rank = int(m.group(1))
            continue
        kept.append(t)
    return "_".join(kept), rank, rr_n


def velocity_ranges(ranks: list[int]) -> dict[int, tuple[int, int]]:
    """Splits velocities 1-127 evenly among the loudness ranks present, softest first."""
    ordered = sorted(set(ranks))
    n = len(ordered)
    out = {}
    for i, r in enumerate(ordered):
        lo = 1 + round(i * 127 / n)
        hi = round((i + 1) * 127 / n)
        out[r] = (lo, hi)
    return out


# --------------------------------------------------------------- zones

CC_OPCODE = re.compile(r"^(lo|hi)cc(\d+)$")


def _cc_value(r: dict, cc: str) -> int:
    return _int(r.get(f"set_cc{cc}", 0))


def playable(regions: list[dict]) -> list[dict]:
    """The regions a sampler without keyswitches or controllers plays: attack triggers
    only (release samples and generators like *sine left out), the default articulation
    of a keyswitched instrument (sw_default, else the lowest switch), and the controller
    layer each region's controllers sit at by default (set_ccN, else 0). Random
    alternatives (lorand/hirand) and round robins stay: they become round robins."""
    out = [r for r in regions if r.get("trigger", "attack") in ("attack", "first", "legato")
           and not str(r.get("sample", "")).startswith("*")]
    switches = sorted({note_value(r["sw_last"]) for r in out if "sw_last" in r})
    if switches:
        default = next((note_value(r["sw_default"]) for r in out if "sw_default" in r), switches[0])
        out = [r for r in out if "sw_last" not in r or note_value(r["sw_last"]) == default]
    kept = []
    for r in out:
        ok = True
        for k, v in r.items():
            m = CC_OPCODE.match(k)
            if m:
                value = _cc_value(r, m.group(2))
                ok &= value >= _int(v) if m.group(1) == "lo" else value <= _int(v)
        if ok:
            kept.append(r)
    return kept


def zones(regions: list[dict], frames_of=None, loops: bool = True) -> list[dict]:
    """The sampler's zones from SFZ regions: one per key and velocity range, with its
    round robins (seq_position order) as 'files'; the root from pitch_keycenter with
    transpose and tune; a loop from loop_start/loop_end or the WAV's smpl chunk when
    loop_mode loops (or the WAV has a loop and loop_mode is unset). Only playable()
    regions. frames_of(path) gives (frames, sample rate) of a file, for the loop. loops=False
    skips reading the WAVs (a listing needs the zones, not their loop points)."""
    groups: dict[tuple, list[dict]] = {}
    for r in playable(regions):
        own = r.get("_own", set(r))
        if "key" in r and ("key" in own or not ({"lokey", "hikey"} & own)):
            lo = hi = center = note_value(r["key"])
        else:
            lo = note_value(r.get("lokey", r.get("key", 0)))
            hi = note_value(r.get("hikey", r.get("key", 127)))
            center = note_value(r["key"]) if "key" in r and not ({"lokey", "hikey"} & own) else None
        if r.get("pitch_keycenter") not in (None, "sample"):
            center = note_value(r["pitch_keycenter"])
        loop = wav_loop(r["path"]) if loops and r["path"].lower().endswith(".wav") else None
        if center is None:
            center = (loop or {}).get("unity_note") or 60
        root = center - float(r.get("transpose", 0)) - float(r.get("tune", 0)) / 100
        key = (lo, hi, _int(r.get("lovel", 1)), _int(r.get("hivel", 127)))
        mode = r.get("loop_mode")
        start = r.get("loop_start") or r.get("loopstart")
        end = r.get("loop_end") or r.get("loopend")
        spans = None
        if start is not None and end is not None:
            spans = (_int(start), _int(end))
        elif loop and "start" in loop:
            spans = (loop["start"], loop["end"])
        looping = spans is not None and (mode in LOOP_MODES or (mode is None and loop and "start" in loop))
        groups.setdefault(key, []).append({"path": r["path"], "root": root, "seq": _int(r.get("seq_position", 1)),
                                           "loop": spans if looping else None})
    out = []
    for (lo, hi, lovel, hivel), takes in sorted(groups.items()):
        takes.sort(key=lambda t: t["seq"])
        first = takes[0]
        z = {"path": first["path"], "root": first["root"], "lo": max(0, lo), "hi": min(127, hi)}
        if (lovel, hivel) != (1, 127):
            z["lovel"], z["hivel"] = max(1, lovel), min(127, hivel)
        if len(takes) > 1:
            z["files"] = [t["path"] for t in takes]
        if first["loop"] and frames_of:
            z.update(loop_fields(first["loop"], *frames_of(first["path"])))
        out.append(z)
    if len(out) > MAX_ZONES:
        raise ValueError(f"that SFZ has {len(out)} key and velocity zones; creaper builds up to {MAX_ZONES} "
                         "(pick one articulation's .sfz, or a smaller set)")
    return out


def loop_fields(span: tuple[int, int], frames: int, rate: int) -> dict:
    """The sampler's loop settings for a loop span in frames: its start in ms and its
    end as a share of the file (ReaSamplOmatic5000 loops up to the sample end offset)."""
    a, b = span
    if not frames or not rate or not 0 <= a < b < frames:
        return {}
    return {"loop": {"start_ms": round(a / rate * 1000, 3), "end_frac": round((b + 1) / frames, 6)}}


def load(path: str, frames_of=None, loops: bool = True) -> list[dict]:
    p = Path(path)
    if p.suffix.lower() != ".sfz" or not p.is_file():
        raise ValueError(f"there's no .sfz file at {path}")
    regions = parse(p.read_text(encoding="utf-8", errors="replace"), p.parent)
    if not regions:
        raise ValueError(f"{p.name} has no regions with samples")
    missing = [r["path"] for r in playable(regions) if not Path(r["path"]).is_file()]
    if missing:
        raise ValueError(f"{len(missing)} of its samples are missing, e.g. {missing[0]}")
    return zones(regions, frames_of, loops)
