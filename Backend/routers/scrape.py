import asyncio
import json
import uuid
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services.scrapService import run_scrape_and_classify_job, register_job, get_job, list_jobs
from services.leadService import run_classify

router = APIRouter(tags=["Scrape"])

_job_queues: dict[str, asyncio.Queue] = {}


def register_queue(job_id: str, queue: asyncio.Queue) -> None:
    _job_queues[job_id] = queue


def get_queue(job_id: str) -> asyncio.Queue | None:
    return _job_queues.get(job_id)


def remove_queue(job_id: str) -> None:
    _job_queues.pop(job_id, None)


class ScrapeRequest(BaseModel):
    keyword:  str           = Field(..., min_length=1)
    location: str           = Field(..., min_length=1)
    target:   Optional[int] = Field(None, ge=1)


class ScrapeResponse(BaseModel):
    job_id:  str
    message: str


def _sse_event(event_type: str, data: dict) -> str:
    payload = json.dumps({"type": event_type, **data}, ensure_ascii=False)
    return f"data: {payload}\n\n"


@router.get("/scrape/jobs")
async def list_active_jobs():
    return {"active_jobs": list_jobs()}


@router.post("/classify")
async def classify_leads():
    log = await run_classify()
    return {"log": log}


@router.post("/scrape", response_model=ScrapeResponse, status_code=202)
async def start_scrape(body: ScrapeRequest):
    job_id = str(uuid.uuid4())
    target = float("inf") if body.target is None else float(body.target)

    queue: asyncio.Queue = asyncio.Queue()
    register_queue(job_id, queue)

    task = asyncio.create_task(
        run_scrape_and_classify_job(job_id, body.keyword, body.location, target, queue)
    )
    register_job(job_id, task)

    return ScrapeResponse(
        job_id=job_id,
        message="Job dimulai. Pantau progress di /scrape/{job_id}/stream",
    )


@router.get("/scrape/{job_id}/stream")
async def stream_scrape(job_id: str):
    queue = get_queue(job_id)
    if queue is None:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan atau sudah selesai.")

    async def event_generator() -> AsyncGenerator[str, None]:
        yield _sse_event("connected", {"job_id": job_id, "message": "Terhubung ke stream."})

        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                except asyncio.TimeoutError:
                    yield _sse_event("ping", {"message": "keepalive"})
                    continue

                if event is None:
                    yield _sse_event("closed", {"message": "Stream selesai."})
                    break

                yield _sse_event(event["type"], {"message": event["message"]})
        finally:
            remove_queue(job_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":               "no-cache",
            "X-Accel-Buffering":           "no",
            "Connection":                  "keep-alive",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.post("/scrape/{job_id}/cancel")
async def cancel_scrape(job_id: str):
    task = get_job(job_id)
    if not task:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan atau sudah selesai.")

    task.cancel()
    remove_queue(job_id)
    return {"job_id": job_id, "message": "Job dibatalkan."}