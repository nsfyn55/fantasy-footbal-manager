"""
Dump teams module for exporting opponent team data to CSV
"""

import sys
import time
import argparse
import csv
import os
from typing import List, Optional
from playwright.sync_api import sync_playwright
from tabulate import tabulate


# Team ID to Manager mapping for analytics
TEAM_MANAGERS = {
    "1": "Manager1",
    "2": "Manager2", 
    "3": "Manager3",
    "4": "Manager4",
    "5": "Manager5",
    "6": "Manager6",
    "7": "Manager7",
    "8": "Manager8",
    "9": "Manager9",
    "10": "Manager10",
    "11": "Manager11",
    "12": "Manager12"
}


def parse_player_name(full_text):
    """Parse combined player name text to extract name, team, and position"""
    if not full_text or full_text in ['MOVE', 'TOTALS', '']:
        return {'name': full_text, 'team': '', 'position': ''}
    
    # Common NFL team abbreviations (clean team names only)
    clean_teams = ['Ari', 'Atl', 'Bal', 'Buf', 'Car', 'Chi', 'Cin', 'Cle', 'Dal', 'Den', 
                   'Det', 'GB', 'Hou', 'Ind', 'Jax', 'KC', 'LV', 'LAC', 'LAR', 'Mia', 
                   'Min', 'NE', 'NO', 'NYG', 'NYJ', 'Phi', 'Pit', 'SF', 'Sea', 'TB', 
                   'Ten', 'Was', 'Wsh']  # Added Wsh for Washington
    
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
    
    # Clean up the name - remove any remaining single letters or special characters at the end
    name = name.strip()
    # Remove trailing single letters that might be leftover
    while name and name[-1].isupper() and len(name) > 1:
        name = name[:-1].strip()
    
    return {'name': name, 'team': team, 'position': position}


def determine_player_status(player_data, player_index, total_players):
    """Determine if player is in current roster, bench, or IR"""
    position = player_data.get('Position', '').strip()
    player_name = player_data.get('Player Name', '').strip()
    status = player_data.get('Status', '').strip()
    projected_points = player_data.get('Projected Points', '0')
    start_percent = player_data.get('Start %', '0')
    
    # Check for IR status first
    if 'IR' in status.upper() or 'INJURED' in status.upper() or 'OUT' in status.upper():
        return 'IR'
    
    # Check for low projected points (likely IR)
    try:
        proj_pts = float(projected_points)
        if proj_pts == 0.0 and position in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
            return 'IR'
    except (ValueError, TypeError):
        pass
    
    # Check if position indicates bench
    if position in ['Bench', 'FLEX']:
        return 'BE'
    
    # Based on typical fantasy roster structure:
    # First ~9-10 players are usually starters (QB, RB, RB, WR, WR, TE, FLEX, K, D/ST)
    # Players after that are typically bench
    
    # If we're in the first 10 players and have a valid position, likely a starter
    if player_index < 10 and position in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
        return position
    
    # If we're beyond the first 10 players, likely bench
    if player_index >= 10:
        return 'BE'
    
    # Check for low start percentage (likely bench)
    try:
        start_pct = float(start_percent)
        if start_pct < 50.0 and position in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
            return 'BE'
    except (ValueError, TypeError):
        pass
    
    # Check if it's a valid position (current roster) - return just the position
    if position in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
        return position
    
    # Default to bench if unclear
    return 'BE'


def dump_teams_command(args):
    """Handle dump-teams command"""
    print("Dumping teams...")
    
    try:
        if args.team:
            # Dump specific teams
            for team_id in args.team:
                success = dump_single_team(
                    team_id=team_id,
                    output_path=args.output,
                    format=args.format,
                    export_csv=args.csv
                )
                if not success:
                    print(f"Failed to dump team {team_id}")
        else:
            # Dump all teams (for now, just dump team 8 as example)
            print("Dumping all teams (starting with team 8)...")
            team_data = fetch_team_data("8")
            display_team_data("8", team_data)
        
        # Operation completed successfully
        print("\nTeam data extraction completed successfully!")
            
    except Exception as e:
        print(f"Error dumping teams: {e}")
        sys.exit(1)


