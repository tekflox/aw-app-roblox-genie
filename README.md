# aw-app-roblox-genie

The lamp-genie NPC any player can chat with in the aw-roblox game. Split
out of `aw-app-roblox` (2026-08-26) so the surface a random player's chat
message can reach never shares a package/permission boundary with
Frederico's own full-power tools (`scale_object`, `kick_players`,
`set_lighting`, the full Kanban board).

## What this app ships

- **MCP upstream `aw-roblox-genie`** (`aw__aw_roblox_genie__*` on the
  gateway, route `/api/apps/roblox-genie/mcp`) — 16 tools:
  `create_genie_card`/`list_genie_cards` (hard-filtered to
  `source=roblox-genie` cards only) + 14 of `npc_control`'s 17 tools
  (never `scale_object`/`kick_players`/`set_lighting` — enforced by a
  module-load-time assertion in `roblox_genie_app/mcp/aw_roblox_genie_server.py`
  and `genie_npc_control.py`, not just an access-control list).
- **Skill** `aw-roblox-genie` — persona + full tool-usage rules.
- **Agent** `roblox-genie` (seeded via `contributes.agents`) — model,
  agent config, group and the agent itself, ready for Agents Platform.

## Before dispatching the `roblox-genie` agent for real

`agent_configs.roblox-genie-config.mcp_servers` ships **empty on
purpose**, not `["aw-gateway"]`. Pointing it at the full gateway would
undo the entire reason this app exists — a chat-injectable NPC would
gain every tool on the gateway, not just its own 16.

The gateway supports named, scoped configs for exactly this
(`ConfigGateway` in `aw-mcp-gateway/back/gateway/server.py`, driven by a
`configs` section in `config/gateway.json`) — not yet exercised in this
workspace. Steps to wire it before the persona goes live:

1. Add to `gateway.json`'s `configs`: `"roblox-genie": {"upstreams": ["aw-roblox-genie"]}`
2. Restart the gateway; it exposes `/mcp/roblox-genie` scoped to only that upstream
3. Reference `"roblox-genie"` (not `"aw-gateway"`) in this app's
   `agent_configs[0].mcp_servers`

## Shared secret with aw-app-roblox

`genie_npc_control` reuses the exact same `roblox-pilot-backend` API
calls as aw-app-roblox's full `npc_control` — same live game, same
backend. Because each app owns its own secret store, the same
`roblox_pilot_backend_api_key` has to be pasted into **both** apps'
Settings after install.

## Where the actual chat pipeline lives

Not here. `GenieDialogue.client.lua` → `GenieNPC.server.lua` →
`roblox-pilot-backend` still calls the *legacy* agents-platform in
agentic-workspace/bare-metal, not this app's seeded agent. Migrating that
pipeline to point at the agent this app seeds is a separate follow-up.
