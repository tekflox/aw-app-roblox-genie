"""The Genie's MCP server: tool inventory and the anti-prompt-injection
boundary (scale_object/kick_players/set_lighting must never appear here).
Ported from aw-app-roblox's test_mcp.py when the Genie's tools moved into
this standalone app. Deliberately no network — every handler that would
call out is only checked for its "not configured" failure path.

Run: python -m pytest tests/test_mcp.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from roblox_genie_app import config  # noqa: E402
from roblox_genie_app.mcp import (  # noqa: E402
    aw_roblox_genie_server,
    genie_kanban,
    genie_npc_control,
    npc_control,
    self_register,
)


@pytest.fixture(autouse=True)
def _reset_config():
    config.install_resolvers(lambda: {}, lambda name: None)
    yield
    config.install_resolvers(lambda: {}, lambda name: None)


def test_aw_roblox_genie_upstream_excludes_scale_object_and_kick_players():
    names = {t["name"] for t in aw_roblox_genie_server.TOOLS_SCHEMA}
    assert "scale_object" not in names
    assert "kick_players" not in names
    assert "set_lighting" not in names
    assert names == set(aw_roblox_genie_server._DISPATCH)
    # 2 genie-kanban + 14 genie-npc-control tools
    assert len(names) == 16


def test_genie_npc_control_is_a_strict_subset_of_npc_control():
    genie_names = set(genie_npc_control.DISPATCH)
    full_names = set(npc_control.DISPATCH)
    assert genie_names < full_names
    assert genie_names == full_names - {"scale_object", "kick_players", "set_lighting"}
    # same handler objects, not reimplemented copies
    for name in genie_names:
        assert genie_npc_control.DISPATCH[name] is npc_control.DISPATCH[name]


def test_upstream_key_matches_the_name_used_when_it_lived_in_aw_app_roblox():
    servers = self_register.build_mcp_servers(port=9030)
    assert set(servers) == {"aw-roblox-genie"}


def test_npc_control_tool_without_api_key_names_the_missing_config():
    text, is_error = npc_control.DISPATCH["npc_list"]({})
    assert is_error is False  # npc_list itself makes no HTTP call

    text, is_error = npc_control.DISPATCH["list_objects"]({})
    assert is_error is True
    assert config.PILOT_BACKEND_API_KEY in text


def test_genie_kanban_prefixes_title_and_never_lets_caller_skip_it():
    box = {}

    import urllib.request

    class _FakeResponse:
        status = 200

        def __init__(self, body):
            self._body = body

        def read(self):
            return self._body

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def _fake_urlopen(req, timeout=30):
        import json as _json
        box["url"] = req.full_url
        box["body"] = _json.loads(req.data.decode())
        return _FakeResponse(b'{"ok": true, "page_id": "abc123"}')

    monkey = urllib.request.urlopen
    urllib.request.urlopen = _fake_urlopen
    try:
        import os
        os.environ["AW_WORKSPACE_API_KEY"] = "test-key"
        # caller already added the prefix itself -- must not be doubled
        text, is_error = genie_kanban.DISPATCH["create_genie_card"](
            {"title": "[GENIE] a house", "request": "quero uma casa",
             "player_name": "tester"})
    finally:
        urllib.request.urlopen = monkey
        os.environ.pop("AW_WORKSPACE_API_KEY", None)

    assert is_error is False
    assert box["body"]["title"] == "[GENIE] a house"
    assert box["body"]["source"] == "roblox-genie"
    assert "/api/apps/notion/kanban/cards" in box["url"]


def test_config_defaults():
    assert config.pilot_backend_url() == config.DEFAULT_PILOT_BACKEND_URL
    assert config.pilot_backend_api_key() == ""


def test_config_resolved_per_call_not_captured_at_import():
    box = {"cfg": {}, "secret": None}
    config.install_resolvers(lambda: box["cfg"], lambda name: box["secret"])
    assert config.pilot_backend_api_key() == ""
    box["secret"] = "sk-later"
    assert config.pilot_backend_api_key() == "sk-later"
