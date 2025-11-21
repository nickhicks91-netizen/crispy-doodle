#!/usr/bin/env python3
"""
Troubleshooting tool for Google Docs Organizer
Diagnoses common setup issues and provides solutions
"""

import os
import sys
import json

def check_python():
    """Check Python version"""
    print("🐍 Python Version")
    version = sys.version_info
    print(f"   Version: {version.major}.{version.minor}.{version.micro}")

    if version.major >= 3 and version.minor >= 7:
        print("   ✅ Version OK")
        return True
    else:
        print("   ❌ Need Python 3.7 or higher")
        print("   → Download from: https://www.python.org/downloads/")
        return False

def check_files():
    """Check required files exist"""
    print("\n📁 Required Files")

    files = {
        'google_docs_organizer.py': 'Main script',
        'requirements.txt': 'Dependencies',
        'config.json.example': 'Config template'
    }

    all_exist = True
    for filename, description in files.items():
        exists = os.path.exists(filename)
        status = "✅" if exists else "❌"
        print(f"   {status} {filename} - {description}")
        if not exists:
            all_exist = False

    return all_exist

def check_credentials():
    """Check Google credentials"""
    print("\n🔑 Google Credentials")

    if not os.path.exists('credentials.json'):
        print("   ❌ credentials.json not found")
        print("\n   How to fix:")
        print("   1. Run: python easy_setup.py")
        print("   2. Or get manually from:")
        print("      https://console.cloud.google.com/")
        print("   3. Enable Google Drive API and Google Docs API")
        print("   4. Create OAuth Desktop credentials")
        print("   5. Download as credentials.json")
        return False

    print("   ✅ credentials.json found")

    # Try to validate it's valid JSON
    try:
        with open('credentials.json', 'r') as f:
            creds = json.load(f)

        if 'installed' in creds or 'web' in creds:
            print("   ✅ Format looks correct")
            return True
        else:
            print("   ⚠️  File format might be incorrect")
            print("   → Should contain 'installed' or 'web' key")
            return False

    except json.JSONDecodeError:
        print("   ❌ File is not valid JSON")
        print("   → Re-download from Google Cloud Console")
        return False
    except Exception as e:
        print(f"   ⚠️  Error reading file: {e}")
        return False

def check_config():
    """Check config.json"""
    print("\n⚙️  Configuration")

    if not os.path.exists('config.json'):
        print("   ❌ config.json not found")
        print("\n   How to fix:")
        print("   1. Run: python easy_setup.py")
        print("   2. Or manually: cp config.json.example config.json")
        print("   3. Edit config.json with your API key")
        return False

    print("   ✅ config.json found")

    try:
        with open('config.json', 'r') as f:
            config = json.load(f)

        # Check API key
        api_key = config.get('anthropic_api_key', '')
        if not api_key or api_key == 'YOUR_ANTHROPIC_API_KEY_HERE':
            print("   ❌ Anthropic API key not set")
            print("\n   How to fix:")
            print("   1. Get key from: https://console.anthropic.com/")
            print("   2. Edit config.json")
            print("   3. Replace YOUR_ANTHROPIC_API_KEY_HERE with your key")
            return False

        print("   ✅ API key configured")

        # Check other settings
        if config.get('dry_run', True):
            print("   ℹ️  Dry run mode: ON (safe - won't move files)")
        else:
            print("   ⚠️  Dry run mode: OFF (will actually move files)")

        max_docs = config.get('max_docs_to_process')
        if max_docs:
            print(f"   ℹ️  Will process max {max_docs} documents")
        else:
            print("   ℹ️  Will process all documents")

        return True

    except json.JSONDecodeError:
        print("   ❌ config.json is not valid JSON")
        print("   → Check for syntax errors")
        return False
    except Exception as e:
        print(f"   ⚠️  Error reading config: {e}")
        return False

