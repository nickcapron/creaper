"""Electronic dance music: house, disco, techno, trance, bass music, breakbeat, hardcore and club styles."""

from . import Genre, Mix

GENRES = [
    # ------------------------------------------------------------------ house and disco
    Genre(
        name="house",
        family="electronic dance",
        aliases=("dance",),
        parent="disco",
        description="The four-on-the-floor club music that grew out of disco in Chicago: a steady kick on every beat, "
                    "offbeat hats, a clap on 2 and 4, and a loop of chords, bass and vocal built to keep a room moving "
                    "for hours.",
        era="Chicago (the Warehouse, the Music Box) and New York/New Jersey, early-to-mid 1980s; global since",
        touchstones=("Frankie Knuckles", "Marshall Jefferson", "Larry Heard", "Masters at Work", "Todd Terry",
                     "Kerri Chandler", "Daft Punk"),
        tempo=(118, 128),
        feel="four-on-the-floor with offbeat open hats and a light 16th-note swing",
        swing=54,
        modes=("minor", "major", "dorian"),
        keys=("A minor", "F minor", "G minor", "C major", "F major"),
        progressions=(
            "i7-iv7",
            "i-VII-VI-VII",
            "dorian: i7-IV9",
            "major: IVmaj7-V-iii7-vi7",
            "major: I-V-vi-IV",
            "major: ii7-V7sus4-Imaj7-vi7",
        ),
        harmonic_rhythm=1,
        harmony="Loop-based: one to four chords repeated for the whole track, often a two-chord vamp. Piano house "
                "uses bright major triads and 7ths in M1-piano stabs; deeper styles use minor 7ths and 9ths. Chords "
                "change on the downbeat or are anticipated by a 16th; key changes are rare, breakdowns strip to the "
                "chord loop alone.",
        voicing="close",
        comping="stabs",
        bass_style="offbeat",
        bass="Mono sub or Juno/Moog-style bass in the gaps between kicks: the classic is a note on every offbeat "
             "'and', or a syncopated 16th riff that lands on the 'e' and 'a' and returns to the root. Octave jumps "
             "and the 5th for movement; ducked by the kick.",
        melody_density="sparse",
        melody_scale="minor pentatonic",
        melody="Hooks are short and repeated: a gospel or soul vocal phrase, a piano riff, an organ line or a "
               "filtered sample, two to four bars long, repeated with small variations and call-and-response "
               "between vocal and keys. Vocals sit around the 5th to the octave above the tonic.",
        groove={"step": 0.25, "swing": 54, "pattern": {
            "kick":       "x... x... x... x...",
            "clap":       ".... x... .... x...",
            "closed hat": "xo.o xo.o xo.o xo.o",
            "open hat":   "..x. ..x. ..x. ..x.",
            "shaker":     "oxox oxox oxox oxox",
        }},
        drums="TR-909 (or 808) kick on every beat, clap or snare on 2 and 4, open hat on every offbeat, closed hats "
              "or shaker in swung 16ths; tambourine or conga loops add the human layer. Fills are drop-outs, snare "
              "rolls into the drop or a filter on the drum bus, never tom fills.",
        form=(("intro", 16), ("groove", 32), ("breakdown", 16), ("drop", 32), ("break", 16), ("drop", 32),
              ("outro", 16)),
        instruments=("drum machine (909/808)", "bass synth", "piano or organ", "pad", "vocal", "percussion loops"),
        sound_design="909 kick with a short punchy tail, crisp open hats, M1 or Rhodes pianos, organ bass or Juno "
                     "saw bass, filtered disco or soul samples; resonant low-pass filter sweeps on loops for "
                     "builds and breakdowns.",
        production="Kick and bass own the low end (mono below 120 Hz) with sidechain ducking from the kick; DJ-"
                   "friendly 16- or 32-bar intros and outros with drums only; elements enter every 8 or 16 bars; "
                   "bus compression for glue, bright but not harsh top end.",
        theory="Built on repetition and phrase structure rather than harmonic development: everything is in 8-bar "
               "units, change happens by adding and removing layers. The offbeat hat against the on-beat kick "
               "creates the push-pull pulse; swing on the 16ths (around 54-58%) gives the shuffle.",
        mix=Mix(lufs=(-9, -7), lra=(3, 6), low_end="heavy", tone="neutral", width="wide"),
    ),
    Genre(
        name="deep house",
        family="electronic dance",
        aliases=("deep",),
        parent="house",
        description="House's soulful, late-night side: warm jazz and gospel chords over a rolling four-on-the-floor "
                    "groove, more about mood and hypnotic swing than big drops.",
        era="Chicago and New Jersey, late 1980s; revived in the 2010s",
        touchstones=("Larry Heard", "Kerri Chandler", "Moodymann", "Theo Parrish", "St Germain"),
        tempo=(118, 125),
        feel="four-on-the-floor with a loose, swung shuffle in the hats and percussion",
        swing=56,
        modes=("minor", "dorian"),
        keys=("A minor", "F minor", "C minor", "D minor"),
        progressions=(
            "i7-iv7",
            "i9-VII-VI-VII",
            "dorian: i7-IV9",
            "i9-iv9-VIImaj7-IIImaj7",
            "iv9-VII13-IIImaj7-VImaj7",
        ),
        harmonic_rhythm=0.5,
        harmony="Minor 7ths, 9ths and 11ths borrowed from jazz and gospel; often a two-chord loop held for 2 bars "
                "each; organ and Rhodes stabs; sus chords for warmth rather than tension. The iv9-VII13-IIImaj7 "
                "move is a ii-V-I into the relative major, used as a soulful lift.",
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
            "kick":       "x... x... x... x...",
            "clap":       ".... x... .... x...",
            "closed hat": "..x. ..x. ..x. ..x.",
            "shaker":     "xoxo xoxo xoxo xoxo",
            "conga":      "...x ..x. .x.. ..x.",
        }},
        drums="909 or 808 kick on every beat, clap on 2 and 4, open or closed hats on the offbeats, swung shaker "
              "16ths; percussion (congas, rimshots) adds the shuffle; fills are filter or drop-outs, not rolls.",
        form=(("intro", 16), ("groove", 32), ("breakdown", 16), ("main", 32), ("break", 16), ("main", 32),
              ("outro", 16)),
        instruments=("drum machine (909/808)", "sub bass", "Rhodes or organ", "pad", "vocal chops", "percussion"),
        sound_design="Warm, slightly dusty: Rhodes and organ through chorus, soft analog pads with slow attack, "
                     "sine/triangle sub, tape saturation; filter sweeps on chords for movement.",
        production="Kick and bass own the low end (mono below 120 Hz), mid-heavy warmth, gentle bus compression; "
                   "DJ-friendly intros and outros in 16- or 32-bar phrases.",
        theory="Lives on extended minor chords and modal loops instead of functional cadences: the i7-iv7 vamp "
               "(dorian if the iv is a IV9) never resolves, which keeps the groove hypnotic.",
        mix=Mix(lufs=(-10, -7), lra=(4, 7), low_end="heavy", tone="warm", width="wide"),
    ),
    Genre(
        name="tech house",
        family="electronic dance",
        parent="house",
        description="House groove with techno's stripped-back attitude: a punchy kick, a bouncing, rubbery bassline "
                    "and clicky percussion carry the track, with a vocal hook instead of chords.",
        era="London (The End, Wiggle parties), mid 1990s; the Ibiza and US festival sound from the mid 2010s",
        touchstones=("Terry Francis", "Eddie Richards", "Jamie Jones", "Fisher", "Patrick Topping", "Chris Lake",
                     "Green Velvet"),
        tempo=(122, 128),
        feel="four-on-the-floor, tight and bouncy, light swing on the percussion 16ths",
        swing=54,
        modes=("minor", "dorian", "phrygian"),
        keys=("G minor", "A minor", "F minor", "D minor"),
        progressions=(
            "i7-i7-VII-VII",
            "i-iv",
            "i7-VI-VII-i7",
            "dorian: i7-IV7",
            "phrygian: i-II",
        ),
        harmonic_rhythm=0.5,
        harmony="Minimal: often a single minor-7 or sus stab that appears only in the breakdown, or a one-note "
                "drone. When chords are used they are short, filtered stabs on the offbeat; the bassline implies the "
                "harmony.",
        voicing="close",
        comping="stabs",
        bass_style="syncopated",
        bass="The star of the track: a short, plucky, rubbery bass (often FM or a saw through a low-pass with "
             "envelope) in a syncopated 16th riff that avoids the kick, using the root, octave, minor 3rd and b7 "
             "with slides and occasional pitch bends. One-bar riff, second bar varied at the end.",
        melody_density="sparse",
        melody_scale="minor pentatonic",
        melody="Melody is mostly a vocal: a spoken or chanted one-liner, chopped and repeated, sometimes pitched "
               "down; or a tiny 2-3 note synth stab hook. Hooks live in rhythm more than pitch.",
        groove={"step": 0.25, "swing": 54, "pattern": {
            "kick":       "x... x... x... x... x... x... x... x...",
            "clap":       ".... x... .... x... .... x... .... x...",
            "closed hat": "xo.x xo.x xo.x xo.x xo.x xo.x xo.x xo.x",
            "open hat":   "..x. ..x. ..x. ..x. ..x. ..x. ..x. ..x.",
            "rim":        "...x ..x. .x.. ..x. ...x ..x. .x.. x..x",
            "shaker":     "oxoo oxoo oxoo oxoo oxoo oxoo oxoo oxoo",
        }},
        drums="Punchy, short 909-style kick with a clicky top, clap and snare layered on 2 and 4, offbeat open hat, "
              "busy 16th closed hats and shakers, syncopated rims, bongos and woodblocks. Drum fills are rolls of "
              "claps or percussion and one-beat kick drops before the main groove returns.",
        form=(("intro", 16), ("groove", 32), ("build", 16), ("drop", 32), ("breakdown", 16), ("build", 8),
              ("drop", 32), ("outro", 16)),
        instruments=("drum machine and samples", "bass synth", "vocal sample", "percussion", "FX and risers",
                     "stab synth"),
        sound_design="Clean, punchy kick (often a short sub-tail kick tuned to the key); FM or analog plucky bass "
                     "with a fast filter envelope; dry spoken vocals; filtered noise sweeps; metallic, clicky "
                     "percussion with little reverb.",
        production="Loud and tight: kick and bass carefully carved (bass sidechained or programmed between kicks), "
                   "dry mid-range, bright percussion panned wide, short reverbs. Arrangements are DJ-tool simple: "
                   "the drop is the bass and vocal returning together.",
        theory="Groove over harmony: the bassline's syncopation against the steady kick (accents on the 'a' of "
               "the beat and the 'e' of the next) is the hook. Mostly one-chord, modal (aeolian or dorian) and "
               "built from repeated 1- and 2-bar cells.",
        mix=Mix(lufs=(-8, -6), lra=(3, 5), low_end="heavy", tone="neutral", width="wide"),
    ),
    Genre(
        name="progressive house",
        family="electronic dance",
        aliases=("prog house",),
        parent="house",
        description="House that builds slowly and hypnotically, layering arpeggios, pads and plucks over long "
                    "evolving arrangements; in its later festival form, big emotive chord progressions and sweeping "
                    "breakdowns.",
        era="UK, early 1990s (Renaissance, Global Underground); the melodic Swedish/festival form in the late 2000s",
        touchstones=("Sasha", "John Digweed", "Leftfield", "Hernan Cattaneo", "Eric Prydz", "Deadmau5",
                     "Swedish House Mafia"),
        tempo=(122, 130),
        feel="four-on-the-floor, smooth and driving, straight 16ths",
        swing=50,
        modes=("minor", "major"),
        keys=("F minor", "A minor", "C minor", "E minor", "G major"),
        progressions=(
            "i-VI-III-VII",
            "i-VI-VII-VII",
            "VI-VII-i-i",
            "i-iv-VI-VII",
            "major: IV-I-V-vi",
            "major: vi-IV-I-V",
        ),
        harmonic_rhythm=0.5,
        harmony="Diatonic minor progressions with each chord held for one or two bars; suspended 2nds and 4ths "
                "on pads; a pedal tone (often the tonic or 5th in the arpeggio) running through the changes so "
                "chords seem to morph rather than change.",
        voicing="spread",
        comping="arpeggio_up",
        bass_style="offbeat",
        bass="Rolling offbeat bass or a 16th pulse that follows the chord roots; in the Prydz/Deadmau5 style a "
             "sidechained saw bass that pumps with the kick. Mono, controlled, always under the arpeggio.",
        melody_density="medium",
        melody_scale="minor",
        melody="Plucked or gated 16th arpeggios that repeat while their filter slowly opens; a simple lead or "
               "piano motif revealed in the breakdown and carried into the drop. Melodies move stepwise and "
               "favour the 5th, 9th and 3rd of the chord.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x... x... x... x...",
            "clap":       ".... x... .... x...",
            "closed hat": "x.x. x.x. x.x. x.x.",
            "open hat":   "..x. ..x. ..x. ..x.",
            "shaker":     "oxox oxox oxox oxox",
        }},
        drums="Steady 909-style kick, clap on 2 and 4, offbeat open hats and 16th shakers; percussion layers "
              "introduced every 16 bars; snare rolls and crash cymbals mark phrase changes; long reverse-cymbal "
              "and noise-sweep transitions.",
        form=(("intro", 32), ("build", 32), ("breakdown", 32), ("build", 16), ("drop", 32), ("break", 16),
              ("drop", 32), ("outro", 32)),
        instruments=("drum machine", "saw bass", "pluck synth", "pad", "arpeggiator", "piano", "FX"),
        sound_design="Analog-style plucks and arps with long filter automation, wide detuned pads, delayed plucks "
                     "(dotted 8th), clean round kick, subtle risers and white-noise sweeps.",
        production="Long arrangements (7-9 minutes for DJ cuts); automation is the arrangement: filter cutoff, "
                   "reverb sends and layer volumes evolve over 64-bar arcs. Sidechain on pads and bass for the "
                   "pump; wide stereo field with mono low end.",
        theory="Tension comes from timbre and layering, not cadences: pedal tones against changing chords, "
               "slowly opening filters and phrase-length builds. The i-VI-III-VII cycle is aeolian and loops "
               "without a dominant, so it never fully resolves.",
        mix=Mix(lufs=(-9, -7), lra=(4, 7), low_end="heavy", tone="neutral", width="wide"),
    ),
    Genre(
        name="acid house",
        family="electronic dance",
        aliases=("acid",),
        parent="chicago house",
        description="Chicago house built around the squelching, resonant line of the Roland TB-303 bass machine: "
                    "raw drum machines and a hypnotic acid riff whose filter is twisted live.",
        era="Chicago 1986-87; exploded in the UK during the 1988 'Second Summer of Love'",
        touchstones=("Phuture", "DJ Pierre", "Armando", "Adonis", "Bam Bam", "808 State", "Hardfloor"),
        tempo=(118, 128),
        feel="four-on-the-floor, raw and jacking, slight swing",
        swing=54,
        modes=("minor", "phrygian"),
        keys=("A minor", "E minor", "C minor", "G minor"),
        progressions=(
            "i-i-iv-iv",
            "i-VII",
            "phrygian: i-II",
            "i7-VI7",
        ),
        harmonic_rhythm=0.5,
        harmony="Minimal or none: the 303 line implies a minor tonality; occasional sustained pad or a "
                "one-chord stab. Movement comes from the 303's filter cutoff and resonance, not chord changes.",
        voicing="close",
        comping="none",
        bass_style="sixteenths",
        bass="The TB-303 line is both bass and lead: a one- or two-bar 16th pattern with accents, slides "
             "(legato glides) and octave jumps, built on the root, b3, 4, b5, 5 and b7. The filter cutoff, "
             "resonance and envelope mod are swept by hand across the track.",
        melody_density="busy",
        melody_scale="blues",
        melody="The acid line is the melody: relentless 16ths with accented notes, slides between pitches and "
               "octave leaps; occasional vocal samples or spoken words over the top.",
        groove={"step": 0.25, "swing": 54, "pattern": {
            "kick":       "x... x... x... x... x... x... x... x...",
            "clap":       ".... x... .... x... .... x... .... x...",
            "closed hat": "x.x. x.x. x.x. x.x. x.x. x.x. x.x. x.xx",
            "open hat":   "..x. ..x. ..x. ..x. ..x. ..x. ..x. ..x.",
            "cowbell":    "...x .... ..x. .... ...x .... ..x. ..x.",
        }},
        drums="TR-808, TR-909 or TR-707 programmed directly: kick on every beat, clap or snare on 2 and 4, "
              "offbeat hats, cowbell and rimshot syncopations. Little processing; drums enter and drop out by "
              "muting channels live.",
        form=(("intro", 16), ("acid line", 32), ("build", 16), ("peak", 32), ("break", 16), ("peak", 32),
              ("outro", 16)),
        instruments=("TB-303", "TR-808", "TR-909", "TR-707", "pad", "vocal sample"),
        sound_design="TB-303 saw or square through its 18 dB/oct resonant filter, often overdriven through a "
                     "distortion pedal or mixer; dry 808/909 drums; plate reverb on claps; occasional string pad.",
        production="Jammed and recorded live from the hardware, so the arrangement is mute-button driven; minimal "
                   "EQ, tape or console saturation, the 303 kept upfront and centred.",
        theory="Pure timbral composition: the same 16-step pattern sounds new as cutoff and resonance move. "
               "Accents and slides create a second rhythmic layer over the 16ths; the b5 'blue note' and octave "
               "displacement give acid lines their snarl.",
        mix=Mix(lufs=(-10, -7), lra=(4, 7), low_end="heavy", tone="bright", width="moderate"),
    ),
    Genre(
        name="chicago house",
        family="electronic dance",
        aliases=("jackin house", "jack house"),
        parent="house",
        description="The original house sound: raw drum-machine 'jack' tracks and soulful piano anthems made on "
                    "cheap hardware for Chicago clubs, with gospel vocals and relentless kick drums.",
        era="Chicago, 1984-1990",
        touchstones=("Frankie Knuckles", "Marshall Jefferson", "Jesse Saunders", "Farley 'Jackmaster' Funk",
                     "Steve 'Silk' Hurley", "Ron Hardy", "Lil Louis"),
        tempo=(118, 126),
        feel="four-on-the-floor, raw and swung, 'jacking' 16ths",
        swing=57,
        modes=("minor", "major"),
        keys=("A minor", "E minor", "C major", "F major"),
        progressions=(
            "i7-iv7",
            "i-VII-VI-VII",
            "major: I-IV",
            "major: vi-IV-V-IV",
            "dorian: i7-IV7",
        ),
        harmonic_rhythm=1,
        harmony="Piano anthems use gospel-style major triads and 7ths in rolling piano riffs; jack tracks use "
                "one-chord stabs or none at all. Chords voice-led in close position with the melody on top.",
        voicing="close",
        comping="stabs",
        bass_style="syncopated",
        bass="Juno-106, TB-303 or sampled bass in a busy syncopated 16th riff that repeats every bar, or a "
             "simple pumping offbeat bass. Often loud and mono, with octave jumps.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Gospel and disco-derived vocal hooks (diva vocals or spoken 'jack' chants), rolling piano riffs "
               "with repeated notes and octaves, and simple synth string lines.",
        groove={"step": 0.25, "swing": 57, "pattern": {
            "kick":       "x... x... x... x...",
            "clap":       ".... x... .... x...",
            "closed hat": "xxox xxox xxox xxox",
            "open hat":   "..x. ..x. ..x. ..x.",
            "tambourine": "..x. ..x. ..x. ..x.",
        }},
        drums="TR-808, TR-707 and TR-909 programmed with swing; kick on every beat, claps on 2 and 4, 16th "
              "closed hats with accents, open hats on offbeats, handclaps and congas; drum rolls and machine-gun "
              "snare builds made on the drum machine.",
        form=(("intro", 16), ("verse", 16), ("chorus", 16), ("break", 16), ("verse", 16), ("chorus", 16),
              ("jam", 32), ("outro", 16)),
        instruments=("TR-808", "TR-909", "TR-707", "Juno-106", "piano", "vocal"),
        sound_design="Raw drum machines with minimal processing, Juno-106 bass and strings, Korg M1 or real "
                     "piano, gated reverb on claps, vocal recorded with spring or plate reverb.",
        production="Cheap and direct: four-track or mixer-board recordings, mono-compatible, gritty and loud in the "
                   "mids. Arrangements made by muting drum-machine parts live while recording to tape.",
        theory="Gospel roots show in the plagal I-IV vamp and call-and-response vocals. The swung 16ths of the "
               "drum machine (around 56-60%) and the syncopated bass against the steady kick create the 'jack'.",
        mix=Mix(lufs=(-11, -8), lra=(4, 8), low_end="heavy", tone="neutral", width="moderate"),
    ),
    Genre(
        name="french house",
        family="electronic dance",
        aliases=("french touch", "filter house"),
        parent="house",
        description="Paris's take on house: looped and filtered disco and funk samples, heavy sidechain pumping, "
                    "phasers and vocoders, all glamour and groove.",
        era="Paris, mid-to-late 1990s",
        touchstones=("Daft Punk", "Stardust", "Modjo", "Cassius", "Alan Braxe", "Bob Sinclar", "Thomas Bangalter"),
        tempo=(118, 128),
        feel="four-on-the-floor with a pumping, sidechained swing",
        swing=54,
        modes=("major", "dorian", "mixolydian", "minor"),
        keys=("E major", "D major", "F# minor", "A minor"),
        progressions=(
            "major: Imaj7-vi7-ii7-V7",
            "major: IVmaj7-iii7-ii7-V7sus4",
            "dorian: i7-IV7",
            "mixolydian: I-VII-IV-I",
            "minor: i7-iv7-VII7-IIImaj7",
        ),
        harmonic_rhythm=1,
        harmony="Lifted from disco and boogie records: major 7ths, minor 7ths and 9ths, ii-V turnarounds and "
                "dorian vamps played by a sampled string section, guitar or Rhodes. The sample loop (1-2 bars) "
                "defines the harmony.",
        voicing="close",
        comping="stabs",
        bass_style="octaves",
        bass="Disco octave bass or a funky slap-bass sample filtered along with the loop; in original lines, "
             "a rubbery 8th-note octave pattern with passing notes, sidechained hard to the kick.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Vocoder or talkbox vocals, filtered sample hooks, and short guitar or synth riffs; the main hook "
               "is often a two-bar sample whose filter opens to reveal it.",
        groove={"step": 0.25, "swing": 54, "pattern": {
            "kick":       "x... x... x... x...",
            "clap":       ".... x... .... x...",
            "closed hat": "x.xx x.xx x.xx x.xx",
            "open hat":   "..x. ..x. ..x. ..x.",
        }},
        drums="Sampled or 909 drums, kick on every beat compressed hard, clap or snare on 2 and 4, open hats on "
              "offbeats; drums often sampled from disco breaks and looped; whole-mix compression makes the hats "
              "and loop breathe with the kick.",
        form=(("intro", 16), ("loop", 32), ("filter build", 16), ("full", 32), ("break", 16), ("full", 32),
              ("outro", 16)),
        instruments=("sampler", "drum machine", "bass", "vocoder or talkbox", "Rhodes or guitar", "filter"),
        sound_design="Disco samples through a resonant low-pass filter swept by hand (the 'filter house' move), "
                     "phaser and flanger on the loop, vocoders, slightly crushed samplers (SP-1200, ASR-10).",
        production="Heavy master and bus compression keyed from the kick for the signature pump; filter "
                   "automation drives the arrangement; warm, slightly lo-fi top end; long DJ intros.",
        theory="Harmony and melody come pre-composed in a sample; composition is curation, looping and "
               "filtering. The pumping compression turns the steady four-on-the-floor into a breathing, swung "
               "envelope that becomes part of the groove.",
        mix=Mix(lufs=(-9, -6), lra=(3, 6), low_end="heavy", tone="warm", width="wide"),
    ),
    Genre(
        name="disco",
        family="electronic dance",
        aliases=("classic disco",),
        parent="funk",
        description="The orchestral dance music of the 1970s: four-on-the-floor drums, octave-jumping bass, chicken-"
                    "scratch guitar, lush strings and horns, and soaring vocals.",
        era="New York and Philadelphia clubs, 1973-1980",
        touchstones=("Chic", "Donna Summer", "Giorgio Moroder", "Bee Gees", "Sylvester", "MFSB",
                     "The Salsoul Orchestra"),
        tempo=(110, 128),
        feel="four-on-the-floor with live, slightly pushed 16th-note hi-hats",
        swing=52,
        modes=("minor", "major", "dorian"),
        keys=("A minor", "E minor", "G major", "Bb major"),
        progressions=(
            "i7-iv7",
            "dorian: i7-IV7",
            "i-iv-VII-III-VI-ii°-V7-V7",
            "major: ii7-V7-Imaj7-vi7",
            "major: IVmaj7-iii7-ii7-Imaj7",
        ),
        harmonic_rhythm=1,
        harmony="Jazz-influenced 7ths and 9ths, dorian vamps (Chic), circle-of-fifths sequences in minor and "
                "descending ii-V chains; strings and horns voice the chords in close harmony; key changes up a "
                "step into the final chorus.",
        voicing="close",
        comping="pulse_16",
        bass_style="octaves",
        bass="Electric bass in driving octave 8ths (root low, octave high on the offbeat) with fills, chromatic "
             "approach notes and funky syncopations; Bernard Edwards-style melodic lines that are hooks in "
             "themselves.",
        melody_density="busy",
        melody_scale="dorian",
        melody="Big, soaring vocal melodies with gospel melisma, backed by call-and-response chorus vocals; "
               "string countermelodies and stabs, horn riffs and swooping string glissandi.",
        groove={"step": 0.25, "swing": 52, "pattern": {
            "kick":       "x... x... x... x...",
            "snare":      ".... x... .... x...",
            "closed hat": "xx.x xx.x xx.x xx.x",
            "open hat":   "..x. ..x. ..x. ..x.",
            "tambourine": "..x. ..x. ..x. ..x.",
            "conga":      "x..x ..x. x..x ..x.",
        }},
        drums="Live drums: kick on every beat, snare on 2 and 4, the open hi-hat on every offbeat ('pea-soup' "
              "hat) with 16th closed hats, tambourine, congas and timbales; drum breaks with only drums and "
              "percussion are built in for DJs; Moroder records replace this with sequencers.",
        form=(("intro", 8), ("verse", 16), ("chorus", 16), ("verse", 16), ("chorus", 16), ("break", 16),
              ("instrumental", 16), ("chorus", 16), ("outro", 16)),
        instruments=("drum kit", "electric bass", "rhythm guitar", "strings", "horns", "piano or Rhodes",
                     "percussion", "vocals"),
        sound_design="Muted 16th chicken-scratch guitar, warm bass with flatwound strings, lush string section "
                     "with plate reverb, bright brass; Moroder's sequenced Minimoog bass for the electronic strand.",
        production="Analog multitrack with wide stereo strings and percussion, dry punchy drums, extended 12-inch "
                   "mixes with breakdowns made by the remixer; tape warmth and gentle compression.",
        theory="Harmonically richer than most dance music: functional ii-V motion and circle-of-fifths sequences "
               "alongside dorian vamps. Rhythmically, the offbeat open hat and octave bass create the 'and' "
               "lift against the steady kick.",
        mix=Mix(lufs=(-12, -9), lra=(5, 9), low_end="moderate", tone="warm", width="wide"),
    ),
    Genre(
        name="nu-disco",
        family="electronic dance",
        aliases=("new disco",),
        parent="disco",
        description="Modern disco revival: disco's octave bass, strings and guitars rebuilt with analog synths, "
                    "drum machines and a loose, cosmic, often instrumental feel.",
        era="Norway, the UK and the US, mid 2000s onward",
        touchstones=("Todd Terje", "Lindstrom", "Prins Thomas", "Breakbot", "Purple Disco Machine", "Aeroplane",
                     "Escort"),
        tempo=(110, 124),
        feel="four-on-the-floor, laid-back, lightly swung 16ths",
        swing=54,
        modes=("minor", "major", "dorian"),
        keys=("F minor", "A minor", "D major", "Eb major"),
        progressions=(
            "i7-iv7",
            "dorian: i9-IV9",
            "major: Imaj7-iii7-vi7-IVmaj7",
            "major: ii7-V7-Imaj7-Imaj7",
            "VImaj7-VII-i7-i7",
        ),
        harmonic_rhythm=1,
        harmony="Disco's 7ths and 9ths with a cosmic, synthy palette: dorian vamps, major 7th progressions, "
                "ii-V turnarounds and sus chords; often instrumental, so the chord pad and arpeggios carry "
                "the emotional arc.",
        voicing="open",
        comping="pulse_16",
        bass_style="octaves",
        bass="Octave-jumping synth bass or live slap bass in 8ths and 16ths with funky fills; arpeggiated "
             "sequenced basslines in the cosmic-disco strand.",
        melody_density="medium",
        melody_scale="dorian",
        melody="Synth leads with portamento, vocoders, filtered vocal snippets and guitar licks; melodies are "
               "playful, often modal, with long phrases and repetition.",
        groove={"step": 0.25, "swing": 54, "pattern": {
            "kick":       "x... x... x... x...",
            "clap":       ".... x... .... x...",
            "closed hat": "xx.x xx.x xx.x xx.x",
            "open hat":   "..x. ..x. ..x. ..x.",
            "tambourine": "..x. ..x. ..x. ..x.",
            "cowbell":    "...x ..x. ...x .x..",
        }},
        drums="Drum machine (LinnDrum, 909, 808) or disco break samples: kick on every beat, clap or snare on "
              "2 and 4, offbeat open hats, tambourine and cowbell; occasional live drum fills and tom flourishes.",
        form=(("intro", 16), ("groove", 32), ("theme", 32), ("breakdown", 16), ("theme", 32), ("outro", 16)),
        instruments=("analog synths", "drum machine", "synth or slap bass", "guitar", "strings or string synth",
                     "vocoder"),
        sound_design="Juno, Prophet and Jupiter-style pads and arps, string machines, slap bass, wah guitar, "
                     "vocoder; tape delay and phaser; warm, slightly saturated analog character.",
        production="Groove-first with sidechain for gentle pump, warm tape-saturated mix, wide stereo synths and "
                   "percussion, loose long-form arrangements of 6-9 minutes.",
        theory="Takes disco's functional harmony (ii-V-I, circle progressions) and fuses it with modal synth "
               "vamping; long arpeggiated phrases often outlast the chord changes for overlapping cycles.",
        mix=Mix(lufs=(-9, -7), lra=(4, 7), low_end="heavy", tone="warm", width="wide"),
    ),
    Genre(
        name="italo disco",
        family="electronic dance",
        aliases=("italo",),
        parent="disco",
        description="Italy's synth-driven disco: sequenced octave basslines, drum machines, catchy minor-key synth "
                    "hooks and heavily accented English vocals, melodramatic and futuristic.",
        era="Italy, 1979-1988",
        touchstones=("Giorgio Moroder", "Gazebo", "Kano", "Klein + M.B.O.", "Alexander Robotnick", "Ryan Paris",
                     "Righeira"),
        tempo=(110, 128),
        feel="four-on-the-floor, straight and mechanical",
        swing=50,
        modes=("minor",),
        keys=("A minor", "E minor", "D minor", "G minor"),
        progressions=(
            "i-VI-VII-i",
            "i-VI-III-VII",
            "i-iv-VII-III",
            "VI-VII-i-i",
            "i-v-VI-VII",
        ),
        harmonic_rhythm=1,
        harmony="Simple diatonic minor progressions, one chord per bar, with pop verse-chorus structure; "
                "triads more than 7ths; the chorus often lifts to VI-VII-i.",
        voicing="close",
        comping="sustain",
        bass_style="octaves",
        bass="Sequenced 8th-note octave bass (root on the beat, octave on the offbeat) running throughout, often "
             "gated or with filter accents; Moroder's 16th 'Feel Love' pulse in the space-disco strand.",
        melody_density="medium",
        melody_scale="minor",
        melody="Catchy, singable synth hooks played on polysynths, repeated as the instrumental chorus; vocals in "
               "English with accents, often vocoded; melodies move by step and leap to the 5th, dramatic and "
               "sentimental.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x... x... x... x...",
            "snare":      ".... x... .... x...",
            "clap":       ".... x... .... x...",
            "closed hat": "x.x. x.x. x.x. x.x.",
            "open hat":   "..x. ..x. ..x. ..x.",
        }},
        drums="LinnDrum, Oberheim DMX or Roland drum machines: kick on every beat, big gated-reverb snare and "
              "claps on 2 and 4, 8th hats with offbeat open hats, Simmons tom fills.",
        form=(("intro", 16), ("verse", 16), ("chorus", 16), ("instrumental hook", 8), ("verse", 16),
              ("chorus", 16), ("break", 16), ("chorus", 16), ("outro", 16)),
        instruments=("polysynth", "sequenced bass synth", "drum machine", "vocoder", "string synth", "vocals"),
        sound_design="Polysynth brass and lead patches (Juno, Polysix, Jupiter-8, OB-Xa), sequenced Moog or "
                     "SH-101 bass, vocoders, string machines, big gated reverb on snares.",
        production="Glossy 1980s studio sound: bright, reverb-rich, mid-forward vocals, wide synths, moderate "
                   "compression; 12-inch versions with long instrumental sections and dub breaks.",
        theory="Natural-minor diatonic harmony with pop phrasing; the relentless octave bass gives harmonic "
               "motion its pulse. Hooks are motivic and sequenced, often a melody repeated on a different "
               "chord tone over each change.",
        mix=Mix(lufs=(-11, -8), lra=(4, 8), low_end="moderate", tone="bright", width="wide"),
    ),
    # ------------------------------------------------------------------ techno
    Genre(
        name="techno",
        family="electronic dance",
        aliases=("berlin techno",),
        parent="detroit techno",
        description="Machine-driven, repetitive dance music: a relentless four-on-the-floor kick, hypnotic loops, "
                    "rumbling bass and texture over melody, built for long DJ sets in dark rooms.",
        era="Detroit, mid 1980s; Berlin, Frankfurt and the UK through the 1990s; global since",
        touchstones=("Jeff Mills", "Derrick May", "Richie Hawtin", "Ben Klock", "Marcel Dettmann", "Adam Beyer",
                     "Amelie Lens"),
        tempo=(125, 140),
        feel="four-on-the-floor, straight, driving and hypnotic",
        swing=50,
        modes=("minor", "phrygian"),
        keys=("F minor", "A minor", "G minor", "E minor"),
        progressions=(
            "i-VII",
            "i-VI",
            "phrygian: i-II",
            "i7-iv7",
            "i-i-VI-VII",
        ),
        harmonic_rhythm=0.5,
        harmony="Sparse or absent: a single minor or sus stab, a drone, or two chords a whole step or semitone "
                "apart. Stabs are often quartal or minor 7th shapes with no 3rd so the tonality stays ambiguous.",
        voicing="quartal",
        comping="stabs",
        bass_style="offbeat",
        bass="Either a dark offbeat bass note between kicks, a rolling 16th pulse, or the modern 'rumble': the "
             "kick fed into reverb and distortion, low-passed and sidechained so it swells between hits.",
        melody_density="sparse",
        melody_scale="phrygian",
        melody="Melody is replaced by motifs: a looping 1-bar synth riff, a stab pattern or a sequenced line "
               "that evolves through filter and delay automation; hooks are rhythmic and timbral.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x... x... x... x... x... x... x... x...",
            "clap":       ".... x... .... x... .... x... .... x...",
            "closed hat": "xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx",
            "open hat":   "..x. ..x. ..x. ..x. ..x. ..x. ..x. ..x.",
            "rim":        "..x. .x.. x..x .... ..x. .x.. x... .x..",
            "ride":       "..x. ..x. ..x. ..x. ..x. ..x. ..x. ..x.",
        }},
        drums="909 kick on every beat (or a heavy, saturated modern kick), offbeat open hats, 16th closed hats "
              "with accent automation, clap or snare on 2 and 4 (sometimes absent), ride on the offbeats, "
              "syncopated rim and percussion loops that phase against the bar. Changes every 8 or 16 bars.",
        form=(("intro", 32), ("groove", 32), ("tension", 32), ("breakdown", 16), ("peak", 32), ("groove", 32),
              ("outro", 32)),
        instruments=("drum machine (909)", "bass synth", "stab synth", "sequencer", "FX", "noise"),
        sound_design="Saturated 909 kicks, distorted rumble, metallic percussion, resonant sequenced synths, "
                     "dub-style stabs through delay and reverb, noise sweeps and tape-like hiss.",
        production="Kick dominates and is often mono, loud and saturated; arrangement through mutes and filter "
                   "and FX automation over 6-8 minutes; dark top end, reverb and delay create space rather than "
                   "chords.",
        theory="Minimalism and repetition: polymetric percussion loops (3- or 5-step cycles over the 16-step "
               "bar) create shifting accents against the steady pulse. Modal colour (aeolian, phrygian's b2) "
               "and timbre replace harmonic progression.",
        mix=Mix(lufs=(-9, -7), lra=(3, 6), low_end="heavy", tone="dark", width="wide"),
    ),
    Genre(
        name="minimal techno",
        family="electronic dance",
        aliases=("minimal",),
        parent="techno",
        description="Techno reduced to its essentials: tiny clicks, blips and microsounds, a dry kick and space, "
                    "with groove coming from subtle shifts in placement and timbre.",
        era="Detroit and Berlin, early-to-mid 1990s; the Berlin and Cologne 'minimal' wave of the 2000s",
        touchstones=("Robert Hood", "Richie Hawtin", "Plastikman", "Daniel Bell", "Ricardo Villalobos",
                     "Zip", "Thomas Brinkmann"),
        tempo=(120, 130),
        feel="four-on-the-floor with loose, swung micro-percussion",
        swing=54,
        modes=("minor", "phrygian"),
        keys=("A minor", "F minor", "D minor"),
        progressions=(
            "i-i-VII-VII",
            "i7-iv7",
            "phrygian: i-II",
            "i-VI",
        ),
        harmonic_rhythm=0.5,
        harmony="Almost none: a single muted stab, a sine blip, or a drone. When chords appear they are short "
                "minor 7th or sus stabs on an offbeat, used rhythmically.",
        voicing="close",
        comping="stabs",
        bass_style="syncopated",
        bass="Short, dry sine or pluck bass blips placed on syncopated 16ths, often one or two notes; much of "
             "the low end is the kick itself.",
        melody_density="sparse",
        melody_scale="minor pentatonic",
        melody="Melody is micro-motifs: a 2-3 note blip pattern, a filtered vocal snippet or a single delayed "
               "stab; phrases repeat for minutes with tiny variations in timing, pitch and filter.",
        groove={"step": 0.25, "swing": 54, "pattern": {
            "kick":       "x... x... x... x...",
            "clap":       ".... x... .... x...",
            "closed hat": "..x. ..x. ..x. ..xo",
            "rim":        "...x .... ..x. .x..",
            "shaker":     "oxoo oxoo oxoo oxoo",
        }},
        drums="Dry kick on every beat, sparse clap or rim on 2 and 4, offbeat hats, tiny clicks and processed "
              "percussion with off-grid swing; elements drop in and out every 8-16 bars; very little reverb.",
        form=(("intro", 32), ("groove", 64), ("variation", 32), ("break", 16), ("groove", 64), ("outro", 32)),
        instruments=("drum machine", "sine bass", "sampler", "modular or software synth", "FX"),
        sound_design="Clicks, glitches and micro-samples, sine and FM blips, dry short sounds with automated "
                     "delay throws, filtered field recordings.",
        production="Space is the mix: few elements, each with its own frequency and stereo slot, dry centre, "
                   "subtle panning automation; quieter and more dynamic than peak-time techno.",
        theory="Groove from micro-timing and repetition: tiny swing offsets, polymetric loops (e.g. a 3-step "
               "rim over 16 steps) and gradual parameter changes. Harmony is a pedal point; interest is "
               "rhythmic and textural.",
        mix=Mix(lufs=(-10, -8), lra=(4, 7), low_end="moderate", tone="neutral", width="wide"),
    ),
    Genre(
        name="detroit techno",
        family="electronic dance",
        aliases=("detroit",),
        parent="electro",
        description="The original techno: futuristic, soulful machine music from Detroit, with string pads, "
                    "melancholy minor chords and funky drum-machine grooves.",
        era="Detroit, 1985-1995 (the Belleville Three and the second wave)",
        touchstones=("Juan Atkins", "Derrick May", "Kevin Saunderson", "Underground Resistance", "Jeff Mills",
                     "Carl Craig", "Robert Hood"),
        tempo=(125, 135),
        feel="four-on-the-floor with funky, slightly swung drum machine programming",
        swing=53,
        modes=("minor", "dorian"),
        keys=("A minor", "F minor", "Eb minor", "C minor"),
        progressions=(
            "i7-iv7",
            "dorian: i7-IV7",
            "i9-VIImaj7",
            "VImaj7-VII-i7-i7",
            "i11-iv9-VImaj7-VII",
        ),
        harmonic_rhythm=0.5,
        harmony="Melancholy minor 7ths, 9ths and 11ths on string pads and synth stabs; jazzy, soulful voicings "
                "that hint at the relative major; often a two-chord vamp, chords anticipated by an 8th or 16th.",
        voicing="spread",
        comping="stabs",
        bass_style="syncopated",
        bass="Funky syncopated synth bass from electro and Parliament-Funkadelic, or rolling offbeat bass; "
             "often an 808 or Juno-type tone moving between root, 5th and b7.",
        melody_density="medium",
        melody_scale="dorian",
        melody="String-pad melodies and synth riffs that are optimistic and wistful at once; short repeated "
               "motifs and stab rhythms (the 'Strings of Life' piano-stab tradition).",
        groove={"step": 0.25, "swing": 53, "pattern": {
            "kick":       "x... x... x... x...",
            "clap":       ".... x... .... x...",
            "closed hat": "xxox xxox xxox xxox",
            "open hat":   "..x. ..x. ..x. ..x.",
            "rim":        "..x. ..x. .x.. x...",
        }},
        drums="TR-909 and TR-808 with handclaps, rimshots and congas, programmed with funk syncopation; tom "
              "fills from the drum machine; hats with accent and swing; claps stacked with snare.",
        form=(("intro", 16), ("groove", 32), ("strings", 32), ("break", 16), ("main", 32), ("outro", 16)),
        instruments=("TR-909", "TR-808", "string synth or pad", "bass synth", "stab synth", "sequencer"),
        sound_design="Analog string machines and polysynth pads (Juno, DX100, Yamaha keys), sharp synth stabs, "
                     "raw 909 drums, tape-saturated, slightly lo-fi.",
        production="Hardware recorded to tape: raw, mid-forward, some hiss; pads and strings wide, drums upfront "
                   "and punchy; arrangement through mutes and filter rides.",
        theory="Combines Kraftwerk's machine pulse with Black American funk and soul harmony: extended minor "
               "chords and dorian major-IV colour give the 'hi-tech soul' feel; syncopated stabs ride on the "
               "straight kick.",
        mix=Mix(lufs=(-10, -8), lra=(4, 7), low_end="heavy", tone="warm", width="wide"),
    ),
    Genre(
        name="acid techno",
        family="electronic dance",
        aliases=("london acid techno",),
        parent="techno",
        description="Fast, distorted techno driven by one or more screaming TB-303 lines, made for squat parties "
                    "and warehouse raves.",
        era="London squat-party scene and Europe, mid 1990s",
        touchstones=("Chris Liberator", "D.A.V.E. The Drummer", "Lochi", "Josh Wink", "Hardfloor",
                     "Liberator DJs"),
        tempo=(135, 150),
        feel="four-on-the-floor, straight and pounding",
        swing=50,
        modes=("phrygian", "minor"),
        keys=("E phrygian", "A minor", "F minor"),
        progressions=(
            "i-II",
            "i-i-vii-i",
            "minor: i-VI",
            "minor: i-VII",
        ),
        harmonic_rhythm=0.5,
        harmony="Essentially atonal: the 303 lines and a drone define a phrygian or minor centre; no real "
                "chords, maybe a single distorted stab.",
        voicing="power",
        comping="none",
        bass_style="sixteenths",
        bass="Overdriven TB-303 in relentless 16ths with accents and slides; often two 303s interlocking, "
             "one bass-register, one higher; the kick's distortion fills the low end.",
        melody_density="busy",
        melody_scale="phrygian",
        melody="The 303 is the lead: tight 16th patterns with b2 and b5 tension, octave jumps and slides, "
               "filter and resonance cranked for screams; vocal samples are shouts and chants.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x... x... x... x...",
            "clap":       ".... x... .... x...",
            "closed hat": "xxxx xxxx xxxx xxxx",
            "open hat":   "..x. ..x. ..x. ..x.",
            "ride":       "..x. ..x. ..x. ..x.",
        }},
        drums="Distorted 909 kick on every beat, offbeat open hats and ride, 16th closed hats, clap or snare "
              "on 2 and 4; snare rolls into peaks.",
        form=(("intro", 16), ("acid line", 32), ("build", 16), ("peak", 32), ("break", 16), ("peak", 32),
              ("outro", 16)),
        instruments=("TB-303", "TR-909", "distortion", "sampler", "FX"),
        sound_design="Multiple 303s through distortion pedals, saturated 909 kick, ride and hats with grit, "
                     "shouted samples, heavy delay throws.",
        production="Loud, gritty, mono-heavy; distortion everywhere; arrangement through acid filter and "
                   "resonance rides.",
        theory="The phrygian b2 against the tonic in the 303 line creates tension; accents and slides form a "
               "second rhythm over the 16ths. Composition is timbral escalation, not harmony.",
        mix=Mix(lufs=(-8, -6), lra=(3, 5), low_end="heavy", tone="bright", width="moderate"),
    ),
    Genre(
        name="hard techno",
        family="electronic dance",
        aliases=("schranz",),
        parent="techno",
        description="Faster, harder techno with pounding distorted kicks, looped percussion and relentless "
                    "energy; the 2020s wave adds rave stabs, trance leads and pitched vocals at 150+ BPM.",
        era="Europe (Germany, the UK, Belgium), mid 1990s; resurgent from about 2020",
        touchstones=("DJ Rush", "Ben Sims", "Chris Liebing", "Sven Wittekind", "Sara Landry", "Dax J",
                     "Klangkuenstler"),
        tempo=(140, 160),
        feel="four-on-the-floor, straight, aggressive",
        swing=50,
        modes=("minor", "phrygian"),
        keys=("F minor", "G minor", "A minor"),
        progressions=(
            "i-VI",
            "i-VII",
            "phrygian: i-II",
            "i-VI-III-VII",
        ),
        harmonic_rhythm=0.5,
        harmony="Little harmony: a minor or phrygian drone, rave stabs or a trance-style minor progression "
                "in the breakdown in modern versions.",
        voicing="power",
        comping="stabs",
        bass_style="offbeat",
        bass="Distorted rumble between kicks, or an offbeat saturated bass; the kick's tail is the bass.",
        melody_density="sparse",
        melody_scale="phrygian",
        melody="Loops of distorted stabs and screeches, rave hoover riffs, pitched-up vocal chops or spoken "
               "phrases; minimal pitch, maximal energy.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "X... X... X... X...",
            "clap":       ".... x... .... x...",
            "closed hat": "xxxx xxxx xxxx xxxx",
            "open hat":   "..x. ..x. ..x. ..x.",
            "rim":        "x..x ..x. .x.. x.x.",
        }},
        drums="Heavily distorted kick on every beat, offbeat open hats, 16th hats, claps on 2 and 4, looped "
              "and filtered percussion; schranz uses chopped, EQ-swept drum loops; builds use snare and kick "
              "rolls.",
        form=(("intro", 16), ("groove", 32), ("build", 16), ("peak", 32), ("break", 16), ("peak", 32),
              ("outro", 16)),
        instruments=("drum machine", "distortion", "rumble bass", "stab synth", "vocal sample", "FX"),
        sound_design="Overdriven kicks with long rumble tails, clipped percussion, metallic hits, hoover and "
                     "rave stabs, heavily processed vocals.",
        production="Very loud and dense, heavy clipping, kick-led low end; bright distorted highs; arrangement "
                   "by EQ and filter sweeps on loops.",
        theory="Energy through tempo, density and distortion; percussion loops in odd cycles against the "
               "4/4 pulse. Modern hard techno borrows trance and rave harmony in breakdowns.",
        mix=Mix(lufs=(-7, -5), lra=(2, 5), low_end="very heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="industrial techno",
        family="electronic dance",
        parent="techno",
        description="Techno fused with industrial noise and power electronics: distorted, metallic, abrasive "
                    "drums and dark atonal textures.",
        era="Birmingham and Berlin, mid 1990s; revived in the 2010s",
        touchstones=("Surgeon", "Regis", "Perc", "Ancient Methods", "Paula Temple", "Blawan", "Adam X"),
        tempo=(128, 145),
        feel="four-on-the-floor or broken, mechanical and punishing",
        swing=50,
        modes=("phrygian", "minor"),
        keys=("E phrygian", "F minor", "C minor"),
        progressions=(
            "i-II",
            "i-vii",
            "i-v°",
            "minor: i-VI",
        ),
        harmonic_rhythm=0.25,
        harmony="Atonal or drone-based: noise, metallic resonances, dissonant clusters and semitone movement "
                "(phrygian b2, tritone) instead of chords.",
        voicing="cluster",
        comping="none",
        bass_style="pedal",
        bass="Distorted drone or rumble on the tonic, or the kick and its distortion as the only bass.",
        melody_density="sparse",
        melody_scale="phrygian",
        melody="No melody in the conventional sense: screeching noise motifs, metallic loops and distorted "
               "vocal fragments.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "X... x... X... x..x",
            "snare":      ".... x... .... x...",
            "closed hat": "x.xx x.xx x.xx x.xx",
            "rim":        "..x. .x.. x... ..x.",
            "tom":        "...x .... ...x .x..",
        }},
        drums="Distorted kicks, sometimes with extra 16th kicks, metallic snares and claps, noise hats; "
              "Birmingham style uses broken, tribal tom patterns; Berlin style is a pounding 4/4.",
        form=(("intro", 16), ("groove", 32), ("noise", 16), ("peak", 32), ("break", 16), ("peak", 32),
              ("outro", 16)),
        instruments=("drum machine", "modular synth", "distortion", "noise generator", "field recordings",
                     "sampler"),
        sound_design="Overdriven 909s, metal-hit samples, feedback, bit-crushing, harsh noise and power "
                     "electronics, reverb as a dark room.",
        production="Saturated, dense, dark; distortion as a compositional tool; less focus on a polished "
                   "top end.",
        theory="Rhythm and timbre carry everything: polyrhythmic percussion against the kick, atonal pitch "
               "material using semitone and tritone relationships.",
        mix=Mix(lufs=(-8, -6), lra=(3, 6), low_end="heavy", tone="dark", width="wide"),
    ),
    Genre(
        name="dub techno",
        family="electronic dance",
        parent="techno",
        description="Techno through a dub reggae lens: a single minor chord stab dissolving into delay and "
                    "reverb over a deep, muffled kick and sub, hypnotic and submerged.",
        era="Berlin (Basic Channel, Chain Reaction), 1993-1998",
        touchstones=("Basic Channel", "Maurizio", "Rhythm & Sound", "Deepchord", "Porter Ricks",
                     "Vladislav Delay", "Echospace"),
        tempo=(115, 125),
        feel="four-on-the-floor, laid-back and spacious",
        swing=52,
        modes=("minor", "dorian"),
        keys=("C minor", "A minor", "F minor", "D minor"),
        progressions=(
            "i9-iv9",
            "i7-VImaj7",
            "dorian: i9-IV9",
            "i11-VII",
        ),
        harmonic_rhythm=0.25,
        harmony="One chord stab, usually a minor 7th, minor 9th or minor 11th, often voiced as stacked 4ths "
                "with no 3rd; changes every 4-8 bars if at all. The chord is a timbre that is constantly filtered "
                "and fed into delay.",
        voicing="quartal",
        comping="stabs",
        bass_style="pedal",
        bass="Deep, round sub pulse on the tonic, often offbeat or with dub-style rests; sometimes absent, the "
             "kick providing low end.",
        melody_density="sparse",
        melody_scale="dorian",
        melody="No melody: the chord stab's echoes and filter movement form the 'melody'; occasional vocal "
               "fragments in Rhythm & Sound style.",
        groove={"step": 0.25, "swing": 52, "pattern": {
            "kick":       "x... x... x... x...",
            "rim":        ".... x... .... x...",
            "closed hat": "..x. ..x. ..x. ..x.",
            "shaker":     "oxoo oxoo oxoo oxoo",
        }},
        drums="Muffled kick on every beat, soft rim or snare on 2 and 4, offbeat hats, hiss-like shakers; "
              "everything slightly low-passed and drenched in tape echo.",
        form=(("intro", 32), ("groove", 64), ("drift", 32), ("groove", 64), ("outro", 32)),
        instruments=("drum machine", "polysynth", "tape delay", "spring reverb", "sub bass", "noise"),
        sound_design="Chord stab through a resonant filter and tape delay with feedback near self-oscillation, "
                     "spring reverb, vinyl and tape hiss, low-passed drums.",
        production="Space and depth over loudness: wide delays, dark top end, dynamic mix, chord echoes "
                   "automated by hand like a dub engineer.",
        theory="Harmonic stasis with timbral motion: a single extended minor chord whose overtones change as "
               "the filter moves; dub delay subdivisions (dotted 8ths, triplets) add polyrhythm.",
        mix=Mix(lufs=(-12, -9), lra=(4, 8), low_end="heavy", tone="warm", width="wide"),
    ),
    Genre(
        name="melodic techno",
        family="electronic dance",
        aliases=("melodic house and techno",),
        parent="techno",
        description="Emotive, cinematic techno with arpeggiated synths, dark minor progressions and huge "
                    "breakdowns, sitting between techno's drive and trance's drama.",
        era="Berlin, Italy and Ibiza, 2010s (the Afterlife and Innervisions era)",
        touchstones=("Tale Of Us", "Stephan Bodzin", "Mind Against", "Adriatique", "Anyma", "Innellea",
                     "Kolsch"),
        tempo=(120, 126),
        feel="four-on-the-floor, rolling, straight 16ths",
        swing=50,
        modes=("minor", "phrygian", "harmonic minor"),
        keys=("F minor", "A minor", "C minor", "G minor"),
        progressions=(
            "i-VI-III-VII",
            "i-VI-iv-V",
            "i-iv-VI-v",
            "phrygian: i-II-i-vii",
            "VI-VII-i-i",
        ),
        harmonic_rhythm=0.5,
        harmony="Dark minor triads and sus chords, phrygian b2 colour and harmonic-minor V for drama; "
                "pads and arps carry the changes, often over a tonic pedal in the bass.",
        voicing="spread",
        comping="arpeggio_up",
        bass_style="offbeat",
        bass="Rolling offbeat or 16th bass sidechained to the kick, following the chord roots; often a "
             "Moog-style mono bass that moves with the arpeggio.",
        melody_density="medium",
        melody_scale="harmonic minor",
        melody="Long arpeggiated sequences (16ths) and sustained cinematic leads with slow filter sweeps; hooks "
               "are simple, modal and emotional, revealed in big breakdowns.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x... x... x... x...",
            "clap":       ".... x... .... x...",
            "closed hat": "xxxx xxxx xxxx xxxx",
            "open hat":   "..x. ..x. ..x. ..x.",
            "shaker":     "oxox oxox oxox oxox",
        }},
        drums="Clean, deep kick on every beat, clap on 2 and 4, offbeat open hats, 16th closed hats and "
              "shakers; percussion is restrained to give the synths room; big snare rolls and risers into drops.",
        form=(("intro", 32), ("groove", 32), ("build", 16), ("breakdown", 32), ("drop", 32), ("groove", 32),
              ("outro", 32)),
        instruments=("drum machine", "bass synth", "arpeggiator", "pads", "lead synth", "FX"),
        sound_design="Analog-style arps (Moog, Prophet, Diva), wide pads with long reverb, metallic plucks, "
                     "processed vocals, cinematic risers and impacts.",
        production="Polished and wide, with deep mono low end and sidechained pads; long breakdowns with "
                   "filtered drums; heavy automation on arps.",
        theory="Harmonic minor and phrygian colours (the raised 7th in V, the b2) for darker drama; "
               "arpeggios outline chords with pedal tones and voice-leading continuity.",
        mix=Mix(lufs=(-8, -6), lra=(3, 6), low_end="heavy", tone="dark", width="wide"),
    ),
    # ------------------------------------------------------------------ trance
    Genre(
        name="trance",
        family="electronic dance",
        parent="techno",
        description="Euphoric, hypnotic dance music built on repeating synth patterns, minor-key chord cycles, "
                    "long breakdowns and soaring leads that release into a driving four-on-the-floor.",
        era="Frankfurt and the Netherlands, early 1990s; the global superclub sound of 1997-2005",
        touchstones=("Sven Vath", "Paul van Dyk", "Armin van Buuren", "Tiesto", "Ferry Corsten",
                     "Robert Miles", "Above & Beyond"),
        tempo=(130, 140),
        feel="four-on-the-floor, straight 16ths, rolling",
        swing=50,
        modes=("minor",),
        keys=("A minor", "F minor", "C minor", "G# minor", "E minor"),
        progressions=(
            "i-VI-III-VII",
            "VI-VII-i-i",
            "i-iv-VI-VII",
            "i-VI-VII-v",
            "i-v-VI-III-iv-i-iv-V",
        ),
        harmonic_rhythm=0.5,
        harmony="Natural-minor progressions with each chord held one or two bars; sus2 and sus4 pads; the "
                "VI-VII-i 'epic' cadence; occasional harmonic-minor V at phrase ends; key changes up a semitone "
                "or tone in the last drop.",
        voicing="spread",
        comping="pulse_16",
        bass_style="offbeat",
        bass="Offbeat bass (a note on each 'and') or a rolling 16th bass with a gap on the kick (the 'x.xx' "
             "gallop), following chord roots; sidechained, mono.",
        melody_density="medium",
        melody_scale="minor",
        melody="Long, anthemic synth leads with wide leaps (5ths, octaves) and stepwise runs, built from 2-bar "
               "motifs repeated over the changing chords; gated supersaw patterns and arps in 16ths; female "
               "vocal toplines in vocal trance.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x... x... x... x...",
            "clap":       ".... x... .... x...",
            "closed hat": "xxxx xxxx xxxx xxxx",
            "open hat":   "..x. ..x. ..x. ..x.",
            "ride":       "..x. ..x. ..x. ..x.",
        }},
        drums="Solid kick on every beat, clap on 2 and 4, offbeat open hat, 16th closed hats, ride in the "
              "drop; 8- and 16-bar snare rolls accelerating from quarters to 16ths and 32nds before drops; "
              "crashes on phrase starts.",
        form=(("intro", 32), ("build", 16), ("break", 16), ("main", 32), ("breakdown", 32), ("build", 16),
              ("drop", 32), ("outro", 32)),
        instruments=("supersaw synth", "pluck synth", "pads", "bass synth", "drum machine", "FX and risers",
                     "vocal"),
        sound_design="Detuned supersaw leads (JP-8000 style), gated trance pads, acid lines in early trance, "
                     "plucky arps, long reverbs and dotted-8th delays, white-noise risers and downlifters.",
        production="Wide and bright with a tight mono low end; heavy sidechain on pads and bass; breakdowns "
                   "strip drums for 32 bars; filter and volume automation drive builds.",
        theory="Euphoria from aeolian loops: the VI-VII-i cadence (the 'Aeolian cadence') resolves without a "
               "leading tone; long phrase structure (16-32 bars) and tension-release from breakdown to drop. "
               "Gates and arps subdivide sustained harmony into 16ths.",
        mix=Mix(lufs=(-8, -6), lra=(4, 7), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="progressive trance",
        family="electronic dance",
        aliases=("prog trance",),
        parent="trance",
        description="Trance with progressive house's patience: smoother grooves, deep evolving arrangements and "
                    "restrained melodies that build over many minutes.",
        era="UK and the US, late 1990s-2000s",
        touchstones=("BT", "Way Out West", "Paul Oakenfold", "Markus Schulz", "Above & Beyond", "Hybrid"),
        tempo=(128, 136),
        feel="four-on-the-floor, smooth, straight 16ths",
        swing=50,
        modes=("minor",),
        keys=("A minor", "D minor", "F minor", "B minor"),
        progressions=(
            "i-VI-III-VII",
            "i-VI-VII-VII",
            "i-III-VII-iv",
            "VI-VII-i-i",
        ),
        harmonic_rhythm=0.5,
        harmony="Minor diatonic chords with sus and add9 colour, held two bars or more; often a pedal note "
                "in the bass or arp so changes are subtle.",
        voicing="spread",
        comping="arpeggio_up",
        bass_style="offbeat",
        bass="Rolling offbeat or 16th bass under the kick, filtered and evolving; sometimes a melodic bassline "
             "that moves stepwise between roots.",
        melody_density="medium",
        melody_scale="minor",
        melody="Arpeggio-led; leads are restrained, emerging in breakdowns; motifs develop slowly through "
               "filter and delay.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x... x... x... x...",
            "clap":       ".... x... .... x...",
            "closed hat": "x.xx x.xx x.xx x.xx",
            "open hat":   "..x. ..x. ..x. ..x.",
            "shaker":     "oxox oxox oxox oxox",
        }},
        drums="Steady kick, claps on 2 and 4, offbeat open hats, shuffling percussion loops; builds use "
              "filtered snare rolls rather than big crescendos.",
        form=(("intro", 32), ("groove", 32), ("build", 32), ("breakdown", 32), ("drop", 32), ("groove", 32),
              ("outro", 32)),
        instruments=("pluck synth", "arpeggiator", "pads", "bass synth", "drum machine", "FX"),
        sound_design="Warm analog plucks, gated pads, delays and reverbs with slow automation, subtle acid lines.",
        production="Long-form (8-10 minute) tracks; smooth dynamics; automation-driven evolution; wide but "
                   "not overly bright.",
        theory="Gradual change and harmonic pedal points: the same arpeggio over changing roots creates shifting "
               "chord qualities, a hypnotic form of voice-leading.",
        mix=Mix(lufs=(-9, -7), lra=(4, 7), low_end="heavy", tone="neutral", width="wide"),
    ),
    Genre(
        name="uplifting trance",
        family="electronic dance",
        aliases=("epic trance", "euphoric trance"),
        parent="trance",
        description="Trance at its most emotional: piano and string breakdowns, huge supersaw melodies and "
                    "explosive drops at 136-140 BPM.",
        era="Netherlands, UK and worldwide, 2000s-2010s",
        touchstones=("Aly & Fila", "John O'Callaghan", "Giuseppe Ottaviani", "Ferry Corsten", "Andy Blueman",
                     "Armin van Buuren"),
        tempo=(136, 140),
        feel="four-on-the-floor, galloping rolling bass, straight",
        swing=50,
        modes=("minor",),
        keys=("A minor", "F# minor", "D minor", "G# minor"),
        progressions=(
            "i-VI-III-VII",
            "VI-VII-i-i",
            "iv-VI-VII-i",
            "i-v-VI-III-iv-i-iv-V",
            "VI-III-VII-i",
        ),
        harmonic_rhythm=1,
        harmony="Diatonic minor progressions with frequent use of VI-VII-i, add9 and sus voicings; breakdown "
                "chords on piano and strings; modulation up a tone or semitone after the climax.",
        voicing="spread",
        comping="pulse_16",
        bass_style="offbeat",
        bass="Rolling 16th 'gallop' bass (rest on the kick, three 16ths after) or offbeat bass, following roots.",
        melody_density="busy",
        melody_scale="minor",
        melody="Big, memorable lead melodies with octave leaps, suspensions and runs, harmonised in 3rds or "
               "6ths with supersaw stacks; piano introduces the theme in the breakdown.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x... x... x... x...",
            "clap":       ".... x... .... x...",
            "closed hat": "xxxx xxxx xxxx xxxx",
            "open hat":   "..x. ..x. ..x. ..x.",
            "ride":       "x.x. x.x. x.x. x.x.",
        }},
        drums="Powerful kick on every beat, claps on 2 and 4, offbeat open hats, 16th hats; long snare rolls "
              "accelerating before the drop, reverse crash and impact on the downbeat.",
        form=(("intro", 32), ("main", 32), ("breakdown", 32), ("build", 16), ("drop", 32), ("break", 16),
              ("drop", 32), ("outro", 32)),
        instruments=("supersaw synth", "piano", "strings", "pads", "bass synth", "drum machine", "FX"),
        sound_design="Thick supersaws, gated pads, piano and string ensembles, big reverbs, noise risers and "
                     "impacts.",
        production="Bright and wide; the drop is the loudest moment, with all layers and sidechain pumping; "
                   "large dynamic contrast between breakdown and drop.",
        theory="Aeolian harmony with occasional harmonic-minor V for a stronger cadence; melodies stress "
               "suspensions (sus4-3, 9-8) for emotional tension; final modulation for lift.",
        mix=Mix(lufs=(-8, -6), lra=(4, 8), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="psytrance",
        family="electronic dance",
        aliases=("psychedelic trance", "psy"),
        parent="trance",
        description="Fast, psychedelic trance: a punchy kick and galloping 16th bass, swirling phrygian synth "
                    "riffs and alien FX, built for outdoor festivals.",
        era="Goa (India) and Israel, early-to-mid 1990s; global festival scene since",
        touchstones=("Astral Projection", "Infected Mushroom", "Astrix", "Hallucinogen", "Vini Vici",
                     "Ace Ventura", "GMS"),
        tempo=(138, 148),
        feel="four-on-the-floor with rolling 16th bass (KBBB)",
        swing=50,
        modes=("phrygian", "harmonic minor", "phrygian dominant"),
        keys=("E phrygian", "F# phrygian", "A phrygian"),
        progressions=(
            "i-II",
            "i-i-II-i",
            "i-vii",
            "harmonic minor: i-V",
        ),
        harmonic_rhythm=0.25,
        harmony="Little harmony: a phrygian or harmonic-minor drone; the b2 and the raised 7th (phrygian "
                "dominant) supply the exotic tension; leads imply chords.",
        voicing="power",
        comping="none",
        bass_style="sixteenths",
        bass="The signature 'rolling bass': a short 16th note after each kick, three notes per beat (K-B-B-B), "
             "usually the tonic, sometimes with octave and b2 notes; tightly synced to the kick.",
        melody_density="busy",
        melody_scale="phrygian dominant",
        melody="Twisting 16th synth riffs and acid-like lines in phrygian or harmonic minor, call-and-response "
               "between left and right; spoken-word samples from films.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "X... X... X... X...",
            "snare":      ".... x... .... x...",
            "closed hat": ".xxx .xxx .xxx .xxx",
            "open hat":   "..x. ..x. ..x. ..x.",
            "ride":       "..x. ..x. ..x. ..x.",
        }},
        drums="Punchy, short kick on every beat (clean, no tail, to leave room for the bass), snare on 2 and 4 "
              "(often subtle), offbeat open hats and rides, 16th hats; constant small fills and FX in every "
              "4-8 bars.",
        form=(("intro", 32), ("main", 64), ("break", 16), ("main", 64), ("breakdown", 32), ("main", 64),
              ("outro", 32)),
        instruments=("bass synth", "lead synth", "drum machine", "FX synth", "sampler"),
        sound_design="Tight, punchy kick tuned to the bass; FM and saw bass with short envelopes; acid-like "
                     "leads with resonance; zaps, swirls and FX from heavy LFO and delay modulation.",
        production="Very tight kick-bass relationship (bass sidechain or programmed between kicks), bright "
                   "busy top end, huge stereo FX; 8-minute tracks.",
        theory="Phrygian and phrygian-dominant scales give the exotic sound; the KBBB 16th grid and constant "
               "variation every 4 bars create hypnotic forward motion.",
        mix=Mix(lufs=(-7, -5), lra=(2, 5), low_end="very heavy", tone="bright", width="wide"),
    ),
    # ------------------------------------------------------------------ EDM and festival
    Genre(
        name="piano house",
        family="electronic dance",
        aliases=("90s house", "italo house", "90s piano house"),
        parent="house",
        description="Late-80s and 90s club house built on a sampled piano riff: syncopated M1-piano chord stabs "
                    "(or organ stabs), a big diva vocal and a pumping 909 groove, the sound of Italo house and the "
                    "early-90s club anthems.",
        era="Italy, the UK and the US club scene, 1988-1996",
        touchstones=("Black Box", "Livin' Joy", "Robin S", "Crystal Waters", "CeCe Peniston", "Alison Limerick",
                     "Ultra Naté", "Inner City"),
        tempo=(118, 128),
        feel="four-on-the-floor, punchy, with a light shuffle in the hats",
        swing=53,
        modes=("major", "minor", "dorian"),
        keys=("C major", "G major", "F major", "A minor", "D minor"),
        progressions=(
            "major: I-IV",
            "major: ii7-V7sus4-Imaj7-vi7",
            "i7-iv7",
            "dorian: i7-IV9",
            "i-VI-VII-i",
        ),
        harmonic_rhythm=1,
        harmony="Two- to four-chord loops: major triads with added 9ths and sus4s in the gospel-flavoured hits, "
                "minor 7ths in darker ones. The piano riff is the harmony: right-hand chords between about C4 "
                "and C5, the left hand doubling the root in octaves below, stabs syncopated and anticipating "
                "the next chord by a 16th or an 8th. Key changes are rare.",
        voicing="close",
        comping="stabs",
        bass_style="offbeat",
        bass="Offbeat or octave-jumping synth or organ bass in the gaps between kicks, following the chord roots; "
             "ducked by the kick.",
        melody_density="sparse",
        melody_scale="major pentatonic",
        melody="The vocal (or a sampled diva phrase) carries the tune; the piano riff answers it. The "
               "instrumental hook is the piano riff itself, one or two bars repeated, not a separate lead synth "
               "line on top.",
        groove={"step": 0.25, "swing": 53, "pattern": {
            "kick":       "x... x... x... x...",
            "clap":       ".... x... .... x...",
            "closed hat": "x.x. x.x. x.x. x.x.",
            "open hat":   "..x. ..x. ..x. ..x.",
            "shaker":     "oxox oxox oxox oxox",
        }},
        drums="909 kick on every beat, clap on 2 and 4, open hats on the offbeats, closed hats or shaker in "
              "16ths, tambourine on 2 and 4; snare rolls and drop-outs into the chorus.",
        form=(("intro", 16), ("piano riff", 8), ("verse", 16), ("chorus", 16), ("breakdown", 16), ("chorus", 16),
              ("piano riff", 8), ("outro", 16)),
        instruments=("drum machine (909)", "M1-style house piano", "organ", "bass synth", "string pad",
                     "diva vocal"),
        sound_design="The Korg M1 'Piano 16'' preset is the sound: a bright, compressed, slightly synthetic sampled "
                     "piano with a fast decay. Get close with a ROMpler or sample-based piano preset, or a "
                     "plain piano layered with a quiet FM electric piano or organ; keep the release short. An "
                     "acoustic piano model sounds too polite and turns harsh if brightened to compensate. Organ "
                     "stabs (the M1 'Organ 2') for the Robin S side; lush strings in breakdowns.",
        production="Piano riff forward in the mids but not harsh: high-pass it around 150-200 Hz so the bass owns "
                   "the low end, light compression, a short plate or room; vocal on top; kick sidechain on bass "
                   "and pads.",
        theory="Gospel-derived major harmony (added 9ths, sus chords) over a dance groove. The syncopation of the "
               "riff, with stabs on the 'and' and anticipated chord changes, supplies the drive, so the chords "
               "themselves can stay simple.",
        mix=Mix(lufs=(-9, -7), lra=(4, 7), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="eurodance",
        family="electronic dance",
        aliases=("euro dance", "90s eurodance"),
        parent="house",
        description="1990s European dance-pop: pounding four-on-the-floor beats, minor-key synth riffs, a rapped "
                    "verse and a soaring sung chorus.",
        era="Germany, Belgium, Italy and the Netherlands, 1990-1997",
        touchstones=("2 Unlimited", "Haddaway", "Snap!", "Culture Beat", "Corona", "La Bouche", "Dr. Alban"),
        tempo=(124, 145),
        feel="four-on-the-floor, straight, punchy",
        swing=50,
        modes=("minor",),
        keys=("A minor", "G minor", "D minor", "F minor"),
        progressions=(
            "i-VI-III-VII",
            "i-VI-VII-i",
            "i-iv-VII-III",
            "VI-VII-i-i",
            "i-VII-VI-VII",
        ),
        harmonic_rhythm=1,
        harmony="Simple diatonic minor progressions, one chord per bar, repeated through verse and chorus; "
                "piano, organ or synth stabs on the offbeat, voiced around C4-C5 with the bass below. Some hits "
                "jump up a tone for the last chorus, but it sounds dated and cheesy today: use it only when the "
                "brief wants that.",
        voicing="close",
        comping="offbeat",
        bass_style="octaves",
        bass="Driving 8th-note octave bass or offbeat bass following chord roots.",
        melody_density="medium",
        melody_scale="minor",
        melody="A catchy instrumental synth hook alternating with a sung female chorus and a male rap verse; "
               "the hook is a one- or two-bar motif repeated four to eight times within an octave, on its own "
               "lead sound, above the stabs rather than doubling them.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x... x... x... x...",
            "snare":      ".... x... .... x...",
            "clap":       ".... x... .... x...",
            "closed hat": "x.x. x.x. x.x. x.x.",
            "open hat":   "..x. ..x. ..x. ..x.",
        }},
        drums="Punchy 909/drum-machine kick on every beat, snare and clap on 2 and 4, offbeat open hats; "
              "snare rolls into choruses.",
        form=(("intro", 16), ("hook", 8), ("verse", 16), ("chorus", 16), ("hook", 8), ("verse", 16),
              ("chorus", 16), ("break", 8), ("chorus", 16), ("outro", 8)),
        instruments=("synth lead", "piano or stab synth", "bass synth", "drum machine", "vocals", "rap"),
        sound_design="Workstation and ROMpler sounds (Korg M1, Roland JD-800/JD-990): M1-style sampled piano and "
                     "organ stabs, detuned-saw or hoover leads, gated pads, big reverb snares. A sampled or preset "
                     "'house piano' rather than an acoustic piano model.",
        production="Pop-oriented mixing: loud vocals, bright synths, clear radio-friendly structure; "
                   "compression for punch.",
        theory="Minor-key pop with dance rhythm: the i-VI-III-VII cycle and a strong instrumental hook; "
               "verse-chorus form inside dance-friendly 8-bar phrases.",
        mix=Mix(lufs=(-9, -7), lra=(4, 7), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="eurobeat",
        family="electronic dance",
        aliases=("euro beat", "super eurobeat", "initial d", "90s eurobeat", "para para"),
        parent="italo disco",
        description="Italian-made, Japan-loved high-speed dance-pop: a galloping octave bass, brass and supersaw "
                    "stabs, a screaming synth riff and a melodramatic minor-key chorus, racing at 150-160 BPM.",
        era="Italy (A-Beat C, Delta, Time, SCP) for Japan's Avex 'Super Eurobeat' series, 1990-2005",
        touchstones=("Dave Rodgers", "Manuel", "Max Coveri", "Ken Blast", "Niko", "Super Eurobeat compilations",
                     "Initial D soundtrack"),
        tempo=(150, 160),
        feel="four-on-the-floor, straight and driving, at a sprint",
        swing=50,
        modes=("minor",),
        keys=("A minor", "E minor", "F# minor", "C# minor", "G minor"),
        progressions=(
            "i-VI-VII-i",
            "i-VII-VI-VII",
            "VI-VII-i-i",
            "iv-V7/V-V-V",
            "iv-VII-III-VI-ii°-V-i-i",
            "i-VI-III-VII",
        ),
        harmonic_rhythm=1,
        harmony="Natural-minor loops, one chord per bar: i-VI-VII-i in the verse, i-VII-VI-VII or VI-VII-i in the "
                "chorus. The pre-chorus climbs iv-VI-VII to the major V (harmonic minor), often through V7/V, so the "
                "chorus lands hard on i. The last chorus jumps up a tone or two (build_song lift_last_chorus) and "
                "stays there; the drama is the point, so here it isn't cheesy, it's expected.",
        voicing="close",
        comping="stabs",
        bass_style="octaves",
        bass="The galloping octave bass: root on the beat, octave on the offbeat, 8ths all song, with 16th pickups "
             "and octave flips into each chord; a punchy, slightly filtered saw or square bass, mid-forward, not a "
             "sub, following every chord root.",
        melody_density="busy",
        melody_scale="harmonic minor",
        melody="Two leads: the synth riff, a busy 16th-note hook high in the octave above C5, played in the intro, "
               "between choruses and as the solo; and the sung chorus, a long, soaring, melodramatic line with big "
               "leaps to the 5th and the raised 7th leaning into the tonic. The riff is the song's identity: catchy, "
               "sequenced across the chords, repeated with small changes.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x... x... x... x...",
            "snare":      ".... x... .... x...",
            "clap":       ".... x... .... x...",
            "closed hat": "xo.o xo.o xo.o xo.o",
            "open hat":   "..x. ..x. ..x. ..x.",
        }},
        drums="Hard, short kick on every beat, snare and clap together on 2 and 4, open hats on every offbeat with "
              "16th closed hats between; 16th snare rolls into every chorus, crashes on the downbeats; the kick "
              "drops out for a bar before the last chorus.",
        form=(("intro", 8), ("synth hook", 16), ("verse", 16), ("pre-chorus", 8), ("chorus", 16), ("synth hook", 8),
              ("verse", 16), ("pre-chorus", 8), ("chorus", 16), ("synth hook", 16), ("break", 8), ("chorus", 16),
              ("outro", 16)),
        instruments=("synth lead", "brass synth", "supersaw stab synth", "octave bass synth", "drum machine",
                     "vocals", "orchestra hit"),
        sound_design="Bright, hard-edged 90s digital synths (JD-800, Nord Lead, JP-8000 supersaw): a detuned saw or "
                     "square lead with portamento and delay, stacked brass and supersaw stabs, orchestra hits, a "
                     "plucky saw bass; 909-style kick and a sharp clap-snare with short bright reverb.",
        production="Bright and forward: the synth lead and brass sit on top, vocals right behind them, the bass "
                   "punchy in the low mids rather than a deep sub; little sidechain pumping, bus compression for "
                   "density and a crisp top end; 4-5 minute extended mixes.",
        theory="Minor-key Hi-NRG at speed: diatonic natural-minor loops brightened by the harmonic-minor V and "
               "secondary dominants at the pre-chorus; the relentless octave bass doubles the harmonic rhythm's "
               "pulse, and the key change up into the last chorus is the climax.",
        fill_style="snare_roll",
        mix=Mix(lufs=(-9, -7), lra=(4, 7), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="edm",
        family="electronic dance",
        aliases=("edm pop", "festival edm"),
        parent="house",
        description="The 2010s festival and radio dance sound: pop toplines over build-ups and drops, big "
                    "supersaw chords, sidechain pumping and a hands-in-the-air release.",
        era="US and European festival circuit, 2009-2016 and onward",
        touchstones=("Avicii", "Calvin Harris", "Swedish House Mafia", "David Guetta", "Zedd", "Martin Garrix"),
        tempo=(124, 150),
        feel="four-on-the-floor build-and-drop, sometimes half-time drops",
        swing=50,
        modes=("minor", "major"),
        keys=("F minor", "A minor", "C major", "G major", "E minor"),
        progressions=(
            "i-VI-III-VII",
            "major: vi-IV-I-V",
            "major: I-V-vi-IV",
            "major: IV-V-vi-vi",
            "VI-VII-i-i",
        ),
        harmonic_rhythm=1,
        harmony="Four-chord pop loops (one chord per bar) with add9 and sus colours; piano chords in the verse, "
                "big supersaw stacks in the drop; the drop often repeats the chorus progression.",
        voicing="spread",
        comping="offbeat",
        bass_style="offbeat",
        bass="Sidechained offbeat bass or sustained saw bass following roots, pumping with the kick.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Pop vocal topline in verse and chorus; the drop is a synth lead or vocal chop playing a simple, "
               "repetitive hook; melodies use pentatonic shapes and repeated notes.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x... x... x... x...",
            "clap":       ".... x... .... x...",
            "closed hat": "x.x. x.x. x.x. x.x.",
            "open hat":   "..x. ..x. ..x. ..x.",
            "snare":      ".... .... .... x.x.",
        }},
        drums="Layered kick on every beat in drops, clap on 2 and 4, offbeat open hats; build-ups with "
              "accelerating snare rolls and risers; drops start with a beat of silence or a vocal 'drop' cue.",
        form=(("intro", 8), ("verse", 16), ("pre-chorus", 8), ("build", 8), ("drop", 16), ("verse", 16),
              ("build", 8), ("drop", 16), ("bridge", 8), ("drop", 16), ("outro", 8)),
        instruments=("supersaw synth", "piano", "pluck synth", "bass synth", "drum samples", "vocals", "FX"),
        sound_design="Huge layered supersaws, pluck synths, piano, vocal chops, white-noise risers and impacts, "
                     "layered punchy kicks.",
        production="Very loud masters, heavy sidechain on everything, wide stereo leads, clean mono low end; "
                   "pop vocal production.",
        theory="Pop four-chord harmony in a dance framework; tension built through risers, rising pitch and "
               "accelerating snare subdivisions, released in the drop.",
        mix=Mix(lufs=(-8, -5), lra=(3, 6), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="big room",
        family="electronic dance",
        aliases=("big room house",),
        parent="electro house",
        description="Festival house stripped down for the main stage: a colossal kick, long snare-roll builds and "
                    "a sparse drop of a single stabbing synth riff and percussion.",
        era="Netherlands and the festival circuit, 2012-2016",
        touchstones=("Hardwell", "Martin Garrix", "W&W", "Dimitri Vegas & Like Mike", "Showtek", "Nicky Romero",
                     "Quintino"),
        tempo=(126, 130),
        feel="four-on-the-floor, stomping, straight",
        swing=50,
        modes=("minor", "phrygian"),
        keys=("F minor", "G minor", "A minor"),
        progressions=(
            "i-VI-III-VII",
            "i-i-VI-VII",
            "VI-VII-i-i",
            "phrygian: i-II",
        ),
        harmonic_rhythm=0.5,
        harmony="Chords appear mostly in the breakdown (piano or supersaw); the drop is nearly harmony-less, "
                "a single riff or octave stab on the tonic and b2 or b6.",
        voicing="power",
        comping="stabs",
        bass_style="offbeat",
        bass="Little bass in the drop besides the kick; offbeat sidechained bass in builds and breakdowns.",
        melody_density="sparse",
        melody_scale="phrygian",
        melody="Drop riff: a short, rhythmic synth stab pattern (often a few notes in octaves) with heavy "
               "rhythmic syncopation; breakdowns have simple piano or vocal melodies.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "X... X... X... X...",
            "clap":       ".... x... .... x...",
            "open hat":   "..x. ..x. ..x. ..x.",
            "tom":        "...x ..x. ...x .x..",
            "snare":      ".... .... .... .xxx",
        }},
        drums="Massive layered kick on every beat, clap on 2 and 4, offbeat hats, tribal toms and percussion; "
              "16- or 32-bar snare rolls into the drop, often with a silence and a 'hey' shout.",
        form=(("intro", 16), ("build", 16), ("breakdown", 16), ("build", 16), ("drop", 16), ("break", 16),
              ("build", 16), ("drop", 16), ("outro", 16)),
        instruments=("layered kick", "lead synth", "piano", "tribal toms", "vocal shouts", "FX"),
        sound_design="Huge, long-tailed kick, detuned 'big room' leads (often a pitched-down supersaw or "
                     "reese), white-noise risers, shouted vocal samples.",
        production="Extremely loud masters, kick dominant, sparse drop for impact; heavy sidechain; wide but "
                   "simple stereo field.",
        theory="Minimalism in the drop: riff and rhythm over harmony; tension through long builds with rising "
               "pitch, accelerating snares and silence before the downbeat.",
        mix=Mix(lufs=(-6, -4), lra=(2, 5), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="future bass",
        family="electronic dance",
        parent="dubstep",
        description="Lush, emotional bass music: swelling, sidechained supersaw chords that wobble in pitch, "
                    "pitched vocal chops and half-time, trap-flavoured drums.",
        era="Australia (Flume) and the US/UK SoundCloud scene, 2012-2018",
        touchstones=("Flume", "San Holo", "Illenium", "Louis The Child", "Cashmere Cat", "Porter Robinson",
                     "Wave Racer"),
        tempo=(130, 160),
        feel="half-time drums at double-time tempo (snare on 3), triplet and 32nd hat rolls",
        swing=50,
        modes=("major", "lydian"),
        keys=("C major", "F major", "D major", "G major", "Eb major"),
        progressions=(
            "IVmaj7-V-iii7-vi7",
            "IVmaj7-V7-iii7-vi9",
            "vi7-IVmaj7-I-V",
            "Imaj7-iii7-vi9-IVmaj9",
            "IVmaj9-Iadd9-V-vi7",
            "minor: VImaj7-VII-i7-v7",
        ),
        harmonic_rhythm=1,
        harmony="Rich major 7ths, 9ths and 11ths borrowed from J-pop and neo-soul; the 'royal road' "
                "IVmaj7-V-iii7-vi progression and IV-to-I plagal lifts; chords voiced wide over two or three "
                "octaves with added 9ths on top, and swelled with volume and pitch automation.",
        voicing="spread",
        comping="stabs",
        bass_style="808",
        bass="Clean sub or 808 on the chord roots, sustained under each chord and ducked hard by the kick; "
             "glides between roots; sometimes a mid-range growl layered with the chord stabs in the drop.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Hooks made from pitched and formant-shifted vocal chops, played like a synth in syncopated "
               "8ths and 16ths; pentatonic, repetitive, with octave jumps; verses carry a pop vocal topline.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x... .... ..x. .... x... ..x. .... ....",
            "snare":      ".... .... x... .... .... .... x... ....",
            "clap":       ".... .... x... .... .... .... x... ...x",
            "closed hat": "x.x. x.xx x.x. xxxx x.x. x.xx x.x. xxxx",
        }},
        drums="Half-time pattern: kick on 1 with a syncopated second kick, snare and clap layered on beat 3, "
              "trap-style hats with triplet and 32nd rolls; the drop's chord stabs are programmed in rhythm "
              "with the kick and snare so harmony becomes percussion.",
        form=(("intro", 8), ("verse", 16), ("build", 8), ("drop", 16), ("verse", 16), ("build", 8),
              ("drop", 16), ("bridge", 8), ("drop", 16), ("outro", 8)),
        instruments=("supersaw synth", "vocal chops", "808 or sub bass", "drum samples", "pluck synth", "FX"),
        sound_design="Supersaw chord stacks (Serum, Sylenth) with a fast volume swell, heavy sidechain and a "
                     "pitch LFO wobble; formant-shifted vocal chops; glitchy stutter FX, white-noise risers, "
                     "bright plucks and bell layers.",
        production="Loud, bright and very wide; volume-shaping (LFOTool-style) on the chords for the pump; "
                   "sub kept mono, chords split wide; drops lean on the chord rhythm rather than bass weight.",
        theory="Jazz and J-pop harmony (major 7ths, 9ths, the royal-road IV-V-iii-vi) in a half-time bass-music "
               "frame; rhythmic gating of sustained chords turns harmony into groove, with syncopated 3+3+2 "
               "stab patterns over the half-time backbeat.",
        mix=Mix(lufs=(-7, -5), lra=(3, 6), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="electro house",
        family="electronic dance",
        aliases=("complextro", "dirty electro"),
        parent="house",
        description="House with distorted, buzzing bass synths and aggressive filtered saw riffs over a hard "
                    "four-on-the-floor beat, loud and brash.",
        era="Europe and North America, 2005-2012 (the blog-house and Ed Banger era)",
        touchstones=("Benny Benassi", "Deadmau5", "Wolfgang Gartner", "Feed Me", "The Bloody Beetroots",
                     "Justice", "MSTRKRFT"),
        tempo=(125, 130),
        feel="four-on-the-floor, punchy and straight",
        swing=50,
        modes=("minor", "phrygian"),
        keys=("F minor", "A minor", "D minor", "G minor"),
        progressions=(
            "i-VI-VII-i",
            "i-VI-III-VII",
            "i-iv-VI-VII",
            "phrygian: i-II",
            "i-i-VII-VI",
        ),
        harmonic_rhythm=1,
        harmony="Simple minor progressions, often only implied by the bass riff; distorted power-chord or "
                "octave stabs in drops; breakdowns may bring in a straight triad pad or piano to show the "
                "changes.",
        voicing="power",
        comping="stabs",
        bass_style="syncopated",
        bass="The hook: a distorted saw or square bass with heavy filter and envelope modulation in a "
             "syncopated 16th riff, root-heavy with octave and b7/b6 moves; complextro chops between several "
             "bass patches every 8th or 16th.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="Riffs instead of tunes: 1-2 bar synth figures with lots of repeated notes and rests, "
               "call-and-response between bass and lead, vocal samples or spoken hooks.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x... x... x... x...",
            "clap":       ".... x... .... x...",
            "snare":      ".... x... .... x...",
            "closed hat": "x.x. x.x. x.x. x.x.",
            "open hat":   "..x. ..x. ..x. ..x.",
        }},
        drums="Punchy, compressed kick on every beat, layered clap and snare on 2 and 4, offbeat open hats, "
              "8th closed hats; 8-bar snare rolls and white-noise risers into the drop; occasional half-bar "
              "kick drops for impact.",
        form=(("intro", 16), ("build", 16), ("drop", 32), ("break", 16), ("build", 16), ("drop", 32),
              ("outro", 16)),
        instruments=("distorted bass synth", "lead synth", "drum samples", "vocal samples", "FX"),
        sound_design="Overdriven and bitcrushed saw basses with resonant filter sweeps (the 'Satisfaction' "
                     "buzz), formant and comb-filtered leads, crunchy sampled drums with hard transients.",
        production="Loud and bright, heavy sidechain from the kick, bass and kick tightly arranged so the bass "
                   "speaks between kicks; mono low end, distorted mids pushed forward, wide stereo leads.",
        theory="Riff-based harmony and timbral variation as the hook: the same few notes re-voiced by filter, "
               "distortion and patch switching; syncopated 16th basslines against the straight kick.",
        mix=Mix(lufs=(-7, -5), lra=(3, 5), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="electro",
        family="electronic dance",
        aliases=("electro funk",),
        parent="funk",
        description="Robotic funk built on the Roland TR-808: syncopated booming kicks, crisp handclaps, "
                    "vocoder vocals and sci-fi synth riffs; a root of techno and Miami bass.",
        era="New York and Detroit, 1982-1986; the Detroit and European electro revival of the 1990s",
        touchstones=("Afrika Bambaataa & Soulsonic Force", "Cybotron", "Kraftwerk", "Egyptian Lover", "Drexciya",
                     "Arthur Baker", "Dopplereffekt"),
        tempo=(120, 135),
        feel="syncopated straight 16ths, funk-derived, no four-on-the-floor",
        swing=50,
        modes=("minor", "phrygian"),
        keys=("E minor", "A minor", "D minor", "C minor"),
        progressions=(
            "i-VII",
            "i-iv",
            "phrygian: i-II",
            "i-VI-VII-i",
            "i7-iv7",
        ),
        harmonic_rhythm=0.5,
        harmony="Minor and phrygian riffs with little harmonic motion: one or two chords, often a minor triad "
                "stab or pad moving to the b7 or b2; Drexciya-style electro adds dark, detuned string pads.",
        voicing="close",
        comping="stabs",
        bass_style="syncopated",
        bass="The 808 kick's long boom doubles as bass, plus a funky synth bass riff in syncopated 16ths with "
             "rests, octave jumps and slides, locking with the kick pattern.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="Vocoder and robotic vocals, rap in the hip-hop strand; short square-wave or saw synth riffs "
               "of 2-4 notes, sci-fi bleeps and orchestra-hit stabs.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x... ..x. ..x. .... x... ..x. .x.. ..x.",
            "snare":      ".... x... .... x... .... x... .... x...",
            "clap":       ".... x... .... x... .... x... .... x...",
            "closed hat": "xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx",
            "cowbell":    "x..x ..x. .... .... x..x ..x. .... ....",
        }},
        drums="TR-808 programmed like a funk drummer: syncopated kicks on the 'and' and 'a' with long boom, "
              "snare and handclap together on 2 and 4, straight 16th hats, cowbell and conga accents, tom "
              "fills; the kick pattern changes in the second bar.",
        form=(("intro", 16), ("verse", 16), ("chorus", 16), ("break", 16), ("verse", 16), ("chorus", 16),
              ("outro", 16)),
        instruments=("TR-808", "synth bass", "vocoder", "lead synth", "sampler"),
        sound_design="Iconic 808 tones (long-decay kick, snappy snare, claps, cowbell), vocoders, square and "
                     "saw leads, Fairlight orchestra hits, laser and sci-fi FX.",
        production="Clean, crisp and dry, 808s upfront, synths wide, kick and bass mono; dynamic compared with "
                   "modern dance music.",
        theory="Funk syncopation transferred to a drum machine: the kick avoids four-on-the-floor and plays "
               "a breakbeat-like 3+3+2 pattern, while the backbeat stays rigid; harmony is a modal riff (aeolian "
               "or phrygian).",
        mix=Mix(lufs=(-11, -8), lra=(4, 8), low_end="heavy", tone="neutral", width="moderate"),
    ),
    # ------------------------------------------------------------------ drum and bass
    Genre(
        name="drum and bass",
        family="electronic dance",
        aliases=("dnb", "d&b", "drum n bass"),
        parent="jungle",
        description="Fast breakbeat music at around 174 BPM: a tight two-step beat of kick and snare, a huge "
                    "sub or reese bass moving at half the speed, and anything from soul to sci-fi on top.",
        era="UK (London, Bristol), from about 1994-95 as jungle refined; global since",
        touchstones=("Goldie", "Roni Size", "Andy C", "Pendulum", "Noisia", "Sub Focus", "Chase & Status"),
        tempo=(165, 178),
        feel="two-step breakbeat at double time, the bass and chords moving at half-time",
        swing=50,
        modes=("minor", "phrygian"),
        keys=("F minor", "E minor", "G minor", "A minor", "D minor"),
        progressions=(
            "i-VI-III-VII",
            "i-VI-VII-i",
            "i-iv-VI-v",
            "phrygian: i-II",
            "i9-iv9",
        ),
        harmonic_rhythm=0.5,
        harmony="Minor-key loops with chords held for two bars (one bar at 174 feels fast); minor 7ths and "
                "9ths in liquid styles, power-chord stabs and drones in rollers and neuro; the bass often "
                "states the harmony on its own.",
        voicing="open",
        comping="sustain",
        bass_style="reese",
        bass="Sub bass and/or a reese (detuned saws, phasing) playing long notes and slides at half-time, "
             "sitting in the gaps of the kick; rollers use a repeated one-bar sub riff, jump-up uses "
             "wobbling, bouncing mid-bass.",
        melody_density="medium",
        melody_scale="minor",
        melody="Melodies move at half-time against the fast drums: long pad lines, vocal hooks in liquid and "
               "vocal DnB, short synth stabs and atmospheric motifs; MC chants in the club tradition.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x... .... ..x. .... ..x. .... ..x. ....",
            "snare":      ".... X..o .... X... .... X..o .o.. X...",
            "closed hat": "x.x. x.x. x.x. x.x. x.x. x.x. x.x. x.x.",
            "shaker":     "oxox oxox oxox oxox oxox oxox oxox oxox",
            "ride":       "..x. ..x. ..x. ..x. ..x. ..x. ..x. ..x.",
        }},
        drums="The two-step: kick on 1 and the 'and' of 3, snare cracking on 2 and 4, ghost snares and "
              "chopped break layers (Amen, Think, Apache) under programmed hits; 8th or 16th hats and "
              "shakers; 8- and 16-bar fills from break edits.",
        form=(("intro", 32), ("build", 16), ("drop", 32), ("break", 16), ("build", 8), ("drop", 32),
              ("outro", 32)),
        instruments=("drum breaks", "sub bass", "reese bass", "pads", "synth stabs", "vocal", "FX"),
        sound_design="Layered snares with a sharp crack and short reverb, tight kicks, clean sine subs, "
                     "reese and FM mid-basses with distortion and movement, wide atmospheric pads and "
                     "risers.",
        production="Very loud and bright: the snare is the loudest transient, sub kept mono and clean under "
                   "100 Hz, mid-bass processed in parallel; DJ intros of 32 bars; drop at bar 33.",
        theory="Two rhythmic layers at once: drums in fast 16ths at 174 and bass and harmony moving at 87 "
               "(half-time). Syncopation from the off-beat second kick against the backbeat; harmony is "
               "aeolian or phrygian loops.",
        mix=Mix(lufs=(-8, -6), lra=(3, 7), low_end="very heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="jungle",
        family="electronic dance",
        aliases=("ragga jungle",),
        parent="breakbeat",
        description="The raw ancestor of drum and bass: chopped, rearranged Amen breaks at 160-170 BPM over "
                    "deep reggae-derived sub bass, with ragga vocal samples and rave stabs.",
        era="London and the UK rave scene, 1992-1995",
        touchstones=("Shy FX", "Congo Natty", "Remarc", "DJ Hype", "Dillinja", "M-Beat", "Ed Rush"),
        tempo=(158, 172),
        feel="frantic chopped breakbeats over half-time dub bass",
        swing=52,
        modes=("minor",),
        keys=("A minor", "E minor", "G minor", "D minor"),
        progressions=(
            "i-VII",
            "i-iv",
            "i-VI-VII-i",
            "i-i-VI-VII",
        ),
        harmonic_rhythm=0.5,
        harmony="Minimal harmony: reggae and dub-style minor chords (skanks), rave stabs and pads; much of "
                "the harmonic content comes from samples and the bassline.",
        voicing="close",
        comping="skank",
        bass_style="syncopated",
        bass="Deep, round sub bass (often 808-like or sine) from dub and reggae sound-system culture, moving "
             "at half the tempo in syncopated phrases with pitch drops and long sustained notes.",
        melody_density="sparse",
        melody_scale="minor pentatonic",
        melody="Ragga MC and dancehall vocal samples, rave stabs and short sampled hooks; melody is often "
               "secondary to rhythm and bass.",
        groove={"step": 0.25, "swing": 52, "pattern": {
            "kick":       "x.x. .... ..xx .... x.x. .... ..x. ....",
            "snare":      ".... x..o .o.. x..o .... x..o .o.. x.oo",
            "ride":       "x.x. x.x. x.x. x.x. x.x. x.x. x.x. x.x.",
            "crash":      "x... .... .... .... .... .... .... ....",
        }},
        drums="Amen, Think and other funk breaks chopped and resequenced on samplers (Akai S950/S1000), "
              "with ghost-note rolls, pitched snare edits and time-stretched fills; the break is the "
              "lead instrument.",
        form=(("intro", 16), ("drop", 32), ("break", 16), ("drop", 32), ("break", 16), ("drop", 32),
              ("outro", 16)),
        instruments=("sampler", "breakbeats", "sub bass", "vocal samples", "rave stabs", "pads"),
        sound_design="Gritty, sampled breaks (often pitched up), deep sine/808 sub, reggae and ragga vocal "
                     "samples, hoover and rave stabs, dub FX like delays and sirens.",
        production="Raw and dynamic, made on samplers and Atari trackers; bass deep and loud, breaks "
                   "crunchy; less polished than later DnB.",
        theory="Polyrhythmic layering: fast chopped breaks (16ths and 32nds) over half-time dub bass; "
               "reggae's offbeat skank and syncopated bass transferred to rave tempos.",
        mix=Mix(lufs=(-9, -6), lra=(4, 8), low_end="very heavy", tone="neutral", width="wide"),
    ),
    Genre(
        name="liquid drum and bass",
        family="electronic dance",
        aliases=("liquid", "liquid funk", "liquid dnb"),
        parent="drum and bass",
        description="Drum and bass at its most soulful: jazzy chords, warm pads, soul vocals and rolling "
                    "breaks at 170-176 BPM.",
        era="UK, late 1990s-2000s (Good Looking, Hospital, Soul:r)",
        touchstones=("LTJ Bukem", "High Contrast", "Calibre", "London Elektricity", "Netsky", "Logistics",
                     "Lenzman"),
        tempo=(170, 176),
        feel="rolling two-step breakbeat, light and fluid",
        swing=50,
        modes=("minor", "dorian"),
        keys=("F minor", "C minor", "Eb minor", "A minor"),
        progressions=(
            "i9-iv9",
            "iv9-VII13-IIImaj7-VImaj7",
            "dorian: i7-IV9",
            "major: IVmaj7-iii7-ii7-Imaj7",
            "i7-VImaj7-VII-III",
        ),
        harmonic_rhythm=0.5,
        harmony="Jazz and soul harmony: minor 9ths and 11ths, major 7ths, dominant 13ths and ii-V-I moves "
                "into the relative major (iv9-VII13-IIImaj7); voiced on Rhodes, pads and strings with smooth "
                "voice-leading, chords held two bars and often anticipated by an 8th.",
        voicing="rootless",
        comping="sustain",
        bass_style="syncopated",
        bass="Warm sine sub or a soft, rounded reese following the chord roots with melodic passing notes "
             "and glides, phrased at half-time; it ducks under the kick and leaves the snare's frequency "
             "range clear.",
        melody_density="medium",
        melody_scale="dorian",
        melody="Soulful sung toplines and chopped soul samples, Rhodes and piano riffs, string lines; "
               "lyrical, stepwise, phrased over 4-8 bars at half-time so they float over the fast drums.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x... .... ..x. .... ..x. .... ..x. ....",
            "snare":      ".... x..o .... x... .... x..o .o.. x...",
            "closed hat": "x.x. x.x. x.x. x.x. x.x. x.x. x.x. x.x.",
            "shaker":     "oxox oxox oxox oxox oxox oxox oxox oxox",
        }},
        drums="Two-step kick and snare softened with layered, filtered breaks (Think, Apache) full of ghost "
              "notes; rolling 16th shakers and hats, rides in the drop; the snare is crisp but rounder and "
              "more reverberant than in neurofunk.",
        form=(("intro", 32), ("verse", 16), ("drop", 32), ("break", 16), ("verse", 16), ("drop", 32),
              ("outro", 32)),
        instruments=("drum breaks", "sub bass", "Rhodes or piano", "pads", "strings", "vocals"),
        sound_design="Rhodes through chorus and tremolo, string ensembles, airy pads with long reverbs, soft "
                     "filtered breaks, rounded sine sub, soul vocal samples, vinyl texture.",
        production="Warm, smooth and wide; less clipped than neurofunk; vocals and keys upfront, sub mono, "
                   "breaks high-passed and tucked under the main snare; 32-bar DJ intros.",
        theory="Extended jazz chords and functional ii-V-I motion over a fast breakbeat: harmony moves at "
               "half-time (one chord per two bars at 174), so the chord rhythm feels like a 87 BPM soul tune "
               "while the drums run at full speed.",
        mix=Mix(lufs=(-9, -7), lra=(4, 7), low_end="heavy", tone="warm", width="wide"),
    ),
    Genre(
        name="neurofunk",
        family="electronic dance",
        aliases=("neuro",),
        parent="drum and bass",
        description="Dark, technical drum and bass: surgically precise drums and constantly morphing, "
                    "distorted reese and FM basses, more machine funk than melody.",
        era="London, 1997-98 (Ed Rush & Optical, Virus Recordings); refined in the Netherlands and beyond in the "
            "2010s",
        touchstones=("Ed Rush & Optical", "Noisia", "Phace", "Mefjus", "Black Sun Empire", "Teddy Killerz",
                     "Konflict"),
        tempo=(172, 176),
        feel="tight two-step at double time with funky, syncopated half-time bass edits",
        swing=50,
        modes=("phrygian", "minor"),
        keys=("F phrygian", "E phrygian", "G minor", "F minor"),
        progressions=(
            "i-II",
            "i-i-II-i",
            "i-vii",
            "minor: i-VI",
        ),
        harmonic_rhythm=0.25,
        harmony="Nearly no chords: a tonic drone, dark atmospheric pads, and semitone (b2) or tritone tension "
                "in the bass; the occasional minor or sus pad in intros and breakdowns for cinematic contrast.",
        voicing="cluster",
        comping="none",
        bass_style="reese",
        bass="The centrepiece: reese and FM basses resampled through distortion, comb filters, formant "
             "filters and phasers, edited into syncopated 1-2 bar 'call and response' phrases that switch "
             "patches every few 16ths; a clean sine sub underneath carries the pitch.",
        melody_density="sparse",
        melody_scale="phrygian",
        melody="Melody is replaced by bass phrasing: the bass edits are the hook, with occasional sci-fi "
               "leads or vocal stabs; intros carry eerie pads and sound-design motifs.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "X... .... ..x. .... ..x. .... ..x. ..x.",
            "snare":      ".... X... .... X..o .... X... .o.. X...",
            "closed hat": "x.xx x.x. x.xx x.x. x.xx x.x. x.xx x.xx",
            "ride":       "..x. ..x. ..x. ..x. ..x. ..x. ..x. ..x.",
        }},
        drums="Precise, programmed two-step: punchy kick on 1 and the 'and' of 3, a massive crisp snare on "
              "2 and 4, tight 16th hats with velocity detail, minimal ghosting; drums often cut out to leave "
              "a bass edit exposed, then slam back.",
        form=(("intro", 32), ("build", 16), ("drop", 32), ("break", 16), ("build", 8), ("drop", 32),
              ("outro", 32)),
        instruments=("drum samples", "reese bass", "FM bass", "sine sub", "pads", "FX"),
        sound_design="Resampled reeses and FM growls with serial distortion, OTT multiband compression, "
                     "comb and formant filters; metallic foley-like hits; dark ambient pads; rigid, clean drum "
                     "layers.",
        production="Extremely loud, clean and detailed: sub mono and separate from the distorted mid-bass "
                   "(split at about 100-150 Hz), snare and bass carved to share 200 Hz-2 kHz, very little "
                   "reverb in the drop.",
        theory="Funk syncopation in the bass phrasing set against a rigid two-step; harmony is a phrygian "
               "drone where the b2 and tritone provide all the tension. Interest is rhythmic and timbral: "
               "the same pitch re-voiced by different filters becomes a melody of timbres.",
        mix=Mix(lufs=(-6, -4), lra=(2, 5), low_end="very heavy", tone="bright", width="wide"),
    ),
    # ------------------------------------------------------------------ dubstep and UK bass
    Genre(
        name="dubstep",
        family="electronic dance",
        aliases=("bass music", "brostep"),
        parent="uk garage",
        description="Half-time bass music at around 140 BPM: sparse kick and snare-on-3 drums and enormous sub "
                    "and wobble basses; from the dark, dubby London original to the aggressive US brostep.",
        era="Croydon and South London, 2002-2008 (FWD>>, DMZ); the US festival brostep wave from 2010",
        touchstones=("Skream", "Benga", "Digital Mystikz", "Kode9", "Rusko", "Skrillex", "Excision"),
        tempo=(138, 150),
        feel="half-time: snare on beat 3, 16th-note detail at the full tempo",
        swing=50,
        modes=("minor", "phrygian"),
        keys=("F minor", "E minor", "F# minor", "G minor"),
        progressions=(
            "i-VI",
            "phrygian: i-II",
            "i-iv",
            "i-VII-VI-VII",
            "i-VI-III-VII",
        ),
        harmonic_rhythm=0.5,
        harmony="Minor and phrygian: often no chords at all, just a sub on the tonic and a b2 or b5 inflection; "
                "UK dubstep borrows dub's sparse minor organ and pad skanks, melodic dubstep uses aeolian "
                "four-chord loops in the build and breakdown.",
        voicing="open",
        comping="sustain",
        bass_style="syncopated",
        bass="UK: a pure sine sub with long notes and slides, plus a mid-range wobble (LFO-modulated low-pass "
             "or wavetable) in triplet or 8th rates. Brostep: distorted, resampled growls and screeches in "
             "rhythmic call-and-response edits, a separate clean sub beneath.",
        melody_density="sparse",
        melody_scale="phrygian",
        melody="Sparse: dub sirens, eerie pads, short vocal samples or MC; in festival dubstep the build has a "
               "pop-style melody or vocal and the drop's 'melody' is the bass phrasing.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x... .... .... .... x... .... ..x. ....",
            "snare":      ".... .... X... .... .... .... X... ....",
            "closed hat": "..x. ..x. ..xx ..x. ..x. ..x. ..xx .xx.",
            "rim":        "...x .... .... .x.. ...x .... .... ..x.",
        }},
        drums="Kick on 1, a big snare (often clap-layered) on beat 3 of each bar, with sparse syncopated kicks; "
              "UK style adds swung, rattling hats and percussion from garage, brostep uses fills of rapid "
              "snare and tom rolls; drop-outs of a beat before the drop.",
        form=(("intro", 16), ("build", 16), ("drop", 32), ("break", 16), ("build", 16), ("drop", 32),
              ("outro", 16)),
        instruments=("sub bass", "wobble or growl bass", "drum samples", "pads", "vocal sample", "FX"),
        sound_design="Sine sub; LFO-wobbled saw and square basses; resampled FM growls and talking basses "
                     "(formant filters); dub sirens, spring reverb and tape delay in the UK strand; huge "
                     "layered snares.",
        production="Sub carries the weight on sound systems (UK style mixes are dynamic and sub-heavy); "
                   "brostep is clipped hard with distorted mids and bright tops; sub mono below 100 Hz.",
        theory="Half-time feel at 140 (the snare on 3 makes it feel 70) with 16th and triplet detail on top; "
               "LFO rates synced to 8ths, triplets and 16ths make rhythm out of timbre; phrygian b2 tension.",
        mix=Mix(lufs=(-7, -5), lra=(3, 6), low_end="very heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="riddim",
        family="electronic dance",
        aliases=("riddim dubstep",),
        parent="dubstep",
        description="Minimal, repetitive dubstep: a single gritty, hollow bass sound in a looping triplet-"
                    "flavoured rhythm, with sparse half-time drums and lots of space.",
        era="UK (Coki's 'Spongebob' lineage, Chestplate) around 2010; North American festival scene from 2015",
        touchstones=("Coki", "Jakes", "Subtronics", "Svdden Death", "Bandlez", "Hydraulix"),
        tempo=(140, 150),
        feel="half-time with snare on 3, triplet-heavy bass rhythms",
        swing=50,
        modes=("minor", "phrygian"),
        keys=("F minor", "F# minor", "G minor"),
        progressions=(
            "i-i",
            "phrygian: i-II",
            "i-VI",
            "i-iv",
        ),
        harmonic_rhythm=0.5,
        harmony="Next to none: a tonic drone and the bass's own pitch movement (root, b2, b3, octave); the "
                "intro or build may carry a short minor melody or chord loop for contrast.",
        voicing="open",
        comping="none",
        bass_style="syncopated",
        bass="One hollow, square-ish, heavily distorted and filtered bass patch repeated in a 1-bar rhythmic "
             "cell (often 8th-note triplets or dotted patterns), with pitch staying on the tonic or moving a "
             "semitone; the gaps are as important as the hits.",
        melody_density="sparse",
        melody_scale="minor pentatonic",
        melody="Minimal: a vocal sample or MC tag, a lead line in the build; the drop's hook is purely the "
               "rhythm of the bass loop.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x... .... .... .... x..x .... .... ....",
            "snare":      ".... .... X... .... .... .... X... ....",
            "closed hat": "x.x. x.x. x.x. x.x. x.x. x.x. x.x. x.xx",
        }},
        drums="Sparse half-time: kick on 1 with one syncopated extra kick, a fat snare on 3, simple 8th hats; "
              "fills are snare rolls or a stutter edit; the drums leave space for the bass rhythm.",
        form=(("intro", 16), ("build", 16), ("drop", 32), ("break", 16), ("build", 8), ("drop", 32),
              ("outro", 8)),
        instruments=("growl bass", "sub bass", "drum samples", "vocal sample", "FX"),
        sound_design="Hollow, phasey square and wavetable basses with comb filtering, heavy distortion and OTT, "
                     "sine sub; crisp, compressed snares; dry, close sounds.",
        production="Very loud, clipped, mono-strong low end; contrast between silence and the bass hits; "
                   "little reverb in the drop.",
        theory="Repetition and rhythmic displacement: triplet and dotted cells phase against the half-time "
               "backbeat; pitch is nearly static, so groove and timbre carry the drop.",
        mix=Mix(lufs=(-6, -4), lra=(2, 5), low_end="very heavy", tone="bright", width="moderate"),
    ),
    Genre(
        name="uk garage",
        family="electronic dance",
        aliases=("ukg", "2-step"),
        parent="house",
        description="London's skippy, swung club music: shuffled 2-step drums or swung 4x4, chopped and "
                    "pitched R&B vocals, organ and Rhodes stabs and rubbery sub basslines.",
        era="London, 1995-2002 (speed garage, then 2-step)",
        touchstones=("MJ Cole", "Artful Dodger", "Todd Edwards", "El-B", "Zed Bias", "Wookie", "Sunship"),
        tempo=(128, 138),
        feel="heavily swung 16ths (2-step: kick skips beat 3), shuffling hats",
        swing=62,
        modes=("minor", "dorian"),
        keys=("F minor", "G minor", "A minor", "C minor"),
        progressions=(
            "i9-iv9",
            "dorian: i7-IV9",
            "iv9-VII13-IIImaj7-VImaj7",
            "i7-VImaj7-v7-v7",
            "major: ii9-V13-Imaj9-vi9",
        ),
        harmonic_rhythm=1,
        harmony="R&B and soulful-house harmony: minor 9ths, 11ths and major 7ths, ii-V movements, organ and "
                "Rhodes stabs placed on syncopated offbeats; the chords often anticipate the bar by a swung "
                "16th.",
        voicing="rootless",
        comping="stabs",
        bass_style="syncopated",
        bass="Rubbery sub or 'warp' bass in syncopated, swung patterns that bounce around the kick, with "
             "slides and octave jumps; speed garage uses a filtered, wobbling reese-like bass.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="Chopped, pitched and re-sequenced R&B vocals (Todd Edwards-style micro-cuts), soulful sung "
               "hooks, MC verses; melodic fragments are short and rhythmic, syncopated against the swing.",
        groove={"step": 0.25, "swing": 62, "pattern": {
            "kick":       "x... .... ..x. .... x... ...x ..x. ....",
            "snare":      ".... x... .... x... .... x... .... x...",
            "closed hat": "..x. .xx. ..x. .xx. ..x. .xx. ..x. .xxx",
            "shaker":     "xoxo xoxo xoxo xoxo xoxo xoxo xoxo xoxo",
            "rim":        "...x .... .x.. ..x. ...x .... .x.. x...",
        }},
        drums="2-step: kick on 1 and a syncopated kick around the 'and' of 3 (skipping beat 3), snare or clap "
              "on 2 and 4, shuffled 16th hats and shakers with heavy swing (60-65%), rimshots and tambourines "
              "in syncopation; 4x4 garage keeps a kick on every beat with the same swing.",
        form=(("intro", 16), ("verse", 16), ("chorus", 16), ("break", 8), ("verse", 16), ("chorus", 16),
              ("bridge", 8), ("chorus", 16), ("outro", 16)),
        instruments=("drum machine and samples", "sub bass", "organ or Rhodes", "vocal chops", "pads", "MC"),
        sound_design="Crisp, short drums with a tight snare, swung shakers, organ stabs (M1 organ), Rhodes, "
                     "pitched and time-stretched vocal chops, warm sub or warp bass.",
        production="Clean, punchy and bright on top, sub-heavy below; vocals upfront; swing quantisation "
                   "(MPC or Cubase groove) is crucial; pop-friendly verse-chorus structure on vocal cuts.",
        theory="Swing is the essence: 16ths swung at 60-65%, with the kick skipping beat 3 to create the "
               "lopsided 2-step lilt. Harmony is jazz-influenced (9ths, 11ths) and rhythmically displaced.",
        mix=Mix(lufs=(-9, -7), lra=(3, 6), low_end="heavy", tone="neutral", width="wide"),
    ),
    Genre(
        name="uk funky",
        family="electronic dance",
        parent="uk garage",
        description="London's late-2000s blend of soulful house, soca and Afro percussion: a syncopated, "
                    "drum-led groove at 130 BPM that often drops the four-on-the-floor kick, with chopped "
                    "vocals and deep sub.",
        era="London pirate radio and clubs, 2007-2011",
        touchstones=("Roska", "Crazy Cousinz", "Marcus Nasty", "Lil Silva", "Donae'o", "Apple", "Kyla"),
        tempo=(126, 132),
        feel="syncopated, percussion-led 4/4 built on soca and Afro rhythms (3-3-2), lightly swung",
        swing=55,
        modes=("minor", "dorian"),
        keys=("G minor", "F minor", "A minor", "C minor"),
        progressions=(
            "i7-iv7",
            "dorian: i7-IV7",
            "i9-VII-VI-VII",
            "VImaj7-VII-i7-i7",
        ),
        harmonic_rhythm=0.5,
        harmony="Soulful-house minor 7ths and 9ths as short, dry stabs or a single chord vamp; in the "
                "instrumental 'tribal' strand there are no chords at all, only percussion, sub and a vocal "
                "chop.",
        voicing="close",
        comping="stabs",
        bass_style="syncopated",
        bass="Deep sine or 808-style sub in short syncopated notes that interlock with the kick and toms, "
             "often a tresillo (3+3+2) shape across the bar, with octave jumps and long gaps.",
        melody_density="sparse",
        melody_scale="minor pentatonic",
        melody="Soulful R&B vocals in vocal cuts; instrumentals use a chopped vocal syllable or synth blip "
               "as a 1-bar hook; MC chants and call-and-response over the percussion.",
        groove={"step": 0.25, "swing": 55, "pattern": {
            "kick":       "x..x ..x. x... ..x.",
            "clap":       ".... x... .... x...",
            "rim":        "x..x ..x. ..x. x...",
            "conga":      "..xo .x.. xo.x .x..",
            "closed hat": "xoxx xoxx xoxx xoxx",
        }},
        drums="Kicks in syncopated soca and Afro-house patterns (3-3-2, kick on the 'a' of 1 and the 'and' "
              "of 2) rather than four-on-the-floor, claps on 2 and 4, interlocking rims, congas, bongos and "
              "toms; swung 16th hats; the percussion pattern is the hook and changes every 8 bars.",
        form=(("intro", 16), ("groove", 32), ("vocal", 16), ("break", 16), ("groove", 32), ("outro", 16)),
        instruments=("drum machine", "percussion samples", "sub bass", "vocal chops", "synth stabs", "MC"),
        sound_design="Dry, punchy, short percussion samples (congas, bongos, toms, rims, woodblocks), clean "
                     "sine sub, chopped and pitched vocal syllables, a few minor-7th stabs.",
        production="Percussion spread across the stereo field, dry and punchy, sub-heavy and mono below "
                   "100 Hz; little reverb; DJ-friendly 16-bar intros for pirate-radio mixing.",
        theory="Afro-Caribbean rhythmic cells (tresillo, 3-3-2, soca kick patterns) set at house tempo; "
               "polyrhythmic percussion layering over a steady clap backbeat, with the downbeat kick often "
               "displaced, creates forward lean.",
        mix=Mix(lufs=(-9, -7), lra=(3, 6), low_end="heavy", tone="neutral", width="wide"),
    ),
    Genre(
        name="bassline",
        family="electronic dance",
        aliases=("bassline house", "niche"),
        parent="uk garage",
        description="Northern England's heavy, bouncy offshoot of speed garage: a four-to-the-floor beat with "
                    "swung garage percussion, cheeky wobbling basslines as the hook, organ stabs and pitched "
                    "R&B vocals.",
        era="Sheffield (the Niche club), Leeds and the Midlands, 2002-2009",
        touchstones=("T2", "DJ Q", "H \"Two\" O", "Jamie Duggan", "TS7", "Delinquent"),
        tempo=(135, 142),
        feel="four-on-the-floor with swung garage hats and shuffled percussion",
        swing=56,
        modes=("minor",),
        keys=("F minor", "G minor", "A minor", "E minor"),
        progressions=(
            "i-VI-III-VII",
            "i-VI-VII-i",
            "i7-iv7",
            "i-iv-VI-VII",
            "VI-VII-i-i",
        ),
        harmonic_rhythm=1,
        harmony="Simple minor four-chord loops played as M1-organ or piano stabs, one chord per bar; the "
                "bassline usually states the harmony on its own while the stabs punctuate the offbeats.",
        voicing="close",
        comping="stabs",
        bass_style="syncopated",
        bass="The hook: a detuned, wobbling saw or square bass with LFO-modulated filter and pitch, playing a "
             "bouncy, melodic 1-2 bar riff in swung 16ths with octave jumps, slides and 'talking' filter "
             "movement; a sub layer underneath keeps it heavy.",
        melody_density="medium",
        melody_scale="minor",
        melody="Pitched-up, chipmunk-like R&B vocal hooks, organ riffs and the bass riff itself; short, "
               "catchy, repetitive phrases built for singalongs, plus MC bars.",
        groove={"step": 0.25, "swing": 56, "pattern": {
            "kick":       "x... x... x... x...",
            "snare":      ".... x... .... x...",
            "closed hat": "..x. .xx. ..x. .xx.",
            "open hat":   "..x. ..x. ..x. ..x.",
            "shaker":     "xoxo xoxo xoxo xoxo",
        }},
        drums="Kick on every beat, snare or clap on 2 and 4, shuffled garage hats and shakers swung around "
              "56%, skippy rimshots; fills are short snare rolls or a beat of silence before the bass returns.",
        form=(("intro", 16), ("verse", 16), ("drop", 32), ("break", 16), ("verse", 16), ("drop", 32),
              ("outro", 16)),
        instruments=("bass synth", "organ", "drum machine", "vocal chops", "MC", "piano"),
        sound_design="Wobbling, detuned saw and reese basses with LFO filters synced to 8ths and 16ths, "
                     "M1 organ stabs, pitched and formant-shifted vocals, crisp garage drum samples.",
        production="Loud and bass-dominant: the riff owns the low mids, the sub mono beneath; tight kick "
                   "sidechain; bright, simple top end; made fast and loud for car sound systems and clubs.",
        theory="The bass as melody: a swung, syncopated riff carries both harmony and hook over a straight "
               "four-to-the-floor kick, combining speed garage's 4x4 with 2-step's swing.",
        mix=Mix(lufs=(-7, -5), lra=(3, 5), low_end="very heavy", tone="bright", width="wide"),
    ),
    # ------------------------------------------------------------------ breaks
    Genre(
        name="breakbeat",
        family="electronic dance",
        aliases=("breaks", "nu skool breaks"),
        parent="electro",
        description="Dance music built on syncopated, broken drum patterns instead of a four-on-the-floor kick, "
                    "with heavy basslines and rave or electro synths at 125-140 BPM.",
        era="UK rave (1990-92) and Florida breaks; the nu skool breaks scene of 1997-2007",
        touchstones=("Adam Freeland", "Plump DJs", "Stanton Warriors", "Hybrid", "Rennie Pilgrem", "DJ Icey",
                     "The Prodigy"),
        tempo=(125, 140),
        feel="broken beat: syncopated kicks, snare on 2 and 4, slight swing",
        swing=52,
        modes=("minor", "phrygian"),
        keys=("E minor", "A minor", "F minor", "G minor"),
        progressions=(
            "i-VII",
            "i-VI-VII-i",
            "phrygian: i-II",
            "i-iv",
            "i-VI-III-VII",
        ),
        harmonic_rhythm=0.5,
        harmony="Minimal minor harmony: a riff or stab on one or two chords, rave piano or hoover stabs in "
                "the hardcore strand, techno and electro stabs in nu skool breaks; pads in breakdowns.",
        voicing="power",
        comping="stabs",
        bass_style="syncopated",
        bass="Big, often distorted basslines (acid 303, reese, or a Moog-ish growl) in syncopated 16ths that "
             "lock with the broken kick pattern; frequently the main hook, filtered and modulated over 8 bars.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="Riffs and stabs rather than tunes: 1-2 bar synth figures, chopped vocal samples and MC "
               "phrases, with hip-hop and electro phrasing.",
        groove={"step": 0.25, "swing": 52, "pattern": {
            "kick":       "x... ..x. ..x. .... x... .... ..x. .x..",
            "snare":      ".... x..o .... x... .... x..o .o.. x...",
            "closed hat": "x.x. x.x. x.x. x.x. x.x. x.x. x.x. x.x.",
            "open hat":   ".... .... .... ..x. .... .... .... ..x.",
        }},
        drums="Sampled breaks (Amen, Think, Funky Drummer, Apache) layered with programmed kicks and snares: "
              "kick on 1 and syncopated 8th/16th positions, snare on 2 and 4 with ghost notes, 8th hats, "
              "open hat on the 'and' of 4; fills from break edits and snare rolls.",
        form=(("intro", 16), ("build", 16), ("drop", 32), ("break", 16), ("build", 8), ("drop", 32),
              ("outro", 16)),
        instruments=("breakbeats", "bass synth", "lead synth", "sampler", "FX"),
        sound_design="Punchy, compressed breaks layered with tight kicks and snares, distorted acid or reese "
                     "basses, electro and rave stabs, vocal samples, filter sweeps.",
        production="Loud, punchy and bright: breaks parallel-compressed, the snare crisp and upfront, bass and "
                   "kick carved to share the low end; DJ-friendly phrasing in 16s.",
        theory="Funk-derived syncopation: the kick lands on off-beat 16ths (e.g. the 'a' of 2 and 'and' of 3) "
               "against a steady backbeat, so the groove lurches forward at house and techno tempos; "
               "harmony is modal (aeolian or phrygian) and static.",
        mix=Mix(lufs=(-8, -6), lra=(3, 6), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="big beat",
        family="electronic dance",
        aliases=("bigbeat",),
        parent="breakbeat",
        description="Late-1990s rock-flavoured dance music: fat, compressed funk and hip-hop breakbeats, "
                    "distorted acid lines, rock guitar and vocal samples, and huge build-and-drop moments.",
        era="UK (Brighton's Big Beat Boutique, London's Heavenly Social), 1995-2000",
        touchstones=("Fatboy Slim", "The Chemical Brothers", "The Prodigy", "The Crystal Method", "Propellerheads",
                     "Bentley Rhythm Ace"),
        tempo=(100, 140),
        feel="hip-hop and funk breakbeats at mid-tempo, punchy with a light swing",
        swing=54,
        modes=("minor", "mixolydian"),
        keys=("E minor", "A minor", "D mixolydian", "G minor"),
        progressions=(
            "i-VII",
            "i-iv",
            "mixolydian: I-VII-IV-I",
            "mixolydian: I7-IV7",
            "i-VI-VII-i",
        ),
        harmonic_rhythm=0.5,
        harmony="Riff-driven on one or two chords; blues and rock colour (mixolydian bVII, dominant 7ths, "
                "the I7-IV7 blues vamp); sampled funk, soul and rock records supply much of the harmony.",
        voicing="power",
        comping="stabs",
        bass_style="syncopated",
        bass="Distorted funk or acid bass riffs, sampled or played on a TB-303 or Moog: syncopated, bluesy "
             "(b3, 4, b5, 5, b7) and often doubled by a guitar riff.",
        melody_density="medium",
        melody_scale="blues",
        melody="Hooks are vocal samples and chants looped to exhaustion, rock guitar riffs and distorted "
               "synth figures; catchy, repetitive phrases with blues inflections.",
        groove={"step": 0.25, "swing": 54, "pattern": {
            "kick":       "x.x. ...x ..x. .... x.x. .... ..x. .x..",
            "snare":      ".... x..o .o.. x..o .... x..o .o.. x...",
            "closed hat": "xxxx xxxx xxxx xxox xxxx xxxx xxxx xxox",
            "open hat":   ".... .... .... ..x. .... .... .... ..x.",
        }},
        drums="Sampled funk and hip-hop breaks (Funky Drummer, Amen, Ashley's Roachclip) heavily compressed "
              "and distorted, kick and snare reinforced with layered one-shots; long builds with snare rolls, "
              "rising filters and pitch-ups, then the full break slams back in.",
        form=(("intro", 16), ("build", 16), ("drop", 32), ("break", 16), ("build", 16), ("drop", 32),
              ("outro", 16)),
        instruments=("sampler", "breakbeats", "TB-303", "guitar", "vocal samples", "synths"),
        sound_design="Crunchy, squashed breaks, overdriven acid lines, rock guitar samples, vocal chops, "
                     "phasers and big resonant filter sweeps, sirens and turntable scratches.",
        production="Loud and punchy, breaks pumped through hard compression and distortion; bright and "
                   "aggressive mids; long builds and dramatic drops borrowed from rave.",
        theory="Blues and rock harmony (mixolydian bVII, b3 against major) over hip-hop breaks at dance "
               "tempos; tension and release from builds (accelerating snares, rising filters) more than "
               "from chord changes.",
        mix=Mix(lufs=(-9, -6), lra=(3, 7), low_end="heavy", tone="bright", width="wide"),
    ),
    # ------------------------------------------------------------------ hard dance and hardcore
    Genre(
        name="hardstyle",
        family="electronic dance",
        aliases=("hard style",),
        parent="hard trance",
        description="Hard dance from the Netherlands at around 150 BPM: a distorted, pitched kick with a "
                    "'reverse bass' tail, euphoric trance-style melodies and epic breakdowns.",
        era="Netherlands and Italy, early 2000s; euphoric and rawstyle branches from about 2010",
        touchstones=("Headhunterz", "Brennan Heart", "Noisecontrollers", "Wildstylez", "Coone",
                     "D-Block & S-te-Fan", "The Prophet"),
        tempo=(150, 160),
        feel="four-on-the-floor, every kick a distorted pitched hit, offbeat reverse bass",
        swing=50,
        modes=("minor", "harmonic minor"),
        keys=("F minor", "G minor", "A minor", "D minor"),
        progressions=(
            "i-VI-III-VII",
            "VI-VII-i-i",
            "i-iv-VI-V",
            "i-VI-VII-v",
            "iv-VI-VII-i",
        ),
        harmonic_rhythm=1,
        harmony="Euphoric minor progressions borrowed from trance, one chord per bar, VI-VII-i cadences and a "
                "harmonic-minor V for the climax; huge supersaw stacks with octaves and 5ths; the kick is "
                "retuned to follow each chord root.",
        voicing="spread",
        comping="pulse_16",
        bass_style="offbeat",
        bass="The kick is the bass: a distorted, pitched kick with a long tonal tail; in 'reverse bass' "
             "hardstyle a sidechained bass note swells on each offbeat between kicks, tuned to the chord "
             "roots; rawstyle uses screeching distorted kick tails as the riff.",
        melody_density="busy",
        melody_scale="harmonic minor",
        melody="Anthemic supersaw leads with big leaps (octaves, 5ths), triplet runs and a memorable "
               "4-bar motif repeated over the progression; emotional vocal hooks and spoken intros in the "
               "breakdown.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "X... X... X... X...",
            "clap":       ".... x... .... x...",
            "open hat":   "..x. ..x. ..x. ..x.",
            "closed hat": "x.x. x.x. x.x. x.x.",
        }},
        drums="Hard, distorted kick on every beat (punch, crunch and tail designed separately), clap on 2 and "
              "4, offbeat hats; kick rolls into drops; breakdowns remove the kick entirely for 32 bars, then "
              "the 'anti-climax' or climax drop slams back.",
        form=(("intro", 16), ("build", 16), ("breakdown", 32), ("drop", 32), ("break", 16), ("drop", 32),
              ("outro", 16)),
        instruments=("distorted kick", "supersaw synth", "pads", "vocal", "screech synth", "FX"),
        sound_design="Layered kicks: a punchy transient, a distorted body and a pitched, overdriven tail tuned "
                     "to the key; thick supersaws, screeches, impacts, risers and orchestral pads.",
        production="Extremely loud, kick-dominated masters; leads wide and bright, everything ducks around the "
                   "kick; the breakdown is quiet and cinematic for maximum contrast with the drop.",
        theory="Trance harmony and melody over a kick that plays the bass part: re-pitching the kick tail per "
               "chord turns the drum into a bassline; the offbeat reverse bass creates the bouncing "
               "kick-bass-kick-bass pulse.",
        mix=Mix(lufs=(-6, -4), lra=(2, 5), low_end="very heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="happy hardcore",
        family="electronic dance",
        aliases=("happycore",),
        parent="breakbeat hardcore",
        description="Joyful, fast UK rave music at 165-180 BPM: bright major-key piano stabs, pitched-up "
                    "diva vocals, bouncing offbeat bass and a hammering four-on-the-floor kick.",
        era="UK and the Netherlands, 1994-1999; revived by the UK hardcore scene in the 2000s",
        touchstones=("Hixxy", "Scott Brown", "DJ Dougal", "Force & Styles", "Brisk", "Slipmatt"),
        tempo=(165, 180),
        feel="four-on-the-floor at high speed with offbeat hats and bass",
        swing=50,
        modes=("major", "minor"),
        keys=("C major", "F major", "D major", "A minor"),
        progressions=(
            "I-V-vi-IV",
            "vi-IV-I-V",
            "IV-V-iii-vi",
            "I-IV-V-V",
            "minor: i-VI-III-VII",
        ),
        harmonic_rhythm=1,
        harmony="Bright major-key pop progressions, one chord per bar; rave piano stabs in root position "
                "triads; key changes up a tone; minor-key 'freeform' and UK hardcore cuts use aeolian loops.",
        voicing="close",
        comping="offbeat",
        bass_style="offbeat",
        bass="A punchy offbeat bass (or reese) on every 'and' following chord roots, bouncing against the "
             "kick; occasionally rolling 16ths.",
        melody_density="busy",
        melody_scale="major pentatonic",
        melody="Pitched-up (chipmunk) female vocals with simple, singable pop melodies, cheerful synth and "
               "piano riffs in 8ths and 16ths; hooks repeat in 4-bar phrases.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x... x... x... x...",
            "clap":       ".... x... .... x...",
            "open hat":   "..x. ..x. ..x. ..x.",
            "closed hat": "xxxx xxxx xxxx xxxx",
        }},
        drums="Fast, punchy kick on every beat, claps or snares on 2 and 4, offbeat open hats, 16th closed "
              "hats; early tracks layer chopped breakbeats; snare rolls up to 32nds into each drop.",
        form=(("intro", 16), ("verse", 16), ("chorus", 16), ("breakdown", 16), ("build", 8), ("drop", 32),
              ("chorus", 16), ("outro", 16)),
        instruments=("piano stabs", "supersaw or rave synth", "drum machine", "vocals", "bass synth", "FX"),
        sound_design="Rave piano (M1 piano), hoover and rave stabs, bright supersaws, pitched vocals, punchy "
                     "kick, crisp claps.",
        production="Bright, loud and energetic; vocals pitched up and upfront; heavy sidechain in the modern "
                   "UK hardcore form.",
        theory="Pop harmony at rave tempo: diatonic major progressions and the I-V-vi-IV loop, with the "
               "offbeat bass and hats doubling the perceived pulse; melodies are major-pentatonic and simple.",
        mix=Mix(lufs=(-7, -5), lra=(3, 5), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="gabber",
        family="electronic dance",
        aliases=("gabba", "rotterdam hardcore"),
        parent="techno",
        description="Rotterdam's extreme hardcore techno: a distorted, overdriven 909 kick at 160-200 BPM that "
                    "is the whole bassline, with hoover synths, horror samples and shouted vocals.",
        era="Rotterdam, 1992-1997; mainstream hardcore since",
        touchstones=("Paul Elstak", "Rotterdam Terror Corps", "Neophyte", "Euromasters", "Angerfist",
                     "Darkraver"),
        tempo=(160, 200),
        feel="four-on-the-floor, relentless, every beat a distorted kick",
        swing=50,
        modes=("minor", "phrygian"),
        keys=("A minor", "F minor", "E phrygian"),
        progressions=(
            "i-VI",
            "phrygian: i-II",
            "i-VII-VI-VII",
            "i-iv",
        ),
        harmonic_rhythm=0.5,
        harmony="Minimal: a minor drone or a hoover riff on one or two chords; happy gabber borrows bright "
                "rave stabs and pop melodies, darker styles use phrygian semitone tension.",
        voicing="power",
        comping="stabs",
        bass_style="none",
        bass="No separate bass: the kick is overdriven until it becomes a pitched, sustained tone that carries "
             "the low end and the root of the key.",
        melody_density="sparse",
        melody_scale="phrygian",
        melody="Hoover synths and Mentasm-style riffs, rave stabs, shouted MC vocals and pitched film samples; "
               "melodies are short, simple and aggressive.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "X... X... X... X...",
            "clap":       ".... x... .... x...",
            "open hat":   "..x. ..x. ..x. ..x.",
            "crash":      "x... .... .... ....",
        }},
        drums="Distorted 909 kick on every beat, sometimes with extra 16th kicks for fills; claps or snares on "
              "2 and 4; offbeat hats; kick rolls and snare rolls into drops; crashes on phrase starts.",
        form=(("intro", 16), ("build", 16), ("drop", 32), ("break", 16), ("build", 8), ("drop", 32),
              ("outro", 16)),
        instruments=("TR-909 kick", "distortion", "hoover synth", "sampler", "vocal shouts"),
        sound_design="909 kick through multiple distortion stages until it 'screams' as a pitched tone, "
                     "hoover and Mentasm patches, horror samples, harsh shouted vocals.",
        production="Extremely loud and saturated, kick-dominated; little dynamic range; the distorted kick "
                   "occupies the whole low and mid range.",
        theory="Extremity of tempo and distortion: the kick's overdriven harmonics turn rhythm into pitch, "
               "and tonal content is a drone; tension is built by speed and density more than harmony.",
        mix=Mix(lufs=(-6, -4), lra=(2, 4), low_end="very heavy", tone="bright", width="moderate"),
    ),
    # ------------------------------------------------------------------ club music
    Genre(
        name="footwork",
        family="electronic dance",
        aliases=("juke",),
        parent="ghetto house",
        description="Chicago's hyper-syncopated dance-battle music at 160 BPM: stuttering 808 kicks and toms, "
                    "skittering triplet hats and obsessively chopped vocal and soul loops, felt at half-time.",
        era="Chicago's South and West Sides, late 1990s-2010s (juke, then footwork)",
        touchstones=("DJ Rashad", "DJ Spinn", "RP Boo", "Traxman", "Jlin", "DJ Clent"),
        tempo=(155, 165),
        feel="160 BPM with a half-time feel, polyrhythmic 3-against-4 kick and triplet hat patterns",
        swing=50,
        modes=("minor", "dorian"),
        keys=("C minor", "F minor", "A minor"),
        progressions=(
            "i7-iv7",
            "dorian: i7-IV7",
            "VImaj7-VII-i7-i7",
            "i-VI",
        ),
        harmonic_rhythm=0.5,
        harmony="Harmony comes from sampled loops (soul, R&B, jazz, film) chopped into 1-2 bar fragments; "
                "often one or two extended minor chords repeated, sometimes pitch-shifted in steps.",
        voicing="open",
        comping="stabs",
        bass_style="808",
        bass="Long-decay 808 kicks and 808 bass hits placed in syncopated, dotted and triplet positions, "
             "pitched to the loop's root and sometimes moving in semitones.",
        melody_density="sparse",
        melody_scale="minor pentatonic",
        melody="A single vocal syllable or phrase looped and stuttered in triplets and dotted rhythms, "
               "sampled melodies chopped into rhythmic cells; the melody is rhythmic repetition.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x..x ..x. ..x. .x.. x..x ..x. .x.. x.x.",
            "clap":       ".... x... .... x... .... x... .... x.x.",
            "closed hat": "x.xx x.x. x.xx x.xx x.xx x.x. x.xx xxxx",
            "low tom":    "..x. .... .x.. .... ..x. .... ...x ....",
        }},
        drums="TR-808 kicks in syncopated 3+3+2 and dotted-8th patterns, claps or snares on 2 and 4 (felt as "
              "half-time at 80), rapid 16th and triplet hats, 808 toms and rimshots in stuttering rolls; "
              "patterns change every 4 bars to challenge dancers.",
        form=(("intro", 8), ("loop", 16), ("variation", 16), ("break", 8), ("loop", 16), ("variation", 16),
              ("outro", 8)),
        instruments=("TR-808", "sampler", "vocal samples", "soul or jazz samples", "FX"),
        sound_design="Raw 808 kicks with long decay, sharp claps, crisp hats, toms; vocal and soul samples "
                     "chopped on FL Studio, minimal processing.",
        production="Raw, dry and loud in the low end; sparse arrangements, loops repeated with small edits; "
                   "short tracks (2-4 minutes) for battle sets.",
        theory="Polyrhythm: 3-against-4 kick patterns and triplet hats over a 4/4 grid, with half-time "
               "backbeat feel at double tempo; loops create harmonic stasis while rhythm constantly shifts.",
        mix=Mix(lufs=(-9, -6), lra=(4, 7), low_end="very heavy", tone="neutral", width="moderate"),
    ),
    Genre(
        name="jersey club",
        family="electronic dance",
        parent="baltimore club",
        description="Newark's bouncy, high-energy club music at around 140 BPM: the signature quarter-quarter-"
                    "triplet kick bounce, bed-squeak samples and chopped, stuttered vocal hooks built for "
                    "dance crews.",
        era="Newark, New Jersey, early 2000s; crossed into rap, pop and drill from the late 2010s",
        touchstones=("DJ Tameil", "DJ Sliink", "UNIIQU3", "Cookiee Kawaii", "DJ Jayhood", "Nadus"),
        tempo=(130, 145),
        feel="steady four-beat pulse with a triplet-feel kick bounce on beats 3 and 4",
        swing=50,
        modes=("minor", "major"),
        keys=("F minor", "A minor", "C major", "G major"),
        progressions=(
            "i-VI-III-VII",
            "major: vi-IV-I-V",
            "i7-iv7",
            "VI-VII-i-i",
            "major: IV-V-vi-vi",
        ),
        harmonic_rhythm=1,
        harmony="Harmony comes from the flipped sample: an R&B, pop or rap hook (or a short synth or piano "
                "loop) of one to four chords, chopped into 1-2 bar fragments; edits often re-trigger the "
                "chord on the kick pattern so it bounces with the beat.",
        voicing="close",
        comping="stabs",
        bass_style="808",
        bass="Mostly the kick itself, tuned and punchy; when there is bass, a short 808 hit on the sample's "
             "root that doubles the kick bounce, sometimes sliding up an octave on the last triplet.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="A vocal phrase from a familiar song chopped into syllables and re-triggered in triplets and "
               "16th stutters, often pitched up; short catchy fragments traded in call-and-response with "
               "DJ drops and chants.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x... x... x..x ..x. x... x... x..x ..x.",
            "clap":       ".... x... .... x... .... x... .... x...",
            "closed hat": "x.x. x.x. x.x. x.x. x.x. x.x. x.x. x.x.",
            "snare":      ".... .... .... .... .... .... .... .xxx",
        }},
        drums="The signature kick: two quarter notes then a triplet-feel bounce of three hits (beats 1, 2, 3, "
              "the 'a' of 3 and the 'and' of 4), claps on 2 and 4, bed-squeak, gunshot and 'hey' samples as "
              "percussion, quick 16th snare and clap rolls at phrase ends, sparse hats.",
        form=(("intro", 8), ("loop", 16), ("vocal", 16), ("break", 8), ("loop", 16), ("outro", 8)),
        instruments=("drum samples", "sampler", "vocal chops", "bed-squeak sample", "808", "DJ drops"),
        sound_design="Punchy, short kicks, the bed-squeak sample, gunshots and crowd chants, chopped and "
                     "pitched vocals; minimal synths; everything dry and upfront.",
        production="Loud, punchy and dry; kick dominant and mono; short 2-3 minute edits made in FL Studio "
                   "for DJ sets and dance videos; abrupt drops and breaks instead of long builds.",
        theory="The quarter-quarter-triplet kick (approximated on the 16th grid as 1, 2, 3, 3a, 4+) lays a "
               "3-against-2 bounce over the 4/4 pulse; vocal chops follow the same cell so melody and drums "
               "share one rhythm.",
        mix=Mix(lufs=(-8, -6), lra=(3, 6), low_end="heavy", tone="bright", width="moderate"),
    ),
    Genre(
        name="baltimore club",
        family="electronic dance",
        aliases=("bmore club", "b-more club", "baltimore breaks"),
        parent="house",
        description="Baltimore's raw club music at about 130 BPM: the 'Think' break chopped over a syncopated "
                    "kick pattern, with vocal snippets looped into chants; house tempo, hip-hop attitude.",
        era="Baltimore, late 1980s-1990s; spread through Philly and Jersey in the 2000s",
        touchstones=("DJ Rod Lee", "Scottie B", "Blaqstarr", "DJ Technics", "KW Griff", "Frank Ski"),
        tempo=(125, 135),
        feel="chopped breakbeat over a kick that lands on 1, 2, 3, the 'and' of 3 and 4",
        swing=52,
        modes=("minor", "major"),
        keys=("A minor", "F minor", "C major"),
        progressions=(
            "i-VII",
            "i7-iv7",
            "major: I-IV",
            "i-VI-VII-i",
        ),
        harmonic_rhythm=0.5,
        harmony="Minimal: a one- or two-chord vamp from a sampled loop, a stab or an organ hit; the track is "
                "about the break and the vocal chant, so harmony rarely changes.",
        voicing="close",
        comping="stabs",
        bass_style="808",
        bass="Mostly the kick and 808 booms on the root; sometimes a short sampled bass loop or a sub hit "
             "doubling the syncopated kick on the 'and' of 3.",
        melody_density="sparse",
        melody_scale="minor pentatonic",
        melody="One vocal snippet (from R&B, hip-hop, TV or a local MC) looped and stuttered as a chant, "
               "repeated for the whole track with edits every 4-8 bars; simple synth or horn stabs.",
        groove={"step": 0.25, "swing": 52, "pattern": {
            "kick":       "x... x... x.x. x... x... x... x.x. x.x.",
            "snare":      ".... x..o .... x.o. .... x..o ..o. x.oo",
            "clap":       ".... x... .... x... .... x... .... x...",
            "closed hat": "x.x. x.x. x.x. x.x. x.x. x.x. x.x. x.x.",
        }},
        drums="Chopped breaks, above all Lyn Collins' 'Think (About It)' and 'Sing Sing', layered over a "
              "drum-machine kick on 1, 2, 3, the 'and' of 3 and 4 (with an extra 'and' of 4 in the second "
              "bar); claps on 2 and 4, ghost snares from the break, quick snare rolls into each new section.",
        form=(("intro", 8), ("loop", 16), ("vocal", 16), ("break", 8), ("loop", 16), ("outro", 8)),
        instruments=("sampler", "breakbeats", "drum machine (808/909)", "vocal samples", "stab synth"),
        sound_design="Gritty, sampled breaks pitched to tempo, punchy 808/909 kicks, looped vocal snippets "
                     "with no effects, horn and orchestra stabs.",
        production="Raw, loud and dry, made on samplers and early DAWs; mono-ish, break and kick upfront; "
                   "short DJ-friendly tracks built for blending and call-outs.",
        theory="Funk breakbeat syncopation at house tempo: the kick's push on the 'and' of 3 against the "
               "steady clap backbeat gives the bounce; the looped vocal turns a phrase into a rhythmic "
               "ostinato.",
        mix=Mix(lufs=(-9, -7), lra=(4, 7), low_end="heavy", tone="neutral", width="moderate"),
    ),
]
