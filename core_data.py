"""
Core data module for Fantasy Football Manager
Provides clean API for data extraction and processing
"""

import os
import logging
from typing import Dict, List, Optional, Any
from tabulate import tabulate
from sources import fetch_roster as source_fetch_roster, fetch_teams as source_fetch_teams
from transformers import to_canonical_roster
from exceptions import FileOperationError

logger = logging.getLogger(__name__)


class FantasyFootballData:
    """Core data access layer for Fantasy Football operations"""
    
    def __init__(self):
        self.session_state = None
        self._load_session()
    
    def _load_session(self):
        """Load saved session state if available"""
        try:
            session_file = ".fantasy-football-manager/session.json"
            if os.path.exists(session_file):
                with open(session_file, 'r') as f:
                    import json
                    self.session_state = json.load(f)
        except Exception:
            self.session_state = None
    
    def get_all_teams(self, input_file: str = "html_input/teams_table.html") -> List[Dict[str, str]]:
        """
        Get all teams from HTML file
        
        Args:
            input_file: Path to HTML file containing teams table
            
        Returns:
            List of team dictionaries with keys: team_id, team_abbrev, team_name, manager_name
        """
        return source_fetch_teams(input_file)
    
    def get_roster(self, team_id: str, source: str = 'espn') -> Dict[str, Any]:
        """
        Get roster data for a specific team
        
        Args:
            team_id: Team ID to fetch roster for
            source: Data source to use ('espn', 'yahoo', etc.)
            
        Returns:
            Canonical roster data
        """
        # Fetch raw data from source
        raw_data = source_fetch_roster(team_id, source, self.session_state)
        if not raw_data:
            return None
        
        # Transform to canonical format
        canonical_data = to_canonical_roster(raw_data, source)
        return canonical_data
    
    def get_multiple_rosters(self, team_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get roster data for multiple teams
        
        Args:
            team_ids: List of team IDs to fetch
            
        Returns:
            Dictionary mapping team_id to roster data
        """
        rosters = {}
        for team_id in team_ids:
            rosters[team_id] = self.get_roster(team_id)
        return rosters
    
    def export_team_to_csv(self, team_id: str, team_data: Dict[str, Any], 
                          filename: str = None) -> Optional[str]:
        """
        Export team data to CSV
        
        Args:
            team_id: Team ID
            team_data: Team data dictionary
            filename: Output filename (optional)
            
        Returns:
            Path to created CSV file or None if failed
        """
        if not team_data or not team_data.get('players'):
            return None
        
        import csv
        
        players = team_data['players']
        manager = team_data.get('manager_name') or f"Manager{team_id}"
        
        if not filename:
            filename = f"output/team_{team_id}_roster.csv"
        elif not filename.startswith('/') and not filename.startswith('./') and not filename.startswith('../'):
            if not filename.startswith('output/'):
                filename = f"output/{filename}"
        
        # Define column order
        csv_columns = [
            'Manager', 'Team_ID', 'Player Name', 'Team', 'Position', 'Roster Status', 
            'Opponent', 'Game Time', 'Projected Points', 'Points', 'Avg Points', 
            'Last Game', 'Rank', 'Ownership %', 'Start %', 'Status', 'Trend', 'Notes'
        ]
        
        # Get available columns
        all_headers = set()
        for player in players:
            all_headers.update(player.keys())
        
        all_headers.discard('Action')
        all_headers.discard('Player_Info')
        
        # Create ordered headers
        headers = []
        for col in csv_columns:
            if col in all_headers:
                headers.append(col)
                all_headers.remove(col)
        headers.extend(sorted(all_headers))
        
        # Ensure Manager and Team_ID are first
        if 'Manager' not in headers:
            headers.insert(0, 'Manager')
        if 'Team_ID' not in headers:
            headers.insert(1, 'Team_ID')
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                
                for player in players:
                    row_data = player.copy()
                    row_data['Manager'] = manager
                    row_data['Team_ID'] = team_id
                    
                    # Clean up data for CSV
                    cleaned_row = {}
                    for header in headers:
                        value = row_data.get(header, '')
                        cleaned_row[header] = str(value).strip() if value is not None else ''
                    
                    writer.writerow(cleaned_row)
            
            return filename
            
        except (FileNotFoundError, PermissionError) as e:
            logger.error(f"File system error exporting team {team_id} to CSV: {e}")
            raise FileOperationError(f"Cannot write CSV file for team {team_id}: {e}") from e
        except (OSError, IOError) as e:
            logger.error(f"I/O error exporting team {team_id} to CSV: {e}")
            raise FileOperationError(f"I/O error writing CSV for team {team_id}: {e}") from e
        except Exception as e:
            # Catch unexpected errors and convert to meaningful exception
            logger.exception(f"Unexpected error exporting team {team_id} to CSV: {e}")
            raise FileOperationError(f"Failed to export team {team_id} to CSV: {e}") from e
    
    def display_teams_table(self, teams: List[Dict[str, str]]) -> None:
        """Display teams in tabular format"""
        if not teams:
            print("No teams found.")
            return
        
        table_data = []
        for team in teams:
            table_data.append([
                team.get('team_id', 'N/A'),
                team.get('team_abbrev', 'N/A'),
                team.get('team_name', 'N/A'),
                team.get('manager_name', 'N/A')
            ])
        
        headers = ['Team ID', 'Abbrev', 'Team Name', 'Manager Name']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    def display_roster_table(self, team_id: str, team_data: Dict[str, Any]) -> None:
        """Display roster in tabular format"""
        if not team_data or not team_data.get('players'):
            print(f"No roster data found for team {team_id}")
            return
        
        players = team_data['players']
        table_data = []
        
        # Define preferred column order (prioritize important columns)
        preferred_columns = [
            'Player Name', 'Team', 'Position', 'Slot', 
            'Projected Points', 'Points', 'Opponent', 'Game Time',
            'Avg Points', 'Last Game', 'Rank', 'Ownership %', 'Start %', 'Trend', 'FPTS'
        ]
        
        # Get all available columns
        all_headers = set()
        for player in players:
            all_headers.update(player.keys())
        
        # Remove unwanted columns
        all_headers.discard('Action')
        all_headers.discard('Player_Info')
        
        # Create ordered headers - prioritize preferred columns
        headers = []
        for col in preferred_columns:
            if col in all_headers:
                headers.append(col)
                all_headers.remove(col)
        
        # Add any remaining columns
        headers.extend(sorted(all_headers))
        
        # Build table data
        for player in players:
            row = []
            for header in headers:
                value = player.get(header, '')
                row.append(str(value) if value is not None else '')
            table_data.append(row)
        
        print(f"\nTeam {team_id} Roster ({len(players)} players):")
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
    


# Global instance for easy access
ff_data = FantasyFootballData()
