#!/usr/bin/env bash
# Interactive local quickstart for idea-inbox.
# Copies example env files if not present, prompts for required values,
# and writes them in-place using sed.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── helpers ──────────────────────────────────────────────────────────────────

info()    { printf '\n%s\n' "$*"; }
success() { printf '  OK: %s\n' "$*"; }

prompt_required() {
  local var_name="$1"
  local prompt_text="$2"
  local input_value
  while true; do
    read -r -p "  $prompt_text: " input_value
    if [[ -n "$input_value" ]]; then
      printf -v "$var_name" '%s' "$input_value"
      return
    fi
    echo "  Value is required."
  done
}

prompt_secret_required() {
  local var_name="$1"
  local prompt_text="$2"
  local input_value
  while true; do
    read -r -s -p "  $prompt_text: " input_value
    echo
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

# Prompt the user to type an exact confirmation token.
# Returns 0 on success (typed exactly), 1 otherwise.
prompt_typed_confirm() {
  local prompt_text="$1"
  local token="$2"
  local input_value
  read -r -p "  $prompt_text (type \"$token\" to confirm): " input_value
  if [[ "$input_value" == "$token" ]]; then
    return 0
  fi
  return 1
}

# Write KEY=VALUE into a file, replacing the existing KEY=... line.
set_env() {
  local file="$1"
  local key="$2"
  local value="$3"
  # Escape characters that would break sed's replacement string
  local escaped_value
  escaped_value="$(printf '%s' "$value" | sed 's/[&/\]/\\&/g')"
  sed -i "s|^${key}=.*|${key}=${escaped_value}|" "$file"
}

# ── env file setup ────────────────────────────────────────────────────────────

info "=== idea-inbox local setup ==="

BACKEND_ENV="$REPO_ROOT/.env.backend"
BOT_ENV="$REPO_ROOT/.env.bot"
ROOT_ENV="$REPO_ROOT/.env"

if [[ ! -f "$BACKEND_ENV" ]]; then
  cp "$REPO_ROOT/.env.backend.example" "$BACKEND_ENV"
  success "Created .env.backend from example"
else
  success ".env.backend already exists — updating values in place"
fi

if [[ ! -f "$BOT_ENV" ]]; then
  cp "$REPO_ROOT/.env.bot.example" "$BOT_ENV"
  success "Created .env.bot from example"
else
  success ".env.bot already exists — updating values in place"
fi

if [[ ! -f "$ROOT_ENV" ]]; then
  cp "$REPO_ROOT/.env.example" "$ROOT_ENV"
  success "Created .env from example"
else
  success ".env already exists — updating values in place"
fi

# ── backend secrets ───────────────────────────────────────────────────────────

info "--- Backend configuration ---"

echo "  GEMINI_API_KEY: needed to call the Gemini API for idea structuring."
prompt_secret_required GEMINI_API_KEY "GEMINI_API_KEY"
set_env "$BACKEND_ENV" "GEMINI_API_KEY" "$GEMINI_API_KEY"

echo
echo "  GITHUB_TOKEN: a Personal Access Token (classic: 'repo' scope;"
echo "    fine-grained: Issues read/write + Labels read/write)."
prompt_secret_required GITHUB_TOKEN "GITHUB_TOKEN"
set_env "$BACKEND_ENV" "GITHUB_TOKEN" "$GITHUB_TOKEN"

echo
echo "  GITHUB_REPO_OWNER: GitHub username or org that owns the target repo."
prompt_required GITHUB_REPO_OWNER "GITHUB_REPO_OWNER"
set_env "$BACKEND_ENV" "GITHUB_REPO_OWNER" "$GITHUB_REPO_OWNER"

echo
echo "  GITHUB_REPO_NAME: repository where issues will be created."
prompt_required GITHUB_REPO_NAME "GITHUB_REPO_NAME"
set_env "$BACKEND_ENV" "GITHUB_REPO_NAME" "$GITHUB_REPO_NAME"

# DRY_RUN defaults to true in the example; leave it as-is for first run safety.
success "DRY_RUN left as 'true' — no real GitHub issues will be created until you change this."

# Show current DRY_RUN value so it's very visible during setup.
DRY_RUN_VALUE="$(grep -m1 '^DRY_RUN=' "$BACKEND_ENV" | cut -d'=' -f2- || true)"
info "!!! IMPORTANT: DRY_RUN is currently: ${DRY_RUN_VALUE:-<unset>} (file: $BACKEND_ENV)"
if [[ "${DRY_RUN_VALUE:-}" != "true" ]]; then
  echo "  Note: DRY_RUN is not 'true'. Real GitHub issues will be created!"
fi

# ── bot provider ──────────────────────────────────────────────────────────────

info "--- Bot provider ---"
echo "  Which bot provider(s) do you want to run?"
echo "  [1] telegram"
echo "  [2] discord"
echo "  [3] both"
read -r -p "  Choice [1]: " PROVIDER_CHOICE
case "${PROVIDER_CHOICE:-1}" in
  2) COMPOSE_PROFILES="discord" ;;
  3) COMPOSE_PROFILES="discord,telegram" ;;
  *) COMPOSE_PROFILES="telegram" ;;
