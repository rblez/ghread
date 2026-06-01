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


class IssueItem(BaseModel):
    number: int
    title: str
    state: str
    created_at: str
    updated_at: str
    closed_at: Optional[str] = None
    labels: List[str] = Field(default_factory=list)
    body: Optional[str] = None
    user_login: Optional[str] = None
    html_url: str


class IssuesResponse(BaseModel):
    repo: str
    count: int
    issues: List[IssueItem]


class PullRequestItem(BaseModel):
    number: int
    title: str
    state: str
    created_at: str
    updated_at: str
    merged_at: Optional[str] = None
    body: Optional[str] = None
    user_login: Optional[str] = None
    head_ref: str
    base_ref: str
    draft: bool = False
    html_url: str


class PullsResponse(BaseModel):
    repo: str
    count: int
    pull_requests: List[PullRequestItem]


class ReleaseItem(BaseModel):
    tag_name: str
    name: Optional[str] = None
    body: Optional[str] = None
    prerelease: bool = False
    created_at: str
    published_at: Optional[str] = None
    html_url: str


class ReleasesResponse(BaseModel):
    repo: str
    count: int
    releases: List[ReleaseItem]


class CommitItem(BaseModel):
    sha: str
    message: str
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    author_date: Optional[str] = None
    author_login: Optional[str] = None
    html_url: str


class CommitsResponse(BaseModel):
    repo: str
    count: int
    commits: List[CommitItem]


class ContributorItem(BaseModel):
    login: str
    avatar_url: str
    html_url: str
    contributions: int


class ContributorsResponse(BaseModel):
    repo: str
    contributors: List[ContributorItem]


class TagItem(BaseModel):
    name: str
    commit_sha: str


class TagsResponse(BaseModel):
    repo: str
    tags: List[TagItem]


class LanguagesResponse(BaseModel):
    repo: str
    languages: Dict[str, int]


class SearchCodeItem(BaseModel):
    name: str
    path: str
    html_url: str
    sha: str


class SearchCodeResponse(BaseModel):
    repo: str
    query: str
    total_count: int
    items: List[SearchCodeItem]
