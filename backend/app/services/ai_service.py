import subprocess
import json
import os
from typing import Optional

from app.core.config import settings
from app.models import schema


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


async def extract_prescription(
    image_path: str,
    patient_id: Optional[str] = None,
) -> dict:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    cmd = [
        "mlx_vlm.generate",
        "--model",
        settings.ai_model,
        "--prompt",
        PROMPT,
        "--image",
        image_path,
        "--max-tokens",
        str(settings.ai_max_tokens),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=settings.ai_timeout,
            env={
                **os.environ,
                "PATH": f"/Users/dharunmr/mediscan-iot/backend/env/bin:{os.environ.get('PATH', '')}",
            },
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr or "Command failed",
            }

        raw_output = result.stdout.strip()

        try:
            if "```json" in raw_output:
                json_str = raw_output.split("```json")[1].split("```")[0]
            elif "```" in raw_output:
                json_str = raw_output.split("```")[1].split("```")[0]
            else:
                json_str = raw_output

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

            return {
                "success": True,
                "patient_name": patient_name,
                "patient_age": patient_age,
                "patient_gender": patient_gender,
                "patient_phone": patient_phone,
                "outpatient_no": outpatient_no,
                "diagnosis": diagnosis,
                "date": date,
                "doctor": doctor,
                "medicines": medicines_json,
                "dosage": dosage,
                "instructions": instructions,
                "raw_response": raw_output,
            }

        except json.JSONDecodeError:
            return {
                "success": True,
                "extracted_text": raw_output,
                "patient_name": "",
                "patient_age": None,
                "patient_gender": "",
                "patient_phone": "",
                "outpatient_no": "",
                "diagnosis": "",
                "date": "",
                "doctor": "",
                "medicines": "[]",
                "dosage": "",
                "instructions": "",
                "raw_response": raw_output,
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"AI extraction timed out after {settings.ai_timeout}s",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def save_extracted_prescription(
    image_id: str,
    patient_id: Optional[str],
    extraction_result: dict,
) -> schema.PrescriptionResponse:
    from app.services import database

    if not extraction_result.get("success"):
        raise Exception(f"Extraction failed: {extraction_result.get('error')}")

    existing = await database.get_prescription_by_image(image_id)
    if existing:
        return existing

    patient_name = extraction_result.get("patient_name")
    patient_age = extraction_result.get("patient_age")
    patient_gender = extraction_result.get("patient_gender")
    patient_phone = extraction_result.get("patient_phone")

    final_patient_id = patient_id

    if patient_name and not patient_id:
        existing_patients = await database.get_all_patients(limit=1000, offset=0)
        matched_patient = None

        for p in existing_patients:
            if p.name.lower().strip() == patient_name.lower().strip():
                matched_patient = p
                break

        if matched_patient:
            final_patient_id = matched_patient.id
        else:
            if patient_gender:
                if patient_gender.lower() in ["male", "female", "other"]:
                    patient_gender = patient_gender.lower()
                else:
                    patient_gender = None

            new_patient = schema.PatientCreate(
                name=patient_name,
                age=patient_age,
                gender=patient_gender,
                phone=patient_phone or None,
            )
            created_patient = await database.create_patient(new_patient)
            final_patient_id = created_patient.id

    prescription = schema.PrescriptionCreate(
        patient_id=final_patient_id,
        image_id=image_id,
        extracted_text=extraction_result.get("extracted_text", ""),
        diagnosis=extraction_result.get("diagnosis"),
        outpatient_no=extraction_result.get("outpatient_no"),
        medicines=extraction_result.get("medicines"),
        dosage=extraction_result.get("dosage"),
        instructions=extraction_result.get("instructions"),
        diagnosed_by=extraction_result.get("doctor"),
    )

    return await database.create_prescription(prescription)
