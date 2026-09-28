"""Record real container sharing, non-root runtime and Docker cache evidence."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "screenshots"


def run(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True, encoding="utf-8")


def main():
    user = "scale-" + uuid.uuid4().hex[:8]
    rows = []
    for i in range(6):
        name = f"day12-scale-agent-{i % 3 + 1}"
        code = (
            "import os,json,urllib.request; "
            "data=json.dumps({'question':'Explain shared Redis'}).encode(); "
            "req=urllib.request.Request('http://127.0.0.1:8000/ask',data=data,"
            "headers={'Content-Type':'application/json',"
            "'X-API-Key':os.environ['AGENT_API_KEY'],'X-User-Id':" + repr(user) + "}); "
            "print(urllib.request.urlopen(req).read().decode())"
        )
        body = json.loads(run("docker", "exec", name, "python", "-c", code))
        rows.append({"container": name, "history_length": body["history_length"]})
    assert [r["history_length"] for r in rows] == [0, 2, 4, 6, 8, 10]
    (EVIDENCE / "scale-results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps(rows), flush=True)
    uid = run("docker", "exec", "day12-scale-agent-1", "id", "-u").strip()
    assert uid == "10001"
    (EVIDENCE / "docker-runtime.txt").write_text(
        "Runtime UID: " + uid + "\n" + run("docker", "compose", "-p", "day12-scale", "-f", "docker-compose.scale.yml", "ps"),
        encoding="utf-8",
    )
    # Copy only build inputs; never put .env into the experimental context.
    with tempfile.TemporaryDirectory(prefix="day12-cache-") as folder:
        context = Path(folder)
        for name in ("app", "utils"):
            shutil.copytree(ROOT / name, context / name, ignore=shutil.ignore_patterns("__pycache__"))
        for name in ("Dockerfile", "requirements.txt", ".dockerignore"):
            shutil.copy2(ROOT / name, context / name)
        with (context / "app" / "main.py").open("a", encoding="utf-8") as stream:
            stream.write("\n# Cache experiment.\n")
        result = subprocess.run(
            ["docker", "build", "--progress=plain", "-t", "day12-agent:cache-check", str(context)],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=900,
        )
        (EVIDENCE / "docker-cache.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
        assert result.returncode == 0, result.stderr[-1500:]
    print("Non-root runtime and cache experiment completed.", flush=True)


if __name__ == "__main__":
    main()
