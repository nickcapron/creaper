"""Sound design and recording on hardware synths. A fake bridge stands in for REAPER with
a microKORG on a MIDI interface: it keeps an edit buffer, answers the dump requests the
way Korg's MIDI implementation lays them out, and "records" a synthesized tone when a
take is started. The patches here are creaper's own (microkorg.init_program), never
Korg's factory data."""

import numpy as np
import pytest
import soundfile as sf
from hardware_fakes import MIC, SSL_WASAPI, WINDOWS, Reaper

from creaper import hardware_setup as setup
from creaper import hardware_sound_tools as hst
from creaper import hardware_tools as hw
from creaper import microkorg as mk
from creaper import server
from creaper.sounds import SoundLibrary



def global_data(protect=True, sysex=True, cc=True, pc=True, clock="internal"):
    g = bytearray(200)
    g[5] = 0x04 | (1 if protect else 0)
    g[8] = ("internal", "external", "auto").index(clock)
    g[11] = 95                                   # timbre select CC
    g[16] = 0x80 if sysex else 0
    g[17] = 0x40 | (0x04 if cc else 0) | (0x01 if pc else 0)
    ccs = [5, 77, 14, 15, 78, 82, 18, 19, 20, 21, 22, 83, 74, 71, 79, 85, 7, 10, 0xFF, 92, 23, 24, 25, 26, 73, 75, 70,
           72, 87, 27, 88, 76, 28, 29, 30, 31, 0xFF, 12, 93, 13, 94, 0xFF]
    g[18:60] = bytes(ccs)
    g[72:200] = bytes(range(128))
    return bytes(g)


class FakeKorg:
    """REAPER with a microKORG behind 'UM-ONE' (output 1, input 0)."""

    def __init__(self, tmp_path):
        self.directory = tmp_path
        self.buffer = mk.init_program(name="user")
        self.programs = {n: mk.apply(mk.init_program(name=f"prog{n}"), {"cutoff": n}) for n in range(128)}
        self.globals = global_data()
        self.history = [{"seq": 0x40000001, "hex": "903C40", "device": 0}]
        self.sent: list[str] = []
        self.answers = True
        self.audio_running = True
        self.commands: list[tuple[str, dict]] = []
        self.take = None
        self.tone_delay = 0.0          # seconds the "synth" answers late
        self.silent = False
        self.gain = 1.0                # the interface's input gain, both inputs
        self.item_seconds = None       # what the project shows of a recording; None = all of it
        self.left_gain = 1.0           # the first input against the second: 0.03 = a plug not making contact
        self.noise_dbfs = None
        self.reaper = Reaper()
        self.patch_items: list[dict] = []
        self.sound_events = None       # the SysEx REAPER finds in a sound item; None = what creaper wrote there
        self.sound_sysex_count = None
        self.parts = [{"id": "{P1}", "start_seconds": 4.0, "end_seconds": 8.0, "start": {"bar": 3, "beat": 1},
                       "sysex_count": 0, "sysex_events": []}]
        self.part_device = "microKORG"  # the device the hardware part in the project plays
        self.printed = "never"         # what the bridge says of the part's print: yes, stale, never
        self.tempo = 120.0             # the project's opening tempo
        self.tempo_changes: list[dict] = []

    def _reply(self, function, payload=b""):
        self.history.append({"seq": self.history[-1]["seq"] + 1, "device": 0,
                             "hex": mk.message(1, function, payload).replace(" ", "")})

    def _receive(self, hexstr):
        self.sent.append(hexstr)
        raw = bytes.fromhex(hexstr.replace(" ", ""))
        if raw[0] & 0xF0 == 0xC0:
            self.buffer = self.programs[raw[1]]
            return
        parsed = mk.parse_message(hexstr)
        if not parsed or not self.answers:
            return
        function, payload = parsed
        if function == mk.F_CURRENT_REQUEST:
            self._reply(mk.F_CURRENT_DUMP, mk.pack(self.buffer))
        elif function == mk.F_GLOBAL_REQUEST:
            self._reply(mk.F_GLOBAL_DUMP, mk.pack(self.globals))
        elif function == mk.F_CURRENT_DUMP:
            data = mk.unpack(payload)
            if len(data) == mk.PROGRAM_BYTES:
                self.buffer = data
                self._reply(mk.F_LOAD_OK)
            else:
                self._reply(mk.F_FORMAT_ERROR)
        elif function == mk.F_WRITE_REQUEST:
            self.programs[payload[1]] = self.buffer
            self._reply(mk.F_WRITE_OK)

    def _sound_item(self, written):
        events = self.sound_events if self.sound_events is not None else [written["sysex"].replace(" ", "")]
        count = self.sound_sysex_count if self.sound_sysex_count is not None else len(events)
        return {"id": "{S1}", "sound": written["name"], "sysex": written["sysex"], "start_seconds": 3.5,
                "end_seconds": 4.0, "start": {"bar": 2, "beat": 4}, "sysex_count": count, "sysex_events": events}

    def _record(self, params):
        """A wav of what the 'synth' played: a decaying tone per note, late by tone_delay."""
        fs = 48000
        seconds = params.get("seconds") or (params["end_seconds"] - params["start_seconds"])
        audio = np.zeros(int(seconds * fs))
        for n in params.get("notes") or [{"at": 0.0, "length": 1.0, "pitch": 60}]:
            a = int((n["at"] + self.tone_delay) * fs)
            t = np.arange(int(n["length"] * fs)) / fs
            tone = 0.5 * np.sin(2 * np.pi * 440 * 2 ** ((n["pitch"] - 69) / 12) * t) * np.exp(-3 * t)
            audio[a:a + tone.size] += tone[: max(0, audio.size - a)]
        if self.silent:
            audio[:] = 0
        if self.noise_dbfs is not None:      # the hiss of an open analog input
            audio += np.random.default_rng(1).uniform(-1, 1, audio.size) * 10 ** (self.noise_dbfs / 20)
        path = self.directory / f"take{len(self.commands)}.wav"
        sf.write(str(path), (np.column_stack([audio * self.left_gain, audio]) * self.gain).astype(np.float32), fs, subtype="FLOAT")
        return str(path)

    def call(self, cmd, params=None, timeout=30.0, on_user_wait=None):
        params = params or {}
        self.commands.append((cmd, params))
        setup_answer = self.reaper.answer(cmd, params)
        if setup_answer is not None:
            return setup_answer
        if cmd == "send_midi":
            for m in params["messages"]:
                self._receive(m)
            return {"device": params["device"], "sent": len(params["messages"]), "audio_running": self.audio_running}
        if cmd == "recent_midi_input":
            newer = [e for e in self.history if e["seq"] > params.get("after", 0)][-params.get("limit", 64):]
            return {"latest": self.history[-1]["seq"], "events": newer, "audio_running": self.audio_running}
        if cmd == "hardware_take_start":
            start = 100.0 if params.get("scratch") else params["start_seconds"]
            end = start + params["seconds"] if params.get("scratch") else params["end_seconds"]
            self.take = {"file": self._record(params), "scratch": bool(params.get("scratch")), "seconds": end - start}
            return {"recording": True, "start_seconds": start, "end_seconds": end}
        if cmd == "recording_status":
            return {"recording": False, "playing": False}
        if cmd == "hardware_take_finish":
            take, self.take = self.take, None
            return {"items": [{"id": "{REC}", "file": take["file"], "file_starts_at_seconds": 0.0,
                               "start": {"bar": 3, "beat": 1},
                               "length_seconds": self.item_seconds or take["seconds"]}], "scratch": take["scratch"]}
        if cmd == "create_hardware_tracks":
            return {"midi_track": {"number": 5, "name": params["name"] + " (MIDI)"},
                    "audio_track": {"number": 6, "name": params["name"]}, "monitoring": params["monitor"]}
        if cmd == "hardware_patch_item":
            self.patch_items.append(params)
            return {"item_id": "{S1}", "loads_before_the_part": params["start_bar"] > 1}
        if cmd == "hardware_tracks":
            return {"hardware_tracks": [{"device": self.part_device, "midi_track": {"number": 5, "name": "MK Lead (MIDI)"},
                                         "audio_track": {"number": 6, "name": "MK Lead"}, "parts": self.parts,
                                         "printed": self.printed,
                                         "sounds": [self._sound_item(i) for i in self.patch_items]}]}
        if cmd == "get_tempo_map":
            return {"start_tempo_bpm": self.tempo, "start_time_signature": "4/4", "changes": self.tempo_changes}
        raise AssertionError(f"unexpected bridge command {cmd}")


