import requests

def update_excel_and_calculate(width, length):
    # URL của Web App đã triển khai
    url = 'https://script.google.com/macros/s/AKfycbwL_bH3CAw5qMMs6G2LSJhvvIt_v-YHgM1xUTvhO3rWC0NMqounYw-2TXWw5l1P6DmU/exec'
    # Tham số width và length
    params = {
        'width': width,
        'length': length
    }

    # Gửi yêu cầu GET
    try:
        response = requests.get(url, params=params)

        if response.status_code == 200:
            result = response.json()
            print("Kết quả tính toán từ API:")
            print(result)
            return result

        else:
            print(f"Lỗi khi gọi API. Mã lỗi: {response.status_code}")
            print("Phản hồi lỗi từ API:", response.text)

    except Exception as e:
        print(f"Lỗi khi gửi yêu cầu: {e}")

update_excel_and_calculate(10,10)