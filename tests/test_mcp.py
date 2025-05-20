#!/usr/bin/env python3
"""
MCP Integration Test Script for NeuroDock

This script tests the Model Context Protocol (MCP) implementation of NeuroDock
by making HTTP requests to the running Docker container and verifying database updates.

It tests both memory and task operations to ensure proper functioning.
"""

import asyncio
import json
import sys
import time
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

import aiohttp
import pytest

# Configuration
MCP_BASE_URL = "http://localhost:4000/mcp"
API_BASE_URL = "http://localhost:4000/api"
MEMORY_ENDPOINT = f"{MCP_BASE_URL}/memory"
TASK_ENDPOINT = f"{MCP_BASE_URL}/task"
CONTEXT_ENDPOINT = f"{MCP_BASE_URL}/context"
CONFIG_ENDPOINT = f"{MCP_BASE_URL}/config"

# Test data
TEST_PROJECT_ID = f"test-project-{uuid.uuid4()}"
TEST_MEMORY_CONTENT = "This is a test memory for unit testing"
TEST_TASK_CONTENT = "This is a test task for unit testing"

class TestResults:
    """Class to track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.failures = []
    
    def pass_test(self, name):
        print(f"✅ PASSED: {name}")
        self.passed += 1
    
    def fail_test(self, name, reason):
        print(f"❌ FAILED: {name} - {reason}")
        self.failures.append((name, reason))
        self.failed += 1
    
    def summary(self):
        print("\n=== TEST SUMMARY ===")
        print(f"Total tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        
        if self.failed > 0:
            print("\nFailures:")
            for name, reason in self.failures:
                print(f"  • {name}: {reason}")
        
        return self.failed == 0

async def test_mcp_config(results):
    """Test if MCP config endpoint returns proper structure"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(CONFIG_ENDPOINT) as response:
                if response.status != 200:
                    results.fail_test("MCP Config", f"Expected status 200, got {response.status}")
                    return False
                
                data = await response.json()
                
                # Check required fields
                required_fields = ["version", "name", "capabilities", "endpoints"]
                for field in required_fields:
                    if field not in data:
                        results.fail_test("MCP Config", f"Missing required field: {field}")
                        return False
                
                # Check capabilities
                if not data["capabilities"].get("memory"):
                    results.fail_test("MCP Config", "Memory capability not enabled")
                    return False
                if not data["capabilities"].get("tasks"):
                    results.fail_test("MCP Config", "Tasks capability not enabled")
                    return False
                
                results.pass_test("MCP Config")
                return True
    except Exception as e:
        results.fail_test("MCP Config", f"Exception: {str(e)}")
        return False

