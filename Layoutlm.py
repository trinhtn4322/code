# def layout(n, image_url):
#     x=5
#     y=10
#     return x,y
#

import requests
import json


def layout(n):
    url = "http://57.155.0.174:5000/process"  # Thay URL server thực tế vào đây

    # Định dạng dữ liệu cần gửi
    # payload = {
    #     'n': n,  # Đảm bảo rằng `n` là dạng JSON hoặc dữ liệu tương thích
    #     'image_url': image_url
    # }

    # Gửi yêu cầu POST lên server
    response = requests.post(url, json=n)

    # Kiểm tra kết quả trả về
    if response.status_code == 200:
        data = response.json()
        print("okeeeee")
        x = data.get('x')
        y = data.get('y')
        print(f"Nhận được từ server: x = {x}, y = {y}")
        return x, y
    else:
        print("Lỗi khi gửi yêu cầu lên server:", response.status_code)
        return None


# Giả sử bạn đã có file JSON và image URL
# n_data = {"sample_key": "sample_value"}  # Thay thế bằng dữ liệu JSON thực tế
# image_url = "http://example.com/sample_image.jpg"  # URL của ảnh
#
# # Gọi hàm
# x, y = send_to_server(n_data, image_url)
