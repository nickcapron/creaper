"""A song as a whole: how it's laid out before it's written (plan_song: which parts play
in each section, at what energy, with which seeds), what each section actually plays
once it is (song_map: per section and track, density, distinct bars, register and
copies), and the scorecard that rolls every check into pass / warn / fail with a score
out of 10 and the change since the last run. Pure functions; the tools are in
song_tools.py."""

from __future__ import annotations

import math
import statistics

from . import composer
from .theory import midi_to_note

PARTS = ("drums", "bass", "chords", "lead", "counter")
CLUB_FAMILIES = {"electronic dance", "electronic"}

# Energy by kind of section (1 calm .. 4 peak), as arrange_tools.energy rates the names.
KIND_ENERGY = {"intro": 1, "verse": 2, "pre": 3, "chorus": 4, "post": 3, "bridge": 2, "breakdown": 1, "outro": 1}


# The calmer way to play each comping rhythm, for the verses: a Donny Benet song had its
# chords pulsing 16ths through every section until the model rewrote the verses as stabs
# by hand. Each partner has fewer hits a bar than its source (composer._COMP:
# pulse_16 16, eighths 8, push 5, offbeat 4, stabs 3, charleston 2) or longer ones.
# Rhythms that define their genre (bossa, montuno, skank, tresillo, waltz) stay.
CALMER_COMPING = {
    "pulse_16": "stabs", "eighths": "stabs", "quarters": "half_notes", "half_notes": "sustain", "offbeat": "stabs",
    "stabs": "half_notes", "charleston": "sustain", "strum": "half_notes", "arpeggio_up": "broken",
    "arpeggio_updown": "arpeggio_up", "broken": "sustain", "alberti": "broken", "push": "stabs", "gospel": "half_notes",
}
PEAK_KINDS = ("chorus", "pre")     # section kinds (composer.section_kind: a drop is a chorus) that comp in full
CALM_ENERGY = 2     # sections at this energy or below comp the calmer way


def comp_rhythm(comping: str, energy: int, kind: str) -> str:
    """How the chords are played in a section: the genre's own comping where the song
    is up (chorus, drop, pre-chorus, any section at energy 3 or more), its calmer
    partner (CALMER_COMPING) in verses and bridges, so the chorus has somewhere to go."""
    if kind in PEAK_KINDS or energy > CALM_ENERGY:
        return comping
    return CALMER_COMPING.get(comping, comping)