@pytest.fixture
def korg(tmp_path, monkeypatch):
    bridge = FakeKorg(tmp_path)
    monkeypatch.setattr(server, "bridge", bridge)
    monkeypatch.setattr(hw, "bridge", bridge)
    monkeypatch.setattr(hw, "_sleep", lambda s: None)
    monkeypatch.setattr(server, "_render_cache", server.RenderCache())
    monkeypatch.setattr(server, "sound_library", SoundLibrary(tmp_path / "sounds"))
    monkeypatch.setattr(hst, "_asked", set())
    asked = []
    monkeypatch.setattr(hst, "confirm_with_user", lambda action, irreversible=False: asked.append(action))
    monkeypatch.setenv(server.CONFIRM_FILE_ENV, "in the panel")     # where creaper can ask
    monkeypatch.delenv(server.ALLOW_UNCONFIRMED_ENV, raising=False)
    bridge.asked = asked
    hw.save_hardware("microKORG", midi_output="UM-ONE", midi_input="UM-ONE", channel=1, audio_input=1, stereo=True,
                     model="Korg microKORG")
    return bridge


# ------------------------------------------------------------ the profile

def test_seven_bit_packing_round_trips_and_has_the_documented_sizes():
    data = bytes((i * 37) % 256 for i in range(254))
    packed = mk.pack(data)
    assert len(packed) == 291 and max(packed) < 0x80 and mk.unpack(packed) == data
    assert len(mk.pack(bytes(200))) == 229
    # the first MIDI byte carries the top bits, bit 0 for the first data byte
    assert mk.pack(bytes([0x80, 0, 0, 0, 0, 0, 0x81]))[:2] == bytes([0b1000001, 0x00])


def test_program_numbers_follow_the_display():
    assert mk.program_number("A.11") == 0 and mk.program_number("b.14") == 67 and mk.program_number("b88") == 127
    assert mk.program_number(1) == 0 and mk.program_name(27) == "A.44"
    with pytest.raises(ValueError, match="A.11"):
        mk.program_number("C.19")


def test_parameters_land_in_the_bytes_the_implementation_chart_gives():
    data = bytearray(mk.apply(mk.init_program(), {
        "voice_mode": "layer", "cutoff": 99, "filter_eg_int": -20, "osc1_wave": "dwgs", "dwgs_wave": 64,
        "osc2_mod": "sync", "osc2_wave": "triangle", "assign_mode": "unison", "patch2_source": "lfo1",
        "patch2_dest": "cutoff", "patch2_int": 63, "arp_on": "on", "arp_type": "random", "arp_octaves": 4,
        "arp_tempo": 300, "arp_pattern": "x-x-x-xx", "arp_steps": 6, "delay_sync": "on", "delay_division": "1/4",
        "kbd_octave": -2, "distortion": "on", "amp_gate": "on", "lfo2_wave": "s/h", "lfo2_tempo_sync": "on"}))
    t = mk.TIMBRE1
    assert data[16] >> 4 & 3 == 2 and data[t + 20] == 99 and data[t + 22] == 44 and data[t + 7] == 5 and data[t + 10] == 63
    assert data[t + 12] == 0x22 and data[t + 1] >> 6 == 2 and data[t + 46] == 0x42 and data[t + 47] == 127
    assert data[32] & 0x80 and data[33] == 0x34 and (data[30], data[31]) == (1, 44)
    assert data[15] == 0b00101010 and data[14] == 5 and data[19] == 0x88 and data[37] == 0xFE
    assert data[t + 27] == 0x41 and data[t + 41] & 3 == 3 and data[t + 43] & 0x80
    assert data[mk.TIMBRE2 + 20] == 127                       # timbre 2 untouched unless asked for
    back = mk.decode_program(bytes(data))
    assert back["voice_mode"] == "layer" and back["timbre1"]["filter_eg_int"] == -20 and "timbre2" in back
    assert back["common"]["arp_tempo"] == 300 and back["common"]["arp_pattern"] == "x-x-x-xx"


