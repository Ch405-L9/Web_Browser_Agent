#!/usr/bin/env python3
"""Bounded local embedding smoke test.

Safety boundary:
- Uses one fixed chunk from the approved retrieval manifest.
- Uses an already-installed local Ollama model only.
- Refuses remote Ollama endpoints.
- Does not pull/download models.
- Does not create Chroma/vector stores.
- Does not create a persistent retrieval index.
- Writes only the explicitly requested disposable report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MANIFEST_PATH = PROJECT_ROOT / "artifacts" / "retrieval" / "evidence_manifest.json"
EXPECTED_MANIFEST_SHA256 = (
    "f0cdd193587668abf4fa92d6347162876b971425b8d3b67ce6554134e15b57b2"
)

TARGET_CHUNK_ID = "EV-AI-001--000--5ebba63c612e"
TARGET_CHUNK_SHA256 = (
    "5ebba63c612e27873829ec1170253fa77b1b0eb86398c620ecc55e753636c51d"
)

MODEL = "nomic-embed-text:latest"
EXPECTED_MODEL_DIGEST = "0a109f422b47"

OLLAMA_HOST = "http://127.0.0.1:11434"

# These are deliberately not production artifact locations.
DISPOSABLE_PREFIX = "embedding_smoke_test_"


class SmokeTestError(RuntimeError):
    """Raised when a smoke-test safety or integrity condition fails."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def verify_local_host(url: str) -> None:
    parsed = urlparse(url)

    if parsed.scheme != "http":
        raise SmokeTestError("Ollama endpoint must use local HTTP.")

    if parsed.hostname != "127.0.0.1":
        raise SmokeTestError(
            f"Refusing non-local Ollama host: {parsed.hostname!r}"
        )

    if parsed.port not in (None, 11434):
        raise SmokeTestError(
            f"Refusing unexpected Ollama port: {parsed.port!r}"
        )


def verify_manifest() -> dict:
    if not MANIFEST_PATH.is_file():
        raise SmokeTestError(f"Approved manifest missing: {MANIFEST_PATH}")

    raw = MANIFEST_PATH.read_bytes()
    actual = sha256_bytes(raw)

    if actual != EXPECTED_MANIFEST_SHA256:
        raise SmokeTestError(
            "Approved manifest SHA-256 mismatch: "
            f"expected {EXPECTED_MANIFEST_SHA256}, got {actual}"
        )

    try:
        manifest = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise SmokeTestError("Approved manifest is not valid UTF-8 JSON.") from exc

    chunks = manifest.get("chunks")
    if not isinstance(chunks, list):
        raise SmokeTestError("Manifest has no valid chunks list.")

    matches = [
        chunk for chunk in chunks
        if chunk.get("chunk_id") == TARGET_CHUNK_ID
    ]

    if len(matches) != 1:
        raise SmokeTestError(
            f"Expected exactly one fixed target chunk; found {len(matches)}."
        )

    chunk = matches[0]
    text = chunk.get("text")

    if not isinstance(text, str) or not text:
        raise SmokeTestError("Target chunk has no non-empty text.")

    actual_chunk_sha256 = sha256_text(text)

    if actual_chunk_sha256 != TARGET_CHUNK_SHA256:
        raise SmokeTestError(
            "Target chunk SHA-256 mismatch: "
            f"expected {TARGET_CHUNK_SHA256}, got {actual_chunk_sha256}"
        )

    if chunk.get("evidence_id") != "EV-AI-001":
        raise SmokeTestError("Target chunk evidence ID changed.")

    if chunk.get("chunk_index") != 0:
        raise SmokeTestError("Target chunk index changed.")

    return {
        "chunk_id": TARGET_CHUNK_ID,
        "text": text,
        "text_sha256": actual_chunk_sha256,
        "char_count": len(text),
        "manifest_sha256": actual,
    }


def verify_model_is_local() -> None:
    """Verify model availability without invoking a model pull/download."""
    import subprocess

    result = subprocess.run(
        ["ollama", "list"],
        cwd=PROJECT_ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10,
        check=False,
    )

    if result.returncode != 0:
        raise SmokeTestError(
            "Unable to inspect locally installed Ollama models."
        )

    matching_lines = [
        line
        for line in result.stdout.splitlines()
        if line.startswith(MODEL)
    ]

    if not matching_lines:
        raise SmokeTestError(
            f"Required local model is not installed: {MODEL}"
        )

    if EXPECTED_MODEL_DIGEST not in matching_lines[0]:
        raise SmokeTestError(
            "Installed model digest does not match the approved local model "
            f"identity {EXPECTED_MODEL_DIGEST}."
        )


def validate_embedding(values: object) -> list[float]:
    if not isinstance(values, list) or not values:
        raise SmokeTestError("Embedding response contained no vector.")

    result: list[float] = []

    for value in values:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise SmokeTestError("Embedding contains a non-numeric value.")

        value_float = float(value)

        if not math.isfinite(value_float):
            raise SmokeTestError("Embedding contains a non-finite value.")

        result.append(value_float)

    if len(result) <= 0:
        raise SmokeTestError("Embedding dimension is zero.")

    return result


