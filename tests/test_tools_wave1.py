"""Tests for the 61-drawer tool organization system."""


def test_tool_command_lookup():
    from graphparti.canvas_widget import TOOL_COMMANDS
    assert TOOL_COMMANDS["line"] == "line"
    assert TOOL_COMMANDS["mirror"] == "mirror"
    assert TOOL_COMMANDS["dim"] == "dim_linear"
    assert TOOL_COMMANDS["h"] == "hatch"
    assert TOOL_COMMANDS["vp"] == "perspective"
