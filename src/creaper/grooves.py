"""Grooves that develop: a genre's one-, two- or four-bar drum pattern spread over a
whole section with what a drummer does to keep it alive. A small variation every 4th
bar (a ghost snare, an open hat, a kick pickup), a fill every 8th in the genre's own
style, a crash on the downbeat after it, and hats and kick that follow the section's
energy. It works on the step patterns (theory.drum_pattern_notes plays them), so it
stays a pure function: same pattern, bars and seed, same groove."""

from __future__ import annotations

import random

FILL_STYLES = ("snare_roll", "clap_roll", "tom", "dropout", "none")
# What each family does at the end of a phrase when the profile doesn't say.
FAMILY_FILLS = {
    "electronic dance": "clap_roll", "electronic": "snare_roll", "hip-hop": "dropout", "r&b and soul": "snare_roll",
    "pop": "snare_roll", "rock": "tom", "metal and punk": "tom", "jazz": "snare_roll", "blues": "tom",
    "funk and gospel": "snare_roll", "country and folk": "snare_roll", "latin": "tom", "caribbean": "snare_roll",
    "african": "tom", "asian": "tom", "middle eastern": "tom", "european folk": "none", "classical": "none",
    "film and games": "tom", "ambient and experimental": "none",
}
VARIATION_EVERY, FILL_EVERY, BIG_FILL_EVERY = 4, 8, 16
REST = "."


def fill_style_for(genre) -> str:
    """The genre's fill: its profile's fill_style, else its family's."""
    own = getattr(genre, "fill_style", "") or ""
    return own if own in FILL_STYLES else FAMILY_FILLS.get(getattr(genre, "family", ""), "snare_roll")


def _cells(steps: str) -> list[str]:
    return [c for c in steps if c not in " |"]


def _lane(lanes: dict[str, list[str]], *names: str) -> str | None:
    return next((n for n in names if n in lanes), None)


def _hit(c: str) -> bool:
    return c not in (".", "-")


