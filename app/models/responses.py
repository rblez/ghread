from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class RepoMetadata(BaseModel):
    full_name: str
    description: Optional[str] = None
    default_branch: str
    stars: int
    language: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    license: Optional[str] = None
    private: bool

class TreeItem(BaseModel):
    path: str
    type: str
    size: Optional[int] = None

class RepoIndexResponse(BaseModel):
    repo: RepoMetadata
    tree: List[TreeItem]
    branches: List[str]
    readme: Optional[str] = None

class FileContentResponse(BaseModel):
    repo: str
    path: str
    size: int
    encoding: str
    content: Optional[str] = None
    note: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    version: str
