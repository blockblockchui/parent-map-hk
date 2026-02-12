"""
CLI entry point for data pipeline
Usage: python -m pipeline [command] [options]

Commands:
  ingest      Ingest new places from sources
  check       Run freshness check on existing places
  export      Export clean data to JSON
  validate    Validate a specific place
"""

import sys
import argparse

# Import command modules
from .ingest_sources import main as ingest_main
from .freshness_check import main as check_main
from .export_json import main as export_main


def main():
    parser = argparse.ArgumentParser(
        description="Parent Map HK Data Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m pipeline ingest --dry-run
  python -m pipeline check --dry-run
  python -m pipeline export --compare
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Ingest command
    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Ingest new places from configured sources"
    )
    ingest_parser.add_argument(
        "--source",
        help="Filter to specific source"
    )
    ingest_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't write to Sheets"
    )
    
    # Check command
    check_parser = subparsers.add_parser(
        "check",
        help="Run freshness check on existing places"
    )
    check_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't update Sheets"
    )
    check_parser.add_argument(
        "--export-flagged",
        help="Export flagged places to CSV file"
    )
    
    # Export command
    export_parser = subparsers.add_parser(
        "export",
        help="Export clean data to JSON"
    )
    export_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't write files"
    )
    export_parser.add_argument(
        "--include-pending",
        action="store_true",
        help="Include pending review places"
    )
    export_parser.add_argument(
        "--min-confidence",
        type=int,
        default=50,
        help="Minimum confidence score"
    )
    export_parser.add_argument(
        "--git-commit",
        action="store_true",
        help="Commit changes to git"
    )
    export_parser.add_argument(
        "--git-push",
        action="store_true",
        help="Push changes to remote"
    )
    export_parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare with existing file"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Route to appropriate command
    if args.command == "ingest":
        sys.argv = [sys.argv[0]] + sys.argv[2:]  # Remove 'ingest' from args
        ingest_main()
    elif args.command == "check":
        # TODO: Implement check_main
        print("Freshness check not yet implemented")
    elif args.command == "export":
        sys.argv = [sys.argv[0]] + sys.argv[2:]  # Remove 'export' from args
        export_main()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
