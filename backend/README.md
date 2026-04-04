# Mediscan Backend

FastAPI backend running on Raspberry Pi for medical data processing.

## Prerequisites

### 1. Install uv

[Install and setup uv](https://docs.astral.sh/uv/getting-started/installation/)

### 2. Python Version
- **Required**: Python 3.11.14

## Setup

### 1. Create Virtual Environment

```bash
cd backend

# Create virtual environment
uv venv --python 3.11.14 env

# Activate the virtual environment
source env/bin/activate

# To deactivate
deactivate
```

### 2. Install Dependencies

```bash
# Install all dependencies
uv pip install -r requirements.txt

# Install additional packages for AI features
uv pip install mlx-vlm torch torchvision aiohttp aiofiles
```

### 3. Run the Backend

```bash
# Development (with hot reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Verify

```bash
# Health check
curl http://localhost:8000/health

# Root endpoint
curl http://localhost:8000/
```

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── routes.py          # REST API endpoints
│   ├── core/
│   │   └── config.py          # Configuration settings
│   ├── models/
│   │   └── schema.py          # Pydantic models
│   ├── services/
│   │   ├── database.py        # SQLite database operations
│   │   ├── image_service.py   # Image upload & duplicate detection
│   │   ├── ai_service.py      # AI extraction & prescription saving
│   │   └── ehr_service.py     # EHR operations
│   └── main.py                # FastAPI application entry
├── data/
│   ├── mediscan.db            # SQLite database
│   └── prescriptions/         # Uploaded images
├── env/                       # Virtual environment
└── requirements.txt           # Python dependencies
```

## API Endpoints

### Images

```bash
# Upload image
curl -X POST http://localhost:8000/api/images/upload \
  -F "file=@path/to/image.jpg"

# Capture from IP Webcam
curl -X POST "http://localhost:8000/api/images/capture?url=http://192.168.1.100:8080/video"

# List images
curl http://localhost:8000/api/images

# Get image
curl http://localhost:8000/api/images/{image_id}

# Download image file
curl http://localhost:8000/api/images/{image_id}/file -o image.jpg

# Delete image
curl -X DELETE http://localhost:8000/api/images/{image_id}
```

### Patients

```bash
# Create patient
curl -X POST http://localhost:8000/api/patients \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "age": 30, "gender": "male", "phone": "1234567890"}'

# List patients
curl http://localhost:8000/api/patients

# Get patient
curl http://localhost:8000/api/patients/{patient_id}

# Update patient
curl -X PATCH http://localhost:8000/api/patients/{patient_id} \
  -H "Content-Type: application/json" \
  -d '{"age": 31}'

# Delete patient
curl -X DELETE http://localhost:8000/api/patients/{patient_id}
```

### Prescriptions

```bash
# Extract prescription (AI)
curl -X POST "http://localhost:8000/api/extract-prescription/{image_id}"

# Extract with patient association
curl -X POST "http://localhost:8000/api/extract-prescription/{image_id}?patient_id={patient_id}"

# Get prescription
curl http://localhost:8000/api/prescriptions/{prescription_id}

# Get patient's prescriptions
curl http://localhost:8000/api/patients/{patient_id}/prescriptions

# Create prescription manually
curl -X POST http://localhost:8000/api/prescriptions \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "...", "image_id": "...", "extracted_text": "..."}'
```

### EHR Records

```bash
# Create EHR record
curl -X POST http://localhost:8000/api/ehr \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "...", "record_type": "diagnosis", "data": {"diagnosis": "Fever"}}'

# Get patient's EHR records
curl http://localhost:8000/api/patients/{patient_id}/ehr
```

## Features

### Duplicate Detection
Images are hashed using SHA256 at upload. Duplicate images return existing data without calling AI.

### Auto Patient Creation
When extracting prescriptions, patient info (name, age, gender) is automatically extracted and created if not exists.

### Image Sources
- `upload` - Manual upload via API
- `ip_webcam` - Captured from IP Webcam

## Database

The backend uses SQLite. Database is automatically created on first run.

**Location**: `backend/data/mediscan.db`

**Tables**:
- `images` - Uploaded images with file hashes
- `patients` - Patient records
- `prescriptions` - Extracted prescription data
- `ehr_records` - EHR records

## Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_filename.py::test_function_name
```

## Linting

```bash
# Install dev dependencies
uv pip install ruff mypy pytest pytest-cov

# Run linter
ruff check --fix .

# Run formatter
ruff format .

# Run type checker
mypy .
```

## Troubleshooting

### Port already in use
```bash
# Kill existing process
lsof -ti:8000 | xargs kill
```

### Module not found
Ensure you're in the virtual environment:
```bash
source env/bin/activate
```

### Import errors
Check PYTHONPATH includes backend root:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## Environment Variables

Create a `.env` file in `backend/` directory:

```env
# Database
DB_PATH=data/mediscan.db

# Image Storage
IMAGE_STORAGE_PATH=data/prescriptions

# AI Server
AI_SERVER_URL=http://localhost:8001
AI_MODEL=mlx-community/Qwen3.5-9B-MLX-4bit
AI_MAX_TOKENS=10000
AI_TIMEOUT=300

# Server
HOST=0.0.0.0
PORT=8000
```

## License

MIT