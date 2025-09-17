import requests
from access_token import get_access_token
import boto3
import time
import os
from dotenv import load_dotenv
import mimetypes
import json 
import io
import gzip

load_dotenv()

#function to upload the image to S3 bucket
def upload_image_to_s3(file_path, content_type, s3_key=None):
    """
    Upload an image from the local device to an S3 bucket.
    
    :param file_path: Local path to the image
    :param s3_key: The name/key to assign in S3 (defaults to original file name)
    :return: URL of the uploaded image or None if failed
    """
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_DEFAULT_REGION")
        )
        print("✅ S3 client initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing S3 client: {e}")
        return None

    # Read bucket name from .env
    bucket_name = os.getenv("S3_BUCKET_NAME")
    if not bucket_name:
        print("❌ S3_BUCKET_NAME not found in environment")
        return None

    # Use original file name if no key provided
    if not s3_key:
        s3_key = os.path.basename(file_path)

    try:
        # Upload the file
        s3_client.upload_file(
            Filename=file_path,
            Bucket=bucket_name,
            Key=s3_key,
            ExtraArgs={'ACL': 'public-read', 'ContentType': content_type}  # adjust content type as needed
        )
        print(f"✅ Image uploaded to S3: {s3_key}")

        # Construct the image URL (public read only works if the bucket or object is public)
        region = os.getenv("AWS_DEFAULT_REGION")
        url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
        print(f"📸 Accessible at: {url}")
        return url
    
    except Exception as e:
        print(f"❌ Error uploading image: {e}")
        return None  
    

#function to get the product type
def get_product_type(seller_id, sku, access_token, marketplace_id="A21TJRUUN4KGV"):
    """Get current productType from listing using GET."""
    endpoint = "https://sellingpartnerapi-eu.amazon.com"
    path = f"/listings/2021-08-01/items/{seller_id}/{sku}"
    url = f"{endpoint}{path}?marketplaceIds={marketplace_id}"

    headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json',
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to get listing data: {response.status_code} - {response.text}")

    data = response.json()
    # ProductType is inside summaries array
    summaries = data.get("summaries", [])
    if not summaries or "productType" not in summaries[0]:
        raise ValueError("productType missing from listing summaries.")

    return summaries[0]["productType"]

#Fucntion to get the documnet id and the url to uload the feed json 
#note the url is active only for 5 minutes
def get_documnet_id_and_url(access_token):
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
        "x-amz-access-token": access_token
    }

    # Send POST request to create feed document
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    print(data)
    doc_id = data.get('documnet_id')
    upload_url = data.get('url')

    return doc_id, upload_url

#To get the place where the image to be uploaded
def get_image_location(image_loaction):
    loaction_map = {
        '1': 'MAIN',
        '2': 'PT01',
        '3': 'PT02',
        '4': 'PT03',
        '5': 'PT04',
        '6': 'PT05',
        '7': 'PT06',
        '8': 'PT07'
    }

    return loaction_map.get(image_loaction, 'MAIN')

#The feed json which is to be updated 
def create_feed(image_location, image_url, seller_id, sku, product_type, operation, marketplace_id):
    image_location = str(image_loc)
    image_url = str(image_url)
    image_loc = get_image_location(image_location)
    feed = {
    "header": {
        "version": "2.0",
        "sellerId": seller_id
    },
    "messages": [
        {
            "messageId": 1,
            "sku": sku,
            "operationType": operation,
            "productType": product_type,
            "images": [
                {
                "marketplaceId": marketplace_id,
                "images": [
                    {
                    "variant": image_loc,
                    "link": image_url
                    }
                ]
            }
            ]
        }
        ]
    }

    return feed

#function to upload the feed to the url 
#note the url is active only for 5 minutes
def upload_feed(upload_url, image_location, image_url, payload):
    upload_url = upload_url

    payload = payload

    feed_data = json.dumps(payload).encode('utf-8')

    upload_headers = {
        'Content-Type': 'application/json; charset=UTF-8'  # update content type here
    }

    response = requests.put(upload_url, data=feed_data, headers=upload_headers)
    print("Status Code:", response.status_code)
    print("Headers:", response.headers)
    if response.status_code == 200:
        print("Feed uploaded successfully!")
    else:
        print("Upload failed:", response.status_code, response.text)

#feed creation and checkind for the status of the feed 
def feed_creation(access_token, region, marketplace_id, doc_id): 
    feed_document_id = doc_id  # Document ID you uploaded earlier

    base_url = f"https://sellingpartnerapi-{region}.amazon.com"

    headers = {
        "x-amz-access-token": access_token,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Step 1: Create the feed
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

    # Step 2: Poll feed status
    get_feed_status_url = f"{base_url}/feeds/2021-06-30/feeds/{feed_id}"
    max_retries = 20
    retries = 0

    while retries < max_retries:
        status_response = requests.get(get_feed_status_url, headers=headers)
        status_response.raise_for_status()
        status_data = status_response.json()
        processing_status = status_data.get("processingStatus")
        print(f"Feed processing status: {processing_status}")

        if processing_status in ("DONE", "DONE_NO_DATA", "CANCELLED", "FATAL"):
            feed_status = status_data
            break

        retries += 1
        time.sleep(30)  # wait before polling again
    else:
        raise TimeoutError("Feed processing timed out.")

    # Step 3: Get processing report document ID
    processing_report_doc_id = feed_status.get("resultFeedDocumentId")
    if not processing_report_doc_id:
        raise ValueError("No processingReportDocumentId found. Feed might not have a processing report yet.")

    print("Processing report document ID:", processing_report_doc_id)

    # Step 4: Get document info to get pre-signed URL
    url_doc = f"{base_url}/feeds/2021-06-30/documents/{processing_report_doc_id}"
    response = requests.get(url_doc, headers=headers)
    response.raise_for_status()
    doc_info = response.json()

    print("Document info response:", doc_info)

    download_url = doc_info.get("url")
    if not download_url:
        raise ValueError("No URL found for processing report document.")

    print("Download URL:", download_url)

    # Step 5: Download and print the processing report
    response = requests.get(download_url)
    response.raise_for_status()

    if doc_info.get("compressionAlgorithm") == "GZIP":
        buf = io.BytesIO(response.content)
        with gzip.GzipFile(fileobj=buf) as f:
            decompressed_data = f.read()
        report_text = decompressed_data.decode('utf-8')
    else:
        report_text = response.text

    print("\n===== PROCESSING REPORT CONTENT =====")
    print(report_text)


if __name__ == "__main__":
    marketplace_id ="A21TJRUUN4KGV"
    region = 'eu'
    seller_id = os.getenv("seller_id")
    sku = "0A-SLD7-P9Y1"
    operation = "PARTIAL_UPDATE"
    file_path = "images/photo.png"
    content_type, _ = mimetypes.guess_type(file_path)

    # Fallback if unknown
    if content_type is None:
        content_type = "application/octet-stream"
    
    image_location = input("Please tell the postion where you want the image to be, if Main then select 1, else 2 to 8 :")
    image_url = upload_image_to_s3(file_path, content_type)
    access_token = get_access_token()
    product_type = get_product_type(seller_id, sku, access_token, marketplace_id)
    payload = create_feed(image_location, image_url, seller_id, sku, product_type, operation, marketplace_id)
    print("the feed that is being uploaded", payload)
    doc_id, upload_url = get_documnet_id_and_url(access_token)
    upload_feed(upload_url, image_location, image_url, payload)
    feed_creation(access_token, region, marketplace_id, doc_id)



