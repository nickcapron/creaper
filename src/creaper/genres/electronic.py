"""Electronic listening music, retro synth styles, and ambient and experimental genres."""

from . import Genre, Mix

GENRES = [
    # ------------------------------------------------------------------ retro synth
    Genre(
        name="synthwave",
        family="electronic",
        aliases=("retrowave", "80s", "outrun"),
        parent="synth-pop",
        description="A nostalgic re-imagining of 1980s film, TV and video-game soundtracks: driving octave basslines, "
                    "gated-reverb snares, lush analog pads and soaring saw or sax leads under neon-lit night-drive "
                    "melancholy.",
        era="France and the US, mid-2000s; broke out after the Drive soundtrack (2011)",
        touchstones=("Kavinsky", "College", "The Midnight", "FM-84", "Mitch Murder", "Lazerhawk", "Timecop1983"),
        tempo=(80, 118),
        feel="straight and driving; a steady eighth-note bass motor under a backbeat, sometimes half-time choruses",
        swing=50,
        modes=("minor", "dorian", "major"),
        keys=("A minor", "F# minor", "E minor", "C minor", "D minor"),
        progressions=(
            "i-VI-III-VII",
            "VI-VII-i-i",
            "i-VII-VI-VII",
            "i-VI-iv-V",
            "iv-VI-VII-i",
            "major: I-V-vi-IV",
        ),
        harmonic_rhythm=1,
        harmony="Plain triads and add9s in natural minor, one chord per bar; the i-VI-III-VII and VI-VII-i loops are "
                "the backbone. Lift the last chorus a whole step, or borrow the major V from harmonic minor for a "
                "cinematic pull back to i. Pads double the chords an octave up with sus2 and add9 colour.",
        voicing="open",
        comping="sustain",
        bass_style="eighths",
        bass="Relentless straight eighth notes on the root (often alternating octaves) from a Juno, SH-101 or "
             "Moog-style saw bass, filtered and slightly plucky; it changes with the chord on the downbeat and "
             "rarely syncopates. Sidechained a touch to the kick.",
        melody_density="medium",
        melody_scale="natural minor",
        melody="Big, singable lead lines in the upper-middle register on a detuned saw or square lead, often "
               "doubled by a sax or a glassy DX7 bell; stepwise hooks that land on chord tones, long held notes "
               "with slow vibrato, and a 16th-note arpeggio running underneath. Choruses repeat a four-bar hook.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.......x.x.....|x.......x.......",
            "snare":      "....X.......X...|....X.......X...",
            "closed hat": "x.x.x.x.x.x.x.x.|x.x.x.x.x.x.x.x.",
            "open hat":   "..............x.|..............x.",
            "high tom":   "................|............x...",
            "mid tom":    "................|.............x..",
            "low tom":    "................|..............x.",
        }},
        drums="LinnDrum, DMX or TR-707 samples: kick on 1 and 3, a huge gated-reverb snare on 2 and 4, steady 8th "
              "hats; Simmons-style tom fills into choruses; crash on every section start. Kept rigid and "
              "unswung; half-time snare on 3 for slow ballads.",
        form=(("intro", 8), ("verse", 16), ("pre-chorus", 8), ("chorus", 16), ("verse", 16), ("chorus", 16),
              ("solo", 16), ("chorus", 16), ("outro", 8)),
        instruments=("analog polysynth pad (Juno/Jupiter)", "saw bass", "drum machine (LinnDrum/707)",
                     "saw or square lead", "DX7 bells and electric piano", "arpeggiator", "saxophone",
                     "gated-reverb snare"),
        sound_design="Detuned saws with chorus (Juno chorus I/II), FM bells and electric piano, square-wave "
                     "arpeggios, gated reverb on the snare, tape saturation and a little wow for VHS warmth; "
                     "big plate and hall reverbs on leads.",
        production="Bright and wide: pads and arps spread hard, bass and kick mono, snare reverb gated around "
                   "300-500 ms; moderate bus compression and saturation rather than brickwall loudness; a "
                   "subtle tape/VHS character on the master.",
        theory="Aeolian loops with the bVI-bVII-i ascent give the 'heroic sadness' sound; the steady 8th-note bass "
               "turns even slow tempos into motion. Melodies outline triads and suspensions (9-8, 4-3) over "
               "static pads, and modulation up a whole step for the final chorus is a cliché used without shame.",
        mix=Mix(lufs=(-11, -8), lra=(4, 7), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="darksynth",
        family="electronic",
        aliases=("dark synthwave",),
        parent="synthwave",
        description="Synthwave's horror-movie side: distorted saw basses, pounding drums and menacing minor and "
                    "phrygian riffs borrowed from John Carpenter scores and metal, built for aggression rather "
                    "than nostalgia.",
        era="France and Europe, early 2010s",
        touchstones=("Perturbator", "Carpenter Brut", "Dan Terminus", "GosT", "Dance with the Dead", "John Carpenter"),
        tempo=(95, 140),
        feel="straight and heavy; metal-style kick patterns, occasional double-time sections",
        swing=50,
        modes=("minor", "phrygian", "harmonic minor"),
        keys=("E minor", "D minor", "C minor", "F minor"),
        progressions=(
            "i-VI-VII-i",
            "i-bII-i-VII",
            "i-iv-VI-V",
            "i-VI-III-VII",
            "i-i-bV-iv",
            "phrygian: i-II-vii-i",
        ),
        harmonic_rhythm=0.5,
        harmony="Power chords and bare minor triads, often a single chord held for two bars under a riff; the "
                "phrygian bII and the tritone bV supply the menace; harmonic-minor V for horror-film suspense. "
                "Pads are layered octaves and fifths rather than extended chords.",
        voicing="power",
        comping="pulse_16",
        bass_style="sixteenths",
        bass="A distorted, sidechained 16th-note saw or reese bass ostinato on the root, with octave and minor-2nd "
             "pickups, often doubled an octave down by a clean sub; it is the riff, not just the foundation.",
        melody_density="medium",
        melody_scale="phrygian",
        melody="Short, chromatic riffs and horror-score motifs (semitone neighbours, tritone leaps) on screaming "
               "detuned leads; arpeggiated minor triads; climaxes with metal-style lead-guitar phrasing on synth.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.....x.x.x.....|x.....x.x.x...xx",
            "snare":      "....X.......X...|....X.......X...",
            "closed hat": "x.x.x.x.x.x.x.x.|x.x.x.x.x.x.x.x.",
            "crash":      "x...............|................",
        }},
        drums="Heavily processed acoustic-style samples or 80s drum machines driven hard: punchy, clipped kicks, "
              "huge compressed snares on 2 and 4, rock-style kick syncopation and double-kick fills; "
              "breakdowns drop to toms and impacts.",
        form=(("intro", 16), ("riff A", 16), ("build", 8), ("main", 16), ("break", 8), ("riff B", 16),
              ("main", 16), ("climax", 16), ("outro", 8)),
        instruments=("distorted saw bass", "drum machine and rock drum samples", "detuned lead synth",
                     "brass and choir pads", "arpeggiator", "impacts and risers"),
        sound_design="Saws through distortion, bitcrushing and amp sims; reese basses; dark brass stabs and "
                     "Carpenter-style sequenced pulses; metallic risers and cinematic hits; filtered noise sweeps.",
        production="Loud and dense: parallel distortion on drums and bass, aggressive sidechain pumping, heavy "
                   "limiting; low mids carved so the bass and kick punch through; wide leads, mono low end.",
        theory="Built on pedal-point riffs where the bII-i semitone (phrygian) and the tritone substitute for "
               "functional harmony; harmonic-minor V and diminished passing chords give a horror-film suspense. "
               "Rhythmic interest comes from metal-style kick syncopation against a rigid 16th-note bass.",
        mix=Mix(lufs=(-9, -6), lra=(3, 6), low_end="heavy", tone="neutral", width="wide"),
    ),
    Genre(
        name="chillwave",
        family="electronic",
        aliases=("glo-fi",),
        parent="synth-pop",
        description="Hazy, sun-faded bedroom pop: washed-out vocals, warbling tape synths and sidechained pads over "
                    "simple drum-machine grooves, like a half-remembered summer on a worn cassette.",
        era="US bedroom producers and music blogs, 2009-2011",
        touchstones=("Washed Out", "Toro y Moi", "Neon Indian", "Small Black", "Memory Tapes", "Tycho"),
        tempo=(75, 110),
        feel="straight, relaxed, gently pumping from heavy sidechain",
        swing=50,
        modes=("major", "lydian", "mixolydian"),
        keys=("C major", "D major", "F major", "A major"),
        progressions=(
            "Imaj7-IVmaj7",
            "I-V-vi-IV",
            "vi-IV-I-V",
            "IVmaj7-iii7-ii7-Imaj7",
            "I-iii-vi-IV",
            "mixolydian: I-bVII-IV-I",
        ),
        harmonic_rhythm=1,
        harmony="Diatonic major-key loops coloured with maj7, add9 and sus2; the I-IV maj7 sway and borrowed "
                "bVII give the sunny-but-melancholy tint. Chords are held for a bar and smeared by reverb, so "
                "voice leading matters less than overall wash.",
        voicing="spread",
        comping="sustain",
        bass_style="root",
        bass="Soft, round synth or DI bass on roots with simple passing notes, ducked hard by the kick; sometimes "
             "a funky disco-ish line in the Toro y Moi vein, but always low in the mix.",
        melody_density="sparse",
        melody_scale="major pentatonic",
        melody="Dreamy, mid-range vocals buried under reverb and delay, doubled or harmonised in thirds; short "
               "pentatonic hooks repeated with little variation; synth leads with pitch wobble.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.......x.x.....",
            "snare":      "....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.",
            "tambourine": "..x...x...x...x.",
        }},
        drums="Cheap drum machines or 80s samples: soft kick, snappy snare or clap on 2 and 4, straight 8th hats, "
              "tambourine on offbeats; everything lo-passed and compressed so the sidechain pump is the groove.",
        form=(("intro", 8), ("verse", 16), ("chorus", 16), ("verse", 16), ("chorus", 16), ("bridge", 8),
              ("chorus", 16), ("outro", 16)),
        instruments=("analog polysynth pad", "drum machine", "soft synth bass", "reverb-drenched vocals",
                     "chorused electric guitar", "sampled 70s-80s soft-rock loops"),
        sound_design="Juno-style pads with slow attack, tape wow and flutter, chorus, bitcrushed samples, "
                     "low-pass filtering, cassette saturation; vocals through long plate reverb and slapback delay.",
        production="Everything sidechained to the kick for a breathing pump; muffled top end, warm low mids, "
                   "wide reverbs; deliberately lo-fi mastering with gentle limiting.",
        theory="Harmonically simple diatonic major with maj7 and bVII colour; the character is timbral rather "
               "than harmonic. Rhythmically the 'pump' of sidechain compression acts as an implied offbeat accent "
               "on every 8th, turning static chords into a pulse.",
        mix=Mix(lufs=(-12, -9), lra=(4, 7), low_end="moderate", tone="warm", width="wide"),
    ),
    Genre(
        name="vaporwave",
        family="electronic",
        aliases=("vapourwave",),
        parent="chillwave",
        description="An internet-born collage of slowed, looped and pitched-down 80s and 90s muzak, smooth jazz, "
                    "city pop and corporate jingles, drenched in reverb: ironic, eerie and nostalgic for a "
                    "consumer future that never came.",
        era="Online (Tumblr, Bandcamp), 2010-2012",
        touchstones=("Macintosh Plus", "Chuck Person (Oneohtrix Point Never)", "James Ferraro", "Saint Pepsi",
                     "Blank Banshee", "2814"),
        tempo=(60, 100),
        feel="slowed-down groove; loops that drift and stutter, sometimes no drums at all",
        swing=50,
        modes=("major", "dorian", "lydian"),
        keys=("Db major", "Eb major", "Ab major", "Gb major"),
        progressions=(
            "IVmaj7-V7-iii7-vi7",
            "Imaj7-vi7-ii7-V7",
            "ii9-V13-Imaj9-Imaj9",
            "Imaj7-IVmaj7",
            "IVmaj7-III7-vi7-vi7",
            "dorian: i9-IV9",
        ),
        harmonic_rhythm=1,
        harmony="Inherited from its samples: smooth-jazz and city-pop extended chords (maj7, m9, 13ths), the "
                "Japanese 'royal road' IVmaj7-V7-iii7-vi7, ii-V-I turnarounds and secondary dominants; pitched "
                "down, which lands it in flat keys.",
        voicing="rootless",
        comping="sustain",
        bass_style="syncopated",
        bass="Whatever is in the sample: slap or fretless electric bass and synth bass from the 80s, slowed and "
             "muddied; added basses are sparse root notes that follow the loop.",
        melody_density="sparse",
        melody_scale="major pentatonic",
        melody="Fragments rather than tunes: a sax lick, a vocal phrase or an elevator-music line chopped to a "
               "one- or two-bar loop, slowed 20-40% and repeated hypnotically with occasional stutters.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.......x.......",
            "snare":      "....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.",
        }},
        drums="Often just the drums inside the sample, slowed; or stiff 80s drum-machine and trap-ish hats (Blank "
              "Banshee); many tracks drop drums entirely and let the loop float.",
        form=(("loop A", 16), ("loop A varied", 16), ("loop B", 16), ("loop A", 16), ("fade", 8)),
        instruments=("sampled smooth jazz and muzak", "city pop records", "electric piano", "saxophone",
                     "slowed vocals", "General MIDI and Windows-era synths"),
        sound_design="Pitch-shifting and time-stretching (slowed and pitched down), heavy plate and hall reverb, "
                     "chorus, VHS and cassette degradation, low-pass filtering, abrupt loop cuts and skips.",
        production="Deliberately cheap: muffled highs, no surgical EQ, wide reverb, gentle limiting; collage "
                   "edits with audible loop points as an aesthetic choice.",
        theory="Harmony is the borrowed jazz-pop language of its samples (IVmaj7-V7-iii7-vi7, ii-V-I with 9ths "
               "and 13ths), but the formal idea is repetition: a loop stripped of its resolution and repeated "
               "until it becomes uncanny. Slowing shifts both pitch and tempo, so keys drift off A=440.",
        mix=Mix(lufs=(-14, -9), lra=(4, 8), low_end="moderate", tone="warm", width="moderate"),
    ),

    # ------------------------------------------------------------- beats and downbeat
    Genre(
        name="lo-fi",
        family="electronic",
        aliases=("lofi", "lofi hip hop", "chillhop"),
        parent="boom bap",
        description="Dusty, mellow instrumental hip-hop for studying and relaxing: jazzy chords on Rhodes or "
                    "piano, swung lazy drums, vinyl crackle and tape warmth, deliberately soft and unhurried.",
        era="YouTube and SoundCloud, mid-2010s, built on J Dilla and Nujabes",
        touchstones=("Nujabes", "J Dilla", "Jinsang", "potsu", "Idealism", "Tomppabeats", "Kupla"),
        tempo=(70, 90),
        feel="swung, behind-the-beat 16ths; drums drunk and quantized loosely",
        swing=60,
        modes=("dorian", "minor", "major"),
        keys=("D dorian", "A minor", "F major", "Eb major", "C minor"),
        progressions=(
            "i9-IV9",
            "major: ii9-V13-Imaj9-Imaj9",
            "major: IVmaj7-III7-vi7-vi7",
            "major: Imaj9-vi9-ii9-V13",
            "minor: iiø7-V7b9-i9-i9",
            "minor: i9-iv9",
        ),
        harmonic_rhythm=1,
        harmony="Jazz vocabulary at slow speed: minor 9ths, major 9ths, 13th dominants, ii-V-I turnarounds and the "
                "'Just the Two of Us' IVmaj7-III7-vi7 descent; dorian two-chord vamps. Chords are often a "
                "sampled or replayed four-bar loop that never changes.",
        voicing="rootless",
        comping="sustain",
        bass_style="syncopated",
        bass="Warm upright, muted electric or sine bass playing roots and fifths with laid-back syncopation, "
             "landing slightly late; walks between chords with chromatic approach notes.",
        melody_density="sparse",
        melody_scale="minor pentatonic",
        melody="Little topline: a short guitar, flute, Rhodes or vocal-chop motif in the middle register, "
               "pentatonic with blue notes, phrased loosely around the beat and repeated.",
        groove={"step": 0.25, "swing": 60, "pattern": {
            "kick":       "x......x..x.....|x.........x..x..",
            "snare":      "....x.......x...|....x.......x..o",
            "closed hat": "x.xox.x.x.xox.x.|x.xox.x.x.xox.xo",
            "rim":        "................|.......o........",
        }},
        drums="Boom bap skeleton at low tempo: soft kick on 1 and the 'and' of 2, snare or rimshot on 2 and 4, "
              "swung hats with ghost 16ths; unquantized or with 55-62% swing, the snare dragged late; "
              "filtered and saturated sampled breaks.",
        form=(("intro", 4), ("loop A", 16), ("loop B", 8), ("loop A", 16), ("outro", 4)),
        instruments=("Rhodes or felt piano", "sampled drum break", "upright or electric bass", "jazz guitar",
                     "vinyl crackle", "vocal chops", "flute or sax sample"),
        sound_design="Sampled or replayed Rhodes and piano through tape saturation, wow and flutter, bitcrushing "
                     "(SP-404 style), low-pass at 8-12 kHz; vinyl noise layer; soft, rounded transients.",
        production="Dark and soft: rolled-off highs, warm low mids, gentle bus glue, side-chain barely there; "
                   "loops 1:30-3:00 long with short intros; mastered quietly to keep it relaxed.",
        theory="Jazz harmony (ii-V-I, m9 and 13 chords, tritone and chromatic approach basses) fixed into short "
               "loops that never resolve; the feel comes from micro-timing: swung 16ths and a late snare (Dilla "
               "feel) instead of grid-perfect drums.",
        mix=Mix(lufs=(-14, -10), lra=(4, 8), low_end="moderate", tone="dark", width="moderate"),
    ),
    Genre(
        name="trip-hop",
        family="electronic",
        aliases=("bristol sound",),
        parent="hip-hop",
        description="Slow, smoky Bristol music: hip-hop breakbeats slowed to a crawl, heavy dub bass, cinematic "
                    "strings and spy-film samples beneath sultry or haunted vocals.",
        era="Bristol, UK, early to mid 1990s",
        touchstones=("Massive Attack", "Portishead", "Tricky", "Morcheeba", "Sneaker Pimps", "Lovage"),
        tempo=(70, 100),
        feel="heavy, slow breakbeat with a slight swing; half-time weight",
        swing=54,
        modes=("minor", "dorian", "harmonic minor"),
        keys=("A minor", "G minor", "E minor", "C minor"),
        progressions=(
            "i-imaj7-i7-i6",
            "i-i-VI-V",
            "i-iv-i-V7",
            "i7-iv7",
            "i-VII-VI-VII",
        ),
        harmonic_rhythm=0.5,
        harmony="Dark minor loops from soul, jazz and film-score samples: the descending line cliché i-imaj7-i7-i6, "
                "harmonic-minor V for a noir pull, minor 7 vamps, and lots of held single chords with tension in "
                "the strings above.",
        voicing="open",
        comping="sustain",
        bass_style="syncopated",
        bass="Deep, dub-inspired bass: sustained subs and slow syncopated roots, lots of space, often a "
             "single repeated figure for the whole track; sometimes an upright-bass sample.",
        melody_density="sparse",
        melody_scale="harmonic minor",
        melody="Breathy, intimate or eerie vocals in a narrow range with long held notes and bluesy bends; "
               "theremin-like synth or vibraphone lines; spy-film guitar licks with tremolo and spring reverb.",
        groove={"step": 0.25, "swing": 54, "pattern": {
            "kick":       "x......x..x.....|x.x.......x.....",
            "snare":      "....X.......X...|....X.......X..o",
            "closed hat": "x.x.x.x.x.x.x.x.|x.x.x.x.x.x.x.x.",
            "open hat":   "................|..............x.",
        }},
        drums="Sampled funk or jazz breaks slowed down and filtered, often from vinyl, with a big, roomy snare on "
              "2 and 4 and a heavy kick; scratching and turntable noise; loops repeat with almost no fills.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("bridge", 8),
              ("chorus", 8), ("outro", 16)),
        instruments=("sampled breakbeat", "sub bass", "string section samples", "Rhodes or piano",
                     "turntable scratches", "theremin or synth lead", "tremolo guitar", "vocal"),
        sound_design="Vinyl-sampled everything: crackle, MPC/S950 grit, tape saturation, spring and plate reverb, "
                     "dub delays; strings and horns from old film scores pitched down.",
        production="Heavy low end and dark highs; wide cinematic strings and reverb, but drums and voice up front "
                   "and dry-ish; dub-style mixing moves (send throws, filter sweeps).",
        theory="Minor-key loops with chromatic inner voice lines (line cliché) and harmonic-minor dominants give "
               "a noir, film-score colour; rhythmically it is hip-hop at 70-90 BPM where the space between kick "
               "and snare is as important as the hits.",
        mix=Mix(lufs=(-12, -9), lra=(5, 9), low_end="heavy", tone="dark", width="wide"),
    ),
    Genre(
        name="downtempo",
        family="electronic",
        aliases=("downbeat",),
        parent="trip-hop",
        description="Groove-led, laid-back electronic music: dubby breaks, jazzy and worldly samples and warm "
                    "basslines at a relaxed pace, made for lounges and late nights rather than dancefloors.",
        era="Vienna, Washington DC and London, mid-1990s onward",
        touchstones=("Kruder & Dorfmeister", "Thievery Corporation", "Bonobo", "Nightmares on Wax", "DJ Shadow"),
        tempo=(80, 110),
        feel="relaxed broken beat with light swing; dub and bossa influences",
        swing=56,
        modes=("dorian", "minor", "major"),
        keys=("D dorian", "A minor", "G dorian", "E minor"),
        progressions=(
            "i7-IV9",
            "i7-ii7-IIImaj7-ii7",
            "i9-VIImaj7",
            "minor: i9-VImaj7-iv9-v7",
            "major: Imaj9-IVmaj9",
        ),
        harmonic_rhythm=0.5,
        harmony="Modal vamps with jazz extensions: dorian i7-IV9, stepwise i7-ii7-bIIImaj7 planing, minor 9 and "
                "11 chords on Rhodes, guitar or strings; two-chord loops held for two bars each.",
        voicing="rootless",
        comping="stabs",
        bass_style="syncopated",
        bass="Warm, melodic electric or synth bass with dub syncopation: notes on the 'and', octave pops and "
             "slides, leaving beat one sometimes empty; locked with the kick rather than the chords.",
        melody_density="sparse",
        melody_scale="dorian",
        melody="Sampled vocal fragments, flute, sitar, harp or guitar phrases; short motifs answered by delays; "
               "occasional guest vocal with simple, repeated lines.",
        groove={"step": 0.25, "swing": 56, "pattern": {
            "kick":       "x.........x.x...|x......x..x.....",
            "snare":      "....x.......x...|....x.......x...",
            "closed hat": "x.xxx.x.x.xxx.x.|x.xxx.x.x.xxx.x.",
            "conga":      "..x..x....x..x..|..x..x....x..x.x",
            "shaker":     "xoxoxoxoxoxoxoxo|xoxoxoxoxoxoxoxo",
        }},
        drums="Mid-tempo breaks, slightly swung, with a fat kick and crisp snare; hand percussion (congas, "
              "bongos, shakers) layered for groove; dub delays on snares and rims as fills.",
        form=(("intro", 16), ("groove A", 16), ("groove B", 16), ("break", 8), ("groove A", 16),
              ("groove B", 16), ("outro", 16)),
        instruments=("sampled breaks", "electric bass", "Rhodes", "strings or harp", "hand percussion",
                     "world instrument samples (sitar, flute)", "dub delay"),
        sound_design="Vinyl-sourced samples, tape delay and spring reverb, filtered Rhodes, warm analog bass, "
                     "subtle bitcrushing, dub echo throws; organic textures over pristine synthesis.",
        production="Warm and spacious: bass and kick strong but rounded, mids rich, top end smooth; dub mixing "
                   "moves (filter sweeps, delay throws); album-oriented dynamics.",
        theory="Modal (mostly dorian) vamps rather than cadences, with jazz extensions; groove comes from "
               "light swing, syncopated bass anticipations and layered percussion polyrhythm over a steady "
               "half-speed backbeat.",
        mix=Mix(lufs=(-12, -9), lra=(5, 8), low_end="heavy", tone="warm", width="wide"),
    ),
    Genre(
        name="chillout",
        family="electronic",
        aliases=("chill out",),
        parent="ambient",
        description="Balearic sunset music: lush pads, Spanish guitar, soft beats and gentle grooves designed for "
                    "after-club comedowns, beach bars and long listening.",
        era="Ibiza and the UK, early 1990s; peaked with Café del Mar compilations around 2000",
        touchstones=("José Padilla", "Zero 7", "Air", "The KLF", "Moby", "Lemongrass"),
        tempo=(85, 120),
        feel="gentle, straight or lightly swung; soft four-on-the-floor or a relaxed broken beat",
        swing=52,
        modes=("major", "lydian", "dorian"),
        keys=("D major", "A major", "E major", "F major"),
        progressions=(
            "Imaj7-IVmaj7",
            "Imaj9-vi9-IVmaj9-V9sus4",
            "vi7-IVmaj7-Imaj7-V7sus4",
            "lydian: Imaj7-II",
            "dorian: i7-IV7",
        ),
        harmonic_rhythm=0.5,
        harmony="Warm, consonant extended chords (maj7, maj9, add9, sus4) moving slowly; the lydian I-II shimmer "
                "and dorian i-IV sway; dominants are usually softened to sus4 so nothing feels like a cadence.",
        voicing="spread",
        comping="sustain",
        bass_style="whole",
        bass="Soft, sustained sub or fretless-style bass on roots, sometimes a gentle syncopated figure; rarely "
             "busy, never aggressive.",
        melody_density="sparse",
        melody_scale="major pentatonic",
        melody="Nylon-string guitar or piano melodies, breathy female vocals, flute or soprano sax; long, "
               "lyrical lines with lots of space, pentatonic and stepwise.",
        groove={"step": 0.25, "swing": 52, "pattern": {
            "kick":       "x.......x.......",
            "rim":        "....x.......x...",
            "shaker":     "xoxoxoxoxoxoxoxo",
            "conga":      "......x...x..x..",
        }},
        drums="Light: a soft kick, rimshot or brushed snare, shakers and congas; sometimes a slowed house groove; "
              "many tracks start beatless and add drums halfway.",
        form=(("intro", 16), ("theme", 16), ("groove", 32), ("breakdown", 16), ("theme", 16), ("groove", 16),
              ("outro", 16)),
        instruments=("analog and digital pads", "nylon-string guitar", "piano or Rhodes", "soft drum machine",
                     "hand percussion", "sub bass", "field recordings (waves, birds)"),
        sound_design="Slow-attack string and choir pads, glassy bells, warm Rhodes, field recordings of sea and "
                     "wind; long reverbs and gentle stereo delays.",
        production="Smooth and spacious, no harsh transients; light compression to preserve dynamics, warm "
                   "tonal balance, wide stereo field; long crossfadeable intros and outros.",
        theory="Avoids dominant function: maj7 and sus chords, lydian #4 colour and plagal motion keep the music "
               "suspended. The harmonic rhythm is slow (one chord every two bars) so the ear settles into the "
               "texture rather than following a progression.",
        mix=Mix(lufs=(-14, -10), lra=(5, 9), low_end="moderate", tone="warm", width="wide"),
    ),

    # ----------------------------------------------------------- experimental electronic
    Genre(
        name="idm",
        family="electronic",
        aliases=("intelligent dance music", "braindance"),
        parent="techno",
        description="Home-listening electronic music that treats dance music's tools as a composer's palette: "
                    "intricate programmed rhythms, detuned nostalgic melodies and restless sound design.",
        era="UK, early 1990s (Warp's Artificial Intelligence series)",
        touchstones=("Aphex Twin", "Autechre", "Boards of Canada", "Squarepusher", "µ-Ziq", "Plaid"),
        tempo=(80, 170),
        feel="programmed and asymmetric; broken beats, ratchets, shifting accents and occasional odd meters",
        swing=50,
        modes=("minor", "lydian", "major", "dorian"),
        keys=("D minor", "F lydian", "A minor", "C major"),
        progressions=(
            "i9-VImaj7",
            "major: IVmaj7-iv-Imaj7-Imaj7",
            "lydian: Imaj7-II",
            "major: I-bIII-I-bVI",
            "i-VI-III-VII",
            "dorian: i9-IV9-bIIImaj7-IV9",
        ),
        harmonic_rhythm=0.5,
        harmony="Nostalgic, slightly off chords: detuned maj7s and minor 9ths, the minor-plagal iv in a major key, "
                "lydian shimmer, chromatic-mediant shifts (I-bIII-bVI) and parallel planing. Often just two "
                "chords, made strange by microtonal detuning.",
        voicing="open",
        comping="broken",
        bass_style="syncopated",
        bass="From warm, wobbly analog roots (Boards of Canada) to frantic, slapped-sounding 16th lines "
             "(Squarepusher); syncopated against the drums, with pitch bends and glides.",
        melody_density="medium",
        melody_scale="lydian",
        melody="Music-box and toy-like melodies, often in a high register on detuned or bit-reduced synths; "
               "short motifs that mutate by note and rhythm each repeat; counter-melodies in canon.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x..x......x..x..|..x...x...x....x",
            "snare":      "....x..o.o..x...|....x...o...x.xx",
            "closed hat": "x.xxx.x.xx.x.xxx|x.x.xxx.x.xxx.x.",
            "rim":        "..o....o....o...|.o....o......o..",
        }},
        drums="Hand-programmed: displaced kicks, snare rolls and ratchets (32nd and 64th note bursts), glitchy "
              "edits, swing that changes bar to bar; drill-and-bass Amen chops at 160+ or slow, crunchy "
              "hip-hop beats (BoC).",
        form=(("intro", 8), ("theme", 16), ("development", 16), ("break", 8), ("theme varied", 16),
              ("climax", 16), ("coda", 8)),
        instruments=("drum machines (TR-606/909)", "analog monosynths", "FM synths", "sampler",
                     "detuned pads", "tape machine", "modular synth"),
        sound_design="Detuned and pitch-wobbled synths, FM metallic tones, granular and bit-crushed textures, "
                     "resampled drum hits, generative patches (Max/MSP, modular); tape warble for nostalgia.",
        production="Detailed and wide: precise stereo placement of every percussive element, automation-heavy, "
                   "dynamics preserved more than in club music; each sound EQ'd as an instrument.",
        theory="Rhythm is the main field of invention: metric displacement, polymeter, tuplets and asymmetric "
               "groupings (3+3+2, 5/8 bars) over a 4/4 frame. Harmony is modal and coloristic (lydian, "
               "chromatic mediants, minor plagal) with microtonal detuning as an expressive device.",
        mix=Mix(lufs=(-12, -8), lra=(5, 10), low_end="moderate", tone="neutral", width="wide"),
    ),
    Genre(
        name="glitch",
        family="electronic",
        aliases=("glitch music", "clicks and cuts"),
        parent="idm",
        description="Music made from digital errors: skipping CDs, clicks, dropouts and sine tones arranged into "
                    "precise, minimal rhythms and fragile textures.",
        era="Germany and Japan, mid-1990s to early 2000s (Mille Plateaux, Raster-Noton)",
        touchstones=("Oval", "Alva Noto", "Ryoji Ikeda", "Fennesz", "Pole", "Ryuichi Sakamoto"),
        tempo=(80, 130),
        feel="microscopic and precise; grid-tight clicks or freely floating fragments",
        swing=50,
        modes=("minor", "major"),
        keys=("A minor", "C major", "E minor"),
        progressions=(
            "i9-i9-VImaj7-VImaj7",
            "major: Imaj7-IVmaj7",
            "i-VII",
            "Isus2-VImaj7",
        ),
        harmonic_rhythm=0.25,
        harmony="Minimal and static: sustained drones or two-chord loops of soft maj7/m9 pads (often granulated "
                "piano or guitar, Fennesz style); much of the music is unpitched, so harmony is a slow bed under "
                "the clicks.",
        voicing="spread",
        comping="sustain",
        bass_style="pedal",
        bass="Sine-wave sub pulses and pedal tones, or dub-like filtered bass (Pole); very clean and pure, often "
             "a single held frequency.",
        melody_density="sparse",
        melody_scale="minor pentatonic",
        melody="Rarely a melody: fragments of piano or guitar granulated into shimmering clouds, or pure sine "
               "tones in simple intervals; repetition with micro-variation.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.......x.......|x.......x.....x.",
            "rim":        "...x.......x....|..x.x......x....",
            "closed hat": "x.x.x.xxx.x.x.x.|x.x.x.x.xxx.x.x.",
            "sticks":     ".o.....o..o.....|.o....o...o..o..",
        }},
        drums="No acoustic kit: clicks, crackles, digital pops, sine-burst kicks and filtered noise hiss make the "
              "rhythm; programmed with sample-accurate precision, sometimes stuttered by buffer repeats.",
        form=(("introduction", 16), ("pattern A", 32), ("dropout", 8), ("pattern B", 32), ("decay", 16)),
        instruments=("laptop (Max/MSP, Reaktor)", "sine and noise generators", "damaged CD samples",
                     "granular processor", "piano or guitar source", "sub bass"),
        sound_design="Clicks, digital clipping, buffer stutters, bit reduction, very short noise bursts, pure "
                     "sine tones, granular time-stretching; extremes of the frequency range (sub and 15 kHz+).",
        production="Clean, quiet and detailed: lots of silence, high dynamic range, hard-panned micro-sounds; "
                   "masters left far from loudness-war levels.",
        theory="An aesthetic of failure: timbre and microrhythm replace harmony as the structure. Rhythms are "
               "built from sample-level events, often in phase-shifting or additive patterns; pitch material is "
               "reduced to drones and simple intervals.",
        mix=Mix(lufs=(-16, -10), lra=(5, 12), low_end="light", tone="bright", width="wide"),
    ),
    Genre(
        name="electronica",
        family="electronic",
        parent="idm",
        description="Melodic, song-minded electronic music for listening: dance-music rhythms and synths fused with "
                    "pop structure, live instruments, folk samples and emotional build-ups.",
        era="UK, Scandinavia and the US, late 1990s and 2000s",
        touchstones=("Röyksopp", "Four Tet", "Caribou", "Jon Hopkins", "Moby", "Ulrich Schnauss"),
        tempo=(90, 130),
        feel="straight or lightly swung; breakbeat or four-on-the-floor depending on the track",
        swing=52,
        modes=("major", "minor", "dorian"),
        keys=("C major", "G major", "A minor", "E minor"),
        progressions=(
            "I-V-vi-IV",
            "vi-IV-I-V",
            "Imaj7-iii7-vi7-IVmaj7",
            "minor: i-VI-III-VII",
            "dorian: i7-IV",
        ),
        harmonic_rhythm=1,
        harmony="Pop-diatonic progressions with maj7 and add9 colour, minor-key loops for melancholy, "
                "dorian vamps; long builds over a single repeating four-chord loop.",
        voicing="open",
        comping="arpeggio_updown",
        bass_style="syncopated",
        bass="Warm analog or electric bass with gentle syncopation; in the Jon Hopkins mould, a distorted "
             "sustained sub that swells with the build.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Arpeggiated synth motifs, chopped vocal or folk-instrument samples (harp, guitar, kalimba), "
               "occasional sung hooks; motifs layered and built up over 16-32 bars.",
        groove={"step": 0.25, "swing": 52, "pattern": {
            "kick":       "x.....x...x.....|x.....x...x..x..",
            "snare":      "....x.......x...|....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.|x.x.x.x.x.x.x.x.",
            "shaker":     ".x.x.x.x.x.x.x.x|.x.x.x.x.x.x.x.x",
        }},
        drums="Mix of programmed and sampled: crunchy breakbeats, chopped acoustic kits, or a house kick that "
              "arrives at the build; percussion layers added one at a time.",
        form=(("intro", 16), ("theme", 16), ("build", 16), ("peak", 32), ("break", 16), ("peak", 16),
              ("outro", 16)),
        instruments=("analog synths", "drum machine and sampled breaks", "piano", "acoustic or folk samples",
                     "vocal chops", "electric bass"),
        sound_design="Warm analog arps, sampled acoustic instruments processed with granular and tape effects, "
                     "sidechained pads, detuned leads; an organic-meets-synthetic palette.",
        production="Polished but dynamic: builds with filter and density, wide stereo pads, clean low end; "
                   "album-friendly loudness.",
        theory="Form is accumulation: a repeating diatonic loop gains layers until a peak, so arrangement does "
               "what harmonic change would do in pop. Arpeggio-based melodies outline the chords, and "
               "cross-rhythms (3-against-4 arps) add motion.",
        mix=Mix(lufs=(-11, -8), lra=(4, 8), low_end="moderate", tone="neutral", width="wide"),
    ),
    Genre(
        name="breakcore",
        family="electronic",
        parent="drum and bass",
        description="Chaotic, hyper-fast chopped breakbeats: Amen breaks sliced at 32nd notes over distorted bass, "
                    "classical or anime samples and sudden genre swerves, from violent to tearfully emotional.",
        era="Europe and the US, late 1990s; revived online in the 2020s",
        touchstones=("Venetian Snares", "Igorrr", "Shitmat", "DJ Scud", "Machine Girl", "Sewerslvt"),
        tempo=(160, 260),
        feel="breakneck chopped breaks; constant edits, rolls and tempo-feel switches",
        swing=50,
        modes=("minor", "harmonic minor"),
        keys=("C minor", "F minor", "A minor", "D minor"),
        progressions=(
            "i-VI-III-VII",
            "i-iv-V7-i",
            "i-VI-VII-i",
            "i-bII-i-V",
            "VI-VII-i-i",
        ),
        harmonic_rhythm=0.5,
        harmony="Lifted from its samples: Romantic string and piano progressions in harmonic minor (i-iv-V7), "
                "emotional aeolian pad loops (Sewerslvt-style i-VI-III-VII), or pure noise with no harmony at all.",
        voicing="close",
        comping="sustain",
        bass_style="reese",
        bass="Distorted reese and 808 basses, gabber-style kicks and sub drops; often half-time against the "
             "drums, sliding and bending into distortion.",
        melody_density="medium",
        melody_scale="harmonic minor",
        melody="Sampled orchestral or piano phrases, vocal snippets, video-game or anime melodies; supersaw or "
               "piano leads in long, sad lines floating over the chaos.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.x.......xx....|x.x...x...x..x..",
            "snare":      "....x..x.x..x.xx|.x..x..x.xx.xxxx",
            "closed hat": "x.xxx.xxx.xxx.xx|xxxxxxxxxxxxxxxx",
            "crash":      "x...............|................",
        }},
        drums="Amen, Think and other breaks sliced and resequenced at 32nd and 64th note resolution: snare "
              "rolls, stutters, pitch-shifted hits, reversed fills; gabber kick sections and sudden halftime "
              "drops; often in 7/4 or odd groupings (Venetian Snares).",
        form=(("intro", 8), ("break assault", 32), ("melodic break", 16), ("assault", 32), ("halftime", 16),
              ("assault", 32), ("outro", 8)),
        instruments=("chopped breakbeats (Amen, Think)", "distorted 808 and reese bass", "gabber kick",
                     "orchestral samples", "piano", "vocal samples", "noise"),
        sound_design="Hard-clipped breaks, bitcrushed and pitched slices, distorted kicks, ring modulation, noise "
                     "bursts; contrasted with clean, reverb-drenched pianos or strings.",
        production="Extremely loud and saturated, deliberately clipping; heavy low end, bright harsh top; "
                   "abrupt cuts to silence or soft passages for contrast.",
        theory="Rhythmic density as expression: breaks re-chopped into irregular groupings, metric modulation "
               "and polymeter (7/4 or 5/4 cycles against 4/4 samples). Harmony, when present, is Romantic "
               "harmonic minor or aeolian loops, giving the emotional counterweight.",
        mix=Mix(lufs=(-8, -5), lra=(3, 7), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="future garage",
        family="electronic",
        parent="uk garage",
        description="Melancholic, night-bus UK garage: skippy 2-step drums, pitched ghostly vocal chops, vinyl "
                    "crackle and rain-soaked minor-key pads over deep sub bass.",
        era="London, late 2000s (after Burial's Untrue, 2007)",
        touchstones=("Burial", "Sorrow", "Submerse", "Phaeleh", "Synkro", "Vacant"),
        tempo=(128, 140),
        feel="shuffled 2-step, swung 16ths with skipped kicks; half-time sub weight",
        swing=60,
        modes=("minor", "dorian"),
        keys=("F minor", "C minor", "G minor", "D minor"),
        progressions=(
            "i9-VImaj7-III-VII",
            "i9-iv9",
            "i7-VImaj7-iv7-v7",
            "VImaj7-VII-i9-i9",
            "dorian: i9-IV9",
        ),
        harmonic_rhythm=0.5,
        harmony="Minor 9 and maj7 pads moving slowly in natural minor, often the same four chords for the whole "
                "track; pads pitched or reversed so chords blur into each other.",
        voicing="spread",
        comping="sustain",
        bass_style="syncopated",
        bass="Deep, clean sine or slightly saturated sub following the 2-step kick syncopation, with long "
             "slides; occasional soft reese mid-bass layer.",
        melody_density="sparse",
        melody_scale="minor pentatonic",
        melody="Pitched and time-stretched R&B vocal chops, gender-shifted, cut into short syllabic phrases "
               "that rhythmically answer the drums; few full melodies.",
        groove={"step": 0.25, "swing": 60, "pattern": {
            "kick":       "x.........x.....|x..........x....",
            "snare":      "....x.......x...|....x.......x..o",
            "closed hat": "..x.x..x..x.x..x|..x.x..x..x.x.x.",
            "rim":        "......o.......o.|...o..o.......o.",
            "shaker":     "xoxoxoxoxoxoxoxo|xoxoxoxoxoxoxoxo",
        }},
        drums="Swung, unquantized-feeling 2-step: kicks on 1 and syncopated 16ths (skipping beat 3), crunchy "
              "snares or rim clicks on 2 and 4, shuffling hats and shakers; sampled from foley (lighters, "
              "keys) and vinyl, not drum machines.",
        form=(("intro", 16), ("A", 32), ("break", 16), ("B", 32), ("break", 8), ("A", 16), ("outro", 16)),
        instruments=("sampled drums and foley", "sub bass", "pitched vocal chops", "pads", "vinyl crackle",
                     "field recordings (rain, traffic)"),
        sound_design="Vinyl crackle and rain field recordings as constant beds, pitched/reversed vocals, "
                     "granular pads, low-passed and lo-fi drum hits; long dark reverbs.",
        production="Dark, foggy top end, heavy clean sub, mid-range left to atmospheres; drums dry-ish and close; "
                   "loudness moderate, with space for the sub.",
        theory="The 2-step shuffle (swung 16ths, kicks avoiding beat 3) against slow half-time harmony gives a "
               "simultaneous 'moving and still' feel; vocal chops function as rhythmic motifs more than melody.",
        mix=Mix(lufs=(-11, -8), lra=(5, 8), low_end="heavy", tone="dark", width="wide"),
    ),

    # ------------------------------------------------------- ambient and experimental
    Genre(
        name="ambient",
        family="ambient and experimental",
        aliases=("ambient music",),
        description="Atmospheric music that prizes texture, space and mood over rhythm and melody, as 'ignorable "
                    "as it is interesting': slowly evolving pads, tape loops and soft tones.",
        era="UK, mid-1970s (Brian Eno); ambient house in the early 1990s",
        touchstones=("Brian Eno", "Harold Budd", "Hiroshi Yoshimura", "Biosphere", "Stars of the Lid",
                     "Aphex Twin (Selected Ambient Works)", "The Orb"),
        tempo=(50, 100),
        feel="beatless or a faint pulse; time measured in breaths, not bars",
        swing=50,
        modes=("major", "lydian", "dorian", "minor"),
        keys=("D major", "F major", "Eb major", "A minor"),
        progressions=(
            "Imaj7-IVmaj7",
            "Iadd9-vi7-IVmaj7-IVmaj7",
            "Imaj9-iii7",
            "lydian: Imaj7-II",
            "dorian: i9-IV",
        ),
        harmonic_rhythm=0.25,
        harmony="Consonant, slow-moving chords with added 9ths, maj7s and sus colour over a tonic pedal; changes "
                "every four bars or more, often by a single voice moving. Overlapping tape loops of different "
                "lengths create harmony by chance.",
        voicing="spread",
        comping="sustain",
        bass_style="pedal",
        bass="Sustained low drones on the tonic or fifth, or no bass at all; occasional soft sub swells.",
        melody_density="sparse",
        melody_scale="major pentatonic",
        melody="Isolated piano notes or synth tones with long decays, pentatonic and widely spaced in time; "
               "phrases that repeat in loops of unequal length so they never line up the same way twice.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x...............|................",
            "shaker":     "..x.......x.....|..x.......x.....",
            "triangle":   "................|........x.......",
        }},
        drums="Usually none. If drums are wanted: a soft, low kick every bar or two, a gentle shaker and a rare "
              "triangle, or a slow ambient-house four-on-the-floor heavily filtered and far back.",
        form=(("emergence", 16), ("drift A", 32), ("drift B", 32), ("thinning", 16), ("dissolve", 16)),
        instruments=("analog and digital pads", "piano", "tape loops", "field recordings", "synth drones",
                     "processed guitar"),
        sound_design="Slow-attack pads, long reverbs (10 s+) and freeze, tape loops and delays, granular "
                     "stretching, soft filtering; field recordings blended until indistinguishable from synths.",
        production="Quiet, very dynamic and wide; little compression, generous headroom; low end soft and "
                   "controlled; long fades in and out.",
        theory="Static or pedal-point harmony and phasing loops (Eno's Music for Airports used loops of "
               "co-prime lengths) replace progression and meter; consonance and slow timbral change are the "
               "form.",
        mix=Mix(lufs=(-20, -14), lra=(6, 14), low_end="moderate", tone="dark", width="wide"),
    ),
    Genre(
        name="drone",
        family="ambient and experimental",
        aliases=("drone music",),
        parent="minimalism",
        description="Music of sustained tones: long, unchanging or slowly shifting pitches and clusters whose "
                    "overtones, beating and tuning become the whole piece.",
        era="New York, early 1960s (La Monte Young, Theatre of Eternal Music); modern revival 2000s-2020s",
        touchstones=("La Monte Young", "Éliane Radigue", "Tony Conrad", "Phill Niblock", "Sarah Davachi",
                     "Kali Malone"),
        tempo=(40, 80),
        feel="beatless; static sustain with slow swells",
        swing=50,
        modes=("major", "mixolydian", "minor"),
        keys=("C major", "D major", "A minor"),
        progressions=(
            "I5-I5-I5-I5",
            "Iadd9-Isus4",
            "I-bVII",
            "i-bII",
        ),
        harmonic_rhythm=0.25,
        harmony="Essentially one sonority: a root with fifth and octave, sometimes in just intonation, with "
                "added 9ths, 4ths or a semitone cluster that beats against it; any change is a single voice "
                "sliding by step over minutes.",
        voicing="cluster",
        comping="sustain",
        bass_style="pedal",
        bass="A continuous low fundamental (organ, cello, synth or amplified string) held for the length of the "
             "piece.",
        melody_density="sparse",
        melody_scale="major pentatonic",
        melody="No melody in the usual sense: overtones emerging from the drone, slow glissandi, or single "
               "pitches entering and leaving the texture.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "low floor tom": "x...............|................",
            "ride":          "........o.......|........o.......",
        }},
        drums="Normally none. If a pulse is wanted: a soft low tom or mallet roll every two bars and an "
              "occasional bowed or brushed cymbal swell.",
        form=(("onset", 16), ("sustain", 64), ("shift", 32), ("sustain", 64), ("release", 16)),
        instruments=("pipe or electric organ", "sine-wave oscillators", "bowed strings", "tanpura",
                     "e-bowed guitar", "modular synth"),
        sound_design="Pure and harmonically rich sustained tones, just-intonation tuning, slowly sweeping filters "
                     "that expose overtones, tape feedback; amplification so beating and combination tones are "
                     "audible.",
        production="Very wide dynamic headroom, minimal compression, careful low-end control so the drone is "
                   "full but not boomy; long fades; listening level matters more than loudness.",
        theory="Replaces harmony and rhythm with tuning and timbre: just intervals (3:2, 5:4, 7:4), "
               "beating between near-unison pitches and the harmonic series heard in real time. Form is "
               "duration itself.",
        mix=Mix(lufs=(-22, -14), lra=(3, 10), low_end="moderate", tone="warm", width="wide"),
    ),
    Genre(
        name="dark ambient",
        family="ambient and experimental",
        parent="ambient",
        description="Ambient's ominous side: subterranean rumbles, metallic resonances, distant choirs and "
                    "decayed field recordings that evoke caves, ruins, ritual and the void.",
        era="Europe, 1980s (out of industrial music); Cold Meat Industry and Cryo Chamber labels",
        touchstones=("Lustmord", "Raison d'être", "Atrium Carceri", "Thomas Köner", "Coil", "Kammarheit"),
        tempo=(40, 80),
        feel="beatless or a slow ritual pulse",
        swing=50,
        modes=("phrygian", "minor", "locrian"),
        keys=("C phrygian", "D minor", "E phrygian"),
        progressions=(
            "i-II-i-i",
            "i-v°",
            "minor: i-bV",
            "minor: i-VI-i-bII",
            "locrian: i°-II",
        ),
        harmonic_rhythm=0.25,
        harmony="Drones on the tonic with semitone (phrygian bII) and tritone shadows; distant choir or string "
                "clusters drifting by step; minor triads appear only fleetingly.",
        voicing="cluster",
        comping="sustain",
        bass_style="pedal",
        bass="Sub-bass rumbles and drones below 60 Hz, sometimes pitched, sometimes noise; slow swells.",
        melody_density="sparse",
        melody_scale="phrygian",
        melody="Fragments: a distant chant, a detuned bell, a slowed choir phrase; semitone neighbour motifs.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "low floor tom": "x...............|x.......o.......",
            "china":         "................|o...............",
        }},
        drums="Usually none. When a pulse is wanted: a slow ritual drum (low floor tom or processed frame drum) "
              "once a bar, and a far-off metallic scrape or gong-like swell.",
        form=(("descent", 16), ("chamber A", 32), ("disturbance", 16), ("chamber B", 32), ("fade", 16)),
        instruments=("synth drones", "processed field recordings", "metallic percussion", "choir samples",
                     "bowed metal", "sub bass"),
        sound_design="Pitched-down and time-stretched recordings, convolution reverbs of caves and tunnels, "
                     "granular textures, ring modulation, bowed metal and resonant filters.",
        production="Huge, enveloping reverbs, deep sub content, dark top end; very wide dynamics with sudden "
                   "swells; immersive stereo or surround placement.",
        theory="Harmony reduced to a pedal with dissonant satellites (b2, tritone) heard as tension that never "
               "resolves; time is non-metrical, and form follows a narrative of spaces rather than sections.",
        mix=Mix(lufs=(-22, -15), lra=(8, 16), low_end="heavy", tone="dark", width="wide"),
    ),
    Genre(
        name="new age",
        family="ambient and experimental",
        aliases=("new age music",),
        parent="ambient",
        description="Gentle, uplifting instrumental music for meditation and relaxation: sweeping synth pads, "
                    "flowing piano, flutes and nature sounds in bright, consonant keys.",
        era="US and Europe, 1970s-80s (Windham Hill, Private Music)",
        touchstones=("Vangelis", "Kitaro", "Enya", "George Winston", "Yanni", "Laraaji", "Steven Halpern"),
        tempo=(60, 100),
        feel="flowing and rubato, or a soft steady pulse",
        swing=50,
        modes=("major", "lydian", "mixolydian", "dorian"),
        keys=("D major", "C major", "G major", "E major"),
        progressions=(
            "Iadd9-IVadd9",
            "I-V-vi-IV",
            "vi-IV-I-V",
            "Imaj7-IVmaj7",
            "lydian: I-II-I-II",
            "mixolydian: I-bVII-IV-I",
        ),
        harmonic_rhythm=0.5,
        harmony="Diatonic and consonant: add9, sus2 and maj7 colour, plagal IV-I motion, lydian I-II shimmer and "
                "mixolydian bVII; pedal tones under slowly changing triads; no harsh dissonance.",
        voicing="open",
        comping="arpeggio_up",
        bass_style="whole",
        bass="Sustained low roots on piano left hand or synth, often with a tonic pedal; gentle and supportive.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Lyrical, singable lines on flute, piano, synth or wordless vocals; pentatonic, stepwise, often "
               "in long arching phrases with sequential repetition.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "low conga": "x.......x.......",
            "shaker":    "..x...x...x...x.",
            "triangle":  "x...............",
        }},
        drums="Mostly absent; at most a soft hand drum, shaker or chimes keeping a gentle pulse, or a slow "
              "electronic beat in 80s Vangelis/Kitaro style.",
        form=(("intro", 8), ("theme A", 16), ("theme B", 16), ("theme A", 16), ("bridge", 8), ("theme A", 16),
              ("outro", 8)),
        instruments=("synth pads (Yamaha CS-80, Jupiter-8)", "piano", "flute or pan flute", "harp",
                     "nature recordings", "wordless choir", "chimes and singing bowls"),
        sound_design="Bright, airy pads with slow attack, glassy digital bells, layered choirs (Enya-style "
                     "multitracked voices), long hall reverb, nature sounds of water and birds.",
        production="Clean and soft with wide stereo pads and natural dynamics; gentle compression only; smooth, "
                   "warm high end.",
        theory="Static, consonant diatonic harmony (often lydian or mixolydian colour) with pedal points and "
               "plagal motion; melodies are pentatonic and sequential, avoiding tension so the music "
               "supports a calm, unresolved state.",
        mix=Mix(lufs=(-18, -12), lra=(6, 12), low_end="moderate", tone="warm", width="wide"),
    ),

    # ---------------------------------------------------------- industrial and dark
    Genre(
        name="industrial",
        family="electronic",
        aliases=("industrial music",),
        description="Abrasive, confrontational music built from noise, tape loops, metal percussion and machine "
                    "rhythms, turning the sounds of factories and media into art.",
        era="UK and Germany, mid-1970s (Industrial Records); industrial dance and rock in the late 1980s",
        touchstones=("Throbbing Gristle", "Cabaret Voltaire", "Einstürzende Neubauten", "SPK", "Test Dept",
                     "Skinny Puppy", "Nine Inch Nails"),
        tempo=(90, 140),
        feel="mechanical and repetitive; machine-straight or lurching tape loops",
        swing=50,
        modes=("phrygian", "minor", "locrian"),
        keys=("E phrygian", "D minor", "C minor"),
        progressions=(
            "i-II-i-i",
            "i-i-i-II",
            "minor: i-bV",
            "minor: i-VI-VII-i",
            "minor: i-iv",
        ),
        harmonic_rhythm=0.5,
        harmony="Little conventional harmony: drones, power-chord riffs and single-chord vamps, with the "
                "phrygian bII and the tritone for menace; harmony serves as a noise bed.",
        voicing="power",
        comping="pulse_16",
        bass_style="sixteenths",
        bass="Sequenced, distorted bass ostinatos on the root, or slow sub drones; often a looped 16th-note "
             "pattern with semitone inflections.",
        melody_density="sparse",
        melody_scale="phrygian",
        melody="Shouted, distorted or spoken vocals; rare synth melodies limited to a few chromatic notes; "
               "found-sound and media samples (radio, speeches) used as hooks.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":     "x.......x.x.....|x.......x.x...x.",
            "snare":    "....X.......X...|....X.......X...",
            "low tom":  "..x...x...x...x.|..x...x...x...xx",
            "cowbell":  "x..x..x..x..x...|x..x..x..x..x...",
        }},
        drums="Drum machines driven into distortion plus sampled or struck metal (sheet metal, pipes, oil "
              "drums); rigid, looping patterns; heavy snares, tom-like metallic pulses, clanging accents in 3s "
              "against 4/4.",
        form=(("intro", 16), ("loop A", 32), ("noise break", 8), ("loop B", 32), ("loop A", 16), ("collapse", 8)),
        instruments=("drum machine", "metal percussion and found objects", "tape loops", "analog synth",
                     "distorted vocals", "sampler", "noise generators"),
        sound_design="Distortion, ring modulation, tape manipulation, metallic samples, white noise, "
                     "feedback; vocals through megaphone, distortion or bitcrushing.",
        production="Harsh and mid-forward with brittle highs; heavy compression and saturation on drums; "
                   "deliberately confrontational balances with noise up front.",
        theory="Timbre and repetition over harmony: ostinatos and loops, metric cross-accents (3-against-4 metal "
               "hits), chromatic semitone and tritone relationships instead of functional progressions.",
        mix=Mix(lufs=(-11, -7), lra=(4, 9), low_end="heavy", tone="bright", width="moderate"),
    ),
    Genre(
        name="ebm",
        family="electronic",
        aliases=("electronic body music",),
        parent="industrial",
        description="Stark, militant dance music: sequenced 16th-note basslines, pounding drum machines and "
                    "barked vocals, built for the body rather than the head.",
        era="Belgium and Germany, early 1980s",
        touchstones=("Front 242", "Nitzer Ebb", "DAF", "Die Krupps", "Front Line Assembly", "Klinik"),
        tempo=(110, 135),
        feel="straight, rigid, marching; four-on-the-floor or kick on every beat with backbeat snare",
        swing=50,
        modes=("minor", "phrygian"),
        keys=("A minor", "E minor", "D minor", "G minor"),
        progressions=(
            "i-i-i-VII",
            "i-VI",
            "i-bII",
            "i-iv",
            "i-VI-VII-i",
        ),
        harmonic_rhythm=0.5,
        harmony="Minimal: one-chord vamps over a sequenced bass, changing to VI, VII or bII every two or four "
                "bars; pads are stabs or sustained fifths, not lush chords.",
        voicing="power",
        comping="stabs",
        bass_style="sixteenths",
        bass="The signature: a sequenced analog 16th-note bass (Korg MS-20, SH-101, Pro-One) on the root with "
             "accented offbeats and octave jumps, often the same figure transposed with the chord.",
        melody_density="sparse",
        melody_scale="natural minor",
        melody="Chanted, shouted or spoken vocals with slogan-like hooks; short monophonic synth riffs and "
               "stabs answering the vocal.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x...x...x...x...",
            "snare":      "....X.......X...",
            "closed hat": "..x...x...x...x.",
            "clap":       "....x.......x...",
        }},
        drums="Drum machines (TR-808, DMX, sampled kits on Emulator): a kick on every beat, heavy snare and clap "
              "on 2 and 4, offbeat hats; few fills, militaristic precision.",
        form=(("intro", 16), ("verse", 16), ("chorus", 16), ("verse", 16), ("chorus", 16), ("break", 8),
              ("chorus", 16), ("outro", 16)),
        instruments=("analog sequencer and monosynth bass", "drum machine", "sampler", "shouted vocals",
                     "synth stabs"),
        sound_design="Hard, filtered analog bass with short decay and accent, metallic samples, gated noise "
                     "snares, distorted or vocoded vocals.",
        production="Dry and punchy: tight low end shared by kick and bass, mid-forward vocals, little reverb, "
                   "strong compression.",
        theory="Rhythmic ostinato is the composition: a 16th-note bass with offbeat accents interlocks with a "
               "quarter-note kick for a motoric groove; harmony is modal and static, changing only by riff "
               "transposition.",
        mix=Mix(lufs=(-10, -7), lra=(4, 7), low_end="heavy", tone="neutral", width="moderate"),
    ),
    Genre(
        name="darkwave",
        family="electronic",
        aliases=("dark wave",),
        parent="post-punk",
        description="Gloomy, romantic synth music from the post-punk underground: cold drum machines, chorused "
                    "bass and guitar, minor-key synth lines and deep, detached vocals.",
        era="Europe, early 1980s (with coldwave and minimal synth); revived in the 2010s",
        touchstones=("Clan of Xymox", "Lebanon Hanover", "Boy Harsher", "She Past Away", "Drab Majesty",
                     "Cold Cave"),
        tempo=(100, 140),
        feel="straight, steady, motorik drum-machine pulse",
        swing=50,
        modes=("minor", "dorian", "phrygian"),
        keys=("E minor", "A minor", "D minor", "B minor"),
        progressions=(
            "i-VI-III-VII",
            "i-VII-VI-VII",
            "i-iv-i-VI",
            "i-III-VII-iv",
            "dorian: i-IV",
        ),
        harmonic_rhythm=1,
        harmony="Natural-minor triads and power chords, one per bar; dorian i-IV for a wistful lift; pads in "
                "bare fifths; guitar arpeggios add 9ths and suspensions.",
        voicing="close",
        comping="eighths",
        bass_style="eighths",
        bass="Driving 8th notes, often played high on the neck with heavy chorus (Peter Hook style) so the bass "
             "carries the melody, or a sequenced synth bass on the root.",
        melody_density="medium",
        melody_scale="natural minor",
        melody="Baritone, monotone or crooned vocals in a narrow range; cold monophonic synth hooks and "
               "chorused guitar lines in the upper register.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.......x.x.....",
            "snare":      "....X.......X...",
            "closed hat": "xxxxxxxxxxxxxxxx",
        }},
        drums="Cheap drum machines (TR-606, TR-707, LinnDrum, Boss DR-55): kick on 1 and 3, cracking snare "
              "with reverb on 2 and 4, constant 16th hats; no fills or human feel.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("bridge", 8),
              ("chorus", 16), ("outro", 8)),
        instruments=("drum machine", "chorused bass", "analog synths", "chorused electric guitar",
                     "baritone vocals"),
        sound_design="Chorus and flanger on bass and guitar, thin analog synths (Korg Polysix, Juno), gated "
                     "plate reverb on snare, slapback and long delays on vocals.",
        production="Cold and spacious: dark tone, mid-range bass and guitar up front, vocals drenched in reverb; "
                   "modest loudness; analog warmth from tape.",
        theory="Static minor-mode harmony with melodic bass (bass as the lead voice) and narrow-range vocal "
               "lines; motorik rhythmic repetition creates trance-like gloom rather than climax.",
        mix=Mix(lufs=(-11, -8), lra=(4, 8), low_end="moderate", tone="dark", width="wide"),
    ),
    Genre(
        name="witch house",
        family="electronic",
        aliases=("drag",),
        parent="darkwave",
        description="Occult, slowed-down electronic music: chopped and screwed hip-hop drums, crushed 808s, "
                    "eerie choir pads and pitched-down, smeared vocals.",
        era="US internet underground, 2009-2011",
        touchstones=("Salem", "oOoOO", "Holy Other", "White Ring", "Balam Acab", "Crystal Castles"),
        tempo=(60, 90),
        feel="half-time, dragged, chopped-and-screwed; trap-style hat rolls",
        swing=50,
        modes=("minor", "phrygian"),
        keys=("F minor", "C minor", "D minor", "G minor"),
        progressions=(
            "i-VI",
            "i-VI-III-VII",
            "i-bII",
            "i-iv-VI-V",
            "phrygian: i-II-i-vii",
        ),
        harmonic_rhythm=0.5,
        harmony="Minor triads and slow two-chord loops, choirs and pads in close clusters; phrygian bII and "
                "harmonic-minor V for occult dread; chords pitched down and smeared by reverb.",
        voicing="cluster",
        comping="sustain",
        bass_style="808",
        bass="Distorted, long-decay 808s that follow the kick and slide between roots, often clipping; or a "
             "slow sub drone.",
        melody_density="sparse",
        melody_scale="harmonic minor",
        melody="Pitched-down, slurred vocals and ghostly samples; detuned bells and choir lines; short "
               "chromatic motifs.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x......x..x.....|x.........x.....",
            "snare":      "........X.......|........X.......",
            "closed hat": "x.x.x.x.x.x.xxxx|x.x.x.x.x.x.x.x.",
            "clap":       "........x.......|........x.......",
        }},
        drums="Hip-hop and trap drums slowed: snare or clap on beat 3 (half-time), booming 808 kicks, "
              "hat rolls in triplets and 32nds; chopped-and-screwed stutters and tape-stop drops.",
        form=(("intro", 8), ("A", 16), ("B", 16), ("break", 8), ("A", 16), ("outro", 8)),
        instruments=("TR-808 and trap samples", "distorted 808 bass", "choir pads", "pitched vocals",
                     "detuned synths", "noise and field recordings"),
        sound_design="Pitch-shifting down, heavy reverb and delay, bitcrushing and distortion, reversed "
                     "samples, tape-stops; occult imagery mirrored in choir and bell timbres.",
        production="Murky and saturated: heavy distorted low end, dark top, wide washed-out pads; drums hit "
                   "hard while everything else stays blurred.",
        theory="Chopped-and-screwed technique (slowing, pitching down, repeating fragments) applied to dark "
               "minor and phrygian loops; half-time backbeat at 60-80 BPM with trap-style subdivisions creates "
               "a dragging, suspended pulse.",
        mix=Mix(lufs=(-11, -8), lra=(4, 8), low_end="heavy", tone="dark", width="wide"),
    ),
    Genre(
        name="musique concrete",
        family="ambient and experimental",
        aliases=("musique concrète", "concrete music"),
        description="Music composed directly from recorded sounds: doors, trains, voices and instruments cut, "
                    "looped, reversed and transformed on tape until their source is less important than their "
                    "shape.",
        era="Paris, 1948 onward (Pierre Schaeffer at the RTF studio, GRM)",
        touchstones=("Pierre Schaeffer", "Pierre Henry", "Bernard Parmegiani", "Luc Ferrari", "François Bayle",
                     "Edgard Varèse"),
        tempo=(40, 120),
        feel="non-metrical; gestures, densities and silences rather than beats",
        swing=50,
        modes=("chromatic", "whole tone", "minor"),
        keys=("C chromatic",),
        melody_scale="chromatic",
        progressions=(
            "minor: i-bII",
            "minor: i-bV",
            "whole tone: I+-II+",
            "minor: i-i",
        ),
        harmonic_rhythm=0.25,
        harmony="No harmony in the tonal sense; pitched material comes from transposed recordings (tape-speed "
                "changes), resonant clusters and drones. If chords are needed, use clusters, semitone and "
                "tritone pairs or whole-tone augmented sonorities.",
        voicing="cluster",
        comping="none",
        bass_style="none",
        bass="No bassline; low frequencies come from slowed recordings, rumbles and resonances of objects.",
        melody_density="sparse",
        melody="Sound objects (objets sonores) instead of tunes: a gesture's attack, sustain and decay shape the "
               "line; recurring sounds act as motifs, transformed by speed, reversal and filtering.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "low woodblock":  "x.....x...x.....|..x.......x.....",
            "high woodblock": "...o.......o....|o.....o.......o.",
        }},
        drums="No drum kit. If a pulse is wanted, a looped recording of a struck object (wood, metal, a "
              "locked groove) repeating irregularly, as in Schaeffer's Étude aux chemins de fer.",
        form=(("exposition of sound objects", 16), ("development", 32), ("dense climax", 16), ("silence", 4),
              ("transformation", 24), ("dissolution", 16)),
        instruments=("tape machines", "microphones and found objects", "turntables (locked grooves)",
                     "piano (prepared or recorded)", "voice", "sampler or granular processor"),
        sound_design="Tape splicing, loops, reversal, speed change, filtering and reverb; in the digital era "
                     "granular synthesis, spectral processing and convolution; reduced listening to the sound "
                     "itself, detached from its source.",
        production="Concert-hall dynamics, often for multichannel speaker orchestras (acousmonium); no limiting, "
                   "wide stereo or surround diffusion, silence used as material.",
        theory="Schaeffer's typology of sound objects (mass, dynamic, grain, allure) replaces pitch and meter "
               "as compositional parameters; form is built from gesture and texture, contrast of density, and "
               "the transformation of recognisable sources into abstract ones.",
        mix=Mix(lufs=(-24, -16), lra=(10, 20), low_end="light", tone="neutral", width="wide"),
    ),
]
