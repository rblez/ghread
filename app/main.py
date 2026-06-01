import httpx
from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader, APIKeyQuery
from typing import Optional

from app.config import settings
from app.github.fetcher import (
    fetch_repo_index, fetch_file_content,
    fetch_issues, fetch_pulls, fetch_releases, fetch_commits,
    fetch_contributors, fetch_tags, fetch_languages, search_code,
)
from app.models.responses import (
    RepoIndexResponse, FileContentResponse, HealthResponse,
    IssuesResponse, PullsResponse, ReleasesResponse, CommitsResponse,
    ContributorsResponse, TagsResponse, LanguagesResponse, SearchCodeResponse,
)


app = FastAPI(
    title="GitHub Repo Reader API",
    description="REST API proxy to fetch GitHub repository trees and file contents for AI Agent consumption.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)
api_key_query = APIKeyQuery(name="key", auto_error=False)


def verify_api_key(
    auth_header: Optional[str] = Security(api_key_header),
    query_key: Optional[str] = Security(api_key_query)
):
    if not settings.API_KEY:
        return
    token = None
    if auth_header:
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
        else:
            token = auth_header
    if not token and query_key:
        token = query_key
    if not token or token != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key."
        )


def _parse_repo(repo: str):
    if not repo or "/" not in repo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid repository format. Must be 'owner/repo'."
        )
    parts = repo.split("/", 1)
    return parts[0], parts[1]


def _handle_github_error(e: Exception):
    if isinstance(e, httpx.HTTPStatusError):
        status_code = e.response.status_code
        detail = f"GitHub API error: {e.response.text}"
        raise HTTPException(status_code=status_code, detail=detail)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"An error occurred: {str(e)}"
    )


@app.get("/", dependencies=[Depends(verify_api_key)])
async def get_repo_or_file(
    repo: str,
    path: Optional[str] = None,
    ref: Optional[str] = None
):
    owner, repo_name = _parse_repo(repo)
    try:
        if path:
            return await fetch_file_content(owner, repo_name, path, ref)
        else:
            return await fetch_repo_index(owner, repo_name, ref)
    except Exception as e:
        _handle_github_error(e)


@app.get("/issues", response_model=IssuesResponse, dependencies=[Depends(verify_api_key)])
async def get_issues(
    repo: str,
    state: str = "open",
    sort: str = "created",
    direction: str = "desc",
    per_page: int = 20
):
    owner, repo_name = _parse_repo(repo)
    try:
        return await fetch_issues(owner, repo_name, state, sort, direction, per_page)
    except Exception as e:
        _handle_github_error(e)


@app.get("/pulls", response_model=PullsResponse, dependencies=[Depends(verify_api_key)])
async def get_pulls(
    repo: str,
    state: str = "open",
    sort: str = "created",
    direction: str = "desc",
    per_page: int = 20
):
    owner, repo_name = _parse_repo(repo)
    try:
        return await fetch_pulls(owner, repo_name, state, sort, direction, per_page)
    except Exception as e:
        _handle_github_error(e)


@app.get("/releases", response_model=ReleasesResponse, dependencies=[Depends(verify_api_key)])
async def get_releases(
    repo: str,
    per_page: int = 20
):
    owner, repo_name = _parse_repo(repo)
    try:
        return await fetch_releases(owner, repo_name, per_page)
    except Exception as e:
        _handle_github_error(e)


@app.get("/commits", response_model=CommitsResponse, dependencies=[Depends(verify_api_key)])
async def get_commits(
    repo: str,
    ref: Optional[str] = None,
    per_page: int = 20
):
    owner, repo_name = _parse_repo(repo)
    try:
        return await fetch_commits(owner, repo_name, ref, per_page)
    except Exception as e:
        _handle_github_error(e)


@app.get("/contributors", response_model=ContributorsResponse, dependencies=[Depends(verify_api_key)])
async def get_contributors(
    repo: str,
    per_page: int = 20
):
    owner, repo_name = _parse_repo(repo)
    try:
        return await fetch_contributors(owner, repo_name, per_page)
    except Exception as e:
        _handle_github_error(e)


@app.get("/tags", response_model=TagsResponse, dependencies=[Depends(verify_api_key)])
async def get_tags(
    repo: str,
    per_page: int = 20
):
    owner, repo_name = _parse_repo(repo)
    try:
        return await fetch_tags(owner, repo_name, per_page)
    except Exception as e:
        _handle_github_error(e)


@app.get("/languages", response_model=LanguagesResponse, dependencies=[Depends(verify_api_key)])
async def get_languages(
    repo: str
):
    owner, repo_name = _parse_repo(repo)
    try:
        return await fetch_languages(owner, repo_name)
    except Exception as e:
        _handle_github_error(e)


@app.get("/search/code", response_model=SearchCodeResponse, dependencies=[Depends(verify_api_key)])
async def get_search_code(
    repo: str,
    q: str,
    per_page: int = 20
):
    owner, repo_name = _parse_repo(repo)
    try:
        return await search_code(owner, repo_name, q, per_page)
    except Exception as e:
        _handle_github_error(e)


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="1.0.0")
