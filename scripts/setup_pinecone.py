"""One-shot Pinecone index bootstrapper.

Creates (or verifies) the Pinecone index used by NeuroAgent's long-term memory.
Idempotent: safe to run repeatedly — existing indexes are validated, not
recreated.

Usage:
    # From repo root, with .env loaded
    python scripts/setup_pinecone.py

    # Override defaults
    python scripts/setup_pinecone.py --index-name custom --region us-west-2

    # Inspect without making changes
    python scripts/setup_pinecone.py --dry-run

Reads these environment variables (matching backend/app/config.py):
    PINECONE_API_KEY         required
    PINECONE_INDEX_NAME      default: neuroagent-memory
    PINECONE_ENVIRONMENT     default: us-east-1-aws  (format: <region>-<cloud>)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# text-embedding-3-small output dimension — matches backend/app/agent/memory/embedder.py
DEFAULT_DIMENSION = 1536
DEFAULT_METRIC = "cosine"
DEFAULT_INDEX_NAME = "neuroagent-memory"
DEFAULT_ENVIRONMENT = "us-east-1-aws"


def _load_env_file(path: Path) -> None:
    """Tiny .env loader — avoids a hard dep on python-dotenv for this script."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _parse_environment(env: str) -> tuple[str, str]:
    """Split a Pinecone environment string of the form '<region>-<cloud>'.

    Examples:
        'us-east-1-aws'   -> ('us-east-1', 'aws')
        'europe-west4-gcp' -> ('europe-west4', 'gcp')
    """
    parts = env.rsplit("-", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(f"Invalid PINECONE_ENVIRONMENT format: {env!r} (expected '<region>-<cloud>')")
    return parts[0], parts[1]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--index-name", default=None, help="Pinecone index name (overrides PINECONE_INDEX_NAME)")
    parser.add_argument("--dimension", type=int, default=DEFAULT_DIMENSION, help=f"Vector dimension (default: {DEFAULT_DIMENSION})")
    parser.add_argument("--metric", default=DEFAULT_METRIC, choices=["cosine", "dotproduct", "euclidean"])
    parser.add_argument("--cloud", default=None, help="Serverless cloud (e.g. aws, gcp, azure). Overrides PINECONE_ENVIRONMENT.")
    parser.add_argument("--region", default=None, help="Serverless region (e.g. us-east-1). Overrides PINECONE_ENVIRONMENT.")
    parser.add_argument("--dry-run", action="store_true", help="Report what would be done, but make no changes")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # Load .env from repo root if present, without overriding existing env.
    _load_env_file(Path(__file__).resolve().parent.parent / ".env")

    api_key = os.environ.get("PINECONE_API_KEY", "").strip()
    if not api_key:
        print("ERROR: PINECONE_API_KEY is not set. Add it to .env or your shell.", file=sys.stderr)
        return 2

    index_name = args.index_name or os.environ.get("PINECONE_INDEX_NAME", DEFAULT_INDEX_NAME)

    if args.cloud and args.region:
        region, cloud = args.region, args.cloud
    else:
        env_string = os.environ.get("PINECONE_ENVIRONMENT", DEFAULT_ENVIRONMENT)
        region, cloud = _parse_environment(env_string)
        if args.region:
            region = args.region
        if args.cloud:
            cloud = args.cloud

    print(f"Pinecone index:  {index_name}")
    print(f"Dimension:       {args.dimension}")
    print(f"Metric:          {args.metric}")
    print(f"Cloud / region:  {cloud} / {region}")

    if args.dry_run:
        print("\n[dry-run] Skipping Pinecone API calls.")
        return 0

    # Import lazily so --dry-run works without the SDK being available.
    from pinecone import Pinecone, ServerlessSpec

    pc = Pinecone(api_key=api_key)
    existing = {idx["name"] for idx in pc.list_indexes()}

    if index_name in existing:
        description = pc.describe_index(index_name)
        actual_dim = description.get("dimension")
        actual_metric = description.get("metric")
        print(f"\nIndex '{index_name}' already exists (dimension={actual_dim}, metric={actual_metric}).")

        mismatches = []
        if actual_dim != args.dimension:
            mismatches.append(f"dimension {actual_dim} != {args.dimension}")
        if actual_metric != args.metric:
            mismatches.append(f"metric {actual_metric} != {args.metric}")

        if mismatches:
            print("WARNING: existing index config differs: " + "; ".join(mismatches), file=sys.stderr)
            print("Delete it manually and rerun this script if the mismatch is intentional.", file=sys.stderr)
            return 1

        print("Configuration matches — no action required.")
        return 0

    print(f"\nCreating index '{index_name}'...")
    pc.create_index(
        name=index_name,
        dimension=args.dimension,
        metric=args.metric,
        spec=ServerlessSpec(cloud=cloud, region=region),
    )
    print("Index created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
