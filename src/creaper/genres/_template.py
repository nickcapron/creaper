"""A worked example of a genre entry (this module isn't loaded: its name starts with _)."""

from . import Genre, Mix

GENRES = [
    Genre(
        name="deep house",
        family="electronic dance",
        aliases=("deep",),
        parent="house",
        description="House's soulful, late-night side: warm jazz and gospel chords over a rolling four-on-the-floor "
                    "groove, more about mood and hypnotic swing than big drops.",
        era="Chicago and New Jersey, late 1980s; revived in the 2010s",
        touchstones=("Larry Heard", "Kerri Chandler", "Moodymann", "Theo Parrish"),
        tempo=(118, 125),
        feel="four-on-the-floor with a loose, swung shuffle in the hats and percussion",
        swing=56,
        modes=("minor", "dorian"),
        keys=("A minor", "F minor", "C minor"),
        progressions=(
            "i7-iv7",
            "i9-VII-VI-VII",
            "dorian: i7-IV9",
            "ii7-V9-Imaj7-vi7",
            "imaj9-iv9-bVIImaj7-IIImaj7",
        ),
        harmonic_rhythm=0.5,
        harmony="Minor 7ths, 9ths and 11ths borrowed from jazz and gospel; often a two-chord loop held for 2 bars "
                "each; organ and Rhodes stabs; sus chords for warmth rather than tension.",
        voicing="rootless",
        comping="stabs",
        bass_style="syncopated",
        bass="Round sub or Moog-style bass on the offbeats and the 'and' of beats, leaving room for the kick; "
             "octave jumps and the 5th; locked to the kick with gentle sidechain.",
        melody_density="sparse",
        melody_scale="minor pentatonic",
        melody="Sparse: chopped soulful vocal phrases, Rhodes or organ riffs, short call-and-response motifs that "
               "repeat for 8-16 bars with small changes.",
        groove={"step": 0.25, "swing": 56, "pattern": {
            "kick":       "x...x...x...x...",
            "clap":       "....x.......x...",
            "closed hat": "..x...x...x...x.",
            "shaker":     "xoxoxoxoxoxoxoxo",
        }},
        drums="909 or 808 kick on every beat, clap on 2 and 4, open or closed hats on the offbeats, swung shaker "
              "16ths; percussion (congas, rimshots) adds the shuffle; fills are filter or drop-outs, not rolls.",
        form=(("intro", 16), ("groove", 32), ("breakdown", 16), ("main", 32), ("break", 16), ("main", 32), ("outro", 16)),
        instruments=("drum machine (909/808)", "sub bass", "Rhodes or organ", "pad", "vocal chops", "percussion"),
        sound_design="Warm, slightly dusty: Rhodes and organ through chorus, soft analog pads with slow attack, "
                     "sine/triangle sub, tape saturation; filter sweeps on chords for movement.",
        production="Kick and bass own the low end (mono below 120 Hz), mid-heavy warmth, gentle bus compression; "
                   "DJ-friendly intros and outros in 16- or 32-bar phrases.",
        theory="Lives on extended minor chords and modal loops instead of functional cadences: the i7-iv7 vamp "
               "(dorian if the iv is a IV9) never resolves, which keeps the groove hypnotic.",
        mix=Mix(lufs=(-10, -7), lra=(4, 7), low_end="heavy", tone="warm", width="wide"),
    ),
]
