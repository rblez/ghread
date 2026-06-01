"""MCP-compatible JSON-RPC endpoint for ghread.

Implements the Model Context Protocol (Streamable HTTP transport)
using the existing ghread fetcher functions, without external dependencies.
"""

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

TOOLS = [
    {
        "name": "read_repo_index",
        "description": "Get full repository metadata, recursive file tree, branches list, and README content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "Repository in owner/name format",
                },
                "ref": {
                    "type": "string",
                    "description": "Branch/tag/commit (optional)",
                },
            },
            "required": ["repo"],
        },
    },
    {
        "name": "read_file",
        "description": "Read a single file's content. Returns utf-8 decoded text or binary flag.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "Repository in owner/name format",
                },
                "path": {
                    "type": "string",
                    "description": "File path within the repository",
                },
                "ref": {
                    "type": "string",
                    "description": "Branch/tag/commit (optional)",
                },
            },
            "required": ["repo", "path"],
        },
    },
    {
        "name": "list_issues",
        "description": "List issues in a repository.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "Repository in owner/name format",
                },
                "state": {
                    "type": "string",
                    "enum": ["open", "closed", "all"],
                    "default": "open",
                },
                "sort": {
                    "type": "string",
                    "enum": ["created", "updated", "comments"],
                    "default": "created",
                },
                "direction": {
                    "type": "string",
                    "enum": ["asc", "desc"],
                    "default": "desc",
                },
                "per_page": {"type": "integer", "default": 20},
            },
            "required": ["repo"],
        },
    },
    {
        "name": "list_pull_requests",
        "description": "List pull requests in a repository.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "Repository in owner/name format",
                },
                "state": {
                    "type": "string",
                    "enum": ["open", "closed", "all"],
                    "default": "open",
                },
                "sort": {
                    "type": "string",
                    "enum": ["created", "updated", "popularity"],
                    "default": "created",
                },
                "direction": {
                    "type": "string",
                    "enum": ["asc", "desc"],
                    "default": "desc",
                },
                "per_page": {"type": "integer", "default": 20},
            },
            "required": ["repo"],
        },
    },
    {
        "name": "list_releases",
        "description": "List releases in a repository.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "Repository in owner/name format",
                },
                "per_page": {"type": "integer", "default": 20},
            },
            "required": ["repo"],
        },
    },
    {
        "name": "list_commits",
        "description": "List recent commits on a branch/ref.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "Repository in owner/name format",
                },
                "ref": {
                    "type": "string",
                    "description": "Branch/tag/commit (optional)",
                },
                "per_page": {"type": "integer", "default": 20},
            },
            "required": ["repo"],
        },
    },
    {
        "name": "list_contributors",
        "description": "List contributors with their commit counts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "Repository in owner/name format",
                },
                "per_page": {"type": "integer", "default": 20},
            },
            "required": ["repo"],
        },
    },
    {
        "name": "list_tags",
        "description": "List git tags with their commit SHA.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "Repository in owner/name format",
                },
                "per_page": {"type": "integer", "default": 20},
            },
            "required": ["repo"],
        },
    },
    {
        "name": "get_languages",
        "description": "Get language breakdown as bytes per language.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "Repository in owner/name format",
                },
            },
            "required": ["repo"],
        },
    },
    {
        "name": "search_code",
        "description": "Search code within a repository.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "Repository in owner/name format",
                },
                "query": {"type": "string", "description": "Search query"},
                "per_page": {"type": "integer", "default": 20},
            },
            "required": ["repo", "query"],
        },
    },
]


def _parse_owner_repo(repo: str) -> tuple[str, str]:
    parts = repo.split("/", 1)
    return parts[0], parts[1]


TOOL_HANDLERS = {
    "read_repo_index": lambda args: fetch_repo_index(
        *_parse_owner_repo(args["repo"]), args.get("ref")
    ),
    "read_file": lambda args: fetch_file_content(
        *_parse_owner_repo(args["repo"]), args["path"], args.get("ref")
    ),
    "list_issues": lambda args: fetch_issues(
        *_parse_owner_repo(args["repo"]),
        args.get("state", "open"),
        args.get("sort", "created"),
        args.get("direction", "desc"),
        args.get("per_page", 20),
    ),
    "list_pull_requests": lambda args: fetch_pulls(
        *_parse_owner_repo(args["repo"]),
        args.get("state", "open"),
        args.get("sort", "created"),
        args.get("direction", "desc"),
        args.get("per_page", 20),
    ),
    "list_releases": lambda args: fetch_releases(
        *_parse_owner_repo(args["repo"]), args.get("per_page", 20)
    ),
    "list_commits": lambda args: fetch_commits(
        *_parse_owner_repo(args["repo"]), args.get("ref"), args.get("per_page", 20)
    ),
    "list_contributors": lambda args: fetch_contributors(
        *_parse_owner_repo(args["repo"]), args.get("per_page", 20)
    ),
    "list_tags": lambda args: fetch_tags(
        *_parse_owner_repo(args["repo"]), args.get("per_page", 20)
    ),
    "get_languages": lambda args: fetch_languages(*_parse_owner_repo(args["repo"])),
    "search_code": lambda args: fetch_search_code(
        *_parse_owner_repo(args["repo"]), args["query"], args.get("per_page", 20)
    ),
}


async def handle_mcp_request(body: dict) -> dict:
    method = body.get("method", "")
    msg_id = body.get("id")
    params = body.get("params", {}) or {}
    arguments = params.get("arguments", {}) if isinstance(params, dict) else {}

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": TOOLS},
        }

    if method == "tools/call":
        tool_name = arguments.get("name", params.get("name", ""))
        tool_args = arguments.get("arguments", params.get("arguments", {}))

        handler = TOOL_HANDLERS.get(tool_name)
        if not handler:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
            }

        try:
            result = await handler(tool_args)
            data = result.model_dump() if hasattr(result, "model_dump") else result
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": str(data)}],
                },
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32000, "message": str(e)},
            }

    if method in ("initialize",):
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "ghread", "version": "1.0.0"},
            },
        }

    if method in ("notifications/initialized", "ping"):
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }
