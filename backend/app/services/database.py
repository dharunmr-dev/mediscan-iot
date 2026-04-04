import aiosqlite
import json
import os
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from app.models import schema


DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "mediscan.db"
)


async def init_db() -> None:
    """Initialize database and create tables if they don't exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                width INTEGER,
                height INTEGER,
                format TEXT,
                source TEXT NOT NULL,
                captured_at TEXT,
                created_at TEXT NOT NULL
            )
        """)

        try:
            await db.execute("ALTER TABLE images ADD COLUMN file_hash TEXT")
        except:
            pass

        await db.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                phone TEXT,
                created_at TEXT NOT NULL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS prescriptions (
                id TEXT PRIMARY KEY,
                patient_id TEXT,
                image_id TEXT,
                extracted_text TEXT,
                diagnosis TEXT,
                outpatient_no TEXT,
                medicines TEXT,
                dosage TEXT,
                instructions TEXT,
                diagnosed_by TEXT,
                extracted_at TEXT NOT NULL,
                FOREIGN KEY (patient_id) REFERENCES patients(id),
                FOREIGN KEY (image_id) REFERENCES images(id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS ehr_records (
                id TEXT PRIMARY KEY,
                patient_id TEXT NOT NULL,
                prescription_id TEXT,
                record_type TEXT NOT NULL,
                data TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (patient_id) REFERENCES patients(id),
                FOREIGN KEY (prescription_id) REFERENCES prescriptions(id)
            )
        """)

        try:
            await db.execute("ALTER TABLE prescriptions ADD COLUMN diagnosis TEXT")
        except:
            pass
        try:
            await db.execute("ALTER TABLE prescriptions ADD COLUMN outpatient_no TEXT")
        except:
            pass

        await db.commit()


async def create_image(image: schema.ImageCreate) -> schema.ImageResponse:
    """Create a new image record."""
    image_id = str(uuid4())
    now = datetime.utcnow().isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO images (id, filename, filepath, file_hash, width, height, format, source, captured_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                image_id,
                image.filename,
                image.filepath,
                image.file_hash,
                image.width,
                image.height,
                image.format,
                image.source.value,
                now,
                now,
            ),
        )
        await db.commit()

    return schema.ImageResponse(
        id=image_id,
        filename=image.filename,
        filepath=image.filepath,
        file_hash=image.file_hash,
        width=image.width,
        height=image.height,
        format=image.format,
        source=image.source,
        captured_at=datetime.fromisoformat(now)
        if image.source == schema.ImageSource.IP_WEBCAM
        else None,
        created_at=datetime.fromisoformat(now),
    )


async def get_image_by_hash(file_hash: str) -> Optional[schema.ImageResponse]:
    """Get an image by file hash."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM images WHERE file_hash = ?", (file_hash,)
        ) as cursor:
            row = await cursor.fetchone()

    if not row:
        return None

    return schema.ImageResponse(
        id=row["id"],
        filename=row["filename"],
        filepath=row["filepath"],
        file_hash=row["file_hash"],
        width=row["width"],
        height=row["height"],
        format=row["format"],
        source=schema.ImageSource(row["source"]),
        captured_at=datetime.fromisoformat(row["captured_at"])
        if row["captured_at"]
        else None,
        created_at=datetime.fromisoformat(row["created_at"]),
    )


async def get_image(image_id: str) -> Optional[schema.ImageResponse]:
    """Get an image by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM images WHERE id = ?", (image_id,)
        ) as cursor:
            row = await cursor.fetchone()

    if not row:
        return None

    file_hash_val = (
        row["file_hash"] if "file_hash" in row.keys() and row["file_hash"] else ""
    )
    return schema.ImageResponse(
        id=row["id"],
        filename=row["filename"],
        filepath=row["filepath"],
        file_hash=file_hash_val,
        width=row["width"],
        height=row["height"],
        format=row["format"],
        source=schema.ImageSource(row["source"]),
        captured_at=datetime.fromisoformat(row["captured_at"])
        if row["captured_at"]
        else None,
        created_at=datetime.fromisoformat(row["created_at"]),
    )


async def get_all_images(
    limit: int = 100, offset: int = 0
) -> List[schema.ImageResponse]:
    """Get all images with pagination."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM images ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ) as cursor:
            rows = await cursor.fetchall()

    images = []
    for row in rows:
        file_hash_val = (
            row["file_hash"] if "file_hash" in row.keys() and row["file_hash"] else ""
        )
        images.append(
            schema.ImageResponse(
                id=row["id"],
                filename=row["filename"],
                filepath=row["filepath"],
                file_hash=file_hash_val,
                width=row["width"],
                height=row["height"],
                format=row["format"],
                source=schema.ImageSource(row["source"]),
                captured_at=datetime.fromisoformat(row["captured_at"])
                if row["captured_at"]
                else None,
                created_at=datetime.fromisoformat(row["created_at"]),
            )
        )
    return images


async def delete_image(image_id: str) -> bool:
    """Delete an image by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM images WHERE id = ?", (image_id,))
        await db.commit()
        return True


async def create_patient(patient: schema.PatientCreate) -> schema.PatientResponse:
    """Create a new patient."""
    patient_id = str(uuid4())
    now = datetime.utcnow().isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO patients (id, name, age, gender, phone, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id,
                patient.name,
                patient.age,
                patient.gender.value if patient.gender else None,
                patient.phone,
                now,
            ),
        )
        await db.commit()

    return schema.PatientResponse(
        id=patient_id,
        name=patient.name,
        age=patient.age,
        gender=patient.gender,
        phone=patient.phone,
        created_at=datetime.fromisoformat(now),
    )


async def get_patient(patient_id: str) -> Optional[schema.PatientResponse]:
    """Get a patient by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM patients WHERE id = ?", (patient_id,)
        ) as cursor:
            row = await cursor.fetchone()

    if not row:
        return None

    return schema.PatientResponse(
        id=row["id"],
        name=row["name"],
        age=row["age"],
        gender=schema.Gender(row["gender"]) if row["gender"] else None,
        phone=row["phone"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


async def get_all_patients(
    limit: int = 100, offset: int = 0
) -> List[schema.PatientResponse]:
    """Get all patients with pagination."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM patients ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ) as cursor:
            rows = await cursor.fetchall()

    patients = []
    for row in rows:
        patients.append(
            schema.PatientResponse(
                id=row["id"],
                name=row["name"],
                age=row["age"],
                gender=schema.Gender(row["gender"]) if row["gender"] else None,
                phone=row["phone"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
        )
    return patients


async def update_patient(
    patient_id: str, patient: schema.PatientUpdate
) -> Optional[schema.PatientResponse]:
    """Update a patient."""
    existing = await get_patient(patient_id)
    if not existing:
        return None

    updates = []
    values: list = []
    if patient.name is not None:
        updates.append("name = ?")
        values.append(patient.name)
    if patient.age is not None:
        updates.append("age = ?")
        values.append(patient.age)
    if patient.gender is not None:
        updates.append("gender = ?")
        values.append(patient.gender.value)
    if patient.phone is not None:
        updates.append("phone = ?")
        values.append(patient.phone)

    if not updates:
        return existing

    values.append(patient_id)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE patients SET {', '.join(updates)} WHERE id = ?", values
        )
        await db.commit()

    return await get_patient(patient_id)


async def delete_patient(patient_id: str) -> bool:
    """Delete a patient by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        await db.commit()
        return True


async def create_prescription(
    prescription: schema.PrescriptionCreate,
) -> schema.PrescriptionResponse:
    """Create a new prescription."""
    prescription_id = str(uuid4())
    now = datetime.utcnow().isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO prescriptions (id, patient_id, image_id, extracted_text, diagnosis, outpatient_no, medicines, dosage, instructions, diagnosed_by, extracted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                prescription_id,
                prescription.patient_id,
                prescription.image_id,
                prescription.extracted_text,
                prescription.diagnosis,
                prescription.outpatient_no,
                prescription.medicines,
                prescription.dosage,
                prescription.instructions,
                prescription.diagnosed_by,
                now,
            ),
        )
        await db.commit()

    return schema.PrescriptionResponse(
        id=prescription_id,
        patient_id=prescription.patient_id,
        image_id=prescription.image_id,
        extracted_text=prescription.extracted_text,
        diagnosis=prescription.diagnosis,
        outpatient_no=prescription.outpatient_no,
        medicines=prescription.medicines,
        dosage=prescription.dosage,
        instructions=prescription.instructions,
        diagnosed_by=prescription.diagnosed_by,
        extracted_at=datetime.fromisoformat(now),
    )


async def get_prescription(
    prescription_id: str,
) -> Optional[schema.PrescriptionResponse]:
    """Get a prescription by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM prescriptions WHERE id = ?", (prescription_id,)
        ) as cursor:
            row = await cursor.fetchone()

    if not row:
        return None

    return schema.PrescriptionResponse(
        id=row["id"],
        patient_id=row["patient_id"],
        image_id=row["image_id"],
        extracted_text=row["extracted_text"],
        diagnosis=row["diagnosis"]
        if "diagnosis" in row.keys() and row["diagnosis"]
        else None,
        outpatient_no=row["outpatient_no"]
        if "outpatient_no" in row.keys() and row["outpatient_no"]
        else None,
        medicines=row["medicines"],
        dosage=row["dosage"],
        instructions=row["instructions"],
        diagnosed_by=row["diagnosed_by"],
        extracted_at=datetime.fromisoformat(row["extracted_at"]),
    )


async def get_prescription_by_image(
    image_id: str,
) -> Optional[schema.PrescriptionResponse]:
    """Get a prescription by image_id."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM prescriptions WHERE image_id = ?", (image_id,)
        ) as cursor:
            row = await cursor.fetchone()

    if not row:
        return None

    return schema.PrescriptionResponse(
        id=row["id"],
        patient_id=row["patient_id"],
        image_id=row["image_id"],
        extracted_text=row["extracted_text"],
        diagnosis=row["diagnosis"]
        if "diagnosis" in row.keys() and row["diagnosis"]
        else None,
        outpatient_no=row["outpatient_no"]
        if "outpatient_no" in row.keys() and row["outpatient_no"]
        else None,
        medicines=row["medicines"],
        dosage=row["dosage"],
        instructions=row["instructions"],
        diagnosed_by=row["diagnosed_by"],
        extracted_at=datetime.fromisoformat(row["extracted_at"]),
    )


