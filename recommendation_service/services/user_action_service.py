# recommendation_service/services/user_action_service.py

from core.kafka import producer
import json


class UserActionService:
    @staticmethod
    async def log_watch_event(user_id: str, movie_id: str):
        event = {"user_id": user_id, "movie_id": movie_id}
        producer.produce("watch_events", key=str(user_id), value=json.dumps(event))
        producer.flush()
