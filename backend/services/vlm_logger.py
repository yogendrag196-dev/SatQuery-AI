"""
vlm_logger.py
Audit Logger for Vision-Language Model prompts, responses, reasoning traces, and latency.
Persists records to MongoDB (database: satquery_db, collection: vlm_audit_logs)
with automatic fallback to JSON persistence.
"""

import os
import json
import time
from datetime import datetime
from config import Config

class VLMAuditLogger:
    def __init__(self):
        self.mongo_client = None
        self.mongo_collection = None
        self.log_file = os.path.join(Config.DATA_DIR, "vlm_audit_logs.json")
        self._init_mongo()

    def _init_mongo(self):
        mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
        try:
            from pymongo import MongoClient
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=800)
            client.admin.command('ping')
            self.mongo_client = client
            db = self.mongo_client["satquery_db"]
            self.mongo_collection = db["vlm_audit_logs"]
            print("[VLMAuditLogger] Connected to MongoDB (satquery_db.vlm_audit_logs)")
        except Exception:
            self.mongo_client = None
            self.mongo_collection = None

    def log_interaction(self, endpoint, prompt, response_text, image_metadata=None, structured_data=None, latency_ms=0.0, model="gemini-2.5-flash"):
        """
        Logs a single VLM prompt, response, metadata, and reasoning trace.
        """
        record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "endpoint": endpoint,
            "model": model,
            "prompt": prompt,
            "response": response_text,
            "image_metadata": image_metadata or {},
            "structured_data": structured_data or {},
            "latency_ms": round(latency_ms, 2)
        }

        # 1. Write to MongoDB if connected
        if self.mongo_collection is not None:
            try:
                self.mongo_collection.insert_one(record.copy())
            except Exception as ex:
                pass

        # 2. Write to local JSON audit trail
        self._append_to_file(record)
        return record

    def _append_to_file(self, record):
        try:
            logs = []
            if os.path.exists(self.log_file):
                try:
                    with open(self.log_file, "r") as f:
                        logs = json.load(f)
                except Exception:
                    logs = []

            logs.append(record)
            # Keep most recent 200 logs
            if len(logs) > 200:
                logs = logs[-200:]

            with open(self.log_file, "w") as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            print(f"[VLMAuditLogger] Error saving audit log to file: {e}")

    def get_logs(self, limit=50):
        """
        Retrieves recent audit logs from MongoDB or fallback file.
        """
        if self.mongo_collection is not None:
            try:
                cursor = self.mongo_collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
                return list(cursor)
            except Exception:
                pass

        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as f:
                    logs = json.load(f)
                    return list(reversed(logs))[:limit]
            except Exception:
                return []
        return []

# Singleton instance
vlm_logger = VLMAuditLogger()
