// Dashboard JavaScript

let currentProject = null;
const confirmationModal = new bootstrap.Modal(document.getElementById('confirmationModal'));
let pendingAction = null;

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', async () => {
    await loadProjects();
    setupEventListeners();
    loadCurrentTab();
});

// Load projects from neurodock.json or available projects
async function loadProjects() {
    try {
        const response = await fetch('/api/projects');
        const projects = await response.json();
        
        const selector = document.getElementById('projectSelector');
        selector.innerHTML = '';
        
        projects.forEach(project => {
            const option = document.createElement('option');
            option.value = project.id;
            option.textContent = project.name;
            selector.appendChild(option);
        });
        
        // Try to load default project from neurodock.json
        const defaultProject = projects.find(p => p.is_default);
        if (defaultProject) {
            selector.value = defaultProject.id;
            currentProject = defaultProject;
            refreshData();
        }
    } catch (error) {
        console.error('Failed to load projects:', error);
    }
}

// Set up event listeners
function setupEventListeners() {
    // Project selection
    document.getElementById('projectSelector').addEventListener('change', (e) => {
        currentProject = e.target.value;
        refreshData();
    });
    
    // Confirmation input validation
    document.getElementById('confirmationInput').addEventListener('input', (e) => {
        const confirmButton = document.getElementById('confirmActionButton');
        confirmButton.disabled = e.target.value !== currentProject?.name;
    });
}

// Load current tab data
function loadCurrentTab() {
    const activeTab = document.querySelector('.tab-pane.active');
    if (activeTab.id === 'memoriesTab') {
        loadMemories();
    } else {
        loadTasks();
    }
}

// Refresh all data
async function refreshData() {
    if (currentProject) {
        await Promise.all([
            loadMemories(),
            loadTasks()
        ]);
    }
}

// Load memories
async function loadMemories() {
    if (!currentProject) return;
    
    try {
        const response = await fetch(`/api/memories?project_id=${currentProject.id}`);
        const memories = await response.json();
        
        const tbody = document.getElementById('memoriesList');
        tbody.innerHTML = '';
        
        memories.forEach(memory => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><span class="badge bg-${getMemoryTypeColor(memory.type)}">${memory.type}</span></td>
                <td>${escapeHtml(memory.content)}</td>
                <td>${escapeHtml(memory.source)}</td>
                <td>${new Date(memory.timestamp).toLocaleString()}</td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="deleteMemory('${memory.id}')">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Failed to load memories:', error);
    }
}

// Load tasks
async function loadTasks() {
    if (!currentProject) return;
    
    try {
        const response = await fetch(`/api/tasks?project_id=${currentProject.id}`);
        const tasks = await response.json();
        
        const tbody = document.getElementById('tasksList');
        tbody.innerHTML = '';
        
        tasks.forEach(task => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <select class="form-select form-select-sm bg-dark text-light border-secondary" 
                            onchange="updateTaskStatus('${task.id}', this.value)">
                        ${getStatusOptions(task.status)}
                    </select>
                </td>
                <td><span class="badge bg-${getPriorityColor(task.priority)}">${task.priority}</span></td>
                <td>${escapeHtml(task.title)}</td>
                <td>${task.task_type}</td>
                <td>${task.complexity}</td>
                <td>${task.estimated_hours}</td>
                <td>
                    <div class="progress bg-dark">
                        <div class="progress-bar" role="progressbar" style="width: ${getTaskProgress(task)}%"></div>
                    </div>
                </td>
                <td>
                    <button class="btn btn-sm btn-primary me-1" onclick="editTask('${task.id}')">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteTask('${task.id}')">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Failed to load tasks:', error);
    }
}

// Add memory
async function addMemory() {
    if (!currentProject) return;
    
    const form = document.getElementById('addMemoryForm');
    const formData = new FormData(form);
    
    const memoryData = {
        content: formData.get('content'),
        type: formData.get('type'),
        source: formData.get('source'),
        project_id: currentProject.id
    };
    
    try {
        const response = await fetch('/api/memories', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(memoryData)
        });
        
        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('addMemoryModal')).hide();
            form.reset();
            await loadMemories();
        }
    } catch (error) {
        console.error('Failed to add memory:', error);
    }
}