esac
set_env "$ROOT_ENV" "COMPOSE_PROFILES" "$COMPOSE_PROFILES"
success "COMPOSE_PROFILES=$COMPOSE_PROFILES"

# ── provider-specific config ──────────────────────────────────────────────────

setup_telegram() {
  info "--- Telegram configuration ---"

  echo "  TELEGRAM_BOT_TOKEN: the token BotFather gave you when you created the bot."
  echo "  See https://core.telegram.org/bots#botfather"
  prompt_secret_required TELEGRAM_BOT_TOKEN "TELEGRAM_BOT_TOKEN"
  set_env "$BOT_ENV" "TELEGRAM_BOT_TOKEN" "$TELEGRAM_BOT_TOKEN"

  echo
  echo "  TELEGRAM_ALLOWED_USER_IDS: comma-separated numeric Telegram user IDs"
  echo "  that are allowed to submit ideas. Find your ID by messaging @userinfobot."
  prompt_required TELEGRAM_ALLOWED_USER_IDS "TELEGRAM_ALLOWED_USER_IDS"
  set_env "$BOT_ENV" "TELEGRAM_ALLOWED_USER_IDS" "$TELEGRAM_ALLOWED_USER_IDS"
}

setup_discord() {
  info "--- Discord configuration ---"

  echo "  DISCORD_BOT_TOKEN: the token from the Discord Developer Portal."
  echo "  See https://discord.com/developers/applications"
  echo "  The bot needs the 'Message Content' privileged intent enabled."
  prompt_secret_required DISCORD_BOT_TOKEN "DISCORD_BOT_TOKEN"
  set_env "$BOT_ENV" "DISCORD_BOT_TOKEN" "$DISCORD_BOT_TOKEN"

  echo
  echo "  DISCORD_ALLOWED_USER_IDS: comma-separated Discord user IDs (numeric)"
  echo "  that are allowed to submit ideas. Enable Developer Mode in Discord,"
  echo "  then right-click a user and choose 'Copy User ID'."
  prompt_required DISCORD_ALLOWED_USER_IDS "DISCORD_ALLOWED_USER_IDS"
  set_env "$BOT_ENV" "DISCORD_ALLOWED_USER_IDS" "$DISCORD_ALLOWED_USER_IDS"

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
echo "  3. Once everything looks good, set DRY_RUN=false in .env.backend"
echo "     to enable real GitHub issue creation."
echo

# Offer to disable DRY_RUN now with a strong typed confirmation.
if grep -q '^DRY_RUN=false' "$BACKEND_ENV"; then
  info "DRY_RUN already set to false in $BACKEND_ENV — real GitHub issues will be created."
else
  echo
  echo "Would you like to disable DRY_RUN now and enable real GitHub issue creation?"
  if prompt_typed_confirm "Confirm disabling DRY_RUN" "LIVE MODE"; then
    set_env "$BACKEND_ENV" "DRY_RUN" "false"
    success "DRY_RUN set to false in $BACKEND_ENV — real GitHub issues will be created."
  else
    info "DRY_RUN left as '${DRY_RUN_VALUE:-}' — you can change it later with:"
    echo "    sed -i 's/^DRY_RUN=.*/DRY_RUN=false/' $BACKEND_ENV"
    echo "  (or open $BACKEND_ENV and edit DRY_RUN=true → DRY_RUN=false)"
  fi
fi
