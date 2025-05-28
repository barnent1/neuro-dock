"""
NeuroDock Configuration Management

This module provides centralized configuration for the NeuroDock system.
All environment variables are loaded from ~/.neuro-dock/.env regardless 
of the current working directory.
"""
import os
import warnings
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class NeuroDockConfig:
    """Centralized configuration manager for NeuroDock."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._load_environment()
            self._initialized = True
    
    def _load_environment(self):
        """Load environment variables from ~/.neuro-dock/.env"""
        # Get the NeuroDock home directory
        home_dir = Path.home()
        neuro_dock_dir = home_dir / ".neuro-dock"
        env_file = neuro_dock_dir / ".env"
        
        # Create the directory if it doesn't exist
        neuro_dock_dir.mkdir(exist_ok=True)
        
        # Load from the fixed location
        if env_file.exists():
            load_dotenv(dotenv_path=env_file)
        else:
            # Configuration file missing - silent graceful degradation
            # Users will get helpful guidance through CLI commands
            pass
    
    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL connection URL."""
        return os.getenv("POSTGRES_URL", "postgresql://localhost/neurodock")
    
    @property
    def llm_backend(self) -> str:
        """Get LLM backend (ollama, claude, etc.)."""
        return os.getenv("NEURO_LLM", "ollama")
    
    @property
    def ollama_model(self) -> str:
        """Get Ollama model name."""
        return os.getenv("NEURO_OLLAMA_MODEL", "openchat")
    
    @property
    def claude_api_key(self) -> Optional[str]:
        """Get Claude API key."""
        return os.getenv("CLAUDE_API_KEY")
    
    @property
    def neuro_dock_dir(self) -> Path:
        """Get the NeuroDock home directory."""
        return Path.home() / ".neuro-dock"
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get an environment variable with optional default."""
        return os.getenv(key, default)
    
    def create_default_env_file(self) -> Path:
        """Create a default .env file with example configuration."""
        env_file = self.neuro_dock_dir / ".env"
        
        default_content = """# LLM Configuration for neuro-dock
# Choose which LLM backend to use: "ollama" or "claude"
NEURO_LLM=ollama

# Ollama-specific settings (uncomment and set if using Ollama)
NEURO_OLLAMA_MODEL=openchat

# Claude API configuration (uncomment and set if using Claude)
# NEURO_LLM=claude
# CLAUDE_API_KEY=your_claude_api_key_here

# PostgreSQL Database Configuration
# Set your PostgreSQL connection URL here
# Format: postgresql://username:password@host:port/database
POSTGRES_URL=postgresql://neurodock:neurodock@localhost:5432/neurodock

# Examples for cloud providers:
# Supabase:
# POSTGRES_URL=postgresql://postgres:your-password@db.project.supabase.co:5432/postgres
# Railway:
# POSTGRES_URL=postgresql://postgres:password@containers-us-west-1.railway.app:5432/railway
# Heroku:
# POSTGRES_URL=postgres://user:pass@hostname:5432/dbname
# Neon:
# POSTGRES_URL=postgresql://user:pass@ep-hostname.us-east-2.aws.neon.tech/dbname
"""
        
        # Only create if it doesn't exist
        if not env_file.exists():
            env_file.write_text(default_content)
            # Reload environment after creating the file
            load_dotenv(dotenv_path=env_file)
        
        return env_file


# Global config instance - singleton pattern
config = NeuroDockConfig()


def get_config() -> NeuroDockConfig:
    """Get the global NeuroDock configuration instance."""
    return config


# Convenience functions for backward compatibility
def get_postgres_url() -> str:
    """Get PostgreSQL connection URL."""
    return config.postgres_url


def get_llm_backend() -> str:
    """Get LLM backend."""
    return config.llm_backend


def get_ollama_model() -> str:
    """Get Ollama model."""
    return config.ollama_model


def get_claude_api_key() -> Optional[str]:
    """Get Claude API key."""
    return config.claude_api_key
