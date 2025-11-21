#!/usr/bin/env python3
"""
Helper script to set up Google OAuth authentication
"""

import os
import sys

def check_credentials():
    """Check if credentials.json exists"""
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found!")
        print("\nTo get credentials.json:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a project or select existing")
        print("3. Enable Google Drive API and Google Docs API")
        print("4. Create OAuth 2.0 Desktop credentials")
        print("5. Download as credentials.json")
        print("\nSee SETUP_GUIDE.md for detailed instructions.")
        return False
    print("✅ credentials.json found")
    return True

def check_config():
    """Check if config.json is set up"""
    if not os.path.exists('config.json'):
        print("❌ config.json not found!")
        print("\nRun: cp config.json.example config.json")
        print("Then edit config.json with your Anthropic API key")
        return False

    import json
    with open('config.json', 'r') as f:
        config = json.load(f)

    api_key = config.get('anthropic_api_key', '')
    if not api_key or api_key == 'YOUR_ANTHROPIC_API_KEY_HERE':
        print("❌ Anthropic API key not configured in config.json")
        print("\nGet your API key from: https://console.anthropic.com/")
        print("Then update the 'anthropic_api_key' field in config.json")
        return False

    print("✅ config.json configured")
    return True

def test_authentication():
    """Test Google authentication"""
    print("\n🔐 Testing Google authentication...")

    try:
        from google_docs_organizer import GoogleDocsOrganizer

        organizer = GoogleDocsOrganizer()
        if organizer.authenticate():
            print("✅ Google authentication successful!")
            return True
        else:
            print("❌ Google authentication failed")
            return False

    except Exception as e:
        print(f"❌ Error during authentication: {e}")
        return False

def main():
    """Main setup validation"""
    print("="*60)
    print("Google Docs Organizer - Setup Validator")
    print("="*60)

    all_good = True

    # Check credentials
    print("\n1. Checking Google credentials...")
    if not check_credentials():
        all_good = False

    # Check config
    print("\n2. Checking configuration...")
    if not check_config():
        all_good = False

    # If basics are good, test auth
    if all_good:
        print("\n3. Testing authentication...")
        if not test_authentication():
            all_good = False

    # Summary
    print("\n" + "="*60)
    if all_good:
        print("✅ Setup complete! You're ready to organize your docs.")
        print("\nRun: python google_docs_organizer.py")
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
        print("\nSee SETUP_GUIDE.md for detailed instructions.")
    print("="*60)

    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())
