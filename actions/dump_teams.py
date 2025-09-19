"""
Dump teams action - CLI interface for exporting team rosters to CSV
"""

import argparse
from core_data import ff_data


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
        print(f"Failed to fetch data for team {team_id}")
        return False
    return True


def handle_team_export(team_id, team_data, output_path, format, export_csv):
    """Handle CSV export if requested"""
    if not (export_csv or format == 'csv'):
        return True
    
    csv_filename = ff_data.export_team_to_csv(team_id, team_data, output_path)
    if csv_filename:
        print(f"Team data exported to: {csv_filename}")
        return True
    return False


def dump_single_team(team_id: str, source: str = 'espn', output_path: str = None, format: str = 'csv', export_csv: bool = False):
    """Dump a single team's data"""
    print(f"Dumping team ID: {team_id} from {source}")
    
    # Guard clause: handle data fetching failure
    team_data = ff_data.get_roster(team_id, source)
    if not validate_team_data(team_data, team_id):
        return False
    
    # Guard clause: handle display failure
    try:
        ff_data.display_roster_table(team_id, team_data)
    except Exception as e:
        print(f"Error displaying team {team_id}: {e}")
        return False
    
    # Guard clause: handle export if needed
    if export_csv or format == 'csv':
        if not handle_team_export(team_id, team_data, output_path, format, export_csv):
            return False
    
    print("Team data extraction completed successfully!")
    return True


def dump_teams_command(args):
    """Handle dump-teams command"""
    print("Dumping teams...")
    
    try:
        if args.team:
            # Dump specific teams
            for team_id in args.team:
                success = dump_single_team(
                    team_id=team_id,
                    source=args.source,
                    output_path=args.output,
                    format=args.format,
                    export_csv=args.csv
                )
                if not success:
                    print(f"Failed to dump team {team_id}")
        else:
            print("No teams specified. Use --team to specify team IDs.")
            
    except Exception as e:
        print(f"Error in dump-teams command: {e}")
        raise