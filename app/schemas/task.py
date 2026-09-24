from pydantic import BaseModel, ConfigDict
from datetime import datetime

class TaskCreate(BaseModel):
    title: str
    description: str | None = None

class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    completed: bool | None = None

class TaskRead(BaseModel):
    id: int
    title: str
    description: str | None
    completed: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )