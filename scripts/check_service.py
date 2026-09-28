"""Run real HTTP probes without printing secrets; save stdout as evidence.

Usage: python scripts/check_service.py http://127.0.0.1:8000
For cloud, set DEPLOY_API_KEY in .env (not in the command line).
"""
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import dotenv_values


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    base = sys.argv[1].rstrip("/")
    values = dotenv_values(Path(__file__).resolve().parents[1] / ".env")
    key = values.get("DEPLOY_API_KEY") if base.startswith("https://") else values.get("AGENT_API_KEY")
    results = {"timestamp": datetime.now(timezone.utc).isoformat(), "base_url": base, "checks": []}

    def record(name, response):
        results["checks"].append({"name": name, "status": response.status_code, "body": response.json()})

    with httpx.Client(base_url=base, timeout=90) as client:
        record("health", client.get("/health"))
        record("ready", client.get("/ready"))
        record("missing_key", client.post("/ask", json={"question": "Hello"}))
        record("wrong_key", client.post("/ask", json={"question": "Hello"}, headers={"X-API-Key": "invalid"}))
        if key:
            headers = {"X-API-Key": key, "X-User-Id": "evidence-" + uuid.uuid4().hex[:10]}
            for i in range(12):
                response = client.post("/ask", json={"question": "Explain Docker"}, headers=headers)
                record(f"ask_{i + 1}", response)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    checks = results["checks"]
    assert [c["status"] for c in checks[:4]] == [200, 200, 401, 401]
    if key:
        assert [c["status"] for c in checks[4:]] == [200] * 10 + [429] * 2
        assert [c["body"]["history_length"] for c in checks[4:14]] == list(range(0, 20, 2))


if __name__ == "__main__":
    main()
