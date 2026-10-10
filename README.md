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
| **Mix** | Add, remove, bypass FX and load presets; set parameters in the plugin's own units ("−18 dB", "2.5 kHz", "4:1"); volume, pan, mute, solo, color; sends and buses |
| **Analyze** | Render the mix or one track and measure integrated/short-term loudness (LUFS), loudness range, true peak, clipping, crest factor, stereo correlation (including the low end), and frequency balance by band and octave, with a loudness timeline in bars |
| **Control** | Play a range of bars, stop, move the cursor, undo, run any REAPER action |

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
| A plugin parameter won't take a `display_value` | Some plugins don't show numbers; Claude can set the raw 0–1 `value` instead. |

## Development

```bash
git clone https://github.com/nickcapron/creaper
cd creaper
python -m venv .venv
.venv/bin/pip install -e ".[dev]"     # Windows: .venv\Scripts\pip install -e ".[dev]"
.venv/bin/pytest
```

- `src/creaper/reaper/creaper_bridge.lua`: the REAPER side, a single dependency-free file
- `src/creaper/server.py`: the MCP tools
- `src/creaper/bridge.py`: the file-based client
- `src/creaper/theory.py`: note names, chord symbols, voice leading, drum patterns
- `src/creaper/analysis.py`: loudness (ITU-R BS.1770-4 / EBU R128), true peak, spectrum, stereo

Issues and pull requests are welcome.

## License

MIT
