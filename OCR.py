
import os
import requests
import sys
sys.path.append('code')
from main import main

def ocr(image_url):
    # Define the URL of the image
    # image_url = "https://api.telegram.org/file/bot7596431038:AAHrfaqqbBvSdTscaFJ8oXegD9v5iJLfPfI/photos/file_8.jpg"
    file_name = os.path.basename(image_url)
    response = requests.get(image_url)
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Content-Type: {response.headers.get('Content-Type')}")

    # Save the image to a file for debugging
    if response.status_code == 200:
        print(f"Successfully fetched the image: {file_name}")

        # Lưu ảnh với tên đúng
        with open(file_name, "wb") as f:
            f.write(response.content)
        print(f"Image saved as '{file_name}'.")
    else:
        print(f"Failed to fetch the image. Status code: {response.status_code}")
    n = main(file_name,image_url)
    print("cc",n)
    os.remove(file_name)

    if n==[] or n is None:
        print(f"Image '{file_name}' has been deleted.")

        return 0
    else:
        return n
