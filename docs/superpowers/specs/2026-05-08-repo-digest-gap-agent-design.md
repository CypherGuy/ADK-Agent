# Design Spec: Repo & Digest Gap Detection Agent

**Date:** 2026-05-08
**Status:** Approved
**Language:** Python
**Framework:** Google ADK (Agent Development Kit)

---

## Problem

There are many repos spanning many technologies. Over time, skills and tools go unused while the broader ecosystem moves on. There is no mechanism to surface "you know X but haven't touched it in months, and the community is actively talking about it right now." DailyDigest, another repo, already curates relevant tech news into local `.txt` files. This agent connects the two.

---

## Goal

A CLI tool that analyses your repos and your DailyDigest files, cross-references technologies you know against recency of use and current trends, and streams up to 10 concrete, personalised project suggestions. If no genuine matches are found between underused technologies and recent digest trends, the tool returns a clear "nothing found" message rather than fabricating suggestions.

---

## Architecture

### Agent Roles

All agents use Gemini 2.0 Flash. There is no Ollama dependency anywhere in this project.

| Agent               | Model            | Responsibility                                                                                      |
| ------------------- | ---------------- | --------------------------------------------------------------------------------------------------- |
| `CoordinatorAgent`  | Gemini 2.0 Flash | Receives the user query, interprets intent, delegates to the pipeline, presents final output        |
| `RepoAnalysisAgent` | Gemini 2.0 Flash | Scans all repos, calls tools, reasons about tech stack and recency, returns structured output       |
| `DigestReaderAgent` | Gemini 2.0 Flash | Reads digest files, reasons about trending topics and their significance, returns structured output |
| `SuggestionAgent`   | Gemini 2.0 Flash | Receives both structured outputs, applies staleness logic, cross-references, generates suggestions  |

Every agent performs meaningful reasoning — none are simple relay agents.

### Pipeline

```
CoordinatorAgent (Gemini)
  └── SequentialAgent
        ├── Phase 1 — ParallelAgent
        │     ├── RepoAnalysisAgent (Gemini)
        │     └── DigestReaderAgent (Gemini)
        └── Phase 2 — SuggestionAgent (Gemini)
```

Phase 1 runs in parallel — both agents operate independently on separate data sources. Phase 2 is sequential — `SuggestionAgent` depends on both Phase 1 outputs.

---

## File Structure

Every agent, tool, and pipeline file lives inside the `agents/` directory. `main.py` and `config.py` live at the project root as they are not agents.

```
ADK-Agent/
├── agents/
│   ├── coordinator.py
│   ├── repo_analysis.py
│   ├── digest_reader.py
│   ├── suggestion.py
│   ├── pipeline.py
│   └── tools/
│       ├── repo_tools.py
│       └── digest_tools.py
├── tests/
│   ├── fixtures/
│   │   ├── fake_repo/
│   │   └── fake_digests/
│   ├── test_repo_tools.py
│   ├── test_digest_tools.py
│   ├── test_agents.py
│   └── test_pipeline.py
├── main.py
├── config.py
├── .env.example
├── .env
└── requirements.txt
```

### File Responsibilities

**`agents/coordinator.py`**
Defines `CoordinatorAgent`. Receives the user's query and delegates to the `SequentialAgent` defined in `pipeline.py`. Acts as a thin router only — it does not reformat or post-process the pipeline output. ADK's sub-agent routing model means the parent agent cannot intercept and transform a sub-agent's response; output from `SuggestionAgent` flows directly to the runner. All formatting and narrative construction is therefore `SuggestionAgent`'s responsibility.

**`agents/repo_analysis.py`**
Defines `RepoAnalysisAgent`. Calls `list_repos`, then `read_git_log` and `read_dependencies` on each repo. Reasons about what technologies are present across the codebase and when each was last used. Returns a structured list — one entry per repo — in the schema defined in the Data Flow section. Does not decide what is "underused" — that is `SuggestionAgent`'s job.

**`agents/digest_reader.py`**
Defines `DigestReaderAgent`. Calls `list_digest_files` to find all available digest files within the lookback window, then `read_digest` on each. Reasons about what technology topics appear, what they mean, and summarises the key signal from each. Returns a structured list in the schema defined in the Data Flow section.

**`agents/suggestion.py`**
Defines `SuggestionAgent`. Receives the structured outputs from both `RepoAnalysisAgent` and `DigestReaderAgent` in context — never the raw files. Applies the staleness threshold (`REPO_STALENESS_DAYS`, injected via system prompt) to determine which technologies are underused. Cross-references underused technologies against digest topics to find genuine matches. Generates up to 10 project suggestions, each grounded in both a real technology gap and a real digest signal. If no matches exist, returns a clear message stating that.

`SuggestionAgent` is also responsible for all output formatting. It must render suggestions as a human-readable narrative — not JSON — in this format:

