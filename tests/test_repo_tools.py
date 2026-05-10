import datetime
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

FIXTURES = Path(__file__).parent / "fixtures"
FAKE_REPO = FIXTURES / "fake_repo"
FAKE_REPO_NO_MANIFEST = FIXTURES / "fake_repo_no_manifest"
FAKE_REPO_LONG = FIXTURES / "fake_repo_long"
FAKE_REPO_NO_EXT = FIXTURES / "fake_repo_no_ext"


def _git_log_output_for_date(date: datetime.date) -> bytes:
    """Build fake git log stdout matching --pretty=format:%at (unix timestamp)."""
    dt = datetime.datetime.combine(date, datetime.time(
        12, 0, 0), tzinfo=datetime.timezone.utc)
    return str(int(dt.timestamp())).encode()


# ---------------------------------------------------------------------------
# list_repos — staleness filtering
# ---------------------------------------------------------------------------


def test_list_repos_excludes_recently_touched_repos(tmp_path):
    import agents.tools.repo_tools as mod
    from agents.tools.repo_tools import list_repos

    recent_date = datetime.date.today() - datetime.timedelta(days=10)
    (tmp_path / "recent_repo").mkdir()

    with patch.object(mod.config, "REPO_STALENESS_DAYS", 180), \
            patch.object(mod.config, "EXCLUDED_REPOS", []), \
            patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout=_git_log_output_for_date(recent_date), returncode=0
        )
        result = list_repos(str(tmp_path))

    assert "recent_repo" not in result


def test_list_repos_includes_stale_repos(tmp_path):
    import agents.tools.repo_tools as mod
    from agents.tools.repo_tools import list_repos

    stale_date = datetime.date.today() - datetime.timedelta(days=365)
    (tmp_path / "stale_repo").mkdir()

    with patch.object(mod.config, "REPO_STALENESS_DAYS", 180), \
            patch.object(mod.config, "EXCLUDED_REPOS", []), \
            patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout=_git_log_output_for_date(stale_date), returncode=0
        )
        result = list_repos(str(tmp_path))

    assert "stale_repo" in result


def test_list_repos_returns_empty_when_all_repos_are_recent(tmp_path):
    import agents.tools.repo_tools as mod
    from agents.tools.repo_tools import list_repos

    recent_date = datetime.date.today() - datetime.timedelta(days=5)
    (tmp_path / "repo_a").mkdir()
    (tmp_path / "repo_b").mkdir()

    with patch.object(mod.config, "REPO_STALENESS_DAYS", 180), \
            patch.object(mod.config, "EXCLUDED_REPOS", []), \
            patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout=_git_log_output_for_date(recent_date), returncode=0
        )
        result = list_repos(str(tmp_path))

    assert result == []


def test_list_repos_excludes_repo_committed_23_hours_ago_with_6_day_threshold(tmp_path):
    import agents.tools.repo_tools as mod
    from agents.tools.repo_tools import list_repos

    twenty_three_hours_ago = (
        datetime.datetime.now() - datetime.timedelta(hours=23)).date()
    (tmp_path / "nearly_day_old_repo").mkdir()

    with patch.object(mod.config, "REPO_STALENESS_DAYS", 6), \
            patch.object(mod.config, "EXCLUDED_REPOS", []), \
            patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout=_git_log_output_for_date(twenty_three_hours_ago), returncode=0
        )
        result = list_repos(str(tmp_path))

    assert "nearly_day_old_repo" not in result, (
        "23 hours is less than 6 days — repo must be excluded regardless of the raw hour count"
    )


def test_list_repos_excludes_repos_in_excluded_repos_config(tmp_path):
    import agents.tools.repo_tools as mod
    from agents.tools.repo_tools import list_repos

    stale_date = datetime.date.today() - datetime.timedelta(days=365)
    (tmp_path / "excluded_repo").mkdir()

    with patch.object(mod.config, "REPO_STALENESS_DAYS", 180), \
            patch.object(mod.config, "EXCLUDED_REPOS", ["excluded_repo"]), \
            patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout=_git_log_output_for_date(stale_date), returncode=0
        )
        result = list_repos(str(tmp_path))

    assert "excluded_repo" not in result


def test_list_repos_skips_repos_with_no_git_history(tmp_path):
    import agents.tools.repo_tools as mod
    from agents.tools.repo_tools import list_repos

    (tmp_path / "no_git_repo").mkdir()

    with patch.object(mod.config, "REPO_STALENESS_DAYS", 180), \
            patch.object(mod.config, "EXCLUDED_REPOS", []), \
            patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=b"", returncode=128)
        result = list_repos(str(tmp_path))

    assert "no_git_repo" not in result


# ---------------------------------------------------------------------------
# list_repos — basic behaviour (pre-staleness-filter checks)
# ---------------------------------------------------------------------------


def test_list_repos_returns_only_directories():
    from agents.tools.repo_tools import list_repos
    repos = list_repos(str(FIXTURES))
    for name in repos:
        assert (FIXTURES / name).is_dir()


def test_list_repos_missing_path_raises():
    from agents.tools.repo_tools import list_repos
    with pytest.raises(Exception):
        list_repos("/nonexistent/path/that/does/not/exist")


