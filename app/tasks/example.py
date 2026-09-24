import time

from celery import Celery

from app.celery_app import celery_app

attempts = 0


@celery_app.task
def add(a: int, b: int) -> int:
    print(f"CALCULATION START: {a} + {b}")

    time.sleep()

    result = a + b

    print(f"CALCULATION END: {result}")

    return result

@celery_app.task
def broken_task():
    print("BROKEN TASK START")
    raise ValueError("Something went wrong")

@celery_app.task
def send_email(email: str) -> str:
    print(f"SENDING EMAIL TO: {email}")
    return f"Email sent to {email}"