#!/usr/bin/env python3
"""
Simple test script to debug Agent Engine scanning.
Tests both user credentials and service account credentials.
"""
import os
import sys
from google.auth import default
from google.auth.transport.requests import Request
import requests

PROJECT_ID = os.getenv("PROJECT_ID", "qwiklabs-asl-04-8e9f23e85ced")
LOCATION = os.getenv("LOCATION", "us-central1")
SERVICE_ACCOUNT = os.getenv("SERVICE_ACCOUNT", "agent-engine-api-sa@qwiklabs-asl-04-8e9f23e85ced.iam.gserviceaccount.com")

def test_scan(credentials_source="default"):
    """Test scanning with different credential sources."""
    print(f"\n{'='*80}")
    print(f"Testing Agent Engine scanning with: {credentials_source}")
    print(f"{'='*80}")
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print()
    
    try:
        # Get credentials
        if credentials_source == "service_account":
            # Try to use service account impersonation
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = ""  # Clear to force ADC
            # This would need service account key file or impersonation setup
            print("⚠ Service account impersonation not implemented in this test")
            print("   Run this script from Cloud Run or with service account key file")
            return
        
        credentials, project = default()
        print(f"✓ Got credentials, project: {project}")
        print(f"  Credentials type: {type(credentials).__name__}")
        
        if not credentials.valid:
            print("  Refreshing credentials...")
            credentials.refresh(Request())
            print("  ✓ Credentials refreshed")
        else:
            print("  ✓ Credentials are valid")
        
        # Build API endpoint
        base_url = f"https://{LOCATION}-aiplatform.googleapis.com/v1"
        endpoint = f"{base_url}/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines"
        
        print(f"\nEndpoint: {endpoint}")
        
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
        }
        
        print(f"Token (first 30 chars): {credentials.token[:30]}...")
        print()
        
        # Make API call
        print("Making API call...")
        response = requests.get(endpoint, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            engines = data.get('reasoningEngines', [])
            print(f"\n✓ SUCCESS! Found {len(engines)} reasoning engine(s):")
            for engine in engines:
                display_name = engine.get('displayName', 'N/A')
                name = engine.get('name', 'N/A')
                engine_id = name.split('/')[-1] if '/' in name else name
                print(f"  - {display_name}: {engine_id}")
            return True
        else:
            print(f"\n✗ FAILED: HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            if response.status_code == 403:
                print("\n⚠ Permission denied - check IAM permissions")
                print(f"  Current identity needs 'roles/aiplatform.user' or 'aiplatform.reasoningEngines.list' permission")
                # Try to get more info about the error
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_info = error_data['error']
                        print(f"\nError details:")
                        print(f"  Message: {error_info.get('message', 'N/A')}")
                        print(f"  Status: {error_info.get('status', 'N/A')}")
                except:
                    pass
            return False
    
    except Exception as e:
        import traceback
        print(f"\n✗ ERROR: {e}")
        traceback.print_exc()
        return False

def main():
    print("Agent Engine Scanning Test")
    print("="*80)
    
    # Test with default credentials (user or service account from environment)
    success = test_scan("default")
    
    if success:
        print(f"\n{'='*80}")
        print("✓ Test PASSED - Scanning works with current credentials")
        print("="*80)
    else:
        print(f"\n{'='*80}")
        print("✗ Test FAILED - Check IAM permissions")
        print("="*80)
        print("\nTo test with service account in Cloud Run:")
        print("  1. Ensure service account has roles/aiplatform.user")
        print("  2. Check Cloud Run logs for detailed error messages")
        print("  3. Verify project ID and location are correct")
        print("\nAPI endpoint format:")
        print(f"  https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines")

if __name__ == "__main__":
    main()

