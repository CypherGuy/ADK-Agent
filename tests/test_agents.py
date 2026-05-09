"""
Phase 4 integration tests for RepoAnalysisAgent and DigestReaderAgent.

Gemini LLM calls are patched so no live API calls are made.
The InMemoryRunner, tool dispatch, and agent logic all execute for real.
"""

import json
import re
import pytest
from unittest.mock import patch
from pathlib import Path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _valid_repo_json():
    return json.dumps([
        {"repo": "my-app", "technologies": ["Python", "FastAPI"], "last_used": "2026-05-01"},
        {"repo": "infra", "technologies": ["Terraform"], "last_used": "2026-04-20"},
    ])


def _valid_digest_json():
    return json.dumps([
        {"topic": "FastAPI", "summary": "FastAPI 0.112 released with async improvements.", "date": "2026-03-15"},
        {"topic": "Rust", "summary": "Rust 2026 edition roadmap published.", "date": "2026-02-10"},
    ])


# ---------------------------------------------------------------------------
# LLM mock helper
# ---------------------------------------------------------------------------

async def _mock_generate(mock_text):
    from google.adk.models.llm_response import LlmResponse
    from google.genai import types as genai_types

    async def _inner(*args, **kwargs):
        yield LlmResponse(
            content=genai_types.Content(
                role="model",
                parts=[genai_types.Part(text=mock_text)],
            ),
            turn_complete=True,
        )

    return _inner


def _run_agent(agent, user_message: str, mock_text: str) -> str:
    import asyncio
    from google.adk.runners import InMemoryRunner
    from google.genai import types as genai_types
    from google.adk.models.llm_response import LlmResponse

    async def _mock_generate_inner(*args, **kwargs):
        yield LlmResponse(
            content=genai_types.Content(
                role="model",
                parts=[genai_types.Part(text=mock_text)],
            ),
            turn_complete=True,
        )

    with patch(
        "google.adk.models.google_llm.Gemini.generate_content_async",
        side_effect=_mock_generate_inner,
    ):
        runner = InMemoryRunner(agent=agent)
        session = asyncio.run(runner.session_service.create_session(
            app_name=runner.app_name, user_id="test-user"
        ))
        final_text = None
        for event in runner.run(
            user_id="test-user",
            session_id=session.id,
            new_message=genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=user_message)],
            ),
        ):
            if event.is_final_response():
                final_text = event.content.parts[0].text
                break
    return final_text


# ---------------------------------------------------------------------------
# RepoAnalysisAgent — configuration
# ---------------------------------------------------------------------------

