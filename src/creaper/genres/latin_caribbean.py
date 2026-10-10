"""Latin American and Caribbean genres: clave music, Brazil, the Southern Cone, Spain, Mexico and the islands."""

from . import Genre, Mix

# Shared step patterns (16ths, 2 bars of 4/4 = 32 steps). Counted from beat 1 of bar 1.
SON_32 = "x.....x.....x...|....x...x......."      # son clave 3-2: 1, 2&, 4 | 2, 3
SON_23 = "....x...x.......|x.....x.....x..."      # son clave 2-3: 2, 3 | 1, 2&, 4
RUMBA_23 = "....x...x.......|x.....x.......x."    # rumba clave 2-3: 3-side's last stroke on 4&
CASCARA_23 = "x...x...x.x...x.|x...x.x...x...x."  # cascara aligned 2-3
GUIRO_LSS = "X...x.x.X...x.x."                     # long, short-short scrape per half bar

GENRES = [
    # ------------------------------------------------------------- Latin urban
    Genre(
        name="reggaeton",
        family="latin",
        aliases=("reguetón", "reggaetón", "perreo"),
        parent="dancehall",
        description="Puerto Rican club music built on the dembow riddim: a steady kick on every beat under a "
                    "tresillo-shaped snare, minor-key loops and rapped or sung Spanish hooks made for perreo.",
        era="San Juan, Puerto Rico, early 1990s underground; global from the mid-2000s and again from 2017",
        touchstones=("Daddy Yankee - Barrio Fino", "Tego Calderón", "Don Omar", "Wisin & Yandel",
                     "Luny Tunes", "Bad Bunny", "J Balvin", "Karol G", "Tainy"),
        tempo=(85, 100),
        feel="dembow: four-on-the-floor kick with a 3+3+2 snare on top, straight 16ths",
        swing=50,
        modes=("minor", "major"),
        keys=("A minor", "C# minor", "F# minor", "D minor"),
        progressions=(
            "i-VI-III-VII",
            "i-iv-VII-III",
            "VI-VII-i-i",
            "i-VII-VI-VII",
            "major: vi-IV-I-V",
            "i7-iv7",
        ),
        harmonic_rhythm=1,
        harmony="Four-chord minor loops repeated for the whole song (i-VI-III-VII is the default), one chord a bar; "
                "added 9ths and sus2 colours on pads; romantic tracks use the major-key vi-IV-I-V; no cadences, "
                "the loop never stops, sections change by arrangement not by harmony.",
        voicing="open",
        comping="tresillo",
        bass_style="808",
        bass="Long 808 or sine sub on the chord roots, hitting with the kick on beat 1 and following the tresillo "
             "(1, the 'a' of 1, the 'and' of 2) or simply the dembow snare accents; short glides between roots; "
             "older records double the kick with a punchy synth bass.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="Chanted, rhythmic vocal hooks in a narrow range (a 5th or so), syllables locked to the dembow 16ths; "
               "verses rapped in 16th-note flows; coro repeated 4 times; ad-libs and call-and-response tags "
               "('dale', producer tags); melodic plucks or pan-flute samples doubling the hook.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x...x...x...x...",
            "snare":      "...x..x....x..x.",
            "closed hat": "x.x.x.x.x.x.x.x.",
            "shaker":     "oxoxoxoxoxoxoxox",
        }},
        drums="The dembow: kick on all four beats, snare (or a tuned timbal/tom sample) on the 'a' of 1, the 'and' "
              "of 2, the 'a' of 3 and the 'and' of 4, i.e. tresillo in each half bar. Light 8th hats, shakers and "
              "a timbal roll or reverse cymbal into each coro. Drop the kick for 1-2 bars before the hook; modern "
              "tracks thin the pattern (kick only on 1 and 3, snare stripped) in verses.",
        form=(("intro", 8), ("coro", 8), ("verse", 16), ("pre-coro", 4), ("coro", 8), ("verse", 16),
              ("coro", 8), ("bridge", 8), ("coro", 8), ("outro", 4)),
        instruments=("dembow drums (kick, snare, timbal samples)", "808 or sub bass", "synth pad", "pluck or bell lead",
                     "guitar or pan-flute samples", "lead vocal", "ad-lib vocals"),
        sound_design="Hard, short dembow one-shots (the snare is often a pitched tom/timbal hit), round 808 with "
                     "a little distortion, glossy supersaw pads, plucky synths with short delays, Auto-Tuned vocals "
                     "with stacked doubles; risers and reverse cymbals into coros.",
        production="Loud and dense: kick and 808 mono and dominant, vocal very forward and bright, heavy limiting; "
                   "8-bar sections; drop-outs and filter sweeps to mark the coro; sidechain the pad lightly to the kick.",
        theory="Rhythmically it's tresillo (3+3+2) over a straight four: the Jamaican dembow riddim descended from "
               "Cuban/African timelines. Harmonically static modal loops in natural minor; interest comes from "
               "the syncopation and the vocal cadence, not chord function.",
        mix=Mix(lufs=(-7, -5), lra=(3, 6), low_end="very heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="dembow",
        family="latin",
        aliases=("dominican dembow", "dembow dominicano"),
        parent="reggaeton",
        description="The Dominican street version of the dembow riddim: faster, rawer and relentlessly percussive, "
                    "with chanted hooks over pounding kicks, chopped one-shots and almost no harmony.",
        era="Santo Domingo, Dominican Republic, late 2000s; mainstream in the late 2010s",
        touchstones=("El Alfa", "Shadow Blow", "Bulin 47", "Chimbala", "Rochy RD", "Tokischa", "Mozart La Para"),
        tempo=(112, 130),
        feel="fast dembow, straight 16ths, hammering kick with fills every 2-4 bars",
        swing=50,
        modes=("minor", "phrygian"),
        keys=("A minor", "G minor", "E minor"),
        progressions=(
            "i-i-VII-VII",
            "i-VI-VII-i",
            "i-iv",
            "phrygian: i-II",
            "i-VI-III-VII",
        ),
        harmonic_rhythm=0.5,
        harmony="Minimal: one or two minor chords, often just a stab or a synth riff on the tonic, a half-step "
                "phrygian rub (i-bII) for menace; harmony is texture behind the chant.",
        voicing="power",
        comping="stabs",
        bass_style="808",
        bass="Short, punchy 808 or bass stabs that double the kick and the dembow snare hits; tonic pedal with "
             "octave jumps; little sustain so the kick stays clear at fast tempos.",
        melody_density="busy",
        melody_scale="minor pentatonic",
        melody="Shouted, chanted catch-phrases repeated many times, crowd-style coros, rapid-fire verses; "
               "short synth or whistle riffs and vocal chops answer the vocal.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x...x...x...x...|x...x...x...x.x.",
            "snare":      "...x..x....x..x.|...x..x....x.xxx",
            "closed hat": "xoxoxoxoxoxoxoxo|xoxoxoxoxoxoxoxo",
            "low conga":  "..x.......x.....|..x.......x.....",
            "clap":       "....x.......x...|....x.......x...",
        }},
        drums="Dembow skeleton (four kicks, tresillo snare) but faster and busier: layered claps on 2 and 4, "
              "16th hats, tumba/conga hits, snare rolls and tom fills closing every 2nd or 4th bar, sound-effect "
              "one-shots (gunshots, horns, vocal 'ey') as percussion. Breaks drop everything but the vocal for a bar.",
        form=(("intro", 4), ("coro", 8), ("verse", 16), ("coro", 8), ("verse", 16), ("coro", 8), ("outro", 4)),
        instruments=("dembow drum kit", "808", "synth stab", "vocal chops", "sound-effect one-shots", "lead vocal"),
        sound_design="Gritty, saturated drums, clipped 808s, cheap-sounding synth leads and sirens on purpose, "
                     "heavily processed chanted vocals, lots of one-shot ear candy.",
        production="Very loud and in-your-face, short songs (2-3 minutes), drums and vocal at the front, little reverb, "
                   "clipping as a sound; arrangement by muting and unmuting loops.",
        theory="Same 3+3+2 tresillo over four as reggaeton, but at a tempo where the kick becomes a drone of energy; "
               "the music is almost purely rhythmic and the phrygian half-step is the main harmonic colour.",
        mix=Mix(lufs=(-7, -4.5), lra=(2, 5), low_end="very heavy", tone="bright", width="moderate"),
    ),
    Genre(
        name="latin trap",
        family="latin",
        aliases=("trap latino",),
        parent="reggaeton",
        description="Spanish-language trap from Puerto Rico: half-time 808 drums and hi-hat rolls with dark minor "
                    "loops, sung-rapped melodies and the occasional dembow switch.",
        era="Puerto Rico, mid-2010s",
        touchstones=("Bad Bunny - X 100pre", "Anuel AA", "Bryant Myers", "Arcángel", "De La Ghetto", "Ozuna",
                     "Farruko", "Myke Towers"),
        tempo=(125, 150),
        feel="half-time trap: snare on beat 3, hats in 8ths, 16ths and triplet rolls",
        swing=50,
        modes=("minor", "harmonic minor"),
        keys=("C# minor", "F minor", "G minor", "B minor"),
        progressions=(
            "i-VI-III-VII",
            "i-VI-iv-V",
            "i-iv-VI-V",
            "harmonic minor: i-VI-V",
            "i-VII-VI-VII",
        ),
        harmonic_rhythm=1,
        harmony="Dark minor loops played as arpeggiated piano, guitar or bells; harmonic-minor V for a Latin, "
                "dramatic pull; occasional nylon-guitar riffs borrowing the Andalusian i-VII-VI-V.",
        voicing="open",
        comping="arpeggio_up",
        bass_style="808",
        bass="Long distorted 808s with glides, landing on the kick pattern and the chord roots; slides into the "
             "next bar; sub cuts out before the snare for space.",
        melody_density="medium",
        melody_scale="harmonic minor",
        melody="Melodic, Auto-Tuned rap-singing, triplet flows, hooks repeated twice per coro; melancholic minor "
               "melodies with harmonic-minor leading tones; ad-libs and doubled hook lines.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.........x.....|x......x..x.....",
            "snare":      "........x.......|........x.......",
            "closed hat": "x.x.x.x.x.x.x.x.|x.x.x.x.xxxxx.x.",
            "open hat":   "..............x.|................",
        }},
        drums="Trap kit: snare/clap on beat 3 of each half-time bar, syncopated 808 kicks, 8th hats with 16th, "
              "32nd and triplet rolls; some tracks switch to a dembow pattern for the coro.",
        form=(("intro", 4), ("coro", 8), ("verse", 16), ("coro", 8), ("verse", 16), ("coro", 8), ("outro", 4)),
        instruments=("808", "trap drums", "piano or bells", "nylon or electric guitar", "pad", "lead vocal"),
        sound_design="Dark keys and bells, filtered guitar loops, distorted 808 with long decay, crisp hats, "
                     "heavy Auto-Tune and reverb throws on the vocal.",
        production="Loud, dark and spacious: 808 dominates the low end, sparse mids, vocal upfront with doubles; "
                   "beat drops (mute drums) on key lines.",
        theory="Half-time trap rhythm with Latin minor harmony: harmonic-minor dominants and Andalusian bass lines "
               "give the melancholy; melodies stress the raised 7th as a leading tone.",
        mix=Mix(lufs=(-8, -5.5), lra=(3, 6), low_end="very heavy", tone="dark", width="wide"),
    ),
    Genre(
        name="moombahton",
        family="latin",
        aliases=("moombah",),
        parent="reggaeton",
        description="Dutch house slowed to reggaeton tempo: a house kick and synths with the dembow snare on top, "
                    "made for DJs bridging club music and Latin dance.",
        era="Washington, D.C., 2009 (Dave Nada); peak early 2010s",
        touchstones=("Dave Nada", "Munchi", "Diplo", "Major Lazer - Lean On", "Dillon Francis", "Valentino Khan"),
        tempo=(105, 112),
        feel="dembow at 108 BPM with a four-on-the-floor house kick, straight 16ths",
        swing=50,
        modes=("minor", "phrygian"),
        keys=("F minor", "G minor", "A minor"),
        progressions=(
            "i-VI-III-VII",
            "i-VII-VI-VII",
            "phrygian: i-II-i-VII",
            "i-iv-VI-V",
        ),
        harmonic_rhythm=1,
        harmony="Minor loops and drops built from a single riff; phrygian bII stabs; big minor chord stabs "
                "with pitch bends in the drop.",
        voicing="power",
        comping="stabs",
        bass_style="808",
        bass="Wobbling or detuned sub following the dembow accents, long 808 notes under the drop, "
             "sometimes a growl or reese layer in the mids.",
        melody_density="sparse",
        melody_scale="phrygian",
        melody="Short synth or vocal-chop riffs, horn-like leads with pitch bends, chant hooks; "
               "builds and drops like EDM.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x...x...x...x...",
            "snare":      "...x..x....x..x.",
            "closed hat": "xxxxxxxxxxxxxxxx",
            "open hat":   "..x...x...x...x.",
        }},
        drums="House kick on every beat, dembow snare/tom (the 'a' of 1, 'and' of 2, 'a' of 3, 'and' of 4), "
              "16th hats and open-hat offbeats, snare rolls and white-noise risers in builds.",
        form=(("intro", 16), ("build", 8), ("drop", 16), ("break", 16), ("build", 8), ("drop", 16), ("outro", 16)),
        instruments=("house kick", "dembow snare", "sub bass", "synth stabs", "vocal chops", "risers"),
        sound_design="Dutch house squeals and stabs, detuned leads, vocal chops, big reverb snares, "
                     "riser and impact FX.",
        production="EDM-style: sidechained everything to the kick, loud masters, DJ-friendly 16-bar intros and outros.",
        theory="A tempo hack: house at 128 slowed to ~108 lines up with reggaeton's dembow, merging "
               "four-on-the-floor with tresillo syncopation.",
        mix=Mix(lufs=(-7, -5), lra=(3, 6), low_end="very heavy", tone="bright", width="wide"),
    ),
    # ------------------------------------------------------------- Cuban and salsa
    Genre(
        name="son cubano",
        family="latin",
        aliases=("son", "son montuno"),
        description="Cuba's foundational dance music: guitar and tres guajeos, anticipated bass, bongó and maracas "
                    "over son clave, with a sung verse that opens into a call-and-response montuno.",
        era="Eastern Cuba (Oriente), early 1900s; Havana sextetos and septetos in the 1920s-30s; revived in the 1990s",
        touchstones=("Sexteto Habanero", "Septeto Nacional Ignacio Piñeiro", "Arsenio Rodríguez", "Trío Matamoros",
                     "Compay Segundo", "Buena Vista Social Club", "Eliades Ochoa"),
        tempo=(80, 125),
        meter="4/4",
        feel="clave (son clave 3-2 or 2-3), straight 8ths, anticipated bass",
        swing=50,
        modes=("major", "minor"),
        keys=("C major", "G major", "D minor", "A minor"),
        progressions=(
            "I-IV-V7-IV",
            "I-V7-V7-I",
            "ii7-V7-I-I",
            "minor: i-iv-V7-i",
            "minor: i-VII-VI-V7",
            "I-vi-ii-V7",
        ),
        harmonic_rhythm=1,
        harmony="Simple functional harmony: I, IV, V7 and ii-V; the montuno vamps a 2- or 4-bar cycle "
                "(I-IV-V7-IV); minor-key sones lean on i-iv-V7 and the Andalusian descent (Chan Chan-style "
                "bass line Dm-F-Gm-A is i-III-iv-V).",
        voicing="close",
        comping="montuno",
        bass_style="tumbao",
        bass="The tumbao: the bass anticipates the harmony, playing on the 'and' of 2 and on beat 4 (tied over the "
             "barline) and usually leaving beat 1 empty, so the next chord arrives before the downbeat; originally "
             "botija or marímbula, later upright bass.",
        melody_density="medium",
        melody_scale="major",
        melody="Verse (largo) sung in parallel 3rds by two voices; then the montuno: a short coro repeated against an "
               "improvised pregón by the sonero; tres and trumpet solos built from guajeo-style riffs.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "claves":     SON_32,
            "high bongo": "x.o.x.o.x.o...o.|x.o.x.o.x.o...o.",
            "low bongo":  "............X...|............X...",
            "maracas":    "X.x.X.x.X.x.X.x.|X.x.X.x.X.x.X.x.",
        }},
        drums="No kit: claves play son clave (often 3-2 in son), bongó plays the martillo (8th notes, thumb and "
              "index strokes with an open tone on the hembra on beat 4) and switches to the bongo bell in the "
              "montuno, maracas play steady 8ths; later conjuntos add conga tumbao.",
        form=(("intro", 8), ("verse", 16), ("verse", 16), ("montuno", 32), ("tres solo", 16), ("montuno", 16),
              ("coda", 4)),
        instruments=("tres cubano", "acoustic guitar", "upright bass", "bongó", "maracas", "claves", "trumpet",
                     "lead and coro vocals"),
        sound_design="Acoustic and woody: the tres's doubled steel strings, nylon guitar, upright bass, "
                     "muted trumpet, natural room ambience.",
        production="Recorded live, warm and roomy; bass and tres carry the groove, vocals in front, little "
                   "compression; percussion panned wide, clave audible but quiet.",
        theory="Everything is organised by clave: the tres guajeo and the bass tumbao are written 'in clave' "
               "(their accents line up with the clave's 3-side and 2-side). The anticipated bass and the "
               "call-and-response montuno are the template for salsa.",
        mix=Mix(lufs=(-14, -10), lra=(6, 11), low_end="moderate", tone="warm", width="moderate"),
    ),
    Genre(
        name="salsa",
        family="latin",
        aliases=("salsa dura", "salsa brava"),
        parent="son cubano",
        description="New York and Caribbean big-band son: piano montuno, anticipated tumbao bass, conga, bongó "
                    "and timbales locked to clave, horn mambos and sonero improvisation over a driving montuno.",
        era="New York City, late 1960s-70s (Fania Records); Puerto Rico, Colombia and Venezuela since",
        touchstones=("Fania All-Stars", "Willie Colón & Héctor Lavoe", "Eddie Palmieri", "Celia Cruz",
                     "Rubén Blades", "El Gran Combo de Puerto Rico", "Grupo Niche", "Marc Anthony"),
        tempo=(150, 215),
        feel="clave (usually 2-3 son clave), straight 8ths felt in cut time",
        swing=50,
        modes=("minor", "major"),
        keys=("A minor", "D minor", "G minor", "C major", "F major"),
        progressions=(
            "i-iv-V7-i",
            "iiø7-V7-i-i",
            "i-VII-VI-V7",
            "major: I-IV-V7-IV",
            "major: ii7-V7-Imaj7-vi7",
            "i7-iv7-bVII7-IIImaj7",
        ),
        harmonic_rhythm=1,
        harmony="Minor-key salsa dura lives on i-iv-V7 and ii-V vamps; salsa romántica uses major ii-V-I and "
                "pop-style progressions; the montuno section vamps a 2- or 4-bar cycle in clave; horn mambos "
                "add 7ths, 9ths and 13ths; V7b9 for drama.",
        voicing="close",
        comping="montuno",
        bass_style="tumbao",
        bass="Tumbao: bass on the 'and' of 2 and on beat 4, tied across the barline, beat 1 left open so the bass "
             "anticipates each chord change; roots and 5ths; in the montuno it locks with the conga's open tones "
             "on 4 and 4&.",
        melody_density="busy",
        melody_scale="harmonic minor",
        melody="Cuerpo (verse) melodies in long phrases; the montuno is a 4-8-beat coro answered by the sonero's "
               "improvised pregón; trumpets and trombones play unison or harmonised mambo riffs, built in clave.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "claves":       SON_23,
            "high timbale": CASCARA_23,
            "slap conga":   "o.o.X.o.o.o.....|o.o.X.o.o.o.....",
            "open conga":   "............x.x.|............x...",
            "low conga":    "................|..............x.",
            "high bongo":   "x.o.x.o.x.o...o.|x.o.x.o.x.o...o.",
            "guiro":        GUIRO_LSS + "|" + GUIRO_LSS,
        }},
        drums="Percussion trio, no kit: timbales play cascara on the shell in verses and the mambo bell in the "
              "montuno, with abanico rolls to set up sections; conga plays the tumbao (heel-toe ghosts, slap on 2, "
              "open tones on 4 and 4&, the tumba on 4& of the 3-side); bongó plays martillo in verses and the bongo "
              "bell (quarter notes, mouth on 1 and 3) in the montuno; güiro long-short-short; clave often implied.",
        form=(("intro", 8), ("cuerpo", 32), ("montuno", 32), ("mambo", 16), ("montuno", 16), ("moña", 16),
              ("coda", 4)),
        instruments=("piano", "upright or electric bass", "congas", "bongó and bongo bell", "timbales", "güiro",
                     "trumpets", "trombones", "lead vocal (sonero)", "coro"),
        sound_design="Bright brass, percussive acoustic piano in octaves, round electric or baby bass, live "
                     "percussion with natural room; Fania-era records are punchy and dry.",
        production="Live-ensemble balance: piano and bass centre, percussion spread across the stereo field "
                   "(timbales one side, conga other, bongó near centre), horns wide; moderate compression, "
                   "brass and vocals bright.",
        theory="Clave governs everything: the piano montuno (octave-doubled broken chords, syncopated) and the "
               "horn lines are written in 2-3 or 3-2 and must not 'cross' the clave; the anticipated tumbao "
               "means the harmonic rhythm is felt before the beat.",
        mix=Mix(lufs=(-11, -8), lra=(5, 9), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="mambo",
        family="latin",
        aliases=("mambo big band", "mambo cubano"),
        parent="son cubano",
        description="Afro-Cuban big-band dance music: riffing saxes against stabbing trumpets in clave, "
                    "piano montunos and a hot rhythm section with timbales, conga and bongó.",
        era="Havana 1938 (Cachao and Orestes López's danzón-mambo); Mexico City and New York, late 1940s-1950s",
        touchstones=("Pérez Prado", "Machito and his Afro-Cubans", "Tito Puente", "Tito Rodríguez", "Benny Moré",
                     "Arsenio Rodríguez", "Israel 'Cachao' López"),
        tempo=(170, 220),
        feel="clave (2-3), cut-time drive, horn riffs in clave",
        swing=50,
        modes=("major", "minor"),
        keys=("Bb major", "F major", "Eb major", "C minor"),
        progressions=(
            "I-V7-V7-I",
            "ii7-V7-I6/9-I6/9",
            "I-IV-V7-IV",
            "minor: i-iv-V7-i",
            "I-vi7-ii7-V7",
        ),
        harmonic_rhythm=1,
        harmony="Big-band jazz colour on Cuban vamps: 6/9 and maj7 tonics, ii-V turnarounds, 13th and altered "
                "dominants in the brass; the mambo section is a 2-4-bar vamp with stacked riffs.",
        voicing="drop2",
        comping="montuno",
        bass_style="tumbao",
        bass="Tumbao anticipations on the 'and' of 2 and beat 4; upright bass, sometimes doubled by baritone sax.",
        melody_density="busy",
        melody_scale="major",
        melody="Riff-based: saxes and trumpets play short contrasting ostinatos (guajeos) that interlock in clave; "
               "shout chorus brass with high trumpet hits and glissandi; Pérez Prado's grunts mark sections.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "claves":     SON_23,
            "cowbell":    "X...x...X...x.x.|X...x...X...x.x.",
            "slap conga": "o.o.X.o.o.o.....|o.o.X.o.o.o.....",
            "open conga": "............x.x.|............x...",
            "low conga":  "................|..............x.",
            "high timbale": "................|............xxx.",
        }},
        drums="Timbales lead (mambo bell on the cowbell in the mambo section, cascara in verses, abanico and "
              "rim-shot fills); bongó on the bongo bell playing quarter notes, mouth tones on 1 and 3; conga "
              "tumbao; clave sometimes played, always felt.",
        form=(("intro", 8), ("head", 32), ("mambo", 16), ("solo", 32), ("mambo", 16), ("head", 16), ("coda", 4)),
        instruments=("trumpets", "saxophones", "trombones", "piano", "upright bass", "timbales", "congas", "bongó",
                     "claves"),
        sound_design="1950s big-band sound: brassy, bright trumpets, reedy saxes, piano, upright bass; ribbon-mic "
                     "warmth and room.",
        production="Big room ambience, horns spread wide, percussion forward; little compression; mono-era balances "
                   "for vintage character.",
        theory="Built from layered ostinatos: each section plays a different riff in clave and the tension comes "
               "from their counterpoint; jazz voicings on Cuban rhythm.",
        mix=Mix(lufs=(-14, -10), lra=(7, 12), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="cha-cha-chá",
        family="latin",
        aliases=("cha-cha-cha", "cha cha", "chachachá"),
        parent="mambo",
        description="Cuban charanga dance music at a relaxed medium tempo: flute and violins over güiro and "
                    "cowbell, with the famous 'cha-cha-chá' on beats 4-and-1.",
        era="Havana, early 1950s (Enrique Jorrín with Orquesta América)",
        touchstones=("Enrique Jorrín", "Orquesta Aragón", "Orquesta América", "Tito Puente", "Cal Tjader",
                     "Pérez Prado"),
        tempo=(112, 128),
        feel="straight, laid-back clave feel (2-3 implied) with the 4-and-1 'cha-cha-chá'",
        swing=50,
        modes=("major", "minor"),
        keys=("C major", "F major", "G major", "D minor"),
        progressions=(
            "I-V7-V7-I",
            "I-vi-ii7-V7",
            "ii7-V7-I-I",
            "I-IV-V7-I",
            "minor: i-iv-V7-i",
        ),
        harmonic_rhythm=1,
        harmony="Clean, functional harmony from danzón: I-V7 alternations, ii-V turnarounds, bright major keys; "
                "the violins voice chords in close position; montuno vamps at the end.",
        voicing="close",
        comping="montuno",
        bass_style="tumbao",
        bass="Lighter tumbao: beat 1 often played, then the 'and' of 2 and beat 4 anticipating the next chord; "
             "roots and 5ths on an upright bass.",
        melody_density="medium",
        melody_scale="major",
        melody="Unison vocal choruses in a comfortable range, syllabic and on the beat; wooden flute improvises "
               "in the high register with trills; violins play rhythmic guajeos.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "cowbell":    "X...x...X...x...|X...x...X...x...",
            "guiro":      GUIRO_LSS + "|" + GUIRO_LSS,
            "slap conga": "o.o.X.o.o.o.....|o.o.X.o.o.o.....",
            "open conga": "............x.x.|............x.x.",
            "low timbale": "................|............x.x.",
        }},
        drums="Güiro (long scrape on 1 and 3, two short strokes on 2-and and 4-and) and the cha-cha cowbell "
              "(cencerro) on quarter notes carry the groove; conga tumbao; timbales mark the 4-and-1 "
              "('cha-cha-chá') at phrase ends; no drum kit.",
        form=(("intro", 8), ("A", 16), ("B", 16), ("A", 16), ("montuno", 16), ("flute solo", 16), ("coda", 4)),
        instruments=("wooden flute", "violins", "piano", "upright bass", "güiro", "cowbell", "congas", "timbales",
                     "unison vocals"),
        sound_design="Sweet charanga sound: five-key wooden flute, string section, bright piano; light, airy percussion.",
        production="Gentle and balanced, strings and flute bright, rhythm section tight but quiet; vintage mono "
                   "or narrow stereo.",
        theory="Slower than mambo so the syncopation is spelled out: the 4-and-1 triple figure is the dance step; "
               "the güiro's long-short-short and the anticipating bass give the swing without swung 8ths.",
        mix=Mix(lufs=(-14, -10), lra=(6, 11), low_end="light", tone="warm", width="moderate"),
    ),
    Genre(
        name="bolero",
        family="latin",
        aliases=("bolero romántico", "trío romántico"),
        description="The slow romantic song of Cuba and Mexico: lush chromatic harmony, a gently syncopated "
                    "bongó-and-maracas lilt and intimate crooned melodies with requinto guitar answers.",
        era="Santiago de Cuba, 1880s (Pepe Sánchez); Mexican tríos and orchestras, 1940s-60s",
        touchstones=("Agustín Lara", "Trío Los Panchos", "Armando Manzanero", "Lucho Gatica", "Benny Moré",
                     "Olga Guillot", "Luis Miguel - Romance"),
        tempo=(60, 92),
        feel="slow 4/4 with clave lilt (2-3) and habanera-style bongó figure",
        swing=50,
        modes=("minor", "major"),
        keys=("D minor", "A minor", "E minor", "F major"),
        progressions=(
            "i-iv-V7-i",
            "i-VII7-III-V7",
            "i-V7/iv-iv-V7",
            "iiø7-V7b9-i-i",
            "major: Imaj7-vi7-ii7-V7",
            "major: I-I7-IV-iv",
        ),
        harmonic_rhythm=1,
        harmony="Rich and chromatic: secondary dominants (V7/iv, V7/ii), diminished passing chords, minor iv in "
                "major keys, maj7 and 9th colours; modulation from minor verse to parallel major chorus is classic.",
        voicing="close",
        comping="arpeggio_updown",
        bass_style="root_fifth",
        bass="Root on beat 1 and 5th on beat 3, with a pickup on the 'and' of 2 (the habanera lilt); chromatic "
             "walk-ups into secondary dominants.",
        melody_density="medium",
        melody_scale="harmonic minor",
        melody="Long, lyrical lines with expressive rubato, wide leaps resolving by step, held notes over chromatic "
               "harmony; requinto guitar plays fills and introductions between phrases; two-voice harmony in 3rds.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "claves":     SON_23,
            "high bongo": "x..xx.x.x..xx.x.|x..xx.x.x..xx.x.",
            "maracas":    "x.x.x.x.x.x.x.x.|x.x.x.x.x.x.x.x.",
        }},
        drums="Soft hand percussion: bongó plays a habanera-like dotted figure, maracas or güiro steady 8ths, "
              "claves (2-3) quietly; orchestral boleros add brushed snare; no backbeat.",
        form=(("intro", 4), ("verse", 16), ("chorus", 16), ("requinto solo", 8), ("chorus", 16), ("coda", 4)),
        instruments=("nylon-string guitars", "requinto guitar", "upright bass", "bongó", "maracas", "piano",
                     "strings", "lead vocal"),
        sound_design="Intimate nylon guitars, warm upright bass, string pads; close-miked crooning vocal with plate "
                     "reverb.",
        production="Dynamic and soft: vocal very present, guitars wide, plenty of reverb; minimal compression to "
                   "keep the rubato breathing.",
        theory="Takes Cuban rhythm (habanera/clave lilt) and pairs it with European art-song harmony: secondary "
               "dominants, borrowed iv and tonicisations make the bolero the most harmonically rich Latin dance form.",
        mix=Mix(lufs=(-16, -12), lra=(7, 13), low_end="light", tone="warm", width="moderate"),
    ),
    # ------------------------------------------------------------- Dominican and Colombian
    Genre(
        name="bachata",
        family="latin",
        aliases=("bachata dominicana",),
        parent="bolero",
        description="Dominican guitar music: a bright, arpeggiating requinto over syncopated bass, bongó and a "
                    "steady scraped güira, singing of heartbreak at a medium dance tempo.",
        era="Dominican Republic, 1960s (bolero campesino); modern urban bachata from the 2000s",
        touchstones=("José Manuel Calderón", "Blas Durán", "Juan Luis Guerra - Bachata Rosa", "Antony Santos",
                     "Raulín Rodríguez", "Aventura", "Romeo Santos", "Prince Royce"),
        tempo=(120, 142),
        feel="straight 8ths, 4-beat dance with the tap on 4; derecho (verse) and majao/mambo (instrumental) grooves",
        swing=50,
        modes=("minor", "major"),
        keys=("A minor", "E minor", "D minor", "G major"),
        progressions=(
            "i-iv-V7-i",
            "i-VII-VI-V7",
            "i-iv-VII-III",
            "major: I-IV-V7-IV",
            "major: I-vi-IV-V7",
            "major: vi-IV-I-V",
        ),
        harmonic_rhythm=1,
        harmony="Simple bolero-derived harmony, I-IV-V7 and i-iv-V7, Andalusian descents in minor; the segunda "
                "guitar arpeggiates each chord; modern bachata uses pop 4-chord loops with added 9ths.",
        voicing="open",
        comping="arpeggio_updown",
        bass_style="syncopated",
        bass="Electric bass with a syncopated pattern: root on 1, a pickup on the 'and' of 2 into the 5th on 3, and "
             "a note on 4 that lines up with the dancers' tap; slides and walk-ups between chords; busier with "
             "octaves in the mambo section.",
        melody_density="busy",
        melody_scale="harmonic minor",
        melody="Requinto lead guitar plays fast arpeggios and 16th-note runs in 3rds and 6ths (the defining sound), "
               "between sung phrases; vocals emotional, high tenor, sobbing ornaments; repeated hook lines.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "guiro":      "X.xxX.xxX.xxX.xx",
            "high bongo": "x.o.x.o.x.o...o.",
            "low bongo":  "............X...",
        }},
        drums="Bongó plays a martillo-based pattern in the derecho (verse) with an open hembra tone on 4, then "
              "switches to cowbell (campana) on the beats in the mambo; güira (metal scraper) plays a long scrape "
              "and two short strokes per beat, louder in the mambo; modern bachata adds a soft kick on 1 and 3.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("mambo", 8), ("verse", 16), ("chorus", 8),
              ("mambo", 16), ("outro", 8)),
        instruments=("requinto guitar", "segunda (rhythm) guitar", "electric bass", "bongó", "güira", "lead vocal"),
        sound_design="Requinto: bright electric or steel-string guitar with chorus and a touch of delay; segunda "
                     "clean and plucked; electric bass round and punchy; güira bright metallic.",
        production="Guitars wide and bright, bass full, güira present but not harsh, vocal compressed and bright with "
                   "reverb; modern productions are polished and loud.",
        theory="The groove alternates sections: derecho (straight bongó) and mambo (cowbell, louder güira, "
               "busier bass); harmony stays bolero-simple while the requinto adds virtuosic arpeggiated colour.",
        mix=Mix(lufs=(-10, -7), lra=(4, 8), low_end="moderate", tone="bright", width="moderate"),
    ),
    Genre(
        name="merengue",
        family="latin",
        aliases=("merengue típico", "perico ripiao"),
        description="The Dominican national dance: a fast 2/4 driven by the two-headed tambora and a hissing "
                    "güira, with saxophone and accordion riffs and a big 'jaleo' call-and-response section.",
        era="Cibao region, Dominican Republic, 19th century; big-band merengue from the 1930s; 1980s pop boom",
        touchstones=("Ñico Lora", "Johnny Ventura", "Wilfrido Vargas", "Juan Luis Guerra y 4.40", "Fernando Villalona",
                     "Los Hermanos Rosario", "Elvis Crespo", "Tatico Henríquez"),
        tempo=(120, 165),
        meter="2/4",
        feel="fast, straight 2/4 with a march-like drive and a syncopated tambora",
        swing=50,
        modes=("major", "minor"),
        keys=("C major", "G major", "D major", "A minor"),
        progressions=(
            "I-V7-V7-I",
            "I-IV-V7-I",
            "I-I-V7-V7",
            "minor: i-iv-V7-i",
            "ii-V7-I-I",
        ),
        harmonic_rhythm=0.5,
        harmony="Very simple: tonic and dominant alternating every bar or two, IV for the chorus; piano or "
                "accordion plays fast syncopated chord riffs.",
        voicing="close",
        comping="offbeat",
        bass_style="syncopated",
        bass="Syncopated bass anticipating the beat: notes on beat 1 and the 'and' of 2 (pushing into the next "
             "bar), root-5th-octave shapes, with 16th pickups in the jaleo.",
        melody_density="busy",
        melody_scale="major",
        melody="Fast syllabic vocal lines and coros; alto saxes play rapid 16th-note jaleo riffs in 3rds; "
               "accordion (in típico) plays nonstop ornamented runs.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "guiro":         "X.xxX.xx|X.xxX.xx",
            "rim":           "x.xxx.x.|x.xxx.x.",
            "low floor tom": "......X.|....x.Xx",
            "open conga":    "......x.|......x.",
        }},
        drums="The tambora, a two-headed drum played with a stick on one side and the bare hand on the other: "
              "stick strokes on the wooden rim and head, open hand tones landing on the 'and' of 2, and the "
              "repique roll that ends every second bar; the güira plays a long stroke and two short ones per beat "
              "('chi-chiki'); conga reinforces the tambora's open tones.",
        form=(("intro", 8), ("paseo", 8), ("merengue (verse)", 32), ("jaleo", 32), ("sax mambo", 16),
              ("jaleo", 16), ("coda", 4)),
        instruments=("tambora", "güira", "alto and tenor saxophones", "accordion", "piano", "electric bass",
                     "trumpets", "conga", "lead vocal", "coro"),
        sound_design="Bright, metallic güira, punchy tambora, reedy saxes; 80s-90s merengue adds DX7 pianos and "
                     "synth brass.",
        production="Fast and bright, percussion forward, saxes and coros wide; loud, compressed masters in the "
                   "modern era.",
        theory="In 2/4 at high tempo, the tambora's syncopations and the bass's anticipations against a steady güira "
               "create the drive; sections (paseo, merengue, jaleo) are defined by groove and density, not harmony.",
        mix=Mix(lufs=(-10, -7), lra=(4, 8), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="cumbia",
        family="latin",
        aliases=("cumbia colombiana", "cumbia sonidera"),
        description="Colombia's coastal dance rhythm, now pan-Latin: a lilting two-beat pulse from tambora, "
                    "llamador and guacharaca under accordion or gaita melodies, slow enough to shuffle to.",
        era="Caribbean coast of Colombia, 19th century; orchestras in the 1950s; Mexico, Peru and Argentina since",
        touchstones=("Lucho Bermúdez", "Andrés Landero", "Los Corraleros de Majagual", "Los Ángeles Azules",
                     "Celso Piña", "Selena", "Los Destellos", "Totó la Momposina"),
        tempo=(85, 105),
        feel="cut-time two-step: bass on 1 and 3, llamador on 2 and 4, constant guacharaca 16ths",
        swing=50,
        modes=("major", "minor"),
        keys=("G major", "D major", "A minor", "E minor"),
        progressions=(
            "I-V7-V7-I",
            "I-IV-V7-I",
            "minor: i-iv-V7-i",
            "minor: i-VII-III-V7",
            "I-vi-IV-V7",
        ),
        harmonic_rhythm=0.5,
        harmony="Two- and three-chord harmony (I-V7, I-IV-V7) changing every bar or two; Andean and Peruvian "
                "cumbia (chicha) leans on minor keys and pentatonic guitar lines.",
        voicing="close",
        comping="offbeat",
        bass_style="root_fifth",
        bass="Root on beat 1 and 5th on beat 3 with a pickup 8th before each, in a steady 'boom...boom'; "
             "walk-ups between chords; it outlines I and V7 clearly.",
        melody_density="medium",
        melody_scale="major",
        melody="Singable diatonic melodies, accordion or gaita riffs answering the voice, short instrumental "
               "hooks repeated; Mexican cumbia uses synth or organ leads; vocals in 3rds.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.......x.......",
            "low conga":  "....x.......x...",
            "open conga": "..x..x.x..x..x.x",
            "guiro":      "X.xxX.xxX.xxX.xx",
        }},
        drums="Tambora (bass drum) on the strong beats, llamador (small drum) on the offbeat of the half-note pulse "
              "(beats 2 and 4 here), tambor alegre improvising on top, guacharaca (ridged scraper) playing a long "
              "stroke and two short ones every beat; modern bands add timbales, congas and güiro.",
        form=(("intro", 8), ("verse", 16), ("chorus", 16), ("instrumental", 16), ("verse", 16), ("chorus", 16),
              ("outro", 8)),
        instruments=("accordion", "gaita flutes", "electric bass", "tambor alegre", "llamador", "tambora",
                     "guacharaca", "congas", "lead vocal"),
        sound_design="Accordion with a reedy bite, gaita flutes for folkloric cumbia, round electric bass, "
                     "bright guacharaca; sonidera and chicha add organ, surf guitar and echo.",
        production="Warm and steady: bass and llamador carry the pulse, guacharaca high and wide, vocals "
                   "in front; moderate loudness.",
        theory="A cut-time feel with the 'and' of the half-note (beats 2 and 4) as the offbeat answer; the "
               "guacharaca's long-short-short subdivision supplies motion while harmony stays tonic-dominant.",
        mix=Mix(lufs=(-11, -8), lra=(5, 9), low_end="moderate", tone="warm", width="moderate"),
    ),
    # ------------------------------------------------------------- Brazil
    Genre(
        name="bossa nova",
        family="latin",
        aliases=("bossa",),
        parent="samba",
        description="Rio's quiet revolution: samba rhythm distilled onto a nylon-string guitar, with jazz harmony, "
                    "whispered vocals and a gently syncopated bossa clave.",
        era="Rio de Janeiro, 1958-1964",
        touchstones=("João Gilberto - Chega de Saudade", "Antônio Carlos Jobim", "Stan Getz & João Gilberto",
                     "Astrud Gilberto", "Vinicius de Moraes", "Baden Powell", "Nara Leão"),
        tempo=(115, 145),
        feel="straight, light syncopation: bossa clave over a 1-and-3 bass, played softly",
        swing=52,
        modes=("major", "minor"),
        keys=("F major", "C major", "D minor", "G major"),
        progressions=(
            "Imaj7-II7-ii7-V7",
            "Imaj7-vi7-ii7-V7",
            "ii7-V7-Imaj7-VI7",
            "Imaj7-bVII7-Imaj7-bII7",
            "minor: i7-iv7-bVII7-IIImaj7",
            "minor: iiø7-V7b9-i7-i7",
        ),
        harmonic_rhythm=1,
        harmony="Jazz-saturated: maj7, m7, 9ths, 13ths and altered dominants; chromatic inner-voice lines in "
                "the guitar, II7 (V7/V) as a colour chord, tritone subs (bII7), modulations by step; one or two "
                "chords per bar.",
        voicing="drop2",
        comping="bossa",
        bass_style="root_fifth",
        bass="Root on beat 1, 5th on beat 3 (often with a pickup 8th on the 'and' of 2 and 4), soft upright or "
             "the guitar's own thumb; never busy.",
        melody_density="medium",
        melody_scale="major",
        melody="Conversational, narrow-range melodies with many repeated notes and chromatic steps over moving "
               "harmony (the melody often sits on 9ths and 13ths); sung softly, close to speech; flute or sax "
               "in the gaps.",
        groove={"step": 0.25, "swing": 52, "pattern": {
            "side stick": "x.....x.....x...|....x.....x.....",
            "kick":       "x.....x.x.....x.|x.....x.x.....x.",
            "closed hat": "x.x.x.x.x.x.x.x.|x.x.x.x.x.x.x.x.",
        }},
        drums="Brushes or hi-hat in straight 8ths, kick on 1 and 3 with pickups (1, 2-and, 3, 4-and), cross-stick "
              "playing the bossa clave (3-2: 1, 2-and, 4 | 2-and, 4... i.e. the son clave with the last note "
              "delayed); very quiet; the guitar's batida (thumb bass, fingers on the partido-alto-derived "
              "syncopations) is the real rhythm section.",
        form=(("intro", 4), ("A", 16), ("A", 16), ("B", 16), ("A", 16), ("solo", 32), ("A", 16), ("coda", 8)),
        instruments=("nylon-string guitar", "upright bass", "brushed drums", "piano", "flute", "tenor saxophone",
                     "soft vocal", "strings"),
        sound_design="Close-miked nylon guitar, soft upright bass, brushes, gentle strings; breathy vocal close to "
                     "the mic.",
        production="Quiet, intimate and dynamic: little compression, natural room, vocal and guitar centre, "
                    "strings wide; nothing loud.",
        theory="Jobim and Gilberto put cool-jazz harmony on samba's rhythm: the guitar's thumb keeps the surdo "
               "pulse while the fingers play syncopations from the tamborim/partido-alto patterns; melodies are "
               "built on chord extensions and chromatic guide-tone lines.",
        mix=Mix(lufs=(-18, -14), lra=(8, 14), low_end="light", tone="warm", width="moderate"),
    ),
    Genre(
        name="samba",
        family="latin",
        aliases=("batucada", "samba enredo"),
        description="Brazil's carnival rhythm in 2/4: surdos pounding beat 2, rattling caixa and ganzá 16ths and "
                    "the tamborim's syncopated teleco-teco, under cavaquinho and singing choruses.",
        era="Rio de Janeiro, 1910s-30s (Estácio de Sá samba schools); pagode in the 1980s",
        touchstones=("Cartola", "Pixinguinha", "Noel Rosa", "Clara Nunes", "Beth Carvalho", "Martinho da Vila",
                     "Zeca Pagodinho", "Jorge Ben"),
        tempo=(95, 145),
        meter="2/4",
        feel="2/4 with a heavy beat 2 (surdo), forward-leaning 16ths",
        swing=54,
        modes=("major", "minor"),
        keys=("G major", "C major", "A minor", "D minor"),
        progressions=(
            "I-VI7-ii7-V7",
            "I-V7/ii-ii7-V7",
            "ii7-V7-I-I",
            "minor: i-V7-V7-i",
            "minor: i-iv7-V7-i",
            "I-I7-IV-iv",
        ),
        harmonic_rhythm=0.5,
        harmony="Choro-derived functional harmony: secondary dominants (VI7 = V7/ii, I7 = V7/IV), diminished "
                "passing chords, minor iv; one chord per 2/4 bar or per two bars; cavaquinho plays strummed "
                "syncopated chords.",
        voicing="close",
        comping="strum",
        bass_style="syncopated",
        bass="Bass (or 7-string guitar baixaria) follows the surdo: root on 1, strong 5th or root on 2, with "
             "16th pickups and descending counter-melodies in the baixaria.",
        melody_density="busy",
        melody_scale="major",
        melody="Syncopated vocal lines with many 16th-note anticipations; samba-enredo choruses sung by the whole "
               "school; cavaquinho fills, flute and 7-string guitar counter-melodies.",
        groove={"step": 0.25, "swing": 54, "pattern": {
            "low floor tom": "....X.......X...",
            "kick":          "o.......o.......",
            "snare":         "x.xxx.xxx.xxx.xx",
            "rim":           "x.x..x.x.x..x.x.",
            "shaker":        "ooxXooxXooxXooxX",
        }},
        drums="Bateria: surdo de primeira (lowest) on beat 2, surdo de segunda answering on beat 1, surdo de "
              "terceira (cortador) improvising; caixa (snare) 16ths with accents; tamborim playing the "
              "teleco-teco syncopation (here on rim); ganzá/chocalho shakers accenting the last 16th of each beat; "
              "agogô, cuíca and pandeiro on top.",
        form=(("intro", 8), ("verse", 16), ("refrão", 8), ("verse", 16), ("refrão", 8), ("bateria break", 8),
              ("refrão", 16)),
        instruments=("surdos", "caixa", "tamborim", "pandeiro", "cuíca", "agogô", "cavaquinho", "7-string guitar",
                     "vocals and choir"),
        sound_design="Bright cavaquinho, deep surdo booms, crackling caixa and tamborim; pagode adds banjo, "
                     "repique de mão and tan-tan.",
        production="Huge percussion section spread wide; surdo low and round under the bass; vocals and "
                   "cavaquinho in the centre.",
        theory="The emphasis on beat 2 of 2/4 (the surdo de primeira) and the 16-pulse tamborim timeline "
               "(x.x..x.x.x..x.x.) define samba; its anticipations ('síncope') lean the melody ahead of the beat.",
        mix=Mix(lufs=(-12, -9), lra=(5, 10), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="baile funk",
        family="latin",
        aliases=("funk carioca", "funk brasileiro", "favela funk"),
        description="Rio's favela party music: Miami-bass-descended drum machines turned into the tamborzão beat, "
                    "chanted MC vocals and stark sampled hooks at high volume.",
        era="Rio de Janeiro, late 1980s; tamborzão from the late 1990s; São Paulo funk and '150 BPM' in the 2010s",
        touchstones=("DJ Marlboro", "MC Marcinho", "Tati Quebra Barraco", "Furacão 2000", "DJ Malvado",
                     "MC Kevin o Chris", "Anitta", "DJ Rennan da Penha"),
        tempo=(125, 150),
        feel="straight, tresillo-based tamborzão, often double-time at 150",
        swing=50,
        modes=("minor", "phrygian"),
        keys=("A minor", "E minor", "F minor"),
        progressions=(
            "i-i-VII-VII",
            "i-iv",
            "phrygian: i-II",
            "i-VI-VII-i",
        ),
        harmonic_rhythm=0.5,
        harmony="Often none: a single sampled stab, a vocal chop or synth note on the tonic; when present, "
                "one or two minor chords.",
        voicing="power",
        comping="stabs",
        bass_style="808",
        bass="808 booms following the tamborzão kicks, long and distorted; or a tonic pedal note.",
        melody_density="sparse",
        melody_scale="minor pentatonic",
        melody="MC chants in short repeated phrases, chopped vocal samples and pitched-up hooks; melodies "
               "are rhythmic more than tuneful.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":     "x..x..x...x..x..",
            "clap":     "....x.......x...",
            "low conga": "...x..x.x..x..x.",
            "closed hat": "x.x.x.x.x.x.x.x.",
        }},
        drums="Tamborzão: drum-machine kicks and sampled atabaque/conga hits in a tresillo-shaped pattern "
              "(1, the 'a' of 1, the 'and' of 2, then the answering half); claps and vocal 'beatbox' samples; "
              "older funk used the Volt Mix 808 loops from Miami bass.",
        form=(("intro", 4), ("hook", 8), ("verse", 16), ("hook", 8), ("verse", 16), ("hook", 8), ("outro", 4)),
        instruments=("drum machine", "808", "atabaque samples", "vocal chops", "MC vocal"),
        sound_design="Raw, lo-fi samples, distorted 808, aggressive EQ, vocal chops and sound effects.",
        production="Extremely loud, minimal arrangement, drums and vocal only for long stretches; clipping is "
                   "part of the sound.",
        theory="Built on tresillo (3+3+2) like many Afro-diasporic grooves, but with no harmony to speak of: "
               "the music is rhythm plus voice.",
        mix=Mix(lufs=(-7, -5), lra=(3, 6), low_end="very heavy", tone="bright", width="moderate"),
    ),
    # ------------------------------------------------------------- Southern Cone, Spain
    Genre(
        name="tango",
        family="latin",
        aliases=("tango argentino", "nuevo tango"),
        description="Buenos Aires' dramatic dance music: bandoneón, violins, piano and bass marking every beat "
                    "(marcato) or the 3-3-2 síncopa, with sweeping minor-key melodies and sudden stops.",
        era="Río de la Plata (Buenos Aires and Montevideo), 1880s-1910s; golden age 1935-1955; nuevo tango 1950s on",
        touchstones=("Carlos Gardel", "Juan D'Arienzo", "Osvaldo Pugliese", "Aníbal Troilo", "Carlos Di Sarli",
                     "Astor Piazzolla", "Gotan Project"),
        tempo=(100, 130),
        feel="marcato en cuatro (four accented beats) alternating with síncopa (3-3-2), with arrastre drags",
        swing=50,
        modes=("minor", "harmonic minor", "major"),
        keys=("D minor", "A minor", "E minor", "G minor"),
        progressions=(
            "i-iv-V7-i",
            "i-VII-VI-V",
            "i-V7/iv-iv-V7",
            "i-VI-iiø7-V7",
            "major: I-V7-V7-I",
        ),
        harmonic_rhythm=1,
        harmony="Minor keys with harmonic-minor dominants, the Andalusian descent i-VII-VI-V, secondary dominants "
                "and diminished 7ths for drama; contrasting major-key trio sections; Piazzolla adds jazz and "
                "classical extensions and chromatic bass lines.",
        voicing="close",
        comping="quarters",
        bass_style="root_fifth",
        bass="Contrabass and piano left hand play the marcato on all four beats or on 1 and 3, then the 3-3-2 "
             "síncopa; arrastre (a slide or drag into the beat); strong pizzicato and string slaps.",
        melody_density="medium",
        melody_scale="harmonic minor",
        melody="Long legato violin or vocal lines against staccato accompaniment, rubato phrases, dramatic leaps "
               "and chromatic appoggiaturas; bandoneón variaciones (fast 16th-note runs) near the end.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick": "X...x...X...x...|X.....X.....X...",
            "rim":  "...o...o...o...o|................",
        }},
        drums="No drums: rhythm comes from bandoneones, piano and bass. The lanes map the orchestra: bar 1 is "
              "the marcato in four with arrastre (a drag leading into each beat), bar 2 the síncopa (3-3-2). "
              "Percussive effects (chicharra, látigo, golpe on the bass body) add colour. Electro-tango uses "
              "a soft programmed kit.",
        form=(("intro", 4), ("A", 16), ("B", 16), ("A", 16), ("trio (C)", 16), ("A", 16), ("variación", 8),
              ("coda", 2)),
        instruments=("bandoneón", "violins", "piano", "contrabass", "viola and cello", "voice"),
        sound_design="Reedy bandoneón, gritty bowed strings, percussive piano, slapped bass; vintage records are "
                     "mono and narrow.",
        production="Highly dynamic orchestral balance, dramatic crescendos and stops; minimal compression; "
                   "room reverb.",
        theory="Rhythmically built on the habanera and the 3-3-2 síncopa (tresillo); harmonically on minor "
               "keys with harmonic-minor V7 and the Andalusian cadence; the signature ending is the "
               "V-i 'chan-chan'.",
        mix=Mix(lufs=(-18, -13), lra=(10, 16), low_end="light", tone="warm", width="wide"),
    ),
    Genre(
        name="flamenco",
        family="latin",
        aliases=("bulerías", "soleá", "flamenco puro"),
        description="Andalusian song, guitar and dance built on 12-beat compás cycles: rasgueado guitar in "
                    "phrygian dominant, palmas and cajón accenting 3, 6, 8, 10 and 12, and raw cante.",
        era="Andalusia, Spain, late 18th-19th century; modern guitar from the 1960s-70s (Paco de Lucía)",
        touchstones=("Paco de Lucía", "Camarón de la Isla", "Tomatito", "Vicente Amigo", "Enrique Morente",
                     "Niño Ricardo", "Rosalía - El mal querer"),
        tempo=(60, 135),
        meter="12/8",
        feel="12-beat compás accented on 3, 6, 8, 10, 12 (soleá slow, bulerías fast); tempo is per quarter = 2 counts",
        swing=50,
        modes=("phrygian dominant", "minor", "major"),
        keys=("E phrygian dominant", "A phrygian dominant", "F# phrygian dominant"),
        progressions=(
            "iv-bIII-II-I",
            "I-II-bIII-II",
            "I7-iv-bIII-II-I",
            "II-I-II-I",
            "minor: i-VII-VI-V",
            "major: I-IV-V7-I",
        ),
        harmonic_rhythm=2,
        harmony="The Andalusian cadence resolves to a major tonic (in E: Am-G-F-E = iv-bIII-II-I in phrygian "
                "dominant). 'Por arriba' is the E position, 'por medio' the A position. The flat 2nd chord (II) "
                "is the main tension; I7 tonicises iv; guitarists add open-string dissonances (F with an open E, "
                "Fmaj7#11 colours). Alegrías and guajiras use major keys with I-IV-V7.",
        voicing="open",
        comping="strum",
        bass_style="pedal",
        bass="No bass player traditionally: the guitar thumb plays bass lines and pedals on the open strings; "
             "modern groups add an electric or acoustic bass following the guitar's chord roots on the accents.",
        melody_density="busy",
        melody_scale="phrygian dominant",
        melody="Cante is melismatic and microtonal-sounding, stepwise around the 1st, b2 and 3rd of phrygian "
               "dominant, with ornaments (quejíos); guitar falsetas are picado (fast alternate-picked scales) "
               "and arpeggio passages ending on the compás accents.",
        groove={"step": 0.5, "swing": 50, "pattern": {
            "clap":  "o.Xo.XoXoX.X",
            "kick":  "..x......x..",
            "snare": ".o.o.x.x.o.x",
        }},
        drums="Palmas (handclaps: claras bright, sordas muted) mark the compás accents on 3, 6, 8, 10 and 12; "
              "the cajón plays bass tones and slaps on the same accents with ghost notes; jaleo shouts and "
              "zapateado footwork add rhythm; castanets only in some dance styles.",
        form=(("intro (salida)", 2), ("falseta", 2), ("letra", 4), ("falseta", 2), ("letra", 4),
              ("escobilla", 4), ("remate", 1)),
        instruments=("flamenco guitar", "cante (voice)", "palmas", "cajón", "zapateado", "bass", "flute"),
        sound_design="Bright, percussive flamenco guitar (cypress, low action, golpe taps), dry palmas, woody cajón, "
                     "intimate voice.",
        production="Natural and dynamic, close-miked guitar and voice, palmas wide; modern productions add reverb "
                   "and a little compression.",
        theory="Phrygian dominant tonality where the 'tonic' sounds like a dominant; the 12-beat compás "
               "(3+3+2+2+2 hemiola shape: 12-1-2 3 | 4-5 6 | 7 8 | 9 10 | 11 12) underlies soleá, alegrías and "
               "bulerías; the cadence on 10 closes every phrase.",
        mix=Mix(lufs=(-17, -12), lra=(9, 15), low_end="light", tone="warm", width="moderate"),
    ),
    # ------------------------------------------------------------- Pan-Latin
    Genre(
        name="latin pop",
        family="latin",
        aliases=("pop latino",),
        parent="pop",
        description="Spanish-language pop with Latin rhythm in the drums: big singable choruses over reggaeton, "
                    "flamenco-guitar or salsa-tinged grooves, polished for radio.",
        era="Miami, Mexico City and Madrid, 1990s; reggaeton-pop crossover from 2017",
        touchstones=("Gloria Estefan", "Ricky Martin", "Shakira", "Enrique Iglesias", "Luis Fonsi", "Juanes",
                     "Camila Cabello", "Sebastián Yatra"),
        tempo=(88, 125),
        feel="pop backbeat or light dembow, straight 16ths with Latin percussion",
        swing=50,
        modes=("minor", "major"),
        keys=("B minor", "A minor", "E minor", "G major"),
        progressions=(
            "i-VI-III-VII",
            "major: vi-IV-I-V",
            "major: I-V-vi-IV",
            "i-VII-VI-V",
            "i-iv-VII-III",
        ),
        harmonic_rhythm=1,
        harmony="Pop four-chord loops; Andalusian descents for a Spanish flavour; modulation up a step for the "
                "last chorus in ballads.",
        voicing="open",
        comping="strum",
        bass_style="syncopated",
        bass="Syncopated pop bass or 808 following the kick; tresillo pushes (1, 'a' of 1, 'and' of 2) in "
             "reggaeton-pop; tumbao-style anticipations in salsa-pop.",
        melody_density="medium",
        melody_scale="minor",
        melody="Big, singable chorus hooks, pre-chorus lift, verse in a lower register; Spanish phrasing with "
               "syllables on the 16th grid; nylon guitar or trumpet hooks.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x...x...x...x...",
            "snare":      "....x.......x...",
            "rim":        "...x..x....x..x.",
            "shaker":     "xoxoxoxoxoxoxoxo",
            "open conga": "..x.......x..x..",
        }},
        drums="Pop kit or programmed beats with the dembow snare tucked in on rim, congas and shakers; "
              "acoustic percussion layers (bongó, timbales fills) for authenticity.",
        form=(("intro", 8), ("verse", 16), ("pre-chorus", 8), ("chorus", 16), ("verse", 16), ("pre-chorus", 8),
              ("chorus", 16), ("bridge", 8), ("chorus", 16), ("outro", 8)),
        instruments=("nylon guitar", "drums", "bass or 808", "synth pad", "congas", "brass", "lead vocal"),
        sound_design="Clean nylon guitar, glossy synths, punchy drums, bright vocals; brass stabs and "
                     "pan flutes as hooks.",
        production="Radio-polished: loud, bright, vocal forward, wide stereo pads; tight low end.",
        theory="Pop song form fused with Latin rhythmic cells (tresillo, clave, dembow) and Spanish harmonic "
               "colour (Andalusian cadence, harmonic-minor V).",
        mix=Mix(lufs=(-9, -7), lra=(4, 7), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="latin jazz",
        family="latin",
        aliases=("afro-cuban jazz", "cubop"),
        parent="mambo",
        description="Jazz harmony and improvisation on Afro-Cuban rhythm: bebop heads and modal vamps over clave, "
                    "conga tumbao, cascara and montuno piano.",
        era="New York, 1940s (Machito, Mario Bauzá, Dizzy Gillespie and Chano Pozo); Cuba (Irakere) in the 1970s",
        touchstones=("Dizzy Gillespie & Chano Pozo - Manteca", "Machito", "Tito Puente", "Mongo Santamaría",
                     "Cal Tjader", "Eddie Palmieri", "Irakere", "Chucho Valdés", "Michel Camilo"),
        tempo=(120, 230),
        feel="clave (2-3), straight 8ths; mambo, cha-cha, songo or 6/8 bembé grooves",
        swing=50,
        modes=("minor", "dorian", "major"),
        keys=("F minor", "C minor", "Bb major", "Eb major"),
        progressions=(
            "i7-iv7-i7-V7b9",
            "iiø7-V7b9-i7-i7",
            "dorian: i7-IV7",
            "major: ii7-V7-Imaj7-VI7",
            "i7-bII7-i7-bII7",
            "major: Imaj7-bIIImaj7-bVImaj7-bIImaj7",
        ),
        harmonic_rhythm=1,
        harmony="Bebop ii-V and modal vamps; montuno sections on a 2-chord vamp (i7-IV7 dorian, i7-bII7); "
                "altered dominants, quartal piano voicings, McCoy-style 4ths over the clave.",
        voicing="quartal",
        comping="montuno",
        bass_style="tumbao",
        bass="Tumbao on the 'and' of 2 and beat 4 under the montuno, walking in swing passages, unison riffs "
             "with the piano in the head.",
        melody_density="busy",
        melody_scale="dorian",
        melody="Bebop-style heads phrased in clave, horn riffs, long improvised solos over vamps; the piano solo "
               "mixes montuno patterns with jazz lines.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "claves":     RUMBA_23,
            "ride":       CASCARA_23,
            "kick":       "............o...|......x.....x...",
            "slap conga": "o.o.X.o.o.o.....|o.o.X.o.o.o.....",
            "open conga": "............x.x.|............x...",
            "low conga":  "................|..............x.",
        }},
        drums="Drum kit plus congas (and often timbales and bongó): ride or shell plays cascara or the mambo bell, "
              "kick on the bombo (the 'and' of 2 on the 3-side) and ponche (beat 4), hi-hat or foot cowbell on "
              "beats or 2 and 4, rumba clave on a woodblock pedal; congas play tumbao or songo patterns.",
        form=(("intro", 8), ("head", 32), ("solos over montuno", 64), ("mambo", 16), ("head", 32), ("coda", 8)),
        instruments=("piano", "upright or electric bass", "drum kit", "congas", "timbales", "trumpet",
                     "saxophone", "trombone", "flute", "vibraphone"),
        sound_design="Acoustic jazz instruments with bright brass, vibes and flute; live percussion with room.",
        production="Live ensemble balance, wide stereo percussion, dynamic solos; light compression.",
        theory="Jazz improvisation over a clave-based rhythm section: the soloist can play across the beat "
               "but arrangers write hits 'in clave'; montuno vamps turn bebop changes into modal platforms.",
        mix=Mix(lufs=(-15, -11), lra=(8, 14), low_end="moderate", tone="bright", width="wide"),
    ),
    # ------------------------------------------------------------- Mexico
    Genre(
        name="mariachi",
        family="latin",
        aliases=("son jalisciense", "ranchera"),
        description="Mexico's string-and-trumpet ensemble: vihuela and guitarrón driving sesquialtera rhythms "
                    "(6/8 against 3/4), soaring violins and trumpets, and full-voiced ranchera singing.",
        era="Jalisco, Mexico, 19th century; modern trumpet mariachi from the 1930s-50s (Mariachi Vargas)",
        touchstones=("Mariachi Vargas de Tecalitlán", "Pedro Infante", "Jorge Negrete", "José Alfredo Jiménez",
                     "Vicente Fernández", "Lola Beltrán", "Linda Ronstadt - Canciones de mi padre"),
        tempo=(150, 200),
        meter="6/8",
        feel="sesquialtera: bars of 6/8 (3+3) alternating with 3/4 (2+2+2); tempo per quarter (dotted quarter ~100-135)",
        swing=50,
        modes=("major", "minor"),
        keys=("D major", "G major", "A major", "C major"),
        progressions=(
            "I-V7-V7-I",
            "I-IV-V7-I",
            "I-I7-IV-V7",
            "minor: i-iv-V7-i",
            "I-V7/V-V7-I",
        ),
        harmonic_rhythm=0.5,
        harmony="Diatonic tonic-dominant harmony in bright keys, I7 to IV for the bridge, secondary dominant V7/V; "
                "violins and trumpets harmonise in parallel 3rds and 6ths.",
        voicing="close",
        comping="strum",
        bass_style="root_fifth",
        bass="Guitarrón (big acoustic bass) plays roots and 5ths on the strong beats of each grouping, often in "
             "octaves, pinching two strings; it marks the 6/8-3/4 alternation.",
        melody_density="medium",
        melody_scale="major",
        melody="Wide-ranging, operatic vocal lines with held climactic notes and falsetto breaks (in huapango); "
               "trumpets and violins play introductions and interludes in 3rds; gritos (shouts) between phrases.",
        groove={"step": 0.5, "swing": 50, "pattern": {
            "kick":   "x..x..|x.x.x.",
            "clap":   ".xx.xx|.x.x.x",
            "shaker": "xoxxox|xoxoxo",
        }},
        drums="No drum kit: the vihuela's rasgueado (bright strummed patterns) and the guitarrón are the rhythm "
              "section. The lanes map them (kick = guitarrón, clap/shaker = vihuela strokes): bar 1 groups 3+3, "
              "bar 2 groups 2+2+2. If programmed, keep them quiet or replace with strummed guitars; zapateado "
              "footwork adds accents in sones.",
        form=(("intro", 8), ("verse", 16), ("interlude", 8), ("verse", 16), ("chorus", 16), ("coda", 4)),
        instruments=("vihuela", "guitarrón", "guitar", "violins", "trumpets", "harp", "lead vocal"),
        sound_design="Bright acoustic strings, brassy trumpets with vibrato, guitarrón boom, vihuela's high, "
                     "percussive strum.",
        production="Live-room ensemble: trumpets and violins wide, vocal in front with reverb, strong dynamics; "
                   "the guitarrón supplies the low end.",
        theory="The sesquialtera (hemiola between 6/8 and 3/4) is the core rhythmic idea; rancheras may be in 3/4 "
               "(valseada), 2/4 (polka) or 4/4 (bolero ranchero).",
        mix=Mix(lufs=(-14, -10), lra=(7, 12), low_end="light", tone="bright", width="wide"),
    ),
    Genre(
        name="regional mexican",
        family="latin",
        aliases=("música mexicana", "norteño", "banda sinaloense", "corridos tumbados"),
        description="Northern and Pacific Mexican popular music: accordion-and-bajo-sexto norteño, brass-band "
                    "banda and modern corridos, mostly polka 2/4 'oom-pah' or 3/4 waltz rhythms.",
        era="Northern Mexico and Texas border, early 20th century; banda from Sinaloa; corridos tumbados 2018-",
        touchstones=("Los Tigres del Norte", "Ramón Ayala", "Chalino Sánchez", "Banda El Recodo",
                     "Los Tucanes de Tijuana", "Natanael Cano", "Peso Pluma", "Grupo Frontera"),
        tempo=(90, 145),
        meter="2/4",
        feel="polka 'oom-pah': bass on the beats, snare and chords on the offbeats",
        swing=50,
        modes=("major", "minor"),
        keys=("G major", "C major", "F major", "A minor"),
        progressions=(
            "I-V7-V7-I",
            "I-IV-V7-I",
            "I-I7-IV-V7",
            "minor: i-iv-V7-i",
            "minor: i-VI-VII-i",
        ),
        harmonic_rhythm=0.5,
        harmony="Tonic and dominant over long stretches (two bars each), IV for contrast; corridos tumbados add "
                "minor keys, sus2 colours and trap-influenced loops on requinto.",
        voicing="close",
        comping="offbeat",
        bass_style="root_fifth",
        bass="Root-fifth alternation on beats 1 and 2 (electric bass in norteño, tuba or sousaphone in banda), "
             "with chromatic walk-ups between chords; in corridos tumbados an acoustic tololoche or bass.",
        melody_density="medium",
        melody_scale="major",
        melody="Narrative vocal lines (corridos tell stories), in 3rds with a second voice; accordion or clarinet "
               "plays fast ornamented interludes; requinto 12-string runs in corridos tumbados.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":  "x...x...x...x...",
            "snare": "..x...x...x...x.",
            "crash": "..............x.",
        }},
        drums="Norteño: drum kit with kick on the beats and snare on the offbeats (polka), fills into each verse. "
              "Banda: tambora (bass drum with cymbal) and tarola (snare) doing the same with more volume. "
              "Corridos tumbados often have no drums at all, just guitars and bass.",
        form=(("intro", 8), ("verse", 16), ("interlude", 8), ("verse", 16), ("interlude", 8), ("verse", 16),
              ("outro", 4)),
        instruments=("button accordion", "bajo sexto", "electric bass or tuba", "drum kit", "clarinets",
                     "trumpets", "trombones", "requinto guitar", "lead vocal"),
        sound_design="Reedy button accordion, jangly bajo sexto, huge brass for banda, crisp 12-string requinto in "
                     "corridos.",
        production="Bright and forward, vocal very present, accordion or brass wide; modern regional is loud and "
                   "polished.",
        theory="European polka and waltz rhythms (via Czech and German immigrants) on Mexican song forms; "
               "harmony stays diatonic so the storytelling carries the song.",
        mix=Mix(lufs=(-10, -7), lra=(5, 9), low_end="heavy", tone="bright", width="moderate"),
    ),
    # ------------------------------------------------------------- Jamaica
    Genre(
        name="ska",
        family="caribbean",
        aliases=("jamaican ska", "first-wave ska"),
        description="Jamaica's first pop music: an up-tempo shuffle with guitar and piano chopping every offbeat, "
                    "a walking bass and riffing horns.",
        era="Kingston, Jamaica, 1959-1966",
        touchstones=("The Skatalites", "Prince Buster", "Desmond Dekker", "Millie Small", "Toots and the Maytals",
                     "Don Drummond", "The Wailers (early)"),
        tempo=(105, 150),
        feel="shuffle; chords on every offbeat ('and'), snare on 2 and 4",
        swing=60,
        modes=("major", "minor"),
        keys=("Bb major", "F major", "C major", "G minor"),
        progressions=(
            "I-IV-V7-IV",
            "I-vi-IV-V7",
            "I-I-IV-V7",
            "minor: i-iv-V7-i",
            "I-V7-I-V7",
        ),
        harmonic_rhythm=1,
        harmony="R&B and calypso-derived diatonic changes, I-IV-V and I-vi-IV-V; horn sections voice in close "
                "4-part harmony; minor-key instrumentals (Skatalites) use jazz vamps.",
        voicing="close",
        comping="offbeat",
        bass_style="walking",
        bass="Walking upright or electric bass in quarter notes, outlining the chord with passing tones; "
             "a shuffle feel.",
        melody_density="medium",
        melody_scale="major",
        melody="Horn-section heads (trumpet, trombone, tenor sax) in unison or harmony, R&B-style vocals, jazz "
               "solos over the changes.",
        groove={"step": 0.25, "swing": 60, "pattern": {
            "kick":       "x.......x.......",
            "snare":      "....x.......x...",
            "ride":       "x.x.x.x.x.x.x.x.",
            "closed hat": "..x...x...x...x.",
        }},
        drums="Shuffle drums (Lloyd Knibb): snare or rim on 2 and 4, kick on 1 and 3, ride and hi-hat swinging "
              "8ths with the hat accenting the offbeats with the guitar; fills on snare.",
        form=(("intro", 8), ("head", 16), ("verse", 16), ("chorus", 8), ("solo", 16), ("head", 16), ("outro", 8)),
        instruments=("electric guitar", "piano", "upright or electric bass", "drums", "trumpet", "trombone",
                     "tenor saxophone", "vocals"),
        sound_design="Choppy, trebly guitar and piano upstrokes, warm horns, upright bass; vintage studio room.",
        production="Studio One / Treasure Isle sound: live, warm, mono or narrow, horns and vocals forward.",
        theory="American R&B shuffle turned inside out: the chord stab moves to the offbeat, inverting the "
               "emphasis; the walking bass keeps the jazz connection.",
        mix=Mix(lufs=(-13, -9), lra=(6, 10), low_end="moderate", tone="bright", width="moderate"),
    ),
    Genre(
        name="rocksteady",
        family="caribbean",
        aliases=("rock steady",),
        parent="ska",
        description="The cool, slow bridge between ska and reggae: relaxed tempos, a melodic and prominent bass, "
                    "close vocal harmony and offbeat guitar.",
        era="Kingston, Jamaica, 1966-1968",
        touchstones=("Alton Ellis", "The Paragons", "Phyllis Dillon", "The Techniques", "Ken Boothe",
                     "The Heptones", "Duke Reid's Treasure Isle"),
        tempo=(72, 100),
        feel="slow, relaxed, lightly swung; skank on 2 and 4 and the first one-drop drums",
        swing=56,
        modes=("major", "minor"),
        keys=("C major", "F major", "G major", "A minor"),
        progressions=(
            "I-vi-IV-V7",
            "I-IV-I-V7",
            "ii7-V7-I-vi7",
            "minor: i-iv-VII-III",
            "I-iii-IV-V7",
        ),
        harmonic_rhythm=1,
        harmony="Soul-influenced (Curtis Mayfield, Impressions): I-vi-IV-V, ii-V, 7th chords; love-song harmony "
                "with vocal-group voicings.",
        voicing="close",
        comping="skank",
        bass_style="one_drop",
        bass="The bass becomes the lead: melodic repeating riffs with rests, often avoiding beat 1, syncopated "
             "and heavy (Jackie Jackson, Lloyd Brevett).",
        melody_density="medium",
        melody_scale="major",
        melody="Smooth lead vocals with trio harmonies in the chorus (Impressions-style), simple memorable "
               "melodies; guitar or horn lines answer.",
        groove={"step": 0.25, "swing": 56, "pattern": {
            "kick":       "x.......x.......",
            "side stick": "........x.......",
            "closed hat": "x.x.x.x.x.x.x.x.",
            "open hat":   "......x.......x.",
        }},
        drums="Laid-back: cross-stick on beat 3 (the early one drop), kick on 1 and 3, hi-hat 8ths with an open "
              "hat lift; very few fills.",
        form=(("intro", 4), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("solo", 8),
              ("chorus", 8), ("outro", 4)),
        instruments=("electric bass", "electric guitar", "piano or organ", "drums", "lead vocal",
                     "harmony vocals", "horns"),
        sound_design="Warm, round bass, clean choppy guitar, organ bubble, soft horns; vintage plate reverb.",
        production="Bass louder than in ska, warm and mid-focused, vocals forward; mono/narrow stereo.",
        theory="Halving ska's tempo leaves space: the bass moves from walking to riffing, and the drums start "
               "dropping beat 1, foreshadowing reggae's one drop.",
        mix=Mix(lufs=(-14, -10), lra=(6, 10), low_end="heavy", tone="warm", width="narrow"),
    ),
    Genre(
        name="reggae",
        family="caribbean",
        aliases=("roots reggae",),
        parent="rocksteady",
        description="Jamaica's heartbeat: the one-drop drum beat, a deep melodic bass, guitar skank on 2 and 4 and "
                    "organ bubble, carrying roots, spiritual and protest songs.",
        era="Kingston, Jamaica, 1968 onwards; roots era 1970s",
        touchstones=("Bob Marley & the Wailers", "Peter Tosh", "Burning Spear", "Toots and the Maytals",
                     "Culture", "Gregory Isaacs", "Sly & Robbie", "Aston 'Family Man' Barrett"),
        tempo=(60, 90),
        feel="one drop: kick and rim together on beat 3, skank on 2 and 4, lightly swung 8ths",
        swing=58,
        modes=("minor", "major", "dorian"),
        keys=("A minor", "E minor", "G major", "D minor"),
        progressions=(
            "i-iv",
            "i-VII",
            "dorian: i-IV",
            "i-VI-VII-i",
            "major: I-IV-V-IV",
            "major: I-vi-IV-V",
        ),
        harmonic_rhythm=1,
        harmony="Two-chord vamps (i-iv, i-VII, dorian i-IV) and simple I-IV-V; triads and minor 7ths, voiced "
                "high and short; the riddim matters more than the changes.",
        voicing="close",
        comping="skank",
        bass_style="one_drop",
        bass="Deep, round melodic riffs that repeat every one or two bars, often leaving beat 1 empty or "
             "landing on beat 3 with the drop; root, 5th, octave and passing tones; it is the hook.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="Relaxed, behind-the-beat vocal phrasing, call-and-response harmonies (I-Threes), pentatonic "
               "melodies; melodica or horn riffs.",
        groove={"step": 0.25, "swing": 58, "pattern": {
            "kick":       "........x.......",
            "side stick": "........x.......",
            "closed hat": "x.x.x.x.x.x.x.x.",
        }},
        drums="The one drop: nothing on beat 1, kick and cross-stick (or snare) together on beat 3, hi-hat 8ths "
              "swung with open-hat accents; variants are the rockers (kick on every beat) and steppers "
              "(four-on-the-floor); fills are short tom rolls.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("dub break", 16),
              ("chorus", 8), ("outro", 8)),
        instruments=("electric bass", "drums", "rhythm guitar", "organ", "piano", "lead guitar", "horns",
                     "vocals and harmonies"),
        sound_design="Fat, round bass with the highs rolled off, short trebly guitar skank, organ 'bubble' "
                     "(8th-note shuffle on the offbeats), spring reverb and tape delay.",
        production="Bass and drums dominate, guitar thin and dry, organ in the background, vocal in front with "
                   "plate reverb; warm and dynamic.",
        theory="The emphasis is on beat 3 and the offbeats: the one drop leaves the downbeat empty, the skank "
               "marks 2 and 4 (the 'and's at double-time), and the bass riff fills the space.",
        mix=Mix(lufs=(-12, -9), lra=(5, 9), low_end="very heavy", tone="warm", width="moderate"),
    ),
    Genre(
        name="dub",
        family="caribbean",
        aliases=("dub reggae",),
        parent="reggae",
        description="Reggae remixed into space: instrumental riddims stripped back to drums and bass, with "
                    "echo, spring reverb and filters played live on the mixing desk.",
        era="Kingston, Jamaica, late 1960s-70s (King Tubby, Lee Perry); UK dub from the late 1970s",
        touchstones=("King Tubby", "Lee 'Scratch' Perry", "Scientist", "Augustus Pablo - King Tubbys Meets Rockers "
                     "Uptown", "Prince Jammy", "Mad Professor", "Keith Hudson"),
        tempo=(60, 85),
        feel="one drop, half the instruments muted at any time, delays in dotted 8ths",
        swing=58,
        modes=("minor", "dorian"),
        keys=("A minor", "E minor", "G minor"),
        progressions=(
            "i-iv",
            "i-VII",
            "dorian: i-IV",
            "i-VI-VII-i",
        ),
        harmonic_rhythm=0.5,
        harmony="Inherited from the reggae riddim: one or two chords; chords are mostly muted and appear as "
                "echoing fragments.",
        voicing="close",
        comping="skank",
        bass_style="one_drop",
        bass="The bass riddim is the centre, louder than anything else, deep and round, with rests; "
             "repeated for the whole track.",
        melody_density="sparse",
        melody_scale="minor pentatonic",
        melody="Fragments: vocal snippets thrown into echo, melodica phrases, a horn line that drops in and out.",
        groove={"step": 0.25, "swing": 58, "pattern": {
            "kick":       "........x.......",
            "rim":        "........x.......",
            "closed hat": "..x...x...x...x.",
            "snare":      "............o...",
        }},
        drums="One-drop or rockers drums with a reverb-drenched snare, hi-hats through tape delay, drum dropouts "
              "and sudden returns; the engineer mutes and unmutes elements in real time.",
        form=(("intro", 8), ("riddim", 16), ("drop to drum and bass", 16), ("echo break", 8), ("riddim", 16),
              ("outro", 8)),
        instruments=("bass", "drums", "skank guitar", "organ", "melodica", "tape delay", "spring reverb",
                     "vocal fragments"),
        sound_design="Spring reverb crashes, tape-echo feedback swells, high-pass filter sweeps (Tubby's filter), "
                     "phaser; deep sub-heavy bass.",
        production="The mixing desk is the instrument: mute/unmute, send throws to delay and reverb, filter "
                   "sweeps; huge dynamic contrasts and space.",
        theory="Arrangement by subtraction: the song is deconstructed so rhythm and space become the content; "
               "dotted-8th delays create polyrhythm against the one drop.",
        mix=Mix(lufs=(-13, -9), lra=(7, 13), low_end="very heavy", tone="dark", width="wide"),
    ),
    Genre(
        name="dancehall",
        family="caribbean",
        aliases=("ragga", "raggamuffin"),
        parent="reggae",
        description="Jamaica's digital party music: deejays toasting over sparse, hard-hitting digital riddims, "
                    "from Sleng Teng's Casio bass to modern syncopated club beats.",
        era="Kingston, late 1970s-80s; digital from 1985 (Under Mi Sleng Teng); global in the 2000s",
        touchstones=("Yellowman", "King Jammy", "Shabba Ranks", "Steely & Clevie", "Beenie Man", "Bounty Killer",
                     "Sean Paul", "Vybz Kartel", "Popcaan"),
        tempo=(88, 110),
        feel="straight or slightly swung, syncopated riddim with tresillo (dembow) accents",
        swing=52,
        modes=("minor", "major"),
        keys=("F minor", "G minor", "A minor", "C minor"),
        progressions=(
            "i-i-VII-VII",
            "i-VI-VII-i",
            "i-iv",
            "i-VI-III-VII",
            "major: I-IV-V-IV",
        ),
        harmonic_rhythm=0.5,
        harmony="Minimal: riddims built on one to four minor chords, often a single synth riff; the riddim is "
                "shared by many deejays.",
        voicing="close",
        comping="stabs",
        bass_style="syncopated",
        bass="Synth bass riddim: a syncopated, repeating 1-2 bar riff, heavy sub; Sleng Teng-style Casio bass "
             "or modern 808.",
        melody_density="busy",
        melody_scale="minor pentatonic",
        melody="Deejay chatting/toasting in rhythmic patois flows, sing-jay hooks, chants; melodic content is "
               "mostly in the vocal.",
        groove={"step": 0.25, "swing": 52, "pattern": {
            "kick":       "x.....x.x.......",
            "clap":       "....x.......x...",
            "rim":        "...x..x....x..x.",
            "closed hat": "x.x.x.x.x.x.x.x.",
        }},
        drums="Drum machine riddims: kick on 1 and the 'and' of 2 into 3, snare/clap on 2 and 4 and the "
              "dembow figure (from Steely & Clevie's 'Poco Man Jam') on rim or tom; modern riddims (Diwali, "
              "Coolie Dance) use 3+3+2 handclaps.",
        form=(("intro", 4), ("hook", 8), ("verse", 16), ("hook", 8), ("verse", 16), ("hook", 8), ("outro", 4)),
        instruments=("drum machine", "synth bass", "synth stab", "riddim samples", "deejay vocal"),
        sound_design="Bright digital drums, heavy synth bass, stabby synths, sirens and air-horn FX, "
                     "soundsystem dub plates.",
        production="Loud and punchy, bass heavy, vocal in front; riddim versions are released for many artists.",
        theory="The riddim system: one instrumental, many songs; rhythmically built on tresillo-based "
               "syncopation against a backbeat.",
        mix=Mix(lufs=(-8, -6), lra=(3, 6), low_end="very heavy", tone="bright", width="moderate"),
    ),
    # ------------------------------------------------------------- Trinidad and the French Antilles
    Genre(
        name="calypso",
        family="caribbean",
        aliases=("kaiso",),
        description="Trinidad's carnival song: witty, topical lyrics sung over a bouncy 2-feel with strummed "
                    "guitars, horns, and a bass pushing the syncopation.",
        era="Trinidad and Tobago, early 20th century; golden age 1940s-60s",
        touchstones=("Lord Kitchener", "Mighty Sparrow", "Roaring Lion", "Lord Invader", "Lord Melody",
                     "Harry Belafonte - Calypso", "Calypso Rose"),
        tempo=(100, 130),
        feel="bouncy cut-time 2-feel, straight 8ths with syncopated pushes",
        swing=50,
        modes=("major",),
        keys=("F major", "C major", "G major", "Bb major"),
        progressions=(
            "I-V7-V7-I",
            "I-IV-V7-I",
            "I-vi-ii-V7",
            "I-I7-IV-V7",
            "ii-V7-I-I",
        ),
        harmonic_rhythm=1,
        harmony="Simple, bright diatonic harmony: I-IV-V7 and ii-V, often 2 chords per verse line; bridge to IV.",
        voicing="close",
        comping="strum",
        bass_style="root_fifth",
        bass="Root on 1, 5th on 3, with pushes on the 'and' of 2 and 4; bouncy and melodic.",
        melody_density="busy",
        melody_scale="major",
        melody="Syllabic, story-telling verse with a catchy chorus, call-and-response; horn riffs between lines.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":    "x.....x.x.......",
            "snare":   "....x.......x...",
            "cowbell": "x.x.xx.xx.x.xx.x",
            "maracas": "x.x.x.x.x.x.x.x.",
        }},
        drums="Light kit or hand percussion: kick on 1 and 3 with the 'and' of 2 pickup, snare on 2 and 4, "
              "iron (brake drum, here cowbell) and maracas for the carnival rattle; steelpan in later calypso.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("verse", 16),
              ("chorus", 8), ("outro", 4)),
        instruments=("acoustic guitar", "bass", "horns", "clarinet", "steelpan", "percussion", "lead vocal"),
        sound_design="Acoustic, bright and woody; reedy horns and clarinet; steelpan shimmer.",
        production="Natural and warm, vocal very clear (the lyrics matter), modest dynamics control.",
        theory="Major-key, tonic-dominant harmony with syncopated pushes; the text and its delivery are the focus.",
        mix=Mix(lufs=(-14, -10), lra=(6, 11), low_end="moderate", tone="warm", width="moderate"),
    ),
    Genre(
        name="soca",
        family="caribbean",
        aliases=("power soca", "groovy soca"),
        parent="calypso",
        description="Calypso supercharged for carnival: a driving four-on-the-floor kick, iron and offbeat hats, "
                    "bright brass and synths and crowd-instruction chants, from groovy to power soca.",
        era="Trinidad, 1970s (Lord Shorty's 'soul of calypso'); power soca from the 1990s",
        touchstones=("Lord Shorty", "Arrow - Hot Hot Hot", "Machel Montano", "Bunji Garlin", "Destra Garcia",
                     "Kes", "Alison Hinds", "Iwer George"),
        tempo=(110, 165),
        feel="four-on-the-floor, straight 16ths; groovy soca ~110-125, power soca 150-165",
        swing=50,
        modes=("major", "minor"),
        keys=("C major", "F major", "G major", "A minor"),
        progressions=(
            "I-V-vi-IV",
            "I-IV-V-IV",
            "vi-IV-I-V",
            "minor: i-VI-VII-i",
            "I-I-IV-V",
        ),
        harmonic_rhythm=1,
        harmony="Bright pop loops with brass stabs; power soca often sits on one or two chords for energy.",
        voicing="close",
        comping="offbeat",
        bass_style="syncopated",
        bass="Syncopated bass and synth bass with octave jumps and offbeat pushes, locked to the kick; "
             "power soca bass in driving 8ths.",
        melody_density="medium",
        melody_scale="major",
        melody="Chanted instructions (wave, jump, wine), short hooky choruses, brass riffs answering vocals.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":     "x...x...x...x...",
            "snare":    "....x..x....x...",
            "cowbell":  "X.xxX.xxX.xxX.xx",
            "open hat": "..x...x...x...x.",
        }},
        drums="Kick on every beat, snare on 2 and 4 with syncopated pickups, iron (brake drum) in 16th "
              "patterns, offbeat open hats; rhythm-section breaks and drum rolls before drops.",
        form=(("intro", 8), ("verse", 16), ("build", 8), ("chorus", 16), ("verse", 16), ("build", 8),
              ("chorus", 16), ("breakdown", 8), ("chorus", 16), ("outro", 8)),
        instruments=("drum machine", "iron", "synth bass", "brass section", "synths", "steelpan", "lead vocal"),
        sound_design="Bright synths and brass, crisp iron, punchy kick, steelpan samples; chants with crowd FX.",
        production="Loud, bright, energetic; vocal chants upfront, big builds and drops for carnival road and fete.",
        theory="Calypso harmony and melody on a four-on-the-floor dance rhythm (Indo-Trinidadian dholak and "
               "tassa influence in the syncopations); tempo defines the sub-style.",
        mix=Mix(lufs=(-8, -6), lra=(3, 6), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="zouk",
        family="caribbean",
        aliases=("zouk béton", "zouk love"),
        description="French Antillean dance music: Kassav's synth-and-horn fusion of gwo ka, kadans and biguine, "
                    "with a rolling syncopated groove and Creole vocals; zouk love is the slow, romantic version.",
        era="Guadeloupe and Martinique (and Paris), early 1980s",
        touchstones=("Kassav'", "Jacob Desvarieux", "Jocelyne Béroard", "Patrick Saint-Éloi", "Malavoi",
                     "Edith Lefel", "Zouk Machine"),
        tempo=(85, 130),
        feel="straight, syncopated 16ths from the tibwa sticks; zouk béton fast, zouk love ~85-95",
        swing=50,
        modes=("major", "minor"),
        keys=("C major", "F major", "A minor", "D minor"),
        progressions=(
            "I-vi-ii-V7",
            "Imaj7-iii7-vi7-ii7",
            "ii7-V7-Imaj7-Imaj7",
            "minor: i-iv-VII-III",
            "IV-V-iii-vi",
        ),
        harmonic_rhythm=1,
        harmony="Lush 80s pop-jazz harmony: maj7, m7, 9ths, ii-V cycles; zouk love leans on sentimental "
                "I-vi-ii-V turnarounds.",
        voicing="open",
        comping="push",
        bass_style="syncopated",
        bass="Busy, melodic and syncopated electric bass (often slap or synth), anticipating the beat with "
             "16th pushes; a lead voice in the groove.",
        melody_density="medium",
        melody_scale="major",
        melody="Creole vocal melodies, catchy choruses, call-and-response with coros; horn-section riffs and "
               "guitar fills.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x...x...x...x...",
            "snare":      "....x.......x...",
            "sticks":     "x.xx.xx.x.xx.xx.",
            "closed hat": "..x...x...x...x.",
        }},
        drums="Programmed and live drums with a steady kick, snare on 2 and 4, and the tibwa (sticks on "
              "bamboo, from gwo ka and bèlè) playing a constant syncopated figure; congas/ka drums add "
              "syncopation; zouk love halves the energy with a softer kit.",
        form=(("intro", 8), ("verse", 16), ("chorus", 16), ("verse", 16), ("chorus", 16), ("horn break", 8),
              ("chorus", 16), ("outro", 8)),
        instruments=("synths (DX7, Juno)", "electric bass", "drum machine", "drums", "ka drums", "horn section",
                     "electric guitar", "vocals"),
        sound_design="1980s digital synths (DX7 bells and brass), slap or synth bass, chorused guitars, gated "
                     "drums; modern zouk is smoother and more R&B.",
        production="Polished, wide, bass-forward 80s production; vocals and horns bright.",
        theory="Guadeloupean gwo ka rhythm (tibwa and ka) fused with Haitian kadans/kompa and funk; harmony from "
               "jazz-pop, rhythm from Creole drumming.",
        mix=Mix(lufs=(-11, -8), lra=(4, 8), low_end="heavy", tone="warm", width="wide"),
    ),
]