def test_values_are_refused_by_name_with_what_is_allowed():
    init = mk.init_program()
    with pytest.raises(ValueError, match="cutoff runs 0 to 127"):
        mk.apply(init, {"cutoff": 200})
    with pytest.raises(ValueError, match="24lpf, 12lpf"):
        mk.apply(init, {"filter_type": "notch"})
    with pytest.raises(ValueError, match="formant_shift.*vocoder"):
        mk.apply(init, {"formant_shift": "+1"})
    with pytest.raises(ValueError, match="layer"):
        mk.apply(init, {"cutoff": 5}, timbre=2)


def test_vocoder_programs_use_their_own_layout():
    data = mk.apply(mk.init_program(), {"voice_mode": "vocoder", "formant_shift": "-2", "band3_level": 40, "band8_pan": -63})
    block = data[mk.TIMBRE1:]
    assert block[21] == 4 and block[46 + 4] == block[46 + 5] == 40 and block[62 + 14] == block[62 + 15] == 1
    voc = mk.decode_program(data)["vocoder"]
    assert voc["formant_shift"] == "-2" and voc["band3_level"] == 40 and voc["osc1_level"] == 127
    synth = mk.decode_program(mk.apply(data, {"voice_mode": "single"}))
    assert synth["timbre1"] == mk.INIT_TIMBRE                 # the shared bytes start afresh


def test_init_keeps_the_bytes_the_chart_does_not_describe():
    template = bytearray(mk.init_program())
    template[18] = 0x3C
    template[mk.TIMBRE1 + 60] = 0x40
    made = mk.init_program(bytes(template))
    assert made[18] == 0x3C and made[mk.TIMBRE1 + 60] == 0x40


def test_every_recipe_builds_and_says_what_it_is_based_on():
    for name, recipe in mk.RECIPES.items():
        prog = mk.decode_program(mk.build({**recipe, "name": name}))
        assert prog["voice_mode"] == recipe["params"].get("voice_mode", "single")
        assert recipe["play"]
        if recipe["kind"] == "artist":
            assert recipe["style_of"] and recipe["evidence"]
    kinds = {r["kind"] for r in mk.RECIPES.values()}
    assert kinds == {"artist", "sfx", "song"}
    # A song needs a sound for every job, each saying where it works and how many notes it plays.
    roles = {r["role"] for r in mk.RECIPES.values() if r.get("role")}
    assert {"bass", "lead", "pad", "chords", "arp", "solo"} <= roles
    for recipe in mk.RECIPES.values():
        if recipe.get("role"):
            assert len(recipe["range"]) == 2 and recipe["voices"] in (1, 2, 4)   # 2: a layer halves the voices


def test_a_sound_says_when_it_does_not_fit_the_part():
    bass = mk.RECIPES["eighth-note saw bass"]                       # C1-C4, one voice
    line = [{"pitch": 28 + (i % 3), "start": i * 0.5, "length": 0.42} for i in range(60)]
    assert mk.part_fit(bass, line) == []
    low = mk.part_fit(bass, [{**n, "pitch": 21} for n in line[:20]] + line[20:])
    assert len(low) == 1 and "20 of 60 notes are below" in low[0] and "A0" in low[0]
    assert mk.part_fit(bass, line + [{"pitch": 21, "start": 40, "length": 0.4}]) == []     # one stray note
    doubled = mk.part_fit(bass, line + [{**n, "pitch": n["pitch"] + 12} for n in line])
    assert "2 notes at once and this sound plays one" in doubled[0]
    strings = mk.RECIPES["dual saw strings"]                        # four voices
    chord = lambda size: [{"pitch": 60 + 3 * i, "start": 0, "length": 4} for i in range(size)]  # noqa: E731
    assert mk.part_fit(strings, chord(4)) == []
    assert "5 notes at once and this sound has 4 voices" in mk.part_fit(strings, chord(5))[0]
    assert mk.part_fit(mk.RECIPES["laser zap"], chord(5)) == []     # an effect: no register, no count
    assert mk.find_recipe("somebody told me")[0] == "phaser glide lead"
    for needed in ("laser zap", "power-up", "alarm", "explosion", "ui blip", "sci-fi drone", "robot voice"):
        assert needed in mk.RECIPES


def test_global_dump_gives_the_knob_map_and_filters():
    setup = mk.decode_global(global_data())
    assert setup["midi_channel"] == 1 and setup["sysex_enabled"] and setup["memory_protect"]
    assert setup["knob_ccs"]["cutoff"] == 74 and setup["knob_ccs"]["resonance"] == 71 and "amp_gate" not in setup["knob_ccs"]
    assert setup["timbre_select_cc"] == 95 and setup["program_change_map_is_default"]


def test_live_messages_use_the_synths_own_cc_numbers_and_nrpns():
    ccs = mk.decode_global(global_data())["knob_ccs"]
    assert mk.live_messages("cutoff", 60, 1, ccs) == ["B0 4A 3C"]
    assert mk.live_messages("filter_eg_int", -63, 3, ccs) == ["B2 4F 01"]
    assert mk.live_messages("osc1_wave", "sine", 1, ccs) == ["B0 4D 38"]        # inside 30-3F
    assert mk.live_messages("osc2_wave", "triangle", 1, ccs) == ["B0 4E 6A"]
    assert mk.live_messages("arp_on", "on", 1, ccs) == ["B0 63 00", "B0 62 02", "B0 06 7F"]
    assert mk.live_messages("patch1_dest", "cutoff", 1, ccs) == ["B0 63 04", "B0 62 08", "B0 06 48"]
    assert mk.live_messages("osc2_semitone", 7, 1, ccs) is None and mk.live_messages("tune", 3, 1, ccs) is None
    assert mk.live_messages("cutoff", 60, 1, {}) is None                        # knob set to OFF on the synth


# ------------------------------------------------------- reading and loading

def test_reading_the_patch_changes_nothing_on_the_synth(korg):
    patch = hst.read_hardware_patch("microKORG")
    assert patch["name"] == "user" and patch["timbre1"]["cutoff"] == 127
    assert korg.sent == ["F0 42 30 58 10 F7"] and korg.asked == []


