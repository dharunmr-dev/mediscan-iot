# Mediscan IoT

An intelligent medical document digitization system that transforms unstructured prescriptions into structured, accessible patient health information.

## Problem Statement

Healthcare systems operate on fragmented and heterogeneous medical records, including handwritten prescriptions, printed reports, and unstructured digital documents. This fragmentation results in poor accessibility of patient information, increased risk of data inconsistency, and delays in clinical decision-making.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Mobile Phone   │────▶│  Raspberry Pi   │────▶│   MacBook M4    │
│  (IP Webcam)    │     │  (Backend API)   │     │  (MLX-VLM AI)   │
└─────────────────┘     └────────┬────────┘     └────────┬────────┘
                                  │                     │
                                  ▼                     ▼
                         ┌─────────────────┐     ┌─────────────────┐
                         │  SQLite DB      │◀────│  Next.js        │
                         │  (mediscan.db)  │     │  (Dashboard)    │
                         └─────────────────┘     └─────────────────┘
```

## Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| Image Capture | IP Webcam (Mobile) | Stream prescription images |
| Edge Backend | FastAPI (Raspberry Pi) | REST API, image processing, data storage |
| AI Inference | MLX-VLM (Qwen3.5-9B-MLX-4bit) | Extract prescription data from images |
| Database | SQLite | Store patients, images, prescriptions |
| Dashboard | Next.js (Future) | Web interface for doctors |

## Project Structure

```
mediscan-iot/
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── api/          # REST API endpoints
│   │   ├── core/          # Configuration
│   │   ├── models/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── main.py         # Application entry
│   ├── data/              # Database & images
│   └── env/                # Virtual environment
├── ai-inference/          # AI Server
│   └── server.py          # MLX-VLM HTTP server
├── data/
│   └── prescriptions/     # Sample prescription images
├── docs/                  # Documentation
└── AGENTS.md              # Agent guidelines for AI coding
```

## Quick Start

### Prerequisites

- Python 3.11.14
- uv (package manager)
- MLX-compatible Mac (for AI inference)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
uv venv --python 3.11.14 env
source env/bin/activate

# Install dependencies
uv pip install -r requirements.txt
uv pip install mlx-vlm torch torchvision

# Run backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. AI Server (Optional - for remote inference)

```bash
# Using backend's virtual environment
source backend/env/bin/activate

# Run AI server
python ai-inference/server.py
```

### 3. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Upload image
curl -X POST http://localhost:8000/api/images/upload \
  -F "file=@data/prescriptions/pr-2.png"

# Extract prescription (replace IMAGE_ID)
curl -X POST "http://localhost:8000/api/extract-prescription/IMAGE_ID"
```

## API Endpoints

### Images
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/images/upload` | Upload prescription image |
| POST | `/api/images/capture?url=...` | Capture from IP Webcam |
| GET | `/api/images` | List all images |
| GET | `/api/images/{id}` | Get image details |
| DELETE | `/api/images/{id}` | Delete image |

### Patients
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/patients` | Create patient |
| GET | `/api/patients` | List all patients |
| GET | `/api/patients/{id}` | Get patient details |
| PATCH | `/api/patients/{id}` | Update patient |
| DELETE | `/api/patients/{id}` | Delete patient |

### Prescriptions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/extract-prescription/{image_id}` | Extract using AI |
| GET | `/api/prescriptions/{id}` | Get prescription |
| GET | `/api/patients/{id}/prescriptions` | Patient's prescriptions |

### EHR
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ehr` | Create EHR record |
| GET | `/api/patients/{id}/ehr` | Get patient's EHR |

## Features

- **Automatic duplicate detection**: Uses SHA256 hash to detect duplicate images at upload
- **AI-powered extraction**: Uses MLX-VLM (Qwen3.5-9B) to extract structured data
- **Auto patient creation**: Extracts patient info from prescription and creates records
- **SQLite database**: Lightweight, perfect for Raspberry Pi
- **IP Webcam support**: Capture images directly from mobile phone camera

## Database Schema

```sql
-- Images (with SHA256 hash for duplicate detection)
images(id, filename, filepath, file_hash, format, source, created_at)

-- Patients (auto-created from prescriptions)
patients(id, name, age, gender, phone, created_at)

-- Prescriptions (linked to patient & image)
prescriptions(id, patient_id, image_id, extracted_text, diagnosis, outpatient_no, medicines, dosage, instructions, diagnosed_by, extracted_at)

-- EHR Records
ehr_records(id, patient_id, prescription_id, record_type, data, created_at)
```

## Raspberry Pi Connection

**Hostname**: `dharun-rasbpi`

**For macOS**:
```bash
ssh dharunmr@dharun-rasbpi.local
```

**For Windows WSL**:
```bash
# Get IP first
hostname -I
# Then connect
ssh dharunmr@<IP_ADDRESS>
```

## Development

See [AGENTS.md](./AGENTS.md) for coding guidelines and standards.

## License

MIT