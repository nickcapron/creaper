"""Performance feel: makes programmed MIDI play like musicians, part by part.

Rule-placed notes all land exactly on the grid at one velocity, which is the
loudest giveaway of a machine-made track. Players differ by role: a drummer keeps
the kick tight, lays the snare back in a relaxed groove and accents the hats on the
beat; a bassist sits in the pocket and leans on the downbeats; a keyboardist rolls
chords a few milliseconds low to high and lets the top note sing; a singer or soloist
shapes each phrase, louder toward its peak. The feel engine applies those habits,
scaled by a feel (tight, natural, laid back, pushed, expressive) that comes from the
genre or is chosen per part. Seeded, so the same part gets the same performance.

Positions are in quarter notes from the item start; milliseconds are converted at
the project tempo. Beats come from the meter: 6/8 and 12/8 pulse in dotted quarters,
7/8 groups 2+2+3, and notes a little off the grid (an imported or already-performed
part, triplets) are judged by the grid position they're nearest."""

from __future__ import annotations

import math
import random
import re
from dataclasses import dataclass

ROLES = ("drums", "bass", "chords", "pad", "lead", "arp")


@dataclass(frozen=True)
class Feel:
    jitter_ms: float      # random timing spread (each note, +/-)
    behind_ms: float      # how far back the backbeat/bass sit (+ = later, laid back; - = pushed)
    dynamics: float       # 0-1: how strongly accents and phrasing shape the velocities
    roll_ms: float        # chord roll: low to high voice spread


FEELS = {
    "tight": Feel(jitter_ms=2.0, behind_ms=0.0, dynamics=0.45, roll_ms=4.0),
    "natural": Feel(jitter_ms=6.0, behind_ms=3.0, dynamics=0.7, roll_ms=8.0),
    "laid back": Feel(jitter_ms=8.0, behind_ms=14.0, dynamics=0.75, roll_ms=12.0),
    "pushed": Feel(jitter_ms=6.0, behind_ms=-7.0, dynamics=0.8, roll_ms=6.0),
    "expressive": Feel(jitter_ms=10.0, behind_ms=4.0, dynamics=1.0, roll_ms=16.0),
}

# General MIDI drum notes by job in the groove.
KICKS = {35, 36}
BACKBEAT = {37, 38, 39, 40}                      # side stick, snare, clap, electric snare
OPEN_HATS = {46}
HATS = {42, 44, 51, 53, 59, 54, 69, 70, 82}      # closed/pedal hats, rides, tambourine, cabasa, maracas, shaker
CYMBALS = {49, 52, 55, 57}
GRID_TOLERANCE_MS = 30.0  # a note this close to a grid position counts as on it


def feel_for_genre(feel_text: str, family: str = "", swing: float = 50, name: str = "") -> str:
    """The feel name for a genre, from its profile's feel description and family:
    electronic and programmed styles (house, synthwave, trap, drum and bass) are tight;
    relaxed grooves laid back; fast rock, metal and punk pushed; rubato styles
    expressive. Whole words only: "galloping" isn't "loping", "no rubato" isn't rubato."""
    t = feel_text.lower()
    fam = family.lower()
    n = name.lower()
    if re.search(r"(?<!no )(?<!little )\brubato\b|\bcolla voce\b|\bunmetered\b|\bfree[- ](time|tempo|rhythm)\b"
                 r"|\bbreath[- ]led\b|\bfollows? the (singer|text|breath)", t):
        return "expressive"
    if re.search(r"\blaid[- ]back\b|\bbehind[- ]the[- ]beat\b|\blazy\b|\bdrunk(en)?\b|\bdilla\b|\brelaxed\b"
                 r"|\bloping\b|\bdragg", t) or re.search(r"\b(reggae|dub|rocksteady|lovers rock)\b", n):
        if fam not in ("electronic", "electronic dance"):
            return "laid back"
    if fam in ("electronic", "electronic dance") or re.search(r"\b(trap|drill|phonk)\b", n):
        return "tight"  # programmed music: on the grid, with accents doing the work
    if re.search(r"\bquantis|\bquantiz|\brigid\b|\bmachine\b|\bmechanical\b|\bmotoric\b|\bclock|\brobotic\b"
                 r"|\bno rubato\b|\bunchanging\b", t):
        return "tight"
    if fam in ("rock", "metal and punk") and re.search(
            r"\bdriving\b|\burgent\b|\bfrantic\b|\bahead of the beat\b|\bfast\b|\bblast\b|\bthrash", t + " " + n):
        return "pushed"
    if swing >= 60:
        return "laid back"
    return "natural"


