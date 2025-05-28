# Contributing to NeuroDock

We're excited that you're interested in contributing to NeuroDock! This document outlines the process for contributing to this project.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- PostgreSQL (for database functionality)
- Basic understanding of AI/LLM concepts

### Development Setup

1. **Fork the repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/yourusername/neurodock.git
   cd neurodock
   ```

2. **Set up development environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   pip install -e .  # Install in development mode
   ```

3. **Set up database**
   ```bash
   # Run setup command
   python -m neurodock.cli setup
   ```

4. **Run tests**
   ```bash
   pytest tests/
   ```

## 🔄 Development Workflow

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following our style guide
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Run unit tests
   pytest tests/unit/
   
   # Run integration tests (if applicable)
   pytest tests/integration/
   
   # Test CLI commands
   python -m neurodock.cli --help
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new functionality"
   ```

### Commit Message Format

We follow conventional commits format:

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Adding or modifying tests
- `chore:` - Maintenance tasks

### Pull Request Process

1. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request**
   - Use a clear, descriptive title
   - Include a detailed description of changes
   - Reference any related issues
   - Add screenshots for UI changes

3. **Address review feedback**
   - Respond to comments
   - Make necessary changes
   - Update tests and documentation

## 🧪 Testing

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_agent.py

# With coverage
pytest --cov=neurodock
```

### Writing Tests

- Write unit tests for all new functions
- Include integration tests for complex workflows
- Test error conditions and edge cases
- Use descriptive test names

Example test structure:
```python
def test_agent_conversation_initialization():
    """Test that conversation agent initializes correctly."""
    agent = ConversationalAgent("/test/path")
    assert agent.conversation_state.phase == "initiation"
    assert agent.conversation_state.current_step == "introduction"
```

## 📝 Documentation

### Code Documentation

- Use clear, descriptive docstrings
- Include parameter and return type information
- Add usage examples for complex functions

```python
def process_conversation(message: str, context: Dict[str, Any]) -> str:
    """
    Process a conversation message with given context.
    
    Args:
        message: The user's message to process
        context: Additional context for processing
        
    Returns:
        The agent's response message
        
    Example:
        >>> response = process_conversation("Hello", {"phase": "initiation"})
        >>> print(response)
        "Hello! I'm Agent 1, ready to help..."
    """
```

### README and Docs

- Update README.md for new features
- Add documentation to `docs/` folder for complex features
- Include code examples and use cases

## 🏗️ Architecture Guidelines

### Code Organization

```
src/neurodock/
├── cli.py              # Command-line interface
├── agent.py            # Core agent functionality  
├── conversational_agent.py  # Agent 1 conversation system
├── db/                 # Database layer
├── memory/             # Memory systems (Qdrant, Neo4J)
└── utils/              # Utility functions
```

### Design Principles

1. **Modularity**: Keep components loosely coupled
2. **Testability**: Write testable code with clear interfaces
3. **Documentation**: Document complex logic and APIs
4. **Error Handling**: Graceful error handling and recovery
5. **Performance**: Consider performance implications

### Coding Standards

- Follow PEP 8 style guide
- Use type hints for function parameters and returns
- Keep functions focused and small
- Use meaningful variable and function names

## 🐛 Bug Reports

### Before Submitting

1. Check existing issues
2. Try to reproduce the bug
3. Gather relevant information

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Run command '...'
2. Enter input '...'
3. See error

**Expected behavior**
What you expected to happen.

**Environment**
- OS: [e.g., macOS, Linux, Windows]
- Python version: [e.g., 3.9.1]
- NeuroDock version: [e.g., 1.0.0]

**Additional context**
Any other context about the problem.
```

## 💡 Feature Requests

### Before Submitting

1. Check if the feature already exists
2. Consider if it fits the project scope
3. Think about implementation implications

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of what the problem is.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Alternative solutions or features you've considered.

**Additional context**
Any other context or screenshots about the feature request.
```

## 🎯 Areas for Contribution

We especially welcome contributions in these areas:

### High Priority
- **LLM Integrations**: Support for new LLM providers
- **Memory Systems**: Enhancements to vector/graph storage
- **CLI Improvements**: Better user experience and error messages
- **Testing**: Increased test coverage and integration tests

### Medium Priority
- **Documentation**: Tutorials, examples, and guides
- **Performance**: Optimization of database queries and memory usage
- **Security**: Enhanced security features and audit logging
- **UI/UX**: Better visualization of project progress

### Future Enhancements
- **Web Interface**: Browser-based project management
- **Team Features**: Multi-user collaboration tools
- **Integrations**: IDE plugins and CI/CD integrations
- **Analytics**: Project metrics and insights

## 🤝 Community

### Communication

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Pull Requests**: Code contributions and reviews

### Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please be respectful and professional in all interactions.

## 📄 License

By contributing to NeuroDock, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to NeuroDock! 🎉
