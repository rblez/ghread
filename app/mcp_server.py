from mcp.server.fastmcp import FastMCP
from app.github.fetcher import (
    fetch_repo_index,
    fetch_file_content,
    fetch_issues,
    fetch_pulls,
    fetch_releases,
    fetch_commits,
    fetch_contributors,
    fetch_tags,
    fetch_languages,
    search_code as fetch_search_code,
)

mcp = FastMCP(
    "ghread",
    instructions="GitHub Repo Reader MCP Server — Read GitHub repositories without direct API access.",
)


def _parse_owner_repo(repo: str) -> tuple[str, str]:
    parts = repo.split("/", 1)
    return parts[0], parts[1]


@mcp.tool()
async def read_repo_index(repo: str, ref: str | None = None) -> dict:
    """Get full repository metadata, recursive file tree, branches list, and README content."""
    owner, name = _parse_owner_repo(repo)
    result = await fetch_repo_index(owner, name, ref)
    return result.model_dump()


@mcp.tool()
async def read_file(repo: str, path: str, ref: str | None = None) -> dict:
    """Read a single file's content. Returns utf-8 decoded text or marks as binary."""
    owner, name = _parse_owner_repo(repo)
    result = await fetch_file_content(owner, name, path, ref)
    return result.model_dump()


@mcp.tool()
async def list_issues(
    repo: str,
    state: str = "open",
    sort: str = "created",
    direction: str = "desc",
    per_page: int = 20,
) -> dict:
    """List issues in a repository. Parameters: state (open/closed/all), sort (created/updated/comments), direction (asc/desc)."""
    owner, name = _parse_owner_repo(repo)
    result = await fetch_issues(owner, name, state, sort, direction, per_page)
    return result.model_dump()


@mcp.tool()
async def list_pull_requests(
    repo: str,
    state: str = "open",
    sort: str = "created",
    direction: str = "desc",
    per_page: int = 20,
) -> dict:
    """List pull requests in a repository. Includes head/base refs and draft status."""
    owner, name = _parse_owner_repo(repo)
    result = await fetch_pulls(owner, name, state, sort, direction, per_page)
    return result.model_dump()


@mcp.tool()
async def list_releases(repo: str, per_page: int = 20) -> dict:
    """List releases in a repository with tag name, title, body, and prerelease flag."""
    owner, name = _parse_owner_repo(repo)
    result = await fetch_releases(owner, name, per_page)
    return result.model_dump()


@mcp.tool()
async def list_commits(repo: str, ref: str | None = None, per_page: int = 20) -> dict:
    """List recent commits on a branch/ref. Returns SHA, message, author, and date."""
    owner, name = _parse_owner_repo(repo)
    result = await fetch_commits(owner, name, ref, per_page)
    return result.model_dump()


@mcp.tool()
async def list_contributors(repo: str, per_page: int = 20) -> dict:
    """List contributors with their commit counts."""
    owner, name = _parse_owner_repo(repo)
    result = await fetch_contributors(owner, name, per_page)
    return result.model_dump()


@mcp.tool()
async def list_tags(repo: str, per_page: int = 20) -> dict:
    """List git tags with their commit SHA."""
    owner, name = _parse_owner_repo(repo)
    result = await fetch_tags(owner, name, per_page)
    return result.model_dump()


@mcp.tool()
async def get_languages(repo: str) -> dict:
    """Get language breakdown as bytes per language (e.g. {'Python': 5000, 'TypeScript': 2000})."""
    owner, name = _parse_owner_repo(repo)
    result = await fetch_languages(owner, name)
    return result.model_dump()


@mcp.tool()
async def search_code(repo: str, query: str, per_page: int = 20) -> dict:
    """Search code within a repository. Returns matching files with path and URL."""
    owner, name = _parse_owner_repo(repo)
    result = await fetch_search_code(owner, name, query, per_page)
    return result.model_dump()
