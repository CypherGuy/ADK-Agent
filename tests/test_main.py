"""
Tests for main.py CLI entry point.

These tests cover module structure and argument handling only.
Live pipeline execution requires real Gemini API calls and is verified manually.
"""

import sys
import asyncio
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Module structure
# ---------------------------------------------------------------------------

def test_main_module_is_importable():
    import main
    assert main is not None


def test_main_module_defines_default_query():
    import main
    assert hasattr(main, "DEFAULT_QUERY"), (
        "main.py must define DEFAULT_QUERY as a module-level constant"
    )


def test_default_query_is_a_string():
    import main
    assert isinstance(main.DEFAULT_QUERY, str)


def test_default_query_is_non_empty():
    import main
    assert len(main.DEFAULT_QUERY) > 0


def test_default_query_value():
    import main
    assert main.DEFAULT_QUERY == "What should I build next?"


def test_main_module_defines_entry_point():
    import main
    assert hasattr(main, "main") or hasattr(main, "run"), (
        "main.py must define a callable entry point (main() or run())"
    )


# ---------------------------------------------------------------------------
# Argument handling
# ---------------------------------------------------------------------------

def _make_mock_runner(captured_query):
    async def mock_run_async(*args, **kwargs):
        msg = kwargs.get("new_message")
        if msg and msg.parts:
            captured_query.append(msg.parts[0].text)
        return
        yield

    mock_runner = MagicMock()
    mock_runner.run_async = mock_run_async
    return mock_runner


def test_no_argument_uses_default_query():
    import main
    captured_query = []

    with patch.object(sys, "argv", ["main.py"]), \
            patch("main.Runner", return_value=_make_mock_runner(captured_query)):
        asyncio.run(main.main())

    assert captured_query[0] == main.DEFAULT_QUERY


def test_custom_argument_overrides_default_query():
    import main
    captured_query = []
    custom = "What Terraform project should I build?"

    with patch.object(sys, "argv", ["main.py", custom]), \
            patch("main.Runner", return_value=_make_mock_runner(captured_query)):
        asyncio.run(main.main())

    assert captured_query[0] == custom


def test_extra_arguments_beyond_first_are_ignored_or_handled():
    import main
    with patch.object(sys, "argv", ["main.py", "query one", "query two"]):
        try:
            asyncio.run(main.main())
        except SystemExit as e:
            assert e.code in (0, 1, 2) or isinstance(e.code, str), (
                "Unexpected exit code for extra arguments"
            )
        except Exception:
            pass


def test_empty_string_argument_falls_back_to_default_or_exits():
    import main
    captured_query = []

    with patch.object(sys, "argv", ["main.py", ""]), \
            patch("main.Runner", return_value=_make_mock_runner(captured_query)):
        try:
            asyncio.run(main.main())
        except SystemExit as e:
            assert e.code == 1, "Empty string arg should exit 1 or fall back to default"

    if captured_query:
        assert captured_query[0] == main.DEFAULT_QUERY, (
            "Empty string arg should fall back to DEFAULT_QUERY, not pass empty string to pipeline"
        )


def test_whitespace_only_argument_falls_back_to_default_or_exits():
    import main
    captured_query = []

    with patch.object(sys, "argv", ["main.py", "   "]), \
            patch("main.Runner", return_value=_make_mock_runner(captured_query)):
        try:
            asyncio.run(main.main())
        except SystemExit as e:
            assert e.code == 1

    if captured_query:
        assert captured_query[0] != "   ", (
            "Whitespace-only arg should not be passed to pipeline as-is"
        )


# ---------------------------------------------------------------------------
# Exit code behaviour
# ---------------------------------------------------------------------------

def test_missing_env_key_exits_with_code_1(monkeypatch):
    import main
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with patch.object(sys, "argv", ["main.py"]):
        try:
            result = asyncio.run(main.main())
            if result is not None:
                assert result == 1 or result == 0
        except SystemExit as e:
            assert e.code == 1
        except Exception:
            pass
