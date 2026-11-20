"""Sound design as creaper knows it: how sounds are built on a subtractive synth, in
units a musician and a meter share (milliseconds, hertz, cents, octaves), not in any one
synth's 0-127.

Three parts:

- METHOD: the loop. creaper can't hear, so a patch is designed against numbers that
  audition_hardware (or audition_instrument for a plugin) can measure.
- TECHNIQUES: the moves that make a sound more than a raw oscillator.
- SOUNDS: blueprints by name. Each says what the sound is, how it's built (a
  `blueprint` in the units above), how to play it, what a recording of it should
  measure, and what to change when it doesn't.

A blueprint is turned into one synth's parameters by that synth's profile
(`from_design`, using its measured calibration: microkorg.py is the first hardware
synth, plugin_design.py holds the plugins, Prophet-5 V first). A synth without a
profile still gets the blueprint: the model sets the nearest controls by name and
checks the result by measuring.

Blueprint fields (all optional; what's left out stays at the synth's plain sound):

    voices        "poly" | "mono" | "unison" (every voice on one note, detuned)
    unison_cents  spread of the unison voices
    glide_ms      time to slide an octave (mono and unison)
    legato        True: notes played overlapping don't restart the envelopes
    osc1, osc2    {"wave": saw | pulse | square | triangle | sine | noise, "level": 0-1,
                   "semitones": n, "cents": n (osc2 against osc1), "width": 0.5 = square .. 0.95 thin,
                   "pwm": 0-1 (LFO1 moves the width)}
    osc_mod       "sync" | "ring" (what osc2 does to/with osc1)
    noise         0-1
    filter        {"type": lp24 | lp12 | bp | hp, "cutoff_hz": n, "resonance": 0-1,
                   "env_octaves": how far the filter envelope opens it (negative closes),
                   "key_track": 0-1 (1 = follows the keys exactly), "velocity": 0-1}
    filter_env, amp_env   {"attack_ms", "decay_ms", "sustain": 0-1, "release_ms"}
                   (decay and release: the time to fall 20 dB)
    lfo1, lfo2    {"shape": triangle | saw | square | sine | random, "hz": n or "sync": "1/8",
                   "to": pitch | cutoff | amp | pan | width, "depth": semitones for pitch,
                   octaves for cutoff, 0-1 otherwise, "retrigger": True}
    pitch_env     {"semitones": n (negative falls up to the note), "decay_ms": n}: uses the
                   filter envelope's shape on most synths, so the two share one decay
    velocity_to_amp  0-1
    fx            {"chorus" | "ensemble" | "phaser": 0-1, "delay": {"sync": "1/8" or "ms": n, "mix": 0-1},
                   "distortion": True}
"""

from __future__ import annotations

from typing import Any

METHOD = [
    "Say the target in words a meter can check before touching a control: role, register, how fast it "
    "speaks (attack ms), whether it holds or dies away (decay s, sustain), how bright (centroid Hz), how it "
    "moves (glide, sweep, wobble, at what rate), how wide, how loud next to the song's other sounds.",
    "Start from the nearest blueprint (sound_design_guide) on the synth's plain sound, not from a preset "
    "somebody else made and not from the last patch.",
    "Build in this order, auditioning after each step: oscillators (the raw tone), filter (how bright, how "
    "much resonance), amp envelope (the shape in time), filter envelope (the movement at the start of each "
    "note), then LFOs and other modulation, then effects last. Effects hide faults in the steps before them.",
    "Change two or three things, then measure with the phrase the part will play (a low eighth-note line for "
    "a bass, held four-note chords for a pad, a line with jumps for a glide lead). One held middle C tells "
    "little about a bass or an arpeggio.",
    "Compare the numbers with the target, not with a feeling that it should be right: attack_ms, decay_s, "
    "release_s, centroid_hz, cents_off, level_db, stereo width, pitch over time. Fix the furthest one first.",
    "Check it where it will be used: the lowest and highest note of the part, soft and hard velocities, a "
    "chord of as many notes as the part plays (voices run out), and at the song's tempo for anything synced.",
    "Match levels between the sounds of one song before judging them: louder reads as better. A sound 15 dB "
    "under the others isn't weak, it's quiet.",
    "Measure chords as well as single notes before setting a level: four notes of a pad peak 8-12 dB over "
    "one, so a level set on a single note clips on the chord.",
    "A patch that measures well alone can still be the harsh part of a mix. Before a song uses it, look at "
    "how much of its energy sits at 2-5 kHz in the register the part plays (over about 15% in a part that "
    "isn't the lead, 25% in a lead, reads as piercing), and fix that in the patch: it is quicker than "
    "re-recording the part after the master refuses the mix.",
    "Keep what works: save the sound with its role, register and how to play it. Write down what you "
    "measured about the synth itself (a control that isn't linear, a range that stops early) in its profile "
    "or a note, so the next patch starts from facts.",
]

