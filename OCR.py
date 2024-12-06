#
# import os
# import requests
# import sys
# sys.path.append('code')
# from main import main
# from PyPDF2 import PdfReader
# from pdf2image import convert_from_path  # Thêm thư viện pdf2image
# from mimetypes import guess_type
#
# def extract_text_from_pdf(pdf_path):
#     reader = PdfReader(pdf_path)
#     full_text = ""
#     for page in reader.pages:
#         full_text += page.extract_text()
#     return full_text
#
# def convert_pdf_to_image(pdf_path, page_num=0):
#     images = convert_from_path(pdf_path, first_page=page_num+1, last_page=page_num+1)
#     image_path = pdf_path.replace('.pdf', '_page_1.jpg')
#     # Lưu hình ảnh của trang đầu tiên
#     images[0].save(image_path, 'JPEG')
#     print(f"First page of PDF saved as image: {image_path}")
#     return image_path
#
# def ocr(image_url):
#     # Define the URL of the image
#     # image_url = "https://api.telegram.org/file/bot7596431038:AAHrfaqqbBvSdTscaFJ8oXegD9v5iJLfPfI/photos/file_8.jpg"
#     file_name = os.path.basename(image_url)
#     response = requests.get(image_url)
#     print(f"Response Status Code: {response.status_code}")
#     print(f"Response Content-Type: {response.headers.get('Content-Type')}")
#
#     # Save the image to a file for debugging
#     if response.status_code == 200:
#         print(f"Successfully fetched the image: {file_name}")
#
#         # Lưu ảnh với tên đúng
#         with open(file_name, "wb") as f:
#             f.write(response.content)
#         print(f"Image saved as '{file_name}'.")
#     else:
#         print(f"Failed to fetch the image. Status code: {response.status_code}")
#     content_type, encoding = guess_type(file_name)
#     if content_type == 'application/pdf' or file_name.endswith('.pdf'):
#         print("This is a PDF file.")
#         # Chuyển trang đầu PDF thành hình ảnh
#         file_name = convert_pdf_to_image(file_name)
#     n = main(file_name,image_url)
#     print("cc",n)
#     text = extract_text_from_pdf(file_name)
#     os.remove(file_name)
#
#     if n==[] or n is None:
#         print(f"Image '{file_name}' has been deleted.")
#         print(text)
#         return 0
#     else:
#         return n
