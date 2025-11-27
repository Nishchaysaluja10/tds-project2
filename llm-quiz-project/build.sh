#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
playwright install-deps
echo "Installing Playwright browsers to $PLAYWRIGHT_BROWSERS_PATH"
playwright install chromium
