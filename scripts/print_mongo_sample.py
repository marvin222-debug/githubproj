#!/usr/bin/env python3
"""
Quick MongoDB connectivity check and data dump for ANPR vehicles collection.
"""

import os
import sys
import json


def main() -> int:
    # Ensure project root is on sys.path so we import root-level config
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    try:
        from pymongo import MongoClient
    except Exception as exc:
        print(json.dumps({"connected": False, "error": f"pymongo not available: {exc}"}))
        return 1

    try:
        # Import root config (D:\...\config\config.py)
        from config.config import DB_URI, DB_NAME, DB_COLLECTION
    except Exception as exc:
        print(json.dumps({"connected": False, "error": f"config import failed: {exc}"}))
        return 1

    try:
        client = MongoClient(DB_URI, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        db = client[DB_NAME]
        col = db[DB_COLLECTION]

        count = col.count_documents({})
        docs = list(col.find({}, {"_id": 0}).limit(20))

        print(json.dumps({
            "connected": True,
            "db": DB_NAME,
            "collection": DB_COLLECTION,
            "count": count,
            "docs": docs
        }, default=str))
        return 0
    except Exception as exc:
        print(json.dumps({"connected": False, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())



