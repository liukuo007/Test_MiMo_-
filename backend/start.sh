#!/bin/sh
set -e

echo "=== Initializing Database & Seeding Data ==="
python -c "
import asyncio
from scripts.seed_data import seed
asyncio.run(seed())
"

echo "=== Starting Server ==="
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
