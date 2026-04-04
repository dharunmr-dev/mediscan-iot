import os

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, status
from fastapi.responses import FileResponse

from app.models import schema
from app.services import image_service, database, ai_service

router = APIRouter(prefix="/api")


@router.post(
    "/images/upload",
    response_model=schema.ImageWithPrescriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_image(file: UploadFile = File(...)):
    try:
        result = await image_service.save_uploaded_image(
            file, schema.ImageSource.UPLOAD
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/images/capture",
    response_model=schema.ImageWithPrescriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def capture_image(url: str = Query(..., description="IP Webcam stream URL")):
    try:
        result = await image_service.capture_from_url(url, "captured.jpg")
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/images", response_model=list[schema.ImageResponse])
async def list_images(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    return await image_service.get_all_images(limit, offset)


@router.get("/images/{image_id}", response_model=schema.ImageResponse)
async def get_image(image_id: str):
    image = await image_service.get_image_by_id(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )
    return image


@router.get("/images/{image_id}/file")
async def download_image(image_id: str):
    image = await image_service.get_image_by_id(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )
    if not os.path.exists(image.filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image file not found"
        )
    return FileResponse(image.filepath, media_type=f"image/{image.format}")


@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(image_id: str):
    deleted = await image_service.delete_image_by_id(image_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )
    return None


@router.post(
    "/patients",
    response_model=schema.PatientResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_patient(patient: schema.PatientCreate):
    return await database.create_patient(patient)


@router.get("/patients", response_model=list[schema.PatientResponse])
async def list_patients(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    return await database.get_all_patients(limit, offset)


@router.get("/patients/{patient_id}", response_model=schema.PatientResponse)
async def get_patient(patient_id: str):
    patient = await database.get_patient(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found"
        )
    return patient


@router.patch("/patients/{patient_id}", response_model=schema.PatientResponse)
async def update_patient(patient_id: str, patient: schema.PatientUpdate):
    updated = await database.update_patient(patient_id, patient)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found"
        )
    return updated


@router.delete("/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(patient_id: str):
    deleted = await database.delete_patient(patient_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found"
        )
    return None


@router.post(
    "/prescriptions",
    response_model=schema.PrescriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_prescription(prescription: schema.PrescriptionCreate):
    return await database.create_prescription(prescription)


@router.get(
    "/prescriptions/{prescription_id}", response_model=schema.PrescriptionResponse
)
async def get_prescription(prescription_id: str):
    prescription = await database.get_prescription(prescription_id)
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found"
        )
    return prescription


@router.get(
    "/patients/{patient_id}/prescriptions",
    response_model=list[schema.PrescriptionResponse],
)
async def get_patient_prescriptions(patient_id: str):
    return await database.get_prescriptions_by_patient(patient_id)


@router.post(
    "/ehr", response_model=schema.EHRRecordResponse, status_code=status.HTTP_201_CREATED
)
async def create_ehr_record(record: schema.EHRRecordCreate):
    return await database.create_ehr_record(record)


@router.get("/patients/{patient_id}/ehr", response_model=list[schema.EHRRecordResponse])
async def get_patient_ehr(patient_id: str):
    return await database.get_ehr_records_by_patient(patient_id)


@router.post(
    "/extract-prescription/{image_id}",
    response_model=schema.PrescriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def extract_prescription(
    image_id: str,
    patient_id: str | None = Query(
        None, description="Optional patient ID to associate"
    ),
):
    try:
        image = await image_service.get_image_by_id(image_id)
        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
            )

        existing_prescription = await database.get_prescription_by_image(image_id)
        if existing_prescription:
            return existing_prescription

        extraction_result = await ai_service.extract_prescription(
            image_path=image.filepath,
            patient_id=patient_id,
        )

        prescription = await ai_service.save_extracted_prescription(
            image_id=image_id,
            patient_id=patient_id,
            extraction_result=extraction_result,
        )

        return prescription
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
