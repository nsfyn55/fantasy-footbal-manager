"""
ESPN roster data transformer
Converts ESPN-specific roster data to canonical format
"""

from typing import Dict, Any, Optional


def to_canonical_roster(espn_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Convert ESPN roster data to canonical format
    
    Args:
        espn_data: Raw ESPN roster data
        
    Returns:
        Canonical roster data or None if invalid
    """
    if not espn_data or not espn_data.get('players'):
        return None
    
    # ESPN data is already in a good format, just ensure consistency
    canonical_data = {
        'source': 'espn',
        'manager_name': espn_data.get('manager_name', ''),
        'players': []
    }
    
    for player in espn_data['players']:
        canonical_player = _transform_player(player)
        if canonical_player:
            canonical_data['players'].append(canonical_player)
    
    return canonical_data


def _transform_player(espn_player: Dict[str, str]) -> Optional[Dict[str, str]]:
    """
    Transform a single ESPN player to canonical format
    
    Args:
        espn_player: Raw ESPN player data
        
    Returns:
        Canonical player data or None if invalid
    """
    if not espn_player or not espn_player.get('Player Name'):
        return None
    
    # Map ESPN fields to canonical fields
    canonical_player = {
        'Player Name': espn_player.get('Player Name', ''),
        'Team': espn_player.get('Team', ''),
        'Position': espn_player.get('Position', ''),
        'Slot': espn_player.get('Slot', ''),
        'Opponent': espn_player.get('Opponent', ''),
        'Game Time': espn_player.get('Game Time', ''),
        'Projected Points': espn_player.get('Projected Points', ''),
        'Points': espn_player.get('Points', ''),
        'Avg Points': espn_player.get('Avg Points', ''),
        'Last Game': espn_player.get('Last Game', ''),
        'Rank': espn_player.get('Rank', ''),
        'Ownership %': espn_player.get('Ownership %', ''),
        'Start %': espn_player.get('Start %', ''),
        'Status': espn_player.get('Status', ''),
        'Trend': espn_player.get('Trend', ''),
        'FPTS': espn_player.get('FPTS', ''),
        'Opponent Rank': espn_player.get('Opponent Rank', ''),
        'Notes': espn_player.get('Notes', '')
    }
    
    # Clean up empty values
    cleaned_player = {}
    for key, value in canonical_player.items():
        if value and str(value).strip():
            cleaned_player[key] = str(value).strip()
        else:
            cleaned_player[key] = ''
    
    return cleaned_player
