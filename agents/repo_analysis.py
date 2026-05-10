from google.adk.agents import LlmAgent
from google.genai import types
from agents.tools import repo_tools
from config import REPOS_PATH
repo_analysis_agent = LlmAgent(
    name="repo_analysis_agent",
    model="gemini-2.5-flash",
    generate_content_config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_budget=0  # Encourage less thinking to speed up response
        )
    ),
    description="Gathers information about the user's repositories, including dependencies and recent git logs.",
    instruction=f"""
    Ignore the contents of the user's message.
    Get information about repositories, including dependencies and recent git logs.
    All repositories live at {REPOS_PATH}.

    Your output should be a structured list, one entry per repo:
   `[{{"repo": str, "technologies": list[str], "last_used": str }}]`
   `last_used` is an ISO 8601 date string (e.g. `"2026-05-01"`). No other fields appear in this output.

    You should iterate through every single repo not excluding any,
    not just one repo only, and add an entry for each in the output list,
    so the output list contains one element for each repo.
    You must include specific library names from specific repos into the technologies list.


    Do not ask the user any questions and do not explain what you can or cannot do,
    just call your tools and return the results.

    """,
    tools=[
        repo_tools.list_repos,
        repo_tools.read_git_log,
        repo_tools.read_dependencies,
    ],
)
