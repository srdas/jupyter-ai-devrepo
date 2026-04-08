# DeepAgent for Jupyter AI — Usage Guide

## Overview

**DeepAgent** is a Jupyter AI persona that lets you interactively create, configure, and run autonomous agents powered by [LangChain Deep Agents](https://github.com/langchain-ai/deepagents). Each agent can have its own tools and search capabilities. Agents are saved to disk so you can reuse them across sessions.

## Prerequisites

1. **Jupyter AI devrepo** set up and running (`just install-all && just start`), or a standalone JupyterLab environment with `jupyter_ai_deepagent` installed.
2. **A chat model configured in Jupyter AI settings.** Open **Settings > AI Settings** in JupyterLab and select a model (e.g., `anthropic/claude-sonnet-4-20250514`, `openai/gpt-4o`). DeepAgent shares this model with Jupyternaut via LiteLLM — no separate API keys or environment variables are needed for the LLM.
3. **(Optional)** For Tavily web search, set the API key as an environment variable before starting JupyterLab:
   ```bash
   export TAVILY_API_KEY="tvly-..."
   ```
   DuckDuckGo search works out of the box with no API key.

## Getting Started

### 1. Open the Chat Panel

In JupyterLab, open the Jupyter AI chat panel from the left sidebar.

### 2. Mention DeepAgent

Type `@DeepAgent` in the chat to interact with the DeepAgent persona. On first use, you'll see a help menu with available commands.

### 3. Create Your First Agent

Send `@DeepAgent create` and follow the interactive prompts:

#### Step 1 — Name Your Agent
```
@DeepAgent create
```
> DeepAgent: What would you like to name your agent?

```
@DeepAgent Research Assistant
```

#### Step 2 — Define Its Purpose
> DeepAgent: What should this agent do?

```
@DeepAgent Research topics on the web and write comprehensive summaries with citations
```

#### Step 3 — Select Tools
> DeepAgent: Which tools should your agent have?

Available tools:

| Tool | Description |
|------|-------------|
| `execute` | Run shell commands (bash) |
| `read_file` | Read file contents from disk |
| `write_file` | Create or overwrite files |
| `edit_file` | Make targeted edits to existing files |
| `ls` | List directory contents |
| `glob` | Find files matching a pattern |
| `grep` | Search file contents with regex |
| `python_repl` | Execute Python code in a REPL |
| `todo` | Create and manage a task/todo list |

```
@DeepAgent default
```
This selects: `execute, read_file, write_file, edit_file, ls, grep`

You can also type `all`, `none`, or a comma-separated list like `execute, read_file, python_repl`.

#### Step 4 — Select Search Tools
> DeepAgent: Which search tools should your agent use?

Available search tools:

| Tool | Description | API Key Required |
|------|-------------|-----------------|
| `duckduckgo_search` | Web search (free) | None |
| `tavily_search` | AI-powered web search | `TAVILY_API_KEY` |
| `wikipedia` | Wikipedia articles | None |
| `arxiv` | Academic papers | None |
| `pubmed` | Biomedical literature | None |

```
@DeepAgent duckduckgo_search, wikipedia
```

#### Step 5 — Confirm
> DeepAgent: Review your configuration... Type `yes` to save.

```
@DeepAgent yes
```

Your agent is saved and immediately activated!

## Commands Reference

All commands are sent as chat messages to `@DeepAgent`:

| Message | Description |
|---------|-------------|
| `@DeepAgent create` | Start the interactive agent creation wizard |
| `@DeepAgent list` | List all saved agents with their configurations |
| `@DeepAgent use <name>` | Activate a saved agent for the current conversation |
| `@DeepAgent run <name>` | Run a saved agent |
| `@DeepAgent info <name>` | Show detailed configuration for an agent |
| `@DeepAgent delete <name>` | Delete a saved agent |
| `@DeepAgent help` | Show the help menu |

**Note:** Commands are plain keywords after the `@DeepAgent` mention, not slash commands. Messages starting with `/` are intercepted by the Jupyter AI router and will not reach the persona.

## Using a Saved Agent

Once an agent is activated (via creation or `@DeepAgent use <name>`), simply send messages and DeepAgent will process them using the configured agent:

```
@DeepAgent What are the latest advances in quantum computing?
```

The agent will:
1. Use its configured search tools to find relevant information
2. Synthesize findings using the LLM configured in AI Settings
3. Stream the response back to chat

## How LLM Authentication Works

DeepAgent does **not** require its own API keys. It reads the model and credentials from the same configuration that Jupyternaut uses, which is managed through **Settings > AI Settings** in JupyterLab.

Under the hood, this uses [LiteLLM](https://docs.litellm.ai/) via the `ChatLiteLLM` wrapper from `jupyter_ai_jupyternaut`. Any provider that Jupyternaut supports (OpenAI, Anthropic, Azure, Google, AWS Bedrock, etc.) works automatically with DeepAgent.

**To configure:**
1. Open **Settings > AI Settings** in JupyterLab
2. Select a chat model and enter the API key for your provider
3. DeepAgent will use this model for all agents

## Example Agents

### Research Assistant
- **Purpose:** Research topics and write summaries
- **Tools:** `execute, read_file, write_file, edit_file, ls, grep, todo`
- **Search:** `duckduckgo_search, wikipedia, arxiv`

### Code Reviewer
- **Purpose:** Review code for bugs, style issues, and security vulnerabilities
- **Tools:** `read_file, ls, glob, grep`
- **Search:** none

### Data Analyst
- **Purpose:** Analyze CSV/JSON data files and create visualizations
- **Tools:** `execute, read_file, write_file, python_repl, ls, glob`
- **Search:** none

### Full Stack Developer
- **Purpose:** Build and modify web applications with frontend and backend
- **Tools:** `all`
- **Search:** `duckduckgo_search`

A sample agent config is included at `jupyter_ai_deepagent/examples/research_agent.json`.

## Where Are Agents Stored?

Agent configurations are saved as JSON files in:
```
~/.local/share/jupyter/jupyter_ai/deepagents/
```

Each agent is a single `.json` file (e.g., `research_assistant.json`) containing:
```json
{
  "name": "Research Assistant",
  "purpose": "Research topics on the web and write summaries",
  "tools": ["execute", "read_file", "write_file"],
  "search_tools": ["duckduckgo_search", "wikipedia"],
  "system_prompt": ""
}
```

You can edit these files manually if needed. The `system_prompt` field is reserved for future use.

## Troubleshooting

### "Jupyternaut config manager not found"
Make sure `jupyter_ai_jupyternaut` is installed and its server extension is enabled. This package provides the model configuration that DeepAgent relies on.

### "No chat model is configured"
Open **Settings > AI Settings** in JupyterLab and select a chat model. DeepAgent cannot run without one.

### "Missing dependency" error
Install the core packages:
```bash
pip install deepagents jupyter_ai_jupyternaut
```

### Search tool not initializing
- **DuckDuckGo:** Requires the `ddgs` package (installed automatically with `jupyter_ai_deepagent`).
- **Tavily:** Requires `tavily-python` and a `TAVILY_API_KEY` environment variable. Install with:
  ```bash
  pip install tavily-python
  ```
- **Wikipedia / arXiv / PubMed:** Require their respective `langchain_community` extras. Install with:
  ```bash
  pip install wikipedia arxiv xmltodict
  ```

### Agent not responding
Check that:
1. A chat model is configured in **Settings > AI Settings**
2. You are using `@DeepAgent` (not a `/` slash command) before your message
3. The `deepagents` package is installed

### Resetting an agent
Delete and recreate:
```
@DeepAgent delete Research Assistant
@DeepAgent create
```
