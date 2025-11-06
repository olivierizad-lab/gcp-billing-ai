# Authentication Setup - Firestore Authentication

## Overview

The GCP Billing Agent uses **custom Firestore-based authentication** with JWT tokens. This provides:
- ✅ **Simple setup** - No OAuth consent screen or IAP configuration needed
- ✅ **Domain restrictions** - Enforce email domain requirements
- ✅ **User management** - Sign up, sign in, and account management
- ✅ **Secure** - Passwords hashed with bcrypt, JWT tokens for sessions

## How It Works

1. **Sign Up**: User creates account with email/password (domain validated)
2. **Password Storage**: Passwords hashed with bcrypt and stored in Firestore
3. **Sign In**: User authenticates, receives JWT token
4. **API Access**: All API requests include JWT token in Authorization header
5. **User Isolation**: Query history and data scoped to user_id from token

## Architecture

```
User → Frontend (Sign Up/Login) → Backend API
                                    ↓
                              Firestore (users collection)
                                    ↓
                              JWT Token Generated
                                    ↓
                              Frontend stores token
                                    ↓
                        All API requests include token
```

## Configuration

### Domain Restrictions

Currently configured for `@asl.apps-eval.com` emails. To change:

1. **Backend** (`web/backend/auth.py`):
   ```python
   REQUIRED_DOMAIN = "your-domain.com"  # Change this
   ```

2. **Frontend** (`web/frontend/src/Auth.jsx`):
   ```javascript
   const REQUIRED_DOMAIN = "your-domain.com";  // Change this
   ```

3. **Redeploy**:
   ```bash
   make deploy-web-simple PROJECT_ID=your-project-id
   ```

### JWT Secret Key

The JWT secret key is automatically generated and stored in Cloud Run environment variables. It's consistent across deployments to ensure tokens remain valid.

**To view the secret key:**
```bash
gcloud run services describe agent-engine-api \
  --region=us-central1 \
  --project=PROJECT_ID \
  --format="value(spec.template.spec.containers[0].env)" | grep JWT_SECRET_KEY
```

**To set a custom secret key:**
```bash
gcloud run services update agent-engine-api \
  --region=us-central1 \
  --project=PROJECT_ID \
  --update-env-vars JWT_SECRET_KEY=your-secret-key
```

⚠️ **Important**: Changing the JWT secret key will invalidate all existing tokens. Users will need to sign in again.

## User Management

### Sign Up

Users can create accounts through the UI:
1. Navigate to the application
2. Click "Sign Up"
3. Enter email (must match required domain)
4. Enter password
5. Account created in Firestore

### Sign In

Users sign in with email and password:
1. Navigate to the application
2. Click "Sign In"
3. Enter credentials
4. Receive JWT token
5. Token stored in browser localStorage

### Account Management

Users can:
- View their profile
- Delete their account (removes user and all query history)

### Password Requirements

- Minimum length: 8 characters
- Maximum length: 72 bytes (bcrypt limit)
- Domain validation: Must be from required domain

## Firestore Structure

### Users Collection

```javascript
users/{user_id} {
  user_id: string,
  email: string,
  password_hash: string,  // bcrypt hash
  created_at: timestamp
}
```

### Query History Collection

```javascript
query_history/{query_id} {
  user_id: string,  // From JWT token (not client-provided)
  agent_name: string,
  message: string,
  response: string,
  timestamp: timestamp
}
```

## Security Considerations

### Password Security

- ✅ Passwords hashed with bcrypt (cost factor 12)
- ✅ Password length validated (8+ chars, max 72 bytes)
- ✅ Passwords never stored in plain text
- ✅ Passwords never logged

### Token Security

- ✅ JWT tokens signed with secret key
- ✅ Tokens expire after 7 days (configurable)
- ✅ Tokens stored in localStorage (browser)
- ✅ Tokens included in Authorization header

### Domain Restrictions

- ✅ Email domain validated on signup
- ✅ Generic error messages (don't reveal domain)
- ✅ Backend validation (frontend validation is convenience only)

### Data Isolation

- ✅ User ID extracted from JWT token (not client-provided)
- ✅ Query history scoped to authenticated user
- ✅ No cross-user data access

## Troubleshooting

### Sign Up Fails

**Error: "Please use your ASL class account email address"**
- Email must be from required domain
- Check domain configuration in `auth.py` and `Auth.jsx`

**Error: "Password hashing failed"**
- Password too long (>72 bytes)
- Check password length
- Try a shorter password

### Sign In Fails

**Error: "Invalid email or password"**
- Check email and password are correct
- Verify account exists in Firestore
- Check password hash is valid

**Error: "Invalid or expired token"**
- Token may have expired (7 days default)
- JWT secret key may have changed
- Sign out and sign in again

### Token Issues

**Error: "Invalid or expired token" on API requests**
- Check token is being sent in Authorization header
- Verify token hasn't expired
- Check JWT_SECRET_KEY is consistent

**Solution:**
```bash
# Check token in browser console
localStorage.getItem('token')

# Sign out and sign in again
```

### Firestore Permissions

**Error: "Missing or insufficient permissions"**
- Service account needs `roles/datastore.user`
- Check IAM permissions:
  ```bash
  gcloud projects get-iam-policy PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:agent-engine-api-sa@PROJECT_ID.iam.gserviceaccount.com"
  ```

## Testing

### Test Sign Up

```bash
# Use curl or Postman
curl -X POST https://api-url.run.app/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@asl.apps-eval.com",
    "password": "testpassword123"
  }'
```

### Test Sign In

```bash
curl -X POST https://api-url.run.app/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@asl.apps-eval.com",
    "password": "testpassword123"
  }'
```

### Test Authenticated Request

```bash
# Use token from sign in response
curl -X GET https://api-url.run.app/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Cleanup

### Delete User Account

Users can delete their own account through the UI, or manually:

```bash
# Using the cleanup script
make clean-history-user PROJECT_ID=project-id USER_ID=user-id
```

### Delete All Users

⚠️ **Use with caution!**

```bash
# Manually delete from Firestore
# Or use Firestore console
```

## References

- [Firestore Documentation](https://cloud.google.com/firestore/docs)
- [JWT Documentation](https://jwt.io/)
- [bcrypt Documentation](https://github.com/pyca/bcrypt/)
