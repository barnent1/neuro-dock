# Installation Guide

## Prerequisites

### System Requirements

- **Python**: 3.8 or higher
- **Operating System**: macOS, Linux, or Windows
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: 2GB free space

### Database Requirements

**PostgreSQL** (Required):
- Version 12 or higher
- Database creation permissions
- Network access (local or remote)

**Optional Enhanced Features**:
- **Qdrant**: For advanced vector search capabilities
- **Neo4J**: For graph-based relationship analysis

## Quick Installation

### 1. Clone Repository

```bash
git clone https://github.com/your-username/neurodock.git
cd neurodock
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install in development mode (optional)
pip install -e .
```

### 3. Database Setup

#### Option A: Quick Setup (PostgreSQL only)

```bash
# Setup with default PostgreSQL configuration
nd setup

# Follow the interactive prompts for database connection
```

#### Option B: Enhanced Setup (All databases)

```bash
# Install additional database dependencies
pip install qdrant-client neo4j

# Run enhanced setup
nd setup --enhanced
```

### 4. Initialize Your First Project

```bash
# Navigate to your project directory
cd your-project-directory

# Initialize NeuroDock
nd init

# Start your first enhanced iterative discussion
nd discuss
```

## Detailed Installation

### PostgreSQL Setup

#### macOS (using Homebrew)

```bash
# Install PostgreSQL
brew install postgresql

# Start PostgreSQL service
brew services start postgresql

# Create database
createdb neurodock_db

# Create user (optional)
createuser -P neurodock_user
```

#### Ubuntu/Debian

```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres createdb neurodock_db
sudo -u postgres createuser -P neurodock_user
```

#### Windows

1. Download PostgreSQL from [postgresql.org](https://www.postgresql.org/download/windows/)
2. Run the installer and follow setup wizard
3. Note the password for the `postgres` user
4. Create database using pgAdmin or command line

### Enhanced Database Setup

#### Qdrant (Vector Database)

```bash
# Option 1: Docker (Recommended)
docker run -p 6333:6333 qdrant/qdrant

# Option 2: Local installation
pip install qdrant-client
# Qdrant will run in embedded mode
```

#### Neo4J (Graph Database)

```bash
# Option 1: Docker (Recommended)
docker run -p 7474:7474 -p 7687:7687 neo4j:latest

# Option 2: Local installation
# Download from https://neo4j.com/download/
# Follow platform-specific installation guide
```

## Configuration

### Environment Configuration

Create a `.env` file in your project root:

```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/neurodock_db

# LLM Configuration (choose one or more)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
OLLAMA_BASE_URL=http://localhost:11434

# Enhanced Features (optional)
QDRANT_HOST=localhost
QDRANT_PORT=6333
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# System Configuration
LOG_LEVEL=INFO
MAX_MEMORY_ENTRIES=10000
CONVERSATION_HISTORY_DAYS=30
```

### System Setup Command

```bash
# Run the setup command
nd setup

# This will:
# 1. Create system configuration directory
# 2. Setup database connections
# 3. Initialize memory systems
# 4. Verify LLM integrations
# 5. Create sample configuration files
```

### Configuration Verification

```bash
# Test database connections
nd status

# Test LLM integration
nd explain "test connection"

# Test memory systems
nd memory --list
```

## LLM Provider Setup

### OpenAI

1. Sign up at [platform.openai.com](https://platform.openai.com)
2. Generate API key in dashboard
3. Add to environment: `OPENAI_API_KEY=your_key`

### Anthropic (Claude)

1. Sign up at [console.anthropic.com](https://console.anthropic.com)
2. Generate API key
3. Add to environment: `ANTHROPIC_API_KEY=your_key`

### Ollama (Local Models)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Download a model
ollama pull llama2

# Start Ollama service
ollama serve

# Configure NeuroDock
export OLLAMA_BASE_URL=http://localhost:11434
```

### Custom LLM Endpoints

```bash
# Set custom endpoint
export CUSTOM_LLM_ENDPOINT=https://your-api.com/v1
export CUSTOM_LLM_API_KEY=your_key
```

## Troubleshooting

### Common Issues

#### Database Connection Errors

```bash
# Test PostgreSQL connection
psql -h localhost -U your_user -d neurodock_db

# Check service status
# macOS: brew services list | grep postgresql
# Linux: systemctl status postgresql
# Windows: Check Services panel
```

#### Permission Errors

```bash
# Grant database permissions
sudo -u postgres psql
GRANT ALL PRIVILEGES ON DATABASE neurodock_db TO your_user;
```

#### Memory System Issues

```bash
# Reset memory systems
nd memory --reset

# Clear vector database
# Docker: docker restart qdrant_container
# Local: Remove ~/.qdrant directory
```

#### LLM Integration Issues

```bash
# Test API connections
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# Verify environment variables
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY
```

### Getting Help

#### Log Files

```bash
# View system logs
tail -f ~/.neuro-dock/logs/system.log

# View conversation logs
tail -f ~/.neuro-dock/logs/conversations.log

# View error logs
tail -f ~/.neuro-dock/logs/errors.log
```

#### Debug Mode

```bash
# Run with debug logging
DEBUG=1 nd begin

# Verbose output
nd status --verbose

# Memory system debug
nd memory --debug
```

## Development Installation

### For Contributors

```bash
# Clone repository
git clone https://github.com/your-username/neurodock.git
cd neurodock

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install development dependencies
pip install -r requirements.txt
pip install -e .

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run tests
python -m pytest tests/

# Run type checking
mypy src/

# Run linting
black src/ tests/
flake8 src/ tests/
```

### IDE Setup

#### VS Code

Install recommended extensions:
- Python
- Pylance
- Black Formatter
- GitLens

#### PyCharm

1. Open project directory
2. Configure Python interpreter to use virtual environment
3. Enable code formatting with Black
4. Configure database connections in Database tool

## Next Steps

After installation:

1. **Initialize your first project**: `nd init`
2. **Start Agent 1 conversation**: `nd begin`
3. **Read the documentation**: Check `documentation/` folder
4. **Join the community**: Participate in GitHub discussions
5. **Contribute**: See `CONTRIBUTING.md` for guidelines

## Deployment Options

### Local Development

- Single-user setup on development machine
- All databases running locally
- Perfect for learning and experimentation

### Team Environment

- Shared PostgreSQL database
- Centralized memory systems
- Multiple developer access

### Production Environment

- High-availability database setup
- Load-balanced memory systems
- Enterprise security configurations
- Monitoring and logging

For detailed deployment guides, see `documentation/deployment/`.
