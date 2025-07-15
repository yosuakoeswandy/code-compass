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

from fastapi import Body
from typing import List


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_llama_index()
    yield


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


@app.post("/collections/{collection_name}/init")
async def init_collection(collection_name: str, path: str = Body(..., embed=True)):
    try:
        num_docs = init_collection_impl(collection_name, path)
        return {
            "message": f"Successfully populated '{collection_name}' with {num_docs} document(s)."
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
