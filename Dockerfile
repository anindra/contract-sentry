FROM python:3.12-slim

# Install system dependencies required for psycopg and sqlite
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Set up the working directory
WORKDIR /app

# Install uv (The lightning-fast Python package manager)
RUN pip install uv

# Copy your dependency files (assuming you have a requirements.txt or just installing directly)
# For this build, we will let uv install them directly to ensure parity

COPY . /app/

# Install the exact packages we used throughout the week

RUN uv pip install --system fastapi uvicorn pydantic langchain-core langchain-ollama langgraph langgraph-checkpoint-postgres psycopg-pool 'psycopg[binary]'

# Expose the FastAPI port
EXPOSE 8000

# Start the server
CMD ["python", "-m", "app.server"]