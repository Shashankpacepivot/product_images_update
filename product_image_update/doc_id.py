import requests
from access_token import get_access_token
import boto3
import time


# Your OAuth Access Token from SP-API
OAUTH_ACCESS_TOKEN = get_access_token()

# Endpoint
url = "https://sellingpartnerapi-eu.amazon.com/feeds/2021-06-30/documents"

# Request body specifying content type of the feed file you want to upload
payload = {
    "contentType": "application/json; charset=UTF-8"
}


# Headers with OAuth token + content type
headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "x-amz-access-token": OAUTH_ACCESS_TOKEN
}

# Send POST request to create feed document
response = requests.post(url, json=payload, headers=headers)
data = response.json()
print(data)