def plan_song(genre, sections: list[tuple[str, int]], seed: int, energies: list[int] | None = None) -> list[dict]:
    """Which parts play in each section and how, so every section is its own version of
    the song rather than one loop copied: drums at the section's energy (busier hats in
    a chorus, a thinner kick in an intro) with a new seed each time, the bass and chords
    on every section's own seed, the lead in the verse's shape in verses (a new line
    each verse) and the same hook in every chorus (the hook should come back), a
    counter-melody from the second chorus on so later choruses add something, and the
    breaks thinned to chords and a hint of the hook. Club genres open and close on
    drums (a DJ needs a beat to mix on). sections: [(name, bars)]."""
    club = genre.family in CLUB_FAMILIES
    has_bass = genre.bass_style != "none"
    has_chords = genre.comping != "none"
    kinds = [composer.section_kind(name) for name, _ in sections]
    choruses = [i for i, k in enumerate(kinds) if k == "chorus"]
    seen: dict[str, int] = {}
    base = seed * 100
    out = []
    bar = 1
    for idx, ((name, bars), kind) in enumerate(zip(sections, kinds)):
        seen[kind] = seen.get(kind, 0) + 1
        nth = seen[kind]
        energy = energies[idx] if energies else KIND_ENERGY.get(kind, 2)
        parts: dict[str, dict] = {}
        drums = {"energy": max(1, min(4, energy)), "seed": base + idx}
        bass = {"seed": base + idx, "style": genre.bass_style if has_bass else "root"}
        chords = {"seed": base + idx, "rhythm": comp_rhythm(genre.comping, energy, kind) if has_chords else "sustain"}
        verse_lead = {"shape": "verse", "seed": base + 10 + nth, "register_lift": 0}
        hook = {"shape": "hook", "seed": base + 50, "register_lift": 0}
        if kind == "intro":
            parts["drums"] = drums
            if not club and has_chords:
                parts["chords"] = dict(chords, rhythm="sustain")
        elif kind == "outro":
            parts["drums"] = drums
            if club and has_bass:
                parts["bass"] = bass
            elif not club and has_chords:
                parts["chords"] = dict(chords, rhythm="sustain")
        elif kind == "breakdown":
            if has_chords:
                parts["chords"] = dict(chords, rhythm="sustain")
            parts["lead"] = dict(hook, shape="answer")   # a hint of the hook over the pads
        else:
            parts["drums"] = drums
            if has_bass:
                parts["bass"] = bass
            if has_chords:
                parts["chords"] = chords
            if kind == "chorus":
                parts["lead"] = hook
                if len(choruses) > 1 and idx != choruses[0]:
                    parts["counter"] = {"seed": base + idx}
            elif kind == "pre":
                parts["lead"] = dict(verse_lead, seed=base + 30 + nth, register_lift=1)
            elif kind == "post":
                parts["lead"] = dict(hook, shape="answer", seed=base + 60)
            elif kind == "bridge":
                parts["lead"] = {"shape": "answer", "seed": base + 70 + nth, "register_lift": 0}
            else:
                parts["lead"] = verse_lead
        if energy <= 1 and "bass" in parts:
            parts["bass"] = dict(parts["bass"], style="whole")
        out.append({"section": name, "kind": kind, "energy": energy, "start_bar": bar, "bars": bars,
                    "parts": parts})
        bar += bars
    return out


# ----------------------------------------------------------------- song map

