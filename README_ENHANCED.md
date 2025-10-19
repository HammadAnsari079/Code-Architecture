# Enhanced Code-to-Architecture Visualizer

This is an enhanced version of the Code-to-Architecture Visualizer with professional-grade features for visualizing code structure and database schemas.

## Features

### 1. True Control Flow Diagrams
- Generates accurate flowcharts showing the logical execution path through a single function/method
- Uses standard flowchart symbols:
  - Oval: Start/End points
  - Rectangle: Process/Statement
  - Diamond: Decision points (if/elif/else)
  - Parallelogram: Input/Output
- Each node contains:
  - Node type (start/end/process/decision/io)
  - Label (plain English description of what the code does)
  - Code snippet (actual code line)
  - File location (file path, line number, column number)

### 2. Proper Database ERD (Entity Relationship Diagram)
- Visualizes database schema with visible relationship lines between tables
- Shows:
  - Table names with bold headers
  - Fields with appropriate icons:
    - 🔑 Primary Key
    - 🔗 Foreign Key
    - ⭐ Unique constraint
    - 📝 Regular field
  - Relationship lines connecting foreign keys to primary keys
  - Cardinality labels (1:N, N:M)

### 3. Interactive Visualization
- Every node/box/table is clickable with detailed information
- Click features:
  - Flowchart nodes: Shows code snippet + file location + line number
  - Database tables: Highlights all relationship lines connected to it
  - Relationship lines: Shows FK details (which field connects where)
- "Jump to Code" functionality:
  - Opens file in VS Code via vscode:// protocol
  - Alternative in-browser code editor (Monaco/CodeMirror) at exact line
  - File download option

## Technical Implementation

### Backend
- **Python AST**: For parsing Python code and building Control Flow Graphs
- **Django Models**: For extracting database schema information
- **ControlFlowGraphBuilder**: Custom class that visits AST nodes and creates flowchart nodes
- **DatabaseSchemaExtractor**: Parses Django models to extract fields, constraints, and relationships

### Frontend
- **Cytoscape.js**: For interactive graph visualization
- **Dagre Layout**: For hierarchical flowchart layout
- **COSE Layout**: For force-directed ERD layout
- **Tailwind CSS**: For responsive UI design

## API Endpoints

### Flowchart Generation
```
GET /enhanced/api/flowchart/<project_id>/<file_path>/<function_name>/
```
Returns Cytoscape.js formatted flowchart data for a specific function.

### Database ERD Generation
```
GET /enhanced/api/erd/<project_id>/
```
Returns Cytoscape.js formatted ERD data for the project's database schema.

### Code Snippet Retrieval
```
GET /enhanced/api/code-snippet/<file_path>/<line_number>/
```
Returns code snippet for a specific file and line number.

### Jump to Code
```
POST /enhanced/api/jump-to-code/
```
Generates URL to jump to code in editor.

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations:
```bash
python manage.py migrate
```

3. Start the development server:
```bash
python manage.py runserver
```

## Usage

1. Navigate to the main page
2. Upload your codebase files
3. Select the "Enhanced Visualization" option
4. Choose between:
   - Function Flow: Visualize control flow of specific functions
   - Database Schema: View ERD of your database models
   - Architecture: See component diagram of your codebase
5. Interact with the diagrams:
   - Click nodes to see details
   - Click relationship lines to see FK information
   - Use "Jump to Code" to navigate to source files

## Development

### Running Tests

```bash
python manage.py test
```

### Adding New Features

1. Extend the `ControlFlowGraphBuilder` for new AST node types
2. Enhance the `DatabaseSchemaExtractor` for additional field types
3. Modify the Cytoscape.js styles in `EnhancedGraphGenerator` for new visual elements
4. Update the frontend template `enhanced_visualization.html` for new UI components

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.