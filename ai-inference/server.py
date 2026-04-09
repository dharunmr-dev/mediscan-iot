from contextlib import asynccontextmanager
import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mlx_vlm import generate
from mlx_vlm.utils import load_image, load


class ExtractRequest(BaseModel):
    image_path: str
    patient_id: str | None = None


class ExtractResponse(BaseModel):
    success: bool
    patient_name: str | None = None
    patient_age: int | None = None
    patient_gender: str | None = None
    patient_phone: str | None = None
    outpatient_no: str | None = None
    diagnosis: str | None = None
    date: str | None = None
    doctor: str | None = None
    medicines: str | None = None
    dosage: str | None = None
    instructions: str | None = None
    extracted_text: str | None = None
    raw_response: str | None = None
    error: str | None = None


PROMPT = """Extract structured JSON from this prescription image:

{
  "patient": {
    "name": "Patient's full name",
    "age": number,
    "gender": "male/female/other",
    "phone": "phone number if available",
    "outpatient_no": "outpatient number if available"
  },
  "prescription": {
    "date": "prescription date if available",
    "diagnosis": "diagnosis or condition",
    "medicines": [
      {"name": "medicine name", "dosage": "dosage like 1-0-1", "duration": "duration like 1 month"}
    ],
    "doctor": "doctor name"
  }
}

Return ONLY valid JSON, no markdown, no text before or after."""


MODEL_NAME = os.environ.get("AI_MODEL", "mlx-community/Qwen3.5-9B-MLX-4bit")
MAX_TOKENS = int(os.environ.get("AI_MAX_TOKENS", "10000"))
PORT = int(os.environ.get("AI_PORT", "8001"))

model = None
processor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, processor
    print(f"Loading model: {MODEL_NAME}...")
    model, processor = load(MODEL_NAME)
    print(f"Model loaded successfully!")
    print(f"Will listen on port: {PORT}")
    yield


app = FastAPI(
    title="Mediscan AI Server",
    description="MLX-VLM server for prescription extraction",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/extract", response_model=ExtractResponse)
async def extract_prescription(request: ExtractRequest):
    global model, processor

    if not os.path.exists(request.image_path):
        raise HTTPException(
            status_code=400, detail=f"Image not found: {request.image_path}"
        )

    if model is None or processor is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    try:
        image = load_image(request.image_path)

        result = generate(
            model=model,
            processor=processor,
            prompt=PROMPT,
            image=image,
            max_tokens=MAX_TOKENS,
        )

        raw_response = result.strip()

        try:
            if "```json" in raw_response:
                json_str = raw_response.split("```json")[1].split("```")[0]
            elif "```" in raw_response:
                json_str = raw_response.split("```")[1].split("```")[0]
            else:
                json_str = raw_response

            parsed = json.loads(json_str.strip())

            patient_data = parsed.get("patient", {})
            prescription_data = parsed.get("prescription", {})

            def to_string(value):
                if isinstance(value, list):
                    return ", ".join(str(v) for v in value)
                return str(value) if value else ""

            def to_int(value):
                if isinstance(value, int):
                    return value
                if isinstance(value, str):
                    try:
                        return int(value)
                    except:
                        return None
                return None

            patient_name = to_string(patient_data.get("name"))
            patient_age = to_int(patient_data.get("age"))
            patient_gender = to_string(patient_data.get("gender"))
            patient_phone = to_string(patient_data.get("phone"))
            outpatient_no = to_string(patient_data.get("outpatient_no"))

            diagnosis = to_string(prescription_data.get("diagnosis"))
            doctor = to_string(prescription_data.get("doctor"))
            date = to_string(prescription_data.get("date"))

            medicines_list = prescription_data.get("medicines", [])
            if isinstance(medicines_list, list):
                medicines_json = json.dumps(medicines_list)
            else:
                medicines_json = "[]"

            dosage_list = [
                m.get("dosage", "") for m in medicines_list if isinstance(m, dict)
            ]
            dosage = ", ".join([d for d in dosage_list if d])

            instructions_list = [
                m.get("duration", "") for m in medicines_list if isinstance(m, dict)
            ]
            instructions = ", ".join([i for i in instructions_list if i])

            return ExtractResponse(
                success=True,
                patient_name=patient_name,
                patient_age=patient_age,
                patient_gender=patient_gender,
                patient_phone=patient_phone,
                outpatient_no=outpatient_no,
                diagnosis=diagnosis,
                date=date,
                doctor=doctor,
                medicines=medicines_json,
                dosage=dosage,
                instructions=instructions,
                raw_response=raw_response,
            )

        except json.JSONDecodeError:
            return ExtractResponse(
                success=True,
                extracted_text=raw_response,
                raw_response=raw_response,
            )

    except Exception as e:
        return ExtractResponse(
            success=False,
            error=str(e),
        )


@app.get("/health")
async def health():
    return {"status": "healthy", "model": MODEL_NAME, "loaded": model is not None}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
