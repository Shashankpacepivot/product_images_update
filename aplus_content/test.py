import mimetypes

file_path = r"C:\Users\WIN 10\Downloads\test.jpg"
content_type, _ = mimetypes.guess_type(file_path)

    # Fallback if unknown
if content_type is None:
    content_type = "application/octet-stream"

print(content_type)