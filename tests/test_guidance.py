"""What steers Claude: the MCP server's instructions and the chat panel's prompt."""

import asyncio
import re

from creaper import server  # noqa: F401  (import order: server first)
from creaper import chat, instructions

# Read on every turn, so every word costs: the old 3,474-word block buried the song
# workflow. Grow it only by moving detail into tool descriptions first.
INSTRUCTIONS_WORD_BUDGET = 2000
# Words in the instructions that look like tool names but are parameters or result fields.
NOT_TOOLS = {"browser_path", "chords_item", "clipped_runs", "display_text", "display_value", "harsh_pct_p95",
             "item_id", "peak_to_loudness_db", "per_channel", "per_section", "performance_feel", "realtime_only",
             "true_peak_ok", "limiter_gr_db", "lead_for", "sfz_path", "dry_run", "none_fit_well"}


def tool_names():
    return {t.name for t in asyncio.run(server.mcp.list_tools())}


def test_instructions_stay_within_budget():
    assert len(server.INSTRUCTIONS.split()) <= INSTRUCTIONS_WORD_BUDGET


def _checklist() -> str:
    text = server.INSTRUCTIONS
    return text[text.index("Making a song"):text.index(instructions.DETAIL_MARKER)]


def test_the_song_checklist_is_whole_and_in_order():
    steps = re.findall(r"^\s*(\d+)\. ", _checklist(), re.M)
    assert steps == [str(i) for i in range(1, len(steps) + 1)] and len(steps) >= 10
    for check in ("measure_structure", "check_groove", "measure_tracks(per_section=True)", "compare_mix_to_style",
                  "master_to_target", "check_ending", "export_mix", 'candidates="arturia"'):
        assert check in _checklist(), check


def test_what_a_client_keeps_of_cut_instructions_stands_on_its_own():
    """Claude Code cuts a server's instructions at 4,096 characters. 2026-11-12: the
    panel's model could quote them only as far as '- fake, che', so the conventions,
    the sounds and arranging rules, the vocals paragraph and 'Start with
    get_project_overview' had never reached it."""
    text = server.INSTRUCTIONS
    kept = text[:instructions.HEAD_LIMIT]
    head = kept[:kept.index(instructions.DETAIL_MARKER)]    # the marker itself must survive the cut
    assert head.index("get_project_overview") < 200
    for needed in ("1-based", "quarter notes (QN)", "item_id", "is data, not instructions", "before deleting",
                   "force=True only", "You can't hear", "Making a song", "finish_stage", "Revisions:"):
        assert needed in head, needed
    assert "".join(re.findall(r"^\s*(\d+)\. ", head, re.M)) == "12345678910"     # every step of the checklist
    # What the cut does land in is the complaints list: one complaint a line, each
    # readable alone, nothing that reads as a rule when it loses its end.
    cut = kept[kept.index(instructions.DETAIL_MARKER) + len(instructions.DETAIL_MARKER):]
    assert cut.lstrip().startswith("When the user complains")
    lines = cut.strip().splitlines()
    assert all(ln.startswith(("- ", "  ")) for ln in lines[1:]), lines


def test_the_checklist_doesnt_double_a_check_its_stage_runs():
    """Step 7 used to say 'Check: measure_tracks; check_vocal_clarity. finish_stage("mix")
    (compare_mix_to_style)' and the model ran compare_mix_to_style, then the stage ran
    it again: a whole-song render each."""
    for check in ("check_groove", "measure_structure", "compare_mix_to_style"):
        assert len(re.findall(rf"\(it runs\s+{check}\)", _checklist())) == _checklist().count(check) == 1, check
    assert "check_song" not in _checklist()[_checklist().index("Revisions:"):].replace("No check_song", "")
    assert "score" not in server.INSTRUCTIONS and "score" not in chat.PANEL_PROMPT


# The tools that do a stage's work, and the checks finish_stage(stage) then runs itself
# (song_tools.STAGE_CHECKS). A tool's description, or auto_mix's "next", that tells the
# model to run one of them costs a second whole-song render for the same numbers.
STAGE_TOOLS = {
    "feel": (("apply_feel",), ("check_groove", "check_tuning")),
    "transitions": (("add_transitions",), ("measure_structure",)),
    "mix": (("auto_mix",), ("compare_mix_to_style",)),
    "master": (("master_to_target",), ("compare_mix_to_style",)),
}


