#!/bin/bash
cd "$(dirname "$0")/frontend" || exit 1
exec npm run dev -- --host 0.0.0.0
