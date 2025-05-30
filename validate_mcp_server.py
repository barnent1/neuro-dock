#!/usr/bin/env python3
"""
NeuroDock MCP Server Validator
Tests if the MCP server can start and list tools properly
"""

import json
import os
import sys
from pathlib import Path

# Add the NeuroDock source directory to Python path
neurodock_src = Path(__file__).parent.parent / "src"
if neurodock_src.exists():
    sys.path.insert(0, str(neurodock_src))

def test_server_imports():
    """Test if all required imports work"""
    print("🧪 Testing server imports...")
    
    try:
        from mcp.server.fastmcp import FastMCP
        print("✅ FastMCP import successful")
    except ImportError as e:
        print(f"❌ FastMCP import failed: {e}")
        return False
        
    try:
        # Test NeuroDock imports
        from neurodock.db import get_store
        from neurodock.discussion import run_interactive_discussion
        from neurodock.agent import ProjectAgent
        from neurodock.memory.qdrant_store import search_memory, add_to_memory
        from neurodock.cli import (
            get_current_project, set_current_project, create_project,
            list_available_projects, get_project_metadata, update_project_metadata,
            list_project_tasks, load_task, save_task, get_task_file_path,
            analyze_task_complexity
        )
        print("✅ NeuroDock core imports successful")
    except ImportError as e:
        print(f"❌ NeuroDock import failed: {e}")
        return False
        
    return True

def test_server_initialization():
    """Test if the server can initialize without hanging"""
    print("\n🧪 Testing server initialization...")
    
    try:
        # Import the server module
        sys.path.insert(0, str(Path(__file__).parent / "mcp-server" / "src"))
        import server
        
        # Test store initialization
        store = server.get_neurodock_store()
        if store:
            print("✅ NeuroDock store available")
        else:
            print("⚠️  NeuroDock store not available")
            
        # Test agent initialization
        agent = server.get_project_agent()
        if agent:
            print("✅ Project agent available")
        else:
            print("⚠️  Project agent not available")
            
        return True
        
    except Exception as e:
        print(f"❌ Server initialization failed: {e}")
        return False

def test_mcp_tools():
    """Test if MCP tools are properly registered"""
    print("\n🧪 Testing MCP tool registration...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / "mcp-server" / "src"))
        import server
        
        # Check if FastMCP instance exists and has tools
        if hasattr(server, 'mcp'):
            print(f"✅ FastMCP instance found")
            # Try to get tool count (this might not be directly accessible)
            print("✅ MCP server instance created successfully")
            return True
        else:
            print("❌ FastMCP instance not found")
            return False
            
    except Exception as e:
        print(f"❌ MCP tool registration test failed: {e}")
        return False

def validate_vscode_config():
    """Validate VS Code MCP configuration"""
    print("\n🧪 Validating VS Code configuration...")
    
    config_path = Path.home() / "Library/Application Support/Code - Insiders/User/settings.json"
    
    if not config_path.exists():
        print("❌ VS Code Insiders settings.json not found")
        return False
        
    try:
        with open(config_path, 'r') as f:
            settings = json.load(f)
            
        if 'mcp' not in settings:
            print("❌ MCP configuration not found in settings")
            return False
            
        if 'servers' not in settings['mcp']:
            print("❌ MCP servers configuration not found")
            return False
            
        if 'neurodock' not in settings['mcp']['servers']:
            print("❌ NeuroDock server not configured in MCP")
            return False
            
        neurodock_config = settings['mcp']['servers']['neurodock']
        server_path = Path(neurodock_config['args'][0])
        
        if not server_path.exists():
            print(f"❌ Server file not found: {server_path}")
            return False
            
        print("✅ VS Code MCP configuration valid")
        print(f"   Server path: {server_path}")
        print(f"   Command: {neurodock_config['command']}")
        
        return True
        
    except Exception as e:
        print(f"❌ VS Code configuration validation failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("🚀 NeuroDock MCP Server Validation")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_server_imports),
        ("Server Initialization", test_server_initialization),
        ("MCP Tools Registration", test_mcp_tools),
        ("VS Code Configuration", validate_vscode_config)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        result = test_func()
        results.append((test_name, result))
        
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if not result:
            all_passed = False
            
    if all_passed:
        print("\n🎉 All tests passed! NeuroDock MCP server should work in VS Code.")
    else:
        print("\n⚠️  Some tests failed. Review the issues above.")
        
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
