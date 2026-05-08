import pytest
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"
FAKE_REPO = FIXTURES / "fake_repo"
FAKE_REPO_NO_MANIFEST = FIXTURES / "fake_repo_no_manifest"
FAKE_REPO_LONG = FIXTURES / "fake_repo_long"
FAKE_REPO_NO_EXT = FIXTURES / "fake_repo_no_ext"

# ---------------------------------------------------------------------------
# list_repos
# ---------------------------------------------------------------------------


def test_list_repos_returns_subdirectory_names():
    from tools.repo_tools import list_repos
    repos = list_repos(str(FIXTURES))
    assert "fake_repo" in repos
    assert "fake_repo_no_manifest" in repos


def test_list_repos_returns_only_directories():
    from tools.repo_tools import list_repos
    repos = list_repos(str(FIXTURES))
    for name in repos:
        assert (FIXTURES / name).is_dir()


def test_list_repos_missing_path_raises():
    from tools.repo_tools import list_repos
    with pytest.raises(Exception):
        list_repos("/nonexistent/path/that/does/not/exist")


# ---------------------------------------------------------------------------
# read_git_log
# ---------------------------------------------------------------------------

def test_read_git_log_returns_dict_with_expected_keys():
    from tools.repo_tools import read_git_log
    result = read_git_log(str(FAKE_REPO))
    assert "last_commit_date" in result
    assert "recent_commits" in result


def test_read_git_log_returns_up_to_ten_commits():
    from tools.repo_tools import read_git_log
    result = read_git_log(str(FAKE_REPO))
    assert len(result["recent_commits"]) <= 10


def test_read_git_log_recent_commits_are_strings():
    from tools.repo_tools import read_git_log
    result = read_git_log(str(FAKE_REPO))
    for msg in result["recent_commits"]:
        assert isinstance(msg, str)


def test_read_git_log_contains_known_commit_message():
    from tools.repo_tools import read_git_log
    result = read_git_log(str(FAKE_REPO))
    combined = " ".join(result["recent_commits"])
    assert "authentication" in combined or "null pointer" in combined or "dependency parser" in combined


def test_read_git_log_last_commit_date_is_string():
    from tools.repo_tools import read_git_log
    result = read_git_log(str(FAKE_REPO))
    assert isinstance(result["last_commit_date"], str)
    assert result["last_commit_date"] != ""


def test_read_git_log_last_commit_date_includes_time_and_timezone():
    from tools.repo_tools import read_git_log
    result = read_git_log(str(FAKE_REPO))
    # e.g. "2026-05-07 14:23:11 +0000" — must have time and offset
    parts = result["last_commit_date"].split()
    assert len(parts) == 3, f"Expected 'YYYY-MM-DD HH:MM:SS +ZZZZ', got: {result['last_commit_date']!r}"
    assert ":" in parts[1], "Second part should be a time (HH:MM:SS)"
    assert parts[2].startswith(("+", "-")), "Third part should be a timezone offset"


def test_read_git_log_caps_at_ten_commits():
    from tools.repo_tools import read_git_log
    result = read_git_log(str(FAKE_REPO_LONG))
    assert len(result["recent_commits"]) == 10


# ---------------------------------------------------------------------------
# read_dependencies — package.json path
# ---------------------------------------------------------------------------

def test_read_dependencies_from_package_json():
    from tools.repo_tools import read_dependencies
    deps = read_dependencies(str(FAKE_REPO))
    assert "express" in deps
    assert "axios" in deps
    assert "lodash" in deps


def test_read_dependencies_returns_list():
    from tools.repo_tools import read_dependencies
    deps = read_dependencies(str(FAKE_REPO))
    assert isinstance(deps, list)


# ---------------------------------------------------------------------------
# read_dependencies — pyproject.toml path (remove package.json first)
# ---------------------------------------------------------------------------

def test_read_dependencies_from_pyproject_toml(tmp_path):
    import shutil
    from tools.repo_tools import read_dependencies

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

def test_read_dependencies_falls_back_to_extension_inference():
    from tools.repo_tools import read_dependencies
    deps = read_dependencies(str(FAKE_REPO_NO_MANIFEST))
    assert isinstance(deps, list)
    # Should infer Python from .py files; result is language labels not package names
    combined = " ".join(deps).lower()
    assert "python" in combined


def test_read_dependencies_fallback_does_not_raise_on_empty_repo(tmp_path):
    from tools.repo_tools import read_dependencies
    empty_repo = tmp_path / "empty"
    empty_repo.mkdir()
    deps = read_dependencies(str(empty_repo))
    assert isinstance(deps, list)


def test_read_dependencies_fallback_does_not_raise_on_extension_less_files():
    from tools.repo_tools import read_dependencies
    deps = read_dependencies(str(FAKE_REPO_NO_EXT))
    assert isinstance(deps, list)
