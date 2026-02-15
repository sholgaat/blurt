#!/usr/bin/env bash
set -euo pipefail

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

prompt_default() {
  local var_name="$1"
  local prompt_text="$2"
  local default_value="$3"
  local input_value
  read -r -p "$prompt_text [$default_value]: " input_value
  if [[ -z "$input_value" ]]; then
    printf -v "$var_name" '%s' "$default_value"
  else
    printf -v "$var_name" '%s' "$input_value"
  fi
}

prompt_required() {
  local var_name="$1"
  local prompt_text="$2"
  local input_value
  while true; do
    read -r -p "$prompt_text: " input_value
    if [[ -n "$input_value" ]]; then
      printf -v "$var_name" '%s' "$input_value"
      return
    fi
    echo "Value is required."
  done
}

prompt_secret_required() {
  local var_name="$1"
  local prompt_text="$2"
  local input_value
  while true; do
    read -r -s -p "$prompt_text: " input_value
    echo
    if [[ -n "$input_value" ]]; then
      printf -v "$var_name" '%s' "$input_value"
      return
    fi
    echo "Value is required."
  done
}

prompt_secret_optional() {
  local var_name="$1"
  local prompt_text="$2"
  local input_value
  read -r -s -p "$prompt_text (leave blank to skip): " input_value
  echo
  printf -v "$var_name" '%s' "$input_value"
}

cleanup() {
  rm -f "$BACKEND_ENV_TMP" "$BOT_ENV_TMP" "$ARCHIVE_TMP"
}

require_cmd gcloud
require_cmd tar
require_cmd mktemp

if ! gcloud auth list --filter=status:ACTIVE --format='value(account)' | grep -q '.'; then
  echo "No active gcloud account found. Run: gcloud auth login" >&2
  exit 1
fi

DEFAULT_PROJECT="$(gcloud config get-value project 2>/dev/null || true)"
if [[ -z "$DEFAULT_PROJECT" || "$DEFAULT_PROJECT" == "(unset)" ]]; then
  prompt_required PROJECT_ID "GCP project ID"
else
  prompt_default PROJECT_ID "GCP project ID" "$DEFAULT_PROJECT"
fi

prompt_default REGION "GCP region" "us-central1"
prompt_default ZONE "GCP zone" "${REGION}-a"
prompt_default VM_NAME "VM name" "idea-inbox-vm"
prompt_default MACHINE_TYPE "Machine type" "e2-small"
prompt_default APP_DIR "Remote app directory" "~/idea-inbox"
prompt_default BOT_PROVIDER "BOT_PROVIDER (discord|telegram)" "discord"

while [[ "$BOT_PROVIDER" != "discord" && "$BOT_PROVIDER" != "telegram" ]]; do
  echo "BOT_PROVIDER must be 'discord' or 'telegram'."
  prompt_default BOT_PROVIDER "BOT_PROVIDER (discord|telegram)" "discord"
done

prompt_secret_required GEMINI_API_KEY "GEMINI_API_KEY"
prompt_secret_required GITHUB_TOKEN "GITHUB_TOKEN"
prompt_required GITHUB_REPO_OWNER "GITHUB_REPO_OWNER"
prompt_required GITHUB_REPO_NAME "GITHUB_REPO_NAME"

if [[ "$BOT_PROVIDER" == "discord" ]]; then
  prompt_secret_required DISCORD_BOT_TOKEN "DISCORD_BOT_TOKEN"
  prompt_required DISCORD_ALLOWED_USER_IDS "DISCORD_ALLOWED_USER_IDS (comma-separated Discord user IDs permitted to submit ideas)"
  prompt_default DISCORD_IDEA_CHANNEL_ID "DISCORD_IDEA_CHANNEL_ID (channel ID to listen in; leave blank for DMs only)" ""
  prompt_secret_optional TELEGRAM_BOT_TOKEN "TELEGRAM_BOT_TOKEN"
  TELEGRAM_ALLOWED_USER_IDS=""
else
  prompt_secret_required TELEGRAM_BOT_TOKEN "TELEGRAM_BOT_TOKEN"
  prompt_required TELEGRAM_ALLOWED_USER_IDS "TELEGRAM_ALLOWED_USER_IDS (comma-separated Telegram user IDs permitted to submit ideas)"
  prompt_secret_optional DISCORD_BOT_TOKEN "DISCORD_BOT_TOKEN"
  DISCORD_ALLOWED_USER_IDS=""
  DISCORD_IDEA_CHANNEL_ID=""
