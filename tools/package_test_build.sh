#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"
ARCHIVE_NAME="sunny-devfix-v0.2.0.tar.gz"
CHECKSUM_FILE="${DIST_DIR}/SHA256SUMS"

mkdir -p "${DIST_DIR}"

echo "Packaging Sunny-DevFix judge-accessible test build..."

tar --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='dist' \
    --exclude='.DS_Store' \
    -czf "${DIST_DIR}/${ARCHIVE_NAME}" \
    -C "${ROOT_DIR}" \
    src tests tools docs extensions Dockerfile Makefile pyproject.toml requirements.lock requirements-dev.lock README.md LICENSE .env.example

cd "${DIST_DIR}"
shasum -a 256 "${ARCHIVE_NAME}" > "${CHECKSUM_FILE}"

echo "Test build archive created:"
echo "  Path:     ${DIST_DIR}/${ARCHIVE_NAME}"
echo "  Size:     $(du -h "${DIST_DIR}/${ARCHIVE_NAME}" | cut -f1)"
echo "  Checksum: $(cat "${CHECKSUM_FILE}")"
