"""The genre library: how each style is composed, played, arranged and mixed.

Each family lives in its own module (electronic_dance.py, jazz_blues.py, ...)
defining GENRES, a list of Genre. Everything here is a rule of thumb drawn from
the records that define a style, not a law: great music breaks these all the time.

Conventions inside a Genre:
- progressions are Roman numerals counted in the genre's first mode (modes[0]),
  e.g. "i-VI-III-VII" in minor is Am-F-C-G in A minor. Prefix a mode to use another
  one: "dorian: i-IV". Separate chords with "-". Numerals follow harmony.py
  (case = quality, 7/maj7/9/sus4/add9, °/ø/+, bVII, V7/V, inversions 6/64/65/43/42).
- harmonic_rhythm is chords per bar (0.5 = one chord every two bars).
- groove is a step pattern: {"step": 0.25, "swing": 50, "pattern": {lane: steps}}.
  Lanes are General MIDI drum names (kick, snare, clap, closed hat, open hat, ride,
  rim, shaker, conga...). Steps: x hit, X accent, o ghost, . rest; one or two bars.
- form is ((section, bars), ...) for a typical full-length arrangement.
"""

from __future__ import annotations

import importlib
import pkgutil
import re
from dataclasses import dataclass, field

FAMILIES = (
    "electronic dance", "electronic", "hip-hop", "r&b and soul", "pop", "rock", "metal and punk",
    "jazz", "blues", "funk and gospel", "country and folk", "latin", "caribbean", "african",
    "asian", "middle eastern", "european folk", "classical", "film and games", "ambient and experimental",
)

# Bass approaches the composer can play (see composer.bassline).
BASS_STYLES = (
    "none", "whole", "root", "eighths", "sixteenths", "root_fifth", "octaves", "walking", "808", "syncopated",
    "offbeat", "one_drop", "tumbao", "arpeggio", "pedal", "boogie", "motown", "alberti", "reese",
)
# Chord voicings (see composer.voice_chords).
VOICINGS = ("close", "open", "drop2", "drop3", "shell", "rootless", "quartal", "spread", "power", "cluster", "satb")
# Rhythms for chords (see composer.comp).
COMPING = (
    "none", "sustain", "half_notes", "quarters", "eighths", "offbeat", "skank", "stabs", "charleston", "bossa",
    "montuno", "strum", "arpeggio_up", "arpeggio_updown", "broken", "alberti", "pulse_16", "push", "tresillo",
    "waltz", "gospel",
)
DENSITIES = ("sparse", "medium", "busy")
LOW_END = ("light", "moderate", "heavy", "very heavy")
TONES = ("dark", "warm", "neutral", "bright")
WIDTHS = ("narrow", "moderate", "wide")


@dataclass(frozen=True)
class Mix:
    lufs: tuple[float, float]       # integrated loudness of a typical finished master
    lra: tuple[float, float]        # loudness range (LU)
    low_end: str                    # light / moderate / heavy / very heavy
    tone: str                       # dark / warm / neutral / bright
    width: str                      # narrow / moderate / wide
    true_peak: float = -1.0


@dataclass(frozen=True)
class Genre:
    name: str
    family: str
    description: str                # what it is and how it feels, 1-2 sentences
    mix: Mix
    aliases: tuple[str, ...] = ()
    parent: str | None = None       # the genre it grew out of, if any
    era: str = ""                   # where and when it took shape
    touchstones: tuple[str, ...] = ()  # defining artists, records or composers
    tempo: tuple[int, int] = (90, 120)
    meter: str = "4/4"
    feel: str = ""                  # straight, swung, shuffle, half-time, four-on-the-floor, clave...
    swing: float = 50               # 50 straight, ~58 light, ~66 triplet
    modes: tuple[str, ...] = ("minor",)
    keys: tuple[str, ...] = ()      # favourite keys, e.g. "E minor" for guitar music
    progressions: tuple[str, ...] = ()
    harmonic_rhythm: float = 1.0
    harmony: str = ""               # chord vocabulary and habits
    voicing: str = "close"
    comping: str = "sustain"
    bass_style: str = "root"
    bass: str = ""                  # how the bass behaves
    melody_density: str = "medium"
    melody_scale: str | None = None  # scale the melodies lean on, e.g. "minor pentatonic"
    melody: str = ""                # melodic habits: range, contour, hooks, phrasing
    groove: dict = field(default_factory=dict)
    drums: str = ""                 # how the drums are played and programmed
    form: tuple[tuple[str, int], ...] = ()
    instruments: tuple[str, ...] = ()
    sound_design: str = ""          # synth, sample and instrument tones
    production: str = ""            # mix and production habits
    theory: str = ""                # what's distinctive about its harmony, rhythm or melody

    @property
    def tempo_default(self) -> int:
        return round((self.tempo[0] + self.tempo[1]) / 2)


