from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from models.filedb import FileDBResponse
from services.files import FileService, get_file_service
from starlette.responses import StreamingResponse

router = APIRouter()


@router.post(
    "/upload/",
    response_model=FileDBResponse,
    summary="Upload a file",
    description="Uploads a file to the MinIO storage and saves the file metadata to the database.",
    responses={
        200: {
            "description": "File uploaded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "uuid-string",
                        "path_in_storage": "path/to/file",
                        "filename": "example.txt",
                        "size": 12345,
                        "file_type": "text/plain",
                        "short_name": "short-uuid",
                        "created": "2024-09-11T12:34:56",
                    }
                }
            },
        },
        500: {"description": "Internal server error"},
    },
)
async def upload_file(
    file: UploadFile,
    path: str = Query(
        ..., description="The destination path in storage where the file will be saved."
    ),
    file_service: FileService = Depends(get_file_service),
):
    """
    Uploads a file to MinIO and saves the file metadata in the database. The uploaded file can be retrieved
    later using the file's `short_name`.
    """
    try:
        file_data = await file_service.save(file, path)
        return FileDBResponse(
            id=file_data.id,
            path_in_storage=file_data.path_in_storage,
            filename=file_data.filename,
            size=file_data.size,
            file_type=file_data.file_type,
            short_name=file_data.short_name,
            created=file_data.created,
        )
    except Exception as error:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(error)
        )


@router.get(
    "/download_stream/{short_name}",
    response_class=StreamingResponse,
    summary="Download a file",
    description="Streams a file for download using the file's short name.",
    responses={
        200: {"description": "File streamed successfully"},
        404: {"description": "File not found"},
        500: {"description": "Internal server error"},
    },
)
async def download_file(
    short_name: str, file_service: FileService = Depends(get_file_service)
) -> StreamingResponse:
    """
    Retrieves a file from storage by its `short_name` and streams it to the client.
    """
    try:
        file_data = await file_service.get_file_data(short_name)
        return await file_service.get_file(
            file_data.path_in_storage, file_data.filename
        )
    except Exception as error:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(error)
        )


@router.get(
    "/list",
    response_model=List[FileDBResponse],
    summary="List all files",
    description="Fetches a list of all files stored in the database.",
    responses={
        200: {
            "description": "List of files",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "uuid-string",
                            "path_in_storage": "path/to/file",
                            "filename": "example.txt",
                            "size": 12345,
                            "file_type": "text/plain",
                            "short_name": "short-uuid",
                            "created": "2024-09-11T12:34:56",
                        }
                    ]
                }
            },
        },
        500: {"description": "Internal server error"},
    },
)
async def list_files(file_service: FileService = Depends(get_file_service)):
    """
    Returns a list of all files in the database with their metadata.
    """
    try:
        files = await file_service.list_files()
        return files
    except Exception as error:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(error)
        )


@router.delete(
    "/delete/{short_name}",
    summary="Delete a file",
    description="Deletes a file from the storage and removes its record from the database.",
    responses={
        200: {"description": "File deleted successfully"},
        404: {"description": "File not found"},
        500: {"description": "Internal server error"},
    },
)
async def delete_file(
    short_name: str, file_service: FileService = Depends(get_file_service)
):
    """
    Deletes a file by its `short_name` both from MinIO and the database.
    """
    try:
        await file_service.delete_file(short_name)
        return {"message": "File deleted successfully"}
    except Exception as error:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(error)
        )


@router.get(
    "/presigned_url/{short_name}",
    summary="Get a pre-signed URL for a file",
    description="Generates a pre-signed URL for downloading a file directly from MinIO without authentication.",
    responses={
        200: {"description": "Pre-signed URL generated successfully"},
        404: {"description": "File not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_presigned_url(
    short_name: str, file_service: FileService = Depends(get_file_service)
):
    """
    Provides a pre-signed URL for file download, allowing temporary access to the file without requiring authentication.
    """
    try:
        presigned_url = await file_service.generate_presigned_url(short_name)
        return {"url": presigned_url}
    except Exception as error:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(error)
        )
