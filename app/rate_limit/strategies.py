from abc import ABC, abstractmethod

from redis.asyncio import Redis

class RateLimitStrategy(ABC):
    @abstractmethod
    async def is_allowed(
            self,
            client_id: str,
            limit: int,
            window: int

    ) -> bool:
        pass

class FixedWindowStrategy(RateLimitStrategy):

    def __init__(self, client: Redis):
        self.client = client

    async def is_allowed(
        self,
        client_id: str,
        limit: int,
        window: int
    ) -> bool:

        key = f"rate_limit:{client_id}"

        count = await self.client.incr(key)

        if count == 1:
            await self.client.expire(
                key,
                window
            )

        return count <= limit