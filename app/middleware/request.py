import time
import uuid

from fastapi import Request

from app.monitoring.metrics import (
    requests_total,
    active_requests,
    request_duration,
)


async def request_middleware(
        request: Request,
        call_next,
):
    request_id = str(uuid.uuid4())

    if request.url.path == "/metrics":
        return await call_next(request)

    active_requests.inc()

    start_time = time.perf_counter()

    response = None

    try:
        response = await call_next(request)

        return response

    finally:
        process_time = time.perf_counter() - start_time

        active_requests.dec()

        route = request.scope.get("route")

        if route is not None:
            route_template = route.path

            status = (
                str(response.status_code)
                if response is not None
                else "500"
            )

            requests_total.labels(
                method=request.method,
                route=route_template,
                status=status,
            ).inc()

            request_duration.labels(
                method=request.method,
                route=route_template,
                status=status,
            ).observe(process_time)

        if response is not None:
            response.headers["X-Request-ID"] = request_id

            print(
                f"[{request_id}] "
                f"{request.method} {request.url.path} "
                f"-> {response.status_code} "
                f"({process_time:.4f}s)"
            )
