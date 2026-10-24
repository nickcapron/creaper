"""auto_mix's plan: roles, levels, EQ, compression, panning, sends, sidechains."""
from creaper import mix_tools
from creaper.mix_tools import plan_mix, role_of


def test_roles_from_names_and_sound():
    assert role_of("909 Kick") == "kick" and role_of("Clap") == "snare" and role_of("Open Hat") == "perc"
    assert role_of("Octave Bass") == "bass" and role_of("Bass Duck") == "bass" and role_of("Robot Vocal") == "vocal"
    assert role_of("Strings Pad") == "pad" and role_of("Clav") == "keys" and role_of("Synth Hook") == "lead"
    assert role_of("909 Drums") == "drums" and role_of("Riser FX") == "fx"
    low = {"bands": {"sub (20-60 Hz)": {"share_pct": 40}, "bass (60-250 Hz)": {"share_pct": 35}}}
    assert role_of("Track 7", low) == "bass"
    assert role_of("Track 8", {"bands": {}, "spectral_centroid_hz": 6000}) == "perc"


def test_roles_for_orchestral_ambient_and_odd_kits():
    """Names from the sessions where auto_mix guessed wrong and buried the featured part."""
    assert role_of("Lead Violin") == "lead" and role_of("Sax Solo") == "lead" and role_of("Main Theme") == "lead"
    assert role_of("Violin II") == "pad" and role_of("Low Cello") == "pad" and role_of("Drone") == "pad"
    assert role_of("Pizz Strings") == "keys" and role_of("French Horn") == "keys" and role_of("Bassoon") == "keys"
    assert role_of("Flute") == "lead" and role_of("Contrabass") == "bass"
    low = {"bands": {"sub (20-60 Hz)": {"share_pct": 40}, "bass (60-250 Hz)": {"share_pct": 35}}}
    assert role_of("City Hum", low) == "fx" and role_of("Passing Cars", low) == "fx"
    assert role_of("Wall Voices", low) != "vocal" and role_of("Robot Voice") == "vocal"
    assert role_of("Guns", low, kit=True) == "drums" and role_of("Guns", low) == "bass"
    assert mix_tools.is_kit(["kick - 909 Kick", "snare - Clap 2", "JS: Volume"])
    assert not mix_tools.is_kit(["VSTi: ReaSamplOmatic5000 (Cockos)"] * 4 + ["VST3: Pro-Q 3 - x (FabFilter)"])


def channel(name, role, level, **kw):
    return {"name": name, "role": role, "level": level, "peak_db": -3, "crest_db": 15,
            "spectrum": {"bands": {"low mids (250-500 Hz)": {"share_pct": 20}}}, "pan": 0, **kw}


def test_plan_sets_levels_relative_to_the_drums_for_the_genre():
    chans = [channel("Kick", "kick", -10), channel("Bass", "bass", -6), channel("Pad", "pad", -8),
             channel("Vocal", "vocal", -15)]
    plan = plan_mix(chans, {"family": "electronic dance", "mix": {"low_end": "heavy"}})
    gains = {a["name"]: a["gain_db"] for a in plan["channels"]}
    assert plan["anchor_lufs"] == -10
    assert gains == {"Kick": 0, "Bass": -5.0, "Pad": -12.0, "Vocal": 4.0}   # bass -1 LU (heavy low end), pad -10, vocal -1
    assert [{k: d[k] for k in ("source", "target", "depth")} for d in plan["sidechains"]] == [
        {"source": "Kick", "target": "Bass", "depth": "medium"}, {"source": "Kick", "target": "Pad", "depth": "light"}]
    pop = plan_mix(chans, {"family": "pop", "mix": {"low_end": "moderate"}})
    assert {a["name"]: a["gain_db"] for a in pop["channels"]}["Vocal"] == 6.0 and not pop["sidechains"]


def test_a_cue_keeps_its_drone_under_the_solo_melody():
    chans = [channel("Heartbeat Drums", "drums", -12), channel("Drone Bass", "bass", -16),
             channel("Flute Lead", "lead", -10)]
    gains = {a["name"]: a["gain_db"] for a in plan_mix(chans, {"family": "film and games"})["channels"]}
    assert -16 + gains["Drone Bass"] < -10 + gains["Flute Lead"] - 2   # the flute leads, the drone sits under it
    dance = {a["name"]: a["gain_db"] for a in plan_mix(chans, {"family": "electronic dance"})["channels"]}
    assert -16 + dance["Drone Bass"] > -10 + dance["Flute Lead"]       # dance music keeps its loud bass


