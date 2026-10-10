from pathlib import Path

import pytest

luaparser = pytest.importorskip("luaparser")
from luaparser import ast  # noqa: E402

SCRIPTS = sorted((Path(__file__).parent.parent / "src" / "creaper" / "reaper").glob("*.lua"))


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_lua_scripts_parse(script):
    ast.parse(script.read_text(encoding="utf-8"))
