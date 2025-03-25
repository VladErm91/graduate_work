import asyncio
from db.redis import redis_client
from db.database import get_db
from repositories.movie_repository import MovieRepository


async def update_popular_movies():
    async with get_db() as db:
        popular_movies = await MovieRepository.get_top_movies(db)

        await redis_client.delete("popular_movies")
        for movie in popular_movies:
            await redis_client.zadd("popular_movies", {movie["id"]: movie["likes"]})


async def main():
    while True:
        await update_popular_movies()
        await asyncio.sleep(3600)  # Обновлять каждый час


if __name__ == "__main__":
    asyncio.run(main())
