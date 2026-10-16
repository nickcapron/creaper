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
