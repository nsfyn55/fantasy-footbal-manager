#!/usr/bin/env python3
"""
Fantasy Football Manager - AI-powered team management
"""

import argparse
import sys
import logging
import logging.config
import os
from .exceptions import FantasyFootballManagerError
from .actions.login import login_command
from .actions.dump_teams import dump_teams_command, add_dump_teams_arguments
from .actions.list_teams import list_teams_command, add_list_teams_arguments


def setup_logging(log_level: str = "INFO"):
    """Set up logging from YAML configuration"""
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Load YAML configuration
    try:
        logging.config.dictConfig({
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                },
                'simple': {
                    'format': '%(levelname)s - %(name)s - %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'WARNING',
                    'formatter': 'simple',
                    'stream': 'ext://sys.stderr'
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': log_level,
                    'formatter': 'standard',
                    'filename': 'logs/fantasy_football_manager.log',
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 5,
                    'encoding': 'utf8'
                }
            },
            'loggers': {
                'fantasy_football_manager': {
                    'level': log_level,
                    'handlers': ['console', 'file'],
                    'propagate': False
                }
            },
            'root': {
                'level': log_level,
                'handlers': ['console', 'file']
            }
        })
    except Exception as e:
        # Fallback to basic logging if YAML fails
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/fantasy_football_manager.log'),
                logging.StreamHandler(sys.stderr)
            ]
        )


def main():
    """Main CLI entry point"""
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Fantasy Football Manager starting up")
    
    parser = argparse.ArgumentParser(
        description="Fantasy Football Manager - AI-powered team management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ffm login                    # Login to ESPN Fantasy Football
  ffm list-teams              # List all teams and their IDs
  ffm dump-teams -t 8         # Export team 8 roster to terminal
  ffm dump-teams -t 8 9 10    # Export multiple teams to terminal
  ffm dump-teams --all        # Export all teams from the league
        """
    )
    
    # Add logging level argument
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Login command
    login_parser = subparsers.add_parser('login', help='Login to ESPN Fantasy Football')
    login_parser.set_defaults(func=login_command)
    
    # List teams command
    list_teams_parser = subparsers.add_parser('list-teams', help='List all teams and their IDs')
    add_list_teams_arguments(list_teams_parser)
    list_teams_parser.set_defaults(func=list_teams_command)
    
    # Dump teams command
    dump_teams_parser = subparsers.add_parser('dump-teams', help='Export team rosters to CSV (specify teams with -t or use --all for all teams)')
    add_dump_teams_arguments(dump_teams_parser)
    dump_teams_parser.set_defaults(func=dump_teams_command)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Reconfigure logging with user-specified level if different
    if hasattr(args, 'log_level') and args.log_level != 'INFO':
        setup_logging(log_level=args.log_level)
        logger = logging.getLogger(__name__)
    
    logger.info(f"Executing command: {args.command}")
    
    # Execute the command with global exception handling
    try:
        args.func(args)
        logger.info(f"Command '{args.command}' completed successfully")
    except FantasyFootballManagerError as e:
        # Application-specific errors - log and show user-friendly message
        logger.exception(f"Application error in command '{args.command}': {e}")
        print(f"✗ Error: {e}", file=sys.stderr)
        print("Check logs/fantasy_football_manager.log for detailed information")
        sys.exit(1)
    except KeyboardInterrupt:
        # User interrupted - clean exit
        logger.info("Command interrupted by user")
        print("⚠ Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        # Unexpected errors - log full traceback and show generic message
        logger.exception(f"Unexpected error in command '{args.command}': {e}")
        print("✗ An unexpected error occurred", file=sys.stderr)
        print("Check logs/fantasy_football_manager.log for detailed information")
        sys.exit(1)


if __name__ == "__main__":
    main()
