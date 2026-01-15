#!/usr/bin/env bash
set -euo pipefail

: "${GDRIVE_SERVICE_ACCOUNT_JSON:?missing}"
: "${TEAM_DRIVE_ID:?missing}"

RCLONE_DIR="/root/.config/rclone"
mkdir -p "${RCLONE_DIR}"

# write service account json
printf "%s" "$GDRIVE_SERVICE_ACCOUNT_JSON" > "${RCLONE_DIR}/sa.json"

# write rclone config for Shared Drive
cat > "${RCLONE_DIR}/rclone.conf" <<EOF
[gdrive]
type = drive
scope = drive
service_account_file = ${RCLONE_DIR}/sa.json
team_drive = ${TEAM_DRIVE_ID}
root_folder_id = ${FOLDER_ID}
EOF

# sanity
rclone version

# create test file
echo "hello from railway shared drive test" > /app/test_upload.txt

# upload
rclone copy /app/test_upload.txt gdrive:test_run --progress

echo "TEST COMPLETE"