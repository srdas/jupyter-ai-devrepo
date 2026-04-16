Using the `jupyter-ai-jupyternaut` submodule as a template, create another persona called `jupyter-ai-quickagent` in its own submodule that implements the langchain deepagents (in https://github.com/langchain-ai/deepagents). 

1. Update all installation files so that the new submodule can be installed with all the other submodules. 
2. Provide full instructions for use. 
3. Provide an example of a deep agent for testing. 
4. Make the quickagent interactive so that it prompts for 
   1. the name of the main agent
   2. what the main agent is supposed to do
   3. If we want to add tools to the main agent - suggest a list of common tools
   4. Suggest a set of possible search tools the agent can use
5. Enable saving the agent and then calling it with a slash command. Include usage instructions in a separate file. 

## Run time instructions

jupyter-ai-quickagent is installed and ready. After running
  just start (or uv run jupyter lab), you can use it:

  1. Open the Jupyter AI chat panel in the left sidebar
  2. Type @QuickAgent to mention the persona — you'll see the
  help menu
  3. Type /quickagent create to interactively build your first
   agent

  Requirements before running:
  - Set at least one LLM API key: export
  ANTHROPIC_API_KEY="sk-ant-..." (or OPENAI_API_KEY)
  - Optionally set TAVILY_API_KEY if you want web search
  tools

  The quickagent entry point is registered alongside
  jupyternaut and the other personas, so persona-manager will
   auto-discover it on startup.

## Commands

New usage (after restarting JupyterLab):                                                                                      
                                                                                                                                
  ┌──────────────────────────────────────┬───────────────────────────┐                                                              
  │          Before (broken)             │      After (works)        │                                                              
  ├──────────────────────────────────────┼───────────────────────────┤                                                              
  │ @QuickAgent /quickagent create       │ @QuickAgent create        │                                                              
  ├──────────────────────────────────────┼───────────────────────────┤                                                              
  │ @QuickAgent /quickagent list         │ @QuickAgent list          │                                                              
  ├──────────────────────────────────────┼───────────────────────────┤                                                              
  │ @QuickAgent /quickagent use My Agent │ @QuickAgent use My Agent  │                                                              
  └──────────────────────────────────────┴───────────────────────────┘                                                              
## Example Agent

Agent NewsAgent saved and activated!

Saved to: /Users/sanjivda/Library/Jupyter/jupyter_ai/quickagents/newsagent.json

You can now send messages and I'll process them with this agent.

You can also invoke it later with <span class="jp-chat-mention">@QuickAgent</span> use NewsAgent.

