from app.models import Task
from app.cache import Cache
from app.repositories.unit_of_work import UnitOfWork
from app.schemas.task import TaskCreate, TaskUpdate, TaskRead


async def create_task(
        uow: UnitOfWork,
        cache: Cache,
        task_data: TaskCreate,
        user_id: int
):
    task = uow.tasks.create(
        title=task_data.title,
        description=task_data.description,
        user_id=user_id
    )

    await cache.delete(
        f"tasks:user:{user_id}"
    )

    return task


async def get_tasks(
        uow: UnitOfWork,
        cache: Cache,
        user_id: int
):
    cache_key = f"tasks:user:{user_id}"

    cached_tasks = await cache.get(cache_key)

    if cached_tasks is not None:
        print("=== CACHE HIT ===")

        return [
            TaskRead.model_validate(task)
            for task in cached_tasks
        ]

    print("=== CACHE MISS ===")

    tasks = await uow.tasks.get_all_by_user(
        user_id=user_id
    )

    tasks_data = [
        TaskRead.model_validate(task).model_dump(
            mode="json"
        )
        for task in tasks
    ]

    await cache.set(
        cache_key,
        tasks_data,
        expire=60
    )

    return [
        TaskRead.model_validate(task)
        for task in tasks_data
    ]


async def get_task_by_id(
        uow: UnitOfWork,
        task_id: int,
        user_id: int
) -> Task | None:
    return await uow.tasks.get_by_id(
        task_id=task_id,
        user_id=user_id
    )


async def update_task(
    uow: UnitOfWork,
    cache: Cache,
    task_id: int,
    user_id: int,
    task_data: TaskUpdate
):
    task = await uow.tasks.get_by_id(
        task_id,
        user_id
    )

    if task is None:
        return None

    if task_data.title is not None:
        task.title = task_data.title

    if task_data.description is not None:
        task.description = task_data.description

    if task_data.completed is not None:
        task.completed = task_data.completed

    await cache.delete(
        f"tasks:user:{user_id}"
    )

    return task


async def delete_task(
        uow: UnitOfWork,
        cache: Cache,
        task_id: int,
        user_id: int
) -> bool | None:
    task = await uow.tasks.get_by_id(
        task_id=task_id,
        user_id=user_id
    )

    if task is None:
        return None

    await uow.tasks.delete(task)

    await cache.delete(
        f"tasks:user:{user_id}"
    )

    return True