def test_metal_vocals_sit_inside_the_guitars():
    chans = [channel("Drums", "drums", -10), channel("Guitars", "lead", -14), channel("Rhythm", "keys", -14),
             channel("Vox", "vocal", -14)]
    level = lambda plan, name: -14 + {a["name"]: a["gain_db"] for a in plan["channels"]}[name]  # noqa: E731
    metal = plan_mix(chans, {"family": "metal and punk"})
    assert level(metal, "Vox") < level(metal, "Guitars") and level(metal, "Vox") < level(metal, "Rhythm")
    pop = plan_mix(chans, {"family": "pop"})
    assert level(pop, "Vox") - level(pop, "Guitars") >= 5
    rock = plan_mix(chans, {"family": "rock"})
    assert level(metal, "Vox") < level(rock, "Vox") < level(pop, "Vox")


def test_plan_cleans_up_without_touching_what_the_user_set():
    chans = [channel("Kick", "kick", -10),
             channel("Keys", "keys", -15, spectrum={"bands": {"low mids (250-500 Hz)": {"share_pct": 40}}}),
             channel("Keys 2", "keys", -15, pan=-0.5),
             channel("Lead", "lead", -12, has_eq=True, has_comp=True),
             channel("Vocal", "vocal", -12, crest_db=8)]
    acts = {a["name"]: a for a in plan_mix(chans)["channels"]}
    assert acts["Keys"]["highpass_hz"] == 140 and acts["Keys"]["mud_cut_db"] == -3.0 and acts["Keys"]["pan"] == 0.25
    assert "pan" not in acts["Keys 2"]                                   # already panned by the user
    assert "highpass_hz" not in acts["Lead"] and "compress" not in acts["Lead"]   # has its own EQ and compressor
    assert "compress" not in acts["Vocal"]                               # already even (crest 8 dB)
    assert "highpass_hz" not in acts["Kick"] and "reverb_send_db" not in acts["Kick"]
    assert acts["Vocal"]["reverb_send_db"] == -12


def test_silent_tracks_are_left_alone():
    acts = {a["name"]: a for a in plan_mix([channel("Kick", "kick", -10), channel("Ghost", "lead", None)])["channels"]}
    assert acts["Ghost"] == {"name": "Ghost", "role": "lead", "ref": "Ghost", "skipped": "silent in this range"}


def test_plan_targets_each_track_by_its_own_id():
    # auto_mix used to apply the plan by track name: two tracks named "Synth" both
    # went to the first one, "808" was read as track number 808, and an unnamed track
    # matched track 1. Each action now carries the track's GUID.
    chans = [
        {"name": "Synth", "ref": "{AAAAAAAA-0000-0000-0000-000000000001}", "role": "lead", "level": -14.0},
        {"name": "Synth", "ref": "{AAAAAAAA-0000-0000-0000-000000000002}", "role": "lead", "level": -20.0},
        {"name": "808", "ref": "{AAAAAAAA-0000-0000-0000-000000000003}", "role": "bass", "level": -12.0},
        {"name": "Kick", "ref": "{AAAAAAAA-0000-0000-0000-000000000004}", "role": "kick", "level": -10.0},
    ]
    plan = plan_mix(chans, {"family": "electronic dance", "mix": {"low_end": "heavy"}})
    assert [a["ref"] for a in plan["channels"]] == [c["ref"] for c in chans]
    gains = [a["gain_db"] for a in plan["channels"][:2]]
    assert gains[0] != gains[1]  # the two Synths get their own levels
    side = plan["sidechains"][0]
    assert side["source_ref"] == chans[3]["ref"] and side["target_ref"] == chans[2]["ref"]



def test_boosts_are_capped_and_sub_drones_barely_raised():
    sub = {"bands": {"sub (20-60 Hz)": {"share_pct": 70}, "bass (60-250 Hz)": {"share_pct": 20}}}
    acts = {a["name"]: a for a in plan_mix([channel("Kick", "kick", -10), channel("Lead", "lead", -30),
                                             channel("Drone", "other", -30, spectrum=sub)])["channels"]}
    assert acts["Lead"]["gain_db"] == 6.0        # wanted +15
    assert acts["Drone"]["gain_db"] == 2.0       # a K-weighted meter underrates sub: barely raised
    assert acts["Lead"]["capped"].startswith("wanted +15.0 dB, boosts stop at +6")
    assert acts["Drone"]["capped"].startswith("wanted +13.0 dB, boosts stop at +2")


def test_highpass_stays_under_a_parts_lowest_notes():
    from creaper.mix_tools import highpass_for
    def octaves(**dbs):
        return {"octave_bands_db": dbs}
    cello = octaves(**{"63 Hz": -6, "125 Hz": -4, "250 Hz": -8, "500 Hz": -14})           # fundamentals from ~65 Hz
    assert highpass_for("pad", cello) is None    # 0.6 x 44.5 Hz is under 40 Hz: no high-pass at all
    viola = octaves(**{"125 Hz": -30, "250 Hz": -6, "500 Hz": -4, "1 kHz": -8})
    assert highpass_for("pad", viola) == 106     # under its lowest strong octave (~177 Hz), not the usual 180
    hats = octaves(**{"2 kHz": -10, "4 kHz": -4, "8 kHz": -3})
    assert highpass_for("perc", hats) == 300     # nothing low: the usual high-pass
    assert highpass_for("bass", cello) is None


