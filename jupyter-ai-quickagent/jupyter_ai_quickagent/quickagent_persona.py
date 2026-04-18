"""QuickAgent persona for Jupyter AI using LangChain Deep Agents."""

import os
from typing import Any, Optional

from jupyter_ai_persona_manager import BasePersona, PersonaDefaults
from jupyterlab_chat.models import Message

from .agent_store import (
    COMMON_TOOLS,
    SEARCH_TOOL_API_KEYS,
    SEARCH_TOOLS,
    AgentConfig,
    delete_agent,
    list_agents,
    load_agent,
    save_agent,
)
from .prompt_template import QUICKAGENT_SYSTEM_PROMPT_TEMPLATE

QUICKAGENT_AVATAR_PATH = str(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "static", "quickagent.svg")
    )
)

# Interactive setup states
STATE_IDLE = "idle"
STATE_ASK_NAME = "ask_name"
STATE_ASK_PURPOSE = "ask_purpose"
STATE_ASK_TOOLS = "ask_tools"
STATE_ASK_SEARCH = "ask_search"
STATE_ASK_API_KEY = "ask_api_key"
STATE_ASK_SKILLS = "ask_skills"
STATE_CONFIRM = "confirm"


class QuickAgentPersona(BasePersona):
    """
    A Jupyter AI persona that creates and runs LangChain Deep Agents.

    Supports an interactive setup flow where users configure:
    - Agent name and purpose
    - Common tools (file ops, shell, Python REPL, etc.)
    - Search tools (Tavily, DuckDuckGo, Wikipedia, etc.)

    Saved agents persist to disk and can be invoked by name.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_state: str = STATE_IDLE
        self._pending_config: dict[str, Any] = {}
        self._active_agent_name: Optional[str] = None

    @property
    def defaults(self):
        return PersonaDefaults(
            name="QuickAgent",
            avatar_path=QUICKAGENT_AVATAR_PATH,
            description=(
                "An interactive quick agent builder powered by LangChain Deep Agents. "
                "Create, configure, save, and run autonomous agents with tools and search."
            ),
            system_prompt="You are QuickAgent, an AI agent builder for JupyterLab.",
        )

    def _strip_mention(self, body: str) -> str:
        """Strip @QuickAgent (or any @mention of this persona) from the message body."""
        import re
        # Remove @-mentions that match this persona's name (case-insensitive)
        cleaned = re.sub(r"@\S+\s*", "", body, count=1).strip()
        return cleaned

    async def process_message(self, message: Message) -> None:
        body = self._strip_mention(message.body.strip())

        # If in interactive setup flow, continue it (takes priority over commands)
        if self._setup_state != STATE_IDLE:
            await self._handle_setup_step(body)
            return

        # Handle commands (e.g. "create", "list", "use MyAgent")
        first_word = body.split()[0].lower() if body else ""
        if first_word in ("create", "list", "use", "delete", "info", "run", "help"):
            await self._handle_command(body)
            return

        # If there's an active agent, run the message through it
        if self._active_agent_name:
            await self._run_agent(self._active_agent_name, body, message)
            return

        # Default: show help
        await self._show_help()

    async def _handle_command(self, body: str) -> None:
        # body is already stripped of @mention, e.g. "create", "use My Agent", "list"
        parts = body.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd == "create":
            await self._start_setup()
        elif cmd == "list":
            await self._list_agents()
        elif cmd == "run" and arg:
            await self._run_agent(arg, None, None)
        elif cmd == "use" and arg:
            config = load_agent(arg)
            if config:
                self._active_agent_name = arg
                self.send_message(
                    f"**Switched to agent: {config.name}**\n\n"
                    f"*{config.purpose}*\n\n"
                    "Send me a message and I'll process it with this agent. "
                    "Say `create` to make a new agent or `list` to see all agents."
                )
            else:
                self.send_message(
                    f"Agent **{arg}** not found. Say `list` to see saved agents."
                )
        elif cmd == "delete" and arg:
            if delete_agent(arg):
                if self._active_agent_name == arg:
                    self._active_agent_name = None
                self.send_message(f"Deleted agent **{arg}**.")
            else:
                self.send_message(f"Agent **{arg}** not found.")
        elif cmd == "info" and arg:
            await self._show_agent_info(arg)
        else:
            await self._show_help()

    async def _show_help(self) -> None:
        agents = list_agents()
        agent_list = ""
        if agents:
            agent_list = "\n\n**Saved agents:**\n"
            for a in agents:
                agent_list += f"- `{a.name}` — {a.purpose}\n"

        self.send_message(
            "**QuickAgent** — Build and run autonomous agents in JupyterLab\n\n"
            "**Commands** (send as a message to @QuickAgent):\n"
            "- `create` — Interactively create a new agent\n"
            "- `list` — List all saved agents\n"
            "- `use <name>` — Activate a saved agent for conversation\n"
            "- `run <name>` — Run a saved agent\n"
            "- `info <name>` — Show agent configuration details\n"
            "- `delete <name>` — Delete a saved agent\n"
            "- `help` — Show this help message\n"
            f"{agent_list}\n"
            "To get started, send `@QuickAgent create` to build your first agent!"
        )

    async def _list_agents(self) -> None:
        agents = list_agents()
        if not agents:
            self.send_message(
                "No saved agents yet. Say `create` to build one!"
            )
            return

        lines = ["**Saved Quick Agents:**\n"]
        for a in agents:
            tools = ", ".join(a.tools) if a.tools else "none"
            search = ", ".join(a.search_tools) if a.search_tools else "none"
            skills = a.skills_dir if a.skills_dir else "none"
            active = " *(active)*" if a.name == self._active_agent_name else ""
            lines.append(
                f"### {a.name}{active}\n"
                f"- **Purpose:** {a.purpose}\n"
                f"- **Tools:** {tools}\n"
                f"- **Search:** {search}\n"
                f"- **Skills dir:** {skills}\n"
            )
        self.send_message("\n".join(lines))

    async def _show_agent_info(self, name: str) -> None:
        config = load_agent(name)
        if not config:
            self.send_message(f"Agent **{name}** not found.")
            return

        tools_desc = "\n".join(
            f"  - `{t}`: {COMMON_TOOLS.get(t, SEARCH_TOOLS.get(t, 'custom'))}"
            for t in config.tools
        )
        search_desc = "\n".join(
            f"  - `{t}`: {SEARCH_TOOLS.get(t, 'custom')}"
            for t in config.search_tools
        )
        skills_display = config.skills_dir if config.skills_dir else "none"

        # Show the model from jupyternaut AI settings
        cm = self._get_config_manager()
        model_display = cm.chat_model if cm and cm.chat_model else "(not configured)"

        self.send_message(
            f"## Agent: {config.name}\n\n"
            f"**Purpose:** {config.purpose}\n\n"
            f"**Model (from AI Settings):** `{model_display}`\n\n"
            f"**Tools:**\n{tools_desc or '  none'}\n\n"
            f"**Search tools:**\n{search_desc or '  none'}\n\n"
            f"**Skills directory:** `{skills_display}`\n\n"
            f"Say `use {config.name}` to activate this agent."
        )

    # ---- Interactive setup flow ----

    async def _start_setup(self) -> None:
        self._setup_state = STATE_ASK_NAME
        self._pending_config = {}
        self.send_message(
            "**Let's create a new Quick Agent!**\n\n"
            "**Step 1/5:** What would you like to name your agent?\n\n"
            "*(e.g., `Research Assistant`, `Code Reviewer`, `Data Analyst`)*"
        )

    async def _handle_setup_step(self, body: str) -> None:
        if self._setup_state == STATE_ASK_NAME:
            self._pending_config["name"] = body
            self._setup_state = STATE_ASK_PURPOSE
            self.send_message(
                f"Great! Your agent will be called **{body}**.\n\n"
                "**Step 2/5:** What should this agent do? Describe its purpose.\n\n"
                "*(e.g., `Research topics on the web and write comprehensive summaries`, "
                "`Review Python code for bugs and suggest improvements`, "
                "`Analyze CSV data files and create visualizations`)*"
            )

        elif self._setup_state == STATE_ASK_PURPOSE:
            self._pending_config["purpose"] = body
            self._setup_state = STATE_ASK_TOOLS

            tools_list = "\n".join(
                f"  {i+1}. `{name}` — {desc}"
                for i, (name, desc) in enumerate(COMMON_TOOLS.items())
            )
            self.send_message(
                "**Step 3/5:** Which tools should your agent have?\n\n"
                f"**Available tools:**\n{tools_list}\n\n"
                "Enter the tool names separated by commas, or type:\n"
                "- `all` for all tools\n"
                "- `none` to skip\n"
                "- `default` for `execute, read_file, write_file, edit_file, ls, grep`\n\n"
                "*(e.g., `execute, read_file, write_file, python_repl`)*"
            )

        elif self._setup_state == STATE_ASK_TOOLS:
            tools = self._parse_tool_selection(body, COMMON_TOOLS)
            self._pending_config["tools"] = tools
            self._setup_state = STATE_ASK_SEARCH

            search_list = "\n".join(
                f"  {i+1}. `{name}` — {desc}"
                for i, (name, desc) in enumerate(SEARCH_TOOLS.items())
            )
            self.send_message(
                "**Step 4/5:** Which search tools should your agent use?\n\n"
                f"**Available search tools:**\n{search_list}\n\n"
                "Enter the tool names separated by commas, or type:\n"
                "- `all` for all search tools\n"
                "- `none` to skip\n\n"
                "*(Note: Some search tools require API keys set as environment variables)*"
            )

        elif self._setup_state == STATE_ASK_SEARCH:
            search_tools = self._parse_tool_selection(body, SEARCH_TOOLS)
            self._pending_config["search_tools"] = search_tools

            # Check for missing API keys
            missing_keys = self._get_missing_api_keys(search_tools)
            if missing_keys:
                self._pending_config["_missing_keys"] = list(missing_keys.items())
                self._setup_state = STATE_ASK_API_KEY
                env_var, tool_name = self._pending_config["_missing_keys"][0]
                self.send_message(
                    f"**API key required:** The `{tool_name}` tool needs "
                    f"the `{env_var}` environment variable.\n\n"
                    f"Please enter your `{env_var}` value, or type `skip` to "
                    f"remove this tool from the agent."
                )
            else:
                self._setup_state = STATE_ASK_SKILLS
                self._prompt_skills_dir()

        elif self._setup_state == STATE_ASK_API_KEY:
            missing_keys = self._pending_config.get("_missing_keys", [])
            if not missing_keys:
                self._setup_state = STATE_ASK_SKILLS
                self._prompt_skills_dir()
                return

            env_var, tool_name = missing_keys[0]
            if body.strip().lower() == "skip":
                # Remove this tool from the selection
                self._pending_config["search_tools"] = [
                    t for t in self._pending_config["search_tools"] if t != tool_name
                ]
                self.send_message(f"Removed `{tool_name}` from agent tools.")
            else:
                os.environ[env_var] = body.strip()
                self.send_message(f"`{env_var}` set for this session.")

            missing_keys.pop(0)
            if missing_keys:
                self._pending_config["_missing_keys"] = missing_keys
                env_var, tool_name = missing_keys[0]
                self.send_message(
                    f"**API key required:** The `{tool_name}` tool needs "
                    f"the `{env_var}` environment variable.\n\n"
                    f"Please enter your `{env_var}` value, or type `skip` to "
                    f"remove this tool from the agent."
                )
            else:
                self._pending_config.pop("_missing_keys", None)
                self._setup_state = STATE_ASK_SKILLS
                self._prompt_skills_dir()

        elif self._setup_state == STATE_ASK_SKILLS:
            skills_dir = self._parse_skills_dir(body)
            self._pending_config["skills_dir"] = skills_dir
            self._setup_state = STATE_CONFIRM

            config_data = {k: v for k, v in self._pending_config.items() if not k.startswith("_")}
            config = AgentConfig(**config_data)
            tools_str = ", ".join(config.tools) if config.tools else "none"
            search_str = ", ".join(config.search_tools) if config.search_tools else "none"
            skills_str = config.skills_dir if config.skills_dir else "none"

            self.send_message(
                "**Review your agent configuration:**\n\n"
                f"- **Name:** {config.name}\n"
                f"- **Purpose:** {config.purpose}\n"
                f"- **Tools:** {tools_str}\n"
                f"- **Search tools:** {search_str}\n"
                f"- **Skills directory:** {skills_str}\n\n"
                "Type `yes` to save, or `no` to cancel."
            )

        elif self._setup_state == STATE_CONFIRM:
            if body.lower() in ("yes", "y", "save", "ok"):
                config_data = {k: v for k, v in self._pending_config.items() if not k.startswith("_")}
                config = AgentConfig(**config_data)
                path = save_agent(config)
                self._active_agent_name = config.name
                self._setup_state = STATE_IDLE
                self._pending_config = {}
                self.send_message(
                    f"**Agent `{config.name}` saved and activated!**\n\n"
                    f"Saved to: `{path}`\n\n"
                    f"You can now send messages and I'll process them with this agent.\n\n"
                    f"You can also invoke it later with `@QuickAgent use {config.name}`."
                )
            else:
                self._setup_state = STATE_IDLE
                self._pending_config = {}
                self.send_message("Agent creation cancelled.")

    def _parse_tool_selection(
        self, body: str, available: dict[str, str]
    ) -> list[str]:
        lower = body.strip().lower()
        if lower == "none":
            return []
        if lower == "all":
            return list(available.keys())
        if lower == "default" and available is COMMON_TOOLS:
            return ["execute", "read_file", "write_file", "edit_file", "ls", "grep"]

        selected = []
        for part in body.split(","):
            name = part.strip().lower()
            if name in available:
                selected.append(name)
        return selected

    def _get_missing_api_keys(self, search_tools: list[str]) -> dict[str, str]:
        """Return {env_var: tool_name} for tools that need an API key not currently set."""
        missing = {}
        for tool_name in search_tools:
            env_var = SEARCH_TOOL_API_KEYS.get(tool_name)
            if env_var and not os.environ.get(env_var):
                missing[env_var] = tool_name
        return missing

    def _prompt_skills_dir(self) -> None:
        """Send the skills directory prompt message."""
        self.send_message(
            "**Step 5/5:** Do you have a **skills directory** for this agent?\n\n"
            "A skills directory contains `.md` files with specialized instructions, "
            "domain knowledge, or workflows that the agent should follow. "
            "All `.md` files in the directory will be loaded into the agent's context.\n\n"
            "Enter the directory path, or type `none` to skip.\n\n"
            "*(Use `~` for your home directory, e.g. `~/skills` or `~/projects/my-skills`)*\n\n"
            "**Note:** Avoid starting with `/` — use `~` or a relative path instead."
        )

    def _parse_skills_dir(self, body: str) -> str:
        """Parse a skills directory path from user input."""
        lower = body.strip().lower()
        if lower in ("none", "skip", ""):
            return ""

        path = body.strip()
        expanded = os.path.expanduser(path)
        return os.path.abspath(expanded)

    def _find_project_root(self, skills_dir: str) -> str:
        """Walk up from the skills directory to find the project root.

        Looks for a directory containing .claude, .git, or pyproject.toml.
        Falls back to the parent of .claude if found in the path.
        """
        path = os.path.abspath(skills_dir)
        # If .claude is in the path, the project root is its parent
        parts = path.split(os.sep)
        if ".claude" in parts:
            idx = parts.index(".claude")
            return os.sep.join(parts[:idx])
        # Otherwise walk up looking for project markers
        current = path
        for _ in range(10):
            parent = os.path.dirname(current)
            if parent == current:
                break
            if any(
                os.path.exists(os.path.join(parent, marker))
                for marker in (".git", ".claude", "pyproject.toml", "package.json")
            ):
                return parent
            current = parent
        return os.path.dirname(skills_dir)

    def _load_skill_content(self, skills_dir: str) -> tuple[str, list[str]]:
        """Load all .md files from the skills directory, recursively.

        Returns a tuple of (concatenated content, list of relative paths loaded).
        """
        if not skills_dir or not os.path.isdir(skills_dir):
            return "", []

        sections = []
        loaded_paths = []
        for dirpath, _, filenames in os.walk(skills_dir):
            for filename in sorted(filenames):
                if filename.endswith(".md"):
                    filepath = os.path.join(dirpath, filename)
                    rel_path = os.path.relpath(filepath, skills_dir)
                    try:
                        with open(filepath) as f:
                            content = f.read()
                        sections.append(
                            f"--- Skill: {rel_path} ---\n{content}"
                        )
                        loaded_paths.append(rel_path)
                    except OSError:
                        pass
        return "\n\n".join(sections), loaded_paths

    # ---- LLM from jupyternaut config ----

    def _get_config_manager(self):
        """
        Get the ConfigManager from jupyternaut's server extension settings.
        This reuses whatever LLM the user has already authenticated in
        Jupyter AI's 'Settings > AI Settings'.

        Chain: persona.parent -> PersonaManager
               PersonaManager.parent -> PersonaManagerExtension
               extension.serverapp.web_app.settings -> global settings dict
        """
        try:
            # self.parent = PersonaManager, self.parent.parent = PersonaManagerExtension
            settings = self.parent.parent.serverapp.web_app.settings
            cm = settings.get("jupyternaut.config_manager")
            if cm is not None:
                return cm
        except AttributeError:
            pass
        return None

    def _get_chat_model(self):
        """
        Build a ChatLiteLLM instance using the model and credentials
        configured in Jupyter AI settings (same model as Jupyternaut).
        """
        from jupyter_ai_jupyternaut.jupyternaut.chat_models import ChatLiteLLM

        cm = self._get_config_manager()
        if cm is None:
            raise RuntimeError(
                "Jupyternaut config manager not found. "
                "Make sure jupyter_ai_jupyternaut is installed and a chat model "
                "is configured in Settings > AI Settings."
            )

        model_id = cm.chat_model
        if not model_id:
            raise RuntimeError(
                "No chat model is configured. "
                "Please set one in Settings > AI Settings first."
            )

        model_args = cm.chat_model_args
        return ChatLiteLLM(**model_args, model=model_id, streaming=True)

    # ---- Agent execution ----

    async def _run_agent(
        self,
        agent_name: str,
        user_message: Optional[str],
        message: Optional[Message],
    ) -> None:
        config = load_agent(agent_name)
        if not config:
            self.send_message(
                f"Agent **{agent_name}** not found. "
                "Say `list` to see saved agents."
            )
            return

        if not user_message:
            self.send_message(
                f"**Agent `{config.name}` is ready.**\n\n"
                f"*{config.purpose}*\n\n"
                "Send a message and I'll process it with this agent."
            )
            self._active_agent_name = config.name
            return

        try:
            model = self._get_chat_model()

            context = ""
            if message:
                context = self.process_attachments(message) or ""
                context = f"User's username is '{message.sender}'\n\n" + context

            skill_content = ""
            skill_names: list[str] = []
            if config.skills_dir:
                skill_content, skill_names = self._load_skill_content(config.skills_dir)

            display_skills = [
                s for s in skill_names
                if "skills" in os.path.join(config.skills_dir, s).split(os.sep)
            ]
            if display_skills:
                skills_list = ", ".join(f"`{s}`" for s in display_skills)
                self.send_message(f"**Using skills:** {skills_list}")

            skills_dir = config.skills_dir
            skills_dir_parent = self._find_project_root(skills_dir) if skills_dir else ""

            system_prompt = QUICKAGENT_SYSTEM_PROMPT_TEMPLATE.render(
                persona_name=config.name,
                purpose=config.purpose,
                context=context,
                skills=skill_content,
                skills_dir=skills_dir,
                skills_dir_parent=skills_dir_parent,
                home_dir=os.path.expanduser("~"),
            )

            agent = self._build_agent(config, model, system_prompt)

            # Run the deep agent and stream the response
            async def create_aiter():
                async for token, metadata in agent.astream(
                    {"messages": [{"role": "user", "content": user_message}]},
                    stream_mode="messages",
                ):
                    node = metadata.get("langgraph_node", "")
                    if node == "model" and hasattr(token, "text") and token.text:
                        yield token.text

            response_aiter = create_aiter()
            await self.stream_message(response_aiter)

        except RuntimeError as e:
            self.send_message(str(e))
        except ImportError as e:
            self.send_message(
                f"**Missing dependency:** {e}\n\n"
                "Please install the required packages:\n"
                "```bash\n"
                "pip install deepagents jupyter_ai_quickagent\n"
                "```"
            )
        except Exception as e:
            self.log.exception("Error running deep agent.")
            self.send_message(f"**Error running agent:** {e}")

    def _build_agent(self, config: AgentConfig, model, system_prompt: str):
        """Build a deep agent from a saved configuration, using the provided LLM."""
        from pathlib import Path

        from deepagents import create_deep_agent
        from deepagents.backends import LocalShellBackend

        tools = self._resolve_tools(config)

        backend = LocalShellBackend(
            root_dir=Path.home(),
            virtual_mode=False,
        )

        agent = create_deep_agent(
            model=model,
            tools=tools,
            system_prompt=system_prompt,
            backend=backend,
        )
        return agent

    def _resolve_tools(self, config: AgentConfig) -> list:
        """Resolve tool names to actual LangChain tool objects."""
        tools = []

        # Common tools (most are built-in to deepagents; we only add custom ones)
        for tool_name in config.tools:
            tool = self._get_common_tool(tool_name)
            if tool:
                tools.append(tool)

        # Search tools
        for tool_name in config.search_tools:
            tool = self._get_search_tool(tool_name)
            if tool:
                tools.append(tool)

        return tools

    def _get_common_tool(self, name: str):
        """Get a common tool by name. Returns None for tools provided by deepagents natively."""
        try:
            if name == "web_fetch":
                return self._make_web_fetch_tool()
        except Exception as e:
            self.log.warning(f"Common tool '{name}' failed to initialize: {e}")
        return None

    def _make_web_fetch_tool(self):
        """Create a web_fetch tool that fetches content from a URL."""
        from langchain_core.tools import tool

        @tool
        def web_fetch(url: str) -> str:
            """Fetch and return the text content of a web page at the given URL."""
            import httpx
            from html.parser import HTMLParser

            class _TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self._pieces: list[str] = []
                    self._skip = False

                def handle_starttag(self, tag, attrs):
                    if tag in ("script", "style", "noscript"):
                        self._skip = True

                def handle_endtag(self, tag):
                    if tag in ("script", "style", "noscript"):
                        self._skip = False

                def handle_data(self, data):
                    if not self._skip:
                        text = data.strip()
                        if text:
                            self._pieces.append(text)

                def get_text(self) -> str:
                    return "\n".join(self._pieces)

            try:
                resp = httpx.get(url, follow_redirects=True, timeout=30)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                return f"Error fetching URL: {e}"

            content_type = resp.headers.get("content-type", "")
            if "html" in content_type:
                extractor = _TextExtractor()
                extractor.feed(resp.text)
                return extractor.get_text()[:50000]
            else:
                return resp.text[:50000]

        return web_fetch

    def _get_search_tool(self, name: str):
        """Get a search tool by name, returning None if unavailable."""
        try:
            if name == "tavily_search":
                from langchain_community.tools.tavily_search import (
                    TavilySearchResults,
                )
                return TavilySearchResults(max_results=5)
            elif name == "duckduckgo_search":
                from langchain_community.tools import DuckDuckGoSearchResults
                return DuckDuckGoSearchResults()
            elif name == "wikipedia":
                from langchain_community.tools import WikipediaQueryRun
                from langchain_community.utilities import WikipediaAPIWrapper
                return WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
            elif name == "arxiv":
                from langchain_community.tools import ArxivQueryRun
                from langchain_community.utilities import ArxivAPIWrapper
                return ArxivQueryRun(api_wrapper=ArxivAPIWrapper())
            elif name == "pubmed":
                from langchain_community.tools import PubmedQueryRun
                from langchain_community.utilities import PubMedAPIWrapper
                return PubmedQueryRun(api_wrapper=PubMedAPIWrapper())
        except ImportError as e:
            self.log.warning(f"Search tool '{name}' not available (missing dependency): {e}")
        except Exception as e:
            self.log.warning(f"Search tool '{name}' failed to initialize: {e}")
        return None
