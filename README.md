# idea-inbox

Turn shower thoughts into structured GitHub issues — just message your bot.

Send a rough idea to your Discord or Telegram bot and idea-inbox uses an LLM to give it a title, summary, and tags, then files it as a GitHub issue automatically.

---

## Getting started

**You'll need:**
- Docker + Docker Compose
- A GitHub repo and a [personal access token](https://github.com/settings/tokens) with Issues write permission
- An LLM API key — Gemini recommended ([free tier available](https://aistudio.google.com/app/apikey))
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications)) or a Telegram bot token ([@BotFather](https://t.me/botfather))

**Then:**

```bash
./quickstart.sh
docker compose up -d
```

That's it. Message your bot and watch the issues appear.

---

## Advanced

### Use a local LLM with Ollama

Start Ollama alongside the stack:

```bash
docker compose -f docker-compose.yml -f docker-compose.ollama.yml up -d
docker compose exec ollama ollama pull phi3:mini
```

Then set these in `.env.backend`:

```bash
LLM_PROVIDER=ollama
OLLAMA_API_BASE=http://ollama:11434
OLLAMA_MODEL=phi3:mini
```

Model data is persisted in the `ollama-data` volume across restarts.