def serialize_embedding(values: list[float]) -> bytes:
    """Stable documented serialization for the smoke-test hash."""
    return json.dumps(
        values,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def embed(text: str) -> list[float]:
    verify_local_host(OLLAMA_HOST)

    import ollama

    client = ollama.Client(host=OLLAMA_HOST)

    # This is an embedding operation only. No pull/download operation is
    # exposed or invoked by this harness.
    response = client.embed(
        model=MODEL,
        input=text,
    )

    embeddings = response.get("embeddings")

    if not isinstance(embeddings, list) or len(embeddings) != 1:
        raise SmokeTestError(
            "Expected exactly one embedding from the fixed input chunk."
        )

    return validate_embedding(embeddings[0])


def build_report(chunk: dict, embedding: list[float], run_label: str) -> dict:
    embedding_bytes = serialize_embedding(embedding)

    return {
        "schema_version": 1,
        "run_label": run_label,
        "mode": "bounded_local_embedding_smoke_test",
        "chunk_id": chunk["chunk_id"],
        "input_text_sha256": chunk["text_sha256"],
        "input_char_count": chunk["char_count"],
        "model": MODEL,
        "model_digest": EXPECTED_MODEL_DIGEST,
        "ollama_host": OLLAMA_HOST,
        "embedding_dimension": len(embedding),
        "embedding_values_finite": all(math.isfinite(x) for x in embedding),
        "embedding_serialization": "json-finite-float-array-utf8",
        "embedding_bytes_sha256": sha256_bytes(embedding_bytes),
        "network_access": True,
        "network_scope": "loopback_only",
        "external_network_access": False,
        "model_download_attempted": False,
        "remote_api_used": False,
        "vector_store_created": False,
        "persistent_storage_created": False,
    }


def compare_repeatability(first: dict, second: dict) -> dict:
    deterministic_fields = [
        "mode",
        "chunk_id",
        "input_text_sha256",
        "input_char_count",
        "model",
        "model_digest",
        "ollama_host",
        "embedding_dimension",
        "embedding_values_finite",
        "embedding_serialization",
        "embedding_bytes_sha256",
        "network_access",
        "network_scope",
        "external_network_access",
        "model_download_attempted",
        "remote_api_used",
        "vector_store_created",
        "persistent_storage_created",
    ]

    differences = {
        key: {
            "first": first.get(key),
            "second": second.get(key),
        }
        for key in deterministic_fields
        if first.get(key) != second.get(key)
    }

    return {
        "deterministic_fields_match": not differences,
        "differences": differences,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the bounded local embedding smoke test."
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional disposable JSON report path.",
    )
    args = parser.parse_args()

    verify_local_host(OLLAMA_HOST)

    # Keep production persistence paths out of the operation entirely.
    chroma_path = PROJECT_ROOT / ".local" / "chroma"
    if chroma_path.exists():
        raise SmokeTestError(
            "Production Chroma path exists; smoke test refuses to proceed."
        )

    chunk = verify_manifest()
    verify_model_is_local()

    # Disposable temporary workspace. It is never used as a vector store.
    with tempfile.TemporaryDirectory(
        prefix=DISPOSABLE_PREFIX,
        dir="/tmp",
    ):
        first_embedding = embed(chunk["text"])
        first_report = build_report(chunk, first_embedding, "run1")

        second_embedding = embed(chunk["text"])
        second_report = build_report(chunk, second_embedding, "run2")

        repeatability = compare_repeatability(
            first_report,
            second_report,
        )

        if not repeatability["deterministic_fields_match"]:
            raise SmokeTestError(
                "Repeatability check failed: "
                + json.dumps(
                    repeatability["differences"],
                    sort_keys=True,
                )
            )

        report = {
            "overall_status": "PASS",
            "run1": first_report,
            "run2": second_report,
            "repeatability": repeatability,
            "safety": {
                "network_access": True,
                "network_scope": "loopback_only",
                "external_network_access": False,
                "model_download_attempted": False,
                "remote_api_used": False,
                "vector_store_created": False,
                "persistent_storage_created": False,
            },
        }

        output = args.output
        if output is not None:
            output = output.resolve()

            # Explicitly prevent writing into production artifact directories.
            forbidden = [
                PROJECT_ROOT / "artifacts" / "retrieval",
                PROJECT_ROOT / "artifacts",
                PROJECT_ROOT / ".local",
            ]

            if any(
                output == directory or directory in output.parents
                for directory in forbidden
            ):
                raise SmokeTestError(
                    "Smoke-test output must not be written under production "
                    "artifact or persistence directories."
                )

            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(
                    report,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("ABORTED: interrupted.", file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
