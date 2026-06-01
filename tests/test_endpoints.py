import pytest
import base64
import httpx
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_invalid_repo_format(client):
    resp = await client.get("/?repo=bad")
    assert resp.status_code == 400
    assert "owner/repo" in resp.text


@pytest.mark.asyncio
async def test_issues_endpoint(client, mock_github_client):
    mock_github_client.get_issues.return_value = [
        {"number": 1, "title": "Bug", "state": "open",
         "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-02T00:00:00Z",
         "closed_at": None, "labels": [{"name": "bug"}], "body": "desc",
         "user": {"login": "user"}, "html_url": "https://github.com/o/r/issues/1"}
    ]
    resp = await client.get("/issues?repo=o/r")
    assert resp.status_code == 200
    data = resp.json()
    assert data["repo"] == "o/r"
    assert data["count"] == 1
    assert data["issues"][0]["title"] == "Bug"
    assert data["issues"][0]["labels"] == ["bug"]


@pytest.mark.asyncio
async def test_pulls_endpoint(client, mock_github_client):
    mock_github_client.get_pulls.return_value = [
        {"number": 1, "title": "Feature", "state": "open",
         "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-02T00:00:00Z",
         "merged_at": None, "body": "desc",
         "user": {"login": "user"},
         "head": {"ref": "feature"}, "base": {"ref": "main"},
         "draft": False,
         "html_url": "https://github.com/o/r/pull/1"}
    ]
    resp = await client.get("/pulls?repo=o/r")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert data["pull_requests"][0]["title"] == "Feature"
    assert data["pull_requests"][0]["head_ref"] == "feature"


@pytest.mark.asyncio
async def test_releases_endpoint(client, mock_github_client):
    mock_github_client.get_releases.return_value = [
        {"tag_name": "v1.0.0", "name": "Release v1.0.0", "body": "notes",
         "prerelease": False, "created_at": "2024-01-01T00:00:00Z",
         "published_at": "2024-01-02T00:00:00Z",
         "html_url": "https://github.com/o/r/releases/tag/v1.0.0"}
    ]
    resp = await client.get("/releases?repo=o/r")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert data["releases"][0]["tag_name"] == "v1.0.0"


@pytest.mark.asyncio
async def test_commits_endpoint(client, mock_github_client):
    mock_github_client.get_commits.return_value = [
        {"sha": "abc123",
         "commit": {"message": "fix: stuff",
                     "author": {"name": "User", "email": "u@c", "date": "2024-01-01T00:00:00Z"}},
         "author": {"login": "user"},
         "html_url": "https://github.com/o/r/commit/abc123"}
    ]
    resp = await client.get("/commits?repo=o/r&ref=main")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert data["commits"][0]["sha"] == "abc123"
    assert data["commits"][0]["author_login"] == "user"
    assert mock_github_client.get_commits.call_args[0][2] == "main"


@pytest.mark.asyncio
async def test_contributors_endpoint(client, mock_github_client):
    mock_github_client.get_contributors.return_value = [
        {"login": "user1", "avatar_url": "https://avatars/1",
         "html_url": "https://github.com/user1", "contributions": 42}
    ]
    resp = await client.get("/contributors?repo=o/r")
    assert resp.status_code == 200
    data = resp.json()
    assert data["contributors"][0]["login"] == "user1"
    assert data["contributors"][0]["contributions"] == 42


@pytest.mark.asyncio
async def test_tags_endpoint(client, mock_github_client):
    mock_github_client.get_tags.return_value = [
        {"name": "v1.0.0", "commit": {"sha": "abc123"}}
    ]
    resp = await client.get("/tags?repo=o/r")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tags"][0]["name"] == "v1.0.0"


@pytest.mark.asyncio
async def test_languages_endpoint(client, mock_github_client):
    mock_github_client.get_languages.return_value = {"Python": 5000, "JavaScript": 2000}
    resp = await client.get("/languages?repo=o/r")
    assert resp.status_code == 200
    data = resp.json()
    assert data["languages"]["Python"] == 5000


@pytest.mark.asyncio
async def test_search_code_endpoint(client, mock_github_client):
    mock_github_client.search_code.return_value = {
        "total_count": 1,
        "items": [
            {"name": "main.py", "path": "app/main.py",
             "html_url": "https://github.com/o/r/blob/main/app/main.py", "sha": "abc"}
        ]
    }
    resp = await client.get("/search/code?repo=o/r&q=import")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_count"] == 1
    assert data["items"][0]["path"] == "app/main.py"
    assert "repo:o/r" in mock_github_client.search_code.call_args[0][0]


@pytest.mark.asyncio
async def test_github_api_error(client, mock_github_client):
    mock_github_client.get_issues.side_effect = httpx.HTTPStatusError(
        "404", request=None, response=httpx.Response(404, json={"message": "Not Found"})
    )
    resp = await client.get("/issues?repo=o/r")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_repo_index_endpoint(client, mock_github_client):
    mock_github_client.get_repo.return_value = {
        "full_name": "o/r", "description": "desc", "default_branch": "main",
        "stargazers_count": 10, "language": "Python", "topics": ["api"],
        "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-02T00:00:00Z",
        "license": {"spdx_id": "MIT"}, "private": False,
    }
    mock_github_client.get_branches.return_value = ["main"]
    mock_github_client.get_tree.return_value = {
        "tree": [{"path": "README.md", "type": "blob", "size": 100}]
    }
    mock_github_client.get_readme.return_value = "# Readme"
    resp = await client.get("/?repo=o/r")
    assert resp.status_code == 200
    data = resp.json()
    assert data["repo"]["full_name"] == "o/r"
    assert data["branches"] == ["main"]
    assert data["readme"] == "# Readme"


@pytest.mark.asyncio
async def test_file_content_endpoint(client, mock_github_client):
    content = base64.b64encode(b"print('hello')").decode()
    mock_github_client.get_file_content.return_value = {
        "size": 14, "encoding": "base64", "content": content
    }
    resp = await client.get("/?repo=o/r&path=main.py")
    assert resp.status_code == 200
    data = resp.json()
    assert data["encoding"] == "utf-8"
    assert "print" in data["content"]


@pytest.mark.asyncio
async def test_binary_file_content(client, mock_github_client):
    content = base64.b64encode(b"\x00\x01\x02\xff").decode()
    mock_github_client.get_file_content.return_value = {
        "size": 4, "encoding": "base64", "content": content
    }
    resp = await client.get("/?repo=o/r&path=file.bin")
    assert resp.status_code == 200
    data = resp.json()
    assert data["encoding"] == "binary"
    assert data["content"] is None
