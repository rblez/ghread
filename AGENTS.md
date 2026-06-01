# ghread

**Repo**: `rblez/ghread` — FastAPI proxy that fetches GitHub repo trees and file contents for AI agents.

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
  -> app/github/fetcher.py  Business logic: fetch_repo_index(), fetch_file_content()
  -> app/github/client.py   GitHubClient — async httpx to api.github.com
  -> app/models/responses.py Pydantic models
```

- Single-package Python project under `app/`. Not a monorepo.
- Auth: `Authorization: Bearer <key>` header or `?key=<key>` query param. If `API_KEY` is empty, auth is skipped (`app/main.py:28-53`).
- CORS allows all origins.
- `GitHubClient` opens a new `httpx.AsyncClient` per call (no connection pooling).
- No database, no caching, no rate limiting, no structured logging — despite README claims.

---

## API endpoints

All endpoints accept `?key=<key>` or `Authorization: Bearer <key>` if `API_KEY` is configured.

### Implemented

#### `GET /?repo=<owner/repo>`
Returns repo metadata, full recursive git tree, branches, and README.
- Optional: `&ref=<branch/tag/commit>` — defaults to the repo's default branch.
- Response: `RepoIndexResponse` (`repo` metadata, `tree[]`, `branches[]`, `readme?`).

#### `GET /?repo=<owner/repo>&path=<filepath>`
Returns a single file's content.
- Optional: `&ref=<branch/tag/commit>`.
- Decodes base64 content. Returns `encoding:"utf-8"` with decoded text, or `encoding:"binary"` with `content:null` and a `note` for binary files.
- Response: `FileContentResponse` (`repo`, `path`, `size`, `encoding`, `content?`, `note?`).

#### `GET /health`
Returns `{"status":"ok","version":"1.0.0"}`.

### Documented but not implemented

These are listed in the README but have **no route, no handler, no model** in code:

| Endpoint | What it should do |
|---|---|
| `GET /issues?repo=<owner/repo>` | List open issues (title, state, created_at) |
| `GET /releases?repo=<owner/repo>` | List releases (tag, name, body) |
| `GET /commits?repo=<owner/repo>&ref=<branch>` | List latest 20 commits on the given ref |

---

## Key files

| File | Role |
|---|---|
| `app/main.py:9-13` | FastAPI app creation, title/description/version |
| `app/main.py:16-22` | CORS middleware (allows all origins) |
| `app/main.py:28-53` | `verify_api_key()` security dependency |
| `app/main.py:55-91` | `GET /` handler with `repo`, `path`, `ref` params |
| `app/main.py:93-95` | `GET /health` |
| `app/github/client.py:15-18` | `get_repo()` — single httpx call to GitHub REST |
| `app/github/client.py:21-24` | `get_branches()` |
| `app/github/client.py:27-32` | `get_tree()` with optional recursive param |
| `app/github/client.py:35-42` | `get_file_content()` — GitHub contents API |
| `app/github/client.py:45-70` | `get_readme()` — handles 404, base64 decode, download_url fallback |
| `app/github/client.py:72` | Module-level singleton `github_client` |
| `app/github/fetcher.py:6-56` | `fetch_repo_index()` — repo meta + branches + tree + readme |
| `app/github/fetcher.py:58-98` | `fetch_file_content()` — decode base64, detect binary via UnicodeDecodeError |
| `app/models/responses.py:4-14` | `RepoMetadata` model |
| `app/models/responses.py:16-19` | `TreeItem` model (path, type, size?) |
| `app/models/responses.py:21-25` | `RepoIndexResponse` model |
| `app/models/responses.py:27-33` | `FileContentResponse` model |
| `app/models/responses.py:35-37` | `HealthResponse` model |
| `app/config.py:4-11` | `Settings` class — reads env vars via `os.getenv`, calls `load_dotenv()` at module level |
| `pyproject.toml:7-13` | Runtime deps: fastapi, uvicorn, httpx, python-dotenv, pydantic |
| `pyproject.toml:16-21` | Dev deps: ruff, black, mypy, pytest, pytest-cov |
| `Dockerfile` | Multi-stage, uses `ghcr.io/astral-sh/uv`, exposes 8080 |
| `.github/workflows/ci.yml` | CI: ruff -> black --check -> mypy -> pytest --cov=app -> docker build |
| `.github/workflows/release.yml` | On `v*` tag: docker build + push to ghcr.io + `railway up` |
| `railway.toml` | Deploys via Dockerfile, starts with `uvicorn app.main:app` |

---

## Gotchas

- **No tests exist.** `pytest --cov=app` returns 0% coverage. Any new feature requires tests from scratch. Put tests in `tests/` at the repo root.
- **`.env` is committed** with live secrets. Do not commit changes to it. High priority: add `.env` to `.gitignore` and rotate the secrets.
- **`uv` is the package manager.** Never use `pip install`. The `requirements.txt` is a stale legacy file — ignore it. Run `uv sync` to install deps, `uv add <pkg>` to add one, `uv lock` to update lockfile.
- **`build/` directory** is a stale artifact from `pip install -e .`. Ignore it. All source is under `app/`.
- **Python 3.12+** required. CI runs 3.12 specifically.
- **Async client reuse**: `GitHubClient` creates a new `httpx.AsyncClient` in every method — no connection pooling. Can be improved but don't break the existing public API.
- **No type stubs for httpx** — mypy may complain if you use `httpx` internals. Either ignore or add `# type: ignore` on specific lines.
- **Branch strategy**: CI triggers on push/PR to `dev` or `main`. Releases trigger on `v*` tags. Do not push directly to `main` — use feature branches and PR to `dev` or `main`.
