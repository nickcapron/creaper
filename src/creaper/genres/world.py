"""World traditions and their modern pop offshoots: African, Asian, Middle Eastern and European folk styles."""

from . import Genre, Mix

GENRES = [
    # ------------------------------------------------------------------ African
    Genre(
        name="afrobeats",
        family="african",
        aliases=("naija pop", "afro pop", "afrofusion"),
        parent="highlife",
        description="West Africa's global pop sound: a mid-tempo, syncopated bounce of shakers, rims and congas "
                    "under melodic, sing-song vocals and bright guitar or piano plucks; made for dancing, not for drops.",
        era="Lagos and Accra, mid-2000s onward; worldwide from the mid-2010s",
        touchstones=("Wizkid", "Davido", "Burna Boy", "Tems", "Rema", "P-Square", "D'banj", "Mr Eazi"),
        tempo=(98, 116),
        feel="syncopated mid-tempo bounce: 3-3-2 rim and kick accents over a steady, slightly swung shaker",
        swing=54,
        modes=("major", "minor", "dorian"),
        keys=("Bb major", "G major", "F# minor", "C# minor"),
        progressions=(
            "I-vi-IV-V",
            "IVmaj7-V-iii7-vi7",
            "ii7-V7-Imaj7",
            "vi7-IVmaj7-Imaj7-V",
            "minor: i7-iv7-VII-III",
        ),
        harmonic_rhythm=1,
        harmony="Simple, sunny loops of 2-4 diatonic chords repeated through the whole song, warmed with maj7, "
                "min7 and add9 colours; IV-V-iii-vi and ii-V-I loops borrowed from R&B; minor songs stay on "
                "i7-iv7. Harmony rarely changes between verse and hook: the topline and drums carry the form.",
        voicing="open",
        comping="stabs",
        bass_style="syncopated",
        bass="Round sub or soft 808 playing short, syncopated notes that answer the kick: root on beat 1, then "
             "pushes on the 'and' of 2 and the 'a' of 3; slides between roots; since 2020 often an amapiano-style "
             "log-drum bass instead. Leaves space so the percussion bounce is felt.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Relaxed, behind-the-beat vocals in a mid range, pentatonic and sing-song; short repeated hook "
               "phrases in Pidgin, Yoruba, Igbo, Twi or English; call-and-response ad-libs and stacked "
               "harmonies on the hook; melisma and slides between notes; guitar or sax licks answer the vocal.",
        groove={"step": 0.25, "swing": 54, "pattern": {
            "kick":       "x.....x...x.....",
            "rim":        "...x..x....x..x.",
            "clap":       "....x.......x...",
            "shaker":     "xoxxxoxxxoxxxoxx",
            "conga":      "..x..x.x..x..xx.",
            "closed hat": "x.x.x.x.x.x.x.x.",
        }},
        drums="Programmed kit built around percussion: soft kick, rim or snap tracing a 3-3-2 figure, clap on 2 "
              "and 4, a constant 16th shaker with accents, congas and talking-drum samples filling the gaps; "
              "hats stay light. Fills are percussion runs and drop-outs, not snare rolls.",
        form=(("intro", 4), ("verse", 16), ("hook", 8), ("verse", 16), ("hook", 8), ("bridge", 8), ("hook", 8),
              ("outro", 4)),
        instruments=("drum programming", "shaker", "congas", "talking drum", "sub or 808 bass",
                     "clean electric guitar", "Rhodes or piano", "synth pluck", "saxophone", "layered vocals"),
        sound_design="Clean highlife-style guitar plucks (chorus, short delay), soft marimba or kalimba plucks, "
                     "Rhodes and felt piano, airy pads, round subs; percussion samples are dry and crisp, panned "
                     "around the stereo field.",
        production="Loud but uncluttered: kick and bass in mono, percussion spread wide, vocals forward with "
                   "plate reverb and tuned tightly; short 3-minute songs, hook within 30 seconds.",
        theory="The pulse is duple but the accents follow 3-3-2 (tresillo) groupings inherited from West African "
               "timelines; harmonic stasis (one loop all song) lets the cross-rhythm between rim, conga and "
               "shaker carry the interest.",
        mix=Mix(lufs=(-9, -7), lra=(4, 7), low_end="heavy", tone="warm", width="wide"),
    ),
    Genre(
        name="afrobeat",
        family="african",
        aliases=("fela afrobeat", "70s afrobeat", "afro-beat"),
        parent="highlife",
        description="Fela Kuti's long-form Nigerian groove music: interlocking guitars, horn riffs, a hypnotic bass "
                    "ostinato and Tony Allen's polyrhythmic drumming, with political call-and-response vocals.",
        era="Lagos, late 1960s-1970s; revived by Antibalas and the 2000s Afrobeat bands",
        touchstones=("Fela Kuti", "Tony Allen", "Africa 70", "Egypt 80", "Antibalas", "Seun Kuti", "Femi Kuti"),
        tempo=(100, 130),
        feel="straight 16ths with a deep, rolling polyrhythmic pocket; one groove held for 10-20 minutes",
        swing=52,
        modes=("dorian", "minor", "mixolydian"),
        keys=("C dorian", "F dorian", "G dorian", "D minor"),
        progressions=(
            "i7-IV7",
            "i7-i7",
            "i7-ii7",
            "minor: i7-iv7",
            "mixolydian: I7-VII",
        ),
        harmonic_rhythm=0.5,
        harmony="Modal vamps on one or two chords for the whole piece, usually dorian i7-IV7 or a static minor 7th; "
                "horn sections harmonise the riff in 4ths and 5ths; the organ comps with stabbed 9th and 11th chords. "
                "Tension comes from layering and dynamics, not chord changes.",
        voicing="shell",
        comping="pulse_16",
        bass_style="syncopated",
        bass="A repeating 1- or 2-bar ostinato on electric bass, syncopated and riff-like, centred on the root "
             "with b7, 4th and 5th; it never stops and barely varies, the anchor every other part locks to.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="Horn riffs (trumpet, tenor and baritone sax) state a short theme in unison or 4ths, then long "
               "tenor-sax and organ solos; vocals are chanted call-and-response between lead and chorus, in "
               "Pidgin English, with the lead preaching over the groove.",
        groove={"step": 0.25, "swing": 52, "pattern": {
            "kick":       "x.....x.x.....x.",
            "snare":      "..o.x..o.o..x.o.",
            "closed hat": "xxxoxx.oxxxoxx.o",
            "open hat":   "......x.......x.",
            "claves":     "x..x..x...x.x...",
            "shaker":     "x.xxx.xxx.xxx.xx",
            "conga":      "..x.x..x..x.x..x",
        }},
        drums="Tony Allen's style: sparse, syncopated kick, ghost-note snare, busy hi-hat 16ths with open-hat "
              "accents on the offbeats, all floating over the bass; around it a clave stick timeline, shekere, "
              "and two or three conga parts interlocking. The drummer plays independence, not fills.",
        form=(("intro jam", 16), ("groove", 32), ("horn theme", 16), ("sax solo", 32), ("vocal call and response", 32),
              ("organ solo", 32), ("horn theme", 16), ("outro", 16)),
        instruments=("drum kit", "congas", "shekere", "clave sticks", "electric bass", "rhythm guitar",
                     "tenor guitar", "Hammond or Farfisa organ", "trumpet", "tenor sax", "baritone sax", "vocals"),
        sound_design="Bright, trebly rhythm guitar muted to percussive 16th chops; a second 'tenor' guitar picks "
                     "a single-note ostinato; reedy combo organ; punchy brass with little reverb; warm, round "
                     "fingered bass.",
        production="Live band to tape: each part in its own frequency and stereo slot (guitars hard left/right), "
                    "little compression, natural room; long tracks with dynamics built by adding and removing layers.",
        theory="An African polyrhythmic ensemble principle (each instrument a fixed interlocking part, like a drum "
               "choir) fused with James Brown funk and jazz horns; dorian vamps give a minor sound with a major IV.",
        mix=Mix(lufs=(-14, -10), lra=(6, 10), low_end="moderate", tone="warm", width="wide"),
    ),
    Genre(
        name="amapiano",
        family="african",
        aliases=("yanos", "ama piano"),
        parent="deep house",
        description="South Africa's slow-burning house offshoot: jazzy piano and pads over airy shakers, sparse "
                    "kicks and the pitched, gliding 'log drum' bass that became its signature.",
        era="Gauteng townships (Pretoria, Johannesburg), mid-2010s; continental mainstream from 2019",
        touchstones=("Kabza De Small", "DJ Maphorisa", "Kelvin Momo", "MFR Souls", "Focalistic", "Tyler ICU",
                     "Uncle Waffles", "Major League DJz"),
        tempo=(108, 116),
        feel="laid-back house pulse at ~112 BPM with swung 16th shakers and off-grid percussion",
        swing=57,
        modes=("minor", "dorian", "major"),
        keys=("F minor", "G minor", "C minor", "Eb major"),
        progressions=(
            "i9-iv9",
            "i7-VImaj7-iv7-v7",
            "dorian: i9-IV9",
            "major: IVmaj7-iii7-ii7-Imaj7",
            "VImaj7-v7-i9",
        ),
        harmonic_rhythm=0.5,
        harmony="Jazz-house harmony: minor 9ths, major 7ths and 11ths, two- or four-chord loops held two bars "
                "each; 'private school' amapiano uses lusher, Rhodes-led chords with passing ii-V moves. Piano "
                "solos noodle over the loop rather than changing it.",
        voicing="rootless",
        comping="stabs",
        bass_style="syncopated",
        bass="The log drum: a pitched, punchy, decaying percussive bass (originally an MPC/FL 'log drum' "
             "preset) playing syncopated figures that glide between notes with pitch bends, often 'answering' "
             "the kick on the 'and' of 2 and the 'a' of 4; it is the lead instrument of the low end. A soft "
             "sub sometimes sustains beneath.",
        melody_density="sparse",
        melody_scale="minor pentatonic",
        melody="Sparse: piano licks and runs in the upper register, whistled or vocal-chop hooks, chant-like "
               "vocals and spoken ad-libs in isiZulu, Sesotho or Setswana; long instrumental stretches.",
        groove={"step": 0.25, "swing": 57, "pattern": {
            "kick":           "x...x...x...x...x...x...x...x...",
            "clap":           "....x.......x.......x.......x...",
            "shaker":         "xoxxxoxxxoxxxoxxxoxxxoxxxoxxxoxx",
            "closed hat":     "..x...x...x...x...x...x...x...x.",
            "high woodblock": "...x..x.....x.......x..x...x.x..",
            "rim":            ".......x...........x.....x......",
        }},
        drums="Soft, short kick (often four-on-the-floor at low level or just on 1 and 3), quiet claps, a "
              "prominent swung 16th shaker that defines the feel, offbeat hats, and scattered woodblock, rim "
              "and conga hits placed off the grid; the log drum does the rhythmic heavy lifting.",
        form=(("intro", 16), ("groove", 32), ("vocal", 16), ("log drum break", 16), ("groove", 32),
              ("piano solo", 16), ("vocal", 16), ("outro", 16)),
        instruments=("log drum bass", "shaker", "soft kick", "woodblock and congas", "piano", "Rhodes",
                     "warm pads", "flute or whistle", "vocals"),
        sound_design="Log drum: short pitched percussive tone with a fast-decaying body and a click, tuned to the "
                     "key and bent between notes, heavily saturated. Piano bright and dry, pads soft and wide, "
                     "shakers airy and high-passed.",
        production="Long DJ-friendly tracks (6-8 minutes), log drum and kick share the low end with careful EQ "
                   "carving, saturation on the log drum so it reads on phones, wide percussion, loud masters.",
        theory="Jazz-derived extended chords over a slow house tempo, but the bass acts as a melodic percussion "
               "voice: its syncopated, pitch-gliding phrases create a cross-rhythm against the steady pulse.",
        mix=Mix(lufs=(-9, -6.5), lra=(4, 7), low_end="very heavy", tone="warm", width="wide"),
    ),
    Genre(
        name="afro house",
        family="african",
        aliases=("afrohouse", "south african house"),
        parent="house",
        description="House music built on African percussion and chant: a four-on-the-floor kick under "
                    "interlocking congas, shakers and talking drums, minor modal chords and hypnotic vocals.",
        era="South Africa, 2000s (Johannesburg and Durban); global club staple from the 2010s",
        touchstones=("Black Coffee", "Culoe De Song", "Da Capo", "Enoo Napa", "Shimza", "Caiiro", "Keinemusik"),
        tempo=(118, 125),
        feel="four-on-the-floor with polyrhythmic percussion layered on top",
        swing=54,
        modes=("minor", "dorian", "phrygian"),
        keys=("A minor", "G minor", "F minor", "D minor"),
        progressions=(
            "i7-iv7",
            "i-VII-VI-VII",
            "i-VI-VII",
            "dorian: i7-IV7",
            "phrygian: i-II",
        ),
        harmonic_rhythm=0.5,
        harmony="Minor-key loops of two to four chords, often modal (dorian i-IV, phrygian i-bII) and held for "
                "long stretches; marimba or kalimba riffs and string pads outline the chords; melancholy and "
                "spiritual rather than euphoric.",
        voicing="open",
        comping="stabs",
        bass_style="syncopated",
        bass="Rolling, syncopated sub or plucked bass that avoids the kick and walks between root, b7 and 5th; "
             "often a short repeated 1-bar riff.",
        melody_density="sparse",
        melody_scale="minor pentatonic",
        melody="Chanted, call-and-response vocals (isiZulu, Xhosa, Yoruba or English), marimba and kalimba "
               "ostinatos, plucked kora-like riffs and flute phrases repeating for 16-32 bars.",
        groove={"step": 0.25, "swing": 54, "pattern": {
            "kick":       "x...x...x...x...",
            "clap":       "....x.......x...",
            "closed hat": "..x...x...x...x.",
            "shaker":     "xoxoxoxoxoxoxoxo",
            "conga":      "..x.x..x.x..x..x",
            "high bongo": "x..x..x...x..x..",
            "rim":        "...x..x...x.....",
        }},
        drums="Deep, rounded kick on every beat; clap or snap on 2 and 4; offbeat hats; multiple layers of live "
              "or sampled percussion (congas, djembe, bongos, talking drum, shakers) in cross-rhythms, often "
              "3-against-4; tom grooves in breakdowns.",
        form=(("intro", 32), ("groove", 32), ("breakdown", 16), ("main", 32), ("break", 16), ("main", 32),
              ("outro", 32)),
        instruments=("drum machine kick", "congas", "djembe", "talking drum", "shakers", "sub bass", "marimba",
                     "kalimba", "string pads", "chanted vocals"),
        sound_design="Organic percussion recorded or sampled dry; warm sub; marimba and kalimba plucks through "
                     "short delays; dark pads and filtered strings; vocals with long hall reverbs.",
        production="Kick and sub mono and dominant, percussion spread across the stereo field in layers, slow "
                   "filter builds, DJ-friendly 32-bar intros and outros.",
        theory="The 4/4 grid carries West and Southern African cross-rhythms (3:2 and 3:4 percussion layers); "
               "modal minor harmony and repetition aim for trance-like immersion rather than song form.",
        mix=Mix(lufs=(-9, -7), lra=(4, 7), low_end="heavy", tone="warm", width="wide"),
    ),
    Genre(
        name="gqom",
        family="african",
        aliases=("durban gqom", "gqom tech"),
        parent="house",
        description="Durban's raw, dark club sound: broken, booming kicks and toms instead of a four-on-the-floor "
                    "pulse, minimal synth stabs, sirens and chanted vocals at around 126 BPM.",
        era="Durban, KwaZulu-Natal, early 2010s; international from 2016",
        touchstones=("DJ Lag", "Distruction Boyz", "Babes Wodumo", "Rudeboyz", "Citizen Boy", "Busiswa",
                     "Griffit Vigo"),
        tempo=(120, 128),
        feel="broken: syncopated kicks in 3-3-2 and off-beat groupings, no steady four-on-the-floor",
        swing=52,
        modes=("minor", "phrygian"),
        keys=("F minor", "G minor", "E minor"),
        progressions=(
            "i-i",
            "phrygian: i-II",
            "i-VI",
            "i-iv",
        ),
        harmonic_rhythm=0.5,
        harmony="Barely any: a single dark minor stab or drone chord, sometimes moving to bII or bVI for menace. "
                "Harmony is texture; the drums are the composition.",
        voicing="cluster",
        comping="stabs",
        bass_style="syncopated",
        bass="No separate bassline in most tracks: the tuned, boomy kicks and low toms carry the low end. When "
             "there is a bass it is a short sub hit doubling the broken kick pattern.",
        melody_density="sparse",
        melody_scale="minor",
        melody="Very sparse: chanted or shouted vocal hooks, one-note synth stabs, eerie flute or siren samples, "
               "short vocal chops repeated hypnotically.",
        groove={"step": 0.25, "swing": 52, "pattern": {
            "kick":     "X..x..x...x.....X..x...x..x.x...",
            "low tom":  "......x.......x.......x.....x...",
            "clap":     "........x...............x.......",
            "shaker":   "x.xxx.xxx.xxx.xxx.xxx.xxx.xxx.xx",
            "woodblock": "...x.......x.......x.....x......",
        }},
        drums="The kick is the lead: booming, distorted, tuned kicks in broken, tresillo-like patterns that "
              "skip beats; tom figures roll between them; sparse claps or snares on unexpected beats; "
              "shakers and chimes keep a faint 16th grid. Tension from where the kick is missing.",
        form=(("intro", 16), ("drums", 32), ("vocal", 16), ("drop", 32), ("break", 8), ("drop", 32), ("outro", 16)),
        instruments=("drum machine kicks", "toms", "claps", "shakers", "synth stabs", "sirens and FX",
                     "chanted vocals"),
        sound_design="Lo-fi FL Studio aesthetic: overdriven, boomy kicks with long tails, reverb-washed toms, "
                     "metallic percussion, dark minor stabs, police sirens and horror-film FX.",
        production="Raw and loud: heavy saturation and clipping on the kick bus, mono low end, little else in "
                   "the mix; space and silence are part of the rhythm.",
        theory="Takes house's tempo but breaks its pulse: kicks grouped 3+3+2 and 3+3+3+3+4 against the bar "
               "create a syncopated, almost Afro-Cuban feel with nothing marking the downbeat.",
        mix=Mix(lufs=(-9, -6), lra=(3, 6), low_end="very heavy", tone="dark", width="moderate"),
    ),
    Genre(
        name="highlife",
        family="african",
        aliases=("ghanaian highlife", "burger highlife", "palm wine music"),
        description="Ghana's (and Nigeria's) swinging dance music: bright, interlocking guitar lines or brass over "
                    "a bell-driven Afro-Atlantic groove, with sweet major-key harmony and joyful vocals.",
        era="Ghana and Nigeria, 1920s palm-wine roots; dance-band golden age 1950s-70s; burger highlife 1980s",
        touchstones=("E.T. Mensah", "Nana Ampadu & the African Brothers", "Victor Olaiya", "Rex Lawson",
                     "Prince Nico Mbarga", "K. Frimpong", "Ebo Taylor", "George Darko"),
        tempo=(100, 136),
        feel="lilting duple groove over a bell timeline, light swing in the guitars",
        swing=56,
        modes=("major", "mixolydian"),
        keys=("C major", "G major", "D major", "F major"),
        progressions=(
            "I-IV-I-V",
            "I-V-I-IV",
            "I-IV-V-I",
            "I-vi-ii-V",
            "mixolydian: I-VII-IV-I",
        ),
        harmonic_rhythm=1,
        harmony="Bright, cyclic major-key harmony: I, IV and V in 2- or 4-bar cycles, some ii and vi in the "
                "dance-band style, dominant 7ths and occasional mixolydian bVII; guitars outline chords as "
                "melodic arpeggios rather than strums.",
        voicing="close",
        comping="broken",
        bass_style="syncopated",
        bass="Melodic, syncopated bass outlining root, 3rd and 5th with pickups into each chord; it dances "
             "around the bell, often pushing the 'and' of beat 4.",
        melody_density="medium",
        melody_scale="major",
        melody="Two or three guitars interlock in high-register picked lines (thumb-and-finger palm-wine style), "
               "parallel 3rds and 6ths; horns state sweet unison or harmonised riffs; vocals in Twi, Fante, "
               "Igbo or English with call-and-response choruses.",
        groove={"step": 0.25, "swing": 56, "pattern": {
            "kick":    "x.......x.....x.",
            "rim":     "....x.......x...",
            "cowbell": "x..x..x...x.x...",
            "conga":   "..x.x..x..x.x..x",
            "shaker":  "x.x.x.x.x.x.x.x.",
        }},
        drums="A bell (gankogui or cowbell) plays the timeline; congas, clips and shakers interlock around it; "
              "trap kit keeps a light kick and rim backbeat; in guitar-band highlife the percussion is "
              "lighter and the guitars carry the rhythm.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("guitar break", 16), ("verse", 16), ("chorus", 8),
              ("horn interlude", 8), ("chorus", 8), ("outro", 8)),
        instruments=("electric guitars", "acoustic guitar", "electric bass", "trumpet", "saxophone", "trombone",
                     "bell", "congas", "drum kit", "vocals"),
        sound_design="Clean, bright guitars (single-coil, light reverb), mellow horn section, warm bass, wooden "
                     "percussion; 1980s burger highlife adds DX7 keys, drum machines and synth bass.",
        production="Natural band balance with the guitars upfront and panned apart so their interlock is audible; "
                   "moderate compression, dynamic arrangements with instrumental breaks.",
        theory="Western hymn and brass-band harmony (I-IV-V) fused with an Akan bell timeline and cross-rhythmic "
               "guitar ostinatos; melody and accompaniment are built from interlocking cycles.",
        mix=Mix(lufs=(-14, -10), lra=(6, 10), low_end="moderate", tone="bright", width="moderate"),
    ),
    Genre(
        name="soukous",
        family="african",
        aliases=("congolese rumba", "rumba congolaise", "kwassa kwassa", "ndombolo"),
        description="Congolese dance music born from Cuban rumba: sweet vocal sections give way to the fast "
                    "'sebene', where shimmering high guitars cycle over a driving cavacha snare beat.",
        era="Kinshasa and Brazzaville, 1950s rumba; soukous and sebene-driven styles 1970s-90s; Paris scene 1980s",
        touchstones=("Franco & TPOK Jazz", "Tabu Ley Rochereau", "Papa Wemba", "Kanda Bongo Man", "Diblo Dibala",
                     "Pepe Kalle", "Koffi Olomide"),
        tempo=(120, 150),
        feel="driving duple: cavacha 16th snare pattern and four-on-the-floor kick in the sebene",
        swing=50,
        modes=("major",),
        keys=("E major", "A major", "D major", "C major"),
        progressions=(
            "I-IV-V-IV",
            "I-IV-I-V",
            "I-V-IV-V",
            "ii-V-I-I",
        ),
        harmonic_rhythm=1,
        harmony="Major-key cycles of I, IV and V repeated hypnotically, especially in the sebene; the rumba "
                "sections add ii and dominant 7ths from Cuban son; harmony is bright and never minor-heavy.",
        voicing="close",
        comping="arpeggio_updown",
        bass_style="syncopated",
        bass="Busy, melodic bass weaving root-5th-octave patterns with syncopated pickups, locking with the "
             "kick but answering the guitars; in the sebene it drives harder with repeated 8th-note figures.",
        melody_density="busy",
        melody_scale="major pentatonic",
        melody="Lead (solo) guitar plays rapid, high-register cyclic arpeggios and runs in 3rds and 6ths; "
               "rhythm and mi-solo guitars interlock below; vocals are smooth close-harmony Lingala choruses "
               "with an atalaku (animator) shouting dance calls during the sebene.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x...x...x...x...",
            "snare":      "X.xxX.xxX.xxX.xx",
            "closed hat": "x.x.x.x.x.x.x.x.",
            "conga":      "..x...x...x..xx.",
        }},
        drums="The cavacha: the snare (or closed hi-hat) plays a constant 16th pattern with accents on the "
              "beat, over a steady kick; congas and maracas add Cuban colour in rumba sections; the drummer "
              "lifts the energy into the sebene with crashes and snare accents.",
        form=(("intro", 8), ("rumba verse", 16), ("chorus", 8), ("rumba verse", 16), ("sebene", 32),
              ("atalaku calls", 16), ("sebene", 32), ("outro", 8)),
        instruments=("solo guitar", "mi-solo guitar", "rhythm guitar", "electric bass", "drum kit", "congas",
                     "saxophone", "lead and harmony vocals", "atalaku"),
        sound_design="Clean, bright, trebly guitars with chorus or light reverb, often a clean amp with "
                     "compression for sustain; punchy bass; tight snare; 1980s Paris productions add synths "
                     "and drum machines.",
        production="Guitars panned and layered so the interlock sparkles; vocals smooth with reverb; long tracks "
                   "with the sebene as the dance climax.",
        theory="Cuban son harmony and clave feeling re-imagined with Central African guitar polyphony: several "
               "cyclic guitar ostinatos interlock like a thumb-piano or xylophone ensemble over a static chord loop.",
        mix=Mix(lufs=(-12, -9), lra=(5, 8), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="afroswing",
        family="african",
        aliases=("afrobashment", "afro swing"),
        parent="afrobeats",
        description="The UK's fusion of afrobeats, dancehall bounce and road rap: melodic, auto-tuned flows over "
                    "syncopated percussion, minor-key guitar loops and heavy 808s.",
        era="London, mid-2010s",
        touchstones=("J Hus", "Kojo Funds", "Not3s", "NSG", "Yxng Bane", "Belly Squad", "Mostack"),
        tempo=(95, 112),
        feel="syncopated, swung bounce: 3-3-2 kick and rim over a shuffling hat",
        swing=56,
        modes=("minor", "dorian"),
        keys=("F minor", "G minor", "C# minor", "A minor"),
        progressions=(
            "i7-iv7",
            "i-VII-VI-VII",
            "VI-VII-i",
            "i-VI-III-VII",
            "dorian: i7-IV9",
        ),
        harmonic_rhythm=1,
        harmony="Melancholic minor loops of two to four chords on guitar or piano, minor 7ths and 9ths, often "
                "sampled or played as a picked guitar figure; harmony stays fixed under every section.",
        voicing="open",
        comping="broken",
        bass_style="808",
        bass="Long, gliding 808s following the kick's 3-3-2 pattern, sliding between roots; heavier and more "
             "sub-focused than Nigerian afrobeats.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="Sing-rap flows mixing London slang, Jamaican patois and West African languages; melodic, "
               "auto-tuned hooks in a narrow pentatonic range; ad-libs and harmonised doubles.",
        groove={"step": 0.25, "swing": 56, "pattern": {
            "kick":       "x..x..x...x.....",
            "clap":       "....x.......x...",
            "rim":        "..x....x..x..x..",
            "closed hat": "x.xxx.x.x.xxx.x.",
            "shaker":     "xoxxxoxxxoxxxoxx",
        }},
        drums="Dancehall-style kick in a 3-3-2 pattern, clap or snare on 2 and 4, syncopated rims and percussion, "
              "swung hats with occasional rolls borrowed from UK rap; shakers and congas for the African side.",
        form=(("intro", 4), ("hook", 8), ("verse", 16), ("hook", 8), ("verse", 16), ("hook", 8), ("outro", 4)),
        instruments=("drum programming", "808", "nylon or clean electric guitar", "piano", "percussion",
                     "synth pads", "auto-tuned vocals"),
        sound_design="Picked nylon or clean guitar loops, soft keys, deep 808 with saturation, crisp rims and "
                     "snaps, airy pads; vocals heavily tuned and doubled.",
        production="Modern rap mixing: 808 and kick dominate, vocals loud and bright, short 2.5-3 minute songs.",
        theory="Dancehall's 3-3-2 kick and afrobeats' percussion layering meet UK rap's 808s; harmonic stasis "
               "keeps the focus on flow and groove.",
        mix=Mix(lufs=(-9, -7), lra=(4, 7), low_end="very heavy", tone="warm", width="wide"),
    ),
    Genre(
        name="mbalax",
        family="african",
        aliases=("mbalakh", "senegalese mbalax"),
        description="Senegal's national pop: fast, crackling sabar drum rhythms and tama talking drum fused with "
                    "Afro-Cuban band music, soaring griot vocals, guitars, keys and horns.",
        era="Dakar, 1970s-80s; defined by Youssou N'Dour and the Super Etoile",
        touchstones=("Youssou N'Dour", "Super Etoile de Dakar", "Omar Pene", "Thione Seck", "Coumba Gawlo",
                     "Viviane Chidid"),
        tempo=(110, 140),
        feel="driving duple with complex, rapid sabar cross-rhythms and sudden unison breaks",
        swing=52,
        modes=("major", "mixolydian", "minor"),
        keys=("D major", "G major", "A major", "E minor"),
        progressions=(
            "I-IV-V-IV",
            "I-V-I-V",
            "IV-I-V-I",
            "mixolydian: I-VII-I",
            "minor: i-VII-i-VII",
        ),
        harmonic_rhythm=1,
        harmony="Short major or mixolydian loops (I-IV-V, I-bVII) from Afro-Cuban dance bands; keyboards and "
                "guitars play bright, repeated riffs rather than complex changes; the harmony is a bed for the "
                "drums and voice.",
        voicing="close",
        comping="broken",
        bass_style="syncopated",
        bass="Funky, syncopated electric bass riffs, often doubling a keyboard ostinato and accenting the "
             "same breaks as the sabar ensemble.",
        melody_density="busy",
        melody_scale="major pentatonic",
        melody="Griot-style vocals in Wolof: high, powerful, melismatic tassou-like declamation with long held "
               "notes and ornamented falls; guitar and keyboard riffs are short and repeated; horn hits mark "
               "the drum breaks.",
        groove={"step": 0.25, "swing": 52, "pattern": {
            "kick":       "x.....x...x.....",
            "snare":      "....x.......x...",
            "low conga":  "x..x..x...x.x...",
            "slap conga": "..x...x.x...x.xx",
            "high bongo": ".....xx.x.x...xo",
            "closed hat": "x.x.x.x.x.x.x.x.",
        }},
        drums="A sabar ensemble (mbëng-mbëng bass drums, nder lead, tungune) plays stick-and-hand patterns "
              "around the kit; the tama talking drum answers the singer; the lead drummer cues bakks (composed "
              "unison breaks) that the whole band hits together.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("sabar break", 8), ("verse", 16), ("chorus", 8),
              ("drum solo", 16), ("chorus", 8), ("outro", 8)),
        instruments=("sabar drums", "tama talking drum", "drum kit", "electric bass", "electric guitar",
                     "synthesizer", "saxophone", "griot vocals"),
        sound_design="Bright, cracking sabar and tama sounds (stick slaps, high pitch), clean guitars, 1980s "
                     "synth keyboards, punchy horns; the drums sit as loud as the vocals.",
        production="Drums upfront and wide, vocals powerful and present, keys and guitars mid-range and tidy; "
                   "dense but punchy.",
        theory="Wolof sabar rhythms (dance patterns tied to spoken phrases) superimposed on a Cuban-influenced "
               "band; the composed drum breaks (bakk) are the structural signposts.",
        mix=Mix(lufs=(-12, -9), lra=(5, 9), low_end="moderate", tone="bright", width="wide"),
    ),
    # ------------------------------------------------------------------- Asian
    Genre(
        name="bhangra",
        family="asian",
        aliases=("punjabi pop", "uk bhangra", "bhangra pop"),
        description="Punjabi harvest-dance music turned global party music: the thundering, swung dhol chaal, "
                    "the tumbi's twanging riff and exuberant vocals with 'balle balle' shouts.",
        era="Punjab folk tradition; UK bhangra in Birmingham and London from the late 1970s; Punjabi pop 1990s-now",
        touchstones=("Alaap", "Heera", "Malkit Singh", "Daler Mehndi", "Panjabi MC", "Bally Sagoo", "Diljit Dosanjh",
                     "Sidhu Moose Wala"),
        tempo=(88, 106),
        feel="heavily swung 16ths: the dhol chaal's lopsided long-short bounce",
        swing=64,
        modes=("mixolydian", "major", "minor"),
        keys=("C mixolydian", "D mixolydian", "G major", "E minor"),
        progressions=(
            "I-I",
            "I-VII-I-I",
            "major: I-IV-V-I",
            "major: vi-IV-I-V",
            "minor: i-VII-VI-VII",
        ),
        harmonic_rhythm=0.5,
        harmony="Folk bhangra is almost chordless: a tonic drone with the tumbi riff and vocal on top, moving to "
                "the bVII (khamaj colour) for a lift. UK and modern Punjabi pop add simple keyboard chords "
                "(I-IV-V, vi-IV-I-V) under the same melodies.",
        voicing="open",
        comping="offbeat",
        bass_style="syncopated",
        bass="Traditional bhangra has no bass instrument: the dhol's bass skin fills that role. Modern "
             "productions add a punchy synth bass or 808 doubling the dhol's bass strokes on the swung pattern.",
        melody_density="busy",
        melody_scale="mixolydian",
        melody="High, open-throated vocals with ornamented slides, boliyan couplets and hooks; the tumbi plays "
               "a short, repeated 2- or 3-note riff on one string; algoza (double flute) and harmonium fill; "
               "shouts of 'hoy', 'balle balle', 'burrah' mark the downbeats.",
        groove={"step": 0.25, "swing": 64, "pattern": {
            "low floor tom": "X.....x.X.....x.",
            "rim":           "o.x.o.x.o.x.o.xx",
            "kick":          "x.......x.....x.",
            "clap":          "....x.......x...",
            "tambourine":    "x.x.x.x.x.x.x.x.",
        }},
        drums="The dhol: a double-headed barrel drum, bass side struck with a curved stick (dagga, here the low "
              "floor tom) and treble side with a thin cane (thapi, here the rim) playing the swung chaal "
              "pattern; chimta tongs jingle (tambourine) on the 8ths; dholak and modern kick-and-clap layers "
              "reinforce it.",
        form=(("intro dhol", 4), ("verse", 16), ("hook", 8), ("dhol break", 4), ("verse", 16), ("hook", 8),
              ("tumbi solo", 8), ("hook", 8), ("outro", 4)),
        instruments=("dhol", "tumbi", "algoza", "chimta", "dholak", "harmonium", "synth bass", "keyboard",
                     "vocals"),
        sound_design="Dhol recorded close and loud with a booming low skin and cracking cane; tumbi bright and "
                     "nasal with a short delay; modern mixes layer the dhol with drum-machine kicks and "
                     "claps, sub bass and hip-hop or dancehall elements.",
        production="Party-loud: dhol and vocals dominate, wide stereo percussion, bright top end; remixes "
                   "and mash-ups with hip-hop and house are standard.",
        theory="Built on the dhol's chaal, a swung, dance-driven 8-beat cycle (keherwa-like) where the long-short "
               "subdivision is the identity; harmony is drone-based (tonic plus mixolydian bVII), melody "
               "pentatonic-to-mixolydian with Punjabi folk ornaments.",
        mix=Mix(lufs=(-9, -6.5), lra=(4, 7), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="bollywood",
        family="asian",
        aliases=("filmi", "hindi film music", "bollywood pop", "indian film music"),
        description="Hindi film song: lavish orchestral and electronic production around a star playback singer, "
                    "mixing Indian melody (raga colour, tabla and dholak) with Western harmony and pop grooves.",
        era="Bombay/Mumbai film industry, 1940s-present; golden age 1950s-70s, A.R. Rahman era from the 1990s",
        touchstones=("R.D. Burman", "Laxmikant-Pyarelal", "S.D. Burman", "A.R. Rahman", "Shankar-Ehsaan-Loy",
                     "Pritam", "Lata Mangeshkar", "Kishore Kumar", "Asha Bhosle", "Arijit Singh"),
        tempo=(70, 130),
        feel="straight or lightly swung keherwa (8-beat) on dholak or tabla; ballads half-time, dance songs driving",
        swing=54,
        modes=("minor", "major", "phrygian", "harmonic minor"),
        keys=("C minor", "D minor", "G major", "E minor"),
        progressions=(
            "i-VII-VI-VII",
            "i-iv-VII-III",
            "i-VI-III-VII",
            "major: I-V-vi-IV",
            "phrygian: i-II-VII-i",
            "harmonic minor: i-iv-V-i",
        ),
        harmonic_rhythm=1,
        harmony="Western chords under raga-flavoured melodies: minor keys with bVI-bVII-i moves, phrygian bII "
                "for raga Bhairavi colour, harmonic-minor V for drama; the chords often follow the melody's "
                "drone-like tonic rather than functional cadences. Modern ballads use pop loops (vi-IV-I-V).",
        voicing="spread",
        comping="arpeggio_up",
        bass_style="root_fifth",
        bass="Supportive root-5th patterns on bass guitar or synth, following the dholak's bass strokes; dance "
             "numbers use octave or 808 bass.",
        melody_density="busy",
        melody_scale="minor",
        melody="The song is the melody: wide-range, ornamented vocal lines with meend (glides), murki (quick "
               "turns) and gamak (oscillation) drawn from Hindustani practice; a mukhda (refrain) and antara "
               "(verse) structure; instrumental interludes on strings, sitar, santoor, bansuri or shehnai "
               "answer the vocal.",
        groove={"step": 0.25, "swing": 54, "pattern": {
            "low conga":  "x.x.......o.x...",
            "high conga": "x...x.x.x...x.x.",
            "kick":       "x.....x.x.......",
            "snare":      "....x.......x...",
            "tambourine": "..x...x...x...x.",
            "shaker":     "x.x.x.x.x.x.x.x.",
        }},
        drums="Dholak or tabla playing keherwa (dha ge na ti na ka dhi na; bayan = low conga, dayan = high "
              "conga) or dadra in 6/8; modern songs layer a drum kit or programmed beat, tambourine and shakers; "
              "dance numbers add dhol and big tom fills.",
        form=(("intro", 8), ("mukhda", 8), ("interlude", 8), ("antara", 16), ("mukhda", 8), ("interlude", 8),
              ("antara", 16), ("mukhda", 8), ("outro", 4)),
        instruments=("string section", "tabla", "dholak", "sitar", "santoor", "bansuri", "shehnai", "harmonium",
                     "piano", "synthesizers", "drum kit", "playback vocals"),
        sound_design="Big studio strings with unison runs, sitar and santoor flourishes, breathy bansuri, "
                     "lush reverbs on the vocal; Rahman-era production blends synth pads, electronic beats and "
                     "Carnatic or Sufi vocal textures.",
        production="Vocal-first, cinematic mixes: the playback singer upfront with long reverb, orchestra wide, "
                   "interludes showcase instruments; modern songs mastered to pop loudness.",
        theory="Raga-based melody (often Bhairavi, Yaman, Kafi or Pahadi flavours) harmonised with Western "
               "chords; the mukhda/antara form mirrors the sthayi/antara of Hindustani compositions.",
        mix=Mix(lufs=(-12, -8), lra=(5, 10), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="hindustani classical",
        family="asian",
        aliases=("indian classical", "north indian classical", "raga", "khayal"),
        description="North India's raga music: an improvised, slowly unfolding melody over a tanpura drone, "
                    "moving from free alap into a composition set to a tala cycle on tabla, rising to virtuosic speed.",
        era="North Indian courts and gharanas, codified from the 13th-18th centuries; modern concert form 20th century",
        touchstones=("Ravi Shankar", "Ali Akbar Khan", "Bhimsen Joshi", "Kishori Amonkar", "Hariprasad Chaurasia",
                     "Zakir Hussain", "Amjad Ali Khan", "Kumar Gandharva"),
        tempo=(40, 260),
        feel="tala cycle: teentaal's 16 matras (4+4+4+4), from vilambit (slow) through madhya to drut (fast)",
        swing=50,
        modes=("yaman", "kafi", "bhairav", "todi", "purvi", "marwa", "bhairavi", "khamaj"),
        keys=("C# yaman", "C kafi", "C bhairav", "D yaman"),
        progressions=(
            "I5-I5",
            "IV5-IV5",
            "kafi: I5-I5",
            "bhairav: I5-I5",
            "todi: I5-I5",
        ),
        harmonic_rhythm=0.25,
        harmony="No chords: the tanpura drone (Sa and Pa, or Sa and Ma for ragas that omit Pa, written IV5) "
                "sounds continuously and every note of the raga is heard against it. The 'progressions' here "
                "are just that drone; never add functional harmony.",
        voicing="open",
        comping="sustain",
        bass_style="pedal",
        bass="No bass line: the tanpura's low Sa and the tabla's bayan provide the low register. If a bass is "
             "needed, hold the tonic drone (with Pa or Ma) for the whole piece.",
        melody_density="medium",
        melody_scale="yaman",
        melody="Raga grammar governs everything: ascending (aroh) and descending (avroh) forms, vadi and samvadi "
               "(the most important notes), characteristic phrases (pakad), and ornaments: meend (slow glides), "
               "gamak (heavy oscillation), andolan (slow vibrato on a note), kan (grace notes), murki, and taans "
               "(fast runs). Alap explores the raga note by note without pulse; the bandish (composition) "
               "returns to the mukhda phrase landing on sam.",
        groove={"step": 1, "swing": 50, "pattern": {
            "low conga":  "Xxxxxxxxx....xxx",
            "high conga": "Xxxxxxxxxxxxxxxx",
        }},
        drums="Tabla only, entering after the alap: the dayan (treble, high conga) and bayan (bass, low conga) "
              "play the theka of the tala, here teentaal: dha dhin dhin dha | dha dhin dhin dha | dha tin tin ta "
              "| ta dhin dhin dha, with the bayan silent in the khali (empty) section. One step = one matra "
              "(four bars of 4/4 = one cycle); sam (beat 1) is the arrival point of every phrase. The tabla "
              "player adds fills, tihais (thrice-repeated cadences ending on sam) and solo passages.",
        form=(("alap", 32), ("jor", 32), ("jhala", 16), ("vilambit gat or bada khayal", 64),
              ("drut gat or chhota khayal", 32), ("tihai and finale", 8)),
        instruments=("sitar", "sarod", "bansuri", "sarangi", "harmonium", "vocals", "tanpura", "tabla"),
        sound_design="Acoustic and resonant: sitar and sarod with buzzing jawari bridges and sympathetic strings, "
                     "breathy bansuri, the tanpura's shimmering overtones; no effects beyond a natural hall.",
        production="Concert recording: wide dynamic range, tanpura low and constant, soloist centred, tabla "
                   "slightly to one side; no compression to speak of, tempos accelerate naturally over 30-60 minutes.",
        theory="Raga is a melodic mode with rules of movement and mood, not just a scale; ragas are grouped into "
               "ten thaats (Bilawal, Kalyan/Yaman, Khamaj, Kafi, Asavari, Bhairavi, Bhairav, Todi, Purvi, Marwa). "
               "Real intonation uses shrutis (microtonal inflections, e.g. the very low komal re and ga of "
               "Todi, the slightly low ga in Darbari); the 12-tone scales here are the nearest approximation. "
               "Tala is cyclic: teentaal 16, ektaal 12, jhaptaal 10, rupak 7, keherwa 8, dadra 6.",
        mix=Mix(lufs=(-23, -16), lra=(8, 16), low_end="light", tone="warm", width="moderate"),
    ),
    Genre(
        name="qawwali",
        family="asian",
        aliases=("sufi qawwali", "sufi devotional"),
        description="Sufi devotional song from Pakistan and North India: a lead singer and chorus with harmonium, "
                    "tabla and hand claps, building in long waves from meditative to ecstatic.",
        era="Delhi Sufi shrines, 13th century (Amir Khusrau); modern concert and recording form 20th century",
        touchstones=("Nusrat Fateh Ali Khan", "Sabri Brothers", "Aziz Mian", "Rahat Fateh Ali Khan",
                     "Fareed Ayaz & Abu Muhammad", "Abida Parveen"),
        tempo=(70, 160),
        feel="keherwa (8 beats) or dadra (6) with hand claps; gradual accelerando through the piece",
        swing=58,
        modes=("minor", "phrygian", "dorian", "major"),
        keys=("C minor", "D minor", "C# phrygian", "C major"),
        progressions=(
            "i-i",
            "i-VII-i",
            "i-iv-i-VII",
            "phrygian: i-II-i",
            "major: I-I",
        ),
        harmonic_rhythm=0.5,
        harmony="Drone and heterophony rather than chords: the harmonium doubles the melody with tonic and "
                "5th drones; when harmonised, keep to the tonic with neighbouring bVII or bII (Bhairavi colour). "
                "The raga mode is the real harmony.",
        voicing="open",
        comping="sustain",
        bass_style="pedal",
        bass="No bass instrument: the harmonium's low drone and the tabla bayan carry the bottom. A tonic pedal "
             "is the honest translation.",
        melody_density="busy",
        melody_scale="minor",
        melody="Lead singer and second voices trade lines; a fixed refrain (the 'girah' and the main verse) "
               "repeats while the lead improvises sargam (sung note names), fast taans and ornamented "
               "variations; the chorus answers in unison; tension rises by repetition of a single line, "
               "climbing in pitch and intensity.",
        groove={"step": 0.5, "swing": 58, "pattern": {
            "low conga":  "Xx...ox.",
            "high conga": "X.xxx.xx",
            "clap":       "x.x.x.x.",
        }},
        drums="Tabla (and sometimes dholak) plays keherwa: dha ge na ti | na ka dhi na (bayan = low conga, "
              "dayan = high conga); the chorus claps on the beats, doubling up as the tempo rises; big "
              "accented tihai-like cadences mark section ends.",
        form=(("harmonium alap", 8), ("introductory verse", 16), ("refrain", 16), ("verse", 16), ("refrain", 16),
              ("sargam improvisation", 32), ("refrain", 16), ("climax", 16)),
        instruments=("lead vocals", "chorus vocals", "harmonium", "tabla", "dholak", "hand claps"),
        sound_design="Reedy hand-pumped harmonium, ringing tabla, natural voices and claps; recordings range from "
                     "shrine field recordings to Real World-style studio productions with added bass and pads.",
        production="Live-ensemble balance: lead vocal dominant, harmonium and claps behind, tabla bright; long "
                   "dynamic arcs, natural room ambience.",
        theory="Hindustani raga and tala practice in a devotional, repetitive form: the key device is cumulative "
               "repetition of a phrase with accelerating tempo toward ecstatic states (hal). Raga intonation "
               "uses microtonal shading; 12-tone modes approximate it.",
        mix=Mix(lufs=(-18, -12), lra=(8, 14), low_end="light", tone="warm", width="moderate"),
    ),
    Genre(
        name="gamelan",
        family="asian",
        aliases=("javanese gamelan", "balinese gamelan", "gong kebyar", "karawitan"),
        description="The bronze percussion orchestras of Java and Bali: metallophones, gong-chimes and hanging "
                    "gongs in layered, cyclic structures, punctuated by great gongs and led by the kendhang drum.",
        era="Java and Bali, centuries old; court traditions of Yogyakarta and Surakarta; Balinese kebyar from c.1915",
        touchstones=("Ki Nartosabdho", "I Wayan Lotring", "I Wayan Beratha", "Gamelan of the Kraton Yogyakarta",
                     "Gunung Sari of Peliatan"),
        tempo=(40, 160),
        feel="colotomic cycles counted in balungan beats; tempo and density (irama) change smoothly",
        swing=50,
        modes=("pelog", "slendro"),
        keys=("C pelog", "D slendro", "E pelog"),
        progressions=(
            "I5-I5",
            "I5-VI5-I5",
            "I5-bII5-I5",
            "slendro: I5-V5-II5-I5",
            "slendro: IV5-I5",
        ),
        harmonic_rhythm=0.25,
        harmony="No chords: harmony is heterophony, many layers elaborating one core melody (balungan) at "
                "different densities, converging on the same goal tone (seleh) at the gong. The progressions "
                "here are those structural gong tones held as open 5ths; avoid triads.",
        voicing="open",
        comping="arpeggio_updown",
        bass_style="whole",
        bass="The gong ageng and kempul supply the 'bass': single deep strokes marking the end of cycles "
             "and phrases, tuned to structural pitches of the balungan. Play long whole notes on cycle ends.",
        melody_density="busy",
        melody_scale="pelog",
        melody="The balungan (skeletal melody on saron and slenthem) moves in 4-note gatra ending on a strong "
               "final beat; bonang paraphrase it in faster patterns; gender, gambang, rebab, suling and "
               "pesindhen (female singer) weave freer lines. In Bali, interlocking kotekan pairs (polos and "
               "sangsih) split fast figures between two players.",
        groove={"step": 1, "swing": 50, "pattern": {
            "low woodblock": "x.x.x.x.x.x.x.x.",
            "high agogo":    "...x...x...x...x",
            "low agogo":     ".....x...x...x..",
            "low floor tom": "...............X",
            "low conga":     "x.ox.ox.x.ox.oxX",
        }},
        drums="Colotomic (punctuating) gongs, here a lancaran cycle of 16 balungan beats: kethuk (low "
              "woodblock) on the off-beats, kenong (high agogo) every 4th beat, kempul (low agogo) on beats "
              "6, 10 and 14, and the gong ageng (low floor tom, a stand-in) on beat 16, which ends and begins "
              "the cycle. The kendhang (low conga) leads tempo changes and signals.",
        form=(("buka (intro)", 4), ("gongan", 16), ("gongan", 16), ("gongan (irama change)", 16),
              ("gongan", 16), ("gongan", 16), ("suwuk (ending)", 4)),
        instruments=("saron", "slenthem", "bonang", "gender", "gambang", "kenong", "kempul", "gong ageng", "kethuk",
                     "kendhang", "rebab", "suling", "pesindhen vocal"),
        sound_design="Bronze metallophones with long, shimmering decay; Balinese instruments are tuned in pairs "
                     "slightly apart so they beat (ombak, the 'wave'); gongs are deep with a slow pitch wobble.",
        production="Ensemble recorded in a pendopo or hall with natural reverb, wide stereo, very dynamic "
                   "(kebyar jumps from whisper to explosive tutti); no compression.",
        theory="Two tuning systems: slendro (five near-equal steps of ~240 cents) and pelog (seven unequal "
               "tones, played in five-note subsets); every gamelan has its own tuning, so 12-tone pelog and "
               "slendro are approximations. Pathet (mode) sets the important tones; music is cyclic and "
               "end-weighted, the strongest beat being the last of the gatra and gongan.",
        mix=Mix(lufs=(-22, -15), lra=(10, 18), low_end="light", tone="bright", width="wide"),
    ),
    Genre(
        name="enka",
        family="asian",
        aliases=("japanese enka",),
        description="Japan's sentimental ballad style: sorrowful minor-key songs of lost love, harbours and "
                    "sake, sung with heavy vibrato and kobushi ornaments over strings, guitar and shamisen.",
        era="Japan, postwar (1950s-80s peak), from earlier ryukoka and Meiji-era street song",
        touchstones=("Misora Hibari", "Sayuri Ishikawa", "Saburo Kitajima", "Hiroshi Itsuki", "Aki Yashiro",
                     "Kiyoshi Hikawa"),
        tempo=(60, 100),
        feel="slow ballad, often a gently swung 'two-beat' or 4/4 lilt",
        swing=58,
        modes=("minor", "harmonic minor", "major"),
        keys=("A minor", "E minor", "D minor", "C major"),
        progressions=(
            "i-iv-V7-i",
            "i-VI-iv-V7",
            "i-iv-i-V7",
            "i-III-iv-V7",
            "major: I-IV-V7-I",
        ),
        harmonic_rhythm=1,
        harmony="Western functional minor harmony with a strong harmonic-minor V7, under a pentatonic melody "
                "that avoids the 4th and 7th; dramatic diminished passing chords and a final ritardando "
                "cadence; occasional major-key songs in yonanuki major.",
        voicing="close",
        comping="arpeggio_up",
        bass_style="root_fifth",
        bass="Simple root-5th bass on electric or upright bass, walking passing tones into each chord change.",
        melody_density="medium",
        melody_scale="hirajoshi",
        melody="Yonanuki minor melodies (the minor scale without its 4th and 7th: same notes as hirajoshi), "
               "slow and wide-ranging, with kobushi (a rapid throat-turn ornament), deep vibrato on long notes, "
               "and dramatic peaks in the final phrase; instrumental obbligato on guitar, sax, shakuhachi or "
               "trumpet between lines.",
        groove={"step": 0.25, "swing": 58, "pattern": {
            "kick":       "x.......x.......",
            "side stick": "....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.",
            "tambourine": "....x.......x...",
        }},
        drums="Gentle drum kit with brushes or side stick, kick on 1 and 3, swung 8th hats; fills are simple "
              "tom rolls into the chorus.",
        form=(("intro", 8), ("verse 1", 16), ("chorus", 8), ("interlude", 8), ("verse 2", 16), ("chorus", 8),
              ("verse 3", 16), ("chorus", 8), ("outro", 4)),
        instruments=("vocals", "string section", "electric guitar", "shamisen", "shakuhachi", "koto", "accordion",
                     "saxophone", "bass", "drum kit"),
        sound_design="Reverb-drenched vocals, a vibrato-laden electric guitar or saxophone lead, lush strings, "
                     "touches of shamisen and koto; a nostalgic Showa-era studio sound.",
        production="Vocal-led, dynamic mix with long hall reverb, orchestral arrangement under a karaoke-ready "
                   "structure; mastered modestly.",
        theory="Japanese pentatonic melody (yonanuki minor) fitted to Western harmonic-minor harmony: the scale "
               "avoids the leading tone the chords provide, a distinctive bittersweet clash.",
        mix=Mix(lufs=(-16, -11), lra=(6, 10), low_end="light", tone="warm", width="moderate"),
    ),
    Genre(
        name="chinese traditional",
        family="asian",
        aliases=("guoyue", "chinese classical", "sizhu", "chinese orchestra"),
        description="Han Chinese instrumental music: pentatonic melodies on erhu, pipa, guzheng, dizi and yangqin, "
                    "played heterophonically and richly ornamented, from intimate silk-and-bamboo to modern orchestra.",
        era="Ancient roots; modern guoyue repertoire and Chinese orchestra from the 1920s-50s",
        touchstones=("Abing", "Liu Tianhua", "Wu Man", "Chen Gang & He Zhanhao", "Lin Shicheng",
                     "Hong Kong Chinese Orchestra"),
        tempo=(50, 140),
        feel="free sanban rubato introductions, then a steady 2/4 or 4/4; sections often accelerate",
        swing=50,
        modes=("major pentatonic", "egyptian", "ritusen", "minor pentatonic", "man gong"),
        keys=("D major pentatonic", "G major pentatonic", "A minor pentatonic", "F major pentatonic"),
        progressions=(
            "I5-I5",
            "Iadd9-vi7",
            "I-vi-ii-V",
            "vi7-Iadd9",
            "minor pentatonic: i-III-VII-i",
        ),
        harmonic_rhythm=0.5,
        harmony="Traditional music is heterophonic, not chordal: all instruments play variants of one melody "
                "over open 5ths. Modern orchestral arrangements add pentatonic-friendly harmony (add9, m7, "
                "quartal stacks) that avoids leading-tone pulls; the progressions here are that modern practice.",
        voicing="quartal",
        comping="arpeggio_updown",
        bass_style="pedal",
        bass="Traditionally none; modern orchestras use gehu or cello and double bass for pedals and slow "
             "root motion, often a tonic or 5th drone.",
        melody_density="busy",
        melody_scale="major pentatonic",
        melody="Pentatonic modes (gong, shang, jue, zhi, yu) with the two 'bian' passing tones as ornaments; "
               "erhu slides (huayin) and vibrato, pipa tremolo (lunzhi) and pushes, guzheng glissandi and "
               "bending pressed notes, dizi flutter and grace notes; phrases expand from a theme by "
               "variation (the 'baban' 68-beat form) and speed up toward the end.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "claves":         "x.......x.......",
            "high woodblock": "x.x.xxx.x.x.xxx.",
            "low tom":        "x...x..x..x.x...",
            "china":          "....x.......x...",
            "ride bell":      "..x...x...x...x.",
        }},
        drums="Luogu (gong and drum) ensemble: bangu and clapper (ban, here claves and high woodblock) lead, "
              "tanggu barrel drum (low tom), bo cymbals (china) and small gong xiaoluo (ride bell) punctuate; "
              "in silk-and-bamboo chamber music the only percussion is the clapper marking strong beats.",
        form=(("sanban rubato intro", 8), ("slow theme", 16), ("variation", 16), ("faster variation", 16),
              ("climax", 16), ("coda", 4)),
        instruments=("erhu", "pipa", "guzheng", "dizi", "yangqin", "sheng", "suona", "ruan", "luogu percussion"),
        sound_design="Acoustic instruments recorded close for detail: erhu's nasal two-string tone, pipa's "
                     "crisp attacks, guzheng's ringing bent notes, bright bamboo dizi with a buzzing membrane; "
                     "natural hall reverb.",
        production="Chamber or concert balance with the solo instrument featured, wide stereo orchestra, "
                   "very dynamic; modern crossovers add pads and light beats.",
        theory="Anhemitonic pentatonic modes rotated from one set of five tones; melody is primary, harmony "
               "secondary. Tuning of some regional styles (e.g. Chaozhou, Kejia) bends pitches between "
               "12-tone steps, which the pentatonic scales here only approximate.",
        mix=Mix(lufs=(-20, -14), lra=(8, 16), low_end="light", tone="bright", width="wide"),
    ),
    # ---------------------------------------------------------- Middle Eastern
    Genre(
        name="arabic pop",
        family="middle eastern",
        aliases=("arab pop", "egyptian pop", "lebanese pop"),
        parent="arabic classical",
        description="Modern pan-Arab pop from Cairo, Beirut and the Gulf: maqam melodies and darbuka rhythms "
                    "like maqsum and baladi under polished pop production, strings, synths and big vocal hooks.",
        era="Cairo and Beirut, 1980s-90s al-jeel wave; pan-Arab satellite pop 2000s onward",
        touchstones=("Amr Diab", "Nancy Ajram", "Haifa Wehbe", "Elissa", "Tamer Hosny", "Wael Kfoury",
                     "Hakim", "Mohamed Mounir"),
        tempo=(90, 128),
        feel="maqsum or baladi on darbuka over a straight pop kit; light swing in the riq",
        swing=53,
        modes=("minor", "hijaz", "harmonic minor", "kurd"),
        keys=("D minor", "C minor", "G minor", "D hijaz"),
        progressions=(
            "i-VII-VI-V",
            "i-iv-V-i",
            "i-VI-III-VII",
            "hijaz: I-II-I",
            "hijaz: I-iv-vii-I",
            "kurd: i-II-i-VII",
        ),
        harmonic_rhythm=1,
        harmony="Pop chords chosen to fit the maqam: nahawand (minor/harmonic minor) songs use i-iv-V and the "
                "descending i-bVII-bVI-V; hijaz songs pivot between the major tonic and the bII; kurd "
                "(phrygian) uses i-bII. Many sections stay on one chord so quarter-tone maqam melodies aren't "
                "contradicted.",
        voicing="close",
        comping="stabs",
        bass_style="syncopated",
        bass="Syncopated synth or electric bass doubling the darbuka's dum strokes (beat 1 and the 'and' of "
             "2 in maqsum), with octave jumps; Gulf styles push heavier subs.",
        melody_density="busy",
        melody_scale="hijaz",
        melody="Ornamented vocals moving stepwise within a maqam, with melisma, trills, and a mawwal (free "
               "improvised vocal intro); hooks answered by unison string-section or qanun and nay fills; "
               "call-and-response with the chorus.",
        groove={"step": 0.25, "swing": 53, "pattern": {
            "low conga":  "x.......x.......",
            "high conga": "..x.o.x...o.x.o.",
            "kick":       "x.......x..x....",
            "clap":       "....x.......x...",
            "tambourine": "xoxoxoxoxoxoxoxo",
        }},
        drums="Darbuka plays maqsum: dum (low conga) on 1 and 3, tek (high conga) on the 'and' of 1, the 'and' "
              "of 2 and beat 4, with kas fills; riq (tambourine) 16ths; a pop kit reinforces dum with kick "
              "and adds claps; fills are darbuka rolls.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("instrumental", 8), ("verse", 16), ("chorus", 8),
              ("bridge", 8), ("chorus", 8), ("outro", 4)),
        instruments=("darbuka", "riq", "drum programming", "string section", "oud", "qanun", "nay", "accordion",
                     "synthesizers", "bass", "vocals"),
        sound_design="Bright, crisp darbuka; Egyptian-style unison string section with wide vibrato; synth "
                     "qanun and plucks; tuned vocals with long delays; Gulf (khaleeji) songs add hand-clap "
                     "layers.",
        production="Glossy, loud pop mix: vocal forward and bright, percussion wide, low end solid; quarter-tone "
                   "synths or retuned samples for maqam notes.",
        theory="Maqam melody (nahawand, hijaz, kurd, bayati, saba, rast) with the iqa' maqsum (dum tek - tek "
               "dum - tek -) and baladi (dum dum - tek dum - tek -); bayati, rast and saba use quarter-tone "
               "notes, here approximated by the nearest 12-tone modes.",
        mix=Mix(lufs=(-10, -7), lra=(4, 8), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="arabic classical",
        family="middle eastern",
        aliases=("tarab", "maqam music", "arab classical", "takht"),
        description="The art music of the Arab world: maqam melodies sung and played by a takht (oud, qanun, nay, "
                    "violin, riq) or a large firqa, aiming for tarab, the shared ecstasy of performer and listener.",
        era="Cairo, Aleppo, Baghdad; 19th-century nahda to the mid-20th-century golden age",
        touchstones=("Umm Kulthum", "Mohammed Abdel Wahab", "Riad Al Sunbati", "Fairuz", "Sabah Fakhri",
                     "Munir Bashir", "Farid al-Atrash"),
        tempo=(50, 130),
        feel="iqa'at (rhythmic modes) such as maqsum, masmoudi, baladi or sama'i thaqil; free-rhythm taqasim",
        swing=52,
        modes=("kurd", "hijaz", "nahawand", "major", "mixolydian"),
        keys=("D kurd", "D hijaz", "C nahawand", "C major"),
        progressions=(
            "I5-I5",
            "I5-IV5-I5",
            "hijaz: I5-IV5-I5",
            "nahawand: I5-V5-I5",
            "major: I5-V5-I5",
        ),
        harmonic_rhythm=0.25,
        harmony="Monophonic and heterophonic: no chords. Interest comes from modulating between maqamat and "
                "between the ajnas (3-5 note cells) inside a maqam. The progressions here are drones on the "
                "qarar (tonic) and the ghammaz (the pivot note, the 4th in bayati/hijaz/kurd, the 5th in "
                "rast/nahawand); never harmonise in triads.",
        voicing="open",
        comping="none",
        bass_style="pedal",
        bass="No bass line; the cello or double bass of a firqa doubles the melody an octave down or holds "
             "the tonic. A quiet tonic pedal is the closest translation.",
        melody_density="busy",
        melody_scale="kurd",
        melody="Long, ornamented melodies within a maqam's ajnas; sayr (the conventional path through the "
               "maqam), modulation to related maqamat, then a qafla (cadence) home; taqasim (free improvised "
               "solos) on oud, qanun or nay; sung lines repeated and varied to build tarab.",
        groove={"step": 0.25, "swing": 52, "pattern": {
            "low conga":  "x.x.....x.......",
            "high conga": "....o.x...o.x.o.",
            "tambourine": "x.o.x.o.x.o.x.o.",
        }},
        drums="Riq (frame drum with jingles) leads with the iqa', here baladi / masmoudi saghir: dum dum - tek "
              "dum - tek - (dum = low conga, tek = high conga); darbuka or daff support it; taqasim sections "
              "are unmetered and unaccompanied.",
        form=(("taqsim", 8), ("muqaddima (instrumental prelude)", 16), ("madhhab (refrain)", 16), ("taqsim", 8),
              ("ghusn (verse)", 16), ("madhhab", 16), ("ghusn", 16), ("qafla", 8)),
        instruments=("oud", "qanun", "nay", "violin", "riq", "darbuka", "cello", "vocals"),
        sound_design="Acoustic takht: oud's dark plucked tone, qanun's bright zither tremolos, breathy nay, "
                     "violin tuned in the Arab manner with wide vibrato; recorded naturally in a room or hall.",
        production="Live-concert dynamics and length (songs of 30-60 minutes), singer central, minimal "
                   "processing; restoration of vintage recordings preserves the room and audience response.",
        theory="Maqam theory: a maqam is built from ajnas (e.g. hijaz, bayati, rast, saba, nahawand, kurd, ajam, "
               "sikah) with a tonic (qarar) and pivot (ghammaz). Rast and bayati use half-flat (neutral) "
               "seconds or thirds and saba a lowered 4th; the 12-tone modes here are approximations: kurd for "
               "bayati, major for rast, phrygian dominant for hijaz.",
        mix=Mix(lufs=(-22, -15), lra=(10, 16), low_end="light", tone="warm", width="moderate"),
    ),
    Genre(
        name="turkish pop",
        family="middle eastern",
        aliases=("turkce pop", "turkpop", "turk pop"),
        description="Turkey's mainstream pop: Western pop production around makam-tinged melodies, darbuka "
                    "rhythms and occasional 9/8, with strings, saz and clarinet colouring big dance hooks.",
        era="Istanbul, 1970s-80s roots (Ajda Pekkan, Sezen Aksu); 1990s boom with Tarkan",
        touchstones=("Tarkan", "Sezen Aksu", "Ajda Pekkan", "Sertab Erener", "Mustafa Sandal", "Hande Yener",
                     "Kenan Dogulu"),
        tempo=(92, 130),
        feel="straight 4/4 with darbuka syncopation; some songs in 9/8 karsilama (2+2+2+3)",
        swing=52,
        modes=("minor", "hijaz", "harmonic minor", "kurd"),
        keys=("A minor", "D minor", "E minor", "A hijaz"),
        progressions=(
            "i-VII-VI-V",
            "i-iv-VII-III",
            "i-VI-VII-i",
            "i-iv-V-i",
            "hijaz: I-II-I",
        ),
        harmonic_rhythm=1,
        harmony="Minor-key pop harmony bent to fit makam melody: descending i-bVII-bVI-V (Andalusian), "
                "harmonic-minor V, and hicaz sections pivoting on the major tonic with bII; choruses lift to "
                "the relative major.",
        voicing="close",
        comping="stabs",
        bass_style="syncopated",
        bass="Syncopated electric or synth bass following the darbuka's dum strokes, with octave pops on the "
             "offbeats.",
        melody_density="busy",
        melody_scale="harmonic minor",
        melody="Makam-flavoured vocals (hicaz, nihavend, kurdi, ussak) with melismatic runs, slides and "
               "trills; catchy repeated chorus hooks; clarinet, saz or violin answer phrases in the gaps.",
        groove={"step": 0.25, "swing": 52, "pattern": {
            "kick":       "x.....x.x.......",
            "clap":       "....x.......x...",
            "low conga":  "x.....x.x.......",
            "high conga": "..x.x...o.x.x.xo",
            "tambourine": "x.x.x.x.x.x.x.x.",
        }},
        drums="Darbuka (low conga dum, high conga tek) plays maqsum or a pop variant with fast rolls (parmak "
              "zil fills); a drum kit or programmed beat adds kick and claps; tambourine 8ths; 9/8 roman "
              "havasi songs accent 2+2+2+3.",
        form=(("intro", 8), ("verse", 16), ("pre-chorus", 4), ("chorus", 8), ("instrumental", 8), ("verse", 16),
              ("chorus", 8), ("chorus", 8), ("outro", 4)),
        instruments=("darbuka", "drum programming", "baglama (saz)", "clarinet", "kanun", "string section", "ney",
                     "synthesizers", "bass", "vocals"),
        sound_design="Bright darbuka, Turkish-style string section with tight unison runs, saz and clarinet "
                     "leads, 1990s synths and modern EDM layers.",
        production="Polished, loud pop mix, vocal forward; percussion wide; makam pitches handled by tuned "
                   "samples or live players.",
        theory="Turkish makam uses a 53-comma division with intervals smaller than a semitone (e.g. the slightly "
               "flat 2nd of ussak); 12-tone hijaz, harmonic minor and phrygian are the nearest approximations. "
               "Aksak meters (9/8, 7/8) appear in folk-derived songs.",
        mix=Mix(lufs=(-10, -7), lra=(4, 8), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="rai",
        family="middle eastern",
        aliases=("pop rai", "algerian rai"),
        description="Algeria's rebellious popular song from Oran: Bedouin melodies and gasba flute turned into "
                    "electric pop with drum machines, synths, accordion and the swung rai rhythm.",
        era="Oran, Algeria; cheikha tradition early 20th century; pop rai 1980s; France and global from the 1990s",
        touchstones=("Cheb Khaled", "Cheb Mami", "Cheikha Rimitti", "Cheb Hasni", "Rachid Taha", "Faudel",
                     "Chaba Fadela"),
        tempo=(90, 124),
        feel="swung, rolling 4/4 (or 6/8) rai rhythm from the gellal and derbouka",
        swing=62,
        modes=("phrygian dominant", "minor", "phrygian"),
        keys=("E phrygian dominant", "A phrygian dominant", "D minor", "E phrygian"),
        progressions=(
            "I-II-I",
            "I-iv-I-II",
            "I-II-vii-I",
            "minor: i-VII-VI-V",
            "minor: i-iv-VII-i",
        ),
        harmonic_rhythm=0.5,
        harmony="Modal: songs sit on the tonic of a hijaz-like (phrygian dominant) or minor mode, moving to the "
                "bII or bVII and back; pop rai adds the descending i-bVII-bVI-V and simple minor loops on synth.",
        voicing="close",
        comping="offbeat",
        bass_style="syncopated",
        bass="Synth or electric bass on syncopated root figures tied to the derbouka dum strokes; funky in 1980s "
             "productions.",
        melody_density="busy",
        melody_scale="phrygian dominant",
        melody="Raw, expressive vocals in Algerian Arabic and French with melismas, trills and long held cries; "
               "short repeated chorus refrains; accordion, synth, trumpet or gasba-style flute answer each line.",
        groove={"step": 0.25, "swing": 62, "pattern": {
            "kick":       "x..x..x.x.......",
            "clap":       "....x.......x...",
            "low conga":  "x..x..x...x.x...",
            "high conga": "..x...x.xx..x.x.",
            "tambourine": "x.x.x.x.x.x.x.x.",
        }},
        drums="Drum machine (classic 1980s units) plus derbouka (low/high conga for dum and tek) and gellal "
              "frame drum in a swung pattern; claps on 2 and 4; tambourine 8ths.",
        form=(("intro", 8), ("verse", 16), ("refrain", 8), ("instrumental", 8), ("verse", 16), ("refrain", 8),
              ("solo", 8), ("refrain", 8), ("outro", 4)),
        instruments=("vocals", "synthesizer", "accordion", "derbouka", "gellal", "drum machine", "electric bass",
                     "trumpet", "saxophone", "gasba"),
        sound_design="1980s synths and drum machines (bright, slightly cheap and charming), wah guitar, reedy "
                     "accordion, raspy brass; later productions polish this with funk and reggae elements.",
        production="Vocal-led, mid-heavy mixes; reverb and delay on vocals; percussion upfront.",
        theory="Arab-Andalusian and Bedouin modes (hijaz-like phrygian dominant, minor) over a swung rhythm; "
               "vocal intonation bends microtonally around the 2nd and 3rd degrees.",
        mix=Mix(lufs=(-12, -8), lra=(5, 8), low_end="moderate", tone="bright", width="moderate"),
    ),
    # ----------------------------------------------------------- European folk
    Genre(
        name="klezmer",
        family="european folk",
        aliases=("klezmorim", "freylekhs", "yiddish music"),
        description="The celebration music of Ashkenazi Jews: clarinet and fiddle crying and laughing through "
                    "freygish modes, over oom-pah bass and drum, from free doinas to whirling freylekhs.",
        era="Eastern Europe 19th century; New York 1910s-40s recordings; revival from the 1970s",
        touchstones=("Naftule Brandwein", "Dave Tarras", "Abe Schwartz", "The Klezmatics", "Andy Statman",
                     "Giora Feidman", "Budowitz", "Brave Old World"),
        tempo=(80, 160),
        meter="2/4",
        feel="2/4 freylekhs and bulgar with a 3-3-2 accent; slow zhok/hora limps in 3/8; doina is unmetered",
        swing=52,
        modes=("phrygian dominant", "ukrainian dorian", "minor", "mixolydian"),
        keys=("D phrygian dominant", "A phrygian dominant", "D ukrainian dorian", "G minor"),
        progressions=(
            "I-iv-I-I",
            "I-II-I",
            "iv-I-vii-I",
            "ukrainian dorian: i-II-i",
            "minor: i-iv-V-i",
        ),
        harmonic_rhythm=1,
        harmony="Modal: freygish (phrygian dominant, 'ahava rabbah') tunes sit on a major tonic with the minor "
                "iv and minor vii (a whole step below) and the bII; mi sheberach (ukrainian dorian) tunes move "
                "i-II-i; 'magen avot' minor uses iv and V. Chords change slowly under fast melodies.",
        voicing="close",
        comping="offbeat",
        bass_style="root_fifth",
        bass="Tuba, bass or cimbalom-left-hand on the beats (root and 5th), oom-pah with the 'secund' "
             "(second fiddle or accordion) on the offbeats; bulgar sections accent the 3-3-2.",
        melody_density="busy",
        melody_scale="phrygian dominant",
        melody="Speech-like, sobbing ornaments: krekhts (a choked 'sob' or hiccup), kneytsh, glissandi, "
               "dreydlekh (trills and mordents), bent notes; doina is a free improvised lament over a held "
               "chord; dance tunes in two or three 8- or 16-bar parts, played repeatedly and getting faster.",
        groove={"step": 0.25, "swing": 52, "pattern": {
            "bass drum": "x..x..x.x..x..x.",
            "snare":     "..x...x...x...x.",
            "crash":     "x...............",
        }},
        drums="Bass drum with a small cymbal mounted on top (poyk and tshinel), struck with a beater and a "
              "switch: the bass drum here accents the bulgar's 3-3-2 across each 2/4 bar, snare or cymbal "
              "on the offbeats; doinas and slow pieces have no drums.",
        form=(("doina (rubato)", 8), ("A", 16), ("A", 16), ("B", 16), ("B", 16), ("C", 16), ("A", 16),
              ("faster A-B", 32), ("tag", 4)),
        instruments=("clarinet", "violin", "accordion", "trumpet", "trombone", "tuba or bass", "cimbalom",
                     "tsimbl", "poyk drum"),
        sound_design="Bright, vocal clarinet (Albert system) with a cutting top, raw fiddle, wheezy accordion, "
                     "brass with a festive edge; 78-rpm-era recordings are mid-heavy and lively.",
        production="Live band in a room, melody instruments forward, minimal processing, dynamic arcs as tunes "
                   "speed up.",
        theory="Modes named after synagogue prayer modes (shteygers): freygish's augmented 2nd between degrees 2 "
               "and 3 and mi sheberach's raised 4th give the characteristic sound; the bulgar's 3-3-2 "
               "subdivision shares roots with Balkan and Greek dance rhythms.",
        mix=Mix(lufs=(-18, -12), lra=(8, 14), low_end="light", tone="bright", width="moderate"),
    ),
    Genre(
        name="celtic",
        family="european folk",
        aliases=("irish traditional", "irish trad", "scottish traditional", "jigs and reels", "celtic trad"),
        description="The dance music of Ireland and Scotland: jigs in 6/8, reels and hornpipes in 4/4, played on "
                    "fiddle, flute, tin whistle, uilleann pipes and accordion over bodhran and guitar or bouzouki.",
        era="Ireland and Scotland, 18th-19th century repertoire; revival and band era from the 1960s-70s",
        touchstones=("The Chieftains", "The Bothy Band", "Planxty", "Altan", "Lunasa", "Martin Hayes",
                     "Matt Molloy", "Capercaillie"),
        tempo=(160, 190),
        meter="6/8",
        feel="lilting compound 6/8 jig (dotted quarter ~105-125, here in quarter-note BPM); reels are 4/4 at "
             "half note ~100-120",
        swing=52,
        modes=("major", "mixolydian", "dorian", "minor"),
        keys=("D major", "G major", "A dorian", "E minor", "A mixolydian"),
        progressions=(
            "I-IV-I-V",
            "I-V-IV-I",
            "mixolydian: I-VII-I",
            "dorian: i-IV-i-VII",
            "minor: i-VII-VI-VII",
            "vi-IV-I-V",
        ),
        harmonic_rhythm=1,
        harmony="Tunes are melodic and modal; accompaniment (DADGAD guitar, bouzouki, piano) favours open, "
                "drone-friendly chords: I, IV, V in major, I-bVII in mixolydian, i-IV and i-bVII in dorian, "
                "sus2/sus4 colours and 5ths ringing over open strings. Harmony changes once or twice a bar.",
        voicing="open",
        comping="strum",
        bass_style="root_fifth",
        bass="Traditional sessions have no bass; band arrangements use bouzouki or guitar bass notes and the "
             "occasional double bass on root and 5th, often over a tonic drone (pipes' drones in Scottish music).",
        melody_density="busy",
        melody_scale="major",
        melody="Fast, stepwise 8th-note lines in 8-bar parts (AABB, each played twice), tunes played in sets "
               "of two or three; ornaments: cuts, taps, rolls, cranns, slides and triplets; modal colour "
               "from mixolydian and dorian; slow airs are free and highly ornamented.",
        groove={"step": 0.5, "swing": 52, "pattern": {
            "low tom":  "X..x..X..x..",
            "high tom": ".xo.xo.xo.xx",
        }},
        drums="Bodhran (frame drum played with a double-ended tipper): bass tones (low tom) on the dotted-quarter "
              "beats and a rolling stream of upstrokes and pressed high tones (high tom) through all six 8ths of "
              "the jig; bands may add a light kit or djembe in arrangements.",
        form=(("intro", 4), ("tune 1 A", 8), ("tune 1 A", 8), ("tune 1 B", 8), ("tune 1 B", 8), ("tune 2 A", 8),
              ("tune 2 A", 8), ("tune 2 B", 8), ("tune 2 B", 8), ("ending", 2)),
        instruments=("fiddle", "flute", "tin whistle", "uilleann pipes", "button accordion", "concertina",
                     "bodhran", "bouzouki", "guitar (DADGAD)", "harp"),
        sound_design="Acoustic and woody: bright fiddle, breathy wooden flute, reedy pipes with drones, guitar "
                     "in open tunings; band productions add warm reverb and occasional pads.",
        production="Natural live balance, melody players centred, accompaniment spread; dynamic, unprocessed.",
        theory="Modal folk melody (ionian, mixolydian, dorian, aeolian) over drones; rhythms named by dance "
               "type: jig 6/8, slip jig 9/8, reel 4/4, hornpipe dotted 4/4, polka 2/4, slide 12/8.",
        mix=Mix(lufs=(-18, -12), lra=(7, 12), low_end="light", tone="bright", width="wide"),
    ),
    Genre(
        name="balkan brass",
        family="european folk",
        aliases=("serbian brass", "guca brass", "romani brass", "balkan brass band"),
        description="The brass bands of Serbia, Macedonia and Romania: blazing trumpets and flugelhorns over tuba "
                    "oom-pah and a tapan drum, in fast kolo 2/4, cocek 9/8 and limping 7/8 aksak meters.",
        era="Serbia, Macedonia and Romania, 19th-century military bands; Guca festival from 1961; global from the 1990s",
        touchstones=("Boban Markovic Orkestar", "Fanfare Ciocarlia", "Kocani Orkestar", "Goran Bregovic",
                     "Esma Redzepova", "Saban Bajramovic"),
        tempo=(130, 200),
        meter="7/8",
        feel="aksak 7/8 (3+2+2), here in quarter-note BPM; also 9/8 (2+2+2+3) cocek and fast 2/4 kolo",
        swing=50,
        modes=("minor", "phrygian dominant", "ukrainian dorian", "major"),
        keys=("G minor", "D minor", "A phrygian dominant", "Bb major"),
        progressions=(
            "i-iv-V-i",
            "i-iv-VII-III",
            "i-VII-i-V",
            "phrygian dominant: I-iv-I",
            "major: I-V-I-IV",
        ),
        harmonic_rhythm=1,
        harmony="Simple functional harmony in minor (i-iv-V) and phrygian dominant (I with minor iv) under "
                "virtuosic melody; tenor horns and baritones fill in the chords on the offbeats.",
        voicing="close",
        comping="offbeat",
        bass_style="root_fifth",
        bass="Tuba or helicon on root and 5th at the start of each beat group (3+2+2), with fast chromatic "
             "runs into new sections.",
        melody_density="busy",
        melody_scale="phrygian dominant",
        melody="Trumpets and flugelhorns in parallel 3rds, fast ornamented runs, trills and bends; Romani "
               "cocek melodies in hijaz-like modes; solos are flashy and show-off; the melody leans into the "
               "long beat of the aksak bar.",
        groove={"step": 0.5, "swing": 50, "pattern": {
            "low floor tom": "X..x.x.X..x.x.",
            "rim":           ".xx.x.x.xx.x.x",
            "crash":         "X.............",
        }},
        drums="Tapan (big double-headed drum): the mallet side (low floor tom) marks each beat group of "
              "3+2+2 and the thin switch side (rim) fills between; a snare often doubles the switch; crash "
              "on section downbeats.",
        form=(("intro", 4), ("A", 16), ("A", 16), ("B", 16), ("solo", 16), ("A", 16), ("B", 16), ("ending", 4)),
        instruments=("trumpet", "flugelhorn", "tenor horn", "baritone horn", "tuba or helicon", "saxophone",
                     "clarinet", "tapan", "snare drum"),
        sound_design="Loud, bright, brassy: open horns with strong vibrato and occasional overblown edge, tuba "
                     "punchy and round, tapan booming with a dry switch crack.",
        production="Live-band energy: horns forward and wide, tuba and tapan the low end, little reverb; "
                   "festival recordings include crowd noise.",
        theory="Aksak ('limping') meters group 8th notes in uneven 2s and 3s: 7/8 = 3+2+2 (lesnoto) or 2+2+3, "
               "9/8 = 2+2+2+3 (cocek), 11/8 = 2+2+3+2+2 (kopanica); modes include phrygian dominant and "
               "ukrainian dorian from Ottoman makam heritage.",
        mix=Mix(lufs=(-14, -9), lra=(6, 10), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="fado",
        family="european folk",
        aliases=("portuguese fado", "fado de coimbra", "fado lisboa"),
        description="Portugal's song of saudade: a solo voice of deep longing accompanied by the shimmering "
                    "12-string guitarra portuguesa and the classical viola, intimate and unhurried.",
        era="Lisbon taverns, 1820s-40s; Coimbra student tradition; Amalia Rodrigues era 1950s-70s; revival 2000s",
        touchstones=("Amalia Rodrigues", "Carlos do Carmo", "Alfredo Marceneiro", "Carlos Paredes", "Mariza",
                     "Ana Moura", "Camane", "Dulce Pontes"),
        tempo=(60, 120),
        feel="rubato vocal over a steady bass-and-chord pulse; fado corrido brisk, fado menor slow",
        swing=50,
        modes=("minor", "major", "harmonic minor"),
        keys=("E minor", "A minor", "D minor", "G major"),
        progressions=(
            "i-V7-i-V7",
            "i-iv-V7-i",
            "i-iv-i-V7",
            "major: I-V7-V7-I",
            "major: I-I7-IV-V7",
        ),
        harmonic_rhythm=1,
        harmony="Very simple: tonic and dominant 7th alternating (fado menor in minor, fado corrido and mouraria "
                "in major), with iv and secondary dominants; traditional fados are fixed chord frames on which "
                "many different lyrics are sung.",
        voicing="close",
        comping="offbeat",
        bass_style="root_fifth",
        bass="The viola (classical guitar) or viola baixo (acoustic bass guitar) plays bass on beats 1 and 3, "
             "root and 5th, with short scalar runs into chord changes.",
        melody_density="medium",
        melody_scale="harmonic minor",
        melody="Free, declamatory vocal phrasing that stretches and anticipates the beat, with ornamental "
               "turns, sighs and dramatic crescendos; the guitarra plays a counter-melody, fills between "
               "vocal lines and an instrumental introduction in 3rds and 6ths with tremolo.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.......x.......",
            "side stick": "....x.......x...",
        }},
        drums="Traditionally no drums at all. This groove only marks the viola's pulse (bass note on 1 and 3, "
              "chord on 2 and 4); mute it or replace it with the guitar part. Modern arrangements may add very "
              "light brushes or a frame drum.",
        form=(("guitarra intro", 4), ("verse", 16), ("verse", 16), ("guitarra interlude", 4), ("verse", 16),
              ("verse", 16), ("final cadence", 2)),
        instruments=("guitarra portuguesa", "viola (classical guitar)", "viola baixo", "voice"),
        sound_design="Guitarra portuguesa: bright, metallic, 6 courses of double steel strings with tremolo "
                     "picking; nylon-string viola warm and percussive; the voice close and natural.",
        production="Intimate, dry-to-roomy: voice centred, guitarra right, viola left; no compression to speak "
                   "of, wide dynamics, a small venue (casa de fado) ambience.",
        theory="A song frame of tonic and dominant (like a ground) over which melodies and lyrics are improvised "
               "and swapped; the harmonic-minor raised 7th and expressive rubato carry the saudade.",
        mix=Mix(lufs=(-20, -14), lra=(8, 14), low_end="light", tone="warm", width="narrow"),
    ),
    Genre(
        name="polka",
        family="european folk",
        aliases=("polka band", "slovenian polka", "polish polka", "bohemian polka"),
        description="The bouncing 2/4 couple dance from Bohemia that swept the world: accordion, clarinet and "
                    "brass over an oom-pah bass and offbeat chords, cheerful, fast and danceable.",
        era="Bohemia, 1830s; spread across Europe and the Americas; Polish-American and Slovenian styles 20th century",
        touchstones=("Frankie Yankovic", "Slavko Avsenik", "Jimmy Sturr", "Ernst Mosch", "Li'l Wally",
                     "Walter Ostanek"),
        tempo=(110, 150),
        meter="2/4",
        feel="bouncy 2/4: bass on the beat, chord on the offbeat (oom-pah)",
        swing=50,
        modes=("major",),
        keys=("Bb major", "F major", "Eb major", "C major"),
        progressions=(
            "I-V7-V7-I",
            "I-IV-V7-I",
            "I-I-V7-I",
            "IV-I-V7-I",
            "I-vi-ii-V7",
        ),
        harmonic_rhythm=1,
        harmony="Plain major-key harmony: I and V7 in 8- or 16-bar strains, IV and secondary dominants for "
                "colour, and a trio section in the subdominant key; melodies run in parallel 3rds.",
        voicing="close",
        comping="offbeat",
        bass_style="root_fifth",
        bass="Tuba or bass guitar alternating root and 5th on each beat (oom), with scalar walk-ups between "
             "strains.",
        melody_density="busy",
        melody_scale="major",
        melody="Bright, arpeggio-based tunes in 8-bar phrases, often harmonised in 3rds by clarinet and trumpet "
               "or accordion; grace notes and short trills; vocal refrains in Polish, Slovenian, Czech, German "
               "or English.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "bass drum": "x...x...x...x...",
            "snare":     "..x...x...x...x.",
            "crash":     "x...............",
        }},
        drums="Bass drum on each beat, snare (or snare plus cymbal) on the offbeats, crash at phrase ends; "
              "Polish-American 'honky' style adds a heavier backbeat; drum rolls lead into new strains.",
        form=(("intro", 4), ("A", 16), ("A", 16), ("B", 16), ("A", 16), ("trio", 16), ("trio", 16),
              ("A", 16), ("tag", 2)),
        instruments=("accordion", "clarinet", "trumpet", "tuba", "tenor horn", "banjo", "drum kit", "vocals"),
        sound_design="Bright accordion with musette tuning, woody clarinet, punchy brass, plucky banjo "
                     "(Slovenian style); simple, honest band sound.",
        production="Band-in-a-hall balance with lead instruments forward, light reverb, moderate compression.",
        theory="March-like strain forms (AABA plus trio in IV) in 2/4; the oom-pah is a bass-chord alternation "
               "that keeps the dance's hop-step.",
        mix=Mix(lufs=(-14, -10), lra=(5, 8), low_end="moderate", tone="bright", width="moderate"),
    ),
    Genre(
        name="schlager",
        family="european folk",
        aliases=("schlagermusik", "german schlager", "disco fox", "discofox"),
        description="German-speaking Europe's sentimental hit music: catchy, singalong melodies about love and "
                    "longing over a disco-fox beat, bright synths and big key-change choruses.",
        era="Germany, Austria and Switzerland, 1950s onward; disco-fox schlager from the 1980s; modern revival 2010s",
        touchstones=("Helene Fischer", "Andrea Berg", "Roland Kaiser", "Udo Jurgens", "Wolfgang Petry",
                     "Howard Carpendale", "Vicky Leandros"),
        tempo=(110, 135),
        feel="disco-fox four-on-the-floor; older schlager in foxtrot or march feel",
        swing=50,
        modes=("major", "minor"),
        keys=("G major", "D major", "A major", "A minor"),
        progressions=(
            "I-V-vi-IV",
            "vi-IV-I-V",
            "I-vi-IV-V",
            "I-IV-V-I",
            "minor: i-VII-VI-V",
        ),
        harmonic_rhythm=1,
        harmony="Diatonic pop harmony with clear cadences; the final chorus modulates up a semitone or whole "
                "tone; minor-key songs use the descending i-bVII-bVI-V; nothing ambiguous.",
        voicing="close",
        comping="offbeat",
        bass_style="octaves",
        bass="Disco octave bass bouncing between root and octave on 8ths, or root-5th; synth bass in modern "
             "productions.",
        melody_density="medium",
        melody_scale="major",
        melody="Simple, stepwise, singable melodies in a comfortable range; the chorus hook is the title, "
               "repeated; syllabic phrasing for crowd singalongs; instrumental hook on synth or sax.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x...x...x...x...",
            "clap":       "....x.......x...",
            "snare":      "....x.......x...",
            "closed hat": "xx.xxx.xxx.xxx.x",
            "open hat":   "..x...x...x...x.",
        }},
        drums="Disco fox: kick on every beat, snare and clap on 2 and 4, offbeat open hats over 16th closed "
              "hats; fills are short snare rolls into choruses.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("bridge", 8),
              ("chorus (key change)", 8), ("chorus", 8), ("outro", 4)),
        instruments=("drum programming", "synth bass", "synth pads", "piano", "electric guitar", "accordion",
                     "saxophone", "strings", "vocals"),
        sound_design="Glossy, bright synths and pianos, clean guitar, 1980s-style polysynth brass, modern EDM "
                     "risers in recent productions; vocals bright and upfront.",
        production="Radio-friendly, loud and polished: vocal on top, four-on-the-floor kick solid, wide synths.",
        theory="Classic pop functional harmony and the truck-driver's modulation for the final chorus; foxtrot "
               "and disco-fox dance rhythms.",
        mix=Mix(lufs=(-10, -7), lra=(4, 7), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="nordic folk",
        family="european folk",
        aliases=("scandinavian folk", "swedish folk", "norwegian folk", "polska", "nordic trad"),
        description="The fiddle and nyckelharpa traditions of Sweden, Norway and Finland: modal tunes with "
                    "drones, lopsided 3/4 polskas, Hardanger fiddle ringing with sympathetic strings, and kulning calls.",
        era="Sweden, Norway and Finland, 18th-19th century repertoire; folk revival from the 1970s",
        touchstones=("Vasen", "Hedningarna", "Varttina", "Annbjorg Lien", "Lena Willemark", "Frifot",
                     "Hoven Droven"),
        tempo=(100, 140),
        meter="3/4",
        feel="3/4 polska with an uneven, dance-shaped pulse (a long or early beat depending on region)",
        swing=54,
        modes=("minor", "dorian", "major", "mixolydian"),
        keys=("D minor", "A minor", "G major", "D dorian"),
        progressions=(
            "i-VII-i-v",
            "I5-VII5-I5",
            "dorian: i-IV-i-VII",
            "major: I-V-I-IV",
            "i-iv-v-i",
        ),
        harmonic_rhythm=1,
        harmony="Modal and drone-based: fiddle double stops and nyckelharpa or Hardanger understrings ring "
                "the tonic and 5th throughout, so accompaniment uses open 5ths, i-bVII, minor v and dorian "
                "IV rather than strong V-I cadences.",
        voicing="open",
        comping="waltz",
        bass_style="root_fifth",
        bass="Traditionally none; ensembles use cello, bass or the low strings of a guitar or harmonium on root "
             "and 5th, often as a drone.",
        melody_density="busy",
        melody_scale="dorian",
        melody="Fiddle and nyckelharpa tunes in 8-bar repeated parts, with double stops, drones, trills, "
               "and characteristic 'neutral' or sliding 3rds and 7ths (between minor and major); 16th-note "
               "runs in polskas; kulning and joik-inspired vocal calls.",
        groove={"step": 0.25, "swing": 54, "pattern": {
            "bass drum":  "X.......x...X.......x...",
            "tambourine": "..x...x...x...x...x...x.",
            "low tom":    "x...o.......x...o.......",
        }},
        drums="Mostly no drums: foot stamping (bass drum here) on the polska's strong beats; folk-rock bands "
              "(Hedningarna, Garmarna) add frame drums, tambourine and heavier toms.",
        form=(("intro", 4), ("A", 8), ("A", 8), ("B", 8), ("B", 8), ("A", 8), ("A", 8), ("B", 8), ("B", 8),
              ("ending", 2)),
        instruments=("fiddle", "Hardanger fiddle", "nyckelharpa", "kantele", "harmonium", "cittern", "guitar",
                     "bass", "voice"),
        sound_design="Resonant, drone-rich bowed strings: nyckelharpa and Hardanger fiddle with sympathetic "
                     "strings shimmering, kantele plucks, airy kulning; recordings are natural with "
                     "spacious reverb.",
        production="Acoustic, dynamic and roomy; folk-rock productions add distortion, synth drones and "
                   "big drums.",
        theory="Modal melody with neutral thirds (old Swedish and Norwegian intonation sits between the 12-tone "
               "minor and major 3rds); polska's uneven 3/4 (e.g. a short 1st or long 2nd beat by region) is "
               "felt rather than notated.",
        mix=Mix(lufs=(-19, -13), lra=(8, 14), low_end="light", tone="warm", width="wide"),
    ),
]
