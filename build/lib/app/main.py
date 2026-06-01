from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader, APIKeyQuery
from typing import Optional
from app.config import settings
from app.github.fetcher import fetch_repo_index, fetch_file_content
from app.models.responses import RepoIndexResponse, FileContentResponse, HealthResponse

app = FastAPI(
    title="GitHub Repo Reader API",
    description="REST API proxy to fetch GitHub repository trees and file contents for AI Agent consumption.",
    version="1.0.0"
)

# Enable CORS for all domains so AI agents can query directly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key Security Definitions
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)
api_key_query = APIKeyQuery(name="key", auto_error=False)

def verify_api_key(
    auth_header: Optional[str] = Security(api_key_header),
    query_key: Optional[str] = Security(api_key_query)
):
    # If no API key is configured, bypass check
    if not settings.API_KEY:
        return
        
    token = None
    
    # 1. Check Authorization header (support "Bearer <key>" or just "<key>")
    if auth_header:
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
        else:
            token = auth_header
            
    # 2. Check query parameter `?key=xxx`
    if not token and query_key:
        token = query_key
        
    if not token or token != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key."
        )

@app.get("/", dependencies=[Depends(verify_api_key)])
async def get_repo_or_file(
    repo: str,
    path: Optional[str] = None,
    ref: Optional[str] = None
):
    """
    Main endpoint.
    - If `repo` is provided (e.g. `owner/repo`) and no `path`, returns the index.
    - If `repo` and `path` are provided, returns the content of the file.
    - Optional `ref` parameter specifies the branch/tag/commit.
    """
    if not repo or "/" not in repo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid repository format. Must be 'owner/repo'."
        )
        
    parts = repo.split("/", 1)
    owner, repo_name = parts[0], parts[1]
    
    try:
        if path:
            return await fetch_file_content(owner, repo_name, path, ref)
        else:
            return await fetch_repo_index(owner, repo_name, ref)
    except Exception as e:
        # Check if it looks like a HTTP status error from Octokit/httpx
        import httpx
        if isinstance(e, httpx.HTTPStatusError):
            status_code = e.response.status_code
            detail = f"GitHub API error: {e.response.text}"
            raise HTTPException(status_code=status_code, detail=detail)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="1.0.0")
