import gzip
import io
import requests
from access_token import get_access_token
access_token = get_access_token()
feed_id = ""
region = "eu"  # adjust if needed
marketplace_id = "A21TJRUUN4KGV" 

base_url = f"https://sellingpartnerapi-{region}.amazon.com"

headers = {
    "accept": "application/json",
    "x-amz-access-token": access_token
}

# Step 1: Get feed status (to find processingReportDocumentId)
url_status = f"{base_url}/feeds/2021-06-30/feeds/{feed_id}"
params = {
        "identifiersType": "feed",
        "feedTypes": "POST_PRODUCT_DATA",
        "marketplaceIds": marketplace_id,
    }
response = requests.get(url_status, headers=headers, params=params)
print(response)
response.raise_for_status()
data = response.json()
print(data)
feed_status = response.json()


print("Feed status response:", feed_status)

processing_report_doc_id = feed_status.get("resultFeedDocumentId")
if not processing_report_doc_id:
    print("No processingReportDocumentId found. Feed might not have a processing report yet.")
    exit()

print("Processing report document ID:", processing_report_doc_id)

# Step 2: Get document info (to get the pre-signed URL)
url_doc = f"{base_url}/feeds/2021-06-30/documents/{processing_report_doc_id}"
response = requests.get(url_doc, headers=headers)
response.raise_for_status()
doc_info = response.json()

print("Document info response:", doc_info)

download_url = doc_info.get("url")
if not download_url:
    print("No URL found for processing report document.")
    exit()

print("Download URL:", download_url)

# Step 3: Download and print the processing report
response = requests.get(download_url)
response.raise_for_status()

if doc_info.get("compressionAlgorithm") == "GZIP":
    # Decompress gzip content
    buf = io.BytesIO(response.content)
    with gzip.GzipFile(fileobj=buf) as f:
        decompressed_data = f.read()
    print("\n===== PROCESSING REPORT CONTENT =====")
    print(decompressed_data.decode('utf-8'))  # Assuming the report is UTF-8 encoded text
else:
    print("\n===== PROCESSING REPORT CONTENT =====")
    print(response.text)
