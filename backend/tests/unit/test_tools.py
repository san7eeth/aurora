"""Agent tool schemas reject path/shell escalation and unknown operations."""
import sys
from types import SimpleNamespace

import pytest

from app.agent.tools import execute_tool, validate_arguments


@pytest.mark.parametrize("tool,args", [
    ("shell", {"command": "whoami"}),
    ("list_files", {"path": "C:/Users"}),
    ("launch_app", {"app": "powershell"}),
])
def test_unallowlisted_operations_and_arguments_are_rejected(tool, args):
    with pytest.raises(ValueError):
        validate_arguments(tool, args)


def test_clipboard_result_is_plain_text_or_explicitly_unavailable(monkeypatch):
    clipboard = SimpleNamespace(
        CF_UNICODETEXT=13,
        OpenClipboard=lambda: None,
        GetClipboardData=lambda _format: "local text",
        CloseClipboard=lambda: None,
    )
    monkeypatch.setattr("app.agent.tools.platform.system", lambda: "Windows")
    monkeypatch.setitem(sys.modules, "win32clipboard", clipboard)
    assert execute_tool("clipboard_read", {})["text"] == "local text"