TECHNIQUES: dict[str, str] = {
    "detune": "Two oscillators a few cents apart beat slowly and sound bigger. 5-10 cents is a chorus-like "
              "shimmer that stays in tune in chords; 15-25 cents is a deliberately wide lead or hoover; over 30 "
              "reads as out of tune. The beat rate doubles every octave up: a detune that is lush at C3 is "
              "seasick at C6, so use less for high parts. Never trust a detune control to be even: measure it.",
    "unison": "Every voice on one note, spread in pitch. The fattest mono sound a small synth makes, and the "
              "loudest: it uses all the voices, so it can't play chords. 8-15 cents of spread for basses and "
              "leads; more only for effect.",
    "octaves and fifths": "Oscillator 2 an octave down adds weight (bass), an octave up adds edge (lead, "
                          "pluck), a fifth up (7 semitones) makes a hollow power-chord lead that only works "
                          "for single lines. Keep the added oscillator a little under the main one.",
    "pulse width": "A square (50%) is hollow and woody; narrower pulses get thinner and more nasal until "
                   "they vanish near 100%. Moving the width slowly with an LFO (PWM, 0.3-1.5 Hz) gives one "
                   "oscillator the motion of two detuned ones: the classic string and pad trick, and it "
                   "leaves the second oscillator free for an octave.",
    "filter envelope": "The shape of a note's brightness. A short decay (40-150 ms) from open to closed is a "
                       "pluck or a bass 'bite'; a slow attack (300 ms and up) is a swell or brass 'blat'. "
                       "Set the cutoff where the note should end up, then the envelope amount for how bright "
                       "it starts: the amount in octaves is what matters, not the knob number.",
    "resonance": "Emphasis at the cutoff. A little (10-25%) adds definition; around half it sings and makes "
                 "the envelope's sweep audible (acid, zaps); near the top the filter rings as a pitch of its "
                 "own, in tune only if it tracks the keyboard exactly. Resonance takes level away from the "
                 "low end on most filters: a resonant bass needs a sub under it or less resonance.",
    "key tracking": "How far the filter opens as notes go up. Without it high notes are dull and low notes "
                    "harsh. About half for most sounds; full (1:1) when the filter itself is the pitch or "
                    "the sound must keep the same colour across the keyboard.",
    "amp envelope": "Organ: instant on, full sustain, instant off. Piano and pluck: instant on, decays to "
                    "nothing while held. Strings and pads: 100-600 ms on, full sustain, 300-1500 ms off. "
                    "Brass: 30-80 ms on, sustain a little under full. A release shorter than 20 ms clicks; a "
                    "long release on a fast part smears every note into the next and eats voices.",
    "glide": "Portamento between notes, in mono or unison. Time it to the music: it should arrive within a "
             "sixteenth to an eighth note at the song's tempo, or lines sound flat and late. With legato "
             "on, only overlapped notes slide, so the player chooses where.",
    "vibrato and tremolo": "Vibrato is a 5-6.5 Hz triangle or sine LFO to pitch, 10-30 cents; faster or "
                           "deeper sounds nervous. Put it on the mod wheel or delay it so short notes stay "
                           "straight. Tremolo is the same LFO to level; to pan it becomes auto-pan.",
    "sync": "Oscillator 2 restarted by oscillator 1: its pitch then changes the tone, not the note. Sweep "
            "osc2's pitch with an envelope or LFO for the tearing 'sync lead'; turn osc1 down so only the "
            "synced oscillator is heard. It has a register: from about A4 up, the swept harmonics all land "
            "at 2-5 kHz and the lead pierces (measured: 30% of its energy there at G#4-A5, 14% an octave "
            "down). Write sync lines around G3-A4, or close the filter for higher ones.",
    "ring and cross modulation": "Multiplying or frequency-modulating two oscillators makes tones that "
                                 "aren't in the harmonic series: bells, metal, clangs. Tune osc2 to a fifth, "
                                 "an octave + fourth or a non-musical interval and listen; short envelopes "
                                 "make bells and percussion, long ones make drones. Smooth waves into a ring "
                                 "modulator make a dull thud; saws make metal. Cross-modulation depth from "
                                 "velocity turns harsh fast in chords (an electric piano's 'bark' measured "
                                 "half its energy at 2-5 kHz): keep velocity's share small and let an "
                                 "envelope make the clang fade before the tone.",
    "noise": "A little noise (5-15%) is breath on a flute or lead and air on a pad. A lot, through a "
             "band-pass or resonant filter with an envelope, is wind, surf, snares, hats and risers. A "
             "noise layer under a pitched one shouldn't follow the keyboard: up high it turns into hiss "
             "louder than the note.",
    "velocity": "Harder notes brighter (velocity to cutoff) sounds more alive than harder notes only louder. "
                "Parts written by a tool carry accents in their velocities: a patch that ignores velocity "
                "flattens them.",
    "layering": "Two timbres for two jobs: a body (dark, steady) and a top (bright, short), or a pad with a "
                "slow twin an octave up. On a small synth a layer halves the voices: fine for leads and "
                "basses, costly for chords.",
    "width": "Chorus and ensemble make a mono synth wide; unsynced LFOs to pan do too. Basses stay mono in the low end: no "
             "ordinary chorus on anything that carries it (at most a mostly dry Dimension-style widener, with the "
             "mix's low-end mono compatibility checked after). Width is measured (stereo_width_db), not assumed.",
    "tempo": "Synced delays (1/8, dotted 1/8 = 3/16), synced LFOs and arpeggios must run at the song's "
             "tempo: a patch carries its own tempo on most hardware. Dotted-eighth delay under sixteenth "
             "plucks is the instant 'more notes than you played' trick.",
    "making room": "A patch is judged in the song. Pads lose low end (the bass has it) and some 2-4 kHz "
                   "(the lead and voice have it); a lead is brighter than the pad under it; two sounds in "
                   "the same octave need different attacks or brightness to be told apart.",
    "distortion": "Drive after the filter puts back the top the filter took off: closing the cutoff on a "
                  "distorted bass doesn't make it less fizzy (measured: no change at 2-5 kHz). Turn the drive "
                  "off, or cut the top after the synth, in the mix.",
    "game sounds": "A game's interface and event sounds are one set heard thousands of times: design them by "
                   "slot-machine rules. Every pitched sound in one key, chosen once (open fifths, fourths and "
                   "seconds), so any two that overlap never clash. Good news rises, and the bigger the news the "
                   "higher and longer the rise: two notes for a small success, a run up an octave or more for a "
                   "big one. Bad news never buzzes: a low soft toll, lower and longer the graver the loss, with "
                   "a voice an octave up so small speakers still carry it. The most frequent sounds are the "
                   "shortest and quietest (hover, click: a soft tick of 20-60 ms, 6-12 dB under the rest). "
                   "Bell-family voices (mallets, chimes, soft bells: bell presets or the 'bell' blueprint) and "
                   "one shared reverb, a plate, make it one set. Bare synth blips, two-note jingles and dry "
                   "'glassy' partials on one voice were heard as cheap and arcade on a real game's set. For a "
                   "darker game (sci-fi, war, strategy): a minor key in stacked fourths and bare fifths, no major "
                   "thirds; one uneasy interval (a tritone or a semitone) in every loss; a low thud under anything "
                   "with weight (orders, construction, losses); a slow airy swell under the big moments; chimes "
                   "an octave lower and a longer, darker plate. Each sound's notes go in their own region named "
                   "as its file; export_regions at the game's sample rate, in three calls by size: big events "
                   "at peak_db -6, ordinary ones -9, the frequent ticks -14 (one peak for all makes a click as "
                   "loud as a defeat).",
    "level": "When the amp is at its top and the patch is still quiet (sines, cross-modulation and digital "
             "waves often are), an EQ can lift it: two shelves that meet at the same frequency, both raised, "
             "are a gain stage. Then check a chord: it must still not clip.",
}

