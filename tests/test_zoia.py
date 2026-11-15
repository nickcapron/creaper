"""ZOIA patch files: the layout, byte for byte, and the edits that are safe on one.

The reader and writer were checked on 2026-11-15 against 26 public patches (firmware
from before 1.04 to 2.x): every one came back byte-identical. Those files are other
people's work and aren't in the repo; the patches here are built field by field from
the format document.
"""

import struct

import pytest

from creaper import zoia


def _module(type_id, position, params=(), options=(), saved=b"", saved_size=None, name=b"", named=True, page=0, color=7):
    words = 10 + len(params) + len(saved) // 4 + (4 if named else 0)
    return (struct.pack("<8I", words, type_id, 0, page, color, position, len(params),
                        len(saved) if saved_size is None else saved_size)
            + bytes(options).ljust(8, b"\0") + struct.pack(f"<{len(params)}I", *params) + saved
            + (name.ljust(16, b"\0") if named else b""))


def _file(body: bytes) -> bytes:
    return (struct.pack("<I", len(body) // 4 + 1) + body).ljust(32768, b"\0")


def _delay_patch() -> bytes:
    """Audio Input -> Delay w/Mod -> Audio Output, as a 1.10+ ZOIA saves it: the delay's
    mix starred on CC 21, one page name, a colour per module."""
    body = b"Slapback".ljust(16, b"\0") + struct.pack("<I", 3)
    body += _module(1, 0, color=1)
    body += _module(43, 8, params=(13107, 26214, 32768, 19661, 13107), saved=bytes(range(8)), name=b"echo", color=3)
    body += _module(2, 38, params=(54614,), options=(1, 0), color=3)
    body += struct.pack("<I", 2) + struct.pack("<5I", 0, 0, 1, 0, 10000) + struct.pack("<5I", 1, 7, 2, 0, 9400)
    body += struct.pack("<I", 1) + b"main".ljust(16, b"\0")
    body += struct.pack("<2I", 1, 1 | 6 << 16 | 22 << 23)
    body += struct.pack("<3I", 11, 8, 14)
    return _file(body)


def test_a_patch_reads_as_what_was_saved_and_writes_back_byte_for_byte():
    data = _delay_patch()
    p = zoia.parse(data)
    assert p.name == "Slapback" and [m.type_name for m in p.modules] == ["Audio Input", "Delay w/Mod", "Audio Output"]
    delay = p.modules[1]
    assert (delay.name, delay.position, delay.params[0], delay.saved) == ("echo", 8, 13107, bytes(range(8)))
    assert p.modules[2].options[:2] == [1, 0] and p.colors == [11, 8, 14] and p.pages == 1
    assert [(c.source, c.source_block, c.dest, c.dest_block, c.db) for c in p.connections] == [(0, 0, 1, 0, 0.0), (1, 7, 2, 0, -6.0)]
    assert zoia.build(p) == data and len(data) == zoia.PATCH_BYTES
    d = zoia.describe(p)
    assert d["modules"][1] == {"index": 1, "type": "Delay w/Mod", "name": "echo", "page": 0, "position": 8, "color": "orange",
                               "version": 0, "options": [0] * 8, "params": [0.2, 0.4, 0.5, 0.3, 0.2], "saved_bytes": 8}
    assert d["starred"] == [{"module": 1, "block": 6, "type": "Delay w/Mod", "midi_cc": 21}]
    assert d["pages"] == [{"page": 0, "name": "main", "modules": 3}] and d["bytes"] == struct.unpack_from("<I", data)[0] * 4


def test_files_from_old_firmware_have_no_module_names_and_no_colours():
    # 'deep water' and four more of the 26: modules of 10 words plus parameters and saved data, then
    # nothing; the saved-data size is in bytes (an Oscillator's 1 is still a whole word).
    body = b"old".ljust(16, b"\0") + struct.pack("<I", 2)
    body += _module(1, 0, named=False) + _module(45, 1, params=(13480,), saved=struct.pack("<I", 50722560), saved_size=1, named=False)
    body += struct.pack("<I", 0) + struct.pack("<I", 0) + struct.pack("<I", 0)
    data = _file(body)
    p = zoia.parse(data)
    assert [m.name_raw for m in p.modules] == [None, None] and p.colors is None
    assert p.modules[1].params == [13480] and len(p.modules[1].saved) == 4 and p.modules[1].name == ""
    assert zoia.build(p) == data
    assert zoia.describe(p)["modules"][1]["color"] == "white"       # the module's own (old) colour


def test_what_is_not_understood_is_carried():
    # Bytes inside the patch size after the colours, and non-zero bytes past it, come back as found.
    data = bytearray(_delay_patch())
    end = struct.unpack_from("<I", data)[0] * 4
    data[end:end + 4] = b"\x05\0\0\0"
    struct.pack_into("<I", data, 0, end // 4 + 1)
    data[end + 8:end + 10] = b"zz"
    p = zoia.parse(bytes(data))
    assert p.extra == b"\x05\0\0\0" and p.tail == b"\0\0\0\0zz"
    assert zoia.build(p) == bytes(data)


def test_stars_on_parameters_and_on_connections():
    assert zoia.Star.from_word(3 | 2 << 16) == zoia.Star(module=3, block=2)
    assert zoia.Star.from_word(3 | 2 << 16 | 1 << 23) == zoia.Star(module=3, block=2, cc=0)       # CC 0 is stored as 1
    on_cable = ~(5 | 64 << 23) & 0xFFFFFFFF                # a connection's star is the same word, every bit flipped
    assert zoia.Star.from_word(on_cable) == zoia.Star(connection=5, cc=63)
    for s in (zoia.Star(module=40, block=9, cc=127), zoia.Star(connection=300), zoia.Star(module=0, block=0)):
        assert zoia.Star.from_word(s.word()) == s


def test_the_edits_that_are_safe_on_any_patch():
    p = zoia.parse(_delay_patch())
    zoia.set_param(p, 1, 0, 0.75)
    zoia.set_strength(p, 1, -12.5)
    zoia.star(p, 1, 3, cc=30)
    zoia.star(p, 1, 6, cc=40)                    # already starred: its CC changes, no second star
    p.name = "Echo 2.0"
    p.modules[0].name = "in"
    again = zoia.parse(zoia.build(p))
    assert again.name == "Echo 2.0" and again.modules[0].name == "in" and again.modules[1].params[0] == 49151
    assert again.connections[1].strength == 8750 and again.connections[1].db == -12.5
    assert [zoia.Star.from_word(w) for w in again.starred] == [zoia.Star(module=1, block=6, cc=40), zoia.Star(module=1, block=3, cc=30)]
    assert again.modules[1].saved == bytes(range(8))            # untouched
    zoia.set_strength(p, 0, 12)                                 # the ZOIA's top: 11200 in the 26 patches
    assert p.connections[0].strength == 11200
    for bad in (lambda: zoia.set_param(p, 1, 5, 0.5), lambda: zoia.set_param(p, 1, 0, 1.2), lambda: zoia.set_param(p, 3, 0, 0.5),
                lambda: zoia.set_strength(p, 2, 0), lambda: zoia.set_strength(p, 0, 13), lambda: zoia.star(p, 9, 0),
                lambda: zoia.star(p, 1, 0, cc=128)):
        with pytest.raises(ValueError):
            bad()


def test_names_are_the_zoias_characters():
    p = zoia.Patch()
    p.name = "Tape Echo v1.2-b"
    assert p.name_raw == b"Tape Echo v1.2-b"
    with pytest.raises(ValueError, match="17 characters"):
        p.name = "seventeen letters"
    with pytest.raises(ValueError, match="'_'"):
        p.name = "tape_echo"


def test_a_patch_built_from_nothing():
    p = zoia.Patch(colors=[1, 3])
    p.name = "thru"
    p.modules = [zoia.Module(1, old_color=1), zoia.Module(2, position=38, old_color=3)]
    p.connections = [zoia.Connection(0, 0, 1, 0), zoia.Connection(0, 1, 1, 1)]
    data = zoia.build(p)
    # The format document's own example (two modules, two connections) is 0x39 words; this is it without
    # its two 16-byte page names.
    assert struct.unpack_from("<I", data)[0] == 0x39 - 8 and len(data) == 32768
    assert struct.unpack_from("<8I", data, 24) == (14, 1, 0, 0, 1, 0, 0, 0)
    assert zoia.parse(data) == p


def test_what_cannot_be_a_patch_is_refused():
    for junk in (b"", b"RIFF" + b"\0" * 100, b"\xff" * 32768, struct.pack("<I", 7) + b"\0" * 32764):
        with pytest.raises(ValueError, match="not a ZOIA patch"):
            zoia.parse(junk)
    cut = bytearray(_delay_patch())
    struct.pack_into("<I", cut, 0, 20)                    # the size ends inside the first module
    with pytest.raises(ValueError, match="not a ZOIA patch"):
        zoia.parse(bytes(cut))
    p = zoia.parse(_delay_patch())
    p.connections.append(zoia.Connection(0, 0, 3, 0))
    with pytest.raises(ValueError, match="the patch has 3"):
        zoia.build(p)
    p = zoia.parse(_delay_patch())
    p.modules.append(zoia.Module(4))
    with pytest.raises(ValueError, match="3 colours for 4 modules"):
        zoia.build(p)
    p.colors.append(1)
    p.modules[3].saved = b"\0" * 33000
    with pytest.raises(ValueError, match="holds 32768"):
        zoia.build(p)


def test_the_card(tmp_path):
    assert zoia.file_name(12, "Tape Echo v1.2") == "012_zoia_Tape_Echo_v1.2.bin" and zoia.file_name(0, "?") == "000_zoia_patch.bin"
    with pytest.raises(ValueError):
        zoia.file_name(64, "x")
    (tmp_path / "003_zoia_Slapback.bin").write_bytes(_delay_patch())
    (tmp_path / "007_zoia_broken.bin").write_bytes(b"\0" * 100)
    (tmp_path / "notes.txt").write_text("x")
    rows = zoia.card_patches(tmp_path)
    assert [(r["slot"], r.get("name"), r.get("modules")) for r in rows] == [(3, "Slapback", 3), (7, None, None)]
    assert "not a ZOIA patch" in rows[1]["error"]
    assert zoia.read(tmp_path / "003_zoia_Slapback.bin").name == "Slapback"


def test_shapes_say_what_a_module_looks_like_in_real_patches():
    a, b = zoia.parse(_delay_patch()), zoia.parse(_delay_patch())
    b.modules[2].options[1] = 1
    got = zoia.shapes([a, b])
    assert sorted(got) == [1, 2, 43]
    assert got[43] == [{"type": "Delay w/Mod", "version": 0, "params": 5, "saved_bytes": 8, "saved_size": 8, "count": 2,
                        "options": [(0,) * 8]}]
    assert got[2][0]["options"] == [(1, 0, 0, 0, 0, 0, 0, 0), (1, 1, 0, 0, 0, 0, 0, 0)]
