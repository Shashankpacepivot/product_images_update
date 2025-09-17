import time
import requests
from access_token import get_access_token

# Replace these with your actual values
access_token = get_access_token()
#refresh_token = "YOUR_REFRESH_TOKEN"  
region = "eu"  # or eu, fe, etc
marketplace_id = "A21TJRUUN4KGV" 
feed_document_id = '' # from step 1, the one you uploaded file for

# Base URL depends on region
base_url = f"https://sellingpartnerapi-{region}.amazon.com"

print(access_token)
headers = {
    "x-amz-access-token": access_token,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Step 1: Create the feed to submit the document
create_feed_url = f"{base_url}/feeds/2021-06-30/feeds"

payload = {
    "feedType": "JSON_LISTINGS_FEED",
    "marketplaceIds": [marketplace_id],
    "inputFeedDocumentId": feed_document_id
}

response = requests.post(create_feed_url, json=payload, headers=headers)
response.raise_for_status()

feed_response = response.json()
feed_id = feed_response["feedId"]
print(f"Feed created with feedId: {feed_id}")

# Step 2: Poll feed status until done
get_feed_status_url = f"{base_url}/feeds/2021-06-30/feeds/{feed_id}"

while True:
    status_response = requests.get(get_feed_status_url, headers=headers)
    status_response.raise_for_status()
    status_data = status_response.json()
    processing_status = status_data["processingStatus"]
    print(f"Feed processing status: {processing_status}")

    if processing_status in ("DONE", "DONE_NO_DATA", "CANCELLED", "FATAL"):
        break

    time.sleep(30)  # wait 30 seconds before polling again

# Step 3: If there's a processing report, get it
if "processingReport" in status_data:
    report = status_data["processingReport"]
    print("Processing report:")
    print(report)
else:
    print("No processing report available.")

