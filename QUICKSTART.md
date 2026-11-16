# Run EEOC Explore locally

Open the directory containing this file and pyproject.toml. With uv installed, run:

```powershell
uv sync --locked
uv run python scripts/demo.py
uv run pytest -q
```

For interactive chat, use the stdio client configuration and the three demo questions in [README.md](README.md). The demo script runs a local MCP client and server.
