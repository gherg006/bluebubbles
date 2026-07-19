"""Measure reproducible local component baselines without external services."""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import time
import tracemalloc
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final
from uuid import UUID

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from bluebubbles.client.services.search import SearchTokenService
from bluebubbles.server.application import create_application
from bluebubbles.server.configuration.settings import ServerSettings
from bluebubbles.shared.protocol.serialisation import canonical_json_bytes
from bluebubbles.version import __version__

MIB: Final = 1024 * 1024


class _SyntheticKeyProvider:
    """Provide deterministic non-production material for a local search probe."""

    async def get_master_key(self) -> bytes:
        """Return fixed synthetic key bytes without touching the secure store."""
        return bytes(range(32))


@dataclass(frozen=True, slots=True)
class PerformanceMeasurement:
    """Record one bounded local measurement and its acceptance threshold."""

    test_id: str
    name: str
    value: float
    unit: str
    threshold: float
    comparison: str
    passed: bool
    iterations: int


def _latency_measurement(
    test_id: str,
    name: str,
    operation: Callable[[], object],
    *,
    iterations: int,
    threshold_ms: float,
) -> PerformanceMeasurement:
    """Measure median single-operation latency after one warm-up invocation."""
    operation()
    samples = []
    for _ in range(iterations):
        started = time.perf_counter_ns()
        operation()
        samples.append((time.perf_counter_ns() - started) / 1_000_000)
    value = statistics.median(samples)
    return PerformanceMeasurement(
        test_id,
        name,
        round(value, 4),
        "ms median",
        threshold_ms,
        "less_than",
        value < threshold_ms,
        iterations,
    )


def measure() -> dict[str, object]:
    """Return local startup, serialization, search, and crypto baselines."""
    key = bytes(range(32))
    nonce = bytes(range(12))
    message = b"m" * 8000
    cipher = AESGCM(key)
    canonical_payload = {
        "conversation_id": UUID(int=1),
        "message_id": UUID(int=2),
        "text": "synthetic performance message" * 100,
        "recipient_ids": [UUID(int=index) for index in range(1, 101)],
    }
    search_text = " ".join(f"synthetic{index}" for index in range(10_000))
    token_service = SearchTokenService(_SyntheticKeyProvider())
    measurements = [
        _latency_measurement(
            "PERF-COMPONENT-001",
            "AES-256-GCM 8000-byte message encryption",
            lambda: cipher.encrypt(nonce, message, b"synthetic-aad"),
            iterations=500,
            threshold_ms=5.0,
        ),
        _latency_measurement(
            "PERF-COMPONENT-002",
            "canonical serialization with 100 recipients",
            lambda: canonical_json_bytes(canonical_payload),
            iterations=500,
            threshold_ms=5.0,
        ),
        _latency_measurement(
            "PERF-COMPONENT-003",
            "Unicode search tokenization of 10000 words",
            lambda: token_service.normalise(search_text),
            iterations=50,
            threshold_ms=500.0,
        ),
        _latency_measurement(
            "PERF-COMPONENT-004",
            "FastAPI application construction without infrastructure startup",
            lambda: create_application(ServerSettings()),
            iterations=20,
            threshold_ms=2000.0,
        ),
    ]
    large_payload = b"a" * (16 * MIB)
    tracemalloc.start()
    started = time.perf_counter()
    encrypted = cipher.encrypt(nonce, large_payload, b"synthetic-attachment")
    elapsed = time.perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    throughput = len(large_payload) / MIB / elapsed
    measurements.extend(
        (
            PerformanceMeasurement(
                "PERF-COMPONENT-005",
                "AES-GCM attachment buffer throughput",
                round(throughput, 2),
                "MiB/s",
                10.0,
                "greater_than",
                throughput > 10.0,
                1,
            ),
            PerformanceMeasurement(
                "PERF-COMPONENT-006",
                "AES-GCM attachment peak traced allocation",
                round(peak / MIB, 2),
                "MiB",
                64.0,
                "less_than",
                peak / MIB < 64.0,
                1,
            ),
        )
    )
    del encrypted, large_payload
    return {
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "application_version": __version__,
        "environment": {
            "operating_system": platform.platform(),
            "python": platform.python_version(),
            "processor": platform.processor() or "not reported by operating system",
            "logical_cpu_count": os.cpu_count(),
            "external_services": "none",
            "dataset": "synthetic in-memory component baselines",
        },
        "scope_limitation": (
            "These are local component baselines, not LAN, PostgreSQL, Redis, "
            "WebSocket, GUI, or full end-to-end acceptance measurements."
        ),
        "measurements": [asdict(item) for item in measurements],
        "passed": all(item.passed for item in measurements),
    }


def main() -> int:
    """Measure, print, optionally persist, and return the aggregate result."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    report = measure()
    serialised = json.dumps(report, indent=2) + "\n"
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(serialised, encoding="utf-8")
    print(serialised, end="")
    return 0 if report["passed"] is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
