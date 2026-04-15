#!/usr/bin/env bash
# Interactive local quickstart for idea-inbox.
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

prompt_optional() {
  local var_name="$1"
  local prompt_text="$2"
  local input_value
  read -r -p "  $prompt_text (leave blank to skip): " input_value
  printf -v "$var_name" '%s' "$input_value"
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

info "=== idea-inbox local setup ==="

BACKEND_ENV="$REPO_ROOT/.env.backend"
BOT_ENV="$REPO_ROOT/.env.bot"
ROOT_ENV="$REPO_ROOT/.env"

ensure_env_file "$BACKEND_ENV" "$REPO_ROOT/.env.backend.example" "Created .env.backend from example" ".env.backend already exists — updating values in place"
ensure_env_file "$BOT_ENV" "$REPO_ROOT/.env.bot.example" "Created .env.bot from example" ".env.bot already exists — updating values in place"
ensure_env_file "$ROOT_ENV" "$REPO_ROOT/.env.example" "Created .env from example" ".env already exists — updating values in place"

# ── backend secrets ───────────────────────────────────────────────────────────

info "--- Backend configuration ---"

echo "  Which LLM provider do you want to use for idea structuring?"
echo "  [1] gemini"
echo "  [2] openai"
echo "  [3] anthropic"
echo "  [4] ollama"
while true; do
  read -r -p "  Choice (1/2/3/4): " LLM_PROVIDER_CHOICE

  case "$LLM_PROVIDER_CHOICE" in
    1)
      LLM_PROVIDER="gemini"
      echo
      echo "  GEMINI_API_KEY: needed to call the Gemini API for idea structuring."
      prompt_value GEMINI_API_KEY "GEMINI_API_KEY" true
      set_env "$BACKEND_ENV" "LLM_PROVIDER" "$LLM_PROVIDER"
      set_env "$BACKEND_ENV" "GEMINI_API_KEY" "$GEMINI_API_KEY"
      set_env "$BACKEND_ENV" "OPENAI_API_KEY" ""
      set_env "$BACKEND_ENV" "ANTHROPIC_API_KEY" ""
      break
      ;;
    2)
      LLM_PROVIDER="openai"
      echo
      echo "  OPENAI_API_KEY: needed to call the OpenAI API for idea structuring."
      prompt_value OPENAI_API_KEY "OPENAI_API_KEY" true
      set_env "$BACKEND_ENV" "LLM_PROVIDER" "$LLM_PROVIDER"
      set_env "$BACKEND_ENV" "OPENAI_API_KEY" "$OPENAI_API_KEY"
      set_env "$BACKEND_ENV" "GEMINI_API_KEY" ""
      set_env "$BACKEND_ENV" "ANTHROPIC_API_KEY" ""
      break
      ;;
    3)
      LLM_PROVIDER="anthropic"
      echo
      echo "  ANTHROPIC_API_KEY: needed to call the Anthropic API for idea structuring."
      prompt_value ANTHROPIC_API_KEY "ANTHROPIC_API_KEY" true
      set_env "$BACKEND_ENV" "LLM_PROVIDER" "$LLM_PROVIDER"
      set_env "$BACKEND_ENV" "ANTHROPIC_API_KEY" "$ANTHROPIC_API_KEY"
      set_env "$BACKEND_ENV" "GEMINI_API_KEY" ""
      set_env "$BACKEND_ENV" "OPENAI_API_KEY" ""
      break
      ;;
    4)
      LLM_PROVIDER="ollama"
      echo
      echo "  MODEL_TIMEOUT_SECONDS: request timeout for local model calls."
      prompt_value MODEL_TIMEOUT_SECONDS "MODEL_TIMEOUT_SECONDS"
      prompt_optional OLLAMA_API_BASE "OLLAMA_API_BASE"
      set_env "$BACKEND_ENV" "LLM_PROVIDER" "$LLM_PROVIDER"
      set_env "$BACKEND_ENV" "GEMINI_API_KEY" ""
      set_env "$BACKEND_ENV" "OPENAI_API_KEY" ""
      set_env "$BACKEND_ENV" "ANTHROPIC_API_KEY" ""
      set_env "$BACKEND_ENV" "MODEL_TIMEOUT_SECONDS" "$MODEL_TIMEOUT_SECONDS"
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

echo
echo "  GITHUB_TOKEN: a Personal Access Token (classic: 'repo' scope;"
echo "    fine-grained: Issues read/write + Labels read/write)."
prompt_value GITHUB_TOKEN "GITHUB_TOKEN" true
set_env "$BACKEND_ENV" "GITHUB_TOKEN" "$GITHUB_TOKEN"

echo
echo "  GITHUB_REPO_OWNER: GitHub username or org that owns the target repo."
prompt_value GITHUB_REPO_OWNER "GITHUB_REPO_OWNER"
set_env "$BACKEND_ENV" "GITHUB_REPO_OWNER" "$GITHUB_REPO_OWNER"

echo
echo "  GITHUB_REPO_NAME: repository where issues will be created."
prompt_value GITHUB_REPO_NAME "GITHUB_REPO_NAME"
set_env "$BACKEND_ENV" "GITHUB_REPO_NAME" "$GITHUB_REPO_NAME"