```
→ You haven't used <Technology> in <human time (e.g. 8 months, over a year)>.
  <One-sentence digest trend summary>.
  Idea: <concrete project linking the technology gap to the trend>.
```

Technology names must be title-cased (React, not react; TypeScript, not typescript). Staleness must be expressed in human time, not ISO dates. If the relevant repo name adds useful context, include it in the Idea line. Do not produce suggestions where the digest match is weak — omit them and note the gap instead.

**`agents/pipeline.py`**
Wires the agent pipeline. Creates the `ParallelAgent` wrapping `RepoAnalysisAgent` and `DigestReaderAgent`, then wraps that in a `SequentialAgent` with `SuggestionAgent` as phase 2. Imported by `coordinator.py`. Contains no agent logic — only assembly.

**`agents/tools/repo_tools.py`**
Contains the three repo analysis tools: `list_repos`, `read_git_log`, `read_dependencies`. Pure functions — no agent logic, no LLM calls, no config side effects beyond accepting paths as arguments.

**`agents/tools/digest_tools.py`**
Contains the two digest tools: `list_digest_files`, `read_digest`. Pure functions — no agent logic, no LLM calls.

**`main.py`**
The CLI entry point. Accepts an optional query string argument. Instantiates the `CoordinatorAgent` and runs it via ADK's streaming runner, printing token output to stdout as it arrives. This is the intended end-user interface.

**`config.py`**
Loads all environment variables from `.env` using `python-dotenv` and exposes them as typed constants for import throughout the project.

---

## Tools

All tool functions take full absolute paths as arguments. Relative paths or bare names are not supported.

### `agents/tools/repo_tools.py`

- `list_repos(repos_path: str) -> list[str]`
  Takes a full absolute path to the repos directory. Returns subdirectory names whose last commit is older than `REPO_STALENESS_DAYS` days — i.e. only repos that qualify as stale. Repos touched more recently than the threshold are excluded entirely. This pre-filtering means `RepoAnalysisAgent` only receives repos it actually needs to process, keeping the tool call count manageable. Repos in `EXCLUDED_REPOS` are always excluded regardless of commit date. Returns an empty list if no repos meet the staleness threshold.

- `read_git_log(repo_path: str) -> dict`
  Takes a full absolute path to a single repo directory. Returns last commit date (ISO 8601 string, e.g. `"2026-05-01"`) and a list of up to 10 recent commit messages. Example return value: `{ "last_commit_date": "2026-05-01", "recent_commits": ["fix bug in parser", "add CSV export"] }`. The `recent_commits` field is available for `RepoAnalysisAgent` to reason about recent activity but does not appear in the agent's output schema.

- `read_dependencies(repo_path: str) -> list[str]`
  Takes a full absolute path to a single repo directory. Reads `package.json`, `pyproject.toml`, `requirements.txt`, or `go.mod` and returns library/framework names. Falls back to inferring language from file extensions in the repo if no dependency file exists.

### `agents/tools/digest_tools.py`

- `list_digest_files(digest_path: str) -> list[str]`
  Takes a full absolute path to the digest directory. Returns absolute paths to all `.txt` digest files found, sorted by filename date descending (most recent first).

- `read_digest(file_path: str) -> str`
  Takes a full absolute path to a single `.txt` digest file. Returns its raw text content unchanged — no parsing, no summarisation.

---

## Data Flow

1. User runs `python main.py` or `python main.py "what should I build this week?"`
2. `CoordinatorAgent` receives the query, interprets it, and delegates to the `SequentialAgent`
3. `ParallelAgent` fires `RepoAnalysisAgent` and `DigestReaderAgent` simultaneously
4. `RepoAnalysisAgent` returns a structured list — one entry per repo:
   `[{ "repo": str, "technologies": list[str], "last_used": str }]`
   `last_used` is an ISO 8601 date string (e.g. `"2026-05-01"`). No other fields appear in this output. `recent_commits` from the raw tool call is used only for internal reasoning and is never forwarded downstream.
5. `DigestReaderAgent` returns a structured list — one entry per notable topic found across the digest files within `DIGEST_LOOKBACK_DAYS`:
   `[{ "topic": str, "summary": str, "date": str }]`
   `summary` is a concise description of why the topic matters and what is new. `date` is the ISO 8601 date of the digest file the topic was found in.
6. `SuggestionAgent` receives both structured lists in context. It compares `last_used` dates against today minus `REPO_STALENESS_DAYS` (injected into its system prompt from config) to identify underused technologies. It then finds digest topics that match those technologies. For each genuine match it generates a suggestion rendered as a human-readable narrative (see File Responsibilities for the exact format). If no matches are found, it returns a clear message instead.
7. `CoordinatorAgent` passes `SuggestionAgent`'s output through to the runner unchanged. It does not reformat — all presentation is owned by `SuggestionAgent`.

### What counts as a suggestion

