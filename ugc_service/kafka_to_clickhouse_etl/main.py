# ugc_sprint_1/etl/main.py
import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from clickhouse_start import clickhouse_start
from configs.logger import setup_logger
from configs.settings import settings
from extractor import KafkaExtractor
from loader import ClickhouseLoader
from transformer import transform_event_data

logger = logging.getLogger("etl")


async def _get_batch(loader, batch):
    """
    Asynchronous function for loading a batch of data to ClickHouse

    Arguments:
        loader {ClickhouseLoader}: ClickhouseLoader instance
        batch {list[dict]}: list of transformed data
    """
    try:
        await loader.load_batch(batch)
    except Exception as e:
        logger.exception(f"Сбой загрузки порции данных: {e}")


async def main():
    try:
        logger.info("Запуск ETL процесса")
        loader = ClickhouseLoader(settings.clsettings)
        transformer = transform_event_data
        extractor = KafkaExtractor(settings.kafkasettings)

        async with extractor:
            batch = []
            async for values in extractor.extract():
                logger.info(
                    f"Сообщение длинны {len(values)} получено: {values}"
                )  # Для отладки
                transformed_values = transformer(values)
                batch.append(transformed_values)
                if len(batch) >= settings.batch_size:
                    await _get_batch(loader, batch)
                    extractor.commit()
                    batch.clear()

            if batch:
                await _get_batch(loader, batch)

        logger.info("ETL процес завершен")
    except Exception:
        logger.exception("Ошибка при выполенинии функции main")
        raise


async def run_scheduler():
    clickhouse_start(settings.clsettings)
    setup_logger()
    ioscheduler = AsyncIOScheduler()
    ioscheduler.add_job(main, "interval", seconds=settings.run_interval_seconds)
    logger.info("Scheduler пуск")
    ioscheduler.start()

    try:
        # Это позволяет сохранить основной поток активным, в то время как выполняются задачи.
        while True:
            await asyncio.sleep(4000)  # Лучше использовать await asyncio.sleep()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler завершил работу с ошибкой")
        ioscheduler.shutdown(wait=False)
        logger.info("Scheduler завершил работу")


if __name__ == "__main__":
    asyncio.run(run_scheduler())