def test_setting_parameters_loads_the_edit_buffer_and_keeps_the_old_sound(korg):
    before = korg.buffer
    result = hst.set_hardware_params("microKORG", {"cutoff": 50, "delay_depth": 30})
    assert result["set"] == {"cutoff": 50, "delay_depth": 30} and result["was"] == {"cutoff": 127, "delay_depth": 0}
    assert mk.decode_program(korg.buffer)["timbre1"]["cutoff"] == 50
    assert len(korg.asked) == 1 and "edit buffer" in korg.asked[0]
    hst.set_hardware_params("microKORG", {"resonance": 80})
    assert len(korg.asked) == 1                                # asked once a session
    listed = hst.read_hardware_patch("microKORG", backups=True)["backups"]
    assert len(listed) == 2
    hst.load_hardware_sound("microKORG", backup=2)
    assert korg.buffer == before
    assert not any(mk.parse_message(m) and mk.parse_message(m)[0] == mk.F_WRITE_REQUEST for m in korg.sent)


def test_start_from_init_gives_a_known_sound(korg):
    korg.buffer = mk.apply(korg.buffer, {"resonance": 99, "delay_depth": 90})
    hst.set_hardware_params("microKORG", {"osc1_wave": "sine"}, start_from="init")
    prog = mk.decode_program(korg.buffer)
    assert prog["timbre1"]["osc1_wave"] == "sine" and prog["timbre1"]["resonance"] == 0 and prog["common"]["delay_depth"] == 0


def test_live_changes_go_out_as_control_changes_without_a_patch_load(korg):
    result = hst.set_hardware_params("microKORG", {"cutoff": 64, "arp_on": "on"}, live=True)
    assert result["sent_live"] == ["arp_on", "cutoff"]
    assert korg.sent[-5:] == ["B0 5F 00", "B0 4A 40", "B0 63 00", "B0 62 02", "B0 06 7F"]
    assert hw._devices()["microKORG"]["midi_setup"]["knob_ccs"]["cutoff"] == 74      # remembered
    with pytest.raises(ValueError, match="osc2_semitone"):
        hst.set_hardware_params("microKORG", {"osc2_semitone": 12}, live=True)


def test_a_silent_synth_gets_setup_help_and_a_closed_audio_device_is_named(korg):
    korg.answers = False
    with pytest.raises(ValueError, match="SystemEx"):
        hst.read_hardware_patch("microKORG")
    korg.audio_running = False
    with pytest.raises(ValueError, match="audio device is closed"):
        hst.read_hardware_patch("microKORG")


def test_nothing_is_loaded_when_the_current_sound_cannot_be_backed_up(korg):
    korg.answers = False
    with pytest.raises(ValueError):
        hst.load_hardware_sound("microKORG", recipe="laser zap")
    assert all(mk.parse_message(m)[0] == mk.F_CURRENT_REQUEST for m in korg.sent)


def test_devices_without_a_profile_say_so(korg):
    hw.save_hardware("Wasp", midi_output="UM-ONE", model="EDP Wasp")
    with pytest.raises(ValueError, match="no sound-design profile"):
        hst.read_hardware_patch("Wasp")


def test_recipes_load_with_how_to_play_them_and_where_they_come_from(korg):
    result = hst.load_hardware_sound("microKORG", recipe="phaser glide lead")
    assert "Somebody Told Me" in result["style_of"] and "b.14" in result["factory_program"] and result["how_to_play"]
    assert mk.decode_program(korg.buffer)["common"]["mod_type"] == "phaser"
    listed = hst.hardware_profile("microKORG", show="recipes", kind="sfx")
    assert {r["kind"] for r in listed["recipes"]} == {"sfx"} and "b.14" in listed["factory_programs"]
    assert "cutoff" in [p["name"] for p in hst.hardware_profile("microKORG")["timbre"]]


def test_selecting_a_stored_program_is_a_program_change_with_a_backup(korg):
    before = korg.buffer
    result = hst.load_hardware_sound("microKORG", program="b.14")
    assert "C0 43" in korg.sent and korg.buffer == korg.programs[67] and "Phaser Lead" in result["factory_preset"]
    hst.load_hardware_sound("microKORG", backup=1)
    assert korg.buffer == before


def test_sounds_go_to_the_library_and_come_back(korg):
    hst.set_hardware_params("microKORG", {"cutoff": 33})
    saved = hst.save_hardware_sound("microKORG", "Plasma Rifle", tags=["sfx", "laser"])
    assert saved["saved"] == "Plasma Rifle"
    assert [s["name"] for s in server.list_sounds(kind="hardware")["sounds"]] == ["Plasma Rifle"]
    assert server.list_sounds(kind="instrument")["sounds"] == []           # never offered to a plugin track
    with pytest.raises(ValueError, match="load_hardware_sound"):
        server.load_sound("Plasma Rifle", track=1)
    hst.set_hardware_params("microKORG", {"cutoff": 120})
    hst.load_hardware_sound("microKORG", sound="plasma rifle")
    assert mk.decode_program(korg.buffer)["timbre1"]["cutoff"] == 33


def test_a_sound_is_written_into_the_song_before_its_part(korg):
    result = hst.load_hardware_sound("microKORG", recipe="laser zap", track="MK Lead", bar=3)
    item = korg.patch_items[0]
    assert item["track"] == "MK Lead" and item["start_bar"] == 3 and item["name"] == "laser zap"
    assert mk.unpack(mk.parse_message(item["sysex"])[1]) == korg.buffer and "warning" not in result
    assert "warning" in hst.load_hardware_sound("microKORG", recipe="laser zap", track="MK Lead", bar=1)
    with pytest.raises(ValueError, match="both track and bar"):
        hst.load_hardware_sound("microKORG", recipe="laser zap", track="MK Lead")


