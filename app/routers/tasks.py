from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from app.models import User
from app.repositories.dependencies import get_uow
from app.repositories.unit_of_work import UnitOfWork
from app.schemas.task import (
    TaskCreate,
    TaskRead,
    TaskUpdate
)
from app.services.task_service import (
    create_task,
    get_tasks as get_tasks_service,
    get_task_by_id,
    update_task,
    delete_task
)
from app.core.dependencies import get_current_active_user
from app.cache import Cache
from app.core.dependencies import get_cache

from app.tasks.example import add
from celery.result import AsyncResult
from app.celery_app import celery_app

from app.rate_limit.dependencies import user_rate_limit

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"]
)


@router.post("/")
async def create_task_endpoint(
        task_data: TaskCreate,
        current_user: User = Depends(get_current_active_user),
        uow: UnitOfWork = Depends(get_uow, scope="function"),
        cache: Cache = Depends(get_cache)
):
    task = await create_task(
        uow=uow,
        cache=cache,
        task_data=task_data,
        user_id=current_user.id
    )

    return task


@router.post(
    "/celery-test",
    status_code=status.HTTP_202_ACCEPTED,

)
async def celery_test():
    result = add.delay(10, 20)

    return {
        "task_id": result.id
    }


@router.get("/celery-result/{task_id}")
async def get_celery_result(task_id: str):
    task = AsyncResult(
        task_id,
        app=celery_app
    )

    if task.status == "FAILURE":
        return {
            "task_id": task_id,
            "status": task.status,
            "error": "Task execution failed",
        }

    response = {
        "task_id": task_id,
        "status": task.status,
    }

    if task.status == "SUCCESS":
        response["result"] = task.result

    return response


@router.get(
    "/",
    response_model=list[TaskRead],
    dependencies=[
        Depends(user_rate_limit(30, 60))
    ]
)
async def read_tasks(
        current_user: User = Depends(get_current_active_user),
        uow: UnitOfWork = Depends(get_uow, scope="function"),
        cache: Cache = Depends(get_cache)
):
    tasks = await get_tasks_service(
        uow=uow,
        cache=cache,
        user_id=current_user.id
    )

    return tasks


@router.get("/{task_id}", response_model=TaskRead)
async def read_task(
        task_id: int,
        current_user: User = Depends(get_current_active_user),
        uow: UnitOfWork = Depends(get_uow, scope="function")
):
    task = await get_task_by_id(
        uow=uow,
        task_id=task_id,
        user_id=current_user.id
    )

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return task


@router.put(
    "/{task_id}",
    response_model=TaskRead
)
async def update_task_endpoint(
        task_id: int,
        task_data: TaskUpdate,
        current_user: User = Depends(
            get_current_active_user
        ),
        uow: UnitOfWork = Depends(get_uow, scope="function"),
        cache: Cache = Depends(get_cache)
):
    task = await update_task(
        uow=uow,
        cache=cache,
        user_id=current_user.id,
        task_id=task_id,
        task_data=task_data
    )

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return task


@router.delete("/{task_id}")
async def delete_task_by_id(
        task_id: int,
        current_user: User = Depends(get_current_active_user),
        uow: UnitOfWork = Depends(get_uow, scope="function"),
        cache: Cache = Depends(get_cache)
):
    deleted = await delete_task(
        uow=uow,
        cache=cache,
        task_id=task_id,
        user_id=current_user.id
    )

    if deleted is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return {
        "message": "Task deleted successfully"
    }
