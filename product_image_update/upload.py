import requests

upload_url = f"https://tortuga-prod-eu.s3-eu-west-1.amazonaws.com/362e68e7-3745-4813-996e-aea3631558d9.amzn1.tortuga.4.eu.T34ZNEK4XZZ9VD?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20250916T102311Z&X-Amz-SignedHeaders=content-type%3Bhost&X-Amz-Expires=300&X-Amz-Credential=AKIAX2ZVOZFBF3Q5DUG3%2F20250916%2Feu-west-1%2Fs3%2Faws4_request&X-Amz-Signature=75d0d7f3f10ac31ffce93fbc13fc33bef67bb4a728db87f96c251a2b6912d4fc"

with open('product_image.json', 'rb') as f:
    feed_data = f.read()

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