def test_writing_a_program_asks_every_time_names_the_slot_and_keeps_what_was_there(korg):
    korg.globals = global_data(protect=False)
    hst.set_hardware_params("microKORG", {"cutoff": 77})
    old = korg.programs[9]
    for _ in range(2):
        result = hst.write_hardware_program("microKORG", "A.22")
    assert result["written"] == "A.22" and mk.decode_program(korg.programs[9])["timbre1"]["cutoff"] == 77
    overwrite = [a for a in korg.asked if "OVERWRITE" in a]
    assert len(overwrite) == 2 and "A.22" in overwrite[0] and "kept a copy" in overwrite[0]
    kept = hst.read_hardware_patch("microKORG", backups=True)["backups"]
    assert any("A.22 before it was overwritten" in b["kept"] for b in kept)
    assert old.hex() in [b["patch"] for b in hst._backups(hst._link("microKORG"))]


def test_memory_protect_stops_a_write_before_anything_is_sent(korg):
    with pytest.raises(ValueError, match="WRITE PROTECT"):
        hst.write_hardware_program("microKORG", "A.11")
    assert not any("OVERWRITE" in a for a in korg.asked)
    assert all(mk.parse_message(m)[0] == mk.F_GLOBAL_REQUEST for m in korg.sent)


def test_a_declined_write_leaves_the_program_alone(korg, monkeypatch):
    korg.globals = global_data(protect=False)
    stored = korg.programs[0]

    def decline(action, irreversible=False):
        if "OVERWRITE" in action:
            raise ValueError("The user declined")
    monkeypatch.setattr(hst, "confirm_with_user", decline)
    with pytest.raises(ValueError, match="declined"):
        hst.write_hardware_program("microKORG", "A.11")
    assert korg.programs[0] == stored


# ------------------------------------------------------------- recording

def test_audition_records_on_scratch_tracks_and_measures_each_note(korg):
    result = hst.audition_hardware("microKORG", notes=[hst.PhraseNote(pitch=57, at=0, length=0.8),
                                                       hst.PhraseNote(pitch=69, at=1.2, length=0.8)])
    start = next(p for c, p in korg.commands if c == "hardware_take_start")
    assert start["scratch"] and start["midi_device"] == 1 and start["audio_input"] == 1 and start["stereo"]
    assert [n["note"] for n in result["notes"]] == ["A3", "A4"]
    assert abs(result["notes"][1]["pitch_hz"] - 440) < 3 and abs(result["notes"][0]["cents_off"]) < 10
    assert result["notes"][0]["attack_ms"] < 30 and "legend" in result and "file" not in result
    assert not list(korg.directory.glob("take*.wav"))            # the scratch recording is cleaned up
    assert len([a for a in korg.asked if "test clips" in a]) == 1
    hst.audition_hardware("microKORG", keep_file=True)
    assert len([a for a in korg.asked if "test clips" in a]) == 1 and len(list(korg.directory.glob("take*.wav"))) == 1


def test_audition_says_when_nothing_came_in(korg):
    korg.silent = True
    result = hst.audition_hardware("microKORG")
    assert result["silent"] and "input 1" in result["problem"]


def test_latency_is_measured_saved_and_the_users_sound_put_back(korg):
    korg.tone_delay = 0.012
    mine = korg.buffer
    result = hst.calibrate_hardware_latency("microKORG")
    assert abs(result["latency_ms"] - 12) < 1.5 and result["clicks_measured"] == 5
    assert hw._devices()["microKORG"]["latency_ms"] == result["latency_ms"]
    assert korg.buffer == mine
    loads = [m for m in korg.sent if mk.parse_message(m) and mk.parse_message(m)[0] == mk.F_CURRENT_DUMP]
    assert len(loads) == 2                                       # the click, then the user's sound again


def test_hardware_tracks_are_made_from_the_hardware_map(korg):
    made = hst.create_hardware_track("microKORG", "MK Lead")
    params = next(p for c, p in korg.commands if c == "create_hardware_tracks")
    assert params["midi_device"] == 1 and params["channel"] == 1 and params["audio_input"] == 1 and params["stereo"]
    assert made["audio_track"]["name"] == "MK Lead" and "calibrate_hardware_latency" in made["note"]


def test_printing_sends_the_parts_sound_first_and_compensates_latency(korg):
    hst.load_hardware_sound("microKORG", recipe="glide distortion lead", track="MK Lead", bar=3)
    wanted = korg.buffer
    korg.buffer = mk.init_program(name="other")                  # the user turned to another sound since
    with jsonstore_latency(8.0):
        result = hst.print_hardware("MK Lead", tail_seconds=2)
    assert korg.buffer == wanted and result["sound"] == "glide distortion lead"
    start = next(p for c, p in korg.commands if c == "hardware_take_start")
    finish = next(p for c, p in korg.commands if c == "hardware_take_finish")
    assert (start["start_seconds"], start["end_seconds"]) == (4.0, 10.0) and start["mute_items"] == []
    assert finish["latency_seconds"] == 0.008 and finish["replace"] and finish["mute_midi"]
    assert result["latency_compensated_ms"] == 8.0 and any("real time" in a for a in korg.asked)
    order = [c for c, _ in korg.commands if c in ("send_midi", "hardware_take_start")]
    assert order.index("hardware_take_start") > max(i for i, c in enumerate(order) if c == "send_midi") - 0


def test_printing_without_a_sound_or_notes_says_so(korg):
    result = hst.print_hardware("MK Lead")
    assert "No sound is written" in result["warning"] and "calibrate_hardware_latency" in result["note"]
    korg.parts = []
    with pytest.raises(ValueError, match="no MIDI items"):
        hst.print_hardware("MK Lead")


class jsonstore_latency:
    """The hardware map with a measured latency for the microKORG, while the block runs."""

    def __init__(self, ms):
        self.ms = ms

    def __enter__(self):
        from creaper import jsonstore
        with jsonstore.updating(hw._store_path(), dict, indent=2) as data:
            data["devices"]["microKORG"]["latency_ms"] = self.ms

    def __exit__(self, *exc):
        return False


# ------------------------------------------- REAPER's setup, checked before recording

def takes(korg):
    return [c for c, _ in korg.commands if c == "hardware_take_start"]