def vary_groove(pattern: dict[str, str], step: float = 0.25, bars: int = 8, fill_style: str = "snare_roll",
                energy: int | None = None, seed: int | None = 0, bar_qn: float = 4.0) -> dict[str, str]:
    """The pattern laid out over `bars` bars and developed, as a drummer keeps a groove
    alive: bar 2 of every four a light change (a ghost hat or kick), bar 4 a stronger one
    (a ghost on the backbeat, an open hat, a kick pickup), never the same twice running;
    every FILL_EVERY-th bar a fill in fill_style (a beat long, two beats every
    BIG_FILL_EVERY bars) and a crash on the next downbeat; energy 4 hats in 16ths,
    energy 1 the kick on the strong beats only. Returns lane -> steps, ready for
    drum_pattern_notes (step as given)."""
    rng = random.Random(seed)
    per_bar = max(1, int(round(bar_qn / step)))
    length = bars * per_bar
    longest = max((len(_cells(s)) for s in pattern.values()), default=per_bar) or per_bar
    lanes: dict[str, list[str]] = {}
    for name, steps in pattern.items():
        cells = _cells(steps) or [REST]
        # Lanes shorter than the longest repeat (as drum_pattern_notes plays them).
        cells = (cells * (longest // len(cells) + 1))[:longest]
        lanes[name] = (cells * (length // len(cells) + 1))[:length]

    def ensure(name: str) -> list[str]:
        return lanes.setdefault(name, [REST] * length)

    backbeat = _lane(lanes, "snare", "clap", "rim", "side stick")
    kick = _lane(lanes, "kick")
    hats = _lane(lanes, "closed hat", "pedal hat", "shaker")
    beat = max(1, per_bar // 4) if per_bar >= 4 else 1
    used: list = []   # the last few variations, oldest first (a list: a set's pop order isn't reproducible)
    for b in range(bars):
        s0, s1 = b * per_bar, (b + 1) * per_bar
        if energy is not None and energy >= 4 and hats:
            lane = lanes[hats]
            for i in range(s0, s1):
                if not _hit(lane[i]) and i % 2 == 1:
                    lane[i] = "o"      # the hats go to 16ths
        if energy is not None and energy <= 1 and kick:
            lane = lanes[kick]
            for i in range(s0, s1):
                if (i - s0) not in (0, per_bar // 2):
                    lane[i] = REST      # a thinner kick in the calm sections
        last = b == bars - 1
        if (b + 1) % FILL_EVERY == 0 and fill_style != "none":
            big = (b + 1) % BIG_FILL_EVERY == 0
            _fill(lanes, ensure, fill_style, s1, beat * (2 if big else 1), backbeat, kick)
            if not last:
                ensure("crash")[s1] = "X"
        elif (b + 1) % VARIATION_EVERY == 0 or ((b + 1) % FILL_EVERY == 0 and fill_style == "none"):
            _variation(lanes, ensure, rng, s0, per_bar, backbeat, kick, hats, used, strong=True)
        elif (b + 1) % VARIATION_EVERY == 2:
            _variation(lanes, ensure, rng, s0, per_bar, backbeat, kick, hats, used, strong=False)
    return {name: "".join(cells) for name, cells in lanes.items()}


def _fill(lanes, ensure, style: str, end: int, span: int, backbeat: str | None, kick: str | None) -> None:
    """A fill over the `span` steps before `end` (a beat, or two for a big one)."""
    start = max(0, end - span)
    if style in ("snare_roll", "clap_roll"):
        name = ("clap" if style == "clap_roll" and "clap" in lanes else backbeat) or "snare"
        lane = ensure(name)
        for k, i in enumerate(range(start, end)):
            # Soft to loud: ghosts, then hits, the last one accented.
            lane[i] = "X" if i == end - 1 else ("x" if k >= span // 2 else "o")
    elif style == "tom":
        toms = ("high tom", "mid tom", "low tom")
        for k, i in enumerate(range(start, end)):
            if k % 2 == 0 or span <= 4:
                ensure(toms[min(2, k * 3 // max(1, span))])[i] = "X" if i >= end - 2 else "x"
        if backbeat:
            for i in range(start, end):
                lanes[backbeat][i] = REST   # the toms replace the snare, or the two flam
    elif style == "dropout" and kick:
        for i in range(max(0, end - span * 2), end):
            lanes[kick][i] = REST
        ensure("open hat")[end - max(1, span // 2)] = "x"


def _variation(lanes, ensure, rng: random.Random, s0: int, per_bar: int, backbeat: str | None, kick: str | None,
               hats: str | None, used: list, strong: bool) -> None:
    """One change in a bar, not the same as the last few: strong ones a ghost on the
    backbeat lane, an open hat near the end or a kick pickup; light ones a ghost hat, a
    ghost kick on an offbeat, or an accent on a soft hat (for grooves too dense for
    ghosts)."""
    options: list[tuple[str, str, int]] = []
    odd = [i for i in range(s0, s0 + per_bar) if (i - s0) % 2 == 1]
    if strong:
        if backbeat:
            options += [("ghost", backbeat, i) for i in odd if not _hit(lanes[backbeat][i])]
        options += [("open", "open hat", i) for i in (s0 + per_bar - 2, s0 + per_bar - 6, s0 + per_bar - 4)
                    if i >= s0 and not _hit(lanes.get("open hat", [REST] * (i + 1))[i])]
        if kick:
            options += [("pickup", kick, i) for i in (s0 + per_bar - 1, s0 + per_bar - 3) if not _hit(lanes[kick][i])]
    else:
        if hats:
            options += [("ghost", hats, i) for i in odd if not _hit(lanes[hats][i])]
            # A dense groove has no room for ghosts: accent one of its soft hats instead.
            options += [("accent", hats, i) for i in range(s0, s0 + per_bar) if lanes[hats][i] in ("o", "g")]
        if kick:
            options += [("ghost", kick, i) for i in odd[len(odd) // 2:] if not _hit(lanes[kick][i])]
    if not options:
        return
    fresh = [o for o in options if (o[0], o[1], (o[2] - s0)) not in used] or options
    kind, lane, i = rng.choice(fresh)
    used.append((kind, lane, i - s0))
    if len(used) > 6:
        used.pop(0)
    ensure(lane)[i] = "o" if kind == "ghost" else ("X" if kind == "accent" else "x")


def distinct_bars(pattern: dict[str, str], step: float = 0.25, bar_qn: float = 4.0) -> float:
    """Distinct bars over all bars of a laid-out pattern (all lanes together)."""
    per_bar = max(1, int(round(bar_qn / step)))
    longest = max((len(_cells(s)) for s in pattern.values()), default=0)
    bars = max(1, longest // per_bar)
    shapes = []
    for b in range(bars):
        shapes.append(tuple((n, "".join(_cells(s)[b * per_bar:(b + 1) * per_bar])) for n, s in sorted(pattern.items())))
    return round(len(set(shapes)) / bars, 2)
