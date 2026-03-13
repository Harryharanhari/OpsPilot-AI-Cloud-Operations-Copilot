"""
Local development runner for OpsPilot.
No Docker needed — uses SQLite by default (set USE_SQLITE=true in .env).

Usage:
    python run.py
"""
import os
import sys

# Load .env before importing app modules
from pathlib import Path
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)
    print(f"✅ Loaded .env from {env_file}")

import uvicorn

if __name__ == "__main__":
    print("\n🚀 Starting OpsPilot locally...")
    use_sqlite = os.getenv("USE_SQLITE", "false").lower() == "true"
    if use_sqlite:
        print("🗄️  Database: SQLite (opspilot.db) — no PostgreSQL needed")
    else:
        host = os.getenv("POSTGRES_HOST", "localhost")
        db = os.getenv("POSTGRES_DB", "opspilot")
        print(f"🗄️  Database: PostgreSQL @ {host}/{db}")

    print("🌐 Server: http://localhost:8000\n")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app"]
    )
