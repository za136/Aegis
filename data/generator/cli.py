"""Command-line interface to execute the Synthetic Bank Data Generator."""

import argparse
import json
import os
import sys
from pathlib import Path

from data.generator.generator import SyntheticBankDataGenerator


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aegis / Meridian Deterministic Bank Data Generator"
    )
    parser.add_argument(
        "--profile",
        type=str,
        choices=["dev", "benchmark"],
        default="dev",
        help="Generation profile: dev (~100 custs, ~1k txs) or benchmark (~1k custs, 20k+ txs)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic reproducibility",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/corpora/synthetic_dev.json",
        help="Output JSON file path",
    )

    args = parser.parse_args()

    print(f"Generating synthetic bank data (profile: {args.profile}, seed: {args.seed})...")
    generator = SyntheticBankDataGenerator(seed=args.seed)
    dataset = generator.generate_full_dataset(profile=args.profile)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    meta = dataset["metadata"]
    print(f"Successfully generated {meta['total_transactions']} transactions across {meta['total_customers']} customers.")
    print(f"Labeled suspicious transactions: {meta['suspicious_transactions_count']}")
    print(f"Saved to: {out_path.resolve()}")


if __name__ == "__main__":
    main()
