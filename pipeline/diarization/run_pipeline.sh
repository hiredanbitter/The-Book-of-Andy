#!/bin/bash
# Cloud-init startup script for the Lambda GPU instance.
# Environment variables (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, OPENAI_API_KEY,
# HUGGING_FACE_TOKEN, LAMBDA_API_KEY, EPISODE_IDS, GITHUB_DEPLOY_TOKEN) are
# injected by lambda_client.py when this script is passed as user_data.

set -euo pipefail

LOGFILE="/var/log/pipeline.log"
REPO_DIR="/root/The-Book-of-Andy"
INSTANCE_NAME="book-of-andy-pipeline"

log() {
    echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] $*" | tee -a "$LOGFILE"
}

log "=== Pipeline startup ==="

# -------------------------------------------------------
# 1. Install system dependencies
# -------------------------------------------------------
log "Installing system dependencies..."
apt-get update -y >> "$LOGFILE" 2>&1
apt-get install -y ffmpeg git python3-pip python3-venv >> "$LOGFILE" 2>&1
log "System dependencies installed."

# -------------------------------------------------------
# 2. Clone the repository
# -------------------------------------------------------
log "Cloning repository..."
git clone "https://${GITHUB_DEPLOY_TOKEN}@github.com/hiredanbitter/The-Book-of-Andy.git" "$REPO_DIR" >> "$LOGFILE" 2>&1
cd "$REPO_DIR"
log "Repository cloned."

# -------------------------------------------------------
# 3. Set up Python environment and install dependencies
# -------------------------------------------------------
log "Setting up Python environment..."
python3 -m venv /root/pipeline-venv
source /root/pipeline-venv/bin/activate
pip install --upgrade pip >> "$LOGFILE" 2>&1
pip install -r pipeline/requirements.txt >> "$LOGFILE" 2>&1
log "Python dependencies installed."

# -------------------------------------------------------
# 4. Process each episode
# -------------------------------------------------------
IFS=',' read -ra EPISODE_ARRAY <<< "$EPISODE_IDS"
TOTAL=${#EPISODE_ARRAY[@]}
SUCCEEDED=0
FAILED=0

log "Processing $TOTAL episode(s): ${EPISODE_IDS}"

for EPISODE_ID in "${EPISODE_ARRAY[@]}"; do
    EPISODE_ID=$(echo "$EPISODE_ID" | xargs)  # trim whitespace
    log "--- Starting episode: $EPISODE_ID ---"

    if python3 pipeline/diarization/transcribe.py "$EPISODE_ID" >> "$LOGFILE" 2>&1; then
        log "transcribe.py completed for episode $EPISODE_ID."
    else
        log "ERROR: transcribe.py failed for episode $EPISODE_ID. Skipping remaining steps."
        FAILED=$((FAILED + 1))
        continue
    fi

    if python3 pipeline/diarization/diarize.py "$EPISODE_ID" >> "$LOGFILE" 2>&1; then
        log "diarize.py completed for episode $EPISODE_ID."
    else
        log "ERROR: diarize.py failed for episode $EPISODE_ID. Skipping remaining steps."
        FAILED=$((FAILED + 1))
        continue
    fi

    if python3 pipeline/diarization/format_output.py "$EPISODE_ID" >> "$LOGFILE" 2>&1; then
        log "format_output.py completed for episode $EPISODE_ID."
    else
        log "ERROR: format_output.py failed for episode $EPISODE_ID. Skipping remaining steps."
        FAILED=$((FAILED + 1))
        continue
    fi

    if python3 pipeline/diarization/ingest.py "$EPISODE_ID" >> "$LOGFILE" 2>&1; then
        log "ingest.py completed for episode $EPISODE_ID."
        SUCCEEDED=$((SUCCEEDED + 1))
    else
        log "ERROR: ingest.py failed for episode $EPISODE_ID."
        FAILED=$((FAILED + 1))
        continue
    fi

    log "--- Finished episode: $EPISODE_ID ---"
done

log "=== Pipeline complete: $SUCCEEDED/$TOTAL succeeded, $FAILED/$TOTAL failed ==="

# -------------------------------------------------------
# 5. Self-terminate the instance
# -------------------------------------------------------
log "Retrieving instance ID for self-termination..."

INSTANCE_ID=$(curl -s \
    -H "Authorization: Bearer ${LAMBDA_API_KEY}" \
    "https://cloud.lambda.ai/api/v1/instances" \
    | python3 -c "
import json, sys
data = json.load(sys.stdin).get('data', [])
for inst in data:
    if inst.get('name') == '${INSTANCE_NAME}':
        print(inst['id'])
        sys.exit(0)
print('', file=sys.stderr)
sys.exit(1)
" || true)

if [ -n "$INSTANCE_ID" ]; then
    log "Found instance ID: $INSTANCE_ID. Terminating..."
    curl -s -X POST \
        -H "Authorization: Bearer ${LAMBDA_API_KEY}" \
        -H "Content-Type: application/json" \
        -d "{\"instance_ids\": [\"${INSTANCE_ID}\"]}" \
        "https://cloud.lambda.ai/api/v1/instance-operations/terminate" >> "$LOGFILE" 2>&1
    log "Terminate request sent."
else
    log "ERROR: Could not determine instance ID. Manual termination required."
fi

log "=== Script exiting ==="
