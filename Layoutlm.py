import requests
import json


def layout(user_id, file_link):
    url = "https://53a1-203-205-34-155.ngrok-free.app/process"

    # Dữ liệu gửi đến backend
    payload = {
        "user_id": user_id,
        "file": file_link
    }

    try:
        # Gửi yêu cầu POST tới backend
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            # Kiểm tra loại phản hồi từ backend
            if 'x' in data and 'y' in data and 'rag' in data:
                x, y = data['x'], data['y']
                if x == 0 and y == 0:
                    if data['rag'] is True:
                        return 1
                    elif data['rag'] is False:
                        return 0
                    return []
                else:
                    return [x,y]

            else:
                print(f"[User {user_id}] Phản hồi không rõ ràng từ backend: {data}")
        else:
            print(f"[User {user_id}] Đã xảy ra lỗi từ server: {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"[User {user_id}] Lỗi kết nối tới server:", e)


