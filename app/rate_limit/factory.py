from redis.asyncio import Redis

from app.rate_limit.strategies import (
    RateLimitStrategy,
    FixedWindowStrategy,
)


def create_rate_limit_strategy(
        strategy: str,
        redis_client: Redis,
) -> RateLimitStrategy:
    if strategy == "fixed":
        return FixedWindowStrategy(redis_client)

    raise ValueError(f"Unknown rate limit strategy: {strategy}")
