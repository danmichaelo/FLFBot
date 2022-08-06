#!/bin/bash

echo "=== This is FFBot running on $(hostname) ==="

. ENV/bin/activate
python ffbot.py

