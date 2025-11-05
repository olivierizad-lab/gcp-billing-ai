"""
Firestore service for managing query history.
"""

from datetime import datetime
from typing import List, Dict, Optional
from google.cloud import firestore
import os

# Initialize Firestore client
PROJECT_ID = os.getenv("BQ_PROJECT") or os.getenv("GCP_PROJECT_ID", "qwiklabs-asl-04-8e9f23e85ced")
try:
    db = firestore.Client(project=PROJECT_ID)
except Exception as e:
    print(f"Warning: Failed to initialize Firestore client: {e}")
    db = None

# Collection name
COLLECTION_NAME = "query_history"


def save_query(user_id: str, agent_name: str, message: str, response: str) -> str:
    """
    Save a query and response to Firestore.
    
    Args:
        user_id: User ID
        agent_name: Name of the agent used
        message: User's query message
        response: Agent's response
    
    Returns:
        Document ID of the saved query
    """
    if db is None:
        raise Exception("Firestore client not initialized - check Firestore API is enabled")
    
    try:
        doc_ref = db.collection(COLLECTION_NAME).document()
        
        doc_data = {
            "user_id": user_id,
            "agent_name": agent_name,
            "message": message,
            "response": response,
            "timestamp": firestore.SERVER_TIMESTAMP,
        }
        
        print(f"Writing to Firestore collection '{COLLECTION_NAME}': {doc_data.keys()}")
        doc_ref.set(doc_data)
        
        query_id = doc_ref.id
        print(f"Successfully saved query with document ID: {query_id}")
        return query_id
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in save_query: {e}")
        print(f"Traceback: {error_details}")
        raise


def get_query_history(user_id: str, limit: int = 50) -> List[Dict]:
    """
    Get query history for a user.
    
    IMPORTANT: Only returns history for the specified user_id.
    This function enforces user isolation - users can only see their own history.
    
    Args:
        user_id: User ID (must be sanitized before calling)
        limit: Maximum number of queries to return
    
    Returns:
        List of query documents (only for the specified user_id)
    """
    if db is None:
        print("Warning: Firestore client not initialized, returning empty history")
        return []
    
    # Double-check user_id is valid (defense in depth)
    if not user_id or not isinstance(user_id, str):
        print(f"Warning: Invalid user_id provided: {user_id}")
        return []
    
    try:
        # Try to get queries with ordering
        # Note: Firestore requires a composite index for where + order_by
        # If index doesn't exist, we'll catch the error during iteration and try without order_by
        queries_with_order = (
            db.collection(COLLECTION_NAME)
            .where("user_id", "==", user_id)
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )
        
        result = []
        needs_index = False
        
        try:
            # Try to iterate - this is where the index error will occur
            for doc in queries_with_order.stream():
                try:
                    data = doc.to_dict()
                    data["id"] = doc.id
                    # Convert timestamp to ISO string for JSON serialization
                    if "timestamp" in data and data["timestamp"]:
                        timestamp = data["timestamp"]
                        # Handle Firestore Timestamp objects
                        if hasattr(timestamp, "isoformat"):
                            data["timestamp"] = timestamp.isoformat()
                        elif hasattr(timestamp, "timestamp"):
                            # Firestore Timestamp has .timestamp() method
                            from datetime import datetime, timezone
                            dt = datetime.fromtimestamp(timestamp.timestamp(), tz=timezone.utc)
                            data["timestamp"] = dt.isoformat()
                        elif isinstance(timestamp, datetime):
                            data["timestamp"] = timestamp.isoformat()
                    result.append(data)
                except Exception as item_error:
                    print(f"Warning: Error processing document {doc.id}: {item_error}")
                    continue
        except Exception as e:
            # Check if it's an index error
            error_str = str(e)
            if "requires an index" in error_str or "FailedPrecondition" in error_str:
                needs_index = True
                print(f"Warning: Index required for ordered query. Using fallback query without order_by.")
                print(f"To fix permanently, create the index: {error_str.split('here: ')[-1] if 'here: ' in error_str else 'see error above'}")
                # Fall back to query without order_by
                queries_no_order = (
                    db.collection(COLLECTION_NAME)
                    .where("user_id", "==", user_id)
                    .limit(limit * 2)  # Get more to account for unsorted
                )
                for doc in queries_no_order.stream():
                    try:
                        data = doc.to_dict()
                        data["id"] = doc.id
                        # Convert timestamp to ISO string for JSON serialization
                        if "timestamp" in data and data["timestamp"]:
                            timestamp = data["timestamp"]
                            # Handle Firestore Timestamp objects
                            if hasattr(timestamp, "isoformat"):
                                data["timestamp"] = timestamp.isoformat()
                            elif hasattr(timestamp, "timestamp"):
                                # Firestore Timestamp has .timestamp() method
                                from datetime import datetime, timezone
                                dt = datetime.fromtimestamp(timestamp.timestamp(), tz=timezone.utc)
                                data["timestamp"] = dt.isoformat()
                            elif isinstance(timestamp, datetime):
                                data["timestamp"] = timestamp.isoformat()
                        result.append(data)
                    except Exception as item_error:
                        print(f"Warning: Error processing document {doc.id}: {item_error}")
                        continue
            else:
                # Re-raise if it's a different error
                raise
        
        # If we didn't use order_by, sort in Python
        if needs_index and result and len(result) > 0 and "timestamp" in result[0]:
            try:
                result.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            except:
                pass  # If sorting fails, just return unsorted
        
        return result[:limit]  # Limit after sorting if we got more
        
    except Exception as e:
        print(f"Error getting query history: {e}")
        import traceback
        traceback.print_exc()
        # Return empty list on error rather than crashing
        return []


def delete_query(query_id: str, user_id: str) -> bool:
    """
    Delete a query by ID (only if it belongs to the user).
    
    Args:
        query_id: Document ID
        user_id: User ID (for verification)
    
    Returns:
        True if deleted, False if not found or doesn't belong to user
    """
    if db is None:
        return False
    
    doc_ref = db.collection(COLLECTION_NAME).document(query_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        return False
    
    data = doc.to_dict()
    if data.get("user_id") != user_id:
        return False
    
    doc_ref.delete()
    return True


def delete_all_history(user_id: str) -> int:
    """
    Delete all query history for a user.
    
    IMPORTANT: Only deletes history for the specified user_id.
    This enforces user isolation - users can only delete their own history.
    
    Args:
        user_id: User ID (must be sanitized before calling)
    
    Returns:
        Number of queries deleted (only for the specified user_id)
    """
    if db is None:
        return 0
    
    # Double-check user_id is valid (defense in depth)
    if not user_id or not isinstance(user_id, str):
        print(f"Warning: Invalid user_id provided: {user_id}")
        return 0
    
    queries = (
        db.collection(COLLECTION_NAME)
        .where("user_id", "==", user_id)
        .stream()
    )
    
    count = 0
    for doc in queries:
        doc.reference.delete()
        count += 1
    
    return count

