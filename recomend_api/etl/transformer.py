# ugc_sprint_1/etl/transformer.py
import logging
from typing import Any

from models.event import EventMessage
from pydantic import ValidationError

logger = logging.getLogger("etl")


def transform_event_data(event_data: dict[str, Any]) -> EventMessage:
    try:
        logger.info(f"Transforming event data: {event_data}")
        transformed_event = EventMessage(**event_data)
    except ValidationError as E:
        logger.exception(f"Ошибка трасформации данных: " f"{E.errors()}.")
        raise ValueError(f"Invalid event data: {E}") from None
    else:
        return transformed_event
