import base64
from typing import Optional
from app.github.client import github_client
from app.models.responses import (
    RepoIndexResponse, RepoMetadata, TreeItem, FileContentResponse,
    IssuesResponse, IssueItem,
    PullsResponse, PullRequestItem,
    ReleasesResponse, ReleaseItem,
    CommitsResponse, CommitItem,
    ContributorsResponse, ContributorItem,
    TagsResponse, TagItem,
    LanguagesResponse,
    SearchCodeResponse, SearchCodeItem,
)


async def fetch_repo_index(owner: str, repo: str, ref: Optional[str] = None) -> RepoIndexResponse:
    repo_meta_raw = await github_client.get_repo(owner, repo)
    branch_ref = ref if ref else repo_meta_raw["default_branch"]
    branches = await github_client.get_branches(owner, repo)
    tree_raw = await github_client.get_tree(owner, repo, branch_ref, recursive=True)
    tree_items = []
    for item in tree_raw.get("tree", []):
        tree_items.append(TreeItem(
            path=item["path"],
            type=item["type"],
            size=item.get("size")
        ))
    readme = None
    try:
        readme = await github_client.get_readme(owner, repo, branch_ref)
    except Exception:
        pass
    license_name = None
    if "license" in repo_meta_raw and repo_meta_raw["license"]:
        license_name = repo_meta_raw["license"].get("spdx_id") or repo_meta_raw["license"].get("name")
    meta = RepoMetadata(
        full_name=repo_meta_raw["full_name"],
        description=repo_meta_raw.get("description"),
        default_branch=repo_meta_raw["default_branch"],
        stars=repo_meta_raw.get("stargazers_count", 0),
        language=repo_meta_raw.get("language"),
        topics=repo_meta_raw.get("topics", []),
        created_at=repo_meta_raw["created_at"],
        updated_at=repo_meta_raw["updated_at"],
        license=license_name,
        private=repo_meta_raw.get("private", False)
    )
    return RepoIndexResponse(
        repo=meta,
        tree=tree_items,
        branches=branches,
        readme=readme
    )


async def fetch_file_content(owner: str, repo: str, path: str, ref: Optional[str] = None) -> FileContentResponse:
    raw_content_data = await github_client.get_file_content(owner, repo, path, ref)
    size = raw_content_data.get("size", 0)
    encoding = raw_content_data.get("encoding", "")
    content = raw_content_data.get("content", "")
    if encoding == "base64" and content:
        try:
            decoded_bytes = base64.b64decode(content)
            decoded_text = decoded_bytes.decode("utf-8")
            return FileContentResponse(
                repo=f"{owner}/{repo}",
                path=path,
                size=size,
                encoding="utf-8",
                content=decoded_text
            )
        except UnicodeDecodeError:
            return FileContentResponse(
                repo=f"{owner}/{repo}",
                path=path,
                size=size,
                encoding="binary",
                content=None,
                note="Binary file — content not available as text"
            )
    else:
        return FileContentResponse(
            repo=f"{owner}/{repo}",
            path=path,
            size=size,
            encoding=encoding or "unknown",
            content=content if content else None,
            note=None if content else "No content available"
        )


async def fetch_issues(
    owner: str, repo: str,
    state: str = "open",
    sort: str = "created",
    direction: str = "desc",
    per_page: int = 20
) -> IssuesResponse:
    raw = await github_client.get_issues(owner, repo, state, sort, direction, per_page)
    items = []
    for i in raw:
        labels = [l["name"] for l in i.get("labels", [])]
        items.append(IssueItem(
            number=i["number"],
            title=i["title"],
            state=i["state"],
            created_at=i["created_at"],
            updated_at=i["updated_at"],
            closed_at=i.get("closed_at"),
            labels=labels,
            body=i.get("body"),
            user_login=i["user"]["login"] if i.get("user") else None,
            html_url=i["html_url"],
        ))
    return IssuesResponse(repo=f"{owner}/{repo}", count=len(items), issues=items)


