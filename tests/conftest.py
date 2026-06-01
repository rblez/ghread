import os
import pytest
from unittest.mock import AsyncMock, patch

from app.config import settings


# Clear API_KEY so tests don't require auth
@pytest.fixture(autouse=True)
def _no_auth():
    original = settings.API_KEY
    settings.API_KEY = ""
    yield
    settings.API_KEY = original


@pytest.fixture
def mock_github_client():
    with patch("app.github.fetcher.github_client") as mock:
        mock.get_repo = AsyncMock()
        mock.get_branches = AsyncMock()
        mock.get_tree = AsyncMock()
        mock.get_file_content = AsyncMock()
        mock.get_readme = AsyncMock()
        mock.get_issues = AsyncMock()
        mock.get_pulls = AsyncMock()
        mock.get_releases = AsyncMock()
        mock.get_commits = AsyncMock()
        mock.get_contributors = AsyncMock()
        mock.get_tags = AsyncMock()
        mock.get_languages = AsyncMock()
        mock.search_code = AsyncMock()
        yield mock


def make_issue(number, title="Test Issue", state="open", labels=None):
    return {
        "number": number,
        "title": title,
        "state": state,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
        "closed_at": None,
        "labels": [{"name": l} for l in (labels or [])],
        "body": "Body text",
        "user": {"login": "testuser"},
        "html_url": f"https://github.com/owner/repo/issues/{number}",
    }


def make_pr(number, title="Test PR", state="open"):
    return {
        "number": number,
        "title": title,
        "state": state,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
        "merged_at": None,
        "body": "PR body",
        "user": {"login": "testuser"},
        "head": {"ref": "feature"},
        "base": {"ref": "main"},
        "draft": False,
        "html_url": f"https://github.com/owner/repo/pull/{number}",
    }


def make_release(tag="v1.0.0"):
    return {
        "tag_name": tag,
        "name": f"Release {tag}",
        "body": "Release notes",
        "prerelease": False,
        "created_at": "2024-01-01T00:00:00Z",
        "published_at": "2024-01-02T00:00:00Z",
        "html_url": f"https://github.com/owner/repo/releases/tag/{tag}",
    }


def make_commit(sha="abc123"):
    return {
        "sha": sha,
        "commit": {
            "message": "fix: something",
            "author": {
                "name": "Test User",
                "email": "test@user.com",
                "date": "2024-01-01T00:00:00Z",
            },
        },
        "author": {"login": "testuser"},
        "html_url": f"https://github.com/owner/repo/commit/{sha}",
    }
