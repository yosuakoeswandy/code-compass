from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel


@dataclass
class SearchQuery(BaseModel):
    query: str
    queryType: Optional[str] = None


@dataclass
class SearchChunkResponse():
    id: str
    filePath: str
    fileName: str
    content: str
    lineStart: int
    lineEnd: int
    vectorScore: float
