# creaper

![creaper: an AI producer that lives inside REAPER](assets/brand/creaper-banner.svg)

**Let Claude compose, arrange, mix and master in [REAPER](https://www.reaper.fm), with
your own plugins, from a chat panel docked right inside it.**

creaper connects Claude to your open REAPER project. You ask in plain language; Claude
writes full-length songs in 264 genres, programs your synths, builds FX chains and
routing, adds vocals, mixes and masters, and exports finished music and game sound
effects. Claude can't hear, so creaper measures the actual audio (loudness, tuning,
clarity, the spectrum) and checks its own work before calling it done.

> "Make a 6-minute piano house track at 124 BPM with a proper DJ intro and outro."
>
> "Reharmonize my chorus with tritone subs and tell me what each change does."
>
> "Add a robot vocal singing the hook: 'we were never here'."
>
> "The chorus feels muddy. Measure the mix from bar 33 to 49 and tell me why."
>
> "Mix every track, then master it for streaming."
>
> "Make 3:00 of tense laboratory music for my game in 7/8, ending so it crossfades
> cleanly into the next track."
>
> "Design five variations of a hockey slap shot and export each as a trimmed, mono
> 24-bit WAV for my game."

Every change is a named undo step (`creaper: add ReaComp to Vocal`), so **Ctrl+Z undoes
anything Claude did**.

