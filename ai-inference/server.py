import os
import subprocess
from fastapi import FastAPI
from pydantic import BaseModel


class ExtractRequest(BaseModel):
    image_path: str
    prompt: str


class ExtractResponse(BaseModel):
    success: bool
    raw_response: str | None = None
    error: str | None = None


MODEL_NAME = os.environ.get("AI_MODEL", "mlx-community/Qwen3.5-9B-MLX-4bit")
MAX_TOKENS = int(os.environ.get("AI_MAX_TOKENS", "10000"))
PORT = int(os.environ.get("AI_PORT", "8001"))

MEDIScan_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MLX_BIN_PATH = os.path.join(MEDIScan_ROOT, "backend", "env", "bin")


app = FastAPI(
    title="Mediscan AI Server",
    description="MLX-VLM CLI wrapper for prescription extraction",
    version="1.0.0",
)


@app.post("/extract", response_model=ExtractResponse)
async def extract_prescription(request: ExtractRequest):
    if not os.path.exists(request.image_path):
        return ExtractResponse(
            success=False, error=f"Image not found: {request.image_path}"
        )

    try:
        env = os.environ.copy()
        env["PATH"] = f"{MLX_BIN_PATH}:{env.get('PATH', '')}"

        result = subprocess.run(
            [
                "mlx_vlm.generate",
                "--model",
                MODEL_NAME,
                "--prompt",
                request.prompt,
                "--image",
                request.image_path,
                "--max-tokens",
                str(MAX_TOKENS),
            ],
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
        )

        if result.returncode != 0:
            return ExtractResponse(
                success=False, error=result.stderr or "MLX command failed"
            )

        raw_response = result.stdout.strip()

        return ExtractResponse(
            success=True,
            raw_response=raw_response,
        )

    except subprocess.TimeoutExpired:
        return ExtractResponse(
            success=False, error="AI extraction timed out after 300 seconds"
        )
    except Exception as e:
        return ExtractResponse(success=False, error=str(e))


@app.get("/health")
async def health():
    return {"status": "healthy", "model": MODEL_NAME, "loaded": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
