# Mediscan IoT - Agent Guidelines

## Project Overview

This is a medical data processing system with a FastAPI backend running on Raspberry Pi. The backend handles image processing, AI inference for prescription parsing, and EHR data management.

- **Backend**: Python FastAPI application in `backend/app/`
- **AI Inference**: MLX-VLM for vision language model inference (`ai-inference/`)
- **Python Version**: 3.11.14
- **Package Manager**: `uv` (required)

## Build & Development Commands

### Backend Setup

```bash
# Create virtual environment (required)
cd backend
uv venv --python 3.11.14 mlx-vlm

# Activate environment
source mlx-vlm/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Run development server (hot reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run production server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Testing Commands

```bash
# Run all tests (pytest)
pytest

# Run a single test file
pytest tests/test_filename.py

# Run a single test function
pytest tests/test_filename.py::test_function_name

# Run tests with coverage
pytest --cov=app --cov-report=html

# Run tests matching a pattern
pytest -k "test_pattern"
```

### Linting & Type Checking

```bash
# Install dev dependencies
uv pip install ruff mypy pytest pytest-cov

# Run Ruff linter (auto-fix)
ruff check --fix .

# Run Ruff formatter
ruff format .

# Run type checker
mypy .

# Run all checks
ruff check . && ruff format . && mypy .
```

## Code Style Guidelines

### Imports

```python
# Standard library imports first
import os
import json
from typing import Optional, List

# Third-party imports
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Local application imports
from app.api.routes import router
from app.core.config import settings
```

- Use absolute imports within the `app` package
- Group imports: stdlib → third-party → local
- Sort alphabetically within groups
- Avoid wildcard imports (`from x import *`)

### Formatting

- **Line length**: 100 characters max
- **Indentation**: 4 spaces (no tabs)
- **Trailing commas**: Yes, for multi-line structures
- **Blank lines**: 2 between top-level definitions, 1 between functions
- Use Ruff formatter for automatic formatting

### Types

- Use Python 3.11+ type hints
- Explicitly type function arguments and return values
- Use `Optional[X]` instead of `X | None`
- Use `List[X]` (not `list[x]`) for compatibility

```python
def process_image(image_path: str) -> Optional[dict]:
    """Process a medical image and return metadata."""
    result: dict = {}
    return result
```

### Naming Conventions

- **Variables/functions**: `snake_case` (e.g., `image_service`, `process_data`)
- **Classes**: `PascalCase` (e.g., `HealthResponse`, `PatientRecord`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_IMAGE_SIZE`)
- **Private methods**: Prefix with underscore (e.g., `_internal_method`)
- Use descriptive, meaningful names (avoid `x`, `temp`, `data`)

### Error Handling

- Use FastAPI's `HTTPException` for HTTP errors
- Return proper HTTP status codes:
  - `200` - Success
  - `201` - Created
  - `400` - Bad Request
  - `401` - Unauthorized
  - `404` - Not Found
  - `500` - Internal Server Error

```python
from fastapi import HTTPException, status

def get_patient(patient_id: str) -> Patient:
    patient = db.get(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )
    return patient
```

- Never expose internal errors to clients; log them internally
- Use try/except for expected error conditions, not for flow control

### Pydantic Models

```python
from pydantic import BaseModel, Field
from typing import Optional

class PatientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=0, le=150)
    medical_history: Optional[str] = None

class PatientResponse(BaseModel):
    id: str
    name: str
    age: int
    medical_history: Optional[str] = None
    
    model_config = {"from_attributes": True}
```

### Project Structure

```
backend/
├── app/
│   ├── api/          # API routes and endpoints
│   ├── core/         # Configuration and core settings
│   ├── models/       # Pydantic schemas
│   ├── services/     # Business logic (AI, EHR, image)
│   ├── utils/        # Utility functions
│   └── main.py       # FastAPI application entry point
├── requirements.txt
└── README.md
```

### Async/Await

- Use async for I/O-bound operations (API calls, file I/O)
- Keep async functions non-blocking
- Use `await` for async calls, never use `.result()` or `.wait()`

### Documentation

- Add docstrings to all public functions and classes
- Use Google-style docstrings:

```python
def process_prescription(image_path: str) -> dict:
    """Process a prescription image using AI inference.

    Args:
        image_path: Path to the prescription image file.

    Returns:
        Dict containing extracted prescription data.

    Raises:
        ValueError: If image format is unsupported.
        RuntimeError: If AI inference fails.
    """
```

### Configuration

- Use environment variables for configuration
- Use `pydantic-settings` for typed settings
- Never hardcode secrets; use `.env` files (add to `.gitignore`)

### Logging

- Use Python's `logging` module
- Include contextual information in log messages
- Use appropriate log levels: DEBUG, INFO, WARNING, ERROR

```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Processing image: {image_path}")
logger.error(f"Failed to process image: {e}")
```

### Security

- Never log sensitive data (passwords, tokens, medical records)
- Validate all user inputs
- Use HTTPS in production
- Keep dependencies updated

## Testing Guidelines

- Write tests for all new features
- Use descriptive test names: `test_<function>_with_<condition>`
- Follow AAA pattern: Arrange, Act, Assert
- Mock external dependencies
- Keep tests fast (< 1 second each when possible)

## Git Conventions

- Use meaningful commit messages
- Keep commits atomic (one feature/fix per commit)
- Create feature branches: `feature/<description>`
- Create bugfix branches: `fix/<description>`

## Common Issues

- **Module not found**: Ensure you're in the correct virtual environment
- **Port in use**: Kill existing process `lsof -ti:8000 | xargs kill`
- **Import errors**: Check PYTHONPATH includes backend root