// Add task
async function addTask() {
    if (!currentProject) return;
    
    const form = document.getElementById('addTaskForm');
    const formData = new FormData(form);
    
    const taskData = {
        title: formData.get('title'),
        description: formData.get('description'),
        task_type: formData.get('task_type'),
        priority: parseInt(formData.get('priority')),
        estimated_hours: parseFloat(formData.get('estimated_hours')) || null,
        estimated_loc: parseInt(formData.get('estimated_loc')) || null,
        skills_required: formData.get('skills_required').split(',').map(s => s.trim()).filter(Boolean),
        project_id: currentProject.id
    };
    
    try {
        const response = await fetch('/api/tasks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(taskData)
        });
        
        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('addTaskModal')).hide();
            form.reset();
            await loadTasks();
        }
    } catch (error) {
        console.error('Failed to add task:', error);
    }
}

// Update task status
async function updateTaskStatus(taskId, status) {
    try {
        const response = await fetch(`/api/tasks/${taskId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status })
        });
        
        if (response.ok) {
            await loadTasks();
        }
    } catch (error) {
        console.error('Failed to update task status:', error);
    }
}

// Delete memory
async function deleteMemory(memoryId) {
    if (!confirm('Are you sure you want to delete this memory?')) return;
    
    try {
        const response = await fetch(`/api/memories/${memoryId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            await loadMemories();
        }
    } catch (error) {
        console.error('Failed to delete memory:', error);
    }
}

// Delete task
async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) return;
    
    try {
        const response = await fetch(`/api/tasks/${taskId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            await loadTasks();
        }
    } catch (error) {
        console.error('Failed to delete task:', error);
    }
}

// Handle project actions
function confirmAction(action) {
    if (!currentProject) return;
    
    pendingAction = action;
    document.getElementById('projectNameToType').textContent = currentProject.name;
    document.getElementById('confirmationInput').value = '';
    document.getElementById('confirmActionButton').disabled = true;
    
    confirmationModal.show();
}

// Execute confirmed action
async function executeConfirmedAction() {
    if (!currentProject || !pendingAction) return;
    
    try {
        const response = await fetch(`/api/projects/${currentProject.id}/${pendingAction}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            confirmationModal.hide();
            await refreshData();
        }
    } catch (error) {
        console.error('Failed to execute action:', error);
    }
}

// Utility functions
function getMemoryTypeColor(type) {
    const colors = {
        important: 'danger',
        normal: 'primary',
        trivial: 'secondary',
        code: 'success',
        documentation: 'info'
    };
    return colors[type] || 'secondary';
}

function getPriorityColor(priority) {
    const colors = {
        1: 'secondary',  // LOW
        3: 'info',       // MEDIUM
        5: 'warning',    // HIGH
        8: 'danger'      // CRITICAL
    };
    return colors[priority] || 'secondary';
}

function getStatusOptions(currentStatus) {
    const statuses = [
        { value: 'pending', label: 'Pending' },
        { value: 'in_progress', label: 'In Progress' },
        { value: 'blocked', label: 'Blocked' },
        { value: 'completed', label: 'Completed' },
        { value: 'failed', label: 'Failed' }
    ];
    
    return statuses.map(status => 
        `<option value="${status.value}" ${status.value === currentStatus ? 'selected' : ''}>
            ${status.label}
        </option>`
    ).join('');
}

function getTaskProgress(task) {
    if (task.status === 'completed') return 100;
    if (task.status === 'failed') return 0;
    if (task.status === 'in_progress') return 50;
    if (task.status === 'blocked') return task.progress || 25;
    return 0;
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
