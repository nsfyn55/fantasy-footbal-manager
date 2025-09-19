"""
List teams action - CLI interface for displaying all league teams and their IDs
"""

from core_data import ff_data


def add_list_teams_arguments(parser):
    """Add list-teams specific arguments to the parser"""
    parser.add_argument(
        '--input', '-i',
        help='Path to HTML file containing teams table (default: html_input/teams_table.html)'
    )


def list_teams_command(args):
    """Handle list-teams command"""
    print("Listing all teams...")
    
    try:
        # Use input file if provided, otherwise use default
        input_file = args.input or "html_input/teams_table.html"
        
        # Get teams using core data module
        teams_list = ff_data.get_all_teams(input_file)
        
        if not teams_list:
            print(f"No teams found in {input_file}")
            return
        
        print(f"Found {len(teams_list)} teams:")
        print()
        
        # Display in tabular format using core data module
        ff_data.display_teams_table(teams_list)
        
    except Exception as e:
        print(f"Error listing teams: {e}")
        raise