_PLUCK_ENV = {"attack_ms": 1, "decay_ms": 220, "sustain": 0.0, "release_ms": 180}
_ORGAN_ENV = {"attack_ms": 2, "decay_ms": 0, "sustain": 1.0, "release_ms": 30}

SOUNDS: dict[str, dict[str, Any]] = {
    # ------------------------------------------------------------------ basses
    "sub bass": {
        "family": "bass", "aka": ["sine bass", "808-style sub"],
        "what": "A pure low tone felt more than heard, under another bass or alone in sparse music.",
        "blueprint": {"voices": "mono", "legato": True, "osc1": {"wave": "sine", "level": 1.0},
                      "filter": {"type": "lp24", "cutoff_hz": 400, "resonance": 0.0, "key_track": 0.5},
                      "amp_env": {"attack_ms": 4, "decay_ms": 0, "sustain": 1.0, "release_ms": 60}},
        "play": "C1-C2, one note at a time.",
        "check": {"attack_ms": "under 15", "centroid_hz": "under 150", "cents_off": "within 5"},
        "if": {"it clicks at the start or end": "raise the amp attack to 5-10 ms and the release to 50-80 ms",
               "it can't be heard on small speakers": "that's what a sub is: add a mid layer (saw bass an octave "
                                                      "up, quietly) or a little distortion for harmonics",
               "notes sound different in level": "the filter is too low or resonant: open it or track the keys"},
    },
    "saw bass": {
        "family": "bass", "aka": ["analog bass", "eighth-note bass", "synth bass"],
        "what": "The all-purpose analogue bass: a saw (often with a square under it) and a filter that bites "
                "at the start of each note.",
        "blueprint": {"voices": "mono", "osc1": {"wave": "saw", "level": 1.0},
                      "osc2": {"wave": "square", "level": 0.8, "semitones": 0, "cents": 4},
                      "filter": {"type": "lp24", "cutoff_hz": 350, "resonance": 0.2, "env_octaves": 2.5,
                                 "key_track": 0.4, "velocity": 0.3},
                      "filter_env": {"attack_ms": 1, "decay_ms": 160, "sustain": 0.25, "release_ms": 80},
                      "amp_env": {"attack_ms": 1, "decay_ms": 400, "sustain": 0.75, "release_ms": 50}},
        "play": "C1-C3: driving eighths on the roots, or a melodic line.",
        "check": {"attack_ms": "under 10", "centroid_hz": "250-900 (darker for dub, brighter for rock)",
                  "energy": "most below 250 Hz, a clear share at 250-2000 Hz so it reads on small speakers"},
        "if": {"it's a dull thud": "raise the cutoff or the envelope amount, or lengthen the filter decay",
               "it's all buzz and no weight": "lower the cutoff, or put osc2 an octave down",
               "it disappears in the mix": "brighter (it needs 700 Hz-2 kHz), not louder",
               "notes blur at fast tempos": "shorten the amp decay and release"},
    },
    "square bass": {
        "family": "bass", "aka": ["hollow bass", "pulse bass"],
        "what": "Two squares or pulses: hollow, growling, more aggressive than a saw bass.",
        "blueprint": {"voices": "mono", "osc1": {"wave": "pulse", "width": 0.5, "level": 1.0},
                      "osc2": {"wave": "square", "level": 1.0, "cents": 6},
                      "filter": {"type": "lp24", "cutoff_hz": 250, "resonance": 0.28, "env_octaves": 3.0, "key_track": 0.4},
                      "filter_env": {"attack_ms": 1, "decay_ms": 260, "sustain": 0.4, "release_ms": 80},
                      "amp_env": {"attack_ms": 1, "decay_ms": 500, "sustain": 0.8, "release_ms": 40}},
        "play": "C1-C3; long notes growl, short ones punch.",
        "check": {"attack_ms": "under 10", "centroid_hz": "300-1500"},
        "if": {"it's thin": "widen toward 50% (a square), or drop osc2 an octave",
               "it's harsh": "less resonance, lower cutoff; a square's odd harmonics get edgy above 2 kHz"},
    },
    "acid bass": {
        "family": "bass", "aka": ["303", "squelch bass"],
        "what": "One oscillator into a resonant filter that an envelope snaps shut: the squelch is the "
                "resonance tracing the envelope. Slides and accents are in how it's played.",
        "blueprint": {"voices": "mono", "legato": True, "glide_ms": 60, "osc1": {"wave": "saw", "level": 1.0},
                      "filter": {"type": "lp24", "cutoff_hz": 300, "resonance": 0.7, "env_octaves": 3.5,
                                 "key_track": 0.3, "velocity": 0.6},
                      "filter_env": {"attack_ms": 1, "decay_ms": 180, "sustain": 0.0, "release_ms": 120},
                      "amp_env": {"attack_ms": 1, "decay_ms": 300, "sustain": 0.6, "release_ms": 40},
                      "fx": {"distortion": True}},
        "play": "C1-C3 sixteenths; overlap two notes for a slide, hit some harder for accents.",
        "check": {"pitch_over_time": "steady (the squelch is in the tone, not the pitch)",
                  "centroid_hz": "falls within each note"},
        "if": {"no squelch": "more resonance and more envelope amount; shorten the filter decay",
               "the low end vanished": "resonance thins the bottom: back it off or add a sub",
               "it whistles": "the filter is self-oscillating: resonance down a little"},
    },
    "reese bass": {
        "family": "bass", "aka": ["detuned bass", "dnb bass"],
        "what": "Two or more detuned saws, low-passed, so the beating between them is the movement.",
        "blueprint": {"voices": "unison", "unison_cents": 14, "legato": True,
                      "osc1": {"wave": "saw", "level": 1.0}, "osc2": {"wave": "saw", "level": 1.0, "cents": 9},
                      "filter": {"type": "lp24", "cutoff_hz": 500, "resonance": 0.15, "key_track": 0.3},
                      "amp_env": {"attack_ms": 5, "decay_ms": 0, "sustain": 1.0, "release_ms": 120},
                      "lfo2": {"shape": "sine", "hz": 0.25, "to": "cutoff", "depth": 0.6}},
        "play": "Long notes C1-C2.",
        "check": {"level over time": "beats slowly; that's the sound", "centroid_hz": "300-800"},
        "if": {"the bass drops out every so often": "the beating cancels the fundamental: less detune, or a "
                                                    "steady sub under it",
               "it's static": "move the cutoff slowly with an LFO"},
    },
    # ------------------------------------------------------------------- leads
    "saw lead": {
        "family": "lead", "aka": ["unison lead", "fat lead", "trance lead"],
        "what": "Detuned saws in unison: loud, bright, cuts through anything.",
        "blueprint": {"voices": "unison", "unison_cents": 12, "legato": True, "glide_ms": 40,
                      "osc1": {"wave": "saw", "level": 1.0}, "osc2": {"wave": "saw", "level": 1.0, "cents": 8},
                      "filter": {"type": "lp24", "cutoff_hz": 6000, "resonance": 0.15, "key_track": 0.5},
                      "amp_env": {"attack_ms": 2, "decay_ms": 0, "sustain": 1.0, "release_ms": 150},
                      "lfo1": {"shape": "triangle", "hz": 5.8, "to": "pitch", "depth": 0.0},
                      "fx": {"delay": {"sync": "1/8", "mix": 0.2}}},
        "play": "A single line, C4-C6. Vibrato from the mod wheel on long notes.",
        "check": {"attack_ms": "under 20", "centroid_hz": "1500-3500", "cents_off": "within 10"},
        "if": {"it's piercing": "cutoff down to 3-4 kHz; unison saws carry a lot above 5 kHz",
               "it's seasick up high": "less detune: beating doubles each octave up",
               "lines sound late": "the glide is too long for the tempo"},
    },
    "glide lead": {
        "family": "lead", "aka": ["portamento lead", "phaser lead", "west coast lead"],
        "what": "A mono lead whose slides between notes are the hook, often through a phaser.",
        "blueprint": {"voices": "unison", "unison_cents": 10, "legato": True, "glide_ms": 90,
                      "osc1": {"wave": "saw", "level": 1.0}, "osc2": {"wave": "saw", "level": 1.0, "cents": 8},
                      "filter": {"type": "lp24", "cutoff_hz": 4500, "resonance": 0.15, "key_track": 0.5},
                      "amp_env": {"attack_ms": 2, "decay_ms": 0, "sustain": 1.0, "release_ms": 120},
                      "fx": {"phaser": 0.75, "delay": {"ms": 300, "mix": 0.18}}},
        "play": "Lines with jumps of a fifth or more, notes overlapped where a slide is wanted.",
        "check": {"pitch_over_time": "reaches each note (within 20 cents) before the next one starts"},
        "if": {"it never lands on the notes": "shorten the glide: an octave should take less than an eighth note",
               "no slides are heard": "the notes aren't overlapping (legato), or turn legato off to slide always"},
    },
    "sync lead": {
        "family": "lead", "aka": ["hard sync", "tearing lead"],
        "what": "Oscillator 2 synced to oscillator 1 with its pitch swept by an envelope: a vocal, tearing "
                "attack on every note.",
        "blueprint": {"voices": "mono", "osc_mod": "sync", "osc1": {"wave": "saw", "level": 0.0},
                      "osc2": {"wave": "saw", "level": 1.0, "semitones": 12},
                      "pitch_env": {"semitones": 19, "decay_ms": 350, "to": "osc2"},
                      "filter": {"type": "lp24", "cutoff_hz": 8000, "resonance": 0.1, "key_track": 0.5},
                      "amp_env": {"attack_ms": 2, "decay_ms": 0, "sustain": 1.0, "release_ms": 150}},
        "play": "C3-C5, notes long enough for the sweep to finish.",
        "check": {"centroid_hz": "falls through each note", "cents_off": "within 10 (the note stays in tune: "
                                                                          "only the tone sweeps)"},
        "if": {"the pitch itself bends": "the envelope is going to both oscillators: route it to osc2 only",
               "no tearing": "sync isn't on, or osc1 is still in the mix masking it"},
    },
    "square lead": {
        "family": "lead", "aka": ["chiptune lead", "hollow lead", "pwm lead"],
        "what": "A pulse wave, hollow and clear; with slow width movement it sings.",
        "blueprint": {"voices": "mono", "legato": True, "glide_ms": 30,
                      "osc1": {"wave": "pulse", "width": 0.55, "pwm": 0.35, "level": 1.0},
                      "filter": {"type": "lp12", "cutoff_hz": 5000, "resonance": 0.1, "key_track": 0.6},
                      "amp_env": {"attack_ms": 3, "decay_ms": 0, "sustain": 1.0, "release_ms": 100},
                      "lfo1": {"shape": "triangle", "hz": 0.8, "to": "width", "depth": 0.35}},
        "play": "C4-C6.", "check": {"attack_ms": "under 20", "centroid_hz": "1200-3000"},
        "if": {"it thins out and vanishes in cycles": "too much width movement: the pulse is reaching 100%"},
    },
    "hoover": {
        "family": "lead", "aka": ["rave lead", "dominator"],
        "what": "Detuned saws across octaves with a pitch swoop into every note and heavy chorus.",
        "blueprint": {"voices": "unison", "unison_cents": 25, "osc1": {"wave": "saw", "level": 1.0},
                      "osc2": {"wave": "saw", "level": 1.0, "semitones": -12, "cents": 12},
                      "pitch_env": {"semitones": -5, "decay_ms": 120},
                      "filter": {"type": "lp12", "cutoff_hz": 5000, "resonance": 0.2},
                      "amp_env": {"attack_ms": 5, "decay_ms": 0, "sustain": 1.0, "release_ms": 200},
                      "fx": {"ensemble": 0.9}},
        "play": "Stabs and held notes C3-C5.", "check": {"pitch_over_time": "rises into the note in about 0.1 s"},
        "if": {"it's a mess": "that's most of it; less detune if the pitch can't be told"},
    },
    # -------------------------------------------------------------------- pads
    "string pad": {
        "family": "pad", "aka": ["strings", "dual saw strings", "string machine"],
        "what": "Two detuned saws with a slow-ish swell and ensemble chorus: synth strings.",
        "blueprint": {"voices": "poly", "osc1": {"wave": "saw", "level": 1.0},
                      "osc2": {"wave": "saw", "level": 1.0, "cents": 8},
                      "filter": {"type": "lp24", "cutoff_hz": 3500, "resonance": 0.05, "key_track": 0.4},
                      "amp_env": {"attack_ms": 180, "decay_ms": 0, "sustain": 0.9, "release_ms": 450},
                      "fx": {"ensemble": 0.7}},
        "play": "Held chords of as many notes as the synth has voices, C3-C6.",
        "check": {"attack_ms": "120-350", "release_s": "0.3-0.8", "stereo_width_db": "above -12",
                  "cents_off": "within 10 on a single note"},
        "if": {"it sounds out of tune": "the detune is too wide (keep it under 10 cents for chords), or it's a "
                                        "control that isn't even: measure osc2 alone",
               "chords cut off": "more notes than voices, or a release so long that old notes hold them",
               "it's dull under the song": "open the filter; pads lose their top first in a mix",
               "it's too slow for the part": "shorten the attack, or use a stab sound for rhythmic chords"},
    },
    "warm pad": {
        "family": "pad", "aka": ["soft pad", "analog pad"],
        "what": "A dark, slow, unobtrusive bed: low-passed saws or a saw and a triangle.",
        "blueprint": {"voices": "poly", "osc1": {"wave": "saw", "level": 1.0},
                      "osc2": {"wave": "triangle", "level": 0.8, "semitones": 12, "cents": 6},
                      "filter": {"type": "lp24", "cutoff_hz": 900, "resonance": 0.1, "env_octaves": 1.0, "key_track": 0.5},
                      "filter_env": {"attack_ms": 900, "decay_ms": 1500, "sustain": 0.6, "release_ms": 900},
                      "amp_env": {"attack_ms": 500, "decay_ms": 0, "sustain": 1.0, "release_ms": 900},
                      "fx": {"chorus": 0.5}},
        "play": "Long chords C3-C5.", "check": {"attack_ms": "300-900", "centroid_hz": "400-1200"},
        "if": {"it's muddy": "it has too much 150-400 Hz: play it higher, or thin the low notes of the chord"},
    },
    "pwm pad": {
        "family": "pad", "aka": ["pulse pad", "juno pad"],
        "what": "One pulse per voice with its width moving slowly: rich like two oscillators, but it keeps "
                "the second oscillator free and stays in tune.",
        "blueprint": {"voices": "poly", "osc1": {"wave": "pulse", "width": 0.6, "pwm": 0.5, "level": 1.0},
                      "osc2": {"wave": "saw", "level": 0.4, "semitones": 12},
                      "filter": {"type": "lp24", "cutoff_hz": 2500, "resonance": 0.08, "key_track": 0.5},
                      "amp_env": {"attack_ms": 250, "decay_ms": 0, "sustain": 1.0, "release_ms": 700},
                      "lfo1": {"shape": "triangle", "hz": 0.6, "to": "width", "depth": 0.5},
                      "fx": {"chorus": 0.6}},
        "play": "Chords C3-C5.", "check": {"attack_ms": "150-400", "cents_off": "within 5"},
        "if": {"it wobbles in pitch": "PWM that's too deep or fast sounds like detune: slow it under 1 Hz"},
    },
    "sweep pad": {
        "family": "pad", "aka": ["filter sweep", "evolving pad"],
        "what": "A pad whose filter opens slowly over bars, by a very slow LFO or a long envelope.",
        "blueprint": {"voices": "poly", "osc1": {"wave": "saw", "level": 1.0},
                      "osc2": {"wave": "saw", "level": 1.0, "cents": 8},
                      "filter": {"type": "lp24", "cutoff_hz": 500, "resonance": 0.35, "key_track": 0.3},
                      "amp_env": {"attack_ms": 400, "decay_ms": 0, "sustain": 1.0, "release_ms": 1200},
                      "lfo2": {"shape": "sine", "hz": 0.08, "to": "cutoff", "depth": 2.5},
                      "fx": {"ensemble": 0.6, "delay": {"sync": "1/4", "mix": 0.2}}},
        "play": "One chord held for 4-8 bars.", "check": {"centroid_hz": "rises and falls over the chord"},
        "if": {"the sweep doesn't line up with the bars": "sync the LFO to the tempo (1/1 or slower) and "
                                                         "retrigger it with the chord"},
    },
    # -------------------------------------------------- plucks, keys and stabs
    "pluck": {
        "family": "keys", "aka": ["synth pluck", "arp pluck", "sequence"],
        "what": "A short bright note that dies away by itself: for arpeggios and sixteenth-note figures.",
        "blueprint": {"voices": "poly", "osc1": {"wave": "pulse", "width": 0.6, "level": 1.0},
                      "osc2": {"wave": "saw", "level": 0.6, "cents": 6},
                      "filter": {"type": "lp12", "cutoff_hz": 700, "resonance": 0.25, "env_octaves": 3.0,
                                 "key_track": 0.5, "velocity": 0.4},
                      "filter_env": {"attack_ms": 1, "decay_ms": 160, "sustain": 0.0, "release_ms": 160},
                      "amp_env": dict(_PLUCK_ENV),
                      "fx": {"delay": {"sync": "3/16", "mix": 0.3}}},
        "play": "Broken chords in sixteenths, C4-C6.",
        "check": {"attack_ms": "under 10", "decay_s": "0.1-0.4", "sustain": "none"},
        "if": {"notes run together": "shorter amp decay and release; less delay",
               "it's all click": "the filter decay is shorter than the amp decay by too much: lengthen it",
               "it's thin and fizzy": "lower the cutoff and resonance, drop the octave-up oscillator"},
    },
    "stab": {
        "family": "keys", "aka": ["chord stab", "poly synth", "comp synth"],
        "what": "Chords that speak at once: for rhythmic comping where a pad would smear.",
        "blueprint": {"voices": "poly", "osc1": {"wave": "saw", "level": 1.0},
                      "osc2": {"wave": "saw", "level": 0.9, "cents": 6},
                      "filter": {"type": "lp12", "cutoff_hz": 1800, "resonance": 0.12, "env_octaves": 2.0,
                                 "key_track": 0.4, "velocity": 0.4},
                      "filter_env": {"attack_ms": 1, "decay_ms": 220, "sustain": 0.0, "release_ms": 120},
                      "amp_env": {"attack_ms": 1, "decay_ms": 500, "sustain": 0.6, "release_ms": 90},
                      "fx": {"chorus": 0.3}},
        "play": "Short chords of up to the synth's voices, C3-C5.",
        "check": {"attack_ms": "under 10", "release_s": "under 0.2"},
        "if": {"chords lose notes": "the release holds voices: shorten it"},
    },
    "organ": {
        "family": "keys", "aka": ["drawbar organ", "combo organ"],
        "what": "On/off notes with no envelope shape: stacked sines or a hollow pulse, with a fast rotary-like "
                "tremolo or chorus.",
        "blueprint": {"voices": "poly", "osc1": {"wave": "sine", "level": 1.0},
                      "osc2": {"wave": "triangle", "level": 0.7, "semitones": 12},
                      "filter": {"type": "lp12", "cutoff_hz": 5000, "resonance": 0.0, "key_track": 0.3},
                      "amp_env": dict(_ORGAN_ENV), "fx": {"chorus": 0.5}},
        "play": "Chords and lines C3-C6.", "check": {"attack_ms": "under 10", "sustain": "full"},
        "if": {"it clicks": "organs click a little; if too much, 5 ms of attack and 30 ms of release"},
    },
    "electric piano": {
        "family": "keys", "aka": ["ep", "tine piano", "bell piano"],
        "what": "A soft bell-like attack over a mellow body that decays slowly.",
        "blueprint": {"voices": "poly", "osc1": {"wave": "triangle", "level": 1.0},
                      "osc2": {"wave": "triangle", "level": 0.35, "semitones": 24},
                      "filter": {"type": "lp12", "cutoff_hz": 1500, "resonance": 0.05, "env_octaves": 1.5,
                                 "key_track": 0.6, "velocity": 0.6},
                      "filter_env": {"attack_ms": 1, "decay_ms": 500, "sustain": 0.2, "release_ms": 300},
                      "amp_env": {"attack_ms": 2, "decay_ms": 1800, "sustain": 0.0, "release_ms": 300},
                      "velocity_to_amp": 0.5, "fx": {"chorus": 0.35}},
        "play": "Chords and comping C3-C5.", "check": {"decay_s": "0.8-2.5", "attack_ms": "under 15"},
        "if": {"it sounds like an organ": "it needs the decay to nothing and velocity on the brightness"},
    },
    "bell": {
        "family": "keys", "aka": ["chime", "fm bell", "metallic"],
        "what": "Inharmonic partials from ring or cross modulation with a long decay.",
        "blueprint": {"voices": "poly", "osc_mod": "ring", "osc1": {"wave": "sine", "level": 0.6},
                      "osc2": {"wave": "triangle", "level": 1.0, "semitones": 19},
                      "filter": {"type": "lp12", "cutoff_hz": 7000, "resonance": 0.0, "key_track": 0.6},
                      "amp_env": {"attack_ms": 1, "decay_ms": 2200, "sustain": 0.0, "release_ms": 1500},
                      "fx": {"delay": {"sync": "1/4", "mix": 0.2}}},
        "play": "Single notes and open intervals C4-C6.",
        "check": {"decay_s": "1-3", "clarity": "lower than a plain tone (it's inharmonic)"},
        "if": {"it's a plain tone": "ring modulation isn't on, or osc2 is at a simple interval: try 19, 17 or "
                                    "14 semitones",
               "it's clangy noise": "a simpler interval (7 or 12 semitones), or less of the modulated oscillator"},
    },
    "brass": {
        "family": "keys", "aka": ["synth brass", "brass stab"],
        "what": "Saws whose filter opens just after the note starts: the 'blat'.",
        "blueprint": {"voices": "poly", "osc1": {"wave": "saw", "level": 1.0},
                      "osc2": {"wave": "saw", "level": 1.0, "cents": 7},
                      "filter": {"type": "lp24", "cutoff_hz": 500, "resonance": 0.1, "env_octaves": 2.8,
                                 "key_track": 0.4, "velocity": 0.5},
                      "filter_env": {"attack_ms": 60, "decay_ms": 400, "sustain": 0.6, "release_ms": 200},
                      "amp_env": {"attack_ms": 25, "decay_ms": 0, "sustain": 0.9, "release_ms": 180}},
        "play": "Stabs and held chords C3-C5.", "check": {"attack_ms": "30-90", "centroid_hz": "rises in the first 0.1 s"},
        "if": {"it's a string pad": "the filter attack is too slow or the amp attack too long",
               "it's a stab": "the filter attack is zero: brass swells into the note"},
    },
    # ---------------------------------------------------------------- effects
    "riser": {
        "family": "fx", "aka": ["noise sweep", "uplifter", "build"],
        "what": "Noise (and often a rising tone) through a filter that opens over bars, into a section change.",
        "blueprint": {"voices": "mono", "osc1": {"wave": "saw", "level": 0.0}, "noise": 1.0,
                      "filter": {"type": "bp", "cutoff_hz": 300, "resonance": 0.45, "env_octaves": 5.0},
                      "filter_env": {"attack_ms": 6000, "decay_ms": 0, "sustain": 1.0, "release_ms": 100},
                      "amp_env": {"attack_ms": 3000, "decay_ms": 0, "sustain": 1.0, "release_ms": 60}},
        "play": "One note held for the length of the build (2, 4 or 8 bars), released on the downbeat.",
        "check": {"centroid_hz": "rises all the way", "level": "rises all the way"},
        "if": {"it peaks early": "the envelope is shorter than the build: time the attack to the bars"},
    },
    "zap": {
        "family": "fx", "aka": ["laser", "pew", "drop"],
        "what": "A pitch that falls fast: the envelope to pitch is the whole sound.",
        "blueprint": {"voices": "mono", "osc1": {"wave": "pulse", "width": 0.6, "level": 1.0},
                      "pitch_env": {"semitones": 36, "decay_ms": 120},
                      "filter": {"type": "lp12", "cutoff_hz": 7000, "resonance": 0.35},
                      "amp_env": {"attack_ms": 1, "decay_ms": 180, "sustain": 0.0, "release_ms": 120}},
        "play": "Short notes C4-C6.", "check": {"pitch_glide": "above 1.5", "sounds_for_seconds": "0.1-0.4"},
        "if": {"it's a blip": "more pitch range or a longer decay", "it's a siren": "shorter decay"},
    },
    "siren": {
        "family": "fx", "aka": ["alarm", "wobble"],
        "what": "An LFO moving the pitch: square for two-tone alarms, triangle or saw for sirens.",
        "blueprint": {"voices": "mono", "osc1": {"wave": "pulse", "width": 0.6, "level": 1.0},
                      "lfo1": {"shape": "triangle", "hz": 0.8, "to": "pitch", "depth": 7, "retrigger": True},
                      "filter": {"type": "bp", "cutoff_hz": 2000, "resonance": 0.3},
                      "amp_env": dict(_ORGAN_ENV)},
        "play": "One held note.", "check": {"pitch_over_time": "swings at the LFO's rate"},
        "if": {"each note starts somewhere else in the sweep": "retrigger the LFO at the note"},
    },
    "wind": {
        "family": "fx", "aka": ["noise", "surf", "atmosphere"],
        "what": "Filtered noise with slow random or sine movement on the filter.",
        "blueprint": {"voices": "mono", "osc1": {"wave": "saw", "level": 0.0}, "noise": 1.0,
                      "filter": {"type": "bp", "cutoff_hz": 900, "resonance": 0.45},
                      "lfo2": {"shape": "sine", "hz": 0.15, "to": "cutoff", "depth": 1.5},
                      "amp_env": {"attack_ms": 800, "decay_ms": 0, "sustain": 1.0, "release_ms": 1500}},
        "play": "One held note.", "check": {"clarity": "near 0 (noise)", "centroid_hz": "wanders"},
        "if": {"it whistles a note": "resonance too high for wind; good for a howl"},
    },
    # ------------------------------------------------------------ synth drums
    "synth kick": {
        "family": "drums", "aka": ["analog kick", "808 kick"],
        "what": "A sine whose pitch drops from a click to a thud in a few hundredths of a second.",
        "blueprint": {"voices": "mono", "osc1": {"wave": "sine", "level": 1.0},
                      "pitch_env": {"semitones": 30, "decay_ms": 45},
                      "filter": {"type": "lp24", "cutoff_hz": 3000, "resonance": 0.0},
                      "amp_env": {"attack_ms": 1, "decay_ms": 280, "sustain": 0.0, "release_ms": 150}},
        "play": "One short note around C1-E1 per hit.",
        "check": {"attack_ms": "under 5", "pitch_glide": "above 2", "decay_s": "0.15-0.5"},
        "if": {"no punch": "more pitch range, shorter pitch decay (30-50 ms)", "it's a tom": "play it lower, "
               "less pitch range", "it's a long boom": "shorter amp decay unless an 808 is wanted"},
    },
    "synth snare": {
        "family": "drums", "aka": ["noise snare", "analog snare"],
        "what": "A short tone for the drum's body and a burst of noise for the wires.",
        "blueprint": {"voices": "mono", "osc1": {"wave": "triangle", "level": 0.6}, "noise": 1.0,
                      "pitch_env": {"semitones": 12, "decay_ms": 40},
                      "filter": {"type": "bp", "cutoff_hz": 2500, "resonance": 0.15},
                      "amp_env": {"attack_ms": 1, "decay_ms": 160, "sustain": 0.0, "release_ms": 100}},
        "play": "One short note around G2-C3.", "check": {"decay_s": "0.08-0.25", "clarity": "low"},
        "if": {"it's a hi-hat": "lower the filter, add the tone", "it's a tom": "more noise"},
    },
    "synth hat": {
        "family": "drums", "aka": ["noise hat", "closed hat"],
        "what": "High-passed noise with a very short decay (closed) or a longer one (open).",
        "blueprint": {"voices": "mono", "osc1": {"wave": "saw", "level": 0.0}, "noise": 1.0,
                      "filter": {"type": "hp", "cutoff_hz": 7000, "resonance": 0.1},
                      "amp_env": {"attack_ms": 1, "decay_ms": 45, "sustain": 0.0, "release_ms": 40}},
        "play": "Short notes, any key.", "check": {"decay_s": "under 0.1 closed, 0.2-0.5 open", "centroid_hz": "above 6000"},
        "if": {"it's a snare": "raise the high-pass"},
    },
}

