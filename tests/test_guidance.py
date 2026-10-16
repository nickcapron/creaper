"""What steers Claude: the MCP server's instructions and the chat panel's prompt."""

import asyncio
import re

from creaper import server  # noqa: F401  (import order: server first)
from creaper import chat

# Read on every turn, so every word costs: the old 3,474-word block buried the song
# workflow. Grow it only by moving detail into tool descriptions first.
INSTRUCTIONS_WORD_BUDGET = 2000
# Words in the instructions that look like tool names but are parameters or result fields.
NOT_TOOLS = {"browser_path", "chords_item", "clipped_runs", "display_text", "display_value", "harsh_pct_p95",
             "item_id", "peak_to_loudness_db", "per_channel", "per_section", "performance_feel", "realtime_only",
             "true_peak_ok"}


def tool_names():
    return {t.name for t in asyncio.run(server.mcp.list_tools())}


def test_instructions_stay_within_budget():
    assert len(server.INSTRUCTIONS.split()) <= INSTRUCTIONS_WORD_BUDGET


def test_instructions_open_with_the_song_checklist():
    text = server.INSTRUCTIONS
    checklist = text.index("Making a song")
    assert checklist < 200  # first thing Claude reads
    steps = re.findall(r"^\s*(\d+)\. ", text[checklist:text.index("When the user complains")], re.M)
    assert steps == [str(i) for i in range(1, len(steps) + 1)] and len(steps) >= 10
    for check in ("measure_structure", "check_groove", "measure_tracks(per_section=True)", "compare_mix_to_style",
                  "master_to_target", "check_ending", "export_mix", 'candidates="arturia"'):
        assert check in text[checklist:text.index("When the user complains")], check


def test_instructions_map_complaints_to_measurements():
    text = server.INSTRUCTIONS
    complaints = text[text.index("When the user complains"):text.index("Conventions:")]
    for word, tool in (("boring", "measure_structure"), ("overpowering", "measure_tracks"),
                       ("harsh", "harsh_pct_p95"), ("fake", "find_arturia_presets"), ("stiff", "check_groove"),
                       ("out of tune", "check_tuning")):
        line = next(ln for ln in complaints.splitlines() if word in ln)
        assert tool in line or tool in complaints[complaints.index(line):complaints.index(line) + 200], word


def test_every_tool_the_guidance_names_exists():
    names = tool_names()
    for text in (server.INSTRUCTIONS, chat.PANEL_PROMPT):
        mentioned = set(re.findall(r"\b[a-z]+(?:_[a-z0-9]+)+\b", text)) - NOT_TOOLS
        assert mentioned <= names, mentioned - names


def test_panel_prompt_carries_the_workflow():
    p = chat.PANEL_PROMPT
    assert "audition_sounds" in p and "load_arturia_preset" in p and "program the synths yourself" not in p
    for check in ("get_genre_profile", "measure_structure", "measure_tracks", "compare_mix_to_style", "check_ending"):
        assert check in p


def test_slash_commands_expand_to_the_prompts():
    composed = chat.expand_slash_command("/compose deep house in F minor")
    assert "deep house" in composed and "in F minor" in composed and "measure_structure" in composed
    assert "full-length" in chat.expand_slash_command("/Compose synthwave")
    assert chat.expand_slash_command("/master -14").startswith("Master my REAPER project for -14 LUFS")
    assert "techno master" in chat.expand_slash_command("/master techno")
    assert "in a house style" in chat.expand_slash_command("/mix house")
    assert chat.expand_slash_command("/critique").startswith("Critique the mix")
    for plain in ("make it louder", "/compose", "/composer thing", "use /mix later"):
        assert chat.expand_slash_command(plain) == plain
