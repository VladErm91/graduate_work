from redis.asyncio import Redis


class TokenRepository:
    @staticmethod
    async def store_tokens(
        redis: Redis,
        user_id: str,
        access_token: str,
        refresh_token: str,
        access_expire: int,
        refresh_expire: int,
    ):
        await redis.set(f"access_token:{user_id}", access_token, ex=access_expire)
        await redis.set(f"refresh_token:{user_id}", refresh_token, ex=refresh_expire)

    @staticmethod
    async def delete_tokens(redis: Redis, user_id: str):
        await redis.delete(f"access_token:{user_id}")
        await redis.delete(f"refresh_token:{user_id}")
