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
the project tempo."""

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
HATS = {42, 44, 46, 51, 53, 59, 54, 69, 70, 82}  # hats, rides, tambourine, cabasa, maracas, shaker
CYMBALS = {49, 52, 55, 57}


def feel_for_genre(feel_text: str, family: str = "", swing: float = 50, name: str = "") -> str:
    """The feel name for a genre, from its profile's feel description and family:
    electronic and programmed styles (house, synthwave, trap, drum and bass) are tight;
    relaxed grooves laid back; rock and metal pushed; rubato styles expressive."""
    t = feel_text.lower()
    fam = family.lower()
    if re.search(r"rubato|breath|free|colla voce|unmetered|expressive", t):
        return "expressive"
    if re.search(r"laid[- ]back|behind[- ]the[- ]beat|lazy|drunk|dilla|relaxed|loping|dragg", t) \
            or re.search(r"\b(reggae|dub|rocksteady|lovers rock)\b", name.lower()):
        return "laid back"
    if fam in ("electronic", "electronic dance") or re.search(r"\b(trap|drill|phonk)\b", name.lower()):
        return "tight"  # programmed music: on the grid, with accents doing the work
    if re.search(r"quantis|quantiz|rigid|machine|mechanical|motoric|clock|four-on-the-floor|robotic|grid", t):
        return "tight"
    if fam in ("rock", "metal and punk") and re.search(r"driving|urgent|frantic|ahead of the beat", t):
        return "pushed"
    if swing >= 60:
        return "laid back"
    return "natural"


def _ms_to_qn(ms: float, bpm: float) -> float:
    return ms / 1000.0 * bpm / 60.0


def _beat_strength(pos: float, beats_per_bar: float) -> int:
    """2 = the bar's downbeat, 1 = another beat, 0 = an 8th offbeat, -1 = a 16th."""
    frac = pos % 1.0
    if abs(frac) < 1e-3 or abs(frac - 1) < 1e-3:
        return 2 if abs(pos % beats_per_bar) < 1e-3 else 1
    if abs(frac - 0.5) < 1e-3:
        return 0
    return -1


def _clamp_vel(v: float) -> int:
    return max(1, min(127, round(v)))


def drum_job(lane: str) -> str | None:
    """A drum lane's job in the groove, from its name: kick, backbeat, hats or cymbal."""
    name = lane.lower()
    if "kick" in name or name in ("bd", "bass drum"):
        return "kick"
    if any(w in name for w in ("snare", "clap", "rim", "side")):
        return "backbeat"
    if any(w in name for w in ("hat", "hh", "ride", "shaker", "tamb", "cabasa", "maraca")):
        return "hats"
    if any(w in name for w in ("crash", "china", "splash", "cymbal")):
        return "cymbal"
    return None


def apply(notes: list[dict], role: str, feel: str = "natural", bpm: float = 120.0, beats_per_bar: float = 4.0,
          amount: float = 1.0, seed: int | None = None, drum_jobs: dict[int, str] | None = None) -> list[dict]:
    """The notes played with a role's feel. amount scales everything (0 = unchanged,
    1 = the feel as defined, up to 2 = exaggerated). Pitches, order and the number of
    notes never change; starts move by milliseconds and velocities by accents.
    drum_jobs: pitch -> kick/backbeat/hats/cymbal for kits that aren't laid out like
    General MIDI (from the lane names); others are judged by their GM note."""
    if role not in ROLES:
        raise ValueError(f"role must be one of {', '.join(ROLES)}")
    if feel not in FEELS:
        raise ValueError(f"feel must be one of {', '.join(FEELS)}")
    if amount <= 0 or not notes:
        return [dict(n) for n in notes]
    f = FEELS[feel]
    rng = random.Random(seed)
    jitter = _ms_to_qn(f.jitter_ms, bpm) * amount
    behind = _ms_to_qn(f.behind_ms, bpm) * amount
    dyn = f.dynamics * amount
    out = [dict(n) for n in notes]

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
            accent = {2: 6, 1: 3, 0: -2, -1: -4}[_beat_strength(start, beats_per_bar)] * dyn
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
            accent = {2: 5, 1: 3, 0: 0, -1: -3}[_beat_strength(n["start"], beats_per_bar)]
            n["start"] += rng.uniform(-jitter, jitter)
            n["velocity"] = _clamp_vel(n["velocity"] + (height - 0.5) * 16 * dyn + accent * dyn
                                       + rng.uniform(-4, 4) * dyn)
    elif role == "arp":
        # Machine-steady timing; the first note of each beat leads.
        for n in out:
            strength = _beat_strength(n["start"], beats_per_bar)
            n["start"] += rng.uniform(-jitter, jitter) * 0.3
            n["velocity"] = _clamp_vel(n["velocity"] + (6 if strength >= 1 else -3) * dyn + rng.uniform(-2, 2) * dyn)
    elif role == "bass":
        # In the pocket with the backbeat; leans on the downbeats.
        for n in out:
            strength = _beat_strength(n["start"], beats_per_bar)
            n["start"] += behind * 0.6 + rng.uniform(-jitter, jitter) * 0.7
            n["velocity"] = _clamp_vel(n["velocity"] + {2: 8, 1: 3, 0: -3, -1: -6}[strength] * dyn
                                       + rng.uniform(-4, 4) * dyn)
    else:  # drums
        jobs = drum_jobs or {}
        for n in out:
            p = n["pitch"]
            job = jobs.get(p) or ("kick" if p in KICKS else "backbeat" if p in BACKBEAT else
                                  "hats" if p in HATS else "cymbal" if p in CYMBALS else None)
            strength = _beat_strength(n["start"], beats_per_bar)
            if job == "kick":
                n["start"] += rng.uniform(-jitter, jitter) * 0.3
                n["velocity"] = _clamp_vel(n["velocity"] + (4 if strength == 2 else 0) * dyn + rng.uniform(-3, 3) * dyn)
            elif job == "backbeat":
                n["start"] += behind + rng.uniform(-jitter, jitter) * 0.6
                n["velocity"] = _clamp_vel(n["velocity"] + rng.uniform(-5, 5) * dyn)
            elif job == "hats":
                n["start"] += behind * 0.3 + rng.uniform(-jitter, jitter)
                n["velocity"] = _clamp_vel(n["velocity"] + {2: 10, 1: 8, 0: -8, -1: -16}[strength] * dyn
                                           + rng.uniform(-6, 6) * dyn)
            elif job == "cymbal":
                n["start"] += rng.uniform(-jitter, jitter) * 0.5
                n["velocity"] = _clamp_vel(n["velocity"] + rng.uniform(-4, 4) * dyn)
            else:  # toms, percussion, other kits' notes
                n["start"] += rng.uniform(-jitter, jitter)
                n["velocity"] = _clamp_vel(n["velocity"] + {2: 6, 1: 4, 0: -2, -1: -6}[strength] * dyn
                                           + rng.uniform(-5, 5) * dyn)

    for n in out:
        n["start"] = round(max(0.0, n["start"]), 6)
        n["length"] = round(max(0.01, n["length"]), 6)
    return out
