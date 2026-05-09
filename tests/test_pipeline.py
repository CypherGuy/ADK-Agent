import pytest
from pathlib import Path

ROOT = Path(__file__).parent.parent

REQUIRED = [
    ROOT / "main.py",
    ROOT / "config.py",
    ROOT / ".env.example",
    ROOT / "agents" / "agent.py",
    ROOT / "agents" / "coordinator.py",
    ROOT / "agents" / "repo_analysis.py",
    ROOT / "agents" / "digest_reader.py",
    ROOT / "agents" / "suggestion.py",
    ROOT / "agents" / "pipeline.py",
    ROOT / "agents" / "tools" / "repo_tools.py",
    ROOT / "agents" / "tools" / "digest_tools.py",
    ROOT / "tests" / "fixtures" / "fake_repo",
    ROOT / "tests" / "fixtures" / "fake_digests",
    ROOT / "tests" / "test_repo_tools.py",
    ROOT / "tests" / "test_digest_tools.py",
    ROOT / "tests" / "test_agents.py",
    ROOT / "tests" / "test_pipeline.py",
]

FORBIDDEN = [
    ROOT / "pipeline.py",
    ROOT / "agents" / "parallel.py",
    ROOT / "agents" / "sequential.py",
]


@pytest.mark.parametrize("path", REQUIRED, ids=lambda p: str(p.relative_to(ROOT)))
def test_required_path_exists(path):
    assert path.exists()


@pytest.mark.parametrize("path", FORBIDDEN, ids=lambda p: str(p.relative_to(ROOT)))
def test_forbidden_path_absent(path):
    assert not path.exists()