async def get_prescriptions_by_patient(
    patient_id: str,
) -> List[schema.PrescriptionResponse]:
    """Get all prescriptions for a patient."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM prescriptions WHERE patient_id = ? ORDER BY extracted_at DESC",
            (patient_id,),
        ) as cursor:
            rows = await cursor.fetchall()

    prescriptions = []
    for row in rows:
        prescriptions.append(
            schema.PrescriptionResponse(
                id=row["id"],
                patient_id=row["patient_id"],
                image_id=row["image_id"],
                extracted_text=row["extracted_text"],
                diagnosis=row.get("diagnosis"),
                outpatient_no=row.get("outpatient_no"),
                medicines=row["medicines"],
                dosage=row["dosage"],
                instructions=row["instructions"],
                diagnosed_by=row["diagnosed_by"],
                extracted_at=datetime.fromisoformat(row["extracted_at"]),
            )
        )
    return prescriptions


async def create_ehr_record(record: schema.EHRRecordCreate) -> schema.EHRRecordResponse:
    """Create a new EHR record."""
    record_id = str(uuid4())
    now = datetime.utcnow().isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO ehr_records (id, patient_id, prescription_id, record_type, data, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                record.patient_id,
                record.prescription_id,
                record.record_type.value,
                json.dumps(record.data) if record.data else None,
                now,
            ),
        )
        await db.commit()

    return schema.EHRRecordResponse(
        id=record_id,
        patient_id=record.patient_id,
        prescription_id=record.prescription_id,
        record_type=record.record_type,
        data=record.data,
        created_at=datetime.fromisoformat(now),
    )


async def get_ehr_records_by_patient(patient_id: str) -> List[schema.EHRRecordResponse]:
    """Get all EHR records for a patient."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM ehr_records WHERE patient_id = ? ORDER BY created_at DESC",
            (patient_id,),
        ) as cursor:
            rows = await cursor.fetchall()

    records = []
    for row in rows:
        records.append(
            schema.EHRRecordResponse(
                id=row["id"],
                patient_id=row["patient_id"],
                prescription_id=row["prescription_id"],
                record_type=schema.RecordType(row["record_type"]),
                data=json.loads(row["data"]) if row["data"] else None,
                created_at=datetime.fromisoformat(row["created_at"]),
            )
        )
    return records
