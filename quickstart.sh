#!/usr/bin/env bash
# Quickstart setup for blurt.
# Prompts for install directory, fetches docker-compose.yml, copies example env
# files if not present, prompts for required values (preserving existing ones),
# and writes them in-place.
set -euo pipefail

BLURT_RAW_BASE="https://raw.githubusercontent.com/sholgaat/blurt/main"

# ── pre-flight checks ─────────────────────────────────────────────────────────

if ! command -v docker &>/dev/null; then
  printf '\n  ✗ Docker not found.\n'
  printf '    Install it from https://docs.docker.com/get-docker/ then re-run.\n\n'
  exit 1
fi

if ! docker compose version &>/dev/null; then
  printf '\n  ✗ Docker Compose v2 not found.\n'
  printf '    Make sure you have Docker Desktop or the compose plugin installed.\n'
  printf '    See https://docs.docker.com/compose/install/\n\n'
  exit 1
fi

# ── helpers ───────────────────────────────────────────────────────────────────

info()    { printf '\n%s\n' "$*"; }
success() { printf '  OK: %s\n' "$*"; }

expand_tilde() { printf '%s' "${1/#\~/$HOME}"; }

get_env() {
  local file="$1" key="$2"
  [[ ! -f "$file" ]] && return
  local line; line="$(grep -m1 "^${key}=" "$file" 2>/dev/null || true)"
  printf '%s' "${line#*=}"
}

set_env() {
  local file="$1" key="$2" value="$3"
  local tmp; tmp="$(mktemp "${file}.XXXXXX")"
  awk -v key="$key" -v value="$value" '
    BEGIN { updated=0 }
    $0 ~ "^" key "=" { print key "=" value; updated=1; next }
    { print }
    END { if (!updated) print key "=" value }
  ' "$file" > "$tmp"
  mv "$tmp" "$file"
}

# Prompt for a required value; secret=true masks input.
# Current value is kept if the user presses enter.
prompt_value() {
  local var_name="$1" prompt_text="$2" secret="${3:-false}" current="${4:-}"
  local flags="-r"; [[ "$secret" == true ]] && flags="-rs"
  local hint=""
  while true; do
    if [[ -n "$current" ]]; then
      hint=" [$([ "$secret" == true ] && printf 'already set — enter to keep' || printf '%s' "$current")]"
    fi
    read $flags -p "  $prompt_text$hint: " val
    [[ "$secret" == true ]] && echo
    val="${val:-$current}"
    if [[ -n "$val" ]]; then printf -v "$var_name" '%s' "$val"; return; fi
    echo "  Value is required."
  done
}

prompt_optional() {
  local var_name="$1" prompt_text="$2" val
  read -r -p "  $prompt_text (leave blank to skip): " val
  printf -v "$var_name" '%s' "$val"
}

# ── install directory ─────────────────────────────────────────────────────────

cat <<'BANNER'

  ╔══════════════════════════════════════════╗
  ║            blurt — setup wizard          ║
  ╚══════════════════════════════════════════╝

BANNER

read -r -p "  Install directory [~/blurt]: " RAW_INSTALL_DIR
RAW_INSTALL_DIR="${RAW_INSTALL_DIR:-~/blurt}"
INSTALL_DIR="$(expand_tilde "$RAW_INSTALL_DIR")"
mkdir -p "$INSTALL_DIR"
INSTALL_DIR="$(cd "$INSTALL_DIR" && pwd)"
cd "$INSTALL_DIR"
success "Using install directory: $INSTALL_DIR"

# ── fetch docker-compose.yml ──────────────────────────────────────────────────

COMPOSE_FILE="$INSTALL_DIR/docker-compose.yml"

if curl -fsSL "$BLURT_RAW_BASE/docker-compose.yml" -o "$INSTALL_DIR/docker-compose.yml.new" 2>/dev/null; then
  if [[ -f "$COMPOSE_FILE" ]] && ! diff -q "$COMPOSE_FILE" "$INSTALL_DIR/docker-compose.yml.new" &>/dev/null; then
    success "docker-compose.yml updated to latest version"
  elif [[ ! -f "$COMPOSE_FILE" ]]; then
    success "docker-compose.yml downloaded"
  fi
  mv "$INSTALL_DIR/docker-compose.yml.new" "$COMPOSE_FILE"
else
  rm -f "$INSTALL_DIR/docker-compose.yml.new"
  if [[ ! -f "$COMPOSE_FILE" ]]; then
    printf '  ✗ Could not fetch docker-compose.yml from GitHub.\n'
    printf '    Check your internet connection and try again.\n\n'
    exit 1
  else
    printf '  Warning: could not fetch latest docker-compose.yml — using existing file.\n'
  fi
fi

# ── env file setup ────────────────────────────────────────────────────────────

BACKEND_ENV="$INSTALL_DIR/.env.backend"
BOT_ENV="$INSTALL_DIR/.env.bot"
ROOT_ENV="$INSTALL_DIR/.env"

