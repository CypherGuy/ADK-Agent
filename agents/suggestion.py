from google.adk.agents.llm_agent import LlmAgent
from config import DIGEST_LOOKBACK_DAYS


GEMINI_MODEL = "gemini-2.5-flash"

suggestion_agent = LlmAgent(
    name="SuggestionAgent",
    model=GEMINI_MODEL,
    instruction=f"""
    Based on the given summaries, cross-reference them and provide 1 to 5 of the following:
    - An underused technology,
    - a relevant trend from the digest, looking back the past {DIGEST_LOOKBACK_DAYS} days,
    - and a concrete project idea revolving around both things.

    You should match repo technologies against the technologies, ideas and concepts
    mentioned in the digests over just picking any random digest item.
    Never pick the same repo more then once, each choice should use a differen repository.


    Receive the structured list and rewrite it as a numbered narrative, one bullet per suggestion, in the format here.
        1) You haven't used TypeScript in months.
          OpenAI released GPT-Realtime-2 with live streaming transcription and translation.
          Idea: build a TypeScript app that streams microphone input to GPT-Realtime-2 and
          renders live transcription + translation side by side.

    Compute the duration between today's date and last_used, then express it in human terms.
    DO NOT reuse the same digest trend for multiple suggestions.
    It should be in Prose, not JSON with the Repo name called out directly.
    Staleness in human time (days, weeks, over a year) is ideal.
    You MUST be honest about non-matches rather than forcing weak suggestions.
    Normalise the names of the technologies: It should start with a Capital letter and be in title case.
    React over react for example.
    Treat TypeScript, JavaScript, React, Next.js, and related packages as one ecosystem;
    output at most one suggestion per ecosystem.


    You must select underused_tech exclusively from the technologies arrays in the repo analysis data.
    If a technology in underused_tech does not appear verbatim in the repo analysis output,
    the suggestion is invalid and must be discarded
    """,
    description="Provides suggestions based on summaries and daily digests from Daily Digest files.",

)
