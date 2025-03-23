# ugc_sprint_1/flask_kafka_app/app/routes.py
import logging
from contextlib import contextmanager

from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from .kafka_producer import close_producer, create_producer
from .shemas.event import Event

bp = Blueprint("routes", __name__)


@contextmanager
def get_producer():
    producer = create_producer()
    try:
        yield producer
    finally:
        close_producer(producer)


@bp.route("/v1/track_event", methods=["POST"])
def track_event():
    """Отправка события
    ---
    parameters:
      - name: data
        in: body
        type: object
        required: true
        schema:
          id: CustomEvent
          properties:
            user_id:
              type: string
              description: Уникальный идентификатор пользователя
            event_type:
              type: string
              description: Тип пользовательского события, например, 'quality_change', 'filter_applied', 'watched_time'
            timestamp:
              type: string
              format: date-time
              description: Время события в формате ISO 8601
            fingerprint:
              type: string
              description: Уникальный отпечаток устройства
            element:
              type: string
              description: Элемент, с которым взаимодействовал пользователь (только для событий типа 'click')
            page_url:
              type: string
              description: URL страницы (только для событий типа 'click' и 'pageview')
            id_film:
              type: string
              description: Идентификатор фильма (только для событий типа 'quality_change' и 'watched_time')
            film:
              type: string
              description: Название фильма (например, "Dummy Film")
            original_quality:
              type: integer
              description: Исходное качество видео (только для событий типа 'quality_change')
            updated_quality:
              type: integer
              description: Обновлённое качество видео (только для событий типа 'quality_change')
            filter:
              type: string
              description: Применённый фильтр (только для событий типа 'filter_applied')
            time:
              type: integer
              description: Время просмотра в минутах (только для событий типа 'watched_time')
    responses:
      200:
        description: событие зафиксировано
        schema:
          id: TrackEventResponse
          properties:
            status:
              type: string
              description: Статус выполнения запроса
    """
    data = request.get_json()

    try:
        event = Event(**data)
    except ValidationError as e:
        logging.error(f"Validation error: {e}")
        return jsonify({"error": "Invalid data"}), 400

    topic = f"{event.event_type}"
    with get_producer() as producer:
        producer.send(topic, value=event.model_dump())
    logging.info(f"{event.event_type} event tracked for user_id: {event.user_id}")
    return jsonify({"status": f"{event.event_type} event tracked"})


def init_routes(app):
    app.register_blueprint(bp)
