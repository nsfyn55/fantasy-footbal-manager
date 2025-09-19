"""
Core data module for Fantasy Football Manager
Provides clean API for data extraction and processing
"""

import os
import time
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from tabulate import tabulate
from playwright.sync_api import sync_playwright, Page


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
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Teams file not found: {input_file}")
        
        try:
            with open(input_file, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find the table and extract rows
            table = soup.find('table')
            if table:
                tbody = table.find('tbody')
                if tbody:
                    rows = tbody.find_all('tr')
                else:
                    rows = table.find_all('tr')
            else:
                rows = soup.find_all('tr')
            
            # Parse each row into team data
            teams = []
            for row in rows:
                team_dict = self._parse_team_row(str(row))
                if team_dict and team_dict.get('team_id'):
                    teams.append(team_dict)
            
            return teams
            
        except Exception as e:
            raise RuntimeError(f"Error parsing teams from {input_file}: {e}")
    
    def get_roster(self, team_id: str) -> Dict[str, Any]:
        """
        Get roster data for a specific team from live ESPN site
        
        Args:
            team_id: Team ID to fetch roster for
            
        Returns:
            Dictionary containing team data and player roster
        """
        team_url = f"https://fantasy.espn.com/football/team?leagueId=1922964857&teamId={team_id}&seasonId=2025"
        
        with sync_playwright() as p:
            try:
                # Launch browser in headless mode
                browser = p.chromium.launch(headless=True)
                
                # Load saved session if available
                if self.session_state:
                    context = browser.new_context(storage_state=self.session_state)
                    page = context.new_page()
                else:
                    page = browser.new_page()
                
                # Navigate to team page
                page.goto(team_url)
                page.wait_for_load_state("domcontentloaded")
                time.sleep(2)
                
                # Extract team data
                team_data = self._extract_team_data_from_page(page)
                
                # Get manager name
                if team_data:
                    manager_name = self._get_manager_name_from_page(page, team_id)
                    team_data['manager_name'] = manager_name
                
                browser.close()
                return team_data
                
            except Exception as e:
                raise RuntimeError(f"Error fetching roster for team {team_id}: {e}")
    
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
            try:
                rosters[team_id] = self.get_roster(team_id)
            except Exception as e:
                print(f"Warning: Failed to fetch roster for team {team_id}: {e}")
                rosters[team_id] = None
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
            
        except Exception as e:
            raise RuntimeError(f"Error exporting to CSV: {e}")
    
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
    
    # Private helper methods
    def _parse_team_row(self, html_row: str) -> Dict[str, str]:
        """Parse a single team row HTML and extract data into a dictionary"""
        soup = BeautifulSoup(html_row, 'html.parser')
        
        tds = soup.find_all('td')
        column_names = {
            0: 'team_id',
            1: 'team_abbrev', 
            2: 'team_name',
            3: 'manager_name'
        }
        
        row_data = {}
        
        for i, td in enumerate(tds[:4]):  # Only process first 4 columns
            cell_div = td.find('div', class_='jsx-2810852873 table--cell')
            
            if cell_div:
                team_name_span = cell_div.find('span', class_='teamName')
                if team_name_span:
                    cell_text = team_name_span.get_text(strip=True)
                else:
                    cell_text = cell_div.get_text(strip=True)
                
                row_data[column_names[i]] = cell_text
            else:
                cell_text = td.get_text(strip=True)
                row_data[column_names[i]] = cell_text
        
        return row_data
    
    def _parse_roster_row(self, html_row: str) -> Dict[str, str]:
        """Parse a single roster row HTML and extract data into a dictionary"""
        soup = BeautifulSoup(html_row, 'html.parser')
        
        # Find all td elements (table cells)
        tds = soup.find_all('td')
        
        # Define meaningful column names based on the headers we saw
        column_names = {
            0: 'Slot',           # QB, RB, WR, TE, FLEX, D/ST, K, Bench, IR
            1: 'Player Name',    # Player name and team/position info
            2: 'Action',         # MOVE button
            3: 'Opponent',       # Opponent team
            4: 'Game Time',      # Game time/status
            5: 'Projected Points', # ESPN projection
            6: 'Points',         # Actual points scored
            7: 'Opponent Rank',  # OPRK
            8: 'Start %',        # %ST
            9: 'Ownership %',    # %ROST
            10: 'Trend',         # +/-
            11: 'Rank',          # PRK (Position Rank)
            12: 'FPTS',          # Fantasy Points (season total)
            13: 'Avg Points',    # Average points
            14: 'Last Game'      # Last game points
        }
        
        # Initialize dictionary to store extracted data
        row_data = {}
        
        # Process each cell
        for i, td in enumerate(tds):
            if i in column_names:
                column_name = column_names[i]
                
                # Skip Action column
                if column_name == 'Action':
                    continue
                    
                # Special handling for Player Name column (column 1)
                if column_name == 'Player Name':
                    # Extract player name, team, and position
                    player_name_elem = td.find('span', class_='truncate')
                    if player_name_elem:
                        player_name = player_name_elem.get_text(strip=True)
                    else:
                        player_name = 'Unknown'
                    
                    # Extract team and position
                    team_elem = td.find('span', class_='playerinfo__playerteam')
                    position_elem = td.find('span', class_='playerinfo__playerpos')
                    
                    team = team_elem.get_text(strip=True) if team_elem else ''
                    position = position_elem.get_text(strip=True) if position_elem else ''
                    
                    row_data['Player Name'] = player_name
                    row_data['Team'] = team
                    row_data['Position'] = position
                    
                else:
                    # For other columns, just get the text content
                    cell_text = td.get_text(strip=True)
                    row_data[column_name] = cell_text
        
        return row_data
    
    def _extract_team_data_from_page(self, page: Page) -> Dict[str, Any]:
        """Extract team data from ESPN page"""
        try:
            html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find the table
            table = soup.find('table', class_='Table')
            if not table:
                return None
            
            # Find tbody and get all rows
            tbody = table.find('tbody', class_='Table__TBODY')
            if not tbody:
                return None
            
            rows = tbody.find_all('tr')
            
            # Parse each row
            players = []
            for row in rows:
                # Skip totals rows
                if 'total-col' in row.get('class', []):
                    continue
                    
                player_dict = self._parse_roster_row(str(row))
                
                # Only add if we have meaningful data and not TOTALS
                if (player_dict and 
                    player_dict.get('Player Name') and 
                    player_dict.get('Player Name') != 'Unknown' and
                    player_dict.get('Opponent') != 'TOTALS'):
                    players.append(player_dict)
            
            return {'players': players}
            
        except Exception as e:
            raise RuntimeError(f"Error extracting team data: {e}")
    
    def _get_manager_name_from_page(self, page: Page, team_id: str) -> str:
        """Extract manager name from the team page"""
        try:
            manager_selectors = [
                ".teamName.truncate",
                ".teamName",
                "span.teamName",
                "h1",
                ".team-name",
                ".manager-name", 
                "[data-testid='team-name']",
                ".team-header h1",
                ".team-header h2"
            ]
            
            for selector in manager_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        text = element.inner_text().strip()
                        if text and len(text) > 0:
                            text = text.replace(f"Team {team_id}", "").strip()
                            if text:
                                return text
                except:
                    continue
            
            # Fallback to generic name
            return f"Manager{team_id}"
            
        except Exception as e:
            return f"Manager{team_id}"
    
    def _parse_player_name(self, full_text: str) -> Dict[str, str]:
        """Parse combined player name text to extract name, team, and position"""
        if not full_text or full_text in ['MOVE', 'TOTALS', '']:
            return {'Player Name': full_text, 'Team': '', 'Position': ''}
        
        # Common NFL team abbreviations
        clean_teams = ['Ari', 'Atl', 'Bal', 'Buf', 'Car', 'Chi', 'Cin', 'Cle', 'Dal', 'Den', 
                       'Det', 'GB', 'Hou', 'Ind', 'Jax', 'KC', 'LV', 'LAC', 'LAR', 'Mia', 
                       'Min', 'NE', 'NO', 'NYG', 'NYJ', 'Phi', 'Pit', 'SF', 'Sea', 'TB', 
                       'Ten', 'Was', 'Wsh']
        
        # Common position abbreviations
        positions = ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST', 'FLEX', 'Bench', 'IR']
        
        # Try to find position first
        position = ''
        for pos in positions:
            if pos in full_text:
                position = pos
                break
        
        # Try to find clean team abbreviation
        team = ''
        for team_abbrev in clean_teams:
            if team_abbrev in full_text:
                team = team_abbrev
                break
        
        # Extract name by removing team and position
        name = full_text
        if team:
            name = name.replace(team, '')
        if position:
            name = name.replace(position, '')
        
        # Clean up the name
        name = name.strip()
        while name and name[-1].isupper() and len(name) > 1:
            name = name[:-1].strip()
        
        return {'Player Name': name, 'Team': team, 'Position': position}
    
    def _determine_player_status(self, player_data: Dict[str, str], player_index: int) -> str:
        """Determine roster status for a player"""
        position = player_data.get('Position', '')
        projected_points = player_data.get('Projected Points', '0.0')
        start_percent = player_data.get('Start %', '0%')
        
        # Convert to float for comparison
        try:
            projected_float = float(projected_points)
        except (ValueError, TypeError):
            projected_float = 0.0
        
        try:
            start_float = float(start_percent.replace('%', ''))
        except (ValueError, TypeError):
            start_float = 0.0
        
        # IR if projected points is 0
        if projected_float == 0.0:
            return 'IR'
        
        # Bench if beyond first 10 players or start % < 50%
        if player_index >= 10 or start_float < 50:
            return 'BE'
        
        # Otherwise, use position
        return position if position else 'BE'


# Global instance for easy access
ff_data = FantasyFootballData()
