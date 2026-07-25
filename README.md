# 🛡️ ContractSentry

ContractSentry is an enterprise-grade AI contract compliance audit tool. It utilizes a LangGraph-powered **ReAct (Reason + Act)** agent to evaluate complex legal contracts against strict corporate playbooks.

Built with an emphasis on **Security, State Persistence, and Human-in-the-Loop (HITL) architecture**, ContractSentry ensures that AI-driven database queries are strictly validated and manually approved before execution.

## ✨ Enterprise Features

* **🔄 Cyclic ReAct Agent (LangGraph):** Dynamically loops between reasoning and tool execution to solve multi-step compliance queries.
* **🛑 Human-in-the-Loop (HITL):** Execution automatically halts before sensitive database queries, requiring asynchronous human approval via a dedicated REST endpoint.
* **📡 Asynchronous SSE Streaming:** Streams agent thoughts, tool calls, and breakpoints in real-time to front-end clients using Server-Sent Events (FastAPI).
* **💾 State Persistence (PostgreSQL):** Agent conversational memory and execution states are stored in Postgres, allowing threads to survive server restarts and scale across multiple workers.
* **🛡️ Secure Data Abstraction:** Strict type-checking boundaries (Pydantic) and parameterized SQL queries (SQLite) neutralize prompt injection attacks targeting the backend playbook.
* **🔒 Local LLM Execution:** Runs entirely locally using Meta's `llama3.2` for zero-latency, zero-cost, and high-privacy inference.

## 🏗️ Architecture Stack

| Layer | Technology | Purpose | 
| ----- | ----- | ----- | 
| **Orchestration** | LangGraph & LangChain | ReAct loop and state machine | 
| **API Gateway** | FastAPI & Uvicorn | Async REST endpoints and SSE Streaming | 
| **AI Runtime** | Ollama (`llama3.2`) | Local tool-calling inference | 
| **State Memory** | PostgreSQL | LangGraph Checkpointer (Thread memory) | 
| **Knowledge Base** | SQLite | Read-only enterprise compliance playbook | 
| **Infrastructure** | Docker & Docker Compose | Containerization and service orchestration | 

## 🚀 Quickstart

### 1. Prerequisites
* [Docker & Docker Compose](https://www.docker.com/)
* [Ollama](https://ollama.com/) (Running locally on your host machine)

### 2. Pull the LLM
Before starting the containers, ensure the host machine has the required tool-calling model cached in Ollama:
` ` `bash
ollama pull llama3.2
` ` `

### 3. Spin up the Cluster
Start the FastAPI gateway and the PostgreSQL state database using Docker Compose:
` ` `bash
docker-compose up --build
` ` `

## 🔌 API Usage

ContractSentry uses a decoupled, asynchronous API design to support Human-in-the-Loop workflows.

> **Step 1: Initiate a Chat (Streamed)**
> Ask the agent to review a contract term. The agent will stream its thoughts, determine it needs to query the playbook, and **hit a breakpoint**.

` ` `bash
curl -X POST http://localhost:8000/chat \
-H "Content-Type: application/json" \
-d '{"thread_id": "audit-session-01", "message": "The vendor wants a $500k liability cap. Is this allowed?"}'
` ` `
*Expected Output: The stream will emit a `tool_call` event and safely close with a `breakpoint` status, freezing the state in PostgreSQL.*

> **Step 2: Approve the Action**
> Act as the Human-in-the-Loop. Approve the pending database tool call for the exact same `thread_id`.

` ` `bash
curl -X POST http://localhost:8000/approve \
-H "Content-Type: application/json" \
-d '{"thread_id": "audit-session-01", "approve": true}'
` ` `
*Expected Output: The agent resumes from Postgres memory, executes the SQLite query, and streams back the final compliance decision.*

## 🧪 Security & Red Teaming

ContractSentry includes an automated Red Team test suite to verify the Pydantic guardrails against classic prompt injection attacks. To run the attack simulation:

` ` `bash
python -m tests.red_team
` ` `
*The agent will successfully reject attempts to bypass the schema or extract raw SQL structure.*
