"""
ESPN Fantasy Football data source
"""

import os
import time
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page


def fetch_roster(team_id: str, session_state: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch roster data for a specific team from ESPN
    
    Args:
        team_id: Team ID to fetch roster for
        session_state: Optional saved session state for authentication
        
    Returns:
        Raw ESPN roster data or None if failed
    """
    team_url = f"https://fantasy.espn.com/football/team?leagueId=1922964857&teamId={team_id}&seasonId=2025"
    
    with sync_playwright() as p:
        try:
            # Launch browser in headless mode
            browser = p.chromium.launch(headless=True)
            
            # Load saved session if available
            if session_state:
                context = browser.new_context(storage_state=session_state)
                page = context.new_page()
            else:
                page = browser.new_page()
            
            # Navigate to team page
            page.goto(team_url)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(2)
            
            # Extract team data
            team_data = _extract_team_data_from_page(page)
            
            # Get manager name
            if team_data:
                manager_name = _get_manager_name_from_page(page, team_id)
                team_data['manager_name'] = manager_name
            
            browser.close()
            return team_data
            
        except Exception as e:
            raise RuntimeError(f"Error fetching roster for team {team_id}: {e}")


def fetch_teams(input_file: str = "html_input/teams_table.html") -> List[Dict[str, str]]:
    """
    Fetch teams data from HTML file
    
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
            team_dict = _parse_team_row(str(row))
            if team_dict and team_dict.get('team_id'):
                teams.append(team_dict)
        
        return teams
        
    except Exception as e:
        raise RuntimeError(f"Error parsing teams from {input_file}: {e}")


def _parse_team_row(html_row: str) -> Dict[str, str]:
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


def _extract_team_data_from_page(page: Page) -> Dict[str, Any]:
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
                
            player_dict = _parse_roster_row(str(row))
            
            # Only add if we have meaningful data and not TOTALS
            if (player_dict and 
                player_dict.get('Player Name') and 
                player_dict.get('Player Name') != 'Unknown' and
                player_dict.get('Opponent') != 'TOTALS'):
                players.append(player_dict)
        
        return {'players': players}
        
    except Exception as e:
        raise RuntimeError(f"Error extracting team data: {e}")


def _get_manager_name_from_page(page: Page, team_id: str) -> str:
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


def _parse_roster_row(html_row: str) -> Dict[str, str]:
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
