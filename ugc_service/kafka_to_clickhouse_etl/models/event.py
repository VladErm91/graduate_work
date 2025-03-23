# ugc_sprint_1/etl/models/event.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EventMessage(BaseModel):
    event_type: str
    timestamp: datetime
    user_id: UUID | None = None
    fingerprint: str
    # специальные
    element: str | None = None
    page_url: str | None = None
    time: int | None = None
    id_film: UUID | None = None
    film: str | None = None
    original_quality: int | None = None
    updated_quality: int | None = None
    filter: str | None = None