def _signature(notes: list[dict], t0: float, bar_qn: float, bars: int) -> list[tuple]:
    """Each bar's content (pitches and positions, to the 16th triplet) from t0."""
    rows: list[list] = [[] for _ in range(bars)]
    for n in notes:
        b = int((n["start"] - t0) // bar_qn + 1e-9)
        if 0 <= b < bars:
            rows[b].append((n["pitch"], round(((n["start"] - t0) % bar_qn) * 6) / 6))
    return [tuple(sorted(r)) for r in rows]


def song_map(tracks: dict[str, list[dict]], sections: list[dict], bar_qn: float = 4.0) -> dict:
    """What each section plays, per track: notes per bar, the share of its bars that are
    distinct, its register, and whether it plays exactly like an earlier section on that
    track (same_as) or mostly repeats bars heard before (copied_share). tracks: name ->
    notes with absolute QN starts. sections: [{'name', 'start_qn', 'end_qn', 'energy'?}].
    Findings name the problems listeners hear: a section that's a copy on every track, a
    track that loops all song, a chorus no busier than the verse, a lead under the chords."""
    table = []
    sigs: dict[str, list[tuple[str, list]]] = {t: [] for t in tracks}
    heard: dict[str, set] = {t: set() for t in tracks}
    for s in sections:
        bars = max(1, int(round((s["end_qn"] - s["start_qn"]) / bar_qn)))
        row = {"section": s["name"], "bars": bars, "tracks": {}}
        if s.get("energy") is not None:
            row["energy"] = s["energy"]
        total = 0
        for t, notes in tracks.items():
            inside = [n for n in notes if s["start_qn"] - 1e-6 <= n["start"] < s["end_qn"] - 1e-6]
            if not inside:
                continue
            total += len(inside)
            sig = _signature(inside, s["start_qn"], bar_qn, bars)
            played = [b for b in sig if b]
            pitches = sorted(n["pitch"] for n in inside)
            cell = {"notes_per_bar": round(len(inside) / bars, 2),
                    "distinct_bars": round(len(set(played)) / max(1, len(played)), 2),
                    "range": f"{midi_to_note(pitches[0])}-{midi_to_note(pitches[-1])}",
                    "median_pitch": int(statistics.median(pitches))}
            same = next((name for name, other in sigs[t] if other == sig), None)
            if same:
                cell["same_as"] = same
            copied = sum(1 for b in played if b in heard[t])
            if heard[t]:
                cell["copied_share"] = round(copied / max(1, len(played)), 2)
            sigs[t].append((s["name"], sig))
            heard[t].update(played)
            row["tracks"][t] = cell
        row["notes_per_bar"] = round(total / bars, 2)
        table.append(row)
    return {"sections": table, "findings": findings(table, tracks, bar_qn)}


# The names auto_mix reads as a lead and as a chord part (mix_tools.ROLE_WORDS).
LEAD_WORDS = ("lead", "melody", "vocal", "hook", "pluck", "arp", "solo", "synth")
CHORD_WORDS = ("chord", "pad", "keys", "piano", "comp", "rhodes", "organ", "string", "stab", "guitar")


def _lead_and_chords(names: list[str]) -> tuple[str | None, str | None]:
    lower = {n: n.lower() for n in names}
    lead = next((n for n, l in lower.items() if any(w in l for w in LEAD_WORDS)), None)
    chords = next((n for n, l in lower.items() if n != lead and any(w in l for w in CHORD_WORDS)), None)
    return lead, chords


def findings(table: list[dict], tracks: dict[str, list[dict]], bar_qn: float) -> list[dict]:
    out: list[dict] = []
    for row in table:
        cells = row["tracks"]
        if len(cells) >= 2:
            copies = {c.get("same_as") for c in cells.values()}
            if len(copies) == 1 and None not in copies:
                out.append({"check": "section copy", "status": "fail", "section": row["section"],
                            "detail": f"{row['section']} plays exactly like {copies.pop()} on every track",
                            "fix": "give it new material: another seed for the drums and bass, a new voicing or "
                                   "comping rhythm, a part in or out"})
    for t, notes in tracks.items():
        bars = sum(r["bars"] for r in table if t in r["tracks"])
        if bars < 16:
            continue
        distinct = _song_distinct(notes, bar_qn)
        if distinct is not None and distinct < 0.15:
            out.append({"check": "track loop", "status": "warn", "track": t, "value": distinct, "threshold": 0.15,
                        "detail": f"{t} plays the same few bars all song ({distinct:.0%} of its bars distinct)",
                        "fix": "vary it by section: write it per section with its own seed or settings"})
    by_energy: dict[int, list[float]] = {}
    for row in table:
        if row.get("energy") is not None:
            by_energy.setdefault(row["energy"], []).append(row["notes_per_bar"])
    if 4 in by_energy and 2 in by_energy:
        peak, verse = statistics.mean(by_energy[4]), statistics.mean(by_energy[2])
        if peak <= verse * 1.05:
            out.append({"check": "density arc", "status": "warn", "value": round(peak / max(verse, 1e-9), 2),
                        "threshold": 1.05,
                        "detail": f"the choruses play {peak:.1f} notes a bar against the verses' {verse:.1f}",
                        "fix": "add to the chorus: busier hats, a counter-melody, a doubled or wider part"})
    lead, chords = _lead_and_chords(list(tracks))
    if lead and chords and tracks[lead] and tracks[chords]:
        lead_mid = statistics.median(n["pitch"] for n in tracks[lead])
        chord_top = statistics.median(_tops(tracks[chords]))
        if lead_mid < chord_top:
            out.append({"check": "register", "status": "warn", "value": round(lead_mid - chord_top, 1), "threshold": 0,
                        "detail": f"the lead ({lead}) sits under the top of the chords ({chords})",
                        "fix": "move the chords down an octave (octave 3) or the lead up"})
    return out


def _tops(notes: list[dict], spread_qn: float = 0.1) -> list[int]:
    """Each chord's top note; notes starting within spread_qn of a chord's first note
    belong to it (a rolled or humanized chord doesn't start all at once)."""
    tops: list[int] = []
    first = None
    for n in sorted(notes, key=lambda n: n["start"]):
        if first is None or n["start"] - first > spread_qn:
            first = n["start"]
            tops.append(n["pitch"])
        else:
            tops[-1] = max(tops[-1], n["pitch"])
    return tops


def _song_distinct(notes: list[dict], bar_qn: float) -> float | None:
    if not notes:
        return None
    t0 = math.floor(min(n["start"] for n in notes) / bar_qn) * bar_qn
    bars = int((max(n["start"] for n in notes) - t0) // bar_qn) + 1
    played = [b for b in _signature(notes, t0, bar_qn, bars) if b]
    return round(len(set(played)) / max(1, len(played)), 2)


# ---------------------------------------------------------------- scorecard

def scorecard(rows: list[dict], previous: dict | None = None) -> dict:
    """Pass / warn / fail rows rolled into a score out of 10 (a pass counts 1, a warn
    half, a fail nothing), with each row's change since the previous run."""
    if not rows:
        return {"score": None, "checks": []}
    points = sum(1.0 if r["status"] == "pass" else 0.5 if r["status"] == "warn" else 0.0 for r in rows)
    score = round(10 * points / len(rows), 1)
    out = {"score": score, "passed": sum(r["status"] == "pass" for r in rows),
           "warnings": sum(r["status"] == "warn" for r in rows), "failed": sum(r["status"] == "fail" for r in rows),
           "checks": rows}
    if previous:
        out["previous_score"] = previous.get("score")
        if previous.get("score") is not None:
            out["score_change"] = round(score - previous["score"], 1)
        before = dict(zip(_keys(previous.get("checks", [])), previous.get("checks", [])))
        for r, key in zip(rows, _keys(rows)):
            p = before.get(key)
            if not p:
                continue
            if p.get("status") != r["status"]:
                r["was"] = p["status"]
            if isinstance(r.get("value"), (int, float)) and isinstance(p.get("value"), (int, float)):
                r["change"] = round(r["value"] - p["value"], 2)
    return out


def _keys(rows: list[dict]) -> list[str]:
    """A key per row for comparing runs: its check, track or section, and which
    occurrence of that pair it is."""
    seen: dict[str, int] = {}
    out = []
    for r in rows:
        base = f"{r.get('stage', '')}|{r['check']}|{r.get('track') or r.get('section') or ''}"
        seen[base] = seen.get(base, 0) + 1
        out.append(f"{base}|{seen[base]}")
    return out


def row(check: str, status: str, value=None, threshold=None, fix: str | None = None, **extra) -> dict:
    r = {"check": check, "status": status}
    if value is not None:
        r["value"] = value
    if threshold is not None:
        r["threshold"] = threshold
    if fix and status != "pass":
        r["fix"] = fix
    r.update({k: v for k, v in extra.items() if v is not None})
    return r


def graded(check: str, value: float | None, warn: float, fail: float, fix: str, higher_is_worse: bool = True,
           **extra) -> dict:
    """A row from a number and its warn and fail limits."""
    if value is None:
        return row(check, "warn", None, warn, "couldn't measure it", **extra)
    bad = (lambda v, t: v >= t) if higher_is_worse else (lambda v, t: v <= t)
    status = "fail" if bad(value, fail) else "warn" if bad(value, warn) else "pass"
    return row(check, status, value, warn, fix, **extra)


def fingerprint_distance(a: dict, b: dict) -> float | None:
    """How alike two songs' fingerprints are: the RMS difference of their octave curves
    in dB, or None when they can't be compared (different tempo or meter)."""
    if a.get("meter") != b.get("meter") or not a.get("tempo") or not b.get("tempo"):
        return None
    if abs(a["tempo"] - b["tempo"]) / b["tempo"] > 0.02:
        return None
    keys = [k for k in a.get("curve", {}) if k in b.get("curve", {})
            and a["curve"][k] is not None and b["curve"][k] is not None]
    if len(keys) < 6:
        return None
    return round(math.sqrt(sum((a["curve"][k] - b["curve"][k]) ** 2 for k in keys) / len(keys)), 2)
