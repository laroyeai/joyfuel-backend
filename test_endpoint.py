import requests
import json

# Vercel deployment URL
url = "https://joyfuel-backend-4cvp757xe-laroye-ais-projects.vercel.app/api/beta/register/"

# Test data
data = {
    "email": "test@example.com",
    "platform": "web"
}

# Headers
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Origin": "https://www.laroye.ai",
    "Referer": "https://www.laroye.ai/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

print(f"Sending request to: {url}")
print(f"With data: {json.dumps(data, indent=2)}")
print(f"And headers: {json.dumps(headers, indent=2)}")

try:
    # First, send an OPTIONS request
    options_response = requests.options(url, headers=headers)
    print("\nOPTIONS request:")
    print(f"Status Code: {options_response.status_code}")
    print(f"Response Headers: {dict(options_response.headers)}")

    # Then send the actual POST request
    print("\nPOST request:")
    response = requests.post(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    try:
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
    except json.JSONDecodeError:
        print(f"Response Body: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"Error making request: {e}") 