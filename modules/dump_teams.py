"""
Dump teams module for exporting opponent team data to CSV
"""

import sys
import time
import argparse
from typing import List, Optional
from playwright.sync_api import sync_playwright


def dump_teams_command(args):
    """Handle dump-teams command"""
    print("Dumping teams...")
    
    try:
        if args.team:
            # Dump specific teams
            for team_id in args.team:
                print(f"\nDumping team ID: {team_id}")
                team_data = fetch_team_data(team_id)
                display_team_data(team_id, team_data)
        else:
            # Dump all teams (for now, just dump team 8 as example)
            print("Dumping all teams (starting with team 8)...")
            team_data = fetch_team_data("8")
            display_team_data("8", team_data)
        
        # Hang and wait for additional processing instructions
        print("\nWaiting for additional processing instructions...")
        input("Press Enter when ready to continue...")
            
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

def fetch_team_data(team_id: str):
    """Fetch team data from ESPN Fantasy Football using saved session"""
    # Import Chrome launcher from login module
    from modules.login import launch_chrome
    
    # Ensure Chrome is running
    if not launch_chrome():
        print("Failed to launch Chrome. Please start Chrome manually with remote debugging.")
        return None
    
    team_url = f"https://fantasy.espn.com/football/team?leagueId=1922964857&teamId={team_id}&seasonId=2025"
    
    with sync_playwright() as p:
        try:
            # Connect to existing Chrome browser
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            
            # Load saved session if available
            session_state = load_session()
            if session_state:
                context = browser.new_context(storage_state=session_state)
                page = context.new_page()
                print("Using saved session...")
            else:
                page = browser.new_page()
                print("No saved session found, using new page...")
            
            print(f"Opening new tab and navigating to: {team_url}")
            page.goto(team_url)
            
            # Wait for the page to load
            page.wait_for_load_state("networkidle")
            time.sleep(3)
            
            # Extract team data
            team_data = extract_team_data_from_page(page)
            
            # Keep the browser open indefinitely for inspection
            print("Browser will stay open for inspection. Press Ctrl+C to close when done.")
            try:
                while True:
                    time.sleep(60)  # Sleep for 1 minute intervals
            except KeyboardInterrupt:
                print("\nClosing browser...")
            
            return team_data
            
        except Exception as e:
            print(f"Error connecting to existing Chrome: {e}")
            print("Make sure Chrome is running with remote debugging enabled")
            raise


def extract_team_data_from_page(page):
    """Extract team data from the ESPN team page"""
    team_data = []
    
    try:
        # Wait for roster table to load
        page.wait_for_selector("table", timeout=10000)
        
        # Look for roster table - ESPN uses various selectors
        roster_selectors = [
            "table[class*='roster']",
            "table[class*='Table']", 
            "table[class*='table']",
            ".roster-table",
            "[data-testid*='roster']"
        ]
        
        roster_table = None
        for selector in roster_selectors:
            try:
                roster_table = page.query_selector(selector)
                if roster_table:
                    print(f"Found roster table with selector: {selector}")
                    break
            except:
                continue
        
        if not roster_table:
            # Fallback: look for any table with player data
            tables = page.query_selector_all("table")
            for table in tables:
                rows = table.query_selector_all("tr")
                if len(rows) > 1:  # Has header + data rows
                    roster_table = table
                    print("Using fallback table detection")
                    break
        
        if roster_table:
            # Extract table data
            rows = roster_table.query_selector_all("tr")
            
            for i, row in enumerate(rows):
                if i == 0:  # Skip header row
                    continue
                    
                cells = row.query_selector_all("td, th")
                if len(cells) > 0:
                    player_data = []
                    for cell in cells:
                        text = cell.inner_text().strip()
                        if text:
                            player_data.append(text)
                    
                    if player_data:
                        team_data.append(player_data)
        else:
            print("Could not find roster table. Page content:")
            print(page.content()[:1000])  # First 1000 chars for debugging
            
    except Exception as e:
        print(f"Error extracting team data: {e}")
        # Try to get any player-related data
        try:
            player_elements = page.query_selector_all("[class*='player'], [class*='Player']")
            for element in player_elements[:10]:  # First 10 player elements
                text = element.inner_text().strip()
                if text and len(text) > 2:
                    team_data.append([text])
        except:
            pass
    
    return team_data


def display_team_data(team_id: str, team_data):
    """Display team data in a formatted way"""
    if not team_data:
        print(f"No team data found for team {team_id}")
        return
    
    print(f"\n{'='*60}")
    print(f"TEAM {team_id} ROSTER")
    print(f"{'='*60}")
    
    for i, player in enumerate(team_data, 1):
        if len(player) == 1:
            print(f"{i:2d}. {player[0]}")
        else:
            # Format multi-column data
            player_info = " | ".join(player)
            print(f"{i:2d}. {player_info}")
    
    print(f"{'='*60}")
    print(f"Total players found: {len(team_data)}")
    print(f"{'='*60}\n")


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
        default='data/teams.csv',
        help='Output CSV file path (default: data/teams.csv)'
    )
    parser.add_argument(
        '--format',
        choices=['csv', 'json'],
        default='csv',
        help='Output format (default: csv)'
    )


def dump_single_team(team_id: str, output_path: str, format: str):
    """Dump a single team's data"""
    # TODO: Implement single team dumping
    pass


def dump_multiple_teams(team_ids: List[str], output_path: str, format: str):
    """Dump multiple teams' data"""
    # TODO: Implement multiple teams dumping
    pass


def dump_all_teams(output_path: str, format: str):
    """Dump all teams' data"""
    # TODO: Implement all teams dumping
    pass