def _modules() -> list[str]:
    return sorted(m.name for m in pkgutil.iter_modules(__path__) if not m.name.startswith("_"))


LOAD_ERRORS: dict[str, str] = {}


def load() -> tuple[Genre, ...]:
    """Every family module's genres. A module that fails to import is skipped (and
    noted in LOAD_ERRORS) so one bad file can't take the whole server down."""
    genres: list[Genre] = []
    for name in _modules():
        try:
            module = importlib.import_module(f"{__name__}.{name}")
        except Exception as e:  # noqa: BLE001 - keep the rest of the library usable
            LOAD_ERRORS[name] = f"{type(e).__name__}: {e}"
            continue
        genres.extend(g for g in getattr(module, "GENRES", ()) if isinstance(g, Genre))
    return tuple(genres)


GENRES: tuple[Genre, ...] = load()


def norm(name: str) -> str:
    return re.sub(r"[\s_\-'’.&/]+", " ", name.strip().lower()).replace(" and ", " ").replace("n b", "nb").strip()


_INDEX: dict[str, Genre] = {}
for _g in GENRES:
    for _n in (_g.name, *_g.aliases):
        _INDEX.setdefault(norm(_n), _g)


def find(name: str) -> Genre:
    """Exact name or alias, then the closest partial match."""
    wanted = norm(name)
    if wanted in _INDEX:
        return _INDEX[wanted]
    for suffix in (" music", " style", " beat", " beats"):
        if wanted.endswith(suffix) and wanted[: -len(suffix)] in _INDEX:
            return _INDEX[wanted[: -len(suffix)]]
    partial = [g for key, g in _INDEX.items() if wanted in key or key in wanted]
    if partial:
        return min(partial, key=lambda g: (abs(len(norm(g.name)) - len(wanted)), g.name))
    words = set(wanted.split())
    scored = sorted(((len(words & set(key.split())), g) for key, g in _INDEX.items()), key=lambda x: -x[0])
    if scored and scored[0][0]:
        return scored[0][1]
    raise ValueError(f"no genre profile for '{name}'. Try list_genres to browse {len(GENRES)} genres.")


def search(text: str | None = None, family: str | None = None, tempo: float | None = None,
           mode: str | None = None) -> list[Genre]:
    out = []
    words = norm(text).split() if text else []
    for g in GENRES:
        if family and norm(family) not in norm(g.family):
            continue
        if tempo is not None and not (g.tempo[0] - 3 <= tempo <= g.tempo[1] + 3
                                      or g.tempo[0] - 3 <= tempo * 2 <= g.tempo[1] + 3
                                      or g.tempo[0] - 3 <= tempo / 2 <= g.tempo[1] + 3):
            continue
        if mode and not any(norm(mode) in norm(m) for m in g.modes):
            continue
        if words:
            hay = norm(" ".join((g.name, *g.aliases, g.family, g.description, g.era, " ".join(g.touchstones),
                                 g.feel, " ".join(g.instruments), g.sound_design, g.parent or "")))
            if not all(w in hay for w in words):
                continue
        out.append(g)
    return out


