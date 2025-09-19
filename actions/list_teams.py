"""
List teams action - CLI interface for displaying all league teams and their IDs
"""

import logging
from core_data import ff_data
from logging_config import get_terminal
from exceptions import DataValidationError, FileOperationError

logger = logging.getLogger(__name__)


def add_list_teams_arguments(parser):
    """Add list-teams specific arguments to the parser"""
    parser.add_argument(
        '--input', '-i',
        help='Path to HTML file containing teams table (default: html_input/teams_table.html)'
    )


def validate_teams_data(teams_list, input_file):
    """Validate that teams data was successfully fetched"""
    if not teams_list:
        logger.error(f"No teams found in {input_file}")
        raise DataValidationError(f"No teams data available in {input_file}")
    return True


def display_teams_info(teams_list):
    """Display teams information in tabular format"""
    terminal = get_terminal()
    logger.info(f"Displaying {len(teams_list)} teams")
    terminal.info(f"Found {len(teams_list)} teams:")
    terminal.info("")  # Empty line for spacing
    ff_data.display_teams_table(teams_list)


def list_teams_command(args):
    """Handle list-teams command"""
    terminal = get_terminal()
    
    logger.info("Starting list-teams command")
    terminal.progress("Listing all teams...")
    
    # Use input file if provided, otherwise use default
    input_file = args.input or "html_input/teams_table.html"
    logger.info(f"Using input file: {input_file}")
    
    # Get teams using core data module - let exceptions propagate
    teams_list = ff_data.get_all_teams(input_file)
    validate_teams_data(teams_list, input_file)
    
    # Display teams information
    display_teams_info(teams_list)
    
    logger.info("list-teams command completed successfully")
    terminal.success("Teams listed successfully")

