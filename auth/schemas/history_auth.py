from datetime import datetime
from uuid import UUID

import orjson
from pydantic import BaseModel


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


class HistoryAuthDBModel(BaseModel):
    id: UUID
    success: bool
    user_device_type: str
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True
        json_loads = orjson.loads
        json_dumps = orjson_dumps
