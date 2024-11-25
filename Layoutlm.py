
import requests
import json


def layout(n):
    url = "http://57.155.0.174:5000/process"  


    response = requests.post(url, json=n)

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



