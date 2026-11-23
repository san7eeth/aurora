"""Unit checks for the agent's fixed local-tool allowlist."""

import pytest

from app.agent.tools import TOOL_SCHEMAS, execute_tool, validate_arguments


def test_tool_registry_contains_only_expected_tools():
    assert {tool["name"] for tool in TOOL_SCHEMAS} == {
        "system_info", "list_files", "launch_app", "clipboard_read"
    }


def test_unknown_tool_is_rejected():
    with pytest.raises(ValueError, match="Unknown tool"):
        validate_arguments("shell", {"command": "whoami"})


def test_launch_app_accepts_only_fixed_allowlist():
    assert validate_arguments("launch_app", {"app": "notepad"}) == {"app": "notepad"}
    with pytest.raises(ValueError, match="allowlist|one of"):
        validate_arguments("launch_app", {"app": "powershell"})


def test_tool_rejects_unexpected_path_argument():
    with pytest.raises(ValueError, match="does not accept arguments"):
        validate_arguments("list_files", {"path": "C:/"})


def test_system_info_returns_basic_host_metadata():
    result = execute_tool("system_info", {})
    assert result["os"]
    assert result["python"]
    assert result["logical_cpus"] >= 1
