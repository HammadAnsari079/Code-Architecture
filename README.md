# Code-to-Architecture Visualizer

A web application that analyzes uploaded codebases and automatically generates system architecture diagrams, dependency graphs, and data flow visualizations.

## Features

- **File Upload & Processing**: Support for .zip, .tar.gz uploads
- **Code Analysis Engine**: Parses Python, JavaScript, and Java files
- **Architecture Diagram Generation**: Auto-detects architectural patterns
- **Dependency Graph**: Module-level dependency mapping
- **Data Flow Diagram**: Traces function call chains and data transformations
- **Interactive Visualization**: Click nodes to see code snippets, filter by component
- **Insights & Metrics**: Cyclomatic complexity, code coupling metrics, dead code detection

## Tech Stack

- **Backend**: Django 5.x with Django REST Framework
- **Frontend**: HTML5, CSS3 (Tailwind CSS), Vanilla JavaScript
- **Visualization**: D3.js, Cytoscape.js, Mermaid.js
- **Code Analysis**: ast (Python), esprima (JavaScript), javalang (Java)
- **Database**: SQLite (default Django)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd code_visualizer
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Start the development server:
   ```bash
   python manage.py runserver
   ```

6. Visit `http://127.0.0.1:8000` in your browser

## Usage

1. Upload a codebase archive (.zip or .tar.gz)
2. The system will automatically analyze the code
3. View generated architecture diagrams, dependency graphs, and data flow visualizations
4. Explore code metrics and insights

## API Endpoints

- `POST /api/upload/` - Upload a codebase
- `GET /api/projects/` - List all analyzed projects
- `GET /api/analyze/<project_id>/` - Trigger analysis for a project
- `GET /api/diagram/<project_id>/<diagram_type>/` - Get diagram data
- `GET /api/export/<project_id>/<diagram_type>/` - Export diagram
- `GET /api/metrics/<project_id>/` - Get code metrics

## Project Structure

```
code_visualizer/
├── analyzer/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── utils/
│       ├── analyzer.py
│       ├── file_handler.py
│       ├── graph_generator.py
│       ├── mermaid_generator.py
│       └── metrics_calculator.py
├── templates/
│   └── index.html
├── static/
├── manage.py
├── requirements.txt
└── README.md
```

## License

This project is licensed under the MIT License.