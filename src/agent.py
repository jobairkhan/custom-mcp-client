"""LangGraph ReAct agent for Jira→GitHub workflow automation."""

import logging
from typing import Any, Dict, List, Optional, TypedDict, Annotated, Sequence
import operator

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import BaseTool, tool as langchain_tool
from pydantic import BaseModel, Field, ConfigDict

from src.mcp_client import MultiServerMCPClient
from src.settings import get_settings

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the ReAct agent."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    jira_key: str
    iterations: int


class MCPToolWrapper(BaseTool):
    """
    Wrapper to convert MCP tools to LangChain tools.
    
    This allows MCP tools to be used directly with LangGraph without manual wrappers.
    """
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    mcp_client: Any = Field(exclude=True)  # Exclude from Pydantic validation
    tool_name: str = Field(exclude=True)
    tool_description: str = Field(exclude=True)
    tool_schema: Dict[str, Any] = Field(exclude=True)
    
    name: str = ""
    description: str = ""
    
    def __init__(self, mcp_client: MultiServerMCPClient, tool_name: str, 
                 tool_description: str, tool_schema: Dict[str, Any]):
        """Initialize the MCP tool wrapper."""
        # Initialize parent class first
        super().__init__(
            name=tool_name.replace(".", "_"),  # Replace dots for LangChain compatibility
            description=tool_description or "MCP Tool",
            mcp_client=mcp_client,
            tool_name=tool_name,
            tool_description=tool_description,
            tool_schema=tool_schema
        )

    def _run(self, **kwargs: Any) -> str:
        """Synchronous run - not supported for async MCP tools."""
        raise NotImplementedError("Use async version (_arun)")

    async def _arun(self, **kwargs: Any) -> str:
        """Execute the MCP tool asynchronously."""
        try:
            result = await self.mcp_client.call_tool(self.tool_name, kwargs)
            # Format the result as a string
            if hasattr(result, 'content'):
                if isinstance(result.content, list):
                    return "\n".join([str(item.text) if hasattr(item, 'text') else str(item) 
                                    for item in result.content])
                return str(result.content)
            return str(result)
        except Exception as e:
            logger.error(f"Error executing MCP tool {self.tool_name}: {e}")
            return f"Error: {str(e)}"


class ApprenticeAgent:
    """
    LangGraph-based ReAct agent for Jira to GitHub workflow automation.
    
    This agent uses MCP servers to interact with Jira and GitHub,
    automating the process of migrating issues from Jira to GitHub.
    """

    def __init__(self, mcp_client: MultiServerMCPClient):
        """
        Initialize the Apprentice agent.
        
        Args:
            mcp_client: Connected MultiServerMCPClient instance
        """
        self.mcp_client = mcp_client
        self.settings = get_settings()
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=self.settings.openai_api_key
        )
        
        # Create tools from MCP client
        self.tools = self._create_langchain_tools()
        
        # Create the agent graph
        self.graph = self._create_graph()

    def _create_langchain_tools(self) -> List[BaseTool]:
        """Convert MCP tools to LangChain tools dynamically."""
        langchain_tools = []
        
        for tool_name, tool_info in self.mcp_client.get_all_tools().items():
            wrapper = MCPToolWrapper(
                mcp_client=self.mcp_client,
                tool_name=tool_name,
                tool_description=tool_info.get("description", ""),
                tool_schema=tool_info.get("inputSchema", {})
            )
            langchain_tools.append(wrapper)
        
        logger.info(f"Created {len(langchain_tools)} LangChain tools from MCP servers")
        return langchain_tools

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
        
        # Define the routing function
        def should_continue(state: AgentState) -> str:
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
        workflow.add_node("tools", ToolNode(self.tools))
        
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