for pair in ".env.backend.example:$BACKEND_ENV" ".env.bot.example:$BOT_ENV" ".env.example:$ROOT_ENV"; do
  example_name="${pair%%:*}"; target="${pair##*:}"
  if [[ ! -f "$target" ]]; then
    if ! curl -fsSL "$BLURT_RAW_BASE/$example_name" -o "$target" 2>/dev/null; then
      printf '  ✗ Could not fetch %s from GitHub.\n' "$example_name"; exit 1
    fi
    success "Created $(basename "$target") from example"
  else
    success "$(basename "$target") already exists — updating values in place"
  fi
done

# ── setup mode ────────────────────────────────────────────────────────────────

echo
echo "  Choose a setup mode:"
echo
echo "  [1] Recommended — Discord bot + Gemini  (fastest, fewest questions)"
echo "  [2] Custom      — choose your LLM provider and bot platform(s)"
echo

while true; do
  read -r -p "  Choice (1/2) [1]: " SETUP_MODE_CHOICE
  case "${SETUP_MODE_CHOICE:-1}" in
    1) LLM_PROVIDER_CHOICE=1; PROVIDER_CHOICE=1; break ;;
    2) LLM_PROVIDER_CHOICE=""; PROVIDER_CHOICE="";  break ;;
    *) echo "  Invalid choice. Enter 1 or 2." ;;
  esac
done

# ── LLM provider ──────────────────────────────────────────────────────────────

ALL_LLM_KEYS=(GEMINI_API_KEY GEMINI_MODEL OPENAI_API_KEY OPENAI_MODEL ANTHROPIC_API_KEY ANTHROPIC_MODEL OLLAMA_API_BASE OLLAMA_MODEL)

# Zero out every LLM key except those belonging to $1 (uppercase provider name).
clear_other_llm_keys() {
  local keep_prefix="${1^^}"
  for key in "${ALL_LLM_KEYS[@]}"; do
    [[ "$key" == "${keep_prefix}"* ]] || set_env "$BACKEND_ENV" "$key" ""
  done
}

collect_llm() {
  local provider="$1"        # gemini | openai | anthropic | ollama
  local PREFIX="${provider^^}"
  local key_var="${PREFIX}_API_KEY"
  local model_var="${PREFIX}_MODEL"

  if [[ "$provider" == "ollama" ]]; then
    local cur; cur="$(get_env "$BACKEND_ENV" "OLLAMA_API_BASE")"
    prompt_optional OLLAMA_API_BASE "OLLAMA_API_BASE (default: http://localhost:11434)"
    [[ -n "$OLLAMA_API_BASE" ]] && set_env "$BACKEND_ENV" "OLLAMA_API_BASE" "$OLLAMA_API_BASE"
  else
    echo
    local cur; cur="$(get_env "$BACKEND_ENV" "$key_var")"
    prompt_value "$key_var" "$key_var" true "$cur"
    set_env "$BACKEND_ENV" "$key_var" "${!key_var}"
  fi

  echo
  echo "  ${model_var}: the ${provider^} model to use for idea structuring."
  local cur; cur="$(get_env "$BACKEND_ENV" "$model_var")"
  prompt_value "$model_var" "$model_var" false "$cur"
  set_env "$BACKEND_ENV" "$model_var" "${!model_var}"

  set_env "$BACKEND_ENV" "LLM_PROVIDER" "$provider"
  clear_other_llm_keys "$provider"
}

info "--- LLM provider ---"
echo "  Which LLM provider do you want to use for idea structuring?"
echo "  [1] gemini"
echo "  [2] openai"
echo "  [3] anthropic"
echo "  [4] ollama (local)"

while true; do
  [[ -n "$LLM_PROVIDER_CHOICE" ]] || read -r -p "  Choice (1/2/3/4): " LLM_PROVIDER_CHOICE
  case "$LLM_PROVIDER_CHOICE" in
    1) collect_llm gemini;    break ;;
    2) collect_llm openai;    break ;;
    3) collect_llm anthropic; break ;;
    4) collect_llm ollama;    break ;;
    *) echo "  Invalid choice. Enter 1, 2, 3, or 4."; LLM_PROVIDER_CHOICE="" ;;
  esac
done

# ── GitHub ────────────────────────────────────────────────────────────────────

info "--- GitHub ---"
echo "  GITHUB_TOKEN: a Personal Access Token (classic: 'repo' scope;"
echo "    fine-grained: Issues read/write + Labels read/write)."
cur="$(get_env "$BACKEND_ENV" "GITHUB_TOKEN")"
prompt_value GITHUB_TOKEN "GITHUB_TOKEN" true "$cur"
set_env "$BACKEND_ENV" "GITHUB_TOKEN" "$GITHUB_TOKEN"