def test_sidechain_level_ignores_the_trigger_tracks_fader(monkeypatch):
    # The send taps the kick before its fader, but the level was measured after it: a
    # kick turned down 10 dB got 10 dB too much send and ducked ~15 dB, not ~4.5.
    from creaper import server

    sends = []

    def fake_call(command, **args):
        if command == "setup_sidechain":
            return {"target": {"number": 2}, "is_reacomp": True, "fx_index": 1}
        if command == "describe_track":
            return {"volume_db": -10.0}
        if command == "set_send":
            sends.append(args["volume_db"])
        return {}

    monkeypatch.setattr(server, "call", fake_call)
    monkeypatch.setattr(server, "analyze_audio", lambda **a: {"levels": {"sample_peak_dbfs": -16.0}})
    result = server.setup_sidechain(source="Kick", target="Bass")
    assert sends == [0.0]  # the kick peaks at -6 dBFS before its fader already
    assert result["sidechain_level"] == {"source_peak_dbfs": -6.0, "send_gain_db": 0.0}


def test_mastering_reports_the_master_as_it_ends_up(monkeypatch):
    # When the passes ran out right after an adjustment, the report showed the
    # measurement from before it: "-20 LUFS, not reached" for a master now at -14.2.
    from creaper import server

    def fake_call(command, **args):
        if command == "get_track_details":
            return {"fx": [{"index": 1, "name": "ReaLimit"}]}
        if command == "get_fx_parameters":
            return {"parameters": [{"display": "0.0"}]}
        if command == "describe_track":
            return {"volume_db": 0.0}
        return {}

    readings = iter([-20.0, -20.0, -14.2])  # the first is the pre-limiter check
    monkeypatch.setattr(server, "call", fake_call)
    monkeypatch.setattr(server, "analyze_audio", lambda **a: {
        "loudness": {"integrated_lufs": next(readings)}, "levels": {"true_peak_dbtp": -1.5}})
    result = server.master_to_target(target_lufs=-14.0, glue=False, passes=1, force=True)
    assert [p["integrated_lufs"] for p in result["passes"]] == [-20.0, -14.2]
    assert result["reached"] is True


def _glue_fake(monkeypatch, tracks, routing=None):
    from creaper import mix_tools, server
    calls = []

    def fake_call(command, **args):
        calls.append((command, args))
        if command == "get_project_overview":
            return {"tracks": tracks, "tempo_bpm": 120}
        if command == "get_routing":
            return {"tracks": routing or [{"name": t["name"], "sends": []} for t in tracks]}
        if command == "create_bus":
            return {"bus": {"guid": "{BUS}", "number": 9}}
        if command == "get_track_details":
            return {"fx": [{"index": 1, "name": "VSTi: ReaSynDr", "instrument": True}]}
        if command == "add_fx":
            return {"name": "VST: ReaComp (Cockos)", "index": 2}
        if command == "create_track":
            return {"track": {"guid": "{DELAY}", "number": 10}}
        if command == "set_fx_parameters":
            return {"results": [{"parameter": c["parameter"]} for c in args["changes"]]}
        return {}

    monkeypatch.setattr(mix_tools, "call", fake_call)
    monkeypatch.setattr(server, "_calibrate_compressor", lambda *a, **k: {"loud_part_reduction_db": 2.0})
    return mix_tools, calls


KICK = {"name": "Kick", "ref": "{K}", "role": "kick", "level": -10}
SNARE = {"name": "Snare", "ref": "{S}", "role": "snare", "level": -12}


def test_drums_are_glued_on_a_new_bus(monkeypatch):
    tracks = [{"guid": "{K}", "name": "Kick"}, {"guid": "{S}", "name": "Snare"}, {"guid": "{B}", "name": "Bass"}]
    mix_tools, calls = _glue_fake(monkeypatch, tracks)
    result = mix_tools._glue_drums([KICK, SNARE, {"name": "Bass", "ref": "{B}", "role": "bass", "level": -12}], None, None)
    bus = next(a for c, a in calls if c == "create_bus")
    assert bus["tracks"] == ["{K}", "{S}"] and "Drum Bus" in result["where"]
    settings = next(a for c, a in calls if c == "set_fx_parameters")["changes"]
    assert {"parameter": "Attack", "display_value": 10} in settings and result["calibration"]


