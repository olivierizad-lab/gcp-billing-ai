#!/usr/bin/env python3
"""
Simple test script for the deployed Agent Engine.

Usage:
    python bq_agent_mick/test_agent.py "What are the top 10 services by cost?"
    
Or run interactively:
    python bq_agent_mick/test_agent.py
"""

import sys
import os
import time
import json
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
PROJECT_ID = os.getenv("BQ_PROJECT", "qwiklabs-asl-04-8e9f23e85ced")
LOCATION = "us-central1"
# Update this ID after each deployment
# Latest: 12934654789156864 (from deployment output)
REASONING_ENGINE_ID = "4581836476756525056"


def query_agent(query_text, session_id=None, user_id="test_user"):
    """Query the deployed Agent Engine using class method calls."""
    try:
        from google.auth import default
        from google.auth.transport.requests import Request
        import requests
        import uuid
        
        # Get credentials
        print("Authenticating...")
        credentials, _ = default()
        if not credentials.valid:
            credentials.refresh(Request())
        
        base_url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{REASONING_ENGINE_ID}"
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
        }
        
        # Generate a session ID if not provided (Agent Engine manages sessions internally)
        if not session_id:
            session_id = f"session-{uuid.uuid4().hex[:8]}"
        
        # Use the correct endpoints from Console
        print(f"\nSending query: {query_text}")
        print("-" * 60)
        
        # Try streamQuery endpoint first (with SSE)
        # AdkApp.stream_query() requires: message (str|dict), user_id (str), session_id (optional)
        stream_query_url = f"{base_url}:streamQuery?alt=sse"
        
        query_payloads = [
            # Format 1: message and user_id in input - let AdkApp manage sessions internally
            # (session_id causes "Invalid Session resource name" error)
            {
                "input": {
                    "message": query_text,
                    "user_id": user_id
                }
            },
            # Format 2: Try with direct message/user_id (no input wrapper)
            {
                "message": query_text,
                "user_id": user_id
            }
        ]
        
        print("Calling streamQuery endpoint...")
        
        # Try payloads until one works
        response = None
        for i, payload in enumerate(query_payloads, 1):
            print(f"  Trying payload format {i}...")
            test_response = requests.post(stream_query_url, headers=headers, json=payload, stream=True, timeout=120)
            if test_response.status_code == 200:
                print(f"  ✓ Payload format {i} accepted!")
                response = test_response
                break
            elif test_response.status_code != 400:
                # Non-400 error might be auth or other issue
                print(f"  Status {test_response.status_code}: {test_response.text[:200]}")
                response = test_response
                break
        
        if not response:
            # All formats failed, use the first one and report error
            response = requests.post(stream_query_url, headers=headers, json=query_payloads[0], stream=True, timeout=120)
        
        # If streamQuery works, process SSE stream
        if response.status_code == 200:
            print("Reading stream response (this may take 30-90 seconds for BigQuery queries)...")
            print("-" * 60)
            print("(Processing may take time while agent queries BigQuery)")
            print()
            output_parts = []
            final_text = ""
            line_count = 0
            max_lines = 1000  # Allow more lines for longer responses
            data_count = 0
            last_activity = time.time()
            timeout_seconds = 180  # 3 minute timeout
            start_time = time.time()
            
            try:
                for line in response.iter_lines(decode_unicode=True):
                    # Check timeout
                    if time.time() - last_activity > timeout_seconds:
                        print(f"\n⚠ No activity for {timeout_seconds}s, timing out")
                        break
                    
                    line_count += 1
                    if line_count > max_lines:
                        print(f"\n⚠ Reached max lines ({max_lines}), stopping read")
                        break
                    
                    if line:
                        last_activity = time.time()
                        line_str = line if isinstance(line, str) else line.decode('utf-8')
                        
                        # The response is JSON lines format, not SSE (no 'data: ' prefix)
                        # Some JSON objects may be split across multiple lines
                        if line_str.strip():
                            # Log line info for first few lines
                            if line_count <= 10:
                                line_len = len(line_str)
                                # Show first and last 100 chars if line is long
                                if line_len > 300:
                                    preview = f"{line_str[:100]}...{line_str[-100:]}"
                                else:
                                    preview = line_str
                                print(f"[DEBUG] Line {line_count} (length={line_len}): {repr(preview)}")
                            
                            # Try to parse as complete JSON
                            try:
                                json_data = json.loads(line_str)
                                data_count += 1
                                output_parts.append(json_data)
                                if line_count <= 10:
                                    print(f"[DEBUG] ✓ Successfully parsed JSON chunk {data_count}")
                                
                                # Extract text content if available
                                if isinstance(json_data, dict):
                                    # Look for content -> parts -> text structure
                                    content = json_data.get('content', {})
                                    if isinstance(content, dict):
                                        parts = content.get('parts', [])
                                        for part in parts:
                                            if isinstance(part, dict):
                                                # Extract text
                                                text = part.get('text')
                                                if text:
                                                    print(text, end='', flush=True)
                                                    final_text += str(text)
                                                
                                                # Extract function responses for debugging
                                                func_response = part.get('function_response')
                                                if func_response:
                                                    func_name = func_response.get('name', 'unknown')
                                                    func_resp = func_response.get('response', {})
                                                    status = func_resp.get('status', 'unknown')
                                                    if status == 'ERROR':
                                                        error = func_resp.get('error_details', 'Unknown error')
                                                        print(f"\n[DEBUG] Function {func_name} error: {error[:200]}")
                                                
                                                # Extract function calls for debugging (to check table_id)
                                                func_call = part.get('function_call')
                                                if func_call:
                                                    func_name = func_call.get('name', 'unknown')
                                                    func_args = func_call.get('args', {})
                                                    if func_name == 'get_table_info' or func_name == 'execute_sql':
                                                        print(f"\n[DEBUG] Function call: {func_name}")
                                                        if 'table_id' in func_args:
                                                            print(f"[DEBUG]   table_id: {func_args.get('table_id')}")
                                                        if 'dataset_id' in func_args:
                                                            print(f"[DEBUG]   dataset_id: {func_args.get('dataset_id')}")
                                                        if 'project_id' in func_args:
                                                            print(f"[DEBUG]   project_id: {func_args.get('project_id')}")
                                    else:
                                        # Direct text or other fields
                                        text = (json_data.get('text') or 
                                               json_data.get('message') or
                                               json_data.get('output') or
                                               json_data.get('response'))
                                        if text:
                                            print(text, end='', flush=True)
                                            final_text += str(text)
                            except json.JSONDecodeError as json_err:
                                # JSON decode error - might be incomplete JSON (split across lines)
                                # For now, just log it but don't crash
                                if line_count <= 10:
                                    # Show more of the line to see if it's complete
                                    line_preview = line_str[:500] if len(line_str) > 500 else line_str
                                    print(f"[DEBUG] JSON parse error (line might be incomplete, length={len(line_str)}): {repr(line_preview)}")
                                # Try to extract partial info if it looks like JSON
                                if '"table_id"' in line_str:
                                    # Try to extract table_id even from partial JSON
                                    match = re.search(r'"table_id":\s*"([^"]*)"', line_str)
                                    if match:
                                        table_id_part = match.group(1)
                                        print(f"[DEBUG] Found table_id in line: {table_id_part}")
                            except Exception as parse_err:
                                # Other parsing errors
                                if line_count <= 10:
                                    print(f"[DEBUG] Parse error: {parse_err} - {repr(line_str[:200])}")
                        elif line_count % 100 == 0:
                            # Log progress every 100 empty lines
                            elapsed = int(time.time() - start_time)
                            print(f"[DEBUG] Still waiting... ({elapsed}s elapsed, {line_count} lines read)")
                
                elapsed = int(time.time() - start_time)
                print(f"\n[DEBUG] Stream ended after {elapsed}s")
                print(f"[DEBUG] Total lines: {line_count}, Data chunks: {data_count}")
                print("\n" + "=" * 60)
                
                # Return the combined output
                if final_text:
                    return final_text
                elif output_parts:
                    return output_parts
                elif data_count == 0:
                    print("⚠ Warning: Stream connected but no data received")
                    print("  This may mean:")
                    print("  - Agent is still processing (check logs in Console)")
                    print("  - Query is taking longer than expected")
                    print("  - There may be an error in the agent execution")
                    print(f"\n  Check logs: https://console.cloud.google.com/logs/query?project={PROJECT_ID}")
                    print(f"  Filter: resource.labels.reasoning_engine_id={REASONING_ENGINE_ID}")
                    return None
                else:
                    return "Stream received but no content extracted"
            except Exception as stream_error:
                print(f"\n⚠ Error reading stream: {stream_error}")
                import traceback
                traceback.print_exc()
                # Can't access response.text after stream is consumed, so skip that
                return None
        
        # If streamQuery doesn't work, try regular query endpoint
        if response.status_code != 200:
            print(f"\n⚠ StreamQuery returned status {response.status_code}")
            print(f"Response text: {response.text[:500]}")
            try:
                error_json = response.json()
                print(f"Error details: {json.dumps(error_json, indent=2)[:1000]}")
            except:
                pass
            
            print(f"\nTrying regular query endpoint...")
            query_url = f"{base_url}:query"
            response = requests.post(query_url, headers=headers, json=query_payloads[0])
            
            if response.status_code == 200:
                result = response.json()
                print("\nAgent Response:")
                print("=" * 60)
                print(json.dumps(result, indent=2)[:2000])
                print("=" * 60)
                return result
            else:
                print(f"Query endpoint also failed with status {response.status_code}")
                print(f"Error: {response.text[:500]}")
                response.raise_for_status()
        
        result = response.json()
        
        # Extract output based on different possible response formats
        output = None
        if "output" in result:
            output = result["output"]
        elif "predictions" in result and len(result["predictions"]) > 0:
            output = result["predictions"][0]
        elif "response" in result:
            output = result["response"]
        elif "content" in result:
            output = result["content"]
        else:
            output = result
        
        print("\nAgent Response:")
        print("=" * 60)
        if isinstance(output, dict):
            # Pretty print if it's a dict
            import json
            print(json.dumps(output, indent=2))
        else:
            print(output)
        print("=" * 60)
        
        return output
        
    except ImportError:
        print("Error: Missing dependencies.")
        print("Install with: pip install google-auth google-auth-httplib2 requests")
        return None
    except Exception as e:
        print(f"Error querying agent: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"Error details: {json.dumps(error_detail, indent=2)[:1000]}")
            except:
                print(f"Error response: {e.response.text[:500]}")
        import traceback
        traceback.print_exc()
        return None


def main():
    session_id = None  # Reuse session across queries in interactive mode
    
    if len(sys.argv) > 1:
        # Single query mode
        query = " ".join(sys.argv[1:])
        query_agent(query, session_id)
    else:
        # Interactive mode - reuse session
        print(f"Agent Engine Test Client")
        print(f"Project: {PROJECT_ID}")
        print(f"Reasoning Engine ID: {REASONING_ENGINE_ID}")
        print(f"\nEnter queries (or 'exit' to quit):")
        print(f"(Session will be created automatically)\n")
        
        while True:
            try:
                query = input("> ").strip()
                if not query:
                    continue
                if query.lower() in ['exit', 'quit', 'q']:
                    break
                
                # Reuse session across queries for conversation continuity
                result = query_agent(query, session_id)
                if result and not session_id:
                    # Extract session ID from first response if available
                    # (This is a placeholder - actual implementation may differ)
                    pass
                
                print()  # Blank line between queries
                
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except EOFError:
                break


if __name__ == "__main__":
    main()
