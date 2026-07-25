from typing import Annotated, Sequence
from typing_extensions import TypedDict
import os

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

# Import your enterprise schema and secure gateway
from app.schemas import RuleQuery
from app.gateway import fetch_playbook_rule


# ---------------------------------------------------------
# 1. TOOL DEFINITION
# ---------------------------------------------------------
@tool(args_schema=RuleQuery)
def check_compliance_rule(category: str) -> str:
    """
    Fetches strict enterprise compliance rules from the corporate playbook.
    Use this tool whenever you need to check if a contract clause violates company policy.
    """
    query = RuleQuery(category=category)
    response = fetch_playbook_rule(query)
    return response.rule_text


tools = [check_compliance_rule]
tool_node = ToolNode(tools)


# ---------------------------------------------------------
# 2. STATE & LLM SETUP
# ---------------------------------------------------------
class AgentState(TypedDict):
    # Sequential list of messages tracking conversation and tool execution history
    messages: Annotated[Sequence[BaseMessage], add_messages]


# Local deterministic LLM execution binding our schema-driven tools
llm = ChatOllama(model="llama3.2", temperature=0)
llm_with_tools = llm.bind_tools(tools)


# ---------------------------------------------------------
# 3. NODE DEFINITIONS
# ---------------------------------------------------------
def reasoning_node(state: AgentState):
    """The LLM reads message history and decides to either use a tool or output a final answer."""
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


# ---------------------------------------------------------
# 4. COMPILING THE CYCLIC GRAPH WITH MEMORY & BREAKPOINTS
# ---------------------------------------------------------
builder = StateGraph(AgentState)

builder.add_node("reasoning", reasoning_node)
builder.add_node("tools", tool_node)

builder.add_edge(START, "reasoning")
builder.add_conditional_edges("reasoning", tools_condition)
builder.add_edge("tools", "reasoning")

# Define our checkpointer to persist conversation threads in-memory
memory = MemorySaver()

# Compile the graph with two safety overrides:
# 1. 'checkpointer' allows multi-turn thread memory
# 2. 'interrupt_before' freezes the state machine right before executing the tool node
contract_sentry_app = builder.compile(
    checkpointer=memory,
    interrupt_before=["tools"]
)


# ---------------------------------------------------------
# 5. HUMAN-IN-THE-LOOP CLI INTERACTION LOOP
# ---------------------------------------------------------
if __name__ == "__main__":
    print("🤖 ContractSentry Agent Initialized with HITL & State Persistence.")
    print("Type 'exit' to quit.\n")
    
    # We assign a hardcoded thread_id to persist this specific terminal session
    config = {"configurable": {"thread_id": "auditor-terminal-session"}}
    
    while True:
        user_input = input("User > ")
        if user_input.lower() in ["quit", "exit", "q"]:
            break
        
        # 1. Start or continue execution
        events = contract_sentry_app.stream(
            {"messages": [HumanMessage(content=user_input)]},
            config,
            stream_mode="values"
        )
        
        for event in events:
            # We stream values to monitor current execution state
            pass
            
        # 2. Check if the state machine is currently paused at a breakpoint
        state_snapshot = contract_sentry_app.get_state(config)
        
        while state_snapshot.next:
            # If 'next' contains values, it means execution paused at a node (our 'tools' node)
            next_node = state_snapshot.next[0]
            
            if next_node == "tools":
                print("\n⚠️  [BREAKPOINT TRIGGERED] Human Approval Required!")
                
                # Retrieve the last message to inspect what parameters the AI generated
                last_msg = state_snapshot.values["messages"][-1]
                tool_calls = getattr(last_msg, "tool_calls", [])
                
                if tool_calls:
                    call = tool_calls[0]
                    print(f"   🤖 AI wishes to call: {call['name']}")
                    print(f"   📝 Arguments generated: {call['args']}")
                
                # Prompt the auditor for a decision
                approval = input("   👉 Approve this database query? (y/n): ")
                
                if approval.lower() in ["y", "yes", "approve"]:
                    print("   🟢 Action Approved. Resuming graph execution...\n")
                    # To resume execution, invoke the graph with a null input payload
                    events = contract_sentry_app.stream(None, config, stream_mode="values")
                    for event in events:
                        pass
                    # Re-verify the current snapshot status
                    state_snapshot = contract_sentry_app.get_state(config)
                else:
                    print("   🔴 Action Rejected. Halting and wiping pending action.\n")
                    # Clear pending actions to allow a new human turn
                    contract_sentry_app.update_state(config, {"messages": [AIMessage(content="User rejected tool execution.")]}, as_node="reasoning")
                    break
        
        # 3. Print the final synthesized answer once graph run terminates
        state_snapshot = contract_sentry_app.get_state(config)
        final_message = state_snapshot.values["messages"][-1]
        print(f"\nSentry > {final_message.content}\n")