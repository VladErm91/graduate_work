import logging
from datetime import timedelta
from typing import List

from aiohttp import ClientSession
from fastapi import UploadFile
from miniopy_async import Minio
from models.filedb import FileDbModel
from shortuuid import uuid as shortuuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

logger = logging.getLogger(__name__)


class FileRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def add(self, file: FileDbModel):
        self.db_session.add(file)
        await self.db_session.commit()
        await self.db_session.refresh(file)
        return file

    async def get_by_short_name(self, short_name: str) -> FileDbModel:
        result = await self.db_session.execute(
            select(FileDbModel).where(FileDbModel.short_name == short_name)
        )
        return result.scalar_one_or_none()

    async def delete(self, file: FileDbModel):
        await self.db_session.delete(file)
        await self.db_session.commit()

    async def list_all(self) -> List[FileDbModel]:
        result = await self.db_session.execute(select(FileDbModel))
        return result.scalars().all()


class FileFactory:
    @staticmethod
    def create(file: UploadFile, path: str, file_size: int) -> FileDbModel:
        short_name = shortuuid()
        return FileDbModel(
            path_in_storage=path,
            filename=file.filename,
            short_name=short_name,
            size=file_size,
            file_type=file.content_type,
        )


class MinioAdapter:
    def __init__(self, minio: Minio):
        self.client = minio

    async def upload_file(
        self, bucket_name: str, path: str, file: UploadFile, file_size: int
    ):
        await self.client.put_object(
            bucket_name=bucket_name,
            object_name=path,
            data=file.file,
            length=file_size,
            part_size=10 * 1024 * 1024,
        )

    async def download_file(self, bucket_name: str, path: str) -> ClientSession:
        async with ClientSession() as session:
            return await self.client.get_object(bucket_name, path, session=session)

    async def delete_file(self, bucket_name: str, path: str):
        await self.client.remove_object(bucket_name, path)

    async def generate_presigned_url(
        self, bucket_name: str, path: str, expires: timedelta
    ):
        return await self.client.presigned_get_object(
            bucket_name, path, expires=expires
        )
