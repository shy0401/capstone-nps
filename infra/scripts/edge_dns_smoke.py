"""Verify edge DNS refresh using isolated synthetic backends, without media or published ports."""

import json
import subprocess
import time
import uuid
from pathlib import Path

from manage import docker_binary

ROOT = Path(__file__).resolve().parents[2]


def run():
    docker = docker_binary()
    prefix = "nps-dns-" + uuid.uuid4().hex[:10]
    network, first, second, edge = [prefix + suffix for suffix in ["-net", "-a", "-b", "-edge"]]

    def command(*args, check=True):
        return subprocess.run(
            [docker, *args],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=check,
        )

    def backend(name, label):
        server = (
            "from http.server import BaseHTTPRequestHandler,HTTPServer\n"
            "class Handler(BaseHTTPRequestHandler):\n"
            " def do_GET(self):\n"
            "  self.send_response(200); self.end_headers(); "
            f"self.wfile.write({label.encode()!r})\n"
            "HTTPServer(('0.0.0.0',8000),Handler).serve_forever()"
        )
        command(
            "run",
            "-d",
            "--name",
            name,
            "--network",
            network,
            "--network-alias",
            "api",
            "--entrypoint",
            "python",
            "capstone-nps-api:0.1.1",
            "-c",
            server,
        )

    def expect(label):
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            result = command(
                "exec", edge, "wget", "-qO-", "-T", "2", "http://127.0.0.1:8080/api/dns-test", check=False
            )
            if result.returncode == 0 and result.stdout == label:
                return
            time.sleep(1)
        raise AssertionError("Edge did not resolve replacement backend: " + label)

    try:
        command("network", "create", "--internal", network)
        backend(first, "before")
        command("run", "-d", "--name", edge, "--network", network, "capstone-nps-edge:0.1.1")
        expect("before")
        # Allocate the second backend while the first exists to guarantee a different IP.
        backend(second, "after")
        command("rm", "-f", first)
        expect("after")
        result = {
            "status": "PASS",
            "backend_ip_changed": True,
            "edge_restarted": False,
            "published_ports": [],
            "media_generated": False,
        }
        (ROOT / "test-results/edge-dns-result.json").write_text(
            json.dumps(result, indent=2), encoding="utf-8"
        )
        print(json.dumps(result))
    finally:
        command("rm", "-f", first, second, edge, check=False)
        command("network", "rm", network, check=False)


if __name__ == "__main__":
    run()
