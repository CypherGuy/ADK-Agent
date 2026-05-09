from google.adk.agents.llm_agent import LlmAgent
from config import REPO_STALENESS_DAYS, DIGEST_LOOKBACK_DAYS


GEMINI_MODEL = "gemini-2.5-flash"

suggestion_agent = LlmAgent(
    name="SuggestionAgent",
    model=GEMINI_MODEL,
    instruction=f"""
    Based on the given summaries, cross-reference them and provide 1 to 5 of the following:
    - An underused technology,
    - a relevant trend from the digest, looking back the past {DIGEST_LOOKBACK_DAYS} days,
    - and a concrete project idea revolving around both things.

    You should match repo technologies against the technologies, ideas anc concepts mentioned in the digests over just picking any random digest item.


    Return a list of dictionaries, one for each suggestion. Each dictionary should have keys "underused_tech", "digest_trend", and "project_idea". Like this:

    [
      {{"underused_tech": "a technology used in a repo", "digest_trend": "a trend",
          "project_idea": "a project idea" }}
      {{"underused_tech": "another technology used in a repo", "digest_trend": "another trend",
          "project_idea": "another project idea" }}
      ...
    ]

    You must select underused_tech exclusively from the technologies arrays in the repo analysis data. 
    A technology is underused if it appears in under 25% of all repositories.
    If a technology in underused_tech does not appear verbatim in the repo analysis output, the suggestion is invalid and must be discarded
    """,
    description="Provides suggestions based on summaries and daily digests from Daily Digest files.",

)