FAMILIES = ("bass", "lead", "pad", "keys", "fx", "drums")


def find(name: str) -> tuple[str, dict] | None:
    """A sound blueprint by its name or one of its other names (exact, then contained)."""
    wanted = " ".join(name.lower().replace("-", " ").split())
    for key, entry in SOUNDS.items():
        if wanted == key or wanted in entry.get("aka", []):
            return key, entry
    near = [k for k, e in SOUNDS.items() if wanted in k or k in wanted or any(wanted in a or a in wanted for a in e.get("aka", []))]
    return (near[0], SOUNDS[near[0]]) if len(near) == 1 else None


def find_technique(name: str) -> tuple[str, str] | None:
    """A technique by its name, by a name that contains it ('filter key tracking'), or by a
    word that only one technique's name has ('tremolo'; 'envelope' is two, so neither)."""
    wanted = " ".join(name.lower().replace("-", " ").split())
    if wanted in TECHNIQUES:
        return wanted, TECHNIQUES[wanted]
    inside = [k for k in TECHNIQUES if k in wanted]
    if inside:
        key = max(inside, key=len)
        return key, TECHNIQUES[key]
    by_word = [k for k in TECHNIQUES if wanted in k.split() and wanted != "and"]
    return (by_word[0], TECHNIQUES[by_word[0]]) if len(by_word) == 1 else None


