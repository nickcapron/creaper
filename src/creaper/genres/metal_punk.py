"""Metal and punk: heavy metal and its extreme, melodic and progressive branches, plus punk, hardcore and their offshoots."""

from . import Genre, Mix

GENRES = [
    # ------------------------------------------------------------------ heavy metal
    Genre(
        name="metal",
        family="metal and punk",
        aliases=("heavy metal", "traditional heavy metal", "trad metal", "nwobhm"),
        parent="hard rock",
        description="Loud, distorted, riff-driven rock built on palm-muted power chords, galloping rhythms, "
                    "harmonized twin-guitar leads and soaring or snarling vocals; epic, defiant and theatrical.",
        era="Birmingham, England, around 1970 (Black Sabbath); codified by Judas Priest and the New Wave of British "
            "Heavy Metal, 1978-1983",
        touchstones=("Black Sabbath (Paranoid)", "Judas Priest (British Steel)", "Iron Maiden (The Number of the Beast)",
                     "Motorhead", "Dio (Holy Diver)", "Accept"),
        tempo=(100, 200),
        feel="straight and driving; 8th-note palm-muted chug or 8th-16th-16th gallop",
        modes=("minor", "phrygian", "harmonic minor"),
        keys=("E minor", "A minor", "D minor", "F# minor"),
        progressions=(
            "I5-VI5-VII5",
            "I5-VI5-VII5-I5",
            "I5-VII5-VI5-VII5",
            "I5-IV5-VI5-VII5",
            "phrygian: I5-II5-I5",
            "harmonic minor: i-VI-V7-i",
        ),
        harmonic_rhythm=1,
        harmony="Aeolian power-chord movement (i-bVI-bVII is the anthem cadence) over an open low-E or A pedal; "
                "riffs alternate the pedal with chords on the beat; phrygian b2 for menace; triads appear only in "
                "clean intros and twin-guitar harmonies in diatonic 3rds; harmonic-minor V for neoclassical solos.",
        voicing="power",
        comping="eighths",
        bass_style="eighths",
        bass="Picked 8th notes doubling the guitar's root, often the gallop (8th + two 16ths) in unison with the "
             "rhythm guitar (Steve Harris style); fills climb the scale into section changes; locks to the kick.",
        melody_density="medium",
        melody_scale="minor",
        melody="Riff first: a 1- or 2-bar motif on the low strings answered by a chord stab. Vocals are high, "
               "sustained and operatic (Halford, Dickinson, Dio), chorus hooks on long notes over the i-VI-VII climb; "
               "solos mix minor pentatonic licks with harmonic-minor runs; twin leads harmonized in 3rds.",
        groove={"step": 0.25, "pattern": {
            "kick":       "x.....x.x.......x.xxx.xxx.xxx.xx",
            "snare":      "....X.......X.......X.......X...",
            "closed hat": "x.x.x.x.x.x.x.x.................",
            "ride":       "................x.x.x.x.x.x.x.x.",
            "crash":      "x...............x...............",
        }},
        drums="Rock backbeat (snare 2 and 4) with 8th hats in verses, crash or ride on 8ths in choruses; galloping "
              "double-kick under the riff in the faster songs; tom fills across the kit into choruses, cymbal "
              "chokes on stop hits.",
        form=(("intro", 8), ("verse", 16), ("pre-chorus", 8), ("chorus", 8), ("verse", 16), ("pre-chorus", 8),
              ("chorus", 8), ("solo", 16), ("bridge", 8), ("chorus", 16), ("outro", 8)),
        instruments=("two distorted electric guitars", "electric bass", "drum kit with double kick", "lead vocal",
                     "occasional clean acoustic guitar"),
        sound_design="E standard or Eb standard tuning; Marshall-style mid-forward crunch, moderate gain so chords "
                     "stay clear; 4x12 cabs miked with an SM57; picked bass with some grind; natural toms, "
                     "reverbed snare in the 80s.",
        production="Double-tracked rhythm guitars hard left and right, lead guitar and vocal up the middle; bass and "
                   "kick share the low end around 80-100 Hz; vocals with plate reverb and slap delay; bus "
                   "compression for drive but still dynamic by modern standards.",
        theory="Built on the aeolian bVI-bVII-i ascent instead of V-i, the open-string pedal riff, the phrygian b2 "
               "and the tritone (Sabbath's diabolus in musica); the gallop is a dactyl rhythm (long-short-short).",
        mix=Mix(lufs=(-9, -6), lra=(3, 6), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="thrash metal",
        family="metal and punk",
        aliases=("thrash", "speed metal", "bay area thrash", "teutonic thrash"),
        parent="metal",
        description="Fast, aggressive metal fusing NWOBHM riffs with hardcore punk speed: tight down-picked "
                    "palm-muted riffs, skank beats, chromatic menace and shouted vocals.",
        era="San Francisco Bay Area and Los Angeles, 1981-1986; Germany (Kreator, Sodom, Destruction) in parallel",
        touchstones=("Metallica (Master of Puppets)", "Slayer (Reign in Blood)", "Megadeth (Peace Sells... but Who's Buying?)",
                     "Anthrax", "Exodus (Bonded by Blood)", "Kreator", "Testament"),
        tempo=(160, 250),
        feel="fast straight 8ths and 16ths; skank beat, with half-time mosh sections",
        modes=("phrygian", "minor", "locrian"),
        keys=("E phrygian", "E minor", "D minor", "Eb minor"),
        progressions=(
            "I5-II5-I5-bV5",
            "I5-III5-II5-I5",
            "I5-bV5-IV5-II5",
            "I5-VI5-V5-II5",
            "minor: I5-VI5-VII5-I5",
        ),
        harmonic_rhythm=2,
        harmony="Little chord harmony: riffs are single-note 16ths on the open low E punctuated by power chords "
                "moving chromatically (b2, b5, b3) for tension; tritone leaps; occasional clean minor arpeggio "
                "intros (i-VI-iv-V) before the speed kicks in.",
        voicing="power",
        comping="pulse_16",
        bass_style="sixteenths",
        bass="Picked (Cliff Burton, Frank Bello) 8ths and 16ths doubling the riff note for note; drops to roots "
             "on chord hits; occasional distorted bass intro or lead break.",
        melody_density="busy",
        melody_scale="phrygian",
        melody="Riffs are 16th-note tremolo or down-picked gallops around the open string with chromatic passing "
               "notes; vocals are barked rhythmic phrases on few pitches, gang-shouted choruses; solos are "
               "fast, chromatic, whammy-heavy (Slayer) or melodic and composed (Metallica, Megadeth).",
        groove={"step": 0.25, "pattern": {
            "kick":  "x...x...x...x...xxxxxxxxxxxxxxxx",
            "snare": "..X...X...X...X.....X.......X...",
            "crash": "x...x...x...x...x...............",
            "ride":  "................x.x.x.x.x.x.x.x.",
        }},
        drums="Skank (thrash) beat: kick on the beat, snare on every 'and', crash or hat riding the kick; "
              "alternates with 16th double-kick runs under snare 2 and 4; half-time mosh breaks; Dave Lombardo-style "
              "fills between riffs.",
        form=(("intro", 8), ("riff", 8), ("verse", 16), ("chorus", 8), ("riff", 8), ("verse", 16), ("chorus", 8),
              ("breakdown", 16), ("solo", 16), ("verse", 8), ("chorus", 8), ("outro", 4)),
        instruments=("two distorted electric guitars", "picked electric bass", "drum kit with double kick",
                     "shouted lead vocal", "gang vocals"),
        sound_design="E standard (Metallica, Megadeth), Eb standard (Slayer) or drop D; scooped-mid high-gain amps "
                     "(Mesa Mark, Marshall with a Tube Screamer), tight noise-gated palm mutes; clicky kick.",
        production="Quad-tracked rhythm guitars panned hard, tight editing, bass clanky to be heard under scooped "
                   "guitars, dry snare, vocals forward and dry-ish; 80s records are thinner and more dynamic.",
        theory="Speed and chromaticism over harmony: the phrygian b2 and the b5 replace functional chords; riffs "
               "are pedal-point figures (open string vs. moving fretted notes) built from 16th-note cells and "
               "gallops, frequent tempo and feel shifts mid-song.",
        mix=Mix(lufs=(-10, -6), lra=(3, 6), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="death metal",
        family="metal and punk",
        aliases=("death", "old school death metal", "osdm", "brutal death metal"),
        parent="thrash metal",
        description="Extreme metal of downtuned chromatic riffs, blast beats, guttural growled vocals and "
                    "complex, shifting song structures; brutal and morbid.",
        era="Florida (Tampa, Morrisound Studios) and Stockholm, 1987-1993",
        touchstones=("Death (Scream Bloody Gore)", "Morbid Angel (Altars of Madness)", "Cannibal Corpse",
                     "Obituary", "Entombed (Left Hand Path)", "Suffocation", "Deicide"),
        tempo=(100, 260),
        feel="fast blast-beat and double-kick passages broken by mid-tempo and half-time grooves",
        modes=("phrygian", "locrian", "minor"),
        keys=("E phrygian", "D phrygian", "C# minor", "B minor"),
        progressions=(
            "I5-II5-I5-bV5",
            "I5-bV5-IV5-II5",
            "I5-III5-II5-bV5",
            "I5-VI5-bV5-II5",
            "locrian: I5-V5-II5-I5",
        ),
        harmonic_rhythm=2,
        harmony="Atonal-leaning chromatic riffing: power chords and single notes moving by semitone and tritone, "
                "diminished and whole-tone shapes, phrygian b2 and locrian b5 as 'home' colours; dissonant "
                "intervals (m2, tritone) stacked deliberately; almost no functional cadences.",
        voicing="power",
        comping="pulse_16",
        bass_style="sixteenths",
        bass="Fingered or picked 16ths tracking the guitar riff exactly (Alex Webster); low-tuned 5-string; "
             "brief chromatic fills; mostly felt as attack and growl rather than separate lines.",
        melody_density="busy",
        melody_scale="chromatic",
        melody="Tremolo-picked chromatic lines and pinch-harmonic accents; vocals are low guttural growls in "
               "rhythmic syllables, effectively percussion; solos are atonal whammy chaos (Trey Azagthoth) or "
               "neoclassical (Chuck Schuldiner).",
        groove={"step": 0.25, "pattern": {
            "kick":  "x.x.x.x.x.x.x.x.xxxxxxxxxxxxxxxx",
            "snare": ".x.x.x.x.x.x.x.x....X.......X...",
            "ride":  "x.x.x.x.x.x.x.x.................",
            "china": "................x...x...x...x...",
        }},
        drums="Traditional blast (kick and cymbal together, snare between, 16ths), alternating with continuous "
              "16th double kick under a snare backbeat; skank beats, gravity blasts in brutal styles; "
              "half-time grooves for the heavy riff; triggered kick for clarity.",
        form=(("intro", 4), ("riff A", 8), ("verse", 16), ("riff B", 8), ("blast section", 16), ("groove", 8),
              ("verse", 16), ("solo", 8), ("riff A", 8), ("outro", 4)),
        instruments=("two downtuned high-gain guitars", "5-string bass", "drum kit with double kick (triggered)",
                     "growled vocal"),
        sound_design="D standard to B standard (or drop B/A); Florida: scooped high-gain solid-state or Mesa tone; "
                     "Swedish: Boss HM-2 pedal with every knob maxed (the buzzsaw 'Sunlight' sound); clicky "
                     "triggered kick, tight noise gate.",
        production="Dense wall of quad-tracked guitars, triggered drums, growl tucked into the mix as an "
                   "instrument; tight editing on blasts; low end controlled below 60 Hz so the tremolo stays "
                   "readable.",
        theory="Chromatic and modal (phrygian/locrian) pitch collections replace keys; tritone and semitone "
               "relations drive the riff; through-composed riff chains (A B C D) rather than verse-chorus; "
               "metric shifts and tempo changes are structural.",
        mix=Mix(lufs=(-9, -6), lra=(3, 5), low_end="very heavy", tone="dark", width="wide"),
    ),
    Genre(
        name="melodic death metal",
        family="metal and punk",
        aliases=("melodeath", "gothenburg metal", "gothenburg sound"),
        parent="death metal",
        description="Death metal's speed and harsh vocals married to harmonized twin-guitar melodies and "
                    "Iron Maiden-style hooks; fast, mournful and catchy.",
        era="Gothenburg, Sweden, 1993-1997",
        touchstones=("At the Gates (Slaughter of the Soul)", "In Flames (The Jester Race)",
                     "Dark Tranquillity (The Gallery)", "Arch Enemy", "Children of Bodom", "Insomnium"),
        tempo=(120, 220),
        feel="driving 16th double kick under skank and backbeat patterns; melodic phrases in 2- and 4-bar units",
        modes=("minor", "harmonic minor"),
        keys=("E minor", "D minor", "C minor", "B minor"),
        progressions=(
            "i-VI-III-VII",
            "i-VI-VII-i",
            "i-iv-VII-III",
            "i-VI-VII-V",
            "harmonic minor: i-VI-iv-V",
        ),
        harmonic_rhythm=1,
        harmony="Diatonic natural minor, implied by twin-guitar lines in 3rds and 6ths over power chords; "
                "i-VI-III-VII and i-VI-VII sequences; harmonic-minor V and diminished passing tones for a "
                "neoclassical lift (Children of Bodom); keyboard pads double the chords.",
        voicing="power",
        comping="pulse_16",
        bass_style="eighths",
        bass="8ths and 16ths on the root, following the rhythm guitar; under twin leads it holds roots so the "
             "harmony is clear.",
        melody_density="busy",
        melody_scale="minor",
        melody="Lead melodies are tremolo-picked or 8th-note folk-like lines harmonized a 3rd apart, repeated "
               "in 4-bar phrases; harsh mid-high screams (not deep growls) in verse, sometimes clean sung "
               "choruses in the later style; shred solos with harmonic-minor and diminished arpeggios.",
        groove={"step": 0.25, "pattern": {
            "kick":  "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "snare": "..X...X...X...X.....X.......X...",
            "crash": "x...x...x...x...x...............",
            "ride":  "................x.x.x.x.x.x.x.x.",
        }},
        drums="Rolling 16th double kick under an offbeat skank snare (the Gothenburg beat), then under a 2-and-4 "
              "backbeat for choruses; occasional blasts; d-beat verses; crash on every quarter for drive.",
        form=(("intro lead", 8), ("verse", 16), ("pre-chorus", 8), ("chorus", 8), ("lead riff", 8), ("verse", 16),
              ("chorus", 8), ("bridge", 8), ("solo", 16), ("chorus", 16), ("outro lead", 8)),
        instruments=("two high-gain guitars (rhythm and harmony lead)", "bass", "drum kit with double kick",
                     "harsh vocal", "keyboards or synth pad"),
        sound_design="D standard, C standard or drop B (7-string in later bands); tight high-gain tone with more "
                     "mids than death metal so the melodies cut; clean bright leads with delay; synth strings "
                     "or 80s lead keys.",
        production="Studio Fredman sound: clear, punchy, quad-tracked rhythms wide, harmony leads panned left and "
                   "right, keys tucked behind; vocals compressed and centred; modern masters loud.",
        theory="Applies NWOBHM twin-guitar harmonization in diatonic 3rds to extreme-metal tempos; tonal "
               "(natural/harmonic minor) where death metal is chromatic; Swedish folk-like melodic contours.",
        mix=Mix(lufs=(-8, -6), lra=(3, 5), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="black metal",
        family="metal and punk",
        aliases=("second wave black metal", "norwegian black metal", "atmospheric black metal"),
        parent="thrash metal",
        description="Cold, raw extreme metal: tremolo-picked minor chords ringing over blast beats, shrieked "
                    "vocals and lo-fi, trebly production; hypnotic, hostile and atmospheric.",
        era="First wave: Venom, Bathory, Hellhammer (early 1980s); second wave: Norway, 1990-1995",
        touchstones=("Mayhem (De Mysteriis Dom Sathanas)", "Darkthrone (Transilvanian Hunger)", "Burzum",
                     "Emperor (In the Nightside Eclipse)", "Immortal", "Bathory"),
        tempo=(140, 240),
        feel="relentless blast and hammer-blast sections, occasional slow mid-tempo marches",
        modes=("minor", "phrygian", "harmonic minor"),
        keys=("E minor", "D minor", "F# minor", "B minor"),
        progressions=(
            "i-VI-iv-i",
            "i-VI-VII-i",
            "i-iv-VI-v",
            "phrygian: i-II-i",
            "harmonic minor: i-V-VI-V",
        ),
        harmonic_rhythm=0.5,
        harmony="Full minor triads (not just power chords) tremolo-picked with open strings ringing as drones; "
                "chords shift by step, often minor-to-minor (i-iv, i-v) or minor chord over a pedal; phrygian b2 "
                "and harmonic-minor V for coldness; 2-bar chords repeated many times for trance.",
        voicing="open",
        comping="pulse_16",
        bass_style="eighths",
        bass="Often buried: root 8ths following the chord changes, occasionally independent counter-lines in "
             "the atmospheric style.",
        melody_density="busy",
        melody_scale="minor",
        melody="Melody lives in the top note of tremolo-picked chords; lines move slowly over fast picking; "
               "shrieked, rasped vocals in long syllables; synth or choir pads double the riff; "
               "solos are rare.",
        groove={"step": 0.25, "pattern": {
            "kick":  "x.x.x.x.x.x.x.x.xxxxxxxxxxxxxxxx",
            "snare": ".x.x.x.x.x.x.x.xx.x.x.x.x.x.x.x.",
            "ride":  "x.x.x.x.x.x.x.x.................",
            "crash": "................x...x...x...x...",
        }},
        drums="Blast beats dominate: traditional blast alternating kick and snare, bomb blast (16th kick under "
              "8th snare), skank and d-beat for verses; cymbals washy; minimal fills, more about the trance of "
              "repetition.",
        form=(("intro", 8), ("riff A", 16), ("riff B", 16), ("riff A", 16), ("slow section", 16), ("riff C", 16),
              ("riff A", 16), ("outro", 8)),
        instruments=("tremolo-picked distorted guitar", "bass", "drum kit", "shrieked vocal",
                     "synth pad or choir (symphonic style)"),
        sound_design="E or Eb standard; thin, fizzy, mid-scooped distortion (often transistor amps or pedals), "
                     "lots of treble, little low end; drums roomy or deliberately weak; synths cheap and cold.",
        production="Raw: guitars dominate, bass and drums low, vocals drenched in reverb; lo-fi is an aesthetic "
                   "choice (4-track, rehearsal-room); modern atmospheric black metal is cleaner and wider.",
        theory="Harmony through sustained tremolo triads with pedal tones, creating a static, modal field; "
               "repetition and slow harmonic rhythm against maximal surface speed; minor-minor root motion "
               "avoids bright dominant resolution.",
        mix=Mix(lufs=(-12, -8), lra=(3, 7), low_end="light", tone="bright", width="wide"),
    ),
    Genre(
        name="doom metal",
        family="metal and punk",
        aliases=("doom", "traditional doom", "epic doom metal", "death-doom"),
        parent="metal",
        description="Metal slowed to a crawl: huge sustained downtuned riffs, tritone and blues-scale menace, "
                    "mournful vocals and crushing weight; funereal and hypnotic.",
        era="Black Sabbath (1970) as blueprint; codified by Pentagram, Saint Vitus, Candlemass and Trouble in the 1980s",
        touchstones=("Black Sabbath", "Candlemass (Epicus Doomicus Metallicus)", "Saint Vitus", "Pentagram",
                     "Trouble", "Electric Wizard (Dopethrone)", "My Dying Bride"),
        tempo=(50, 80),
        feel="slow, heavy and behind the beat; half-time grooves and sustained chords",
        modes=("minor", "phrygian"),
        keys=("C minor", "D minor", "E minor", "C# minor"),
        progressions=(
            "I5-bV5-I5",
            "I5-VI5-VII5-I5",
            "I5-III5-IV5-bV5",
            "I5-VII5-VI5",
            "phrygian: I5-II5-I5",
        ),
        harmonic_rhythm=0.5,
        harmony="Sustained power chords with the tritone (bV) and b2 as the darkest colours; blues-scale riffs "
                "(b3, 4, b5) slowed down; epic doom adds harmonic-minor and choral i-VI-VII; death-doom uses "
                "minor triads and dissonant clusters.",
        voicing="power",
        comping="sustain",
        bass_style="whole",
        bass="Doubles the riff root an octave down, fuzzed, letting notes ring through the bar; slides between "
             "roots; occasionally the only moving voice under a held chord.",
        melody_density="sparse",
        melody_scale="blues",
        melody="Riffs are a few long notes per bar with bends and vibrato; vocals are sustained, lamenting "
               "(Messiah Marcolin operatic, Ozzy-like chant or death growls); solos are slow and bluesy with "
               "wah.",
        groove={"step": 0.25, "pattern": {
            "kick":  "x.......x.x.....",
            "snare": "....X.......X...",
            "ride":  "x...x...x...x...",
            "crash": "x...............",
        }},
        drums="Slow backbeat (snare 2 and 4 at 60 bpm feels like half time), crash on the downbeat of each riff "
              "cycle, rides on quarters; big tom fills; space between hits matters more than speed.",
        form=(("intro", 8), ("riff", 8), ("verse", 16), ("riff", 8), ("verse", 16), ("bridge", 8),
              ("solo", 16), ("riff", 8), ("outro", 16)),
        instruments=("fuzz or overdriven guitar", "fuzz bass", "drum kit", "lead vocal", "organ (occasional)"),
        sound_design="C standard, C# or B standard (Electric Wizard much lower); vintage amps (Orange, Sunn, "
                     "Laney, Matamp) through fuzz pedals; huge sustain; bass as loud as guitars.",
        production="Huge low mids, roomy drums, vocals with reverb or slapback; long dynamic swells; less "
                   "limiting than modern metal so the weight breathes.",
        theory="Tempo as expression: the tritone (diabolus in musica) and b2 at very slow harmonic rhythm; "
               "minor blues vocabulary stretched until each note becomes an event.",
        mix=Mix(lufs=(-11, -8), lra=(4, 8), low_end="very heavy", tone="dark", width="wide"),
    ),
    Genre(
        name="sludge metal",
        family="metal and punk",
        aliases=("sludge", "nola sludge"),
        parent="doom metal",
        description="Doom's slow weight cross-bred with hardcore punk's rage: abrasive, feedback-laced downtuned "
                    "riffs, screamed vocals and lurching grooves; filthy, swampy and furious.",
        era="Melvins in Washington (mid-1980s); New Orleans scene (Eyehategod, Crowbar, Down) in the early 1990s",
        touchstones=("Melvins (Bullhead)", "Eyehategod (Take as Needed for Pain)", "Crowbar", "Neurosis",
                     "Mastodon (Remission)", "Iron Monkey", "Down (NOLA)"),
        tempo=(60, 110),
        feel="half-time crawl that lurches into hardcore-speed bursts; swung, Southern-blues phrasing",
        swing=54,
        modes=("minor", "phrygian"),
        keys=("C minor", "B minor", "A minor", "D minor"),
        progressions=(
            "I5-III5-IV5-bV5",
            "phrygian: I5-II5-I5",
            "I5-VII5-I5",
            "I5-IV5-bV5-IV5",
            "I5-VI5-bV5",
        ),
        harmonic_rhythm=0.5,
        harmony="Power chords and open-string pedals from the minor blues scale; chromatic slides (IV-bV-IV) "
                "and b2 grinds; dissonant held chords and feedback between riffs.",
        voicing="power",
        comping="half_notes",
        bass_style="root",
        bass="Distorted, often louder than you'd expect: doubles riff roots with grinding attack, sometimes "
             "sustains while guitars feed back.",
        melody_density="sparse",
        melody_scale="blues",
        melody="Riffs bent and slurred with Southern-blues swagger; vocals are hoarse screams and yells; few "
               "solos, more feedback squeals and noise textures.",
        groove={"step": 0.25, "swing": 54, "pattern": {
            "kick":      "x.....x.........x..x..x.........",
            "snare":     "........X...............X.......",
            "floor tom": "............x.x.............xxxx",
            "crash":     "x...x...x...x...x...x...x...x...",
        }},
        drums="Half-time backbeat (snare on 3) with crash riding the quarters; floor-tom pounding; abrupt "
              "switches to punk beats or d-beat; loose, heavy-handed playing.",
        form=(("feedback intro", 4), ("riff", 8), ("verse", 16), ("riff", 8), ("fast section", 8), ("verse", 16),
              ("breakdown", 8), ("outro", 8)),
        instruments=("downtuned distorted guitar", "distorted bass", "drum kit", "screamed vocal"),
        sound_design="Drop C, drop B or lower; fuzzed and overdriven amps (Sunn, Orange, Ampeg, Marshall JCM800) "
                     "dimed with feedback; gritty mid-heavy tone, less gated than metalcore.",
        production="Raw and loud with room mics on drums; guitars thick in low mids; vocals distorted and "
                   "pushed into the band; noise and feedback kept, not edited out.",
        theory="Hardcore's rhythmic aggression at doom's tempo; harmonic language is minor-pentatonic blues "
               "with chromatic bV and b2; tension comes from tempo contrast and sustained noise.",
        mix=Mix(lufs=(-10, -7), lra=(4, 8), low_end="very heavy", tone="dark", width="moderate"),
    ),
    Genre(
        name="stoner rock",
        family="metal and punk",
        aliases=("stoner metal", "desert rock", "stoner", "stoner doom"),
        parent="doom metal",
        description="Fuzz-drenched, groove-heavy riff rock: blues-rooted, repetitive, mid-tempo and psychedelic, "
                    "with bass-amp guitar tone and long jams.",
        era="Palm Desert, California, early 1990s (generator parties); also Sleep in San Jose",
        touchstones=("Kyuss (Blues for the Red Sun)", "Sleep (Sleep's Holy Mountain)", "Fu Manchu",
                     "Monster Magnet", "Queens of the Stone Age (Rated R)", "Electric Wizard"),
        tempo=(70, 130),
        feel="loose, swaggering, slightly swung 8ths; laid-back and behind the beat",
        swing=54,
        modes=("minor", "dorian", "mixolydian"),
        keys=("C minor", "D minor", "E minor", "C# minor"),
        progressions=(
            "I5-III5-IV5",
            "I5-VII5-IV5",
            "I5-bV5-IV5-III5",
            "dorian: i-IV",
            "mixolydian: I5-VII5-IV5",
        ),
        harmonic_rhythm=1,
        harmony="Minor-pentatonic power chords (i, bIII, IV, bVII), dorian IV for a hippie lift, chromatic "
                "bV passing chords; long single-riff vamps where harmony barely moves.",
        voicing="power",
        comping="eighths",
        bass_style="root",
        bass="Fuzzed bass doubling the guitar riff, loud and round; sustained roots during jams; sometimes the "
             "riff starts on bass alone.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="Riffs are bluesy pentatonic phrases looped for minutes; vocals are melodic, laid-back, often "
               "reverbed (John Garcia, Josh Homme); long wah and fuzz solos and jams.",
        groove={"step": 0.25, "swing": 54, "pattern": {
            "kick":     "x.....x.x.......",
            "snare":    "....X..o....X..o",
            "open hat": "x.x.x.x.x.x.x.x.",
            "crash":    "x...............",
        }},
        drums="Big, loose rock backbeat with washy open hats or ride, ghost notes, John Bonham-style kick "
              "patterns; jams drift into tom grooves and builds.",
        form=(("intro riff", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("jam", 32),
              ("riff", 8), ("chorus", 8), ("outro", 8)),
        instruments=("fuzz guitar (often through a bass amp)", "fuzz bass", "drum kit", "lead vocal",
                     "organ or theremin (occasional)"),
        sound_design="C standard or D standard; vintage fuzz (Big Muff, Fuzz Face) into Ampeg or Sunn bass "
                     "heads; warm, saturated, wooly tone; analog tape warmth.",
        production="Live-feeling, warm, low-mid heavy, roomy drums; vocals with plate reverb or delay; "
                   "compression for thickness rather than loudness.",
        theory="Riff repetition and minor-pentatonic modality (with dorian and mixolydian colour) instead of "
               "progressions; the groove is a Sabbath-style blues riff slowed and looped as psychedelic trance.",
        mix=Mix(lufs=(-10, -8), lra=(4, 8), low_end="very heavy", tone="warm", width="wide"),
    ),
    # ------------------------------------------------------------------ melodic and epic
    Genre(
        name="power metal",
        family="metal and punk",
        aliases=("european power metal", "euro power metal", "happy metal"),
        parent="metal",
        description="Fast, uplifting, anthemic metal: galloping double kick, soaring high tenor vocals, big "
                    "choral choruses, neoclassical solos and fantasy themes.",
        era="Germany (Helloween, 1985-1988); Finland, Italy and Sweden in the 1990s",
        touchstones=("Helloween (Keeper of the Seven Keys)", "Blind Guardian (Nightfall in Middle-Earth)",
                     "Stratovarius", "Gamma Ray", "Sonata Arctica", "Sabaton", "Iced Earth"),
        tempo=(140, 220),
        feel="driving straight 16th double kick with a backbeat; triumphant and relentless",
        modes=("minor", "harmonic minor", "major"),
        keys=("E minor", "F# minor", "D minor", "A minor"),
        progressions=(
            "i-VI-VII-i",
            "i-VI-III-VII",
            "VI-VII-i",
            "i-VI-VII-V",
            "harmonic minor: i-iv-V7-i",
            "major: I-V-vi-IV",
        ),
        harmonic_rhythm=1,
        harmony="Diatonic minor with the epic VI-VII-i ascent and harmonic-minor V for drama; choruses often "
                "lift to the relative major or modulate up a step for the last chorus; triads in keyboards and "
                "choirs over guitar power chords.",
        voicing="power",
        comping="eighths",
        bass_style="eighths",
        bass="Fast picked 8ths on the root, gallops with the guitar; walks scale steps into the chorus.",
        melody_density="busy",
        melody_scale="harmonic minor",
        melody="Very high tenor lead vocals (up to A5-C6), long sustained chorus hooks stacked in choirs; "
               "guitar and keyboard duelling solos with harmonic-minor runs, sweep arpeggios and diminished "
               "sequences; twin-guitar harmonies in 3rds.",
        groove={"step": 0.25, "pattern": {
            "kick":  "xxxxxxxxxxxxxxxx",
            "snare": "....X.......X...",
            "ride":  "x.x.x.x.x.x.x.x.",
            "crash": "x...............",
        }},
        drums="Continuous 16th double kick under snare 2 and 4 at 160-200 bpm; crash or ride on 8ths in choruses; "
              "gallops and stops for drama; triggered, very even kicks.",
        form=(("intro", 8), ("verse", 16), ("pre-chorus", 8), ("chorus", 8), ("verse", 16), ("pre-chorus", 8),
              ("chorus", 8), ("solo", 16), ("bridge", 8), ("chorus", 8), ("chorus (up a step)", 8), ("outro", 8)),
        instruments=("two electric guitars", "bass", "drum kit with double kick", "high lead vocal",
                     "keyboards and orchestral synths", "backing choir"),
        sound_design="E standard or Eb standard (some 7-strings now); bright, tight mid-gain tone; keys with "
                     "strings, choirs and harpsichord patches; lead synth for solo trades.",
        production="Polished and loud: dense layered choirs, keys widened, very consistent triggered kicks, "
                   "vocals huge with reverb; the chorus must sound like a stadium.",
        theory="Major-sounding catharsis within minor (VI-VII-I picardy-style lifts), harmonic-minor "
               "neoclassicism (Bach and Paganini via Yngwie), truck-driver modulations for the final chorus.",
        mix=Mix(lufs=(-9, -6), lra=(3, 6), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="symphonic metal",
        family="metal and punk",
        aliases=("operatic metal", "symphonic power metal"),
        parent="power metal",
        description="Metal with a full orchestra and choir as equal partners: cinematic arrangements, operatic "
                    "or ethereal female lead vocals, and dramatic dynamic swings.",
        era="Finland and the Netherlands, late 1990s (Nightwish, Within Temptation); Italy (Rhapsody)",
        touchstones=("Nightwish (Once)", "Epica (The Divine Conspiracy)", "Within Temptation (Mother Earth)",
                     "Therion", "Rhapsody of Fire", "Delain"),
        tempo=(80, 180),
        feel="mid-tempo stomps and fast double-kick sections; orchestral rubato in intros",
        modes=("minor", "harmonic minor"),
        keys=("E minor", "D minor", "B minor", "C# minor"),
        progressions=(
            "i-VI-III-VII",
            "i-VI-iv-V",
            "i-iv-VI-V",
            "VI-VII-i",
            "harmonic minor: i-VI-iv-V7",
        ),
        harmonic_rhythm=1,
        harmony="Film-score minor harmony: i-VI-III-VII, harmonic-minor V, chromatic mediants (i to bVI to "
                "IV) in orchestral bridges, pedal points under string ostinatos; choirs voiced in full triads "
                "while guitars play power chords.",
        voicing="power",
        comping="eighths",
        bass_style="eighths",
        bass="Root 8ths locked to the kick and guitar chug; drops out or sustains in orchestral passages; "
             "orchestral low strings and timpani share the low end.",
        melody_density="medium",
        melody_scale="harmonic minor",
        melody="Lead vocal is operatic soprano (Tarja Turunen, Simone Simons) or pop-clean, with long arching "
               "phrases; choirs sing Latin-sounding hooks; growled male counterpoint in some bands; string "
               "ostinatos and brass fanfares carry counter-melodies.",
        groove={"step": 0.25, "pattern": {
            "kick":  "x.xxx.xxx.xxx.xx",
            "snare": "....X.......X...",
            "crash": "x...x...x...x...",
            "ride":  "..x...x...x...x.",
        }},
        drums="Double-kick gallops and 16th runs under a steady backbeat; orchestral percussion (timpani, "
              "taiko, cymbal swells) layered; tight triggered kicks, big tom builds.",
        form=(("orchestral intro", 16), ("verse", 16), ("pre-chorus", 8), ("chorus", 16), ("verse", 16),
              ("pre-chorus", 8), ("chorus", 16), ("orchestral bridge", 16), ("solo", 8), ("chorus", 16),
              ("outro", 8)),
        instruments=("orchestra (strings, brass, timpani)", "choir", "two electric guitars", "bass",
                     "drum kit with double kick", "operatic lead vocal", "keyboards"),
        sound_design="E standard to drop C or 7-string B; tight, modern high-gain guitars carved around the "
                     "orchestra; orchestral sample libraries or live orchestra; choirs with long reverb tails.",
        production="Huge arrangement density: guitars carved in the mids (cut 2-4 kHz) to make room for strings "
                   "and choir; orchestra wide, vocals centred with lush reverb; dynamic contrast between "
                   "orchestral and full-band sections.",
        theory="Merges film-score orchestration (ostinatos, chromatic mediants, brass pedals) with metal riffs; "
               "functional minor with harmonic-minor dominants; contrast of operatic timbre against distortion.",
        mix=Mix(lufs=(-10, -7), lra=(4, 8), low_end="heavy", tone="neutral", width="wide"),
    ),
    Genre(
        name="progressive metal",
        family="metal and punk",
        aliases=("prog metal",),
        parent="metal",
        description="Technical, ambitious metal with odd meters, long multi-section songs, virtuosic playing and "
                    "jazz and classical harmony; cerebral but heavy.",
        era="Late 1980s US (Fates Warning, Queensryche, Dream Theater); Opeth and Tool in the 1990s",
        touchstones=("Dream Theater (Images and Words)", "Queensryche (Operation: Mindcrime)", "Fates Warning",
                     "Opeth (Blackwater Park)", "Tool (Lateralus)", "Symphony X", "Haken"),
        tempo=(70, 180),
        meter="7/8",
        feel="odd meters (7/8, 5/4, 13/16) and metric modulation between sections; tight unison hits",
        modes=("minor", "dorian", "phrygian", "lydian"),
        keys=("E minor", "D minor", "B minor", "F# minor"),
        progressions=(
            "i-VI-III-VII",
            "i-bII-VI-VII",
            "i-iiø7-VImaj7-V7",
            "dorian: i-IV",
            "lydian: I-II",
        ),
        harmonic_rhythm=1,
        harmony="Wide vocabulary: minor with chromatic bII, maj7 and add9 chords in clean sections, jazz "
                "ii-V moves, lydian and dorian colours, quartal voicings on keys; modulations by mediant "
                "or tritone between movements.",
        voicing="power",
        comping="stabs",
        bass_style="syncopated",
        bass="Melodic and independent (John Myung, Justin Chancellor): locks with odd-meter kick patterns in "
             "unison, then moves to counter-lines, tapping or chordal fills in quieter parts.",
        melody_density="busy",
        melody_scale="minor",
        melody="Long vocal melodies with wide range over complex rhythm; instrumental themes in unison "
               "guitar/keys at speed; solos trade between guitar and keyboard; motifs recur across a 10-20 "
               "minute piece.",
        groove={"step": 0.25, "pattern": {
            "kick":  "x.....x.x..x..",
            "snare": "....X.......X.",
            "ride":  "x.x.x.x.x.x.x.",
            "crash": "x.............",
        }},
        drums="7/8 grouped 2+2+3 (or 3+2+2), accents follow the riff; Mike Portnoy/Danny Carey style: "
              "orchestrated fills, polyrhythms, double kick and ride-bell patterns; meter changes every section.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("instrumental", 16), ("verse", 16), ("chorus", 8),
              ("interlude", 16), ("solo section", 32), ("bridge", 16), ("chorus", 16), ("outro", 16)),
        instruments=("electric guitar (6- or 7-string)", "bass", "drum kit with double kick",
                     "keyboards (piano, synth, organ)", "lead vocal", "acoustic guitar"),
        sound_design="E standard, drop D or 7-string B standard; articulate medium-high gain (Mesa Mark IV), "
                     "clean chorused tones for ballads; synth leads and piano; more mids for clarity.",
        production="Clarity over brute force: every instrument readable, wider dynamics, keys and guitars "
                   "panned to opposite sides, natural-sounding drums.",
        theory="Odd and changing meters, metric modulation, polyrhythm (e.g. 7 against 4), modal interchange and "
               "jazz extensions inside metal, and long-form thematic development.",
        mix=Mix(lufs=(-10, -7), lra=(4, 9), low_end="heavy", tone="neutral", width="wide"),
    ),
    Genre(
        name="djent",
        family="metal and punk",
        aliases=("djent metal", "polymetric metal"),
        parent="progressive metal",
        description="Ultra-tight, extended-range progressive metal built on palm-muted low-string syncopations "
                    "that cycle in odd groupings over steady 4/4, with ambient clean passages.",
        era="Meshuggah in Sweden (1990s) as the source; named and spread online by Periphery and others, 2008-2012",
        touchstones=("Meshuggah (ObZen)", "Periphery (Periphery II)", "TesseracT (One)", "Animals as Leaders",
                     "Monuments", "Vildhjarta"),
        tempo=(90, 150),
        feel="steady 4/4 hats and snare on 3 against polymetric kick-and-guitar cycles that 'resolve' every 4 or 8 bars",
        modes=("phrygian", "locrian", "minor", "lydian"),
        keys=("F# phrygian", "B phrygian", "A minor", "D# minor"),
        progressions=(
            "I5-II5",
            "I5-II5-I5-VII5",
            "I5-bV5-II5",
            "locrian: I5-V5-II5",
            "lydian: Imaj7-II",
            "minor: i-VImaj7-III-VII",
        ),
        harmonic_rhythm=0.5,
        harmony="Heavy parts sit on one low note (single-note chugs on an open 7th or 8th string) with dissonant "
                "upper clusters (b2, tritone, maj7); clean parts use lydian and add9/maj7 chords with open "
                "strings, often ambient and floating.",
        voicing="power",
        comping="push",
        bass_style="syncopated",
        bass="Usually doubles the low-string riff exactly (or replaced by an 8-string guitar line), sometimes "
             "tuned to match; slap or tapping in Animals as Leaders style; clean parts hold roots.",
        melody_density="medium",
        melody_scale="phrygian",
        melody="Riff is rhythm, not pitch: one note in syncopated groupings (e.g. 5+5+3+... summed to 32 16ths). "
               "Vocals alternate harsh and soaring clean melodic choruses; lead guitar is legato, fusion-like "
               "and atmospheric with delay.",
        groove={"step": 0.25, "pattern": {
            "kick":  "xx.x.xx.x.xx.x.xx.x.xx.x.xx.x.xx",
            "snare": "........X...............X.......",
            "china": "x...x...x...x...x...x...x...x...",
        }},
        drums="Snare on beat 3 and quarter-note hats or china keep the 4/4 grid while the kick doubles the "
              "guitar's odd-grouped syncopation; heavily quantized, sample-replaced; ghost-note fills.",
        form=(("ambient intro", 8), ("riff", 16), ("verse", 16), ("chorus", 8), ("riff", 8), ("verse", 16),
              ("chorus", 8), ("clean interlude", 16), ("breakdown", 16), ("chorus", 16), ("outro", 8)),
        instruments=("7- or 8-string guitar", "bass (or bass-replaced 8-string)", "programmed or sample-replaced drums",
                     "harsh and clean vocals", "ambient synth pads"),
        sound_design="7-string drop A or B standard; 8-string F or F# standard (Meshuggah, Animals as Leaders) or "
                     "drop E; boosted high-gain (Tube Screamer into Mesa or Axe-Fx/amp sims), extremely gated so "
                     "chugs stop dead; the 'djent' is the midrange pluck of a palm-muted open low string.",
        production="Surgically edited and quantized, DI-reamped guitars, sample-based drums; low end tightly "
                   "controlled with multiband compression; loud masters; ambient sections wide with reverbs.",
        theory="Polymeter: riff cycles of 5, 7, 11 or 23 16ths repeat over a 4/4 pulse and realign at the "
               "phrase end; harmony is a pedal tone plus dissonant upper structures; rhythmic displacement is "
               "the main compositional tool.",
        mix=Mix(lufs=(-8, -5), lra=(3, 5), low_end="very heavy", tone="bright", width="wide"),
    ),
    # ------------------------------------------------------------------ alternative, core and crossovers
    Genre(
        name="nu metal",
        family="metal and punk",
        aliases=("numetal", "rap metal", "aggro metal"),
        parent="metal",
        description="Downtuned, groove-first metal with hip-hop rhythm and attitude: bouncy syncopated 7-string "
                    "riffs, rapped and screamed vocals, turntables and samples; angsty and physical.",
        era="California and the US, 1994-2003",
        touchstones=("Korn (Korn)", "Deftones (White Pony)", "Limp Bizkit", "Slipknot (Slipknot)",
                     "Linkin Park (Hybrid Theory)", "System of a Down (Toxicity)", "Coal Chamber"),
        tempo=(85, 120),
        feel="hip-hop bounce: syncopated 16ths, slightly swung, half-time choruses",
        swing=54,
        modes=("phrygian", "minor"),
        keys=("A phrygian", "B phrygian", "C# minor", "D minor"),
        progressions=(
            "I5-II5",
            "I5-II5-I5-bV5",
            "I5-III5-II5",
            "minor: i-VI-III-VII",
            "minor: i-VI-VII",
        ),
        harmonic_rhythm=1,
        harmony="Minimal: single low-note bounce riffs on the open low string with b2 and b5 jumps; dissonant "
                "high-string harmonics and clean minor arpeggios in verses; anthemic minor choruses (i-VI-III-VII) "
                "in the Linkin Park mould.",
        voicing="power",
        comping="push",
        bass_style="syncopated",
        bass="5-string bass in low B or A, slapped and percussive (Fieldy), mirroring the kick; or a fat sub "
             "doubling the guitar.",
        melody_density="medium",
        melody_scale="phrygian",
        melody="Rapped or half-spoken verses, whispered-to-screamed dynamics, big melodic sung choruses; "
               "guitar 'melodies' are dissonant harmonics, slides and noise; DJ scratches and synth hooks fill gaps.",
        groove={"step": 0.25, "swing": 54, "pattern": {
            "kick":       "x..x..x...x.....",
            "snare":      "....X..o....X...",
            "closed hat": "x.x.x.x.x.x.x...",
            "open hat":   "..............x.",
        }},
        drums="Hip-hop-derived grooves: syncopated kick, fat snare on 2 and 4 with ghost notes, swung hats; "
              "half-time choruses; percussion layers (Slipknot); breakdowns lock to the riff.",
        form=(("intro", 8), ("verse", 16), ("pre-chorus", 4), ("chorus", 8), ("verse", 16), ("pre-chorus", 4),
              ("chorus", 8), ("breakdown", 8), ("bridge", 8), ("chorus", 16), ("outro", 4)),
        instruments=("7-string guitar", "5-string bass", "drum kit", "rapped and sung vocals", "turntables",
                     "samples and synths"),
        sound_design="7-string A standard (Korn), drop B or drop C on 6-string; scooped Mesa Rectifier tone; "
                     "clanky slap bass; DJ scratches, glitchy samples, industrial textures.",
        production="Modern loud mix with hip-hop low end: big kick and bass, dense guitars, vocals stacked and "
                   "doubled with effects; dynamic drop-outs for verses.",
        theory="Rhythm over harmony: hip-hop syncopation and bounce applied to single-note riffs, with the "
               "phrygian b2 and tritone as the main colours; verse/chorus contrast is timbral (rap vs. sung).",
        mix=Mix(lufs=(-9, -6), lra=(3, 7), low_end="very heavy", tone="neutral", width="wide"),
    ),
    Genre(
        name="metalcore",
        family="metal and punk",
        aliases=("melodic metalcore",),
        parent="hardcore punk",
        description="Hardcore punk's breakdowns and energy fused with melodic death metal riffs: harsh verses, "
                    "soaring clean choruses and chug-heavy half-time breakdowns.",
        era="US late 1990s (Earth Crisis, Converge, Botch); mainstream 2002-2010s",
        touchstones=("Killswitch Engage (Alive or Just Breathing)", "As I Lay Dying", "Converge (Jane Doe)",
                     "August Burns Red", "Parkway Drive (Horizons)", "Architects", "Bring Me the Horizon (Sempiternal)"),
        tempo=(100, 190),
        feel="fast skank and d-beat verses, big half-time choruses and syncopated breakdowns",
        modes=("minor", "phrygian", "harmonic minor"),
        keys=("C minor", "D minor", "B minor", "C# minor"),
        progressions=(
            "i-VI-III-VII",
            "VI-VII-i",
            "i-VI-VII-III",
            "I5-VI5-VII5",
            "phrygian: I5-II5",
        ),
        harmonic_rhythm=1,
        harmony="Melodeath-style harmonized minor riffs in verses; choruses are pop-minor (i-VI-III-VII) with "
                "add9 and open-string ringing chords; breakdowns are a single open low note plus b2 and b5 "
                "stabs.",
        voicing="power",
        comping="push",
        bass_style="syncopated",
        bass="Doubles the guitar's low-string rhythm; in breakdowns plays the chug pattern with the kick; sub "
             "drops under the first hit of a breakdown.",
        melody_density="medium",
        melody_scale="minor",
        melody="Screamed/growled verses alternate with soaring clean sung choruses (often a second vocalist); "
               "guitar leads are melodeath-style harmonized lines; breakdowns have no melody at all.",
        groove={"step": 0.25, "pattern": {
            "kick":  "x...x...x...x...x..x..x.x..x..x.",
            "snare": "..X...X...X...X.........X.......",
            "crash": "x...x...x...x...................",
            "china": "................x...x...x...x...",
        }},
        drums="Skank beats and blasts in verses, open double-time backbeats under choruses; breakdowns put the "
              "snare on beat 3 (half time) with kicks doubling the chug rhythm (3+3+2 groupings) and china "
              "on quarters.",
        form=(("intro", 8), ("verse", 16), ("pre-chorus", 8), ("chorus", 8), ("verse", 16), ("pre-chorus", 8),
              ("chorus", 8), ("bridge", 8), ("breakdown", 16), ("chorus", 16), ("outro", 4)),
        instruments=("two high-gain guitars", "bass", "drum kit with double kick (sample-replaced)",
                     "harsh vocal", "clean vocal", "synths and pads (modern)"),
        sound_design="Drop C, drop B or drop A (7-string); tight modern high-gain (5150/Rectifier or amp sims) "
                     "with a boost; clicky sample kicks, snappy snare; atmospheric synths and drops (sub booms, "
                     "reverse cymbals) into breakdowns.",
        production="Loud, edited and quantized; guitars quad-tracked and wide, clean vocals huge and tuned; "
                   "breakdowns emphasized by sub drops and silence before the hit.",
        theory="Contrast structure: harsh vs. clean, fast vs. half-time; the breakdown is a rhythmic, not "
               "harmonic, climax (syncopated chugs on one pitch); choruses use pop-minor loops.",
        mix=Mix(lufs=(-8, -5), lra=(3, 6), low_end="very heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="deathcore",
        family="metal and punk",
        aliases=("death core",),
        parent="metalcore",
        description="Death metal's blasts, low growls and chromatic riffing combined with metalcore's crushing "
                    "breakdowns; extremely low tunings and maximal heaviness.",
        era="Southwestern US and California, 2004-2010; symphonic revival in the 2020s",
        touchstones=("Suicide Silence (The Cleansing)", "Whitechapel (This Is Exile)", "Job for a Cowboy (Doom)",
                     "Despised Icon", "Thy Art Is Murder", "Lorna Shore (Pain Remains)", "Carnifex"),
        tempo=(100, 230),
        feel="blast-beat sections slamming into half- or quarter-time breakdowns",
        modes=("phrygian", "locrian", "harmonic minor"),
        keys=("A phrygian", "G# phrygian", "B phrygian", "F# phrygian"),
        progressions=(
            "I5-II5-I5",
            "I5-bV5-II5-I5",
            "locrian: I5-V5-I5",
            "harmonic minor: i-VI-V",
            "minor: i-VI-iv-V",
        ),
        harmonic_rhythm=1,
        harmony="Breakdowns on the open low string with b2/b5 dissonances; tremolo sections in harmonic minor "
                "or chromatic; modern symphonic deathcore adds orchestral minor progressions (i-VI-iv-V) under "
                "blasts.",
        voicing="power",
        comping="push",
        bass_style="syncopated",
        bass="Mirrors the low guitar chugs; sub drops and 808-like booms under breakdown hits.",
        melody_density="medium",
        melody_scale="phrygian",
        melody="Vocals are extreme: low gutturals, pig squeals, high shrieks, often in rhythmic unison with "
               "the riff; leads are dissonant tremolo or harmonic-minor sweeps; symphonic bands add "
               "orchestral themes.",
        groove={"step": 0.125, "pattern": {
            "kick":  "x.....x.x.......x.....x.x...xxxx",
            "snare": "................X...............",
            "china": "x.......x.......x.......x.......",
        }},
        drums="Blast beats (traditional, bomb, gravity) at 200+ bpm, then breakdowns: snare on beat 3 (or "
              "every other bar), china quarters, kick doubling chugs with 32nd-note triggers; heavily "
              "sample-replaced.",
        form=(("intro", 4), ("verse", 16), ("blast section", 8), ("chorus", 8), ("verse", 16), ("breakdown", 8),
              ("bridge", 8), ("blast section", 8), ("final breakdown", 16), ("outro", 4)),
        instruments=("7- or 8-string guitar", "bass", "sample-replaced drum kit", "extreme vocals",
                     "orchestral and synth layers (modern)"),
        sound_design="Drop A, drop G or lower (7-string, baritone or 8-string); very tight high gain with heavy "
                     "gating; clicky kicks, ringing snares; sub drops and impact samples.",
        production="As loud and dense as possible; extreme editing; sub-bass reinforcement under breakdowns; "
                   "vocals layered (lows and highs doubled).",
        theory="Takes death metal chromaticism and metalcore's breakdown to extremes; tension built through "
               "tempo halving (blast to half to quarter time) rather than harmony.",
        mix=Mix(lufs=(-8, -5), lra=(3, 5), low_end="very heavy", tone="neutral", width="wide"),
    ),
    Genre(
        name="industrial metal",
        family="metal and punk",
        aliases=("neue deutsche harte", "ndh", "cyber metal"),
        parent="industrial",
        description="Metal riffs fused with industrial electronics: drum machines, sequenced synths, samples and "
                    "machine-tight repetition; cold, mechanical and militaristic.",
        era="Late 1980s (Ministry, Godflesh); 1990s US (Nine Inch Nails, Fear Factory); Germany's Neue Deutsche Harte",
        touchstones=("Ministry (Psalm 69)", "Godflesh (Streetcleaner)", "Nine Inch Nails (The Downward Spiral)",
                     "Fear Factory (Demanufacture)", "Rammstein (Mutter)", "Marilyn Manson (Antichrist Superstar)"),
        tempo=(90, 140),
        feel="machine-straight, quantized grid; marching quarter and 8th pulses",
        modes=("phrygian", "minor"),
        keys=("E phrygian", "D minor", "C# minor", "B minor"),
        progressions=(
            "I5-II5",
            "I5-II5-I5-bV5",
            "minor: I5-VI5-VII5",
            "minor: i-VI-III-VII",
            "minor: i-iv-VI-v",
        ),
        harmonic_rhythm=1,
        harmony="One- or two-chord riffs on palm-muted low strings repeated as loops; phrygian b2 and tritone; "
                "synth pads or strings add minor triads in choruses; harmony matters less than the grid.",
        voicing="power",
        comping="eighths",
        bass_style="eighths",
        bass="Sequenced synth bass in 8ths or 16ths locked to the guitar chug, often layered with electric bass.",
        melody_density="sparse",
        melody_scale="phrygian",
        melody="Chanted, barked or distorted vocals with short repeated phrases (Rammstein's baritone, Reznor's "
               "whisper-to-scream); synth arpeggios and sampled noise act as hooks.",
        groove={"step": 0.25, "pattern": {
            "kick":       "x...x.x.x...x.x.",
            "snare":      "....X.......X...",
            "clap":       "....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.",
        }},
        drums="Drum machine or quantized drums layered with samples; double kick perfectly synced to the guitar "
              "(Fear Factory); NDH marches with kick on quarters; snare often layered with claps or metal hits.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("bridge", 8),
              ("breakdown", 8), ("chorus", 16), ("outro", 8)),
        instruments=("distorted guitar", "synth bass and electric bass", "drum machine and samples", "synthesizers",
                     "processed vocal"),
        sound_design="Drop D, drop C or 7-string B; ultra-gated chugs; distorted drum machines, metal-hit "
                     "samples, noisy synths, bitcrushed vocals; Rammstein's huge, clean palm mutes.",
        production="Grid-tight, everything quantized; guitars and synths interlocked; vocals often distorted or "
                   "megaphone-filtered; modern masters loud with controlled low end.",
        theory="Repetition and the machine grid as aesthetic; harmonic stasis on the phrygian b2; the riff "
               "functions like a sequencer loop.",
        mix=Mix(lufs=(-9, -6), lra=(3, 6), low_end="heavy", tone="neutral", width="wide"),
    ),
    Genre(
        name="folk metal",
        family="metal and punk",
        aliases=("pagan metal", "viking metal"),
        parent="metal",
        description="Metal woven with traditional folk instruments and melodies: fiddles, pipes and accordions "
                    "over riffs, drinking-song choruses and humppa or jig rhythms.",
        era="Skyclad in England (early 1990s); Scandinavia and the Alps, late 1990s-2000s",
        touchstones=("Skyclad", "Finntroll", "Korpiklaani", "Eluveitie (Slania)", "Ensiferum", "Moonsorrow",
                     "Turisas"),
        tempo=(110, 200),
        feel="humppa/polka oom-pah or jig-like pulses mixed with metal double kick",
        modes=("minor", "dorian", "mixolydian"),
        keys=("E minor", "A minor", "D minor", "D dorian"),
        progressions=(
            "i-VII-VI-VII",
            "i-VII-i",
            "i-VI-VII-i",
            "dorian: i-IV-i-VII",
            "mixolydian: I-VII-IV-I",
        ),
        harmonic_rhythm=1,
        harmony="Modal folk harmony: aeolian i-bVII-bVI shuttles, dorian IV for brighter tunes, mixolydian "
                "bVII in drinking songs; drones from bagpipe or hurdy-gurdy hold the tonic under chords.",
        voicing="power",
        comping="eighths",
        bass_style="root_fifth",
        bass="Root-fifth oom-pah in humppa sections, driving root 8ths in metal sections; drones on the tonic.",
        melody_density="busy",
        melody_scale="dorian",
        melody="Folk instruments carry dance-tune melodies in 8th and triplet runs, doubled by guitar in "
               "unison or 3rds; gang-sung choruses; vocals mix harsh and clean, often in native languages.",
        groove={"step": 0.25, "pattern": {
            "kick":       "x...x...x...x...x.x.x.x.x.x.x.x.",
            "snare":      "..x...x...x...x.....X.......X...",
            "closed hat": "..x...x...x...x.................",
            "crash":      "x...............x...x...x...x...",
        }},
        drums="Humppa beat (kick on beats, snare on offbeats, like a polka) alternating with double-kick metal "
              "sections; frame drums or bodhran layers; tom-heavy marching parts in viking styles.",
        form=(("folk intro", 8), ("verse", 16), ("chorus", 8), ("instrumental tune", 8), ("verse", 16), ("chorus", 8),
              ("folk interlude", 16), ("solo", 8), ("chorus", 16), ("outro", 8)),
        instruments=("distorted guitars", "bass", "drum kit", "fiddle", "accordion", "tin whistle or bagpipes",
                     "hurdy-gurdy", "harsh and clean vocals"),
        sound_design="E or D standard; mid-gain guitars bright enough to sit with acoustic folk instruments; "
                     "accordion and fiddle close-miked; choirs and gang vocals.",
        production="Folk instruments featured up front and panned opposite the lead guitar; drums punchy; "
                   "vocals big and communal; sounds like a festival.",
        theory="Modal (aeolian, dorian, mixolydian) folk melodies and dance rhythms (polka 2/4, jig 6/8 feel) "
               "superimposed on metal; drones replace functional bass motion.",
        mix=Mix(lufs=(-9, -6), lra=(4, 7), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="gothic metal",
        family="metal and punk",
        aliases=("goth metal",),
        parent="doom metal",
        description="Melancholic, romantic metal combining doom's heaviness with gothic rock's darkness: slow "
                    "minor riffs, lush keyboards, and beauty-and-the-beast vocal contrasts.",
        era="England and Norway, early-mid 1990s (Paradise Lost, Theatre of Tragedy); Type O Negative in New York",
        touchstones=("Paradise Lost (Draconian Times)", "Type O Negative (October Rust)", "Theatre of Tragedy",
                     "Tiamat (Wildhoney)", "Moonspell", "Lacuna Coil (Comalies)"),
        tempo=(70, 130),
        feel="slow-to-mid tempo, heavy and swaying; ballads in 6/8 or 12/8",
        modes=("minor", "harmonic minor"),
        keys=("D minor", "E minor", "C minor", "B minor"),
        progressions=(
            "i-VI-III-VII",
            "i-iv-VI-V",
            "i-VI-iv-V",
            "i-III-VI-VII",
            "harmonic minor: i-V-VI-iv",
        ),
        harmonic_rhythm=0.5,
        harmony="Romantic minor: i-VI-III-VII and i-iv-VI-V with harmonic-minor V; keyboards add sus and add9 "
                "colours; organ and string pads hold triads under power chords; occasional major-key "
                "bittersweet turns.",
        voicing="power",
        comping="half_notes",
        bass_style="root",
        bass="Sustained roots and 8ths following chords; in Type O Negative a fuzzy, prominent bass carries "
             "the riff.",
        melody_density="medium",
        melody_scale="harmonic minor",
        melody="Deep baritone croon or death growl answered by ethereal female soprano; long, sorrowful vocal "
               "lines; lead guitar plays slow, singing melodies with lots of vibrato.",
        groove={"step": 0.25, "pattern": {
            "kick":  "x.......x.x.....",
            "snare": "....X.......X...",
            "ride":  "x.x.x.x.x.x.x.x.",
            "crash": "x...............",
        }},
        drums="Mid-tempo backbeat, ride or crash 8ths, tom-heavy builds; occasional double kick in heavier "
              "parts; restrained so the atmosphere breathes.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("bridge", 16),
              ("solo", 8), ("chorus", 16), ("outro", 16)),
        instruments=("distorted guitars", "bass", "drum kit", "keyboards (organ, strings, piano)",
                     "male baritone or growl", "female soprano"),
        sound_design="D standard, C standard or drop C; warm mid-gain guitars, lots of chorus and reverb on "
                     "cleans; church organ and string pads; piano interludes.",
        production="Lush, reverberant and atmospheric; keys wide and prominent; vocals with long reverb tails; "
                   "less compressed than modern metal.",
        theory="Romantic-era minor harmony (harmonic-minor V, iv, VI) at doom tempos; timbral contrast between "
               "two voices is a structural device.",
        mix=Mix(lufs=(-10, -7), lra=(4, 8), low_end="heavy", tone="dark", width="wide"),
    ),
    Genre(
        name="grindcore",
        family="metal and punk",
        aliases=("grind", "goregrind", "deathgrind"),
        parent="hardcore punk",
        description="Short, savage bursts of blast beats, hardcore punk and death metal: songs under two minutes "
                    "(some seconds long), noise-laden riffs and screamed or growled vocals.",
        era="Birmingham, England, mid-1980s (Napalm Death); US (Repulsion, Terrorizer) in parallel",
        touchstones=("Napalm Death (Scum)", "Repulsion (Horrified)", "Carcass (Reek of Putrefaction)",
                     "Terrorizer (World Downfall)", "Pig Destroyer", "Nasum", "Brutal Truth"),
        tempo=(150, 280),
        feel="blast beats at full speed alternating with punk beats and short mid-tempo grooves",
        modes=("phrygian", "locrian", "minor"),
        keys=("E phrygian", "D phrygian", "C# minor", "B minor"),
        progressions=(
            "I5-bV5-II5",
            "I5-II5-IV5-bV5",
            "I5-VII5-bV5",
            "locrian: I5-V5",
            "minor: I5-III5-IV5-bV5",
        ),
        harmonic_rhythm=2,
        harmony="Barely there: chromatic power-chord runs, tritones, semitone grinds and open-string noise; "
                "crust/punk progressions in groove parts.",
        voicing="power",
        comping="pulse_16",
        bass_style="sixteenths",
        bass="Distorted, often as loud as the guitar (sometimes replacing a second guitar), mirroring riffs.",
        melody_density="busy",
        melody_scale="chromatic",
        melody="No melody to speak of: screamed and growled vocals traded between two voices, riffs are "
               "tremolo chromatic blur.",
        groove={"step": 0.25, "pattern": {
            "kick":  "x...x...x...x...x.x.x.x.x.x.x.x.",
            "snare": "..X...X...X...X..x.x.x.x.x.x.x.x",
            "crash": "x...x...x...x...x.x.x.x.x.x.x.x.",
        }},
        drums="Blast beats (traditional, hammer and gravity blasts) are the core, switched abruptly with fast "
              "skank/punk beats and short half-time grooves; songs stop and start on a hit.",
        form=(("intro hit", 1), ("blast", 8), ("punk section", 4), ("blast", 8), ("groove", 4), ("blast", 4),
              ("end hit", 1)),
        instruments=("distorted guitar", "distorted bass", "drum kit", "screamed and growled vocals"),
        sound_design="Drop B to standard tuning; fuzzy, saturated, HM-2 or solid-state distortion; noise and "
                     "feedback welcome; snare cracking and loud.",
        production="Raw, loud and compressed, little separation; drums roomy; vocals distorted; lo-fi is "
                   "authentic, modern grind (Pig Destroyer) is cleaner but still harsh.",
        theory="Brevity and velocity as form: micro-songs made of 2-4 riff fragments; blast beat as the basic "
               "unit; harmony reduced to chromatic noise.",
        mix=Mix(lufs=(-10, -6), lra=(2, 5), low_end="heavy", tone="bright", width="moderate"),
    ),
    # ------------------------------------------------------------------ punk and its descendants
    Genre(
        name="punk",
        family="metal and punk",
        aliases=("punk rock", "77 punk", "first wave punk"),
        parent="rock",
        description="Stripped-down, fast and loud rock: three-chord barre progressions, down-stroked 8ths, "
                    "short songs and sneering, shouted vocals; DIY and rebellious.",
        era="New York (Ramones, CBGB) and London (Sex Pistols, The Clash), 1975-1979",
        touchstones=("Ramones (Ramones)", "Sex Pistols (Never Mind the Bollocks)", "The Clash (The Clash)",
                     "Buzzcocks", "The Damned", "Dead Boys", "Stiff Little Fingers"),
        tempo=(140, 210),
        feel="straight, driving 8th notes; everything downstroked",
        modes=("major", "mixolydian", "minor"),
        keys=("A major", "E major", "D major", "G major"),
        progressions=(
            "I5-IV5-V5",
            "I5-IV5-I5-V5",
            "I5-bVII5-IV5",
            "I5-V5-VI5-IV5",
            "I5-bIII5-IV5-I5",
        ),
        harmonic_rhythm=1,
        harmony="Three-chord rock: I-IV-V barre or power chords, mixolydian bVII and chromatic bIII borrowed "
                "from 60s garage rock; occasional minor key; no extensions.",
        voicing="power",
        comping="eighths",
        bass_style="eighths",
        bass="Downpicked root 8ths (Dee Dee Ramone), relentless; occasional walk-ups between chords.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Shouted or sneered vocals on a narrow range, chant-like hooks and gang 'oi'/'hey' backups; "
               "short, simple guitar solos (often just the melody or a one-note rhythm).",
        groove={"step": 0.25, "pattern": {
            "kick":       "x.x.....x.x.....",
            "snare":      "....X.......X...",
            "closed hat": "x.x.x.x.x.x.x.x.",
            "crash":      "x...............",
        }},
        drums="Fast backbeat with 8th hats or crash, kick on 1 and 3 with pickups; snare rolls into choruses; "
              "simple, no-nonsense, often slightly rushing.",
        form=(("count-in", 1), ("intro", 4), ("verse", 8), ("chorus", 8), ("verse", 8), ("chorus", 8),
              ("solo", 8), ("chorus", 8), ("end", 2)),
        instruments=("overdriven electric guitar", "electric bass", "drum kit", "lead vocal", "gang vocals"),
        sound_design="E standard; Marshall or Hiwatt crunch, moderate gain, barre chords; picked bass; small, "
                     "dry drum kit.",
        production="Live-in-the-room, minimal overdubs (often one rhythm guitar), dry vocals; 2-3 minutes; "
                   "energy over polish.",
        theory="Reduces rock to I-IV-V and bVII mixolydian borrowings at high tempo; rhythmic monotony of "
               "downstroked 8ths is the defining texture.",
        mix=Mix(lufs=(-11, -7), lra=(4, 7), low_end="moderate", tone="bright", width="moderate"),
    ),
    Genre(
        name="pop punk",
        family="metal and punk",
        aliases=("pop-punk revival", "easycore"),
        parent="punk",
        description="Punk's speed and power chords with pop melody: catchy major-key hooks, bright palm-muted "
                    "verses, big singalong choruses and youthful, snotty or heartfelt vocals.",
        era="California, early-mid 1990s (Green Day, Blink-182); 2000s mainstream; 2010s and 2020s revivals",
        touchstones=("Descendents (Milo Goes to College)", "Green Day (Dookie)", "Blink-182 (Enema of the State)",
                     "New Found Glory", "Fall Out Boy (Take This to Your Grave)", "Paramore (Riot!)",
                     "The Wonder Years"),
        tempo=(140, 210),
        feel="straight, fast skank and backbeat; half-time bridges",
        modes=("major", "minor"),
        keys=("D major", "E major", "C major", "B major"),
        progressions=(
            "I5-V5-VI5-IV5",
            "VI5-IV5-I5-V5",
            "I5-IV5-VI5-V5",
            "I5-III5-IV5-V5",
            "IV5-I5-V5-VI5",
        ),
        harmonic_rhythm=1,
        harmony="Four-chord pop loops as power chords (I-V-vi-IV and rotations), palm-muted single-chord verses, "
                "key change or IV-iv borrowing for bittersweet bridges; 3-note barre or 5ths with open strings.",
        voicing="power",
        comping="eighths",
        bass_style="eighths",
        bass="Picked root 8ths with melodic walk-ups and passing notes into chorus downbeats (Mark Hoppus, "
             "Mike Dirnt); occasional bass-only breaks.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Bright, nasal lead vocal in the upper register, verses conversational, choruses big and "
               "stepwise with 'whoa-oh' gang hooks; octave guitar lead riffs instead of long solos.",
        groove={"step": 0.25, "pattern": {
            "kick":  "x...x...x...x...x.....x.x.......",
            "snare": "..X...X...X...X.....X.......X...",
            "crash": "x...x...x...x...x...............",
            "ride":  "................x.x.x.x.x.x.x.x.",
        }},
        drums="Fast skank (polka) beats in choruses, open-hat or ride backbeats, tom-heavy verse grooves, "
              "busy Travis Barker-style fills and snare rolls; half-time breakdowns before the last chorus.",
        form=(("intro", 8), ("verse", 16), ("pre-chorus", 4), ("chorus", 8), ("verse", 16), ("pre-chorus", 4),
              ("chorus", 8), ("bridge", 8), ("chorus", 16), ("outro", 4)),
        instruments=("two distorted electric guitars", "electric bass", "drum kit", "lead vocal",
                     "gang backing vocals"),
        sound_design="E standard or Eb standard (drop D for heavier parts); Mesa Rectifier or Marshall with "
                     "medium-high gain but clear; bright, compressed acoustic-ish chord attack.",
        production="Glossy and tight: double/quad-tracked guitars wide, vocals doubled and tuned, bright drums "
                   "with sampled reinforcement, loud masters.",
        theory="Pop's four-chord loops at punk tempo, with power chords making the major/minor ambiguity of "
               "vi and iii vanish; the hook lives in the vocal over a constant 8th-note pulse.",
        mix=Mix(lufs=(-8, -6), lra=(3, 6), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="hardcore punk",
        family="metal and punk",
        aliases=("us hardcore", "melodic hardcore", "skate punk", "nyhc"),
        parent="punk",
        description="Faster, harder, shorter punk: blistering skank beats, shouted vocals, gang chants and "
                    "half-time mosh parts; intense, communal and political.",
        era="Washington DC, Los Angeles and New York, 1980-1986",
        touchstones=("Black Flag (Damaged)", "Minor Threat", "Bad Brains (Bad Brains)", "Dead Kennedys",
                     "Cro-Mags (The Age of Quarrel)", "Agnostic Front", "Gorilla Biscuits"),
        tempo=(160, 250),
        feel="very fast skank beats switched with half-time two-step mosh parts",
        modes=("minor", "major", "phrygian"),
        keys=("E minor", "A minor", "D major", "E major"),
        progressions=(
            "I5-III5-IV5-I5",
            "I5-VII5-VI5-VII5",
            "I5-bII5-I5",
            "major: I5-IV5-V5",
            "phrygian: I5-II5-III5-II5",
        ),
        harmonic_rhythm=2,
        harmony="Power chords moving fast in minor-pentatonic or chromatic shapes; I-IV-V in melodic hardcore; "
                "b2 and tritone stabs in mosh parts; one chord per beat or two in the fast parts.",
        voicing="power",
        comping="eighths",
        bass_style="eighths",
        bass="Picked root 8ths at speed, locked with the kick; drives mosh parts with sustained low roots.",
        melody_density="busy",
        melody_scale="minor pentatonic",
        melody="Barked, shouted vocals with dense rhythmic lyrics; gang-chant choruses; little lead guitar "
               "beyond noisy, short solos (Greg Ginn); melodic hardcore and skate punk add sung harmonies.",
        groove={"step": 0.25, "pattern": {
            "kick":  "x...x...x...x...x.....x.x.....x.",
            "snare": "..X...X...X...X.........X.......",
            "crash": "x...x...x...x...x...x...x...x...",
        }},
        drums="Skank beat (kick on the beat, snare on the 'and', crash riding) at breakneck speed; "
              "half-time two-step with snare on 3 for mosh parts; stops and gang-shout breaks.",
        form=(("intro", 4), ("verse", 8), ("chorus", 8), ("verse", 8), ("chorus", 8), ("mosh part", 8),
              ("chorus", 8), ("end", 1)),
        instruments=("distorted electric guitar", "electric bass", "drum kit", "shouted lead vocal",
                     "gang vocals"),
        sound_design="E standard or drop D; crunchy mid-gain Marshall or solid-state tone; picked, overdriven "
                     "bass; small cracking snare.",
        production="Fast, raw, live-tracked; songs 1-2 minutes; vocals loud and up front, gang vocals roomy; "
                   "later NYHC more metallic and polished.",
        theory="Maximizes punk's tempo and compresses form; the skank vs. two-step half-time switch is the "
               "main structural device; harmony is power-chord motion in minor pentatonic and chromatic steps.",
        mix=Mix(lufs=(-10, -7), lra=(3, 6), low_end="moderate", tone="bright", width="moderate"),
    ),
    Genre(
        name="post-hardcore",
        family="metal and punk",
        aliases=("scene post-hardcore",),
        parent="hardcore punk",
        description="Hardcore's intensity opened up with dynamics, angular dissonant guitars, unusual "
                    "structures and both screamed and sung vocals; tense, emotional and experimental.",
        era="Washington DC, mid-late 1980s (Fugazi, Rites of Spring); 2000s screamo-tinged wave",
        touchstones=("Fugazi (Repeater)", "Refused (The Shape of Punk to Come)",
                     "At the Drive-In (Relationship of Command)", "Glassjaw", "Thursday (Full Collapse)",
                     "La Dispute", "Touche Amore"),
        tempo=(100, 180),
        feel="driving 8ths that drop into sparse, tense verses and explode in loud choruses; occasional odd meters",
        modes=("minor", "major", "dorian"),
        keys=("D minor", "E minor", "A minor", "G major"),
        progressions=(
            "i-VI-III-VII",
            "VI-VII-i",
            "i-VIadd9-IIIadd9-VII",
            "dorian: i-IV",
            "major: I-IV-vi-V",
        ),
        harmonic_rhythm=1,
        harmony="Open-string add9 and sus chords, dissonant intervals (m2, tritone) ringing against open "
                "strings, angular single-note lines instead of chords; dorian and minor; chromatic shifts.",
        voicing="open",
        comping="eighths",
        bass_style="syncopated",
        bass="Melodic and independent, often carrying the riff while guitars play dissonant textures "
             "(Joe Lally); punchy and mid-forward.",
        melody_density="medium",
        melody_scale="minor",
        melody="Sung verses rising to screamed climaxes, sometimes two vocalists trading; guitars play "
               "interlocking, angular riffs and harmonics; hooks are shouted refrains.",
        groove={"step": 0.25, "pattern": {
            "kick":  "x.....x...x.x...",
            "snare": "....X.......X..o",
            "ride":  "x.x.x.x.x.x.x.x.",
            "crash": "x...............",
        }},
        drums="Dynamic, inventive: tom grooves in quiet verses, open-hat or ride backbeats in choruses, "
              "fast skank bursts, syncopated hits with the riff; dramatic builds.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("bridge", 16),
              ("climax", 8), ("chorus", 8), ("outro", 8)),
        instruments=("two electric guitars", "electric bass", "drum kit", "sung and screamed vocals"),
        sound_design="E standard, drop D or alternate tunings; mid-gain amps (Marshall, Orange) with "
                     "edge-of-breakup cleans; delays and fuzz for texture; punchy room drums.",
        production="Dynamic range kept for loud-quiet contrast; guitars spread left/right with different parts; "
                   "vocals raw; 2000s scene records glossier.",
        theory="Expands hardcore with dynamics, dissonant open-string voicings and through-composed or "
               "irregular forms; harmonic ambiguity from add9/sus chords and pedal tones.",
        mix=Mix(lufs=(-9, -7), lra=(4, 8), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="emo",
        family="metal and punk",
        aliases=("midwest emo", "emocore", "screamo", "emotional hardcore"),
        parent="hardcore punk",
        description="Emotionally raw, confessional punk-derived rock: twinkly clean guitar arpeggios, odd "
                    "tunings, loud-quiet dynamics and earnest, strained vocals.",
        era="Washington DC 1985 (Rites of Spring, Embrace); Midwest 1990s; mainstream third wave in the 2000s",
        touchstones=("Rites of Spring", "Sunny Day Real Estate (Diary)", "Jawbreaker", "Cap'n Jazz",
                     "American Football (American Football)", "Mineral", "The Get Up Kids",
                     "Jimmy Eat World (Clarity)"),
        tempo=(90, 180),
        feel="mid-tempo, with mixed meters (6/8, 7/8 passages) and loud-quiet swells",
        modes=("major", "lydian", "mixolydian"),
        keys=("E major", "A major", "D major", "F major"),
        progressions=(
            "Imaj7-IVmaj7",
            "IVmaj7-V-iii7-vi7",
            "I-iii-IV-iv",
            "vi7-IVmaj7-Iadd9-Vsus4",
            "lydian: Imaj7-II",
        ),
        harmonic_rhythm=1,
        harmony="Jazz-tinged open-string chords: maj7, add9, sus2 and 6ths ringing against open strings in "
                "alternate tunings; IV-iv borrowed minor for heartbreak; lydian colour; distorted choruses "
                "collapse these into power chords.",
        voicing="open",
        comping="arpeggio_updown",
        bass_style="syncopated",
        bass="Melodic, counter-melodic lines under arpeggios; root 8ths in loud sections.",
        melody_density="medium",
        melody_scale="major",
        melody="Twinkly interlocking guitar arpeggios and tapped lines as hooks; vocals intimate and cracked "
               "in verses, yelled or screamed at the climax; diary-like phrasing that ignores bar lines.",
        groove={"step": 0.25, "pattern": {
            "kick":       "x.....x...x.....",
            "snare":      "....X..o....X.o.",
            "closed hat": "x.x.x.x.x.x.x.x.",
            "crash":      "x...............",
        }},
        drums="Busy, musical drumming with ghost notes, ride patterns, tom grooves and frequent fills; "
              "meter shifts handled smoothly; explodes into crash-heavy 8ths at climaxes.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("bridge", 16),
              ("build", 8), ("climax", 16), ("outro", 8)),
        instruments=("clean electric guitars", "distorted guitar", "electric bass", "drum kit", "lead vocal",
                     "trumpet (occasional)"),
        sound_design="Open and alternate tunings (FACGCE in American Football, open D, drop D); clean Fender "
                     "Twin or Roland Jazz Chorus tones with light compression; fuzz or crunchy Marshall for "
                     "loud sections.",
        production="Intimate and natural, wide dynamic range; guitars panned to interlock; vocals dry and close; "
                   "third-wave records loud and polished.",
        theory="Jazz-like extended chords via open strings and alternate tunings, mixed meters and through-"
               "composed builds; emotional arc built by dynamics more than harmony.",
        mix=Mix(lufs=(-11, -8), lra=(5, 9), low_end="moderate", tone="warm", width="wide"),
    ),
    Genre(
        name="ska punk",
        family="metal and punk",
        aliases=("skacore", "third wave ska"),
        parent="ska",
        description="Ska's offbeat upstrokes and horn section welded to punk's speed and distortion: bouncy skank "
                    "verses that explode into punk choruses; fun, fast and danceable.",
        era="California and Boston, late 1980s-1990s (Operation Ivy, Mighty Mighty Bosstones); third-wave boom 1995-1999",
        touchstones=("Operation Ivy (Energy)", "The Mighty Mighty Bosstones", "Less Than Jake",
                     "Reel Big Fish (Turn the Radio Off)", "Streetlight Manifesto", "Rancid", "Goldfinger"),
        tempo=(140, 210),
        feel="ska offbeat upstrokes alternating with straight punk 8ths and skank beats",
        modes=("major", "minor", "mixolydian"),
        keys=("C major", "G major", "D major", "A minor"),
        progressions=(
            "I-IV-V-IV",
            "I-vi-IV-V",
            "I-V-vi-IV",
            "minor: i-VII-VI-VII",
            "mixolydian: I-VII-IV-I",
        ),
        harmonic_rhythm=1,
        harmony="Major-key pop and rock changes (I-IV-V, I-vi-IV-V), minor ska vamps; full triads skanked on "
                "the offbeat in ska sections, power chords in punk sections; horns harmonize in 3rds and 6ths.",
        voicing="close",
        comping="skank",
        bass_style="walking",
        bass="Busy, melodic walking lines in ska sections (scale runs, chromatic approaches), root 8ths in "
             "punk sections.",
        melody_density="busy",
        melody_scale="major",
        melody="Horn riffs (trumpet, trombone, sax) state the hooks in unison or harmony; vocals melodic and "
               "punky, gang-sung choruses; horn soli in breakdowns.",
        groove={"step": 0.25, "pattern": {
            "kick":       "x.......x.......x...x...x...x...",
            "snare":      "....X.......X.....X...X...X...X.",
            "closed hat": "..x...x...x...x.................",
            "crash":      "................x...x...x...x...",
        }},
        drums="Ska sections: backbeat with offbeat hats and rimshots; punk sections: fast skank beat with "
              "crash; quick snare fills and stops for the switch.",
        form=(("intro (horns)", 8), ("verse (ska)", 16), ("chorus (punk)", 8), ("verse (ska)", 16),
              ("chorus (punk)", 8), ("horn break", 8), ("bridge", 8), ("chorus (punk)", 16), ("outro", 4)),
        instruments=("electric guitar", "electric bass", "drum kit", "trumpet", "trombone", "saxophone",
                     "lead vocal"),
        sound_design="E standard; clean, bright, choppy upstroke guitar for ska, switch to crunchy distortion "
                     "for punk; horns bright and close-miked.",
        production="Horns up front and wide, guitar skank thin and percussive, bass prominent; punchy, live "
                   "energy.",
        theory="Alternates the ska offbeat (guitar on the 'and', bass walking) with the punk downbeat; the "
               "feel switch between sections is the hook as much as the harmony.",
        mix=Mix(lufs=(-9, -7), lra=(4, 7), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="crust punk",
        family="metal and punk",
        aliases=("crust", "d-beat", "stenchcore"),
        parent="hardcore punk",
        description="Bleak, heavy hardcore punk fused with extreme metal: d-beat drumming, distorted bass, "
                    "dark minor riffs and roared vocals; apocalyptic and political.",
        era="England, 1980-1986 (Discharge, Amebix, Antisect); Sweden (Wolfbrigade, Disfear) in the 1990s",
        touchstones=("Discharge (Hear Nothing See Nothing Say Nothing)", "Amebix (Arise!)", "Antisect",
                     "Extreme Noise Terror", "Doom", "Wolfbrigade", "Tragedy"),
        tempo=(140, 200),
        feel="d-beat gallop: kick, snare, kick-kick, snare; straight and relentless",
        modes=("minor", "phrygian"),
        keys=("E minor", "D minor", "A minor", "B minor"),
        progressions=(
            "I5-VII5-VI5-VII5",
            "I5-bII5",
            "I5-VI5-III5-VII5",
            "I5-III5-IV5-III5",
            "phrygian: I5-II5-I5-VII5",
        ),
        harmonic_rhythm=1,
        harmony="Dark minor power-chord movement (i-bVII-bVI), phrygian b2, metal-tinged chromatic runs in "
                "stenchcore; tremolo-picked minor triads in modern (Tragedy) crust.",
        voicing="power",
        comping="eighths",
        bass_style="eighths",
        bass="Heavily distorted bass, as loud as the guitar, doubling the riff in 8ths; Motorhead-like grind.",
        melody_density="medium",
        melody_scale="minor",
        melody="Roared, hoarse vocals in short slogan-like lines, often two vocalists trading; melodic "
               "tremolo leads in Swedish and modern crust.",
        groove={"step": 0.25, "pattern": {
            "kick":     "x.....x.x.......",
            "snare":    "....X.......X...",
            "open hat": "x.x.x.x.x.x.x.x.",
            "crash":    "x...............",
        }},
        drums="The d-beat: kick on 1, snare on 2, kick on the 'and' of 2 and on 3, snare on 4, with open hats "
              "or crash on 8ths; switches to skank beats and blasts; heavy floor-tom parts in slow stenchcore.",
        form=(("intro", 4), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("bridge", 8),
              ("chorus", 8), ("outro", 4)),
        instruments=("distorted electric guitar", "distorted bass", "drum kit", "roared vocals"),
        sound_design="E standard or lower (D, C, B for modern crust); HM-2 or fuzzy high-gain; overdriven, "
                     "clanky bass; dirty, roomy drums.",
        production="Raw, murky and loud; little polish; guitars and bass merged in a wall; vocals distorted "
                   "and buried slightly in the mix.",
        theory="The d-beat's kick pattern (a stuttering, galloping push into the snare) is the genre's "
               "rhythmic identity; harmony is dark aeolian and phrygian power-chord motion.",
        mix=Mix(lufs=(-10, -7), lra=(3, 6), low_end="heavy", tone="dark", width="moderate"),
    ),
]
