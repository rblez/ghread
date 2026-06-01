import httpx
from typing import Dict, Any, List, Optional
from app.config import settings


class GitHubClient:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ghread-api-agent",
        }
        if settings.GITHUB_TOKEN:
            self.headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    async def _get(
        self, url: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(headers=self.headers) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            return r.json()

    async def _get_list(
        self, url: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        async with httpx.AsyncClient(headers=self.headers) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            return r.json()

    async def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        return await self._get(f"{self.base_url}/repos/{owner}/{repo}")

    async def get_branches(self, owner: str, repo: str) -> List[str]:
        data = await self._get_list(f"{self.base_url}/repos/{owner}/{repo}/branches")
        return [b["name"] for b in data]

    async def get_tree(
        self, owner: str, repo: str, sha: str, recursive: bool = True
    ) -> Dict[str, Any]:
        params = {"recursive": "1" if recursive else "0"}
        return await self._get(
            f"{self.base_url}/repos/{owner}/{repo}/git/trees/{sha}", params=params
        )

    async def get_file_content(
        self, owner: str, repo: str, path: str, ref: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {}
        if ref:
            params["ref"] = ref
        return await self._get(
            f"{self.base_url}/repos/{owner}/{repo}/contents/{path}", params=params
        )

    async def get_readme(
        self, owner: str, repo: str, ref: Optional[str] = None
    ) -> Optional[str]:
        params = {}
        if ref:
            params["ref"] = ref
        async with httpx.AsyncClient(headers=self.headers) as client:
            r = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/readme", params=params
            )
            if r.status_code == 404:
                return None
            r.raise_for_status()
            readme_data = r.json()
            if "content" in readme_data and readme_data.get("encoding") == "base64":
                import base64

                try:
                    return base64.b64decode(readme_data["content"]).decode(
                        "utf-8", errors="ignore"
                    )
                except Exception:
                    pass
            download_url = readme_data.get("download_url")
            if download_url:
                r_dl = await client.get(download_url)
                r_dl.raise_for_status()
                return r_dl.text
            return None

    async def get_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        sort: str = "created",
        direction: str = "desc",
        per_page: int = 20,
    ) -> List[Any]:
        params = {
            "state": state,
            "sort": sort,
            "direction": direction,
            "per_page": str(per_page),
        }
        return await self._get_list(
            f"{self.base_url}/repos/{owner}/{repo}/issues", params=params
        )

    async def get_pulls(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        sort: str = "created",
        direction: str = "desc",
        per_page: int = 20,
    ) -> List[Any]:
        params = {
            "state": state,
            "sort": sort,
            "direction": direction,
            "per_page": str(per_page),
        }
        return await self._get_list(
            f"{self.base_url}/repos/{owner}/{repo}/pulls", params=params
        )

    async def get_releases(
        self, owner: str, repo: str, per_page: int = 20
    ) -> List[Any]:
        params = {"per_page": str(per_page)}
        return await self._get_list(
            f"{self.base_url}/repos/{owner}/{repo}/releases", params=params
        )

    async def get_commits(
        self, owner: str, repo: str, ref: Optional[str] = None, per_page: int = 20
    ) -> List[Any]:
        params = {"per_page": str(per_page)}
        if ref:
            params["sha"] = ref
        return await self._get_list(
            f"{self.base_url}/repos/{owner}/{repo}/commits", params=params
        )

    async def get_contributors(
        self, owner: str, repo: str, per_page: int = 20
    ) -> List[Any]:
        params = {"per_page": str(per_page)}
        return await self._get_list(
            f"{self.base_url}/repos/{owner}/{repo}/contributors", params=params
        )

    async def get_tags(self, owner: str, repo: str, per_page: int = 20) -> List[Any]:
        params = {"per_page": str(per_page)}
        return await self._get_list(
            f"{self.base_url}/repos/{owner}/{repo}/tags", params=params
        )

    async def get_languages(self, owner: str, repo: str) -> Dict[str, int]:
        return await self._get(f"{self.base_url}/repos/{owner}/{repo}/languages")

    async def search_code(self, query: str, per_page: int = 20) -> Dict[str, Any]:
        params = {"q": query, "per_page": str(per_page)}
        return await self._get(f"{self.base_url}/search/code", params=params)


github_client = GitHubClient()