def validate(g: Genre) -> list[str]:
    """Problems with a genre entry (empty list = fine). Used by the tests."""
    from .. import harmony, scales, theory

    problems = []

    def bad(msg: str) -> None:
        problems.append(f"{g.name}: {msg}")

    if g.family not in FAMILIES:
        bad(f"family '{g.family}' isn't one of {FAMILIES}")
    if len(g.description) < 40:
        bad("description too short")
    lo, hi = g.tempo
    if not (30 <= lo <= hi <= 300):
        bad(f"tempo {g.tempo} out of range")
    if not 50 <= g.swing <= 75:
        bad("swing must be 50-75")
    if not re.fullmatch(r"\d+/\d+", g.meter):
        bad(f"meter '{g.meter}' should look like 4/4 or 12/8")
    for m in g.modes:
        try:
            scales.find_scale(m)
        except ValueError as e:
            bad(str(e))
    if g.melody_scale:
        try:
            scales.find_scale(g.melody_scale)
        except ValueError as e:
            bad(str(e))
    for k in g.keys:
        try:
            harmony.parse_key(k)
        except ValueError as e:
            bad(f"key '{k}': {e}")
    if len(g.progressions) < 2:
        bad("give at least two progressions")
    for p in g.progressions:
        mode = g.modes[0] if g.modes else "major"
        body = p
        if ":" in p:
            mode, _, body = p.partition(":")
        try:
            chords = harmony.parse_progression(body.strip(), harmony.parse_key(f"C {mode.strip()}"))
            if not chords:
                bad(f"empty progression '{p}'")
            for rc in chords:
                if "bb" in rc.chord.root_name or "##" in rc.chord.root_name:
                    bad(f"progression '{p}': {rc.numeral} lands on {rc.chord.root_name} in C, probably a wrong accidental")
        except ValueError as e:
            bad(f"progression '{p}': {e}")
    if g.harmonic_rhythm not in (0.25, 0.5, 1, 1.0, 2, 2.0, 4, 4.0):
        bad("harmonic_rhythm should be 0.25, 0.5, 1, 2 or 4 chords per bar")
    if g.voicing not in VOICINGS:
        bad(f"voicing '{g.voicing}' not in {VOICINGS}")
    if g.comping not in COMPING:
        bad(f"comping '{g.comping}' not in {COMPING}")
    if g.bass_style not in BASS_STYLES:
        bad(f"bass_style '{g.bass_style}' not in {BASS_STYLES}")
    if g.melody_density not in DENSITIES:
        bad(f"melody_density '{g.melody_density}' not in {DENSITIES}")
    groove = g.groove
    if not groove or "pattern" not in groove:
        bad("needs a groove with a pattern")
    else:
        step = groove.get("step", 0.25)
        lengths = set()
        for lane, steps in groove["pattern"].items():
            try:
                theory.drum_pitch(lane)
            except ValueError:
                bad(f"groove lane '{lane}' isn't a General MIDI drum name")
            cells = [c for c in steps if c not in " |"]
            lengths.add(len(cells))
            for c in cells:
                if c not in "xXog.-_" and not c.isdigit():
                    bad(f"groove lane '{lane}' has a bad step '{c}'")
        beats_per_bar = int(g.meter.split("/")[0]) * 4 / int(g.meter.split("/")[1])
        bar_steps = beats_per_bar / step
        for n in lengths:
            if abs(n / bar_steps - round(n / bar_steps)) > 1e-6 or round(n / bar_steps) not in (1, 2, 4):
                bad(f"groove lanes should be 1, 2 or 4 bars of {g.meter} ({bar_steps:g} steps per bar), got {n}")
        if not 50 <= groove.get("swing", 50) <= 75:
            bad("groove swing must be 50-75")
    if not g.form:
        bad("needs a form")
    for section, bars in g.form:
        if not section or not (1 <= bars <= 128):
            bad(f"form section {section!r} has {bars} bars")
    m = g.mix
    if not (-30 <= m.lufs[0] <= m.lufs[1] <= -4):
        bad(f"mix lufs {m.lufs} out of range")
    if not (1 <= m.lra[0] <= m.lra[1] <= 25):
        bad(f"mix lra {m.lra} out of range")
    if m.low_end not in LOW_END or m.tone not in TONES or m.width not in WIDTHS:
        bad("mix low_end/tone/width use the wrong words")
    for text_field in ("harmony", "bass", "melody", "drums", "sound_design", "production", "theory"):
        if len(getattr(g, text_field)) < 30:
            bad(f"{text_field} is missing or too short")
    if len(g.instruments) < 3:
        bad("list at least three instruments")
    if len(g.touchstones) < 2:
        bad("list at least two touchstones")
    return problems
