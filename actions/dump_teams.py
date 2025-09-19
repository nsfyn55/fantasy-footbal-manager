"""
Dump teams action - CLI interface for exporting team rosters to CSV
"""

import argparse
import logging
from core_data import ff_data
from exceptions import DataValidationError, FileOperationError

logger = logging.getLogger(__name__)


def add_dump_teams_arguments(parser):
    """Add dump-teams specific arguments to the parser"""
    parser.add_argument(
        '--team', '-t',
        nargs='+',
        required=True,
        help='Team ID(s) to dump (e.g., 8 for your team)'
    )
    parser.add_argument(
        '--source', '-s',
        choices=['espn', 'yahoo'],
        default='espn',
        help='Data source to use (default: espn)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output CSV file path (default: output/team_{id}_roster.csv)'
    )
    parser.add_argument(
        '--csv',
        action='store_true',
        help='Export team data to CSV with Manager column for analytics'
    )
    parser.add_argument(
        '--format',
        choices=['csv', 'json'],
        default='csv',
        help='Output format (default: csv)'
    )


def validate_team_data(team_data, team_id):
    """Validate that team data was successfully fetched"""
    if not team_data:
        logger.error(f"Failed to fetch data for team {team_id}")
        raise DataValidationError(f"No data available for team {team_id}")
    return True


def handle_team_export(team_id, team_data, output_path, format, export_csv):
    """Handle CSV export if requested"""
    if not (export_csv or format == 'csv'):
        return True
    
    logger.info(f"Exporting team {team_id} data to CSV")
    csv_filename = ff_data.export_team_to_csv(team_id, team_data, output_path)
    if csv_filename:
        logger.info(f"Team data exported to: {csv_filename}")
        return True
    
    logger.error(f"Failed to export team {team_id} data to CSV")
    raise FileOperationError(f"Could not export team {team_id} data to CSV")


def dump_single_team(team_id: str, source: str = 'espn', output_path: str = None, format: str = 'csv', export_csv: bool = False):
    """Dump a single team's data"""
    logger.info(f"Dumping team ID: {team_id} from {source}")
    print(f"→ Dumping team {team_id} from {source}")
    
    # Fetch team data - let exceptions propagate
    team_data = ff_data.get_roster(team_id, source)
    validate_team_data(team_data, team_id)
    
    # Display roster table - let exceptions propagate
    ff_data.display_roster_table(team_id, team_data)
    
    # Export if needed - let exceptions propagate
    if export_csv or format == 'csv':
        handle_team_export(team_id, team_data, output_path, format, export_csv)
    
    logger.info(f"Team {team_id} data extraction completed successfully")
    print(f"✓ Team {team_id} data extraction completed")
    return True


def dump_teams_command(args):
    """Handle dump-teams command"""
    logger.info("Starting dump-teams command")
    print("→ Dumping teams...")
    
    if not args.team:
        print("⚠ No teams specified. Use --team to specify team IDs.")
        return
    
    # Process each team - let exceptions propagate to global handler
    for team_id in args.team:
        logger.info(f"Processing team {team_id}")
        dump_single_team(
            team_id=team_id,
            source=args.source,
            output_path=args.output,
            format=args.format,
            export_csv=args.csv
        )
    
    logger.info("dump-teams command completed successfully")
    print("✓ All teams processed successfully")