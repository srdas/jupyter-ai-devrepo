"""Persistent storage for saved quick agent configurations."""

import json
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


AGENTS_DIR = str(Path.home() / ".jupyter" / "jupyter-ai" / "quickagents")


class AgentConfig(BaseModel):
    """A saved quick agent configuration."""

    name: str = Field(description="Display name of the agent")
    purpose: str = Field(description="What the agent is supposed to do")
    tools: list[str] = Field(default_factory=list, description="Selected tool names")
    search_tools: list[str] = Field(
        default_factory=list, description="Selected search tool names"
    )
    skills_dir: str = Field(
        default="",
        description="Path to a directory containing skill (.md) files for the agent",
    )
    system_prompt: str = Field(default="", description="Custom system prompt override")


# Common tools that can be added to agents
COMMON_TOOLS = {
    "execute": "Run shell commands (bash)",
    "read_file": "Read file contents from disk",
    "write_file": "Create or overwrite files",
    "edit_file": "Make targeted edits to existing files",
    "ls": "List directory contents",
    "glob": "Find files matching a pattern",
    "grep": "Search file contents with regex",
    "python_repl": "Execute Python code in a REPL",
    "web_fetch": "Fetch and read content from a URL",
    "todo": "Create and manage a task/todo list",
}

# Search tools the agent can use
SEARCH_TOOLS = {
    "tavily_search": "Tavily AI-powered web search (requires TAVILY_API_KEY)",
    "duckduckgo_search": "DuckDuckGo web search (no API key needed)",
    "wikipedia": "Search and retrieve Wikipedia articles",
    "arxiv": "Search academic papers on arXiv",
    "pubmed": "Search biomedical literature on PubMed",
}

# Maps search tool names to their required environment variable (if any)
SEARCH_TOOL_API_KEYS = {
    "tavily_search": "TAVILY_API_KEY",
}


def _ensure_dir():
    os.makedirs(AGENTS_DIR, exist_ok=True)


def save_agent(config: AgentConfig) -> str:
    """Save an agent configuration to disk. Returns the file path."""
    _ensure_dir()
    slug = config.name.lower().replace(" ", "_")
    path = os.path.join(AGENTS_DIR, f"{slug}.json")
    with open(path, "w") as f:
        json.dump(config.model_dump(), f, indent=2)
    return path


def load_agent(name: str) -> Optional[AgentConfig]:
    """Load an agent configuration by name."""
    _ensure_dir()
    slug = name.lower().replace(" ", "_")
    path = os.path.join(AGENTS_DIR, f"{slug}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    return AgentConfig(**data)


def list_agents() -> list[AgentConfig]:
    """List all saved agent configurations."""
    _ensure_dir()
    agents = []
    for filename in sorted(os.listdir(AGENTS_DIR)):
        if filename.endswith(".json"):
            path = os.path.join(AGENTS_DIR, filename)
            with open(path) as f:
                data = json.load(f)
            agents.append(AgentConfig(**data))
    return agents


def delete_agent(name: str) -> bool:
    """Delete a saved agent configuration. Returns True if deleted."""
    _ensure_dir()
    slug = name.lower().replace(" ", "_")
    path = os.path.join(AGENTS_DIR, f"{slug}.json")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False
