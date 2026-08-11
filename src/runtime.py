"""Deterministic manifests, incremental checks and atomic publication helpers."""

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .config import BASE_DIR, PIPELINE_VERSION, SCHEMA_VERSION, PipelinePaths


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_normalized_text(path: Path) -> str:
    payload = path.read_bytes().replace(b"\r\n", b"\n")
    return sha256_bytes(payload)


def pipeline_code_hash() -> str:
    digest = hashlib.sha256()
    tracked_inputs = sorted((BASE_DIR / "src").glob("*.py")) + [
        BASE_DIR / "requirements.lock"
    ]
    for path in tracked_inputs:
        digest.update(str(path.relative_to(BASE_DIR)).replace("\\", "/").encode())
        digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def build_input_state(
    customers_path: Path,
    yelp_path: Path,
    mapping_path: Path,
    customer_rows: int,
    yelp_rows: int,
    mapping_rows: int,
) -> list[dict]:
    inputs = (
        ("customers", customers_path, customer_rows),
        ("yelp", yelp_path, yelp_rows),
        ("category_mapping", mapping_path, mapping_rows),
    )
    return [
        {
            "dataset": label,
            "file": path.name,
            "rows": rows,
            "sha256": sha256_normalized_text(path),
        }
        for label, path, rows in inputs
    ]


def deterministic_run_id(mode: str, inputs: list[dict], code_hash: str) -> str:
    identity = json.dumps(
        {
            "mode": mode,
            "pipeline_version": PIPELINE_VERSION,
            "schema_version": SCHEMA_VERSION,
            "code_sha256": code_hash,
            "inputs": inputs,
        },
        sort_keys=True,
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256_bytes(identity)[:16]


def _relative_output(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def build_manifest(
    paths: PipelinePaths,
    inputs: list[dict],
    code_hash: str,
    output_payloads: dict[Path, bytes],
    row_counts: dict[Path, int | None],
) -> dict:
    run_id = deterministic_run_id(paths.mode, inputs, code_hash)
    outputs = []
    for path in sorted(
        output_payloads,
        key=lambda item: _relative_output(item, paths.publication_root),
    ):
        outputs.append(
            {
                "file": _relative_output(path, paths.publication_root),
                "rows": row_counts.get(path),
                "sha256": sha256_bytes(output_payloads[path]),
            }
        )
    return {
        "manifest_version": "1.0.0",
        "pipeline_version": PIPELINE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "mode": paths.mode,
        "run_id": run_id,
        "code_sha256": code_hash,
        "inputs": inputs,
        "outputs": outputs,
    }


def manifest_is_current(
    paths: PipelinePaths,
    inputs: list[dict],
    code_hash: str,
) -> tuple[bool, str | None]:
    if not paths.pipeline_manifest.exists():
        return False, "manifest_missing"
    try:
        manifest = json.loads(paths.pipeline_manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, "manifest_invalid"

    expected_identity = {
        "pipeline_version": PIPELINE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "mode": paths.mode,
        "code_sha256": code_hash,
        "inputs": inputs,
    }
    for key, expected in expected_identity.items():
        if manifest.get(key) != expected:
            return False, f"changed_{key}"

    for output in manifest.get("outputs", []):
        output_path = paths.publication_root / output["file"]
        if not output_path.exists():
            return False, f"missing_output:{output['file']}"
        if sha256_file(output_path) != output["sha256"]:
            return False, f"changed_output:{output['file']}"
    return True, None


def atomic_publish(payloads: dict[Path, bytes]) -> None:
    """Replace a bundle and restore its prior state if any replacement fails."""
    temporary: dict[Path, Path] = {}
    backups: dict[Path, Path | None] = {}
    published: list[Path] = []
    try:
        for target, payload in payloads.items():
            target.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{target.name}.",
                suffix=".tmp",
                dir=target.parent,
            )
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            temporary[target] = Path(temporary_name)

            if target.exists():
                backup_descriptor, backup_name = tempfile.mkstemp(
                    prefix=f".{target.name}.",
                    suffix=".bak",
                    dir=target.parent,
                )
                os.close(backup_descriptor)
                shutil.copy2(target, backup_name)
                backups[target] = Path(backup_name)
            else:
                backups[target] = None

        for target, temporary_path in temporary.items():
            os.replace(temporary_path, target)
            published.append(target)
    except Exception:
        for target in reversed(published):
            backup = backups[target]
            if backup is None:
                target.unlink(missing_ok=True)
            elif backup.exists():
                os.replace(backup, target)
        raise
    finally:
        for path in (*temporary.values(), *(item for item in backups.values() if item)):
            path.unlink(missing_ok=True)


def record_runtime(
    paths: PipelinePaths,
    run_id: str,
    status: str,
    elapsed_seconds: float,
    peak_memory_mb: float,
    cache_reason: str | None,
) -> dict:
    executed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    record = {
        "executed_at_utc": executed_at,
        "run_id": run_id,
        "mode": paths.mode,
        "status": status,
        "cache_reason": cache_reason,
        "elapsed_seconds": round(elapsed_seconds, 4),
        "peak_memory_mb": round(peak_memory_mb, 2),
    }
    paths.runtime_dir.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(record, indent=2, ensure_ascii=False) + "\n").encode()
    safe_timestamp = executed_at.replace(":", "").replace("+", "-")
    atomic_publish(
        {
            paths.runtime_dir / "last_run.json": payload,
            paths.runtime_dir / f"{safe_timestamp}-{run_id}.json": payload,
        }
    )
    return record
