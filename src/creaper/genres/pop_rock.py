"""Pop and rock: from chart pop, K-pop and city pop to classic, alternative and progressive rock."""

from . import Genre, Mix

GENRES = [
    # ------------------------------------------------------------------ pop
    Genre(
        name="pop",
        family="pop",
        aliases=("mainstream", "top 40", "chart pop"),
        description="Mainstream song-first music built for radio and streaming: a big, instantly singable chorus, "
                    "tight three-minute forms and glossy production in which the lead vocal is king.",
        era="US and UK charts since the 1950s; the modern sound from Stockholm and Los Angeles, 1990s-2020s",
        touchstones=("Michael Jackson", "Max Martin", "Taylor Swift", "Dua Lipa", "Ed Sheeran", "The Weeknd"),
        tempo=(90, 130),
        feel="straight eighths and sixteenths; sparse or half-time verses opening into a driving chorus",
        swing=50,
        modes=("major", "minor"),
        keys=("C major", "G major", "D major", "A minor", "F# minor"),
        progressions=(
            "I-V-vi-IV",
            "vi-IV-I-V",
            "IV-I-V-vi",
            "I-vi-IV-V",
            "I-V6-vi-IV",
            "minor: i-VI-III-VII",
        ),
        harmonic_rhythm=1,
        harmony="Four-chord diatonic loops that often run unchanged through verse and chorus, so energy comes from "
                "arrangement and melody, not new chords; the pre-chorus climbs on IV-V or ii-IV and withholds the "
                "tonic; bridges dip to vi or a borrowed bVI; add9 and sus2 colours in guitars and synths; an "
                "up-a-step key change for the last chorus in ballad-leaning songs.",
        voicing="open",
        comping="eighths",
        bass_style="eighths",
        bass="Roots on straight eighths in the chorus, held whole notes or tacet in the verse for contrast; synth "
             "bass doubled by a sub or 808 an octave down; stepwise passing inversions (I-V6-vi) under piano loops; "
             "locks to the kick and is sidechained lightly.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Range about a 10th; verse low, rhythmically busy and conversational, chorus a 3rd to a 5th higher "
               "with longer notes on open vowels; short 2-4 syllable hook cells repeated three or four times; "
               "'melodic math' (matching syllable counts and rhythms between lines); a wordless or one-word "
               "post-chorus hook; stressed syllables always on strong beats.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.....x.x.......",
            "snare":      "....x.......x...",
            "clap":       "....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.",
        }},
        drums="Programmed samples layered with live hits: snare plus clap on 2 and 4, kick pattern changing by "
              "section (sparse verse, syncopated or four-on-the-floor chorus); hats on eighths opening to "
              "sixteenths in the chorus; risers, reversed cymbals and snare rolls into choruses; a one-beat "
              "drop-out right before the chorus lands.",
        form=(("intro", 4), ("verse", 16), ("pre-chorus", 8), ("chorus", 8), ("post-chorus", 8), ("verse", 8),
              ("pre-chorus", 8), ("chorus", 8), ("post-chorus", 8), ("bridge", 8), ("chorus", 16), ("outro", 4)),
        instruments=("lead vocal with stacked harmonies", "drum programming", "synth bass", "piano",
                     "acoustic or electric guitar", "synth pads and plucks"),
        sound_design="Clean, expensive-sounding: bright plucks and pianos, supersaw or filtered pads in the chorus, "
                     "tight sampled kicks with a sub layer, crisp claps; vocal chops and pitched vocal FX as "
                     "ear-candy; one signature sound that announces the song in the first two seconds.",
        production="Vocal-forward: comped, tuned, de-essed, parallel-compressed, with doubles and harmonies in the "
                   "chorus; something new enters every 4-8 bars; intro under ten seconds and the hook inside the "
                   "first 30 seconds for streaming; bright, wide and loud master.",
        theory="The axis progression (I-V-vi-IV) and its rotations do most of the work; the pre-chorus acts as an "
               "extended dominant preparation, so the chorus feels like arrival even when it starts on IV or vi. "
               "Contrast is engineered by register, rhythm and density rather than harmony.",
        mix=Mix(lufs=(-10, -7), lra=(4, 7), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="dance pop",
        family="pop",
        aliases=("club pop",),
        parent="pop",
        description="Pop built on the dancefloor: four-on-the-floor kicks, house and disco basslines and EDM-style "
                    "builds under a diva-sized vocal and a chorus made to be shouted in a club.",
        era="New York and Europe, 1980s (Madonna); global chart dominance in the late 2000s-2010s",
        touchstones=("Madonna", "Kylie Minogue", "Lady Gaga", "Rihanna", "Calvin Harris", "Dua Lipa"),
        tempo=(115, 130),
        feel="four-on-the-floor, straight sixteenths",
        swing=50,
        modes=("minor", "major"),
        keys=("A minor", "F minor", "C# minor", "G minor"),
        progressions=(
            "i-VI-III-VII",
            "VI-VII-i-i",
            "i-iv-VII-III",
            "i-v-VI-VII",
            "major: I-V-vi-IV",
        ),
        harmonic_rhythm=1,
        harmony="Minor-key loops of four chords that never resolve with a V-i, giving bittersweet euphoria; the "
                "same loop drives verse, chorus and drop; house piano or synth stabs voice the chords; builds "
                "hold one chord or a pedal while a riser climbs.",
        voicing="close",
        comping="stabs",
        bass_style="octaves",
        bass="Disco octave bass or off-beat house bass between the kicks; a sub layer sidechained hard to the kick "
             "for the pumping feel; roots only, so the chord loop stays clear; drops out in the build.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="Chant-like chorus hooks on 1-3 notes, often a title phrase repeated; belted top notes around a "
               "6th above the verse; a synth or vocal-chop 'drop' hook in place of a second chorus vocal; call-and-"
               "response between lead and gang vocals.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x...x...x...x...",
            "clap":       "....x.......x...",
            "closed hat": "xxxxxxxxxxxxxxxx",
            "open hat":   "..x...x...x...x.",
        }},
        drums="Kick on every beat, clap or snare on 2 and 4, open hat on the off-beats, closed sixteenths; snare "
              "rolls doubling in speed through 8-bar builds, a white-noise riser and a beat of silence before the "
              "drop; verses sometimes drop to a half-time or kick-only pattern.",
        form=(("intro", 8), ("verse", 16), ("pre-chorus", 8), ("chorus", 16), ("drop", 8), ("verse", 16),
              ("pre-chorus", 8), ("chorus", 16), ("drop", 8), ("breakdown", 8), ("build", 8), ("chorus", 16),
              ("outro", 8)),
        instruments=("lead vocal", "four-on-the-floor drum programming", "sidechained synth bass", "house piano",
                     "supersaw lead", "risers and FX"),
        sound_design="Punchy club kick, layered clap, saw stabs and supersaw leads with sidechain pumping, house "
                     "piano (M1-style), plucks through ping-pong delay, white-noise risers and impact downlifters.",
        production="Kick and bass own the low end with heavy sidechain; vocal bright and compressed to sit over a "
                   "loud track; arrangement planned in 8-bar blocks with DJ-friendly intro; master loud and dense "
                   "but with punch kept by the sidechain gaps.",
        theory="Aeolian loops (i-VI-III-VII) avoid the leading tone, so there is no cadence to stop the motion: the "
               "track feels endless, suited to dancing. Tension comes from builds (pedal points, rhythmic "
               "acceleration, filter sweeps) rather than harmonic dominants.",
        mix=Mix(lufs=(-8, -6), lra=(3, 6), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="synth-pop",
        family="pop",
        aliases=("synthpop", "technopop"),
        parent="new wave",
        description="Pop played on synthesizers and drum machines: cool, melodic and often melancholy, with "
                    "sequenced basslines, catchy synth riffs and a detached vocal.",
        era="UK and Germany, late 1970s-mid 1980s; revived constantly since",
        touchstones=("Depeche Mode", "The Human League", "Pet Shop Boys", "Yazoo", "Eurythmics", "OMD"),
        tempo=(100, 135),
        feel="straight, machine-tight eighths and sixteenths",
        swing=50,
        modes=("minor", "major"),
        keys=("C minor", "A minor", "D minor", "F major"),
        progressions=(
            "i-VI-V",
            "i-VI-III-VII",
            "i-VII-VI-VII",
            "i-iv-VII-III",
            "major: I-V-vi-iii-IV",
        ),
        harmonic_rhythm=1,
        harmony="Simple triads in minor keys, often with the major V for a dramatic turn (i-VI-V); a single riff "
                "over a pedal bass; chords voiced as sustained string-machine pads or short brass stabs; little "
                "use of 7ths, which keeps it stark.",
        voicing="close",
        comping="arpeggio_up",
        bass_style="eighths",
        bass="Sequenced analog bass on relentless eighths or sixteenths, often octave-jumping; roots under the "
             "pads; the bass sequence is frequently the main hook.",
        melody_density="medium",
        melody_scale="minor",
        melody="Cool, narrow-range verse (a 5th or 6th), sung low and deadpan; chorus lifts an octave or switches "
               "to a soaring female or falsetto line; instrumental synth riffs as memorable as the vocal, played "
               "monophonically in 4- or 8-bar phrases.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x...x...x...x...",
            "snare":      "....x.......x...",
            "clap":       "....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.",
        }},
        drums="LinnDrum, DMX or Simmons: kick on the beats or 1 and 3, snare plus handclap on 2 and 4 with gated "
              "reverb, eighth-note hats; programmed fills on electronic toms; no swing, everything quantised.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("instrumental", 8), ("verse", 16), ("chorus", 8),
              ("bridge", 8), ("chorus", 16), ("outro", 8)),
        instruments=("analog polysynth", "monosynth bass", "drum machine", "string machine", "lead vocal",
                     "sampler stabs"),
        sound_design="Juno, Jupiter, Prophet-5 and DX7 patches: square and saw leads, PWM string pads, brassy "
                     "stabs, Fairlight or Emulator sample hits; gated reverb on snare; chorus and analog delay on "
                     "everything.",
        production="Clean separation, each synth in its own register; vocals dry and close or with plate reverb; "
                   "drum machine upfront; period masters dynamic, modern revivals louder.",
        theory="Minor-mode triads with harmonic-minor V give an urgent, slightly gothic tension; repetition of a "
               "sequenced ostinato against changing chords creates pedal-point dissonance that defines the sound.",
        mix=Mix(lufs=(-11, -8), lra=(4, 8), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="electropop",
        family="pop",
        aliases=("electro-pop",),
        parent="synth-pop",
        description="The harder, club-ready descendant of synth-pop: distorted synth bass, electro-house energy and "
                    "big, often icy hooks, with a confident, sometimes ironic vocal.",
        era="UK, Sweden and US, mid 2000s-2010s",
        touchstones=("Robyn", "La Roux", "Goldfrapp", "Chvrches", "Marina and the Diamonds", "Lady Gaga"),
        tempo=(100, 130),
        feel="straight sixteenths, punchy and quantised",
        swing=50,
        modes=("minor", "major"),
        keys=("A minor", "E minor", "F# minor", "C major"),
        progressions=(
            "i-VI-III-VII",
            "i-VII-VI-VII",
            "VI-III-VII-i",
            "iv-VI-i-VII",
            "major: vi-IV-I-V",
        ),
        harmonic_rhythm=1,
        harmony="Minor-key loops with bright major chords around them (VI and III), so chorus hooks feel happy and "
                "sad at once ('crying on the dancefloor'); stabs and supersaws rather than sustained pads; chord "
                "changes timed to land exactly on the downbeat with the kick.",
        voicing="close",
        comping="stabs",
        bass_style="syncopated",
        bass="Distorted, detuned saw or square bass in syncopated sixteenths, often doubling the hook riff; sub "
             "below for weight; octave jumps on the 'and' of beats; sidechained to the kick.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="Hooky, repetitive chorus with short phrases and lots of rests; verses half-spoken or clipped; range "
               "about an octave; vocal often double-tracked and processed; synth leads answer the vocal.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x...x...x...x...",
            "snare":      "....x.......x...",
            "closed hat": "x.xxx.xxx.xxx.xx",
            "clap":       "....x.......x...",
        }},
        drums="Drum-machine and electro-house hybrid: 909 or 808 kick, crunchy clap and snare layered, closed hat "
              "sixteenths with gaps, 808 toms and claps for fills; half-time verses into four-on-the-floor "
              "choruses.",
        form=(("intro", 8), ("verse", 16), ("pre-chorus", 8), ("chorus", 16), ("verse", 16), ("pre-chorus", 8),
              ("chorus", 16), ("bridge", 8), ("chorus", 16), ("outro", 8)),
        instruments=("analog and virtual-analog synths", "distorted synth bass", "drum machine", "lead vocal",
                     "vocoder or processed vocal", "arpeggiator"),
        sound_design="Saturated saws, bitcrushed leads, gritty square bass through distortion and filter envelopes, "
                     "arpeggiated plucks; vocals with vocoder, formant shift or heavy tuning as a sound.",
        production="Loud and bright, more aggressive than 80s synth-pop; sidechain everywhere; vocal upfront and "
                   "slightly distorted; stereo synths with a mono, saturated bass.",
        theory="Relies on the relative-major ambiguity of aeolian loops (VI-III-VII-i reads as major until the tonic "
               "returns); rhythmic syncopation in bass and synths against a straight kick drives the energy.",
        mix=Mix(lufs=(-9, -6), lra=(3, 6), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="k-pop",
        family="pop",
        aliases=("kpop", "korean pop"),
        parent="pop",
        description="South Korean idol pop: maximalist, precisely produced songs that switch genre between "
                    "sections (trap verse, EDM drop, R&B bridge), built for group vocals, rap parts and dance "
                    "choreography.",
        era="Seoul, late 1990s idol groups; global from the 2010s",
        touchstones=("BTS", "BLACKPINK", "TWICE", "EXO", "Red Velvet", "NewJeans"),
        tempo=(95, 135),
        feel="straight; sections jump between half-time trap, four-on-the-floor and double-time",
        swing=50,
        modes=("minor", "major"),
        keys=("C# minor", "F minor", "G minor", "E major"),
        progressions=(
            "i-VI-III-VII",
            "i-VII-VI-V",
            "VI-VII-i-i",
            "iv-v-i-i",
            "major: IVmaj7-V7-iii7-vi7",
        ),
        harmonic_rhythm=1,
        harmony="Minor-key loops in the verses, a pre-chorus that climbs to a dominant (V or VII) for a vocal "
                "belt, and choruses that sometimes change key or mode entirely; jazz and R&B 7th chords in "
                "SM-style songs; J-pop royal-road (IVmaj7-V7-iii7-vi7) in brighter girl-group tracks; a final "
                "chorus modulation is common.",
        voicing="close",
        comping="stabs",
        bass_style="808",
        bass="Long 808 slides under trap verses, switching to a punchy synth or slap-style bass in funkier "
             "sections; drops out completely for breakdown bars; heavily layered and loud in the low end.",
        melody_density="busy",
        melody_scale="minor pentatonic",
        melody="Lines split between 4-9 members, each with a distinct register (main vocal, lead vocal, rapper); a "
               "'killing part' hook of 2-4 bars designed with matching choreography; high belted ad-libs from the "
               "main vocal in the last chorus; English-word hooks dropped into Korean lyrics; rap verses on "
               "sixteenth-note triplet flows.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x..x..x...x.....",
            "snare":      "....x.......x...",
            "clap":       "....x.......x..x",
            "closed hat": "xxxxxxxxxxxxxxxx",
        }},
        drums="Each section gets its own kit: trap hats with triplet rolls in rap verses, four-on-the-floor or "
              "moombahton kick in the chorus, live-sounding drums in the bridge; huge snare builds, gunshot or "
              "glass FX and full stops for choreography hits; a dedicated dance break with drum-led groove.",
        form=(("intro", 4), ("verse", 16), ("pre-chorus", 8), ("chorus", 8), ("post-chorus", 8), ("verse", 16),
              ("pre-chorus", 8), ("chorus", 8), ("post-chorus", 8), ("bridge", 8), ("dance break", 8),
              ("chorus", 16), ("outro", 4)),
        instruments=("group vocals and rap", "808 and synth bass", "trap and EDM drums", "brass stabs or synth "
                     "leads", "piano", "vocal chops and FX"),
        sound_design="Big brass hits, whistles, sirens, supersaws and vocal chops; sub-heavy 808s; signature sound "
                     "FX for each idol concept (sword swipes, cash registers); polished Western-style kits.",
        production="Written by international songwriting camps; dense arrangement with a new texture every 4 bars; "
                   "vocals comped line by line per member, heavily tuned and stacked; one of the loudest, most "
                   "limited masters in pop.",
        theory="'Genre-switching' structure: each section can change tempo feel, kit and mode, glued by the hook "
               "and key; modulation up a semitone or to the relative major for the final chorus; borrowed iv and "
               "harmonic-minor V for drama.",
        mix=Mix(lufs=(-7, -5), lra=(3, 6), low_end="heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="j-pop",
        family="pop",
        aliases=("jpop", "japanese pop"),
        parent="pop",
        description="Japanese pop: harmonically rich, melodically dense songs with fast tempos, busy band or "
                    "synth arrangements and soaring choruses, shaped by anime, idol culture and Vocaloid.",
        era="Japan, 1990s (Komuro and Being era) to the 2020s streaming wave",
        touchstones=("Utada Hikaru", "Mr.Children", "Ayumi Hamasaki", "Kenshi Yonezu", "YOASOBI",
                     "Official Hige Dandism"),
        tempo=(100, 175),
        feel="straight, driving eighths and sixteenths; busy, pushed band playing",
        swing=50,
        modes=("major", "minor"),
        keys=("Eb major", "Ab major", "Db major", "C minor", "F# minor"),
        progressions=(
            "IVmaj7-V7-iii7-vi",
            "IVmaj7-III7-vi7-v7-I7",
            "vi-IV-V-I",
            "I-V-vi-iii-IV-I-IV-V",
            "ii7-V7-iii7-vi7",
        ),
        harmonic_rhythm=2,
        harmony="The royal road progression (IV-V-iii-vi, 'oudou shinkou') with 7ths is the default; the "
                "'Just the Two of Us' / Marunouchi progression (IVmaj7-III7-vi7-v7-I7) with secondary dominants; "
                "Komuro's vi-IV-V-I; frequent secondary dominants, diminished passing chords and a half- or "
                "whole-step modulation into the last chorus; chords change every two beats.",
        voicing="open",
        comping="eighths",
        bass_style="syncopated",
        bass="Busy, melodic bass with fills, octave pops and slap in funkier songs; walks between chord tones on "
             "the royal road; pushes sixteenth anticipations into the chorus; never just roots.",
        melody_density="busy",
        melody_scale="major pentatonic",
        melody="One note per mora, so melodies are very dense; wide range (often an octave and a 5th) with a high "
               "tessitura in the chorus (sabi); A-melo verse low and syncopated, B-melo pre-chorus building, sabi "
               "chorus on long high notes; leaps of a 6th and chromatic passing tones; the chorus is often heard "
               "first as an intro hook.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x..x..x.x..x..x.",
            "snare":      "....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.",
            "crash":      "x...............",
        }},
        drums="Live-band energy at high tempos: kick syncopations matching bass pushes, snare on 2 and 4, eighth "
              "hats or ride in the chorus, crash on every phrase start; dense fills into each section; "
              "four-on-the-floor disco variants in idol songs; the drop chorus (ochisabi) strips drums out.",
        form=(("intro", 8), ("A-melo verse", 16), ("B-melo pre-chorus", 8), ("sabi chorus", 16),
              ("interlude", 8), ("A-melo verse", 8), ("B-melo pre-chorus", 8), ("sabi chorus", 16),
              ("C-melo bridge", 8), ("ochisabi drop chorus", 8), ("sabi chorus", 16), ("outro", 8)),
        instruments=("lead vocal", "electric guitars", "busy electric bass", "piano", "strings or synth pads",
                     "live drums"),
        sound_design="Bright, saturated band sound with piano and string section; glossy synth leads and "
                     "Vocaloid-style arpeggios; overdriven guitars doubling fast melodic lines.",
        production="Wall-to-wall arrangement with every instrument busy; vocals bright and upfront; mastered very "
                   "loud (Japanese CD-era loudness); intros start with the chorus or a guitar hook.",
        theory="Functional harmony with jazz colours: secondary dominants (III7 = V7/vi), the minor v7-I7 turn into "
               "IV, and the royal road's avoidance of the tonic, which keeps choruses floating; modulation "
               "(often +1 semitone) is a structural device, not decoration.",
        mix=Mix(lufs=(-8, -5), lra=(3, 6), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="city pop",
        family="pop",
        aliases=("citypop", "japanese city pop"),
        description="Sophisticated Japanese pop of the bubble era: AOR, funk and jazz-fusion harmony, slick session "
                    "playing and an urban, nocturnal glamour; revived worldwide via online rediscovery.",
        era="Tokyo, late 1970s-late 1980s; global revival from the 2010s",
        touchstones=("Tatsuro Yamashita", "Mariya Takeuchi", "Anri", "Miki Matsubara", "Taeko Ohnuki",
                     "Toshiki Kadomatsu"),
        tempo=(90, 130),
        feel="sixteenth-note funk and disco feel with a light lilt",
        swing=54,
        modes=("major", "dorian"),
        keys=("Eb major", "F major", "Bb major", "D major"),
        progressions=(
            "IVmaj7-III7-vi7-v7-I7",
            "ii7-V7-Imaj7-vi7",
            "IVmaj7-V7-iii7-vi7",
            "iii7-VI7-ii7-V7sus4",
            "Imaj7-vi9-ii9-V13",
            "dorian: i7-IV9",
        ),
        harmonic_rhythm=2,
        harmony="Major 7ths, minor 9ths, dominant 13ths and sus4 dominants everywhere; ii-V-I's and circle-of-fifths "
                "chains (iii-VI-ii-V); the Marunouchi IVmaj7-III7-vi7 descent; tritone substitutions and passing "
                "diminished chords in the bridges; modulations up a 3rd for the last chorus.",
        voicing="drop2",
        comping="pulse_16",
        bass_style="syncopated",
        bass="Funky fingerstyle or slap bass in sixteenths with octave pops and ghost notes; walks chromatically "
             "into chord changes; locks with the kick on disco tracks, plays melodic counterlines in ballads.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Smooth, wide-arched melodies (about an octave and a 3rd) with jazz tensions on long notes (9ths, "
               "11ths, 13ths); English-phrase hooks; relaxed, slightly behind-the-beat delivery; lush stacked "
               "backing vocals answering the lead.",
        groove={"step": 0.25, "swing": 54, "pattern": {
            "kick":       "x...x...x...x...",
            "snare":      "....x.......x...",
            "closed hat": "xo.oxo.oxo.oxo.o",
            "open hat":   "..x...x...x...x.",
        }},
        drums="Session-tight live drums: disco four-on-the-floor with open hat off-beats, or backbeat with "
              "sixteenth hats and ghost notes; handclaps and congas; tasteful fills, no drum machine until the "
              "late 80s (then LinnDrum).",
        form=(("intro", 8), ("verse", 16), ("pre-chorus", 8), ("chorus", 16), ("interlude", 8), ("verse", 16),
              ("pre-chorus", 8), ("chorus", 16), ("sax or guitar solo", 16), ("chorus", 16), ("outro", 16)),
        instruments=("Rhodes and acoustic piano", "funky electric bass", "clean cutting guitar", "live drums",
                     "brass section and alto sax", "strings", "DX7 or Prophet synths"),
        sound_design="Rhodes through chorus, clean Stratocaster 'cutting' rhythm guitar, DX7 electric piano and "
                     "bells, lush string sections, punchy brass; analog tape warmth.",
        production="Studio-perfect analog recordings with wide, airy stereo and lots of plate reverb on vocals; "
                   "many layers but clear separation; original masters dynamic, revival remasters louder.",
        theory="Imports American AOR and fusion harmony into Japanese pop: extended chords as the default sonority, "
               "secondary dominants and ii-V chains drive the motion, and the melody sits on chord tensions "
               "rather than roots.",
        mix=Mix(lufs=(-13, -9), lra=(5, 9), low_end="moderate", tone="warm", width="wide"),
    ),
    Genre(
        name="hyperpop",
        family="pop",
        aliases=("pc music", "bubblegum bass"),
        parent="electropop",
        description="Pop pushed to cartoon extremes: pitched-up vocals, clipping 808s, glossy saccharine synths "
                    "and abrupt switches into noise, trance or emo guitar, all in one song.",
        era="London (PC Music) mid 2010s; US internet scene around 2019-2021",
        touchstones=("SOPHIE", "A. G. Cook", "100 gecs", "Charli XCX", "Dorian Electra"),
        tempo=(120, 180),
        feel="straight; fast synths over half-time drums, sudden tempo and feel switches",
        swing=50,
        modes=("major", "minor"),
        keys=("C major", "D major", "F# minor", "B minor"),
        progressions=(
            "I-V-vi-IV",
            "IV-V-vi-I",
            "I-iii-IV-iv",
            "vi-IV-I-V",
            "minor: i-VI-III-VII",
        ),
        harmonic_rhythm=1,
        harmony="Deliberately naive, bubblegum major progressions (I-V-vi-IV, IV-V-vi-I) played on hyper-bright "
                "synths, set against moments of noise and dissonance; the minor iv for nostalgia; trance-style "
                "supersaw chords in climaxes; key changes can be abrupt and unprepared.",
        voicing="spread",
        comping="pulse_16",
        bass_style="808",
        bass="Distorted, clipping 808s with long glides, often louder than everything else; occasional dubstep or "
             "drum'n'bass reese bass in switch-ups; may drop out for pure-synth sections.",
        melody_density="busy",
        melody_scale="major pentatonic",
        melody="Pitched-up, heavily Auto-Tuned vocals with hard tuning artifacts; nursery-rhyme simple hooks on "
               "3-5 notes; screamed or emo-sung sections; wide leaps exaggerated by formant shifting; layered "
               "sped-up doubles.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.....x...x.x...",
            "snare":      "........x.......",
            "clap":       "........x.......",
            "closed hat": "x.x.xxx.x.x.xxxx",
        }},
        drums="Trap skeleton at half-time (snare on 3 of a fast bar) with hat rolls, then sudden switches to "
              "gabber kicks, breakbeats or blast-like double-time; metallic, hyper-compressed one-shots; "
              "glitches and stutter edits as fills.",
        form=(("intro", 4), ("verse", 8), ("chorus", 8), ("verse", 8), ("chorus", 8), ("switch-up", 16),
              ("chorus", 8), ("outro", 4)),
        instruments=("pitched and Auto-Tuned vocals", "distorted 808", "supersaw and bell synths",
                     "metallic percussion", "distorted guitar", "glitch FX"),
        sound_design="SOPHIE-style synthetic, rubbery physical-model sounds, latex snaps, metallic hits; "
                     "candy-bright bells and supersaws; bitcrushing, clipping and extreme pitch shifting as "
                     "musical gestures.",
        production="Intentionally overloud and clipping; extreme contrasts in density; vocals pushed through "
                   "heavy tuning and distortion; songs short (often under 2:30) with switch-ups replacing bridges.",
        theory="Maximal contrast: diatonic, almost childlike harmony is the frame against which noise, distortion "
               "and genre collisions register; form is collage-like, with modulation and tempo change used as "
               "shock rather than preparation.",
        mix=Mix(lufs=(-7, -4), lra=(2, 5), low_end="very heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="bedroom pop",
        family="pop",
        aliases=("lo-fi pop", "bedroom"),
        parent="indie pop",
        description="Intimate, home-recorded pop: jazzy, chorus-soaked guitars, soft drum machines and close, "
                    "murmured vocals, with a deliberately lo-fi, diary-like warmth.",
        era="Internet-era US and UK, mid 2010s",
        touchstones=("Clairo", "Rex Orange County", "Beabadoobee", "Boy Pablo", "Cuco", "Mac DeMarco"),
        tempo=(70, 115),
        feel="laid back, slightly swung, behind the beat",
        swing=54,
        modes=("major", "dorian"),
        keys=("D major", "G major", "E major", "A major"),
        progressions=(
            "Imaj7-vi7-ii7-V7",
            "IVmaj7-iii7-ii7-Imaj7",
            "Imaj7-IVmaj7",
            "IVmaj7-iv7-Imaj7",
            "ii7-V7-Imaj7-IVmaj7",
        ),
        harmonic_rhythm=1,
        harmony="Jazzy 7th chords from guitar shapes (maj7, m7, the borrowed iv7) in slow loops; ii-V movement "
                "without real jazz voice leading; two-chord vamps; chords often slightly detuned or warbly.",
        voicing="open",
        comping="broken",
        bass_style="root",
        bass="Simple, melodic electric or synth bass, roots with passing tones and slides; soft attack, rolled-off "
             "highs; sometimes played on a keyboard by the songwriter.",
        melody_density="sparse",
        melody_scale="major pentatonic",
        melody="Breathy, close-mic'd and quiet; narrow range (a 6th or so) in a comfortable chest voice; "
               "conversational phrasing and diaristic lyrics; doubled softly or layered with harmonies a 3rd up; "
               "short guitar or synth motifs as hooks.",
        groove={"step": 0.25, "swing": 54, "pattern": {
            "kick":       "x.......x.x.....",
            "snare":      "....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.",
            "shaker":     "..x...x...x...x.",
        }},
        drums="Soft drum machine or a lightly played kit: kick and snare on a lazy backbeat, quiet hats, maybe "
              "shaker; lo-fi sampled kits with tape saturation; few fills.",
        form=(("intro", 4), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("bridge", 8),
              ("chorus", 8), ("outro", 8)),
        instruments=("chorus-heavy clean electric guitar", "soft vocal", "electric bass", "drum machine",
                     "cheap keyboard or Rhodes", "synth pad"),
        sound_design="Wobbly tape-chorus guitars, detuned keyboards, warm saturation, vinyl or room noise; drums "
                     "with soft transients; everything slightly wow-and-fluttered.",
        production="Home-studio aesthetic kept on purpose: vocals upfront and dry-ish, mix warm and low-passed, "
                   "gentle compression, room for imperfections; masters quieter than chart pop.",
        theory="Lifts jazz extended chords as colours rather than function, so maj7 and m7 loops float without "
               "cadences; the borrowed iv7 gives a wistful plagal sigh.",
        mix=Mix(lufs=(-14, -10), lra=(5, 9), low_end="light", tone="warm", width="moderate"),
    ),
    Genre(
        name="indie pop",
        family="pop",
        aliases=("indiepop", "twee pop"),
        parent="pop",
        description="Melodic, guitar-based pop from outside the mainstream: jangly guitars, bright tambourine-driven "
                    "grooves and wry, literate songs, ranging from twee to festival-sized synth anthems.",
        era="UK (C86) mid 1980s; global indie scene 2000s-2010s",
        touchstones=("Belle and Sebastian", "Camera Obscura", "Vampire Weekend", "Phoenix", "Alvvays",
                     "Passion Pit"),
        tempo=(100, 145),
        feel="straight, bouncy eighths",
        swing=50,
        modes=("major", "mixolydian"),
        keys=("G major", "D major", "A major", "E major"),
        progressions=(
            "I-IV-vi-V",
            "I-iii-IV-V",
            "IV-I-V-vi",
            "I-vi-IV-V",
            "I-bVII-IV-I",
        ),
        harmonic_rhythm=1,
        harmony="Bright major-key progressions with the iii and vi for sweetness; jangle-friendly open chords and "
                "add9 shapes; occasional borrowed bVII; bridges modulate to the relative minor; more chords per "
                "song than in mainstream pop.",
        voicing="open",
        comping="strum",
        bass_style="eighths",
        bass="Melodic eighth-note bass that moves between roots with passing tones, sometimes Peter Hook-style "
             "high melodies; bouncy and upfront rather than sub-heavy.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Light, unforced vocals, often a 9th or 10th range; wordy verses and an 'oh-oh' or la-la group "
               "chorus; guitar or glockenspiel counter-melodies; falsetto lifts in synthier strands.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.....x.x.......",
            "snare":      "....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.",
            "tambourine": "..x...x...x...x.",
        }},
        drums="Simple, upbeat backbeat with tambourine and handclaps; sometimes motorik or four-on-the-floor kick "
              "in synthier songs; light touch, few fills.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("bridge", 8),
              ("chorus", 16), ("outro", 8)),
        instruments=("jangly electric guitars", "acoustic guitar", "electric bass", "drums and tambourine",
                     "glockenspiel or keyboards", "lead and group vocals"),
        sound_design="Clean Rickenbacker or Telecaster jangle with chorus, warm analog synths, glockenspiel, "
                     "handclaps; brass or strings on bigger arrangements.",
        production="Natural, bright and roomy; vocals not over-processed; less compression than chart pop; "
                   "keyboards and guitars stacked for shimmer.",
        theory="Diatonic major harmony made distinctive through voicing (open strings, add9) and melodic "
               "counterpoint between guitar lines and voice; iii and vi chords supply the bittersweet tint.",
        mix=Mix(lufs=(-12, -9), lra=(5, 9), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="dream pop",
        family="pop",
        aliases=("dreampop",),
        parent="indie pop",
        description="Hazy, atmospheric pop: reverb-washed guitars, slow tempos and breathy, half-heard vocals that "
                    "prize mood and texture over clear words.",
        era="UK and US, early-mid 1980s (4AD); revived 2000s-2010s",
        touchstones=("Cocteau Twins", "Mazzy Star", "Galaxie 500", "Beach House", "Julee Cruise",
                     "Cigarettes After Sex"),
        tempo=(65, 110),
        feel="slow, floating straight eighths",
        swing=50,
        modes=("major", "lydian"),
        keys=("D major", "A major", "E major", "B minor"),
        progressions=(
            "Imaj7-IVmaj7",
            "I-iii-IV-iv",
            "vi-IV-I-V",
            "lydian: I-II",
            "IVmaj7-Imaj7-vi7-V",
        ),
        harmonic_rhythm=0.5,
        harmony="Slow-moving major 7ths, added 9ths and suspended chords, often a two-chord oscillation held for "
                "two bars each; the borrowed iv for melancholy; lydian I-II shimmer; chords ring on open strings "
                "so they blur into each other.",
        voicing="spread",
        comping="arpeggio_updown",
        bass_style="root",
        bass="Simple sustained or eighth-note roots, often soft and low in the mix; occasional melodic high-neck "
             "lines; it anchors the haze rather than drives it.",
        melody_density="sparse",
        melody_scale="major pentatonic",
        melody="Breathy, airy vocals with long held notes and slow stepwise motion; a range of about an octave, "
               "often sung in a soft head voice; words blurred into vowels; doubled and drenched in reverb.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.......x.......",
            "snare":      "....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.",
        }},
        drums="Drum machine (often a basic preset) or soft, steady live kit; plain kick-snare backbeat, quiet "
              "hats; slow tempos and no fills, deliberately hypnotic.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("instrumental", 16),
              ("chorus", 8), ("outro", 16)),
        instruments=("reverb-drenched electric guitar", "organ or synth pad", "breathy vocal", "electric bass",
                     "drum machine", "slide guitar"),
        sound_design="Guitars through chorus, long reverb and tape delay; Farfisa or Vox organ drones; soft "
                     "analog pads; reverse reverb; the sound of a room heard through fog.",
        production="Everything sits in a shared reverb space; vocals tucked into the mix; soft transients and a "
                   "warm, rolled-off top; dynamic, not loud.",
        theory="Harmonic stasis and modal colour (lydian #4, borrowed iv) replace functional cadence; long "
               "harmonic rhythm and sustained common tones make chords bleed together.",
        mix=Mix(lufs=(-13, -9), lra=(5, 9), low_end="moderate", tone="warm", width="wide"),
    ),
    Genre(
        name="art pop",
        family="pop",
        aliases=("avant-pop", "experimental pop"),
        parent="pop",
        description="Pop as an art form: ambitious, conceptual songs that keep pop's hooks and forms but bring in "
                    "unusual harmony, theatrical vocals and experimental production.",
        era="UK and US, late 1960s-1980s; continuously reinvented since",
        touchstones=("Kate Bush", "David Bowie", "Björk", "Peter Gabriel", "St. Vincent", "FKA twigs"),
        tempo=(70, 130),
        feel="varied: straight, tribal tom grooves, or rubato",
        swing=50,
        modes=("major", "minor", "lydian", "dorian"),
        keys=("Ab major", "C minor", "F# minor", "Bb major"),
        progressions=(
            "I-bVI-bVII-I",
            "minor: VI-VII-i-i",
            "lydian: Imaj7-II7",
            "dorian: i7-IV7-i7-VIImaj7",
            "minor: i-bII-i-VII",
        ),
        harmonic_rhythm=1,
        harmony="Modal mixture and unexpected chords inside pop frames: bVI-bVII-I and VI-VII-i cadences, lydian "
                "II, phrygian bII, chromatic mediants; pedal points under shifting chords; sudden key changes for "
                "dramatic effect.",
        voicing="open",
        comping="sustain",
        bass_style="pedal",
        bass="Pedal tones and ostinatos that hold against moving harmony, or fretless and synth basses with "
             "melodic slides; drops in and out with the drama.",
        melody_density="medium",
        melody_scale="dorian",
        melody="Theatrical and wide: leaps over an octave, character voices, whispers to wails; hooks often "
               "rhythmic or wordless; melodies built on modal notes (raised 6th in dorian, #4 in lydian).",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.....x...x.....",
            "floor tom":  "x..x..x...x..x..",
            "snare":      "........x.......",
            "shaker":     "x.x.x.x.x.x.x.x.",
        }},
        drums="Tom-heavy, tribal or hypnotic patterns (gated-reverb toms, LinnDrum ostinatos), programmed "
              "beats with world-percussion sounds, or no drums at all for long stretches; no cymbals as a "
              "deliberate choice.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("interlude", 16),
              ("bridge", 8), ("chorus", 16), ("outro", 16)),
        instruments=("lead vocal", "Fairlight or modern sampler", "piano", "synthesizers", "orchestral strings",
                     "tom-heavy drums"),
        sound_design="Fairlight and sample-based textures, found sounds, processed choirs, orchestral and folk "
                     "instruments repurposed; each song gets its own palette.",
        production="Production is part of the composition: extreme contrasts, unusual panning, vocals layered as "
                   "choirs or set very dry; masters keep their dynamics.",
        theory="Uses modal mixture and pedal points to undercut pop's tonic-dominant expectations; the aeolian "
               "VI-VII-i ascent and lydian II give an uplift without a V chord.",
        mix=Mix(lufs=(-13, -9), lra=(6, 11), low_end="moderate", tone="neutral", width="wide"),
    ),
    Genre(
        name="power pop",
        family="pop",
        aliases=("powerpop",),
        parent="pop",
        description="Beatles melodies played with Who-sized guitars: crunchy, upbeat, harmony-rich songs with "
                    "short forms, big hooks and a youthful ache.",
        era="UK and US, early 1970s; revivals late 1970s and 1990s",
        touchstones=("Big Star", "Badfinger", "The Raspberries", "Cheap Trick", "The Knack", "Weezer"),
        tempo=(120, 165),
        feel="straight, driving eighths",
        swing=50,
        modes=("major", "mixolydian"),
        keys=("E major", "A major", "D major", "G major"),
        progressions=(
            "I-IV-V-IV",
            "I-iii-IV-V",
            "I-III7-vi-IV",
            "I-bVII-IV-I",
            "IV-V-I-vi",
        ),
        harmonic_rhythm=1,
        harmony="Beatles-derived major-key writing: the III7 secondary dominant (V/vi), borrowed bVII and iv, "
                "suspended chords resolving; pre-choruses built on IV-V; key changes and stop-time breaks before "
                "the last chorus.",
        voicing="power",
        comping="eighths",
        bass_style="eighths",
        bass="Driving root eighths, McCartney-style melodic runs at section changes, walking up to the IV; locks "
             "with the kick and pushes into the downbeats.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Bright, high tenor melodies with a yearning edge, range about a 10th; chorus hooks with stacked "
               "three-part harmonies; 'ooh' backing parts; guitar solos that restate the melody.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.....x.x.......",
            "snare":      "....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.",
            "tambourine": "....x.......x...",
        }},
        drums="Energetic backbeat with eighth-note hats or ride in the chorus, crash on the one of each section, "
              "snare-roll pickups and fills on toms; Keith Moon energy kept tidy.",
        form=(("intro", 4), ("verse", 16), ("pre-chorus", 4), ("chorus", 8), ("verse", 16), ("pre-chorus", 4),
              ("chorus", 8), ("guitar solo", 8), ("bridge", 8), ("chorus", 16), ("outro", 4)),
        instruments=("crunchy electric guitars", "12-string or jangle guitar", "electric bass", "drums",
                     "lead and harmony vocals", "piano"),
        sound_design="Marshall or Vox crunch, Rickenbacker 12-string jangle, double-tracked rhythm guitars panned "
                     "hard; clean, punchy drums.",
        production="Guitars layered wide, vocals with bright doubles and harmonies, tight two-and-a-half to three "
                   "minute arrangements; polished but rocking.",
        theory="Pop harmonic language (secondary dominants, modal mixture) delivered with rock rhythm; the III7 "
               "to vi move and IV-iv-I plagal tricks give the bittersweet power-pop sound.",
        mix=Mix(lufs=(-10, -8), lra=(4, 7), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="pop ballad",
        family="pop",
        aliases=("piano ballad", "ballad"),
        parent="pop",
        description="The slow, emotional showpiece: piano or guitar-led songs that build from an intimate verse to a "
                    "belted, orchestrated climax, often with a final key change.",
        era="Tin Pan Alley roots; the modern form from 1970s-1990s power ballads to the 2010s",
        touchstones=("Whitney Houston", "Celine Dion", "Elton John", "Adele", "Sam Smith", "Lewis Capaldi"),
        tempo=(60, 85),
        feel="slow straight eighths, sometimes a lilting 12/8 feel",
        swing=50,
        modes=("major", "minor"),
        keys=("C major", "Eb major", "Bb major", "A minor"),
        progressions=(
            "I-V6-vi-I64-IV-I6-ii7-V",
            "I-V6-vi-IV",
            "vi-IV-I-V",
            "IV-V-iii-vi",
            "IVadd9-I6-ii7-Vsus4",
        ),
        harmonic_rhythm=1,
        harmony="Descending bass lines through inversions (I-V6-vi), suspended dominants (Vsus4-V), ii7 and IV "
                "pre-dominants, secondary dominants (V7/vi) and a truck-driver modulation (up a semitone or tone) "
                "for the last chorus; the chorus often starts on IV for lift.",
        voicing="open",
        comping="broken",
        bass_style="whole",
        bass="Absent or a sustained pedal in verse one; enters with long whole and half notes on roots and "
             "inversions, moving stepwise; gets more rhythmic only in the final chorus.",
        melody_density="medium",
        melody_scale="major",
        melody="Wide range (an octave and a 5th) with a low, intimate verse and a belted chorus; long phrases with "
               "melisma at line ends; a climactic sustained top note in the final chorus; the bridge reaches the "
               "highest pitch before a breath-pause.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.......x.x.....",
            "snare":      "....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.",
        }},
        drums="Tacet in verse one; brushes, side stick or a soft kit in verse two; full backbeat with big tom "
              "fills and cymbal swells in the last chorus; timpani or orchestral hits at the climax.",
        form=(("intro", 4), ("verse", 8), ("pre-chorus", 4), ("chorus", 8), ("verse", 8), ("pre-chorus", 4),
              ("chorus", 8), ("bridge", 8), ("chorus", 8), ("chorus", 8), ("outro", 4)),
        instruments=("grand piano", "lead vocal", "strings", "acoustic or electric bass", "drums",
                     "acoustic guitar"),
        sound_design="Close-mic'd grand piano, lush string section or pads, soft electric piano; big hall reverb "
                     "on the climax; choir pads in the final chorus.",
        production="Arrangement as a dynamic arc: piano and voice, then layers added each section; vocal riding "
                   "and heavy automation; dynamic master with a wider loudness range than uptempo pop.",
        theory="Classical voice-leading habits inside pop: stepwise descending bass via first and second "
               "inversions, plagal and suspended cadences, and modulation as the emotional peak.",
        mix=Mix(lufs=(-12, -9), lra=(6, 11), low_end="moderate", tone="warm", width="wide"),
    ),
    # ------------------------------------------------------------------ rock
    Genre(
        name="rock",
        family="rock",
        aliases=("rock music",),
        description="Guitar, bass and drums with attitude: riff-driven songs on a heavy backbeat, built around "
                    "electric guitars, power chords and a voice that cuts through a loud band.",
        era="US and UK, from 1960s rock and roll onward",
        touchstones=("The Rolling Stones", "Led Zeppelin", "The Who", "Tom Petty", "Bruce Springsteen",
                     "Foo Fighters"),
        tempo=(100, 140),
        feel="straight eighths on a heavy backbeat",
        swing=50,
        modes=("major", "mixolydian", "minor"),
        keys=("E major", "A major", "D major", "G major", "E minor"),
        progressions=(
            "I-bVII-IV-I",
            "I-IV-V-IV",
            "I-bIII-IV-I",
            "vi-IV-I-V",
            "I-V-IV-I",
            "minor: i-VII-VI-VII",
        ),
        harmonic_rhythm=1,
        harmony="Power chords and open triads; mixolydian I-bVII-IV and the bIII from the minor pentatonic are "
                "the rock fingerprint; IV-V-IV turnarounds; chord changes often stated as riffs rather than "
                "block chords; sus4 and add9 embellishments on open strings.",
        voicing="power",
        comping="eighths",
        bass_style="eighths",
        bass="Pick or finger eighths on the root, following the guitar riff or locking with the kick; walk-ups "
             "into chord changes; octaves and 5ths in choruses.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="Melodies over major chords lean on the minor pentatonic for grit (blue 3rd against the major "
               "chord); range about a 10th with a high, belted chorus; short title hooks; guitar riffs act as "
               "the second hook.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.....x.x.......",
            "snare":      "....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.",
            "crash":      "x...............",
        }},
        drums="Live kit: kick on 1 and the 'and' of 3, snare cracking on 2 and 4, eighth-note hats in the verse "
              "opening to ride or crash in the chorus; tom fills into every section, crash on the downbeat.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("guitar solo", 16),
              ("bridge", 8), ("chorus", 16), ("outro", 8)),
        instruments=("electric guitars", "electric bass", "drum kit", "lead vocal", "Hammond organ or piano"),
        sound_design="Overdriven tube amps (Marshall, Fender, Vox), humbucker or single-coil crunch, clean "
                     "arpeggios for verses; natural room sound on the drums.",
        production="Two or more rhythm guitars panned hard left and right, vocal and snare in the centre, room "
                   "mics for drum size; moderate bus compression; mixes built to feel like a band in a room.",
        theory="Rock harmony is pentatonic and modal rather than functional: bVII and bIII come from the minor "
               "pentatonic laid over a major key, so the blue 3rd and b7 rub against the tonic chord.",
        mix=Mix(lufs=(-10, -8), lra=(4, 8), low_end="moderate", tone="neutral", width="wide"),
    ),
    Genre(
        name="classic rock",
        family="rock",
        aliases=("album rock", "70s rock"),
        parent="rock",
        description="The canon of late-60s and 70s rock: blues-based riffs, big drums, virtuoso guitar solos and "
                    "album-length ambition, recorded on analog tape.",
        era="UK and US, 1965-1980",
        touchstones=("Led Zeppelin", "The Rolling Stones", "Lynyrd Skynyrd", "Queen", "Creedence Clearwater Revival",
                     "The Who"),
        tempo=(90, 140),
        feel="straight eighths with a loose, human push and pull; some shuffles",
        swing=50,
        modes=("major", "minor", "mixolydian"),
        keys=("A major", "E major", "D major", "G major", "A minor"),
        progressions=(
            "I-bVII-IV-I",
            "minor: i-VII-VI-VII",
            "I-bIII-IV-I",
            "I-IV-I-V",
            "I7-I7-I7-I7-IV7-IV7-I7-I7-V7-IV7-I7-V7",
        ),
        harmonic_rhythm=1,
        harmony="Blues-derived: 12-bar forms, I-bVII-IV mixolydian vamps, the aeolian i-VII-VI descent; "
                "sus4-to-major hammer-ons on open chords (Keith Richards, Pete Townshend); riffs built from the "
                "minor pentatonic; piano and organ add 7ths.",
        voicing="power",
        comping="eighths",
        bass_style="root_fifth",
        bass="Roots, 5ths and octaves with blues walk-ups; often doubling the main guitar riff an octave down; "
             "melodic runs at turnarounds (John Paul Jones, John Entwistle).",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="Bluesy, belted vocals with wide range and screams at the top; call-and-response with guitar "
               "fills; pentatonic hooks; long guitar solos with string bends and repeating licks over 16-32 bars.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.......x.x.....",
            "snare":      "....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.",
            "crash":      "x...............",
        }},
        drums="Big, live, roomy drums with a lot of feel: kick and snare backbeat, washy hats or ride, heavy "
              "tom fills (Bonham-style triplets), cowbell and tambourine overdubs.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("guitar solo", 24),
              ("verse", 16), ("chorus", 16), ("outro", 16)),
        instruments=("Les Paul or Stratocaster through tube amps", "electric bass", "drum kit", "Hammond organ",
                     "piano", "lead vocal"),
        sound_design="Cranked Marshall stacks, Leslie-speaker organ, honky-tonk or grand piano; drums recorded "
                     "with distant room mics; tape saturation everywhere.",
        production="Analog 16- or 24-track tape, little editing, performance over perfection; drums big and "
                   "ambient, guitars panned; mastered with dynamics intact (original LPs ~-14 LUFS, remasters "
                   "louder).",
        theory="Mixes blues tonality (dominant 7ths, blue notes, 12-bar) with modal rock harmony: the bVII and "
               "bIII from minor pentatonic over a major key are its defining borrowed chords.",
        mix=Mix(lufs=(-13, -9), lra=(6, 10), low_end="moderate", tone="warm", width="wide"),
    ),
    Genre(
        name="alternative rock",
        family="rock",
        aliases=("alternative", "alt rock", "college rock"),
        parent="rock",
        description="The rock that grew outside the mainstream and then took it over: angular or droning guitars, "
                    "loud-quiet-loud dynamics, odd chord moves and introspective lyrics.",
        era="US and UK college radio, 1980s; mainstream from 1991",
        touchstones=("R.E.M.", "Pixies", "Radiohead", "The Smashing Pumpkins", "Weezer", "Foo Fighters"),
        tempo=(90, 150),
        feel="straight eighths, dynamic contrasts between restrained verses and loud choruses",
        swing=50,
        modes=("major", "minor"),
        keys=("E minor", "G major", "D major", "A minor"),
        progressions=(
            "I-III-IV-iv",
            "minor: i-iv-III-VI",
            "vi-IV-I-V",
            "I-bIII-IV-bVI",
            "IV-I-V-vi",
        ),
        harmonic_rhythm=1,
        harmony="Chromatic mediant and borrowed chords used as hooks (I-III-IV-iv, bIII and bVI from the "
                "parallel minor); power chords moved by unusual intervals; drones on open strings over moving "
                "bass; verse and chorus often on different progressions to sharpen the dynamic jump.",
        voicing="power",
        comping="eighths",
        bass_style="eighths",
        bass="Driving eighths that outline the progression, often carrying the melody in quiet verses (Kim Deal "
             "style) while guitars drop out; locks to the kick in the loud chorus.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="Mumbled or restrained verses an octave below a shouted or soaring chorus; melodies with "
               "non-chord tones and drones; range about an octave and a 3rd; falsetto hooks in the Radiohead "
               "strand.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.x...x.x.x.....",
            "snare":      "....x.......x...",
            "open hat":   "x.x.x.x.x.x.x.x.",
            "crash":      "x...............",
        }},
        drums="Quiet verse on hats or rim, then loud chorus on washy open hats or crash-ride; driving tom-heavy "
              "fills (Dave Grohl), sometimes motorik; dynamics are the main arrangement tool.",
        form=(("intro", 8), ("verse", 16), ("pre-chorus", 4), ("chorus", 8), ("verse", 16), ("pre-chorus", 4),
              ("chorus", 8), ("bridge", 8), ("guitar break", 8), ("chorus", 16), ("outro", 8)),
        instruments=("distorted and clean electric guitars", "electric bass", "drum kit", "lead vocal",
                     "occasional keyboards or strings"),
        sound_design="Fuzz pedals (Big Muff, DS-1), chorus-laden clean tones, Rickenbacker jangle in the 80s "
                     "strand; noise and feedback as texture; dry, punchy drums.",
        production="Loud-quiet-loud arrangement automated into the mix; walls of double-tracked distorted "
                   "guitars in choruses; 90s mixes punchy and compressed (Butch Vig, Andy Wallace).",
        theory="Borrowed and chromatic-mediant chords (III, bIII, bVI, iv) give an uneasy major/minor ambiguity; "
               "dynamic form replaces harmonic contrast as the main source of drama.",
        mix=Mix(lufs=(-10, -7), lra=(4, 8), low_end="moderate", tone="neutral", width="wide"),
    ),
    Genre(
        name="indie",
        family="rock",
        aliases=("indie rock",),
        parent="alternative rock",
        description="Guitar rock from independent labels and its descendants: wiry riffs, interlocking guitar "
                    "parts, wry or earnest vocals and a deliberately unpolished, live feel.",
        era="US and UK, mid 1980s; garage-revival and festival indie in the 2000s",
        touchstones=("Pavement", "Built to Spill", "Modest Mouse", "The Strokes", "Arctic Monkeys", "The National"),
        tempo=(90, 140),
        feel="straight, nervy eighths",
        swing=50,
        modes=("major", "minor"),
        keys=("E major", "A major", "D major", "B minor", "F# minor"),
        progressions=(
            "I-iii-vi-IV",
            "vi-V-IV-I",
            "I-IV-vi-V",
            "Iadd9-IVmaj7",
            "minor: i-III-VII-iv",
        ),
        harmonic_rhythm=1,
        harmony="Diatonic progressions made distinctive by voicing: add9, open-string drones, partial chords and "
                "two interlocking guitar lines that imply the harmony; occasional unresolved maj7s; minor-key "
                "songs lean on III and VII.",
        voicing="open",
        comping="eighths",
        bass_style="eighths",
        bass="Melodic, often busy eighths that counter the guitars; walks through passing tones; in the Strokes "
             "strand, straight root eighths doubling the kick drive everything.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Conversational, talk-sung verses with wry phrasing; range around an octave; chorus hooks often "
               "a repeated phrase or 'ooh'; vocals sometimes deliberately flat-affect or through a lo-fi filter.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.....x...x.....",
            "snare":      "....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.",
        }},
        drums="Tight, dry backbeat with eighth hats; disco-punk off-beat hats or motorik pulses in the 2000s "
              "strand; fills short and functional; drummer often plays the same pattern through the whole song.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("bridge", 8),
              ("guitar break", 8), ("chorus", 8), ("outro", 8)),
        instruments=("two electric guitars", "electric bass", "drum kit", "lead vocal", "occasional synth or "
                     "keys"),
        sound_design="Clean to light-crunch guitars (Telecaster, Jazzmaster, small combos), lead-and-rhythm "
                     "interplay panned left and right; dry drums; lo-fi or room-mic aesthetic.",
        production="Live-band feel with minimal overdubs; less compression and gloss than mainstream rock; vocals "
                   "sit inside the band rather than on top.",
        theory="Harmony is often implied by counterpoint between two guitars and bass rather than stated in full "
               "chords, producing open 5ths, 9ths and dyads that blur the chord quality.",
        mix=Mix(lufs=(-12, -9), lra=(5, 9), low_end="moderate", tone="warm", width="wide"),
    ),
    Genre(
        name="hard rock",
        family="rock",
        aliases=("arena rock", "heavy rock"),
        parent="classic rock",
        description="Rock turned up: loud, riff-centred songs with distorted guitars, a pounding backbeat, "
                    "shredding solos and a screaming high vocal, built for arenas.",
        era="UK and US, late 1960s-1980s",
        touchstones=("AC/DC", "Deep Purple", "Van Halen", "Aerosmith", "Guns N' Roses", "Def Leppard"),
        tempo=(100, 150),
        feel="straight, heavy eighths",
        swing=50,
        modes=("major", "minor", "mixolydian"),
        keys=("A major", "E major", "E minor", "D major"),
        progressions=(
            "I5-bVII5-IV5-I5",
            "I-bIII-IV-I",
            "minor: i-VII-VI-VII",
            "I-bVI-bVII-I",
            "I-IV-I-V",
        ),
        harmonic_rhythm=1,
        harmony="Power chords and riff-based harmony from the minor pentatonic over a major key: I-bVII-IV, "
                "bIII and bVI-bVII-I (the 'arena' cadence); open-string pedal riffs; power ballads add big sus and "
                "add9 chords.",
        voicing="power",
        comping="eighths",
        bass_style="eighths",
        bass="Relentless pumping root eighths locked to the kick (Cliff Williams style), or doubling the riff; "
             "few fills so the guitar owns the space.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="High, raspy belted vocals (tenor range up to A4-C5 and beyond) with screams; gang-shouted chorus "
               "hooks; pentatonic melody with blue notes; solos of 8-16 bars with tapping, bends and fast runs.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.......x.x.....",
            "snare":      "....X.......X...",
            "closed hat": "X.x.X.x.X.x.X.x.",
            "crash":      "x...............",
        }},
        drums="Simple, huge and steady: kick on 1 and 3, cracking snare on 2 and 4, hats or ride on eighths; "
              "crash accents with the riff, stops and big tom fills; tempo rock-solid.",
        form=(("intro riff", 8), ("verse", 16), ("pre-chorus", 8), ("chorus", 8), ("verse", 16),
              ("pre-chorus", 8), ("chorus", 8), ("guitar solo", 16), ("bridge", 8), ("chorus", 16),
              ("outro", 8)),
        instruments=("distorted electric guitars", "electric bass", "drum kit", "lead vocal", "gang vocals",
                     "Hammond organ"),
        sound_design="Cranked Marshall with humbuckers, mid-forward crunch rather than metal scoop; big snare "
                     "with plate or gated room; Hammond through distorted Leslie (Deep Purple).",
        production="Rhythm guitars doubled hard left and right, lead vocal and snare dominant in the centre; big "
                   "room drums; Mutt Lange-style layered backing vocals in the 80s strand.",
        theory="The minor pentatonic is the harmonic engine: its b3, b7 and b6 become the bIII, bVII and bVI "
               "power chords, played over a major tonic for swagger.",
        mix=Mix(lufs=(-10, -7), lra=(4, 7), low_end="heavy", tone="neutral", width="wide"),
    ),
    Genre(
        name="blues rock",
        family="rock",
        aliases=("heavy blues",),
        parent="classic rock",
        description="The blues electrified and amplified: 12-bar and shuffle forms, dominant 7th chords and long, "
                    "expressive guitar solos played at rock volume.",
        era="UK blues boom, mid 1960s; Texas revival 1980s; garage-blues 2000s",
        touchstones=("Cream", "The Jimi Hendrix Experience", "The Allman Brothers Band", "ZZ Top",
                     "Stevie Ray Vaughan", "The Black Keys"),
        tempo=(70, 130),
        feel="shuffle (triplet swing), or straight heavy eighths",
        swing=50,
        modes=("major", "minor", "mixolydian"),
        keys=("E major", "A major", "G major", "A minor"),
        melody_scale="blues",
        progressions=(
            "I7-I7-I7-I7-IV7-IV7-I7-I7-V7-IV7-I7-V7",
            "I7-IV7-I7-I7-IV7-IV7-I7-I7-V7-IV7-I7-V7",
            "minor: i7-i7-i7-i7-iv7-iv7-i7-i7-VI7-V7-i7-V7",
            "I7-bVII-IV-I",
            "I-bIII-IV-I",
        ),
        harmonic_rhythm=1,
        harmony="Dominant 7th chords on I, IV and V (all three are dominants, against classical rules); 12-bar "
                "with quick-change and turnaround (V-IV-I-V); minor blues with the bVI7-V7 turnaround; riffs on "
                "the minor pentatonic and blues scale over major chords.",
        voicing="power",
        comping="eighths",
        bass_style="boogie",
        bass="Shuffle boogie lines (root-3rd-5th-6th-b7) on the triplet swing, or doubling the main riff; walks up "
             "chromatically into the IV.",
        melody_density="medium",
        melody="Call-and-response: vocal phrase, then guitar answer, in 2-bar units of the 12-bar; blue notes "
               "(b3, b5, b7) bent against major chords; AAB lyric structure; solos built from repeated licks and "
               "long bends with vibrato.",
        groove={"step": 1 / 3, "swing": 50, "pattern": {
            "kick":       "x.....x.....",
            "snare":      "...x.....x..",
            "ride":       "x.xx.xx.xx.x",
        }},
        drums="Shuffle on the ride or hats (long-short triplet), backbeat on 2 and 4, kick on 1 and 3; or a "
              "straight, heavy rock beat; fills in triplets; the drummer follows the soloist's dynamics.",
        form=(("intro", 4), ("verse", 12), ("verse", 12), ("guitar solo", 24), ("verse", 12), ("guitar solo", 12),
              ("verse", 12), ("outro", 4)),
        instruments=("overdriven electric guitar", "electric bass", "drum kit", "lead vocal", "Hammond organ",
                     "harmonica"),
        sound_design="Stratocaster or Les Paul into a pushed tube amp (Fender, Marshall, Dumble), Tube Screamer, "
                     "fuzz, wah; Hammond with Leslie; slide guitar.",
        production="Live trio feel with minimal overdubs, solos recorded in one pass; warm, mid-forward mix; guitar "
                   "panned centre or slightly off; dynamics left in.",
        theory="Blues tonality: dominant 7ths as stable tonic chords, the b3/major 3rd clash, and the blues scale's "
               "b5 passing tone; the 12-bar's three 4-bar phrases (statement, repeat over IV, answer over V-IV).",
        mix=Mix(lufs=(-12, -9), lra=(5, 9), low_end="moderate", tone="warm", width="wide"),
    ),
    Genre(
        name="psychedelic rock",
        family="rock",
        aliases=("psychedelia", "acid rock", "psych rock", "psych"),
        parent="rock",
        description="Rock that bends perception: drones, modal jams, backwards tapes, fuzz and phasing, Indian and "
                    "studio-experimental colours, and songs that dissolve into long improvisations.",
        era="San Francisco, London and Texas, 1966-1970; neo-psych revival 2010s",
        touchstones=("The Jimi Hendrix Experience", "Pink Floyd", "The 13th Floor Elevators", "Jefferson Airplane",
                     "The Doors", "Tame Impala"),
        tempo=(70, 130),
        feel="loose straight eighths, often stretched into jams",
        swing=50,
        modes=("major", "mixolydian", "dorian"),
        keys=("E major", "A major", "D major", "E minor"),
        progressions=(
            "I-bVII-IV-I",
            "dorian: i7-IV7",
            "I-II7-IV-I",
            "minor: i-VII-VI-VII",
            "I-bVI-bVII-I",
        ),
        harmonic_rhythm=0.5,
        harmony="Modal vamps held for bars at a time (dorian i-IV, mixolydian I-bVII), drones on the tonic, "
                "lydian II major chords, chromatic shifts; long single-chord jams; sitar-like drones and "
                "unresolved sus chords.",
        voicing="open",
        comping="arpeggio_updown",
        bass_style="syncopated",
        bass="Melodic and roaming over static harmony; riffs and ostinatos that the band jams over; pedal tones "
             "under shifting guitar chords.",
        melody_density="medium",
        melody_scale="mixolydian",
        melody="Hypnotic, chant-like vocal melodies in a narrow modal range; drones and repeated phrases; "
               "Eastern-sounding melismas (mixolydian, dorian); long improvised guitar or organ solos.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.......x.x.....",
            "snare":      "....x.......x...",
            "ride":       "x.x.x.x.x.x.x.x.",
            "tambourine": "x.x.x.x.x.x.x.x.",
        }},
        drums="Loose, jazzy rock drumming (Mitch Mitchell, Ringo): busy fills, rolling toms, ride-led grooves; "
              "tabla or hand percussion in Eastern-flavoured songs; neo-psych uses compressed, phased breakbeats.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("jam", 32),
              ("verse", 16), ("outro", 16)),
        instruments=("fuzz electric guitar", "Farfisa or Hammond organ", "electric bass", "drum kit", "sitar",
                     "Mellotron", "lead vocal"),
        sound_design="Fuzz Face and Uni-Vibe, wah, tape-flanging and phasing, Leslie-speaker vocals, backwards "
                     "guitar and cymbals, tape echo; in neo-psych, phaser-drenched synths and compressed drums.",
        production="The studio as an instrument: extreme panning, tape loops, varispeed, automated phasing; "
                   "mixes swirl and move; dynamic masters.",
        theory="Modal harmony and drones replace functional progressions; static tonics invite improvisation in "
               "dorian or mixolydian, and the lydian II major chord adds a dreamy brightness.",
        mix=Mix(lufs=(-14, -10), lra=(6, 12), low_end="moderate", tone="warm", width="wide"),
    ),
    Genre(
        name="garage rock",
        family="rock",
        aliases=("60s garage", "garage rock revival"),
        parent="rock",
        description="Raw, primitive rock and roll played by amateurs at full volume: three chords, fuzz guitar, "
                    "a cheap combo organ and a snarling vocal, recorded fast and dirty.",
        era="US, 1963-1968; revival in the early 2000s",
        touchstones=("The Sonics", "The Kingsmen", "The Troggs", "The Stooges", "The White Stripes", "The Hives"),
        tempo=(110, 170),
        feel="straight, bashing eighths",
        swing=50,
        modes=("major", "mixolydian"),
        keys=("A major", "E major", "G major", "D major"),
        progressions=(
            "I-IV-v-IV",
            "I-IV-V-IV",
            "I-bIII-IV-I",
            "I-bVII-IV-I",
            "I-IV-I-V",
        ),
        harmonic_rhythm=2,
        harmony="Three or four chords at most, often a two-bar I-IV-V-IV riff repeated all song; bVII and bIII "
                "from blues; chords bashed as barre or power chords; organ doubles the riff.",
        voicing="power",
        comping="eighths",
        bass_style="eighths",
        bass="Root eighths following the riff exactly; in revival duos the bass is absent and the guitar's low "
             "strings cover it.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="Shouted, sneering vocals with screams, narrow range on the verse, a chanted title in the chorus; "
               "fuzz guitar or organ riff as the main hook; short, wild solos.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.x...x.x.x...x.",
            "snare":      "....x.......x...",
            "open hat":   "x.x.x.x.x.x.x.x.",
        }},
        drums="Bashing, slightly sloppy backbeat with washy open hats or crash-ride; floor-tom pounding; few "
              "cymbals or a single crash; tempos rush in the chorus.",
        form=(("intro", 4), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("guitar solo", 8),
              ("chorus", 8), ("outro", 4)),
        instruments=("fuzz electric guitar", "Farfisa or Vox Continental organ", "electric bass", "drum kit",
                     "shouted lead vocal", "tambourine"),
        sound_design="Fuzz boxes (Maestro, Tone Bender), small overdriven combos, Vox AC30 grit, cheesy combo "
                     "organ; drums recorded with one or two mics.",
        production="Mono or narrow stereo, recorded live in one or two takes, distortion everywhere including the "
                   "vocal; revival records keep the rawness but are louder.",
        theory="Harmony reduced to riff: the I-IV-V(v)-IV cell is rock and roll's 'Louie Louie' loop, and the "
               "minor v makes it mixolydian; energy comes from tempo and distortion, not chords.",
        mix=Mix(lufs=(-11, -8), lra=(4, 8), low_end="moderate", tone="neutral", width="moderate"),
    ),
    Genre(
        name="surf rock",
        family="rock",
        aliases=("surf", "surf guitar"),
        parent="rock",
        description="Instrumental guitar rock from Southern California: spring-reverb-drenched Fender guitars, "
                    "tremolo-picked melodies, driving drums and an exotic, minor-key thrill.",
        era="Southern California, 1961-1965; revived 1990s",
        touchstones=("Dick Dale", "The Ventures", "The Chantays", "The Surfaris", "The Lively Ones",
                     "Los Straitjackets"),
        tempo=(130, 180),
        feel="fast, driving straight eighths",
        swing=50,
        modes=("minor", "phrygian dominant", "major"),
        keys=("E minor", "A minor", "E major", "D major"),
        progressions=(
            "i-VII-VI-V",
            "phrygian dominant: I-II-I-II",
            "major: I-vi-IV-V",
            "major: I-IV-I-V",
            "i-iv-V-i",
        ),
        harmonic_rhythm=1,
        harmony="The Andalusian descent (i-VII-VI-V) and harmonic-minor V; phrygian dominant I-bII vamps for the "
                "Middle-Eastern flavour; 12-bar and I-vi-IV-V in the major-key strand; chromatic slides between "
                "chords.",
        voicing="open",
        comping="eighths",
        bass_style="root_fifth",
        bass="Picked Precision bass on root-5th or walking eighths, doubling the guitar riff in unison on the "
             "low strings.",
        melody_density="busy",
        melody_scale="harmonic minor",
        melody="Instrumental: lead guitar plays the melody with rapid tremolo picking on the low strings, "
               "glissandos down the neck, and harmonic-minor or phrygian-dominant lines; 8-bar phrases repeated "
               "with key changes.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.......x.......",
            "snare":      "....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.",
            "floor tom":  "x.x.x.x.x.x.x.x.",
        }},
        drums="Driving, tom-heavy surf beat: floor-tom eighths or sixteenths with snare backbeat, rolling tom "
              "patterns as breaks; ride or hats on eighths; snappy, reverb-soaked snare.",
        form=(("intro", 8), ("theme A", 16), ("theme B", 16), ("theme A", 16), ("break", 8), ("theme A", 16),
              ("outro", 8)),
        instruments=("Fender Stratocaster or Jazzmaster", "Fender spring reverb tank", "electric bass", "drum kit",
                     "rhythm guitar", "saxophone or organ"),
        sound_design="Wet spring reverb ('drip'), bright single-coil clean tone at high volume, heavy-gauge strings "
                     "for tremolo picking, tremolo effect on rhythm guitar.",
        production="Early-60s mono or narrow stereo, live in the room; reverb on guitar part of the tone, not added "
                   "after; light low end.",
        theory="Exotic minor colours inside rock: harmonic minor's raised 7th, the phrygian dominant's b2 (I-bII) "
               "and the Andalusian cadence; melody carried entirely by the guitar.",
        mix=Mix(lufs=(-14, -10), lra=(5, 9), low_end="light", tone="bright", width="narrow"),
    ),
    Genre(
        name="shoegaze",
        family="rock",
        aliases=("shoegazing", "nu gaze"),
        parent="alternative rock",
        description="Overwhelming walls of distorted, pitch-bent guitar wash with buried, dreamy vocals: noisy and "
                    "loud, but blissful and melodic underneath.",
        era="UK, 1988-1993; revival 2010s",
        touchstones=("My Bloody Valentine", "Slowdive", "Ride", "Lush", "Swervedriver", "Chapterhouse"),
        tempo=(80, 140),
        feel="steady straight eighths beneath a wash of guitar",
        swing=50,
        modes=("major", "lydian"),
        keys=("E major", "A major", "D major", "B major"),
        progressions=(
            "I-bVII-I-bVII",
            "Iadd9-IVadd9",
            "I-iii-IV-iv",
            "vi-IV-I-V",
            "lydian: I-II",
        ),
        harmonic_rhythm=0.5,
        harmony="Few chords held long; open-string drones and unisons ring through every change so chords smear "
                "together; add9s and sus2s; borrowed bVII and iv; the 'glide guitar' tremolo-arm bend makes every "
                "chord slightly out of tune.",
        voicing="cluster",
        comping="strum",
        bass_style="eighths",
        bass="Simple root eighths or whole notes giving the wash a floor; often the clearest pitch in the mix, "
             "carrying the harmony.",
        melody_density="sparse",
        melody_scale="major pentatonic",
        melody="Breathy, androgynous vocals mixed as one more layer, words barely audible; slow, stepwise "
               "melodies in a narrow range; dual male-female unison vocals; guitar melodies hidden in the noise.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.......x.x.....",
            "snare":      "....x.......x...",
            "ride":       "x.x.x.x.x.x.x.x.",
            "crash":      "x.......x.......",
        }},
        drums="Steady, sometimes driving backbeat buried under guitars; crash-ride wash, tom rolls; occasionally "
              "breakbeat-influenced loops (Madchester crossover).",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("noise section", 16),
              ("chorus", 8), ("outro", 16)),
        instruments=("heavily effected electric guitars", "electric bass", "drum kit", "soft vocals",
                     "occasional synth or sampler"),
        sound_design="Fender Jazzmasters with tremolo arm, fuzz (Big Muff), reverse reverb (Yamaha SPX90), "
                     "shimmer and long delays; guitars layered dozens deep.",
        production="Guitars dominate the stereo field; vocals and drums low in the mix; everything saturated; "
                   "loud and dense masters with little dynamic contrast inside a song.",
        theory="Texture as harmony: microtonal pitch-bend and open-string drones create clusters and beating, so "
               "the ear hears a glowing timbre rather than clear chord changes.",
        mix=Mix(lufs=(-11, -8), lra=(4, 8), low_end="moderate", tone="warm", width="wide"),
    ),
    Genre(
        name="post-rock",
        family="rock",
        aliases=("postrock",),
        parent="alternative rock",
        description="Rock instruments used for texture and slow-building drama rather than songs: mostly "
                    "instrumental pieces that swell from quiet tremolo guitars to cathartic crescendos.",
        era="UK and US, early-mid 1990s; peak in the 2000s",
        touchstones=("Mogwai", "Explosions in the Sky", "Godspeed You! Black Emperor", "Sigur Rós", "Slint",
                     "Tortoise"),
        tempo=(60, 130),
        feel="patient straight eighths, gradually intensifying",
        swing=50,
        modes=("major", "minor"),
        keys=("E major", "A major", "D major", "B minor"),
        progressions=(
            "I-V-vi-IV",
            "vi-IV-I-V",
            "Iadd9-IVmaj7-vi7-V",
            "minor: i-VI-III-VII",
            "I-iii-IV-IV",
        ),
        harmonic_rhythm=0.5,
        harmony="Simple diatonic loops repeated for minutes, changing only in density and dynamics; added 9ths "
                "and maj7s from open strings; pedal tones under moving chords; key shifts or a new loop mark the "
                "climax.",
        voicing="spread",
        comping="arpeggio_up",
        bass_style="root",
        bass="Sparse sustained roots in quiet sections, eighth-note drive in the crescendo; sometimes bowed or "
             "pedal-heavy; often the tune's harmonic anchor while guitars arpeggiate.",
        melody_density="sparse",
        melody_scale="major pentatonic",
        melody="Mostly instrumental: tremolo-picked or delay-repeated guitar melodies in high registers; motifs "
               "of 4-8 notes repeated and layered; Sigur Rós-style falsetto in invented language when vocals "
               "appear.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.......x.......",
            "snare":      "....x.......x...",
            "ride":       "x.x.x.x.x.x.x.x.",
            "floor tom":  "x...x...x...x...",
        }},
        drums="Starts silent or on rims and brushes, then builds through rolling tom patterns to a crash-ride "
              "climax with snare rolls; tempo usually constant while density doubles.",
        form=(("intro", 16), ("build A", 32), ("quiet section", 16), ("build B", 32), ("climax", 32),
              ("coda", 16)),
        instruments=("delay-heavy electric guitars", "electric bass", "drum kit", "glockenspiel", "strings",
                     "piano"),
        sound_design="Clean guitars with long delays and reverbs, EBow and tremolo picking, swelling volume "
                     "pedals; fuzz walls at the peak; strings and glockenspiel for colour.",
        production="Huge dynamic range: quiet passages near silence and climaxes at full force; reverb as space; "
                   "minimal limiting so crescendos really grow.",
        theory="Form by crescendo rather than verse-chorus: repetition with additive layering, dynamic "
               "climaxes and textural change carry the structure while harmony stays static.",
        mix=Mix(lufs=(-16, -11), lra=(8, 16), low_end="moderate", tone="warm", width="wide"),
    ),
    Genre(
        name="math rock",
        family="rock",
        aliases=("mathrock",),
        parent="indie",
        description="Intricate, rhythmically complex rock: odd meters, tapped clean guitar lines, stop-start "
                    "dynamics and interlocking parts that feel like a puzzle but still groove.",
        era="US and UK late 1980s-1990s; Japanese and UK revival 2000s-2010s",
        touchstones=("Don Caballero", "Battles", "This Town Needs Guns", "toe", "Hella", "Covet"),
        tempo=(110, 170),
        meter="7/8",
        feel="odd meters (7/8, 5/4, mixed bars) grouped 2+2+3, with sudden metric shifts",
        swing=50,
        modes=("major", "lydian", "minor"),
        keys=("E major", "A major", "D major", "C# minor"),
        progressions=(
            "IVmaj7-Imaj7-vi7-V",
            "Imaj9-IVmaj7#11",
            "vi9-IVmaj7-Iadd9-V",
            "lydian: Imaj7-II",
            "minor: i9-VImaj7-IIImaj7-VII",
        ),
        harmonic_rhythm=1,
        harmony="Extended, open-string chords (maj7, maj9, add9, #11) borrowed from emo and jazz; lydian "
                "colour; tapped arpeggios that outline chords instead of strumming them; harmonic sequences moved "
                "up the neck.",
        voicing="spread",
        comping="arpeggio_updown",
        bass_style="syncopated",
        bass="Busy, syncopated and melodic, often tapping or playing counterlines; accents the odd-meter grouping "
             "with the kick.",
        melody_density="busy",
        melody_scale="lydian",
        melody="Often instrumental; lead lines are fast tapped arpeggios and hammer-on figures with wide "
               "intervals; when sung, short, gentle phrases across bar lines.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.......x.x...",
            "snare":      "....x.......x.",
            "closed hat": "x.x.x.x.x.x.x.",
        }},
        drums="Precise and busy: odd-meter grooves grouped 2+2+3 or 3+3+2, metric modulation, linear fills, "
              "hits locked to guitar accents, sudden full stops; ride-bell and splash accents.",
        form=(("intro", 8), ("section A", 16), ("section B", 16), ("section A", 8), ("break", 8),
              ("section C", 16), ("climax", 16), ("outro", 8)),
        instruments=("clean electric guitars with tapping", "electric bass", "drum kit", "loop pedal",
                     "occasional trumpet or synth"),
        sound_design="Bright clean guitars (Telecaster, open tunings), compression for tapping, light chorus; "
                     "loops; dry, articulate drums.",
        production="Clear, separated mix so every interlocking part is audible; little reverb; moderate loudness "
                   "to keep transients sharp.",
        theory="Additive meter (7/8 as 2+2+3) and polymetric guitar loops against the drum grouping; harmony "
               "uses lydian and extended chords for a bright, unresolved colour.",
        mix=Mix(lufs=(-12, -9), lra=(5, 10), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="progressive rock",
        family="rock",
        aliases=("prog", "prog rock", "art rock"),
        parent="psychedelic rock",
        description="Ambitious, long-form rock that borrows from classical music and jazz: suites with "
                    "movements, odd meters, virtuoso keyboard and guitar parts and mythic concepts.",
        era="UK, 1969-1977; revivals since",
        touchstones=("Yes", "Genesis", "King Crimson", "Pink Floyd", "Rush", "Emerson, Lake & Palmer"),
        tempo=(70, 150),
        feel="straight, with frequent changes to 7/8, 5/4, 6/8 and 9/8",
        swing=50,
        modes=("major", "minor", "lydian", "dorian"),
        keys=("E major", "A major", "D minor", "F# minor"),
        progressions=(
            "I-V6-vi-iii6-IV-I6-ii7-V",
            "lydian: I-II-vii-I",
            "I-bVI-bVII-I",
            "minor: i-VI-iv-V",
            "dorian: i-IV-i-IV",
        ),
        harmonic_rhythm=1,
        harmony="Classical-style descending bass lines and inversions, modal mixture (bVI-bVII-I), lydian and "
                "dorian vamps, pedal points under shifting chords, and modulations between movements; "
                "quartal and polychordal keyboard voicings in the jazzier bands.",
        voicing="open",
        comping="arpeggio_up",
        bass_style="syncopated",
        bass="Prominent and melodic (Rickenbacker, Chris Squire, Geddy Lee), playing counter-melodies and "
             "unison runs with guitar and keys; Taurus bass pedals under sustained sections.",
        melody_density="medium",
        melody_scale="dorian",
        melody="Long, lyrical vocal lines alternating with extended instrumental themes; motifs that return "
               "across a suite (leitmotif); wide range and high tenor vocals; keyboard and guitar solos built on "
               "scales and arpeggios.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.....x...x.....",
            "snare":      "....x.......x...",
            "ride":       "x.x.x.x.x.x.x.x.",
            "high tom":   "..............xx",
        }},
        drums="Technical and orchestral: odd-meter grooves, ride-bell and cymbal colours, tom-heavy fills, "
              "big kits with gongs, timpani and tuned percussion; meter shifts mark sections.",
        form=(("overture", 16), ("verse", 16), ("chorus", 8), ("instrumental", 32), ("verse", 16), ("chorus", 8),
              ("odd-meter interlude", 16), ("solo", 32), ("reprise", 16), ("finale", 16)),
        instruments=("Hammond organ and Mellotron", "Minimoog", "electric guitars", "Rickenbacker bass",
                     "drum kit with percussion", "12-string acoustic guitar", "lead vocal"),
        sound_design="Mellotron strings and flutes, Moog leads, Hammond through Leslie, 12-string arpeggios, "
                     "church organ and harpsichord; later polysynths.",
        production="Album-oriented and dynamic: long tracks with wide loudness range, detailed stereo staging, "
                   "orchestral layering; masters left dynamic.",
        theory="Classical form (suites, movements, recapitulation) and harmonic devices (stepwise bass via "
               "inversions, modulation, pedal points) combined with modal rock and odd, additive meters.",
        mix=Mix(lufs=(-14, -10), lra=(8, 14), low_end="moderate", tone="warm", width="wide"),
    ),
    Genre(
        name="grunge",
        family="rock",
        aliases=("seattle sound",),
        parent="alternative rock",
        description="Seattle's heavy, sludgy alternative rock: punk energy and Sabbath weight, drop-D power chords, "
                    "loud-quiet-loud dynamics and an anguished, raw vocal.",
        era="Seattle, late 1980s-mid 1990s",
        touchstones=("Nirvana", "Soundgarden", "Alice in Chains", "Pearl Jam", "Mudhoney", "Stone Temple Pilots"),
        tempo=(80, 140),
        feel="straight eighths, heavy and slightly behind the beat",
        swing=50,
        modes=("minor", "major"),
        keys=("E minor", "D minor", "F minor", "C# minor"),
        progressions=(
            "i-iv-III-VI",
            "i-bII-i-VII",
            "i-III-IV-VI",
            "i-i-VI-VII",
            "major: I-bIII-bVII-IV",
        ),
        harmonic_rhythm=1,
        harmony="Power chords moved in parallel through the minor pentatonic and chromatic neighbours (bII, "
                "tritone moves); minor keys with a major IV for a dorian sting; drop-D open-string pedals; verse "
                "on clean arpeggios, chorus on the same progression with distortion.",
        voicing="power",
        comping="eighths",
        bass_style="eighths",
        bass="Heavy root eighths doubling the guitar riff in drop-D, often carrying the melody in clean verses "
             "(Krist Novoselic); thick, slightly overdriven tone.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="Mumbled, low verses jumping to a screamed or howled chorus; melodies outline minor pentatonic "
               "with semitone rubs; harmonised vocals in 4ths and 5ths (Alice in Chains); short, repetitive "
               "hooks.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.x...x.x.x.....",
            "snare":      "....X.......X...",
            "open hat":   "x.x.x.x.x.x.x.x.",
            "crash":      "x...............",
        }},
        drums="Hard-hitting, large-kit drumming: thunderous snare and floor toms, washy open hats or crash-ride "
              "in choruses, quiet hats in verses; big tom fills (Dave Grohl, Matt Cameron); odd meters in "
              "Soundgarden.",
        form=(("intro", 8), ("verse", 16), ("pre-chorus", 4), ("chorus", 8), ("verse", 16), ("pre-chorus", 4),
              ("chorus", 8), ("guitar solo", 8), ("chorus", 16), ("outro", 8)),
        instruments=("distorted electric guitars in drop D", "electric bass", "drum kit", "lead vocal",
                     "clean chorus guitar"),
        sound_design="Big Muff and DS-1 fuzz, Mesa or Marshall amps, small-chorus clean tones; drums big but "
                     "dry; downtuned and slightly detuned guitars.",
        production="Raw-sounding but compressed; double-tracked guitars wide, bass upfront; dynamic jumps "
                   "between clean verses and fuzz choruses; mix dark and heavy in the low mids.",
        theory="Chromatic power-chord riffs (bII, tritone) and minor-pentatonic voice leading avoid functional "
               "cadences; modal mixture (the major IV in minor) adds sourness; dynamics replace modulation.",
        mix=Mix(lufs=(-10, -7), lra=(4, 8), low_end="heavy", tone="dark", width="wide"),
    ),
    Genre(
        name="britpop",
        family="rock",
        aliases=("brit pop", "cool britannia"),
        parent="indie",
        description="1990s British guitar pop looking back to the Beatles, Kinks and Small Faces: anthemic "
                    "singalong choruses, jangly or swaggering guitars and very British lyrics.",
        era="UK, 1993-1997",
        touchstones=("Oasis", "Blur", "Pulp", "Suede", "Supergrass", "The Verve"),
        tempo=(90, 140),
        feel="straight eighths, sometimes a mid-tempo swagger",
        swing=50,
        modes=("major", "mixolydian"),
        keys=("G major", "D major", "A major", "E major"),
        progressions=(
            "I-V6-vi-IV",
            "vi7-I-Vsus4-II7sus4",
            "I-III7-IV-iv",
            "I-bVII-IV-I",
            "I-IV-vi-V",
        ),
        harmonic_rhythm=1,
        harmony="Beatles-era moves: descending bass through I-V6-vi, the III7 and II7 secondary dominants, "
                "IV-iv-I plagal minor, sus4 and add9 open chords ringing on the top strings (Oasis's G and "
                "D shapes with 3rd-fret drones).",
        voicing="open",
        comping="strum",
        bass_style="eighths",
        bass="Root eighths in the anthems, melodic McCartney-style lines in Blur's more pop moments; walks down "
             "with the descending inversions.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Singalong choruses in a narrow, chantable range; nasal, accented vocal delivery; long vowels "
               "stretched over bars; 'la la' and 'oh' hooks; music-hall touches in Blur and Pulp.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.....x.x.......",
            "snare":      "....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.",
            "tambourine": "x.x.x.x.x.x.x.x.",
        }},
        drums="Straight, solid backbeat with tambourine on eighths; occasional baggy Madchester breakbeat; "
              "crash wash in the chorus; simple fills.",
        form=(("intro", 8), ("verse", 16), ("pre-chorus", 8), ("chorus", 8), ("verse", 16), ("pre-chorus", 8),
              ("chorus", 8), ("guitar solo", 16), ("chorus", 16), ("outro", 16)),
        instruments=("strummed acoustic guitar", "overdriven electric guitars", "electric bass", "drum kit",
                     "piano or Mellotron", "strings", "lead vocal"),
        sound_design="Les Paul and Epiphone through Marshall, layered acoustics, Mellotron and string sections, "
                     "Hammond; tambourine and handclaps.",
        production="Walls of overdubbed guitars and loud mastering (Oasis records were early loudness-war "
                   "casualties); vocals with slapback or plate; 60s-inspired arrangements.",
        theory="1960s British pop harmony (secondary dominants, minor iv, descending inversion bass lines) "
               "recast as stadium anthems, with open-string pedal tones droning through the changes.",
        mix=Mix(lufs=(-10, -7), lra=(4, 7), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="new wave",
        family="rock",
        aliases=("new romantic",),
        parent="punk",
        description="Punk's pop-savvy, art-school offshoot: jittery rhythms, choppy guitars and synths, ironic or "
                    "stylish vocals and catchy, compact songs.",
        era="UK and US, 1977-1985",
        touchstones=("Blondie", "Talking Heads", "The Cars", "Devo", "The Police", "Duran Duran"),
        tempo=(110, 160),
        feel="straight, nervy eighths; sometimes disco or reggae-tinged",
        swing=50,
        modes=("major", "minor"),
        keys=("E major", "A major", "D minor", "G major"),
        progressions=(
            "I-bVII-IV-I",
            "vi-IV-V-I",
            "Iadd9-IVadd9-vi-V",
            "I-iii-vi-IV",
            "minor: i-VI-VII-i",
        ),
        harmonic_rhythm=1,
        harmony="Compact triads and power chords played staccato; sus2 and add9 (The Police); synth-pad "
                "versions of rock progressions; bVII mixolydian moves; minor-key romantic songs in the Duran "
                "strand.",
        voicing="close",
        comping="eighths",
        bass_style="eighths",
        bass="Pumping root eighths (The Cars, Blondie) or melodic, funky lines (Talking Heads, Duran Duran's John "
             "Taylor); octave disco bass in dance-leaning songs.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Quirky, clipped or deadpan vocals; short catchy hooks; yelps and falsetto; synth or guitar riffs "
               "as memorable as the vocal; range about an octave.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x...x...x...x...",
            "snare":      "....x.......x...",
            "closed hat": "xxxxxxxxxxxxxxxx",
        }},
        drums="Tight, dry drumming at higher tempos: four-on-the-floor disco-rock, hi-hat sixteenths, Simmons "
              "toms; reggae one-drop and off-beat hats in The Police; drum machines by the mid 80s.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("bridge", 8),
              ("instrumental", 8), ("chorus", 16), ("outro", 8)),
        instruments=("choppy electric guitar", "analog synthesizers", "electric bass", "drum kit or drum machine",
                     "lead vocal", "saxophone"),
        sound_design="Thin, chorused or clean guitars, Prophet-5 and Oberheim synths, Farfisa organ in the early "
                     "years, Simmons toms, gated snare.",
        production="Clean, punchy and bright; drums upfront and dry; synths and guitars in tight interlocking "
                   "parts; masters of the era dynamic.",
        theory="Punk's simplicity made pop: staccato rhythm, open add9 voicings and synth timbres freshen "
               "standard diatonic and mixolydian progressions.",
        mix=Mix(lufs=(-13, -9), lra=(5, 9), low_end="moderate", tone="bright", width="wide"),
    ),
    Genre(
        name="post-punk",
        family="rock",
        aliases=("post-punk revival",),
        parent="punk",
        description="Punk's experimental, darker aftermath: lead bass lines, angular, scratchy guitars, motorik or "
                    "funk-influenced drums and cold, baritone vocals.",
        era="UK, 1978-1984; revival early 2000s and 2020s",
        touchstones=("Joy Division", "Siouxsie and the Banshees", "Gang of Four", "Wire", "The Cure",
                     "Interpol"),
        tempo=(110, 160),
        feel="straight, driving eighths or angular funk sixteenths",
        swing=50,
        modes=("minor", "dorian", "phrygian"),
        keys=("E minor", "A minor", "D minor", "B minor"),
        progressions=(
            "i-VI-i-VI",
            "i-VII-VI-VII",
            "dorian: i-IV-i-IV",
            "i-bII-i-bII",
            "i-v-VI-iv",
        ),
        harmonic_rhythm=0.5,
        harmony="Very few chords: one- or two-chord vamps, often implied by bass riffs and single-note guitar "
                "lines; dissonant open-string dyads, phrygian bII and dorian IV for a cold modal colour; "
                "avoidance of resolution.",
        voicing="spread",
        comping="stabs",
        bass_style="eighths",
        bass="Bass as lead instrument: melodic high-register riffs (Peter Hook, Simon Gallup) on driving eighths, "
             "or funky sixteenth syncopation (Gang of Four); played with a pick, trebly and chorused.",
        melody_density="sparse",
        melody_scale="minor",
        melody="Detached, low baritone or chanted vocals in a narrow range; repetition and drone; shouted "
               "slogans in the funk strand; guitar melodies thin and angular.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.....x.x.....x.",
            "snare":      "....x.......x...",
            "closed hat": "xxxxxxxxxxxxxxxx",
            "floor tom":  "..x.......x.....",
        }},
        drums="Metronomic, motorik or tom-driven patterns (Stephen Morris), sixteenth hats, dry snare; drum "
              "machines and electronic toms; disco-punk off-beat hats in the revival.",
        form=(("intro", 16), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("instrumental", 16),
              ("chorus", 8), ("outro", 16)),
        instruments=("chorused lead bass", "trebly electric guitar", "drum kit or drum machine", "baritone vocal",
                     "synthesizer"),
        sound_design="Bass through chorus and pick attack, scratchy treble guitars with flanger and delay, Syndrums "
                     "and electronic toms, cavernous digital reverb (Martin Hannett).",
        production="Spacious and cold: dry drums placed in big artificial rooms, bass forward, guitars thin and "
                   "wide; dynamics kept, tone dark.",
        theory="Modal minor stasis (aeolian, dorian, phrygian bII) with melodic bass riffs carrying the harmonic "
               "motion; repetition and texture over chord progression.",
        mix=Mix(lufs=(-13, -9), lra=(5, 9), low_end="moderate", tone="dark", width="moderate"),
    ),
    Genre(
        name="soft rock",
        family="rock",
        aliases=("mellow gold", "adult contemporary"),
        parent="rock",
        description="Gentle, melodic 70s rock for the radio: acoustic guitars, electric piano, warm harmonies and "
                    "polished, heartfelt songwriting at relaxed tempos.",
        era="US and UK, early 1970s-early 1980s",
        touchstones=("Fleetwood Mac", "Eagles", "Carole King", "Elton John", "Bread", "America"),
        tempo=(70, 115),
        feel="relaxed straight eighths and sixteenths",
        swing=50,
        modes=("major", "mixolydian"),
        keys=("C major", "G major", "D major", "F major"),
        progressions=(
            "I-V6-vi-IV",
            "Imaj7-IVmaj7-iii7-vi7",
            "ii7-V7-Imaj7-IVmaj7",
            "IVadd9-V-iii7-vi7",
            "I-iii-IV-V",
        ),
        harmonic_rhythm=1,
        harmony="Diatonic progressions softened with maj7, add9 and sus chords; descending bass inversions; "
                "slash-chord colours (IV over V); singer-songwriter piano and acoustic voicings with gentle "
                "secondary dominants.",
        voicing="open",
        comping="strum",
        bass_style="root",
        bass="Smooth, melodic roots and passing tones, often fretless or flatwound; follows inversions; locks with "
             "the kick in a laid-back pocket.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Warm, unstrained vocals in a comfortable range (about an octave and a 2nd); singalong choruses "
               "with lush three-part harmonies (Eagles, Fleetwood Mac); tasteful guitar solos echoing the tune.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.......x.x.....",
            "snare":      "....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.",
            "shaker":     "xoxoxoxoxoxoxoxo",
        }},
        drums="Laid-back, dampened 70s kit (towels on toms), relaxed backbeat, sixteenth shakers and "
              "tambourine; few fills, everything in the pocket.",
        form=(("intro", 4), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("guitar solo", 8),
              ("bridge", 8), ("chorus", 16), ("outro", 8)),
        instruments=("acoustic guitars", "Rhodes or Wurlitzer", "electric bass", "drum kit", "lead and harmony "
                     "vocals", "pedal steel or slide guitar", "strings"),
        sound_design="Dead, warm 70s drums, layered acoustic guitars, Rhodes with tremolo, clean electric with "
                     "light compression; string pads.",
        production="Warm, polished analog production; lush stacked harmonies; little distortion; moderate "
                   "dynamics.",
        theory="Diatonic harmony enriched with 7ths and suspensions and smooth bass voice leading; the "
               "pleasure is in voicing and vocal harmony rather than surprise.",
        mix=Mix(lufs=(-13, -10), lra=(5, 9), low_end="moderate", tone="warm", width="wide"),
    ),
    Genre(
        name="yacht rock",
        family="rock",
        aliases=("west coast aor", "yacht"),
        parent="soft rock",
        description="Smooth, studio-perfect Los Angeles soft rock with jazz chords, R&B grooves and session-ace "
                    "playing: the sound of late-70s sophistication.",
        era="Los Angeles, 1976-1984",
        touchstones=("Steely Dan", "The Doobie Brothers", "Michael McDonald", "Toto", "Christopher Cross",
                     "Boz Scaggs"),
        tempo=(85, 120),
        feel="sixteenth-note R&B groove with a light shuffle; half-time shuffle variants",
        swing=56,
        modes=("major", "dorian"),
        keys=("Eb major", "Bb major", "F major", "Ab major"),
        progressions=(
            "ii9-V13-Imaj9-vi9",
            "IVmaj7-iii7-ii7-Imaj7",
            "iii7-VI7-ii7-V7",
            "IVmaj7-V7sus4-iii7-vi7",
            "Imaj7-bVIImaj7-IVmaj7",
            "dorian: i7-IV9",
        ),
        harmonic_rhythm=2,
        harmony="Jazz harmony in pop songs: ii-V-I chains, slash chords and upper-structure triads (a triad over "
                "a foreign bass), maj9 and 13th chords, Steely Dan's 'mu' major add2 chord, sus4 dominants and "
                "chromatic passing chords; frequent key changes.",
        voicing="rootless",
        comping="push",
        bass_style="syncopated",
        bass="Smooth, syncopated sixteenth-note bass with ghost notes and anticipations, fingerstyle on a "
             "Precision or Jazz bass; walks chromatically between the many chord changes.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Soulful, smooth tenor or baritone vocals with R&B phrasing; melodies resting on 9ths and 11ths; "
               "stacked, falsetto-tinged background vocals (Michael McDonald); sax and guitar solos with jazz "
               "vocabulary.",
        groove={"step": 0.25, "swing": 56, "pattern": {
            "kick":       "x......x..x.....",
            "snare":      "....x..o....x.o.",
            "closed hat": "XoxoXoxoXoxoXoxo",
        }},
        drums="Session-perfect drumming (Jeff Porcaro, Steve Gadd, Bernard Purdie): sixteenth-note hats with "
              "accents, ghost-note snare, half-time shuffles; tight, dry and in the pocket.",
        form=(("intro", 8), ("verse", 16), ("pre-chorus", 8), ("chorus", 8), ("verse", 16), ("pre-chorus", 8),
              ("chorus", 8), ("sax solo", 16), ("chorus", 16), ("outro vamp", 16)),
        instruments=("Rhodes and acoustic piano", "electric bass", "session drums", "clean electric guitars",
                     "alto or tenor saxophone", "synth pads and brass", "lead and background vocals"),
        sound_design="Rhodes through phaser, Yamaha CP-80, clean compressed Strat and Les Paul, Prophet-5 brass and "
                     "pads; flawless, dry drums.",
        production="Meticulous multi-track studio craft, dozens of takes; pristine, warm and wide mixes with "
                   "every instrument clear; dynamic masters.",
        theory="Jazz-pop: extended chords, upper-structure slash chords and ii-V chains give constant harmonic "
               "motion under smooth melodies; sixteenth-note R&B rhythm provides the groove.",
        mix=Mix(lufs=(-13, -10), lra=(5, 9), low_end="moderate", tone="warm", width="wide"),
    ),
]