class TestRepoAnalysisAgentConfiguration:
    def test_module_exports_repo_analysis_agent(self):
        from agents.repo_analysis import repo_analysis_agent
        assert repo_analysis_agent is not None

    def test_repo_analysis_agent_is_llm_agent(self):
        from agents.repo_analysis import repo_analysis_agent
        from google.adk.agents import LlmAgent
        assert isinstance(repo_analysis_agent, LlmAgent)

    def test_repo_analysis_agent_uses_gemini_model(self):
        from agents.repo_analysis import repo_analysis_agent
        assert "gemini" in str(repo_analysis_agent.model).lower()

    def test_repo_analysis_agent_has_list_repos_tool(self):
        from agents.repo_analysis import repo_analysis_agent
        from agents.tools.repo_tools import list_repos
        tool_fns = [t.func if hasattr(t, "func") else t for t in repo_analysis_agent.tools]
        assert list_repos in tool_fns

    def test_repo_analysis_agent_has_read_git_log_tool(self):
        from agents.repo_analysis import repo_analysis_agent
        from agents.tools.repo_tools import read_git_log
        tool_fns = [t.func if hasattr(t, "func") else t for t in repo_analysis_agent.tools]
        assert read_git_log in tool_fns

    def test_repo_analysis_agent_has_read_dependencies_tool(self):
        from agents.repo_analysis import repo_analysis_agent
        from agents.tools.repo_tools import read_dependencies
        tool_fns = [t.func if hasattr(t, "func") else t for t in repo_analysis_agent.tools]
        assert read_dependencies in tool_fns

    def test_repo_analysis_agent_has_exactly_three_tools(self):
        from agents.repo_analysis import repo_analysis_agent
        assert len(repo_analysis_agent.tools) == 3

    def test_repo_analysis_agent_has_a_name(self):
        from agents.repo_analysis import repo_analysis_agent
        assert repo_analysis_agent.name and len(repo_analysis_agent.name) > 0

    def test_repo_analysis_agent_name_is_correct_value(self):
        from agents.repo_analysis import repo_analysis_agent
        assert repo_analysis_agent.name == "repo_analysis_agent"

    def test_repo_analysis_agent_has_description(self):
        from agents.repo_analysis import repo_analysis_agent
        assert repo_analysis_agent.description and len(repo_analysis_agent.description) > 0, (
            "repo_analysis_agent must have a description — ADK uses this for multi-agent routing"
        )

    def test_repo_analysis_agent_system_prompt_mentions_repo_field(self):
        from agents.repo_analysis import repo_analysis_agent
        prompt = repo_analysis_agent.instruction or ""
        assert "repo" in prompt.lower()

    def test_repo_analysis_agent_system_prompt_mentions_technologies_field(self):
        from agents.repo_analysis import repo_analysis_agent
        prompt = repo_analysis_agent.instruction or ""
        assert "technolog" in prompt.lower()

    def test_repo_analysis_agent_system_prompt_mentions_last_used_field(self):
        from agents.repo_analysis import repo_analysis_agent
        prompt = repo_analysis_agent.instruction or ""
        assert "last_used" in prompt.lower() or "last used" in prompt.lower()


# ---------------------------------------------------------------------------
# DigestReaderAgent — configuration
# ---------------------------------------------------------------------------

class TestDigestReaderAgentConfiguration:
    def test_module_exports_digest_reader_agent(self):
        from agents.digest_reader import digest_reader_agent
        assert digest_reader_agent is not None

    def test_digest_reader_agent_is_llm_agent(self):
        from agents.digest_reader import digest_reader_agent
        from google.adk.agents import LlmAgent
        assert isinstance(digest_reader_agent, LlmAgent)

    def test_digest_reader_agent_uses_gemini_model(self):
        from agents.digest_reader import digest_reader_agent
        assert "gemini" in str(digest_reader_agent.model).lower()

    def test_digest_reader_agent_has_list_digest_files_tool(self):
        from agents.digest_reader import digest_reader_agent
        from agents.tools.digest_tools import list_digest_files
        tool_fns = [t.func if hasattr(t, "func") else t for t in digest_reader_agent.tools]
        assert list_digest_files in tool_fns

    def test_digest_reader_agent_has_read_digest_tool(self):
        from agents.digest_reader import digest_reader_agent
        from agents.tools.digest_tools import read_digest
        tool_fns = [t.func if hasattr(t, "func") else t for t in digest_reader_agent.tools]
        assert read_digest in tool_fns

    def test_digest_reader_agent_has_exactly_two_tools(self):
        from agents.digest_reader import digest_reader_agent
        assert len(digest_reader_agent.tools) == 2

    def test_digest_reader_agent_has_a_name(self):
        from agents.digest_reader import digest_reader_agent
        assert digest_reader_agent.name and len(digest_reader_agent.name) > 0

    def test_digest_reader_agent_name_is_correct_value(self):
        from agents.digest_reader import digest_reader_agent
        assert digest_reader_agent.name == "digest_reader"

    def test_digest_reader_agent_has_description(self):
        from agents.digest_reader import digest_reader_agent
        assert digest_reader_agent.description and len(digest_reader_agent.description) > 0, (
            "digest_reader_agent must have a description — ADK uses this for multi-agent routing"
        )

    def test_digest_reader_agent_system_prompt_mentions_json(self):
        from agents.digest_reader import digest_reader_agent
        prompt = digest_reader_agent.instruction or ""
        assert "json" in prompt.lower()

    def test_digest_reader_agent_system_prompt_mentions_topic_field(self):
        from agents.digest_reader import digest_reader_agent
        prompt = digest_reader_agent.instruction or ""
        assert "topic" in prompt.lower()

    def test_digest_reader_agent_system_prompt_mentions_summary_field(self):
        from agents.digest_reader import digest_reader_agent
        prompt = digest_reader_agent.instruction or ""
        assert "summary" in prompt.lower()

    def test_digest_reader_agent_system_prompt_mentions_date_field(self):
        from agents.digest_reader import digest_reader_agent
        prompt = digest_reader_agent.instruction or ""
        assert "date" in prompt.lower()


