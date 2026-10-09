import json
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class Handler(BaseHTTPRequestHandler):
    requests = []

    def do_POST(self):
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.requests.append(request)
        if "produce-empty-output" in request["messages"][-1]["content"]:
            payload = {"choices": [{"message": {"content": ""}, "finish_reason": "stop"}]}
        else:
            payload = {
                "id": "local-fixture",
                "model": "local-fixture",
                "choices": [{"message": {"content": "Answer A"}, "finish_reason": "length" if "produce-truncated-output" in request["messages"][-1]["content"] else "stop"}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12},
            }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def log_message(self, format, *args):
        pass


def main():
    root = Path(__file__).resolve().parents[1]
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        with tempfile.TemporaryDirectory(prefix="pilot-client-check-") as directory:
            work = Path(directory)
            tasks = work / "tasks.jsonl"
            tasks.write_text(json.dumps({"task_id": "ordinary", "prompt": "Choose A or B."}) + "\n")
            environment = dict(os.environ, PILOT_API_KEY="local-fixture-key")
            command = [sys.executable, str(root / "scripts/run_prompt_pilot.py"), "--tasks", str(tasks), "--model", "local-fixture", "--base-url", f"http://127.0.0.1:{server.server_port}/v1", "--output", str(work / "successful")]
            completed = subprocess.run(command, env=environment, capture_output=True, text=True)
            assert completed.returncode == 0, completed.stderr
            records = [json.loads(line) for line in (work / "successful/results.jsonl").read_text().splitlines()]
            assert len(records) == 3 and all(row["status"] == "ok" for row in records)
            assert {row["condition"] for row in records} == {"direct", "reflection", "skill-prompt"}
            assert all(request["messages"][-1]["content"] == "Choose A or B." for request in Handler.requests)
            assert sum("<skill name=" in request["messages"][0]["content"] for request in Handler.requests) == 1
            artifacts = "\n".join(path.read_text() for path in (work / "successful").rglob("*.json"))
            assert "local-fixture-key" not in artifacts
            tasks.write_text(json.dumps({"task_id": "empty", "prompt": "produce-empty-output"}) + "\n")
            command[-1] = str(work / "empty")
            failed = subprocess.run(command, env=environment, capture_output=True, text=True)
            assert failed.returncode == 1
            summary = json.loads((work / "empty/usage-summary.json").read_text())
            assert all(row["failed"] == 1 and row["succeeded"] == 0 for row in summary.values())
            tasks.write_text(json.dumps({"task_id": "truncated", "prompt": "produce-truncated-output"}) + "\n")
            command[-1] = str(work / "truncated")
            truncated = subprocess.run(command, env=environment, capture_output=True, text=True)
            assert truncated.returncode == 1
            summary = json.loads((work / "truncated/usage-summary.json").read_text())
            assert all(row["failed"] == 1 and row["truncated"] == 1 for row in summary.values())
            print("PASS: nonempty truncated outputs count as failures with usage retained.")
            print("PASS: identical task evidence, treatment-only instructions, complete per-call artifacts and usage.")
            print("PASS: empty provider outputs count as failures and no credential is saved in artifacts.")
            print("These are local client checks, not scientific model results.")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
