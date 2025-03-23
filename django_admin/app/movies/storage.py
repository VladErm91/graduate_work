import os
from uuid import uuid4

import requests
from config.components.base import FILE_API_HOST, FILE_API_PORT
from django.core.files.storage import Storage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.deconstruct import deconstructible

FileAPI_url = f"http://{FILE_API_HOST}:{FILE_API_PORT}/api/v1/files"
FileAPI_download_url = f"http://{FILE_API_HOST}:{FILE_API_PORT}/api/v1/files"


def get_uniqe_filename(basic_name):
    return f"{uuid4()}-{os.path.basename(basic_name)}"


@deconstructible
class CustomStorage(Storage):
    def _save(self, name, content: InMemoryUploadedFile):
        # Генерация уникального имени файла
        r = requests.post(
            f"{FileAPI_url}/upload/?path={get_uniqe_filename(name)}",
            files={"file": (content.name, content, content.content_type)},
        )
        response_data = r.json()
        return response_data.get("short_name")

    def url(self, name):
        return f"{FileAPI_download_url}/download_stream/{name}"

    def exists(self, name):
        return False
