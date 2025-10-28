Let's run it!

uv run python main.py

It uses standard input/output as transport:

📦 Transport:       STDIO 

Which means, we can paste things into our terminal to test it (and simulate the interaction with the server)


Once its ran - send initialization request:
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {"roots": {"listChanged": true}, "sampling": {}}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}

### Running with HTTP (SSE) transport

The MCP server can also run as an HTTP SSE endpoint. `mcp_faq/main.py` already calls:

```py
# inside mcp_faq/main.py
mcp.run(transport="sse")
```

This exposes the MCP server at:

```
http://localhost:8000/sse
```

How to run the server and the SSE client:

1. Start the server (from the `mcp_faq` folder):

```bash
cd mcp_faq
uv run python main.py
```

2. In another terminal, run the SSE client (from the repo root):

```bash
uv run python test_sse_client.py
```

3. The client uses `pydantic_ai.mcp.MCPServerSSE` and will connect to the server at the SSE URL.

Dependencies (using uv):

```bash
uv init
uv add pydantic-ai[mcp] openai toyaikit
```

Notes:
- Ensure the MCP server is started before running the client.
- If you change the port or path in the server, update the `url` in `test_sse_client.py` accordingly.

