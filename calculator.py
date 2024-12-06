import requests

def update_excel_and_calculate(category, width,length,h):
    # URL của Web App đã triển khai
    cate=category
    if cate=="nha xuong":
        category=1
    elif cate=="nha thep tien che" or cate=="nha thep":
        category=2
    else:
        category=3

    # url = 'https://script.google.com/macros/s/AKfycbwL_bH3CAw5qMMs6G2LSJhvvIt_v-YHgM1xUTvhO3rWC0NMqounYw-2TXWw5l1P6DmU/exec'
        # Tham số width và length
    url='https://script.google.com/macros/s/AKfycbxishVM1zzUIechwKKEX4kDju0mb9xGG4tLx0SD41M1SMOPPGFHb-Cup9RMt7H3XQUT/exec'
    params = {
            'category':category,
            'width': width,
            'length': length,
            'h':h
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

