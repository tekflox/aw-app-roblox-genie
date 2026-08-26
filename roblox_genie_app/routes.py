"""This app's backend sub-app, mounted by the runtime at
``/api/apps/roblox-genie`` behind the workspace's IdentityGuard.

The real credential goes to ``ctx.secrets`` via ``POST /settings``, never
through the generic config path (which would land it in plain,
cloud-syncable app config) -- same split as aw-app-roblox's
roblox_pilot_backend_api_key.
"""
from __future__ import annotations

from fastapi import Body, FastAPI, Request
from fastapi.responses import JSONResponse, Response

from . import config, mcp_config
from .mcp import aw_roblox_genie_server

SECRET_KEYS = (config.PILOT_BACKEND_API_KEY,)


def build_routes(ctx) -> FastAPI:
    app = FastAPI(title="roblox-genie")

    @app.get("/status")
    async def status() -> dict:
        return {
            "pilot_backend_configured": bool(config.pilot_backend_api_key()),
            "pilot_backend_url": config.pilot_backend_url(),
            "logged_in": bool(config.pilot_backend_api_key()),
            "tools": [t["name"] for t in aw_roblox_genie_server.TOOLS_SCHEMA],
        }

    @app.post("/settings")
    async def save_settings(data: dict = Body(...)) -> dict:
        saved = []
        for key in SECRET_KEYS:
            value = (data.get(key) or "").strip()
            if value:
                ctx.secrets.write(key, value)
                saved.append(key)
        if not saved:
            return JSONResponse(
                {"ok": False, "error": f"none of {SECRET_KEYS} were provided"},
                status_code=400,
            )
        return {"ok": True, "saved": saved}

    @app.post("/logout")
    async def clear_secrets(data: dict = Body(default={})) -> dict:
        keys = data.get("keys") or list(SECRET_KEYS)
        for key in keys:
            if key in SECRET_KEYS:
                ctx.secrets.delete(key)
        return {"ok": True, "cleared": keys}

    @app.get("/mcp.json")
    async def mcp_json() -> dict:
        return {"mcpServers": mcp_config.build_mcp_servers()}

    @app.post("/mcp")
    async def mcp_post(request: Request):
        data = await request.json()
        messages = data if isinstance(data, list) else [data]
        responses = []
        for m in messages:
            r = await aw_roblox_genie_server.handle_request(m)
            if r is not None:
                responses.append(r)
        if not responses:
            return Response(status_code=202)
        return JSONResponse(responses if isinstance(data, list) else responses[0])

    @app.get("/mcp")
    async def mcp_get():
        return Response(status_code=405)

    return app
