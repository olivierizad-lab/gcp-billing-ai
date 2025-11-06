#!/usr/bin/env python3
"""
Test service account permissions for listing reasoning engines.
This script can be used to test permissions both locally (with impersonation)
and in Cloud Run (where the service account runs natively).
"""
import os
import sys
from google.auth import default
from google.auth.transport.requests import Request
from google.auth import impersonated_credentials
from google.oauth2 import service_account
import requests

PROJECT_ID = os.getenv("PROJECT_ID", "qwiklabs-asl-04-8e9f23e85ced")
LOCATION = os.getenv("LOCATION", "us-central1")
SERVICE_ACCOUNT = os.getenv("SERVICE_ACCOUNT", "agent-engine-api-sa@qwiklabs-asl-04-8e9f23e85ced.iam.gserviceaccount.com")

def test_with_impersonation():
    """Test using service account impersonation (for local testing)."""
    print(f"\n{'='*80}")
    print("Testing with Service Account Impersonation")
    print(f"{'='*80}")
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"Service Account: {SERVICE_ACCOUNT}")
    print()
    
    try:
        # Get source credentials (your user account)
        source_credentials, project = default()
        print(f"✓ Got source credentials (project: {project})")
        
        # Create impersonated credentials
        target_scopes = ['https://www.googleapis.com/auth/cloud-platform']
        credentials = impersonated_credentials.Credentials(
            source_credentials=source_credentials,
            target_principal=SERVICE_ACCOUNT,
            target_scopes=target_scopes,
        )
        
        print(f"✓ Created impersonated credentials for {SERVICE_ACCOUNT}")
        
        # Refresh to get token
        credentials.refresh(Request())
        print(f"✓ Got access token (first 30 chars): {credentials.token[:30]}...")
        
        # Test the API call
        return test_api_call(credentials, "impersonated")
        
    except Exception as e:
        import traceback
        print(f"\n✗ ERROR with impersonation: {e}")
        print("Note: Service account impersonation requires:")
        print("  1. roles/iam.serviceAccountTokenCreator on the service account")
        print("  2. Your user account must have permission to impersonate")
        traceback.print_exc()
        return False

def test_with_default():
    """Test using default credentials (for Cloud Run)."""
    print(f"\n{'='*80}")
    print("Testing with Default Credentials (ADC)")
    print(f"{'='*80}")
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print()
    
    try:
        credentials, project = default()
        print(f"✓ Got credentials (project: {project})")
        print(f"  Credentials type: {type(credentials).__name__}")
        
        if not credentials.valid:
            credentials.refresh(Request())
            print("✓ Credentials refreshed")
        
        return test_api_call(credentials, "default")
        
    except Exception as e:
        import traceback
        print(f"\n✗ ERROR: {e}")
        traceback.print_exc()
        return False

def test_api_call(credentials, source_type):
    """Make the actual API call to list reasoning engines."""
    base_url = f"https://{LOCATION}-aiplatform.googleapis.com/v1"
    endpoint = f"{base_url}/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines"
    
    print(f"\nEndpoint: {endpoint}")
    
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
    }
    
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
            print("\n⚠ Permission denied!")
            print(f"  Service account: {SERVICE_ACCOUNT}")
            print(f"  Required permission: aiplatform.reasoningEngines.list")
            print(f"  Source: {source_type}")
            print("\n  Check IAM bindings:")
            print(f"    gcloud projects get-iam-policy {PROJECT_ID} \\")
            print(f"      --flatten='bindings[].members' \\")
            print(f"      --filter='bindings.members:{SERVICE_ACCOUNT}'")
        
        # Try to parse error details
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

def main():
    print("Service Account Permissions Test")
    print("="*80)
    
    # Test 1: Default credentials (works in Cloud Run, might work locally too)
    success_adc = test_with_default()
    
    # Test 2: Impersonation (only works locally with proper permissions)
    if not success_adc:
        print("\n" + "="*80)
        print("Default credentials failed. Trying service account impersonation...")
        print("="*80)
        success_impersonation = test_with_impersonation()
    else:
        success_impersonation = True
    
    # Summary
    print(f"\n{'='*80}")
    print("Summary")
    print(f"{'='*80}")
    print(f"Default Credentials (ADC): {'✓ PASSED' if success_adc else '✗ FAILED'}")
    print(f"Service Account Impersonation: {'✓ PASSED' if success_impersonation else '✗ FAILED'}")
    
    if not success_adc and not success_impersonation:
        print("\n⚠ All tests failed!")
        print("\nTroubleshooting steps:")
        print("1. Verify service account has required permissions:")
        print(f"   gcloud projects get-iam-policy {PROJECT_ID} \\")
        print(f"     --flatten='bindings[].members' \\")
        print(f"     --filter='bindings.members:{SERVICE_ACCOUNT}'")
        print("\n2. Required roles:")
        print("   - roles/aiplatform.user (or)")
        print("   - roles/aiplatform.admin (or)")
        print("   - Custom role with: aiplatform.reasoningEngines.list")
        print("\n3. Update custom role (if using):")
        print("   gcloud iam roles update gcpBillingAgentService \\")
        print(f"     --project={PROJECT_ID} \\")
        print("     --file=web/deploy/custom-iam-role.yaml")
        print("\n4. Wait a few minutes for IAM changes to propagate")
        print("\n5. In Cloud Run, restart the service to refresh credentials")

if __name__ == "__main__":
    main()

