# Tools

This repository includes a Discord control-layer bot built with **discord.js v14**, **axios**, **better-sqlite3**, and **archiver**. The bot orchestrates access to an Open WebUI-backed AI assistant and focuses on deterministic, auditable interactions.

## Discord Bot

### Capabilities
- Listens to **guild messages only**, ignores DMs/bots, and responds **only when mentioned**.
- Per-channel controls persisted in SQLite: listening toggle, prompt type, and allowed intents.
- Intent routing via `qwen2.5-3b-instruct:free` into chat/code/tool/admin/search before calling Open WebUI.
- Admin gating by Discord role name `ADMIN`; destructive admin commands need a 30s confirmation reply.
- Dynamic system prompts: immutable base + channel prompt + immutable safety block.
- Model routing: chat → `openai/gpt-oss-120b:free`, code → `starcoder-3b:free`, tool/admin → `mistral-7b-instruct:free`, search → `openai/gpt-oss-120b:free`.
- File outputs from Open WebUI are saved to temp files (zipped when multiple) and uploaded as attachments.

### Setup
1. Install dependencies (captured in `package-lock.json`):
   ```bash
   npm install
   ```
2. Provide environment variables:
   - `DISCORD_BOT_TOKEN` (required)
   - `OPENWEBUI_BASE_URL` (default `http://localhost:3000`)
   - `OPENWEBUI_API_KEY` (optional bearer token)
   - `OPENWEBUI_TIMEOUT_MS` (default `15000`)
   - `BOT_DB_PATH` (default `./data/discord-bot.sqlite`)
   - `AUDIT_LOG_PATH` (default `./data/discord_audit.log`)

### Run
```bash
npm start
```

### How to use
- Mention the bot in a guild text channel: `@BotName help me debug this error`.
- Admins can toggle channel listening with `@BotName listen on/off`.
- Destructive admin commands trigger a confirmation; reply `@BotName confirm` within 30 seconds to proceed.
- The bot replies in-channel and attaches any returned files (zipped when multiple, up to 8 MB).
