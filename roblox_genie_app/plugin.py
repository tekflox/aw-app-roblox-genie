"""Entrypoint referenced by aw-app.json's ``runtime.entrypoint``
("roblox_genie_app.plugin:RobloxGenieAppPlugin").

Same shape as aw-app-roblox: no subprocess, no venv, no port beyond this
process's own. The MCP server is served in-process over HTTP (see
``mcp_config.py`` / ``routes.py``); ``ctx.config``/``ctx.secrets`` are
resolved through callables (:mod:`roblox_genie_app.config`) rather than
read once, so a value saved in Settings takes effect on the very next
tool call with no restart and no gateway reload.
"""
from __future__ import annotations

import logging
import os

from . import config, mcp_config, routes as routes_mod

log = logging.getLogger("aw_apps.roblox_genie")


class RobloxGenieAppPlugin:
    async def activate(self, ctx) -> None:
        self.ctx = ctx

        config.install_resolvers(
            lambda: getattr(ctx, "config", {}) or {},
            lambda name: ctx.secrets.read(name),
        )

        ctx.routes.register(routes_mod.build_routes(ctx))

        port = int(os.environ.get("AW_PORT") or 9030)
        # Rebuilt every boot rather than persisted: the entry embeds this
        # process's hostname, which changes when the workspace container
        # is recreated.
        doc = mcp_config.write_mcp_json(ctx.package_dir, port)

        log.info(
            "aw-app-roblox-genie activated: mcp servers=%s, pilot backend key=%s",
            sorted(doc["mcpServers"]),
            "saved" if config.pilot_backend_api_key() else "NOT SET",
        )

    async def deactivate(self) -> None:
        log.info("aw-app-roblox-genie deactivated")
