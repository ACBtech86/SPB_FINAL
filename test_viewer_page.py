"""Test viewer page with authentication.

Usage:
    py test_viewer_page.py
"""

import requests
from requests import Session

# Create a session to maintain cookies
session = Session()

base_url = "http://localhost:8000"

print("\n" + "="*60)
print("Testing SPBSite Viewer with Authentication")
print("="*60 + "\n")

# Step 1: Login
print("1. Logging in...")
login_response = session.post(
    f"{base_url}/login",
    data={"username": "admin", "password": "admin"},
    allow_redirects=False
)
print(f"   Login response: {login_response.status_code}")
if login_response.status_code not in (200, 303):
    print(f"   ERROR: Login failed with status {login_response.status_code}")
    exit(1)

# Step 2: Access messages page
print("\n2. Accessing BACEN messages page...")
messages_response = session.get(f"{base_url}/monitoring/messages/inbound/bacen")
print(f"   Response status: {messages_response.status_code}")

if messages_response.status_code == 500:
    print("\n   ERROR: Internal Server Error detected!")
    print("\n   Response content (first 500 chars):")
    print(messages_response.text[:500])
elif messages_response.status_code == 200:
    print("   SUCCESS: Page loaded correctly")
    # Check if composite_key is in the HTML
    if "viewer/spb_bacen_to_local/" in messages_response.text:
        print("   ✓ Viewer links found in page")
        # Extract first viewer link
        import re
        matches = re.findall(r'/viewer/spb_bacen_to_local/([^"]+)', messages_response.text)
        if matches:
            first_key = matches[0]
            print(f"   ✓ First composite key: {first_key[:50]}...")
        else:
            print("   ✗ No composite keys found in viewer links")
    else:
        print("   ✗ No viewer links found")
else:
    print(f"   Unexpected status: {messages_response.status_code}")

print("\n" + "="*60)
