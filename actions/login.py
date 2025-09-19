"""
Login module for ESPN Fantasy Football
"""

import time
import os
import json
import subprocess
import psutil
from playwright.sync_api import sync_playwright


def load_credentials():
    """Load credentials from file"""
    try:
        credentials = {}
        with open(".fantasy-football-manager/credentials", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    credentials[key.strip()] = value.strip()
        return credentials
    except Exception as e:
        print(f"Error reading credentials: {e}")
        return None


def save_session(context):
    """Save the browser context state to file"""
    try:
        os.makedirs(".fantasy-football-manager", exist_ok=True)
        storage_state = context.storage_state()
        with open(".fantasy-football-manager/session.json", "w") as f:
            json.dump(storage_state, f)
        print("Session saved successfully!")
        return True
    except Exception as e:
        print(f"Error saving session: {e}")
        return False

def load_session():
    """Load session state from file if it exists"""
    session_file = ".fantasy-football-manager/session.json"
    if os.path.exists(session_file):
        try:
            with open(session_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading session: {e}")
    return None

def check_chrome_running():
    """Check if Chrome is running with remote debugging"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['name'] and 'Chrome' in proc.info['name']:
                cmdline = proc.info['cmdline']
                if cmdline and '--remote-debugging-port=9222' in ' '.join(cmdline):
                    return True
        return False
    except Exception:
        return False

def launch_chrome():
    """Launch Chrome with remote debugging if not already running"""
    if check_chrome_running():
        print("Chrome with remote debugging is already running")
        return True
    
    print("Launching Chrome with remote debugging...")
    try:
        chrome_cmd = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "--remote-debugging-port=9222",
            "--user-data-dir=/tmp/chrome-persistent",
            "--no-first-run",
            "--no-default-browser-check"
        ]
        
        subprocess.Popen(chrome_cmd, 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        
        # Wait for Chrome to start
        print("Waiting for Chrome to start...")
        time.sleep(3)
        
        # Verify it's running
        if check_chrome_running():
            print("Chrome launched successfully!")
            return True
        else:
            print("Failed to launch Chrome")
            return False
            
    except Exception as e:
        print(f"Error launching Chrome: {e}")
        return False

def perform_login(credentials):
    """Perform the actual login using Playwright with session persistence"""
    # Ensure Chrome is running
    if not launch_chrome():
        print("Failed to launch Chrome. Please start Chrome manually with remote debugging.")
        return False
    
    with sync_playwright() as p:
        try:
            # Connect to existing Chrome browser
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            
            # Create context with saved session if available
            session_state = load_session()
            context = browser.new_context(storage_state=session_state)
            page = context.new_page()
            
            # Check if already logged in by trying to access team page
            print("Checking if already logged in...")
            team_url = f"https://fantasy.espn.com/football/team?leagueId={credentials.get('league_id', '1922964857')}&teamId={credentials.get('team_id', '8')}&seasonId=2025"
            page.goto(team_url)
            time.sleep(3)
            
            # Check if we're on the team page (not redirected to login)
            if "fantasy.espn.com/football/team" in page.url:
                print("Already logged in! Session restored successfully.")
                save_session(context)
                return True
            
            print("Not logged in, performing login...")
            
            # Navigate to ESPN Fantasy page for login
            page.goto("https://www.espn.com/fantasy/#")

            print("Navigating to ESPN Fantasy page...")
            page.goto("https://www.espn.com/fantasy/#")

            print("Waiting for login icon to load...")
            page.wait_for_selector("#global-user-trigger", timeout=10000)

            print("Clicking the login icon...")
            page.click("#global-user-trigger")

            print("Waiting for dropdown to expand...")
            time.sleep(2)

            print("Clicking the 'Log In' link in dropdown...")
            page.click("a[data-affiliatename='espn'][data-behavior='overlay']:has-text('Log In')")

            print("Waiting for login form to load...")
            time.sleep(3)

            print("Looking for email input field in iframes...")
            iframes = page.query_selector_all("iframe")
            print(f"Found {len(iframes)} iframes on the page")
            
            email_field = None
            iframe_with_form = None
            
            for i, iframe in enumerate(iframes):
                try:
                    print(f"Checking iframe {i+1}...")
                    iframe_content = iframe.content_frame()
                    if iframe_content:
                        email_field = iframe_content.query_selector("#InputIdentityFlowValue")
                        if email_field and email_field.is_visible():
                            print(f"Found email field in iframe {i+1}")
                            iframe_with_form = iframe_content
                            break
                except Exception as e:
                    print(f"Could not access iframe {i+1}: {e}")
                    continue
            
            if not email_field:
                print("Could not find email field")
                return False
            
            print("Entering email...")
            email_field.fill(credentials['username'])
            
            print("Looking for Continue button...")
            continue_button = iframe_with_form.query_selector("#BtnSubmit")
            if continue_button:
                print("Clicking Continue button...")
                continue_button.click()
                print("Email entered and Continue clicked!")
            else:
                print("Could not find Continue button")
                return False
            
            print("Waiting for password field to appear...")
            time.sleep(3)
            
            print("Looking for password field in iframes...")
            password_field = None
            
            for i, iframe in enumerate(iframes):
                try:
                    print(f"Checking iframe {i+1} for password field...")
                    iframe_content = iframe.content_frame()
                    if iframe_content:
                        password_field = iframe_content.query_selector("input[type='password']")
                        if password_field and password_field.is_visible():
                            print(f"Found password field in iframe {i+1}")
                            iframe_with_form = iframe_content
                            break
                except Exception as e:
                    print(f"Could not access iframe {i+1}: {e}")
                    continue
            
            if not password_field:
                print("Could not find password field")
                return False
            
            print("Entering password...")
            password_field.fill(credentials['password'])
            
            print("Looking for login button...")
            login_button = iframe_with_form.query_selector("button[type='submit']")
            if login_button:
                print("Clicking login button...")
                login_button.click()
                print("Password entered and login button clicked!")
            else:
                print("Could not find login button")
                return False
            
            print("Waiting for login to complete...")
            time.sleep(5)
            
            # Navigate to team page to verify login
            print("Navigating to team page to verify login...")
            team_url = f"https://fantasy.espn.com/football/team?leagueId={credentials.get('league_id', '1922964857')}&teamId={credentials.get('team_id', '8')}&seasonId=2025"
            page.goto(team_url)
            time.sleep(3)
            
            # Save the session for future use
            save_session(context)
            
            print("Login complete and session saved!")
            print("You can now use other commands without logging in again.")

            return True

        except Exception as e:
            print(f"Login error: {e}")
            return False


def login_command(args):
    """Handle login command"""
    print("Logging in...")
    
    credentials = load_credentials()
    if not credentials:
        print("Could not load credentials. Please check .fantasy-football-manager/credentials file.")
        return
    
    if perform_login(credentials):
        print("Login successful!")
    else:
        print("Login failed!")
