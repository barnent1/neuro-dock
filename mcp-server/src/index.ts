#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
    CallToolRequestSchema,
    GetPromptRequestSchema,
    ListPromptsRequestSchema,
    ListResourcesRequestSchema,
    ListToolsRequestSchema,
    ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { execSync } from "child_process";
import * as fs from "fs";
import * as path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables from .env files
function loadEnvFiles() {
  const envPaths = [
    path.join(process.cwd(), '.env'),
    path.join(process.cwd(), '.env.local'),
    path.join(__dirname, '..', '.env'),
  ];

  for (const envPath of envPaths) {
    if (fs.existsSync(envPath)) {
      try {
        const envContent = fs.readFileSync(envPath, 'utf8');
        const lines = envContent.split('\n');
        
        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed && !trimmed.startsWith('#')) {
            const [key, ...valueParts] = trimmed.split('=');
            if (key && valueParts.length > 0) {
              const value = valueParts.join('=').replace(/^["']|["']$/g, '');
              if (!process.env[key.trim()]) {
                process.env[key.trim()] = value;
              }
            }
          }
        }
        console.log(`📄 Loaded environment from: ${envPath}`);
      } catch (error) {
        console.warn(`⚠️  Failed to load ${envPath}:`, error instanceof Error ? error.message : String(error));
      }
    }
  }
}

// Load environment variables at startup
loadEnvFiles();

/**
 * NeuroDock MCP Server - Node.js Wrapper for Python Implementation
 * This bridges the MCP protocol to the full-featured Python server
 */
class NeuroDockMCPServer {
  private server: Server;
  private workspacePath: string;
  private pythonServerPath: string;

  constructor() {
    // Determine project path - support for new projects
    this.workspacePath = this.detectProjectPath();
    this.pythonServerPath = this.findPythonServerPath();
    
    this.server = new Server(
      {
        name: "neurodock-mcp-server",
        version: "2.0.0",
      },
      {
        capabilities: {
          tools: {},
          resources: {},
          prompts: {},
        },
      }
    );

    this.setupHandlers();
    this.setupErrorHandling();
  }

  /**
   * Detect the project path - can be current directory or specified via environment
   */
  private detectProjectPath(): string {
    // 1. Check environment variable first
    if (process.env.NEURODOCK_PROJECT_PATH) {
      return process.env.NEURODOCK_PROJECT_PATH;
    }

    // 2. Check if we're in a NeuroDock workspace already
    const cwd = process.cwd();
    if (fs.existsSync(path.join(cwd, '.neuro-dock'))) {
      return cwd;
    }

    // 3. Check if we're in the main NeuroDock repo
    if (fs.existsSync(path.join(cwd, 'src', 'neurodock'))) {
      return cwd;
    }

    // 4. Default to the main NeuroDock installation
    const defaultPath = "/Users/barnent1/.neuro-dock";
    if (fs.existsSync(defaultPath)) {
      return defaultPath;
    }

    // 5. Fall back to current working directory
    return cwd;
  }

  /**
   * Find the Python server path - check multiple locations
   */
  private findPythonServerPath(): string {
    const possiblePaths = [
      path.join(this.workspacePath, "mcp-server", "src", "server.py"),
      path.join("/Users/barnent1/.neuro-dock", "mcp-server", "src", "server.py"),
      path.join(__dirname, "..", "..", "mcp-server", "src", "server.py"),
    ];

    for (const serverPath of possiblePaths) {
      if (fs.existsSync(serverPath)) {
        return serverPath;
      }
    }

    // Default path
    return path.join(this.workspacePath, "mcp-server", "src", "server.py");
  }

