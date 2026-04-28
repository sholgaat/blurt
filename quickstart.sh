#!/usr/bin/env bash
# Quickstart setup for idea-inbox.
# Copies example env files if not present, prompts for required values,
# and writes them in-place.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── helpers ──────────────────────────────────────────────────────────────────

info()    { printf '\n%s\n' "$*"; }
success() { printf '  OK: %s\n' "$*"; }

prompt_value() {
  local var_name="$1"
  local prompt_text="$2"
  local secret="${3:-false}"
  local input_value

  while true; do
    if [[ "$secret" == true ]]; then
      read -r -s -p "  $prompt_text: " input_value
      echo
    else
      read -r -p "  $prompt_text: " input_value
    fi

    if [[ -n "$input_value" ]]; then
      printf -v "$var_name" '%s' "$input_value"
      return
    fi

    echo "  Value is required."
  done
}

prompt_optional() {
  local var_name="$1"
  local prompt_text="$2"
  local input_value
  read -r -p "  $prompt_text (leave blank to skip): " input_value
  printf -v "$var_name" '%s' "$input_value"
}

ensure_env_file() {
  local file="$1"
  local example="$2"
  local created_message="$3"
  local exists_message="$4"

  if [[ ! -f "$file" ]]; then
    cp "$example" "$file"
    success "$created_message"
  else
    success "$exists_message"
  fi
}

# Write KEY=VALUE into a file, replacing the existing KEY=... line.
set_env() {
  local file="$1"
  local key="$2"
  local value="$3"
  local tmp_file

  tmp_file="$(mktemp "${file}.XXXXXX")"
  awk -v key="$key" -v value="$value" '
    BEGIN { updated = 0 }
    $0 ~ "^" key "=" {
      print key "=" value
      updated = 1
      next
    }
    { print }
    END {
      if (!updated) {
        print key "=" value
      }
    }
  ' "$file" > "$tmp_file"
  mv "$tmp_file" "$file"
}

# ── env file setup ────────────────────────────────────────────────────────────

BACKEND_ENV="$REPO_ROOT/.env.backend"
BOT_ENV="$REPO_ROOT/.env.bot"
ROOT_ENV="$REPO_ROOT/.env"

ensure_env_file "$BACKEND_ENV" "$REPO_ROOT/.env.backend.example" "Created .env.backend from example" ".env.backend already exists — updating values in place"
ensure_env_file "$BOT_ENV" "$REPO_ROOT/.env.bot.example" "Created .env.bot from example" ".env.bot already exists — updating values in place"
ensure_env_file "$ROOT_ENV" "$REPO_ROOT/.env.example" "Created .env from example" ".env already exists — updating values in place"

# ── setup mode ────────────────────────────────────────────────────────────────

printf '\n'
printf '  ╔══════════════════════════════════════════╗\n'
printf '  ║       idea-inbox — setup wizard          ║\n'
printf '  ╚══════════════════════════════════════════╝\n'
printf '\n'
echo "  Choose a setup mode:"
echo
echo "  [1] Recommended — Discord bot + Gemini  (fastest, fewest questions)"
echo "  [2] Custom      — choose your LLM provider and bot platform(s)"
echo

while true; do
  read -r -p "  Choice (1/2) [1]: " SETUP_MODE_CHOICE
  SETUP_MODE_CHOICE="${SETUP_MODE_CHOICE:-1}"
  case "$SETUP_MODE_CHOICE" in
    1) SETUP_MODE="recommended"; break ;;
    2) SETUP_MODE="custom"; break ;;
    *) echo "  Invalid choice. Enter 1 or 2." ;;
  esac
done

# ── shared: GitHub config ─────────────────────────────────────────────────────

collect_github() {
  info "--- GitHub ---"

  echo "  GITHUB_TOKEN: a Personal Access Token (classic: 'repo' scope;"
  echo "    fine-grained: Issues read/write + Labels read/write)."
  prompt_value GITHUB_TOKEN "GITHUB_TOKEN" true
  set_env "$BACKEND_ENV" "GITHUB_TOKEN" "$GITHUB_TOKEN"

  echo
  echo "  GITHUB_REPO: the repository where issues will be created, in owner/repo format."
  echo "  e.g. myusername/idea-inbox"
  prompt_value GITHUB_REPO "GITHUB_REPO"
  set_env "$BACKEND_ENV" "GITHUB_REPO" "$GITHUB_REPO"
}

