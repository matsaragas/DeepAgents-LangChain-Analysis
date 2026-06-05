import os
from typing import Literal, Optional, Dict, Any
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from tavily import TavilyClient
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from urllib.request import urlopen
import logging
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain.chat_models import init_chat_model



import certifi
import ssl

logger = logging.getLogger(__name__)

load_dotenv()

# --- Generic Tools ---
tavily_api_key = os.getenv("TAVILY_API_KEY")
tavily = TavilyClient(api_key=tavily_api_key) if tavily_api_key else None

def internet_search(
        query: str,
        max_results: int = 5,
        topic: Literal["general", "news", "finance"] = "general",
):
    """Search the web for current information. Use when you need data from the internet."""
    if not tavily:
        return "Tavily API key not found. Please set TAVILY_API_KEY in .env."
    return tavily.search(query, max_results=max_results, topic=topic)


def fmp_balance_sheet(ticker: str) -> Optional[str]:
    """Hits the FMP API to retrieve the balance sheet information for the company with the given ticker.

    Args:
        ticker: The ticker of the company we want to access the balance sheet

    Returns:
        A formatted string with search results, or None if no results.
    """
    url = (f"https://financialmodelingprep.com/stable/balance-sheet-statement?symbol={ticker}&apikey={os.getenv('FMP_KEY')}")
    try:
        context = ssl.create_default_context(cafile=certifi.where())
        response = urlopen(url, context=context)
        data = response.read().decode("utf-8")
        return data
    except Exception as e:
        logger.error(f"fmp API request for balance sheet informaation failed for {ticker}")



# --- Agent Factory ---
def get_deep_agent():
    """Create and return a generic Deep Agent orchestrator.

    This agent is designed to be purely generic, relying on dynamically loaded
    skills from the './skills/' directory to handle specialized tasks.
    """
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if anthropic_key:
        model = ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620"),
            temperature=0,
        )
    elif openai_key:
        rate_limiter = InMemoryRateLimiter(
            requests_per_second=0.5,  # <-- Super slow! We can only make a request once every 10 seconds!!
            check_every_n_seconds=4,  # Wake up every 100 ms to check whether allowed to make a request,
            max_bucket_size=10,  # Controls the maximum burst size.
        )
        #model = ChatOpenAI(
        #    model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        #    temperature=0,
        #)
        model = init_chat_model("gpt-5.4", rate_limiter=rate_limiter)
    else:
        raise ValueError("Neither ANTHROPIC_API_KEY nor OPENAI_API_KEY found in .env. Please set one.")

    workspace_root = os.getenv("WORKSPACE_ROOT", "./workspace")
    if not os.path.exists(workspace_root):
        os.makedirs(workspace_root)

    skills_root = "./skills"
    if not os.path.exists(skills_root):
        os.makedirs(skills_root)

    return create_deep_agent(
        model=model,
        system_prompt="""You are a generic Deep Agent, an expert orchestrator designed to perform any task.
Your primary goal is to use the provided skill library to handle specialized requirements on-demand.

1. **Strategic Planning**: Use `write_todos` to map out your approach for complex requests.
2. **On-Demand Skills**: You have access to a library of skills in the `skills/` directory. 
   - You ONLY see names and descriptions of skills in your system prompt initially.
   - For any specialized task (e.g. research, writing, coding), you MUST look for matching skills and use `read_file` to load the `SKILL.md` before executing.
3. **Generic Subagents**: Use the `task` tool with the 'general-purpose' subagent to handle independent, complex, or context-heavy sub-tasks.
   - The 'general-purpose' subagent is also generic and can load the same skills.
4. **NO /tmp/ FOLDER**: NEVER save files to the `/tmp/` directory. This is a critical requirement.

Follow the instructions in the loaded SKILL.md exactly once they are retrieved. If no skill exists for a task, proceed using your general knowledge and reasoning.""",
        tools=[internet_search, fmp_balance_sheet],
        skills=[skills_root],
        memory=["./AGENTS.md"],
        backend=FilesystemBackend(root_dir="."),
        name="generic_deep_agent",
    )