echo
echo "  GITHUB_REPO: the repository where issues will be created, in owner/repo format."
echo "  e.g. myusername/blurt"
cur="$(get_env "$BACKEND_ENV" "GITHUB_REPO")"
prompt_value GITHUB_REPO "GITHUB_REPO" false "$cur"
set_env "$BACKEND_ENV" "GITHUB_REPO" "$GITHUB_REPO"

# ── bot platform ──────────────────────────────────────────────────────────────

info "--- Bot platform ---"
echo "  Which bot platform(s) do you want to run?"
echo "  [1] discord"
echo "  [2] telegram"
echo "  [3] both"

while true; do
  [[ -n "$PROVIDER_CHOICE" ]] || read -r -p "  Choice (1/2/3): " PROVIDER_CHOICE
  case "$PROVIDER_CHOICE" in
    1) COMPOSE_PROFILES="discord";          break ;;
    2) COMPOSE_PROFILES="telegram";         break ;;
    3) COMPOSE_PROFILES="discord,telegram"; break ;;
    *) echo "  Invalid choice. Enter 1, 2, or 3."; PROVIDER_CHOICE="" ;;
  esac
done
set_env "$ROOT_ENV" "COMPOSE_PROFILES" "$COMPOSE_PROFILES"

# ── Discord ───────────────────────────────────────────────────────────────────

if [[ "$COMPOSE_PROFILES" == *"discord"* ]]; then
  info "--- Discord ---"
  echo "  DISCORD_BOT_TOKEN: the token from the Discord Developer Portal."
  echo "  See https://discord.com/developers/applications"
  echo "  The bot needs the 'Message Content' privileged intent enabled."
  cur="$(get_env "$BOT_ENV" "DISCORD_BOT_TOKEN")"
  prompt_value DISCORD_BOT_TOKEN "DISCORD_BOT_TOKEN" true "$cur"
  set_env "$BOT_ENV" "DISCORD_BOT_TOKEN" "$DISCORD_BOT_TOKEN"

  echo
  echo "  Your Discord user ID: enable Developer Mode in Discord (Settings >"
  echo "  Advanced > Developer Mode), then right-click yourself and choose 'Copy User ID'."
  cur_ids="$(get_env "$BOT_ENV" "ALLOWED_USER_IDS")"
  cur_discord_id=""
  [[ "$cur_ids" =~ \"discord:([^\"]+)\" ]] && cur_discord_id="${BASH_REMATCH[1]}"
  prompt_value DISCORD_USER_ID "Your Discord user ID" false "$cur_discord_id"
fi

# ── Telegram ──────────────────────────────────────────────────────────────────

if [[ "$COMPOSE_PROFILES" == *"telegram"* ]]; then
  info "--- Telegram ---"
  echo "  TELEGRAM_BOT_TOKEN: the token BotFather gave you when you created the bot."
  echo "  See https://core.telegram.org/bots#botfather"
  cur="$(get_env "$BOT_ENV" "TELEGRAM_BOT_TOKEN")"
  prompt_value TELEGRAM_BOT_TOKEN "TELEGRAM_BOT_TOKEN" true "$cur"
  set_env "$BOT_ENV" "TELEGRAM_BOT_TOKEN" "$TELEGRAM_BOT_TOKEN"

  echo
  echo "  Your Telegram user ID: message @userinfobot on Telegram to find it."
  cur_ids="$(get_env "$BOT_ENV" "ALLOWED_USER_IDS")"
  cur_telegram_id=""
  [[ "$cur_ids" =~ \"telegram:([^\"]+)\" ]] && cur_telegram_id="${BASH_REMATCH[1]}"
  prompt_value TELEGRAM_USER_ID "Your Telegram user ID" false "$cur_telegram_id"
fi

# ── ALLOWED_USER_IDS ──────────────────────────────────────────────────────────

ALLOWED_IDS_JSON="["
[[ "$COMPOSE_PROFILES" == *"telegram"* ]] && ALLOWED_IDS_JSON="${ALLOWED_IDS_JSON}\"telegram:${TELEGRAM_USER_ID}\""
if [[ "$COMPOSE_PROFILES" == *"discord"* ]]; then
  [[ "$ALLOWED_IDS_JSON" != "[" ]] && ALLOWED_IDS_JSON="${ALLOWED_IDS_JSON},"
  ALLOWED_IDS_JSON="${ALLOWED_IDS_JSON}\"discord:${DISCORD_USER_ID}\""
fi
ALLOWED_IDS_JSON="${ALLOWED_IDS_JSON}]"
set_env "$BOT_ENV" "ALLOWED_USER_IDS" "$ALLOWED_IDS_JSON"

# ── done ──────────────────────────────────────────────────────────────────────

cat <<DONE

=== Setup complete ===

Start the stack:
  cd $INSTALL_DIR
  docker compose up -d

Watch logs:
  docker compose logs -f

To update blurt in future, re-run this script. It will fetch the latest
configuration and walk you through any new settings — existing values are
preserved unless you choose to change them.

Message your bot and watch the issues appear.
DONE
