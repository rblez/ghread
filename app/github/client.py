import httpx
from typing import Dict, Any, List, Optional
from app.config import settings

class GitHubClient:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ghread-api-agent"
        }
        if settings.GITHUB_TOKEN:
            self.headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    async def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(headers=self.headers) as client:
            r = await client.get(f"{self.base_url}/repos/{owner}/{repo}")
            r.raise_for_status()
            return r.json()

    async def get_branches(self, owner: str, repo: str) -> List[str]:
        async with httpx.AsyncClient(headers=self.headers) as client:
            r = await client.get(f"{self.base_url}/repos/{owner}/{repo}/branches")
            r.raise_for_status()
            return [b["name"] for b in r.json()]

    async def get_tree(self, owner: str, repo: str, sha: str, recursive: bool = True) -> Dict[str, Any]:
        async with httpx.AsyncClient(headers=self.headers) as client:
            url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/{sha}"
            params = {"recursive": "1" if recursive else "0"}
            r = await client.get(url, params=params)
            r.raise_for_status()
            return r.json()

    async def get_file_content(self, owner: str, repo: str, path: str, ref: Optional[str] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient(headers=self.headers) as client:
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
            params = {}
            if ref:
                params["ref"] = ref
            r = await client.get(url, params=params)
            r.raise_for_status()
            return r.json()

    async def get_readme(self, owner: str, repo: str, ref: Optional[str] = None) -> Optional[str]:
        async with httpx.AsyncClient(headers=self.headers) as client:
            url = f"{self.base_url}/repos/{owner}/{repo}/readme"
            params = {}
            if ref:
                params["ref"] = ref
            r = await client.get(url, params=params)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            readme_data = r.json()
            # If download_url exists, we can fetch it, or decode from base64
            if "content" in readme_data and readme_data.get("encoding") == "base64":
                import base64
                try:
                    return base64.b64decode(readme_data["content"]).decode("utf-8", errors="ignore")
                except Exception:
                    pass
            
            # fallback to fetching from download_url
            download_url = readme_data.get("download_url")
            if download_url:
                r_dl = await client.get(download_url)
                r_dl.raise_for_status()
                return r_dl.text
            return None

github_client = GitHubClient()
