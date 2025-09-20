"""
ESPN players data transformer
Converts ESPN-specific players data to canonical format
"""

from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
import re


def to_canonical_players(espn_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """
    Convert ESPN players data to canonical format
    
    Args:
        espn_data: Raw ESPN players data
        
    Returns:
        List of canonical player dictionaries or None if invalid
    """
    if not espn_data or not espn_data.get('html_content'):
        return None
    
    # Parse HTML content
    soup = BeautifulSoup(espn_data['html_content'], 'html.parser')
    
    # Find the main table
    main_table = soup.find('table', class_='Table')
    if not main_table:
        return None
    
    # Get all rows
    rows = main_table.find_all('tr', class_='Table__TR')
    
    players = []
    for row in rows:
        cells = row.find_all(['td', 'th'], class_='Table__TD')
        
        if len(cells) < 15:
            continue  # Skip header rows
        
        # Parse player row
        player_data = _parse_player_row(cells)
        if player_data:
            players.append(player_data)
    
    return players


def _parse_player_row(cells) -> Optional[Dict[str, Any]]:
    """
    Parse a single player row into canonical format
    
    Args:
        cells: List of table cells from a player row
        
    Returns:
        Canonical player dictionary or None if invalid
    """
    if len(cells) < 15:
        return None
    
    # Extract player info from first cell using proper HTML structure
    player_cell = cells[0]
    player_name, team, position = _parse_player_info_from_html(player_cell)
    
    # Parse numeric values - corrected cell mapping
    projected_points = _parse_numeric_value(cells[5].get_text().strip())  # Cell 6 in 1-based
    ownership_percent = _parse_numeric_value(cells[8].get_text().strip())  # Cell 9 in 1-based
    start_percent = _parse_numeric_value(cells[9].get_text().strip())      # Cell 10 in 1-based
    trend = _parse_numeric_value(cells[10].get_text().strip())             # Cell 11 in 1-based
    games_played = _parse_numeric_value(cells[11].get_text().strip())      # Cell 12 in 1-based
    avg_points = _parse_numeric_value(cells[12].get_text().strip())        # Cell 13 in 1-based
    last_game = _parse_numeric_value(cells[13].get_text().strip())         # Cell 14 in 1-based
    season_total = _parse_numeric_value(cells[14].get_text().strip())      # Cell 15 in 1-based
    
    return {
        'name': player_name,
        'position': position,
        'team': team,
        'status': cells[1].get_text().strip(),      # Cell 2: Status
        'action': cells[2].get_text().strip(),      # Cell 3: Action (usually empty)
        'opponent': cells[3].get_text().strip(),    # Cell 4: Opponent
        'game_time': cells[4].get_text().strip(),   # Cell 5: Game time
        'projected_points': projected_points,       # Cell 6: Projected points
        'points': cells[6].get_text().strip(),      # Cell 7: Points
        'rank': cells[7].get_text().strip(),        # Cell 8: Rank
        'ownership_percent': ownership_percent,     # Cell 9: Ownership %
        'start_percent': start_percent,             # Cell 10: Start %
        'trend': trend,                             # Cell 11: Trend
        'games_played': games_played,               # Cell 12: Games played
        'avg_points': avg_points,                   # Cell 13: Avg points
        'last_game': last_game,                     # Cell 14: Last game
        'season_total': season_total                # Cell 15: Season total
    }


def _parse_player_info_from_html(player_cell) -> tuple[str, str, str]:
    """
    Parse player name, team, and position from HTML cell structure
    
    Args:
        player_cell: BeautifulSoup element containing player info
        
    Returns:
        Tuple of (player_name, team, position)
    """
    player_name = ""
    team = ""
    position = ""
    
    try:
        # Look for the player info div
        player_info = player_cell.find('div', class_='player-info')
        if player_info:
            # Extract name from link
            name_span = player_info.find('span', class_='truncate')
            if name_span:
                name_link = name_span.find('a')
                if name_link:
                    player_name = name_link.get_text().strip()
            
            # Extract team and position
            position_div = player_info.find('div', class_='player-column__position')
            if position_div:
                team_span = position_div.find('span', class_='playerinfo__playerteam')
                pos_span = position_div.find('span', class_='playerinfo__playerpos')
                
                if team_span:
                    team = team_span.get_text().strip()
                if pos_span:
                    position = pos_span.get_text().strip()
    
    except Exception as e:
        # Fallback to text parsing if HTML structure fails
        player_cell_text = player_cell.get_text().strip()
        player_name = player_cell_text
        team = ""
        position = ""
    
    return player_name, team, position


def _parse_numeric_value(text: str) -> Optional[float]:
    """
    Parse numeric value from text, handling common formats
    
    Args:
        text: Text that may contain a numeric value
        
    Returns:
        Numeric value or None if not parseable
    """
    if not text or text == '--':
        return None
    
    # Remove common suffixes and prefixes
    text = text.replace('%', '').replace('+', '').replace('-', '')
    
    try:
        return float(text)
    except ValueError:
        return None