async def fetch_pulls(
    owner: str, repo: str,
    state: str = "open",
    sort: str = "created",
    direction: str = "desc",
    per_page: int = 20
) -> PullsResponse:
    raw = await github_client.get_pulls(owner, repo, state, sort, direction, per_page)
    items = []
    for pr in raw:
        items.append(PullRequestItem(
            number=pr["number"],
            title=pr["title"],
            state=pr["state"],
            created_at=pr["created_at"],
            updated_at=pr["updated_at"],
            merged_at=pr.get("merged_at"),
            body=pr.get("body"),
            user_login=pr["user"]["login"] if pr.get("user") else None,
            head_ref=pr["head"]["ref"],
            base_ref=pr["base"]["ref"],
            draft=pr.get("draft", False),
            html_url=pr["html_url"],
        ))
    return PullsResponse(repo=f"{owner}/{repo}", count=len(items), pull_requests=items)


async def fetch_releases(owner: str, repo: str, per_page: int = 20) -> ReleasesResponse:
    raw = await github_client.get_releases(owner, repo, per_page)
    items = []
    for r in raw:
        items.append(ReleaseItem(
            tag_name=r["tag_name"],
            name=r.get("name"),
            body=r.get("body"),
            prerelease=r.get("prerelease", False),
            created_at=r["created_at"],
            published_at=r.get("published_at"),
            html_url=r["html_url"],
        ))
    return ReleasesResponse(repo=f"{owner}/{repo}", count=len(items), releases=items)


async def fetch_commits(owner: str, repo: str, ref: Optional[str] = None, per_page: int = 20) -> CommitsResponse:
    raw = await github_client.get_commits(owner, repo, ref, per_page)
    items = []
    for c in raw:
        author = c.get("author")
        commit_info = c.get("commit", {})
        author_info = commit_info.get("author", {})
        items.append(CommitItem(
            sha=c["sha"],
            message=commit_info.get("message", ""),
            author_name=author_info.get("name"),
            author_email=author_info.get("email"),
            author_date=author_info.get("date"),
            author_login=author["login"] if author else None,
            html_url=c["html_url"],
        ))
    return CommitsResponse(repo=f"{owner}/{repo}", count=len(items), commits=items)


async def fetch_contributors(owner: str, repo: str, per_page: int = 20) -> ContributorsResponse:
    raw = await github_client.get_contributors(owner, repo, per_page)
    items = []
    for c in raw:
        items.append(ContributorItem(
            login=c["login"],
            avatar_url=c.get("avatar_url", ""),
            html_url=c["html_url"],
            contributions=c["contributions"],
        ))
    return ContributorsResponse(repo=f"{owner}/{repo}", contributors=items)


async def fetch_tags(owner: str, repo: str, per_page: int = 20) -> TagsResponse:
    raw = await github_client.get_tags(owner, repo, per_page)
    items = []
    for t in raw:
        items.append(TagItem(
            name=t["name"],
            commit_sha=t["commit"]["sha"],
        ))
    return TagsResponse(repo=f"{owner}/{repo}", tags=items)


async def fetch_languages(owner: str, repo: str) -> LanguagesResponse:
    raw = await github_client.get_languages(owner, repo)
    return LanguagesResponse(repo=f"{owner}/{repo}", languages=raw)


async def search_code(owner: str, repo: str, query: str, per_page: int = 20) -> SearchCodeResponse:
    github_query = f"repo:{owner}/{repo}+{query}"
    raw = await github_client.search_code(github_query, per_page)
    items = []
    for item in raw.get("items", []):
        items.append(SearchCodeItem(
            name=item["name"],
            path=item["path"],
            html_url=item["html_url"],
            sha=item["sha"],
        ))
    return SearchCodeResponse(
        repo=f"{owner}/{repo}",
        query=query,
        total_count=raw.get("total_count", 0),
        items=items,
    )
