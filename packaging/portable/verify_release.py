"""CLI wrapper suitable for a bundled Windows release verifier."""
import argparse
import sys

from release_security import verify_zip


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True)
    parser.add_argument("--public-key", required=True)
    parser.add_argument("--fingerprint", required=True)
    args = parser.parse_args()
    try:
        manifest = verify_zip(args.zip, args.public_key, args.fingerprint)
        print(f"Verified Aurora {manifest['version']} ({manifest['architecture']})")
        return 0
    except Exception as exc:
        print(f"Release verification failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
