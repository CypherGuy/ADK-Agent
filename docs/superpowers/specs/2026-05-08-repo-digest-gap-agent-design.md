# Design Spec: Repo & Digest Gap Detection Agent

**Date:** 2026-05-08
**Status:** Approved
**Language:** Python
**Framework:** Google ADK (Agent Development Kit)

---

## Problem

Kabir has ~39 personal repos spanning many technologies. Over time, skills and tools go unused while the broader ecosystem moves on. There is no mechanism to surface "you know X but haven't touched it in months, and the community is actively talking about it right now." DailyDigest already curates relevant tech news into local `.txt` files. This agent connects the two.

---

## Goal

A CLI tool that analyses your repos and your DailyDigest files, cross-references technologies you know against recency of use and current trends, and streams 3–5 concrete, personalised project suggestions.

---

## Architecture

### Agent Roles

| Agent | Model | Responsibility |
|---|---|---|
| `CoordinatorAgent` | Gemini 2.0 Flash | Entry point, receives user query, owns the pipeline |
| `RepoAnalysisAgent` | Gemma 3 (Ollama) | Scans repos, extracts tech stack + recency |
| `DigestReaderAgent` | Gemma 3 (Ollama) | Reads DailyDigest files, extracts trending topics |
| `SuggestionAgent` | Gemini 2.0 Flash | Cross-references both outputs, generates suggestions |

### Pipeline

```
CoordinatorAgent (Gemini)
  └── SequentialAgent
        ├── Phase 1 — ParallelAgent
        │     ├── RepoAnalysisAgent (Gemma)
        │     └── DigestReaderAgent (Gemma)
        └── Phase 2 — SuggestionAgent (Gemini)
```

Phase 1 runs in parallel (independent data sources). Phase 2 is sequential (depends on both Phase 1 outputs).

---

## Tools

### `repo_tools.py`

- `list_repos(repos_path: str) -> list[str]`
  Returns all subdirectory names under `REPOS_PATH`.

- `read_git_log(repo_path: str) -> dict`
  Returns last commit date and recent commit messages for a repo.

- `read_dependencies(repo_path: str) -> list[str]`
  Reads `package.json`, `pyproject.toml`, `requirements.txt`, or `go.mod` and returns library/framework names. Falls back to inferring language from file extensions in git log if no dependency file exists.

### `digest_tools.py`

- `list_digest_files(digest_path: str) -> list[str]`
  Returns paths to all `.txt` digest files, sorted by date descending.

- `read_digest(file_path: str) -> str`
  Returns the raw text content of a single digest file.

---

## Data Flow

1. User runs `python main.py` or `python main.py "what should I build this week?"`
2. `CoordinatorAgent` receives the query and starts the `SequentialAgent`
3. `ParallelAgent` fires `RepoAnalysisAgent` and `DigestReaderAgent` simultaneously
4. `RepoAnalysisAgent` returns structured list: `[{ repo, technologies[], last_used }]`
5. `DigestReaderAgent` returns structured list: `[{ topic, mentions, date }]`
6. `SuggestionAgent` receives both summaries in context (never raw files), cross-references them, and streams 3–5 suggestions to the terminal
7. Each suggestion includes: the underused technology, the relevant trend from the digest, and a concrete project idea

### Example output

```
→ You haven't used MySQL in 7 months.
  Your digest mentioned database change data capture (CDC) twice this week.
  Idea: build a lightweight CDC listener using MySQL binlog + Python.

→ You haven't touched Terraform in 4 months.
  Digest flagged OpenTofu 1.9 release last Tuesday.
  Idea: migrate your AWS infra project from Terraform to OpenTofu.
```

---

## Project Structure

```
ADK-Agent/
├── agents/
│   ├── coordinator.py
│   ├── repo_analysis.py
│   ├── digest_reader.py
│   └── suggestion.py
├── tools/
│   ├── repo_tools.py
│   └── digest_tools.py
├── pipeline.py
├── main.py
├── config.py
├── .env.example
├── .env                  # gitignored
├── requirements.txt
└── tests/
    ├── fixtures/
    │   ├── fake_repo/
    │   └── fake_digests/
    ├── test_tools.py
    ├── test_agents.py
    └── test_pipeline.py
```

---

## Configuration

All paths and keys in `.env`, gitignored. `.env.example` committed.

```
REPOS_PATH=/path/to/your/repos
DIGEST_PATH=/path/to/your/dailydigest/output
GEMINI_API_KEY=your_key_here
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3
DIGEST_LOOKBACK_DAYS=30
```

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Ollama not running | Fail fast: `"Ollama is not running. Start it with: ollama serve"` |
| Repo path not found | Skip repo, log warning, continue |
| No dependency file in repo | Fall back to inferring from file extensions |
| Digest directory empty/missing | SuggestionAgent runs on repo data only, notes gap in output |
| Gemini API failure | Surface error directly, no retry |

No silent failures. Every error produces a clear, actionable message.

---

## Testing

| Layer | What | How |
|---|---|---|
| Unit | `repo_tools`, `digest_tools` | Against `tests/fixtures/`, no API calls |
| Integration | Each agent | Mocked Ollama + Gemini responses |
| Smoke | Full pipeline | End-to-end against fixtures, confirms suggestions stream |

Framework: `pytest`

---

## Out of Scope (Phase 1)

- Persistent memory / session state (planned for Phase 2)
- Scheduled/autonomous runs (planned for Phase 2)
- Web or WhatsApp interface
- Multi-user support
