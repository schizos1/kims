#!/bin/bash
cd "$(dirname "$0")"
NOW=$(date "+%Y-%m-%d %H:%M:%S")
git add .
git commit -m "💾 자동 백업: $NOW"
git push localbackup main