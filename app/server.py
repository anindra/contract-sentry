from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
from langchain_core.messages import HumanMessage, AIMessage

# Import our compiled, stateful graph from Day 4
from app.orchestrator import contract_sentry_app

app = FastAPI(title="ContractSentry API")

# --- API CONTRACTS (Pydantic) ---
class ChatRequest(BaseModel):
    thread_id: str
    message: str

class ApproveRequest(BaseModel):
    thread_id: str
    approve: bool

# --- ENDPOINTS ---
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Starts or continues a conversation thread."""
    config = {"configurable": {"thread_id": request.thread_id}}
    
    def event_stream():
        # Stream the graph execution
        events = contract_sentry_app.stream(
            {"messages": [HumanMessage(content=request.message)]},
            config,
            stream_mode="values"
        )
        
        for event in events:
            last_msg = event["messages"][-1]
            
            # Check if the AI wants to call a tool
            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                call = last_msg.tool_calls[0]
                yield f"data: {json.dumps({'type': 'tool_call', 'tool': call['name'], 'args': call['args']})}\n\n"
            
            # Check if it's just the AI talking
            elif last_msg.type == "ai" and last_msg.content:
                yield f"data: {json.dumps({'type': 'message', 'content': last_msg.content})}\n\n"
        
        # Check if execution paused at our HITL breakpoint
        state = contract_sentry_app.get_state(config)
        if state.next and state.next[0] == "tools":
            yield f"data: {json.dumps({'type': 'breakpoint', 'message': '⚠️ Halting execution. Waiting for human approval.'})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'end', 'message': 'Turn complete.'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/approve")
async def approve_endpoint(request: ApproveRequest):
    """Resumes the graph after human approval/rejection."""
    config = {"configurable": {"thread_id": request.thread_id}}
    state = contract_sentry_app.get_state(config)
    
    # Verify the graph is actually waiting at the breakpoint
    if not state.next or state.next[0] != "tools":
        raise HTTPException(status_code=400, detail="No pending tool call to approve on this thread.")
    
    if request.approve:
        # If approved, resume the stream with a None payload
        def resume_stream():
            yield f"data: {json.dumps({'type': 'status', 'message': '🟢 Action Approved. Resuming...'})}\n\n"
            events = contract_sentry_app.stream(None, config, stream_mode="values")
            
            for event in events:
                last_msg = event["messages"][-1]
                if last_msg.type == "ai" and last_msg.content:
                    yield f"data: {json.dumps({'type': 'message', 'content': last_msg.content})}\n\n"
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
            
        return StreamingResponse(resume_stream(), media_type="text/event-stream")
        
    else:
        # If rejected, wipe the pending tool call to prevent an infinite loop
        contract_sentry_app.update_state(
            config, 
            {"messages": [AIMessage(content="User rejected tool execution.")]}, 
            as_node="reasoning"
        )
        return {"status": "🔴 Action Rejected. Halting and awaiting new user input."}

if __name__ == "__main__":
    import uvicorn
    # FDE Note: Running on a single worker is required right now because 
    # MemorySaver lives in RAM. If we used multiple workers, they wouldn't share memory!
    uvicorn.run("app.server:app", host="0.0.0.0", port=8000, reload=True)