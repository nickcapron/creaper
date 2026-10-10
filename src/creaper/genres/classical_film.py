"""Classical, film, game and stage music: concert-hall eras, screen scoring, game audio and musical theatre."""

from . import Genre, Mix

GENRES = [
    # ------------------------------------------------------------------ classical
    Genre(
        name="classical",
        family="classical",
        aliases=("orchestra", "chamber", "orchestral classical", "classical music", "chamber music", "symphony"),
        description="Western concert music of the common-practice era and its orchestral and chamber descendants: "
                    "functional harmony, developed themes and a huge dynamic range, played by acoustic instruments "
                    "in a real hall.",
        era="Europe, c.1600-1910 (the common-practice period); still the concert-hall mainstream",
        touchstones=("J.S. Bach", "Mozart", "Beethoven", "Brahms", "Tchaikovsky", "Dvorak Symphony No. 9"),
        tempo=(40, 180),
        feel="Steady pulse shaped by rubato at phrase ends; tempo terms: Largo (40-60), Adagio (66-76), Andante "
             "(76-108), Moderato (108-120), Allegro (120-156), Presto (168+)",
        swing=50,
        modes=("major", "minor", "harmonic minor"),
        keys=("C major", "D major", "Eb major", "A major", "G minor", "D minor"),
        progressions=(
            "I-IV-V7-I",
            "I-ii6-Cad64-V7-I",
            "I-vi-IV-V7-vi",
            "I-V7/V-V-V7-I",
            "minor: i-iv6-V",
            "minor: i-VI-Ger+6-Cad64-V-i",
        ),
        harmonic_rhythm=1,
        harmony="Functional tonic-predominant-dominant motion: IV or ii6 to V(7) to I, a cadential 6/4 before "
                "strong cadences, secondary dominants and leading-tone sevenths (V7/V, vii°7/V) to tonicise, and "
                "modulation to the dominant (major keys) or relative major (minor keys) for the second key area. "
                "Antecedent phrases end on a half cadence, consequents on a perfect authentic cadence; deceptive "
                "V-vi cadences extend a phrase, the Phrygian half cadence (iv6-V) closes slow minor-key sections.",
        voicing="open",
        comping="sustain",
        bass_style="root",
        bass="Cellos with basses an octave below: roots at cadences, first inversions (I6, ii6, IV6) elsewhere so "
             "the line moves by step; contrary motion against the melody, no parallel 5ths or octaves with the "
             "soprano; tonic pedals in codas and dominant pedals in retransitions.",
        melody_density="medium",
        melody_scale="major",
        melody="Themes are periods (4-bar antecedent to a HC, 4-bar consequent to a PAC) or sentences (2-bar basic "
               "idea, its repetition, 4-bar continuation to the cadence). Mostly stepwise, leaps recovered by step "
               "in the opposite direction, one climax about two-thirds through, developed by sequence, inversion "
               "and fragmentation; first violins, flute or oboe carry it within about a 10th.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "low floor tom": "X.......x.......x...x...X.......",
            "floor tom":     "........................x...x...",
        }},
        drums="Timpani, usually a pair tuned to tonic and dominant, reinforce cadences, tutti accents and dominant "
              "pedals with rolls; cymbals, bass drum and triangle are colours for climaxes or 'Turkish' passages, "
              "never a steady beat. Map the tonic timpano to low floor tom and the dominant drum to floor tom.",
        form=(("exposition: first theme", 16), ("transition", 12), ("second theme (new key)", 20),
              ("closing section", 8), ("development", 40), ("recapitulation: first theme", 16),
              ("transition (stays in tonic)", 10), ("second theme (tonic)", 20), ("coda", 16)),
        instruments=("strings (violins I and II, violas, cellos, basses)", "flutes", "oboes", "clarinets",
                     "bassoons", "French horns", "trumpets", "timpani", "piano"),
        sound_design="Full strings with legato for melody, detache/spiccato for accompaniment figures, tremolo for "
                     "agitation and pizzicato basses; winds in pairs doubling at the octave, horns sustaining the "
                     "middle. In libraries (BBC Symphony Orchestra, VSL, Cinematic Studio Strings) use true-legato "
                     "patches and keyswitched articulations, one track per section, and divisi patches for chords "
                     "instead of stacking a full section on every note.",
        production="Hall first: one shared hall reverb (RT60 2.0-2.8 s) over a Decca-tree-style blend, panned by "
                   "seating (violins I left, violas and cellos centre-right, basses right, woodwinds centre "
                   "behind, horns left rear, brass and timpani rear). Ride CC1 (dynamic layer) and CC11 "
                   "(expression) on every sustained line; no bus limiting, only peak safety, so pp passages sit "
                   "around -40 LUFS short-term and tutti ff near -12.",
        theory="Tonality as narrative: departure from the tonic, conflict in a second key, return. Voice-leading "
               "rules (leading tone up, chordal 7th down, no parallel perfect intervals) and the cadence hierarchy "
               "(PAC > IAC > HC) give the punctuation that makes long forms intelligible.",
        mix=Mix(lufs=(-24, -16), lra=(10, 20), low_end="light", tone="neutral", width="wide"),
    ),
    Genre(
        name="baroque",
        family="classical",
        aliases=("baroque music", "baroque era", "baroque concerto", "figured bass"),
        parent="classical",
        description="Music of the figured-bass age: a driving continuo line under motoric counterpoint, terraced "
                    "dynamics, sequences and ornamented melody, from Monteverdi to Bach and Handel.",
        era="Italy, Germany, France and England, c.1600-1750",
        touchstones=("J.S. Bach", "Handel", "Vivaldi", "Corelli", "Telemann", "Purcell", "Brandenburg Concertos"),
        tempo=(50, 140),
        feel="Motoric, unbroken 8th or 16th pulse (Allegro, Vivace, Presto) or stately dotted rhythms (French "
             "overture, Grave); dance characters: allemande, courante, sarabande, gigue; little rubato",
        swing=50,
        modes=("major", "minor", "harmonic minor"),
        keys=("D major", "C major", "F major", "G minor", "A minor", "B minor"),
        progressions=(
            "I-IV-vii°-iii-vi-ii-V-I",
            "minor: i-v6-iv6-V",
            "I-V-vi-iii-IV-I-IV-V",
            "I-V6-vi-iii6-IV-I6-ii6-V",
            "minor: i-iv7-VII7-IIImaj7-VImaj7-iiø7-V7-i",
        ),
        harmonic_rhythm=2,
        harmony="Figured-bass thinking: chords are intervals over the bass (6 = first inversion, 6/4, 7, 4-3) "
                "realised by harpsichord or organ. Sequences drive every middle section (descending fifths with "
                "7ths, ascending 5-6), 4-3 and 7-6 suspensions decorate cadences, the lament bass (descending "
                "tetrachord 1-b7-b6-5) and Phrygian half cadence (iv6-V) end slow minor movements, and a Picardy "
                "third closes minor-key works on a major tonic.",
        voicing="close",
        comping="quarters",
        bass_style="walking",
        bass="The continuo line (cello, bassoon or gamba with harpsichord or organ) is the engine: steady walking "
             "8ths or running 16ths, octave leaps, stepwise descending tetrachords, a dominant pedal before the "
             "final cadence; it is a real melody that often imitates the upper voices.",
        melody_density="busy",
        melody_scale="major",
        melody="Fortspinnung: a short head motif, spun out by sequence, then a cadential close. Busy 16th-note "
               "figuration, compound melody implying two voices, trills on cadential notes, mordents and "
               "appoggiaturas, improvised embellishment of repeats; in fugues a subject answered at the 5th "
               "(real or tonal answer) with countersubjects in invertible counterpoint.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "low floor tom": "X.......X.x.x...",
            "floor tom":     "....x.......X...",
        }},
        drums="No kit: the continuo is the rhythm section. In festive D-major works (Handel's Music for the Royal "
              "Fireworks, Bach's cantatas) timpani on tonic and dominant play with the natural trumpets, in short "
              "dotted figures and cadential rolls; map them to low floor tom (D) and floor tom (A).",
        form=(("ritornello (tonic)", 12), ("solo episode 1", 8), ("ritornello (dominant)", 6),
              ("solo episode 2 (sequences)", 12), ("ritornello (relative minor)", 6), ("solo episode 3", 10),
              ("ritornello (tonic)", 12)),
        instruments=("harpsichord", "chamber or church organ", "baroque strings (gut)", "cello and violone (continuo)",
                     "oboes", "natural trumpets", "recorder or traverso", "theorbo", "timpani"),
        sound_design="Small forces: 4-4-3-2-1 strings or one per part, gut strings with sparing vibrato and shaped "
                     "messa di voce bow strokes; harpsichord (8' and 4' registers) or chamber organ continuo, "
                     "theorbo for colour. In libraries use short-bow/detache and non-vibrato legato patches; oboes "
                     "double violins in tuttis, trumpets play high clarino lines, and A=415 tuning is optional.",
        production="Chamber room (about 1.2 s) or church (1.6-2.2 s); harpsichord centre and slightly back, audible "
                   "but not dominant, continuo cello beside it. Terraced dynamics (forte/piano by section, echo "
                   "effects) mean CC1 moves in blocks rather than long swells; keep harpsichord transients crisp "
                   "and barely compress.",
        theory="Counterpoint and figured bass are the pillars: every voice is a melody, dissonance is prepared "
               "and resolved (suspension: preparation, dissonance, resolution down by step), and harmony grows "
               "from the bass. One movement keeps one affect and one rhythmic motor, unlike Classical contrast.",
        mix=Mix(lufs=(-22, -15), lra=(8, 15), low_end="light", tone="warm", width="moderate"),
    ),
    Genre(
        name="classical period",
        family="classical",
        aliases=("classical era", "viennese classical", "classicism", "galant style"),
        parent="classical",
        description="The Viennese Classical style of Haydn, Mozart and early Beethoven: clear melody over light "
                    "accompaniment, periodic 4- and 8-bar phrases, balanced cadences and sonata-form drama.",
        era="Vienna and Mannheim, c.1750-1820",
        touchstones=("Haydn", "Mozart", "early Beethoven", "Clementi", "Mozart Piano Sonata K. 545",
                     "Haydn London Symphonies"),
        tempo=(60, 168),
        feel="Clear, even pulse and articulate phrasing: Allegro con brio, Andante, Menuetto (Allegretto in 3/4), "
             "Rondo Allegro; rubato only at fermatas and cadenzas",
        swing=50,
        modes=("major", "minor"),
        keys=("C major", "G major", "D major", "F major", "Bb major", "D minor"),
        progressions=(
            "I-ii6-Cad64-V7-I",
            "I-V43-I6-IV-V",
            "I-IV-V7/V-V",
            "I-vi-IV-ii6-V7-vi",
            "minor: i-V7/III-III-iv-V7-i",
        ),
        harmonic_rhythm=1,
        harmony="Diatonic and functional with a slow, clear harmonic rhythm: I, IV, V and ii6 do most of the work, "
                "V7/V sets up half cadences and the medial caesura, the cadential 6/4 precedes every PAC, and the "
                "Neapolitan or an augmented sixth appears in minor-key and development passages. Expositions "
                "modulate to V (major) or III (minor); a dominant pedal retransition prepares the recapitulation.",
        voicing="close",
        comping="alberti",
        bass_style="alberti",
        bass="Keyboard left hand plays Alberti bass (low-high-middle-high 16ths, C-G-E-G) or drum bass (repeated "
             "8ths) under the tune; in orchestras cellos and basses play repeated-8th roots with violas filling. "
             "The bass takes first inversions for stepwise lines and lands on 5 for half cadences.",
        melody_density="medium",
        melody_scale="major",
        melody="Singable and symmetrical, decorated with appoggiaturas, turns and grace notes: periods (antecedent "
               "to HC, consequent to PAC) or sentences (presentation 2+2, continuation 4 with fragmentation and "
               "faster harmonic rhythm). Second themes are lyrical; Sturm und Drang minor themes use leaps and "
               "syncopation; right-hand range up to about C6.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "low floor tom": "X.......x.......",
            "floor tom":     "....x.......x...",
        }},
        drums="Timpani in C-G or D-A pairs play with trumpets in tuttis, marking downbeats, cadences and the "
              "closing hammer-stroke chords; bass drum, cymbals and triangle appear only for alla turca colour "
              "(Mozart's Abduction from the Seraglio, Haydn's Military Symphony).",
        form=(("exposition: primary theme", 8), ("transition (to HC in V)", 8), ("secondary theme", 16),
              ("closing theme", 8), ("exposition repeat", 40), ("development", 32),
              ("retransition (dominant pedal)", 8), ("recapitulation", 40), ("coda", 8)),
        instruments=("fortepiano or piano", "string quartet", "flutes", "oboes", "clarinets", "bassoons",
                     "natural horns", "trumpets", "timpani"),
        sound_design="Lean orchestra (strings about 8-6-4-4-2, pairs of winds, two horns): violins take the tune, "
                     "second violins and violas play repeated-note accompaniment, winds sustain and colour, horns "
                     "hold pedals. Fortepiano has light, quick decay; in libraries use short detache/staccato for "
                     "accompaniment, light-vibrato legato and a lighter piano with sparing sustain pedal.",
        production="Smaller hall (1.6-2.2 s) for clarity over grandeur: melody forward, Alberti or repeated-note "
                   "accompaniment 4-6 dB under it. Dynamics p to f with sfz accents and Mannheim crescendos; ride "
                   "CC1/CC11 in 2-4 bar swells, keep transients crisp, nothing beyond peak-safety limiting.",
        theory="Periodicity and contrast: harmony is simple so that phrase structure, cadence types and key "
               "relations articulate the form. Signposts (medial caesura, essential expositional closure, "
               "retransition on V) guide the listener; surprises come from irregular phrase lengths and sudden "
               "dynamics (Haydn).",
        mix=Mix(lufs=(-23, -16), lra=(9, 16), low_end="light", tone="neutral", width="wide"),
    ),
    Genre(
        name="romantic",
        family="classical",
        aliases=("romantic era", "romanticism", "late romantic", "romantic orchestral"),
        parent="classical",
        description="19th-century expressive music: singing melodies, rich chromatic harmony, distant modulations "
                    "and huge dynamic arcs, from Schubert and Chopin to Wagner, Tchaikovsky and Mahler.",
        era="Europe, c.1820-1910",
        touchstones=("Chopin", "Schumann", "Brahms", "Tchaikovsky", "Wagner Tristan und Isolde", "Mahler",
                     "Rachmaninoff Piano Concerto No. 2"),
        tempo=(40, 160),
        feel="Flexible pulse with expressive rubato: accelerando into climaxes, ritardando at cadences; Adagio, "
             "Andante cantabile, Allegro appassionato; long-breathed phrasing",
        swing=50,
        modes=("major", "minor", "harmonic minor"),
        keys=("Db major", "Ab major", "E major", "C# minor", "F minor", "Bb minor"),
        progressions=(
            "I-bVI-iv-V7-I",
            "I-III-IV-iv-I",
            "minor: i-N6-vii°7/V-V7-i",
            "minor: i-VI-Ger+6-Cad64-V7-i",
            "I-vi-ii65-vii°7/V-Cad64-V7-I",
            "I-V7/vi-vi-V7/IV-IV-iv-I",
        ),
        harmonic_rhythm=1,
        harmony="Functional tonality stretched by chromaticism: mixture (iv, bVI, bIII borrowed into major), the "
                "Neapolitan and augmented sixths as predominants, diminished sevenths as pivots to distant keys, "
                "chromatic-mediant modulations (to bVI or III), enharmonic reinterpretation (a Ger+6 respelled as "
                "the V7 of a new key), and delayed resolution (the Tristan chord, appoggiatura chords, evaded "
                "cadences) before the final PAC.",
        voicing="spread",
        comping="broken",
        bass_style="arpeggio",
        bass="Wide left-hand arpeggios spanning a 10th or more (nocturne style: root, 5th, 10th) held with the "
             "pedal; orchestral basses in long lines with chromatic passing tones, descending chromatic lament "
             "basses and pedal points under swelling harmony.",
        melody_density="medium",
        melody_scale="major",
        melody="Long, vocal cantabile lines (bel canto influence): leaps of a 6th or 7th resolved by step, "
               "expressive appoggiaturas on strong beats, chromatic neighbour notes, climaxes prepared over 8-16 "
               "bars; thematic transformation (Liszt, Berlioz's idée fixe) and octave doubling (violins plus "
               "cellos) at the climax.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "low floor tom": "X...............x.x.x.xxxxxxxxxx",
            "kick":          "X...............................",
            "crash":         "X...............................",
        }},
        drums="Expanded percussion for drama, never a groove: three or four timpani with rolls building into "
              "climaxes, bass drum and clashed cymbals on climactic downbeats, tam-tam for tragedy (Tchaikovsky "
              "6), triangle and glockenspiel for sparkle. Timpani on low floor tom, bass drum on kick, cymbals on "
              "crash.",
        form=(("introduction", 4), ("A: main theme", 16), ("A: varied", 16), ("B: contrasting key (bVI or relative)", 24),
              ("retransition", 8), ("A': ornamented return", 16), ("coda", 8)),
        instruments=("piano", "full strings", "French horns (4)", "woodwinds in pairs or threes", "English horn",
                     "trombones and tuba", "harp", "timpani", "cymbals and bass drum"),
        sound_design="Lush strings with full vibrato and portamento between melody notes, cellos singing in their "
                     "tenor register, four horns for warmth, harp arpeggios, woodwind solos (clarinet, English "
                     "horn). In libraries use expressive legato with portamento crossfades, divisi strings for "
                     "rich chords, marcato layered under longs for accents, and a concert grand with pedal "
                     "resonance for piano works.",
        production="Large concert hall (2.2-3 s), warm and full: tame 2-4 kHz edge on violins, a little body at "
                   "200-300 Hz, wide stage. Long CC1/CC11 arcs over whole phrases (pp to fff) and a rubato tempo "
                   "map instead of grid playback; let the climax sit 15-20 LU above the quietest passage.",
        theory="Expression through delay: deceptive cadences, chromatic appoggiaturas and suspensions postpone "
               "resolution, keys relate by thirds as often as by fifths, and the dominant can be withheld for "
               "pages. Mixture and third relations colour the emotional arc of a whole work.",
        mix=Mix(lufs=(-24, -16), lra=(12, 20), low_end="moderate", tone="warm", width="wide"),
    ),
    Genre(
        name="impressionism",
        family="classical",
        aliases=("impressionist", "french impressionism", "impressionist music"),
        parent="romantic",
        description="Fin-de-siècle French music of colour and atmosphere: planed parallel chords, whole-tone and "
                    "pentatonic scales, modal melody and blurred, pedalled textures that evoke rather than argue.",
        era="France, c.1890-1925",
        touchstones=("Debussy", "Ravel", "Debussy Prélude à l'après-midi d'un faune", "Ravel Daphnis et Chloé",
                     "Satie", "Lili Boulanger"),
        tempo=(40, 120),
        feel="Floating and metrically blurred: Lent, Modéré, Très calme, Doux et expressif; ties across barlines "
             "and duplet/triplet mixtures hide the downbeat",
        swing=50,
        modes=("lydian", "major", "dorian", "whole tone"),
        keys=("Db major", "F# major", "E major", "C lydian", "A dorian"),
        progressions=(
            "Imaj7-II7-Imaj7-II7",
            "major: Imaj7-ii7-iii7-IVmaj7-iii7-ii7",
            "major: I9-bVII9-bVI9-bVII9",
            "major: I+-II+-bVII+-I+",
            "dorian: i7-IV9-i7-IV9",
        ),
        harmonic_rhythm=1,
        harmony="Chords as colour, not function: unresolved 7ths and 9ths, planing (diatonic or exact chromatic "
                "parallel chords moving with the melody), added 6ths and 9ths, quartal stacks, whole-tone "
                "augmented triads and pentatonic fields over long pedals. Dominants rarely resolve; modal cadences "
                "(bVII-I, plagal, lydian II-I) replace V-I, and a section may sit on one sonority for many bars.",
        voicing="spread",
        comping="arpeggio_updown",
        bass_style="pedal",
        bass="Long pedal points and low sustained octaves held through changing harmony with the damper pedal, "
             "slow whole-step descents, two-note ostinatos; the bass rarely moves by functional 5ths.",
        melody_density="sparse",
        melody_scale="major pentatonic",
        melody="Arabesque lines (flute, oboe, English horn) curling around a few notes, pentatonic or modal, "
               "ending on the 2nd, 6th or 9th rather than the tonic; short motifs repeated over changing harmony, "
               "ornate grace notes and triplets, phrases that dissolve instead of cadencing; range a 6th to an "
               "octave, dynamics rarely above mf.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "crash":    "x...............................",
            "triangle": "........x...............x.......",
        }},
        drums="Percussion as shimmer: suspended cymbal with soft mallets (swells), crotales/antique cymbals, "
              "triangle, harp glissandi, celesta and glockenspiel; soft timpani rolls on pedal points. Nothing "
              "marks a beat; map cymbal swells to crash with low velocities (30-60).",
        form=(("introduction (pedal and motif)", 8), ("A", 16), ("B (new mode or whole-tone)", 16), ("climax", 8),
              ("A' (fragmented)", 12), ("coda (dissolving)", 6)),
        instruments=("piano (with pedal)", "harp", "flute", "oboe and English horn", "muted strings (divisi)",
                     "clarinet", "muted horns", "celesta", "crotales and suspended cymbal"),
        sound_design="Muted strings (con sordino) in many divisi parts, harmonics, sul tasto and flautando bowing, "
                     "tremolo sul ponticello for shimmer; harp glissandi and harmonics, celesta and glockenspiel "
                     "an octave above flute lines, muted horns and solo woodwinds on top. In libraries use con "
                     "sordino/flautando patches, harp gliss tuned to a whole-tone or pentatonic set, and a softly "
                     "voiced piano with sustain pedal and una corda.",
        production="Soft focus: a long, diffuse hall (2.5-3.5 s), air rather than presence peak, instruments a "
                   "little further back so reverb carries the sustain. Dynamics hover pp-mf, so CC1 stays low "
                   "(20-70); no bus compression; piano pedal resonance and sympathetic ring are part of the sound.",
        theory="Non-functional harmony: chords are sonorities joined by parallel motion, common tones and "
               "symmetrical collections (whole-tone, octatonic, pentatonic) instead of dominant pull. Form comes "
               "from texture and colour changes, and stasis over pedals replaces goal-directed progression.",
        mix=Mix(lufs=(-26, -18), lra=(12, 20), low_end="light", tone="warm", width="wide"),
    ),
    Genre(
        name="minimalism",
        family="classical",
        aliases=("minimalist", "minimalist classical", "process music", "postminimalism"),
        parent="contemporary classical",
        description="Pulse-based process music: short diatonic cells repeated, layered and shifted by additive "
                    "rhythm, phasing and slow harmonic change, creating hypnotic, gradually transforming textures.",
        era="New York and San Francisco, 1960s-1980s; postminimalism since",
        touchstones=("Steve Reich Music for 18 Musicians", "Philip Glass Einstein on the Beach", "Terry Riley In C",
                     "John Adams Shaker Loops", "Arvo Pärt", "Michael Nyman"),
        tempo=(60, 190),
        feel="Steady, unchanging pulse of 8ths or 16ths; additive groupings (3+3+2, 1, 1+2, 1+2+3) and "
             "phase-shifted loops; no rubato, change only through process",
        swing=50,
        modes=("minor", "major", "dorian", "mixolydian"),
        keys=("A minor", "E minor", "C major", "D major", "F major"),
        progressions=(
            "i-VI-i-VI",
            "i-VI-iv-V",
            "i-VI-III-VII",
            "major: I-V6-vi-iii6-IV-I6-IV-V",
        ),
        harmonic_rhythm=0.5,
        harmony="Diatonic, consonant and slow-changing: one chord or a two-chord oscillation held for 4-32 bars, "
                "pulsing chord cycles (Reich's eleven-chord cycle in Music for 18 Musicians), added 2nds and "
                "suspensions, relative major/minor ambiguity. Change happens one note at a time, or by moving the "
                "bass under a fixed pattern so the same notes take a new function.",
        voicing="close",
        comping="arpeggio_updown",
        bass_style="whole",
        bass="Long sustained roots or repeated 8th-note pulses on the root (bass clarinet, synth bass, piano left "
             "hand) that change only with the harmonic cycle; Glass reharmonises a constant arpeggio by moving "
             "the bass, Pärt holds drones.",
        melody_density="busy",
        melody_scale="minor",
        melody="Cells, not tunes: 3-8 note figures repeated dozens of times and transformed by additive process "
               "(adding or removing one note per cycle), phasing (two identical loops, one drifting ahead), "
               "augmentation, and resultant patterns that emerge between layers. Pärt's tintinnabuli pairs a "
               "stepwise melodic voice with a voice that only sounds the tonic triad.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "claves":        "x.x.x.x.x.x.x.x.",
            "low woodblock": "x..x..x.x..x..x.",
        }},
        drums="Usually no drums: pulse comes from marimbas, pianos, clapping (Reich's Clapping Music), mallets "
              "and pulsing voices. Unpitched percussion, when used, is claves or woodblocks playing additive "
              "3+3+2 patterns against a steady 8th pulse.",
        form=(("pulse established", 8), ("cell A (additive build)", 32), ("phase / new layer", 32),
              ("chord change (next step of the cycle)", 32), ("full texture", 32), ("subtraction", 16),
              ("pulse alone", 8)),
        instruments=("marimbas", "pianos", "vibraphone", "electric organ", "string ensemble", "bass clarinet",
                     "wordless voices", "soprano saxophone"),
        sound_design="Clean, transient-rich mallets (marimba, vibraphone with motor off), several pianos, "
                     "Farfisa/Yamaha-style organs (the Glass ensemble), sustained clarinets and wordless voices "
                     "breathing the harmony. Program cells as exactly quantised MIDI loops, duplicate the track "
                     "and nudge one copy a 16th per section (or run it at a fractionally faster tempo) to fake "
                     "phasing; accents come from velocity patterns, not humanising.",
        production="Clear and even: each layer on its own pan position so interlocking parts stay audible, medium "
                   "room (1.2-1.8 s) so fast pulses don't smear. Dynamics move by adding and removing layers and "
                   "slow CC11 crescendos over whole sections; light compression on mallets is fine.",
        theory="Gradual process as form: change is audible because everything else stays constant. Additive "
               "rhythm, phase shifting and resultant patterns are rhythmic counterpoint, while static or cyclic "
               "harmony makes a single new bass note feel like a modulation.",
        mix=Mix(lufs=(-22, -15), lra=(6, 12), low_end="light", tone="neutral", width="wide"),
    ),
    Genre(
        name="contemporary classical",
        family="classical",
        aliases=("avant-garde classical", "new music", "atonal", "serialism", "twelve-tone", "spectral music",
                 "20th century classical"),
        parent="classical",
        description="Post-tonal concert music: serial and atonal pitch organisation, clusters, extended "
                    "techniques, spectral and textural writing, from Darmstadt modernism to today's eclectic "
                    "composers.",
        era="Europe and the Americas, 1910s-present (the post-1945 avant-garde especially)",
        touchstones=("Schoenberg", "Webern", "Ligeti Atmosphères", "Penderecki Threnody to the Victims of Hiroshima",
                     "Messiaen", "Gérard Grisey", "Kaija Saariaho"),
        tempo=(40, 160),
        feel="Often unmetered or constantly changing metre (5/8, 7/8, mixed bars), proportional notation and "
             "gesture-led timing; time felt as texture rather than beat",
        swing=50,
        modes=("major", "diminished half-whole", "whole tone", "chromatic"),
        keys=("C major", "C# minor"),
        progressions=(
            "I-bIII-#IV-VI",
            "I-#IV-I-#IV",
            "I-iii-III-bvi-bVI-i-I",
            "Iquartal-IIquartal-bIIIquartal-IVquartal",
        ),
        harmonic_rhythm=0.5,
        harmony="Pitch organisation replaces chord progression: twelve-tone rows (prime, inversion, retrograde, "
                "retrograde-inversion), pitch-class sets, symmetrical modes (octatonic, whole-tone, Messiaen's "
                "modes of limited transposition: the octatonic holds major triads a minor third apart, I-bIII-#IV-"
                "VI), quartal stacks, semitone clusters, polychords (C over F#), the hexatonic cycle of alternating "
                "major and minor triads, and spectral chords built on a low fundamental's overtones.",
        voicing="cluster",
        comping="sustain",
        bass_style="pedal",
        bass="Rarely a functional bass: low drones and pedal fundamentals (spectral music builds the chord on "
             "them), registral extremes (contrabass harmonics, contrabassoon), isolated pointillistic attacks; "
             "often the bass function is simply absent.",
        melody_density="sparse",
        melody_scale="chromatic",
        melody="Angular lines with leaps of 7ths, 9ths and tritones, rows unfolded across registers, Webern-style "
               "pointillism and Klangfarbenmelodie (one or two notes per instrument), Ligeti's micropolyphony "
               "(many tiny canons fused into a texture), glissandi and microtones; gesture and texture matter "
               "more than tune.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "high woodblock": "x..x...x.x...x..",
            "low tom":        ".....x.....x....",
            "low floor tom":  "X.......x.......",
        }},
        drums="Large, varied percussion for colour and gesture, not metre: tam-tam and bowed cymbals, temple "
              "blocks, log drums, tom-toms, marimba and vibraphone, thunder sheet; irregular attacks, Messiaen's "
              "added values and non-retrogradable rhythms, Stravinsky's asymmetric accents. Temple blocks map to "
              "woodblock lanes, tom-toms to the tom lanes.",
        form=(("opening gesture / sonority", 6), ("texture A", 20), ("density build", 12), ("climax (tutti cluster)", 8),
              ("texture B (sparse)", 16), ("coda (decay to niente)", 8)),
        instruments=("string orchestra (divisi)", "prepared piano", "percussion ensemble", "flute",
                     "bass clarinet", "contrabassoon", "live electronics", "voice"),
        sound_design="Extended techniques: col legno, sul ponticello, sul tasto, overpressure scratch tone, "
                     "harmonics, quarter-tone glissandi, flutter-tongue, multiphonics, key clicks, prepared piano "
                     "(bolts, felt, rubber). In libraries use aleatoric and texture patches (Spitfire LCO and "
                     "Albion Tundra textures, 8Dio Aleatoric toolkits), solo players rather than sections for "
                     "pointillism, and live electronics (granular delay, spectral freeze) as instruments.",
        production="Transparent and detailed: spot mics close enough for bow noise and key clicks, natural hall "
                   "(2-2.5 s), huge dynamic range (ppppp to fff) with nothing compressed. Pan players "
                   "individually so pointillistic lines move in space; automate CC1/CC11 for hairpins from niente "
                   "and tiny dynamic gestures.",
        theory="Equality of the twelve pitch classes (no tonic), structure from rows, sets, symmetries and "
               "processes; timbre, register and density become structural parameters equal to pitch. Spectralism "
               "derives harmony from acoustics, and many living composers reintroduce tonal and modal material "
               "freely.",
        mix=Mix(lufs=(-26, -18), lra=(14, 22), low_end="light", tone="neutral", width="wide"),
    ),
    Genre(
        name="choral",
        family="classical",
        aliases=("choir", "choral music", "chorale", "sacred choral", "motet"),
        parent="classical",
        description="Music for choir, a cappella or accompanied: four-part chorale harmony, imitative polyphony and "
                    "lush close-harmony writing, from Renaissance motets and Bach chorales to Rachmaninoff, "
                    "Lauridsen and Whitacre.",
        era="Western sacred and secular tradition, c.1500-present",
        touchstones=("Palestrina", "J.S. Bach chorales", "Mozart Requiem", "Fauré Requiem",
                     "Rachmaninoff All-Night Vigil", "Morten Lauridsen O Magnum Mysterium", "Eric Whitacre"),
        tempo=(40, 120),
        feel="Breath-led: tempo follows the text and the singers' breath; Adagio and Andante most common, "
             "fermatas at phrase ends in chorales, gentle rubato, a calm half-note tactus in Renaissance polyphony",
        swing=50,
        modes=("major", "minor", "dorian", "mixolydian"),
        keys=("D major", "G major", "F major", "Bb major", "E minor"),
        progressions=(
            "I-V43-I6-ii65-V7-I",
            "I-vi-ii6-Cad64-V-I",
            "I-IV-I",
            "minor: i-iv6-V",
            "minor: i-iv-ii°6-V-I",
            "Iadd9-vi7-IVmaj7-Iadd9",
        ),
        harmonic_rhythm=2,
        harmony="Four-part chorale harmony with strict voice leading: keep common tones, move other voices by "
                "step, double the root (never the leading tone), avoid parallel 5ths and octaves, resolve 7ths "
                "down. Passing V43 and 6/4 chords between I and I6, 4-3, 7-6 and 9-8 suspensions at cadences, the "
                "Picardy third in minor, plagal 'Amen' cadences, and in modern writing added 2nds/9ths and close "
                "clusters that bloom in a resonant acoustic.",
        voicing="satb",
        comping="sustain",
        bass_style="root",
        bass="The bass voice (about E2-D4) sings roots at cadences and stepwise lines between, often in contrary "
             "motion to the soprano; octave drops at final cadences, and in Russian Orthodox writing oktavist "
             "basses sustain pedals an octave below.",
        melody_density="medium",
        melody_scale="major",
        melody="Singable soprano lines within C4-G5 (climax up to A5/Bb5), mostly stepwise and shaped to the "
               "text's stresses: syllabic for clarity, melismatic on key words ('Alleluia', 'Amen'). Polyphony "
               "uses points of imitation (each voice enters with the same motif); alto and tenor parts stay "
               "smooth and within about a 6th.",
        groove={"step": 0.5, "swing": 50, "pattern": {
            "low floor tom": "X.......",
            "floor tom":     "....x...",
        }},
        drums="Usually none: a cappella choirs carry the pulse through declamation. Orchestrated choral works "
              "(requiems, oratorios, Carmina Burana) add timpani rolls under climaxes, bass drum and cymbal for "
              "the Dies irae, and tubular bells; timpani map to low floor tom and floor tom.",
        form=(("introduction (organ or unison)", 4), ("verse 1 (homophonic)", 16), ("verse 2 (imitative)", 16),
              ("climax (divisi, full choir)", 8), ("verse 3 (soft, reharmonised)", 16), ("Amen / coda", 6)),
        instruments=("sopranos", "altos", "tenors", "basses", "pipe organ", "piano", "string orchestra", "timpani"),
        sound_design="SATB with divisi (SSAATTBB) for richer chords; vowels set the colour ('ah' open, 'oo' dark "
                     "and soft, humming 'mm' as a pad). Choir libraries with word builders or vowel patches "
                     "(Hollywood Choirs, Spitfire's Eric Whitacre Choir, Soundiron): one track per section, legato "
                     "patches for lines, staccato syllables for rhythmic text, and real ranges (sopranos strain "
                     "above about B5).",
        production="Church or cathedral acoustic (2.5-4 s) with 20-40 ms pre-delay to keep diction; choir on a "
                   "spaced pair or ABC array, sections arranged S-A front, T-B behind. Ride CC1 for blooms on "
                   "sustained chords; cut 200-400 Hz mud, add a gentle air shelf, no compression on a cappella.",
        theory="Voice leading is everything: each line must be singable, so harmony arises from smooth melodic "
               "motion and suspensions. Text drives rhythm and form, and in a resonant room close seconds become "
               "warm colour, the basis of modern choral clusters.",
        mix=Mix(lufs=(-24, -17), lra=(10, 16), low_end="light", tone="warm", width="wide"),
    ),
    Genre(
        name="opera",
        family="classical",
        aliases=("operatic", "aria", "bel canto", "verismo", "grand opera"),
        parent="classical",
        description="Drama sung with orchestra: recitative to move the plot, arias and ensembles to stop time for "
                    "emotion, the voice soaring over a pit orchestra, from Mozart and Verdi to Wagner, Puccini and "
                    "Britten.",
        era="Italy from 1600; bel canto and verismo in Italy, music drama in Germany, 18th-20th centuries",
        touchstones=("Mozart Don Giovanni", "Rossini", "Verdi La traviata", "Wagner Der Ring des Nibelungen",
                     "Bizet Carmen", "Puccini La bohème", "Britten Peter Grimes"),
        tempo=(40, 170),
        feel="Follows the singer: colla voce rubato, fermatas on high notes, accompanied recitative in free time, "
             "Andante or Larghetto cantabile arias, brisk Allegro cabalettas",
        swing=50,
        modes=("major", "minor", "harmonic minor"),
        keys=("Bb major", "Eb major", "Ab major", "D major", "F minor", "C minor"),
        progressions=(
            "I-V65-I-ii6-Cad64-V7-I",
            "I6-V42/IV-IV6-V7/V-V",
            "minor: i-iv-vii°7-i-N6-Cad64-V7-i",
            "I-bVI-I64-V7-I",
            "minor: i-vii°7/V-Cad64-V7-i",
        ),
        harmonic_rhythm=1,
        harmony="Functional tonal harmony at the service of drama: diminished sevenths for shock, the Neapolitan "
                "and augmented sixths for pathos, a cadential 6/4 with a fermata for the high note or cadenza, "
                "bVI and chromatic mediants for sudden emotional turns (Verdi, Puccini), Wagner's continuous "
                "chromaticism and leitmotifs instead of closed numbers. Secco recitative uses simple chords on "
                "harpsichord and the stock recitative cadence (ii6-V7-I after the voice finishes).",
        voicing="open",
        comping="offbeat",
        bass_style="root",
        bass="In arias the basses play roots on the beats under an 'oom-pah' (Verdi's 'big guitar') or "
             "arpeggiated accompaniment; in recitative a continuo cello holds the bass; chromatic descending "
             "basses and long dominant pedals build ensemble finales.",
        melody_density="medium",
        melody_scale="major",
        melody="Written for the voice type: legato cantabile spanning about an octave and a 5th, climbing to a "
               "held high note near the end (tenor A4-C5, soprano A5-C6); bel canto ornaments (runs, turns, trills, "
               "cadenzas) in Rossini, Bellini and Donizetti; syllabic recitative following speech rhythm; the "
               "double aria (slow cantabile, then fast cabaletta). Orchestra doubles the voice at climaxes.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "low floor tom": "X.......x.......",
            "floor tom":     "....x.......x...",
            "crash":         "X...............",
        }},
        drums="Pit percussion is dramatic: timpani rolls under suspense and at curtains, bass drum and cymbals "
              "for storms and triumphs (Verdi's Dies irae, Aida's triumphal march), side drum for military "
              "scenes, offstage bands and bells. Timpani on low floor tom/floor tom, cymbal clash on crash.",
        form=(("orchestral introduction", 8), ("recitative (scena)", 16), ("cantabile: A", 16),
              ("cantabile: A' to climax", 16), ("tempo di mezzo", 12), ("cabaletta", 24),
              ("cabaletta repeat (ornamented)", 24), ("stretta / coda", 8)),
        instruments=("soprano", "mezzo-soprano", "tenor", "baritone", "opera orchestra", "harp", "chorus",
                     "harpsichord (recitative)", "timpani"),
        sound_design="Voice first: a pit orchestra of 50-80 supports, strings doubling the vocal line at climaxes, "
                     "woodwind obbligatos answering the singer, horns and trombones for drama, harp for love "
                     "scenes. Solo opera voices are hard to sample, so lead with a recorded singer or an "
                     "instrumental stand-in (cello, oboe) for the vocal line, and keep accompaniment patches in the "
                     "p-mf layers under it.",
        production="Opera-house acoustic (1.5-2 s, drier than a concert hall), singer centre and forward on a spot "
                   "mic blended with the stage pair, orchestra behind. Ride the accompaniment under the voice "
                   "instead of compressing it; a singer's range from pianissimo to full voice can exceed 25 dB, so "
                   "let the climactic high note ring.",
        theory="Musical form follows dramatic function: recitative for plot, aria for frozen emotion, ensemble "
               "for characters in conflict singing at once. Keys carry meaning (Mozart's Eb for solemn warmth, D "
               "for brilliance), and leitmotif turns harmony and orchestration into a narrative code.",
        mix=Mix(lufs=(-24, -16), lra=(12, 20), low_end="moderate", tone="warm", width="wide"),
    ),
    Genre(
        name="neoclassical piano",
        family="classical",
        aliases=("modern classical", "neo-classical piano", "post-classical", "felt piano", "contemporary piano"),
        parent="minimalism",
        description="Intimate post-classical solo piano and chamber music: simple diatonic loops, repeated "
                    "arpeggios and sparse melodies, recorded close and soft with felt-piano warmth, between "
                    "classical, minimalism and ambient.",
        era="Europe and Iceland, 2000s-present (Erased Tapes, Deutsche Grammophon's modern classical roster)",
        touchstones=("Ludovico Einaudi", "Ólafur Arnalds", "Nils Frahm", "Max Richter On the Nature of Daylight",
                     "Yann Tiersen", "Joep Beving", "Hania Rani"),
        tempo=(60, 120),
        feel="Gentle, steady pulse with breathing rubato; Andante to Moderato, 8th-note arpeggios under soft "
             "dynamic swells",
        swing=50,
        modes=("minor", "major", "dorian"),
        keys=("A minor", "E minor", "D minor", "B minor", "C major", "F major"),
        progressions=(
            "i-VI-III-VII",
            "i-iv-VI-V",
            "VI-VII-i-v",
            "iadd9-VImaj7-III-VIIsus2",
            "major: I-V6-vi-IV",
        ),
        harmonic_rhythm=1,
        harmony="Diatonic triads with add9 and sus2 colour, four-chord loops moving between relative minor and "
                "major, inversions for a stepwise descending bass, sus resolutions instead of dominants, rarely a "
                "V7; harmony changes every one or two bars and one loop carries a whole piece through textural "
                "variation.",
        voicing="open",
        comping="arpeggio_up",
        bass_style="whole",
        bass="Left hand holds low roots or open 5ths/octaves (about A1-A2) under the sustain pedal, or rolls a "
             "1-5-10 broken chord; in chamber versions a cello takes the bass in long tones.",
        melody_density="sparse",
        melody_scale="minor",
        melody="Simple, mostly stepwise right-hand motifs of 3-6 notes, repeated with small variations and often "
               "growing out of the top of the arpeggio; octave doubling at the climax; silence between phrases; "
               "mid register (C4-C6), mostly p-mf.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "low floor tom": "x...............o...............",
        }},
        drums="None in the classic sound: hammer and pedal noise are the rhythm. Crossover tracks (Arnalds, Frahm) "
              "may add a soft electronic pulse, a felt kick or a muffled timpani thump on beat 1, always below "
              "the piano.",
        form=(("intro (arpeggio alone)", 4), ("A (melody enters)", 8), ("A' (octaves)", 8),
              ("B (relative-key loop)", 8), ("build (strings join)", 8), ("A'' (climax)", 8),
              ("outro (arpeggio fades)", 4)),
        instruments=("felt or upright piano", "grand piano", "string quartet", "solo cello", "soft synth pad",
                     "celesta", "tape machine"),
        sound_design="Felt piano (felt between hammers and strings) for a muffled, intimate tone with audible "
                     "mechanics, or an upright/grand with una corda; strings flautando or sul tasto with light "
                     "vibrato. Libraries: Spitfire Original Felt Piano and Soft Piano, Native Instruments Noire, "
                     "felt and upright pianos with mechanical noise kept; tape saturation, light wow and flutter, "
                     "and Frahm-style tape delay for texture.",
        production="Close mics inside the piano for intimacy, a small room or plate plus a long soft tail, stereo "
                   "image from low notes left to high right (player's perspective). Low cut at 40 Hz, 1-2 dB of "
                   "gentle bus compression, hammer noise left in; mastered louder than concert classical but still "
                   "dynamic.",
        theory="The appeal is reduction: consonant diatonic loops, repetition and the intimacy of the recording "
               "carry the emotion. Harmonic interest comes from inversions and bass motion under a fixed "
               "right-hand pattern, a technique shared with minimalism.",
        mix=Mix(lufs=(-18, -12), lra=(6, 12), low_end="light", tone="warm", width="moderate"),
    ),
    # ---------------------------------------------------------------- film and games
    Genre(
        name="cinematic",
        family="film and games",
        aliases=("film score", "orchestral", "film music", "movie score", "soundtrack", "cinematic orchestral"),
        parent="romantic",
        description="Orchestral film scoring: themes and leitmotifs over lush strings, horns and percussion, with "
                    "chromatic-mediant colour, hybrid synths and dynamic arcs that follow the picture.",
        era="Hollywood Golden Age of the 1930s (Korngold, Steiner) to today's hybrid scoring",
        touchstones=("John Williams", "Hans Zimmer", "Howard Shore The Lord of the Rings", "Thomas Newman",
                     "Alexandre Desplat", "Ennio Morricone", "James Horner"),
        tempo=(60, 140),
        feel="Follows picture: tempo maps and metre changes hit sync points; Adagio for emotion, Allegro for "
             "action, often felt in half time",
        swing=50,
        modes=("minor", "major", "dorian", "lydian"),
        keys=("D minor", "C minor", "E minor", "D major", "Eb major"),
        progressions=(
            "i-VI-III-VII",
            "i-iv-VI-V",
            "major: I-bVI-IV-I",
            "major: I-III-IV-iv-I",
            "lydian: I-II-I-II",
            "i-bII-i-V",
        ),
        harmonic_rhythm=0.5,
        harmony="Romantic-orchestral vocabulary with modal and mixture colour: minor-key loops (i-VI-III-VII), "
                "chromatic mediants (I-bVI, I-III, i-bvi) for wonder and heroism, the lydian #4 for flight and "
                "magic, minor iv in major for nostalgia (I-IV-iv-I), Phrygian bII for menace, pedal points under "
                "changing chords for tension, sus and quartal chords in modern scores. One chord per 1-2 bars so "
                "the music can bend to the edit.",
        voicing="spread",
        comping="sustain",
        bass_style="whole",
        bass="Cellos, basses, tuba and bass trombone in long roots and octaves, pedal tones under modulating "
             "harmony, 8th-note ostinatos in action, and a sine or low-pulse sub layer reinforcing downbeats in "
             "hybrid scores.",
        melody_density="medium",
        melody_scale="minor",
        melody="Leitmotif-driven: a short theme (4-8 bars) built on a strong interval (rising 5th or 4th for "
               "heroism, minor 6th for longing) stated by horns or strings, fragmented in tension cues and "
               "delivered in full at the emotional payoff, with woodwind counter-melodies; themes recur in new "
               "orchestrations and modes to follow characters.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":          "X.......x.......",
            "low floor tom": "X..x..x...x..x..",
            "snare":         "....x.......x...",
            "crash":         "X...............",
        }},
        drums="Orchestral percussion as drama: timpani rolls and hits on sync points, bass drum and cymbal "
              "crashes for impacts, snare rolls and marches, tam-tam swells; hybrid scores add taiko ensembles "
              "and processed hits. Timpani on low floor tom/floor tom, bass drum on kick, cymbals on crash.",
        form=(("establishing (pads, motif)", 8), ("theme A (strings)", 16), ("development / tension", 16),
              ("build", 8), ("theme A (tutti climax)", 16), ("resolution / tag", 8)),
        instruments=("string orchestra", "French horns", "trumpets and trombones", "woodwinds", "harp", "piano",
                     "timpani and orchestral percussion", "choir", "synth pads and sub"),
        sound_design="Layered orchestra: 16-14-12-10-8 strings with divisi, six to eight horns in unison for "
                     "themes, trumpets for fanfares, low brass and tuba for weight, woodwinds doubling at the "
                     "octave, harp and celesta for magic. Libraries: Cinematic Studio Series, Spitfire Symphony "
                     "Orchestra, Berlin series, Cinesamples; longs and shorts on separate tracks, marcato or "
                     "staccato layered under longs for attack, Omnisphere-style pads and pulses for hybrid cues.",
        production="Scoring-stage sound (AIR Lyndhurst, Abbey Road Studio One): a 2-3 s hall over a Decca-tree "
                   "perspective, close mics only for definition, traditional seating panned across the stage. "
                   "CC1 for dynamics and CC11 for phrasing on every long note, tempo map from picture; deliver "
                   "stems (strings, brass, winds, percussion, synths, choir) with headroom for dialogue and "
                   "effects.",
        theory="Harmony serves narrative: chromatic mediants give awe without functional direction, modal colour "
               "encodes character (lydian wonder, dorian resolve, Phrygian menace), leitmotif transformation tells "
               "the story, and pedal points let the music hold tension for as long as a shot lasts.",
        mix=Mix(lufs=(-18, -12), lra=(8, 18), low_end="moderate", tone="neutral", width="wide"),
    ),
    Genre(
        name="epic trailer",
        family="film and games",
        aliases=("trailer music", "epic music", "trailer", "epic orchestral", "hybrid orchestral"),
        parent="cinematic",
        description="Hybrid orchestral trailer music: relentless string ostinatos, braams, taiko and impacts, "
                    "massive choir and a three-act build to a final tutti, mastered as loud as rock.",
        era="Hollywood trailer houses, 2000s-present",
        touchstones=("Two Steps from Hell", "Thomas Bergersen", "Audiomachine", "Immediate Music",
                     "Hans Zimmer Inception", "Really Slow Motion"),
        tempo=(80, 150),
        feel="Driving 8th/16th string ostinatos at 120-140 BPM felt in half time, with stops, rises and hits "
             "that cut with the edit",
        swing=50,
        modes=("minor", "harmonic minor", "phrygian", "major"),
        keys=("D minor", "C minor", "E minor", "F minor", "A minor"),
        progressions=(
            "i-VI-III-VII",
            "VI-VII-i-i",
            "i-VI-iv-V",
            "i-bII-i-bII",
            "major: vi-IV-I-V",
        ),
        harmonic_rhythm=0.5,
        harmony="Minimal and modal: the i-VI-III-VII loop and its rotations, two-chord pivots (i-VI, i-bII for "
                "menace), pedal tones under moving upper chords, power-5th brass braams on a single low note, and "
                "a switch to the relative major or a major-key lift for the uplifting third act. Chords change "
                "every bar or two and are never complex.",
        voicing="open",
        comping="pulse_16",
        bass_style="sixteenths",
        bass="Low strings, piano and synth bass hammer the root in 8th or 16th ostinatos (often a 3+3+2 accented "
             "16th pattern), octave-doubled by contrabasses and tuba; sub hits and braams (low brass plus synth, "
             "40-60 Hz) on the downbeat of each new section.",
        melody_density="sparse",
        melody_scale="minor",
        melody="Big, simple themes in long notes: horns in unison, choir on 'ah' or Latin-style syllables, or a "
               "solo cello or female voice in act one; climbing by 4ths and 5ths and repeated an octave higher in "
               "the final act; hooks are 3-5 note motifs so they survive the edit.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":          "X.......X..x....X.......X..x.x..",
            "low floor tom": "X..x..x.X..x..x.X..x..x.X..x.xxx",
            "snare":         "....x.......x.......x.......x.x.",
            "crash":         "X...............................",
        }},
        drums="Epic percussion ensembles: taiko and big toms in 3+3+2 16th patterns, booms on every downbeat, "
              "ensemble snares and rolls, metal hits and anvils, risers (reverse cymbals, synth sweeps) into each "
              "section and a silent drop before the final hit. Taiko on low floor tom, big bass drum on kick, "
              "cymbals on crash.",
        form=(("act 1: intro (piano or solo, sparse)", 16), ("braam / hit", 2), ("act 2: build (ostinato, percussion)", 24),
              ("riser and silence", 2), ("act 3: tutti (choir, brass theme)", 24), ("final hits and tail", 4)),
        instruments=("spiccato string ostinatos", "French horns and low brass", "epic choir", "taiko and ensemble drums",
                     "piano", "synth braams and risers", "sub bass", "electric cello or guitar"),
        sound_design="Layering is the sound: spiccato ostinato doubled by a synth arp and piano, 12-horn unison "
                     "patches, low brass plus distorted synth for braams, choir with syllables (Strezov, Hollywood "
                     "Choirs), taiko and ensemble drums (Heavyocity Damage, Action Strikes), and hits, whooshes and "
                     "risers from trailer toolkits; saturate and transient-shape the percussion.",
        production="Big, close and loud: a shorter, darker hall (1.8-2.4 s) plus a long epic tail on percussion "
                   "and choir, parallel compression and saturation on drums, multiband control of the low end, "
                   "orchestra ducked under the hits. Master with clipping and limiting to about -10 LUFS while "
                   "keeping act one far quieter (around -20 LUFS short-term) than act three.",
        theory="Build is the form: density, register and percussion increase every 8 bars while the harmony "
               "barely moves, so the energy comes from orchestration and rhythm. Silence before the final hit and "
               "the move from the minor loop to a major lift deliver the payoff.",
        mix=Mix(lufs=(-13, -9), lra=(5, 10), low_end="very heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="horror score",
        family="film and games",
        aliases=("horror", "horror music", "scary music", "horror film score"),
        parent="cinematic",
        description="Music of dread: atonal clusters, tritones and creeping drones, aleatoric string effects and "
                    "sudden stingers, alternating near-silence with shocking loudness.",
        era="From Bernard Herrmann's Psycho (1960) and the Penderecki-inspired 1970s to modern hybrid horror",
        touchstones=("Bernard Herrmann Psycho", "Jerry Goldsmith The Omen", "John Carpenter Halloween",
                     "Penderecki in The Shining", "Christopher Young", "Joseph Bishara", "Mica Levi Under the Skin"),
        tempo=(40, 110),
        feel="Unmetered or slow (Lento, Grave); time stretched by drones, broken by ostinatos or stingers synced "
             "to scares",
        swing=50,
        modes=("minor", "phrygian", "diminished whole-half", "chromatic"),
        keys=("C minor", "D minor", "Bb minor", "E phrygian"),
        progressions=(
            "imaj7-iv-imaj7-V7b9",
            "i-bII-i-bII",
            "i-#iv-i-#iv",
            "i-vi-i-vi",
        ),
        harmonic_rhythm=0.25,
        harmony="Deny tonal comfort: the minor-major 7th (imaj7, the 'Hitchcock chord'), diminished 7ths, "
                "tritone-related triads (i-#iv), semitone shifts (i-bII), minor chords a major third apart "
                "(i-vi in minor, e.g. Cm-Abm), semitone clusters in the strings, augmented triads and the "
                "octatonic scale; often just a drone plus one dissonant interval (minor 2nd, tritone) that slowly "
                "widens. Detuned lullaby or music-box tunes provide irony.",
        voicing="cluster",
        comping="sustain",
        bass_style="pedal",
        bass="Sub drones and low pedals (contrabass sul ponticello, synth sub, bowed tam-tam fundamentals), slow "
             "chromatic descents, one low piano note struck repeatedly, low brass clusters for menace.",
        melody_density="sparse",
        melody_scale="diminished whole-half",
        melody="Few real melodies: two-note semitone motifs, tritone leaps, slowly bending pitches (glissando, "
               "detuning), child-like tunes on music box or solo voice twisted for irony; stingers built from "
               "shrieking high string clusters (the Psycho shower violins).",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":    "X..x............",
            "low tom": "........o.......",
        }},
        drums="Percussion for shock: bowed cymbals and tam-tam, a bass-drum heartbeat (lub-dub), low tom thuds, "
              "piano-lid slams, waterphone, metal scrapes, and stinger hits synced to jump scares after silence. "
              "No steady groove except a heartbeat or a Carpenter-style piano ostinato in 5/4.",
        form=(("drone / unease", 16), ("creeping build (clusters widen)", 16), ("false calm", 8), ("stinger", 1),
              ("chase ostinato", 16), ("aftermath drone", 8)),
        instruments=("strings (clusters, aleatoric effects)", "waterphone", "prepared or detuned piano",
                     "bowed cymbals and tam-tam", "low brass", "synth drones", "music box", "solo voice / whispers"),
        sound_design="Aleatoric strings: col legno battuto, sul ponticello tremolo, cluster glissandi, playing "
                     "behind the bridge, scratch tone and random high pitches (aleatoric/FX string libraries, "
                     "Symphobia FX, Albion Tundra); waterphone, bowed metals, reversed piano, granular drones, "
                     "detuned music box, sub booms and stingers prefaced by reverse cymbals.",
        production="Extreme dynamics are the effect: drones near -40 LUFS short-term, stingers near -10; wide, "
                   "enveloping reverb (3-6 s) and pitch-shifted tails, rumble below 40 Hz for unease, moving and "
                   "hard-panned elements (surround if available). Slow CC1 crescendos, and no master compression "
                   "that would flatten the scare.",
        theory="Horror music denies expectation: no stable tonic, dissonance that never resolves, silence and "
               "unpredictable timing. Tritones and minor 2nds give maximum instability, and sudden contrast "
               "(quiet to loud, low to high) triggers the startle reflex.",
        mix=Mix(lufs=(-22, -14), lra=(12, 20), low_end="heavy", tone="dark", width="wide"),
    ),
    Genre(
        name="adventure score",
        family="film and games",
        aliases=("adventure", "heroic score", "swashbuckler", "fantasy score", "superhero score"),
        parent="cinematic",
        description="Heroic, swashbuckling orchestral scoring: brass fanfares, soaring string themes, major-key "
                    "chromatic mediants and busy, lively orchestration for quests, flight and triumph.",
        era="Hollywood's Golden Age (Korngold), revived by John Williams in the late 1970s; still the blockbuster "
            "sound",
        touchstones=("Erich Wolfgang Korngold The Adventures of Robin Hood", "John Williams Star Wars",
                     "John Williams Raiders of the Lost Ark", "Alan Silvestri Back to the Future",
                     "John Powell How to Train Your Dragon", "James Horner"),
        tempo=(90, 150),
        feel="Allegro marziale or con spirito: a march in cut time or a galloping 6/8 feel with triplet brass "
             "fanfares; broad Maestoso for the main theme",
        swing=50,
        modes=("major", "lydian", "mixolydian", "dorian"),
        keys=("Bb major", "C major", "D major", "Eb major", "F major"),
        progressions=(
            "I-III-IV-I",
            "I-bVI-bVII-I",
            "I-bIII-IV-I",
            "lydian: I-II-I-II",
            "I-V-vi-iii-IV-I-ii-V",
            "mixolydian: I-VII-IV-I",
        ),
        harmonic_rhythm=1,
        harmony="Bright major keys with chromatic-mediant colour: I-III (the 'hero' major mediant), I-bVI and "
                "I-bIII borrowed from minor for nobility, the bVI-bVII-I triumphant cadence, lydian II for flight "
                "and wonder, secondary dominants for momentum, and a sudden lift up a half or whole step for the "
                "final statement. Action passages turn to octatonic and polytonal brass clusters before the theme "
                "returns.",
        voicing="open",
        comping="eighths",
        bass_style="root_fifth",
        bass="March basses alternate root and fifth on beats 1 and 3 (tuba, basses, bassoons), galloping "
             "8th-16th-16th ostinatos in action cues, pedal points under rising sequences before the theme "
             "returns.",
        melody_density="medium",
        melody_scale="major",
        melody="Leap-driven heroic themes: a rising perfect 5th or 4th opening (5 up to 1, or 1 up to 5), triplet "
               "pickups, dotted rhythms, a high climax on a long note, then a stepwise descent; stated by "
               "trumpets and horns and answered by strings an octave up; a lyrical B theme (the love theme) in "
               "the strings.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "snare":         "X.xxX.x.X.xxX.x.",
            "kick":          "X.......X.......",
            "crash":         "X.......X.......",
            "low floor tom": "X...x...X...x...",
        }},
        drums="Military and pageant percussion: snare marches and rolls, bass drum with clashed cymbals on 1 and "
              "3, timpani on tonic and dominant under the fanfares, glockenspiel doubling the melody, triangle "
              "sparkle; action cues add tom ostinatos and big hits. Timpani on low floor tom/floor tom.",
        form=(("intro fanfare", 4), ("A: main theme (trumpets)", 16), ("A: repeat (horns and strings)", 16),
              ("B: lyrical trio (IV or bVI)", 16), ("development / action", 16),
              ("A: final statement (up a half step)", 16), ("coda fanfare", 8)),
        instruments=("trumpets", "French horns", "trombones and tuba", "strings", "piccolo and flutes",
                     "snare drum", "timpani", "glockenspiel", "harp"),
        sound_design="Brass-forward orchestra: trumpets on the tune, horns on countermelodies and rips, trombones "
                     "for weight; strings in fast runs, tremolo and soaring octaves; woodwind flourishes and "
                     "trills; glockenspiel and xylophone for sparkle. Use marcato and staccato brass patches for "
                     "fanfares, true-legato strings for themes, and written-out or runs patches for flourishes.",
        production="Bright, open scoring-stage sound (2-2.5 s), brass a little closer than in concert recordings, "
                   "strings wide, percussion with clear transients. Heavy CC1 riding for brass swells, a large "
                   "dynamic range and only light bus glue; when mixing to picture leave room in 1-4 kHz for "
                   "dialogue.",
        theory="Optimism through chromatic-mediant brightness: borrowed bVI and bIII and the major III add "
               "grandeur plain diatonic harmony lacks, while rising-5th themes and march rhythms evoke heroism and "
               "motion. Golden-Age leitmotif technique keeps characters musically identifiable.",
        mix=Mix(lufs=(-18, -12), lra=(10, 18), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="suspense score",
        family="film and games",
        aliases=("thriller score", "thriller", "suspense", "tension music", "action score"),
        parent="cinematic",
        description="Tension and action-thriller scoring: pulsing ostinatos, low string and synth pulses, "
                    "unresolved minor and Phrygian harmony and slow builds that keep the audience on edge.",
        era="Herrmann's Hitchcock scores onward; modern pulse-driven thriller scoring since the late 1990s",
        touchstones=("Bernard Herrmann Vertigo", "John Powell The Bourne Identity", "Hans Zimmer The Dark Knight",
                     "Trent Reznor and Atticus Ross The Social Network", "Harry Gregson-Williams",
                     "Hildur Guðnadóttir"),
        tempo=(70, 140),
        feel="Steady clock-like 8th or 16th pulse (often 120-140, or half time around 70), building through "
             "layers rather than tempo",
        swing=50,
        modes=("minor", "phrygian", "harmonic minor", "dorian"),
        keys=("D minor", "C minor", "E minor", "F# minor", "A minor"),
        progressions=(
            "i-VI-i-VI",
            "i-imaj7-i7-VI",
            "i-bII-i-bII",
            "i-v-VI-iv",
            "i-VI-iv-V",
        ),
        harmonic_rhythm=0.5,
        harmony="Minor and Phrygian with very slow change: two-chord oscillations (i-VI, i-bII), the chromatic "
                "line cliché (i-imaj7-i7-VI, an inner voice falling by semitones), 5th-only or sus chords that "
                "refuse major/minor clarity, pedals under rising chromatic upper voices, and an unresolved V or "
                "diminished chord ending the cue. Tension rises through register, density and added b2/b6, not "
                "new chords.",
        voicing="open",
        comping="pulse_16",
        bass_style="eighths",
        bass="Low string and synth pulses in steady 8ths (or 16ths) on the root, often with 3+3+2 accents, "
             "staying on one note for 8-16 bars while the harmony moves above; sub booms at section changes.",
        melody_density="sparse",
        melody_scale="minor",
        melody="Motifs, not tunes: 2-4 note cells (rising minor 2nd, falling minor 3rd) repeated and transposed "
               "upward to build, long high string harmonics for unease, a slow piano figure or solo cello as the "
               "human element; phrases avoid landing on the tonic.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":          "X.......x.......",
            "low floor tom": "X..x..x.x..x..x.",
            "closed hat":    "x.x.x.x.x.x.x.x.",
            "rim":           "....x.......x...",
        }},
        drums="Low, muted and propulsive: frame drums and low toms in 3+3+2, ticking hats or clock-like synth "
              "percussion, processed hits and reversed swells into section changes, building snare rolls; "
              "orchestral and electronic percussion blended. Save cymbal crashes for the climax.",
        form=(("pulse alone", 8), ("motif enters", 16), ("layer build (strings, percussion)", 16),
              ("tension peak / riser", 8), ("hit or sudden drop", 2), ("aftermath sustain", 8)),
        instruments=("low strings (spiccato ostinato)", "synth pulse and bass", "piano", "frame drums and low toms",
                     "string harmonics", "solo cello", "low brass clusters", "processed percussion"),
        sound_design="Spiccato and staccatissimo string ostinatos layered with arpeggiated analog synth pulses; "
                     "col legno and ricochet for ticking; harmonics and sul ponticello tremolo on top; low brass "
                     "cluster swells; prepared or felt piano motifs; designed rises (reverse cymbals, Shepard "
                     "tones) for an endless build.",
        production="Darker, drier and closer than adventure scoring (1.5-2 s hall), mid-heavy, low end controlled "
                   "and ducked under booms, synths and orchestra glued with bus compression. Automate CC1/CC11 "
                   "and filter cutoff in long 16-bar ramps; dip 1-3 kHz in the strings for dialogue.",
        theory="Suspense is delayed resolution: a tonic pedal or repeated cell holds while dissonance accumulates "
               "above, so the ear waits for a resolution that never arrives. Shepard tones and rising chromatic "
               "sequences give endless ascent without arrival.",
        mix=Mix(lufs=(-20, -14), lra=(8, 15), low_end="heavy", tone="dark", width="wide"),
    ),
    Genre(
        name="sci-fi score",
        family="film and games",
        aliases=("sci-fi", "science fiction score", "space score", "sci-fi soundtrack"),
        parent="cinematic",
        description="Science-fiction scoring that blends orchestra and synthesizers: lydian and whole-tone wonder, "
                    "electronic textures and sequenced pulses, vast reverbs and alien, otherworldly harmony.",
        era="1950s theremin and electronic scores (The Day the Earth Stood Still, Forbidden Planet) through "
            "Vangelis's Blade Runner to today's hybrid scores",
        touchstones=("Bernard Herrmann The Day the Earth Stood Still", "Jerry Goldsmith Alien",
                     "John Williams Close Encounters of the Third Kind", "Vangelis Blade Runner",
                     "Hans Zimmer Interstellar", "Jóhann Jóhannsson Arrival"),
        tempo=(60, 130),
        feel="Slow, vast pulses and suspended time (Adagio, half time), or clockwork sequencer ostinatos",
        swing=50,
        modes=("lydian", "minor", "whole tone", "phrygian"),
        keys=("C lydian", "F lydian", "D minor", "E minor"),
        progressions=(
            "I-II-I-II",
            "Imaj7-II-iii7-II",
            "major: I-bvi-I-bvi",
            "major: Imaj7-bVImaj7-Imaj7-bVImaj7",
            "minor: i-bII-i-bII",
        ),
        harmonic_rhythm=0.5,
        harmony="Wonder and strangeness: lydian I-II and maj7#11 sonorities for awe, chromatic-mediant and "
                "hexatonic-pole pairs (I-bVI, I-bvi) that feel uncanny, whole-tone and octatonic fields for alien "
                "or technological colour, quartal and sus chords without a 3rd, long pedals under slowly shifting "
                "triads (Interstellar's organ), and microtonal or cluster textures for alien threat.",
        voicing="spread",
        comping="arpeggio_up",
        bass_style="pedal",
        bass="Deep synth sub drones and organ pedals (16' and 32'), slowly moving roots, sequenced 16th-note "
             "analog bass in action, and huge low braams for scale.",
        melody_density="sparse",
        melody_scale="lydian",
        melody="Spare, signal-like motifs (short interval cells used as communication, as in Close Encounters), "
               "slow singing synth leads with brassy swells and aftertouch vibrato (Vangelis's CS-80), wordless "
               "soprano or theremin glissandi, high string harmonics; melodies float on the #4 or 9th and avoid "
               "the tonic.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":           "X.......X.......",
            "electric snare": "....x.......x...",
            "closed hat":     "x.x.x.x.x.x.x.x.",
        }},
        drums="Electronic and processed percussion: gated synth toms, metallic hits, granular clicks and "
              "sequenced hats for technology; orchestral timpani and bass drum for scale; often no drums at all "
              "in wonder cues. Synth kicks on kick, electronic snares on electric snare, orchestral booms on low "
              "floor tom.",
        form=(("void / drone", 8), ("motif (synth or soprano)", 16), ("arpeggiator pulse enters", 16),
              ("orchestral swell", 16), ("revelation tutti (organ, brass)", 16), ("fade to space", 8)),
        instruments=("analog polysynth (CS-80, Jupiter, Prophet)", "modular sequencer", "pipe organ",
                     "string orchestra (harmonics, divisi)", "French horns and low brass",
                     "theremin or wordless soprano", "piano", "synth sub bass"),
        sound_design="Synths as main instruments: CS-80-style brass and pads with ribbon and aftertouch vibrato, "
                     "Juno/Prophet pads, sequenced Moog bass, granular and spectral textures, vocoder; strings in "
                     "harmonics, flautando and sul ponticello; pipe organ for cosmic scale; reverse swells and "
                     "shimmer tails. Omnisphere, Arturia V Collection and Spitfire/Orchestral Tools strings are the "
                     "usual palette.",
        production="Huge spaces: long reverbs (4-10 s) and shimmer or diffuse delays on synths, wide pads with "
                   "mono sub below 80 Hz, orchestra and synths sharing reverb sends so they sit in one space. "
                   "Automate filter cutoff and CC1 together for slow builds; dynamic, but with heavy low end for "
                   "size.",
        theory="Ambiguity of third and tonic: the lydian #4, sus and quartal chords and chromatic third relations "
               "remove functional gravity, which reads as weightless and otherworldly. Electronic timbre signals "
               "the future, and pedal-based harmony matches slow, vast visuals.",
        mix=Mix(lufs=(-18, -12), lra=(8, 15), low_end="heavy", tone="dark", width="wide"),
    ),
    Genre(
        name="video game",
        family="film and games",
        aliases=("game music", "video game music", "vgm", "game soundtrack", "game ost"),
        parent="cinematic",
        description="Interactive music built to loop and adapt: memorable themes, seamless loops and layered "
                    "stems that rise and fall with gameplay, from orchestral adventure to electronic action.",
        era="Arcades and consoles from the late 1970s; orchestral and adaptive scores since the 2000s",
        touchstones=("Koji Kondo Super Mario Bros.", "Koji Kondo The Legend of Zelda",
                     "Jeremy Soule The Elder Scrolls V: Skyrim", "Martin O'Donnell Halo", "Austin Wintory Journey",
                     "Bear McCreary God of War", "Lena Raine Celeste"),
        tempo=(70, 170),
        feel="Constant, loop-friendly tempo so stems and transitions swap on bar lines; action at 140-170, "
             "exploration at 80-110",
        swing=50,
        modes=("major", "minor", "dorian", "mixolydian", "lydian"),
        keys=("C major", "G major", "F major", "D minor", "A minor", "E minor"),
        progressions=(
            "I-bVI-bVII-I",
            "minor: i-VI-VII-i",
            "dorian: i7-IV7-i7-IV7",
            "I-IV-ii7-V7",
            "I-bVII-IV-I",
        ),
        harmonic_rhythm=1,
        harmony="Clear tonal harmony that survives looping: diatonic 2- and 4-bar cycles, borrowed bVI-bVII-I for "
                "victory and level-complete fanfares, dorian and mixolydian for adventure, chromatic mediants and "
                "lydian colour in fantasy scores. The last chord of a loop must lead back to the first (V or bVII "
                "into I), and stems are voiced so any combination of layers sounds complete.",
        voicing="open",
        comping="eighths",
        bass_style="root_fifth",
        bass="Carries groove and harmony even when other layers drop out: root-fifth patterns, driving 8ths in "
             "action, walking or syncopated lines in town and platformer themes; usually lives in the base stem "
             "with the percussion.",
        melody_density="medium",
        melody_scale="major",
        melody="Hummable, built for repetition: 4- or 8-bar phrases with strong rhythmic identity and a motif that "
               "can be re-orchestrated for menus, victory stingers and boss variations; leaves gaps for sound "
               "effects and dialogue and avoids piercing registers that fatigue over long loops.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "X.......X.......",
            "snare":      "....X.......X...",
            "closed hat": "x.x.x.x.x.x.x.x.",
            "crash":      "X...............",
        }},
        drums="Style-dependent: orchestral percussion (timpani, taiko, snare) for epic games, drum kit or "
              "electronic beats for action and platformers, light hand percussion for towns. Percussion is "
              "usually its own stem, added or removed with intensity (exploration: none; combat: full kit or "
              "taiko).",
        form=(("intro (plays once)", 4), ("A (loop start)", 16), ("B", 16), ("A'", 16), ("C (bridge)", 8),
              ("turnaround to loop start", 4)),
        instruments=("orchestra (strings, brass, winds)", "synths", "piano", "drum kit or electronic drums",
                     "orchestral percussion", "electric guitar", "choir", "solo world instruments (flutes, strings)"),
        sound_design="Match the palette to the game world and keep it consistent across cues: orchestral libraries "
                     "for fantasy, synths and processed guitars for sci-fi and action, chip sounds for retro. Write "
                     "in layered stems (base, rhythm, melody, intensity) and keep reverb tails short in the stems, "
                     "or render tails separately, so the loop point doesn't double the reverb.",
        production="Loops must be sample-accurate: bounce with the last bar's tail wrapped back onto the start, "
                   "check zero crossings, and mark loop points for the middleware (Wwise, FMOD). Mix less dense "
                   "than film so effects and dialogue cut through, control the low end, and deliver stems at the "
                   "audio team's target (often -23 to -18 LUFS in game; soundtrack albums mastered louder).",
        theory="Repetition-aware composition: music heard for hours needs strong themes, clear harmony and "
               "unfatiguing textures. Adaptive techniques (vertical layering of stems, horizontal re-sequencing "
               "between sections, stingers on game events) shape the form at runtime.",
        mix=Mix(lufs=(-18, -13), lra=(5, 12), low_end="moderate", tone="neutral", width="wide"),
    ),
    Genre(
        name="chiptune",
        family="film and games",
        aliases=("8-bit", "8 bit music", "chip music", "nes music", "game boy music"),
        parent="video game",
        description="Music made with, or emulating, the sound chips of 8-bit consoles and home computers: "
                    "square-wave leads, triangle bass, noise drums and lightning-fast arpeggios that fake chords.",
        era="Japan, the US and Europe on 1980s consoles and computers (NES, Game Boy, C64); a demoscene and indie "
            "scene since the 2000s",
        touchstones=("Koji Kondo", "Hirokazu Tanaka Metroid", "Takashi Tateishi Mega Man 2", "Rob Hubbard",
                     "Yuzo Koshiro", "Anamanaguchi", "Disasterpeace"),
        tempo=(110, 200),
        feel="Fast, rigid and perfectly quantised 16th-note drive at 130-180 BPM, with tempo steps set by the "
             "sound driver's 60 Hz frame ticks",
        swing=50,
        modes=("minor", "major", "dorian", "harmonic minor"),
        keys=("A minor", "E minor", "D minor", "C major", "G major"),
        progressions=(
            "i-VI-VII-i",
            "i-VII-VI-VII",
            "major: I-bVI-bVII-I",
            "i-iv-V-i",
            "VI-VII-i-i",
        ),
        harmonic_rhythm=1,
        harmony="Three or four monophonic channels, so chords are implied: fast arpeggios cycling the chord tones "
                "every frame or two on one pulse channel, two-note harmony or 5ths between the pulses, and strong "
                "minor or diatonic loops ending bVI-bVII-I. Neo-Baroque habits (Mega Man, Castlevania): sequences, "
                "harmonic-minor V, pedal-point arpeggios.",
        voicing="close",
        comping="arpeggio_up",
        bass_style="octaves",
        bass="The triangle channel (fixed volume, soft and slightly stepped) plays octave-jumping 8ths or 16ths "
             "and fast runs in rock style; on Game Boy a 4-bit wave channel, on the C64 a filtered SID voice takes "
             "the bass.",
        melody_density="busy",
        melody_scale="minor",
        melody="Fast, catchy pulse-wave leads: wide leaps, 16th-note runs, trills, pitch slides and software "
               "vibrato; echo made by repeating the line on the second pulse a 16th or 8th late and quieter; duty "
               "changes (12.5%, 25%, 50%) contrast sections; loops every 16-32 bars.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "X.....x.X.......",
            "snare":      "....X.......X...",
            "closed hat": "x.xxx.xxx.xxx.xx",
        }},
        drums="All from the noise channel: short high noise bursts for hats, longer mid noise with fast decay for "
              "snares, kicks faked by a quick triangle pitch drop or a DPCM sample; rock and dance beats at high "
              "tempo with rapid 16th fills, drum hits often stolen from the bass channel.",
        form=(("intro", 4), ("A (loop)", 16), ("B", 16), ("A'", 16), ("bridge", 8), ("turnaround (to loop)", 4)),
        instruments=("pulse/square wave 1 (lead)", "pulse/square wave 2 (harmony or echo)", "triangle wave (bass)",
                     "noise channel (drums)", "DPCM samples", "C64 SID voices"),
        sound_design="Emulate the chips: NES 2A03 (two pulses at 12.5/25/50% duty, triangle, noise, DPCM), Game Boy "
                     "(two pulses, 4-bit wavetable, noise), C64 SID (three voices with filter and ring mod). Use "
                     "FamiTracker, Furnace or DefleMask, or plugins (Plogue Chipsounds, Magical 8bit Plug, "
                     "Chipsynth): fast volume envelopes, arpeggio macros, pitch vibrato, no reverb on the chip.",
        production="Mono or near-mono like the hardware (modern chip-pop pans channels a little), bright, harsh "
                   "highs left intact, no reverb or just a short room; square waves clip easily, so leave 1-2 dB "
                   "of headroom and watch inter-sample peaks. Modern chiptune adds real drums, synth bass and "
                   "sidechain.",
        theory="Constraint drives the style: with three or four monophonic voices harmony becomes melodic "
               "(arpeggios), counterpoint replaces pads and duty-cycle changes stand in for orchestration, giving "
               "Baroque-like counterpoint at rock tempos.",
        mix=Mix(lufs=(-14, -9), lra=(3, 7), low_end="light", tone="bright", width="narrow"),
    ),
    Genre(
        name="jrpg",
        family="film and games",
        aliases=("jrpg music", "rpg music", "japanese rpg"),
        parent="video game",
        description="Japanese role-playing-game music: lyrical, emotionally direct themes over pop-classical "
                    "harmony, battle themes with prog-rock drive, town waltzes and sweeping world-map orchestration.",
        era="Japan, from Dragon Quest and Final Fantasy (1986-87) through the PlayStation era to today",
        touchstones=("Nobuo Uematsu Final Fantasy", "Koichi Sugiyama Dragon Quest", "Yasunori Mitsuda Chrono Trigger",
                     "Yoko Shimomura Kingdom Hearts", "Motoi Sakuraba", "Shoji Meguro Persona", "Keiichi Okabe NieR"),
        tempo=(70, 180),
        feel="Scene by scene: lyrical Andante themes, 3/4 or 6/8 town and field themes, 140-180 BPM battle themes "
             "in driving 16ths with odd-metre bars, fanfares for victory",
        swing=50,
        modes=("major", "minor", "dorian", "harmonic minor"),
        keys=("C major", "D major", "Eb major", "A minor", "E minor", "B minor"),
        progressions=(
            "IVmaj7-V7-iii7-vi7",
            "I-V6-vi-iii6-IV-I6-ii7-V7",
            "I-bVI-bVII-I",
            "minor: VI-VII-V-i",
            "minor: i-iv-VII-III-VI-iiø7-V7-i",
        ),
        harmonic_rhythm=1,
        harmony="Pop-classical hybrid: the Royal Road progression (IVmaj7-V7-iii7-vi), Canon-style descending "
                "basses, descending-fifths sequences and harmonic-minor dominants from Baroque models, major 7ths "
                "and add9s for sentiment, the bVI-bVII-I victory fanfare, a step-up modulation for the last "
                "statement, diminished passing chords. Battle themes sit in minor with VI-VII-V-i and syncopated "
                "rock chord stabs.",
        voicing="spread",
        comping="arpeggio_updown",
        bass_style="root",
        bass="Melodic bass with stepwise descents (Canon and lament lines), octave-pumping 8ths on bass guitar or "
             "synth in battles, waltz or walking basses in towns, pedals under world-map themes.",
        melody_density="medium",
        melody_scale="major",
        melody="Long, singable themes in clear 8-bar phrases with an emotional climax (appoggiaturas on the major "
               "7th or 9th resolving down), as likely to end on the 3rd or 5th as the tonic; leitmotifs reused "
               "across the game (main theme on the world map, slow piano version for sad scenes, march for the "
               "finale); battle leads in fast 16ths on synth, guitar or violin.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "X..x..x.X..x....",
            "snare":      "....X.......X...",
            "closed hat": "x.x.x.x.x.x.x.x.",
            "crash":      "X...............",
        }},
        drums="Rock kit or electronic drums drive battle themes (busy hats, 16th fills, a crash on every section), "
              "timpani and snare for marches and boss themes, light shaker and tambourine for towns, nothing for "
              "emotional piano themes.",
        form=(("intro (stabs)", 4), ("A (melody)", 16), ("B (contrast, relative key)", 16), ("C (bridge or solo)", 16),
              ("A' (turnaround)", 8), ("transition to loop", 2)),
        instruments=("strings", "piano", "flute and oboe", "harp", "brass", "synth lead", "electric guitar",
                     "bass guitar", "drum kit", "choir"),
        sound_design="Two eras: SNES/PS1 samples (bright short-looped strings, flute, pizzicato, synth brass) and "
                     "modern live orchestra plus rock band. Recreate the first with vintage romplers (Roland "
                     "SC-88, JV-1080) or lo-fi sample sets, the second with full orchestral libraries; harp "
                     "arpeggios and flute/oboe solos for fields and towns, distorted guitar and organ in battles, "
                     "piano for sad scenes.",
        production="Clear and bright, melody front and centre, moderate hall (1.8-2.2 s) on orchestral cues, a "
                   "tighter rock mix with compressed drums and bass on battles, wide strings. Loop-ready edits; "
                   "OST releases mastered around -14 to -12 LUFS.",
        theory="Emotion through clear functional and pop harmony with classical procedures: the Royal Road delays "
               "the tonic for longing, sequences and descending basses add Baroque gravity, and leitmotif reuse "
               "lets themes gather meaning over a 40-hour game.",
        mix=Mix(lufs=(-18, -12), lra=(6, 14), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="game ambient",
        family="film and games",
        aliases=("exploration music", "open world music", "sandbox game music", "game ambience"),
        parent="video game",
        description="Sparse, unobtrusive exploration music for open-world and sandbox games: soft piano and pads, "
                    "long silences, slow modal harmony and fragmentary motifs that can play for hours without "
                    "fatigue.",
        era="2000s-present (Minecraft, Breath of the Wild, Journey, indie exploration games)",
        touchstones=("C418 Minecraft", "Manaka Kataoka The Legend of Zelda: Breath of the Wild",
                     "Austin Wintory Journey", "Disasterpeace Hyper Light Drifter", "Lena Raine", "Kumi Tanioka"),
        tempo=(50, 100),
        feel="Free, slow and breathing (Lento, Andante), notes placed with lots of space and no felt downbeat; "
             "phrases separated by 10-60 seconds of silence",
        swing=50,
        modes=("lydian", "major", "dorian", "major pentatonic"),
        keys=("C lydian", "F major", "G major", "D dorian"),
        progressions=(
            "Iadd9-II-Iadd9-II",
            "major: IVmaj7-Iadd9-IVmaj7-Iadd9",
            "major: Imaj7-iii7-IVmaj7-vi7",
            "dorian: i9-IVadd9-i9-IVadd9",
        ),
        harmonic_rhythm=0.25,
        harmony="Slow, consonant and unresolved: maj7, add9, sus2 and lydian II chords drifting between two or "
                "three sonorities, plagal (IV-I) rather than dominant motion, pentatonic note fields so phrases "
                "fit in any order, and modal shifts (major to lydian or dorian) for biome or time-of-day changes.",
        voicing="spread",
        comping="sustain",
        bass_style="pedal",
        bass="Barely there: a low piano note or soft sub pad holding the root for whole phrases, occasionally "
             "stepping down; no rhythmic bass.",
        melody_density="sparse",
        melody_scale="major pentatonic",
        melody="Fragmentary piano, celesta or harp phrases of 3-7 notes, pentatonic so they fit any chord in the "
               "field, played rubato with long decays and silence between; the game's main theme appears only as "
               "hints and fragments.",
        groove={"step": 0.5, "swing": 50, "pattern": {
            "triangle": "x.......",
            "shaker":   "....o...",
        }},
        drums="Normally none; at most soft textural percussion (brushed frame drum, light shaker, wind chimes, "
              "tiny glitch clicks) fading in at moments of discovery. Adaptive systems add a light pulse when "
              "enemies are near and remove it afterwards.",
        form=(("silence / world ambience", 8), ("phrase A (piano)", 8), ("pad swell", 8), ("phrase B (variation)", 8),
              ("silence", 8), ("phrase A' (fragment)", 8)),
        instruments=("soft or felt piano", "warm synth pads", "celesta or glockenspiel", "harp",
                     "field recordings", "soft strings", "music box"),
        sound_design="Gentle timbres with soft attacks: felt piano, Rhodes, mallets with soft sticks, airy pads "
                     "with slow filter LFOs, granular textures from field recordings; C418-style lo-fi synth piano "
                     "with slight detune and tape noise. Avoid sharp transients and piercing content above about "
                     "6 kHz that tires the ear.",
        production="Low-level and wide, sitting under in-game ambience and effects: deep reverb (4-8 s) and long "
                   "delays, low cut near 60 Hz, barely any compression. Implemented with randomised playback, long "
                   "silences and crossfades, so deliver phrase files and stems rather than one long track.",
        theory="Generative-friendly writing: pentatonic and modal fields remove wrong-note risk so phrases can be "
               "triggered in any order, static plagal harmony avoids goal-directed tension that would compete "
               "with play, and silence is part of the composition.",
        mix=Mix(lufs=(-24, -16), lra=(5, 12), low_end="light", tone="warm", width="wide"),
    ),
    Genre(
        name="musical theatre",
        family="film and games",
        aliases=("musical theater", "broadway", "show tunes", "west end", "musicals"),
        parent="opera",
        description="Broadway and West End song-and-dance storytelling: book songs in AABA and verse-chorus forms, "
                    "character-driven lyrics, and a pit orchestra with brassy show-stoppers, ballads and patter "
                    "songs.",
        era="New York and London, from 1920s Tin Pan Alley shows through the Golden Age (1940s-60s) to "
            "contemporary pop musicals",
        touchstones=("Rodgers and Hammerstein", "Leonard Bernstein West Side Story", "Stephen Sondheim",
                     "Andrew Lloyd Webber", "Alan Menken", "Jason Robert Brown", "Lin-Manuel Miranda Hamilton"),
        tempo=(60, 180),
        feel="Varied by number: swung 4/4 or cut-time two-beat for up-tempo songs, colla voce ballads, waltz and "
             "tango numbers, vamp-till-ready intros; tempos lock to the choreography",
        swing=50,
        modes=("major", "minor", "mixolydian"),
        keys=("Eb major", "Bb major", "F major", "Ab major", "C major", "D minor"),
        progressions=(
            "I-vi-ii7-V7",
            "I-V7/vi-vi-V7/V-ii7-V7-I",
            "I-IV-iv-I",
            "Imaj7-ii7-iii7-IVmaj7-V7sus4-V7",
            "minor: i-imaj7-i7-VI",
        ),
        harmonic_rhythm=2,
        harmony="Tin Pan Alley and jazz-inflected tonal harmony: ii-V-I turnarounds, secondary dominants around "
                "the circle (III7-VI7-II7-V7), diminished passing chords, minor iv for sentiment, the minor line "
                "cliché, and the key change up a half or whole step for the last A or chorus. Contemporary pop "
                "musicals use pop loops and sus chords; Sondheim adds clusters, pedals and ostinato vamps.",
        voicing="drop2",
        comping="quarters",
        bass_style="root_fifth",
        bass="Two-beat root-fifth in cut-time numbers, walking 4 in swing numbers, sustained roots or arpeggios in "
             "ballads; the pit bassist doubles the left hand of the piano-conductor score.",
        melody_density="medium",
        melody_scale="major",
        melody="Text first: melody follows the lyric's natural stresses, the title phrase hooks the start or end "
               "of each A section, ranges suit the character (belt to about D5-E5 for women, A4-Bb4 for men), a "
               "held 'money note' crowns the climax, patter songs run in rapid syllabic 8ths, and reprises reuse "
               "earlier tunes with new words.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":  "X.......X.......",
            "snare": "....x.......x...",
            "ride":  "x...x..xx...x..x",
        }},
        drums="The pit drummer plays for the stage: brushes on ballads, two-beat or swing ride with hi-hat on 2 "
              "and 4 for classic numbers, kicks and fills that catch choreography (stop-time, button endings), "
              "cymbal rolls under the money note, Latin and rock grooves when the story calls for them.",
        form=(("vamp / intro", 4), ("verse", 16), ("A", 8), ("A", 8), ("B (bridge)", 8), ("A", 8),
              ("dance break", 16), ("B (bridge)", 8), ("A (key change, money note)", 8), ("button", 2)),
        instruments=("lead vocals", "piano (conductor)", "reeds (doubling flute, clarinet, sax)", "trumpets",
                     "trombone", "French horn", "strings", "bass", "drum kit", "guitar"),
        sound_design="A pit of 10-25: reed players doubling flute, clarinet and sax, two or three trumpets, "
                     "trombone, horn, a few strings (often padded by keyboard string patches), piano-conductor, "
                     "bass, drums and percussion. Brass shout chords for show-stoppers, strings and woodwinds in "
                     "ballads; for mock-ups combine pop-orchestral libraries, big-band brass and a jazz kit with "
                     "brushes.",
        production="Vocals front and centre with clear diction (presence at 2-5 kHz, gentle de-essing), orchestra "
                   "arranged around them; cast-album sound uses a theatre-like room (1.2-1.8 s) and moderate vocal "
                   "compression while keeping the big ending's lift. Ride CC1/CC11 on strings and brass to follow "
                   "the singer's rubato.",
        theory="Song as drama: verse sets up, AABA or verse-chorus develops, the bridge turns, and the key change "
               "delivers the eleven o'clock payoff, mirroring the character's journey. Harmony comes from Tin Pan "
               "Alley and jazz, and characters often get their own musical style or motif.",
        mix=Mix(lufs=(-16, -10), lra=(6, 12), low_end="moderate", tone="warm", width="wide"),
    ),
    Genre(
        name="anime score",
        family="film and games",
        aliases=("anime", "anime soundtrack", "anime ost", "anime music"),
        parent="cinematic",
        description="Japanese animation scoring: emotional piano and string themes, hybrid orchestral-rock action "
                    "cues, J-pop chord movement (the Royal Road, the Just-the-Two-of-Us cycle) and bright, "
                    "energetic orchestration.",
        era="Japan, 1970s-present (Studio Ghibli films, mecha and shonen series)",
        touchstones=("Joe Hisaishi", "Yoko Kanno Cowboy Bebop", "Shiro Sagisu Neon Genesis Evangelion",
                     "Kenji Kawai Ghost in the Shell", "Yuki Kajiura", "Hiroyuki Sawano Attack on Titan",
                     "Radwimps Your Name"),
        tempo=(70, 180),
        feel="Emotional Andante piano themes with rubato, 140-180 BPM action cues in driving 8ths, J-pop insert "
             "songs, comic stingers on cuts",
        swing=50,
        modes=("major", "minor", "lydian", "dorian"),
        keys=("C major", "D major", "Eb major", "A minor", "E minor"),
        progressions=(
            "IVmaj7-V-iii7-vi",
            "IVmaj7-III7-vi7-v7-I7",
            "vi-IV-V-I",
            "minor: i-VI-VII-V",
            "IVmaj7-V7sus4-V7-iii7-vi7-ii7-V7-Iadd9",
        ),
        harmonic_rhythm=1,
        harmony="J-pop and jazz-tinged: the Royal Road (IVmaj7-V-iii-vi), the Just-the-Two-of-Us cycle "
                "(IVmaj7-III7-vi7-v7-I7, the 'marusa' progression), sus4 dominants that resolve late, secondary "
                "dominants and passing diminished chords, tonic avoidance (phrases start on IV), and half-step "
                "modulations for the final chorus; Ghibli-style scores add lydian and Romantic colour, action "
                "cues use minor loops with power chords.",
        voicing="open",
        comping="arpeggio_updown",
        bass_style="root",
        bass="Electric bass with busy, melodic 8th lines and octave pumps in action and pop cues, orchestral basses "
             "on long roots under emotional themes, synth sub in hybrid battle tracks.",
        melody_density="medium",
        melody_scale="major",
        melody="Strongly melodic, wide-ranging themes with emotional leaps (rising 6ths and 7ths), appoggiaturas on "
               "the major 7th or 9th, syncopated J-pop phrasing; piano or solo violin for sentimental cues, choir "
               "on pseudo-Latin or invented text and belted vocals in hybrid battle themes (Sawano, Kajiura).",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "X...x.x.X...x...",
            "snare":      "....X.......X...",
            "closed hat": "xxxxxxxxxxxxxxxx",
            "crash":      "X...............",
        }},
        drums="Rock and electronic kits drive action and opening-style cues (four-on-the-floor or double-time snare "
              "in choruses, tom fills), orchestral percussion and taiko in epic battles, little or none in "
              "emotional piano cues; comedy uses woodblock, slide whistle and timpani accents.",
        form=(("intro (piano motif)", 4), ("A theme", 16), ("B (build)", 8), ("theme tutti", 16),
              ("breakdown (solo piano)", 8), ("final tutti (half step up)", 16), ("outro", 4)),
        instruments=("piano", "strings", "solo violin", "flute", "brass", "choir", "electric guitar", "bass guitar",
                     "drum kit", "synths"),
        sound_design="Two toolkits: Ghibli-style acoustic orchestra and piano (clear woodwinds, string unisons, "
                     "glockenspiel) and hybrid orchestral rock (distorted guitars, EDM synths and drums layered "
                     "with orchestra and choir). Typical libraries: Cinematic Studio Strings, a bright concert "
                     "grand, Strezov or Hollywood choirs, a sampled rock kit, Serum or Omnisphere synths.",
        production="Bright, clean and present: melody up front, compression on the rock elements, moderate hall "
                   "(1.8-2.2 s) on the orchestra; hybrid tracks mixed dense and mid-forward like J-rock, while "
                   "emotional cues keep wide dynamics. OSTs master around -14 to -10 LUFS.",
        theory="J-pop functional harmony with jazz substitutions stresses longing (starting on IV, delaying the "
               "tonic), and frequent half-step modulations heighten climaxes. Leitmotifs re-orchestrated across "
               "episodes give long-form continuity.",
        mix=Mix(lufs=(-16, -10), lra=(6, 14), low_end="moderate", tone="bright", width="wide"),
    ),
]
