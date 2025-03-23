from core.config import settings
from miniopy_async import Minio

minio: Minio = None


def get_minio() -> Minio:
    return minio


def set_minio_conn(client: Minio) -> None:
    global minio
    minio = client


def close_minio_conn() -> None:
    global minio
    minio = None


async def create_bucket(bucket_name: str) -> None:
    client = get_minio()
    if not await client.bucket_exists(bucket_name):
        await client.make_bucket(bucket_name)


def start_minio_client():
    minio_client = Minio(
        endpoint=settings.minio_host,
        access_key=settings.minio_root_user,
        secret_key=settings.minio_root_password,
        secure=False,
    )
    return set_minio_conn(minio_client)