fi
prompt_default DRY_RUN "DRY_RUN (true|false)" "true"
prompt_default BACKEND_URL "BACKEND_URL for bot container" "http://backend:8000"

echo
echo "Deployment summary:"
echo "- Project: $PROJECT_ID"
echo "- Region/Zone: $REGION / $ZONE"
echo "- VM: $VM_NAME ($MACHINE_TYPE)"
echo "- BOT_PROVIDER: $BOT_PROVIDER"
echo "- DRY_RUN: $DRY_RUN"
echo
read -r -p "Proceed with deployment? [y/N]: " PROCEED
if [[ "${PROCEED,,}" != "y" ]]; then
  echo "Aborted."
  exit 0
fi

gcloud config set project "$PROJECT_ID" >/dev/null
gcloud services enable compute.googleapis.com >/dev/null

if ! gcloud compute instances describe "$VM_NAME" --zone "$ZONE" >/dev/null 2>&1; then
  echo "Creating VM $VM_NAME..."
  gcloud compute instances create "$VM_NAME" \
    --zone "$ZONE" \
    --machine-type "$MACHINE_TYPE" \
    --image-family "debian-12" \
    --image-project "debian-cloud" \
    --boot-disk-size "30GB" \
    --tags "http-server,https-server"
else
  echo "VM $VM_NAME already exists; reusing it."
fi

BACKEND_ENV_TMP="$(mktemp)"
BOT_ENV_TMP="$(mktemp)"
ARCHIVE_TMP="$(mktemp --suffix=.tar.gz)"
trap cleanup EXIT

cat >"$BACKEND_ENV_TMP" <<EOF
GITHUB_TOKEN=$GITHUB_TOKEN
GITHUB_REPO_OWNER=$GITHUB_REPO_OWNER
GITHUB_REPO_NAME=$GITHUB_REPO_NAME
GEMINI_API_KEY=$GEMINI_API_KEY
DRY_RUN=$DRY_RUN
EOF

cat >"$BOT_ENV_TMP" <<EOF
BOT_PROVIDER=$BOT_PROVIDER
DISCORD_BOT_TOKEN=$DISCORD_BOT_TOKEN
DISCORD_ALLOWED_USER_IDS=$DISCORD_ALLOWED_USER_IDS
DISCORD_IDEA_CHANNEL_ID=$DISCORD_IDEA_CHANNEL_ID
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
TELEGRAM_ALLOWED_USER_IDS=$TELEGRAM_ALLOWED_USER_IDS
BACKEND_URL=$BACKEND_URL
EOF

echo "Packaging repo..."
tar \
  --exclude='.git' \
  --exclude='.venv' \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  -czf "$ARCHIVE_TMP" .

echo "Preparing VM dependencies..."
gcloud compute ssh "$VM_NAME" --zone "$ZONE" --command "
set -euo pipefail
if ! command -v docker >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y ca-certificates curl gnupg
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    \"deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \\
    \$(. /etc/os-release && echo \$VERSION_CODENAME) stable\" | \
    sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi
mkdir -p $APP_DIR
"

echo "Uploading app and env files..."
gcloud compute scp --zone "$ZONE" "$ARCHIVE_TMP" "$VM_NAME:/tmp/idea-inbox.tar.gz"
gcloud compute scp --zone "$ZONE" "$BACKEND_ENV_TMP" "$VM_NAME:/tmp/.env.backend"
gcloud compute scp --zone "$ZONE" "$BOT_ENV_TMP" "$VM_NAME:/tmp/.env.bot"

echo "Deploying on VM..."
gcloud compute ssh "$VM_NAME" --zone "$ZONE" --command "
set -euo pipefail
mkdir -p $APP_DIR
tar -xzf /tmp/idea-inbox.tar.gz -C $APP_DIR
mv /tmp/.env.backend $APP_DIR/.env.backend
mv /tmp/.env.bot $APP_DIR/.env.bot
rm -f /tmp/idea-inbox.tar.gz
cd $APP_DIR
sudo docker compose up -d --build
sudo docker compose ps
"

echo
echo "Deployment complete."
echo "To inspect logs:"
echo "  gcloud compute ssh $VM_NAME --zone $ZONE --command 'cd $APP_DIR && sudo docker compose logs -f backend'"
echo "  gcloud compute ssh $VM_NAME --zone $ZONE --command 'cd $APP_DIR && sudo docker compose logs -f bot'"
