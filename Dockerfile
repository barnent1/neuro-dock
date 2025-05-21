FROM python:3.10-slim

WORKDIR /app

# Copy source code first

# Copy requirements and setup first for better cache
COPY requirements.txt setup.py ./

# Install dependencies
RUN pip install --no-cache-dir -e .

# Copy source code and the rest of the application
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY bin/ ./bin/
COPY neurodock.json ./
COPY run.sh ./
COPY run_mcp_tests.sh ./
COPY start_memory_dashboard.sh ./
COPY docker.sh ./
COPY MEMORY.md ./
COPY README.md ./
COPY PROJECT_STRUCTURE.md ./
COPY MEMORY_DASHBOARD.md ./
COPY MEMORY_DASHBOARD_IMPLEMENTATION.md ./
COPY IMPLEMENTATION_REPORT.md ./
COPY docker-compose.yml ./

# (Optional) Make CLI script executable if needed
# RUN chmod +x /app/scripts/cli.py

# Expose the port
EXPOSE 4000

# Set environment variables
ENV PYTHONPATH=/app
ENV NEO4J_URI=bolt://neo4j:7687
ENV NEO4J_USER=neo4j
ENV NEO4J_PASSWORD=neurodock

# Set the entrypoint to run the FastAPI application with reload mode disabled for production
CMD ["uvicorn", "neurodock.main:app", "--host", "0.0.0.0", "--port", "4000", "--workers", "1", "--log-level", "info"]
