# ADK Agent

A CLI tool using Google's Agent Developer Kit ([ADK](https://adk.dev)) that surfaces personalised project ideas by cross-referencing your underused technologies against recent trends in newsletters or digests you store. It scans your repos, identifies technology gaps (skills you have worked on but haven't touched recently), reads your local digest files for trending topics, and prints up to 10 concrete suggestions grounded in both a real gap and a real signal.

If no genuine match exists between stale technologies and recent digest trends, the tool says so clearly rather than fabricating suggestions.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A directory of repos and a directory of `.txt` files. I have a private repo that covers multiple daily newsletters and digests into `.txt` files.
- A Google Gemini API key

## Installation

```bash
git clone https://github.com/CypherGuy/ADK-Agent
cd ADK-Agent
uv sync
```

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable                    | Required | Default                     | Description                                                             |
| --------------------------- | -------- | --------------------------- | ----------------------------------------------------------------------- |
| `REPOS_PATH`                | Yes      | —                           | Absolute path to the directory containing your repos                    |
| `DIGEST_PATH`               | Yes      | —                           | Absolute path to the directory containing your DailyDigest `.txt` files |
| `GEMINI_API_KEY`            | Yes      | —                           | Google Gemini API key                                                   |
| `REPO_STALENESS_DAYS`       | No       | 180                         | Days since last commit before a technology is considered underused      |
| `DIGEST_LOOKBACK_DAYS`      | No       | 7                           | How many days back `DigestReaderAgent` reads digest files               |
| `EXCLUDED_REPOS`            | No       | —                           | Comma-separated repo names to skip entirely                             |
| `DEFAULT_QUERY`             | No       | `What should I build next?` | Query used when none is provided on the command line                    |
| `GOOGLE_GENAI_USE_VERTEXAI` | No       | `FALSE`                     | Set to `TRUE` to route requests through Vertex AI instead of Gemini API |

`REPO_STALENESS_DAYS` and `DIGEST_LOOKBACK_DAYS` are independent. A short digest window paired with a long staleness window is the intended default: recent signals against genuinely unused skills.

## Usage

```bash
python main.py
python main.py "what should I build this week?"
```

Suggestions print to the terminal once the pipeline completes.

## Example output

```
→ You haven't used Terraform in 8 months.
  OpenTofu 1.9 released last week with state encryption not available in Terraform.
  Idea: migrate your cloud-foundations-aws project from Terraform to OpenTofu.

→ You haven't used mysql2 in 7 months.
  Claude Managed Agents now support multiagent orchestration in production at scale.
  Idea: build a CDC listener that writes MySQL binlog events to a Claude agent for natural language querying.
```

## Architecture

All agents run on Gemini 2.5 Flash. The pipeline runs in two phases:

```
CoordinatorAgent
  └── SequentialAgent
        ├── Phase 1 (parallel)
        │     ├── RepoAnalysisAgent  — scans repos, identifies tech stack and recency
        │     └── DigestReaderAgent  — reads digest files, extracts trending topics
        └── Phase 2
              └── SuggestionAgent    — cross-references gaps vs. trends, generates suggestions
```

Phase 1 agents run concurrently against separate data sources. Phase 2 depends on both Phase 1 outputs.

### Tools

**`agents/tools/repo_tools.py`**

- `list_repos(repos_path)` — returns repo names whose last commit is older than `REPO_STALENESS_DAYS`; excludes `EXCLUDED_REPOS`
- `read_git_log(repo)` — returns last commit date (ISO 8601) and up to 10 recent commit messages
- `read_dependencies(repo)` — reads `requirements.txt`, `pyproject.toml`, or `package.json`; falls back to inferring language from file extensions

**`agents/tools/digest_tools.py`**

- `list_digest_files(digest_path)` — returns absolute paths to `.txt` digest files, sorted newest first
- `read_digest(file_path)` — returns raw file content unchanged

### Suggestion criteria

A suggestion is only generated when both conditions hold:

- The technology has not appeared in any repo within the past `REPO_STALENESS_DAYS` days
- A matching topic exists in digest files from the past `DIGEST_LOOKBACK_DAYS` days

## Testing

```bash
pytest
```

Tests are split across three layers:

| Layer       | Scope                        | Approach                                                              |
| ----------- | ---------------------------- | --------------------------------------------------------------------- |
| Unit        | `repo_tools`, `digest_tools` | Called directly against `tests/fixtures/`; no mocks, no API calls     |
| Integration | Each agent individually      | ADK `InMemoryRunner` with Gemini responses mocked at generation level |
| Smoke       | Full pipeline end-to-end     | All four agents run against fixtures with all LLM responses mocked    |

No test makes real API calls to Gemini.

## Project structure

```
ADK-Agent/
├── agents/
│   ├── coordinator.py     # Entry point agent; delegates to the pipeline
│   ├── repo_analysis.py   # Gets repos and identifies tech stack and date of last commit
│   ├── digest_reader.py   # Gets digests and summarises trending topics
│   ├── suggestion.py      # Cross-references the repos and recent trends and provides suggestions
│   ├── pipeline.py        # Wires the parallel + sequential pipeline
│   └── tools/
│       ├── repo_tools.py
│       └── digest_tools.py
├── tests/
│   ├── fixtures/
│   ├── test_repo_tools.py
│   ├── test_digest_tools.py
│   ├── test_agents.py
│   ├── test_pipeline.py
│   └── test_main.py
├── main.py                # CLI entry point
├── config.py              # Loads .env and exposes typed constants
└── .env.example
```

# License

MIT
