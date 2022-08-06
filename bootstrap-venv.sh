#!/bin/bash
# Usage:
# toolforge-jobs run bootstrap-venv --command "./bootstrap-venv.sh" --image tf-python39 --wait
set -euo pipefail

# create the venv
if [ -d ENV ]; then
    echo "Removing old venv"
    rm -r ENV
fi

echo "Creating new venv ($(python3 --version))"
mkdir -p ENV
python3 -m venv ENV

# activate it
. ENV/bin/activate

# upgrade pip inside the venv and add support for the wheel package format
pip install -U pip wheel

pip install -r requirements.txt


# osv...
