"""CLI admin mode for MCP Fair Shake cache management."""

import argparse
import sys

from .cache import CacheManager
from .fetcher import LEGISLATION_SOURCES, LegislationFetcher

# Priority 0 legislation for MVP
P0_LEGISLATION = [
    "/au-federal/fwa/2009",
    "/au-victoria/ohs/2004",
    "/au-victoria/eoa/2010",
]


def cmd_cache(args: argparse.Namespace) -> int:
    """Pre-cache legislation based on priority.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for errors)
    """
    cache_manager = CacheManager()
    fetcher = LegislationFetcher(cache_manager=cache_manager)

    # Determine which legislation to cache
    if args.priority == "P0":
        to_cache = P0_LEGISLATION
        print(f"Pre-caching P0 legislation ({len(to_cache)} items)...")
    elif args.priority == "all":
        to_cache = list(LEGISLATION_SOURCES.keys())
        print(f"Pre-caching all legislation ({len(to_cache)} items)...")
    else:
        print(f"Error: Unknown priority '{args.priority}'")
        return 1

    # Cache each item
    cached = 0
    failed = 0
    skipped = 0

    for canonical_id in to_cache:
        source_info = LEGISLATION_SOURCES.get(canonical_id)
        if not source_info:
            print(f"  ⚠️  {canonical_id}: No source configured")
            failed += 1
            continue

        # Check if already cached
        if not args.force and fetcher.is_cached(canonical_id):
            print(f"  ✓  {canonical_id}: Already cached (use --force to re-download)")
            skipped += 1
            continue

        # Fetch and cache
        try:
            print(f"  ⬇️  {canonical_id}: Downloading from {source_info['url'][:50]}...")
            content = fetcher.fetch(canonical_id, force=args.force)
            size_kb = len(content.encode("utf-8")) / 1024
            print(f"  ✓  {canonical_id}: Cached ({size_kb:.1f} KB)")
            cached += 1
        except Exception as e:
            print(f"  ✗  {canonical_id}: Failed - {e}")
            failed += 1

    # Summary
    print("\nCache Summary:")
    print(f"  Cached: {cached}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed: {failed}")

    fetcher.close()
    return 0 if failed == 0 else 1


def cmd_status(args: argparse.Namespace) -> int:
    """Check cache coverage and status.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (always 0)
    """
    cache_manager = CacheManager()
    fetcher = LegislationFetcher(cache_manager=cache_manager)

    # Get cache stats
    total_cached = len(cache_manager.list_cached())
    cache_size_bytes = cache_manager.get_cache_size()
    cache_size_mb = cache_size_bytes / (1024 * 1024)

    # P0 coverage
    p0_cached = sum(1 for cid in P0_LEGISLATION if fetcher.is_cached(cid))
    p0_total = len(P0_LEGISLATION)
    p0_pct = (p0_cached / p0_total * 100) if p0_total > 0 else 0

    # All legislation coverage
    all_cached = sum(1 for cid in LEGISLATION_SOURCES.keys() if fetcher.is_cached(cid))
    all_total = len(LEGISLATION_SOURCES)
    all_pct = (all_cached / all_total * 100) if all_total > 0 else 0

    print("Cache Status")
    print("=" * 60)
    print(f"Total cached items: {total_cached}")
    print(f"Total cache size: {cache_size_mb:.2f} MB ({cache_size_bytes:,} bytes)")
    print()
    print(f"P0 Coverage (MVP): {p0_cached}/{p0_total} ({p0_pct:.1f}%)")
    print(f"All Coverage: {all_cached}/{all_total} ({all_pct:.1f}%)")
    print()

    # List cached items
    if args.verbose:
        print("Cached Items:")
        print("-" * 60)
        for path in cache_manager.list_cached():
            size_kb = path.stat().st_size / 1024
            print(f"  {path.name}: {size_kb:.1f} KB")
        print()

    # List missing P0 items
    missing_p0 = [cid for cid in P0_LEGISLATION if not fetcher.is_cached(cid)]
    if missing_p0:
        print("Missing P0 Items:")
        print("-" * 60)
        for cid in missing_p0:
            source_info = LEGISLATION_SOURCES.get(cid)
            title = source_info["title"] if source_info else "Unknown"
            print(f"  {cid}: {title}")
        print()
        print("Run 'mcp-fair-shake cache --priority P0' to cache missing items.")

    fetcher.close()
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    """Verify cache integrity using checksums.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 if all valid, 1 if any invalid)
    """
    cache_manager = CacheManager()
    fetcher = LegislationFetcher(cache_manager=cache_manager)

    print("Verifying cache integrity...")
    print("=" * 60)

    valid = 0
    invalid = 0

    for cid in LEGISLATION_SOURCES.keys():
        if not fetcher.is_cached(cid):
            continue

        # Verify checksum
        from .canonical_id import parse_canonical_id

        parsed = parse_canonical_id(cid)
        if parsed and cache_manager.verify_checksum(parsed):
            print(f"  ✓  {cid}: Valid")
            valid += 1
        else:
            print(f"  ✗  {cid}: Checksum mismatch")
            invalid += 1

    print()
    print(f"Summary: {valid} valid, {invalid} invalid")

    fetcher.close()
    return 0 if invalid == 0 else 1


def cmd_update(args: argparse.Namespace) -> int:
    """Check for amendments and update cached legislation.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code
    """
    print("Update checking not yet implemented.")
    print("This will be added in Phase 2.")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        prog="mcp-fair-shake",
        description="MCP Fair Shake - Australian Workplace Legislation Lookup",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Cache command
    cache_parser = subparsers.add_parser("cache", help="Pre-cache legislation")
    cache_parser.add_argument(
        "--priority",
        choices=["P0", "all"],
        default="P0",
        help="Priority level to cache (default: P0)",
    )
    cache_parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if cached",
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Check cache status")
    status_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed information"
    )

    # Verify command
    subparsers.add_parser("verify", help="Verify cache integrity")

    # Update command
    update_parser = subparsers.add_parser("update", help="Check for amendments (Phase 2)")
    update_parser.add_argument("--all", action="store_true", help="Update all cached legislation")

    # Parse arguments
    args = parser.parse_args(argv)

    # Handle commands
    if args.command == "cache":
        return cmd_cache(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "verify":
        return cmd_verify(args)
    elif args.command == "update":
        return cmd_update(args)
    else:
        # No command - run MCP server
        from .server import main as server_main

        server_main()
        return 0


if __name__ == "__main__":
    sys.exit(main())
