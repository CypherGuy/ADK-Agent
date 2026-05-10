from google.adk.events import Event
from google.adk.agents.run_config import RunConfig
import asyncio
import config
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from agents.coordinator import coordinator_agent as root_agent
from google.genai import types
import sys

DEFAULT_QUERY = config.DEFAULT_QUERY


async def main():

    # Get sys args
    args = sys.argv

    if len(args) > 2:
        raise SystemExit("Incorrect arguments. Usage: main.py <query>")

    query = args[1].strip() if len(args) > 1 and len(
        args[1].strip()) > 0 else DEFAULT_QUERY

    session_service = InMemorySessionService()

    runner = Runner(
        app_name='Repo-Digest-Project-Generator-Runner',
        agent=root_agent,
        session_service=session_service
    )

    session = await session_service.create_session(
        app_name='Repo-Digest-Project-Generator-Runner',
        user_id='user'
    )

    user_input = types.Content(role="user", parts=[types.Part(
        text=query)])

    await session_service.append_event(session, Event(author="user", content=user_input))

    # Configure the run to expect TEXT responses
    run_config = RunConfig(response_modalities=["TEXT"])

    # Pass the run_config to the runner
    async for event in runner.run_async(
            user_id="user", session_id=session.id,
            run_config=run_config, new_message=user_input):
        if event.is_final_response() and event.author == "SuggestionAgent" and event.content and event.content.parts:
            text = "".join(
                part.text for part in event.content.parts if part.text)
            if text:
                print("\n\n\n" + text, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