def test_a_bus_the_drums_already_feed_is_reused_not_doubled(monkeypatch):
    # A second auto_mix run made a second Drum Bus: the drums played through both (+6 dB).
    tracks = [{"guid": "{K}", "name": "Kick"}, {"guid": "{S}", "name": "Snare"},
              {"guid": "{BUS}", "number": 9, "name": "Drum Bus", "fx": []},
              {"guid": "{R}", "number": 8, "name": "Reverb", "fx": ["VST: ReaVerbate (Cockos)"]}]
    routing = [{"name": "Kick", "sends": [{"to": "Drum Bus"}]},
               {"name": "Snare", "sends": [{"to": "Drum Bus"}, {"to": "Reverb"}]}]
    mix_tools, calls = _glue_fake(monkeypatch, tracks, routing)
    result = mix_tools._glue_drums([KICK, SNARE], None, None)
    assert not any(c == "create_bus" for c, _ in calls) and "Drum Bus" in result["where"]
    assert next(a for c, a in calls if c == "add_fx")["track"] == "{BUS}"


def test_the_reverb_return_is_never_taken_for_a_drum_bus(monkeypatch):
    tracks = [{"guid": "{K}", "name": "Kick"}, {"guid": "{S}", "name": "Snare"},
              {"guid": "{R}", "number": 8, "name": "Reverb", "fx": ["VST: ReaVerbate (Cockos)"]}]
    routing = [{"name": "Kick", "sends": [{"to": "Reverb"}]}, {"name": "Snare", "sends": [{"to": "Reverb"}]}]
    mix_tools, calls = _glue_fake(monkeypatch, tracks, routing)
    mix_tools._glue_drums([KICK, SNARE], None, None)
    assert any(c == "create_bus" for c, _ in calls)


def test_drums_in_one_folder_are_glued_on_the_folder(monkeypatch):
    tracks = [{"guid": "{K}", "name": "Kick", "parent": 3}, {"guid": "{S}", "name": "Snare", "parent": 3}]
    mix_tools, calls = _glue_fake(monkeypatch, tracks)
    result = mix_tools._glue_drums([KICK, SNARE], None, None)
    assert not any(c == "create_bus" for c, _ in calls)
    assert next(a for c, a in calls if c == "add_fx")["track"] == 3 and "folder" in result["where"]


def test_a_folder_that_also_holds_the_bass_isnt_compressed_as_drums(monkeypatch):
    tracks = [{"guid": "{K}", "name": "Kick", "parent": 3}, {"guid": "{S}", "name": "Snare", "parent": 3},
              {"guid": "{B}", "name": "Bass", "parent": 3, "item_count": 1}]
    mix_tools, calls = _glue_fake(monkeypatch, tracks)
    assert "skipped" in mix_tools._glue_drums([KICK, SNARE], None, None)
    assert not any(c == "add_fx" for c, _ in calls)


def test_an_arturia_reverb_the_drums_send_to_is_never_the_drum_bus(monkeypatch):
    # The reverb return is recognised by its FX ("Rev PLATE-140"), not only by "verb" in its name.
    kick = {"name": "Kick", "ref": "{K}", "role": "kick", "level": -10}
    snare = {"name": "Snare", "ref": "{S}", "role": "snare", "level": -12}
    tracks = [{"guid": "{K}", "name": "Kick"}, {"guid": "{S}", "name": "Snare"},
              {"guid": "{P}", "name": "Plate", "item_count": 0, "fx": ["VST3: Rev PLATE-140 (Arturia)"]}]
    routing = [{"name": "Kick", "sends": [{"to": "Plate"}]}, {"name": "Snare", "sends": [{"to": "Plate"}]}]
    mix_tools, calls = _glue_fake(monkeypatch, tracks, routing)
    result = mix_tools._glue_drums([kick, snare], None, None)
    added = next(a for c, a in calls if c == "add_fx")
    assert added["track"] == "{BUS}" and "new Drum Bus" in result["where"]


def test_a_whole_kit_on_one_track_is_glued_after_its_instrument(monkeypatch):
    # creaper's own songs have one Drums track: they used to get no drum glue at all.
    mix_tools, calls = _glue_fake(monkeypatch, [{"guid": "{D}", "name": "Drums"}])
    result = mix_tools._glue_drums([{"name": "Drums", "ref": "{D}", "role": "drums", "level": -10}], None, None)
    added = next(a for c, a in calls if c == "add_fx")
    assert added["track"] == "{D}" and added["position"] == 2 and "itself" in result["where"]


