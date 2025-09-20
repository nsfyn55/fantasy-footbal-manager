"""
Data sources for Fantasy Football Manager
"""

from .espn import fetch_roster as espn_fetch_roster, fetch_teams as espn_fetch_teams
from .yahoo import fetch_roster as yahoo_fetch_roster, fetch_teams as yahoo_fetch_teams

def fetch_roster(team_id: str, source: str = 'espn', session_state=None):
    """Fetch roster from specified source"""
    if source == 'espn':
        return espn_fetch_roster(team_id, session_state)
    elif source == 'yahoo':
        return yahoo_fetch_roster(team_id, session_state)
    else:
        raise ValueError(f"Unknown source: {source}")

def fetch_teams(input_file: str = "html_input/teams_table.html", source: str = 'espn'):
    """Fetch teams from specified source"""
    if source == 'espn':
        return espn_fetch_teams(input_file)
    elif source == 'yahoo':
        return yahoo_fetch_teams(input_file)
    else:
        raise ValueError(f"Unknown source: {source}")

__all__ = ['fetch_roster', 'fetch_teams']
