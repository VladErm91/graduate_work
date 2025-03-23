# flask_kafka_app/app/schemas/event.py
from pydantic import BaseModel


class Event(BaseModel):
    user_id: str
    event_type: str
    timestamp: str
    fingerprint: str
    element: str = None
    page_url: str = None
    id_film: str = None
    film: str = None
    original_quality: int = None
    updated_quality: int = None
    filter: str = None
    time: int = None
