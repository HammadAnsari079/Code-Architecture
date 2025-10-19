# Simplified Code Analysis Tool

This is a simplified version of the Code-to-Architecture Visualizer with a streamlined interface.

## Features

1. **Simple Upload Interface**: Clean UI with just file upload functionality
2. **Two Analysis Options**:
   - **Analyze Code Flow**: Generates a comprehensive flowchart showing code structure
   - **Database Relations**: Shows database table relationships

## How to Use

1. Navigate to `/simple/` in your browser
2. Upload your code files or zip folder
3. Click either:
   - "Analyze Code Flow" to see the code structure visualization
   - "Database Relations" to see database table relationships

## Interface Elements

- **Upload Area**: Drag and drop or browse for files
- **File List**: Shows selected files with sizes
- **Action Buttons**: 
  - "Analyze Code Flow" - Generates a flowchart showing how your code works
  - "Database Relations" - Shows how database tables are connected
- **Progress Indicator**: Shows processing status

## Visualization Types

### Code Flow Chart
- **Rectangles**: Files
- **Ovals**: Classes
- **Boxes**: Functions
- **Arrows**: Relationships and data flow

This visualization helps non-technical users understand what the code does and how different parts work together.

### Database Relations
- **Boxes**: Database tables
- **Lines with arrows**: Relationships between tables
- **Labels**: Show relationship types (one-to-one, one-to-many, etc.)

This visualization helps understand how data is structured and related in the system.

## Supported File Types

- Python (.py)
- JavaScript (.js)
- Java (.java)
- Zip archives (.zip)

## Access Points

- Main simplified interface: `/simple/`
- Analysis results: `/simple/results/<project_id>/`
- API endpoints for data: 
  - `/simple/api/process/`
  - `/simple/api/flowchart/<project_id>/`
  - `/simple/api/database/<project_id>/`