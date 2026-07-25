🛡️ ContractSentry

ContractSentry is an enterprise-grade AI contract compliance audit tool. It utilizes a LangGraph-powered ReAct (Reason + Act) agent to evaluate complex legal contracts against strict corporate playbooks.

Built with an emphasis on Security, State Persistence, and Human-in-the-Loop (HITL) architecture, ContractSentry ensures that AI-driven database queries are strictly validated and manually approved before execution.

✨ Enterprise Features

Cyclic ReAct Agent (LangGraph): Dynamically loops between reasoning and tool execution to solve multi-step compliance queries.

Human-in-the-Loop (HITL) Breakpoints: Execution automatically halts before sensitive database queries, requiring an asynchronous human approval via a dedicated REST endpoint.

Asynchronous SSE Streaming (FastAPI): Streams agent thoughts, tool calls, and breakpoints in real-time to front-end clients using Server-Sent Events.

State Persistence (PostgreSQL): Agent conversational memory and execution states are stored in Postgres, allowing threads to survive server restarts and scale across multiple workers.

Secure Data Abstraction (Pydantic & SQLite): Strict type-checking boundaries and parameterized SQL queries completely neutralize prompt injection attacks targeting the backend playbook.

Local LLM Execution (Ollama): Runs entirely locally using Meta's llama3.2 (fine-tuned for tool calling) for zero-latency, zero-cost, and high-privacy inference.

🏗️ Architecture Stack

Orchestration: LangGraph, LangChain

API Gateway: FastAPI, Uvicorn (Server-Sent Events)

Local AI: Ollama (llama3.2)

Databases: PostgreSQL (State/Checkpoints), SQLite (Enterprise Playbook)

Containerization: Docker, Docker Compose

Package Management: uv

🚀 Quickstart

1. Prerequisites

Docker & Docker Compose

Ollama (Running locally on your host machine)

2. Pull the LLM

Before starting the containers, ensure the host machine has the required tool-calling model cached in Ollama:

ollama pull llama3.2


3. Spin up the Cluster

Start the FastAPI gateway and the PostgreSQL state database using Docker Compose:

docker-compose up --build


🔌 API Usage

ContractSentry uses a decoupled, asynchronous API design to support Human-in-the-Loop workflows.

Step 1: Initiate a Chat (Streamed)

Ask the agent to review a contract term. The agent will stream its thoughts, determine it needs to query the playbook, and hit a breakpoint.

curl -X POST http://localhost:8000/chat \
-H "Content-Type: application/json" \
-d '{"thread_id": "audit-session-01", "message": "The vendor wants a $500k liability cap. Is this allowed?"}'


Expected Output: The stream will emit a tool_call event and safely close with a breakpoint status, freezing the state in PostgreSQL.

Step 2: Approve the Action

Act as the Human-in-the-Loop. Approve the pending database tool call for the exact same thread_id.

curl -X POST http://localhost:8000/approve \
-H "Content-Type: application/json" \
-d '{"thread_id": "audit-session-01", "approve": true}'


Expected Output: The agent resumes from Postgres memory, executes the SQLite query, and streams back the final compliance decision.

🧪 Security & Red Teaming

ContractSentry includes an automated Red Team test suite to verify the Pydantic guardrails against classic prompt injection attacks.

To run the attack simulation:

python -m tests.red_team


The agent will successfully reject attempts to bypass the schema or extract raw SQL structure.

📁 Project Structure

contract-sentry/
├── docker-compose.yml      # Multi-container orchestration (API + Postgres)
├── Dockerfile              # FastAPI application image
├── data/
│   └── playbook.db         # Seeded SQLite database (Read-Only Knowledge)
├── app/
│   ├── schemas.py          # SSOT Pydantic Models for Tool Calling
│   ├── gateway.py          # Parameterized DB access & absolute pathing
│   ├── orchestrator.py     # LangGraph State Machine & Postgres Checkpointer
│   ├── server.py           # FastAPI SSE & HITL Endpoints
│   └── playbook_server.py  # FastMCP stdio tool server (Legacy/Internal)
└── tests/
    └── red_team.py         # Automated Prompt Injection guardrail tests