def test_the_drum_bus_uses_bus_force_when_installed(monkeypatch):
    from creaper import server
    mix_tools, calls = _glue_fake(monkeypatch, [{"guid": "{D}", "name": "Drums"}])
    plain = mix_tools.call
    calibrated = []

    def with_bus_force(command, **args):
        if command == "add_fx":
            calls.append((command, args))
            return {"name": f"VST3: {args['name']} (Arturia)", "index": 2}
        return plain(command, **args)

    monkeypatch.setattr(mix_tools, "call", with_bus_force)
    monkeypatch.setattr(server, "_calibrate_compressor",
                        lambda track, fx, profile, *a, **k: calibrated.append(profile.name) or {"value": -14})
    result = mix_tools._glue_drums([{"name": "Drums", "ref": "{D}", "role": "drums", "level": -10}], None, None)
    assert next(a for c, a in calls if c == "add_fx")["name"] == "Bus FORCE" and "Bus FORCE" in result["compressor"]
    changes = [c for cmd, a in calls if cmd == "set_fx_parameters" for c in a["changes"]]
    assert {"parameter": "Comp Path Mute", "display_text": "Off"} in changes      # its compressor path opened
    assert {"parameter": "Comp Attack", "display_value": 30} in changes and calibrated == ["Bus FORCE"]
    mix_tools, calls = _glue_fake(monkeypatch, [{"guid": "{D}", "name": "Drums"}])
    monkeypatch.setattr(mix_tools, "call", lambda command, **a: {"fx": [{"index": 2, "name": "VST3: Bus FORCE (Arturia)"}]}
                        if command == "get_track_details" else plain(command, **a))
    assert "skipped" in mix_tools._glue_drums([{"name": "Drums", "ref": "{D}", "role": "drums", "level": -10}], None, None)


def test_a_vocal_fet_is_calibrated_or_taken_out(monkeypatch):
    from creaper import mix_tools, plugin_profiles, server
    calls = []
    monkeypatch.setattr(mix_tools, "call", lambda command, **a: calls.append((command, a)) or {})
    fet = plugin_profiles.find_profile("VST3: Comp FET-76 (Arturia)")
    monkeypatch.setattr(server, "_calibrate_compressors", lambda jobs, s, e: [
        {"value": -20.0, "loud_part_reduction_db": 4.1} if j["track"] == "Lead Vox" else {"error": "too quiet"}
        for j in jobs])
    planned = {"ratio": 3.0, "attack_ms": 5, "release_ms": 80, "threshold_db": -16}
    comps = [{"a": {"name": "Lead Vox", "compress": dict(planned)}, "track": "Lead Vox", "fx": 3, "profile": fet},
             {"a": {"name": "Whisper", "compress": dict(planned)}, "track": "Whisper", "fx": 2, "profile": fet}]
    report: dict = {}
    mix_tools._calibrate_vocal_comps(comps, None, None, report)
    assert comps[0]["a"]["compress"] == {"compressor": "Comp FET-76", "reduction_db": 4.1, "input_gain_db": -20.0}
    assert ("remove_fx", {"track": "Whisper", "fx": 2}) in calls and "Whisper" in report["warnings"][0]
    # The plan no longer claims a compressor that was taken out.
    assert "compress" not in comps[1]["a"] and comps[1]["a"]["compressor_removed"] == "too quiet"


def test_the_delay_return_is_a_dotted_eighth_and_reused_when_there(monkeypatch):
    mix_tools, calls = _glue_fake(monkeypatch, [])
    made = mix_tools._delay_return(120)
    assert made["time_ms"] == 375.0 and not made["reused"]   # a dotted 8th at 120 BPM
    mix_tools, calls = _glue_fake(monkeypatch, [{"guid": "{D}", "name": "Vocal Delay", "item_count": 0,
                                                 "fx": ["VST: ReaDelay (Cockos)"]}])
    assert mix_tools._delay_return(120) == {"track": "{D}", "name": "Vocal Delay", "reused": True}


def test_an_empty_track_named_echo_without_a_delay_isnt_reused(monkeypatch):
    mix_tools, calls = _glue_fake(monkeypatch, [{"guid": "{E}", "name": "Echo", "item_count": 0, "fx": []}])
    assert mix_tools._delay_return(120)["reused"] is False


def test_the_drums_get_their_own_short_room(monkeypatch):
    mix_tools, calls = _glue_fake(monkeypatch, [])
    room = mix_tools._drum_room()
    settings = next(a for c, a in calls if c == "set_fx_parameters")["changes"]
    assert room["name"] == "Drum Room" and not room["reused"]
    assert {"parameter": "Room size", "value": 0.18} in settings
    mix_tools, calls = _glue_fake(monkeypatch, [{"guid": "{R}", "name": "Drum Room", "item_count": 0}])
    assert mix_tools._drum_room() == {"track": "{R}", "name": "Drum Room", "reused": True}


def test_the_main_reverb_is_never_the_drum_room(monkeypatch):
    mix_tools, calls = _glue_fake(monkeypatch, [{"guid": "{R}", "name": "Drum Room", "item_count": 0,
                                                 "fx": ["VST: ReaVerbate (Cockos)"]}])
    assert mix_tools._reverb_return() == "Reverb" and any(c == "create_track" for c, _ in calls)


