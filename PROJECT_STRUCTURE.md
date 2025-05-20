# Project Structure

The NeuroDock project follows a professional Python package structure:

```
neuro-dock/                # Project root
├── backup/                # Backup of old structure
├── bin/                   # Executable scripts
│   ├── memory-dashboard   # Script to start the memory dashboard
│   └── neurodock          # Main executable script
├── docs/                  # Documentation
├── src/                   # Source code
│   └── neurodock/         # Main package
│       ├── __init__.py    # Package initialization
│       ├── agents/        # AI agent components
│       ├── cli/           # Command-line interface
│       ├── main.py        # FastAPI application entry point
│       ├── models/        # Domain models
│       ├── neo4j/         # Database operations
│       ├── routes/        # API endpoints
│       ├── scripts/       # Utility scripts
│       ├── services/      # Business logic
│       ├── static/        # Static files (CSS, JS)
│       └── templates/     # HTML templates
├── tests/                 # Test suite
├── .env.example           # Example environment variables
├── docker-compose.yml     # Docker Compose configuration
├── Dockerfile             # Docker build instructions
├── README.md              # Project documentation
├── run.sh                 # Script to run the project locally
├── start_memory_dashboard.sh # Script to start the memory dashboard
├── requirements.txt       # Project dependencies
└── setup.py               # Package configuration
```

This structure follows Python best practices and allows for clean separation of concerns, making the codebase maintainable and extensible.