# ---------------------------------------------------------------------------
# RepoAnalysisAgent — output schema (mocked LLM)
# ---------------------------------------------------------------------------

class TestRepoAnalysisAgentOutputSchema:
    def _run(self, mock_text: str) -> str:
        from agents.repo_analysis import repo_analysis_agent
        return _run_agent(repo_analysis_agent, "Analyse all my repos and return a summary.", mock_text)

    def test_output_is_valid_json(self):
        parsed = json.loads(self._run(_valid_repo_json()))
        assert isinstance(parsed, list)

    def test_output_is_a_list(self):
        assert isinstance(json.loads(self._run(_valid_repo_json())), list)

    def test_each_item_has_repo_key(self):
        for item in json.loads(self._run(_valid_repo_json())):
            assert "repo" in item

    def test_each_item_has_technologies_key(self):
        for item in json.loads(self._run(_valid_repo_json())):
            assert "technologies" in item

    def test_each_item_has_last_used_key(self):
        for item in json.loads(self._run(_valid_repo_json())):
            assert "last_used" in item

    def test_repo_field_is_string(self):
        for item in json.loads(self._run(_valid_repo_json())):
            assert isinstance(item["repo"], str)

    def test_technologies_field_is_list(self):
        for item in json.loads(self._run(_valid_repo_json())):
            assert isinstance(item["technologies"], list)

    def test_technologies_entries_are_strings(self):
        for item in json.loads(self._run(_valid_repo_json())):
            for tech in item["technologies"]:
                assert isinstance(tech, str)

    def test_last_used_field_is_string(self):
        for item in json.loads(self._run(_valid_repo_json())):
            assert isinstance(item["last_used"], str)

    def test_repo_names_are_non_empty(self):
        for item in json.loads(self._run(_valid_repo_json())):
            assert len(item["repo"]) > 0

    def test_empty_result_is_still_a_list(self):
        parsed = json.loads(self._run(json.dumps([])))
        assert isinstance(parsed, list) and len(parsed) == 0

    def test_no_recent_commits_key_in_output(self):
        for item in json.loads(self._run(_valid_repo_json())):
            assert "recent_commits" not in item, (
                "recent_commits is an internal tool field and must not appear in the agent's final output"
            )

    def test_last_used_matches_iso8601_date_pattern(self):
        for item in json.loads(self._run(_valid_repo_json())):
            assert re.match(r"^\d{4}-\d{2}-\d{2}$", item["last_used"]), (
                f"last_used must be YYYY-MM-DD, got: {item['last_used']!r}"
            )


# ---------------------------------------------------------------------------
# DigestReaderAgent — output schema (mocked LLM)
# ---------------------------------------------------------------------------

