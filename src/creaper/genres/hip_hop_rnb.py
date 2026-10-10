"""Hip-hop, R&B and soul: from Stax and Motown to boom bap, trap, drill and alternative R&B."""

from . import Genre, Mix

GENRES = [
    # ------------------------------------------------------------------ hip-hop
    Genre(
        name="hip-hop",
        family="hip-hop",
        aliases=("rap", "rap music"),
        description="Beats built for an MC: a hard kick and snare backbeat, a looped sample or keyboard riff and a "
                    "heavy bass line, leaving the middle of the mix open for the voice and its rhythm.",
        era="The Bronx, 1970s; global by the late 1980s",
        touchstones=("DJ Kool Herc", "Grandmaster Flash", "Run-DMC", "Public Enemy", "Dr. Dre", "Kanye West",
                     "Kendrick Lamar"),
        tempo=(80, 100),
        feel="straight or lightly swung backbeat, snare on 2 and 4, head-nod pocket",
        swing=54,
        modes=("minor", "dorian"),
        keys=("C minor", "F minor", "G minor", "A minor"),
        progressions=(
            "i-VI",
            "i7-iv7",
            "i-VI-III-VII",
            "dorian: i7-IV9",
            "i-iv-VI-V7",
        ),
        harmonic_rhythm=0.5,
        harmony="Loop-based: one to four chords repeated for the whole song, usually lifted from a sample or played "
                "as a 1-2 bar riff; minor 7ths and 9ths from soul and jazz records; changes mark the hook rather "
                "than functional cadences.",
        voicing="open",
        comping="stabs",
        bass_style="syncopated",
        bass="Sub-heavy bass or 808 doubling the kick pattern, root and fifth with an octave pickup into the next "
             "bar; locks to the kick and leaves the snare hits clear; long notes under the hook.",
        melody_density="sparse",
        melody_scale="minor pentatonic",
        melody="The beat's melody is a short sampled or played motif (1-2 bars) that loops; the vocal is rhythmic "
               "speech: flows sit on 16ths, rhyme on the 4th beat or across the bar line, internal rhymes and "
               "triplet pockets; hooks are chanted or sung over 4-8 bars, often a simple pentatonic phrase.",
        groove={"step": 0.25, "swing": 54, "pattern": {
            "kick":       "x.....x...x.....|x.....x..x..x...",
            "snare":      "....x.......x...|....x.......x..o",
            "closed hat": "x.x.x.x.x.x.x.x.|x.x.x.x.x.x.x.x.",
            "open hat":   "................|..............x.",
        }},
        drums="Drum machine or chopped breaks: kick on 1 with syncopated pickups on the 'and' of 2 and 3, a fat "
              "snare or clap on 2 and 4, 8th or 16th hats; fills are drop-outs, a reversed cymbal or a break stab, "
              "rarely tom rolls.",
        form=(("intro", 4), ("verse", 16), ("hook", 8), ("verse", 16), ("hook", 8), ("bridge", 8), ("verse", 16),
              ("hook", 8), ("outro", 4)),
        instruments=("drum machine or sampler", "chopped sample", "808 or sub bass", "keys or synth", "lead vocal",
                     "turntable scratches"),
        sound_design="Punchy kick with a clicky top, crackly snare with room, sampled soul or funk loops filtered "
                     "and pitched, Rhodes and string stabs; vinyl texture optional; the voice is the lead instrument.",
        production="Vocal on top and dry-ish, drums loud and upfront, low end mono and heavy; parallel compression on "
                   "drums; beat drops out for punchlines; 16-bar verses and 8-bar hooks.",
        theory="Rhythm over harmony: the meaning sits in the interaction of flow and backbeat (syncopation, "
               "rhymes landing off the beat, polyrhythmic triplet flows) over a static modal loop.",
        mix=Mix(lufs=(-10, -7), lra=(4, 7), low_end="heavy", tone="warm", width="moderate"),
    ),
    Genre(
        name="boom bap",
        family="hip-hop",
        aliases=("boombap", "golden age hip hop", "east coast hip hop"),
        parent="hip-hop",
        description="Golden-age East Coast hip-hop: dusty chopped samples, a knocking kick ('boom') and cracking "
                    "snare ('bap') with MPC swing, made for lyricism.",
        era="New York, late 1980s to mid 1990s; revived constantly since",
        touchstones=("DJ Premier", "Pete Rock", "Large Professor", "RZA", "Gang Starr", "Nas", "Wu-Tang Clan"),
        tempo=(84, 96),
        feel="swung 16ths (MPC/SP-1200 swing), lazy behind-the-beat snare",
        swing=60,
        modes=("minor", "dorian"),
        keys=("C minor", "D minor", "F minor", "A minor"),
        progressions=(
            "i7-iv7",
            "i9-VImaj7",
            "dorian: i7-ii7",
            "i-VI-iiø7-V7",
            "iv7-v7",
        ),
        harmonic_rhythm=0.5,
        harmony="Whatever the sample gives: jazz and soul minor 7ths, often a single chord or a two-chord loop; "
                "chopped stabs re-sequenced so the harmony stutters; horn hits and piano chops for accents.",
        voicing="open",
        comping="stabs",
        bass_style="syncopated",
        bass="Filtered sample bass or a sampled upright line, often lifted from the same record and pitched down; "
             "plays short notes that follow the kick, sometimes just a low sine boosting the kick.",
        melody_density="sparse",
        melody_scale="minor pentatonic",
        melody="Short sample chops (1-2 bars), piano or horn stabs; scratched hooks cutting up vocal phrases from "
               "other records instead of a sung chorus; flows are dense, multisyllabic and on the beat.",
        groove={"step": 0.25, "swing": 60, "pattern": {
            "kick":       "x.........x.....|x......x..x.....",
            "snare":      "....X.......X...|....X.......X...",
            "closed hat": "x.x.x.xox.x.x.xo|x.x.x.xox.x.x.x.",
            "shaker":     "..x...x...x...x.|..x...x...x...x.",
        }},
        drums="Kicks and snares chopped from funk breaks, layered and truncated; snare on 2 and 4 slightly late; "
              "kick on 1 and the 'and' of 3 with a pickup; hats 8ths with swung 16th ghosts; 55-62% swing on the "
              "MPC; no quantised hi-hat rolls.",
        form=(("intro", 4), ("verse", 16), ("hook", 8), ("verse", 16), ("hook", 8), ("verse", 16), ("hook", 8),
              ("outro", 8)),
        instruments=("MPC or SP-1200", "chopped vinyl samples", "break drums", "sample bass", "turntables", "rap vocal"),
        sound_design="12-bit grit (SP-1200), samples low-passed around 8-10 kHz, kick with sub thump, snare with "
                     "noisy crack and room; vinyl crackle; pitched-down samples for darkness.",
        production="Drums loud and punchy, vocal dry and upfront, mono-ish samples; heavy compression on the drum bus; "
                   "low-pass filtering of the loop under verses, unfiltered on hooks; scratch hooks.",
        theory="Harmony is found rather than written: static modal loops (dorian and aeolian) chosen for mood; the "
               "groove's swing and micro-timing between kick, snare and sample is the defining 'theory'.",
        mix=Mix(lufs=(-11, -8), lra=(4, 7), low_end="heavy", tone="warm", width="moderate"),
    ),
    Genre(
        name="trap",
        family="hip-hop",
        aliases=("trap music", "atlanta trap", "southern trap"),
        parent="hip-hop",
        description="Southern hip-hop built on booming 808s, skittering hi-hat rolls and a half-time snare, with dark "
                    "minor-key bells, pads and orchestral stabs.",
        era="Atlanta, early 2000s; mainstream from the 2010s",
        touchstones=("T.I.", "Gucci Mane", "Young Jeezy", "Lex Luger", "Zaytoven", "Metro Boomin", "Future", "Migos"),
        tempo=(130, 160),
        feel="half-time: snare/clap on beat 3 at the producer's BPM; 16th hats with 32nd and triplet rolls",
        swing=50,
        modes=("minor", "harmonic minor", "phrygian"),
        keys=("F minor", "F# minor", "G minor", "C# minor"),
        progressions=(
            "i-VI",
            "i-iv",
            "i-VI-III-VII",
            "i-VI-iv-V",
            "i-bII",
        ),
        harmonic_rhythm=0.5,
        harmony="Simple minor loops, often one or two chords for the whole song; harmonic minor's raised 7th and the "
                "flat 2 for menace; chords are implied by the melody and 808 more than played as pads.",
        voicing="open",
        comping="sustain",
        bass_style="808",
        bass="Long tuned 808 with distortion, playing the kick rhythm plus rolls into the snare; glides of an octave "
             "or a 5th, root notes on the downbeat; the 808 note follows the chord root (tune it to the key).",
        melody_density="medium",
        melody_scale="harmonic minor",
        melody="A 2-4 bar bell, piano, flute or synth-lead loop in the upper-middle register, often with a counter "
               "melody; vocal flows in triplets (the 'Migos flow'), ad-libs between lines; melodic Auto-Tuned hooks.",
        groove={"step": 0.125, "swing": 50, "pattern": {
            "kick":       "x.......|....x...|........|..x...x.|x.......|........|..x.....|x...x...",
            "clap":       "........|........|X.......|........|........|........|X.......|........",
            "snare":      "........|........|x.......|........|........|........|x.......|....o.o.",
            "closed hat": "x.x.x.x.|x.x.x.x.|x.x.x.x.|xxxxxxxx|x.x.x.x.|x.x.xxxx|x.x.x.x.|x.xxxxxx",
            "open hat":   "........|........|........|........|........|......x.|........|........",
        }},
        drums="TR-808 world: clap and snare stacked on beat 3, syncopated kicks that the 808 doubles, 16th hats with "
              "1/32 and 1/16-triplet rolls, pitch-ramped hats; snare rolls and reverse cymbals into hooks; drop-outs "
              "of the drums for a bar before the drop.",
        form=(("intro", 8), ("hook", 16), ("verse", 32), ("hook", 16), ("verse", 32), ("hook", 16), ("outro", 8)),
        instruments=("TR-808 kit", "808 bass", "bells or plucks", "dark pads or choir", "orchestral brass and strings",
                     "Auto-Tuned vocal"),
        sound_design="Distorted, saturated 808 with a long tail (clip or soft-clip for presence on small speakers), "
                     "crisp clap layered with a snare, tight closed hats; bell and flute presets, choirs and string "
                     "staccatos, reverb-washed leads.",
        production="Very loud masters with clipping on the 808 and drum bus; 808 owns the sub, kick short and "
                   "clicky; vocals with Auto-Tune, doubles and ad-lib throws; producer tags; bars counted at the "
                   "DAW BPM (a 16-bar verse = 32 DAW bars).",
        theory="Half-time rhythmic layering: the snare implies 65-80 BPM while hats run at double time, giving two "
               "simultaneous tempos; harmony is minor-modal and static, with harmonic-minor and phrygian colour.",
        mix=Mix(lufs=(-9, -6), lra=(3, 6), low_end="very heavy", tone="bright", width="moderate"),
    ),
    Genre(
        name="drill",
        family="hip-hop",
        aliases=("brooklyn drill", "ny drill", "new york drill"),
        parent="uk drill",
        description="The drill sound as producers now mean it: UK-style sliding 808s, syncopated half-time snares "
                    "and triplet-pocket hats under dark minor melodies; the Brooklyn and global strain.",
        era="Brooklyn, 2019 onward, from the UK drill template",
        touchstones=("Pop Smoke", "808Melo", "Fivio Foreign", "Sheff G", "Axl Beats", "Sleepy Hallow"),
        tempo=(138, 148),
        feel="half-time with snare on 3, hats in swung triplet-feel groupings, syncopated second snare",
        swing=54,
        modes=("minor", "harmonic minor"),
        keys=("C# minor", "F minor", "F# minor", "A minor"),
        progressions=(
            "i-VI",
            "i-iv-VI-V",
            "i-VI-III-VII",
            "i-v-VI-iv",
            "i-bII",
        ),
        harmonic_rhythm=0.5,
        harmony="Minor-key loops of one to four chords, string or choir pads; harmonic-minor V for tension; vocal "
                "samples (often R&B hooks) pitched and chopped as the melodic bed.",
        voicing="open",
        comping="sustain",
        bass_style="808",
        bass="The signature: 808s that slide (portamento of a 3rd to an octave) between notes in a syncopated "
             "pattern independent of the kick; notes trail across the bar line; distorted and very loud.",
        melody_density="medium",
        melody_scale="harmonic minor",
        melody="Dark piano, strings, choir or sampled vocals in 2-bar phrases; flows are aggressive and percussive, "
               "with call-outs and ad-libs; hooks are chanted, catchphrase-like.",
        groove={"step": 0.25, "swing": 54, "pattern": {
            "kick":       "x.........x.....|x.....x.........",
            "snare":      "........x.......|........x..x....",
            "closed hat": "x..x..x.x..x..x.|x..x..x.x.x.xxx.",
            "rim":        "......x.......x.|..x.............",
        }},
        drums="Half-time snare on 3 with a displaced extra snare in the second bar (on the 'a' of 3 or a 16th "
              "early), hats in 3-3-2 groupings with 1/16-triplet bursts, sparse punchy kick, rim and perc "
              "fills; the 808 pattern carries the groove.",
        form=(("intro", 8), ("hook", 16), ("verse", 32), ("hook", 16), ("verse", 32), ("hook", 16), ("outro", 8)),
        instruments=("drill kit", "sliding 808", "strings", "choir", "piano", "sampled vocal", "rap vocal"),
        sound_design="808s with heavy saturation and glide time 50-150 ms, crisp snare with short reverb, dry hats; "
                     "eerie string ensembles, choir 'ah' pads, piano with low-pass; sampled R&B vocal flipped.",
        production="Extremely loud, clipped masters; 808 dominates below 100 Hz and is distorted for audibility; "
                   "vocals aggressive and upfront with ad-lib stacks; minimal effects on drums.",
        theory="Rhythm displacement is the identity: the snare syncopation breaks the half-time backbeat, the 808 "
               "slides form a counter-melody, and hats imply a tresillo (3+3+2) against 4/4.",
        mix=Mix(lufs=(-8, -6), lra=(3, 6), low_end="very heavy", tone="dark", width="moderate"),
    ),
    Genre(
        name="uk drill",
        family="hip-hop",
        aliases=("london drill", "british drill"),
        parent="chicago drill",
        description="London's re-imagining of drill: sliding 808s and gliding bass, skippy triplet hats and "
                    "syncopated snares at 140, with ominous strings, piano and a cold, bleak mood.",
        era="Brixton and south London, 2012-2016 onward",
        touchstones=("67", "Harlem Spartans", "Headie One", "Digga D", "M1onTheBeat", "Ghosty", "Unknown T"),
        tempo=(138, 146),
        feel="half-time at 140, snare on 3 with off-grid second snare, swung skippy hats",
        swing=56,
        modes=("minor", "harmonic minor", "phrygian"),
        keys=("C# minor", "D# minor", "F minor", "G minor"),
        progressions=(
            "i-VI",
            "i-iv",
            "i-VI-iv-V",
            "i-bII-i-VII",
            "i-VII-VI-V",
        ),
        harmonic_rhythm=0.5,
        harmony="Minor loops with harmonic-minor V and phrygian bII for darkness; long string pads and piano "
                "ostinatos; harmony changes every 2 bars or not at all.",
        voicing="open",
        comping="sustain",
        bass_style="808",
        bass="Sliding 808s or gliding sub bass in syncopated rhythms, many notes per bar, portamento between "
             "pitches a 4th, 5th or octave apart; the bass line is a melody in its own right, inherited from grime "
             "and UK rap.",
        melody_density="medium",
        melody_scale="harmonic minor",
        melody="Eerie string lines, piano or bell ostinatos, choir; flows sit in triplet pockets and change cadence "
               "every few bars, with London slang and hard ad-libs; hooks short and repeated.",
        groove={"step": 0.25, "swing": 56, "pattern": {
            "kick":       "x.........x.....|..x.......x.....",
            "snare":      "........x.......|...x....x.......",
            "closed hat": "x..x..x...x..x..|x..x..x.x..x.x.x",
            "rim":        "......x.......x.|......x....x....",
        }},
        drums="Snare on 3 of bar one, then pushed and doubled in bar two (on the 'a' of 1 plus beat 3), hats in "
              "triplet-feel groupings with gaps, sparse kick, rim and shaker percussion; hats often swung and "
              "pitch-bent.",
        form=(("intro", 8), ("hook", 16), ("verse", 32), ("hook", 16), ("verse", 32), ("hook", 16), ("outro", 4)),
        instruments=("drill kit", "sliding 808", "string ensemble", "piano", "choir pad", "bells", "rap vocal"),
        sound_design="Gliding 808 with saturation, sharp short snare, dry ticky hats; cinematic strings and dark "
                     "pianos, sometimes a plucked or bell lead; little reverb on drums.",
        production="Loud and dry; vocals forward with double tracks on punchlines; 808 and vocal fight for midrange so "
                   "carve 200-500 Hz in the 808; tag at the start.",
        theory="Built on syncopation between snare, hats and 808 slides; the hats imply 12/8 against a 4/4 grid; "
               "minor and harmonic-minor colour with chromatic slides in the bass.",
        mix=Mix(lufs=(-9, -6), lra=(3, 6), low_end="very heavy", tone="dark", width="moderate"),
    ),
    Genre(
        name="chicago drill",
        family="hip-hop",
        aliases=("chiraq drill", "chicago drill music"),
        parent="trap",
        description="The original drill from Chicago's South Side: raw, nihilistic trap with menacing synth brass, "
                    "bells and strings, hard 808s and rapid triplet hats.",
        era="Chicago, 2010-2013",
        touchstones=("Chief Keef", "Young Chop", "Lil Durk", "King Louie", "Lil Reese", "Lil Bibby"),
        tempo=(128, 150),
        feel="half-time, snare/clap on beat 3, rapid hat rolls and triplets",
        swing=50,
        modes=("minor", "harmonic minor"),
        keys=("C minor", "D minor", "F minor", "G minor"),
        progressions=(
            "i-VI",
            "i-VI-VII-i",
            "i-iv",
            "i-VI-iv-V",
            "i-bII",
        ),
        harmonic_rhythm=0.5,
        harmony="One to three minor chords as cheap-synth brass and string stabs; harmonic-minor leading tone in "
                "bell melodies; nothing resolves.",
        voicing="close",
        comping="stabs",
        bass_style="808",
        bass="Booming 808 doubling the kick, fewer slides than UK drill, long sustains on the root; often "
             "distorted to the point of breaking up.",
        melody_density="medium",
        melody_scale="harmonic minor",
        melody="Synth-brass fanfares, glockenspiel and bell loops, horror-movie string motifs; vocals chanted, "
               "melodic and slurred in Auto-Tune, repetitive hooks with gang chants and ad-libs.",
        groove={"step": 0.125, "swing": 50, "pattern": {
            "kick":       "x.......|......x.|........|x...x...|x.......|....x...|........|x.x.....",
            "clap":       "........|........|X.......|........|........|........|X.......|........",
            "closed hat": "x.x.x.x.|xxxxx.x.|x.x.x.x.|x.xxxxxx|x.x.x.x.|x.x.x.x.|xxxxx.x.|xxxxxxxx",
            "crash":      "x.......|........|........|........|........|........|........|........",
        }},
        drums="Clap/snare on 3, kicks clustered and syncopated, constant hat rolls (1/32 and triplets), crashes "
              "on downbeats, snare-roll fills into hooks; aggressive and mechanical.",
        form=(("intro", 8), ("hook", 16), ("verse", 32), ("hook", 16), ("verse", 32), ("hook", 16), ("outro", 8)),
        instruments=("TR-808 kit", "808 bass", "synth brass", "bells", "synth strings", "choir", "rap vocal"),
        sound_design="Fruity Loops-style stock synth brass and orchestra hits, glockenspiel, distorted 808s, bright "
                     "claps; deliberately raw and cheap-sounding.",
        production="Loud, raw mixes; 808 and vocals clipped; minimal polish; heavy ad-lib layering; mixtape tags.",
        theory="Static minor tonality with harmonic-minor menace; rhythmic aggression from hat subdivision changes "
               "(16th, triplet 16th, 32nd) rather than harmonic movement.",
        mix=Mix(lufs=(-9, -6), lra=(3, 6), low_end="very heavy", tone="dark", width="moderate"),
    ),
    Genre(
        name="phonk",
        family="hip-hop",
        aliases=("drift phonk", "phonk rap"),
        parent="memphis rap",
        description="Memphis rap revived through SoundCloud: lo-fi cowbell melodies, distorted 808s and chopped "
                    "Memphis vocal samples; the later 'drift phonk' strain is louder and faster, built for car videos.",
        era="SoundCloud early 2010s; drift phonk from about 2020",
        touchstones=("SpaceGhostPurrp", "DJ Smokey", "Soudiere", "Kordhell", "DVRST", "Ghostface Playa"),
        tempo=(125, 150),
        feel="half-time snare on 3, driving cowbell pattern, hard straight 16ths",
        swing=50,
        modes=("minor", "phrygian"),
        keys=("F minor", "G minor", "A minor", "C# minor"),
        progressions=(
            "i-bII",
            "i-iv",
            "i-VI-VII",
            "i7-iv7",
            "i-VI-V",
        ),
        harmonic_rhythm=0.5,
        harmony="Minimal: a one- or two-chord minor or phrygian vamp; classic phonk loops jazzy minor 7th samples "
                "slowed down; drift phonk carries harmony in the cowbell and 808.",
        voicing="close",
        comping="sustain",
        bass_style="808",
        bass="Heavily distorted 808 following the kick, sliding on drift phonk; plays the root with octave jumps; "
             "often clipped into a square-ish tone.",
        melody_density="busy",
        melody_scale="phrygian",
        melody="The TR-808 cowbell is the lead: tuned to the key, playing fast 16th riffs with 3-3-2 accents; "
               "chopped and pitched Memphis vocal samples answer it; little or no rapping on drift phonk.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.....x...x.....|x.....x.x.......",
            "clap":       "........x.......|........x.......",
            "closed hat": "x.x.x.x.x.x.x.x.|x.x.x.x.xxxxx.x.",
            "cowbell":    "x..x..x.x..x..x.|x..x..x.x.x.x.x.",
        }},
        drums="808 kit with a clap or crunchy snare on 3, punchy syncopated kicks, steady 16th hats; drift phonk "
              "adds hard-clipped kicks and cowbell riffs; classic phonk keeps a lo-fi tape-saturated swing.",
        form=(("intro", 8), ("drop", 16), ("break", 8), ("drop", 16), ("break", 8), ("drop", 16), ("outro", 8)),
        instruments=("TR-808 kit", "808 cowbell", "distorted 808", "Memphis vocal samples", "dark pad", "piano"),
        sound_design="Bitcrushed and tape-saturated samples, pitched-down vocals, 808 cowbell through distortion and "
                     "chorus, 808 clipped hard; drift phonk adds big reverb and a 'wall' of saturation.",
        production="Very loud, clipped masters; sidechained pads; vocal samples heavily processed; arranged in "
                   "8-bar blocks with drops instead of verses.",
        theory="Phrygian bII and a static minor tonic give the menace; the cowbell ostinato's tresillo accents "
               "create cross-rhythm against the half-time backbeat.",
        mix=Mix(lufs=(-8, -5), lra=(3, 5), low_end="very heavy", tone="dark", width="moderate"),
    ),
    Genre(
        name="cloud rap",
        family="hip-hop",
        aliases=("based music", "cloud hip hop"),
        parent="hip-hop",
        description="Hazy, dreamlike rap: reverb-drenched ethereal samples and pads over slow, sparse trap drums, "
                    "with drifting, half-sung delivery.",
        era="Internet era, roughly 2009-2013 (Bay Area, New York, Stockholm)",
        touchstones=("Clams Casino", "Lil B", "A$AP Rocky", "Main Attrakionz", "Yung Lean", "Bladee"),
        tempo=(60, 80),
        feel="slow, floating; snare on 2 and 4 at this BPM (= half-time trap at double), trap-style hat rolls",
        swing=52,
        modes=("minor", "major"),
        keys=("Eb minor", "F minor", "A minor", "Db major"),
        progressions=(
            "i9-VImaj7",
            "iv9-i9",
            "i-VI-III-VII",
            "major: Imaj7-IVmaj7",
            "VImaj7-VII-i",
        ),
        harmonic_rhythm=0.5,
        harmony="Lush, unresolved extended chords drowned in reverb; pitched vocal samples that sound like pads; "
                "major 7th and minor 9th colours; long chords, slow change.",
        voicing="spread",
        comping="sustain",
        bass_style="808",
        bass="Soft, long 808s or sub swells under the chord root, few notes; never aggressive; sometimes no bass "
             "at all, just the reverb tail.",
        melody_density="sparse",
        melody_scale="minor pentatonic",
        melody="Pitched and stretched vocal samples, choir-like; the rapper's delivery is laid-back, slurred and "
               "melodic, falling behind the beat; hooks are mantras.",
        groove={"step": 0.125, "swing": 52, "pattern": {
            "kick":       "x.......|........|....x...|........|x.......|..x.....|........|........",
            "snare":      "........|x.......|........|x.......|........|x.......|........|x.....o.",
            "closed hat": "x...x...|x...x...|x...x...|x.x.xxxx|x...x...|x...x...|x...x...|x.x.x.x.",
            "open hat":   "........|........|..x.....|........|........|........|..x.....|........",
        }},
        drums="Sparse trap drums at slow tempo: soft kick, snare or clap on 2 and 4, 8th-note hats with "
              "occasional rolls; drums sit back in the reverb rather than knocking.",
        form=(("intro", 4), ("hook", 8), ("verse", 16), ("hook", 8), ("verse", 16), ("hook", 8), ("outro", 4)),
        instruments=("pitched vocal samples", "ambient pads", "808", "trap drums", "reverb-heavy synths", "rap vocal"),
        sound_design="Washed-out samples (pitched, time-stretched, reverb and delay), shoegaze-like textures, "
                     "lo-fi saturation; soft-attack pads; drums with reverb sends.",
        production="Wide, wet mixes; vocals with reverb and echo, sometimes buried; low end soft; mood over punch.",
        theory="Static, unresolved extended harmony (maj7, m9, add9) and slow harmonic rhythm make a timeless "
               "ambient field; rhythm is half-time and sparse to keep the float.",
        mix=Mix(lufs=(-11, -8), lra=(4, 8), low_end="heavy", tone="warm", width="wide"),
    ),
    Genre(
        name="g-funk",
        family="hip-hop",
        aliases=("gangsta funk", "west coast g funk sound"),
        parent="hip-hop",
        description="West Coast gangsta rap with a slow, rolling funk groove: P-Funk interpolations, whining "
                    "high-pitched Moog leads, deep synth bass and laid-back vocal melodies.",
        era="Los Angeles and Long Beach, 1992-1997",
        touchstones=("Dr. Dre", "Snoop Dogg", "Warren G", "DJ Quik", "Nate Dogg", "Battlecat", "Daz Dillinger"),
        tempo=(88, 100),
        feel="relaxed, slightly swung 16ths; laid-back bounce",
        swing=56,
        modes=("dorian", "minor", "mixolydian"),
        keys=("D minor", "E minor", "G minor", "C minor"),
        progressions=(
            "i7-IV7",
            "i9-IV9",
            "i7-v7",
            "minor: i7-iv7-VImaj7-V7",
            "mixolydian: I9-VII",
        ),
        harmonic_rhythm=1,
        harmony="Funk vamps: dorian minor 7th to IV7 (the major IV is the dorian signature), sometimes a 4-chord "
                "soul turnaround with major 7ths; interpolated (re-played) funk records rather than raw samples.",
        voicing="open",
        comping="stabs",
        bass_style="syncopated",
        bass="Minimoog or live electric bass: round, deep, syncopated 16th lines with slides and octave pops, "
             "playing a funk riff that repeats every 1-2 bars.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="The high portamento Moog sine/saw 'whistle' lead in the 2-3 octave range, playing slow bluesy "
               "pentatonic lines; talk box hooks; smooth sung hooks (Nate Dogg-style) answering the rap.",
        groove={"step": 0.25, "swing": 56, "pattern": {
            "kick":       "x......x..x.....|x......x..x..x..",
            "snare":      "....x.......x...|....x.......x...",
            "clap":       "....x.......x...|....x.......x...",
            "closed hat": "x.xxx.xxx.xxx.xx|x.xxx.xxx.xxx.xx",
            "shaker":     "..x...x...x...x.|..x...x...x...x.",
        }},
        drums="Drum machine (808/LinnDrum style) or replayed breaks: snare with clap layered on 2 and 4, kick on 1 "
              "and the 'a' of 2, 16th hats with an open hat lift, shakers and tambourine; never busy.",
        form=(("intro", 8), ("verse", 16), ("hook", 8), ("verse", 16), ("hook", 8), ("verse", 16), ("hook", 8),
              ("outro", 8)),
        instruments=("Minimoog lead", "synth bass", "talk box", "Rhodes", "drum machine", "live guitar", "rap vocal"),
        sound_design="Sine/triangle Moog lead with glide and vibrato, fat analog synth bass, clean wah or chorus "
                     "guitar licks, Rhodes and string pads; warm, polished, expensive-sounding.",
        production="Clean and wide for its era; bass deep and round, lead panned or centred above the vocal; "
                   "live musicians replaying samples; car-system low end.",
        theory="Dorian modal vamps (i7-IV7) and blues-pentatonic leads from P-Funk; the major IV gives a sunny, "
               "cool tension against the minor tonic; portamento leads bend between pentatonic tones.",
        mix=Mix(lufs=(-11, -8), lra=(4, 7), low_end="heavy", tone="warm", width="wide"),
    ),
    Genre(
        name="crunk",
        family="hip-hop",
        aliases=("crunk music", "crunk rap"),
        parent="hip-hop",
        description="Party-starting Southern club rap: booming 808s, piercing synth riffs and shouted call-and-"
                    "response chants, built for energy rather than lyricism.",
        era="Memphis and Atlanta, late 1990s to mid 2000s",
        touchstones=("Lil Jon", "Ying Yang Twins", "Three 6 Mafia", "Pastor Troy", "YoungBloodZ", "Bone Crusher"),
        tempo=(75, 105),
        feel="straight, stomping 4/4; snare/clap on 2 and 4",
        swing=50,
        modes=("minor", "phrygian"),
        keys=("C minor", "D minor", "E minor", "F minor"),
        progressions=(
            "i",
            "i-bII",
            "i-VI-VII",
            "i-iv-i-V",
        ),
        harmonic_rhythm=0.5,
        harmony="Next to none: a one-chord riff or a two-note synth stab ostinato in minor or phrygian; the bII "
                "half-step adds menace; harmony is in the riff.",
        voicing="power",
        comping="stabs",
        bass_style="808",
        bass="Huge boomy 808s on the kick pattern, long decays, sustained root notes; sometimes a synth bass "
             "doubling the riff.",
        melody_density="medium",
        melody_scale="phrygian",
        melody="High, piercing synth riff (Triton-style lead or whistle) of 2-4 notes repeated; vocals are shouted "
               "chants, crowd responses and call-and-response hooks ('what?', 'yeah!').",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.....x.x.......|x.....x.x..x....",
            "clap":       "....X.......X...|....X.......X...",
            "snare":      "....x.......x...|....x.......x.x.",
            "closed hat": "x.x.x.x.x.x.x.x.|x.x.x.x.x.x.x.x.",
        }},
        drums="TR-808 kick and hard clap/snare on 2 and 4, 8th hats, syncopated kick pairs; crash on every new "
              "section; snare rolls building into chants; stops for shouted lines.",
        form=(("intro", 8), ("hook", 8), ("verse", 16), ("hook", 8), ("verse", 16), ("hook", 8), ("chant break", 8),
              ("hook", 8)),
        instruments=("TR-808", "808 bass", "Korg Triton-style synth lead", "synth stabs", "gang vocals", "lead vocal"),
        sound_design="Bright detuned synth leads and whistles, 808 boom with long decay, hard clap, shouted vocals "
                     "doubled and stacked; cheap workstation presets used deliberately.",
        production="Loudness-war masters, low end maxed for club systems, vocals shouted and stacked in crowd "
                   "layers, hype ad-libs; simple 8-bar blocks.",
        theory="Minimal harmony (one chord or a phrygian half-step) and riff repetition; energy comes from "
               "call-and-response and dynamic drop-outs.",
        mix=Mix(lufs=(-8, -5), lra=(3, 5), low_end="very heavy", tone="bright", width="moderate"),
    ),
    Genre(
        name="memphis rap",
        family="hip-hop",
        aliases=("memphis hip hop", "memphis underground", "tape rap"),
        parent="hip-hop",
        description="Dark, lo-fi Memphis underground tapes: horrorcore atmospheres, eerie minor-key synths and "
                    "samples, 808 cowbells and rapid triplet flows, recorded cheap and raw.",
        era="Memphis, early to late 1990s",
        touchstones=("DJ Spanish Fly", "Three 6 Mafia", "DJ Paul", "Juicy J", "Tommy Wright III", "Gangsta Pat",
                     "Kingpin Skinny Pimp"),
        tempo=(65, 85),
        feel="slow and menacing, straight 16th hats, triplet flows over the beat",
        swing=52,
        modes=("minor", "phrygian", "harmonic minor"),
        keys=("C minor", "E minor", "F minor", "G minor"),
        progressions=(
            "i-bII",
            "i-iv",
            "i7",
            "i-VI-V",
        ),
        harmonic_rhythm=0.5,
        harmony="One or two minor chords, often a horror-film synth or a slowed sample; phrygian bII and "
                "diminished tones for dread.",
        voicing="close",
        comping="sustain",
        bass_style="808",
        bass="Long 808 booms on the kick, root notes held; tape-saturated and muddy.",
        melody_density="sparse",
        melody_scale="harmonic minor",
        melody="Creepy synth bells, organ or piano motifs (1-2 bars); vocals in fast triplet cadences, chanted "
               "hooks repeated four or eight times, whispered and pitched voices.",
        groove={"step": 0.25, "swing": 52, "pattern": {
            "kick":       "x..x......x.....|x..x....x.x.....",
            "snare":      "....x.......x...|....x.......x...",
            "closed hat": "xxxxxxxxxxxxxxxx|xxxxxxxxxxxxxxxx",
            "cowbell":    "..x...x...x...x.|..x...x...x.x.x.",
        }},
        drums="Roland TR-808 throughout: boomy kick, snare on 2 and 4, constant 16th hats, the 808 cowbell "
              "playing offbeats; drums slightly sloppy from tape and live finger-drumming.",
        form=(("intro", 4), ("hook", 8), ("verse", 16), ("hook", 8), ("verse", 16), ("hook", 8), ("outro", 4)),
        instruments=("TR-808", "808 cowbell", "cheap synths", "slowed samples", "four-track tape", "rap vocal"),
        sound_design="Hissy, saturated cassette sound, dark synth patches, pitched-down horror samples, distorted "
                     "vocals; 808 cowbell and claps.",
        production="Four-track tape lo-fi: noisy, mono-ish, overdriven; vocals loud and dry, lots of hiss; "
                   "tape-dubbed generation loss is part of the sound.",
        theory="Static minor and phrygian loops with diminished colour; the triplet flow (three syllables per beat) "
               "against straight 16th hats is Memphis's lasting rhythmic contribution to trap.",
        mix=Mix(lufs=(-12, -8), lra=(4, 8), low_end="heavy", tone="dark", width="narrow"),
    ),
    Genre(
        name="grime",
        family="hip-hop",
        aliases=("eskibeat", "grime music"),
        parent="uk garage",
        description="London's 140 BPM MC music: stark square-wave bass, cold synth riffs, skippy garage-derived "
                    "drums and rapid-fire bars in 8- and 16-bar blocks.",
        era="East London, 2002-2005; revived mid 2010s",
        touchstones=("Wiley", "Dizzee Rascal", "Skepta", "JME", "Kano", "D Double E", "Ruff Sqwad", "Jammer"),
        tempo=(138, 142),
        feel="140 BPM half-time snare on 3 with syncopated kicks; MCs ride double-time",
        swing=52,
        modes=("minor", "phrygian"),
        keys=("C minor", "F minor", "G minor", "A minor"),
        progressions=(
            "i",
            "i-bII",
            "i-VI-VII",
            "i-bV",
            "i-iv-v",
        ),
        harmonic_rhythm=0.5,
        harmony="Minimal and dissonant: one-chord riffs, tritone (bV) and phrygian bII moves, square-wave stabs; "
                "Eastern-sounding string or flute presets on 'eski' beats.",
        voicing="close",
        comping="stabs",
        bass_style="syncopated",
        bass="Square or sine sub bass ('eski' bass), pulsing syncopated notes, sometimes Reese-like on darker "
             "tracks; leaves gaps for the MC.",
        melody_density="medium",
        melody_scale="phrygian",
        melody="Short cold synth riffs (square waves, string or pizzicato presets) in 1-2 bar loops; MC flows "
               "are rapid 16th-note bars with tempo switches, hooks short and chanted.",
        groove={"step": 0.25, "swing": 52, "pattern": {
            "kick":       "x.....x.......x.|x.....x..x......",
            "snare":      "........x.......|........x.......",
            "clap":       "........x.......|........x.....x.",
            "closed hat": "..x...x...x...x.|..x...x...x...xx",
        }},
        drums="Sparse, hard drums at 140: snare/clap on 3, syncopated kicks, offbeat hats and gunshot or glass "
              "FX; 'eight-bar' style instrumentals with drop-outs; wheel-ups on raves.",
        form=(("intro", 8), ("hook", 16), ("verse", 32), ("hook", 16), ("verse", 32), ("hook", 16)),
        instruments=("Fruity Loops", "Korg Triton", "square-wave bass", "synth stabs", "string presets", "MC vocal"),
        sound_design="Raw square and saw waves, workstation presets (Triton, stock FL synths), metallic hits, "
                     "glass and gunshot FX; cold and bare.",
        production="Dry and stark; space for the MC; bass powerful but simple; tracks arranged in 8-bar phrases for "
                   "pirate radio and clashes.",
        theory="Dissonant minimalism: tritones, phrygian half-steps and one-chord ostinatos; rhythm sits between "
               "garage's 2-step and dancehall riddim culture.",
        mix=Mix(lufs=(-9, -6), lra=(3, 6), low_end="heavy", tone="neutral", width="moderate"),
    ),
    Genre(
        name="jazz rap",
        family="hip-hop",
        aliases=("jazz hip hop", "jazzy hip hop"),
        parent="hip-hop",
        description="Hip-hop built from jazz: upright bass and Rhodes samples, muted trumpet and vibraphone loops, "
                    "swung drums and conversational, cerebral flows.",
        era="New York, late 1980s to mid 1990s",
        touchstones=("A Tribe Called Quest", "De La Soul", "Digable Planets", "Guru", "Pete Rock & CL Smooth",
                     "The Roots", "Madlib"),
        tempo=(84, 98),
        feel="swung 16ths, relaxed pocket",
        swing=60,
        modes=("dorian", "minor", "major"),
        keys=("D minor", "F minor", "Bb major", "Eb major"),
        progressions=(
            "i7-IV7",
            "i9-ii7",
            "major: ii7-V7-Imaj7",
            "major: Imaj7-vi7-ii7-V7",
            "minor: iiø7-V7-i7",
        ),
        harmonic_rhythm=0.5,
        harmony="Jazz harmony from samples: minor 7, 9 and 11 chords, ii-V cells, dorian vamps; chords looped 1-2 "
                "bars, sometimes the whole sample turnaround.",
        voicing="rootless",
        comping="stabs",
        bass_style="walking",
        bass="Sampled or played upright bass: walking or semi-walking lines, root on 1, chromatic approach notes; "
             "warm and woody, not sub-heavy.",
        melody_density="medium",
        melody_scale="dorian",
        melody="Horn and vibraphone phrases, Rhodes riffs, flute; vocals relaxed and conversational, jazz-like "
               "phrasing that floats over bar lines.",
        groove={"step": 0.25, "swing": 60, "pattern": {
            "kick":       "x.......x.x.....|x.....x...x.....",
            "snare":      "....x.......x...|....x.......x..o",
            "closed hat": "x.x.x.x.x.x.x.x.|x.x.x.x.x.xox.x.",
            "side stick": "..o.......o.....|..o.......o.....",
        }},
        drums="Breakbeat-based, swung: kick on 1 and the 'and' of 3, snare on 2 and 4 behind the beat, 8th hats "
              "with ghost notes; jazz drum samples (ride, brushes) mixed in.",
        form=(("intro", 4), ("verse", 16), ("hook", 8), ("verse", 16), ("hook", 8), ("verse", 16), ("hook", 8),
              ("outro", 8)),
        instruments=("upright bass", "Rhodes", "vibraphone", "muted trumpet", "sampled drums", "rap vocal"),
        sound_design="Warm, dusty vinyl samples, round upright bass, mellow Rhodes and vibes, filtered horns.",
        production="Warm and unhurried mixes; vocal intimate; bass round rather than booming; less compression than "
                   "boom bap.",
        theory="Imports jazz's extended chords and ii-V cells but loops them, turning functional progressions into "
               "modal vamps; swing and behind-the-beat placement drive the feel.",
        mix=Mix(lufs=(-12, -9), lra=(5, 8), low_end="moderate", tone="warm", width="moderate"),
    ),
    Genre(
        name="emo rap",
        family="hip-hop",
        aliases=("sad rap", "emo trap", "soundcloud emo"),
        parent="cloud rap",
        description="Confessional trap with emo and pop-punk DNA: sad guitar loops, half-time 808s and sung, "
                    "Auto-Tuned melodies about heartbreak and depression.",
        era="SoundCloud, 2015-2019",
        touchstones=("Lil Peep", "XXXTentacion", "Juice WRLD", "Nick Mira", "Wicca Phase Springs Eternal",
                     "Smokeasac"),
        tempo=(130, 170),
        feel="half-time trap at the DAW tempo, snare/clap on beat 3",
        swing=50,
        modes=("minor", "major"),
        keys=("C# minor", "E minor", "F minor", "B minor"),
        progressions=(
            "i-VI-III-VII",
            "VI-VII-i",
            "i-iv-VI-V",
            "major: I-V-vi-IV",
            "major: vi-IV-I-V",
        ),
        harmonic_rhythm=1,
        harmony="Guitar-chord loops (often arpeggiated) in minor or relative major; axis-style progressions shared "
                "with emo and pop-punk; added 9ths from open strings.",
        voicing="open",
        comping="arpeggio_up",
        bass_style="808",
        bass="Soft-to-mid 808s on the root, long sustains following the chord changes, few slides.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="Fingerpicked electric or acoustic guitar loops (Internet Money style); vocals sung-rapped in "
               "Auto-Tune, melodic pentatonic hooks with falling contours, freestyled phrasing.",
        groove={"step": 0.125, "swing": 50, "pattern": {
            "kick":       "x.......|........|........|..x.....|x.......|....x...|........|........",
            "clap":       "........|........|X.......|........|........|........|X.......|........",
            "closed hat": "x...x...|x...x...|x...x...|x.x.x.x.|x...x...|x...x...|x...x...|x.xxx.xx",
            "open hat":   "........|........|........|........|........|........|........|......x.",
        }},
        drums="Simple trap pattern: clap on 3, 8th hats with occasional rolls, sparse kick; drums often drop out "
              "under the first hook bars to let the guitar breathe.",
        form=(("intro", 8), ("hook", 16), ("verse", 32), ("hook", 16), ("verse", 32), ("hook", 16), ("outro", 8)),
        instruments=("electric guitar", "acoustic guitar", "808", "trap drums", "pads", "Auto-Tuned vocal"),
        sound_design="Clean guitar with chorus, reverb and lo-fi tape, sometimes distorted pop-punk guitar; soft "
                     "808; pads and vinyl crackle.",
        production="Vocal-forward, wet with reverb and delay, stacked harmonies; guitar loop sidechained lightly to "
                   "the 808; loud but less clipped than trap.",
        theory="Diatonic emo progressions (relative-major/minor ambiguity, i-VI-III-VII) over half-time trap; "
               "melody leans on pentatonic and stepwise falling lines for the 'sad' contour.",
        mix=Mix(lufs=(-9, -6), lra=(3, 6), low_end="heavy", tone="warm", width="wide"),
    ),
    Genre(
        name="rage",
        family="hip-hop",
        aliases=("rage beat", "rage rap"),
        parent="trap",
        description="Maximalist trap for mosh pits: blown-out 808s, buzzing detuned supersaw leads borrowed from "
                    "trance and video games, and chaotic, high-energy vocals.",
        era="Atlanta and online, 2020 onward",
        touchstones=("Playboi Carti", "Trippie Redd", "Ken Carson", "Destroy Lonely", "F1lthy", "Yeat"),
        tempo=(145, 170),
        feel="half-time at the DAW tempo, snare/clap on 3, relentless 16th hats",
        swing=50,
        modes=("minor",),
        keys=("C# minor", "D minor", "F minor", "G# minor"),
        progressions=(
            "i-VI-III-VII",
            "i-VI",
            "i-v-VI-iv",
            "i-iv",
            "VI-VII-i",
        ),
        harmonic_rhythm=1,
        harmony="Simple minor triad loops played as trance-style supersaw stabs and arps; one chord per bar; "
                "harmony is a bright wall of detuned saws.",
        voicing="open",
        comping="pulse_16",
        bass_style="808",
        bass="Massively distorted 808s, often behaving like a synth bass with slides; the 808 is the loudest "
             "element and frequently clips.",
        melody_density="busy",
        melody_scale="minor",
        melody="Buzzing, detuned supersaw or square lead arpeggios in 16ths, video-game and trance flavour; "
               "vocals shouted, baby-voice or melodic, repetitive one-line hooks with ad-libs.",
        groove={"step": 0.125, "swing": 50, "pattern": {
            "kick":       "x.......|......x.|........|x...x...|x.......|..x.....|........|x.......",
            "clap":       "........|........|X.......|........|........|........|X.......|........",
            "closed hat": "x.x.x.x.|x.x.x.x.|x.x.x.x.|x.x.xxxx|x.x.x.x.|x.x.x.x.|x.x.x.x.|xxxxxxxx",
            "open hat":   "........|..x.....|........|........|........|..x.....|........|........",
        }},
        drums="Hard-clipped kick and clap on 3, straight 16th hats with rolls, heavy distortion on the drum bus; "
              "drops where everything cuts but the synth.",
        form=(("intro", 8), ("hook", 16), ("verse", 32), ("hook", 16), ("verse", 16), ("hook", 16), ("outro", 4)),
        instruments=("supersaw synth", "distorted 808", "trap drums", "square lead", "vocal"),
        sound_design="Detuned supersaws with unison, chorus and saturation, 'buzzy' squares, sidechained pads; "
                     "808 through heavy distortion and clipping.",
        production="Loudest masters in hip-hop: clipping everything, sidechain synths to the 808, vocals aggressive "
                   "and distorted; wide synths, mono 808.",
        theory="Trance-like minor loops and arps fused with half-time trap; intensity from saturation and "
               "density rather than harmonic movement.",
        mix=Mix(lufs=(-7, -4), lra=(2, 5), low_end="very heavy", tone="bright", width="wide"),
    ),
    Genre(
        name="plugg",
        family="hip-hop",
        aliases=("plug music", "pluggnb"),
        parent="trap",
        description="Bouncy, airy Atlanta trap: soft 808s, sparse drums and sweet, video-game-like synth melodies "
                    "in major keys; pluggnb adds R&B chords and sung vocals.",
        era="Atlanta and online, 2014 onward; pluggnb from about 2017",
        touchstones=("StoopidXool", "MexikoDro", "Beatpluggz", "Pi'erre Bourne", "Summrs", "Autumn!"),
        tempo=(140, 165),
        feel="half-time bounce, snare on 3, simple 8th hats",
        swing=50,
        modes=("major", "minor"),
        keys=("C major", "F major", "Bb major", "A minor"),
        progressions=(
            "Imaj7-IVmaj7",
            "IVmaj7-V7-iii7-vi7",
            "Imaj7-iii7-IVmaj7",
            "vi7-IVmaj7-Imaj7-V",
            "minor: i-VI-III-VII",
        ),
        harmonic_rhythm=1,
        harmony="Major 7ths and the 4-5-3-6 royal-road progression, airy and nostalgic; pluggnb adds 9ths and "
                "R&B voicings; lots of space.",
        voicing="spread",
        comping="arpeggio_updown",
        bass_style="808",
        bass="Soft, round 808s with short slides, bouncy rhythm, rarely distorted; sometimes a sine sub.",
        melody_density="medium",
        melody_scale="major pentatonic",
        melody="Bright synth bells, flutes, plucks and soft square leads in pentatonic hooks, chiptune-like; "
               "vocals melodic and mumbled, catchy short hooks.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.........x.....|x.....x...x.....",
            "snare":      "........x.......|........x.......",
            "clap":       "........x.......|........x.......",
            "closed hat": "x.x.x.x.x.x.x.x.|x.x.x.x.x.x.xxxx",
        }},
        drums="Minimal: snare/clap on 3, 8th hats with a single roll per 2 bars, light kick; drum sounds clean "
              "and soft, not knocking.",
        form=(("intro", 8), ("hook", 16), ("verse", 32), ("hook", 16), ("verse", 32), ("hook", 16)),
        instruments=("synth bells", "plucks", "flute", "soft 808", "trap drums", "vocal"),
        sound_design="Glassy synths, SNES-like plucks and pads, reverb-heavy leads, soft 808s; dreamy and light.",
        production="Airy, wide mixes with reverb; low end present but gentle; vocals melodic and blended.",
        theory="Major-key, nostalgic harmony (maj7 and IV-V-iii-vi) inside trap's half-time frame, an inversion "
               "of trap's usual minor menace.",
        mix=Mix(lufs=(-9, -6), lra=(3, 6), low_end="heavy", tone="bright", width="wide"),
    ),

    # ------------------------------------------------------------------ r&b and soul
    Genre(
        name="r&b",
        family="r&b and soul",
        aliases=("rnb", "contemporary r&b", "modern r&b"),
        parent="soul",
        description="Contemporary rhythm and blues: lush extended chords, hip-hop drums and intimate, melismatic "
                    "vocals with stacked harmonies, from the 2000s to today.",
        era="US, late 1990s to the present",
        touchstones=("Usher", "Beyonce", "Alicia Keys", "Chris Brown", "The-Dream", "SZA", "H.E.R."),
        tempo=(65, 100),
        feel="laid-back hip-hop pocket, lightly swung 16ths",
        swing=56,
        modes=("minor", "dorian", "major"),
        keys=("Eb minor", "F minor", "Ab major", "Db major"),
        progressions=(
            "i9-iv9",
            "VImaj9-v9",
            "i7-VImaj7-iv7-V7",
            "major: IVmaj7-iii7-vi9-V7sus4",
            "major: ii9-V13-Imaj9-vi9",
        ),
        harmonic_rhythm=1,
        harmony="Extended chords throughout: minor 9ths, major 9ths, 11ths and sus chords; 2-4 chord loops with "
                "a pre-chorus lift to the IV; gospel passing chords in ballads.",
        voicing="rootless",
        comping="sustain",
        bass_style="syncopated",
        bass="Sub or 808 under the chord roots with syncopated pickups, smooth slides; sometimes a warm electric "
             "or synth bass doubling the kick.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="Vocal-led: verses conversational and rhythmic, hooks melodic with pentatonic runs and melisma on "
               "held words; harmony stacks and ad-lib responses; range about a 10th, peaking in the chorus.",
        groove={"step": 0.25, "swing": 56, "pattern": {
            "kick":       "x.....x...x.....|x......x..x.....",
            "snare":      "....x.......x...|....x.......x...",
            "clap":       "....x.......x...|....x.......x...",
            "closed hat": "x.xxx.x.x.xxx.x.|x.xxx.x.x.xxx.xx",
            "rim":        "..o.......o.....|..o.....o.......",
        }},
        drums="Programmed hip-hop drums: kick on 1 with syncopated pickups, snare or snap on 2 and 4, busy 16th "
              "hats with gaps, rim and perc fills; fewer rolls than trap.",
        form=(("intro", 4), ("verse", 16), ("pre-chorus", 4), ("chorus", 8), ("verse", 16), ("pre-chorus", 4),
              ("chorus", 8), ("bridge", 8), ("chorus", 8), ("outro", 4)),
        instruments=("electric piano", "pads", "sub or 808 bass", "programmed drums", "lead vocal", "background vocals"),
        sound_design="Silky pads, Rhodes and Wurli, plucked synths, finger snaps; vocal production is the centrepiece: "
                     "lead, doubles, harmonies, ad-libs.",
        production="Vocal on top with tuning, de-essing and reverb/delay throws, big stacked BVs; low end heavy but "
                   "soft; warm top end; drums tucked under the vocal.",
        theory="Extended-chord harmony (9ths, 11ths, sus) and gospel melisma over hip-hop rhythm; the vocal "
               "carries blues inflections (b3, b7) against diatonic changes.",
        mix=Mix(lufs=(-11, -8), lra=(4, 8), low_end="heavy", tone="warm", width="moderate"),
    ),
    Genre(
        name="90s r&b",
        family="r&b and soul",
        aliases=("hip hop soul", "90s rnb", "nineties r&b"),
        parent="new jack swing",
        description="The 90s golden age of R&B: hip-hop soul grooves, lush keyboards and tight vocal-group "
                    "harmonies, from smooth ballads to Timbaland's stuttering syncopation.",
        era="US, 1991-2001",
        touchstones=("Jodeci", "TLC", "Boyz II Men", "Aaliyah", "Mary J. Blige", "SWV", "Babyface", "Timbaland"),
        tempo=(65, 100),
        feel="swung hip-hop pocket, lazy 16ths",
        swing=58,
        modes=("major", "minor"),
        keys=("Eb major", "Ab major", "F minor", "C minor"),
        progressions=(
            "IVmaj7-V7-iii7-vi7",
            "Imaj9-vi9-ii9-V13",
            "IVmaj7-iii7-ii7-Imaj7",
            "ii7-iii7-IVmaj7-V7sus4",
            "minor: i9-iv9-VImaj7-V7",
        ),
        harmonic_rhythm=1,
        harmony="Jazz- and gospel-derived 7ths and 9ths, descending IV-iii-ii-I lines, sus4 dominants; key changes "
                "up a step for the last chorus in ballads.",
        voicing="rootless",
        comping="sustain",
        bass_style="syncopated",
        bass="Synth bass or deep sub doing smooth syncopated lines, slides and octave pickups; MPC-style sampled "
             "bass on hip-hop soul tracks.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="Lead vocal with gospel runs and melisma, group harmonies in close 3- and 4-part voicings, "
               "call-and-response with the lead; hooks repeat over chorus vamps and ad-libbed outros.",
        groove={"step": 0.25, "swing": 58, "pattern": {
            "kick":       "x......x..x.....|x.x....x..x.....",
            "snare":      "....x.......x...|....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.|x.x.x.x.x.x.x.xx",
            "shaker":     "xoxoxoxoxoxoxoxo|xoxoxoxoxoxoxoxo",
        }},
        drums="MPC and drum machine with swing: hip-hop kick patterns, crisp snare on 2 and 4, swung hats, shaker "
              "and tambourine; late-90s tracks use stuttering, syncopated Timbaland kicks and odd percussion.",
        form=(("intro", 4), ("verse", 16), ("pre-chorus", 4), ("chorus", 8), ("verse", 16), ("pre-chorus", 4),
              ("chorus", 8), ("bridge", 8), ("chorus", 16), ("outro", 8)),
        instruments=("Rhodes and keys", "synth pads", "synth bass", "MPC drums", "lead vocal", "group harmonies"),
        sound_design="Warm electric pianos, glossy pads, Juno-style strings, crunchy MPC drums, sampled soul loops on "
                     "hip-hop soul; vocals smooth with plate reverb.",
        production="Vocals and harmonies dominate; drums punchy but warm; low end deep; analog warmth with digital "
                   "polish; ad-lib outros.",
        theory="Diatonic 7th-chord harmony with gospel-derived passing chords and the IV-V-iii-vi pattern; group "
               "harmony arrangement (close voicings, suspensions resolving) is central.",
        mix=Mix(lufs=(-12, -9), lra=(5, 8), low_end="heavy", tone="warm", width="moderate"),
    ),
    Genre(
        name="neo soul",
        family="r&b and soul",
        aliases=("nu soul", "neosoul"),
        parent="soul",
        description="Organic, jazz-informed soul with hip-hop drums: rich extended chords on Rhodes, 'drunk' "
                    "behind-the-beat grooves and intimate, improvisatory vocals.",
        era="US, mid 1990s to mid 2000s (Soulquarians); revived in the 2010s",
        touchstones=("D'Angelo", "Erykah Badu", "Jill Scott", "Maxwell", "Bilal", "J Dilla", "Questlove"),
        tempo=(70, 95),
        feel="heavy swing with Dilla-style uneven, late snares and early kicks",
        swing=62,
        modes=("dorian", "major", "minor"),
        keys=("Eb major", "Ab major", "F minor", "C minor"),
        progressions=(
            "i9-IV9",
            "major: ii9-V13-Imaj9",
            "major: IVmaj9-iii7-vi9",
            "major: Imaj7-I7-IVmaj7-iv7",
            "minor: iv9-VII13-IIImaj7-VImaj7",
        ),
        harmonic_rhythm=1,
        harmony="Jazz extensions (9ths, 11ths, 13ths), chromatic parallel chords, minor iv borrowed in major, "
                "cycle-of-4ths movement; loops that slip a chord in at odd places.",
        voicing="rootless",
        comping="push",
        bass_style="syncopated",
        bass="Live electric bass, round and behind the beat, melodic fills and slides, often leaving beat 1 for "
             "the kick and landing late on chord roots.",
        melody_density="medium",
        melody_scale="dorian",
        melody="Improvisatory vocals: behind-the-beat phrasing, falsetto stacks, blue notes and jazz phrasing; "
               "Rhodes and guitar fills answer the vocal.",
        groove={"step": 0.25, "swing": 62, "pattern": {
            "kick":       "x.......x.x.....|x..x......x...x.",
            "snare":      "....x.......x...|....x.......x.o.",
            "closed hat": "x.x.x.xox.x.x.xo|x.x.x.xox.x.xox.",
            "side stick": "..o.......o.....|......o.........",
        }},
        drums="Live or MPC drums played unquantised: kick early, snare late, hats loose; ghost notes on snare and "
              "side stick; 'drunk' feel from mixing straight and swung subdivisions.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("bridge", 8),
              ("vamp", 16), ("outro", 8)),
        instruments=("Rhodes", "Wurlitzer", "electric bass", "live drums", "guitar", "organ", "lead and stacked vocals"),
        sound_design="Analog warmth: Rhodes with tremolo and phaser, tape saturation, dark drums, Hammond, clean "
                     "jazz guitar; little synthesis.",
        production="Analog-sounding, dynamic mixes; vocals layered intimately; bass upfront; drums dark and dry; "
                   "long vamped outros.",
        theory="Jazz harmony (extended and altered chords, chromatic planing) over hip-hop's loop form; the "
               "rhythmic signature is micro-timing: deliberately late snares and quintuplet-ish swing.",
        mix=Mix(lufs=(-13, -9), lra=(5, 9), low_end="moderate", tone="warm", width="moderate"),
    ),
    Genre(
        name="alternative r&b",
        family="r&b and soul",
        aliases=("alt r&b", "pbr&b", "indie r&b"),
        parent="r&b",
        description="Moody, experimental R&B: sparse, atmospheric production, minimal drums, dark pads and "
                    "electronic textures under introspective, often falsetto vocals.",
        era="Online and Toronto/LA, 2010-2016 onward",
        touchstones=("Frank Ocean", "The Weeknd", "FKA twigs", "Solange", "How to Dress Well", "Kelela",
                     "Blood Orange"),
        tempo=(60, 110),
        feel="sparse, often half-time or freely flowing; straight to lightly swung",
        swing=52,
        modes=("minor", "major"),
        keys=("C minor", "Bb minor", "Eb major", "A minor"),
        progressions=(
            "i7-VImaj7",
            "iv7-i",
            "i-VII-VI-VII",
            "major: IVmaj7-Imaj7",
            "major: I-iii-IV-iv",
        ),
        harmonic_rhythm=0.5,
        harmony="Slow-moving, ambiguous harmony: two-chord loops, borrowed minor iv, unresolved maj7s; pads and "
                "drones replace keyboards; sometimes no chords at all.",
        voicing="spread",
        comping="sustain",
        bass_style="808",
        bass="Deep, soft 808 or sub tones under long chord roots, sparse; occasionally a synth bass ostinato.",
        melody_density="sparse",
        melody_scale="minor",
        melody="Intimate vocals with falsetto and breathy delivery, stacked harmonies, vocal chops; melodies wander "
               "over few chords; space between phrases.",
        groove={"step": 0.25, "swing": 52, "pattern": {
            "kick":       "x.........x.....|x.....x.........",
            "snare":      "....x.......x...|....x.......x...",
            "closed hat": "x...x...x...x...|x...x...x.x.x.x.",
            "rim":        "..........o.....|......o.....o...",
        }},
        drums="Minimal and atmospheric: a soft kick, snaps or rim on 2 and 4, sparse hats; drums can disappear for "
              "whole sections; electronic textures stand in for percussion.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("bridge", 8), ("outro", 16)),
        instruments=("synth pads", "808", "electronic drums", "processed guitar", "vocal chops", "lead vocal"),
        sound_design="Dark, reverb-soaked pads, pitched vocal chops, grainy textures, filtered guitars; dub-style "
                     "delays and ambient washes.",
        production="Space and mood first: wide reverbs, dynamic sections, vocals intimate and close, low end deep "
                   "but sparse; songs may change shape mid-way.",
        theory="Modal and borrowed harmony (minor iv in major, unresolved maj7) with slow harmonic rhythm; "
               "texture and space carry the form more than chord changes.",
        mix=Mix(lufs=(-12, -8), lra=(5, 9), low_end="heavy", tone="dark", width="wide"),
    ),
    Genre(
        name="new jack swing",
        family="r&b and soul",
        aliases=("new jack", "swingbeat"),
        parent="r&b",
        description="Late-80s fusion of R&B vocals and hip-hop beats: hard-swinging drum machines, snapping "
                    "snares, synth stabs and sing-along hooks with tight choreography energy.",
        era="New York, 1987-1993",
        touchstones=("Teddy Riley", "Guy", "Bobby Brown", "Keith Sweat", "Bell Biv DeVoe", "Jimmy Jam and Terry Lewis",
                     "Johnny Kemp"),
        tempo=(100, 118),
        feel="hard-swung 16ths, snare and clap stacked on 2 and 4",
        swing=64,
        modes=("minor", "dorian", "major"),
        keys=("C minor", "D minor", "G minor", "F major"),
        progressions=(
            "i7-iv7",
            "dorian: i7-IV9",
            "VImaj7-VII7-i7",
            "i9-iv9-v7-i9",
            "major: IVmaj7-V7-iii7-vi7",
        ),
        harmonic_rhythm=1,
        harmony="Minor 7th vamps and gospel-flavoured turnarounds, voiced as bright synth-brass or piano stabs; "
                "key change up for the last chorus.",
        voicing="close",
        comping="stabs",
        bass_style="syncopated",
        bass="Synth bass (Minimoog, DX7) in swung 16th syncopations and octave jumps, locking with the kick.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="Punchy pop-R&B hooks, group vocals in unison and harmony, rap verses or breaks; melodies in short "
               "riffs answered by synth stabs.",
        groove={"step": 0.25, "swing": 64, "pattern": {
            "kick":       "x..x..x...x..x..|x..x..x...x.x...",
            "snare":      "....X.......X...|....X.......X..x",
            "clap":       "....x.......x...|....x.......x...",
            "closed hat": "xxxxxxxxxxxxxxxx|xxxxxxxxxxxxxxxx",
        }},
        drums="Drum machines (SP-1200, Roland TR-808/R-8, LinnDrum) heavily swung: snare and clap on 2 and 4 with "
              "gated reverb, busy syncopated kick, swung 16th hats; break samples layered underneath.",
        form=(("intro", 8), ("verse", 16), ("pre-chorus", 4), ("chorus", 8), ("verse", 16), ("chorus", 8),
              ("rap break", 8), ("chorus", 16)),
        instruments=("drum machine", "synth bass", "synth brass", "DX7 keys", "sampler", "lead and group vocals"),
        sound_design="Bright digital synths (DX7, Juno), orchestra hits, gated snares, metallic hats; crisp and "
                     "glossy late-80s sound.",
        production="Bright and punchy; drums upfront; vocals compressed and doubled; dance-routine-ready structure.",
        theory="Gospel-derived R&B harmony laid over a hip-hop drum machine with heavy 16th swing; the swing "
               "ratio (near triplet) is the genre's signature.",
        mix=Mix(lufs=(-12, -9), lra=(5, 8), low_end="moderate", tone="bright", width="moderate"),
    ),
    Genre(
        name="quiet storm",
        family="r&b and soul",
        aliases=("slow jam", "late night soul"),
        parent="soul",
        description="Smooth, romantic late-night R&B: mellow tempos, soft drums, lush jazz-inflected chords and "
                    "polished, sensual vocals.",
        era="US radio format, mid 1970s to early 1990s",
        touchstones=("Smokey Robinson", "Luther Vandross", "Anita Baker", "Sade", "Freddie Jackson", "Peabo Bryson"),
        tempo=(60, 85),
        feel="relaxed, lightly swung ballad pocket",
        swing=54,
        modes=("major", "minor"),
        keys=("Db major", "Eb major", "Ab major", "F minor"),
        progressions=(
            "Imaj7-IVmaj7",
            "ii9-V13-Imaj9",
            "Imaj7-vi9-ii9-V13",
            "IVmaj7-iv7-iii7-VI7",
            "minor: i9-iv9",
        ),
        harmonic_rhythm=1,
        harmony="Jazz-pop harmony: major 7ths and 9ths, ii-V turnarounds, borrowed minor iv, secondary dominants; "
                "slow-moving changes for intimacy.",
        voicing="drop2",
        comping="sustain",
        bass_style="root_fifth",
        bass="Fretless or smooth electric bass, round tone, roots and 5ths with gentle slides and fills at phrase "
             "ends.",
        melody_density="sparse",
        melody_scale="major pentatonic",
        melody="Smooth, legato vocals with restrained melisma, saxophone solos and fills, long phrases with "
               "breathing space; big final-chorus ad-libs.",
        groove={"step": 0.25, "swing": 54, "pattern": {
            "kick":       "x.......x.......|x......x..x.....",
            "snare":      "....x.......x...|....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.|x.x.x.x.x.x.x.x.",
            "shaker":     "..x...x...x...x.|..x...x...x...x.",
        }},
        drums="Soft live drums or LinnDrum: light kick, soft snare or rim on 2 and 4, closed hats, shaker; "
              "brushes on jazzier tracks; fills sparse and gentle.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("sax solo", 8),
              ("chorus", 8), ("outro", 16)),
        instruments=("Rhodes or DX7 electric piano", "fretless bass", "saxophone", "strings or pads", "soft drums",
                     "lead vocal"),
        sound_design="Lush electric pianos with chorus, string pads, smooth sax, soft drums with plate reverb; "
                     "silky and polished.",
        production="Dynamic, warm, wide mixes; vocals intimate and present; reverb generous; low end smooth.",
        theory="Jazz-derived functional harmony (ii-V-I, secondary dominants) at ballad tempos; restraint and "
               "texture over rhythmic drive.",
        mix=Mix(lufs=(-15, -11), lra=(6, 10), low_end="moderate", tone="warm", width="wide"),
    ),
    Genre(
        name="trap soul",
        family="r&b and soul",
        aliases=("trapsoul", "trap&b", "trap r&b"),
        parent="r&b",
        description="R&B sung over trap production: slow, moody minor chords, sub-heavy 808s and rolling hats, "
                    "with melodic, half-rapped vocals.",
        era="Toronto and US, 2013 onward",
        touchstones=("Bryson Tiller", "PARTYNEXTDOOR", "6LACK", "Tory Lanez", "Summer Walker", "Noah \"40\" Shebib"),
        tempo=(60, 85),
        feel="snare on 2 and 4 at this slow BPM, trap hats in 16ths with 32nd rolls",
        swing=52,
        modes=("minor",),
        keys=("Eb minor", "F minor", "Bb minor", "C# minor"),
        progressions=(
            "i9-VImaj7",
            "i-VI-III-VII",
            "iv9-v7-i9",
            "VImaj7-v7",
            "i7-iv7-VImaj7-V7",
        ),
        harmonic_rhythm=0.5,
        harmony="Dark minor 7ths and 9ths, often two chords; low-passed pads and Rhodes; harmony slow and moody.",
        voicing="spread",
        comping="sustain",
        bass_style="808",
        bass="Deep, clean 808s with long decays and slides between chord roots; the 808 often carries the hook "
             "rhythm.",
        melody_density="medium",
        melody_scale="minor pentatonic",
        melody="Sung-rapped melodic flows with pentatonic hooks, harmonised doubles and ad-libs; melodies fall "
               "into the pocket of the hats; sampled R&B vocal snippets.",
        groove={"step": 0.125, "swing": 52, "pattern": {
            "kick":       "x.......|........|....x...|..x.....|x.......|..x.....|........|....x...",
            "clap":       "........|x.......|........|x.......|........|x.......|........|x.......",
            "closed hat": "x.x.x.x.|x.x.x.x.|x.x.xxxx|x.x.x.x.|x.x.x.x.|x.x.x.x.|x.x.x.x.|xxxxx.x.",
            "rim":        "........|........|......o.|........|........|........|......o.|........",
        }},
        drums="Trap kit at R&B tempo: clap or snap on 2 and 4, 16th hats with 32nd and triplet rolls, sparse "
              "kick; snare rolls rare; softer than rap trap.",
        form=(("intro", 4), ("hook", 8), ("verse", 16), ("hook", 8), ("verse", 16), ("hook", 8), ("outro", 8)),
        instruments=("808", "trap drums", "Rhodes", "dark pads", "sampled R&B vocals", "lead vocal"),
        sound_design="Low-passed, underwater pads and keys (the OVO '40' sound), clean deep 808, crisp snaps; "
                     "vocal chops pitched and filtered.",
        production="Dark, low-passed mixes with heavy sub; vocals intimate and stacked; muffled instrumentals "
                   "under clear vocals.",
        theory="Minor-key R&B harmony with slow harmonic rhythm fused with trap rhythm; heavy low-pass filtering "
               "is a structural tool (open the filter for the hook).",
        mix=Mix(lufs=(-10, -7), lra=(4, 7), low_end="heavy", tone="dark", width="wide"),
    ),
    Genre(
        name="soul",
        family="r&b and soul",
        aliases=("soul music", "southern soul", "deep soul", "memphis soul"),
        parent="gospel",
        description="Gospel fervour applied to secular love songs: a tight rhythm section, horns, organ and "
                    "impassioned, testifying lead vocals.",
        era="US South and North, late 1950s to mid 1970s",
        touchstones=("Otis Redding", "Aretha Franklin", "Sam Cooke", "Al Green", "Booker T. & the M.G.'s",
                     "Ray Charles", "Wilson Pickett"),
        tempo=(65, 120),
        feel="backbeat-driven, lightly swung, behind-the-beat snare",
        swing=56,
        modes=("major", "mixolydian", "minor"),
        keys=("C major", "D major", "E major", "G major"),
        progressions=(
            "I-IV",
            "I-vi-IV-V",
            "I7-IV7-V7",
            "I-iii-IV-V",
            "mixolydian: I-VII-IV",
        ),
        harmonic_rhythm=1,
        harmony="Gospel and blues harmony: I-IV vamps, I-vi-IV-V doo-wop changes, dominant 7ths, plagal (IV-I) "
                "cadences; horns voiced in 3rds and 6ths; ballads often in 12/8 feel.",
        voicing="close",
        comping="gospel",
        bass_style="syncopated",
        bass="Electric bass (Fender Precision) playing roots, 5ths and octaves with syncopated pickups and "
             "chromatic approaches; locks with the kick, Duck Dunn-style economy.",
        melody_density="medium",
        melody_scale="blues",
        melody="Testifying lead vocal with blue notes, melisma and gospel shouts; call-and-response with backing "
               "vocals or horns; dynamic builds to a climactic vamp.",
        groove={"step": 0.25, "swing": 56, "pattern": {
            "kick":       "x.......x.x.....|x.......x.....x.",
            "snare":      "....x.......x...|....x.......x...",
            "closed hat": "x.x.x.x.x.x.x.x.|x.x.x.x.x.x.x.x.",
            "tambourine": "....x.......x...|....x.......x...",
        }},
        drums="Live drums: heavy snare on 2 and 4 laid back (Al Jackson Jr.), kick on 1 and 3 with pickups, 8th "
              "hats, tambourine on the backbeat; fills short and functional.",
        form=(("intro", 4), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("bridge", 8),
              ("chorus", 8), ("vamp", 8)),
        instruments=("electric bass", "drums", "Hammond organ", "electric guitar", "horn section", "piano", "lead vocal"),
        sound_design="Live room sound: Hammond with Leslie, clean Telecaster rhythm, punchy horns, warm bass; "
                     "tape saturation and room reverb.",
        production="Recorded live in one room on tape; vocals upfront, often mono or narrow stereo; natural dynamics.",
        theory="Gospel's plagal motion and call-and-response married to blues inflections and pop song form; "
               "the I-IV vamp and the climactic vamp-out are signatures.",
        mix=Mix(lufs=(-15, -11), lra=(6, 10), low_end="moderate", tone="warm", width="narrow"),
    ),
    Genre(
        name="motown",
        family="r&b and soul",
        aliases=("motown sound", "detroit soul", "hitsville"),
        parent="soul",
        description="Detroit's hit-factory soul: pop-structured songs, tambourine and snare on every beat, "
                    "melodic Jamerson bass lines, strings, vibes and polished vocal groups.",
        era="Detroit, 1960-1972",
        touchstones=("Holland-Dozier-Holland", "The Supremes", "The Temptations", "Four Tops", "Marvin Gaye",
                     "The Funk Brothers", "James Jamerson"),
        tempo=(100, 135),
        feel="driving 4/4, backbeat on every quarter, straight",
        swing=50,
        modes=("major",),
        keys=("C major", "F major", "Bb major", "Eb major"),
        progressions=(
            "I-vi-IV-V",
            "I-IV-V-IV",
            "I-iii-IV-V",
            "vi-ii7-V7-I",
            "I-ii-iii-IV",
        ),
        harmonic_rhythm=1,
        harmony="Major-key pop harmony with doo-wop and gospel roots; secondary dominants and stepwise climbs; the "
                "'truck driver' modulation up a half or whole step for the last chorus.",
        voicing="close",
        comping="quarters",
        bass_style="motown",
        bass="James Jamerson style: melodic, syncopated electric bass with chromatic passing notes, ghosted "
             "16ths and anticipations, played with one finger on flatwound strings.",
        melody_density="medium",
        melody_scale="major",
        melody="Catchy, singable hooks in a comfortable range, call-and-response between lead and group, gospel "
               "inflections; title line repeated.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x.......x.....x.|x.......x.x.....",
            "snare":      "X...X...X...X...|X...X...X...X...",
            "closed hat": "x.x.x.x.x.x.x.x.|x.x.x.x.x.x.x.x.",
            "tambourine": "....x.......x...|....x.......x...",
        }},
        drums="Snare (often doubled by hand claps or foot stomps) on all four beats, tambourine on 2 and 4, "
              "kick on 1 and 3, 8th hats; drive comes from the four-to-the-bar backbeat.",
        form=(("intro", 4), ("verse", 8), ("chorus", 8), ("verse", 8), ("chorus", 8), ("bridge", 8), ("chorus", 8),
              ("chorus", 8)),
        instruments=("electric bass", "drums", "tambourine", "piano", "guitar", "strings", "vibraphone",
                     "baritone sax", "vocal group"),
        sound_design="Hitsville 'Snakepit' room sound, compressed and bright for AM radio; vibes and strings "
                     "doubling lines; Jamerson's Precision bass upfront.",
        production="Mono-focused mixes, loud and bright, heavy limiting; vocals and tambourine cut through on "
                   "car radios; songs under three minutes.",
        theory="Pop-form major-key harmony with gospel and doo-wop roots; four-beat backbeat and syncopated, "
               "melodic bass make the groove; key changes lift final choruses.",
        mix=Mix(lufs=(-14, -10), lra=(5, 9), low_end="moderate", tone="bright", width="narrow"),
    ),
    Genre(
        name="philly soul",
        family="r&b and soul",
        aliases=("philadelphia soul", "sound of philadelphia", "tsop"),
        parent="soul",
        description="Philadelphia's lush, orchestral soul: sweeping strings and horns, vibes, a silky four-on-"
                    "the-floor-leaning groove and sweet vocal-group harmonies; the bridge to disco.",
        era="Philadelphia (Sigma Sound), late 1960s to late 1970s",
        touchstones=("Gamble and Huff", "Thom Bell", "MFSB", "The O'Jays", "Harold Melvin & the Blue Notes",
                     "The Stylistics", "The Delfonics"),
        tempo=(95, 125),
        feel="smooth, straight 4/4 with four-on-the-floor kick and open hi-hat offbeats",
        swing=50,
        modes=("major", "minor"),
        keys=("C major", "F major", "Bb major", "Eb major"),
        progressions=(
            "Imaj7-vi7-ii7-V7",
            "IVmaj7-iii7-ii7-Imaj7",
            "Imaj9-IVmaj9",
            "ii9-V13-Imaj9",
            "minor: i9-iv9-VII13-IIImaj7",
        ),
        harmonic_rhythm=1,
        harmony="Sophisticated jazz-pop harmony: major 7ths, 9ths and 13ths, ii-V chains, chromatic passing chords; "
                "Thom Bell's string and woodwind voicings; modulations.",
        voicing="drop2",
        comping="offbeat",
        bass_style="syncopated",
        bass="Ronnie Baker-style electric bass: melodic, octave-leaping syncopated lines with 16th pickups, "
             "driving the four-on-the-floor.",
        melody_density="medium",
        melody_scale="major",
        melody="Sweet lead vocals (falsetto in Thom Bell productions) answered by group harmonies; string "
               "countermelodies and horn punctuations around the vocal.",
        groove={"step": 0.25, "swing": 50, "pattern": {
            "kick":       "x...x...x...x...",
            "snare":      "....x.......x...",
            "closed hat": "xo.oxo.oxo.oxo.o",
            "open hat":   "..x...x...x...x.",
            "conga":      "......x.x.....x.",
        }},
        drums="Earl Young's style: four-on-the-floor kick, snare on 2 and 4, open hi-hat on the offbeats, congas "
              "and percussion; precise and danceable; fills on toms into choruses.",
        form=(("intro", 8), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("instrumental", 8),
              ("chorus", 8), ("vamp", 16)),
        instruments=("string section", "horn section", "vibraphone", "electric bass", "drums", "congas",
                     "electric piano", "vocal group"),
        sound_design="Lush orchestral strings, French horns, vibes, wah guitar, warm Rhodes; polished Sigma Sound "
                     "studio warmth.",
        production="Wide, layered orchestral mixes with plate reverb; rhythm section tight and centred; dynamics "
                   "preserved; long vamps for the dance floor.",
        theory="Jazz-pop extended harmony and ii-V chains over a proto-disco four-on-the-floor; orchestration "
               "(strings, woodwinds, vibes) is treated as composition.",
        mix=Mix(lufs=(-15, -11), lra=(6, 10), low_end="moderate", tone="warm", width="wide"),
    ),
]
