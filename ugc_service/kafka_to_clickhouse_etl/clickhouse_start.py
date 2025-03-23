# ugc_sprint_1/etl/clickhouse_start.py
import logging

import backoff
import clickhouse_connect
from clickhouse_connect.driver.exceptions import InterfaceError, OperationalError
from configs.settings import ClickhouseSettings

logger = logging.getLogger("etl")


@backoff.on_exception(
    backoff.expo,
    (OperationalError, InterfaceError),
    max_tries=15,
    max_time=20,
)
def clickhouse_start(settings: ClickhouseSettings):
    logger.info("Началась процедура запуска clickhouse")
    try:
        with clickhouse_connect.get_client(
            host=settings.host,
            username=settings.user,
            password=settings.password,
            port=settings.port,
        ) as client:
            create_db_query = f"CREATE DATABASE IF NOT EXISTS {settings.database} ON CLUSTER company_cluster"
            result = client.command(create_db_query)
            logger.info(f"Create DB result: {result}")

            create_table_query = (
                f"CREATE TABLE IF NOT EXISTS {settings.database}.{settings.table} ON CLUSTER company_cluster "
                "(event_type String, timestamp DateTime64, user_id UUID NULL, fingerprint String, element String NULL, "
                "page_url String NULL, time Int NULL, id_film UUID NULL, film String NULL, original_quality Int NULL, "
                "updated_quality Int NULL, filter String NULL) ENGINE=MergeTree() ORDER BY timestamp"
            )
            result = client.command(create_table_query)
            logger.info(f"Создание таблицы: {result}")
    except Exception as e:
        logger.exception(f"Ошибка при проведении процедуры запуска clickhouse: {e}")
