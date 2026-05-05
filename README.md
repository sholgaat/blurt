# blurt 🤖

Never forget a project idea again!

Turn shower thoughts into structured GitHub issues with 0 friction — just message your bot.

Send a rough idea to your Discord or Telegram bot and blurt turns it into a polished GitHub issue automatically.

---

## Getting started

**You'll need:**
- Docker + Docker Compose
- A GitHub repo and a [personal access token](https://github.com/settings/tokens) with Issues write permission
- An LLM API key — Gemini recommended ([free tier available](https://aistudio.google.com/app/apikey))
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications)) or a Telegram bot token ([@BotFather](https://t.me/botfather))

**Then run:**

```bash
curl -fsSL https://raw.githubusercontent.com/sholgaat/blurt/main/quickstart.sh -o /tmp/blurt-setup.sh && bash /tmp/blurt-setup.sh
```

The script will choose an install directory, collect your credentials, and tell you when to run `docker compose up -d`.

**Prefer to inspect before running?**

```bash
curl -fsSL https://raw.githubusercontent.com/sholgaat/blurt/main/quickstart.sh -o blurt-setup.sh
# read blurt-setup.sh
bash blurt-setup.sh
```

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

### Build images from source

By default, Docker pulls pre-built images. To build images locally from source instead, before running `docker compose up -d`:

```bash
mv docker-compose.override.yml.disabled docker-compose.override.yml
```
