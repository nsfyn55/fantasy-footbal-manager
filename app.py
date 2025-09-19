#!/usr/bin/env python3
"""
Fantasy Football Manager - AI-powered team management
"""

import argparse
import sys
from modules.login import login_command
from modules.dump_teams import dump_teams_command, add_dump_teams_arguments


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Fantasy Football Manager - AI-powered team management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ffm login                    # Login to ESPN Fantasy Football
  ffm roster                  # Display your current roster
  ffm dump-teams -t 8         # Export team 8 roster to terminal
  ffm dump-teams -t 8 9 10    # Export multiple teams to terminal
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Login command
    login_parser = subparsers.add_parser('login', help='Login to ESPN Fantasy Football')
    login_parser.set_defaults(func=login_command)
    
    # Dump teams command
    dump_teams_parser = subparsers.add_parser('dump-teams', help='Export opponent teams to CSV')
    add_dump_teams_arguments(dump_teams_parser)
    dump_teams_parser.set_defaults(func=dump_teams_command)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute the command
    try:
        args.func(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
