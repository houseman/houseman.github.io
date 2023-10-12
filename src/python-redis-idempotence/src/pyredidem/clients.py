import redis

# Use the DNS name of the Redis service
REDIS_HOST = "redis"  # Kubernetes takes care of DNS resolution for services,
REDIS_PORT = 6379


class RedisClient:
    def __init__(self) -> None:
        self.r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