# ---------------------------------------------------------------------------
# read_git_log
# ---------------------------------------------------------------------------

def test_read_git_log_returns_dict_with_expected_keys():
    from agents.tools.repo_tools import read_git_log
    result = read_git_log(str(FAKE_REPO))
    assert "last_commit_date" in result
    assert "recent_commits" in result


def test_read_git_log_returns_up_to_ten_commits():
    from agents.tools.repo_tools import read_git_log
    result = read_git_log(str(FAKE_REPO))
    assert len(result["recent_commits"]) <= 10


def test_read_git_log_recent_commits_are_strings():
    from agents.tools.repo_tools import read_git_log
    result = read_git_log(str(FAKE_REPO))
    for msg in result["recent_commits"]:
        assert isinstance(msg, str)


def test_read_git_log_contains_known_commit_message():
    from agents.tools.repo_tools import read_git_log
    fake_output = (
        b"commit abc123\n"
        b"Author: Dev <dev@example.com>\n"
        b"Date:   Thu May  1 12:00:00 2026 +0000\n"
        b"\n"
        b"    feat: add authentication support\n"
        b"\n"
        b"commit def456\n"
        b"Author: Dev <dev@example.com>\n"
        b"Date:   Wed Apr 30 09:00:00 2026 +0000\n"
        b"\n"
        b"    fix: resolve null pointer exception\n"
    )
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=fake_output, returncode=0)
        result = read_git_log(str(FAKE_REPO))
    combined = " ".join(result["recent_commits"])
    assert "authentication" in combined or "null pointer" in combined


def test_read_git_log_last_commit_date_is_string():
    from agents.tools.repo_tools import read_git_log
    result = read_git_log(str(FAKE_REPO))
    assert isinstance(result["last_commit_date"], str)
    assert result["last_commit_date"] != ""


def test_read_git_log_last_commit_date_is_iso8601():
    import re
    from agents.tools.repo_tools import read_git_log
    result = read_git_log(str(FAKE_REPO))
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", result["last_commit_date"]), (
        f"Expected ISO 8601 'YYYY-MM-DD' format, got: {result['last_commit_date']!r}"
    )


def test_read_git_log_caps_at_ten_commits():
    import agents.tools.repo_tools as repo_tools_mod
    from agents.tools.repo_tools import read_git_log

    commit_entry = (
        "commit {}\nAuthor: Dev <dev@example.com>\n"
        "Date:   Thu May  1 12:00:00 2026 +0000\n\n    feat: commit {{}}\n\n"
    ).format("a" * 40)
    twelve_commits = b"".join(
        commit_entry.format(i).encode()
        for i in range(1, 13)
    )
    with patch.object(repo_tools_mod.config, "REPOS_PATH", FIXTURES):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout=twelve_commits, returncode=0)
            result = read_git_log("fake_repo_long")
    assert len(result["recent_commits"]) <= 10


# ---------------------------------------------------------------------------
# read_dependencies — package.json path
# ---------------------------------------------------------------------------

def test_read_dependencies_from_package_json():
    from agents.tools.repo_tools import read_dependencies
    deps = read_dependencies(str(FAKE_REPO))
    assert "express" in deps
    assert "axios" in deps
    assert "lodash" in deps


def test_read_dependencies_returns_list():
    from agents.tools.repo_tools import read_dependencies
    deps = read_dependencies(str(FAKE_REPO))
    assert isinstance(deps, list)


def test_read_dependencies_package_json_without_dependencies_key_does_not_raise(tmp_path):
    import json
    from agents.tools.repo_tools import read_dependencies
    (tmp_path /
     "package.json").write_text(json.dumps({"name": "my-app", "version": "1.0.0"}))
    deps = read_dependencies(str(tmp_path))
    assert isinstance(deps, list)


# ---------------------------------------------------------------------------
# read_dependencies — pyproject.toml path (remove package.json first)
# ---------------------------------------------------------------------------

def test_read_dependencies_from_pyproject_toml(tmp_path):
    import shutil
    from agents.tools.repo_tools import read_dependencies

    # Copy fake_repo but drop package.json so pyproject.toml is used
    repo_copy = tmp_path / "py_only_repo"
    shutil.copytree(FAKE_REPO, repo_copy)
    (repo_copy / "package.json").unlink()

    deps = read_dependencies(str(repo_copy))
    assert "requests" in deps
    assert "rich" in deps
    assert "click" in deps


# ---------------------------------------------------------------------------
# read_dependencies — extension-inference fallback (no manifest files)
# ---------------------------------------------------------------------------

def test_read_dependencies_fallback_does_not_raise_on_empty_repo(tmp_path):
    from agents.tools.repo_tools import read_dependencies
    empty_repo = tmp_path / "empty"
    empty_repo.mkdir()
    deps = read_dependencies(str(empty_repo))
    assert isinstance(deps, list)


def test_read_dependencies_fallback_does_not_raise_on_extension_less_files():
    from agents.tools.repo_tools import read_dependencies
    deps = read_dependencies(str(FAKE_REPO_NO_EXT))
    assert isinstance(deps, list)