def load_session():
    """Load session state from file if it exists"""
    import os
    import json
    session_file = ".fantasy-football-manager/session.json"
    if os.path.exists(session_file):
        try:
            with open(session_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading session: {e}")
    return None


def export_team_to_csv(team_id: str, team_data, filename: str = None):
    """Export team data to CSV with Manager column for analytics"""
    if not team_data or not team_data.get('players'):
        print(f"No team data found for team {team_id}")
        return None
    
    players = team_data['players']
    # Use manager name from team data if available, otherwise fallback to mapping
    manager = team_data.get('manager_name') or TEAM_MANAGERS.get(team_id, f"Manager{team_id}")
    
    if not filename:
        # Default to output folder
        filename = f"output/team_{team_id}_roster.csv"
    elif not filename.startswith('/') and not filename.startswith('./') and not filename.startswith('../'):
        # If it's a relative path and doesn't specify output folder, put it in output
        if not filename.startswith('output/'):
            filename = f"output/{filename}"
    
    # Define preferred column order with Manager first for analytics
    csv_columns = [
        'Manager', 'Team_ID', 'Player Name', 'Team', 'Position', 'Roster Status', 
        'Opponent', 'Game Time', 'Projected Points', 'Points', 'Avg Points', 
        'Last Game', 'Rank', 'Ownership %', 'Start %', 'Status', 'Trend', 'Notes'
    ]
    
    # Get all available columns from the data
    all_headers = set()
    for player in players:
        all_headers.update(player.keys())
    
    # Remove unwanted columns
    all_headers.discard('Action')
    all_headers.discard('Player_Info')
    
    # Create ordered headers list
    headers = []
    for col in csv_columns:
        if col in all_headers:
            headers.append(col)
            all_headers.remove(col)
    
    # Add any remaining columns
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
                # Create a copy of player data and add Manager and Team_ID
                row_data = player.copy()
                row_data['Manager'] = manager
                row_data['Team_ID'] = team_id
                
                # Clean up data for CSV
                cleaned_row = {}
                for header in headers:
                    value = row_data.get(header, '')
                    # Convert to string and handle None values
                    if value is None:
                        cleaned_row[header] = ''
                    else:
                        cleaned_row[header] = str(value).strip()
                
                writer.writerow(cleaned_row)
        
        print(f"✅ Exported {len(players)} players to {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Error exporting to CSV: {e}")
        return None


def fetch_team_data(team_id: str):
    """Fetch team data from ESPN Fantasy Football using headless browser"""
    team_url = f"https://fantasy.espn.com/football/team?leagueId=1922964857&teamId={team_id}&seasonId=2025"
    
    with sync_playwright() as p:
        try:
            # Launch browser in headless mode
            browser = p.chromium.launch(headless=True)
            
            # Load saved session if available
            session_state = load_session()
            if session_state:
                context = browser.new_context(storage_state=session_state)
                page = context.new_page()
                print("Using saved session...")
            else:
                page = browser.new_page()
                print("No saved session found, using new page...")
            
            print(f"Navigating to: {team_url}")
            page.goto(team_url)
            
            # Wait for the page to load (optimized - much faster)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(2)
            
            # Extract team data
            team_data = extract_team_data_from_page(page)
            
            # Get manager name from page
            if team_data:
                manager_name = get_manager_name_from_page(page, team_id)
                team_data['manager_name'] = manager_name
            
            # Close browser
            browser.close()
            
            return team_data
            
        except Exception as e:
            print(f"Error fetching team data: {e}")
            raise


def get_manager_name_from_page(page, team_id):
    """Extract manager name from the team page"""
    try:
        # Look for manager name in common locations
        manager_selectors = [
            "h1",  # Often the team name/manager name is in h1
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
                        # Clean up the text - remove team numbers, extra whitespace
                        text = text.replace(f"Team {team_id}", "").strip()
                        if text:
                            print(f"Found manager name: {text}")
                            return text
            except:
                continue
        
        # Fallback to TEAM_MANAGERS mapping
        return TEAM_MANAGERS.get(team_id, f"Manager{team_id}")
        
    except Exception as e:
        print(f"Error extracting manager name: {e}")
        return TEAM_MANAGERS.get(team_id, f"Manager{team_id}")


def extract_team_data_from_page(page):
    """Extract team data from the ESPN team page using improved HTML table parsing"""
    try:
        # Wait for the roster table to load
        page.wait_for_selector(".jsx-1925058086.team-page", timeout=10000)
        
        # Wait for the table to be fully loaded
        page.wait_for_selector("div.Table__Scroller table.Table", timeout=10000)
        
        print("Extracting roster data from HTML table...")
        
        # Get the HTML content and parse it
        html_content = page.content()
        
        # Use BeautifulSoup to parse the HTML
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the parent div with class "Table__Scroller"
        table_scroller = soup.find('div', class_='Table__Scroller')
        
        if not table_scroller:
            print("Could not find div with class 'Table__Scroller'")
            return None
        
        # Find the table within the scroller div
        table = table_scroller.find('table', class_='Table')
        
        if not table:
            print("Could not find table with class 'Table'")
            return None
        
        print("Found table! Extracting player data...")
        
        players = []
        
        # Find table body
        tbody = table.find('tbody')
        if not tbody:
            print("No tbody found, looking for rows directly in table")
            rows = table.find_all('tr')
        else:
            rows = tbody.find_all('tr')
        
        # Get header information for column mapping
        header_row = table.find('tr')
        headers = []
        if header_row:
            for th in header_row.find_all(['th', 'td']):
                headers.append(th.get_text(strip=True))
        
        print(f"Found {len(headers)} columns: {headers}")
        print(f"Found {len(rows)} rows")
        
        # Define meaningful column names based on observed data
        column_mapping = {
            'STARTERS': 'Position',
            'NFL Week 3': 'Player_Info',  # This will be parsed into separate columns
            '2025 season': 'Action',  # Will be filtered out in display
            'column_3': 'Opponent',
            'column_4': 'Game Time',
            'column_5': 'Projected Points',
            'column_6': 'Status',
            'column_7': 'Rank',
            'column_8': 'Ownership %',
            'column_9': 'Start %',
            'column_10': 'Points',
            'column_11': 'Avg Points',
            'column_12': 'Last Game',
            'column_13': 'Trend',
            'column_14': 'Notes'
        }
        
        # Extract data from each row
        for i, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])
            
            # Skip header row if it's the first row
            if i == 0 and all(cell.name == 'th' for cell in cells):
                continue
                
            if len(cells) == 0:
                continue
                
            player_data = {}
            
            # Map cell data to headers
            for j, cell in enumerate(cells):
                original_header = headers[j] if j < len(headers) else f"column_{j}"
                header = column_mapping.get(original_header, original_header)
                
                # Get text content, handling nested elements
                text = cell.get_text(strip=True)
                
                # Special handling for player name column
                if header == 'Player_Info' and text:
                    parsed_player = parse_player_name(text)
                    player_data['Player Name'] = parsed_player['name']
                    player_data['Team'] = parsed_player['team']
                    player_data['Position'] = parsed_player['position']
                else:
                    player_data[header] = text
            
            # Skip TOTALS rows and empty rows
            if player_data and player_data.get('Player Name', '').strip() not in ['TOTALS', 'MOVE', '']:
                # Determine player status based on position and other indicators
                status = determine_player_status(player_data, len(players), len(rows))
                player_data['Roster Status'] = status
                players.append(player_data)
        
        print(f"Successfully extracted {len(players)} players")
        return {
            "team_id": "8",
            "players": players,
            "status": "loaded",
            "url": page.url
        }
        
    except Exception as e:
        print(f"Error extracting team data: {e}")
        import traceback
        traceback.print_exc()
        return None


