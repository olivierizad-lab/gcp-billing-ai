#!/usr/bin/env python3
"""
Script to clean up query history from Firestore.

This script can:
- Delete all history for a specific user
- Delete all history in the collection (use with caution!)
- List history statistics
"""

import os
import sys
from google.cloud import firestore
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file, override=False)

PROJECT_ID = os.getenv("BQ_PROJECT") or os.getenv("GCP_PROJECT_ID", "qwiklabs-asl-04-8e9f23e85ced")
COLLECTION_NAME = "query_history"

def get_firestore_client(project_id=None):
    """Initialize Firestore client."""
    project = project_id or PROJECT_ID
    try:
        return firestore.Client(project=project)
    except Exception as e:
        print(f"Error initializing Firestore client: {e}")
        sys.exit(1)

def list_history_stats(db):
    """List statistics about query history."""
    print(f"\n📊 Query History Statistics")
    print(f"{'='*60}")
    
    try:
        # Get all documents
        docs = db.collection(COLLECTION_NAME).stream()
        
        total_count = 0
        user_counts = {}
        
        for doc in docs:
            total_count += 1
            data = doc.to_dict()
            user_id = data.get("user_id", "unknown")
            user_counts[user_id] = user_counts.get(user_id, 0) + 1
        
        print(f"Total queries: {total_count}")
        print(f"Unique users: {len(user_counts)}")
        print(f"\nQueries per user:")
        for user_id, count in sorted(user_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {user_id}: {count} queries")
        
        return total_count, user_counts
    except Exception as e:
        print(f"Error listing history: {e}")
        return 0, {}

def delete_user_history(db, user_id):
    """Delete all history for a specific user."""
    print(f"\n🗑️  Deleting history for user: {user_id}")
    print(f"{'='*60}")
    
    try:
        queries = (
            db.collection(COLLECTION_NAME)
            .where("user_id", "==", user_id)
            .stream()
        )
        
        count = 0
        for doc in queries:
            doc.reference.delete()
            count += 1
        
        print(f"✅ Deleted {count} queries for user {user_id}")
        return count
    except Exception as e:
        print(f"❌ Error deleting user history: {e}")
        return 0

def delete_all_history(db):
    """Delete ALL history from the collection (use with caution!)."""
    print(f"\n⚠️  WARNING: Deleting ALL query history!")
    print(f"{'='*60}")
    
    try:
        docs = db.collection(COLLECTION_NAME).stream()
        
        count = 0
        batch = db.batch()
        batch_count = 0
        
        for doc in docs:
            batch.delete(doc.reference)
            batch_count += 1
            count += 1
            
            # Firestore batches are limited to 500 operations
            if batch_count >= 500:
                batch.commit()
                print(f"  Deleted batch of {batch_count} documents...")
                batch = db.batch()
                batch_count = 0
        
        # Commit remaining batch
        if batch_count > 0:
            batch.commit()
            print(f"  Deleted final batch of {batch_count} documents...")
        
        print(f"✅ Deleted {count} total queries")
        return count
    except Exception as e:
        print(f"❌ Error deleting all history: {e}")
        return 0

def main():
    """Main function."""
    import argparse
    
    # Use module-level PROJECT_ID as default
    default_project_id = PROJECT_ID
    
    parser = argparse.ArgumentParser(description="Clean up query history from Firestore")
    parser.add_argument(
        "--list",
        action="store_true",
        help="List history statistics"
    )
    parser.add_argument(
        "--user",
        type=str,
        help="Delete history for a specific user_id"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Delete ALL history (use with caution!)"
    )
    parser.add_argument(
        "--project-id",
        type=str,
        default=default_project_id,
        help=f"GCP Project ID (default: {default_project_id})"
    )
    
    args = parser.parse_args()
    
    # Use the project ID from args (or default)
    project_id = args.project_id or default_project_id
    
    print(f"🔧 Query History Cleanup Tool")
    print(f"{'='*60}")
    print(f"Project ID: {project_id}")
    print(f"Collection: {COLLECTION_NAME}")
    
    # Initialize Firestore client with the specified project
    db = get_firestore_client(project_id=project_id)
    
    if args.list:
        list_history_stats(db)
    elif args.user:
        # Confirm deletion
        print(f"\n⚠️  This will delete all history for user: {args.user}")
        confirm = input("Are you sure? (yes/no): ")
        if confirm.lower() == "yes":
            delete_user_history(db, args.user)
        else:
            print("Cancelled.")
    elif args.all:
        # Double confirmation for deleting all
        print(f"\n⚠️  WARNING: This will delete ALL query history for ALL users!")
        confirm1 = input("Type 'DELETE ALL' to confirm: ")
        if confirm1 == "DELETE ALL":
            confirm2 = input("Are you absolutely sure? (yes/no): ")
            if confirm2.lower() == "yes":
                delete_all_history(db)
            else:
                print("Cancelled.")
        else:
            print("Cancelled.")
    else:
        # Default: show stats
        list_history_stats(db)
        print("\n💡 Usage:")
        print("  --list              List history statistics")
        print("  --user USER_ID      Delete history for specific user")
        print("  --all               Delete ALL history (use with caution!)")

if __name__ == "__main__":
    main()