def _ms_to_qn(ms: float, bpm: float) -> float:
    return ms / 1000.0 * bpm / 60.0


def _meter(meter: str | None) -> tuple[int, int]:
    try:
        num, den = (int(x) for x in (meter or "4/4").split("/"))
        return (num, den) if num > 0 and den > 0 else (4, 4)
    except ValueError:
        return 4, 4


def pulses(meter: str | None) -> tuple[float, list[float], float]:
    """The bar length in QN, where its felt beats fall (QN from the bar line), and the
    offbeat grid: 4/4 beats every quarter with 8th offbeats; 6/8, 9/8 and 12/8 pulse in
    dotted quarters with 8th offbeats; odd 8ths group in twos and a final three (7/8 =
    2+2+3); x/2 beats every half note."""
    num, den = _meter(meter)
    unit = 4.0 / den
    bar = num * unit
    if den >= 8 and num % 3 == 0 and num > 3:
        beats = [i * 3 * unit for i in range(num // 3)]
    elif den >= 8 and num > 3:
        groups = [2] * ((num - 3) // 2) + [3] if num % 2 else [2] * (num // 2)
        beats, at = [], 0
        for g in groups:
            beats.append(at * unit)
            at += g
    else:
        beats = [i * unit for i in range(num)]
    offbeat = unit if den >= 8 else unit / 2
    return bar, beats, offbeat


def _beat_strength(pos: float, meter: str | None = "4/4", tol: float = 1e-3) -> int:
    """2 = the bar's downbeat, 1 = another felt beat, 0 = an offbeat (an 8th, or the
    swung 'and' of a triplet), -1 = anything finer. Within tol (QN) of a position counts."""
    bar, beats, off = pulses(meter)
    p = pos % bar

    def near(x: float) -> bool:
        return abs(p - x) <= tol or abs(p - x - bar) <= tol or abs(p - x + bar) <= tol

    if near(0.0):
        return 2
    if any(near(b) for b in beats):
        return 1
    k = round(p / off)
    if abs(p - k * off) <= tol:
        return 0
    third = (beats[1] - beats[0] if len(beats) > 1 else bar) / 3  # the beat split in three
    k3 = round(p / third)
    if abs(p - k3 * third) <= tol and k3 % 3 == 2:
        return 0  # the swung "and": a triplet's last part leans like an offbeat
    return -1


def _clamp_vel(v: float) -> int:
    return max(1, min(127, round(v)))


def drum_job(lane: str) -> str | None:
    """A drum lane's job in the groove, from its name: kick, backbeat, open hat, hats or
    cymbal."""
    name = lane.lower()
    if "kick" in name or name in ("bd", "bass drum"):
        return "kick"
    if any(w in name for w in ("snare", "clap", "rim", "side")):
        return "backbeat"
    if "open" in name and ("hat" in name or "hh" in name):
        return "open hat"
    if any(w in name for w in ("hat", "hh", "ride", "shaker", "tamb", "cabasa", "maraca")):
        return "hats"
    if any(w in name for w in ("crash", "china", "splash", "cymbal")):
        return "cymbal"
    return None


def apply(notes: list[dict], role: str, feel: str = "natural", bpm: float = 120.0, beats_per_bar: float | None = None,
          amount: float = 1.0, seed: int | None = None, drum_jobs: dict[int, str] | None = None,
          meter: str | None = None) -> list[dict]:
    """The notes played with a role's feel. amount scales everything (0 = unchanged,
    1 = the feel as defined, up to 2 = exaggerated). Pitches, order and the number of
    notes never change; starts move by milliseconds and velocities by accents, and no
    note is pushed past where the part ended (a 4-bar loop stays 4 bars).
    meter: '4/4', '6/8', '7/8'... (beats_per_bar alone is read as x/4).
    drum_jobs: pitch -> kick/backbeat/open hat/hats/cymbal for kits that aren't laid
    out like General MIDI (from the lane names); others are judged by their GM note."""
    if role not in ROLES:
        raise ValueError(f"role must be one of {', '.join(ROLES)}")
    if feel not in FEELS:
        raise ValueError(f"feel must be one of {', '.join(FEELS)}")
    if amount <= 0 or not notes:
        return [dict(n) for n in notes]
    if meter is None:
        meter = f"{round(beats_per_bar)}/4" if beats_per_bar else "4/4"
    f = FEELS[feel]
    rng = random.Random(seed)
    jitter = _ms_to_qn(f.jitter_ms, bpm) * amount
    behind = _ms_to_qn(f.behind_ms, bpm) * amount
    dyn = f.dynamics * amount
    tol = _ms_to_qn(GRID_TOLERANCE_MS, bpm)

    def strength(pos: float) -> int:
        return _beat_strength(pos, meter, tol)

    out = [dict(n) for n in notes]
    part_end = max(n["start"] + n["length"] for n in notes)

    if role == "chords":
        # Roll each chord low to high and balance the voicing: the top note sings, inner
        # voices sit back. Accents follow the beat.
        groups: dict[float, list[dict]] = {}
        for n in out:
            groups.setdefault(round(n["start"], 3), []).append(n)
        roll = _ms_to_qn(f.roll_ms, bpm) * amount
        for start, chord in groups.items():
            chord.sort(key=lambda n: n["pitch"])
            shift = rng.uniform(-jitter, jitter) * 0.5
            accent = {2: 6, 1: 3, 0: -2, -1: -4}[strength(start)] * dyn
            for i, n in enumerate(chord):
                spread = roll * (i / max(1, len(chord) - 1)) if len(chord) > 1 else 0.0
                n["start"] = n["start"] + shift + spread
                n["length"] = max(0.02, n["length"] - spread)  # keep the chord's ends together
                voice = 5 if i == len(chord) - 1 else (-4 if 0 < i < len(chord) - 1 else 0)
                n["velocity"] = _clamp_vel(n["velocity"] + accent + voice * dyn + rng.uniform(-3, 3) * dyn)
    elif role == "pad":
        # Pads stay smooth: barely any timing change, gentle velocity variation.
        for n in out:
            n["start"] += rng.uniform(-jitter, jitter) * 0.3
            n["velocity"] = _clamp_vel(n["velocity"] + rng.uniform(-2, 2) * dyn)
    elif role == "lead":
        # Phrase shape: louder toward the high notes and on strong beats; small timing life.
        pitches = [n["pitch"] for n in out]
        lo, hi = min(pitches), max(pitches)
        span = max(1, hi - lo)
        for n in out:
            height = (n["pitch"] - lo) / span                     # 0 at the lowest note, 1 at the peak
            accent = {2: 5, 1: 3, 0: 0, -1: -3}[strength(n["start"])]
            n["start"] += rng.uniform(-jitter, jitter)
            n["velocity"] = _clamp_vel(n["velocity"] + (height - 0.5) * 16 * dyn + accent * dyn
                                       + rng.uniform(-4, 4) * dyn)
    elif role == "arp":
        # Machine-steady timing; the first note of each beat leads.
        for n in out:
            s = strength(n["start"])
            n["start"] += rng.uniform(-jitter, jitter) * 0.3
            n["velocity"] = _clamp_vel(n["velocity"] + (6 if s >= 1 else -3) * dyn + rng.uniform(-2, 2) * dyn)
    elif role == "bass":
        # In the pocket with the backbeat; leans on the downbeats.
        for n in out:
            s = strength(n["start"])
            n["start"] += behind * 0.6 + rng.uniform(-jitter, jitter) * 0.7
            n["velocity"] = _clamp_vel(n["velocity"] + {2: 8, 1: 3, 0: -3, -1: -6}[s] * dyn
                                       + rng.uniform(-4, 4) * dyn)
    else:  # drums
        jobs = drum_jobs or {}
        # Layers on the same step (a clap on the snare, two kicks) move together: one
        # offset per job and position, or they'd flam against each other.
        shared: dict[tuple, float] = {}

        def offset(job: str, start: float, spread: float) -> float:
            key = (job, round(start, 3))
            if key not in shared:
                shared[key] = rng.uniform(-spread, spread)
            return shared[key]

        for n in out:
            p = n["pitch"]
            job = jobs.get(p) or ("kick" if p in KICKS else "backbeat" if p in BACKBEAT else
                                  "open hat" if p in OPEN_HATS else "hats" if p in HATS else
                                  "cymbal" if p in CYMBALS else "other")
            s = strength(n["start"])
            start = n["start"]
            if job == "kick":
                n["start"] += offset(job, start, jitter * 0.3)
                n["velocity"] = _clamp_vel(n["velocity"] + (4 if s == 2 else 0) * dyn + rng.uniform(-3, 3) * dyn)
            elif job == "backbeat":
                n["start"] += behind + offset(job, start, jitter * 0.6)
                n["velocity"] = _clamp_vel(n["velocity"] + rng.uniform(-5, 5) * dyn)
            elif job == "open hat":
                # The offbeat open hat (house, disco) is the accent, not a softer offbeat.
                n["start"] += behind * 0.3 + offset(job, start, jitter)
                n["velocity"] = _clamp_vel(n["velocity"] + {2: -2, 1: -4, 0: 6, -1: -4}[s] * dyn
                                           + rng.uniform(-4, 4) * dyn)
            elif job == "hats":
                n["start"] += behind * 0.3 + offset(job, start, jitter)
                n["velocity"] = _clamp_vel(n["velocity"] + {2: 10, 1: 8, 0: -8, -1: -16}[s] * dyn
                                           + rng.uniform(-6, 6) * dyn)
            elif job == "cymbal":
                n["start"] += offset(job, start, jitter * 0.5)
                n["velocity"] = _clamp_vel(n["velocity"] + rng.uniform(-4, 4) * dyn)
            else:  # toms, percussion, other kits' notes
                n["start"] += offset(job, start, jitter)
                n["velocity"] = _clamp_vel(n["velocity"] + {2: 6, 1: 4, 0: -2, -1: -6}[s] * dyn
                                           + rng.uniform(-5, 5) * dyn)

    for n in out:
        n["start"] = round(min(max(0.0, n["start"]), part_end - 0.01), 6)
        # Nothing rings past where the part ended: the item would grow by a whole bar.
        n["length"] = round(max(0.01, min(n["length"], part_end - n["start"])), 6)
    return out


# ------------------------------------------------------------------ checking a groove

ON_GRID_MS = 0.5          # closer than this to the grid is "on the grid"
ROBOTIC_SHARE = 0.95      # this share of notes on the grid reads as machine timing
FLAT_VELOCITY_SD = 2.0    # a lane whose velocities vary less than this is one velocity
SAME_BAR_MS = 30.0        # bars match when their notes sit within this of each other


def _grid_offset_qn(pos: float, beat: float) -> float:
    """Distance (QN, signed) from the nearest 16th or 8th-triplet position."""
    best = None
    for step in (beat / 4, beat / 3, beat / 6):
        d = pos - round(pos / step) * step
        if best is None or abs(d) < abs(best):
            best = d
    return best


def swing_pct(positions: list[float], beat: float, subdivision: int = 2) -> float | None:
    """How late the offbeats sit, as the genre profiles' swing (50 straight, ~58 light,
    ~66 triplet): for 8ths (subdivision 2) the offbeat's place in the beat; for 16ths
    (4) its place in the half beat. None without enough offbeats to tell."""
    span = beat * 2 / subdivision
    fracs = []
    for p in positions:
        x = (p % span) / span
        if 0.45 <= x <= 0.70:  # the second of the pair, straight to triplet (a 16th at 0.75 isn't one)
            fracs.append(x)
    if len(fracs) < 4:
        return None
    fracs.sort()
    return round(100 * fracs[len(fracs) // 2], 1)


def check_groove(notes: list[dict], bar: float, beat: float, bpm: float, jobs: dict[int, str] | None = None,
                 sections: list[tuple[str, int]] | None = None, genre_swing: float | None = None) -> dict:
    """How played a part sounds, from its MIDI. notes: absolute positions in QN from the
    project start (start, pitch, velocity); bar/beat: lengths in QN; jobs: pitch -> drum
    job (feel.drum_job) for a kit; sections: (name, first bar) to look for a fill or
    change in the bar before each. Returns the numbers and the findings."""
    import statistics

    played = [n for n in notes if not n.get("muted")]
    if len(played) < 8:
        return {"notes": len(played), "findings": ["too few notes to judge a groove (needs 8)"], "verdict": "n/a"}
    ms_per_qn = 60000.0 / bpm
    offsets = [_grid_offset_qn(n["start"], beat) * ms_per_qn for n in played]
    on_grid = sum(abs(o) < ON_GRID_MS for o in offsets) / len(offsets)
    buckets = {"<1 ms": 0, "1-5 ms": 0, "5-10 ms": 0, "10-20 ms": 0, ">20 ms": 0}
    for o in (abs(o) for o in offsets):
        key = "<1 ms" if o < 1 else "1-5 ms" if o < 5 else "5-10 ms" if o < 10 else "10-20 ms" if o < 20 else ">20 ms"
        buckets[key] += 1
    lanes: dict[str, list[int]] = {}
    for n in played:
        lane = (jobs or {}).get(n["pitch"]) or (str(n["pitch"]) if jobs is not None else "notes")
        lanes.setdefault(lane, []).append(n.get("velocity", 100))
    spread = {lane: round(statistics.pstdev(v), 1) for lane, v in lanes.items() if len(v) >= 4}
    flat = bool(spread) and all(sd < FLAT_VELOCITY_SD for sd in spread.values())

    # Bars that repeat the bar before note for note: the same pitches within
    # SAME_BAR_MS of the same places (a feel's millisecond moves don't make a new bar).
    tol = SAME_BAR_MS / ms_per_qn
    by_bar: dict[int, list[tuple]] = {}
    for n in played:
        b = int((n["start"] + tol) // bar)
        by_bar.setdefault(b, []).append((n["pitch"], n["start"] - b * bar))
    first, last = min(by_bar), max(by_bar)
    shapes = [sorted(by_bar.get(b, [])) for b in range(first, last + 1)]

    def same(a: list[tuple], b_: list[tuple]) -> bool:
        return bool(a) and len(a) == len(b_) and all(p == q and abs(x - y) <= tol for (p, x), (q, y) in zip(a, b_))
    repeats = sum(1 for a, b_ in zip(shapes, shapes[1:]) if same(a, b_))
    repeat_share = round(repeats / max(1, len(shapes) - 1), 2)

    out: dict = {"notes": len(played), "bars": len(shapes),
                 "timing": {"on_grid_share": round(on_grid, 2), "offsets": buckets,
                            "median_offset_ms": round(statistics.median(abs(o) for o in offsets), 1)},
                 "velocity_spread": spread, "bars_same_as_previous": repeat_share}
    sw8 = swing_pct([n["start"] for n in played], beat, 2)
    sw16 = swing_pct([n["start"] for n in played], beat, 4)
    if sw8 is not None:
        out["swing_8ths_pct"] = sw8
    if sw16 is not None:
        out["swing_16ths_pct"] = sw16

    findings = []
    if flat and on_grid >= ROBOTIC_SHARE:
        findings.append("every note is on the grid at one velocity: it plays like a machine. Run apply_feel with the "
                        "part's role (and the genre's feel)")
    elif flat:
        findings.append("one velocity throughout: add accents (apply_feel, or vary velocities by beat)")
    elif on_grid >= ROBOTIC_SHARE:
        findings.append("on the grid with accents: right for programmed electronic music; for a played feel, "
                        "apply_feel with 'natural' or 'laid back'")
    if repeat_share >= 0.9 and len(shapes) >= 8:
        findings.append(f"{round(repeat_share * 100)}% of bars repeat the bar before note for note: add a variation "
                        "every 4 bars and a fill every 8 (an open hat, a ghost note, a kick pickup)")
    if genre_swing is not None:
        # Whichever subdivision swings closer to the genre is the one it swings.
        measured = min((v for v in (sw8, sw16) if v is not None), key=lambda v: abs(v - genre_swing), default=None)
        if measured is not None and abs(measured - genre_swing) > 6:
            findings.append(f"swing is {measured:g} but the genre swings about {genre_swing:g}: "
                            "quantize with swing or apply_feel")
    missing = []
    for name, first_bar in sections or []:
        before = first_bar - 2  # the bar before the section, counted from 0 as by_bar is
        if before - 1 < first or before > last:
            continue
        if same(sorted(by_bar.get(before, [])), sorted(by_bar.get(before - 1, []))):
            missing.append(f"{name} (bar {first_bar})")
    if missing:
        out["no_fill_into"] = missing
        findings.append("nothing changes in the bar before " + ", ".join(missing) + ": add a fill, a drop-out or "
                        "a pickup there (add_transitions does it for every section)")
    out["findings"] = findings or ["it plays like a performance: timing and accents move, bars vary"]
    out["verdict"] = "fail" if flat else "check" if findings else "pass"
    return out


# ------------------------------------------------------------------ vibrato

VIBRATO_STEPS = 16      # pitch-bend points per vibrato cycle: under 6 cents a step at 15 cents deep
VIBRATO_FADE_S = 0.4    # the vibrato widens over this long, as a player's does


def vibrato_bends(notes: list[dict], bpm: float, depth_cents: float = 15.0, rate_hz: float = 5.0,
                  min_qn: float = 1.0, delay_qn: float = 0.25, bend_range: float = 2.0,
                  skip: set[int] | None = None) -> tuple[list[dict], int]:
    """Pitch-bend events (position QN, cc 'pitchbend', value -8192..8191) that give each
    long note of a single line a vibrato: still for delay_qn, then a sine rate_hz wide
    widening to depth_cents over VIBRATO_FADE_S, back to centre before the note ends or
    the next note starts (a legato line's tail overlaps it). Notes shorter than min_qn
    and pitches in skip (open strings) stay still. Returns (events, notes vibrated)."""
    qn_per_s = bpm / 60
    full = 8192 * depth_cents / (bend_range * 100)
    ordered = sorted(notes, key=lambda n: n["start"])
    events: list[dict] = []
    done = 0
    for i, n in enumerate(ordered):
        if n["length"] < min_qn or (skip and n["pitch"] in skip):
            continue
        end = n["start"] + n["length"]
        nxt = next((m["start"] for m in ordered[i + 1:] if m["start"] > n["start"] + 1e-6), None)
        if nxt is not None:
            end = min(end, nxt)
        t0, t1 = n["start"] + delay_qn, end - 0.05 * qn_per_s
        if t1 - t0 < 1 / rate_hz * qn_per_s:      # not one whole cycle: leave it still
            continue
        step = 1 / (rate_hz * VIBRATO_STEPS) * qn_per_s
        k = 0
        while t0 + k * step < t1:
            s = k * step / qn_per_s
            v = full * min(1.0, s / VIBRATO_FADE_S) * math.sin(2 * math.pi * rate_hz * s)
            events.append({"position": round(t0 + k * step, 4), "cc": "pitchbend",
                           "value": max(-8192, min(8191, round(v)))})
            k += 1
        events.append({"position": round(t1, 4), "cc": "pitchbend", "value": 0})
        done += 1
    return events, done
