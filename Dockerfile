FROM python:3.10-slim

WORKDIR /app

# Copy source code first
COPY src/ ./src/
COPY requirements.txt setup.py ./

# Install dependencies
RUN pip install --no-cache-dir -e .

# Copy the rest of the application
COPY . .

# Make the CLI script executable
RUN chmod +x /app/scripts/cli.py

# Expose the port
EXPOSE 4000

# Set environment variables
ENV PYTHONPATH=/app
ENV NEO4J_URI=bolt://neo4j:7687
ENV NEO4J_USER=neo4j
ENV NEO4J_PASSWORD=password

# Set the entrypoint to run the FastAPI application with reload mode disabled for production
CMD ["uvicorn", "neurodock.main:app", "--host", "0.0.0.0", "--port", "4000", "--workers", "1", "--log-level", "info"]
ENV NEO4J_USER=neo4j
ENV NEO4J_PASSWORD=neurodock

# Command to run the application
CMD ["python", "-m", "neurodock.cli", "serve"]