# ── shared: Discord config ────────────────────────────────────────────────────

collect_discord() {
  info "--- Discord ---"

  echo "  DISCORD_BOT_TOKEN: the token from the Discord Developer Portal."
  echo "  See https://discord.com/developers/applications"
  echo "  The bot needs the 'Message Content' privileged intent enabled."
  prompt_value DISCORD_BOT_TOKEN "DISCORD_BOT_TOKEN" true
  set_env "$BOT_ENV" "DISCORD_BOT_TOKEN" "$DISCORD_BOT_TOKEN"

  echo
  echo "  Your Discord user ID: enable Developer Mode in Discord (Settings >"
  echo "  Advanced > Developer Mode), then right-click yourself and choose 'Copy User ID'."
  prompt_value DISCORD_USER_ID "Your Discord user ID"
}

# ── shared: Telegram config ───────────────────────────────────────────────────

collect_telegram() {
  info "--- Telegram ---"

  echo "  TELEGRAM_BOT_TOKEN: the token BotFather gave you when you created the bot."
  echo "  See https://core.telegram.org/bots#botfather"
  prompt_value TELEGRAM_BOT_TOKEN "TELEGRAM_BOT_TOKEN" true
  set_env "$BOT_ENV" "TELEGRAM_BOT_TOKEN" "$TELEGRAM_BOT_TOKEN"

  echo
  echo "  Your Telegram user ID: message @userinfobot on Telegram to find it."
  prompt_value TELEGRAM_USER_ID "Your Telegram user ID"
}

# ── recommended path ──────────────────────────────────────────────────────────

if [[ "$SETUP_MODE" == "recommended" ]]; then

  info "--- Gemini ---"
  echo "  GEMINI_API_KEY: get one free at https://aistudio.google.com/app/apikey"
  prompt_value GEMINI_API_KEY "GEMINI_API_KEY" true
  set_env "$BACKEND_ENV" "LLM_PROVIDER" "gemini"
  set_env "$BACKEND_ENV" "GEMINI_API_KEY" "$GEMINI_API_KEY"
  set_env "$BACKEND_ENV" "OPENAI_API_KEY" ""
  set_env "$BACKEND_ENV" "ANTHROPIC_API_KEY" ""

  collect_github
  collect_discord

  COMPOSE_PROFILES="discord"
  set_env "$ROOT_ENV" "COMPOSE_PROFILES" "$COMPOSE_PROFILES"

  ALLOWED_IDS_JSON="[\"discord:${DISCORD_USER_ID}\"]"
  set_env "$BOT_ENV" "ALLOWED_USER_IDS" "$ALLOWED_IDS_JSON"

fi

# ── custom path ───────────────────────────────────────────────────────────────