def test_nothing_is_recorded_while_reaper_listens_to_another_device(korg):
    hw.save_hardware("microKORG", midi_output="UM-ONE", midi_input="UM-ONE", audio_input=1, model="Korg microKORG",
                     interface="SSL 2+")
    korg.reaper.mode, korg.reaper.input = "WASAPI", MIC
    for record in (lambda: hst.audition_hardware("microKORG"), lambda: hst.calibrate_hardware_latency("microKORG"),
                   lambda: hst.create_hardware_track("microKORG", "MK Lead"), lambda: hst.print_hardware("MK Lead")):
        with pytest.raises(ValueError, match="recording from 'Microphone Array.*not the SSL 2\\+.*action='fix'"):
            record()
    assert takes(korg) == [] and korg.sent == [] and korg.asked == []   # not a note, not a question
    korg.reaper.input = SSL_WASAPI
    assert "problem" not in hst.audition_hardware("microKORG")


def test_a_disabled_midi_port_stops_a_hardware_tool_by_name(korg):
    korg.reaper.midi_outputs[1]["enabled"] = False
    with pytest.raises(ValueError, match="'UM-ONE' is plugged in but not enabled"):
        hst.audition_hardware("microKORG")
    assert takes(korg) == []


def test_digital_silence_is_told_from_a_quiet_synth(korg):
    korg.silent = True
    dead = hst.audition_hardware("microKORG")["problem"]
    assert "digital silence" in dead and "Privacy" in dead and "Not the synth's volume" in dead
    korg.noise_dbfs = -95.0                                             # an open analog input, nothing playing
    live = hst.audition_hardware("microKORG")["problem"]
    assert "answers over MIDI" in live and "digital silence" not in live
    assert live.index("volume knob") < live.index("audio cables") < live.index("input gain")
    korg.answers = False
    mute = hst.audition_hardware("microKORG")["problem"]
    assert "doesn't answer over MIDI" in mute and "switched on" in mute and "volume knob" not in mute


def test_a_silent_take_names_the_device_before_any_cable(korg):
    korg.silent = True
    korg.reaper.mode, korg.reaper.input = "WASAPI", MIC                 # no interface known for this synth
    result = hst.audition_hardware("microKORG")
    assert "REAPER's setup, not the synth" in result["problem"] and "Microphone Array" in result["problem"]
    assert "cable" not in result["problem"] and "looks like the computer's own microphone" in result["setup_warnings"][0]


def test_a_heard_synth_proves_the_device_and_it_is_kept(korg):
    assert "interface" not in hw._devices()["microKORG"]
    hst.audition_hardware("microKORG")
    kept = hw._devices()["microKORG"]["interface"]
    assert kept["found_by"] == "heard" and kept["audio"]["input"] == "ASIO Test Interface"
    korg.reaper.input = MIC
    with pytest.raises(ValueError, match="not the Test Interface"):
        hst.audition_hardware("microKORG")


def test_latency_belongs_to_the_audio_settings_it_was_measured_on(korg):
    korg.tone_delay = 0.012
    first = hst.calibrate_hardware_latency("microKORG")
    assert first["measured_on"] == "ASIO at 48000 Hz, block 512"
    korg.reaper.block_size = 64
    warned = hst.audition_hardware("microKORG")["setup_warnings"]
    assert "block 512" in warned[0] and "block 64" in warned[0] and "calibrate_hardware_latency" in warned[0]
    korg.tone_delay = 0.004
    hst.calibrate_hardware_latency("microKORG")
    device = hw._devices()["microKORG"]
    assert len(device["latencies"]) == 2 and abs(device["latency_ms"] - 4) < 1.5
    korg.reaper.block_size = 512                                        # back: the first measurement counts again
    result = hst.print_hardware("MK Lead")
    assert abs(result["latency_compensated_ms"] - 12) < 1.5 and "setup_warnings" not in result


def test_recording_turns_the_save_window_off_where_reaper_allows(korg):
    korg.reaper.settings["promptendrec"] = True
    result = hst.audition_hardware("microKORG")
    assert not korg.reaper.settings["promptendrec"] and korg.reaper.session == {"promptendrec": 1}
    assert "setup_warnings" not in result
    hw.setup_hardware(action="finish")
    korg.reaper.can_change = False
    told = hst.audition_hardware("microKORG")["setup_warnings"]
    assert korg.reaper.settings["promptendrec"] and "Prompt to save/delete/rename new files on stop" in told[0]


def test_the_interface_is_worked_out_for_a_device_saved_before_creaper_did_that(korg, monkeypatch):
    monkeypatch.setattr(setup, "windows_audio", lambda: WINDOWS)
    korg.reaper.midi_outputs[1]["name"] = korg.reaper.midi_inputs[0]["name"] = "SSL 2+ MIDI"
    from creaper import jsonstore
    with jsonstore.updating(hw._store_path(), dict, indent=2) as data:  # as the hardware.json of 2026-11-11 has it
        data["devices"]["microKORG"].update(midi_output="SSL 2+ MIDI", midi_input="SSL 2+ MIDI")
    korg.reaper.mode, korg.reaper.input = "WASAPI", MIC
    with pytest.raises(ValueError, match="ASIO driver: SSL ASIO Driver 1"):
        hst.audition_hardware("microKORG")
    assert hw._devices()["microKORG"]["interface"]["name"] == "SSL 2+"


# --------------------------------------- the security review of 2026-11-11

WRITE_REQUEST = mk.message(1, mk.F_WRITE_REQUEST, [0, 5]).replace(" ", "")   # "store the edit buffer in A.16"


def _dumps_sent(korg):
    return [mk.unpack(mk.parse_message(m)[1]) for m in korg.sent
            if mk.parse_message(m) and mk.parse_message(m)[0] == mk.F_CURRENT_DUMP]


def test_a_program_write_is_refused_outside_the_panel_before_the_synth_is_touched(korg, monkeypatch):
    korg.globals = global_data(protect=False)
    monkeypatch.delenv(server.CONFIRM_FILE_ENV)                  # Claude Desktop, Claude Code: nobody to ask
    stored = dict(korg.programs)
    with pytest.raises(ValueError, match="chat panel.*CREAPER_ALLOW_UNCONFIRMED=1"):
        hst.write_hardware_program("microKORG", "A.22")
    assert korg.sent == [] and korg.programs == stored and korg.asked == []
    monkeypatch.setenv(server.ALLOW_UNCONFIRMED_ENV, "1")        # the user's own opt-in
    assert hst.write_hardware_program("microKORG", "A.22")["written"] == "A.22"