def _fx_fake(monkeypatch, installed):
    """auto_mix's returns against a REAPER with these plugins (add_fx fails on others)."""
    from creaper import mix_tools
    calls = []

    def fake_call(command, **args):
        calls.append((command, args))
        if command == "get_project_overview":
            return {"tracks": [], "tempo_bpm": 120}
        if command == "create_track":
            return {"track": {"guid": "{NEW}", "number": 5}}
        if command == "add_fx":
            if not any(n.lower() in args["name"].lower() for n in installed):
                raise RuntimeError(f"no FX named '{args['name']}'")
            return {"name": f"VST3: {args['name']} (Arturia)" if "Rea" not in args["name"] else f"VST: {args['name']} (Cockos)",
                    "index": 1}
        if command == "set_fx_parameters":
            return {"results": [{"parameter": c["parameter"]} for c in args["changes"]]}
        return {}

    monkeypatch.setattr(mix_tools, "call", fake_call)
    settings = lambda: {c["parameter"]: c.get("display_value", c.get("display_text", c.get("value")))  # noqa: E731
                        for cmd, a in calls if cmd == "set_fx_parameters" for c in a["changes"]}
    return mix_tools, calls, settings


def test_the_returns_use_the_users_arturia_effects(monkeypatch):
    mix_tools, calls, settings = _fx_fake(monkeypatch, ["Rev PLATE-140", "Rev INTENSITY", "Delay TAPE-201"])
    assert mix_tools._reverb_return(120, "pop") == "Reverb"
    assert [a["name"] for c, a in calls if c == "add_fx"] == ["Rev PLATE-140"]
    assert settings() == {"Blend Dry/wet": 1.0, "Decay Time": 2, "Pre Delay": 31.2, "HP Filter": 280}
    mix_tools, calls, settings = _fx_fake(monkeypatch, ["Rev PLATE-140", "Rev INTENSITY", "Delay TAPE-201"])
    mix_tools._reverb_return(90, "film and games")                       # a hall for a cue
    assert [a["name"] for c, a in calls if c == "add_fx"] == ["Rev INTENSITY"] and settings()["Size"] == 0.65
    mix_tools, calls, settings = _fx_fake(monkeypatch, ["Delay TAPE-201"])
    out = mix_tools._delay_return(120)
    assert out["plugin"].startswith("VST3: Delay TAPE-201") and settings()["Repeat Rate Left"] == 375.0
    assert settings()["Dry / Wet"] == 1.0 and settings()["Rates Sync"] == "Off"


def test_the_returns_fall_back_to_reapers_own(monkeypatch):
    mix_tools, calls, settings = _fx_fake(monkeypatch, ["ReaVerbate", "ReaDelay"])
    mix_tools._reverb_return(120, "pop")
    assert [a["name"] for c, a in calls if c == "add_fx"] == ["Rev PLATE-140", "ReaVerbate"]
    assert settings()["Room size"] == 0.35
    mix_tools, calls, settings = _fx_fake(monkeypatch, ["ReaVerbate", "ReaDelay"])
    assert mix_tools._delay_return(120)["plugin"] == "VST: ReaDelay (Cockos)" and settings()["Feedback"] == -9


def test_an_arturia_reverb_return_is_reused(monkeypatch):
    from creaper import mix_tools
    monkeypatch.setattr(mix_tools, "call", lambda command, **a: {"tracks": [
        {"name": "Space", "item_count": 0, "fx": ["VST3: Rev PLATE-140 (Arturia)"]}]} if command == "get_project_overview" else {})
    assert mix_tools._reverb_return() == "Space"


def test_mix_bus_glue_goes_before_the_limiter(monkeypatch):
    from creaper import mix_tools, server
    calls = []

    def fake_call(command, **args):
        calls.append((command, args))
        if command == "get_track_details":
            return {"fx": [{"index": 1, "name": "VST: ReaEQ (Cockos)"}, {"index": 2, "name": "VST: ReaLimit (Cockos)"}]}
        if command == "add_fx":
            return {"name": "VST: ReaComp (Cockos)", "index": 2}
        return {}

    monkeypatch.setattr(mix_tools, "call", fake_call)
    monkeypatch.setattr(server, "_calibrate_compressor", lambda *a, **k: {"loud_part_reduction_db": 1.0})
    result = mix_tools._mix_bus_glue(None, None)
    added = next(a for c, a in calls if c == "add_fx")
    assert added["track"] == "master" and added["position"] == 2 and result["calibration"]


