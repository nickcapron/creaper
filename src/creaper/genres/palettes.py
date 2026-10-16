"""Sound palettes: what each part of a genre sounds like, in the words of Arturia's preset
library (type, subtype, characteristics, genre tag) so audition_sounds can search it,
with a layer recipe, and what its drums measure like (for choosing samples).

Only the genres the user works in most are filled in so far; any other genre falls back
to its parent genre's palette, then to the role's plain type (a bass is a Bass). The
words are checked against the library in tests/test_genres.py when it's installed.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Sound:
    type: str                                 # the library's type: Bass, Pad, Lead, Keys...
    subtype: str | None = None                # e.g. "Sub Bass", "Classic Synth Pad"
    characteristics: tuple[str, ...] = ()     # sound and style words, e.g. ("Analog",), ("Warm",)
    genre: str | None = None                  # the library's genre tag, e.g. "Synthwave", "80s"
    layers: str = ""                          # how to layer it for weight


@dataclass(frozen=True)
class Drum:
    """What a drum sample measures like in the genre (samplelib.analyze's numbers).
    Calibrated against a real sample library (60 hits per lane, 10th-90th percentile):
    kicks sub_share 0.5-1.0 (median 0.95), decay 0.09-0.5 s, punch -4 to +6 dB (a kick's
    body peaks after its click); snares brightness 170-4400 Hz, decay 0.1-0.4 s; claps
    680-2500 Hz; closed hats 1300-10400 Hz (median 5300), decay 0.04-0.28 s."""
    sub_share: tuple[float, float] = (0.0, 1.0)      # energy share under 90 Hz
    decay_s: tuple[float, float] = (0.0, 5.0)        # time to fall 30 dB
    brightness_hz: tuple[float, float] = (0, 20000)  # spectral centroid
    punch_db: tuple[float, float] = (0.0, 60.0)      # rise in the first 5 ms


@dataclass(frozen=True)
class Palette:
    sounds: dict[str, Sound] = field(default_factory=dict)   # by audition role
    drums: dict[str, Drum] = field(default_factory=dict)     # kick, snare, clap, hat
    notes: str = ""


SUB_LAYER = "a mono sine or triangle sub an octave down, filtered mid layer on top (high-pass it near 120 Hz)"

PALETTES: dict[str, Palette] = {
    "synthwave": Palette(
        sounds={
            "bass": Sound("Bass", "Bass Line", ("Analog",), "Synthwave", "the octave-pulse bass on 8ths, with " + SUB_LAYER),
            "sub": Sound("Bass", "Sub Bass", ("Analog",), "80s"),
            "lead": Sound("Lead", "Poly Lead", ("Analog",), "Synthwave",
                          "an octave-down double 8 dB under it, tape delay on the lead"),
            "pad": Sound("Pad", "Classic Synth Pad", ("Analog",), "Synthwave",
                         "two pads, one high-passed at 300 Hz and wide"),
            "keys": Sound("Keys", "Classic Synth Keys", (), "80s"),
            "pluck": Sound("Keys", "Plucked Keys", (), "Synthwave"),
            "arp": Sound("Lead", "Plucked Lead", (), "Synthwave"),
            "strings": Sound("Strings", "Strings Pad", (), "80s"),
            "brass": Sound("Brass & Winds", "Brass Synth", (), "80s"),
            "bell": Sound("Keys", "Bells", (), "80s"),
        },
        drums={"kick": Drum(sub_share=(0.6, 1.0), decay_s=(0.12, 0.5), punch_db=(0, 60)),
               "snare": Drum(decay_s=(0.25, 0.9), brightness_hz=(900, 6000)),  # big gated/roomy snares
               "hat": Drum(decay_s=(0.02, 0.25), brightness_hz=(4000, 12000))},
        notes="LinnDrum/707-style machine drums with a gated-reverb snare; analog polysynths, wide chorus"),
    "house": Palette(
        sounds={
            "bass": Sound("Bass", "Bass Line", (), "House", "a short plucky bass with " + SUB_LAYER),
            "sub": Sound("Bass", "Sub Bass", (), "House"),
            "lead": Sound("Lead", "Plucked Lead", (), "House"),
            "pad": Sound("Pad", None, ("Warm",), "House", "sidechained to the kick"),
            "keys": Sound("Keys", None, ("Chord",), "House", "stab chords, short release"),
            "pluck": Sound("Keys", "Plucked Keys", (), "House"),
            "arp": Sound("Lead", "Plucked Lead", (), "House"),
            "strings": Sound("Strings", "String Ensemble", (), "Disco"),
            "brass": Sound("Brass & Winds", "Brass Synth", (), "Disco"),
            "bell": Sound("Keys", "Bells", (), "House"),
        },
        drums={"kick": Drum(sub_share=(0.6, 1.0), decay_s=(0.12, 0.45), punch_db=(0, 60)),
               "clap": Drum(decay_s=(0.1, 0.4), brightness_hz=(800, 4000)),
               "hat": Drum(decay_s=(0.02, 0.2), brightness_hz=(4500, 13000))},
        notes="909-style kick and claps, open hats on the offbeat"),
    "french house": Palette(
        sounds={
            "bass": Sound("Bass", "Bass Line", ("Filtered",), "Disco", "a funky filtered bass; " + SUB_LAYER),
            "lead": Sound("Lead", "Synced Lead", (), "House"),
            "pad": Sound("Pad", None, ("Filtered",), "Disco"),
            "keys": Sound("Electric Piano", "Classic EP", (), "Disco", "through a filter that opens across the build"),
            "strings": Sound("Strings", "String Ensemble", (), "Disco"),
            "brass": Sound("Brass & Winds", "Brass Synth", (), "Disco"),
        },
        drums={"kick": Drum(sub_share=(0.6, 1.0), decay_s=(0.12, 0.45), punch_db=(0, 60)),
               "snare": Drum(decay_s=(0.1, 0.4)),
               "hat": Drum(decay_s=(0.02, 0.25))},
        notes="filtered disco samples, compressed and pumping; vocoder or talk box hooks"),
    "trap": Palette(
        sounds={
            "bass": Sound("Bass", "Sub Bass", (), "Hip Hop/Trap", "an 808 with a little saturation for the mids"),
            "sub": Sound("Bass", "Sub Bass", (), "Hip Hop/Trap"),
            "lead": Sound("Lead", "Plucked Lead", ("Dark",), "Hip Hop/Trap"),
            "pad": Sound("Pad", None, ("Dark",), "Hip Hop/Trap"),
            "keys": Sound("Keys", "Bells", (), "Hip Hop/Trap"),
            "bell": Sound("Keys", "Bells", (), "Hip Hop/Trap"),
            "pluck": Sound("Keys", "Plucked Keys", (), "Hip Hop/Trap"),
        },
        drums={"kick": Drum(sub_share=(0.7, 1.0), decay_s=(0.2, 2.0)),  # 808 kicks ring
               "snare": Drum(decay_s=(0.08, 0.35), brightness_hz=(1000, 6000)),
               "clap": Drum(decay_s=(0.08, 0.35)),
               "hat": Drum(decay_s=(0.01, 0.12), brightness_hz=(5000, 14000))},
        notes="808 sub and kick, rolling hats, dark bells and plucks"),
    "boom bap": Palette(
        sounds={
            "bass": Sound("Bass", "Soft Bass", (), "Hip Hop/Trap"),
            "keys": Sound("Electric Piano", None, ("Dusty",), "Lofi"),
            "pad": Sound("Pad", None, ("Warm",), "Lofi"),
            "lead": Sound("Lead", "Soft Lead", (), "Hip Hop/Trap"),
        },
        drums={"kick": Drum(sub_share=(0.4, 1.0), decay_s=(0.08, 0.4)),
               "snare": Drum(decay_s=(0.1, 0.4), brightness_hz=(800, 5000)),
               "hat": Drum(decay_s=(0.02, 0.2), brightness_hz=(3000, 10000))},
        notes="dusty sampled drums, swung; Rhodes and jazz samples"),
    "cinematic": Palette(
        sounds={
            "bass": Sound("Bass", "Sub Bass", (), "Cinematic", "a low string or brass line doubled by a soft sub"),
            "sub": Sound("Bass", "Sub Bass", (), "Cinematic"),
            "pad": Sound("Pad", "Atmosphere", (), "Cinematic", "an evolving pad under real strings"),
            "strings": Sound("Strings", "String Ensemble", ("Orchestral",), None),
            "brass": Sound("Brass & Winds", "Brass Hybrid", (), "Cinematic"),
            "keys": Sound("Piano", "Acoustic Grand", (), None),
            "lead": Sound("Lead", "Soft Lead", (), "Cinematic"),
            "bell": Sound("Keys", "Mallets", (), "Cinematic"),
        },
        drums={"kick": Drum(sub_share=(0.5, 1.0), decay_s=(0.3, 3.0)),  # booms and taikos
               "snare": Drum(decay_s=(0.2, 2.0))},
        notes="orchestral and hybrid: strings, brass, big percussion, evolving pads"),
    "sci-fi score": Palette(
        sounds={
            "bass": Sound("Bass", "Hard Bass", (), "Soundtrack"),
            "sub": Sound("Bass", "Sub Bass", (), "Soundtrack"),
            "pad": Sound("Pad", "Evolving Pad", ("Sci-Fi",), None, "an evolving pad and a drone a fifth apart"),
            "lead": Sound("Lead", "Synced Lead", (), "Soundtrack"),
            "keys": Sound("Keys", "Evolving Keys", (), "Soundtrack"),
            "strings": Sound("Strings", "Strings Pad", (), "Soundtrack"),
            "brass": Sound("Brass & Winds", "Brass Hybrid", (), "Cinematic"),
            "bell": Sound("Keys", "Bells", ("Sci-Fi",), None),
        },
        drums={"kick": Drum(sub_share=(0.5, 1.0), decay_s=(0.2, 2.0))},
        notes="synths and processed orchestra; pulses, drones, metallic textures"),
}


def palette(genre) -> Palette | None:
    """The genre's palette, else its parent's (a few generations up)."""
    from . import find

    g, seen = genre, set()
    while g is not None and g.name not in seen:
        seen.add(g.name)
        if g.name in PALETTES:
            return PALETTES[g.name]
        try:
            g = find(g.parent) if g.parent else None
        except ValueError:
            g = None
    return None


def sound_for(genre, role: str) -> Sound | None:
    p = palette(genre)
    return p.sounds.get(role) if p else None
