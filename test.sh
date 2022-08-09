#!/bin/bash
export LC_ALL=C
set -e -o pipefail

TARGET_WHEEL=$(find . -maxdepth 2 -type f -regex ".*libdogecoin-.*")
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade wheel pytest
wheel unpack "$TARGET_WHEEL"
cp -r libdogecoin-*/* .
python3 -m pytest
deactivate
rm -rf .venv *.so libdogecoin-*/ *.libs tests/__pycache__ .pytest_cache
