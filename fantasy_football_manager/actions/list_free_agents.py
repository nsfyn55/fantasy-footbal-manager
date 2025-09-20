"""
List free agents command
"""

import argparse
from typing import List, Dict, Any, Optional
from ..core_data import ff_data


def list_free_agents_command(args):
    """
    List free agents with optional filtering
    
    Args:
        args: Parsed command line arguments
    """
    try:
        # Build filters from command line arguments
        filters = {}
        if args.position:
            filters['position'] = args.position
        if args.status:
            filters['status'] = args.status
        if args.team:
            filters['team'] = args.team
        if args.limit:
            filters['limit'] = args.limit
        
        # Get players data using core_data
        players = ff_data.get_players(source='espn', filters=filters)
        
        if not players:
            print("No players found or failed to fetch data")
            return
        
        # Display results
        _display_players(players, args)
        
    except Exception as e:
        print(f"Error listing free agents: {e}")


def _display_players(players: List[Dict[str, Any]], args):
    """Display players in a formatted table"""
    
    if not players:
        print("No players found matching criteria")
        return
    
    print(f"\nFound {len(players)} players:")
    print("-" * 80)
    
    # Use tabulate for consistent formatting like other commands
    from tabulate import tabulate
    
    # Prepare table data
    table_data = []
    headers = ['Rank', 'Name', 'Position', 'Team', 'Status', 'Proj Pts']
    
    if args.verbose:
        headers.extend(['Own%', 'Trend'])
    
    for i, player in enumerate(players, 1):
        row = [
            i,
            player.get('name', '')[:24],  # Truncate long names
            player.get('position', ''),
            player.get('team', ''),
            player.get('status', '')[:10],  # Truncate long status
            f"{player.get('projected_points', 0) or 0:.1f}"
        ]
        
        if args.verbose:
            ownership = player.get('ownership_percent', 0) or 0
            trend = player.get('trend', 0) or 0
            row.extend([f"{ownership:.1f}", f"{trend:.1f}"])
        
        table_data.append(row)
    
    # Display table using tabulate
    print(tabulate(table_data, headers=headers, tablefmt='grid'))


def add_list_free_agents_parser(subparsers):
    """Add list-free-agents subcommand to argument parser"""
    
    parser = subparsers.add_parser(
        'list-free-agents',
        help='List available free agents with optional filtering'
    )
    
    # Filtering options
    parser.add_argument(
        '-p', '--position',
        help='Filter by position (QB, RB, WR, TE, K, D/ST). Use comma-separated for multiple positions'
    )
    
    parser.add_argument(
        '-s', '--status',
        help='Filter by status (FA, WA, etc.)'
    )
    
    parser.add_argument(
        '-t', '--team',
        help='Filter by team abbreviation. Use comma-separated for multiple teams'
    )
    
    parser.add_argument(
        '-l', '--limit',
        type=int,
        help='Limit number of results'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show additional details (ownership percent, trend)'
    )
    
    parser.set_defaults(func=list_free_agents_command)
