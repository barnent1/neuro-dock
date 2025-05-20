# NeuroDock Memory Dashboard

The Memory Dashboard provides a user-friendly interface for viewing, searching, and managing memories in the NeuroDock system.

![Memory Dashboard](https://github.com/your-username/neurodock/raw/main/docs/images/memory-dashboard.png)

## Features

- **View and Search Memories:** Easily browse through your stored memories or search for specific content.
- **Filter by Type:** Filter memories by their type (Important, Normal, Trivial, Code, etc.).
- **Create New Memories:** Add new memories directly from the dashboard.
- **Delete Memories:** Remove memories that are no longer needed.
- **View Memory Details:** View detailed information about each memory.
- **Project Filtering:** Filter memories by project ID to view only memories related to a specific project.

## Accessing the Dashboard

The Memory Dashboard is available at:

- **URL:** `http://localhost:4000/ui/memories`
- **Port:** 4000 (configurable)

## Usage

### Viewing Memories

1. Navigate to `http://localhost:4000/ui/memories`
2. The dashboard will display a list of recent memories
3. Click on a memory to view its details

### Searching Memories

1. Enter your search query in the search box at the top of the dashboard
2. The results will update as you type
3. Search is performed on the memory content

### Creating Memories

1. Click the "Create Memory" button in the top right corner
2. Fill in the memory details:
   - **Content:** The text content of the memory
   - **Type:** The type of memory (Normal, Important, Code, etc.)
   - **Source:** The source of the memory (default is "Manual")
   - **Project ID:** Optional project identifier to associate with this memory
3. Click "Create Memory" to save

### Deleting Memories

1. Click the three dots (...) button on a memory
2. Select "Delete" from the menu
3. Confirm the deletion when prompted

## API Endpoints

The Memory Dashboard interacts with the following API endpoints:

- `GET /api/memories`: Get all memories (with optional filters)
- `POST /api/memories`: Create a new memory
- `GET /api/memories/{memory_id}`: Get a specific memory
- `DELETE /api/memories/{memory_id}`: Delete a memory

## Customization

You can customize the dashboard by modifying the following files:

- `app/templates/memory_dashboard.html`: Main HTML template
- `app/static/css/styles.css`: CSS styles
- `app/static/js/memory-dashboard.js`: JavaScript functionality

## Integration with Neo4j

The Memory Dashboard uses the Neo4j database as its storage backend. This provides several advantages:

- **Relationship Management:** Neo4j's graph database is ideal for handling relationships between memories
- **Fast Queries:** Graph queries are optimized for retrieving related data
- **Scalability:** Neo4j can handle large numbers of memories efficiently

## Troubleshooting

If you encounter issues with the Memory Dashboard:

1. Check that the NeuroDock service is running (`docker-compose up`)
2. Verify that Neo4j is accessible (`http://localhost:7474`)
3. Check the browser console for JavaScript errors
4. Review the server logs for backend errors
