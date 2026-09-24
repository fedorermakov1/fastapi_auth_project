from app.rate_limit.strategies import RateLimitStrategy


class RateLimiter:

    def __init__(
            self,
            strategy: RateLimitStrategy
    ):
        self.strategy = strategy

    async def is_allowed(
            self,
            client_id: str,
            limit: int,
            window: int
    ) -> bool:
        return await self.strategy.is_allowed(
            client_id=client_id,
            limit=limit,
            window=window
        )
