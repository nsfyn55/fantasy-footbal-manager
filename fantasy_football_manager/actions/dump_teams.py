"""
Dump teams action - CLI interface for exporting team rosters to CSV
"""

import argparse
import logging
from ..core_data import ff_data
from ..exceptions import DataValidationError, FileOperationError

logger = logging.getLogger(__name__)


def add_dump_teams_arguments(parser):
    """Add dump-teams specific arguments to the parser"""
    team_group = parser.add_mutually_exclusive_group(required=True)
    team_group.add_argument(
        '--team', '-t',
        nargs='+',
        help='Team ID(s) to dump (e.g., 8 for your team)'
    )
    team_group.add_argument(
        '--all', '-a',
        action='store_true',
        help='Dump all teams from the league'
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
        '--unified-csv',
        action='store_true',
        help='Export all teams to a single unified CSV file (requires --all)'
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
    
    # Validate unified-csv usage
    if args.unified_csv and not args.all:
        print("⚠ --unified-csv requires --all flag. Use --all --unified-csv to export all teams to a single CSV.")
        return
    
    # Determine which teams to process
    if args.all:
        logger.info("Fetching all teams from league")
        print("→ Fetching all teams from league...")
        
        # Get all teams from core_data
        all_teams = ff_data.get_all_teams()
        if not all_teams:
            print("⚠ No teams found in league data.")
            return
        
        # Extract team IDs
        team_ids = [team.get('team_id') for team in all_teams if team.get('team_id')]
        if not team_ids:
            print("⚠ No valid team IDs found in league data.")
            return
        
        print(f"→ Found {len(team_ids)} teams: {', '.join(team_ids)}")
        
        # Handle unified CSV export
        if args.unified_csv:
            logger.info("Exporting all teams to unified CSV")
            print("→ Exporting all teams to unified CSV...")
            
            # Set output filename for unified CSV
            unified_output = args.output
            if not unified_output:
                unified_output = "league_unified_roster.csv"
            elif not unified_output.endswith('.csv'):
                unified_output = f"{unified_output}.csv"
            
            try:
                csv_filename = ff_data.export_all_teams_to_csv(
                    team_ids=team_ids,
                    source=args.source,
                    filename=unified_output
                )
                
                if csv_filename:
                    logger.info(f"Unified CSV exported successfully: {csv_filename}")
                    print(f"✓ Unified CSV exported: {csv_filename}")
                else:
                    logger.error("Failed to export unified CSV")
                    print("⚠ Failed to export unified CSV")
                    return
                    
            except Exception as e:
                logger.error(f"Error exporting unified CSV: {e}")
                print(f"⚠ Error exporting unified CSV: {e}")
                return
        
        # If not unified CSV, process each team individually
        if not args.unified_csv:
            # Process each team - let exceptions propagate to global handler
            for team_id in team_ids:
                logger.info(f"Processing team {team_id}")
                dump_single_team(
                    team_id=team_id,
                    source=args.source,
                    output_path=args.output,
                    format=args.format,
                    export_csv=args.csv
                )
    
    elif args.team:
        team_ids = args.team
        print(f"→ Processing {len(team_ids)} specified team(s): {', '.join(team_ids)}")
        
        # Process each team - let exceptions propagate to global handler
        for team_id in team_ids:
            logger.info(f"Processing team {team_id}")
            dump_single_team(
                team_id=team_id,
                source=args.source,
                output_path=args.output,
                format=args.format,
                export_csv=args.csv
            )
    else:
        print("⚠ No teams specified. Use --team to specify team IDs or --all to dump all teams.")
        return
    
    logger.info("dump-teams command completed successfully")
    if args.all and not args.unified_csv:
        print(f"✓ All {len(team_ids)} teams processed successfully")
    elif args.all and args.unified_csv:
        print(f"✓ Unified CSV export completed for {len(team_ids)} teams")
    else:
        print(f"✓ All {len(team_ids)} teams processed successfully")