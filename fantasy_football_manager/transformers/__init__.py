"""
Data transformers for Fantasy Football Manager
Converts source-specific data to canonical format
"""

from .espn_roster import to_canonical_roster as espn_to_canonical
from .yahoo_roster import to_canonical_roster as yahoo_to_canonical
from .espn_players import to_canonical_players as espn_to_canonical_players

def to_canonical_roster(data: dict, source: str = 'espn'):
    """Transform data to canonical format based on source"""
    if source == 'espn':
        return espn_to_canonical(data)
    elif source == 'yahoo':
        return yahoo_to_canonical(data)
    else:
        raise ValueError(f"Unknown source: {source}")

def to_canonical_players(data: dict, source: str = 'espn'):
    """Transform players data to canonical format based on source"""
    if source == 'espn':
        return espn_to_canonical_players(data)
    else:
        raise ValueError(f"Unknown source: {source}")

__all__ = ['to_canonical_roster', 'to_canonical_players']