def test_no_mix_bus_glue_when_the_master_already_compresses(monkeypatch):
    from creaper import mix_tools
    monkeypatch.setattr(mix_tools, "call", lambda command, **a: {"fx": [{"index": 1, "name": "VST3: Bus FORCE (Arturia)"}]}
                        if command == "get_track_details" else {})
    assert "skipped" in mix_tools._mix_bus_glue(None, None)



def test_plan_narrows_spread_lows_and_widens_pads_in_wide_genres():
    from creaper import mix_tools
    channels = [
        {"name": "Bass", "role": "bass", "level": -14, "stereo": {"low_end_correlation_below_150hz": 0.4}},
        {"name": "Kick", "role": "kick", "level": -12, "stereo": {"low_end_correlation_below_150hz": 0.98}},
        {"name": "Kit", "role": "drums", "level": -12, "stereo": {"low_end_correlation_below_150hz": 0.5}},
        {"name": "Pad", "role": "pad", "level": -22, "stereo": {"correlation": 0.9, "side_to_mid_db": -20}},
        {"name": "Keys", "role": "keys", "level": -20, "stereo": {"correlation": 0.2, "side_to_mid_db": -20}},
    ]
    wide = {a["name"]: a for a in mix_tools.plan_mix(channels, {"mix": {"width": "wide"}})["channels"]}
    assert wide["Bass"].get("mono_low") and not wide["Kick"].get("mono_low")
    assert wide["Kit"]["low_end_not_mono"] == 0.5 and not wide["Kit"].get("mono_low")
    assert wide["Pad"]["widen_db"] == mix_tools.WIDEN_DB
    assert "widen_db" not in wide["Keys"]        # widening would make it worse in mono
    narrow = {a["name"]: a for a in mix_tools.plan_mix(channels, {"mix": {"width": "narrow"}})["channels"]}
    assert "widen_db" not in narrow["Pad"]



def test_a_new_reverb_is_sized_for_the_genre_with_predelay_and_filters(monkeypatch):
    from creaper import mix_tools
    sets = []

    def fake_call(cmd, **kw):
        if cmd == "get_project_overview":
            return {"tracks": []}
        if cmd == "set_fx_parameters":
            sets.append({c["parameter"]: c.get("display_value", c.get("value")) for c in kw["changes"]})
        return {}

    monkeypatch.setattr(mix_tools, "call", fake_call)
    assert mix_tools._reverb_return(120, "pop") == "Reverb"
    assert sets[0]["Room size"] == 0.35 and sets[0]["Delay"] == 31.2   # a 64th at 120 BPM
    assert (sets[0]["Hipass"], sets[0]["Lowpass"]) == mix_tools.REVERB_FILTER_HZ
    mix_tools._reverb_return(60, "film and games")
    assert sets[1]["Room size"] == 0.65 and sets[1]["Delay"] == 40.0     # slow songs: capped at 40 ms
    mix_tools._reverb_return(200, None)
    assert sets[2]["Room size"] == 0.5 and sets[2]["Delay"] == 20.0     # fast songs: at least 20 ms



def _spec(low=10, mids=40, upper=5, presence=2, air=1.0, oct31=-20, oct63=-10):
    return {"bands": {"sub (20-60 Hz)": {"share_pct": low / 2}, "bass (60-250 Hz)": {"share_pct": low / 2},
                      "low mids (250-500 Hz)": {"share_pct": 5}, "mids (500 Hz-2 kHz)": {"share_pct": mids},
                      "upper mids (2-4 kHz)": {"share_pct": upper}, "presence (4-6 kHz)": {"share_pct": presence},
                      "air (6-20 kHz)": {"share_pct": air}},
            "octave_bands_db": {"31.5 Hz": oct31, "63 Hz": oct63, "125 Hz": -15, "1 kHz": -10}}


def test_tone_pass_presence_air_carve_and_low_heavy_keys():
    from creaper import mix_tools
    channels = [
        {"name": "Kick", "role": "kick", "level": -10, "spectrum": _spec(low=80, oct31=-6, oct63=-12)},
        {"name": "Bass", "role": "bass", "level": -12, "spectrum": _spec(low=70, oct31=-14, oct63=-5)},
        {"name": "Lead", "role": "lead", "level": -15, "spectrum": _spec(upper=3, presence=2, air=0.5)},
        {"name": "Vocal", "role": "vocal", "level": -13, "spectrum": _spec(upper=25, presence=12, air=5)},
        {"name": "Pad", "role": "pad", "level": -20, "spectrum": _spec(low=30)},
    ]
    acts = {a["name"]: a for a in mix_tools.plan_mix(channels)["channels"]}
    assert acts["Bass"]["carve"] == {"hz": 32, "db": mix_tools.CARVE_DB}     # where the kick is loudest
    assert acts["Kick"]["carve"] == {"hz": 63, "db": mix_tools.CARVE_DB}     # and the other way round
    assert acts["Lead"]["presence_db"] == mix_tools.PRESENCE_LIFT_DB and acts["Lead"]["air_db"] == mix_tools.AIR_LIFT_DB
    assert acts["Vocal"]["presence_db"] == mix_tools.PRESENCE_CUT_DB and "air_db" not in acts["Vocal"]
    assert acts["Pad"]["highpass_hz"] >= 250
    # Every EQ sets band 5 on purpose: a bass with only a carve isn't high-passed at ReaEQ's default 100 Hz.
    bass_eq = {c["parameter"]: c["display_value"] for c in mix_tools.eq_changes(acts["Bass"])}
    assert bass_eq["Freq-High Pass 5"] == mix_tools.NO_HIGHPASS_HZ and bass_eq["Freq-Band 2"] == 32