A suggestion is only generated when both conditions are met:

- The technology has not appeared in any repo's `last_used` within the past `REPO_STALENESS_DAYS` days
- A matching topic exists in digest files from the past `DIGEST_LOOKBACK_DAYS` days

Each suggestion contains: the underused technology, the relevant digest trend and its summary, and a concrete project idea linking the two.

### Example output

```
→ You haven't used Terraform in 8 months.
  OpenTofu 1.9 released last week with state encryption not available in Terraform.
  Idea: migrate your cloud-foundations-aws project from Terraform to OpenTofu.

→ You haven't used mysql2 in 7 months.
  Claude Managed Agents now support multiagent orchestration in production at scale.
  Idea: build a CDC listener that writes MySQL binlog events to a Claude agent for natural language querying.
```

---

## Mode of Use

**`python main.py`**
Run `python main.py` or `python main.py "your query"` from the project root. Suggestions stream to the terminal as they are generated. This is the only supported interface.

---

## CLI Specification

### Invocation

```
python main.py [query]
```

`query` is optional. If omitted, the default query `"What should I build next?"` is used. If provided, the query string is passed directly to `CoordinatorAgent`.

### Input

| Argument | Required | Default                    | Description                              |
| -------- | -------- | -------------------------- | ---------------------------------------- |
| `query`  | No       | `"What should I build next?"` | Natural language query passed to the agent |

### Output

Suggestions stream to stdout token by token as `CoordinatorAgent` generates them. The process does not buffer and print at the end — output appears incrementally as each token arrives.

On success, the output is the formatted suggestions from `CoordinatorAgent`. On "nothing found", the output is the clear message from `SuggestionAgent` as presented by `CoordinatorAgent`.

### Exit Codes

| Code | Condition                                      |
| ---- | ---------------------------------------------- |
| `0`  | Run completed — including "nothing found" case |
| `1`  | Fatal error before the pipeline could start (missing `.env` keys, Gemini API unreachable) |

### Error Messages

Errors that prevent the pipeline from starting are printed to stderr and exit with code `1`. Errors that occur inside the pipeline (e.g. a single repo failing to parse) are surfaced inline in the output and do not abort the run.

### Constants

`main.py` must define `DEFAULT_QUERY = "What should I build next?"` as a module-level constant so it is testable and changeable in one place.

---

## Configuration

All paths and keys live in `.env`, which is gitignored. `.env.example` is committed with placeholder values.

| Variable               | Default | Purpose                                                                      |
| ---------------------- | ------- | ---------------------------------------------------------------------------- |
| `REPOS_PATH`           | —       | Full absolute path to the directory containing your repos                    |
| `DIGEST_PATH`          | —       | Full absolute path to the directory containing your DailyDigest `.txt` files |
| `GEMINI_API_KEY`       | —       | API key for Google Gemini                                                    |
| `DIGEST_LOOKBACK_DAYS` | 30      | How many days back `DigestReaderAgent` reads digest files                    |
| `REPO_STALENESS_DAYS`  | 180     | Days since last commit before a technology is considered underused           |

`DIGEST_LOOKBACK_DAYS` and `REPO_STALENESS_DAYS` are independent. A short digest window (recent signals) paired with a long staleness window (genuinely unused skills) is the intended configuration.

---

## Error Handling

| Scenario                       | Behaviour                                                     |
| ------------------------------ | ------------------------------------------------------------- |
| Repo path not found            | Skip that repo, log a warning, continue with the rest         |
| No dependency file in repo     | Fall back to inferring language from file extensions          |
| Digest directory empty/missing | `SuggestionAgent` runs on repo data only, notes the gap       |
| Gemini API failure             | Surface the error directly to the user, no retry              |
| No matches found               | Return a clear "nothing found" message, no forced suggestions |

No silent failures. Every error or exceptional case produces a clear, actionable message.

---

## Testing

Integration tests mock at the LLM response level only. The ADK runner, tool dispatch, and agent logic all execute for real. Only the model's generated text is substituted. Mocking the runner or skipping tool execution is not permitted in integration tests.

No test makes real API calls to Gemini. All live runs are manual verification only.

| Layer       | What                         | How                                                                         |
| ----------- | ---------------------------- | --------------------------------------------------------------------------- |
| Unit        | `repo_tools`, `digest_tools` | Called directly against `tests/fixtures/`, no mocking, no API calls         |
| Integration | Each agent individually      | ADK `InMemoryRunner` with Gemini LLM response mocked at generation level    |
| Smoke       | Full pipeline end-to-end     | All four agents run against `tests/fixtures/` with all LLM responses mocked |

Framework: `pytest`

---

## Out of Scope (Phase 1)

- Persistent memory / session state (planned for Phase 2)
- Scheduled / autonomous runs (planned for Phase 2)
- Web or WhatsApp interface
- Multi-user support