class TestDigestReaderAgentOutputSchema:
    def _run(self, mock_text: str) -> str:
        from agents.digest_reader import digest_reader_agent
        return _run_agent(digest_reader_agent, "Summarise the trending topics from my digests.", mock_text)

    def test_output_is_valid_json(self):
        assert isinstance(json.loads(self._run(_valid_digest_json())), list)

    def test_output_is_a_list(self):
        assert isinstance(json.loads(self._run(_valid_digest_json())), list)

    def test_each_item_has_topic_key(self):
        for item in json.loads(self._run(_valid_digest_json())):
            assert "topic" in item

    def test_each_item_has_summary_key(self):
        for item in json.loads(self._run(_valid_digest_json())):
            assert "summary" in item

    def test_each_item_has_date_key(self):
        for item in json.loads(self._run(_valid_digest_json())):
            assert "date" in item

    def test_topic_field_is_string(self):
        for item in json.loads(self._run(_valid_digest_json())):
            assert isinstance(item["topic"], str)

    def test_summary_field_is_string(self):
        for item in json.loads(self._run(_valid_digest_json())):
            assert isinstance(item["summary"], str)

    def test_date_field_is_string(self):
        for item in json.loads(self._run(_valid_digest_json())):
            assert isinstance(item["date"], str)

    def test_topic_field_is_non_empty(self):
        for item in json.loads(self._run(_valid_digest_json())):
            assert len(item["topic"]) > 0

    def test_summary_field_is_non_empty(self):
        for item in json.loads(self._run(_valid_digest_json())):
            assert len(item["summary"]) > 0

    def test_date_field_is_non_empty(self):
        for item in json.loads(self._run(_valid_digest_json())):
            assert len(item["date"]) > 0

    def test_empty_result_is_still_a_list(self):
        parsed = json.loads(self._run(json.dumps([])))
        assert isinstance(parsed, list) and len(parsed) == 0

    def test_no_mentions_field_in_output(self):
        for item in json.loads(self._run(_valid_digest_json())):
            assert "mentions" not in item, (
                "mentions is not part of the DigestReaderAgent output schema"
            )

    def test_date_matches_iso8601_date_pattern(self):
        for item in json.loads(self._run(_valid_digest_json())):
            assert re.match(r"^\d{4}-\d{2}-\d{2}$", item["date"]), (
                f"date must be YYYY-MM-DD, got: {item['date']!r}"
            )


# ---------------------------------------------------------------------------
# RepoAnalysisAgent — edge cases
# ---------------------------------------------------------------------------

class TestRepoAnalysisAgentEdgeCases:
    def _run(self, mock_text: str) -> str:
        from agents.repo_analysis import repo_analysis_agent
        return _run_agent(repo_analysis_agent, "Analyse all my repos.", mock_text)

    def test_single_repo_result_is_a_list(self):
        parsed = json.loads(self._run(json.dumps(
            [{"repo": "solo", "technologies": ["Go"], "last_used": "2026-05-01"}]
        )))
        assert isinstance(parsed, list) and len(parsed) == 1

    def test_technologies_list_can_be_empty(self):
        parsed = json.loads(self._run(json.dumps(
            [{"repo": "mystery", "technologies": [], "last_used": "2026-04-01"}]
        )))
        assert parsed[0]["technologies"] == []

    def test_technologies_list_can_contain_multiple_entries(self):
        parsed = json.loads(self._run(json.dumps([{
            "repo": "polyglot",
            "technologies": ["Python", "TypeScript", "Bash", "SQL"],
            "last_used": "2026-03-01",
        }])))
        assert len(parsed[0]["technologies"]) == 4

    def test_multiple_repos_all_have_required_keys(self):
        data = [
            {"repo": "alpha", "technologies": ["Python"], "last_used": "2026-05-01"},
            {"repo": "beta", "technologies": ["Rust"], "last_used": "2026-04-15"},
            {"repo": "gamma", "technologies": [], "last_used": "2026-03-10"},
        ]
        parsed = json.loads(self._run(json.dumps(data)))
        for item in parsed:
            assert "repo" in item and "technologies" in item and "last_used" in item


# ---------------------------------------------------------------------------
# DigestReaderAgent — edge cases
# ---------------------------------------------------------------------------

