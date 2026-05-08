import pytest
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"
FAKE_DIGESTS = FIXTURES / "fake_digests"

# ---------------------------------------------------------------------------
# list_digest_files
# ---------------------------------------------------------------------------


def test_list_digest_files_returns_list():
    from tools.digest_tools import list_digest_files
    result = list_digest_files(str(FAKE_DIGESTS))
    assert isinstance(result, list)


def test_list_digest_files_returns_only_txt_paths():
    from tools.digest_tools import list_digest_files
    result = list_digest_files(str(FAKE_DIGESTS))
    for path in result:
        assert path.endswith(".txt")


def test_list_digest_files_returns_all_three_fixtures():
    from tools.digest_tools import list_digest_files
    result = list_digest_files(str(FAKE_DIGESTS))
    assert len(result) == 3


def test_list_digest_files_sorted_descending_by_filename_date():
    from tools.digest_tools import list_digest_files
    result = list_digest_files(str(FAKE_DIGESTS))
    filenames = [Path(p).name for p in result]
    assert filenames == sorted(filenames, reverse=True)


def test_list_digest_files_first_entry_is_most_recent():
    from tools.digest_tools import list_digest_files
    result = list_digest_files(str(FAKE_DIGESTS))
    assert Path(result[0]).name == "2026-03-15.txt"


def test_list_digest_files_last_entry_is_oldest():
    from tools.digest_tools import list_digest_files
    result = list_digest_files(str(FAKE_DIGESTS))
    assert Path(result[-1]).name == "2026-01-05.txt"


def test_list_digest_files_returns_absolute_paths():
    from tools.digest_tools import list_digest_files
    result = list_digest_files(str(FAKE_DIGESTS))
    for path in result:
        assert Path(path).is_absolute()


def test_list_digest_files_returns_absolute_paths_when_given_relative_path(tmp_path):
    import os
    from tools.digest_tools import list_digest_files
    (tmp_path / "2026-01-01.txt").write_text("hello")
    rel_path = os.path.relpath(str(tmp_path))
    result = list_digest_files(rel_path)
    for path in result:
        assert Path(path).is_absolute()


def test_list_digest_files_empty_directory_returns_empty_list(tmp_path):
    from tools.digest_tools import list_digest_files
    result = list_digest_files(str(tmp_path))
    assert result == []


def test_list_digest_files_ignores_non_txt_files(tmp_path):
    from tools.digest_tools import list_digest_files
    (tmp_path / "2026-01-01.txt").write_text("hello")
    (tmp_path / "2026-01-02.md").write_text("ignored")
    (tmp_path / "2026-01-03.json").write_text("{}")
    result = list_digest_files(str(tmp_path))
    assert len(result) == 1
    assert result[0].endswith(".txt")


def test_list_digest_files_missing_directory_raises():
    from tools.digest_tools import list_digest_files
    with pytest.raises(Exception):
        list_digest_files("/nonexistent/path/that/does/not/exist")


# ---------------------------------------------------------------------------
# read_digest
# ---------------------------------------------------------------------------


def test_read_digest_returns_string():
    from tools.digest_tools import read_digest
    path = str(FAKE_DIGESTS / "2026-03-15.txt")
    result = read_digest(path)
    assert isinstance(result, str)


def test_read_digest_fastapi_file_contains_fastapi():
    from tools.digest_tools import read_digest
    path = str(FAKE_DIGESTS / "2026-03-15.txt")
    result = read_digest(path)
    assert "FastAPI" in result


def test_read_digest_rust_file_contains_rust():
    from tools.digest_tools import read_digest
    path = str(FAKE_DIGESTS / "2026-02-10.txt")
    result = read_digest(path)
    assert "Rust" in result


def test_read_digest_opentofu_file_contains_opentofu():
    from tools.digest_tools import read_digest
    path = str(FAKE_DIGESTS / "2026-01-05.txt")
    result = read_digest(path)
    assert "OpenTofu" in result


def test_read_digest_returns_full_content(tmp_path):
    from tools.digest_tools import read_digest
    content = "line one\nline two\nline three"
    digest_file = tmp_path / "2026-06-01.txt"
    digest_file.write_text(content)
    result = read_digest(str(digest_file))
    assert result == content


def test_read_digest_returns_raw_text_not_parsed():
    from tools.digest_tools import read_digest
    path = str(FAKE_DIGESTS / "2026-03-15.txt")
    result = read_digest(path)
    assert isinstance(result, str)
    assert not isinstance(result, (list, dict))


def test_read_digest_missing_file_raises():
    from tools.digest_tools import read_digest
    with pytest.raises(Exception):
        read_digest("/nonexistent/path/digest.txt")
