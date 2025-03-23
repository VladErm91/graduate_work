import backoff
from functional.settings import test_settings
from redis import Redis
from redis.exceptions import ConnectionError


@backoff.on_exception(
    backoff.expo, (ConnectionError, ConnectionRefusedError), max_tries=20
)
def ping_redis(redis_client):
    redis_client.ping()


if __name__ == "__main__":
    redis_client = Redis(host=test_settings.redis_host, port=test_settings.redis_port)
    ping_redis(redis_client)