class TestDigestReaderAgentEdgeCases:
    def _run(self, mock_text: str) -> str:
        from agents.digest_reader import digest_reader_agent
        return _run_agent(digest_reader_agent, "Summarise trending topics.", mock_text)

    def test_single_digest_entry_is_a_list(self):
        parsed = json.loads(self._run(json.dumps(
            [{"topic": "Rust", "summary": "Rust 2026 edition roadmap published.", "date": "2026-02-10"}]
        )))
        assert isinstance(parsed, list) and len(parsed) == 1

    def test_multiple_entries_all_have_required_keys(self):
        data = [
            {"topic": "FastAPI", "summary": "FastAPI 0.112 released.", "date": "2026-03-15"},
            {"topic": "Rust", "summary": "Rust 2026 edition roadmap published.", "date": "2026-02-10"},
            {"topic": "OpenTofu", "summary": "OpenTofu 1.9 released.", "date": "2026-01-05"},
        ]
        parsed = json.loads(self._run(json.dumps(data)))
        for item in parsed:
            assert "topic" in item and "summary" in item and "date" in item

    def test_no_mentions_field_in_edge_case_output(self):
        data = [
            {"topic": "FastAPI", "summary": "FastAPI 0.112 released.", "date": "2026-03-15"},
        ]
        parsed = json.loads(self._run(json.dumps(data)))
        for item in parsed:
            assert "mentions" not in item


# ---------------------------------------------------------------------------
# agents/agent.py — root_agent entry point (required by `adk web`)
# ---------------------------------------------------------------------------

class TestRootAgentEntryPoint:
    """
    `adk web` discovers agents by importing `agents.agent` and reading a
    module-level `root_agent` variable. These tests verify that contract so
    the web UI can boot without a 500 error.
    """

    def test_agents_agent_module_is_importable(self):
        import importlib
        assert importlib.import_module("agents.agent") is not None

    def test_agents_module_exposes_root_agent(self):
        import agents.agent as agent_mod
        assert hasattr(agent_mod, "root_agent"), (
            "agents/agent.py must expose a module-level 'root_agent' variable "
            "so that `adk web` can discover it"
        )

    def test_root_agent_is_not_none(self):
        import agents.agent as agent_mod
        assert agent_mod.root_agent is not None

    def test_root_agent_is_an_adk_base_agent(self):
        import agents.agent as agent_mod
        from google.adk.agents import BaseAgent
        assert isinstance(agent_mod.root_agent, BaseAgent)

    def test_root_agent_has_a_name(self):
        import agents.agent as agent_mod
        assert agent_mod.root_agent.name and len(agent_mod.root_agent.name) > 0

    def test_root_agent_incorporates_repo_analysis_agent(self):
        import agents.agent as agent_mod
        from agents.repo_analysis import repo_analysis_agent

        def _find(agent, target, visited=None):
            if visited is None:
                visited = set()
            if id(agent) in visited:
                return False
            visited.add(id(agent))
            if agent is target:
                return True
            return any(_find(sub, target, visited) for sub in (getattr(agent, "sub_agents", None) or []))

        assert _find(agent_mod.root_agent, repo_analysis_agent), (
            "root_agent must include repo_analysis_agent in its sub-agent graph"
        )

    def test_agent_py_does_not_define_agents_inline(self):
        import agents.agent as agent_mod
        from google.adk.agents import LlmAgent
        inline_agents = [
            name for name, val in vars(agent_mod).items()
            if isinstance(val, LlmAgent) and name != "root_agent"
        ]
        assert inline_agents == [], (
            f"agents/agent.py must not define LlmAgents inline — found: {inline_agents}. "
            "Each agent belongs in its own file per the spec."
        )

    def test_root_agent_incorporates_digest_reader_agent(self):
        import agents.agent as agent_mod
        from agents.digest_reader import digest_reader_agent

        def _find(agent, target, visited=None):
            if visited is None:
                visited = set()
            if id(agent) in visited:
                return False
            visited.add(id(agent))
            if agent is target:
                return True
            return any(_find(sub, target, visited) for sub in (getattr(agent, "sub_agents", None) or []))

        assert _find(agent_mod.root_agent, digest_reader_agent), (
            "root_agent must include digest_reader_agent in its sub-agent graph"
        )
