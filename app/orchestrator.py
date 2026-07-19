from typing import Annotated
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

# Import your Day 1 architecture
from app.schemas import RuleQuery
from app.gateway import fetch_playbook_rule

# ---------------------------------------------------------
# 1. TOOL DEFINITION
# We use args_schema to bind your Pydantic prompt-injection 
# shield directly to the LangChain tool.
# ---------------------------------------------------------
@tool(args_schema=RuleQuery)
def check_compliance_rule(category: str) -> str:
    """
    Fetches strict enterprise compliance rules from the corporate playbook.
    Use this tool whenever you need to check if a contract clause violates company policy.
    """
    # Wrap the string back into your Pydantic model to hit the gateway
    query = RuleQuery(category=category)
    response = fetch_playbook_rule(query)
    return response.rule_text


# ---------------------------------------------------------
# 2. STATE DEFINITION
# The memory payload passed between nodes in the graph.
# ---------------------------------------------------------
class AgentState(TypedDict):
    # 'add_messages' ensures new messages append to the list rather than overwriting it
    messages: Annotated[list[BaseMessage], add_messages]


# ---------------------------------------------------------
# 3. LLM & GRAPH SETUP
# ---------------------------------------------------------
# Initialize the local LLM. (Make sure you pulled this model via Ollama first!)
# We use temperature=0 for strict, analytical responses.
llm = ChatOllama(model="llama3.2", temperature=0)

# Bind the tool to the LLM so it knows it exists
tools = [check_compliance_rule]
llm_with_tools = llm.bind_tools(tools)

# Define the "Reasoning" Node
def reasoning_node(state: AgentState):
    """The LLM reads the message history and decides what to do next."""
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

# Define the "Acting" Node
tool_node = ToolNode(tools)

# Build the Graph
builder = StateGraph(AgentState)

# Add our two nodes
builder.add_node("reasoning", reasoning_node)
builder.add_node("tools", tool_node)

# Define the flow (Edges)
builder.add_edge(START, "reasoning")

# Conditional Edge: If the LLM wants to use a tool, go to 'tools'. 
# Otherwise, it has the final answer, so go to END.
builder.add_conditional_edges("reasoning", tools_condition)

# After a tool runs, ALWAYS go back to reasoning so the LLM can read the result
builder.add_edge("tools", "reasoning")

# Compile the graph into an executable application
contract_sentry_app = builder.compile()

# ---------------------------------------------------------
# 4. EXECUTION TEST
# ---------------------------------------------------------
if __name__ == "__main__":
    print("🤖 ContractSentry Agent Initialized.")
    print("Type 'exit' to quit.\n")
    
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            break
            
        # Execute the graph
        result = contract_sentry_app.invoke(
            {"messages": [HumanMessage(content=user_input)]}
        )
        
        # The final message in the state is the LLM's final answer
        print(f"\nSentry: {result['messages'][-1].content}\n")