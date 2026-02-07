"""LangGraph ReAct agent for Jira→GitHub workflow automation."""

import logging
from typing import Any, Dict, List, TypedDict, Annotated, Sequence, Literal
import operator

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.tools import BaseTool

from src.mcp_client import MultiServerMCPClient
from src.settings import get_settings

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the ReAct agent."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    jira_key: str
    iterations: int


async def execute_tools(state: AgentState, tools: List[BaseTool]) -> Dict[str, Any]:
    """Execute tools based on the last message's tool calls.
    
    Custom implementation to replace ToolNode from langgraph.prebuilt.
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    tool_messages = []
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        # Create a mapping of tool names to tools
        tools_by_name = {tool.name: tool for tool in tools}
        
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call.get("args", {})
            tool_call_id = tool_call.get("id", "")
            
            logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
            
            if tool_name in tools_by_name:
                try:
                    # Execute the tool
                    result = await tools_by_name[tool_name].ainvoke(tool_args)
                    
                    # Format result as string if needed
                    if isinstance(result, list):
                        content = str(result)
                    else:
                        content = str(result)
                    
                    tool_messages.append(
                        ToolMessage(
                            content=content,
                            tool_call_id=tool_call_id,
                            name=tool_name
                        )
                    )
                except Exception as e:
                    logger.error(f"Error executing tool {tool_name}: {e}")
                    tool_messages.append(
                        ToolMessage(
                            content=f"Error: {str(e)}",
                            tool_call_id=tool_call_id,
                            name=tool_name
                        )
                    )
            else:
                logger.error(f"Tool not found: {tool_name}")
                tool_messages.append(
                    ToolMessage(
                        content=f"Error: Tool {tool_name} not found",
                        tool_call_id=tool_call_id,
                        name=tool_name
                    )
                )
    
    return {"messages": tool_messages}


class ApprenticeAgent:
    """
    LangGraph-based ReAct agent for Jira to GitHub workflow automation.
    
    This agent uses MCP servers to interact with Jira and GitHub,
    automating the process of migrating issues from Jira to GitHub.
    """

    def __init__(self, mcp_client: MultiServerMCPClient, tools: List[BaseTool]):
        """
        Initialize the Apprentice agent.
        
        Args:
            mcp_client: MultiServerMCPClient instance (for reference)
            tools: List of LangChain BaseTool instances from MCP servers
        """
        self.mcp_client = mcp_client
        self.tools = tools
        self.settings = get_settings()
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=self.settings.openai_api_key
        )
        
        logger.info(f"Initialized agent with {len(self.tools)} tool(s)")
        
        # Create the agent graph
        self.graph = self._create_graph()

    def _create_graph(self) -> StateGraph:
        """Create the LangGraph ReAct workflow."""
        
        # Create the prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert assistant that helps migrate Jira issues to GitHub.

Your goal is to:
1. Fetch the Jira issue details using the provided Jira key
2. Extract relevant information (title, description, labels, etc.)
3. Create a corresponding GitHub issue with the extracted information
4. Link back to the original Jira issue if needed
5. Keep the user informed of your actions and any issues you encounter along the way.
6. Keep the comments sync between Jira and GitHub issues until the Jira issue is closed.
7. If the Jira issue is closed, close the GitHub issue as well.
8. If the description is changed in Jira, update the GitHub issue description accordingly.
9. If there is any video or image attachments in Jira, download them and upload to GitHub issue.
10. Add the PR link to the Jira issue when the PR is created.

Use the available MCP tools to interact with Jira and GitHub.
Be concise and efficient in your actions.

Organization: {github_org}
Default Assignee: {github_assignee}
"""),
            MessagesPlaceholder(variable_name="messages"),
        ])

        # Bind tools to LLM
        llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Define the agent node
        async def agent_node(state: AgentState) -> AgentState:
            """Agent reasoning and tool selection node."""
            messages = state["messages"]
            iterations = state.get("iterations", 0)
            
            # Check max iterations
            if iterations >= self.settings.max_iterations:
                logger.warning(f"Max iterations ({self.settings.max_iterations}) reached")
                return {
                    **state,
                    "messages": [AIMessage(content="Maximum iterations reached. Stopping.")],
                }
            
            # Format prompt with settings
            formatted_prompt = prompt.format_messages(
                messages=messages,
                github_org=self.settings.github_org or "N/A",
                github_assignee=self.settings.github_assignee or "N/A"
            )
            
            # Get LLM response
            response = await llm_with_tools.ainvoke(formatted_prompt)
            
            return {
                **state,
                "messages": [response],
                "iterations": iterations + 1
            }
        
        # Define the tool execution node
        async def tools_node(state: AgentState) -> AgentState:
            """Execute tools based on the agent's tool calls."""
            return await execute_tools(state, self.tools)
        
        # Define the routing function
        def should_continue(state: AgentState) -> Literal["continue", "end"]:
            """Determine if we should continue or end."""
            messages = state["messages"]
            last_message = messages[-1]
            
            # If there are tool calls, continue to tools
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "continue"
            
            # Otherwise, end
            return "end"
        
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", agent_node)
        workflow.add_node("tools", tools_node)
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        # Add edges
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        workflow.add_edge("tools", "agent")
        
        return workflow.compile()

    async def run(self, jira_key: str) -> Dict[str, Any]:
        """
        Run the agent to migrate a Jira issue to GitHub.
        
        Args:
            jira_key: The Jira issue key (e.g., PROJ-123)
            
        Returns:
            Dictionary with execution results
        """
        logger.info(f"Starting agent for Jira issue: {jira_key}")
        
        # Initial state
        initial_state = AgentState(
            messages=[
                HumanMessage(content=f"Migrate Jira issue {jira_key} to GitHub. "
                                   f"Fetch the issue details and create a GitHub issue.")
            ],
            jira_key=jira_key,
            iterations=0
        )
        
        # Run the graph
        try:
            final_state = await self.graph.ainvoke(initial_state)
            
            return {
                "success": True,
                "jira_key": jira_key,
                "messages": final_state.get("messages", []),
                "iterations": final_state.get("iterations", 0)
            }
        except Exception as e:
            logger.error(f"Error running agent: {e}")
            return {
                "success": False,
                "jira_key": jira_key,
                "error": str(e)
            }
