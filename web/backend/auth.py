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
# Passwords are hashed using bcrypt (one-way, secure, industry standard)
# Bcrypt hashes are ~60 characters and cannot be reversed
# Configure passlib to use bcrypt with explicit settings
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Standard bcrypt rounds
    bcrypt__ident="2b"  # Use bcrypt version 2b
)

# JWT token signing (NOT for password encryption!)
# HS256 = HMAC-SHA256 (256-bit hash algorithm for signing JWT tokens)
# This signs authentication tokens to prevent tampering
# Passwords are NOT encrypted with this - they use bcrypt above
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"  # For JWT token signing, not password hashing
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
    # Try passlib first (handles both passlib and direct bcrypt hashes)
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Fallback to direct bcrypt verification if passlib fails
        try:
            import bcrypt
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False


def get_password_hash(password: str) -> str:
    """Hash a password."""
    # Bcrypt has a 72-byte limit
    # Convert to bytes to check actual byte length (not character length)
    if not isinstance(password, str):
        password = str(password)
    
    # Normalize the password string (remove any hidden characters)
    password = password.strip()
    
    password_bytes = password.encode('utf-8')
    
    # Debug: log password info if there's an issue
    if len(password_bytes) > 72:
        # Truncate to exactly 72 bytes
        truncated_bytes = password_bytes[:72]
        password = truncated_bytes.decode('utf-8', errors='ignore')
        # Verify: re-encode to ensure it's <= 72 bytes
        verify_bytes = password.encode('utf-8')
        if len(verify_bytes) > 72:
            # Edge case: if decoding somehow added bytes, force truncate again
            password = verify_bytes[:72].decode('utf-8', errors='ignore')
    
    # Ensure password is a clean string (no None, no empty)
    if not password:
        raise ValueError("Password cannot be empty")
    
    # Try hashing - if it fails, we'll get a better error
    try:
        # Use hash() method directly - this should work for passwords <= 72 bytes
        hash_result = pwd_context.hash(password)
        return hash_result
    except Exception as e:
        # If we get a 72-byte error, something is very wrong
        error_msg = str(e)
        final_bytes = password.encode('utf-8')
        
        # Check if it's actually the 72-byte error
        if "72" in error_msg and "byte" in error_msg.lower():
            # This shouldn't happen if password is <= 72 bytes
            # But passlib might be checking something else
            # Try using bcrypt directly as a workaround
            import bcrypt
            try:
                # Hash with bcrypt directly (bypasses passlib's check)
                salt = bcrypt.gensalt(rounds=12)
                hash_bytes = bcrypt.hashpw(password.encode('utf-8'), salt)
                return hash_bytes.decode('utf-8')
            except Exception as bcrypt_error:
                raise ValueError(
                    f"Password hashing failed. Password: {len(password)} chars, "
                    f"{len(final_bytes)} bytes. Passlib error: {error_msg}. "
                    f"Bcrypt direct error: {str(bcrypt_error)}"
                )
        else:
            # Some other error
            raise ValueError(f"Password hashing failed: {error_msg}")


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
    
    # Validate password length
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters long")
    # Note: Password length over 72 bytes will be handled in get_password_hash
    
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
    
    # Verify password (handle truncation for passwords over 72 bytes)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password = password_bytes[:72].decode('utf-8', errors='ignore')
    
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