  private setupErrorHandling(): void {
    this.server.onerror = (error) => {
      console.error("[MCP Error]", error);
    };

    process.on("SIGINT", async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  /**
   * Execute Python function via the Python server
   */
  private async executePythonFunction(functionName: string, args: any = {}): Promise<any> {
    try {
      // Create a simpler Python execution approach with better path handling
      const neurodockSrcPath = this.findNeuroDockSrc();
      const mcpServerPath = path.dirname(this.pythonServerPath);
      
      const pythonScript = `
import sys
import os
import json
import asyncio
from pathlib import Path

# Add the NeuroDock source paths
sys.path.insert(0, '${neurodockSrcPath}')
sys.path.insert(0, '${mcpServerPath}')

# Set the working directory to the project path
os.chdir('${this.workspacePath}')

async def execute_function():
    try:
        # Import the server module
        import server
        
        # Get the function by name
        func = getattr(server, '${functionName}', None)
        if func is None:
            return {"error": f"Function ${functionName} not found"}
        
        # Execute the function with arguments
        result = await func(**${JSON.stringify(args)})
        return {"result": result}
        
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

# Run the async function
result = asyncio.run(execute_function())
print(json.dumps(result))
`;

      // Write script to temporary file
      const scriptPath = path.join(this.workspacePath, 'temp_mcp_script.py');
      fs.writeFileSync(scriptPath, pythonScript);

      try {
        const result = execSync(`python3 "${scriptPath}"`, {
          cwd: this.workspacePath,
          encoding: "utf8",
          timeout: 30000,
          env: { ...process.env, PYTHONPATH: `${neurodockSrcPath}:${mcpServerPath}` }
        });

        const parsed = JSON.parse(result.trim());
        if (parsed.error) {
          throw new Error(`${parsed.error}\n${parsed.traceback || ''}`);
        }
        return parsed.result;
      } finally {
        // Clean up temporary file
        if (fs.existsSync(scriptPath)) {
          fs.unlinkSync(scriptPath);
        }
      }
    } catch (error) {
      throw new Error(`Python execution failed: ${error}`);
    }
  }

  /**
   * Find NeuroDock source directory
   */
  private findNeuroDockSrc(): string {
    const possiblePaths = [
      path.join(this.workspacePath, "src"),
      path.join("/Users/barnent1/.neuro-dock", "src"),
      path.join(__dirname, "..", "..", "src"),
    ];

    for (const srcPath of possiblePaths) {
      if (fs.existsSync(path.join(srcPath, "neurodock"))) {
        return srcPath;
      }
    }

    // Default
    return path.join(this.workspacePath, "src");
  }

  /**
   * Execute Python resource function
   */
  private async executePythonResource(resourceName: string): Promise<any> {
    try {
      const pythonScript = `
import sys
import os
import json
import asyncio

# Add the NeuroDock source to path
sys.path.insert(0, '${this.workspacePath}/src')
sys.path.insert(0, '${this.workspacePath}/mcp-server/src')

async def execute_resource():
    try:
        # Import the server module
        import server
        
        # Map resource names to functions
        resource_map = {
            'neurodock://project/files': 'get_project_files',
            'neurodock://project/tasks': 'get_project_tasks',
            'neurodock://project/memory': 'get_project_memory',
            'neurodock://project/context': 'get_full_project_context'
        }
        
        func_name = resource_map.get('${resourceName}')
        if func_name is None:
            return {"error": f"Resource ${resourceName} not found"}
        
        # Get the function by name
        func = getattr(server, func_name, None)
        if func is None:
            return {"error": f"Function {func_name} not found"}
        
        # Execute the function
        result = await func()
        return {"result": result}
        
    except Exception as e:
        return {"error": str(e)}

# Run the async function
result = asyncio.run(execute_resource())
print(json.dumps(result))
`;

      // Write script to temporary file
      const scriptPath = path.join(this.workspacePath, 'temp_mcp_resource.py');
      fs.writeFileSync(scriptPath, pythonScript);

      try {
        const result = execSync(`python3 "${scriptPath}"`, {
          cwd: this.workspacePath,
          encoding: "utf8",
          timeout: 15000,
        });

        const parsed = JSON.parse(result.trim());
        if (parsed.error) {
          throw new Error(parsed.error);
        }
        return parsed.result;
      } finally {
        // Clean up temporary file
        if (fs.existsSync(scriptPath)) {
          fs.unlinkSync(scriptPath);
        }
      }
    } catch (error) {
      throw new Error(`Python resource execution failed: ${error}`);
    }
  }

  private setupHandlers(): void {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: "neurodock_agent_info",
            description: "Load cognitive context and behavioral instructions for AI agents. Auto-called to provide agent context.",
            inputSchema: {
              type: "object",
              properties: {},
            },
          },
          {
            name: "neurodock_add_project", 
            description: "Create a new isolated project workspace with metadata and directory structure",
            inputSchema: {
              type: "object",
              properties: {
                name: {
                  type: "string",
                  description: "Project name (alphanumeric, hyphens, underscores only)",
                },
                description: {
                  type: "string", 
                  description: "Optional project description",
                  default: "",
                },
              },
              required: ["name"],
            },
          },
          {
            name: "neurodock_list_projects",
            description: "List all available project workspaces with metadata and status",
            inputSchema: {
              type: "object",
              properties: {},
            },
          },
          {
            name: "neurodock_remove_project",
            description: "Remove a project workspace and all its data permanently",
            inputSchema: {
              type: "object", 
              properties: {
                name: {
                  type: "string",
                  description: "Project name to remove",
                },
                confirm: {
                  type: "boolean",
                  description: "Skip confirmation prompt",
                  default: false,
                },
              },
              required: ["name"],
            },
          },
          {
            name: "neurodock_set_active_project",
            description: "Switch to a different project workspace context",
            inputSchema: {
              type: "object",
              properties: {
                name: {
                  type: "string", 
                  description: "Project name to activate",
                },
              },
              required: ["name"],
            },
          },
          {
            name: "neurodock_project_status",
            description: "Get comprehensive project status with tasks, memory, and completion analytics",
            inputSchema: {
              type: "object",
              properties: {
                name: {
                  type: "string",
                  description: "Project name (default: current active project)",
                },
              },
            },
          },
          {
            name: "neurodock_get_project_status",
            description: "Get the current status of the NeuroDock project including active tasks and recent activity",
            inputSchema: {
              type: "object",
              properties: {
                project_path: {
                  type: "string",
                  description: "Optional path to specific project directory",
                },
              },
            },
          },
          {
            name: "neurodock_list_tasks",
            description: "List tasks in the NeuroDock project with optional filtering",
            inputSchema: {
              type: "object",
              properties: {
                status: {
                  type: "string",
                  description: "Filter by task status (pending, in_progress, completed, failed, or all)",
                  enum: ["pending", "in_progress", "completed", "failed", "all"],
                  default: "all",
                },
                limit: {
                  type: "number",
                  description: "Maximum number of tasks to return",
                  default: 10,
                },
              },
            },
          },
          {
            name: "neurodock_update_task",
            description: "Update the status or details of a specific task",
            inputSchema: {
              type: "object",
              properties: {
                task_id: {
                  type: "string",
                  description: "ID of the task to update",
                },
                status: {
                  type: "string",
                  description: "New status for the task",
                  enum: ["pending", "in_progress", "completed", "failed"],
                },
                notes: {
                  type: "string",
                  description: "Additional notes about the task update",
                },
              },
              required: ["task_id"],
            },
          },
          {
            name: "neurodock_create_task",
            description: "Create a new task in the NeuroDock project",
            inputSchema: {
              type: "object",
              properties: {
                description: {
                  type: "string",
                  description: "Description of the task to create",
                },
                priority: {
                  type: "string",
                  description: "Priority level of the task",
                  enum: ["low", "medium", "high"],
                  default: "medium",
                },
                category: {
                  type: "string",
                  description: "Category or type of task",
                  default: "general",
                },
              },
              required: ["description"],
            },
          },
          {
            name: "neurodock_add_memory",
            description: "Store important information or decisions in the project memory",
            inputSchema: {
              type: "object",
              properties: {
                content: {
                  type: "string",
                  description: "The information to store in memory",
                },
                category: {
                  type: "string",
                  description: "Category for the memory",
                  enum: ["note", "decision", "requirement", "bug", "feature"],
                  default: "note",
                },
                tags: {
                  type: "array",
                  items: { type: "string" },
                  description: "Tags to help organize and search the memory",
                },
              },
              required: ["content"],
            },
          },
          {
            name: "neurodock_search_memory",
            description: "Search through project memories and past decisions",
            inputSchema: {
              type: "object",
              properties: {
                query: {
                  type: "string",
                  description: "Search terms to find relevant memories",
                },
                category: {
                  type: "string",
                  description: "Filter by memory category",
                },
                limit: {
                  type: "number",
                  description: "Maximum number of results to return",
                  default: 5,
                },
              },
              required: ["query"],
            },
          },
          {
            name: "neurodock_get_project_context",
            description: "Get comprehensive context about the current project including structure, recent changes, and configuration",
            inputSchema: {
              type: "object",
              properties: {
                include_files: {
                  type: "boolean",
                  description: "Include file tree and important file contents",
                  default: true,
                },
                include_git: {
                  type: "boolean",
                  description: "Include git status and recent commits",
                  default: true,
                },
              },
            },
          },
          {
            name: "neurodock_start_discussion",
            description: "Start an interactive discussion workflow with the NeuroDock system",
            inputSchema: {
              type: "object",
              properties: {
                topic: {
                  type: "string",
                  description: "The main topic or question to discuss",
                },
                context: {
                  type: "string",
                  description: "Additional context or background information",
                },
                participants: {
                  type: "array",
                  items: { type: "string" },
                  description: "List of participant roles",
                  default: ["user", "system"],
                },
              },
              required: ["topic"],
            },
          },
          {
            name: "neurodock_continue_discussion",
            description: "Continue an existing interactive discussion with new input",
            inputSchema: {
              type: "object",
              properties: {
                discussion_id: {
                  type: "string",
                  description: "ID of the discussion to continue",
                },
                message: {
                  type: "string",
                  description: "The message or input to add to the discussion",
                },
                participant: {
                  type: "string",
                  description: "The role of the participant sending the message",
                  default: "user",
                },
              },
              required: ["discussion_id", "message"],
            },
          },
          {
            name: "neurodock_get_discussion_status",
            description: "Get the status and history of discussions",
            inputSchema: {
              type: "object",
              properties: {
                discussion_id: {
                  type: "string",
                  description: "Specific discussion ID to check (if empty, returns all recent discussions)",
                },
                include_history: {
                  type: "boolean",
                  description: "Whether to include the full discussion history",
                  default: true,
                },
              },
            },
          },
          {
            name: "generate_ui_component",
            description: "Generate React UI components using V0.dev with mandatory visual preview",
            inputSchema: {
              type: "object",
              properties: {
                component_description: {
                  type: "string",
                  description: "Detailed description of what the component should do",
                },
                design_requirements: {
                  type: "string",
                  description: "Visual and UX requirements (colors, layout, interactions)",
                  default: "Clean, modern design with good UX",
                },
                component_type: {
                  type: "string",
                  description: "Type of component",
                  enum: ["react", "vue", "angular"],
                  default: "react",
                },
                framework: {
                  type: "string",
                  description: "Framework to use",
                  enum: ["nextjs", "react", "vite"],
                  default: "nextjs",
                },
                styling: {
                  type: "string",
                  description: "Styling approach",
                  enum: ["tailwindcss", "shadcn", "styled-components"],
                  default: "tailwindcss",
                },
                data_structure: {
                  type: "string",
                  description: "JSON string describing the data/props structure",
                  default: "{}",
                },
              },
              required: ["component_description"],
            },
          },
          {
            name: "approve_ui_component",
            description: "Approve a UI component after visual preview and export the code",
            inputSchema: {
              type: "object",
              properties: {
                component_id: {
                  type: "string",
                  description: "The component ID from generate_ui_component",
                },
                feedback: {
                  type: "string",
                  description: "Optional feedback about the component",
                },
              },
              required: ["component_id"],
            },
          },
          {
            name: "generate_full_app",
            description: "Generate complete full-stack applications using Loveable with mandatory preview",
            inputSchema: {
              type: "object",
              properties: {
                app_description: {
                  type: "string",
                  description: "Detailed description of the application and its purpose",
                },
                tech_requirements: {
                  type: "string",
                  description: "Technologies needed (databases, APIs, integrations)",
                  default: "React, TypeScript, Tailwind CSS",
                },
                user_flows: {
                  type: "string",
                  description: "JSON string describing main user journeys and workflows",
                  default: "[]",
                },
                app_type: {
                  type: "string",
                  description: "Type of application",
                  enum: ["web_app", "mobile_app", "dashboard", "saas"],
                  default: "web_app",
                },
                deployment_preference: {
                  type: "string",
                  description: "Preferred hosting platform",
                  enum: ["vercel", "netlify", "custom"],
                  default: "vercel",
                },
              },
              required: ["app_description"],
            },
          },
          {
            name: "approve_full_app",
            description: "Approve a full application after preview and finalize deployment",
            inputSchema: {
              type: "object",
              properties: {
                app_id: {
                  type: "string",
                  description: "The app ID from generate_full_app",
                },
                custom_domain: {
                  type: "string",
                  description: "Optional custom domain for deployment",
                },
                feedback: {
                  type: "string",
                  description: "Optional feedback about the application",
                },
              },
              required: ["app_id"],
            },
          },
          {
            name: "list_ui_generations",
            description: "List all UI component and app generation requests",
            inputSchema: {
              type: "object",
              properties: {
                status_filter: {
                  type: "string",
                  description: "Filter by status",
                  enum: ["all", "preview_required", "approved", "cancelled"],
                  default: "all",
                },
              },
            },
          },
          {
            name: "cancel_ui_generation",
            description: "Cancel a pending UI generation request",
            inputSchema: {
              type: "object",
              properties: {
                generation_id: {
                  type: "string",
                  description: "The component or app ID to cancel",
                },
                reason: {
                  type: "string",
                  description: "Reason for cancellation",
                  default: "User cancelled",
                },
              },
              required: ["generation_id"],
            },
          },
          // Task Management Tools
          {
            name: "neurodock_rate_task_complexity",
            description: "Rate the complexity of a task using AI analysis",
            inputSchema: {
              type: "object",
              properties: {
                task_id: {
                  type: "string",
                  description: "The ID of the task to analyze"
                }
              },
              required: ["task_id"]
            }
          },
          {
            name: "neurodock_decompose_task", 
            description: "Decompose a complex task into smaller subtasks",
            inputSchema: {
              type: "object",
              properties: {
                task_id: {
                  type: "string",
                  description: "The ID of the task to decompose"
                },
                auto_create: {
                  type: "boolean", 
                  description: "Whether to automatically create the subtasks",
                  default: true
                }
              },
              required: ["task_id"]
            }
          },
          {
            name: "neurodock_complete_task",
            description: "Mark a task as completed and update project status", 
            inputSchema: {
              type: "object",
              properties: {
                task_id: {
                  type: "string",
                  description: "The ID of the task to complete"
                },
                completion_notes: {
                  type: "string",
                  description: "Optional notes about task completion",
                  default: ""
                }
              },
              required: ["task_id"]
            }
          },
          {
            name: "neurodock_remove_task",
            description: "Remove a task and handle dependencies",
            inputSchema: {
              type: "object", 
              properties: {
                task_id: {
                  type: "string",
                  description: "The ID of the task to remove"
                },
                force: {
                  type: "boolean",
                  description: "Force removal despite dependencies or subtasks",
                  default: false
                }
              },
              required: ["task_id"]
            }
          },
        ],
      };
    });

    // List available resources
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => {
      return {
        resources: [
          {
            uri: "neurodock://project/files",
            name: "Project Files",
            description: "Get the project file structure and important configuration files",
            mimeType: "application/json",
          },
          {
            uri: "neurodock://project/tasks",
            name: "Project Tasks",
            description: "Get all tasks and their current status",
            mimeType: "application/json",
          },
          {
            uri: "neurodock://project/memory",
            name: "Project Memory",
            description: "Get project memories and decisions",
            mimeType: "application/json",
          },
          {
            uri: "neurodock://project/context",
            name: "Project Context",
            description: "Get comprehensive project context including files, tasks, and memories",
            mimeType: "application/json",
          },
        ],
      };
    });

    // List available prompts
    this.server.setRequestHandler(ListPromptsRequestSchema, async () => {
      return {
        prompts: [
          {
            name: "neurodock-requirements-gathering",
            description: "Template for gathering project requirements systematically",
            arguments: [
              {
                name: "project_name",
                description: "Name of the project",
                required: false,
              },
              {
                name: "stakeholder",
                description: "Name or role of the stakeholder",
                required: false,
              },
            ],
          },
          {
            name: "neurodock-sprint-planning",
            description: "Template for agile sprint planning sessions",
            arguments: [
              {
                name: "sprint_number",
                description: "Sprint number",
                required: false,
              },
              {
                name: "duration_weeks",
                description: "Sprint duration in weeks",
                required: false,
              },
            ],
          },
          {
            name: "neurodock-daily-standup",
            description: "Template for daily standup meetings",
            arguments: [
              {
                name: "team_name",
                description: "Name of the team",
                required: false,
              },
              {
                name: "date",
                description: "Date of the standup",
                required: false,
              },
            ],
          },
        ],
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        const result = await this.executePythonFunction(name, args || {});
        return {
          content: [
            {
              type: "text",
              text: result,
            },
          ],
        };
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: `Error executing ${name}: ${error}`,
            },
          ],
          isError: true,
        };
      }
    });

    // Handle resource reads
    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const { uri } = request.params;

      try {
        const result = await this.executePythonResource(uri);
        return {
          contents: [
            {
              uri: uri,
              mimeType: "application/json",
              text: result,
            },
          ],
        };
      } catch (error) {
        return {
          contents: [
            {
              uri: uri,
              mimeType: "text/plain",
              text: `Error reading resource ${uri}: ${error}`,
            },
          ],
        };
      }
    });

    // Handle prompt requests
    this.server.setRequestHandler(GetPromptRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        let prompt = "";
        
        switch (name) {
          case "neurodock-requirements-gathering":
            const projectName = args?.project_name || "Project";
            const stakeholder = args?.stakeholder || "user";
            prompt = `# Requirements Gathering Session for ${projectName}

## Stakeholder: ${stakeholder}

### 1. Project Overview
- What is the main purpose/goal of this project?
- Who are the primary users/beneficiaries?
- What problem does this solve?

### 2. Functional Requirements
- What specific features/capabilities must the system have?
- What are the user stories or use cases?
- What are the acceptance criteria for each feature?

### 3. Non-Functional Requirements
- Performance requirements (speed, scalability, etc.)
- Security and compliance needs
- Usability and accessibility requirements
- Integration requirements with existing systems

### 4. Constraints and Assumptions
- Budget and timeline constraints
- Technology or platform restrictions
- Resource availability
- Regulatory or compliance requirements

### 5. Success Criteria
- How will success be measured?
- What are the key performance indicators (KPIs)?
- What constitutes project completion?

## Next Steps
1. Review and prioritize requirements
2. Identify dependencies and risks
3. Create initial project plan
4. Schedule follow-up sessions as needed

Use the neurodock_add_memory tool to capture important decisions and requirements discussed.`;
            break;

          case "neurodock-sprint-planning":
            const sprintNumber = args?.sprint_number || 1;
            const durationWeeks = args?.duration_weeks || 2;
            prompt = `# Sprint ${sprintNumber} Planning Session

## Sprint Details
- Duration: ${durationWeeks} weeks
- Start Date: [TO BE FILLED]
- End Date: [TO BE FILLED]

## Sprint Goal
[Define the high-level objective for this sprint]

## Backlog Review
1. Review product backlog priorities
2. Identify tasks ready for development
3. Estimate effort for each task

## Capacity Planning
- Team availability (accounting for holidays, PTO, etc.)
- Estimated velocity based on historical data
- Risk factors and dependencies

## Task Selection
- Select tasks that align with sprint goal
- Ensure tasks fit within team capacity
- Consider task dependencies

## Definition of Done
- All acceptance criteria met
- Code reviewed and approved
- Tests passing
- Documentation updated

Use neurodock_create_task to add selected tasks to the sprint.`;
            break;

          case "neurodock-daily-standup":
            const teamName = args?.team_name || "Development Team";
            const date = args?.date || new Date().toISOString().split('T')[0];
            prompt = `# Daily Standup - ${teamName}
## Date: ${date}

### Format
Each team member should briefly share:

1. **What did you complete yesterday?**
   - Specific tasks or progress made
   - Any blockers that were resolved

2. **What will you work on today?**
   - Planned tasks and priorities
   - Expected outcomes

3. **Are there any blockers or impediments?**
   - Technical challenges
   - Resource needs
   - Dependencies on other team members

### Notes and Action Items
- [ ] Follow up on any blockers identified
- [ ] Schedule follow-up discussions if needed

## Notes and Decisions
Use neurodock_add_memory to capture any important decisions or information shared.

## Team Availability
- [Note any planned absences or limited availability]

Keep this meeting focused and timeboxed to 15 minutes or less.`;
            break;

          default:
            throw new Error(`Unknown prompt: ${name}`);
        }

        return {
          description: `Generated ${name} prompt`,
          messages: [
            {
              role: "user",
              content: {
                type: "text",
                text: prompt,
              },
            },
          ],
        };
      } catch (error) {
        throw new Error(`Error generating prompt ${name}: ${error}`);
      }
    });
  }

  async run(): Promise<void> {
    const transport = new StdioServerTransport();
    console.error("🚀 NeuroDock MCP Server starting...");
    console.error("🔗 Connecting to Python backend...");
    
    // Test Python backend connection
    try {
      await this.executePythonFunction("neurodock_get_project_status", {});
      console.error("✅ Python backend connected successfully!");
    } catch (error) {
      console.error("⚠️  Python backend connection failed, some features may be limited:", error);
    }
    
    await this.server.connect(transport);
    console.error("✅ NeuroDock MCP Server ready with full feature set!");
  }
}

// Start the server
const server = new NeuroDockMCPServer();
server.run().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});