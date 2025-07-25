import os
import re
from dotenv import load_dotenv
from pymilvus import connections, utility
from typing import List, Optional
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.core import Settings
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.core.postprocessor import LLMRerank
from src.app.models import SearchChunkResponse
from src.app.custom_splitter import CustomCodeSplitter
from llama_index.core.ingestion import IngestionPipeline


load_dotenv()
MILVUS_URI = os.getenv("MILVUS_URI")
MILVUS_TOKEN = os.getenv("MILVUS_TOKEN")


def _get_or_create_store(collection_name: str) -> MilvusVectorStore:
    return MilvusVectorStore(
        uri=MILVUS_URI, token=MILVUS_TOKEN,
        collection_name=collection_name,
        enable_dense=True,
        dim=1536,
        enable_sparse=True,
        overwrite=False,
    )


def create_collections_impl(collection_name: str):
    connections.connect(uri=MILVUS_URI, token=MILVUS_TOKEN)

    if utility.has_collection(collection_name):
        raise ValueError(f"Collection '{collection_name}' already exists.")

    _get_or_create_store(collection_name)


def delete_collection_impl(collection_name: str):
    connections.connect(uri=MILVUS_URI, token=MILVUS_TOKEN)

    if not utility.has_collection(collection_name):
        raise ValueError(f"Collection '{collection_name}' does not exist.")

    utility.drop_collection(collection_name)


async def init_collection_impl(collection_name: str, path: str):
    connections.connect(uri=MILVUS_URI, token=MILVUS_TOKEN)

    if not utility.has_collection(collection_name):
        raise ValueError(f"Collection '{collection_name}' does not exist.")

    # TODO: Sanitize input
    documents = SimpleDirectoryReader(input_dir=path, recursive=True).load_data()

    vector_store = _get_or_create_store(collection_name)

    pipeline = IngestionPipeline(
        transformations=[CustomCodeSplitter(), Settings.embed_model],
        vector_store=vector_store,
    )
    nodes = await pipeline.arun(documents=documents)
    await vector_store.async_add(nodes)

    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context)

    return len(nodes)


def try_connection():
    connections.connect(uri=MILVUS_URI, token=MILVUS_TOKEN, _async=True)

    print("Success")


def search_collection_impl(
    collection_name: str, query: str, query_type: Optional[str]
) -> List[SearchChunkResponse]:
    connections.connect(uri=MILVUS_URI, token=MILVUS_TOKEN)

    if not utility.has_collection(collection_name):
        raise ValueError(f"Collection '{collection_name}' does not exist.")

    vector_store = _get_or_create_store(collection_name)
    index = VectorStoreIndex.from_vector_store(vector_store)

    mode = query_type if query_type is not None else "hybrid"

    retriever = index.as_retriever(vector_store_query_mode=mode, similarity_top_k=10)
    retrieved_nodes = retriever.retrieve(query)

    reranker = LLMRerank(top_n=5)
    reranked_nodes = reranker.postprocess_nodes(nodes=retrieved_nodes, query_str=query)

    return [
        SearchChunkResponse(
            id=node_with_score.node.id_,
            filePath=_get_relative_file_path(
                collection_name, node_with_score.node.metadata.get("file_path", "")
            ),
            fileName=node_with_score.node.metadata.get("file_name", ""),
            content=node_with_score.node.text,
            lineStart=node_with_score.node.metadata.get("line_start", 0),
            lineEnd=node_with_score.node.metadata.get("line_end", 0),
            vectorScore=node_with_score.score,
        )
        for node_with_score in reranked_nodes
    ]


def _get_relative_file_path(collection_name: str, file_path: str) -> str:
    # Replace whitespace and hyphen with underscore in both strings
    def normalize(s):
        return re.sub(r"[\s\-]+", "_", s)

    # Split the file path into parts and normalize each part
    parts = file_path.strip(os.sep).split(os.sep)
    norm_parts = [normalize(part) for part in parts]

    # Find the index of the collection_name in the normalized parts
    try:
        idx = norm_parts.index(collection_name)
        # Join the path after collection_name
        rel_parts = parts[idx + 1 :]
        return os.path.join(*rel_parts)
    except ValueError:
        # If not found, return the original file_path
        return file_path
