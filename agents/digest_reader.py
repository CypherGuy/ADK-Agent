from google.adk.agents import LlmAgent
from agents.tools import digest_tools
from google.genai import types
import config

digest_reader_agent = LlmAgent(
    name="digest_reader",
    model="gemini-2.5-flash",
    description="Reads the user's daily digests.",
    generate_content_config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_budget=0  # Encourage less thinking to speed up response
        )
    ),
    instruction=f"""
    Ignore the contents of the user's message.
    Read digest files in {config.DIGEST_PATH}. Look for a folder called digests.
    Your response must be a structured list of dicts, written in perfect JSON, in this format:

    [
    {{ topic: topic goes here, summary: Create a summary of the topic and put it here,
    date: date of the digest in ISO 8601 format (e.g. "2026-04-29") }},
    {{ topic: topic goes here, summary: Create a summary of the toppic and put it here,
    date: date of the digest in ISO 8601 format (e.g. "2026-04-29") }},
    ...
    ]

    There should be one entry per notable topic found across all files, not one entry per file.


    Do not ask the user any questions and do not explain what you can or cannot do,
    just call your tools and return the results.
    """,
    tools=[digest_tools.list_digest_files, digest_tools.read_digest],
)
