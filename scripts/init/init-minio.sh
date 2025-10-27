#!/bin/bash
# ===========================================
# MinIO Initialization Script
# ===========================================
# Creates buckets and sets up policies

set -e

# Wait for MinIO to be ready
echo "Waiting for MinIO to be ready..."
until mc alias set minio http://minio:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD}; do
    echo "MinIO is not ready yet. Retrying in 5 seconds..."
    sleep 5
done

echo "MinIO is ready. Initializing buckets..."

# Create buckets
mc mb --ignore-existing minio/rika-backups
mc mb --ignore-existing minio/rika-models
mc mb --ignore-existing minio/rika-media
mc mb --ignore-existing minio/rika-artifacts
mc mb --ignore-existing minio/rika-temp

# Set bucket policies
# Backups - private
mc policy set none minio/rika-backups

# Models - read-only for authenticated users
mc policy set download minio/rika-models

# Media - public read for served content
mc policy set public minio/rika-media

# Artifacts - private
mc policy set none minio/rika-artifacts

# Temp - auto-expire after 7 days
mc ilm add --expiry-days 7 minio/rika-temp

# Create lifecycle rules for backups (keep 30 days)
cat > /tmp/backup-lifecycle.json <<EOF
{
    "Rules": [
        {
            "ID": "backup-retention",
            "Status": "Enabled",
            "Expiration": {
                "Days": 30
            }
        }
    ]
}
EOF

mc ilm import minio/rika-backups < /tmp/backup-lifecycle.json

# Set versioning on critical buckets
mc version enable minio/rika-backups
mc version enable minio/rika-models

# Create service accounts for different components
echo "Creating service accounts..."

# n8n service account
mc admin user add minio n8n-user n8n-password-change-me
mc admin policy set minio readwrite user=n8n-user

# Backup service account (full access to backup bucket only)
mc admin user add minio backup-user backup-password-change-me
cat > /tmp/backup-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:*"],
            "Resource": ["arn:aws:s3:::rika-backups/*"]
        }
    ]
}
EOF
mc admin policy add minio backup-policy /tmp/backup-policy.json
mc admin policy set minio backup-policy user=backup-user

# Create notification endpoints (webhook to n8n)
# mc admin config set minio notify_webhook:1 \
#     endpoint="http://n8n:5678/webhook/minio-events" \
#     queue_dir="/data/.minio/events"

# Set up bucket notifications
# mc event add minio/rika-backups \
#     arn:minio:sqs::1:webhook \
#     --event put,delete \
#     --prefix "backup-" \
#     --suffix ".json"

echo "MinIO initialization completed successfully!"
echo "========================="
echo "Buckets created:"
echo "  - rika-backups (versioned, 30-day retention)"
echo "  - rika-models (versioned)"
echo "  - rika-media (public read)"
echo "  - rika-artifacts (private)"
echo "  - rika-temp (7-day auto-expiry)"
echo "========================="