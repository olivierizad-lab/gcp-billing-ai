"""
Custom authentication using Firestore for user storage.
No Firebase Authentication required - just Firestore!
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from google.cloud import firestore
import secrets

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Required email domain
REQUIRED_DOMAIN = "asl.apps-eval.com"

# Initialize Firestore
PROJECT_ID = os.getenv("BQ_PROJECT") or os.getenv("GCP_PROJECT_ID", "qwiklabs-asl-04-8e9f23e85ced")
try:
    db = firestore.Client(project=PROJECT_ID)
except Exception as e:
    print(f"Warning: Failed to initialize Firestore client: {e}")
    db = None

USERS_COLLECTION = "users"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    # Bcrypt has a 72-byte limit
    # Convert to bytes to check actual byte length (not character length)
    password_bytes = password.encode('utf-8')
    
    # If password exceeds 72 bytes, we need to handle it
    # For security, we'll reject passwords over 72 bytes rather than truncate
    if len(password_bytes) > 72:
        raise ValueError(f"Password is too long. Maximum is 72 bytes (your password is {len(password_bytes)} bytes). Please use a shorter password.")
    
    # Passlib will handle the hashing
    try:
        return pwd_context.hash(password)
    except ValueError as e:
        # If passlib still complains, provide a better error
        if "72 bytes" in str(e).lower():
            raise ValueError("Password is too long. Maximum is 72 bytes. Please use a shorter password.")
        raise


def validate_email_domain(email: str) -> bool:
    """Validate that email is from the required domain."""
    if not email or "@" not in email:
        return False
    domain = email.split("@")[1]
    return domain == REQUIRED_DOMAIN


def create_user(email: str, password: str) -> Dict:
    """
    Create a new user in Firestore.
    
    Returns:
        User document dict with user_id, email, created_at
    """
    if db is None:
        raise Exception("Firestore client not initialized")
    
    # Validate email domain
    if not validate_email_domain(email):
        raise ValueError("Please use your ASL class account email address")
    
    # Validate password length (bcrypt limit is 72 bytes)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        raise ValueError("Password is too long. Maximum length is 72 bytes (approximately 72 ASCII characters)")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters long")
    
    # Check if user already exists
    users_ref = db.collection(USERS_COLLECTION)
    existing = users_ref.where("email", "==", email.lower()).limit(1).stream()
    if list(existing):
        raise ValueError("User with this email already exists")
    
    # Create user document
    user_id = secrets.token_urlsafe(16)  # Generate unique user ID
    user_data = {
        "user_id": user_id,
        "email": email.lower(),
        "password_hash": get_password_hash(password),
        "created_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP,
        "active": True
    }
    
    # Save to Firestore
    doc_ref = db.collection(USERS_COLLECTION).document(user_id)
    doc_ref.set(user_data)
    
    return {
        "user_id": user_id,
        "email": email.lower(),
        "created_at": datetime.utcnow().isoformat()
    }


def authenticate_user(email: str, password: str) -> Optional[Dict]:
    """
    Authenticate a user by email and password.
    
    Returns:
        User dict if authenticated, None otherwise
    """
    if db is None:
        return None
    
    # Find user by email
    users_ref = db.collection(USERS_COLLECTION)
    users = users_ref.where("email", "==", email.lower()).limit(1).stream()
    
    user_doc = None
    for doc in users:
        user_doc = doc
        break
    
    if not user_doc:
        return None
    
    user_data = user_doc.to_dict()
    
    # Check if user is active
    if not user_data.get("active", True):
        return None
    
    # Verify password
    if not verify_password(password, user_data.get("password_hash", "")):
        return None
    
    return {
        "user_id": user_data.get("user_id"),
        "email": user_data.get("email")
    }


def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Get user by user_id."""
    if db is None:
        return None
    
    doc_ref = db.collection(USERS_COLLECTION).document(user_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        return None
    
    user_data = doc.to_dict()
    if not user_data.get("active", True):
        return None
    
    # Don't return password hash
    return {
        "user_id": user_data.get("user_id"),
        "email": user_data.get("email"),
        "created_at": user_data.get("created_at")
    }


def delete_user(user_id: str) -> bool:
    """
    Delete a user account (soft delete by setting active=False).
    
    Returns:
        True if deleted, False otherwise
    """
    if db is None:
        return False
    
    doc_ref = db.collection(USERS_COLLECTION).document(user_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        return False
    
    # Soft delete - set active to False
    doc_ref.update({
        "active": False,
        "updated_at": firestore.SERVER_TIMESTAMP,
        "deleted_at": firestore.SERVER_TIMESTAMP
    })
    
    return True


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return {"user_id": user_id, "email": payload.get("email")}
    except JWTError:
        return None