def check_dependencies():
    """Check Python dependencies"""
    print("\n📦 Python Dependencies")

    required_packages = {
        'google.auth': 'google-auth',
        'google.oauth2': 'google-auth-oauthlib',
        'googleapiclient': 'google-api-python-client',
        'anthropic': 'anthropic'
    }

    missing = []
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"   ✅ {package_name}")
        except ImportError:
            print(f"   ❌ {package_name}")
            missing.append(package_name)

    if missing:
        print("\n   How to fix:")
        print("   Run: pip install -r requirements.txt")
        print("   Or: pip install " + " ".join(missing))
        return False

    return True

def check_token():
    """Check authentication token"""
    print("\n🎫 Authentication Token")

    if os.path.exists('token.pickle'):
        print("   ✅ token.pickle found (you're authenticated)")
        print("   ℹ️  If having auth issues, delete this file to re-authenticate")
    else:
        print("   ℹ️  No token.pickle (normal for first run)")
        print("   → Will authenticate when you first run the organizer")

    return True

def test_google_auth():
    """Test Google authentication"""
    print("\n🔐 Testing Google Authentication")

    try:
        from google_docs_organizer import GoogleDocsOrganizer
        organizer = GoogleDocsOrganizer()

        print("   Testing authentication...")
        if organizer.authenticate():
            print("   ✅ Google authentication successful!")
            return True
        else:
            print("   ❌ Authentication failed")
            return False

    except Exception as e:
        print(f"   ❌ Error: {e}")
        print("\n   Common causes:")
        print("   • credentials.json is invalid")
        print("   • APIs not enabled in Google Cloud")
        print("   • Network connection issues")
        return False

def test_claude():
    """Test Claude API"""
    print("\n🤖 Testing Claude API")

    try:
        import anthropic

        if not os.path.exists('config.json'):
            print("   ❌ config.json not found")
            return False

        with open('config.json', 'r') as f:
            config = json.load(f)

        api_key = config.get('anthropic_api_key', '')
        if not api_key or api_key == 'YOUR_ANTHROPIC_API_KEY_HERE':
            print("   ❌ API key not configured")
            return False

        client = anthropic.Anthropic(api_key=api_key)

        print("   Testing API connection...")
        # Test with a simple message
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )

        print("   ✅ Claude API working!")
        return True

    except anthropic.AuthenticationError:
        print("   ❌ Invalid API key")
        print("   → Check your API key in config.json")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def get_quick_fixes():
    """Show quick fixes for common issues"""
    print("\n" + "="*60)
    print("🔧 Quick Fixes")
    print("="*60)

    print("\n1. Start fresh with easy setup:")
    print("   python easy_setup.py")

    print("\n2. Re-install dependencies:")
    print("   pip install -r requirements.txt")

    print("\n3. Reset Google authentication:")
    print("   rm token.pickle")
    print("   python google_docs_organizer.py")

    print("\n4. Reset everything:")
    print("   rm token.pickle config.json")
    print("   python easy_setup.py")

    print("\n5. Get help:")
    print("   • Check QUICKSTART.md")
    print("   • Check README.md")
    print("   • Check SETUP_GUIDE.md")

def main():
    """Main troubleshooting routine"""
    print("="*60)
    print("🔍 Google Docs Organizer - Troubleshooter")
    print("="*60)
    print()

    # Run all checks
    checks = [
        check_python,
        check_files,
        check_dependencies,
        check_credentials,
        check_config,
        check_token,
    ]

    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Check failed with error: {e}")
            results.append(False)

    # Summary
    print("\n" + "="*60)
    print("📊 Summary")
    print("="*60)

    passed = sum(results)
    total = len(results)

    print(f"\nPassed: {passed}/{total} checks")

    if all(results):
        print("\n✅ Everything looks good!")
        print("\nReady to run:")
        print("   python google_docs_organizer.py")

        # Offer to test more
        response = input("\n🧪 Want to test authentication now? [Y/n]: ").strip().lower()
        if response != 'n':
            print()
            test_google_auth()
            print()
            test_claude()

    else:
        print("\n❌ Some issues found. See above for details.")
        get_quick_fixes()

    print("\n" + "="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted")
        sys.exit(1)
