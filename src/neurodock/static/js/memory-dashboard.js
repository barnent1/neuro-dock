/**
 * NeuroDock Memory Dashboard JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize UI elements
    const createMemoryBtn = document.getElementById('create-memory-btn');
    const saveMemoryBtn = document.getElementById('save-memory-btn');
    const refreshBtn = document.getElementById('refresh-btn');
    const searchInput = document.getElementById('search-memories');
    const gridViewBtn = document.getElementById('grid-view-btn');
    const listViewBtn = document.getElementById('list-view-btn');
    const filterBtn = document.getElementById('filter-btn');
    const memoriesContainer = document.getElementById('memories-container');
    
    // Modal elements
    const createMemoryModal = new bootstrap.Modal(document.getElementById('createMemoryModal'));
    
    // Load memories when page loads
    loadMemories();
    
    // Event listeners
    createMemoryBtn.addEventListener('click', function() {
        createMemoryModal.show();
    });
    
    saveMemoryBtn.addEventListener('click', createMemory);
    
    refreshBtn.addEventListener('click', function() {
        loadMemories();
    });
    
    searchInput.addEventListener('input', function() {
        const query = searchInput.value.trim();
        if (query.length > 2 || query.length === 0) {
            loadMemories(query);
        }
    });
    
    gridViewBtn.addEventListener('click', function() {
        gridViewBtn.classList.add('active');
        listViewBtn.classList.remove('active');
        // Future enhancement: implement grid view
    });
    
    listViewBtn.addEventListener('click', function() {
        listViewBtn.classList.add('active');
        gridViewBtn.classList.remove('active');
        // Default view is list view
    });
    
    /**
     * Load memories from the API
     */
    function loadMemories(searchQuery = '') {
        memoriesContainer.innerHTML = '<div class="text-center py-5"><div class="spinner-border" role="status"></div><p class="mt-3">Loading memories...</p></div>';
        
        let url = '/api/memories';
        if (searchQuery) {
            url += `?query=${encodeURIComponent(searchQuery)}`;
        }
        
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load memories');
                }
                return response.json();
            })
            .then(data => {
                displayMemories(data);
            })
            .catch(error => {
                memoriesContainer.innerHTML = `
                    <div class="alert alert-danger m-3" role="alert">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        ${error.message}
                    </div>
                `;
                console.error('Error loading memories:', error);
            });
    }
    
    /**
     * Display memories in the UI
     */
    function displayMemories(memories) {
        if (memories.length === 0) {
            memoriesContainer.innerHTML = `
                <div class="text-center py-5">
                    <i class="bi bi-search fs-1 mb-3"></i>
                    <p>No memories found. Try a different search or create a new memory.</p>
                </div>
            `;
            return;
        }
        
        memoriesContainer.innerHTML = '';
        
        memories.forEach(memory => {
            const categoryClass = getCategoryClass(memory.type);
            const sourceClass = getSourceClass(memory.source);
            const formattedDate = formatDate(memory.timestamp);
            
            const memoryElement = document.createElement('div');
            memoryElement.className = 'memory-item d-flex align-items-center';
            memoryElement.innerHTML = `
                <div class="form-check me-3">
                    <input class="form-check-input" type="checkbox" value="${memory.id}">
                </div>
                <div class="memory-content flex-grow-1">
                    "${memory.content}"
                </div>
                <div class="memory-category text-center">
                    <span class="memory-category ${categoryClass}">${memory.type.toLowerCase()} <span class="memory-category-count">+2</span></span>
                </div>
                <div class="memory-source text-center">
                    <span class="memory-source-icon ${sourceClass}">${memory.source.charAt(0).toUpperCase()}</span>
                    ${memory.source}
                </div>
                <div class="memory-date text-center">
                    ${formattedDate}
                </div>
                <div class="memory-actions text-center">
                    <button class="btn btn-sm btn-dark" onclick="viewMemory('${memory.id}')">
                        <i class="bi bi-three-dots-vertical"></i>
                    </button>
                </div>
            `;
            
            memoriesContainer.appendChild(memoryElement);
        });
    }
    
    /**
     * Create a new memory
     */
    function createMemory() {
        const content = document.getElementById('memory-content').value.trim();
        const type = document.getElementById('memory-type').value;
        const source = document.getElementById('memory-source').value.trim();
        const projectId = document.getElementById('memory-project').value.trim();
        
        if (!content) {
            alert('Memory content is required');
            return;
        }
        
        const memoryData = {
            content: content,
            type: type,
            source: source,
        };
        
        if (projectId) {
            memoryData.project_id = projectId;
        }
        
        fetch('/api/memories', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(memoryData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to create memory');
            }
            return response.json();
        })
        .then(data => {
            createMemoryModal.hide();
            document.getElementById('create-memory-form').reset();
            loadMemories();
        })
        .catch(error => {
            alert(`Error creating memory: ${error.message}`);
            console.error('Error creating memory:', error);
        });
    }
    
    /**
     * Format memory date
     */
    function formatDate(isoDate) {
        const date = new Date(isoDate);
        const day = date.getDate();
        const month = date.toLocaleString('default', { month: 'short' });
        const year = date.getFullYear();
        const hours = date.getHours();
        const minutes = date.getMinutes().toString().padStart(2, '0');
        const ampm = hours >= 12 ? 'PM' : 'AM';
        const formattedHours = hours % 12 || 12;
        
        return `${day} ${month} ${year}, ${formattedHours}:${minutes} ${ampm}`;
    }
    
    /**
     * Get CSS class for memory type/category
     */
    function getCategoryClass(type) {
        switch(type.toLowerCase()) {
            case 'important':
                return 'cat-education';
            case 'normal':
                return 'cat-health';
            case 'trivial':
                return 'cat-preference';
            case 'code':
                return 'cat-education';
            case 'comment':
                return 'cat-relationship';
            case 'documentation':
                return 'cat-education';
            default:
                return 'cat-preference';
        }
    }
    
    /**
     * Get CSS class for memory source
     */
    function getSourceClass(source) {
        switch(source.toLowerCase()) {
            case 'manual':
                return 'source-manual';
            case 'chatgpt':
                return 'source-chatgpt';
            case 'claude':
                return 'source-claude';
            default:
                return 'source-manual';
        }
    }
    
    // Expose viewMemory function to global scope for button click access
    window.viewMemory = function(memoryId) {
        // Future enhancement: implement memory viewing modal
        console.log('View memory:', memoryId);
        // For now, let's just alert
        alert(`View memory ${memoryId}`);
    };
});
