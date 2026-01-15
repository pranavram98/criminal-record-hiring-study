#!/usr/bin/env bash
set -euo pipefail

echo "=== RCLONE OAUTH TEST START ==="

# -------------------------
# 0) Sanity check
# -------------------------
: "${RCLONE_CONF:?Missing RCLONE_CONF environment variable}"

# -------------------------
# 1) Ensure rclone exists
# -------------------------
echo "Checking rclone..."
which rclone
rclone version

# -------------------------
# 2) Write rclone config
# -------------------------
echo "Writing rclone config..."
mkdir -p /root/.config/rclone
printf "%s" "$RCLONE_CONF" > /root/.config/rclone/rclone.conf

echo "rclone config written:"
sed 's/token = .*/token = <REDACTED>/' /root/.config/rclone/rclone.conf

# -------------------------
# 3) Create test file
# -------------------------
echo "Creating test file..."
echo "hello from railway oauth test" > /app/test_upload.txt
ls -la /app/test_upload.txt

# -------------------------
# 4) Upload to Google Drive
# -------------------------
echo "Uploading test file..."
rclone copy /app/test_upload.txt gdrive:test_run --progress

echo "=== TEST COMPLETE ==="