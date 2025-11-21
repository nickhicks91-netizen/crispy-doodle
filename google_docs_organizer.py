#!/usr/bin/env python3
"""
Google Docs AI Organizer Agent
Automatically organizes Google Docs into labeled folders based on content analysis
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import anthropic


# Google Drive API scopes
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents.readonly'
]

class GoogleDocsOrganizer:
    """AI-powered Google Docs organizer"""

    def __init__(self, config_path: str = "config.json"):
        """Initialize the organizer with configuration"""
        self.config = self._load_config(config_path)
        self.creds = None
        self.drive_service = None
        self.docs_service = None
        self.claude_client = None

        # Statistics
        self.stats = {
            'analyzed': 0,
            'organized': 0,
            'folders_created': 0,
            'errors': 0
        }

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file"""
        if not os.path.exists(config_path):
            print(f"⚠️  Config file not found at {config_path}")
            print("Creating default config template...")
            default_config = {
                "anthropic_api_key": "YOUR_ANTHROPIC_API_KEY_HERE",
                "credentials_file": "credentials.json",
                "token_file": "token.pickle",
                "organize_root_folder": "My Drive",
                "create_organized_folder": True,
                "organized_folder_name": "Organized Docs",
                "dry_run": False,
                "max_docs_to_process": None,
                "categories": {
                    "default": [
                        "Work",
                        "Personal",
                        "Finance",
                        "Health",
                        "Education",
                        "Projects",
                        "Notes",
                        "Miscellaneous"
                    ],
                    "custom": []
                }
            }
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            print(f"✅ Created template config at {config_path}")
            print("Please update it with your API key and preferences.")
            return default_config

        with open(config_path, 'r') as f:
            return json.load(f)

    def authenticate(self) -> bool:
        """Authenticate with Google Drive and Docs APIs"""
        print("🔐 Authenticating with Google...")

        # Check for existing token
        token_file = self.config.get('token_file', 'token.pickle')
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                self.creds = pickle.load(token)

        # Refresh or get new credentials
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                print("Refreshing access token...")
                self.creds.refresh(Request())
            else:
                credentials_file = self.config.get('credentials_file', 'credentials.json')
                if not os.path.exists(credentials_file):
                    print(f"❌ Credentials file not found: {credentials_file}")
                    print("\nTo set up Google Drive API access:")
                    print("1. Go to https://console.cloud.google.com/")
                    print("2. Create a new project or select existing")
                    print("3. Enable Google Drive API and Google Docs API")
                    print("4. Create OAuth 2.0 credentials (Desktop app)")
                    print("5. Download credentials.json to this directory")
                    return False

                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file, SCOPES)
                self.creds = flow.run_local_server(port=0)

            # Save credentials for future use
            with open(token_file, 'wb') as token:
                pickle.dump(self.creds, token)

        # Build service objects
        try:
            self.drive_service = build('drive', 'v3', credentials=self.creds)
            self.docs_service = build('docs', 'v1', credentials=self.creds)
            print("✅ Successfully authenticated with Google")
            return True
        except Exception as e:
            print(f"❌ Error building service: {e}")
            return False

    def initialize_claude(self) -> bool:
        """Initialize Claude API client"""
        api_key = self.config.get('anthropic_api_key')
        if not api_key or api_key == "YOUR_ANTHROPIC_API_KEY_HERE":
            print("❌ Anthropic API key not configured")
            print("Please update config.json with your API key")
            return False

        try:
            self.claude_client = anthropic.Anthropic(api_key=api_key)
            print("✅ Claude API initialized")
            return True
        except Exception as e:
            print(f"❌ Error initializing Claude: {e}")
            return False

    def get_all_docs(self) -> List[Dict]:
        """Retrieve all Google Docs from the user's Drive"""
        print("\n📄 Fetching Google Docs...")

        docs = []
        page_token = None

        try:
            while True:
                query = "mimeType='application/vnd.google-apps.document'"
                response = self.drive_service.files().list(
                    q=query,
                    spaces='drive',
                    fields='nextPageToken, files(id, name, parents, createdTime, modifiedTime)',
                    pageToken=page_token,
                    pageSize=100
                ).execute()

                docs.extend(response.get('files', []))
                page_token = response.get('nextPageToken', None)

                if page_token is None:
                    break

            print(f"✅ Found {len(docs)} Google Docs")

            # Limit if specified
            max_docs = self.config.get('max_docs_to_process')
            if max_docs and len(docs) > max_docs:
                print(f"⚠️  Limiting to {max_docs} docs (configured limit)")
                docs = docs[:max_docs]

            return docs

        except HttpError as error:
            print(f"❌ Error fetching docs: {error}")
            return []

    def get_document_content(self, doc_id: str) -> Optional[str]:
        """Get the text content of a Google Doc"""
        try:
            document = self.docs_service.documents().get(documentId=doc_id).execute()

            # Extract text content
            content = []
            for element in document.get('body', {}).get('content', []):
                if 'paragraph' in element:
                    for text_run in element['paragraph'].get('elements', []):
                        if 'textRun' in text_run:
                            content.append(text_run['textRun']['content'])

            full_text = ''.join(content)
            # Limit to first 5000 characters for analysis
            return full_text[:5000] if full_text else None

        except HttpError as error:
            print(f"  ⚠️  Error reading document: {error}")
            return None

    def categorize_document(self, doc_name: str, content: str) -> str:
        """Use Claude to categorize the document"""
        available_categories = (
            self.config['categories']['custom'] or
            self.config['categories']['default']
        )

        prompt = f"""Analyze this document and categorize it into ONE of the following categories:

{', '.join(available_categories)}

Document Title: {doc_name}
Document Content (excerpt):
{content[:2000]}

Based on the title and content, which single category best fits this document?
Respond with ONLY the category name, nothing else."""

        try:
            message = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=50,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            category = message.content[0].text.strip()

            # Validate category
            if category in available_categories:
                return category
            else:
                # Try to find closest match
                category_lower = category.lower()
                for cat in available_categories:
                    if cat.lower() in category_lower or category_lower in cat.lower():
                        return cat

                # Default fallback
                return "Miscellaneous"

        except Exception as e:
            print(f"  ⚠️  Error categorizing: {e}")
            return "Miscellaneous"

    def create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Create a folder in Google Drive"""
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        if parent_id:
            file_metadata['parents'] = [parent_id]

        try:
            folder = self.drive_service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()

            print(f"  ✅ Created folder: {folder_name}")
            self.stats['folders_created'] += 1
            return folder.get('id')

        except HttpError as error:
            print(f"  ❌ Error creating folder: {error}")
            return None

    def get_or_create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Get existing folder or create if it doesn't exist"""
        # Search for existing folder
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"

        try:
            response = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            folders = response.get('files', [])

            if folders:
                return folders[0]['id']
            else:
                return self.create_folder(folder_name, parent_id)

        except HttpError as error:
            print(f"  ❌ Error searching for folder: {error}")
            return None

    def move_file_to_folder(self, file_id: str, folder_id: str, current_parents: List[str]) -> bool:
        """Move a file to a specific folder"""
        try:
            # Remove from current parents and add to new folder
            previous_parents = ','.join(current_parents) if current_parents else None

            self.drive_service.files().update(
                fileId=file_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()

            return True

        except HttpError as error:
            print(f"  ❌ Error moving file: {error}")
            return False

    def organize_documents(self):
        """Main orchestration method to organize all documents"""
        print("\n" + "="*60)
        print("🤖 Google Docs AI Organizer Agent")
        print("="*60)

        # Authenticate
        if not self.authenticate():
            return

        if not self.initialize_claude():
            return

        # Get all docs
        docs = self.get_all_docs()
        if not docs:
            print("No documents found to organize.")
            return

        # Setup organized folder
        organized_folder_id = None
        if self.config.get('create_organized_folder', True):
            folder_name = self.config.get('organized_folder_name', 'Organized Docs')
            print(f"\n📁 Setting up '{folder_name}' folder...")
            organized_folder_id = self.get_or_create_folder(folder_name)
            if not organized_folder_id:
                print("❌ Failed to create organized folder")
                return

        # Track category folders
        category_folders = {}

        # Process each document
        print(f"\n🔄 Processing {len(docs)} documents...")
        print("-" * 60)

        dry_run = self.config.get('dry_run', False)
        if dry_run:
            print("⚠️  DRY RUN MODE - No changes will be made\n")

        for idx, doc in enumerate(docs, 1):
            doc_name = doc['name']
            doc_id = doc['id']

            print(f"\n[{idx}/{len(docs)}] {doc_name}")

            # Get content
            content = self.get_document_content(doc_id)
            if not content:
                print("  ⚠️  Skipping - no content")
                self.stats['errors'] += 1
                continue

            # Categorize
            print("  🤔 Analyzing content...")
            category = self.categorize_document(doc_name, content)
            print(f"  📂 Category: {category}")

            self.stats['analyzed'] += 1

            # Get or create category folder
            if category not in category_folders:
                if not dry_run:
                    category_folder_id = self.get_or_create_folder(
                        category,
                        organized_folder_id
                    )
                    if category_folder_id:
                        category_folders[category] = category_folder_id
                    else:
                        print(f"  ❌ Failed to create folder for {category}")
                        self.stats['errors'] += 1
                        continue
                else:
                    print(f"  [DRY RUN] Would create/use folder: {category}")
                    category_folders[category] = "dry_run_folder_id"

            # Move document
            if not dry_run:
                if self.move_file_to_folder(
                    doc_id,
                    category_folders[category],
                    doc.get('parents', [])
                ):
                    print(f"  ✅ Moved to {category}")
                    self.stats['organized'] += 1
                else:
                    print(f"  ❌ Failed to move")
                    self.stats['errors'] += 1
            else:
                print(f"  [DRY RUN] Would move to {category}")
                self.stats['organized'] += 1

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print organization summary"""
        print("\n" + "="*60)
        print("📊 Organization Summary")
        print("="*60)
        print(f"Documents analyzed: {self.stats['analyzed']}")
        print(f"Documents organized: {self.stats['organized']}")
        print(f"Folders created: {self.stats['folders_created']}")
        print(f"Errors: {self.stats['errors']}")
        print("="*60)

        if self.config.get('dry_run', False):
            print("\n⚠️  This was a DRY RUN - no actual changes were made")
            print("Set 'dry_run': false in config.json to organize for real")


def main():
    """Main entry point"""
    print("\n🚀 Starting Google Docs Organizer Agent...\n")

    organizer = GoogleDocsOrganizer()

    try:
        organizer.organize_documents()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        organizer.print_summary()
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
