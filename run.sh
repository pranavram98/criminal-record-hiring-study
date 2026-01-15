#!/usr/bin/env bash
set -e

# Debug info
pwd
ls -la

# Create fake output dirs
mkdir -p /app/output_csvs_openai
mkdir -p /app/output_csvs_anthropic
mkdir -p /app/output_csvs_mistral

# Create test CSVs
echo "id,value" > /app/output_csvs_openai/test_openai.csv
echo "id,value" > /app/output_csvs_anthropic/test_anthropic.csv
echo "id,value" > /app/output_csvs_mistral/test_mistral.csv

# Setup rclone
mkdir -p ~/.config/rclone
cat > ~/.config/rclone/rclone.conf <<EOF
[gdrive]
type = drive
scope = drive
service_account_credentials = ${GDRIVE_SERVICE_ACCOUNT_JSON}
root_folder_id = ${FOLDER_ID}
EOF

# Upload
rclone copy /app/output_csvs_openai gdrive:output_csvs_openai --progress
rclone copy /app/output_csvs_anthropic gdrive:output_csvs_anthropic --progress
rclone copy /app/output_csvs_mistral gdrive:output_csvs_mistral --progress
