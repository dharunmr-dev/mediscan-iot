import hashlib
import os
from datetime import datetime
from typing import Optional
from uuid import uuid4

import aiofiles
from fastapi import UploadFile

from app.models import schema
from app.services import database

ALLOWED_FORMATS = {"jpeg", "jpg", "png"}
MAX_FILE_SIZE = 10 * 1024 * 1024
MIN_DIMENSION = 100
MAX_DIMENSION = 8000


def get_storage_path() -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base_dir, "data", "prescriptions")


def calculate_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


async def save_uploaded_image(
    file: UploadFile,
    source: schema.ImageSource = schema.ImageSource.UPLOAD,
) -> schema.ImageWithPrescriptionResponse:
    content_type = file.content_type or ""
    if content_type not in ALLOWED_FORMATS and not any(
        fmt in content_type.lower() for fmt in ALLOWED_FORMATS
    ):
        raise ValueError(f"Invalid file format. Allowed: {ALLOWED_FORMATS}")

    filename = file.filename or "image.jpg"
    file_ext = os.path.splitext(filename)[1].lower().lstrip(".")
    if file_ext not in ALLOWED_FORMATS:
        file_ext = "jpg" if "jpeg" in content_type.lower() else "jpg"

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise ValueError(f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB")

    file_hash = calculate_hash(content)

    existing_image = await database.get_image_by_hash(file_hash)
    if existing_image:
        prescription = await database.get_prescription_by_image(existing_image.id)
        return schema.ImageWithPrescriptionResponse(
            id=existing_image.id,
            filename=existing_image.filename,
            filepath=existing_image.filepath,
            file_hash=existing_image.file_hash,
            width=existing_image.width,
            height=existing_image.height,
            format=existing_image.format,
            source=existing_image.source,
            captured_at=existing_image.captured_at,
            created_at=existing_image.created_at,
            is_duplicate=True,
            prescription=prescription,
        )

    file_id = str(uuid4())
    now = datetime.utcnow()
    date_path = now.strftime("%Y/%m/%d")
    storage_dir = os.path.join(get_storage_path(), date_path)
    os.makedirs(storage_dir, exist_ok=True)

    filename = f"{file_id}.{file_ext}"
    filepath = os.path.join(storage_dir, filename)

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    db_image = await database.create_image(
        schema.ImageCreate(
            filename=filename,
            filepath=filepath,
            file_hash=file_hash,
            width=None,
            height=None,
            format=file_ext,
            source=source,
        )
    )

    return schema.ImageWithPrescriptionResponse(
        id=db_image.id,
        filename=db_image.filename,
        filepath=db_image.filepath,
        file_hash=db_image.file_hash,
        width=db_image.width,
        height=db_image.height,
        format=db_image.format,
        source=db_image.source,
        captured_at=db_image.captured_at,
        created_at=db_image.created_at,
        is_duplicate=False,
        prescription=None,
    )


async def capture_from_url(
    url: str, filename: str
) -> schema.ImageWithPrescriptionResponse:
    import aiohttp

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise ValueError(f"Failed to capture image from URL: {response.status}")

            content = await response.read()
            if len(content) > MAX_FILE_SIZE:
                raise ValueError(
                    f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"
                )

    file_hash = calculate_hash(content)

    existing_image = await database.get_image_by_hash(file_hash)
    if existing_image:
        prescription = await database.get_prescription_by_image(existing_image.id)
        return schema.ImageWithPrescriptionResponse(
            id=existing_image.id,
            filename=existing_image.filename,
            filepath=existing_image.filepath,
            file_hash=existing_image.file_hash,
            width=existing_image.width,
            height=existing_image.height,
            format=existing_image.format,
            source=existing_image.source,
            captured_at=existing_image.captured_at,
            created_at=existing_image.created_at,
            is_duplicate=True,
            prescription=prescription,
        )

    file_id = str(uuid4())
    now = datetime.utcnow()
    date_path = now.strftime("%Y/%m/%d")
    storage_dir = os.path.join(get_storage_path(), date_path)
    os.makedirs(storage_dir, exist_ok=True)

    content_type = response.headers.get("Content-Type", "image/jpeg")
    file_ext = "jpg"
    if "png" in content_type:
        file_ext = "png"

    filename = f"{file_id}.{file_ext}"
    filepath = os.path.join(storage_dir, filename)

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    db_image = await database.create_image(
        schema.ImageCreate(
            filename=filename,
            filepath=filepath,
            file_hash=file_hash,
            width=None,
            height=None,
            format=file_ext,
            source=schema.ImageSource.IP_WEBCAM,
        )
    )

    return schema.ImageWithPrescriptionResponse(
        id=db_image.id,
        filename=db_image.filename,
        filepath=db_image.filepath,
        file_hash=db_image.file_hash,
        width=db_image.width,
        height=db_image.height,
        format=db_image.format,
        source=db_image.source,
        captured_at=db_image.captured_at,
        created_at=db_image.created_at,
        is_duplicate=False,
        prescription=None,
    )


async def get_image_by_id(image_id: str) -> Optional[schema.ImageResponse]:
    return await database.get_image(image_id)


async def get_all_images(
    limit: int = 100, offset: int = 0
) -> list[schema.ImageResponse]:
    return await database.get_all_images(limit, offset)


async def delete_image_by_id(image_id: str) -> bool:
    image = await database.get_image(image_id)
    if not image:
        return False

    if os.path.exists(image.filepath):
        os.remove(image.filepath)

    return await database.delete_image(image_id)
