from contextlib import asynccontextmanager
import uvicorn
from models import SearchChunkResponse, SearchQuery
from setup import setup_llama_index
from store import (
    create_collections_impl,
    delete_collection_impl,
    init_collection_impl,
    search_collection_impl,
)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from fastapi import Body, status
from typing import List

import asyncio
import uuid

job_queue = None
job_status = {}
worker_task = None


async def async_worker():
    while True:
        job = await job_queue.get()
        if job is None:
            break
        job_id, collection_name, path = job
        job_status[job_id] = "running"
        try:
            num_docs = await init_collection_impl(collection_name, path)
            job_status[job_id] = f"done ({num_docs} chunks)"
        except Exception as e:
            job_status[job_id] = f"error: {e}"
        finally:
            job_queue.task_done()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global job_queue, worker_task
    job_queue = asyncio.Queue()
    setup_llama_index()
    worker_task = asyncio.create_task(async_worker())
    yield
    await job_queue.put(None)  # Signal to exit worker
    await worker_task


app = FastAPI(lifespan=lifespan)

origins = [
    "codesearch-vscode-extension",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/collections/{collection_name}")
async def create_collection(collection_name: str):
    try:
        create_collections_impl(collection_name)
        return {"message": f"Collection '{collection_name}' created successfully."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/collections/{collection_name}")
async def delete_collection(collection_name: str):
    try:
        delete_collection_impl(collection_name)
        return {"message": f"Collection '{collection_name}' deleted successfully."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/collections/{collection_name}/init", status_code=status.HTTP_202_ACCEPTED)
async def init_collection(collection_name: str, path: str = Body(..., embed=True)):
    job_id = str(uuid.uuid4())
    job_status[job_id] = "pending"
    await job_queue.put((job_id, collection_name, path))
    return {"message": f"Job to populate '{collection_name}' queued.", "job_id": job_id}


@app.get("/collections/init/status/{job_id}")
def get_status(job_id: str):
    return {"status": job_status.get(job_id, "unknown")}


@app.post(
    "/collections/{collection_name}/search", response_model=List[SearchChunkResponse]
)
async def search_collection(collection_name: str, search_query: SearchQuery):
    try:
        results = search_collection_impl(
            collection_name, search_query.query, search_query.queryType
        )
        return results
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