def display_team_data(team_id: str, team_data):
    """Display team data in a formatted way using tabular format"""
    if not team_data or not team_data.get('players'):
        print(f"No team data found for team {team_id}")
        return
    
    players = team_data['players']
    
    if not players:
        print("No player data to display")
        return
    
    # Define preferred column order for better display (excluding Action and Player_Info)
    preferred_columns = [
        'Player Name', 'Team', 'Position', 'Roster Status', 'Opponent', 'Game Time', 
        'Projected Points', 'Points', 'Avg Points', 'Last Game', 'Rank', 
        'Ownership %', 'Start %', 'Status', 'Trend', 'Notes'
    ]
    
    # Get all available columns from the data
    all_headers = set()
    for player in players:
        all_headers.update(player.keys())
    
    # Remove unwanted columns
    all_headers.discard('Action')
    all_headers.discard('Player_Info')
    
    # Create ordered headers list
    headers = []
    for col in preferred_columns:
        if col in all_headers:
            headers.append(col)
            all_headers.remove(col)
    
    # Add any remaining columns
    headers.extend(sorted(all_headers))
    
    # Prepare table data
    table_data = []
    for i, player in enumerate(players):
        row = []
        for header in headers:
            if header in player and player[header].strip():
                # Truncate long text for better table display
                text = str(player[header])
                if len(text) > 25:
                    text = text[:22] + "..."
                row.append(text)
            else:
                row.append("")
        table_data.append(row)
    
    print(f"\n--- Fantasy Football Team {team_id} Roster ({len(players)} players) ---")
    print(tabulate(table_data, headers=headers, tablefmt="grid", maxcolwidths=[25]*len(headers)))
    
    print(f"\nTotal columns: {len(headers)}")
    print(f"Total players: {len(players)}")


def add_dump_teams_arguments(parser: argparse.ArgumentParser):
    """Add dump-teams specific arguments to the parser"""
    parser.add_argument(
        '--team', '-t',
        nargs='+',
        required=True,
        help='Team ID(s) to dump (e.g., 8 for your team)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output CSV file path (default: output/team_{id}_roster.csv)'
    )
    parser.add_argument(
        '--csv',
        action='store_true',
        help='Export team data to CSV with Manager column for analytics'
    )
    parser.add_argument(
        '--format',
        choices=['csv', 'json'],
        default='csv',
        help='Output format (default: csv)'
    )


def dump_single_team(team_id: str, output_path: str = None, format: str = 'csv', export_csv: bool = False):
    """Dump a single team's data"""
    print(f"Dumping team ID: {team_id}")
    
    # Fetch team data
    team_data = fetch_team_data(team_id)
    
    if not team_data:
        print(f"Failed to fetch data for team {team_id}")
        return False
    
    # Display team data
    display_team_data(team_id, team_data)
    
    # Export to CSV if requested
    if export_csv or format == 'csv':
        csv_filename = export_team_to_csv(team_id, team_data, output_path)
        if csv_filename:
            print(f"Team data exported to: {csv_filename}")
            return True
    
    print("Team data extraction completed successfully!")
    return True


def dump_multiple_teams(team_ids: List[str], output_path: str, format: str):
    """Dump multiple teams' data"""
    # TODO: Implement multiple teams dumping
    pass


def dump_all_teams(output_path: str, format: str):
    """Dump all teams' data"""
    # TODO: Implement all teams dumping
    pass