if [[ "$SETUP_MODE" == "custom" ]]; then

  info "--- LLM provider ---"
  echo "  Which LLM provider do you want to use for idea structuring?"
  echo "  [1] gemini"
  echo "  [2] openai"
  echo "  [3] anthropic"
  echo "  [4] ollama (local)"
  while true; do
    read -r -p "  Choice (1/2/3/4): " LLM_PROVIDER_CHOICE

    case "$LLM_PROVIDER_CHOICE" in
      1)
        echo
        echo "  GEMINI_API_KEY: get one free at https://aistudio.google.com/app/apikey"
        prompt_value GEMINI_API_KEY "GEMINI_API_KEY" true
        set_env "$BACKEND_ENV" "LLM_PROVIDER" "gemini"
        set_env "$BACKEND_ENV" "GEMINI_API_KEY" "$GEMINI_API_KEY"
        set_env "$BACKEND_ENV" "OPENAI_API_KEY" ""
        set_env "$BACKEND_ENV" "ANTHROPIC_API_KEY" ""
        break
        ;;
      2)
        echo
        prompt_value OPENAI_API_KEY "OPENAI_API_KEY" true
        set_env "$BACKEND_ENV" "LLM_PROVIDER" "openai"
        set_env "$BACKEND_ENV" "OPENAI_API_KEY" "$OPENAI_API_KEY"
        set_env "$BACKEND_ENV" "GEMINI_API_KEY" ""
        set_env "$BACKEND_ENV" "ANTHROPIC_API_KEY" ""
        break
        ;;
      3)
        echo
        prompt_value ANTHROPIC_API_KEY "ANTHROPIC_API_KEY" true
        set_env "$BACKEND_ENV" "LLM_PROVIDER" "anthropic"
        set_env "$BACKEND_ENV" "ANTHROPIC_API_KEY" "$ANTHROPIC_API_KEY"
        set_env "$BACKEND_ENV" "GEMINI_API_KEY" ""
        set_env "$BACKEND_ENV" "OPENAI_API_KEY" ""
        break
        ;;
      4)
        prompt_optional OLLAMA_API_BASE "OLLAMA_API_BASE (default: http://localhost:11434)"
        set_env "$BACKEND_ENV" "LLM_PROVIDER" "ollama"
        set_env "$BACKEND_ENV" "GEMINI_API_KEY" ""
        set_env "$BACKEND_ENV" "OPENAI_API_KEY" ""
        set_env "$BACKEND_ENV" "ANTHROPIC_API_KEY" ""
        if [[ -n "$OLLAMA_API_BASE" ]]; then
          set_env "$BACKEND_ENV" "OLLAMA_API_BASE" "$OLLAMA_API_BASE"
        fi
        set_env "$BACKEND_ENV" "OLLAMA_MODEL" "llama3.2"
        break
        ;;
      *)
        echo "  Invalid choice. Enter 1, 2, 3, or 4."
        ;;
    esac
  done

  collect_github

  info "--- Bot platform ---"
  echo "  Which bot platform(s) do you want to run?"
  echo "  [1] discord"
  echo "  [2] telegram"
  echo "  [3] both"
  while true; do
    read -r -p "  Choice (1/2/3): " PROVIDER_CHOICE
    case "$PROVIDER_CHOICE" in
      1) COMPOSE_PROFILES="discord";          break ;;
      2) COMPOSE_PROFILES="telegram";         break ;;
      3) COMPOSE_PROFILES="discord,telegram"; break ;;
      *) echo "  Invalid choice. Enter 1, 2, or 3." ;;
    esac
  done
  set_env "$ROOT_ENV" "COMPOSE_PROFILES" "$COMPOSE_PROFILES"

  # Provider-specific tokens
  [[ "$COMPOSE_PROFILES" == *"discord"*  ]] && collect_discord
  [[ "$COMPOSE_PROFILES" == *"telegram"* ]] && collect_telegram

  # Build ALLOWED_USER_IDS JSON array
  info "--- User authorization ---"
  ALLOWED_IDS_JSON="["

  if [[ "$COMPOSE_PROFILES" == *"telegram"* ]]; then
    ALLOWED_IDS_JSON="${ALLOWED_IDS_JSON}\"telegram:${TELEGRAM_USER_ID}\""
  fi

  if [[ "$COMPOSE_PROFILES" == *"discord"* ]]; then
    [[ "$ALLOWED_IDS_JSON" != "[" ]] && ALLOWED_IDS_JSON="${ALLOWED_IDS_JSON},"
    ALLOWED_IDS_JSON="${ALLOWED_IDS_JSON}\"discord:${DISCORD_USER_ID}\""
  fi

  ALLOWED_IDS_JSON="${ALLOWED_IDS_JSON}]"
  set_env "$BOT_ENV" "ALLOWED_USER_IDS" "$ALLOWED_IDS_JSON"

fi

# ── done ──────────────────────────────────────────────────────────────────────

info "=== Setup complete ==="
echo
echo "Next steps:"
echo "  1. Start the stack:"
echo "       docker compose up -d"
echo
echo "  2. Watch logs:"
echo "       docker compose logs -f"
echo
echo "  3. Message your bot and it will reply with a link to your new GitHub issue!"
