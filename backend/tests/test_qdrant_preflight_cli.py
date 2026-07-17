import json
import os
import subprocess
import sys
from pathlib import Path


def test_preflight_cli_emits_json_and_nonzero_when_qdrant_is_unreachable():
    backend = Path(__file__).parents[1]
    environment = os.environ | {"QDRANT_URL": "http://127.0.0.1:1"}

    result = subprocess.run(
        [sys.executable, "scripts/qdrant_preflight.py"],
        cwd=backend,
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode == 2
    assert result.stderr == ""
    assert json.loads(result.stdout)["status"] == "unreachable"


def test_qdrant_yaml_uses_runner_readyz_without_container_tools():
    root = Path(__file__).parents[2]
    compose = (root / "docker-compose.yml").read_text(encoding="utf-8")
    qdrant_service = compose.split("\n  qdrant:\n", 1)[1].split("\nvolumes:", 1)[0]
    workflow = (root / ".github/workflows/backend-ci.yml").read_text(encoding="utf-8")
    wait_step = workflow.split("- name: Wait for Qdrant", 1)[1].split("- name:", 1)[0]
    env_example = (root / ".env.example").read_text(encoding="utf-8")

    assert "healthcheck:" not in qdrant_service
    assert "condition: service_started" in compose
    assert "http://127.0.0.1:6333/readyz" in wait_step
    assert not any(tool in wait_step for tool in ("wget", "curl", " nc "))
    assert "cd backend; uv run --no-sync python scripts/qdrant_preflight.py" in env_example
