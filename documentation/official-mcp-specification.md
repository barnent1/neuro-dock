# Official Model Context Protocol (MCP) Specification

This document contains the official MCP specification and implementation guidelines from modelcontextprotocol.io, compiled for NeuroDock MCP server development.

## Table of Contents

1. [Overview](#overview)
2. [Core Architecture](#core-architecture)
3. [Tools](#tools)
4. [Resources](#resources)
5. [Prompts](#prompts)
6. [Implementation Patterns](#implementation-patterns)
7. [Security Considerations](#security-considerations)
8. [Best Practices](#best-practices)

## Overview

MCP is an open protocol that standardizes how applications provide context to LLMs. It follows a client-server architecture where:

- **Hosts**: LLM applications (like Claude Desktop, IDEs) that initiate connections
- **Clients**: Protocol clients that maintain 1:1 connections with servers
- **Servers**: Lightweight programs that expose capabilities through MCP

### Key Benefits
- Growing list of pre-built integrations
- Flexibility to switch between LLM providers
- Best practices for securing data within infrastructure

## Core Architecture

### Protocol Layer
Uses JSON-RPC 2.0 for message exchange with these message types:

1. **Requests**: Expect a response from the other side
```json
{
  "method": "string",
  "params": { ... }
}
```

2. **Results**: Successful responses to requests
```json
{
  "[key]": "unknown"
}
```

3. **Errors**: Request failures
```json
{
  "code": "number",
  "message": "string", 
  "data": "unknown"
}
```

4. **Notifications**: One-way messages (no response expected)
```json
{
  "method": "string",
  "params": { ... }
}
```

### Transport Layer
Supports multiple mechanisms:

1. **Stdio Transport**: Uses standard input/output (ideal for local processes)
2. **HTTP with SSE**: Server-Sent Events for server-to-client, HTTP POST for client-to-server

### Connection Lifecycle

1. **Initialization**:
   - Client sends `initialize` request with protocol version and capabilities
   - Server responds with its protocol version and capabilities
   - Client sends `initialized` notification
   - Normal message exchange begins

2. **Message Exchange**: Request-Response and Notifications patterns

3. **Termination**: Clean shutdown via `close()`, transport disconnection, or error conditions

### Standard Error Codes
```javascript
enum ErrorCode {
  ParseError = -32700,
  InvalidRequest = -32600,
  MethodNotFound = -32601,
  InvalidParams = -32602,
  InternalError = -32603
}
```

## Tools

Tools enable servers to expose executable functions that LLMs can invoke to perform actions.

### Tool Definition Structure
```json
{
  "name": "string",
  "description": "string", 
  "inputSchema": {
    "type": "object",
    "properties": { ... }
  },
  "annotations": {
    "title": "string",
    "readOnlyHint": "boolean",
    "destructiveHint": "boolean", 
    "idempotentHint": "boolean",
    "openWorldHint": "boolean"
  }
}
```

### Tool Discovery
- Clients list tools via `tools/list` endpoint
- Tools invoked via `tools/call` endpoint
- Servers can notify changes via `notifications/tools/list_changed`

### Tool Implementation Pattern (Python)
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("server-name")

@mcp.tool()
async def my_tool(param1: str, param2: int) -> str:
    """Tool description for LLM understanding.
    
    Args:
        param1: Description of parameter
        param2: Description of parameter
    """
    # Tool implementation
    return "result"
```

### Tool Error Handling
Return errors within result object, not as protocol errors:
```python
try:
    result = perform_operation()
    return {
        "content": [{"type": "text", "text": f"Success: {result}"}]
    }
except Exception as error:
    return {
        "isError": True,
        "content": [{"type": "text", "text": f"Error: {error.message}"}]
    }
```

### Tool Annotations
- **readOnlyHint**: Tool doesn't modify environment
- **destructiveHint**: Tool may perform destructive updates
- **idempotentHint**: Repeated calls have no additional effect
- **openWorldHint**: Tool interacts with external entities

### Tool Categories

1. **System Operations**: Execute commands, file operations
2. **API Integrations**: Wrap external APIs
3. **Data Processing**: Transform or analyze data

## Resources

Resources represent data that servers make available to clients (file contents, database records, API responses, etc.).

### Resource Structure
```json
{
  "uri": "string",
  "name": "string", 
  "description": "string",
  "mimeType": "string"
}
```

### Resource URIs
Format: `[protocol]://[host]/[path]`

Examples:
- `file:///home/user/documents/report.pdf`
- `postgres://database/customers/schema`
- `screen://localhost/display1`

### Resource Types

1. **Text Resources**: UTF-8 encoded text (code, configs, logs, JSON/XML)
2. **Binary Resources**: Base64 encoded binary data (images, PDFs, audio, video)

### Resource Discovery

1. **Direct Resources**: Concrete list via `resources/list`
2. **Resource Templates**: URI templates for dynamic resources following RFC 6570

### Resource Reading
Request via `resources/read` with URI, server responds with:
```json
{
  "contents": [
    {
      "uri": "string",
      "mimeType": "string",
      "text": "string",      // For text resources
      "blob": "string"      // For binary (base64)
    }
  ]
}
```

### Resource Updates

1. **List Changes**: `notifications/resources/list_changed`
2. **Content Changes**: Subscribe via `resources/subscribe`, get `notifications/resources/updated`

## Prompts

Prompts are predefined templates for reusable LLM interactions and workflows.

### Prompt Structure
```json
{
  "name": "string",
  "description": "string",
  "arguments": [
    {
      "name": "string",
      "description": "string", 
      "required": "boolean"
    }
  ]
}
```

### Prompt Discovery
Via `prompts/list` endpoint

### Prompt Usage
Request via `prompts/get`:
```json
{
  "method": "prompts/get",
  "params": {
    "name": "prompt-name",
    "arguments": {
      "arg1": "value1"
    }
  }
}
```

Response:
```json
{
  "description": "string",
  "messages": [
    {
      "role": "user|assistant",
      "content": {
        "type": "text|resource",
        "text": "string",
        "resource": { ... }
      }
    }
  ]
}
```

### Dynamic Prompts
Can include:
- Embedded resource context
- Multi-step workflows
- Variable substitution

## Implementation Patterns

### FastMCP Server Pattern (Python)
```python
from mcp.server.fastmcp import FastMCP
import asyncio

# Initialize server
mcp = FastMCP("server-name")

@mcp.tool() 
async def example_tool(param: str) -> str:
    """Tool description."""
    return f"Result: {param}"

@mcp.resource("example://resource/{id}")
async def get_resource(id: str) -> str:
    """Resource provider."""
    return f"Resource content for {id}"

@mcp.prompt()
async def example_prompt(arg: str) -> list:
    """Prompt template."""
    return [
        {
            "role": "user",
            "content": {
                "type": "text", 
                "text": f"Process: {arg}"
            }
        }
    ]

if __name__ == "__main__":
    mcp.run(transport='stdio')
```

### Traditional Server Pattern
```python
from mcp.server import Server
from mcp.server.stdio import StdioServerTransport

server = Server("server-name", "1.0.0")

@server.list_tools()
async def list_tools():
    return [
        {
            "name": "example_tool",
            "description": "Example tool",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "param": {"type": "string"}
                },
                "required": ["param"]
            }
        }
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "example_tool":
        return {
            "content": [
                {"type": "text", "text": f"Result: {arguments['param']}"}
            ]
        }

if __name__ == "__main__":
    transport = StdioServerTransport()
    server.run(transport)
```

## Security Considerations

### Input Validation
- Validate all parameters against schema
- Sanitize file paths and system commands
- Validate URLs and external identifiers
- Check parameter sizes and ranges
- Prevent command injection

### Access Control
- Implement authentication where needed
- Use appropriate authorization checks
- Audit tool usage
- Rate limit requests
- Monitor for abuse

### Error Handling
- Don't expose internal errors to clients
- Log security-relevant errors
- Handle timeouts appropriately
- Clean up resources after errors
- Validate return values

### Transport Security
- Use TLS for remote connections
- Validate connection origins
- Implement authentication when needed

### Message Validation
- Validate all incoming messages
- Sanitize inputs
- Check message size limits
- Verify JSON-RPC format

### Resource Protection
- Implement access controls
- Validate resource paths
- Monitor resource usage
- Rate limit requests

## Best Practices

### Tool Development
1. Provide clear, descriptive names and descriptions
2. Use detailed JSON Schema definitions for parameters
3. Include examples in tool descriptions
4. Implement proper error handling and validation
5. Use progress reporting for long operations
6. Keep tool operations focused and atomic
7. Document expected return value structures
8. Implement proper timeouts
9. Consider rate limiting for resource-intensive operations
10. Log tool usage for debugging and monitoring

### Resource Development
1. Use clear, descriptive resource names and URIs
2. Include helpful descriptions to guide LLM understanding
3. Set appropriate MIME types when known
4. Implement resource templates for dynamic content
5. Use subscriptions for frequently changing resources
6. Handle errors gracefully with clear error messages
7. Consider pagination for large resource lists
8. Cache resource contents when appropriate
9. Validate URIs before processing
10. Document your custom URI schemes

### Prompt Development
1. Use clear, descriptive prompt names
2. Provide detailed descriptions for prompts and arguments
3. Validate all required arguments
4. Handle missing arguments gracefully
5. Consider versioning for prompt templates
6. Cache dynamic content when appropriate
7. Implement error handling
8. Document expected argument formats
9. Consider prompt composability
10. Test prompts with various inputs

### General Implementation
1. **Transport Selection**: Use stdio for local, SSE for remote
2. **Message Handling**: Validate inputs, use type-safe schemas, handle errors gracefully
3. **Progress Reporting**: Use progress tokens for long operations
4. **Error Management**: Use appropriate error codes, include helpful messages
5. **Testing**: Cover functional, integration, security, performance, and error handling
6. **Debugging**: Log protocol events, track message flow, monitor performance
7. **Documentation**: Document custom URI schemes, tool behaviors, security requirements

### UI Integration
Prompts can be surfaced as:
- Slash commands
- Quick actions
- Context menu items
- Command palette entries
- Guided workflows
- Interactive forms

### Monitoring and Debugging
1. **Logging**: Protocol events, message flow, performance, errors
2. **Diagnostics**: Health checks, connection state, resource usage, performance profiling
3. **Testing**: Different transports, error handling, edge cases, load testing

## Claude Desktop Integration

To connect MCP server to Claude Desktop:

1. **Install Claude Desktop**: Download latest version
2. **Configure**: Edit `~/Library/Application Support/Claude/claude_desktop_config.json`
3. **Add Server**:
```json
{
    "mcpServers": {
        "server-name": {
            "command": "uv",
            "args": [
                "--directory",
                "/absolute/path/to/server",
                "run", 
                "server.py"
            ]
        }
    }
}
```
4. **Restart**: Restart Claude Desktop
5. **Test**: Look for tools icon in interface

## References

- Official Documentation: https://modelcontextprotocol.io/
- GitHub Organization: https://github.com/modelcontextprotocol
- Specification: https://modelcontextprotocol.io/specification  
- Python SDK: https://github.com/modelcontextprotocol/python-sdk
- Examples: https://modelcontextprotocol.io/examples
- Debugging Guide: https://modelcontextprotocol.io/docs/tools/debugging

---

*This document compiled from official MCP documentation at modelcontextprotocol.io for NeuroDock MCP server implementation.*
