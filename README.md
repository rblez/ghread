# README.md

[![](https://img.shields.io/github/actions/workflow/status/rblez/ghread/ci.yml?branch=main&label=CI&logo=github)](https://github.com/rblez/ghread/actions)
[![](https://img.shields.io/github/v/tag/rblez/ghread?label=version)](https://github.com/rblez/ghread/releases)
[![](https://img.shields.io/github/license/rblez/ghread)](https://github.com/rblez/ghread/blob/main/LICENSE)

# ghread – GitHub Repo Reader API

**A fast, production‑ready REST proxy written in Python 3.12 + FastAPI, powered by `uv`.**

It enables AI agents (or any client) to fetch an entire repository structure and file contents without needing direct GitHub access.

---

## ✨ Features

- **Two‑step consumption** – first fetch the repo index (tree), then request individual files on demand.
- **Full GitHub data** – supports **issues**, **releases**, **commits** and branch listings.
- **Secure API key** – protect the public endpoint with a custom `API_KEY`.
- **Async & ultra‑fast** – built on `httpx` + `uv` for rapid dependency installation.
- **Docker & Railway ready** – multi‑stage Dockerfile, `railway.toml`, and CI workflow.
- **Rate limiting** – 60 requests per minute per IP, with `X‑RateLimit‑Remaining` header.
- **In‑memory cache** – tree and file responses cached for 5 minutes.
- **Structured logging** – `loguru` outputs JSON‑compatible logs.
- **Comprehensive CI** – lint (`ruff`), format (`black`), type checking (`mypy`), tests (`pytest`), and Docker build.

---

## 📦 Quick start (local)

```bash
# clone the repo
git clone https://github.com/rblez/ghread.git && cd ghread

# copy the example env and set your secrets
cp .env.example .env
# edit .env → add GITHUB_TOKEN and API_KEY

# install uv (if not already)
curl -LsSf https://astral.sh/uv/install.sh | sh

# install deps and run
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs for the OpenAPI UI.

---

## 🚀 Deploy to Railway

1. Create a new project on Railway and link the GitHub repository `rblez/ghread`.
2. Add the following **Environment Variables** in Railway:
   - `GITHUB_TOKEN` – your personal access token (read‑only).
   - `API_KEY` – secret token for your clients.
   - `PORT` – default `8000` (Railway will override automatically).
3. Railway will detect the `Dockerfile` and build the image automatically.

---

## 🔗 API Endpoints

| Endpoint | Description |
|---|---|
| `GET /?repo=<owner/repo>` | Returns repo metadata, full tree, branches, and README. |
| `GET /?repo=<owner/repo>&path=<file>` | Returns the complete file content (utf‑8 or binary flag). |
| `GET /issues?repo=<owner/repo>` | List open issues (title, state, created_at). |
| `GET /releases?repo=<owner/repo>` | List releases (tag, name, body). |
| `GET /commits?repo=<owner/repo>&ref=<branch>` | List latest 20 commits on the given ref. |
| `GET /health` | Health check. |

All endpoints require the API key either via `Authorization: Bearer <key>` header **or** `?key=<key>` query param.

---

## 🧪 Running tests

```bash
uv run pytest
```

Test coverage is enforced at **≥85 %**.

---

## 📚 Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to propose changes, run tests, and submit pull requests.

---

## 📜 License

MIT – see the [LICENSE](LICENSE) file for details.
