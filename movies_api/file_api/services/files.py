import logging
import urllib
from datetime import timedelta
from functools import lru_cache
from typing import List

from core.config import settings
from db.db import get_db_session
from db.minio import get_minio
from fastapi import Depends, HTTPException, UploadFile
from miniopy_async import Minio
from models.filedb import FileDbModel
from services.basic import FileFactory, FileRepository, MinioAdapter
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

logger = logging.getLogger(__name__)


class FileService:
    def __init__(self, file_repository: FileRepository, minio_adapter: MinioAdapter):
        self.file_repository = file_repository
        self.minio_adapter = minio_adapter

    async def save(self, file: UploadFile, path: str) -> FileDbModel:
        try:
            file_content = await file.read()
            file_size = len(file_content)
            await file.seek(0)

            # Загружаем файл в MinIO через адаптер
            await self.minio_adapter.upload_file(
                settings.bucket_name, path, file, file_size
            )

            # Создаем модель файла через фабрику
            new_file = FileFactory.create(file, path, file_size)

            # Сохраняем файл через репозиторий
            saved_file = await self.file_repository.add(new_file)

            logger.info(
                f"File {file.filename} uploaded successfully with short_name {new_file.short_name}."
            )
            return saved_file
        except Exception as error:
            logger.error(f"Failed to save file {file.filename}: {error}")
            raise HTTPException(
                status_code=500, detail="Failed to upload and save file."
            )

    async def get_file_data(self, short_name: str) -> FileDbModel:
        try:
            file_data = await self.file_repository.get_by_short_name(short_name)
            if not file_data:
                raise HTTPException(status_code=404, detail="File not found")
            logger.info(
                f"File data retrieved successfully for short_name {short_name}."
            )
            return file_data
        except Exception as error:
            logger.error(f"Failed to retrieve file data for {short_name}: {error}")
            raise HTTPException(status_code=500, detail="Failed to retrieve file data.")

    async def get_file(self, path: str, filename: str) -> StreamingResponse:
        try:
            result = await self.minio_adapter.download_file(settings.bucket_name, path)

            async def file_stream():
                async for chunk in result.content.iter_chunked(32 * 1024):
                    yield chunk

            encoded_filename = urllib.parse.quote(filename)
            return StreamingResponse(
                file_stream(),
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
                },
            )
        except Exception as error:
            logger.error(f"Failed to download file {filename}: {error}")
            raise HTTPException(status_code=500, detail="Failed to download file.")

    async def list_files(self) -> List[FileDbModel]:
        try:
            files = await self.file_repository.list_all()
            logger.info(f"Retrieved list of {len(files)} files.")
            return files
        except Exception as error:
            logger.error(f"Failed to list files: {error}")
            raise HTTPException(status_code=500, detail="Failed to list files.")

    async def delete_file(self, short_name: str):
        try:
            file_data = await self.get_file_data(short_name)
            if not file_data:
                raise HTTPException(status_code=404, detail="File not found")

            await self.minio_adapter.delete_file(
                settings.bucket_name, file_data.path_in_storage
            )
            await self.file_repository.delete(file_data)

            logger.info(f"File record for {short_name} deleted from database.")
        except Exception as error:
            logger.error(f"Failed to delete file {short_name}: {error}")
            raise HTTPException(status_code=500, detail="Failed to delete file.")

    async def generate_presigned_url(
        self, short_name: str, expires=timedelta(days=1)
    ) -> str:
        try:
            file_data = await self.get_file_data(short_name)
            if not file_data:
                raise HTTPException(status_code=404, detail="File not found")

            presigned_url = await self.minio_adapter.generate_presigned_url(
                settings.bucket_name, file_data.path_in_storage, expires=expires
            )

            logger.info(f"Presigned URL generated for file {file_data.filename}.")
            return presigned_url
        except Exception as error:
            logger.error(f"Failed to generate presigned URL for {short_name}: {error}")
            raise HTTPException(
                status_code=500, detail="Failed to generate presigned URL."
            )


@lru_cache()
def get_file_service(
    minio: Minio = Depends(get_minio),
    db_session: AsyncSession = Depends(get_db_session),
) -> FileService:
    file_repository = FileRepository(db_session)
    minio_adapter = MinioAdapter(minio)
    return FileService(file_repository, minio_adapter)
