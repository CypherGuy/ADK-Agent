from google.adk.agents.llm_agent import LlmAgent
from agents.pipeline import sequential_agent

GEMINI_MODEL = "gemini-2.5-flash"


coordinator_agent = LlmAgent(
    name="CoordinatorAgent",
    sub_agents=[sequential_agent],
    model=GEMINI_MODEL,
    instruction=(
        "Your job is to analyse the user's repos and digest to generate project suggestions. "
        "You must ALWAYS kick off the pipeline via the SequentialAgent, not SuggestionAgent "
        "or ParallelAgent, and never answer from your own knowledge. "
        "Once the pipeline is complete, return the solutions in a friendly and engaging manner."
    ),
)
