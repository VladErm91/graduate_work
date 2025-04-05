from contextvars import ContextVar
import hashlib
from uuid import UUID
from bson import ObjectId

ctx_request_id: ContextVar[str] = ContextVar("request_id")

def convert_objectid(data):
    if isinstance(data, list):
        for item in data:
            item["_id"] = str(item["_id"])
    else:
        data["_id"] = str(data["_id"])
    return data

def hash_uid(uuid_str: str) -> str:
    """
    Хеширует UUID и обрезает до 12 байт 
    """
    uuid_bytes = UUID(uuid_str).bytes
    hashed = hashlib.sha1(uuid_bytes).digest()[:12]
    return hashed

def uuid_to_objectid(uuid_str: str) -> ObjectId:
    """
    Cоздает ObjectId
    """
    hashed = hash_uid(uuid_str)
    return ObjectId(hashed)

def hash_to_str(uuid_str: str) -> str:
    """
    Хеширует UUID и обрезает до 12 байт 
    """
    hashed = hash_uid(uuid_str)
    return str(ObjectId(hashed))