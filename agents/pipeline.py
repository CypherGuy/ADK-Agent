from agents.suggestion import suggestion_agent
from google.adk.agents.sequential_agent import SequentialAgent
from agents.repo_analysis import repo_analysis_agent
from agents.digest_reader import digest_reader_agent
from google.adk.agents.parallel_agent import ParallelAgent

GEMINI_MODEL = "gemini-2.5-flash"


parallel_agent = ParallelAgent(
    name="ParallelAgent",
    sub_agents=[repo_analysis_agent, digest_reader_agent],
    description="Runs multiple research agents in parallel to gather information."
)


sequential_agent = SequentialAgent(
    name="SequentialAgent",
    sub_agents=[parallel_agent, suggestion_agent],
    description="Runs multiple research agents in sequence to gather information."
)
