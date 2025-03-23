import psycopg2
import random
import uuid
from datetime import datetime, timedelta
from clickhouse_driver import Client

# Подключение к PostgreSQL
pg_conn = psycopg2.connect(
    dbname="recommendations",
    user="admin",
    password="password",
    host="localhost",
    port="5432",
)
pg_cursor = pg_conn.cursor()

# Подключение к ClickHouse
ch_client = Client(host="localhost", user="admin", password="password")

# Фейковые данные
MOVIE_TITLES = ["Интерстеллар", "Начало", "Дюна", "Аватар", "Матрица"]
GENRES = ["Фантастика", "Боевик", "Драма", "Триллер"]


# Генерация пользователей
def generate_users(n=10):
    users = []
    for _ in range(n):
        user_id = str(uuid.uuid4())
        username = f"user_{random.randint(1000, 9999)}"
        email = f"{username}@example.com"
        users.append((user_id, username, email))

    pg_cursor.executemany(
        "INSERT INTO users (id, username, email) VALUES (%s, %s, %s)", users
    )
    pg_conn.commit()
    return [u[0] for u in users]


# Генерация фильмов
def generate_movies(n=5):
    movies = []
    for _ in range(n):
        movie_id = str(uuid.uuid4())
        title = random.choice(MOVIE_TITLES)
        genre = [random.choice(GENRES)]
        release_date = datetime.now() - timedelta(days=random.randint(100, 5000))
        description = f"{title} - отличный фильм"
        movies.append((movie_id, title, genre, release_date, description))

    pg_cursor.executemany(
        "INSERT INTO movies (id, title, genre, release_date, description) VALUES (%s, %s, %s, %s, %s)",
        movies,
    )
    pg_conn.commit()
    return [m[0] for m in movies]


# Генерация истории просмотров
def generate_watch_history(users, movies, n=50):
    history = []
    for _ in range(n):
        user_id = random.choice(users)
        movie_id = random.choice(movies)
        watched_at = datetime.now() - timedelta(days=random.randint(1, 30))
        watch_time = timedelta(minutes=random.randint(10, 120))
        completed = random.choice([True, False])
        history.append(
            (str(uuid.uuid4()), user_id, movie_id, watched_at, watch_time, completed)
        )

    pg_cursor.executemany(
        "INSERT INTO watch_history (id, user_id, movie_id, watched_at, watch_time, completed) VALUES (%s, %s, %s, %s, %s, %s)",
        history,
    )
    pg_conn.commit()


# Генерация событий в ClickHouse
def generate_events(users, movies, n=100):
    events = []
    event_types = ["click", "watch", "like", "search"]

    for _ in range(n):
        user_id = random.choice(users)
        movie_id = random.choice(movies)
        event_type = random.choice(event_types)
        event_time = datetime.now() - timedelta(minutes=random.randint(1, 1440))
        extra_data = '{"detail": "some metadata"}'
        events.append(
            (str(uuid.uuid4()), user_id, movie_id, event_type, event_time, extra_data)
        )

    ch_client.execute(
        "INSERT INTO user_events (event_id, user_id, movie_id, event_type, event_time, extra_data) VALUES",
        events,
    )


# Запуск генерации данных
users = generate_users(10)
movies = generate_movies(5)
generate_watch_history(users, movies, 50)
generate_events(users, movies, 100)

pg_cursor.close()
pg_conn.close()
