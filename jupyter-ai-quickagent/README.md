# jupyter-ai-quickagent

A Jupyter AI persona that implements [LangChain Deep Agents](https://github.com/langchain-ai/deepagents) with an interactive agent configuration flow.

## Features

- **Interactive agent builder** — step-by-step setup via chat (name, purpose, tools, search, skill files)
- **Shared LLM authentication** — automatically uses the model and credentials configured in Jupyter AI's **Settings > AI Settings** (via LiteLLM), so there is no separate API key setup
- **Persistent agents** — saved to disk and reusable across sessions
- **Built-in tools** — file I/O, shell execution, Python REPL, planning (provided by the Deep Agents framework)
- **Search integration** — DuckDuckGo (built-in, no API key), plus optional Tavily, Wikipedia, arXiv, PubMed
- **Skills directory** — point to a folder of `.md` files with specialized instructions, domain knowledge, or workflows (same as Claude's `--add-dir`)
- **Chat commands** — `@QuickAgent create`, `@QuickAgent list`, `@QuickAgent use <name>`, etc.

## Prerequisites

- **Jupyternaut** (`jupyter_ai_jupyternaut`) must be installed and a chat model must be configured in **Settings > AI Settings**. QuickAgent reuses this model — no environment-variable API keys are needed for the LLM itself.
- **Python >= 3.11**

## Installation

### Within the devrepo

The package is included in the devrepo workspace as an optional dependency. From the devrepo root:

```bash
just sync          # or: uv sync --extra optional
```

### Standalone

```bash
pip install jupyter_ai_quickagent
```

## Quick Start

1. Ensure a chat model is configured in **Settings > AI Settings** (the same one Jupyternaut uses).
2. Start JupyterLab: `just start`
3. Open the Jupyter AI chat panel from the left sidebar.
4. Send `@QuickAgent create` to build your first agent.
5. Follow the five interactive prompts (name, purpose, tools, search tools, skill files).

See [USAGE.md](USAGE.md) for the full walkthrough and command reference.

## How Authentication Works

QuickAgent does **not** manage its own API keys. Instead, it reads the model ID and credentials from Jupyternaut's `ConfigManager`, which is populated through the **Settings > AI Settings** UI. Under the hood this uses [LiteLLM](https://docs.litellm.ai/), so any provider supported there (OpenAI, Anthropic, Azure, Google, AWS Bedrock, etc.) works automatically.

## Development

```bash
cd jupyter-ai-quickagent
just pytest     # run tests
just lint       # run linters
```

## Update `pyproject.toml`

In the following two places. 

```toml
[project.optional-dependencies]
optional = [
    "jupyter_ai_litellm",
    "jupyter_ai_jupyternaut",
    "jupyter_ai_magic_commands",
    "jupyter_ai_quickagent",
]
```

```toml
[tool.uv.sources]
jupyter_ai = { workspace = true }
jupyter_server_documents = { workspace = true }
jupyterlab_chat = { workspace = true }
jupyter_ai_router = { workspace = true }
jupyter_ai_persona_manager = { workspace = true }
jupyter_ai_litellm = { workspace = true }
jupyter_ai_magic_commands = { workspace = true }
jupyter_ai_chat_commands = { workspace = true }
jupyterlab_commands_toolkit = { workspace = true }
jupyter_ai_jupyternaut = { workspace = true }
jupyter_ai_acp_client = { workspace = true }
jupyter_server_mcp = { workspace = true }
jupyter_ai_tools = { workspace = true }
jupyter_ai_quickagent = { workspace = true }
```
