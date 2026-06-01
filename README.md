# GHread

**Repo**: `rblez/ghread` — FastAPI proxy that fetches GitHub repo data for AI agents.

---

## Setup

```bash
uv sync                           # install all deps (runtime + dev)
cp .env.example .env              # then edit GITHUB_TOKEN and API_KEY
uv run uvicorn app.main:app --reload --port 8000   # dev server
```

Config loads from `.env` at import time (`app/config.py:4`). See `.env.example` for the 3 vars (`GITHUB_TOKEN`, `API_KEY`, `PORT`).

---

## Validation commands (run in order, CI enforces this)

| Step | Command |
|---|---|
| Lint | `uv run ruff check .` |
| Format | `uv run black --check .` |
| Type check | `uv run mypy .` |
| Test | `uv run pytest --cov=app` |
| Docker build | `docker build -t ghread-api:ci .` |

---

## Architecture

```
HTTP request
  -> app/main.py          FastAPI app, routes, verify_api_key()
  -> app/github/fetcher.py  Business logic — transforms GitHub API data into response models
  -> app/github/client.py   GitHubClient — async httpx to api.github.com
  -> app/models/responses.py Pydantic models
```

- Single-package Python under `app/`. Not a monorepo.
- Auth: `Authorization: Bearer <key>` header or `?key=<key>` query param. If `API_KEY` is empty, auth is skipped (`app/main.py:28-53`).
- CORS allows all origins.
- `GitHubClient` opens a new `httpx.AsyncClient` per call (no connection pooling).
- No database, no caching, no rate limiting, no structured logging.

---

## API endpoints

All endpoints accept `?key=<key>` or `Authorization: Bearer <key>` if `API_KEY` is configured. `repo` must be `owner/repo` format.

### Repo data

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Repo index: metadata + recursive git tree + branches + README |
| GET | `/?path=<filepath>` | Single file content (utf-8 decoded or binary flag) |
| GET | `/languages` | Language breakdown `{ "Python": 5000, "Go": 2000 }` |

Params: `repo` (required), `ref` (optional, branch/tag/commit).

### Collaboration data

| Method | Endpoint | Description |
|---|---|---|
| GET | `/issues` | Open issues (title, state, labels, body) |
| GET | `/pulls` | Pull requests (title, state, head/base ref, draft flag) |
| GET | `/commits` | Recent commits (sha, message, author, date) |
| GET | `/contributors` | Contributors with commit count |

Params: `repo` (required), `state` (default `open`), `sort` (default `created`), `direction` (default `desc`), `per_page` (default 20), `ref` (commits only).

### Releases & tags

| Method | Endpoint | Description |
|---|---|---|
| GET | `/releases` | Releases (tag_name, name, body, prerelease) |
| GET | `/tags` | Git tags (name, commit_sha) |

Params: `repo` (required), `per_page` (default 20).

### Search

| Method | Endpoint | Description |
|---|---|---|
| GET | `/search/code` | Search code within the repo |

Params: `repo` (required), `q` (search query), `per_page` (default 20).

### System

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | `{"status":"ok","version":"1.0.0"}` |

---

## Key files

