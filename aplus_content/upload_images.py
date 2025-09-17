import requests
import json
import os
import hashlib
from typing import Dict, List, Optional, Tuple
import datetime
import mimetypes
from access_token import get_access_token

image_path_2 = "test.jpg"

"""
AMAZON A+ CONTENT UPLOAD MODULE - TESTING VERSION
================================================

⚠️ IMPORTANT NOTES:
- This module is FOR TESTING PURPOSES ONLY
- Contains HARDCODED values that need to be parameterized for production
- Many variables in functions are redundant and need cleanup

📋 PROCESS OVERVIEW:
This module implements Amazon's official A+ Content upload process using SP-API.
Complete workflow orchestrated by `complete_aplus_upload_official()` function.

🔄 7-STEP PROCESS:
1. Image Upload to S3 (using upload_image_to_s3 utility)
2. Content Validation (validate_content_document)
3. Content Document Creation (create_content_document_official)
4. ASIN Association (add_asins_to_content)
5. Approval Submission (submit_for_approval)
6. Status Monitoring (get_content_status_official)
7. Final Review (7-14 business days)

🔧 HARDCODED TEST VALUES (NEED TO BE PARAMETERIZED):
- ACCESS_TOKEN: "your_sp_api_access_token"
- MARKETPLACE_ID: "A21TJRUUN4KGV" (India)
- TEST_ASIN: "B09NP5DN4P"
- IMAGE_PATH: "/home/mizutoocha/Work/repo/ecomB/backend-mvp/static/temp/6057529352549158114.jpg"
- REGION: "eu" (Europe)
- CONTENT_TYPE: "STANDARD_HEADER_IMAGE_TEXT"
- LOCALE: "en-IN" / "en-US" (inconsistent usage)

📊 API ENDPOINTS USED:
- POST /aplus/2020-11-01/contentAsinValidations (Validation)
- POST /aplus/2020-11-01/contentDocuments (Creation)
- POST /aplus/2020-11-01/contentDocuments/{key}/asins (ASIN Association)
- POST /aplus/2020-11-01/contentDocuments/{key}/approvalSubmissions (Approval)
- GET /aplus/2020-11-01/contentDocuments/{key} (Status Check)

💡 USAGE:
Main function: complete_aplus_upload_official()
Returns: Dict with contentReferenceKey, status, and process results
"""
def create_upload_destination(image_path: str, access_token: str,  
                              region: str = "eu", marketplace_id: str = "A21TJRUUN4KGV") -> Tuple[str, str, Dict]:
    """
    Step 3b: Create upload destinations for images using Uploads API v2020-11-01
    """
    import base64

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found at: {image_path}")
    
    content_type, _ = mimetypes.guess_type(image_path)
    content_type = content_type or "application/octet-stream"

    with open(image_path, 'rb') as f:
        content_bytes = f.read()
        content_md5 = base64.b64encode(hashlib.md5(content_bytes).digest()).decode('utf-8')

    url = f"https://sellingpartnerapi-{region}.amazon.com/uploads/2020-11-01/uploadDestinations/aplus/2020-11-01/contentDocuments?marketplaceIds={marketplace_id}"

    headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json'
    }

    payload = {
        "contentMd5": content_md5,
        "contentType": content_type
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        print(f"❌ Failed to create upload destination: {response.status_code} - {response.text}")
        return None, None, None

    result = response.json()
    payload = result.get('payload', {})

    upload_destination_id = payload.get('uploadDestinationId')
    upload_url = payload.get('url')
    upload_headers = {header['name']: header['value'] for header in payload.get('headers', [])}

    print(f"✅ Upload destination created.")
    print(f"Upload Destination ID: {upload_destination_id}")

    return upload_destination_id, upload_url, upload_headers

def upload_image_to_s3(image_path: str, upload_url: str, form_fields: dict) -> bool:
    """
    Step 3c: Upload image to S3 using signed POST form fields
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    try:
        with open(image_path, 'rb') as image_file:
            files = {
                'file': (os.path.basename(image_path), image_file)
            }

            response = requests.post(upload_url, data=form_fields, files=files)

            if response.status_code in [200, 204]:
                print("✅ Image uploaded to S3 successfully")
                return True
            else:
                print(f"❌ S3 upload failed with status: {response.status_code}")
                print(f"Response: {response.text}")
                return False

    except Exception as e:
        print(f"❌ Exception during upload: {e}")
        return False
   

def validate_content_document_ckeck_for_fixes(access_token: str, upload_destination_id: str, marketplace_id: str,
                            doc_name:str, locale: str, headline_value: str, alt_text:str, body_text:str,
                            asin_list: list) -> Dict:
    """
    Step 3e: Create the actual content document
    
    Args:
        access_token: SP-API access token
        content_document: The validated content document JSON
        region: API region
        
    Returns:
        Dict with contentReferenceKey
    """
    asins = ",".join(asin_list)
    length = len(headline_value)
    url = f"https://sellingpartnerapi-eu.amazon.com/aplus/2020-11-01/contentDocuments?marketplaceId={marketplace_id}"
    
    headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json',
        "accept": "application/json",
    }

    payload = {
        "contentDocument": {
            "name": doc_name,
            "locale": locale,
            "contentType": "EBC",
            "contentModuleList": [
                {
                "contentModuleType": "STANDARD_HEADER_IMAGE_TEXT",
                "standardHeaderImageText": {
                    "headline": {
                        "value": headline_value,
                        "decoratorSet": [
                            {
                                "offset": 0,
                                "length": length,
                                "type": "STYLE_BOLD",
                                "depth": 1
                            }
                        ]
                    },
                    "block": {
                        "image": {
                            "imageCropSpecification": {
                                "size": {
                                    "width": {
                                        "value": 970,  
                                        "units": "pixels"
                                    },
                                    "height": {
                                        "value": 600, 
                                        "units": "pixels"
                                    }
                                }
                            },
                            "uploadDestinationId": upload_destination_id,
                            "altText": alt_text
                        },
                        "body": {
                            "textList": [
                                {
                                    "value": body_text,
                                    "decoratorSet": [
                                        {
                                            "type": "STYLE_BOLD",
                                            "offset": 0,
                                            "length": 0,
                                            "depth": 1
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                }
            }
        ]
    }}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Content document created successfully")
        print(f"Content Reference Key: {result.get('contentReferenceKey')}")
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to create content document: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        raise


def create_content_document(access_token: str, upload_destination_id: str, marketplace_id: str,
                            doc_name:str, locale: str, headline_value: str, alt_text:str, body_text:str) -> Dict:
    """
    Step 3e: Create the actual content document
    
    Args:
        access_token: SP-API access token
        content_document: The validated content document JSON
        region: API region
        
    Returns:
        Dict with contentReferenceKey
    """
    length = len(headline_value)
    url = f"https://sellingpartnerapi-eu.amazon.com/aplus/2020-11-01/contentDocuments?marketplaceId={marketplace_id}"
    
    headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json',
        "accept": "application/json",
    }

    payload = {
        "contentDocument": {
            "name": doc_name,
            "locale": locale,
            "contentType": "EBC",
            "contentModuleList": [
                {
                "contentModuleType": "STANDARD_HEADER_IMAGE_TEXT",
                "standardHeaderImageText": {
                    "headline": {
                        "value": headline_value,
                        "decoratorSet": [
                            {
                                "offset": 0,
                                "length": length,
                                "type": "STYLE_BOLD",
                                "depth": 1
                            }
                        ]
                    },
                    "block": {
                        "image": {
                            "imageCropSpecification": {
                                "size": {
                                    "width": {
                                        "value": 970,  
                                        "units": "pixels"
                                    },
                                    "height": {
                                        "value": 600, 
                                        "units": "pixels"
                                    }
                                }
                            },
                            "uploadDestinationId": upload_destination_id,
                            "altText": alt_text
                        },
                        "body": {
                            "textList": [
                                {
                                    "value": body_text,
                                    "decoratorSet": [
                                        {
                                            "type": "STYLE_BOLD",
                                            "offset": 0,
                                            "length": 0,
                                            "depth": 1
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                }
            }
        ]
    }}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        print(result)
        ref_key = result.get('contentReferenceKey')
        
        print(f"✅ Content document created successfully")
        print(f"Content Reference Key: {ref_key}")
        return ref_key
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to create content document: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        raise

def add_asins_to_content_to_re_ckeck(access_token: str, content_reference_key: str, marketplace_id: str, asins: list) -> Dict:
    """
    Step 3f: Add ASINs to the content document
    
    Args:
        access_token: SP-API access token
        content_reference_key: Content reference key from create_content_document_official
        asin_list: List of ASINs to associate
        region: API region
        
    Returns:
        Dict with response data
    """
    url = f"https://sellingpartnerapi-eu.amazon.com/aplus/2020-11-01/contentDocuments/{content_reference_key}/asins?marketplaceId={marketplace_id}"
    
    headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json'
    }

    payload = {"asinSet": asins}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json() if response.content else {"status": "success"}
        
        print(f"✅ ASINs added to content document")
        print(result)
        #return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to add ASINs to content: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        raise

def get_content_status_official(access_token: str, content_reference_key: str, region: str = "na") -> Dict:
    """
    Check content document approval status
    Note: Amazon recommends checking no more than once per hour
    
    Args:
        access_token: SP-API access token
        content_reference_key: Content reference key
        region: API region
        
    Returns:
        Dict with status information
    """
    url = f"https://sellingpartnerapi-{region}.amazon.com/aplus/2020-11-01/contentDocuments/{content_reference_key}?includedDataSet=METADATA"
    
    headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        print(result)
        
        content_doc = result.get('contentDocument', {})
        status = content_doc.get('contentStatus', 'UNKNOWN')
        
        print(f"📊 Content Status: {status}")
        
        status_messages = {
            'APPROVED': '✅ Content is approved and published to ASINs',
            'REJECTED': '❌ Content was rejected - check rejection reasons',
            'DRAFT': '📝 Content is in draft - not yet submitted',
            'SUBMITTED': '⏳ Content is under review - wait minimum 1 hour before checking again'
        }
        
        print(status_messages.get(status, f"Status: {status}"))
        
        return {
            'success': True,
            'status': status,
            'data': result
        }
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to get content status: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        raise

if __name__ == "__main__":
    file_path = r"/absolute/path/to/Image1.jpeg"  # replace with actual path
    access_token = get_access_token()  # implement this to get valid SP-API token
    region = 'eu'
    marketplace_id = "A21TJRUUN4KGV"
    doc_name = "First one to create"
    locale = "en-IN"
    headline_value = "Experience Superior Sound Quality"
    alt_text = "Premium wireless headphones with noise cancellation"
    body_text = "Advanced Noise Cancellation Technology delivers crystal-clear audio experience."
    asin_list = ["B01234567890", "B09876543210"]

    upload_destination_id, upload_url, upload_headers = create_upload_destination(file_path, access_token, region, marketplace_id)

    if upload_destination_id and upload_url:
        check_upload = upload_image_to_s3(file_path, upload_url, upload_headers)
    else:
        print("❌ Upload destination creation failed.")
        check_upload = False

    validate_content_document_ckeck_for_fixes(access_token, upload_destination_id, marketplace_id, doc_name, locale,
                                           headline_value, alt_text, body_text, asin_list)
    

    ref_key = create_content_document(access_token, upload_destination_id, marketplace_id, doc_name, locale, headline_value, alt_text, body_text)

    add_asins_to_content_to_re_ckeck(access_token, ref_key, marketplace_id, asin_list)

    get_content_status_official(access_token, ref_key, region)

    