def test_the_overwrite_question_is_the_irreversible_kind(korg, monkeypatch):
    korg.globals = global_data(protect=False)
    kinds = {}
    monkeypatch.setattr(hst, "confirm_with_user", lambda action, irreversible=False: kinds.update({action: irreversible}))
    hst.write_hardware_program("microKORG", "A.22")
    assert [k for a, k in kinds.items() if "OVERWRITE" in a] == [True]


def test_a_declined_write_does_not_allow_later_loads(korg, monkeypatch):
    korg.globals = global_data(protect=False)

    def decline(action, irreversible=False):
        korg.asked.append(action)
        if "OVERWRITE" in action:
            raise ValueError("The user declined")
    monkeypatch.setattr(hst, "confirm_with_user", decline)
    with pytest.raises(ValueError, match="declined"):
        hst.write_hardware_program("microKORG", "A.11")
    assert "microKORG" not in hst._asked
    assert not [a for a in korg.asked if "load sounds" in a]     # putting the user's own sound back isn't asked
    hst.load_hardware_sound("microKORG", recipe="glide distortion lead")
    assert len([a for a in korg.asked if "load sounds" in a]) == 1


def test_printing_refuses_sysex_creaper_did_not_write(korg):
    korg.parts[0].update(sysex_count=1, sysex_events=[WRITE_REQUEST], name="imported.mid")
    with pytest.raises(ValueError, match=r"'imported.mid' at bar 3.*1 SysEx message\(s\) that creaper didn't write"):
        hst.print_hardware("MK Lead")
    assert not any(c == "hardware_take_start" for c, _ in korg.commands)
    assert korg.sent == [] and korg.asked == []                  # refused before the user is asked or anything is sent


@pytest.mark.parametrize("bad", ["a write request", "a short dump", "another maker's message", "an extra message",
                                 "more than listed", "a tampered copy"])
def test_printing_refuses_a_sound_item_that_is_not_one_whole_patch(korg, bad):
    hst.load_hardware_sound("microKORG", recipe="glide distortion lead", track="MK Lead", bar=3)
    good = korg.patch_items[0]["sysex"].replace(" ", "")
    short = mk.message(1, mk.F_CURRENT_DUMP, mk.pack(bytes([1, 2]))).replace(" ", "")
    if bad == "a write request":
        korg.sound_events = [WRITE_REQUEST]
    elif bad == "a short dump":
        korg.sound_events = [short]
    elif bad == "another maker's message":
        korg.sound_events = ["F07E7F0601F7"]
    elif bad == "an extra message":
        korg.sound_events = [good, WRITE_REQUEST]
    elif bad == "more than listed":
        korg.sound_events, korg.sound_sysex_count = [good] * 8, 20
    else:
        korg.patch_items[0]["sysex"], korg.sound_events = WRITE_REQUEST, [good]    # the copy creaper would load from
    sent, asked = len(korg.sent), len(korg.asked)
    with pytest.raises(ValueError, match="not recorded: the sound item 'glide distortion lead' at bar 2"):
        hst.print_hardware("MK Lead")
    assert not any(c == "hardware_take_start" for c, _ in korg.commands)
    assert len(korg.sent) == sent and len(korg.asked) == asked


def test_printing_needs_a_bridge_that_shows_the_sysex(korg):
    del korg.parts[0]["sysex_count"]                             # a bridge from before this check
    with pytest.raises(ValueError, match="install-bridge"):
        hst.print_hardware("MK Lead")
    assert not any(c == "hardware_take_start" for c, _ in korg.commands)


def test_a_patch_of_the_wrong_length_is_never_sent(korg):
    from creaper import jsonstore

    server.sound_library.save_hardware("Cut Short", mk.MODEL, "0102", {})      # a library file someone edited
    with pytest.raises(ValueError, match="isn't a whole Korg microKORG patch"):
        hst.load_hardware_sound("microKORG", sound="Cut Short")
    hst.set_hardware_params("microKORG", {"cutoff": 50})                        # keeps a backup
    with jsonstore.updating(hst._backups_path(), dict, indent=None) as store:
        store["devices"]["microKORG"][0]["patch"] = "00" * 10
    with pytest.raises(ValueError, match="isn't a whole Korg microKORG patch"):
        hst.load_hardware_sound("microKORG", backup=1)
    assert all(len(d) == mk.PROGRAM_BYTES for d in _dumps_sent(korg)) and len(_dumps_sent(korg)) == 1


def test_a_channel_that_is_not_one_stops_every_hardware_sound_tool(korg):
    from creaper import jsonstore

    with jsonstore.updating(hw._store_path(), dict, indent=2) as data:
        data["devices"]["microKORG"]["channel"] = 97             # 0x90 | 96 is 0xF0, the start of a SysEx
    for tool in (lambda: hst.read_hardware_patch("microKORG"), lambda: hst.audition_hardware("microKORG"),
                 lambda: hst.write_hardware_program("microKORG", "A.11")):
        with pytest.raises(ValueError, match="isn't a channel"):
            tool()
    assert korg.sent == []


# ------------------------------------------------- input level, with the user
# Live, 2026-11-13: a song's parts were printed with input 1 thirty dB under input 2 (a plug
# not seated) and nothing said so; the user asked for creaper to help set the level first.

def test_the_level_check_plays_the_loudest_sound_and_puts_the_users_back(korg):
    mine = korg.buffer
    assert "Input 1 is hot" in hw.setup_hardware("microKORG", action="level")["turn"][0]   # -6: no room for a louder sound
    korg.gain = 0.3
    result = hw.setup_hardware("microKORG", action="level")
    assert result["level_ok"] and result["inputs"] == {"input 1": "-16.5 dBFS peak", "input 2": "-16.5 dBFS peak"}
    assert "turn" not in result and "loud plain sound" in result["measured_with"]
    assert korg.buffer == mine                                              # the user's sound is back
    loaded = [mk.unpack(mk.parse_message(m)[1]) for m in korg.sent if (mk.parse_message(m) or (0,))[0] == mk.F_CURRENT_DUMP]
    assert mk.decode_program(loaded[0])["timbre1"]["assign_mode"] == "unison"   # the test sound went first
    assert any("loud two-second test note" in a for a in korg.asked)
    kept = hw._devices()["microKORG"]["input_level"]
    assert kept["ok"] and kept["peaks_dbfs"] == [-16.5, -16.5]


