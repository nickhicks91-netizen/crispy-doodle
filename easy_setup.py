#!/usr/bin/env python3
"""
Interactive Setup Wizard for Google Docs Organizer
Makes setup easy with step-by-step guidance
"""

import os
import sys
import json
import webbrowser
from pathlib import Path

class Colors:
    """Terminal colors for better readability"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print a styled header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def print_step(number, text):
    """Print step number"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}Step {number}: {text}{Colors.END}")

def prompt_yes_no(question, default=True):
    """Ask a yes/no question"""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{Colors.CYAN}? {question} [{default_str}]: {Colors.END}").strip().lower()

    if not response:
        return default
    return response in ['y', 'yes']

def prompt_input(question, default=None):
    """Ask for text input"""
    if default:
        response = input(f"{Colors.CYAN}? {question} [{default}]: {Colors.END}").strip()
        return response if response else default
    else:
        response = input(f"{Colors.CYAN}? {question}: {Colors.END}").strip()
        return response

def check_python_version():
    """Check Python version"""
    print_step(1, "Checking Python Version")

    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} - Good to go!")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor} detected. Need Python 3.7+")
        return False

def install_dependencies():
    """Install required Python packages"""
    print_step(2, "Installing Dependencies")

    if not os.path.exists('requirements.txt'):
        print_error("requirements.txt not found!")
        return False

    print_info("Installing Python packages...")
    print("This may take a minute...\n")

    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print_success("All dependencies installed!")
            return True
        else:
            print_error("Failed to install dependencies")
            print(result.stderr)
            return False
    except Exception as e:
        print_error(f"Installation error: {e}")
        return False

def setup_google_credentials():
    """Guide user through Google credentials setup"""
    print_step(3, "Google Cloud Credentials")

    if os.path.exists('credentials.json'):
        print_success("credentials.json already exists!")
        if not prompt_yes_no("Want to replace it?", default=False):
            return True

    print_info("You need to create Google Cloud credentials.")
    print("\nI'll walk you through it:\n")

    print("1. I'll open Google Cloud Console in your browser")
    print("2. Create a new project (or select existing)")
    print("3. Enable Google Drive API")
    print("4. Enable Google Docs API")
    print("5. Create OAuth credentials (Desktop app)")
    print("6. Download the credentials.json file")
    print("7. Move it to this directory")

    if not prompt_yes_no("\nReady to open Google Cloud Console?", default=True):
        print_info("You can do this later. Run this script again when ready.")
        return False

    # Open Google Cloud Console
    webbrowser.open('https://console.cloud.google.com/apis/dashboard')

    print_info("\n📱 Your browser should open to Google Cloud Console")
    print("\nDetailed steps:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("1. Click 'Select Project' → 'New Project'")
    print("   - Name it 'docs-organizer' or whatever you like")
    print("   - Click 'Create'\n")

    print("2. In the sidebar, go to 'APIs & Services' → 'Library'")
    print("   - Search for 'Google Drive API' → Click it → Enable")
    print("   - Search for 'Google Docs API' → Click it → Enable\n")

    print("3. In the sidebar, go to 'APIs & Services' → 'Credentials'")
    print("   - Click 'Configure Consent Screen' (if needed)")
    print("     • User Type: External")
    print("     • App name: Google Docs Organizer")
    print("     • Your email for support and developer contact")
    print("     • Save and Continue (skip scopes)")
    print("     • Add yourself as a test user")
    print("     • Save and Continue\n")

    print("4. Still in Credentials page:")
    print("   - Click 'Create Credentials' → 'OAuth client ID'")
    print("   - Application type: 'Desktop app'")
    print("   - Name: 'Docs Organizer'")
    print("   - Click 'Create'\n")

    print("5. Download the JSON file")
    print("   - Click the download button (↓)")
    print("   - Save it in this directory as 'credentials.json'")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Wait for user to download
    input(f"\n{Colors.YELLOW}Press Enter once you've saved credentials.json...{Colors.END}")

    # Check if file exists
    if os.path.exists('credentials.json'):
        print_success("Found credentials.json!")
        return True
    else:
        print_error("credentials.json not found in this directory")
        print_info("Make sure you saved it as 'credentials.json' (not 'client_secret_xxx.json')")
        return False

def setup_anthropic_key():
    """Set up Anthropic API key"""
    print_step(4, "Anthropic API Key")

    # Check existing config
    config = {}
    config_exists = os.path.exists('config.json')

    if config_exists:
        with open('config.json', 'r') as f:
            config = json.load(f)

        existing_key = config.get('anthropic_api_key', '')
        if existing_key and existing_key != 'YOUR_ANTHROPIC_API_KEY_HERE':
            print_success("API key already configured!")
            if not prompt_yes_no("Want to update it?", default=False):
                return True

    print_info("You need an Anthropic API key to use Claude AI.")

    if prompt_yes_no("\nOpen Anthropic Console to get your API key?", default=True):
        webbrowser.open('https://console.anthropic.com/settings/keys')
        print_info("📱 Browser opened to Anthropic Console")
        print("\nSteps:")
        print("1. Sign up or log in")
        print("2. Go to 'API Keys' section")
        print("3. Click 'Create Key'")
        print("4. Copy the key (starts with 'sk-ant-api03-')")

    print()
    api_key = prompt_input("Paste your Anthropic API key")

    if not api_key or api_key == 'YOUR_ANTHROPIC_API_KEY_HERE':
        print_error("Invalid API key")
        return False

    # Create or update config
    if not config_exists:
        if os.path.exists('config.json.example'):
            with open('config.json.example', 'r') as f:
                config = json.load(f)
        else:
            config = {
                "credentials_file": "credentials.json",
                "token_file": "token.pickle",
                "create_organized_folder": True,
                "organized_folder_name": "Organized Docs",
                "dry_run": True,
                "max_docs_to_process": None,
                "categories": {
                    "default": [
                        "Work", "Personal", "Finance", "Health",
                        "Education", "Projects", "Notes", "Miscellaneous"
                    ],
                    "custom": []
                }
            }

    config['anthropic_api_key'] = api_key

    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)

    print_success("API key saved to config.json!")
    return True

