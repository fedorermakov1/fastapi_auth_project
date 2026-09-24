from uuid import uuid4, UUID

from fastapi import APIRouter, Request, Depends
import json
import aio_pika

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models import User

from app.core.dependencies import get_cache
from app.cache.cache import Cache

router = APIRouter(
    prefix="/dev",
    tags=["Development"]
)

@router.get("/health")
async def health():
    return {
        "status": "ok"
    }


@router.get("/redis-test")
async def redis_test(request: Request):
    redis_client = request.app.state.redis

    await redis_client.set("lifespan_test", "Hello from FastAPI")

    value = await redis_client.get("lifespan_test")

    return {
        "value": value
    }


@router.get("/cache-test1")
async def cache_test(cache: Cache = Depends(get_cache)):
    print("CACHE OBJECT:", cache)
    print("REDIS OBJECT:", cache.redis)

    return {
        "message": "Cache dependency works"
    }


@router.get("/cache-test2")
async def cache_test(cache: Cache = Depends(get_cache)):
    await cache.set("test_key", "hello")

    return {"message": "saved"}


@router.get("/cache-test3")
async def cache_test(cache: Cache = Depends(get_cache)):
    value = await cache.get("test_key")

    return {
        "value": value
    }


@router.delete("/cache-test/{key}")
async def delete_cache(
        key: str,
        cache: Cache = Depends(get_cache),
):
    deleted = await cache.delete(key)

    return {
        "deleted": deleted
    }


@router.get("/redis-json-test")
async def redis_json_test(cache: Cache = Depends(get_cache)):
    task = {
        "id": 1,
        "title": "Изучить Redis",
        "completed": False,
    }

    await cache.set("task:1", task)

    task_from_redis = await cache.get("task:1")

    return {
        "task": task_from_redis,
        "type": str(type(task_from_redis)),
    }


@router.get("/monitoring-error-test")
async def monitoring_error_test():
    raise RuntimeError("Monitoring test")


@router.post("/test-transaction")
async def test_transaction_endpoint(
        db: AsyncSession = Depends(get_db),
):
    user = User(
        username="commit_test",
        email="commit@test.com",
        full_name="Commit Test",
        hashed_password="fake_hash",
        disabled=False,
        role="user",
    )

    db.add(user)

    await db.commit()
    await db.refresh(user)

    return {
        "id": user.id,
        "username": user.username,
    }


@router.post("/test-transaction-rollback")
async def test_transaction_rollback_endpoint(
        db: AsyncSession = Depends(get_db),
):
    user = User(
        username="rollback_test",
        email="rollback@test.com",
        full_name="Rollback Test",
        hashed_password="fake_hash",
        disabled=False,
        role="user",
    )

    db.add(user)

    await db.flush()

    await db.rollback()

    return {
        "message": "rolled back",
    }


@router.post("/test-transaction-error")
async def test_transaction_error(
        db: AsyncSession = Depends(get_db),
):
    try:
        user = User(
            username="atomic_test",
            email="atomic@test.com",
            full_name="Atomic Test",
            hashed_password="fake_hash",
            disabled=False,
            role="user",
        )

        db.add(user)

        await db.flush()

        await db.commit()

        return {
            "message": "success",
        }

    except Exception:
        await db.rollback()

        raise


@router.post("/test-transaction-context")
async def test_transaction_context(
        db: AsyncSession = Depends(get_db),
):
    async with db.begin():
        user = User(
            username="context_test",
            email="context@test.com",
            full_name="Context Test",
            hashed_password="fake_hash",
            disabled=False,
            role="user",
        )

        db.add(user)

    return {
        "message": "committed",
    }


@router.post("/test-transaction-context-error")
async def test_transaction_context_error(
        db: AsyncSession = Depends(get_db),
):
    async with db.begin():
        user = User(
            username="context_error_test",
            email="context_error@test.com",
            full_name="Context Error Test",
            hashed_password="fake_hash",
            disabled=False,
            role="user",
        )

        db.add(user)

        await db.flush()

        raise ValueError("Something went wrong")

    return {
        "message": "committed",
    }


@router.post("/test-commit-inside-begin")
async def test_commit_inside_begin(
        db: AsyncSession = Depends(get_db),
):
    async with db.begin():
        user = User(
            username="commit_inside_begin",
            email="commit_inside_begin@test.com",
            full_name="Commit Inside Begin",
            hashed_password="fake_hash",
            disabled=False,
            role="user",
        )

        db.add(user)

        await db.commit()

    return {
        "message": "done",
    }


@router.post("/test-savepoint")
async def test_savepoint(
        db: AsyncSession = Depends(get_db),
):
    async with db.begin():
        user_1 = User(
            username="savepoint_1",
            email="savepoint1@test.com",
            full_name="Savepoint 1",
            hashed_password="fake_hash",
            disabled=False,
            role="user",
        )

        db.add(user_1)

        try:
            async with db.begin_nested():
                user_2 = User(
                    username="savepoint_2",
                    email="savepoint2@test.com",
                    full_name="Savepoint 2",
                    hashed_password="fake_hash",
                    disabled=False,
                    role="user",
                )

                db.add(user_2)

                raise ValueError("Ошибка внутри savepoint")

        except ValueError:
            pass

        user_3 = User(
            username="savepoint_3",
            email="savepoint3@test.com",
            full_name="Savepoint 3",
            hashed_password="fake_hash",
            disabled=False,
            role="user",
        )

        db.add(user_3)

    return {"message": "ok"}

@router.post("/publish")
async def publish_order(request: Request):
    exchange = request.app.state.exchange

    message = aio_pika.Message(
        body=json.dumps({
            "event_id": str(uuid4()),
            "event": "order.created",
            "order_id": 123,
        }).encode(),
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )

    await exchange.publish(
        message,
        routing_key="order.created",
    )

    return {"status": "published"}

@router.post("/publish-invalid")
async def publish_invalid_order(request: Request):
    exchange = request.app.state.exchange

    message = aio_pika.Message(
        body=b'{"event": "order.created", "order_id": 123',
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )

    await exchange.publish(
        message,
        routing_key="order.created",
    )

    return {"status": "published invalid message"}

@router.post("/publish/{event_id}")
async def publish_order(
    event_id: UUID,
    request: Request,
):
    exchange = request.app.state.exchange

    message = aio_pika.Message(
        body=json.dumps({
            "event_id": str(event_id),
            "event": "order.created",
            "order_id": 123,
        }).encode(),
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )

    await exchange.publish(
        message,
        routing_key="order.created",
    )

    return {
        "status": "published",
        "event_id": str(event_id),
    }