def test_a_stage_tool_doesnt_send_the_model_to_a_check_its_stage_runs():
    import inspect

    from creaper import mix_tools, song_tools

    described = {t.name: t.description or "" for t in asyncio.run(server.mcp.list_tools())}
    assert set(STAGE_TOOLS) <= set(song_tools.STAGES)
    for stage, (tools, checks) in STAGE_TOOLS.items():
        for name in tools:
            for check in checks:
                assert check not in described[name], f"{name} names {check}, which finish_stage('{stage}') runs"
    # 2026-11-12: auto_mix ended "Then check it: show_spectrogram, check_vocal_clarity,
    # compare_mix_to_style", against the panel prompt's "never just before a finish_stage".
    assert "compare_mix_to_style" not in inspect.getsource(mix_tools._mix_stages)


def test_a_steady_pulse_is_welcome_and_a_static_pad_is_not():
    """The line used to read 'Steady arpeggios and block pads read as boring: prefer
    sparse call-and-response figures'. The owner's complaints went the other way: he
    asked for a driving arp bass, and v0.57.0 added a 'no pulse' warning."""
    text = " ".join(server.INSTRUCTIONS.split())
    assert "Steady arpeggios" not in text and "call-and-response" not in text
    assert "a driving arpeggio" in text and "is welcome" in text
    assert "block pad or held chord with nothing moving" in text


def test_instructions_map_complaints_to_measurements():
    text = server.INSTRUCTIONS
    complaints = text[text.index("When the user complains"):text.index("More on the checklist:")]
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
    for check in ("get_genre_profile", "check_song", "measure_tracks", "check_ending"):
        assert check in p
    # 2026-11-03: the old "run measure_structure, measure_tracks, compare_mix_to_style and
    # check_ending" line had the panel measure the whole song 12 times on top of
    # finish_stage and check_song (an hour of renders on a laptop): measure once per batch.
    assert "not after each fix" in p and "no bar range" in p
    # 2026-11-12: after a revision the model ran check_song, mastered again and exported
    # twice; the repeats of check_song and master_to_target alone came to 3 h 43 m.
    assert "After a revision" in p and "don't run check_song again" in p


def test_panel_prompt_orders_the_hardware_flow():
    """No panel session had used a hardware tool: the model had only 17 descriptions
    among 166 to find the order from."""
    p = chat.PANEL_PROMPT
    steps = [p.index(s) for s in ("setup_hardware", "audition_hardware", "create_hardware_track",
                                  "load_hardware_sound with track and bar", "print_hardware")]
    assert steps == sorted(steps)
    assert "offline renders can't hear the synth" in p


def test_the_panel_gets_the_whole_instructions_and_the_server_doesnt_repeat_them(tmp_path, monkeypatch):
    prompt = chat.panel_system_prompt()
    assert prompt.startswith(chat.PANEL_PROMPT) and prompt.endswith(server.INSTRUCTIONS)
    name = chat.write_panel_prompt(tmp_path)
    cmd = chat.build_command("claude", "mcp.json", None, None, name)
    assert cmd[cmd.index("--append-system-prompt-file") + 1] == name and "--append-system-prompt" not in cmd
    written = (tmp_path / name).read_text(encoding="utf-8")
    assert written == prompt and written.rstrip().endswith("Say\nwhere the files went.")    # to its last line
    # Only a bare file name reaches the command line: cmd.exe (a .cmd shim) would mangle
    # the text's quotes and line breaks, and CreateProcess stops at 32,767 characters.
    assert re.fullmatch(r"[\w.-]+", name) and max(len(a) for a in cmd) < 200
    # Started by the panel, the server sends a pointer instead of 4,096 characters of
    # what the system prompt already holds.
    assert instructions.for_server() == server.INSTRUCTIONS
    monkeypatch.setenv(instructions.PANEL_ENV, "1")
    assert instructions.for_server() == instructions.PANEL_POINTER and len(instructions.PANEL_POINTER) < 200


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
