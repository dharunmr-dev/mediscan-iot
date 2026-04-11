from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class ImageSource(str, Enum):
    IP_WEBCAM = "ip_webcam"
    UPLOAD = "upload"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class RecordType(str, Enum):
    DIAGNOSIS = "diagnosis"
    PRESCRIPTION = "prescription"
    LAB_REPORT = "lab_report"


class ImageCreate(BaseModel):
    filename: str
    filepath: str
    file_hash: str
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    source: ImageSource = ImageSource.UPLOAD


class ImageResponse(BaseModel):
    id: str
    filename: str
    filepath: str
    file_hash: str
    width: Optional[int]
    height: Optional[int]
    format: Optional[str]
    source: ImageSource
    captured_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class PrescriptionCreate(BaseModel):
    patient_id: Optional[str] = None
    image_id: Optional[str] = None
    extracted_text: Optional[str] = None
    diagnosis: Optional[str] = None
    outpatient_no: Optional[str] = None
    medicines: Optional[str] = None
    dosage: Optional[str] = None
    instructions: Optional[str] = None
    diagnosed_by: Optional[str] = None


class PrescriptionResponse(BaseModel):
    id: str
    patient_id: Optional[str]
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    image_id: Optional[str]
    extracted_text: Optional[str]
    diagnosis: Optional[str]
    outpatient_no: Optional[str]
    medicines: Optional[str]
    dosage: Optional[str]
    instructions: Optional[str]
    diagnosed_by: Optional[str]
    extracted_at: datetime

    model_config = {"from_attributes": True}


class ImageWithPrescriptionResponse(BaseModel):
    id: str
    filename: str
    filepath: str
    file_hash: str
    width: Optional[int]
    height: Optional[int]
    format: Optional[str]
    source: ImageSource
    captured_at: Optional[datetime]
    created_at: datetime
    is_duplicate: bool = False
    prescription: Optional[PrescriptionResponse] = None

    model_config = {"from_attributes": True}


class PatientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[Gender] = None
    phone: Optional[str] = Field(None, max_length=20)


class PatientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[Gender] = None
    phone: Optional[str] = Field(None, max_length=20)


class PatientResponse(BaseModel):
    id: str
    name: str
    age: Optional[int]
    gender: Optional[Gender]
    phone: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class EHRRecordCreate(BaseModel):
    patient_id: str
    prescription_id: Optional[str] = None
    record_type: RecordType
    data: Optional[dict] = None


class EHRRecordResponse(BaseModel):
    id: str
    patient_id: str
    prescription_id: Optional[str]
    record_type: RecordType
    data: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}
