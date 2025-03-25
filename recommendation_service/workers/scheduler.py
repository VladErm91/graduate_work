import time
from workers.train_model import train_model

INTERVAL = 24 * 60 * 60  # 24 часа

while True:
    print("Запуск обновления модели...")
    train_model()
    print("Ожидание следующего запуска...")
    time.sleep(INTERVAL)