async def test_memory_creation(results):
    """Test memory creation via MCP endpoint"""
    try:
        memory_data = {
            "content": TEST_MEMORY_CONTENT,
            "type": "important",
            "source": "mcp_test",
            "projectId": TEST_PROJECT_ID
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(MEMORY_ENDPOINT, json=memory_data) as response:
                if response.status != 200:
                    results.fail_test("Memory Creation", f"Expected status 200, got {response.status}")
                    return None
                
                data = await response.json()
                
                if not data.get("success"):
                    results.fail_test("Memory Creation", f"Expected success=True, got {data.get('success')}")
                    return None
                
                memory_id = data.get("memory_id")
                if not memory_id:
                    results.fail_test("Memory Creation", "No memory_id returned")
                    return None
                
                results.pass_test("Memory Creation")
                return memory_id
    except Exception as e:
        results.fail_test("Memory Creation", f"Exception: {str(e)}")
        return None

async def test_memory_retrieval(results, memory_id):
    """Test memory retrieval through context query"""
    if not memory_id:
        results.fail_test("Memory Retrieval", "No memory ID provided")
        return False
    
    try:
        query_data = {
            "query": TEST_MEMORY_CONTENT[:20],  # Use part of the memory content as query
            "projectId": TEST_PROJECT_ID,
            "maxMemories": 10
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(CONTEXT_ENDPOINT, json=query_data) as response:
                if response.status != 200:
                    results.fail_test("Memory Retrieval", f"Expected status 200, got {response.status}")
                    return False
                
                data = await response.json()
                
                if not data.get("success"):
                    results.fail_test("Memory Retrieval", f"Expected success=True, got {data.get('success')}")
                    return False
                
                context_items = data.get("context", [])
                found = False
                for item in context_items:
                    if item.get("id") == memory_id:
                        found = True
                        break
                
                if not found:
                    results.fail_test("Memory Retrieval", f"Created memory not found in context results")
                    return False
                
                results.pass_test("Memory Retrieval")
                return True
    except Exception as e:
        results.fail_test("Memory Retrieval", f"Exception: {str(e)}")
        return False

async def test_task_creation(results):
    """Test task creation via MCP endpoint"""
    try:
        task_data = {
            "title": TEST_TASK_CONTENT,
            "description": "Description for test task",
            "priority": "high",
            "projectId": TEST_PROJECT_ID
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(TASK_ENDPOINT, json=task_data) as response:
                if response.status != 200:
                    results.fail_test("Task Creation", f"Expected status 200, got {response.status}")
                    return None
                
                data = await response.json()
                
                if not data.get("success"):
                    results.fail_test("Task Creation", f"Expected success=True, got {data.get('success')}")
                    return None
                
                task_id = data.get("task_id")
                if not task_id:
                    results.fail_test("Task Creation", "No task_id returned")
                    return None
                
                results.pass_test("Task Creation")
                return task_id
    except Exception as e:
        results.fail_test("Task Creation", f"Exception: {str(e)}")
        return None

async def test_task_updates(results, task_id):
    """Test task updates for the newly created task"""
    if not task_id:
        results.fail_test("Task Update", "No task ID provided")
        return False
    
    try:
        update_data = {
            "taskId": task_id,
            "status": "in_progress",
            "progress": 25,
            "projectId": TEST_PROJECT_ID
        }
        
        async with aiohttp.ClientSession() as session:
            # We'll use the task update endpoint from the API
            update_endpoint = f"{API_BASE_URL}/tasks/{task_id}"
            async with session.patch(update_endpoint, json=update_data) as response:
                if response.status != 200:
                    results.fail_test("Task Update", f"Expected status 200, got {response.status}")
                    return False
                
                data = await response.json()
                
                if data.get("status") != "in_progress" or data.get("progress") != 25:
                    results.fail_test("Task Update", "Task wasn't updated correctly")
                    return False
                
                results.pass_test("Task Update")
                return True
    except Exception as e:
        results.fail_test("Task Update", f"Exception: {str(e)}")
        return False

async def wait_for_service():
    """Wait for the service to be available"""
    max_retries = 30
    retry_delay = 2  # seconds
    
    print("Waiting for NeuroDock service to be available...")
    
    for i in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{MCP_BASE_URL}/config") as response:
                    if response.status == 200:
                        print(f"NeuroDock service is up and running!")
                        return True
        except aiohttp.ClientError:
            pass
        
        print(f"Waiting for service... (attempt {i+1}/{max_retries})")
        await asyncio.sleep(retry_delay)
    
    print("Timed out waiting for service")
    return False

async def main():
    # Initialize results tracker
    results = TestResults()
    
    # Wait for service to be available
    if not await wait_for_service():
        results.fail_test("Service Check", "Service not available after timeout")
        return 1
    
    # Test MCP Configuration
    await test_mcp_config(results)
    
    # Test Memory Operations
    memory_id = await test_memory_creation(results)
    await test_memory_retrieval(results, memory_id)
    
    # Test Task Operations
    task_id = await test_task_creation(results)
    await test_task_updates(results, task_id)
    
    # Print summary
    success = results.summary()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