echo
info "--- GitHub issue creation mode ---"
echo "  How should the bot handle ideas?"
echo "  [1] Test mode — the bot replies with an example URL. No real GitHub issues are created."
echo "  [2] Live mode — real GitHub issues are created in the configured repository."
echo
while true; do
  read -r -p "  Choice (1/2): " DRY_RUN_CHOICE
  case "$DRY_RUN_CHOICE" in
    1)
      set_env "$BACKEND_ENV" "DRY_RUN" "true"
      success "Running in test mode — DRY_RUN=true"
      echo "  To switch to live mode later, set DRY_RUN=false in $BACKEND_ENV"
      break
      ;;
    2)
      set_env "$BACKEND_ENV" "DRY_RUN" "false"
      success "Running in live mode — DRY_RUN=false. Real GitHub issues will be created."
      break
      ;;
    *)
      echo "  Invalid choice. Enter 1 or 2."
      ;;
  esac
done

# ── bot provider ──────────────────────────────────────────────────────────────

info "--- Bot provider ---"
echo "  Which bot provider(s) do you want to run?"
echo "  [1] telegram"
echo "  [2] discord"
echo "  [3] both"
while true; do
  read -r -p "  Choice (1/2/3): " PROVIDER_CHOICE

  case "$PROVIDER_CHOICE" in
    1)
      COMPOSE_PROFILES="telegram"
      break
      ;;
    2)
      COMPOSE_PROFILES="discord"
      break
      ;;
    3)
      COMPOSE_PROFILES="discord,telegram"
      break
      ;;
    *)
      echo "  Invalid choice. Enter 1, 2, or 3."
      ;;
  esac
done

# Announce the chosen providers immediately for clarity
success "Selected COMPOSE_PROFILES=$COMPOSE_PROFILES"
set_env "$ROOT_ENV" "COMPOSE_PROFILES" "$COMPOSE_PROFILES"

# ── provider-specific config ──────────────────────────────────────────────────

setup_telegram() {
  info "--- Telegram configuration ---"

  echo "  TELEGRAM_BOT_TOKEN: the token BotFather gave you when you created the bot."
  echo "  See https://core.telegram.org/bots#botfather"
  prompt_value TELEGRAM_BOT_TOKEN "TELEGRAM_BOT_TOKEN" true
  set_env "$BOT_ENV" "TELEGRAM_BOT_TOKEN" "$TELEGRAM_BOT_TOKEN"
}

setup_discord() {
  info "--- Discord configuration ---"

  echo "  DISCORD_BOT_TOKEN: the token from the Discord Developer Portal."
  echo "  See https://discord.com/developers/applications"
  echo "  The bot needs the 'Message Content' privileged intent enabled."
  prompt_value DISCORD_BOT_TOKEN "DISCORD_BOT_TOKEN" true
  set_env "$BOT_ENV" "DISCORD_BOT_TOKEN" "$DISCORD_BOT_TOKEN"

  echo
  echo "  DISCORD_IDEA_CHANNEL_ID: (optional) numeric ID of the guild channel where"
  echo "  the bot should also accept ideas. Right-click the channel > 'Copy Channel ID'."
  echo "  If left blank, the bot will only respond to Direct Messages."
  prompt_optional DISCORD_IDEA_CHANNEL_ID "DISCORD_IDEA_CHANNEL_ID"
  set_env "$BOT_ENV" "DISCORD_IDEA_CHANNEL_ID" "$DISCORD_IDEA_CHANNEL_ID"
}

case "$COMPOSE_PROFILES" in
  telegram)         setup_telegram ;;
  discord)          setup_discord ;;
  discord,telegram) setup_discord; setup_telegram ;;
esac

# ── allowed user IDs (platform-scoped JSON array) ──────────────────────────────

info "--- User authorization ---"
echo "  ALLOWED_USER_IDS: JSON array of allowed user IDs in format 'platform:id'."
echo "  Each provider's user IDs are prefixed to prevent cross-contamination."
echo
ALLOWED_IDS_JSON="["

if [[ "$COMPOSE_PROFILES" == *"telegram"* ]]; then
  echo "  Telegram: Find your user ID by messaging @userinfobot."
  prompt_value TELEGRAM_USER_ID "Your Telegram user ID"
  ALLOWED_IDS_JSON="${ALLOWED_IDS_JSON}\"telegram:${TELEGRAM_USER_ID}\""
fi

if [[ "$COMPOSE_PROFILES" == *"discord"* ]]; then
  if [[ "$ALLOWED_IDS_JSON" != "[" ]]; then
    ALLOWED_IDS_JSON="${ALLOWED_IDS_JSON},"
  fi
  echo
  echo "  Discord: Enable Developer Mode in Discord settings, then right-click"
  echo "  yourself and choose 'Copy User ID'."
  prompt_value DISCORD_USER_ID "Your Discord user ID"
  ALLOWED_IDS_JSON="${ALLOWED_IDS_JSON}\"discord:${DISCORD_USER_ID}\""
fi

ALLOWED_IDS_JSON="${ALLOWED_IDS_JSON}]"
set_env "$BOT_ENV" "ALLOWED_USER_IDS" "$ALLOWED_IDS_JSON"

# BACKEND_URL is always correct for Docker Compose — no prompt needed.

# ── done ──────────────────────────────────────────────────────────────────────

info "=== Setup complete ==="
echo
echo "Next steps:"
echo "  1. Start the stack:"
echo "       docker compose up -d --build"
echo
echo "  2. Watch logs:"
echo "       docker compose logs -f"
echo
echo "  3. Message your bot and see it reply with your new GitHub Issues!"