def test_low_strings_and_brass_keep_their_fundamentals():
    """The low-heavy keys/pad high pass took 'Strings Low' to 250 Hz and 'Low Brass' to 210."""
    from creaper import mix_tools
    low = {"bands": {"bass (60-250 Hz)": {"share_pct": 45}, "low mids (250-500 Hz)": {"share_pct": 20}},
           "octave_bands_db": {"63 Hz": -6, "125 Hz": -4, "250 Hz": -8, "500 Hz": -14}}
    channels = [{"name": "Drums", "role": "drums", "level": -10},
                {"name": "Strings Low", "role": "pad", "level": -20, "spectrum": low},
                {"name": "Low Brass", "role": "keys", "level": -20, "spectrum": low},
                {"name": "Synth Pad", "role": "pad", "level": -20, "spectrum": low}]
    acts = {a["name"]: a for a in mix_tools.plan_mix(channels)["channels"]}
    assert "highpass_hz" not in acts["Strings Low"] and "highpass_hz" not in acts["Low Brass"]  # under 40 Hz: none
    assert acts["Synth Pad"]["highpass_hz"] >= 250     # a pad crowding the bass still gets cleared


def test_kick_and_bass_sharing_an_octave_leave_it_to_the_kick():
    from creaper import mix_tools
    carve = mix_tools._kick_bass_carve([{"name": "K", "role": "kick", "spectrum": _spec(oct63=-4)},
                                        {"name": "B", "role": "bass", "spectrum": _spec(oct63=-3)}])
    assert carve == {"B": {"hz": 63, "db": mix_tools.CARVE_DB}}



def test_section_lifts_raise_choruses_that_dont_lift():
    from creaper import mix_tools
    table = mix_tools.plan_section_lifts([
        {"name": "Intro", "lufs": -16.0}, {"name": "Verse", "lufs": -12.0}, {"name": "Chorus", "lufs": -11.8},
        {"name": "Breakdown", "lufs": -16.0}, {"name": "Drop", "lufs": -10.0}, {"name": "Outro", "lufs": -15.0}])
    gains = {r["section"]: r["gain_db"] for r in table}
    assert gains["Chorus"] == 1.3          # 0.2 LU over the verse: 1.3 more makes 1.5
    assert gains["Drop"] == 0.0            # 6 LU over the breakdown already
    assert gains["Verse"] == 0.0 and gains["Breakdown"] == 0.0 and gains["Outro"] == 0.0
    flat = mix_tools.plan_section_lifts([{"name": "Verse", "lufs": -10.0}, {"name": "Chorus", "lufs": -12.0}])
    assert flat[1]["gain_db"] == mix_tools.MAX_SECTION_GAIN_DB   # capped



def test_colour_picks_the_first_amount_that_lifts_the_top_without_losing_punch():
    from creaper import mix_tools
    trials = [{"amount": 15, "rise_db": 0.8, "crest_drop_db": 0.1}, {"amount": 30, "rise_db": 2.4, "crest_drop_db": 0.4},
              {"amount": 45, "rise_db": 3.9, "crest_drop_db": 1.6}]
    assert mix_tools.choose_colour(trials)["amount"] == 30
    crushing = [{"amount": 15, "rise_db": 0.9, "crest_drop_db": 0.3}, {"amount": 30, "rise_db": 2.6, "crest_drop_db": 1.4}]
    assert mix_tools.choose_colour(crushing)["amount"] == 15          # the most it can take with its punch
    assert mix_tools.choose_colour([{"amount": 15, "rise_db": 0.1, "crest_drop_db": 0.0}]) is None


def test_band_db_hears_added_harmonics():
    import numpy as np
    from creaper import mix_tools
    fs = 22050
    t = np.arange(fs) / fs
    clean = 0.5 * np.sin(2 * np.pi * 110 * t)
    driven = np.tanh(3 * clean) / 3 * 1.5
    assert mix_tools.band_db(driven, fs) > mix_tools.band_db(clean, fs) + 20