It works with Claude Desktop, Claude Code, and any other app that supports the
[Model Context Protocol](https://modelcontextprotocol.io). Each user signs in with their
own Claude account; no API key needed.

## What Claude can do

| Area | Tools |
| --- | --- |
| **Read the project** | Overview (tempo, time signature, markers, regions, tracks, selection), track details (items, FX, sends), FX parameters, installed plugins |
| **Compose** | Create tracks with instruments, MIDI items and notes; chord parts from symbols (`Am7`, `Cmaj7/E`) or Roman numerals (`ii7-V7/V-bVII`) in 11 voicings and 20 comping rhythms; basslines in 18 styles; motif-based melodies; genre drum grooves; a whole genre sketch in one call; sustain/mod/expression/pitch bend/aftertouch, program changes with bank select, reading and clearing controllers, markers and regions |
| **Music theory** | Scales and modes spelled correctly, chord naming, Roman-numeral and harmony analysis (of symbols or your MIDI), key detection, cadences, progression suggestions, reharmonization, four-part voice leading and a rule checker, modulation routes, rhythms (clave, Euclidean, polyrhythms) |
| **Plugins** | Browse installed plugins by kind, category and developer; load instruments and effects by loose name; read and set parameters by value or by label, several at once; list and load presets; split multi-output instruments onto tracks |
| **Sound library** | Save any plugin's current sound with a name and tags, browse, and recall it on any track in any project |
| **Edit MIDI** | Quantize (grid, strength, swing), humanize, transpose, snap to a scale, set or ramp velocities, strum chords, legato, and motif development (diatonic transposition, inversion, retrograde, augmentation, harmony lines, sequences, negative harmony); on all notes, a pitch/time range, or what's selected in the MIDI editor |
| **Automate** | Volume, pan and any plugin parameter: points, ramps (a filter sweep over the build) or LFOs (wobbles, tremolo), in real units; read and clear envelopes |
| **Edit clips** | Move, trim, split, duplicate, fade, re-pitch, time-stretch and delete audio or MIDI items; import audio files |
| **Vocals** | Uses the best source on your machine: chops real vocal samples into rhythmic, in-key chops; sings through VocalVST (a singing plugin) with the lyrics set, the notes captured and the take rendered for you; hands a melody and lyrics to singing synth apps (Synthesizer V, ACE Studio, VOCALOID, OpenUtau) as MIDI with the words on the notes; or sings lyrics itself as a talk box or vocoder from your computer's own voices |
| **Record** | Audio interface inputs and MIDI devices; arm, monitor and set the record mode (input, resample the track's output, MIDI overdub/replace); record a bar range that stops by itself; pick, compare or explode takes. Claude warns you before REAPER asks which new files to keep, and waits while you answer |
| **Save & deliver** | Save, save as, and snapshot copies; export the mix (or a region or bar range) to WAV/FLAC/MP3/OGG (Vorbis quality of your choice) with loudness and true peak checked and no clipping; stems for every track, lined up; a check that the ending suits its use (no fade or silence for tracks a game or playlist crossfades, a real ending for a finale, a tight stinger). Exports and mastering refuse a mix that clips, never changes level or is piercing, and say why (you can still ask for it anyway) |
| **Themes across songs** | Save a motif (a game's or album's signature theme) and place it in any later song, in that song's key and mode, slower, faster or in another octave |
| **Arrange** | Tempo changes, ramps and time-signature changes over the song; markers and regions (add, rename, move, resize, recolor, delete); time selection, loop points and repeat; track templates; freeze and unfreeze heavy tracks |
| **Samples & loops** | Search your sample folders by name, role, tempo and key, with each result checked by ear; place loops stretched to the project tempo and moved into key; build drum kits from any samples in REAPER's sampler |
| **Routing** | A map of folders, sends, sidechains and outputs; folders; sends; master-send on/off |
| **Mix** | A whole first mix in one call (auto_mix): every track measured and given a role, then levels for the genre, high-pass and mud cuts, compression, panning, reverb, sidechain, headroom, and robot vocals kept clear of the parts covering them. Plus add, remove, bypass FX; volume, pan, mute, solo, color; sends; side-chain ducking (calibrated to a depth), submix buses, parallel compression, a starting vocal chain, mastering to a loudness target |
| **Genres** | 265 genre profiles, from house and drill to bebop, flamenco, amapiano and Baroque: how each is composed, played, arranged and mixed, and a check of your mix against one |
| **Remember** | Notes Claude keeps between sessions: your taste, plugin quirks, mix lessons |
| **Check by measuring** | Claude can't hear, so it measures what a listener would notice: whether the song develops or just loops (bars that copy other bars, sections that copy earlier ones, the energy arc across sections, the length against the genre's form); whether a part plays like a performance or a machine (timing, accents, swing, fills); each track's level in every section against its role, and each drum's level on a one-track kit; how understandable a vocal's words are, alone and in the mix (STOI); whether each part is in tune; and a spectrogram picture of the song it can look at |
| **Analyze** | Render the mix or one track and measure integrated/short-term loudness (LUFS), loudness range, true peak, clipping, crest factor, stereo correlation (including the low end), frequency balance by band and octave, harshness, sibilance and mud over time and narrow resonances, with a loudness timeline in bars |
| **Control** | Play a range of bars, stop, move the cursor, undo, run any REAPER action |

In Claude Desktop and Claude Code, creaper also adds five commands: **Compose in a genre**,
**Critique the mix**, **Mix the song**, **Master the song** and **Design a sound**.

## Music theory and genres

creaper gives Claude a composer's toolkit, so it works from theory instead of guessing:

- **Keys and spelling.** About 60 scales and modes (church modes, melodic and harmonic
  minor modes, bebop, pentatonic and symmetric scales, and 12-tone versions of maqam,
  raga and Japanese scales), with notes spelled as a musician writes them: E# in F#
  major, Bbb in a C dim7.
- **Analysis.** Roman numerals with inversions, secondary dominants, borrowed chords,
  tritone substitutes, the Neapolitan and augmented sixths; cadences; key detection;
  famous progressions recognised by name. `analyze_harmony` reads a MIDI item in your
  project and explains it, including a melody's passing tones, suspensions and
  appoggiaturas.
- **Writing.** Progressions by genre or mood (a library of about 50 named ones plus
  new ones from functional harmony), 15 reharmonization techniques, voicings from close
  position to rootless and quartal, four-part writing that follows the common-practice
  voice-leading rules, basslines (walking, 808, tumbao, one-drop...), comping (stabs,
  skank, bossa, montuno, strum, arpeggios...), and melodies built from a motif developed
  over phrases.
- **265 genres in 20 families.** Each profile has the style's era and touchstones,
  tempo, feel and swing, modes, typical progressions and harmonic rhythm, voicing,
  comping, bass and melody habits, a drum groove, song form with bar counts,
  instruments, sound design, production habits and mix targets. `sketch_song` turns a
  profile into drums, bass, chords and melody on new tracks in one call.

These are rules of thumb drawn from the records that define each style, not laws.

## Works with your plugins

creaper uses whatever is installed: VST, VST3, CLAP, AU and JS, instruments and effects.

- **Learns what your plugins do by testing them.** `scan_plugins` loads each plugin on a
  hidden temporary track, plays notes into instruments and a test signal through effects,
  and measures the result: pitched synth or drum kit, range and character; reverb or delay
  tail, compression or gating, EQ curve, saturation, modulation, pitch shift, stereo width,
  latency. The findings go into a catalog (`get_plugin_catalog`, and alongside each plugin
  in `list_installed_fx`), so Claude picks plugins by what they do, not by their names.
- **Knows your library.** Claude can browse plugins by kind, category ("what reverbs do I
  have?") and developer. A plugin installed in several formats shows up once and loads
  as CLAP or VST3 first. Loose names work: "FET-76" finds *Comp FET-76*. Ambiguous names
  come back with the candidates instead of a guess.
- **Speaks each plugin's language.** Parameters are set in the plugin's own units and
  labels: `-18` dB, `2500` Hz, or text for switches and menus ("Saw", "Low Pass", "16'").
  Several settings can change in one undo step. The thousands of placeholder "MIDI CC"
  parameters that many VST3 plugins expose are hidden.
- **Presets.** Factory programs and presets saved in REAPER can be listed and loaded.
  Plugins that keep presets in their own browser (Arturia, for example) are detected,
  and Claude offers to open the plugin window instead.
- **Arturia's library, searchable.** With Arturia instruments installed,
  `find_arturia_presets` searches their factory presets (read-only, from Arturia's own
  preset database) by type (Bass, Pad, Lead...), subtype (Sub Bass, Evolving Pad...),
  character (warm, dark, wide...) and genre tags, for the plugins you have. Claude then
  tells you which preset to pick in the plugin's browser.
- **Your own sound library.** Pick a sound in any plugin's own browser and tell Claude
  "save this as Dark Pad". creaper captures the plugin's complete state with tags and a
  description, and Claude can recall it on any track, in any project ("use a warm pad
  from my library"). Plugins that don't share their state are saved as parameter
  values instead. The library lives in `<REAPER resource path>/creaper/sounds/`.
- **Kits mapped by ear.** `map_drum_kit` plays every key of a drum instrument offline,
  identifies each sound (kick, snare, clap, hats, cymbals, toms, rim, percussion) and saves
  the layout. It compares sounds within the kit and checks for the General MIDI layout most
  commercial kits use; on held-out real-sample kits it gets about 84% of lanes right for
  General MIDI layouts and about half for custom ones, and says which case it's in.
  `audition_instrument` reports what a patch does: range, pitch tracking, envelope, tone.
- **Drums on any kit.** Drum patterns follow the instrument's own note names when it
  reports them ("Kick", "HH Closed"…). Otherwise creaper uses a drum map you've saved
  for that instrument (which can also put each drum on its own MIDI channel), then
  General MIDI. Every pattern reports which note each lane used, so a wrong guess is
  easy to spot and fix.
- **Multi-output instruments.** Drum machines, Elektron Overbridge, multitimbral synths:
  `split_instrument_outputs` gives each output its own track, named after the plugin's
  outputs (e.g. *Rytm - BD 1*, *Rytm - SD 2*).
- **Hardware plugins.** Plugins REAPER marks as real-time only (e.g. Overbridge) can't be
  rendered offline. Analysis warns when they'd be missing from a measurement.

Drum maps are saved in `<REAPER resource path>/creaper/drum_maps.json`. Some
instruments are known out of the box (currently **SILA**: each lane on its own MIDI
channel); a map you save under the same name overrides the built-in one. Claude
prefers a real drum instrument over REAPER's basic ReaSynDr, and skips hardware-only
plugins unless you say the device is connected.

## Mixing jobs, measured

The one-call jobs were checked against real renders, not just set up:

- **Side-chain ducking** measures the trigger (e.g. the kick) and sets its level and the
  compressor's threshold so it ducks by about the depth asked for (light ~2 dB, medium
  ~4-5 dB, heavy ~10 dB with ReaComp). Instrument tracks are ducked on a small bus right
  after them, because an instrument lets a trigger arriving on channels 3/4 through to
  its output. Sidechain-capable plugins (e.g. compressors with an "SC Source: External"
  switch) are switched over automatically.
- **Mastering** builds EQ → glue compressor → limiter on the master. A glue compressor
  creaper knows is set up and calibrated by measurement until it takes about 1.5 dB
  off the loud moments (how much the gap between loud and quiet moments shrinks, which
  make-up gain can't fake). Then the limiter and master level are adjusted until the
  integrated loudness is within 0.5 LU of the target, the true peak is checked against
  the ceiling (tightened if needed), and it warns when peaks and loudness are less
  than 7 dB apart (squashed). Before changing anything it checks the mix, and refuses a
  mix that clips, plays every section at one level, or is piercing for its genre. Tested with Arturia's Bus FORCE, Comp VCA-65, FET-76 and
  TUBE-STA and REAPER's ReaComp.
- **Plugin profiles** describe how specific plugins work, e.g. Bus FORCE's parallel
  dry/compressor/saturation paths (its compressor path is muted by default), or that
  FET-76 compresses more as its input goes up. Built in for REAPER's ReaComp and
  Arturia's Bus FORCE, Comp VCA-65/FET-76/TUBE-STA, EQ SITRAL-295 and Pre 1973/TridA/V76.
- **Plugin plumbing is off-limits.** Parameters that browse or save presets, drive
  hardware controllers or undo inside the plugin are hidden and refused.
- The jobs take your own plugins (`compressor=`, `eq=`, `glue_compressor=`, `fx=`);
  creaper configures REAPER's stock plugins itself and tells Claude what to set on
  others.

Notes are kept in `<REAPER resource path>/creaper/knowledge.json`; you can read, edit or
delete them.

## Install

You need **REAPER 7** (opened at least once) and a **Claude** account.

### Windows: one command

Open **PowerShell** (Start menu → type `powershell` → Enter; not *Run as administrator*,
so creaper installs for your own account), paste this whole line and press Enter:

```powershell
irm https://raw.githubusercontent.com/nickcapron/creaper/main/install.ps1 | iex
```

Copy it in one piece: `irm` on its own asks for a `Uri:`, and without `| iex` at the end
PowerShell only prints the installer instead of running it. When it's running you'll
see **creaper installer**, then *Installing creaper…*, then a few questions.

It installs Python if needed, puts creaper in its own folder (`%LOCALAPPDATA%\creaper`),
offers to install Claude Code with Anthropic's official installer, then runs
`creaper setup`, which:

- installs **ReaImGui** (for the chat panel) from its official GitHub release, if you
  don't have it;
- installs creaper's scripts in REAPER and starts them with REAPER;
- offers to connect creaper to **Claude Desktop** and to **Claude Code**.

It also adds a `creaper` command (`creaper doctor`, `creaper install-bridge` …) for new
terminals. Then sign in to Claude Code once (run `claude` in a new terminal) and restart
REAPER: the creaper panel opens by itself. Run the same command again to update.

The installer never asks for a Claude password or key; signing in happens in Claude's
own apps. To see what it does first, [read install.ps1](install.ps1).

### macOS, Linux, or by hand

You need Python 3.10 or newer.

```bash
pip install https://github.com/nickcapron/creaper/archive/refs/heads/main.zip
creaper setup
```

`creaper setup --dry-run` shows what it would do without changing anything. The
individual steps are below if you'd rather do them yourself.

**Optional extras** (never installed unless you ask for them):

- `creaper[ml]`: a music model (LAION's CLAP, Apache-2.0) that adds a "how it comes
  across" line to `check_song` (realistic or synthetic, modern or dated) and a
  sounds-alike score to `compare_to_reference`. About 1 GB with the model, which
  downloads the first time it's used.
- `creaper[asr]`: a speech recogniser (faster-whisper with Whisper's base.en model, MIT)
  that transcribes each line of a vocal, a robot vocal after `add_robot_vocal` or a
  VocalVST take after `render_vocalvst` (and in the mix, with `check_vocal_clarity`),
  and names the lines a listener would mishear and the words it missed, so Claude can
  rewrite them before you listen. About 300 MB with the model, which downloads the first
  time it's used.
- `creaper[analysis]`: librosa's beat tracker, for finding the bars of reference tracks.

```bash
pip install "creaper[ml] @ https://github.com/nickcapron/creaper/archive/refs/heads/main.zip"
```

**1. Install creaper** (manual steps)

```bash
pip install https://github.com/nickcapron/creaper/archive/refs/heads/main.zip
```

**2. Install the bridge script into REAPER**

```bash
creaper install-bridge
```

This copies creaper's scripts into REAPER's `Scripts/creaper` folder and sets REAPER
to start creaper whenever it launches: the bridge runs quietly in the background, and
the chat panel opens (once ReaImGui is installed; see *Chat inside REAPER*). It does
this with one clearly marked block in `Scripts/__startup.lua`, leaving anything else
in that file alone. Options:

- `--no-chat`: start only the bridge, not the panel.
- `--no-autostart`: don't start anything at launch (and remove creaper's block if it's
  there). Then run `Scripts/creaper/creaper_bridge.lua` yourself from the action list
  (*New action → Load ReaScript*); running it again stops it.

**3. Restart REAPER.**

**4. Check the connection**

```bash
creaper doctor
```

**5. Connect Claude**

*Claude Desktop:* open *Settings → Developer → Edit Config* and add creaper to
`claude_desktop_config.json`, then restart Claude Desktop:

```json
{
  "mcpServers": {
    "creaper": {
      "command": "python",
      "args": ["-m", "creaper"]
    }
  }
}
```

If `python` isn't on your PATH, use the full path to the Python you installed creaper
with (on Windows, something like `C:\\Users\\you\\AppData\\Local\\Programs\\Python\\Python312\\python.exe`).

*Claude Code:*

```bash
claude mcp add creaper -- python -m creaper
```

Then ask Claude something like "What's in my REAPER project?"

## Chat inside REAPER

Prefer not to switch windows? creaper includes a chat panel you can dock inside REAPER,
like the mixer. It runs your own installed **Claude Code**, signed in with your own
account, and that Claude can only use the creaper tools: it can work in your REAPER
project and nothing else on your computer.

**Which account pays:** the panel never handles logins or keys. It uses whatever Claude
Code is signed in with. Normally that's your Claude plan, and the panel shows how much
of your plan's limits you've used. If `ANTHROPIC_API_KEY` is set, Claude Code uses that
key instead and bills it per use. You're responsible for using your account within
[Anthropic's terms](https://www.anthropic.com/legal/consumer-terms); the
[API key route](https://code.claude.com/docs/en/authentication.md) is the one Anthropic
documents for third-party tools.

**You need:** [Claude Code](https://claude.com/claude-code), signed in once (run
`claude` in a terminal), and the free **ReaImGui** extension: install
[ReaPack](https://reapack.com), then in REAPER *Extensions → ReaPack → Browse packages*,
search for **ReaImGui**, install it and restart REAPER.

**Then:**

1. Run `creaper install-bridge` again, so the panel knows where Python and Claude Code are.
2. Restart REAPER: the panel opens by itself. (Closed it? Run **Script: creaper_chat.lua**
   from the action list, or put it on a toolbar or a shortcut.)
3. Click **Dock** to dock it. Type a message and press Enter (Ctrl+Enter adds a line).

The panel shows what Claude is doing as it works (each tool it runs) and how much of
your plan's 5-hour limit you've used. **Stop** interrupts a turn, and **New chat**
starts over. Conversations continue across REAPER restarts. Start a message with
`/compose`, `/mix`, `/master` or `/critique` (e.g. `/compose deep house in F minor`,
`/master -14`) to run the same step-by-step jobs Claude Desktop offers as commands.

Claude doesn't ask before routine edits in the panel (they're all undoable), but it
shows **Allow / Deny** before anything riskier: running an arbitrary REAPER action
(some can't be undone, like saving or deleting media) or deleting a track.

## Security notes

- creaper opens no network ports. The MCP server talks to its app over stdio, and the
  bridge exchanges files in your own REAPER resource folder.
- It never handles logins or API keys.
- The bridge runs only its own fixed commands, never code sent to it.
- The chat panel's Claude has no shell, file or web tools, only creaper's.
- Projects can come from other people, and names inside them (tracks, markers,
  presets) reach Claude as text. Claude is told to treat them as data, never as
  instructions, and the riskier tools need your confirmation in the panel. In Claude
  Desktop, keep per-tool approval on for `run_action` and `delete_track`.
- In the panel, replacing an existing file always asks, and so does the first write
  into a folder outside the project's, REAPER's project folder and your Music,
  Documents, Videos, Desktop and Downloads folders.
- `run_action` won't run scripts or actions that save, close, quit, delete files or
  open preferences; run those yourself from REAPER's action list.
- Notes Claude saves (`save_note`) are shown in full in the panel and come back to
  Claude marked as information, not instructions. They're in
  `<REAPER resource folder>/creaper/knowledge.json`; delete any you don't recognise.
- The installer installs a tagged release, and checks ReaImGui's plugin against its
  recorded SHA-256 before REAPER can load it. The optional music and speech models are each
  pinned to one commit.
- The panel's Claude runs with your Claude Code user settings (so your sign-in works),
  which includes any hooks you've set up there.

## Conventions Claude uses

- Tracks are named by number (1 = top), by name, or `master`.
- Bars and beats are 1-based, like REAPER's ruler.
- Inside a MIDI item, positions and lengths are in quarter notes: `1` = quarter,
  `0.5` = eighth, `0.25` = sixteenth, `4` = one bar of 4/4.
- Middle C is `C4` = 60.
- Drum lanes are step strings: `x` hit, `X` accent, `o` ghost, `1`–`9` velocity, `.` rest.
  Lane names are General MIDI drums (`kick`, `snare`, `closed hat`…) or note numbers for
  other kits.

## How it works

```
Claude app  ⇄  creaper MCP server (Python)  ⇄  files  ⇄  creaper_bridge.lua (inside REAPER)
```

REAPER's Lua has no networking, so the two halves talk through small JSON files in
REAPER's resource folder (`<resource path>/creaper/`). The bridge checks for a request
about 30 times a second, runs it with the ReaScript API, and writes the answer back. A
round trip takes about 40 ms.

For analysis, the bridge renders the requested range to a temporary 32-bit float WAV
(so overs above 0 dBFS aren't hidden). It saves your render settings first and restores
them afterwards. The server measures the file in Python, then deletes it.

## Better robot voices with Piper (optional)

Robot vocals use your computer's own speech voices. For clearer, more natural ones,
install [Piper](https://github.com/OHF-Voice/piper1-gpl), a free offline voice engine
(GPL-3.0, so it's a separate install), into creaper's Python environment:

```bash
python -m pip install piper-tts
```

Then put voices (an `.onnx` file and its `.onnx.json`, from
[rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices)) in
`<REAPER resource folder>/creaper/voices/piper/`. creaper lists them first and shows each
voice's license: for music you'll release, pick public domain or CC0 voices such as
Norman, John, Bryce, Joe, Kristin, LJSpeech or Cori. Some popular voices (Lessac, Ryan,
HFC) are for non-commercial use only.

## Good to know

- **Undo.** Each tool call is one undo step. Claude can also call `undo` itself.
- **Your render settings** are saved and restored around every analysis render, and
  rendered files are deleted afterwards (set `CREAPER_KEEP_RENDERS=1` to keep them in
  `<resource path>/creaper/renders`).
- **Portable REAPER installs:** set `CREAPER_REAPER_RESOURCE_PATH` to the portable
  folder for both `creaper install-bridge --reaper-resource-path ...` and the MCP
  server's environment.
- **Updating:** on Windows, run the installer command again. Otherwise
  `pip install --upgrade https://github.com/nickcapron/creaper/archive/refs/heads/main.zip`,
  then `creaper install-bridge` again and restart the bridge. A newly started bridge takes
  over from a running one, so you don't need to restart REAPER.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| "REAPER isn't answering" | Is REAPER open and the bridge running? Run `creaper doctor`. |
| `doctor` finds no heartbeat with a portable REAPER | Set `CREAPER_REAPER_RESOURCE_PATH` (see above). |
| "REAPER didn't answer within N seconds" | Close any open dialog in REAPER; modal windows can pause scripts. |
| A plugin parameter won't take a `display_value` | It may show text instead; use `display_text`, or the raw 0–1 `value`. |
| Drums land on the wrong sounds | The kit doesn't follow General MIDI or report note names. Tell Claude which note each drum is on; it saves a drum map for that instrument. |
| The chat panel says it needs ReaImGui | Install ReaImGui through ReaPack (see *Chat inside REAPER*) and restart REAPER. |
| `claude` or `creaper` "is not recognized" | Open a new PowerShell window (PATH changes only reach new ones). Still not found? Run the installer again: it adds both to your PATH. |
| The chat panel says Claude Code wasn't found | Install Claude Code, run `claude` once to sign in, then `creaper install-bridge` again. |
| An analysis of a hardware/Overbridge track is silent | Real-time-only plugins can't render offline. Record their output to an audio track first. |
| Audio items go offline while you're in another app | That's REAPER's "Set media items offline when application is not active" (Options > Preferences > Media, on by default). creaper brings them back online before every render; untick the setting to stop it. |

## Development

```bash
git clone https://github.com/nickcapron/creaper
cd creaper
python -m venv .venv
.venv/bin/pip install -e ".[dev]"     # Windows: .venv\Scripts\pip install -e ".[dev]"
.venv/bin/pytest
```

- `src/creaper/reaper/creaper_bridge.lua`: the REAPER side (plus `creaper_json.lua`)
- `src/creaper/reaper/creaper_chat.lua`: the dockable chat panel (ReaImGui)
- `src/creaper/chat.py`: runs one panel turn on Claude Code, limited to creaper's tools
- `src/creaper/server.py`: the MCP tools
- `src/creaper/bridge.py`: the file-based client
- `src/creaper/theory.py`: note names, chord symbols, drum patterns and MIDI edits
- `src/creaper/scales.py`, `harmony.py`: scales and modes, spelling, Roman numerals, chord naming, key detection, cadences, modulation
- `src/creaper/composer.py`: progressions, reharmonization, voicings and voice leading, bass, comping, melody, rhythm, MIDI harmony analysis
- `src/creaper/genres/`: the genre library, one module per family (`genres/__init__.py` has the schema and validator)
- `src/creaper/music_tools.py`: the theory, genre, composition and listening tools
- `src/creaper/listen.py`: per-note audio features, drum classification and kit mapping
- `src/creaper/pluginscan.py`, `scan_tools.py`: testing plugins and the plugin catalog
- `src/creaper/project_tools.py`: tempo map, program changes and controllers, routing
- `src/creaper/samplelib.py`, `sample_tools.py`: the sample library, loop tempo/key analysis, sampler kits
- `src/creaper/export_tools.py`: saving the project, exporting the mix and stems
- `src/creaper/record_tools.py`: recording and takes, time selection, markers, track templates, freezing
- `src/creaper/vocal_tools.py`, `speech.py`, `talkbox.py`: vocals (chops, singing-synth MIDI, text-to-speech, talk box and vocoder)
- `src/creaper/perception.py`, `ear_tools.py`: measuring what a listener would notice (clarity, tuning, spectrograms, structure, groove, per-section balance)
- `src/creaper/structure.py`: bar fingerprints, repetition and the energy arc (`measure_structure`)
- `src/creaper/arturia.py`: read-only search of Arturia's preset database
- `src/creaper/mix_tools.py`: auto_mix
- `src/creaper/motif_tools.py`: motifs reused across songs
- `src/creaper/installer.py`, `install.ps1`: `creaper setup` and the one-command Windows installer
- `assets/make_brand.py`: regenerates the logo, banner and thumbnail in `assets/brand/`
- `src/creaper/drums.py`: saved drum maps
- `src/creaper/analysis.py`: loudness (ITU-R BS.1770-4 / EBU R128), true peak, spectrum, stereo

Issues and pull requests are welcome.

## License

MIT
