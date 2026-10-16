#!/usr/bin/env python3
"""Fail before build/deployment if runtime documents contain private source data."""
import argparse
from pathlib import Path
from public_data import validate_public


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    count = validate_public(args.root)
    print(f'PASS: {count} public documents contain no prohibited source paths, account fields, or run commands.')


if __name__ == '__main__':
    main()
