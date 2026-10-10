# creaper

**Let Claude compose, mix and analyze in [REAPER](https://www.reaper.fm).**

creaper connects Claude to your open REAPER project. You ask in plain language;
Claude reads the project, writes MIDI, builds FX chains, sets up routing, and measures
the actual audio before giving mix feedback.

> "Make an 8-bar lo-fi progression in D minor on a new Keys track, with a swung drum
> beat underneath."
>
> "The chorus feels muddy. Measure the mix from bar 33 to 49 and tell me why."
>
> "Put a compressor on the vocal: threshold −18 dB, 4:1, and send it to a reverb bus at −12."
>
> "Play bars 17 to 25 so I can hear it."

Every change is a named undo step (`creaper: add ReaComp to Vocal`), so **Ctrl+Z undoes
anything Claude did**.

It works with Claude Desktop, Claude Code, and any other app that supports the
[Model Context Protocol](https://modelcontextprotocol.io). Each user signs in with their
own Claude account; no API key needed.

## What Claude can do

| Area | Tools |
| --- | --- |
| **Read the project** | Overview (tempo, time signature, markers, regions, tracks, selection), track details (items, FX, sends), FX parameters, installed plugins |
| **Compose** | Create tracks with instruments, MIDI items, notes, chord progressions from symbols (`Am7`, `Cmaj7/E`, `F#m7b5`) with voice leading, step-sequenced drums with swing and humanize, sustain/mod/expression/pitch bend, tempo and time signature, markers and regions |
| **Plugins** | Browse installed plugins by kind, category and developer; load instruments and effects by loose name; read and set parameters by value or by label, several at once; list and load presets; split multi-output instruments onto tracks |
| **Mix** | Add, remove, bypass FX; volume, pan, mute, solo, color; sends and buses |
| **Analyze** | Render the mix or one track and measure integrated/short-term loudness (LUFS), loudness range, true peak, clipping, crest factor, stereo correlation (including the low end), and frequency balance by band and octave, with a loudness timeline in bars |
| **Control** | Play a range of bars, stop, move the cursor, undo, run any REAPER action |

## Works with your plugins

creaper uses whatever is installed: VST, VST3, CLAP, AU and JS, instruments and effects.

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

Drum maps are saved in `<REAPER resource path>/creaper/drum_maps.json`.

## Install

You need **REAPER 7** (tested on 7.58) and **Python 3.10 or newer**.

**1. Install creaper**

```bash
pip install git+https://github.com/nickcapron/creaper
```

**2. Install the bridge script into REAPER**

```bash
creaper install-bridge --autostart
```

This copies `creaper_bridge.lua` into REAPER's `Scripts/creaper` folder. `--autostart`
also starts it whenever REAPER launches (it adds one line to `Scripts/__startup.lua`).
Leave the flag off if you'd rather start it yourself.

**3. Start the bridge.** Restart REAPER, or in REAPER open *Actions → Show action list →
New action → Load ReaScript*, pick `Scripts/creaper/creaper_bridge.lua` and run it.
It runs quietly in the background; running the action again stops it.

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
like the mixer. It runs on your own **Claude Code** (so your Claude plan, no API key),
and that Claude can only use the creaper tools: it can work in your REAPER project
and nothing else on your computer.

**You need:** [Claude Code](https://claude.com/claude-code), signed in once (run
`claude` in a terminal), and the free **ReaImGui** extension: install
[ReaPack](https://reapack.com), then in REAPER *Extensions → ReaPack → Browse packages*,
search for **ReaImGui**, install it and restart REAPER.

**Then:**

1. Run `creaper install-bridge` again, so the panel knows where Python and Claude Code are.
2. In REAPER, open the action list and run **Script: creaper_chat.lua**. Put it on a
   toolbar or give it a shortcut if you like.
3. Click **Dock** to dock it. Type a message and press Enter (Ctrl+Enter adds a line).

The panel shows what Claude is doing as it works (each tool it runs) and how much of
your plan's 5-hour limit you've used. **Stop** interrupts a turn, and **New chat**
starts over. Conversations continue across REAPER restarts.

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

## Good to know

- **Undo.** Each tool call is one undo step. Claude can also call `undo` itself.
- **Your render settings** are saved and restored around every analysis render, and
  rendered files are deleted afterwards (set `CREAPER_KEEP_RENDERS=1` to keep them in
  `<resource path>/creaper/renders`).
- **Portable REAPER installs:** set `CREAPER_REAPER_RESOURCE_PATH` to the portable
  folder for both `creaper install-bridge --reaper-resource-path ...` and the MCP
  server's environment.
- **Updating:** `pip install --upgrade git+https://github.com/nickcapron/creaper`, then
  `creaper install-bridge` again and restart the bridge. A newly started bridge takes
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
| The chat panel says Claude Code wasn't found | Install Claude Code, run `claude` once to sign in, then `creaper install-bridge` again. |
| An analysis of a hardware/Overbridge track is silent | Real-time-only plugins can't render offline. Record their output to an audio track first. |

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
- `src/creaper/theory.py`: note names, chord symbols, voice leading, drum patterns and drum-name matching
- `src/creaper/drums.py`: saved drum maps
- `src/creaper/analysis.py`: loudness (ITU-R BS.1770-4 / EBU R128), true peak, spectrum, stereo

Issues and pull requests are welcome.

## License

MIT
