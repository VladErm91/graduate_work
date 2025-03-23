import random
from typing import List
from unittest.mock import AsyncMock

import pytest
from faker import Faker
from fastapi import UploadFile
from models.filedb import FileDbModel
from services.files import FileRepository, FileService, MinioAdapter
from starlette.responses import StreamingResponse

fake = Faker()

mime_types = ["image/jpeg", "audio/mp3", "video/mp4"]


@pytest.mark.asyncio
async def test_save_file():
    mock_uploadfile = AsyncMock(spec=UploadFile)
    mock_repo = AsyncMock(spec=FileRepository)
    mock_storage_minio = AsyncMock(spec=MinioAdapter)
    file_type = random.choice(mime_types)
    path_in_storage = "test/test"
    mock_uploadfile.filename = fake.file_name(
        category=None, extension=file_type.split("/")[-1]
    )
    mock_uploadfile.content_type = file_type
    mock_uploadfile.size = fake.random_number(digits=5)
    file_service = FileService(
        file_repository=mock_repo, minio_adapter=mock_storage_minio
    )
    await file_service.save(file=mock_uploadfile, path=path_in_storage)
    mock_storage_minio.upload_file.assert_called_once()
    mock_repo.add.assert_called_once()


@pytest.mark.asyncio
async def test_get_file_data():
    mock_repo = AsyncMock(spec=FileRepository)
    mock_storage_minio = AsyncMock(spec=MinioAdapter)
    mock_file_db_modele = AsyncMock(spec=FileDbModel)
    mock_file_db_modele.short_name = "test_short_name"
    mock_repo.get_by_short_name.return_value = mock_file_db_modele
    file_service = FileService(
        file_repository=mock_repo, minio_adapter=mock_storage_minio
    )
    result = await file_service.get_file_data("test_short_name")
    assert isinstance(result, FileDbModel)
    assert result.short_name == "test_short_name"


@pytest.mark.asyncio
async def test_get_file():
    mock_repo = AsyncMock(spec=FileRepository)
    mock_storage_minio = AsyncMock(spec=MinioAdapter)
    path_in_storage = "test/test"
    file_type = random.choice(mime_types)
    filename = fake.file_name(extension=file_type.split("/")[-1])
    file_service = FileService(
        file_repository=mock_repo, minio_adapter=mock_storage_minio
    )
    test_data = b"Data1 Data2 Data3"
    mock_storage_minio.download_file.return_value = StreamingResponse(iter([test_data]))
    result = await file_service.get_file(path=path_in_storage, filename=filename)
    mock_storage_minio.download_file.assert_called_once()
    assert isinstance(result, StreamingResponse)


@pytest.mark.asyncio
async def test_list_files():
    mock_repo = AsyncMock(spec=FileRepository)
    mock_storage_minio = AsyncMock(spec=MinioAdapter)
    mock_file_db_modele = AsyncMock(spec=FileDbModel)
    mock_file_db_modele2 = AsyncMock(spec=FileDbModel)
    mock_file_db_modele3 = AsyncMock(spec=FileDbModel)
    mock_repo.list_all.return_value = [
        mock_file_db_modele,
        mock_file_db_modele2,
        mock_file_db_modele3,
    ]
    file_service = FileService(
        file_repository=mock_repo, minio_adapter=mock_storage_minio
    )
    result = await file_service.list_files()
    mock_repo.list_all.assert_called_once()
    assert isinstance(result, List)


@pytest.mark.asyncio
async def test_delete_file():
    mock_repo = AsyncMock(spec=FileRepository)
    mock_storage_minio = AsyncMock(spec=MinioAdapter)
    mock_file_db_modele = AsyncMock(spec=FileDbModel)
    mock_file_db_modele.short_name = "test_short_name"
    mock_file_db_modele.path_in_storage = "test/test"
    mock_file_db_modele.short_name = random.choice(mime_types)
    mock_repo.get_by_short_name.return_value = mock_file_db_modele
    short_name = "test_short_name"
    file_service = FileService(
        file_repository=mock_repo, minio_adapter=mock_storage_minio
    )
    await file_service.delete_file(short_name)
    mock_storage_minio.delete_file.assert_called_once()
    mock_repo.delete.assert_called_once()


@pytest.mark.asyncio
async def test_generate_presigned_url():
    mock_repo = AsyncMock(spec=FileRepository)
    mock_storage_minio = AsyncMock(spec=MinioAdapter)
    mock_file_db_modele = AsyncMock(spec=FileDbModel)
    mock_file_db_modele.short_name = "test_short_name"
    mock_file_db_modele.path_in_storage = "test_path"
    mock_storage_minio.generate_presigned_url.return_value = "test_path"
    mock_repo.get_by_short_name.return_value = mock_file_db_modele
    short_name = "test_short_name"
    file_service = FileService(
        file_repository=mock_repo, minio_adapter=mock_storage_minio
    )
    result = await file_service.generate_presigned_url(short_name)
    assert result == "test_path"
    mock_storage_minio.generate_presigned_url.assert_called_once()
