"""
List teams module for displaying all league teams and their IDs
"""

from bs4 import BeautifulSoup
import os
from tabulate import tabulate


def parse_team_row(html_row):
    """Parse a single team row HTML and extract data into a dictionary"""
    soup = BeautifulSoup(html_row, 'html.parser')
    
    # Find all td elements (table cells)
    tds = soup.find_all('td')
    
    # Define meaningful column names for the first 4 columns
    column_names = {
        0: 'team_id',
        1: 'team_abbrev', 
        2: 'team_name',
        3: 'manager_name'
    }
    
    # Initialize dictionary to store extracted data
    row_data = {}
    
    # Process only the first 4 columns (0-3) and extract the text from the table-cell div
    for i, td in enumerate(tds[:4]):  # Only process first 4 columns
        # Look for the specific table-cell div with class "jsx-2810852873 table--cell"
        cell_div = td.find('div', class_='jsx-2810852873 table--cell')
        
        if cell_div:
            # Check if this is the team name column (has teamName class)
            team_name_span = cell_div.find('span', class_='teamName')
            if team_name_span:
                # Extract team name from the span
                cell_text = team_name_span.get_text(strip=True)
            else:
                # Get the text content normally
                cell_text = cell_div.get_text(strip=True)
            
            row_data[column_names[i]] = cell_text
        else:
            # If no table-cell div found, try to get any text from the td
            cell_text = td.get_text(strip=True)
            row_data[column_names[i]] = cell_text
    
    return row_data


def parse_teams_table_from_file(file_path):
    """Parse a full HTML table file and return a list of team dictionaries"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return []
    
    try:
        # Read the HTML file
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Step 1: Get the rows from the table as a list of HTML fragments (each one a row)
        # Find the table first
        table = soup.find('table')
        if table:
            # Look for tbody within the table
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
            else:
                # If no tbody, get all tr elements from the table
                rows = table.find_all('tr')
        else:
            # Fallback: find all tr elements in the document
            rows = soup.find_all('tr')
        
        row_html_fragments = [str(row) for row in rows]
        
        # Step 2 & 3: Loop over those rows, feed each to parse_team_row(), put each returned dictionary into a list
        list_of_dictionaries = []
        for row_html in row_html_fragments:
            team_dict = parse_team_row(row_html)
            # Only add dictionaries that have meaningful data
            if team_dict and team_dict.get('team_id'):
                list_of_dictionaries.append(team_dict)
        
        # Step 4: Return the list of dictionaries
        return list_of_dictionaries
        
    except Exception as e:
        print(f"Error parsing HTML file: {e}")
        return []


def display_teams_table(teams_list):
    """Display teams in a nice tabular format"""
    if not teams_list:
        print("No teams found.")
        return
    
    # Prepare data for tabulation
    table_data = []
    for team in teams_list:
        table_data.append([
            team.get('team_id', 'N/A'),
            team.get('team_abbrev', 'N/A'),
            team.get('team_name', 'N/A'),
            team.get('manager_name', 'N/A')
        ])
    
    # Define headers
    headers = ['Team ID', 'Abbrev', 'Team Name', 'Manager Name']
    
    # Display the table
    print(tabulate(table_data, headers=headers, tablefmt='grid'))


# Test the function with the provided HTML row
test_html = '''<tr class="rowbg-white Table__TR Table__TR--sm Table__even" data-idx="0"><td class="leagueMembersTable__column Table__TD"><div class="leagueMembersTable__column"><div class="jsx-2810852873 table--cell">1</div></div></td><td class="leagueMembersTable__column Table__TD"><div class="leagueMembersTable__column"><div class="jsx-2810852873 table--cell"><span class="teamAbbrev">ZA</span></div></div></td><td class="leagueMembersTable__column Table__TD"><div class="leagueMembersTable__column"><div title="NEPA Pizza" class="jsx-2810852873 table--cell team__column"><div class="jsx-740313253 flex team__column__content w-100"><a class="AnchorLink flex items-center team--link inline-flex v-mid" tabindex="0" rel=""><div class="jsx-1141285347 croppable-image team-logo custom-logo w-100 customTeamLogo" style="height: 20px; overflow: hidden; width: 20px;"><div class="image-custom" style="background-image: url(&quot;https://mystique-api.fantasy.espn.com/apis/v1/domains/lm/images/42942cf0-8800-11f0-89de-d1ac062a5dc6&quot;);"><img src="https://mystique-api.fantasy.espn.com/apis/v1/domains/lm/images/42942cf0-8800-11f0-89de-d1ac062a5dc6" class="dn"></div></div><span title="NEPA Pizza" class="teamName truncate">NEPA Pizza</span></a></div></div></div></td><td class="leagueMembersTable__column Table__TD"><div class="leagueMembersTable__column"><div class="jsx-2810852873 table--cell">Brandon Mirigliani</div></div></td><td class="leagueMembersTable__column Table__TD"><div class="leagueMembersTable__column"><div class="jsx-2810852873 table--cell"><a class="AnchorLink clr-link" tabindex="0" rel="" href="/football/league/email?seasonId=2025&amp;leagueId=1922964857&amp;memberId={1424A1BE-BB7D-49E9-82D5-F474BD5B5BF2}">Send Email</a></div></div></td><td class="leagueMembersTable__column Table__TD"><div class="leagueMembersTable__column"><div class="jsx-2810852873 table--cell">Joined</div></div></td><td class="leagueMembersTable__column Table__TD"><div class="leagueMembersTable__column"><div class="jsx-2810852873 table--cell"><div class="leagueMembersAction"></div></div></div></td></tr>'''

if __name__ == "__main__":
    # Test the single row function
    print("=== Testing single row function ===")
    result = parse_team_row(test_html)
    print("Parsed row data:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*50)
    print("=== Testing full table function ===")
    
    # Test the full table function
    teams_list = parse_teams_table_from_file("html_input/teams_table.html")
    print(f"Found {len(teams_list)} teams:")
    print()
    
    # Display in tabular format
    display_teams_table(teams_list)