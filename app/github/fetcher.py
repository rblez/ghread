import base64
from typing import Dict, Any, Optional
from app.github.client import github_client
from app.models.responses import RepoIndexResponse, RepoMetadata, TreeItem, FileContentResponse

async def fetch_repo_index(owner: str, repo: str, ref: Optional[str] = None) -> RepoIndexResponse:
    # 1. Fetch metadata
    repo_meta_raw = await github_client.get_repo(owner, repo)
    
    # Decide which ref/sha to use for tree
    branch_ref = ref if ref else repo_meta_raw["default_branch"]
    
    # 2. Fetch branches
    branches = await github_client.get_branches(owner, repo)
    
    # 3. Fetch tree
    tree_raw = await github_client.get_tree(owner, repo, branch_ref, recursive=True)
    tree_items = []
    for item in tree_raw.get("tree", []):
        tree_items.append(TreeItem(
            path=item["path"],
            type=item["type"],  # 'blob' or 'tree'
            size=item.get("size")
        ))
        
    # 4. Fetch readme (optional/best-effort)
    readme = None
    try:
        readme = await github_client.get_readme(owner, repo, branch_ref)
    except Exception:
        # Ignore errors fetching readme
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
        # Check if it's binary or text
        # Fast way to decode
        try:
            decoded_bytes = base64.b64decode(content)
            # Try to decode to string
            decoded_text = decoded_bytes.decode("utf-8")
            return FileContentResponse(
                repo=f"{owner}/{repo}",
                path=path,
                size=size,
                encoding="utf-8",
                content=decoded_text
            )
        except UnicodeDecodeError:
            # It's a binary file
            return FileContentResponse(
                repo=f"{owner}/{repo}",
                path=path,
                size=size,
                encoding="binary",
                content=None,
                note="Binary file — content not available as text"
            )
    else:
        # If it's returned differently (e.g. submodule or symlink)
        return FileContentResponse(
            repo=f"{owner}/{repo}",
            path=path,
            size=size,
            encoding=encoding or "unknown",
            content=content if content else None,
            note=None if content else "No content available"
        )
