"""Jazz, blues, funk and gospel, country and folk: how the American roots styles are written, played and mixed."""

from . import Genre, Mix

GENRES = [
    # ------------------------------------------------------------------ jazz
    Genre(
        name="jazz",
        family="jazz",
        aliases=("jazz trio", "straight-ahead jazz", "jazz standards", "mainstream jazz"),
        description="Straight-ahead acoustic jazz: a swinging rhythm section (piano, upright bass, ride cymbal) "
                    "playing standards and originals, the melody stated, improvised on, and stated again.",
        era="New Orleans origins c. 1910s; the straight-ahead small-group language codified in New York, 1940s-60s",
        touchstones=("Miles Davis", "Bill Evans Trio", "Oscar Peterson Trio", "Sonny Rollins", "Ahmad Jamal",
                     "Wynton Kelly", "Ella Fitzgerald", "Keith Jarrett Standards Trio"),
        tempo=(60, 220),
        feel="swung eighths over a walking four; ride cymbal spang-a-lang with hi-hat on 2 and 4",
        swing=62,
        modes=("major", "dorian", "minor"),
        keys=("Bb major", "F major", "Eb major", "C major", "Ab major", "G minor"),
        progressions=(
            "ii9-V13-Imaj9-Imaj9",
            "minor: iiø7-V7b9-i6/9-i6/9",
            "Imaj7-VI7b9-ii7-V7",
            "iii7-VI7-ii7-bII7",
            "Imaj7-iv7-bVII7-Imaj7",
            "ii7-V7-Imaj7-IVmaj7-viiø7-III7-vi7-vi7",
            "I7-IV7-I7-I7-IV7-#iv°7-I7-VI7b9-ii7-V7-I7-V7",
        ),
        harmonic_rhythm=1,
        harmony="Functional tonal harmony built from ii-V-I cells that tonicize one key after another (cycle-of-fifths "
                "root motion). Every chord carries at least a 7th; 9ths and 13ths on tonics and dominants, b9/#9/#5 "
                "alterations on dominants that resolve to minor. Turnarounds (I-VI7-ii-V, iii-VI7-ii-V) fill the "
                "last two bars of a section; tritone subs (bII7 for V7) and backdoor cadences (iv7-bVII7-I) recolour "
                "them. Minor ii-V's are iiø7-V7b9 resolving to a minor 6/9 or m(maj7) tonic.",
        voicing="rootless",
        comping="charleston",
        bass_style="walking",
        bass="Upright bass walking quarter notes: a chord tone (usually the root) on beat 1, scale or chromatic "
             "passing tones on 2-3, and a half-step or 5th approach into the next root on beat 4. Two-feel (half "
             "notes) on the head of a ballad-ish tune or first A sections, then walk; pedal points under intros and "
             "tags; occasional skip-beat triplet drops.",
        melody_density="medium",
        melody_scale="bebop dominant",
        melody="Head: the tune stated with a singer's phrasing, behind the beat. Solos: swung eighth-note lines "
               "built on guide tones (3rds and 7ths resolving by half step across each ii-V), chord tones on "
               "downbeats, chromatic approach notes and enclosures (above-below-target), arpeggios from the 3rd or "
               "7th up to the 9th; dorian on ii, mixolydian or altered on V, ionian/lydian on I. Motivic development "
               "and call-and-response with the comping; quotes and blues inflections (b3, b5) are part of the "
               "language. Phrases of 2-4 bars that often start on an upbeat and cross bar lines.",
        groove={"step": 0.5, "swing": 62, "pattern": {
            "ride":      "x.xxx.xxx.xxx.xx",
            "pedal hat": "..x...x...x...x.",
            "kick":      "o.o.o.o.o.o.o.o.",
            "snare":     "...o......o..x..",
        }},
        drums="Ride cymbal carries the time: ding, ding-a, ding, ding-a (quarter, then a swung skip note on the "
              "last triplet of beats 2 and 4). Hi-hat foot crisp on 2 and 4. Bass drum feathered softly on all "
              "four quarters with occasional 'bombs'; snare comps with ghosted triplets and conversational accents "
              "that answer the soloist. Brushes on ballads and quieter heads; trading fours or eights with the "
              "soloist near the end.",
        form=(("intro", 8), ("head A", 8), ("head A", 8), ("head B", 8), ("head A", 8), ("solos", 64),
              ("trading fours", 32), ("head out", 32), ("tag ending", 4)),
        instruments=("acoustic piano", "upright bass", "drum kit (ride, brushes)", "tenor saxophone", "trumpet",
                     "hollow-body jazz guitar"),
        sound_design="All acoustic. Upright bass with a woody attack and natural sustain (pickup blended with a mic), "
                     "warm felt piano, dark ride cymbal with a long wash (K-style), round archtop guitar on the neck "
                     "pickup with the tone rolled off, horns with natural breath.",
        production="Recorded live in one room with minimal overdubs (Rudy Van Gelder / Blue Note tradition); room "
                   "mics and spill are part of the sound. Very little compression, no limiting to speak of, wide "
                   "stereo spread (drums and piano across the field, bass centred), honest dynamics.",
        theory="Built on the ii-V-I as the unit of harmonic motion and on chord-scale theory: each chord implies a "
               "mode (ii7 dorian, V7 mixolydian or altered, Imaj7 ionian/lydian). The swing ratio slides with "
               "tempo (near triplet at medium, flatter above 240), and the soloist's guide-tone line (3-7-3) keeps "
               "the changes audible even without the piano. The jazz blues adds a #iv°7 in bar 6 and a VI7-ii-V "
               "turnaround to the 12-bar form.",
        mix=Mix(lufs=(-18, -12), lra=(8, 15), low_end="light", tone="warm", width="wide"),
    ),
    Genre(
        name="swing",
        family="jazz",
        aliases=("big band", "swing era", "big band swing", "big band jazz"),
        parent="dixieland",
        description="The dance music of the 1930s-40s: big bands riffing in call-and-response sections over a "
                    "pulsing four-to-the-bar rhythm section, built to make a ballroom jump.",
        era="Kansas City, New York and Chicago, 1930s-mid 1940s",
        touchstones=("Count Basie Orchestra", "Duke Ellington Orchestra", "Benny Goodman", "Chick Webb",
                     "Jimmie Lunceford", "Fletcher Henderson", "Glenn Miller", "Artie Shaw"),
        tempo=(120, 240),
        feel="four-to-the-bar swing: walking bass, guitar chopping every quarter, hi-hat ching-chicka, heavy triplet lilt",
        swing=64,
        modes=("major", "minor"),
        keys=("Bb major", "Eb major", "F major", "Ab major", "C major"),
        progressions=(
            "I6/9-vi7-ii7-V7-I6/9-vi7-ii7-V7",
            "I6/9-I7-IV6/9-#iv°7-I64-V7-I6/9-I6/9",
            "III7-III7-III7-III7-VI7-VI7-VI7-VI7-II7-II7-II7-II7-V7-V7-V7-V7",
            "I6/9-#i°7-ii7-#ii°7-iii7-VI7b9-ii7-V7",
            "I7-I7-IV7-#iv°7-I7-I7-VI7-VI7-ii7-ii7-V7-V7",
        ),
        harmonic_rhythm=2,
        harmony="Sweet, triadic-plus-6th harmony: I6 and I6/9 tonics (not maj7), dominant 7ths and 9ths, passing "
                "diminished 7ths (#i°7, #ii°7, #iv°7) connecting diatonic chords chromatically, and circle-of-"
                "dominants bridges (III7-VI7-II7-V7, the rhythm-changes bridge). Riff tunes sit on the 12-bar blues "
                "or I Got Rhythm changes; ballads on 32-bar AABA songs.",
        voicing="drop2",
        comping="quarters",
        bass_style="walking",
        bass="Walking quarters, mostly roots and 5ths on strong beats with chromatic approaches; the bass, guitar "
             "and bass drum land together on every beat (the Basie 'All-American Rhythm Section'); two-beat "
             "(roots on 1 and 3) in some first choruses.",
        melody_density="medium",
        melody_scale="major blues",
        melody="Riffs: short, bluesy, syncopated 1-2 bar figures repeated by one section while another answers "
               "(saxes vs. brass call-and-response). Melodies sit in the major-6 / major-blues sound with b3-to-3 "
               "slides; soloists (Lester Young, Coleman Hawkins, Roy Eldridge) phrase in lyrical arpeggios. The "
               "shout chorus stacks the whole band on a high, syncopated riff; brass shakes, falls and doits.",
        groove={"step": 0.5, "swing": 64, "pattern": {
            "closed hat": "x.xxx.xxx.xxx.xx",
            "kick":       "x.x.x.x.x.x.x.x.",
            "snare":      "......o.......X.",
        }},
        drums="Hi-hat half-open, ching-chicka on 2 and 4 (Jo Jones), or ride; bass drum softly on all four beats "
              "(Gene Krupa played it audibly). Snare and bass drum set up and kick the ensemble's accents "
              "(rimshots on the 'and' of 4); tom-tom showcases (Sing Sing Sing) and crash on shout-chorus hits.",
        form=(("intro", 8), ("head A", 8), ("head A", 8), ("head B", 8), ("head A", 8), ("sax soli", 32),
              ("solos", 64), ("shout chorus", 32), ("head out", 16), ("ending", 4)),
        instruments=("saxophone section (2 alto, 2 tenor, baritone)", "trumpet section", "trombone section",
                     "piano", "acoustic rhythm guitar", "upright bass", "drum kit", "clarinet"),
        sound_design="Bright, punchy brass with plunger and cup mutes, warm reed section with vibrato, unamplified "
                     "archtop guitar chunking quarters, upright bass, small-room or ballroom ambience; vintage "
                     "ribbon-mic colour.",
        production="Sections recorded as sections, panned by seating (saxes front, trombones and trumpets behind); "
                   "room sound essential; dynamic arc from soft sax soli to full-band shout; gentle compression at "
                   "most. Mono feel in classic records, wide in modern big-band productions.",
        theory="Arranging is the craft: 4- and 5-part sax soli in close or drop-2 voicings harmonized from the lead "
               "line, chromatic passing diminished chords to voice-lead between harmonized melody notes, and "
               "riff-based call-and-response between sections. The rhythm-changes bridge is a cycle of secondary "
               "dominants (V7/V/V/V...).",
        mix=Mix(lufs=(-16, -11), lra=(7, 13), low_end="light", tone="warm", width="wide"),
    ),
    Genre(
        name="bebop",
        family="jazz",
        aliases=("bop",),
        parent="swing",
        description="Fast, virtuosic small-group jazz for listening: dense chromatic eighth-note lines over "
                    "rapidly moving, reharmonized standard changes, with drums driving from the ride cymbal.",
        era="New York (Minton's Playhouse, 52nd Street), early-mid 1940s",
        touchstones=("Charlie Parker", "Dizzy Gillespie", "Bud Powell", "Thelonious Monk", "Max Roach",
                     "Kenny Clarke", "Fats Navarro", "Sonny Stitt"),
        tempo=(140, 300),
        feel="swung eighths flattening toward straight at fast tempos; ride cymbal time, drummer 'dropping bombs'",
        swing=58,
        modes=("major", "minor"),
        keys=("Bb major", "F major", "Eb major", "Ab major", "C major", "Db major"),
        progressions=(
            "Imaj7-vi7-ii7-V7-iii7-VI7-ii7-V7",
            "III7-III7-III7-III7-VI7-VI7-VI7-VI7-II7-II7-II7-II7-V7-V7-V7-V7",
            "Imaj7-Imaj7-viiø7-III7-vi7-II7-v7-I7-IV7-IV7-iv7-bVII7-iii7-VI7-biii7-bVI7-ii7-ii7-V7-V7-Imaj7-VI7-ii7-V7",
            "Imaj7-bIIImaj7-bVImaj7-bIImaj7",
            "iii7-bIII7-ii7-bII7",
            "minor: iiø7-V7b9-i6/9-i6/9",
        ),
        harmonic_rhythm=2,
        harmony="Two chords per bar is normal. Every dominant gets its ii (ii-V everything), chains of ii-V's "
                "descending chromatically (iii7-bIII7-ii7-bII7), tritone substitutions, the Dameron turnaround "
                "(Imaj7-bIIImaj7-bVImaj7-bIImaj7) and upper extensions/alterations (b9, #9, #11, b13). Tunes are "
                "contrafacts: new melodies over the changes of standards (rhythm changes, the blues, Cherokee, "
                "How High the Moon). The 'Bird blues' reharmonizes the 12-bar into descending ii-V's.",
        voicing="shell",
        comping="charleston",
        bass_style="walking",
        bass="Fast walking quarters, strongly outlining roots on beat 1 and chromatic approach tones on 4 to make "
             "the dense changes audible; at very fast tempos lines get simpler (roots, 5ths, chromatic steps).",
        melody_density="busy",
        melody_scale="bebop dominant",
        melody="Long swung eighth-note lines with chromatic passing tones placed so chord tones fall on the beat "
               "(the bebop scales' added passing tone), enclosures, approach notes from a half step below, "
               "arpeggios of upper structures (3-5-7-9), the b9 on dominants resolving to the 5th of the next chord, "
               "triplet turns, sudden double-time bursts. Heads are angular unison lines (alto and trumpet) that "
               "start and end on offbeats, often ending with the 'bebop' two-note cadence. Phrases end on the "
               "'and' of a beat.",
        groove={"step": 0.5, "swing": 58, "pattern": {
            "ride":      "x.xxx.xxx.xxx.xx",
            "pedal hat": "..x...x...x...x.",
            "snare":     "...o.x.....o..o.",
            "kick":      "...........X....",
        }},
        drums="Time moves from the bass drum to the ride cymbal (Kenny Clarke); hi-hat on 2 and 4; snare and bass "
              "drum free for irregular accents and 'bombs' that prod the soloist; fours and eights traded with "
              "horns; drum solos melodic and in form.",
        form=(("intro", 8), ("head", 32), ("head", 32), ("solos", 128), ("trading fours", 32), ("head out", 32),
              ("tag", 8)),
        instruments=("alto saxophone", "trumpet", "piano", "upright bass", "drum kit", "tenor saxophone"),
        sound_design="Small acoustic quintet: bright alto, open trumpet, percussive piano comping, woody upright, "
                     "thin-crash ride cymbals; vintage mono or narrow-stereo character with tape warmth.",
        production="Live in the studio; solos are first takes. Horns prominent, piano comping behind, ride cymbal "
                   "audible over everything; little or no compression; short tracks (3 minutes) on 78s, longer on LP.",
        theory="The harmonic tension is horizontal: lines imply passing ii-V's, tritone subs and altered tensions "
               "faster than the rhythm section states them. The bebop dominant scale (mixolydian + natural 7) "
               "keeps chord tones on the beat in descending lines; enclosures surround a target chord tone by "
               "step from above and below.",
        mix=Mix(lufs=(-18, -12), lra=(7, 14), low_end="light", tone="warm", width="moderate"),
    ),
    Genre(
        name="cool jazz",
        family="jazz",
        aliases=("west coast jazz",),
        parent="bebop",
        description="Bebop's relaxed, lyrical answer: lighter tone, restrained dynamics, counterpoint and arranged "
                    "textures, and soft swing at moderate tempos.",
        era="New York (Birth of the Cool) then Los Angeles and San Francisco, 1949-late 1950s",
        touchstones=("Miles Davis Birth of the Cool", "Chet Baker", "Gerry Mulligan Quartet", "Dave Brubeck Quartet",
                     "Paul Desmond", "Lennie Tristano", "Lee Konitz", "Stan Getz", "Modern Jazz Quartet"),
        tempo=(90, 200),
        feel="light, even swing; brushes; 'laid back' phrasing slightly behind the beat",
        swing=60,
        modes=("major", "minor"),
        keys=("F major", "Bb major", "C major", "Eb minor", "D minor"),
        progressions=(
            "ii9-V13-Imaj9-IVmaj7",
            "Imaj7-vi7-ii7-V7",
            "minor: i7-v7-i7-v7",
            "iii7-VI7-ii7-V7",
            "ii7-bII7-Imaj7-Imaj7",
            "ii7-V7-iv7-bVII7-Imaj7",
        ),
        harmonic_rhythm=1,
        harmony="Standard-song harmony (ii-V-I, turnarounds, tritone subs) voiced softly: maj7, maj9 and 6/9 tonics, "
                "unaltered 9th and 13th dominants rather than harsh alterations, backdoor cadences. Pianoless "
                "groups (Mulligan-Baker) imply the changes through two-line counterpoint; Brubeck adds odd meters "
                "(5/4, 9/8) and block-chord polytonality.",
        voicing="drop2",
        comping="half_notes",
        bass_style="walking",
        bass="Melodic walking with a soft, round tone, frequently in two (half notes) on heads; in pianoless "
             "groups the bass carries the harmony alone, so roots on downbeats and clear guide tones.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Lyrical, mid-register, vibrato-light lines with space; fewer notes than bebop, more long tones and "
               "rests; linear counterpoint between two horns (baritone under trumpet), canons and fugue-like "
               "entries; Tristano-school long asymmetric lines. Pentatonic and diatonic shapes more than chromatic "
               "runs; phrasing laid back.",
        groove={"step": 0.5, "swing": 60, "pattern": {
            "snare":     "x.xxx.xxx.xxx.xx",
            "pedal hat": "..x...x...x...x.",
            "kick":      "o.......o.......",
        }},
        drums="Brushes on snare stirring a continuous swish with taps on the ride pattern, hi-hat on 2 and 4, "
              "bass drum barely there. When on sticks, light ride and little bomb-dropping; Joe Morello-style "
              "odd-meter grooves with Brubeck.",
        form=(("intro", 4), ("head", 32), ("solos", 64), ("counterpoint chorus", 32), ("head out", 32), ("ending", 4)),
        instruments=("trumpet (often muted)", "baritone saxophone", "alto saxophone", "upright bass",
                     "drum kit with brushes", "piano", "French horn", "tuba"),
        sound_design="Soft, breathy alto and tenor, Harmon- or cup-muted trumpet, mellow baritone, warm upright, "
                     "brushed snare; nonet colours with French horn and tuba (Gil Evans/Gerry Mulligan scoring).",
        production="Intimate and clean, wide stereo on 1950s Contemporary/Pacific Jazz records, lots of space "
                   "around instruments, almost no compression; quiet overall level with long fades of ambience.",
        theory="Contrapuntal texture replaces chordal comping; dynamics stay mezzo-piano, and tone colour (French "
               "horn, tuba, muted brass) does the arranging work. Brubeck's experiments put swing in 5/4 (3+2) and "
               "9/8 (2+2+2+3).",
        mix=Mix(lufs=(-19, -13), lra=(8, 15), low_end="light", tone="warm", width="wide"),
    ),
    Genre(
        name="hard bop",
        family="jazz",
        aliases=("soul jazz", "blue note jazz"),
        parent="bebop",
        description="Bebop with the blues and church put back in: driving, earthy small-group jazz with gospel "
                    "cadences, minor-key grooves, funky shuffles and fiery solos.",
        era="New York and Detroit/Philadelphia players on Blue Note and Prestige, 1954-mid 1960s",
        touchstones=("Art Blakey and the Jazz Messengers", "Horace Silver", "Clifford Brown and Max Roach",
                     "Lee Morgan", "Cannonball Adderley", "Sonny Rollins", "Hank Mobley", "Jimmy Smith",
                     "John Coltrane Blue Train"),
        tempo=(100, 280),
        feel="hard-swinging eighths over walking bass; Blakey shuffles, press rolls and a heavy hi-hat on 2 and 4",
        swing=62,
        modes=("major", "minor", "dorian"),
        keys=("F major", "Bb major", "F minor", "C minor", "Eb major"),
        progressions=(
            "I7-I7-IV7-IV7-I7-I7-v7-I7-IV7-IV7-#iv°7-#iv°7-I7-I7-VI7b9-VI7b9-ii7-ii7-V7-V7-I7-VI7b9-ii7-V7",
            "minor: i7-i7-iv7-iv7-i7-i7-i7-i7-iv7-iv7-iv7-iv7-i7-i7-i7-i7-VI7-VI7-V7alt-V7alt-i7-i7-iiø7-V7alt",
            "dorian: i7-i7-IV7-IV7",
            "ii7-bIII7-bVImaj7-VII7-IIImaj7-V7-Imaj7-Imaj7",
            "minor: iiø7-V7b9-i6/9-i6/9",
            "Imaj7-VI7#9-ii7-V7b9",
        ),
        harmonic_rhythm=2,
        harmony="Bebop's ii-V vocabulary plus the blues and gospel: jazz blues with a ii-V into IV (v7-I7 in bar "
                "4) and #iv°7 in bar 6, minor blues with VI7-V7alt, dorian vamps with a soulful IV7 (Moanin', "
                "The Sidewinder), pedal-point intros and 'Amen' plagal endings. Coltrane substitutions "
                "(ii7-bIII7-bVImaj7-VII7-IIImaj7-V7-Imaj7: key centres a major third apart) on Coltrane's own "
                "tunes. Horace Silver writes Latin-tinged sections that break into swing.",
        voicing="rootless",
        comping="charleston",
        bass_style="walking",
        bass="Strong, deep walking with a fat attack (Paul Chambers, Doug Watkins, Sam Jones); funky two-beat or "
             "ostinato riffs on soul-jazz tunes and Latin sections, then a walk into the solos; pedal tones under "
             "intros.",
        melody_density="busy",
        melody_scale="blues",
        melody="Heads are memorable riffs and call-and-response figures in unison or 4ths between trumpet and tenor, "
               "often bluesy and gospel-tinged. Solos mix bebop chromaticism with blues licks (b3-3 bends, b5 "
               "grace notes, repeated-note 'preaching'), long-tone shouts and 'sheets of sound' runs; guide-tone "
               "resolutions at every ii-V; minor tunes lean on dorian and melodic minor.",
        groove={"step": 0.5, "swing": 62, "pattern": {
            "ride":      "x.xxx.xxx.xxx.xx",
            "pedal hat": "..X...X...X...X.",
            "snare":     "....o..x...o.ox.",
            "kick":      "o.o.o.o.o.o.o..X",
        }},
        drums="Assertive ride and an audible, emphatic hi-hat on 2 and 4; Blakey's press roll building into each "
              "new chorus, shuffles and backbeats on soul-jazz tunes, Afro-Cuban breaks on intros. Snare and kick "
              "comping is loud and conversational; drummers 'kick' the soloist forward.",
        form=(("intro", 8), ("head", 32), ("solos", 96), ("piano solo", 32), ("drum solo / fours", 32),
              ("head out", 32), ("vamp out", 8)),
        instruments=("tenor saxophone", "trumpet", "piano", "upright bass", "drum kit", "Hammond organ"),
        sound_design="Fat tenor tone, brassy open trumpet, percussive piano with gospel block chords, Hammond B3 with "
                     "percussion and Leslie on soul-jazz dates, big ride cymbal; Van Gelder studio sound (close, "
                     "present horns with a short room).",
        production="Live-to-two-track sessions; horns close-miked and bright, piano slightly roomy, bass "
                   "woody; strong solos kept whole. Very light compression; natural, wide mix.",
        theory="Fuses functional bebop harmony with blues and gospel: plagal IV-I cadences, minor-blues forms, and "
               "dorian vamps sit next to ii-V chains. Coltrane changes divide the octave into three equal parts "
               "(major-third key centres), each approached by its own V7.",
        mix=Mix(lufs=(-17, -12), lra=(7, 14), low_end="light", tone="warm", width="wide"),
    ),
    Genre(
        name="modal jazz",
        family="jazz",
        aliases=("modal",),
        parent="hard bop",
        description="Jazz built on long stretches of a single mode instead of fast chord changes: open, "
                    "meditative or intensely building, with quartal harmony and improvisation that develops "
                    "melody rather than running changes.",
        era="New York, 1958-1960s (Milestones, Kind of Blue, the classic Coltrane quartet)",
        touchstones=("Miles Davis Kind of Blue", "John Coltrane A Love Supreme", "McCoy Tyner", "Bill Evans",
                     "Herbie Hancock Maiden Voyage", "Elvin Jones", "Wayne Shorter", "Pharoah Sanders"),
        tempo=(100, 280),
        feel="swung but open; triplet-based polyrhythmic drumming over a walking or pedalled bass",
        swing=64,
        modes=("dorian", "mixolydian", "phrygian", "lydian"),
        keys=("D dorian", "Eb dorian", "F dorian", "C dorian"),
        progressions=(
            "i7-i7-i7-i7-bii7-bii7-i7-i7",
            "i7-IV7-i7-IV7",
            "I7sus4-III7sus4-I7sus4-III7sus4",
            "phrygian: i7-IImaj7-i7-IImaj7",
            "lydian: Imaj7#11-Imaj7#11-II7-II7",
        ),
        harmonic_rhythm=0.25,
        harmony="One mode for 8-16 bars, then a shift (So What: D dorian 16 bars, Eb dorian 8, D dorian 8). Chords "
                "are voiced in 4ths (the 'So What' voicing: three stacked 4ths plus a major 3rd), sus4 and 7sus4 "
                "chords, pedal points and planed quartal shapes moved through the mode. No functional cadences; "
                "colour comes from the mode's characteristic note (dorian 6th, lydian #4, phrygian b2).",
        voicing="quartal",
        comping="stabs",
        bass_style="walking",
        bass="Walks inside the mode, or holds a pedal ostinato (A Love Supreme's four-note figure, Impressions' "
             "drone-like walk). Pedal roots under the vamp for long stretches; the bass and piano left hand often "
             "sound open 5ths.",
        melody_density="medium",
        melody_scale="dorian",
        melody="Melodic development over many choruses: motifs restated, sequenced through the mode, transposed "
               "a half step 'outside' and back (side-slipping), pentatonic patterns from several roots over one "
               "chord (Coltrane, Tyner), quartal arpeggios, intervallic leaps. Heads are simple and riff-like "
               "(bass call, horn 'Amen' answer). Climaxes build by density, register and intensity rather than "
               "harmonic motion.",
        groove={"step": 1 / 3, "swing": 50, "pattern": {
            "ride":      "x..x.xx..x.xx..x.xx..x.x",
            "pedal hat": "...x.....x.....x.....x..",
            "snare":     "..o.o..o..o...o..o.o.o.o",
            "kick":      "o.....o..x.....o..o.....",
        }},
        drums="Elvin Jones style: rolling triplet polyrhythms spread across ride, snare and toms, implying 3 over "
              "4 and 6/8 inside 4/4, the ride and hi-hat keeping a loose anchor; waves of intensity that crest "
              "with the soloist. Jimmy Cobb-style restraint on the cooler modal records.",
        form=(("intro (bass and piano)", 8), ("head A", 16), ("head B (up a half step)", 8), ("head A", 8),
              ("solos", 128), ("piano solo", 64), ("head out", 32), ("vamp out", 16)),
        instruments=("tenor or soprano saxophone", "trumpet", "piano", "upright bass", "drum kit"),
        sound_design="Acoustic quartet/quintet: dark, singing tenor, soprano sax with an Eastern reed sound, "
                     "piano with open 5ths in the left hand and quartal clusters in the right, deep upright, "
                     "large washy ride cymbals.",
        production="Recorded live, long takes (10-20 minutes), wide natural stereo; the drummer's dynamics are "
                   "allowed to swell without compression. Quiet beginnings, enormous crescendos.",
        theory="Replaces vertical, chord-by-chord harmony with horizontal mode-centred improvisation; quartal "
               "voicings avoid the tertian tonic-dominant pull, so a single chord can last 16 bars without "
               "sounding static. Side-slipping (playing a half step away and resolving back) and pentatonic "
               "superimposition provide controlled tension.",
        mix=Mix(lufs=(-18, -12), lra=(8, 16), low_end="light", tone="warm", width="wide"),
    ),
    Genre(
        name="post-bop",
        family="jazz",
        aliases=("modern jazz", "contemporary acoustic jazz"),
        parent="hard bop",
        description="Acoustic jazz after hard bop and modal: harmonically adventurous compositions, elastic "
                    "rhythm sections that stretch and break the time, and open, interactive improvisation.",
        era="New York, 1960s (the second Miles Davis quintet, Blue Note's 'new breed') onward",
        touchstones=("Wayne Shorter Speak No Evil", "Miles Davis E.S.P.", "Herbie Hancock", "Tony Williams",
                     "Joe Henderson", "Woody Shaw", "Freddie Hubbard", "Kenny Garrett", "Brad Mehldau"),
        tempo=(80, 280),
        feel="swing that stretches: implied double-time and half-time, broken time on the ride, metric modulation",
        swing=58,
        modes=("major", "dorian", "minor", "lydian"),
        keys=("B major", "Eb major", "C minor", "F minor", "Db major"),
        progressions=(
            "Imaj7-bIII7-bVImaj7-VII7-IIImaj7-IIImaj7-bvii7-bIII7",
            "Imaj7#11-Imaj7#11-bVIImaj7#11-bVIImaj7#11-bVImaj7#11-bVImaj7#11-Vmaj7#11-Vmaj7#11",
            "minor: imaj7-imaj7-iiø7-V7alt",
            "I7sus4-bVI7sus4-bIImaj7#11-V7alt",
            "ii11-bII7#11-Imaj9-bIIImaj7#11",
        ),
        harmonic_rhythm=2,
        harmony="Non-functional or ambiguous motion: constant-structure planing (the same chord type moving by "
                "step or third, e.g. maj7#11 descending), Coltrane's major-third cycles (Giant Steps), sus "
                "chords and slash chords, melodic-minor sonorities (m(maj7), 7alt, maj7#5), modal sections "
                "inside through-composed forms of irregular length (14, 18, 22 bars). Shorter's tunes resolve "
                "by voice-leading rather than ii-V gravity.",
        voicing="rootless",
        comping="stabs",
        bass_style="walking",
        bass="Walking that turns into counterlines, pedals and ostinatos; Ron Carter's elastic time, slides and "
             "upper-register answers; the bass may imply a different harmony than the piano for colour.",
        melody_density="medium",
        melody_scale="melodic minor",
        melody="Composed heads with long tones, wide intervals and unexpected landing notes (the #11, the "
               "natural 7 over minor). Solos use melodic minor modes (altered over V7, lydian dominant over bII7), "
               "intervallic and pentatonic patterns, 'inside-outside' side-slips, motivic cells, and rhythmic "
               "displacement; Shorter-style sparse, riddling phrases as much as Hubbard-style flurries.",
        groove={"step": 0.5, "swing": 58, "pattern": {
            "ride":      "x.xxx.xxx..xx.xx",
            "pedal hat": "x.x.x.x.x.x.x.x.",
            "snare":     "..o..x.o...o.x..",
            "kick":      "......x.......x.",
        }},
        drums="Tony Williams: ride time that keeps breaking up, hi-hat on every beat, snare and bass drum "
              "punctuations that fracture the bar line, sudden dynamic drops to near silence, implied tempos. "
              "The rhythm section reacts in real time ('controlled freedom').",
        form=(("intro", 8), ("head", 32), ("solos (open)", 96), ("collective section", 32), ("head out", 32),
              ("coda", 8)),
        instruments=("tenor saxophone", "trumpet", "acoustic piano", "upright bass", "drum kit", "soprano saxophone"),
        sound_design="Acoustic quintet, darker and more transparent than hard bop: flat-ride and dry crash "
                     "cymbals, rich mid-register piano voicings, upright with gut-like growl; modern recordings "
                     "with clear, detailed close mics and a natural room.",
        production="Live ensemble takes; wide, deep stereo image; dynamics left almost entirely intact; no bus "
                   "limiting; quiet master levels that respect the drummer's range.",
        theory="Harmony as colour rather than function: chord qualities persist while roots move by thirds, half "
               "steps or tritones; melodic minor supplies the dominant colours (altered, lydian dominant). "
               "Coltrane changes (three tonal centres a major 3rd apart, each preceded by its V7) are the "
               "set-piece test; forms are often irregular in length.",
        mix=Mix(lufs=(-18, -12), lra=(8, 16), low_end="light", tone="neutral", width="wide"),
    ),
    Genre(
        name="free jazz",
        family="jazz",
        aliases=("free improvisation", "avant-garde jazz", "the new thing"),
        parent="hard bop",
        description="Jazz freed from fixed changes, form and steady meter: collective improvisation, raw timbres "
                    "and pulse instead of time, ranging from ecstatic shrieks to fragile chamber textures.",
        era="New York and Chicago, 1959-1970s (Ornette Coleman, Cecil Taylor, the AACM)",
        touchstones=("Ornette Coleman The Shape of Jazz to Come", "Cecil Taylor", "Albert Ayler",
                     "John Coltrane Ascension", "Sun Ra Arkestra", "Art Ensemble of Chicago", "Don Cherry",
                     "Pharoah Sanders", "Peter Brötzmann"),
        tempo=(40, 300),
        feel="rubato or free pulse; tempo is a density, not a grid",
        swing=58,
        modes=("dorian", "phrygian", "minor"),
        keys=("C dorian", "Bb minor", "E phrygian"),
        progressions=(
            "i7-i7-i7-i7",
            "i7-bIImaj7#11-i7-V7alt",
            "phrygian: i-II-i-II",
        ),
        harmonic_rhythm=0.25,
        harmony="Often no predetermined changes at all. Ornette's 'harmolodics' let melody set the harmony moment "
                "by moment; others use a drone or single-mode springboard, tone clusters (Cecil Taylor), or "
                "collective polyphony where harmony is whatever the lines create. Write a head, then let the "
                "harmony dissolve.",
        voicing="cluster",
        comping="none",
        bass_style="pedal",
        bass="Arco drones, double stops, rapid bowed tremolos, pizzicato flurries or a steady but tempo-free "
             "walking pulse (Charlie Haden with Ornette: walking that follows the soloist's implied keys).",
        melody_density="busy",
        melody_scale="chromatic",
        melody="Folk-like or bluesy short heads stated in loose unison, then free development: motivic cells "
               "transformed, extreme registers, overblowing, multiphonics, screams and honks (Ayler), "
               "microtonal inflection, simultaneous collective improvisation. Phrases are shaped by breath and "
               "energy rather than bar lines.",
        groove={"step": 1 / 3, "swing": 50, "pattern": {
            "ride":      "x..x..xxx...x.x..xx..x..",
            "snare":     "..o.oo...o.ooo.....o.oo.",
            "high tom":  ".x.....x.....x......x...",
            "floor tom": "......x.......x..x.....x",
            "kick":      "x........x....x.....x...",
            "crash":     "x...................x...",
        }},
        drums="Pulse not time (Sunny Murray, Milford Graves, Rashied Ali): continuous cymbal washes, rolling toms, "
              "irregular bass-drum accents, textures that surge and recede with the group; no backbeat, no "
              "repeating pattern for long.",
        form=(("head", 16), ("collective improvisation", 64), ("solo episodes", 64), ("collective climax", 32),
              ("head out", 16)),
        instruments=("alto or tenor saxophone", "trumpet or pocket cornet", "upright bass (arco and pizz)",
                     "drum kit", "piano", "little instruments (bells, gongs, whistles)"),
        sound_design="Raw acoustic timbres pushed to extremes: split tones, multiphonics, bowed cymbals, prepared "
                     "piano, percussion 'little instruments'. Nothing polished; texture is content.",
        production="Recorded live with room ambience; extremely wide dynamic range kept intact; no compression or "
                   "limiting; double-quartet stereo layouts (Free Jazz) with one group per side.",
        theory="Abandons the chord-scale grid: pitch organization is motivic and intervallic, form is emergent, "
               "and rhythm is pulse and density. Tension and release come from texture, register and dynamics.",
        mix=Mix(lufs=(-20, -13), lra=(10, 20), low_end="light", tone="neutral", width="wide"),
    ),
    Genre(
        name="jazz fusion",
        family="jazz",
        aliases=("fusion", "jazz-rock", "jazz-funk", "electric jazz"),
        parent="modal jazz",
        description="Jazz improvisation and harmony welded to rock and funk rhythm and electric instruments: "
                    "straight-16th grooves, synths and electric piano, virtuoso unison lines and long modal vamps.",
        era="New York and Los Angeles, 1969-early 1980s (Bitches Brew onward)",
        touchstones=("Miles Davis Bitches Brew", "Mahavishnu Orchestra", "Weather Report Heavy Weather",
                     "Return to Forever", "Herbie Hancock Head Hunters", "Tony Williams Lifetime", "Jaco Pastorius",
                     "Allan Holdsworth", "Chick Corea Elektric Band"),
        tempo=(80, 200),
        feel="straight 16ths, funk or rock backbeat, odd meters (7/8, 11/8) in sections, long vamps",
        swing=52,
        modes=("dorian", "mixolydian", "lydian", "minor"),
        keys=("D dorian", "Bb dorian", "E dorian", "F dorian", "C lydian"),
        progressions=(
            "i7-i7-IV7-IV7",
            "i11-VIImaj7-bVImaj7#11-i11",
            "lydian: Imaj7#11-II9-Imaj7#11-II9",
            "major: ii9-V7alt-Imaj9-bVImaj7#11",
            "i7-i7-i7-V7#9",
        ),
        harmonic_rhythm=0.5,
        harmony="Modal vamps of 2-8 bars (dorian i7-IV7, mixolydian I7sus4) alternating with composed sections "
                "full of slash chords, upper-structure triads over bass notes, quartal stacks, maj7#11 and 7#9 "
                "sonorities, and non-functional root motion by 3rds and half steps. ii-V's appear but as colour.",
        voicing="quartal",
        comping="stabs",
        bass_style="syncopated",
        bass="Electric bass as a lead voice: syncopated 16th funk lines with ghost notes and octave pops "
             "(Paul Jackson on Chameleon), fretless melodic lines with harmonics (Jaco), unison runs with the "
             "keys and guitar; sustained pedal roots under solos.",
        melody_density="busy",
        melody_scale="dorian",
        melody="Long, fast unison heads (guitar + synth + violin), odd-grouping runs, pentatonic and dorian "
               "solos with rock-guitar bends and legato, outside side-slips, synth leads with pitch-bend and "
               "portamento; McLaughlin-style raga-inflected scales; Holdsworth's wide-interval legato.",
        groove={"step": 0.25, "swing": 52, "pattern": {
            "kick":       "x.....x...x..x..",
            "snare":      "....X..o.o..X..o",
            "closed hat": "xoxoxoxoxoxoxo..",
            "open hat":   "..............x.",
        }},
        drums="Rock-weight backbeat with jazz independence: busy 16th hi-hats, ghost notes, linear fills, double "
              "bass drum (Billy Cobham), odd-meter grooves and polyrhythmic solos; congas and percussion layered "
              "in funk-oriented bands.",
        form=(("intro vamp", 8), ("head A", 16), ("head B", 16), ("solo vamp", 64), ("unison interlude", 8),
              ("solo vamp", 64), ("head out", 16), ("fade", 8)),
        instruments=("Fender Rhodes", "synthesizers (Minimoog, ARP, Oberheim)", "electric guitar", "electric bass",
                     "drum kit", "soprano or tenor saxophone", "percussion", "electric violin"),
        sound_design="Rhodes through phaser, wah and tremolo; Minimoog and ARP Odyssey leads with portamento; "
                     "overdriven guitar with sustain; fretless bass with chorus; clavinet through envelope filter "
                     "on funk-leaning tracks.",
        production="Studio-built (Teo Macero's tape editing on Bitches Brew), multitracked with overdubs; punchy "
                   "drums and bass, stereo keys, leads up front; moderate compression, more dynamic than rock.",
        theory="Modal harmony over a rock/funk rhythmic grid: a single dorian or mixolydian chord sustains a solo "
               "for minutes while slash chords and polychords colour the composed sections. Odd meters are built "
               "from groupings of 2s and 3s (7/8 = 2+2+3).",
        mix=Mix(lufs=(-14, -10), lra=(6, 11), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="smooth jazz",
        family="jazz",
        aliases=("contemporary jazz", "smooth"),
        parent="jazz fusion",
        description="Polished, radio-friendly instrumental jazz-pop: a lyrical sax or guitar melody over a soft R&B "
                    "groove and lush extended chords, built for mood rather than tension.",
        era="US radio, late 1970s-2000s",
        touchstones=("Grover Washington Jr. Winelight", "George Benson Breezin'", "David Sanborn", "Bob James",
                     "Kenny G", "Spyro Gyra", "Fourplay", "Dave Koz", "Boney James"),
        tempo=(70, 110),
        feel="laid-back R&B 16ths with a gentle swing; backbeat on 2 and 4",
        swing=54,
        modes=("major", "dorian"),
        keys=("F major", "Eb major", "Ab major", "Bb major", "C dorian"),
        progressions=(
            "IVmaj7-IVmaj7-III7-III7-vi7-vi7-v7-I7",
            "ii9-ii9-V13-V13-Imaj9-Imaj9-vi9-vi9",
            "IVmaj9-IVmaj9-V9sus4-V9sus4-iii7-iii7-vi9-vi9",
            "Imaj9-Imaj9-IVmaj9-IVmaj9",
            "dorian: i9-i9-IV9-IV9",
        ),
        harmonic_rhythm=2,
        harmony="Lush but consonant: maj9, m9, 9sus4 and 13 chords, IVmaj7-iii7-vi7 chains, chromatic III7 "
                "secondary dominants (the IVmaj7-III7-vi7 'Just the Two of Us' pattern), slash chords like IV/V; "
                "rarely altered dominants, almost never dissonant.",
        voicing="spread",
        comping="stabs",
        bass_style="syncopated",
        bass="Smooth fingered or slapped electric bass with syncopated R&B lines, slides into the downbeat, "
             "octave fills at the end of phrases; tight with the kick.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Singable lead in the soprano/alto sax or guitar range with long held notes, pentatonic runs, "
               "grace-note scoops and bends, a few blues inflections; statement-response phrases of 2-4 bars, "
               "climax via a key change or ad-lib over the outro.",
        groove={"step": 0.25, "swing": 54, "pattern": {
            "kick":       "x.....x...x.....",
            "side stick": "....x.......x...",
            "closed hat": "xoxoxoxoxoxoxoxo",
            "shaker":     "oxoxoxoxoxoxoxox",
        }},
        drums="Clean, steady R&B pocket: kick on 1 and the 'and' of 2, cross-stick or soft snare on 2 and 4, "
              "16th hi-hats with dynamics, light percussion (shaker, congas); drum machines common from the late "
              "1980s on.",
        form=(("intro", 8), ("theme A", 16), ("theme B", 8), ("chorus", 8), ("solo", 16), ("theme A", 16),
              ("chorus", 16), ("outro ad-lib", 16)),
        instruments=("soprano or alto saxophone", "electric guitar (clean)", "Rhodes or DX7 electric piano",
                     "electric bass", "drum kit or drum machine", "synth pads", "percussion"),
        sound_design="Glossy and soft: chorused clean guitar (Benson-style octaves), DX7 'E.Piano' or Rhodes, warm "
                     "string pads, reverb-wet soprano sax, fretless or round electric bass.",
        production="Highly polished studio sound, gentle bus compression, lots of plate reverb on leads, wide "
                   "stereo keys; mid-level loudness with a smooth top end.",
        theory="Extended tertian harmony without bite: every chord a 7th-plus but voiced consonantly; secondary "
               "dominants (III7) add colour without leaving the key. Form follows pop song structure rather than "
               "head-solos-head.",
        mix=Mix(lufs=(-13, -9), lra=(4, 8), low_end="moderate", tone="warm", width="wide"),
    ),
    Genre(
        name="acid jazz",
        family="jazz",
        aliases=("nu jazz", "club jazz"),
        parent="jazz fusion",
        description="London's dancefloor jazz: rare-groove funk and soul-jazz grooves with hip-hop breakbeats, "
                    "Hammond and Rhodes, horn riffs and soulful vocals.",
        era="London club scene (Talkin' Loud, Acid Jazz Records), late 1980s-1990s; nu jazz in the late 1990s-2000s",
        touchstones=("Jamiroquai", "Incognito", "The Brand New Heavies", "Galliano", "US3", "Corduroy",
                     "James Taylor Quartet", "St Germain Tourist"),
        tempo=(90, 125),
        feel="swung 16th funk groove or a looped breakbeat; head-nodding, danceable",
        swing=56,
        modes=("dorian", "minor", "mixolydian"),
        keys=("D dorian", "E dorian", "A dorian", "G minor"),
        progressions=(
            "i9-i9-IV9-IV9",
            "i9-VII6/9-bVImaj7-V7#9",
            "i7-iv9-i7-iv9",
            "major: ii9-V13-Imaj9-Imaj9",
            "i11-i11-i11-bVII9",
        ),
        harmonic_rhythm=0.5,
        harmony="Soul-jazz and jazz-funk vamps: dorian i9-IV9, minor 9ths and 11ths, dominant 9ths and 13ths, "
                "occasional ii-V-I in the chorus; Rhodes and organ voicings, chromatic slides into the chord.",
        voicing="rootless",
        comping="stabs",
        bass_style="syncopated",
        bass="Fat, syncopated finger bass (or synth bass) in 16ths with octave jumps and ghosted notes, "
             "disco-funk octaves on uptempo cuts, locked to the kick of the break.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="Hooky vocal or horn riffs in minor pentatonic/dorian, unison horn lines (trumpet + sax + flute), "
               "Hammond solos with glissandi and percussive repeated notes, sax solos mixing blues licks and "
               "bebop runs; rapped verses in the US3-style cuts.",
        groove={"step": 0.25, "swing": 56, "pattern": {
            "kick":       "x......x.x......",
            "snare":      "....X..o..o.X..o",
            "closed hat": "x.xxx.xxx.xxx.x.",
            "conga":      "..o.x..o..o.x..o",
        }},
        drums="Live funk drumming with a swung 16th hat and ghosted snare, or sampled breaks (rare groove LPs) "
              "looped and layered with live percussion: congas, bongos, shakers.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("solo", 16),
              ("breakdown", 8), ("chorus", 16), ("outro", 8)),
        instruments=("Hammond organ", "Rhodes", "electric bass", "drum kit or breakbeat", "horn section",
                     "congas and percussion", "vocals", "wah guitar"),
        sound_design="Hammond B3 with Leslie and drawbar grit, Rhodes through tremolo and phaser, wah-wah "
                     "guitar, dusty sampled breaks with vinyl crackle, flute and muted trumpet.",
        production="Club-ready low end and punchy drums with vintage warmth: tape saturation, moderate bus "
                   "compression, horns and keys spread wide.",
        theory="Recontextualizes 1960s-70s soul-jazz harmony (dorian vamps, minor 9ths) over hip-hop and house "
               "rhythmic production; the groove is the form.",
        mix=Mix(lufs=(-11, -8), lra=(4, 8), low_end="heavy", tone="warm", width="wide"),
    ),
    Genre(
        name="gypsy jazz",
        family="jazz",
        aliases=("jazz manouche", "manouche", "hot club jazz"),
        parent="swing",
        description="Django Reinhardt's string swing: virtuosic acoustic lead guitar and violin over the driving "
                    "'la pompe' rhythm guitars and upright bass, with a Romani melodic flavour.",
        era="Paris, 1930s (Quintette du Hot Club de France); living tradition in Romani communities since",
        touchstones=("Django Reinhardt", "Stéphane Grappelli", "Quintette du Hot Club de France", "Biréli Lagrène",
                     "Stochelo Rosenberg", "Tchavolo Schmitt", "Angelo Debarre", "Joscho Stephan"),
        tempo=(100, 280),
        feel="la pompe: four-to-the-bar rhythm guitar with a short, snapped upstroke on 2 and 4; light swing",
        swing=60,
        modes=("minor", "major", "harmonic minor"),
        keys=("A minor", "D minor", "G minor", "G major", "C major"),
        progressions=(
            "i6/9-i6/9-iv6/9-iv6/9-i6/9-i6/9-V7-V7-iv6/9-iv6/9-i6/9-i6/9-V7-V7-i6/9-i6/9",
            "iiø7-V7b9-i6/9-i6/9",
            "i6/9-VI7-V7-i6/9",
            "major: VI7-VI7-II7-II7-V7-V7-I6/9-I6/9",
            "major: I6/9-#i°7-ii7-V7",
        ),
        harmonic_rhythm=1,
        harmony="Minor 6th chords (m6, m6/9) as tonic and iv, dominant 7ths and 9ths, diminished 7ths, the "
                "bVI7-V7 approach in minor, circle-of-dominants tunes (VI7-II7-V7-I), and swing-era standards. "
                "Chords are voiced as compact three- and four-note grips on the guitar's middle strings.",
        voicing="close",
        comping="quarters",
        bass_style="root_fifth",
        bass="Upright bass in two (roots and 5ths on 1 and 3, slapped) or walking on fast tunes, under the "
             "rhythm guitars' four.",
        melody_density="busy",
        melody_scale="harmonic minor",
        melody="Arpeggio-driven lines (minor-6 and diminished arpeggios swept across the strings), chromatic "
               "runs, the harmonic minor and 'gypsy' augmented-2nd colour over V7, octave melodies, rapid "
               "tremolo, bends and vibrato on the last note; violin lines by Grappelli are lyrical and swing hard.",
        groove={"step": 0.5, "swing": 60, "pattern": {
            "snare":     "o.x.o.x.",
            "pedal hat": "..x...x.",
        }},
        drums="Usually no drums at all: the rhythm guitars are the drums. If any, brushes on snare with light "
              "accents on 2 and 4 and a closed hi-hat foot.",
        form=(("intro", 4), ("head", 32), ("guitar solo", 64), ("violin solo", 32), ("rhythm guitar solo", 32),
              ("head out", 32), ("ending (diminished run)", 4)),
        instruments=("Selmer-Maccaferri lead guitar", "rhythm guitars (two)", "violin", "upright bass", "clarinet",
                     "accordion"),
        sound_design="Bright, cutting oval-hole Selmer-style guitars with heavy picks and strong attack, dry rhythm "
                     "guitars, violin with expressive vibrato, slapped upright; no amplification.",
        production="Acoustic, close-miked and live; lead guitar and violin up front, rhythm guitars panned left and "
                   "right, bass centre; bright tone, little reverb, light compression on the lead.",
        theory="Minor-key swing grounded in i-iv-V with the m6 (dorian 6th) as the defining tonic colour; lead "
               "lines rely on arpeggio substitution (play the m6 arpeggio of the ii over V7, diminished arpeggios "
               "over V7b9).",
        mix=Mix(lufs=(-17, -12), lra=(7, 13), low_end="light", tone="bright", width="moderate"),
    ),
    Genre(
        name="dixieland",
        family="jazz",
        aliases=("new orleans jazz", "trad jazz", "traditional jazz", "hot jazz"),
        parent="ragtime",
        description="Early New Orleans jazz: a front line of trumpet, clarinet and trombone improvising "
                    "polyphonically over a two-beat rhythm of tuba or bass, banjo and drums.",
        era="New Orleans and Chicago, 1910s-1920s; revival from the 1940s on",
        touchstones=("Louis Armstrong Hot Five and Hot Seven", "King Oliver's Creole Jazz Band", "Jelly Roll Morton",
                     "Sidney Bechet", "Kid Ory", "Original Dixieland Jass Band", "Preservation Hall Jazz Band"),
        tempo=(90, 240),
        feel="two-beat (bass on 1 and 3) with a bouncing swing; collective polyphony",
        swing=62,
        modes=("major",),
        keys=("Bb major", "F major", "Eb major", "C major", "G major"),
        progressions=(
            "I-I-VI7-VI7-II7-II7-V7-V7",
            "I-I-I-I-I-I-V7-V7-I-I7-IV-iv-I-V7-I-I",
            "I7-IV7-I7-I7-IV7-IV7-I7-I7-V7-V7-I7-I7",
            "I-III7-VI7-II7-V7-V7-I-I",
            "I-#i°7-ii7-V7",
        ),
        harmonic_rhythm=1,
        harmony="Simple triads, 6th chords and dominant 7ths; chains of secondary dominants (III7-VI7-II7-V7, the "
                "'ragtime progression'), passing diminished chords, the minor iv borrowed before the tonic, 12-bar "
                "blues and multi-strain marches inherited from ragtime and brass bands.",
        voicing="close",
        comping="quarters",
        bass_style="root_fifth",
        bass="Tuba or upright bass in two: root on 1, 5th on 3, with walk-ups into chord changes; four-to-the-bar "
             "walking in later Chicago style.",
        melody_density="busy",
        melody_scale="major blues",
        melody="Trumpet (cornet) states and decorates the melody in the middle; clarinet weaves fast arpeggios and "
               "obbligatos above; trombone plays tailgate counterlines and smears below. Blue notes, call-and-"
               "response breaks (two-bar solo breaks over stop-time), and Armstrong-style rhythmic paraphrase.",
        groove={"step": 0.5, "swing": 62, "pattern": {
            "kick":      "x...x...x...x...",
            "snare":     "..x...x...x..ox.",
            "woodblock": "x...x.x.x...x.x.",
        }},
        drums="Bass drum on 1 and 3, snare press rolls and backbeats, woodblock and rims, choke-cymbal accents "
              "(Baby Dodds, Zutty Singleton); New Orleans second-line street beats on parade tunes.",
        form=(("intro", 4), ("ensemble chorus", 32), ("clarinet solo", 32), ("trumpet solo", 32),
              ("trombone solo", 32), ("stop-time breaks", 16), ("out chorus (collective)", 32), ("tag", 4)),
        instruments=("cornet or trumpet", "clarinet", "trombone", "tuba or upright bass", "banjo", "piano",
                     "drum kit"),
        sound_design="Open brass with growl and plunger effects, woody clarinet, bright four-string banjo strumming "
                     "the beat, tuba oom-pah; acoustic horn-era recording colour (narrow, mid-focused).",
        production="Historically acoustic-horn or early electric recordings: mono, mid-heavy, little bass. Modern "
                   "trad bands recorded live and natural with the front line centred and close.",
        theory="Polyphonic texture is the identity: three independent improvised lines in distinct registers and "
               "roles over a two-beat pulse; harmony comes from ragtime's secondary-dominant chains and the blues.",
        mix=Mix(lufs=(-17, -12), lra=(7, 13), low_end="light", tone="warm", width="moderate"),
    ),
    Genre(
        name="ragtime",
        family="jazz",
        aliases=("rag", "piano rag", "classic rag"),
        description="Syncopated, march-form piano music: a steady oom-pah left hand under a right hand full of "
                    "offbeat accents, written out and played straight.",
        era="US Midwest (Sedalia, St. Louis), 1895-1918",
        touchstones=("Scott Joplin", "James Scott", "Joseph Lamb", "Eubie Blake", "Jelly Roll Morton",
                     "Joshua Rifkin's Joplin recordings"),
        tempo=(70, 110),
        meter="2/4",
        feel="straight (not swung) syncopation over a march pulse; 'not fast', as Joplin wrote",
        swing=50,
        modes=("major", "minor"),
        keys=("Ab major", "Bb major", "F major", "C major", "Eb major"),
        progressions=(
            "I-I-I-I-V7-V7-I-I",
            "I-VI7-II7-V7-I-VI7-II7-V7",
            "I-I7-IV-iv-I64-V7-I-I",
            "I-#i°7-ii-#ii°7-I6-VI7-II7-V7",
            "vi-vi-III7-III7-vi-II7-V7-I",
        ),
        harmonic_rhythm=1,
        harmony="Common-practice harmony in a march frame: I, IV, V7, secondary dominants in chains (VI7-II7-V7), "
                "diminished 7ths as chromatic passing chords, cadential 6/4s, the borrowed minor iv, and the trio "
                "strain modulating to the subdominant key.",
        voicing="close",
        comping="offbeat",
        bass_style="root_fifth",
        bass="Left-hand 'stride' oom-pah: single bass notes or octaves on the beats (root, then 5th) alternating "
             "with mid-register chords on the offbeat 8ths; chromatic octave bass walks at cadences.",
        melody_density="busy",
        melody_scale="major",
        melody="Right-hand syncopation: the 16th-8th-16th 'cakewalk' figure, tied notes across the beat, broken "
               "octaves and 3-3-2 groupings of 16ths, chromatic neighbour tones; 16-bar strains built from 4-bar "
               "phrases.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":      "x...x...x...x...",
            "snare":     "..x...x...x...x.",
            "woodblock": "x..x..x.x..x..x.",
        }},
        drums="Usually solo piano, no drums. In ragtime orchestras (Red Back Book) a light snare and bass drum "
              "play march style: bass drum on the beats, snare on offbeats, woodblock doubling the syncopation.",
        form=(("intro", 4), ("A strain", 16), ("A strain", 16), ("B strain", 16), ("B strain", 16), ("A strain", 16),
              ("trio C (in IV)", 16), ("trio C", 16), ("D strain", 16), ("D strain", 16)),
        instruments=("acoustic piano (upright)", "banjo", "cornet", "violin", "tuba", "clarinet"),
        sound_design="Bright, slightly honky upright piano with a short natural room; for ensembles, parlour "
                     "orchestra colour (cornet, violin, clarinet, tuba).",
        production="Solo piano recorded close and natural, with a stereo pair and little processing; keep the "
                   "dynamic range of the written accents.",
        theory="Syncopation against an unvarying duple pulse is the essence: right-hand accents fall on the second "
               "16th of the beat and across beats while the left hand never deviates. Multi-strain march form "
               "(AABBACCDD) with the trio in the subdominant key.",
        mix=Mix(lufs=(-18, -13), lra=(6, 12), low_end="light", tone="warm", width="moderate"),
    ),
    Genre(
        name="jazz ballad",
        family="jazz",
        aliases=("jazz ballads", "torch song"),
        parent="jazz",
        description="The slow jazz standard: a singer or horn caressing a melody over rich, slow-moving "
                    "reharmonized changes, brushes and space, every note weighted.",
        era="Great American Songbook, 1930s-50s; a jazz staple ever since",
        touchstones=("John Coltrane and Johnny Hartman", "Billie Holiday", "Ben Webster", "Chet Baker Sings",
                     "Bill Evans", "Shirley Horn", "Coleman Hawkins Body and Soul", "Miles Davis 'Round Midnight"),
        tempo=(50, 80),
        feel="slow and floating with a triplet undercurrent; rubato intros and cadenzas; double-time feel in solos",
        swing=66,
        modes=("major", "minor"),
        keys=("Eb major", "Db major", "Ab major", "F major", "C minor"),
        progressions=(
            "Imaj9-VI7b9-ii9-V13b9",
            "Imaj7-#i°7-ii7-#ii°7-iii7-VI7b9-ii7-V7",
            "IVmaj7-IVmaj7-iv7-bVII7-Imaj7-Imaj7-iii7-VI7",
            "iii7-bIII7-ii7-bII7",
            "minor: iiø7-V7b9-imaj7-i7-iv9-VII7-IIImaj7-VImaj7",
        ),
        harmonic_rhythm=2,
        harmony="Two chords per bar at a slow tempo gives room for rich reharmonization: tritone subs, "
                "chromatic ii-V's, passing diminished chords between diatonic chords, backdoor iv7-bVII7, "
                "altered dominants with b9 and b13, maj7#11 and m(maj7) tonics, pedal points under the tag. Endings "
                "often extend with iii-VI-ii-V or bII7 before the final Imaj9.",
        voicing="drop2",
        comping="sustain",
        bass_style="walking",
        bass="Long half notes and dotted rhythms in two, with chromatic passing tones and occasional double-time "
             "walking in the solos; pedal under the intro; bowed notes for the final chord.",
        melody_density="sparse",
        melody_scale="major",
        melody="Melody first: paraphrase with delayed attacks, long held notes with slow vibrato, grace notes and "
               "turns, rubato phrasing behind the beat. Solos alternate lyrical half-chorus statements with "
               "double-time runs; land on extensions (9, #11, 13) for colour; breathy subtone on tenor.",
        groove={"step": 1 / 3, "swing": 50, "pattern": {
            "snare":     "x..o.ox..o.o",
            "ride":      "o..o.oo..o.o",
            "pedal hat": "...x.....x..",
            "kick":      "o.....o.....",
        }},
        drums="Brushes: a continuous circular sweep on the snare with taps marking the triplet ride pattern, "
              "hi-hat foot on 2 and 4, bass drum almost silent; mallet cymbal swells in rubato sections.",
        form=(("rubato intro", 4), ("head A", 8), ("head A", 8), ("head B", 8), ("head A", 8),
              ("solo (half chorus)", 16), ("head out B-A", 16), ("cadenza and tag", 4)),
        instruments=("tenor saxophone or voice", "acoustic piano", "upright bass", "drum kit with brushes",
                     "flugelhorn", "strings"),
        sound_design="Breathy, close tenor or voice, warm piano with sustain pedal, round upright, soft brushes; "
                     "strings arrangement (with-strings albums) in sustained divisi chords.",
        production="Intimate and close with natural room or plate reverb; the quietest jazz masters, huge dynamic "
                   "range, no limiting; voice/horn upfront centre.",
        theory="Slow tempo invites harmonic density: reharmonization with tritone substitution and chromatic "
               "approach chords, inner-voice motion (descending lines inside a static tonic, e.g. maj7 to 6), "
               "and melody notes harmonized as upper extensions.",
        mix=Mix(lufs=(-21, -14), lra=(9, 17), low_end="light", tone="warm", width="wide"),
    ),
    # ----------------------------------------------------------------- blues
    Genre(
        name="blues",
        family="blues",
        aliases=("12-bar blues", "twelve-bar blues", "blues shuffle"),
        description="The 12-bar foundation of American popular music: call-and-response vocals and guitar over "
                    "dominant-7th I-IV-V changes, blue notes, and a rolling triplet shuffle.",
        era="African American South, c. 1900s; electrified in Chicago, Memphis and Texas, 1940s-50s",
        touchstones=("B.B. King", "Muddy Waters", "Howlin' Wolf", "T-Bone Walker", "Albert King", "Freddie King",
                     "Bessie Smith", "John Lee Hooker", "Robert Johnson"),
        tempo=(60, 140),
        feel="triplet shuffle (12/8 feel) or slow 12/8; some straight-eighth rhumba and boogie grooves",
        swing=66,
        modes=("major", "minor"),
        keys=("E major", "A major", "G major", "C major", "Bb major", "A minor"),
        progressions=(
            "I7-IV7-I7-I7-IV7-IV7-I7-I7-V7-IV7-I7-V7",
            "I7-I7-I7-I7-IV7-IV7-I7-I7-V7-IV7-I7-I7",
            "I7-I7-I7-I7-IV7-IV7-I7-I7-V7-V7-I7-I7",
            "minor: i7-i7-i7-i7-iv7-iv7-i7-i7-VI7-V7-i7-V7",
            "I7-V7-IV7-IV7-I7-V7-I7-V7",
        ),
        harmonic_rhythm=1,
        harmony="All three primary chords are dominant 7ths (I7, IV7, V7), which no classical key allows: the b7 of "
                "I7 and the b3 of the melody are the blue notes made into harmony. 12-bar form: I-I-I-I / IV-IV-I-I "
                "/ V-IV-I-V (quick change puts IV in bar 2; the last bar is the V7 turnaround). 9ths and 13ths "
                "on the dominants; minor blues uses i7-iv7 with a VI7-V7 in bars 9-10; 8-bar blues (I-V-IV-IV-I-V-I-V).",
        voicing="close",
        comping="stabs",
        bass_style="boogie",
        bass="Shuffle bass walking the chord: root-3-5-6-b7-6-5-3 figures in swung 8ths, or root-5-6-5 boogie "
             "patterns; on slow blues, long roots with walk-ups into IV and the turnaround (5-#5-6 or chromatic "
             "down from the b7).",
        melody_density="medium",
        melody_scale="blues",
        melody="AAB lyric form: a 4-bar line, repeated over the IV, answered by a resolving line over V-IV-I; each "
               "vocal phrase leaves 2 bars for a guitar answer (call and response). Minor pentatonic + b5 over "
               "major chords, the b3 bent toward the major 3rd, b7, quarter-tone 'curls', mixing major and minor "
               "pentatonic (major 6th and 3rd over I7, the b3 over IV7), vibrato on long notes, repeated-note "
               "rhythmic licks; the turnaround lick descends chromatically to the V.",
        groove={"step": 1 / 3, "swing": 50, "pattern": {
            "closed hat": "x.xx.xx.xx.x",
            "snare":      "...X.....X..",
            "kick":       "x.....x.....",
        }},
        drums="Shuffle: triplet-based hi-hat or ride (long-short on each beat), snare backbeat on 2 and 4, kick on "
              "1 and 3 or four on the floor; slow blues in 12/8 with a heavy backbeat on beat 3 of the 12/8 "
              "bar (every second dotted quarter); fills are triplet rolls into the turnaround.",
        form=(("intro (turnaround)", 4), ("verse 1", 12), ("verse 2", 12), ("guitar solo", 24), ("verse 3", 12),
              ("outro", 12)),
        instruments=("electric guitar", "vocals", "electric bass", "drum kit", "piano", "harmonica",
                     "Hammond organ", "horn section"),
        sound_design="Tube amp tone (Fender Bassman, Twin, Deluxe) on the edge of breakup, Strat/Les Paul/ES-335, "
                     "spring reverb; harmonica through a bullet mic and small amp; warm round bass.",
        production="Live-band recording with natural room; vocal and guitar share the spotlight; moderate "
                   "compression, warm midrange, not overly loud.",
        theory="Blue notes (b3, b5, b7) sit between major and minor; the melody's b3 clashing against the chord's "
               "major 3rd is the sound. Dominant-7th chords on I, IV and V are non-functional colour, and the "
               "12-bar AAB form ends each chorus with a V7 turnaround.",
        mix=Mix(lufs=(-14, -10), lra=(5, 10), low_end="moderate", tone="warm", width="moderate"),
    ),
    Genre(
        name="delta blues",
        family="blues",
        aliases=("country blues", "acoustic blues", "mississippi blues", "hill country blues"),
        parent="blues",
        description="The raw acoustic blues of the Mississippi Delta: one voice and one guitar, bottleneck slide, "
                    "droning thumb bass, and loose, speech-like timing.",
        era="Mississippi Delta, 1920s-1930s; North Mississippi hill country tradition after",
        touchstones=("Robert Johnson", "Charley Patton", "Son House", "Skip James", "Bukka White",
                     "Mississippi Fred McDowell", "Tommy Johnson", "R.L. Burnside"),
        tempo=(60, 130),
        feel="loose shuffle or straight driving thumb, often with irregular bar lengths",
        swing=64,
        modes=("major", "minor"),
        keys=("E major", "A major", "G major", "D major", "E minor"),
        progressions=(
            "I7-IV7-I7-I7-IV7-IV7-I7-I7-V7-IV7-I7-I7",
            "I7-I7-I7-I7-I7-I7-I7-I7",
            "I7-I7-I7-I7-IV7-IV7-I7-I7-V7-V7-I7-I7",
            "I7-IV7-I7-I7-IV7-IV7-I7-I7-V7-IV7-I7-V7",
        ),
        harmonic_rhythm=1,
        harmony="Implied rather than strummed harmony: open-tuning drones (open G, open D, open E, cross-note D "
                "minor) with the tonic ringing under everything; changes follow the singer, so 12-bar forms "
                "stretch to 13 or 14 bars; one-chord drone pieces in the hill-country style.",
        voicing="open",
        comping="broken",
        bass_style="pedal",
        bass="No bass player: the guitarist's thumb pounds a steady tonic (often muted) on every beat, or an "
             "alternating root-octave, while the fingers play the melody and slide licks above.",
        melody_density="medium",
        melody_scale="blues",
        melody="Speech-like, melismatic vocal moaning with falsetto breaks; slide guitar echoing and finishing the "
               "vocal line, landing on b3-to-3 and b7 between frets, repeated treble-string riffs, hammer-ons from "
               "the b3; phrases start on the upbeat and end on the tonic.",
        groove={"step": 1 / 3, "swing": 50, "pattern": {
            "kick":       "x..x..x..x..",
            "tambourine": "...x.....x..",
        }},
        drums="Traditionally none: the foot stomp is the kick (on every beat) and the guitar body taps the "
              "backbeat; add at most a stomp box or tambourine, or a sparse hill-country trance beat.",
        form=(("intro (guitar)", 4), ("verse 1", 12), ("verse 2", 12), ("guitar break", 12), ("verse 3", 12),
              ("verse 4", 12), ("outro", 4)),
        instruments=("acoustic guitar (steel-string or resonator)", "bottleneck slide", "vocals", "harmonica",
                     "foot stomp"),
        sound_design="Steel-bodied resonator (National) or cheap flat-top with heavy strings in open tuning, glass "
                     "or metal bottleneck, raw voice; old 78-rpm character: narrow band, surface noise.",
        production="One or two microphones in a room, live, mono or nearly so; no compression or a little; let "
                   "the voice and guitar breathe and the timing wander.",
        theory="Modal and drone-based: the tonic pedal under a blues-scale melody makes the b3 and b7 the main "
               "colours; form is elastic because the phrase, not the bar line, rules.",
        mix=Mix(lufs=(-18, -12), lra=(6, 12), low_end="light", tone="warm", width="narrow"),
    ),
    Genre(
        name="chicago blues",
        family="blues",
        aliases=("electric blues", "chicago electric blues", "chess blues"),
        parent="delta blues",
        description="The Delta amplified in Chicago: loud electric guitar and amplified harp with a full band, "
                    "heavy shuffles, stop-time riffs and boastful vocals.",
        era="Chicago South and West Side, late 1940s-1960s (Chess, Vee-Jay, Cobra)",
        touchstones=("Muddy Waters", "Howlin' Wolf", "Little Walter", "Willie Dixon", "Elmore James", "Otis Rush",
                     "Buddy Guy", "Junior Wells", "Jimmy Reed", "Magic Sam"),
        tempo=(70, 160),
        feel="heavy triplet shuffle, stop-time riffs, slow 12/8 grinders",
        swing=66,
        modes=("major", "minor"),
        keys=("E major", "A major", "G major", "Bb major", "C major"),
        progressions=(
            "I7-IV7-I7-I7-IV7-IV7-I7-I7-V7-IV7-I7-V7",
            "I7-I7-I7-I7-IV7-IV7-I7-I7-V7-IV7-I7-I7",
            "I7-I7-I7-I7-I7-I7-I7-I7-I7-I7-I7-I7",
            "minor: i7-i7-i7-i7-iv7-iv7-i7-i7-VI7-V7-i7-V7",
            "I7-V7-IV7-IV7-I7-V7-I7-V7",
        ),
        harmonic_rhythm=1,
        harmony="12-bar dominant-7th blues (often quick change), one-chord stop-time riff songs where the band hits "
                "a riff and stops for the vocal, 9th chords on IV and V, minor blues in the West Side style.",
        voicing="close",
        comping="eighths",
        bass_style="boogie",
        bass="Walking boogie shuffles on bass and the guitar's low strings in unison (root-5-6-b7 patterns), "
             "riff ostinatos doubling the guitar on stop-time tunes.",
        melody_density="medium",
        melody_scale="blues",
        melody="Shouted, confident vocals with growls and falsetto; amplified harp riffs (chordal 'train' "
               "rhythms, bent cross-harp 2nd position, octave splits); slide guitar in open E/D with triplet "
               "Elmore James figures; West Side guitar with B.B.-style bends, minor pentatonic and "
               "major/minor mixing.",
        groove={"step": 1 / 3, "swing": 50, "pattern": {
            "ride":      "x.xx.xx.xx.xx.xx.xx.xx.x",
            "snare":     "...X..o..X.....X..o..X.o",
            "kick":      "x.....x..o..x.....x.....",
            "pedal hat": "...x.....x.....x.....x..",
        }},
        drums="Heavy shuffle on ride or half-open hat, fat snare backbeat with ghosted triplets, kick locked to "
              "the walking bass; stop-time hits with the band; Fred Below's swing-to-blues drumming.",
        form=(("intro", 4), ("verse 1", 12), ("verse 2", 12), ("harp solo", 12), ("verse 3", 12), ("guitar solo", 12),
              ("verse 4", 12), ("outro", 4)),
        instruments=("electric guitar", "amplified harmonica", "vocals", "piano", "upright or electric bass",
                     "drum kit", "second guitar"),
        sound_design="Small tube amps pushed hard (Fender Deluxe, Bassman), harp through a Shure Green Bullet into "
                     "a cranked amp (thick, distorted, compressed), barrelhouse piano, slapback room sound.",
        production="Live ensemble in a small room (Chess studio), with bleed; mono or narrow; amps cranked so "
                   "natural compression; vocal forward.",
        theory="Riff-based arrangement: a one- or two-bar riff in unison (guitar, bass, harp) stops to leave space "
               "for the vocal line (stop-time); the shuffle's triplet subdivision governs all phrasing.",
        mix=Mix(lufs=(-14, -10), lra=(5, 10), low_end="moderate", tone="warm", width="moderate"),
    ),
    Genre(
        name="texas blues",
        family="blues",
        aliases=("texas shuffle",),
        parent="blues",
        description="Texas blues: single-note lead guitar that swings like a horn, 9th-chord jazz colour, "
                    "big-hearted shuffles, and slow minor blues.",
        era="Texas (Dallas, Houston, Austin), 1920s acoustic; electric from T-Bone Walker in the 1940s; Austin revival in the 1980s",
        touchstones=("T-Bone Walker", "Lightnin' Hopkins", "Freddie King", "Albert Collins", "Stevie Ray Vaughan",
                     "Clarence 'Gatemouth' Brown", "Jimmie Vaughan", "Johnny Copeland"),
        tempo=(70, 170),
        feel="swinging Texas shuffle (double shuffle), slow blues in 12/8, straight-eighth 'Hideaway' boogie",
        swing=64,
        modes=("major", "minor"),
        keys=("E major", "A major", "Eb major", "Bb major", "C minor"),
        progressions=(
            "I9-IV9-I9-I9-IV9-IV9-I9-I9-V9-IV9-I9-V9",
            "I7-I7-I7-I7-IV9-IV9-I7-I7-V7#9-IV9-I7-V7#9",
            "minor: i9-i9-i9-i9-iv9-iv9-i9-i9-VI9-V7#9-i9-V7#9",
            "I7-IV7-I7-I7-IV7-IV7-I7-I7-V7-IV7-I7-V7",
        ),
        harmonic_rhythm=1,
        harmony="12-bar blues with jazzy 9th and 13th chords (T-Bone Walker), the 7#9 'Hendrix chord' on V, minor "
                "slow blues with VI9-V7#9, sliding chromatic 9th chords (a half step below into the target), and "
                "rhythm 'chank' on 2 and 4 in jump-flavoured songs.",
        voicing="close",
        comping="stabs",
        bass_style="walking",
        bass="Swinging walking-shuffle lines, root-5-6-b7 patterns doubling the guitar riff, heavy 'Pride and Joy' "
             "double-shuffle boogie with the guitar's low E.",
        melody_density="busy",
        melody_scale="blues",
        melody="Horn-like single-note lines: T-Bone's jazzy major 6th and 9th mixed with blues, Freddie King's "
               "minor/major pentatonic mix, SRV's aggressive raked bends, wide vibrato and double stops, the "
               "Albert King 'box'; call-and-response with vocals.",
        groove={"step": 1 / 3, "swing": 50, "pattern": {
            "ride":      "x.xx.xx.xx.x",
            "snare":     "..oX.o..oX.o",
            "kick":      "x.....x.....",
            "pedal hat": "...x.....x..",
        }},
        drums="Texas double shuffle: triplets with the middle partial ghosted on snare, heavy backbeat, swinging "
              "ride (Chris Layton); slow blues with triplet hi-hat and huge snare on beat 3 of 12/8.",
        form=(("intro", 4), ("verse 1", 12), ("verse 2", 12), ("guitar solo", 36), ("verse 3", 12), ("outro", 8)),
        instruments=("Stratocaster or hollow-body electric guitar", "vocals", "electric bass", "drum kit",
                     "Hammond organ", "horn section"),
        sound_design="Loud, clean-to-crunchy Fender tone (Vibroverb, Super Reverb, heavy strings, 'Tube "
                     "Screamer' push), bright Telecaster ice-picking for Albert Collins; organ pads; tight horns.",
        production="Live trio/band in the room, guitar up front and loud, vocals natural; some slapback/room "
                   "reverb; moderate compression.",
        theory="Bridges blues and jazz: 9th and 13th chords, swing phrasing and chromatic approaches inside the "
               "blues scale; slow minor blues use the VI9 (b6 of the key) to V7#9 for a bittersweet turn.",
        mix=Mix(lufs=(-13, -9), lra=(5, 9), low_end="moderate", tone="bright", width="moderate"),
    ),
    Genre(
        name="jump blues",
        family="blues",
        aliases=("jump", "jump and jive", "jive"),
        parent="swing",
        description="Uptempo, horn-driven party blues bridging swing and rock'n'roll: shouting vocals, honking "
                    "tenor sax, boogie bass and a heavy backbeat.",
        era="US cities (Los Angeles, New York, Kansas City), 1940s-early 1950s",
        touchstones=("Louis Jordan and his Tympany Five", "Big Joe Turner", "Wynonie Harris", "Roy Brown",
                     "Amos Milburn", "Big Jay McNeely", "Roomful of Blues", "Brian Setzer Orchestra"),
        tempo=(130, 220),
        feel="hard swing with a strong 2 and 4 backbeat; walking or boogie bass",
        swing=64,
        modes=("major",),
        keys=("Bb major", "F major", "C major", "Eb major", "G major"),
        progressions=(
            "I7-IV7-I7-I7-IV7-IV7-I7-VI7-ii7-V7-I7-V7",
            "I7-I7-I7-I7-IV7-IV7-I7-I7-V7-IV7-I7-V7",
            "I6/9-vi7-ii7-V7",
            "III7-III7-VI7-VI7-II7-II7-V7-V7",
        ),
        harmonic_rhythm=1,
        harmony="12-bar blues with swing-band touches (VI7-ii-V into the turnaround, 6th and 9th chords), rhythm "
                "changes and riff tunes; horn section riffs on the dominant 7th chords.",
        voicing="close",
        comping="stabs",
        bass_style="boogie",
        bass="Walking or boogie-woogie bass in swung 8ths (root-3-5-6-b7-6-5-3), doubled by piano left hand.",
        melody_density="busy",
        melody_scale="major blues",
        melody="Shouted, humorous, rhythmic vocals with tag-line hooks; honking, screaming tenor solos on one or two "
               "notes with growl and altissimo; horn riffs answer each vocal line; blues and major-blues licks.",
        groove={"step": 0.5, "swing": 64, "pattern": {
            "ride":  "x.xxx.xxx.xxx.xx",
            "snare": "..X...X...X...X.",
            "kick":  "x.x.x.x.x.x.x.x.",
            "crash": "x...............",
        }},
        drums="Swing ride with a heavy rimshot backbeat on 2 and 4, four-on-the-floor kick, horn-kicks and stops "
              "set up with snare fills; a direct ancestor of the rock'n'roll beat.",
        form=(("intro", 4), ("verse", 12), ("verse", 12), ("tenor sax solo", 24), ("verse", 12), ("stop-time chorus", 12),
              ("out chorus", 12), ("ending", 2)),
        instruments=("tenor saxophone", "vocals", "alto and baritone saxophones", "trumpet", "piano", "upright bass",
                     "drum kit", "electric guitar"),
        sound_design="Gritty honking tenor, punchy small horn section, upright bass slapped, boogie piano, early "
                     "hollow-body electric guitar; vintage ribbon-mic warmth.",
        production="Tight, live small-band sound with a forward vocal and sax; mono-era character; moderate "
                   "compression; punchy and bright.",
        theory="Swing-era blues with the backbeat moved to the front: the 2 and 4 snare and boogie bass make it the "
               "bridge between big-band swing and rock'n'roll.",
        mix=Mix(lufs=(-14, -10), lra=(5, 10), low_end="moderate", tone="bright", width="moderate"),
    ),
    Genre(
        name="boogie-woogie",
        family="blues",
        aliases=("boogie", "boogie piano", "barrelhouse"),
        parent="blues",
        description="Driving blues piano: a relentless rolling left-hand ostinato of eight notes to the bar under "
                    "right-hand riffs, tremolos and crushed blue notes.",
        era="Texas and Louisiana barrelhouses, 1920s; Chicago and New York (Carnegie Hall 'From Spirituals to Swing'), late 1930s",
        touchstones=("Meade Lux Lewis", "Albert Ammons", "Pete Johnson", "Pinetop Smith", "Jimmy Yancey",
                     "Big Joe Turner", "Axel Zwingenberger"),
        tempo=(120, 200),
        feel="eight-to-the-bar left hand, shuffled or nearly straight; very driving",
        swing=62,
        modes=("major",),
        keys=("C major", "G major", "F major", "Bb major", "E major"),
        progressions=(
            "I7-IV7-I7-I7-IV7-IV7-I7-I7-V7-IV7-I7-V7",
            "I7-I7-I7-I7-IV7-IV7-I7-I7-V7-V7-I7-I7",
            "I7-I7-IV7-IV7-I7-V7-I7-V7",
            "I6/9-IV9-I6/9-V7",
        ),
        harmonic_rhythm=1,
        harmony="Strict 12-bar blues on dominant 7ths, sometimes 6ths on the tonic; the left-hand pattern moves "
                "intact to IV and V; turnaround with chromatic descending 6ths or diminished chord to V7.",
        voicing="close",
        comping="stabs",
        bass_style="boogie",
        bass="The left hand is the bass: walking broken octaves or root-5-6-b7-6-5 in eighths, 'rolling' octave "
             "patterns, or Yancey's slower dotted ostinatos; the same shape transposed to each chord.",
        melody_density="busy",
        melody_scale="blues",
        melody="Right hand plays riffs in 3rds and 6ths, crushed grace notes (b3 to 3), tremolos on the tonic "
               "triad, repeated-note riffs crossing the left hand's cross-rhythm (3 against 4 groupings), and "
               "glissandi; choruses build in intensity.",
        groove={"step": 1 / 3, "swing": 50, "pattern": {
            "closed hat": "x.xx.xx.xx.x",
            "snare":      "...X.....X..",
            "kick":       "x..x..x..x..",
        }},
        drums="Solo piano by tradition; with a band, shuffle on hi-hat or snare brushes, backbeat on 2 and 4, kick "
              "on all four.",
        form=(("intro", 4), ("chorus 1", 12), ("chorus 2", 12), ("chorus 3", 12), ("chorus 4 (tremolo)", 12),
              ("chorus 5 (climax)", 12), ("ending", 4)),
        instruments=("acoustic piano", "upright bass", "drum kit", "vocals", "tenor saxophone"),
        sound_design="Bright, punchy upright or grand piano, a little out of tune for barrelhouse flavour; dry "
                     "close mics with a short room.",
        production="Piano captured in stereo with strong low-mid weight; live energy, moderate compression.",
        theory="The left-hand ostinato is a rhythmic and harmonic engine (the blues bass line that rock'n'roll "
               "inherited); right-hand cross-rhythms against it create the drive.",
        mix=Mix(lufs=(-15, -11), lra=(6, 11), low_end="moderate", tone="warm", width="moderate"),
    ),
    # -------------------------------------------------------- funk and gospel
    Genre(
        name="funk",
        family="funk and gospel",
        aliases=("funky", "classic funk"),
        parent="soul",
        description="Rhythm as everything: interlocking syncopated 16th-note parts (scratch guitar, popping bass, "
                    "horn stabs, a tight drummer) built on 'the One', usually over one dominant chord.",
        era="US (James Brown's bands, New Orleans, the Bay Area), mid 1960s-1970s",
        touchstones=("James Brown Cold Sweat", "The Meters", "Sly and the Family Stone", "Tower of Power",
                     "The J.B.'s", "Kool & the Gang", "Ohio Players", "Earth, Wind & Fire", "Clyde Stubblefield"),
        tempo=(90, 125),
        feel="straight or lightly swung 16ths, heavy on the downbeat 'One', syncopated interlocking parts",
        swing=54,
        modes=("mixolydian", "dorian"),
        keys=("E mixolydian", "A mixolydian", "D mixolydian", "E dorian", "G dorian"),
        progressions=(
            "I9-I9-I9-I9",
            "I7#9-I7#9-IV9-IV9",
            "dorian: i7-i7-IV9-IV9",
            "I9-I9-bIII9-IV9",
            "IV9-IV9-IV9-IV9-I9-I9-I9-I9",
        ),
        harmonic_rhythm=0.5,
        harmony="One chord for long stretches, usually a dominant 9th or 7#9 (mixolydian) or a minor 7th "
                "(dorian), with a contrasting 'bridge' on the IV9 or a chromatic slide (bIII9-IV9, or into the "
                "chord from a half step below). Harmony is rhythm: chords are chopped, not held.",
        voicing="close",
        comping="pulse_16",
        bass_style="syncopated",
        bass="Syncopated 16th lines nailing the One, then dancing around it: octave pops, ghosted dead notes, "
             "slides, chromatic approach to the root; slap-and-pop (Larry Graham, Bootsy) or fingerstyle "
             "(Jamerson-influenced, George Porter Jr.). Leaves space; repetition is the point.",
        melody_density="sparse",
        melody_scale="minor pentatonic",
        melody="Shouted, chanted vocal hooks and grunts, call-and-response with horns; horn section stabs and "
               "unison riffs in minor pentatonic over the dominant chord; sax solos repeating rhythmic cells; "
               "everything placed percussively on the 16th grid.",
        groove={"step": 0.25, "swing": 54, "pattern": {
            "kick":       "x.x....x..x.....",
            "snare":      "....X..o.o..X..o",
            "closed hat": "xxxxxxxxxxxxxx.x",
            "open hat":   "..............x.",
        }},
        drums="Tight, dry kit: kick heavy on the One and syncopated 16ths, snare backbeat on 2 and 4 surrounded "
              "by ghost notes, 16th hi-hats with a quick open on an upbeat; breaks where everything drops but "
              "the drums (the 'break' later sampled by hip-hop).",
        form=(("intro", 8), ("groove A", 16), ("vocal", 16), ("bridge (IV)", 8), ("groove A", 16), ("break", 8),
              ("horn solo", 16), ("vamp out", 16)),
        instruments=("electric bass", "rhythm guitar (scratch)", "drum kit", "horn section", "clavinet",
                     "Hammond organ", "vocals", "congas"),
        sound_design="Dry, close sounds: bright single-coil scratch guitar (muted 16ths), punchy fingered or "
                     "slapped bass, Hohner clavinet through a wah or envelope filter, tight horns with tenor and "
                     "trumpet, deadened snare and kick.",
        production="Separation: every part in its own pocket and space, little reverb, bass and kick loud and "
                   "upfront, guitar panned to one side, horns punchy; tight compression on bass and drums.",
        theory="A rhythmic rather than harmonic music: interlocking ostinatos (each part a different 16th "
               "syncopation) produce a composite groove; emphasis on beat one ('the One') anchors the "
               "syncopation. Static mixolydian/dorian harmony keeps attention on rhythm.",
        mix=Mix(lufs=(-11, -8), lra=(4, 8), low_end="heavy", tone="bright", width="moderate"),
    ),
    Genre(
        name="p-funk",
        family="funk and gospel",
        aliases=("parliament-funkadelic", "funkadelic", "space funk"),
        parent="funk",
        description="George Clinton's cosmic funk: slower, deeper grooves, Minimoog bass, psychedelic guitar, "
                    "big chanted choruses and Afrofuturist theatre.",
        era="Detroit and the US touring circuit, 1970-early 1980s",
        touchstones=("Parliament Mothership Connection", "Funkadelic One Nation Under a Groove", "George Clinton",
                     "Bootsy's Rubber Band", "Bernie Worrell", "Eddie Hazel", "Zapp"),
        tempo=(95, 115),
        feel="deep, heavy 16th groove slightly swung, everything landing on the One",
        swing=56,
        modes=("dorian", "mixolydian", "minor"),
        keys=("E dorian", "F# dorian", "A dorian", "C mixolydian"),
        progressions=(
            "i9-i9-IV9-IV9",
            "i7-i7-i7-i7",
            "mixolydian: I9-I9-VII-IV",
            "i11-VII6/9-i11-IV9",
            "minor: i7-i7-iv7-v7",
        ),
        harmonic_rhythm=0.5,
        harmony="Long one- or two-chord vamps (dorian i7-IV9, mixolydian I-bVII-IV), Bernie Worrell's classical "
                "and gospel organ/synth voicings layered on top, chanted unison choruses, psychedelic guitar "
                "drones.",
        voicing="close",
        comping="stabs",
        bass_style="syncopated",
        bass="Bootsy's fat, envelope-filtered bass with slides and octave pops, or Bernie Worrell's Minimoog "
             "synth bass (portamento slides, huge low end); sparse, rubbery, hitting the One hard.",
        melody_density="sparse",
        melody_scale="minor pentatonic",
        melody="Chanted gang-vocal hooks and catchphrases, call-and-response between lead and crowd, character "
               "voices, high falsetto; Minimoog lead lines with portamento; fuzz-guitar solos (Eddie Hazel) with "
               "long sustained bends.",
        groove={"step": 0.25, "swing": 56, "pattern": {
            "kick":       "X.....x.x.....x.",
            "snare":      "....x.......x...",
            "clap":       "....x.......x...",
            "closed hat": "x.xxx.xxx.xxx.xx",
        }},
        drums="Heavy, steady pocket with big kick on the One, fat snare and claps on 2 and 4, swung 16th hats; "
              "less busy than James Brown, more weight; drum machines (LinnDrum) in the later Zapp era.",
        form=(("intro", 8), ("groove", 16), ("verse", 16), ("chant chorus", 16), ("verse", 16), ("chant chorus", 16),
              ("synth/guitar solo", 32), ("chant vamp out", 32)),
        instruments=("Minimoog", "electric bass (envelope filter)", "electric guitar (fuzz, wah)", "drum kit",
                     "horn section", "Hammond organ", "ARP string ensemble", "group vocals"),
        sound_design="Minimoog bass and leads with portamento, Mu-Tron envelope-filter bass, fuzz and wah guitars, "
                     "clavinet, ARP strings, vocoder and talk box (Zapp/Roger), pitched-voice characters.",
        production="Dense, psychedelic, big-low-end mixes with many layered vocals; heavy compression on bass "
                   "and drums, long reverbs and phasing on vocals and guitars, wide stereo.",
        theory="Funk's static-harmony groove stretched into long modal vamps; the synth bass's portamento and "
               "the chant chorus make form out of repetition and layering rather than chord changes.",
        mix=Mix(lufs=(-11, -8), lra=(4, 8), low_end="very heavy", tone="warm", width="wide"),
    ),
    Genre(
        name="gospel",
        family="funk and gospel",
        aliases=("black gospel", "gospel choir", "traditional gospel", "contemporary gospel"),
        description="African American church music: a lead singer and choir in call and response over Hammond "
                    "organ and piano, building from a slow 6/8 hymn to a shouting climax.",
        era="Chicago (Thomas A. Dorsey), 1930s; quartets and choirs through the 1950s-60s; contemporary gospel from the 1970s",
        touchstones=("Mahalia Jackson", "Thomas A. Dorsey", "Rev. James Cleveland", "The Edwin Hawkins Singers",
                     "Andraé Crouch", "The Clark Sisters", "Richard Smallwood", "Kirk Franklin",
                     "Aretha Franklin Amazing Grace"),
        tempo=(60, 140),
        feel="slow 12/8-style triplet ballads, mid-tempo swing, uptempo 'shout' with handclaps on 2 and 4",
        swing=64,
        modes=("major",),
        keys=("Ab major", "Db major", "Eb major", "F major", "Bb major"),
        progressions=(
            "I-I7-IV-#iv°7-I64-V7-I-I",
            "IV-IV-I-I",
            "I-I6-IV-#iv°7-I64-VI7-ii7-V7",
            "viiø7-III7-vi7-II7-ii7-V7-I-I",
            "ii7-#ii°7-I6-VI7b9-ii7-V7-I-I",
            "IV-IV-iv6/9-iv6/9-I-I-I-I",
        ),
        harmonic_rhythm=2,
        harmony="Hymn harmony with blues and jazz colour: I-I7-IV-#iv°7-I64-V7-I (the passing diminished and "
                "cadential 6/4 walk), the plagal 'Amen' IV-I and minor plagal iv-I, 7-3-6-2-5-1 chains of "
                "dominants (viiø7-III7-vi7-II7-ii7-V7-I), passing diminished chords between every diatonic step, "
                "sus4 dominants, and step-up key changes (half or whole step) for each new chorus. Contemporary "
                "gospel adds 9ths, 11ths and 13ths, slash chords and chromatic 'walk-ups'.",
        voicing="satb",
        comping="gospel",
        bass_style="syncopated",
        bass="Busy, melodic gospel bass: octave runs, chromatic walk-ups into each chord, slides and fills between "
             "vocal lines, walking on the shout tunes; left-hand piano octaves doubling the bass in traditional style.",
        melody_density="medium",
        melody_scale="major blues",
        melody="Lead vocalist phrases freely around the beat with melismatic runs (major pentatonic with the b3 "
               "and b7 'blue' passing tones), held climactic high notes, ad-libs and vamp repetitions; choir "
               "answers in 3-part close harmony (soprano, alto, tenor); call-and-response grows in intensity "
               "over a repeating vamp.",
        groove={"step": 1 / 3, "swing": 50, "pattern": {
            "kick":       "x.....x..x..",
            "snare":      "...X.....X..",
            "closed hat": "xooxooxooxoo",
            "clap":       "...x.....x..",
        }},
        drums="Slow songs: 12/8 triplet hats with a heavy backbeat on beat 3; shout tunes: fast swung 'shout' with "
              "handclaps, tambourine and snare on 2 and 4; contemporary gospel drummers ('gospel chops') play "
              "fast linear fills and huge builds.",
        form=(("intro", 4), ("verse", 16), ("chorus", 16), ("verse", 16), ("chorus", 16), ("vamp", 32),
              ("key change chorus", 16), ("shout / praise break", 32), ("ending", 4)),
        instruments=("Hammond B3 organ with Leslie", "acoustic piano", "choir", "lead vocals", "electric bass",
                     "drum kit", "tambourine", "handclaps"),
        sound_design="Hammond B3 with drawbars 888000000 or full, Leslie switching slow to fast on builds, "
                     "percussive gospel piano with fills, big natural choir, tambourine.",
        production="Live-in-church recordings with audience and room; choir wide, lead vocal centred and dry-ish; "
                   "dynamics build across the song (quiet verse to shout), moderate compression.",
        theory="Functional harmony enriched by chromatic passing chords (diminished 7ths, secondary dominants) "
               "and plagal cadences; vamps over a repeated 2-4 chord pattern are the engine of the climax; the "
               "step-up modulation is a structural device.",
        mix=Mix(lufs=(-13, -9), lra=(6, 11), low_end="moderate", tone="warm", width="wide"),
    ),
    Genre(
        name="doo-wop",
        family="funk and gospel",
        aliases=("street corner harmony", "vocal group harmony"),
        parent="gospel",
        description="1950s vocal-group R&B: lead tenor over close-harmony background vocals singing nonsense "
                    "syllables, triplet piano and the I-vi-IV-V progression.",
        era="US East Coast cities (New York, Philadelphia), 1950s-early 1960s",
        touchstones=("The Platters", "The Penguins", "The Five Satins", "Frankie Lymon and the Teenagers",
                     "The Flamingos", "Dion and the Belmonts", "The Moonglows", "The Del-Vikings"),
        tempo=(60, 140),
        feel="slow 12/8-style triplet ballads and swinging uptempo shuffles",
        swing=66,
        modes=("major",),
        keys=("C major", "G major", "Bb major", "Eb major", "F major"),
        progressions=(
            "I-vi-IV-V7",
            "I-vi-ii7-V7",
            "III7-III7-VI7-VI7-II7-II7-V7-V7",
            "I-I7-IV-iv-I-vi-ii7-V7",
        ),
        harmonic_rhythm=1,
        harmony="The '50s progression' (I-vi-IV-V or I-vi-ii-V) looped for the whole verse, a bridge of secondary "
                "dominants (III7-VI7-II7-V7), occasional minor iv borrowed before the return; mostly triads with "
                "6ths and 7ths in the vocal harmony.",
        voicing="close",
        comping="eighths",
        bass_style="root_fifth",
        bass="Upright bass in two (root, 5th), or the bass singer himself ('bom bom bom') walking arpeggios of "
             "root-3-5-6 under the group.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Smooth tenor or falsetto lead with emotional swells and spoken bridges; background vocals on "
               "nonsense syllables ('doo-wop', 'sh-boom', 'oo-wah') in close 3-4 part harmony; a bass voice riff "
               "and a soaring falsetto obbligato on top.",
        groove={"step": 1 / 3, "swing": 50, "pattern": {
            "kick":       "x.....x.....",
            "snare":      "...x.....x..",
            "closed hat": "xooxooxooxoo",
        }},
        drums="Light: brushes or sticks with a backbeat on 2 and 4, triplet ride or hi-hat on ballads, simple "
              "shuffle on uptempo songs; often the group's handclaps and snaps are the percussion.",
        form=(("intro (vocal)", 4), ("verse", 8), ("verse", 8), ("bridge", 8), ("verse", 8), ("sax solo", 8),
              ("bridge", 8), ("verse", 8), ("tag ending", 4)),
        instruments=("lead vocal", "background vocal group", "bass vocal", "piano (triplet chords)", "upright bass",
                     "drums", "tenor saxophone", "electric guitar"),
        sound_design="Vocal-forward: warm ribbon-mic voices in a room with echo-chamber reverb, triplet piano "
                     "chords, a honking tenor-sax break, simple clean guitar.",
        production="Mono, vocal-centric mixes; one or two microphones for the whole group; natural echo-chamber "
                   "reverb; band quiet underneath.",
        theory="The I-vi-IV-V loop with triplet subdivision defines the style; the vocal group replaces the band's "
               "harmonic role with close-voiced triads and the bass voice's arpeggios.",
        mix=Mix(lufs=(-15, -11), lra=(5, 10), low_end="light", tone="warm", width="narrow"),
    ),
    # -------------------------------------------------------- country and folk
    Genre(
        name="country",
        family="country and folk",
        aliases=("classic country", "country and western", "traditional country"),
        parent="folk",
        description="American country music: plain-spoken story songs over I-IV-V changes, twangy guitars, "
                    "fiddle and pedal steel, and a boom-chick two-beat or train-beat groove.",
        era="US South and Appalachia; Nashville from the 1940s; the Grand Ole Opry era to today's traditionalists",
        touchstones=("Hank Williams", "Patsy Cline", "Johnny Cash", "George Jones", "Loretta Lynn",
                     "Merle Haggard", "Dolly Parton", "George Strait", "Alan Jackson", "Chris Stapleton"),
        tempo=(75, 170),
        feel="boom-chick two-beat (bass on 1 and 3, strum on 2 and 4), train beat, or a shuffle; straight eighths",
        swing=50,
        modes=("major",),
        keys=("G major", "D major", "A major", "E major", "C major"),
        progressions=(
            "I-I-IV-IV-V7-V7-I-I",
            "I-IV-I-V7",
            "I-I-II7-II7-V7-V7-I-I",
            "I-I7-IV-IV-I-V7-I-I",
            "I-vi-IV-V7",
        ),
        harmonic_rhythm=1,
        harmony="Diatonic triads, mostly I, IV and V7, with the II7 (V7/V) secondary dominant as the signature "
                "colour, I7 leading to IV, occasional vi and the minor iv in ballads; chords change on strong bars "
                "and hold for 2-4 bars. Key changes up a half/whole step for the last chorus.",
        voicing="open",
        comping="strum",
        bass_style="root_fifth",
        bass="Root on 1, 5th on 3 (alternating bass), with diatonic walk-ups and walk-downs (e.g. 1-2-3 into IV, "
             "5-6-7 into I) between chord changes; electric bass or upright.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Conversational, narrative vocal in a comfortable range, syllabic setting, often pickup-led phrases "
               "ending on the tonic; major pentatonic with a b3-to-3 'cry' and yodel-like breaks; instrumental "
               "fills between vocal lines (steel, fiddle, Telecaster chicken-pickin' with double-stop bends).",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":  "x.......x.......",
            "snare": "ooooXoooooooXooo",
        }},
        drums="Train beat on snare with brushes or sticks (steady 16ths, accented 2 and 4), kick on 1 and 3; or a "
              "simple two-beat with cross-stick on 2 and 4; minimal fills; shuffle for honky-tonk numbers.",
        form=(("intro", 4), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("instrumental break", 8),
              ("chorus", 8), ("tag", 4)),
        instruments=("acoustic guitar", "Telecaster electric guitar", "pedal steel guitar", "fiddle",
                     "electric or upright bass", "drum kit", "piano", "vocals"),
        sound_design="Twangy Telecaster on the bridge pickup with compression and slapback, crying pedal steel "
                     "with volume-pedal swells, sweet fiddle, bright strummed dreadnought.",
        production="Vocal and lyrics upfront and dry-ish; tight Nashville session-player arrangements; "
                   "moderate compression; clean, warm, radio-ready but not crushed.",
        theory="Tonic-subdominant-dominant harmony with the II7 secondary dominant and bass walk-ups as hallmarks; "
               "melodies built on the major pentatonic with blue-note inflections borrowed from the blues.",
        mix=Mix(lufs=(-12, -9), lra=(5, 9), low_end="moderate", tone="warm", width="moderate"),
    ),
    Genre(
        name="honky-tonk",
        family="country and folk",
        aliases=("hard country", "honkytonk", "bakersfield sound"),
        parent="country",
        description="Barroom country: a shuffle or two-step for dancing, crying steel and fiddle, honky-tonk piano, "
                    "and songs about drinking, heartbreak and cheating.",
        era="Texas and Oklahoma dance halls, late 1940s-1950s; Bakersfield in the 1960s; neotraditional revival in the 1980s",
        touchstones=("Hank Williams", "Ernest Tubb", "Lefty Frizzell", "Ray Price", "George Jones", "Webb Pierce",
                     "Buck Owens", "Merle Haggard", "Dwight Yoakam"),
        tempo=(95, 180),
        feel="the 'Ray Price shuffle' (walking 4/4 bass under a shuffle) or a fast two-step",
        swing=62,
        modes=("major",),
        keys=("G major", "A major", "E major", "D major", "C major"),
        progressions=(
            "I-I-IV-IV-V7-V7-I-I",
            "I-I7-IV-IV-I-I-V7-V7",
            "I-I-II7-II7-V7-V7-I-I",
            "IV-IV-I-I-V7-V7-I-I",
        ),
        harmonic_rhythm=1,
        harmony="Three-chord country with the I7 into IV and II7 into V; choruses that start on the IV; simple "
                "major triads, 2-4 bars per chord, walk-ups in the bass; bluesy dominant 7ths on fiddle and piano.",
        voicing="open",
        comping="strum",
        bass_style="root_fifth",
        bass="Two-beat root-5th on 1 and 3, or a walking 4/4 line (the Ray Price shuffle) with diatonic walk-ups "
             "into each chord change.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Emotional, nasal vocal with sobs and catches (George Jones' vocal bends and dips), sung close to "
               "the beat; fills from steel guitar, fiddle double stops, and honky-tonk piano with grace-note slides "
               "(b3-3) between the vocal lines.",
        groove={"step": 1 / 3, "swing": 50, "pattern": {
            "kick":       "x.....x.....",
            "side stick": "...x.....x..",
            "closed hat": "x.xx.xx.xx.x",
        }},
        drums="Shuffle on snare or hi-hat with cross-stick backbeat on 2 and 4, kick on 1 and 3 (or no drums at "
              "all in early honky-tonk, with the rhythm guitar and upright providing the beat); quick two-step "
              "with snare on 2 and 4.",
        form=(("intro (steel or fiddle)", 4), ("verse", 16), ("chorus", 16), ("instrumental break", 16), ("verse", 16),
              ("chorus", 16), ("tag", 4)),
        instruments=("pedal steel guitar", "fiddle", "Telecaster electric guitar", "acoustic guitar",
                     "honky-tonk piano", "upright or electric bass", "drum kit", "vocals"),
        sound_design="Weeping pedal steel, double-stop fiddle, bright Telecaster through a Fender amp with "
                     "slapback (Bakersfield: Buck Owens' bright Tele twang), tack-piano honky-tonk sound.",
        production="Live-band feel, vocal-centred with slapback echo; mono or narrow in the classics; bright "
                   "top end; moderate compression.",
        theory="Diatonic three-chord harmony is carried by a danceable rhythm (shuffle or two-step) and expressive "
               "vocal ornaments rather than chord colour; the steel guitar adds sixth and ninth tensions over plain "
               "triads.",
        mix=Mix(lufs=(-13, -9), lra=(5, 9), low_end="moderate", tone="bright", width="moderate"),
    ),
    Genre(
        name="outlaw country",
        family="country and folk",
        aliases=("outlaw", "outlaw movement"),
        parent="honky-tonk",
        description="Country that rejected the Nashville polish: rawer, rock-edged band sound, a thumping beat, "
                    "phased Telecaster and long-haired, first-person songwriting.",
        era="Austin and Nashville, early-late 1970s; revived in the 2000s-2010s",
        touchstones=("Waylon Jennings", "Willie Nelson Red Headed Stranger", "Kris Kristofferson",
                     "Billy Joe Shaver", "David Allan Coe", "Jessi Colter", "Hank Williams Jr.",
                     "Sturgill Simpson", "Jamey Johnson"),
        tempo=(80, 160),
        feel="driving 'Waylon beat': kick on every quarter, snare on 2 and 4, straight eighths, slightly behind the beat",
        swing=52,
        modes=("major", "mixolydian"),
        keys=("E major", "A major", "G major", "D major"),
        progressions=(
            "I-IV-I-V",
            "I-bVII-IV-I",
            "I-I-IV-I-V-IV-I-I",
            "vi-IV-I-V",
            "I-V-IV-I",
        ),
        harmonic_rhythm=1,
        harmony="Three chords plus the mixolydian bVII from rock, IV-I endings, minor vi for moody ballads; few "
                "embellishments; long holds on the tonic for groove tunes.",
        voicing="open",
        comping="strum",
        bass_style="root_fifth",
        bass="Thumping root-5th or straight eighths on the root locked to the kick; electric bass with a pick "
             "and a dark tone; walk-downs at chord changes.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Laconic, deep-voiced, speech-like delivery, laid back of the beat (Willie's rubato phrasing); "
               "blues-tinged guitar fills with low-string twang; harmonica on Willie's records.",
        groove={"step": 0.25, "swing": 52, "pattern": {
            "kick":       "x...x...x...x...",
            "snare":      "....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.",
        }},
        drums="Simple and heavy: four-on-the-floor kick with a snare backbeat (Richie Albright), or brushes on "
              "Willie's sparse arrangements; no slick fills.",
        form=(("intro", 4), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("guitar solo", 8),
              ("chorus", 8), ("outro", 8)),
        instruments=("Telecaster with phaser", "acoustic guitar", "electric bass", "drum kit", "pedal steel",
                     "harmonica", "nylon-string guitar (Trigger)", "vocals"),
        sound_design="Waylon's black-and-white Telecaster through a phaser (MXR) and Fender amp, Willie's beat-up "
                     "nylon-string Martin, gritty bass, minimal strings or none.",
        production="Raw, band-in-a-room recordings, with less sweetening than Nashville Sound; vocal upfront, "
                   "drums dry and punchy; moderate compression.",
        theory="A deliberate simplification: rock-derived bVII and driving four-on-the-floor feel replace the "
               "Nashville Sound's strings and choirs; space and behind-the-beat phrasing define the style.",
        mix=Mix(lufs=(-12, -9), lra=(5, 9), low_end="moderate", tone="warm", width="moderate"),
    ),
    Genre(
        name="country pop",
        family="country and folk",
        aliases=("nashville sound", "countrypolitan", "pop country", "modern country"),
        parent="country",
        description="Country crossing over to pop: polished production, big choruses and pop progressions, from "
                    "the strings-and-choir Nashville Sound to today's radio country.",
        era="Nashville, late 1950s-60s (Nashville Sound, countrypolitan); 1990s crossover; 2010s radio country",
        touchstones=("Patsy Cline", "Glen Campbell", "Kenny Rogers", "Dolly Parton", "Shania Twain Come On Over",
                     "Faith Hill", "Taylor Swift Fearless", "Carrie Underwood", "Kacey Musgraves Golden Hour"),
        tempo=(70, 140),
        feel="straight eighths, pop backbeat; mid-tempo anthems and ballads",
        swing=50,
        modes=("major",),
        keys=("G major", "D major", "A major", "E major", "C major"),
        progressions=(
            "I-V-vi-IV",
            "vi-IV-I-V",
            "I-IV-vi-V",
            "IV-I-V-vi",
            "Iadd9-V-vi7-IVmaj7",
        ),
        harmonic_rhythm=1,
        harmony="Pop loops (I-V-vi-IV and rotations) with add9 and sus colours from open-string guitars; "
                "classic Nashville Sound adds strings, smooth vocal choirs and secondary dominants; bridges to "
                "the IV or vi; truck-driver modulation up a step for the last chorus.",
        voicing="open",
        comping="strum",
        bass_style="eighths",
        bass="Root-note eighths in the chorus, sparser root-5th in verses; modern productions blend electric bass "
             "with a sub or 808 layer under the kick.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Pop-structured hooks: a conversational verse, a pre-chorus lift and a high, repetitive chorus "
               "title hook; country inflections (a twang slide into the 3rd, yodel-ish flips); steel or fiddle "
               "doubling the hook.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.......x.x.....",
            "snare":      "....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.",
            "shaker":     "oxoxoxoxoxoxoxox",
        }},
        drums="Polished pop-rock drums with a big snare on 2 and 4, kick on 1 and 3 with pickups, 8th hats; "
              "modern country adds loops, claps, trap-style hats in places; Nashville Sound used brushes and "
              "light sticks.",
        form=(("intro", 4), ("verse", 16), ("pre-chorus", 4), ("chorus", 8), ("verse", 16), ("pre-chorus", 4),
              ("chorus", 8), ("bridge", 8), ("chorus", 16), ("outro", 4)),
        instruments=("acoustic guitar", "electric guitars", "pedal steel", "fiddle", "electric bass", "drum kit",
                     "piano", "strings", "banjo"),
        sound_design="Bright, layered acoustic strums, chimey clean and crunchy electrics, banjo as texture, "
                     "glossy steel, Nashville strings/choir in classic tracks, synth pads in modern ones.",
        production="Radio-polished: tight-tuned vocals, layered guitars, loud bright masters; country timbres sit "
                   "on a pop rhythm section.",
        theory="Pop's four-chord loops and verse/pre-chorus/chorus architecture dressed in country instruments "
               "and vocal inflection.",
        mix=Mix(lufs=(-10, -7), lra=(4, 7), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="western swing",
        family="country and folk",
        aliases=("texas swing",),
        parent="country",
        description="Texas dance-hall fusion of country fiddle music and big-band jazz: twin fiddles, steel "
                    "guitar and horns swinging over a two-beat or walking rhythm.",
        era="Texas and Oklahoma, 1930s-1940s; revival from the 1970s",
        touchstones=("Bob Wills and His Texas Playboys", "Milton Brown and His Musical Brownies", "Spade Cooley",
                     "Hank Thompson", "Asleep at the Wheel", "Merle Haggard"),
        tempo=(110, 220),
        feel="swing eighths over a two-beat or four-to-the-bar walking feel; danceable",
        swing=62,
        modes=("major",),
        keys=("G major", "D major", "A major", "C major", "F major"),
        progressions=(
            "I-VI7-II7-V7",
            "I-I7-IV-iv-I-VI7-II7-V7",
            "I7-IV7-I7-I7-IV7-#iv°7-I7-VI7-II7-V7-I7-V7",
            "I6/9-#i°7-ii7-V7",
            "III7-III7-VI7-VI7-II7-II7-V7-V7",
        ),
        harmonic_rhythm=1,
        harmony="Swing-era harmony in a country band: 6th and 9th chords, secondary-dominant chains "
                "(III7-VI7-II7-V7), passing diminished chords, minor iv, and jazz blues forms; fiddle tunes and "
                "pop standards alike.",
        voicing="drop2",
        comping="quarters",
        bass_style="walking",
        bass="Upright bass slapping a two-beat (root-5th on 1 and 3) on fiddle tunes, walking 4/4 on the swing "
             "numbers.",
        melody_density="busy",
        melody_scale="major blues",
        melody="Twin and triple fiddle harmony lines in 3rds and 6ths, hot fiddle breakdowns with double stops "
               "and slides, steel guitar jazz solos, crooned vocals with Bob Wills' hollered asides; swing-era "
               "riffs in the horns.",
        groove={"step": 0.5, "swing": 62, "pattern": {
            "kick":       "x...x...x...x...",
            "snare":      "..x...x...x...x.",
            "closed hat": "x.xxx.xxx.xxx.xx",
        }},
        drums="Light swing drumming: two-beat kick, brush or stick backbeat on 2 and 4, hi-hat swing pattern; "
              "fills from big-band style.",
        form=(("intro", 4), ("verse", 16), ("fiddle break", 16), ("vocal chorus", 16), ("steel solo", 16),
              ("horn/piano solo", 16), ("out chorus", 16), ("tag", 2)),
        instruments=("fiddles (twin)", "steel guitar (lap or pedal)", "electric guitar", "upright bass", "piano",
                     "drum kit", "trumpet and saxophone", "rhythm guitar"),
        sound_design="Sweet twin fiddles, early electric lap steel and archtop guitars with a clean tone, "
                     "slapped upright, swing-band horns; dance-hall ambience.",
        production="Natural live dance-band sound, fiddles and steel featured, moderate room, light compression.",
        theory="Applies jazz harmony and swing rhythm to string-band instrumentation; the twin-fiddle harmony is "
               "the arranging signature.",
        mix=Mix(lufs=(-15, -11), lra=(6, 11), low_end="light", tone="bright", width="moderate"),
    ),
    Genre(
        name="bluegrass",
        family="country and folk",
        aliases=("progressive bluegrass", "newgrass"),
        parent="folk",
        description="Fast, virtuosic acoustic string-band music: banjo rolls, mandolin chop, flatpicked guitar "
                    "and fiddle trading breaks over a driving boom-chick, with high lonesome harmony singing.",
        era="Kentucky and the Appalachians; Bill Monroe's Blue Grass Boys, mid 1940s; newgrass from the 1970s",
        touchstones=("Bill Monroe and his Blue Grass Boys", "Flatt & Scruggs", "The Stanley Brothers", "Doc Watson",
                     "J.D. Crowe", "Tony Rice", "Alison Krauss & Union Station", "Béla Fleck", "Del McCoury",
                     "Billy Strings"),
        tempo=(90, 180),
        feel="driving two-beat: here each beat is a boom-chick pair (bass on the beat, mandolin chop on the 'and'); banjo rolls in straight 16ths",
        swing=50,
        modes=("major", "mixolydian", "minor"),
        keys=("G major", "A major", "B major", "D major", "C major"),
        progressions=(
            "I-I-IV-I-I-V-I-I",
            "I-IV-I-V-I-IV-V-I",
            "I-VI7-II7-V7",
            "I-I-I-bVII-I-I-bVII-I",
            "minor: i-i-VII-VII-i-i-VII-i",
        ),
        harmonic_rhythm=1,
        harmony="Simple triads, I-IV-V with the II7 or VI7 in 'Salty Dog' type tunes, the mixolydian bVII in old-"
                "time fiddle tunes, modal minor (aeolian/dorian i-bVII) in mountain songs; chords played with "
                "capos in G, A, B; no 7ths except dominants.",
        voicing="open",
        comping="offbeat",
        bass_style="root_fifth",
        bass="Upright bass slapping root on one beat and 5th on the next, steady as a clock, with diatonic "
             "walk-ups (G-A-B into C) into chord changes; the guitar's 'G run' bass lick ending phrases.",
        melody_density="busy",
        melody_scale="major pentatonic",
        melody="High, tight vocal harmony (lead, tenor above, baritone below) with a nasal, 'high lonesome' tone; "
               "instrumental breaks in turn: Scruggs three-finger banjo rolls (forward, backward, alternating) "
               "outlining the chord with melody notes on the beat, crosspicked or flatpicked guitar runs, "
               "mandolin tremolo and blues-inflected Monroe licks, double-stop fiddle shuffles.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":  "o...o...o...o...",
            "snare": "..o...o...o...o.",
        }},
        drums="Traditionally no drums: the mandolin chop is the snare and the bass the kick. These lanes only mark "
              "the boom-chick; keep them silent or very soft (brush, cajón) in a modern band.",
        form=(("intro (kickoff break)", 8), ("verse", 16), ("chorus (trio harmony)", 16), ("banjo break", 16),
              ("verse", 16), ("chorus", 16), ("fiddle break", 16), ("chorus", 16), ("tag", 4)),
        instruments=("5-string banjo", "mandolin", "acoustic guitar (dreadnought)", "fiddle", "upright bass",
                     "dobro (resonator)", "vocals"),
        sound_design="All acoustic: bright, punchy banjo with resonator, woody mandolin chop, booming "
                     "dreadnought, sweet-to-gritty fiddle, slapped upright, singing dobro slides.",
        production="Recorded live around one or a few mics (or close-miked for clarity in newgrass); stereo "
                   "spread across instruments; little compression; natural acoustic tone.",
        theory="A rhythmic grid of interlocking acoustic roles (bass on the beat, chop on the offbeat, banjo "
               "16ths) sustains high tempos; the 'break' system rotates solos over the song's chords; Scruggs rolls "
               "are syncopated 3+3+2 groupings of 16ths.",
        mix=Mix(lufs=(-16, -11), lra=(6, 11), low_end="light", tone="bright", width="wide"),
    ),
    Genre(
        name="americana",
        family="country and folk",
        aliases=("alt-country", "alternative country", "roots music"),
        parent="country",
        description="Rootsy songwriter music mixing country, folk, blues, gospel and rock: organic band "
                    "sound, earthy vocals, and literate, often dark storytelling.",
        era="US, from Gram Parsons and The Band in the late 1960s; alt-country in the 1990s; an industry format since the 2000s",
        touchstones=("Gram Parsons", "The Band", "Emmylou Harris", "Lucinda Williams", "Uncle Tupelo", "Wilco",
                     "Gillian Welch", "Jason Isbell", "Brandi Carlile"),
        tempo=(70, 150),
        feel="laid-back, straight or lightly swung eighths; band breathing together",
        swing=52,
        modes=("major", "mixolydian"),
        keys=("G major", "D major", "A major", "E major", "C major"),
        progressions=(
            "I-IV-I-V",
            "I-vi-IV-I",
            "mixolydian: I-VII-IV-I",
            "vi-IV-I-V",
            "I-iii-vi-IV",
        ),
        harmonic_rhythm=1,
        harmony="Folk and country triads with add9/sus2 open-string colour, mixolydian bVII from rock and "
                "gospel-flavoured IV-I, occasional ii and iii; bass-note movement (I-I/7-vi) inside chords.",
        voicing="open",
        comping="strum",
        bass_style="root_fifth",
        bass="Supportive root-5th with walk-ups, electric or upright; lets the song lead; occasional melodic "
             "gospel-style fills.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Plain, characterful vocal with narrative lyrics, close two-part harmony (often a male/female duet), "
               "phrases that end on the 5th or 3rd, short instrumental hooks on fiddle, pedal steel, mandolin or "
               "slide guitar.",
        groove={"step": 0.25, "swing": 52, "pattern": {
            "kick":       "x.....x.x.......",
            "snare":      "....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.",
            "tambourine": "....x.......x...",
        }},
        drums="Played-in-the-room drums: brushes or sticks, soft backbeat, tambourine on 2 and 4, unhurried "
              "fills; sometimes only a kick and tambourine.",
        form=(("intro", 4), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("instrumental", 8),
              ("bridge", 8), ("chorus", 8), ("outro", 8)),
        instruments=("acoustic guitar", "electric guitar", "pedal steel", "fiddle", "mandolin", "upright or electric bass",
                     "drum kit", "Hammond organ", "vocals"),
        sound_design="Organic and vintage: small-bodied acoustics, Telecaster or Gretsch through small amps, "
                     "pedal steel pads, tube-mic'd vocals, room sound and tape warmth.",
        production="Recorded live where possible, analog warmth, natural reverb, vocals intimate and present; "
                   "moderate loudness with dynamics intact.",
        theory="Blends folk modality (bVII), country voice-leading (walk-ups, II7) and gospel cadences (IV-I) in "
               "song-first arrangements.",
        mix=Mix(lufs=(-14, -10), lra=(6, 10), low_end="moderate", tone="warm", width="wide"),
    ),
    Genre(
        name="folk",
        family="country and folk",
        aliases=("folk revival", "traditional folk", "american folk", "protest folk"),
        description="Song-centred acoustic music from oral tradition and the 1960s revival: voice and guitar "
                    "(or banjo), simple diatonic and modal harmony, and words that carry the song.",
        era="Anglo-American and African American traditions; the urban folk revival, late 1940s-1960s",
        touchstones=("Woody Guthrie", "Pete Seeger", "Lead Belly", "The Weavers", "Joan Baez", "Odetta",
                     "Bob Dylan The Freewheelin'", "Peter, Paul and Mary", "The Kingston Trio"),
        tempo=(70, 140),
        feel="straight, steady strum or fingerpicking; waltz time (3/4) common too",
        swing=50,
        modes=("major", "mixolydian", "dorian", "minor"),
        keys=("G major", "C major", "D major", "A minor", "E minor"),
        progressions=(
            "I-IV-I-V",
            "I-I-IV-I-I-I-V-I",
            "I-IV-V-I",
            "mixolydian: I-VII-IV-I",
            "dorian: i-VII-i-IV",
            "minor: i-VII-VI-VII",
        ),
        harmonic_rhythm=1,
        harmony="Three-chord diatonic harmony (I, IV, V) and modal ballads: mixolydian I-bVII, dorian i-IV (the "
                "major IV gives the Celtic/Appalachian colour), aeolian i-VII-VI; drones and capo'd open chords; "
                "harmony changes follow the verse lines.",
        voicing="open",
        comping="broken",
        bass_style="root_fifth",
        bass="The guitarist's thumb provides the bass: alternating root and 5th (Carter-family 'thumb-brush', or "
             "Travis picking with the thumb on beats 1-2-3-4 alternating strings) with bass runs between chords.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Strophic ballads and singalongs: many verses on one tune, stepwise pentatonic or modal melodies "
               "in a narrow range, syllabic text-setting, refrains for the audience to join; harmonica or banjo "
               "fills between verses.",
        groove={"step": 0.5, "swing": 50, "pattern": {
            "kick":       "x.x.x.x.",
            "tambourine": "..x...x.",
        }},
        drums="Usually none; foot stomps, a kick-drum pulse or tambourine at most.",
        form=(("intro", 4), ("verse", 16), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8),
              ("instrumental verse", 16), ("verse", 16), ("chorus", 8)),
        instruments=("acoustic guitar", "5-string banjo", "vocals", "harmonica", "upright bass", "autoharp",
                     "mandolin"),
        sound_design="Unprocessed acoustic tone: steel-string flat-top or 12-string, frailing banjo, rack "
                     "harmonica, plain unadorned voice, group singalong vocals.",
        production="Simple and live: one take, a couple of microphones, voice dominant; light compression and "
                   "natural room reverb.",
        theory="Modal and pentatonic melodies from oral tradition sit over minimal harmony; strophic form puts "
               "the lyric first. Travis picking (alternating-thumb bass with syncopated treble pinches) is the "
               "core fingerstyle technique.",
        mix=Mix(lufs=(-16, -12), lra=(6, 12), low_end="light", tone="warm", width="moderate"),
    ),
    Genre(
        name="singer-songwriter",
        family="country and folk",
        aliases=("acoustic", "acoustic singer-songwriter", "confessional songwriting"),
        parent="folk",
        description="Personal, lyric-driven songs performed by their writer, built around acoustic guitar or "
                    "piano and an intimate voice, with arrangements that serve the words.",
        era="US and UK, late 1960s-1970s (Laurel Canyon, Greenwich Village); thriving ever since",
        touchstones=("Joni Mitchell Blue", "James Taylor", "Carole King Tapestry", "Nick Drake", "Jackson Browne",
                     "Tracy Chapman", "Elliott Smith", "Damien Rice", "Bon Iver For Emma, Forever Ago",
                     "Phoebe Bridgers"),
        tempo=(70, 130),
        feel="straight, gentle; fingerpicked or softly strummed; rubato in places",
        swing=50,
        modes=("major", "minor", "mixolydian"),
        keys=("G major", "D major", "C major", "E major", "A minor"),
        progressions=(
            "I-V-vi-IV",
            "Iadd9-IVmaj7-vi7-Vsus4",
            "Imaj7-IVmaj7-Imaj7-IVmaj7",
            "vi-IV-I-V",
            "I-iii-IV-iv",
        ),
        harmonic_rhythm=1,
        harmony="Diatonic chords coloured by open-string extensions (add9, sus2, sus4, maj7), descending bass "
                "lines under a held chord (I-I/7-vi), borrowed minor iv for a bittersweet turn, alternate "
                "tunings (Joni's open tunings, DADGAD) that make unusual clusters; piano writers add ii-V and "
                "gospel inflections (Carole King).",
        voicing="open",
        comping="arpeggio_up",
        bass_style="root",
        bass="Often no bass player: the guitar's thumb or the piano's left hand carries the roots; in a band, "
             "a soft root-note bass with occasional passing tones and descending lines.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Conversational, intimate vocal close to the mic with natural breaks and falsetto; melodies follow "
               "speech rhythm, many words per phrase in the verse, a longer-note, higher chorus; lyric detail "
               "carries the song; doubled or harmonized vocal in the chorus.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":   "x.......x.......",
            "snare":  "....o.......o...",
            "shaker": "xoxoxoxoxoxoxoxo",
        }},
        drums="Minimal or none: brushes, a soft kick and shaker, or a cajón; full drums only in later choruses.",
        form=(("intro", 4), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("bridge", 8),
              ("chorus", 8), ("outro", 4)),
        instruments=("acoustic guitar", "piano", "vocals", "upright or electric bass", "cello or strings",
                     "brushed drums", "harmonica"),
        sound_design="Close-miked acoustic guitar with string and finger noise, felt or upright piano, a warm "
                     "large-diaphragm vocal; sparse strings or pads for lift.",
        production="Intimate and dry-to-roomy; voice upfront with gentle compression; room for breath and "
                   "dynamics; acoustic guitar spread with two mics.",
        theory="Harmony serves the lyric: diatonic progressions enriched with add9/sus colour, inversions and "
               "pedal tones; Travis-style fingerpicking and alternate tunings give each writer a signature texture.",
        mix=Mix(lufs=(-16, -11), lra=(6, 12), low_end="light", tone="warm", width="moderate"),
    ),
]
