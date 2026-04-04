# Mediscan AI Server

MLX-VLM HTTP server for prescription extraction using Apple's MLX framework.

> **Note**: This server runs on MacBook M4 (or any MLX-compatible Mac) for AI inference. The Raspberry Pi backend calls this server over HTTP to extract prescription data.

## Model

**Qwen3.5-9B-MLX-4bit** (`mlx-community/Qwen3.5-9B-MLX-4bit`)

This model performs well on prescription text extraction and is optimized for Apple Silicon.

## Prerequisites

### 1. Huggingface Account

```bash
# Install huggingface-cli
brew install hf

# Login to Huggingface
hf auth login
```

[Learn more about HF CLI setup](https://huggingface.co/docs/huggingface_hub/en/guides/cli#hf-auth-login)

### 2. uv Package Manager

[Install and setup uv](https://docs.astral.sh/uv/getting-started/installation/)

### 3. Python Version

- **Required**: Python 3.11.14

## Setup

### Using Backend's Virtual Environment

The easiest way - use the backend's already configured environment:

```bash
# Activate backend's virtual environment (has mlx-vlm installed)
source ../backend/env/bin/activate
```

### Or Create Separate Environment

```bash
# Create virtual environment
uv venv --python 3.11.14 mlx-vlm

# Activate
source mlx-vlm/bin/activate

# Install mlx-vlm
uv pip install git+https://github.com/Blaizzy/mlx-vlm.git

# Install dependencies
uv pip install fastapi pydantic pydantic-settings uvicorn torch torchvision
```

## Running the Server

### Start the AI Server

```bash
# Using backend's venv
source ../backend/env/bin/activate

# Run server (default port 8001)
python ai-inference/server.py

# Or with custom port
AI_PORT=8002 python ai-inference/server.py
```

### Verify

```bash
# Health check
curl http://localhost:8001/health

# Response:
# {"status":"healthy","model":"mlx-community/Qwen3.5-9B-MLX-4bit","loaded":true}
```

## API Endpoints

### POST /extract

Extract prescription data from an image.

**Request:**
```bash
curl -X POST http://localhost:8001/extract \
  -H "Content-Type: application/json" \
  -d '{"image_path": "/path/to/prescription.jpg"}'
```

**Response:**
```json
{
  "success": true,
  "patient_name": "John Doe",
  "patient_age": 35,
  "patient_gender": "male",
  "patient_phone": "",
  "outpatient_no": "123456",
  "diagnosis": "Fever",
  "date": "2024-01-15",
  "doctor": "Dr. Smith",
  "medicines": "[{\"name\": \"Paracetamol\", \"dosage\": \"1-0-1\", \"duration\": \"5 days\"}]",
  "dosage": "1-0-1",
  "instructions": "5 days",
  "raw_response": "..."
}
```

### GET /health

Check server health and model status.

```bash
curl http://localhost:8001/health
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_MODEL` | `mlx-community/Qwen3.5-9B-MLX-4bit` | Model to use |
| `AI_MAX_TOKENS` | `10000` | Max tokens for generation |
| `AI_PORT` | `8001` | Server port |

### Changing Model

```bash
AI_MODEL=mlx-community/Qwen2.5-7B-MLX-4bit python ai-inference/server.py
```

## Testing with CLI

You can also test the model directly using the CLI:

```bash
# Activate environment
source ../backend/env/bin/activate

# Run model
mlx_vlm.generate \
  --model mlx-community/Qwen3.5-9B-MLX-4bit \
  --prompt "Extract all text from the doctor prescription and give the output in json format" \
  --image ~/mediscan-iot/data/prescriptions/pr-2.png \
  --max-tokens 10000
```

## How It Works

1. Backend receives image upload
2. Backend calculates SHA256 hash and checks for duplicates
3. If new image, backend sends to AI server at `/extract`
4. AI server loads image through MLX-VLM processor
5. Qwen3.5-9B-MLX generates JSON response with prescription data
6. Backend saves extracted data to SQLite, creates patient if needed

## Troubleshooting

### Model not loading

First run takes time to download model (~4GB). Check logs:
```bash
tail -f ai-server.log
```

### Out of memory

The model requires ~8GB of RAM. Close other applications or use smaller model.

### Port already in use

```bash
# Find process using port 8001
lsof -ti:8001 | xargs kill
```

## Project Structure

```
ai-inference/
├── server.py              # FastAPI server with MLX-VLM
├── mlx-vlm/               # Virtual environment (if separate)
└── README.md              # This file
```

## License

MIT