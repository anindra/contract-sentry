from typing import Annotated, Sequence
from typing_extensions import TypedDict
import os

from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

# The Enterprise Upgrade: PostgreSQL Memory Checkpointer
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver

from app.schemas import RuleQuery
from app.gateway import fetch_playbook_rule

@tool(args_schema=RuleQuery)
def check_compliance_rule(category: str) -> str:
    """Fetches strict enterprise compliance rules from the corporate playbook."""
    query = RuleQuery(category=category)
    response = fetch_playbook_rule(query)
    return response.rule_text

tools = [check_compliance_rule]
tool_node = ToolNode(tools)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# Point to Docker's internal host mapping for Ollama, fallback to localhost if running natively
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
llm = ChatOllama(model="llama3.2", temperature=0, base_url=OLLAMA_URL)
llm_with_tools = llm.bind_tools(tools)

def reasoning_node(state: AgentState):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

builder = StateGraph(AgentState)
builder.add_node("reasoning", reasoning_node)
builder.add_node("tools", tool_node)
builder.add_edge(START, "reasoning")
builder.add_conditional_edges("reasoning", tools_condition)
builder.add_edge("tools", "reasoning")

# ---------------------------------------------------------
# DATABASE MEMORY SETUP
# ---------------------------------------------------------
DB_URI = os.getenv("POSTGRES_URI")

if DB_URI:
    # PRODUCTION: Use Postgres if the URI is set (e.g., inside Docker)
    pool = ConnectionPool(conninfo=DB_URI)
    memory = PostgresSaver(pool)
    memory.setup() # Automatically creates the LangGraph tables if they don't exist
    print("🟢 Connected to PostgreSQL Checkpointer")
else:
    # DEVELOPMENT: Fallback to RAM if running locally without Docker
    from langgraph.checkpoint.memory import MemorySaver
    memory = MemorySaver()
    print("🟡 Using ephemeral MemorySaver (No Postgres URI found)")

contract_sentry_app = builder.compile(
    checkpointer=memory,
    interrupt_before=["tools"]
)