def family(name: str) -> tuple[str, dict[str, str]] | None:
    """A family asked for by name ('pad', 'basses', 'drum'): its sounds and what each is."""
    wanted = name.lower().strip()
    for fam in FAMILIES:
        if wanted in (fam, fam + "s", fam + "es", fam.rstrip("s")):
            return fam, {k: e["what"] for k, e in SOUNDS.items() if e["family"] == fam}
    return None


# Every field a blueprint may hold: a misspelt one would be left out without a word.
FIELDS = {
    None: {"voices", "unison_cents", "glide_ms", "legato", "osc1", "osc2", "osc_mod", "noise", "filter", "filter_env",
           "amp_env", "lfo1", "lfo2", "pitch_env", "velocity_to_amp", "fx"},
    "osc1": {"wave", "level", "width", "pwm"}, "osc2": {"wave", "level", "semitones", "cents"},
    "filter": {"type", "cutoff_hz", "resonance", "env_octaves", "key_track", "velocity"},
    "filter_env": {"attack_ms", "decay_ms", "sustain", "release_ms"},
    "amp_env": {"attack_ms", "decay_ms", "sustain", "release_ms"},
    "lfo1": {"shape", "hz", "sync", "to", "depth", "retrigger"}, "lfo2": {"shape", "hz", "sync", "to", "depth", "retrigger"},
    "pitch_env": {"semitones", "decay_ms", "to"}, "fx": {"chorus", "ensemble", "phaser", "delay", "distortion"},
}


def unknown_fields(blueprint: dict) -> list[str]:
    """The names in a blueprint that aren't blueprint fields."""
    bad = [k for k in blueprint if k not in FIELDS[None]]
    for part, allowed in FIELDS.items():
        if part and isinstance(blueprint.get(part), dict):
            bad += [f"{part}.{k}" for k in blueprint[part] if k not in allowed]
    return bad


def index() -> dict:
    """What the guide holds: the method, the sound names by family, the technique names."""
    return {
        "method": METHOD,
        "sounds": {family: [k for k, e in SOUNDS.items() if e["family"] == family] for family in FAMILIES},
        "also_known_as": {k: e["aka"] for k, e in SOUNDS.items() if e.get("aka")},
        "techniques": list(TECHNIQUES),
    }
