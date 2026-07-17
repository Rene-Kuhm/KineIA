import json
import os
import re
import subprocess
import sys
from pathlib import Path

ONNX_PCI_WARNING = re.compile(
    r"(?:\x1b\[0;93m)?\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+ "
    r"\[W:onnxruntime:Default, device_discovery\.cc:\d+ GetPciBusId\] "
    r'Skipping pci_bus_id for PCI path at "/sys/devices/[A-Za-z0-9:._/-]+" '
    r'because filename "[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}" '
    r"did not match expected pattern of \[0-9a-f\]\+:\[0-9a-f\]\+:"
    r"\[0-9a-f\]\+\[\.\]\[0-9a-f\]\+(?:\x1b\[m)?\n")


def diagnostics_are_safe(stderr):
    return not stderr or ONNX_PCI_WARNING.fullmatch(stderr) is not None


def test_preflight_cli_emits_json_and_nonzero_when_qdrant_is_unreachable():
    backend = Path(__file__).parents[1]
    environment = os.environ | {"QDRANT_URL": "http://127.0.0.1:1"}
    result = subprocess.run(
        [sys.executable, "scripts/qdrant_preflight.py"],
        cwd=backend,
        env=environment,
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 2
    assert diagnostics_are_safe(result.stderr)
    assert len(result.stdout.splitlines()) == 1
    assert json.loads(result.stdout)["status"] == "unreachable"


def test_preflight_diagnostic_policy_rejects_unsanitized_errors():
    warning = (
        '\x1b[0;93m2026-07-17 05:14:33.471618474 [W:onnxruntime:Default, '
        'device_discovery.cc:133 GetPciBusId] Skipping pci_bus_id for PCI path at '
        '"/sys/devices/LNXSYSTM:00/VMBUS:00/5620e0c7-8062-4dce-aeb7-520c7ef76171" '
        'because filename "5620e0c7-8062-4dce-aeb7-520c7ef76171" did not match '
        'expected pattern of [0-9a-f]+:[0-9a-f]+:[0-9a-f]+[.][0-9a-f]+\x1b[m\n'
    )
    assert diagnostics_are_safe("") and diagnostics_are_safe(warning)
    suffixes = (" secret", " token", " password", " api-key", " Bearer", " /x.py:1")
    for suffix in suffixes:
        assert not diagnostics_are_safe(warning.rstrip() + suffix + "\n")


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