def configure_preferences():
    """Configure user preferences"""
    print_step(5, "Configure Preferences")

    with open('config.json', 'r') as f:
        config = json.load(f)

    print_info("Let's set up your preferences...\n")

    # Organized folder name
    folder_name = prompt_input(
        "What should the organized folder be called?",
        default=config.get('organized_folder_name', 'Organized Docs')
    )
    config['organized_folder_name'] = folder_name

    # Max docs to process
    print()
    if prompt_yes_no("Want to limit how many docs to process? (Good for testing)", default=True):
        max_docs = prompt_input("How many docs to process?", default="10")
        try:
            config['max_docs_to_process'] = int(max_docs)
        except:
            config['max_docs_to_process'] = 10
    else:
        config['max_docs_to_process'] = None

    # Categories
    print()
    print_info("Default categories:")
    for cat in config['categories']['default']:
        print(f"  • {cat}")

    if prompt_yes_no("\nWant to add custom categories?", default=False):
        print_info("Enter categories one per line. Press Enter twice when done.")
        custom_cats = []
        while True:
            cat = prompt_input("Category name (or press Enter to finish)")
            if not cat:
                break
            custom_cats.append(cat)

        if custom_cats:
            config['categories']['custom'] = custom_cats
            print_success(f"Added {len(custom_cats)} custom categories!")

    # Always start with dry run enabled for safety
    config['dry_run'] = True

    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)

    print_success("Preferences saved!")
    return True

def test_setup():
    """Test the complete setup"""
    print_step(6, "Testing Setup")

    print_info("Running setup validation...\n")

    all_good = True

    # Check credentials
    if os.path.exists('credentials.json'):
        print_success("credentials.json: Found")
    else:
        print_error("credentials.json: Missing")
        all_good = False

    # Check config
    if os.path.exists('config.json'):
        print_success("config.json: Found")

        with open('config.json', 'r') as f:
            config = json.load(f)

        api_key = config.get('anthropic_api_key', '')
        if api_key and api_key != 'YOUR_ANTHROPIC_API_KEY_HERE':
            print_success("API key: Configured")
        else:
            print_error("API key: Not configured")
            all_good = False
    else:
        print_error("config.json: Missing")
        all_good = False

    # Test imports
    print()
    print_info("Testing Python packages...")
    try:
        import google.auth
        import google.oauth2
        import googleapiclient.discovery
        import anthropic
        print_success("All packages installed correctly")
    except ImportError as e:
        print_error(f"Missing package: {e}")
        all_good = False

    return all_good

def run_test_mode():
    """Run the organizer in test mode"""
    print_step(7, "Test Run")

    print_info("Let's do a test run (dry run mode - no changes will be made)")

    if not prompt_yes_no("\nReady to test?", default=True):
        print_info("You can test later by running: python google_docs_organizer.py")
        return True

    print()
    print_info("Starting organizer...")
    print_info("You'll need to authorize Google access in your browser\n")
    print("━"*60)

    try:
        from google_docs_organizer import GoogleDocsOrganizer

        organizer = GoogleDocsOrganizer()
        organizer.organize_documents()

        print("━"*60)
        print_success("\nTest run completed!")
        return True

    except Exception as e:
        print("━"*60)
        print_error(f"\nError during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main setup wizard"""
    print_header("🚀 Google Docs Organizer - Easy Setup Wizard")

    print("This wizard will guide you through the entire setup process.\n")
    print_info("You'll need:")
    print("  • A Google account with Google Docs")
    print("  • An Anthropic API key (for Claude AI)")
    print("  • About 10 minutes\n")

    if not prompt_yes_no("Ready to start?", default=True):
        print_info("Come back when you're ready! Run: python easy_setup.py")
        return 1

    # Run setup steps
    steps = [
        (check_python_version, "Python version check"),
        (install_dependencies, "Installing dependencies"),
        (setup_google_credentials, "Google credentials setup"),
        (setup_anthropic_key, "Anthropic API key setup"),
        (configure_preferences, "Configuring preferences"),
        (test_setup, "Testing setup"),
    ]

    for step_func, step_name in steps:
        try:
            if not step_func():
                print_error(f"\n{step_name} failed!")
                print_warning("Fix the issue and run this script again.")
                return 1
        except KeyboardInterrupt:
            print_warning("\n\nSetup interrupted. Run again to continue.")
            return 1
        except Exception as e:
            print_error(f"\nUnexpected error in {step_name}: {e}")
            return 1

    # Success!
    print_header("✅ Setup Complete!")

    print_success("Everything is configured and ready to go!\n")

    # Offer to run test
    if prompt_yes_no("Want to run a test now?", default=True):
        run_test_mode()

    print_header("📚 Next Steps")
    print(f"{Colors.BOLD}To organize your docs:{Colors.END}")
    print(f"  1. Review the dry run results")
    print(f"  2. When ready, edit config.json and set 'dry_run': false")
    print(f"  3. Run: python google_docs_organizer.py\n")

    print(f"{Colors.BOLD}Need help?{Colors.END}")
    print(f"  • Check README.md for full documentation")
    print(f"  • Re-run this wizard: python easy_setup.py\n")

    print_success("Happy organizing! 🎉")

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  Setup cancelled{Colors.END}")
        sys.exit(1)