| File | Role |
|---|---|
| `app/main.py:9-13` | FastAPI app creation, title/description/version |
| `app/main.py:16-22` | CORS middleware (allows all origins) |
| `app/main.py:28-67` | `verify_api_key()` security dependency + `_parse_repo()` + `_handle_github_error()` |
| `app/main.py:69-91` | `GET /` — repo index or file content |
| `app/main.py:93-177` | `GET /issues`, `/pulls`, `/releases`, `/commits`, `/contributors`, `/tags`, `/languages`, `/search/code` |
| `app/main.py:179-181` | `GET /health` |
| `app/github/client.py:17-18` | `_get()` / `_get_list()` — shared httpx helpers |
| `app/github/client.py:20-59` | `get_repo()`, `get_branches()`, `get_tree()`, `get_file_content()`, `get_readme()` — original methods |
| `app/github/client.py:61-111` | `get_issues()`, `get_pulls()`, `get_releases()`, `get_commits()`, `get_contributors()`, `get_tags()`, `get_languages()`, `search_code()` |
| `app/github/client.py:113` | Module-level singleton `github_client` |
| `app/github/fetcher.py:9-58` | `fetch_repo_index()` — repo meta + branches + tree + readme |
| `app/github/fetcher.py:60-97` | `fetch_file_content()` — decode base64, detect binary via UnicodeDecodeError |
| `app/github/fetcher.py:99-168` | `fetch_issues()`, `fetch_pulls()`, `fetch_releases()`, `fetch_commits()`, `fetch_contributors()`, `fetch_tags()`, `fetch_languages()` |
| `app/github/fetcher.py:170-193` | `search_code()` — builds `repo:owner/repo+query` and transforms results |
| `app/models/responses.py:4-14` | `RepoMetadata` model |
| `app/models/responses.py:16-19` | `TreeItem` model (path, type, size?) |
| `app/models/responses.py:21-25` | `RepoIndexResponse` model |
| `app/models/responses.py:27-33` | `FileContentResponse` model |
| `app/models/responses.py:35-37` | `HealthResponse` model |
| `app/models/responses.py:39-97` | `IssueItem`/`IssuesResponse`, `PullRequestItem`/`PullsResponse`, `ReleaseItem`/`ReleasesResponse`, `CommitItem`/`CommitsResponse`, `ContributorItem`/`ContributorsResponse`, `TagItem`/`TagsResponse`, `LanguagesResponse`, `SearchCodeItem`/`SearchCodeResponse` |
| `app/config.py:4-11` | `Settings` class — reads env vars via `os.getenv`, calls `load_dotenv()` at module level |
| `pyproject.toml:7-13` | Runtime deps: fastapi, uvicorn, httpx, python-dotenv, pydantic |
| `pyproject.toml:16-22` | Dev deps: ruff, black, mypy, pytest, pytest-cov, pytest-asyncio |
| `tests/` | Test suite — 14 tests covering all endpoints + error handling |
| `Dockerfile` | Multi-stage, uses `ghcr.io/astral-sh/uv`, exposes 8080 |
| `.github/workflows/ci.yml` | CI: ruff -> black --check -> mypy -> pytest --cov=app -> docker build |
| `.github/workflows/release.yml` | On `v*` tag: docker build + push to ghcr.io + `railway up` |
| `railway.toml` | Deploys via Dockerfile, starts with `uvicorn app.main:app` |

---

## Gotchas

- **No tests existed before this work.** `pytest --cov=app` now targets 74%+. Put new tests in `tests/`.
- **`.env` is committed** with live secrets. Do not commit changes to it. High priority: add `.env` to `.gitignore` and rotate the secrets.
- **`uv` is the package manager.** Never use `pip install`. The `requirements.txt` is a stale legacy file — ignore it. Run `uv sync` to install deps, `uv add <pkg>` to add one, `uv lock` to update lockfile.
- **`build/` directory** is a stale artifact from `pip install -e .`. Ignore it. All source is under `app/`.
- **Python 3.12+** required. CI runs 3.12 specifically.
- **Async client reuse**: `GitHubClient` creates a new `httpx.AsyncClient` in every method — no connection pooling. Can be improved but don't break the existing public API.
- **No type stubs for httpx** — mypy may complain if you use `httpx` internals. Either ignore or add `# type: ignore` on specific lines.
- **Branch strategy**: CI triggers on push/PR to `dev` or `main`. Releases trigger on `v*` tags. Do not push directly to `main` — use feature branches and PR to `dev` or `main`.
- **Tests disable auth**: The `conftest.py` fixture `_no_auth` sets `settings.API_KEY = ""` so tests don't need real credentials.
- **Tests use `httpx.ASGITransport`**: FastAPI's `TestClient` is not used. Tests use `httpx.AsyncClient` with `ASGITransport(app=app)` for async requests.
