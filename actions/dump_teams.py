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


def dump_single_team(team_id: str, output_path: str = None, format: str = 'csv', export_csv: bool = False):
    """Dump a single team's data"""
    print(f"Dumping team ID: {team_id}")
    
    try:
        # Get roster data using core data module
        team_data = ff_data.get_roster(team_id)
        
        if not team_data:
            print(f"Failed to fetch data for team {team_id}")
            return False
        
        # Display team data using core data module
        ff_data.display_roster_table(team_id, team_data)
        
        # Export to CSV if requested
        if export_csv or format == 'csv':
            csv_filename = ff_data.export_team_to_csv(team_id, team_data, output_path)
            if csv_filename:
                print(f"Team data exported to: {csv_filename}")
                return True
        
        print("Team data extraction completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error dumping team {team_id}: {e}")
        return False


def dump_teams_command(args):
    """Handle dump-teams command"""
    print("Dumping teams...")
    
    try:
        if args.team:
            # Dump specific teams
            for team_id in args.team:
                success = dump_single_team(
                    team_id=team_id,
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