def test_a_dead_input_is_named_with_its_causes_and_prints_say_so_too(korg):
    korg.left_gain = 0.03
    result = hw.setup_hardware("microKORG", action="level")
    assert not result["level_ok"] and "Input 1 gets next to nothing" in result["turn"][0]
    assert "one knob at a time" in result["next"] and not hw._devices()["microKORG"]["input_level"]["ok"]
    printed = hst.print_hardware("MK Lead")
    assert "one-sided" in printed["problem"] and printed["peaks_dbfs"][0] < printed["peaks_dbfs"][1] - 25
    heard = hst.audition_hardware("microKORG")
    assert "one-sided" in heard["problem"]


def test_a_part_made_before_the_level_was_set_says_so(korg):
    made = hst.create_hardware_track("microKORG", "MK Lead")
    assert "action='level'" in made["input_level"] and "hasn't been set" in made["input_level"]
    korg.gain = 0.3
    hw.setup_hardware("microKORG", action="level")
    assert "input_level" not in hst.create_hardware_track("microKORG", "MK Bass")
    assert "input_level" not in hst.print_hardware("MK Lead")
    with pytest.raises(ValueError, match="level needs the device's name"):
        hw.setup_hardware(action="level")


def test_a_print_whose_item_is_a_sliver_of_the_recording_says_so(korg):
    """Motel Neon MK, 2026-11-13: three parts printed with healthy peaks (read from the
    files) while their items were 10-30 ms long, and the mix had no bass or pad."""
    assert "problem" not in hst.print_hardware("MK Lead")
    korg.item_seconds = 0.01
    printed = hst.print_hardware("MK Lead")
    assert "shows only 0.0" in printed["problem"] and "missing from the song" in printed["problem"]


# ------------------------------------------------------------ the design guide

def test_the_guide_lists_what_it_knows_and_gives_a_blueprint():
    listed = hst.sound_design_guide()
    assert "string pad" in listed["sounds"]["pad"] and "detune" in listed["techniques"] and len(listed["method"]) >= 6
    strings = hst.sound_design_guide("strings")
    assert strings["sound"] == "string pad" and strings["blueprint"]["osc2"]["cents"] == 8 and "on_this_synth" not in strings
    assert strings["check"] and strings["if"]
    assert "cents" in hst.sound_design_guide("detune")["how"]
    with pytest.raises(ValueError, match="no blueprint or technique named 'a kazoo'.*string pad"):
        hst.sound_design_guide("a kazoo")
    pads = hst.sound_design_guide("pads")                       # a family by name lists it
    assert pads["family"] == "pad" and "string pad" in pads["sounds"] and "sub bass" not in pads["sounds"]
    assert hst.sound_design_guide("tremolo")["technique"] == "vibrato and tremolo"
    with pytest.raises(ValueError, match="no blueprint or technique named 'envelope'"):   # two techniques: neither
        hst.sound_design_guide("envelope")


def test_a_blueprint_of_ones_own_becomes_the_synths_values(korg):
    """The pad that was heard as out of tune came from a 0-127 value worked out by eye."""
    mine = {"voices": "mono", "glide_ms": 90, "osc2": {"wave": "saw", "cents": 9}, "amp_env": {"attack_ms": 158}}
    on = hst.sound_design_guide(synth="microKORG", blueprint=mine)["on_this_synth"]
    assert on["params"]["osc2_tune"] == 6 and on["params"]["eg2_attack"] == 32 and on["params"]["assign_mode"] == "mono"
    with pytest.raises(ValueError, match="not blueprint fields: cutoff, osc2.detune"):
        hst.sound_design_guide(synth="microKORG", blueprint={"osc2": {"detune": 9}, "cutoff": 60})
    with pytest.raises(ValueError, match="blueprint needs synth"):
        hst.sound_design_guide(blueprint=mine)


def test_the_guide_gives_a_synths_own_values_and_they_load(korg):
    guide = hst.sound_design_guide("acid bass", synth="microKORG")
    on = guide["on_this_synth"]
    assert on["device"] == "microKORG" and on["params"]["assign_mode"] == "mono" and on["params"]["resonance"] == 89
    assert "start_from='init'" in on["how"] and "osc2_tune (cents)" in on["calibration"]
    hst.set_hardware_params("microKORG", on["params"], start_from="init")
    now = mk.decode_program(korg.buffer)
    assert now["timbre1"]["distortion"] == "on" and now["timbre1"]["trigger_mode"] == "single"
    hw.save_hardware("Box", midi_output="UM-ONE", audio_input=1)                 # a synth creaper has no profile for
    assert "no profile" in hst.sound_design_guide("pluck", synth="Box")["on_this_synth"]


def test_the_programs_designed_on_the_synth_are_recipes_with_their_lessons():
    """2026-11-14: sixteen programs made, measured and used in a song on the user's microKORG."""
    for name in ("glass choir", "rust bell", "tear lead", "clockwork", "sub terra", "monsoon", "tin toy", "wobbler",
                 "iron gong", "brass halo", "acidic", "seance", "shutter", "velvet ep", "morse", "vortex"):
        assert mk.RECIPES[name]["kind"] == "song" and mk.RECIPES[name]["role"]
    layer = mk.decode_program(mk.build(mk.RECIPES["monsoon"]))
    assert layer["voice_mode"] == "layer" and mk.RECIPES["monsoon"]["voices"] == 2
    assert mk.RECIPES["monsoon"]["timbre2"]["filter_kbd_track"] == 0      # the rain doesn't follow the keys
    assert mk.RECIPES["tear lead"]["range"] == ["C3", "A4"]               # a sync lead pierces above that
    high = [{"pitch": 81, "start": i, "length": 0.5} for i in range(8)]
    assert "above where this sound works" in mk.part_fit(mk.RECIPES["tear lead"], high)[0]
    # The four recipes that measured 5-8 dB over the rest are brought down.
    assert mk.RECIPES["ringing filter note"]["params"]["amp_level"] < mk.RECIPES["sci-fi drone"]["params"]["amp_level"] < 127
