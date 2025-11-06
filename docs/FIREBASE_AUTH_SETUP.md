# Firebase Authentication Setup Guide

This guide explains how to set up Firebase Authentication for the GCP Billing Agent application.

## Overview

The application uses Firebase Authentication for user login with the following features:
- **Email/Password authentication** with domain restriction (`@asl.apps-eval.com`)
- **Account creation** with domain validation
- **Account management** (view profile, delete account)
- **Password reset** functionality
- **Secure API access** using Firebase ID tokens

## Prerequisites

1. ✅ Google Cloud Project (already have: `qwiklabs-asl-04-8e9f23e85ced`)
2. ✅ Firestore already enabled and working (used for query history)
3. ⚠️ Firebase Authentication needs to be enabled

## Setup Steps

### 1. Enable Firebase Authentication

Since you're already using Firestore, your Firebase project is already set up! You just need to enable Authentication:

```bash
# Enable Firebase Authentication API
gcloud services enable identitytoolkit.googleapis.com --project=qwiklabs-asl-04-8e9f23e85ced
```

### 2. Access Firebase Console

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your existing project (`qwiklabs-asl-04-8e9f23e85ced`)
3. You should already see Firestore in the left menu (since it's working)

### 3. Enable Email/Password Authentication

1. In Firebase Console, go to **Authentication** > **Sign-in method**
2. Click on **Email/Password**
3. Enable **Email/Password** (first toggle)
4. Click **Save**

### 4. Get Firebase Configuration

1. In Firebase Console, go to **Project Settings** (gear icon)
2. Scroll down to **Your apps** section
3. Click **Web** icon (`</>`) to add a web app
4. Register your app (e.g., "GCP Billing Agent")
5. Copy the Firebase configuration object

### 5. Set Environment Variables

Create a `.env` file in `web/frontend/` (for local development):

```bash
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=qwiklabs-asl-04-8e9f23e85ced
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=your-app-id
```

**For Cloud Run deployment**, set these as environment variables in your Cloud Run service.

### 6. Set Up Firebase Admin SDK (Backend)

**Good news**: Since Firestore is already working, your service account already has the necessary permissions! However, we need to add the Firebase Admin role for authentication:

#### Option A: Use Default Credentials (Cloud Run - Recommended)

The backend will automatically use the Cloud Run service account credentials. Add the Firebase Admin role:

```bash
PROJECT_ID="qwiklabs-asl-04-8e9f23e85ced"
SERVICE_ACCOUNT="agent-engine-api-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant Firebase Admin role (for authentication)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/firebase.admin"
```

**Note**: The service account already has Firestore access, so this just adds authentication capabilities.

#### Option B: Use Service Account Key (Local Development - Optional)

Only needed if you want to test authentication locally:

1. In Firebase Console, go to **Project Settings** > **Service Accounts**
2. Click **Generate New Private Key**
3. Save the JSON file securely
4. Set environment variable:
   ```bash
   export FIREBASE_SERVICE_ACCOUNT_KEY=/path/to/service-account-key.json
   ```

### 7. Deploy the Application

```bash
# Deploy with Firebase authentication
make deploy-web-cloud-run PROJECT_ID="qwiklabs-asl-04-8e9f23e85ced"
```

Or use the simple deployment script:

```bash
./web/deploy/deploy-simple-iap.sh PROJECT_ID="qwiklabs-asl-04-8e9f23e85ced" -y
```

## Features

### Account Creation
- Users can create accounts with email/password
- **Domain validation**: Only `@asl.apps-eval.com` emails are allowed
- Password must be at least 6 characters

### Login
- Users sign in with email and password
- Session persists across browser sessions
- Automatic token refresh

### Account Management
- View account information (email, UID)
- Delete account (with confirmation)
- Password reset via email

### Security
- All API endpoints require Firebase ID token
- Domain restriction enforced on both frontend and backend
- User can only access their own data (history, queries)

## Testing

1. **Create Account**:
   - Go to the application URL
   - Click "Sign up"
   - Enter email: `test@asl.apps-eval.com`
   - Enter password (min 6 characters)
   - Click "Create Account"

2. **Sign In**:
   - Enter email and password
   - Click "Sign In"

3. **Test API Access**:
   - After signing in, you should be able to:
     - View agents
     - Send queries
     - View history
     - Delete history

4. **Test Domain Restriction**:
   - Try creating account with `test@example.com`
   - Should show error: "Email must be from asl.apps-eval.com"

## Troubleshooting

### "Firebase Admin SDK initialization failed"
- Make sure Firebase Admin SDK service agent role is granted
- For local dev, set `FIREBASE_SERVICE_ACCOUNT_KEY` environment variable

### "Authentication failed" errors
- Check Firebase configuration in environment variables
- Verify Firebase Authentication is enabled in Firebase Console
- Check browser console for detailed error messages

### "Access denied. Only @asl.apps-eval.com emails are allowed"
- This is expected behavior - domain restriction is working
- Use an email ending with `@asl.apps-eval.com`

## Security Notes

1. **Domain Restriction**: Enforced on both frontend (signup) and backend (API access)
2. **Token Verification**: All API requests verify Firebase ID tokens
3. **User Isolation**: Users can only access their own data
4. **Password Security**: Firebase handles password hashing and security

## Next Steps

- Consider adding email verification
- Add user roles/permissions if needed
- Set up Firebase Hosting for custom domain (optional)
- Configure password reset email templates

