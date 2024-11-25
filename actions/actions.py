
from rasa_sdk import Action, Tracker
from typing import Any, Text, Dict, List
from OCR import ocr
from Layoutlm import layout
from calculator import update_excel_and_calculate
from rasa_sdk.events import FollowupAction
import re
import requests
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import UserUtteranceReverted
from rasa_sdk import Action
from rasa_sdk.events import SlotSet
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class ActionProcessImage(Action):
    def name(self) -> Text:
        return "process_image"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> List[Dict[Text, Any]]:
        # Lấy thông tin ảnh từ tin nhắn
        text = tracker.latest_message['text']
        print("Received text:", text)

        if text:
            try:
                if len(text) == 15:
                    url = "http://57.155.0.174:5000/update"
                    img_url= "http://57.155.0.174:5000"
                else:
                    url="https://api.telegram.org/bot7596431038:AAHrfaqqbBvSdTscaFJ8oXegD9v5iJLfPfI"
                    img_url="https://api.telegram.org/file/bot7596431038:AAHrfaqqbBvSdTscaFJ8oXegD9v5iJLfPfI"
                # Giả sử `file_id` được lưu trữ trực tiếp trong `text`
                file_id = text
                print('ok1')
                # Gọi API Telegram để lấy thông tin file
                response = requests.get(
                    f"{url}/getFile?file_id={file_id}"
                )
                print('ok2')
                file_info = response.json()

                # Kiểm tra phản hồi từ API Telegram
                print('ok3',file_info)
                if file_info.get('ok'):
                    file_path = file_info['result']['file_path']
                    image_url = f"{img_url}/{file_path}"

                    # Tải ảnh về hoặc thông báo thành công
                    dispatcher.utter_message(text="Đã nhận được ảnh! Cảm ơn bạn đã gửi.")
                    print('ok4',image_url)

                    # Tải ảnh về nếu cần xử lý
                    print(requests.get(image_url))
                    image_response = requests.get(image_url)
                    print('ok5')
                    if image_response.status_code == 200:
                        print('ok6')
                        # with open("received_image.jpg", 'wb') as f:
                        #     f.write(image_response.content)
                        # dispatcher.utter_message(text="Ảnh đã được tải về và lưu trữ.")
                        n=ocr(image_url)
                        if n==0:
                            dispatcher.utter_message(text="Có vẻ ảnh của bạn chưa đảm bảo chất lượng. Hãy tham khảo chất lượng ảnh tại đây.")
                        else:
                            dispatcher.utter_message(text="Ảnh đã được trích xuất, Đang phân tích...")

                            x, y = layout(n)
                            if x<y:
                                width=x
                                length=y
                            else:
                                width = y
                                length = x
                            width = int(width / 100) / 10
                            length = int(length / 100) / 10

                            area = width * length
                            dispatcher.utter_message(text=f"Chiều dài: {length}m, Chiều rộng: {width}m, Diện tích: {area}m²")
                            return [
                                SlotSet("width", width),
                                SlotSet("length", length),
                                SlotSet("area", area)
                            ]

                    else:
                        dispatcher.utter_message(text="Không thể tải ảnh về từ server.")

                    # Trả về sự kiện thành công
                    return []
                else:
                    dispatcher.utter_message(text="Không thể lấy ảnh. Vui lòng thử lại.")
            except Exception as e:
                dispatcher.utter_message(text=f"Đã xảy ra lỗi khi xử lý ảnh: {e}")
        else:
            dispatcher.utter_message(text="Không có ảnh nào được gửi. Vui lòng gửi lại.")

        # Trả về sự kiện nếu không có ảnh hoặc có lỗi
        return []




class ActionCalculatePrice(Action):
    def name(self) -> Text:
        return "calculate_price"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        width = tracker.get_slot("width")
        length = tracker.get_slot("length")
        area = tracker.get_slot("area")
        print(width,length)
        if width and length:
            width = width.replace("m", "")
            length = length.replace("m", "")
            print(width, length)
            price=update_excel_and_calculate(width, length)
            dispatcher.utter_message(text=f"Dưới đây là tính toán sơ bộ cho dự án của bạn bao gồm Chiều dài: {length}m, Chiều rộng: {width}m\n")
            for i in range(len(price)):
                stt=i+1
                text=price[i]
                dispatcher.utter_message(text=f"{stt}. {text}\n")

        else:
            user_message = tracker.latest_message.get("text")
            length = None
            width = None

            # Tìm chiều dài
            length_match = re.search(r"chiều dài\s*([0-9]+)\s*m?", user_message, re.IGNORECASE)
            if length_match:
                length = length_match.group(1)

            # Tìm chiều rộng
            width_match = re.search(r"chiều rộng\s*([0-9]+)\s*m?", user_message, re.IGNORECASE)
            if width_match:
                width = width_match.group(1)

            # Xử lý logic nếu tìm thấy chiều dài và chiều rộng
            if length and width:
                dispatcher.utter_message(text=f"Chiều dài: {length}m, Chiều rộng: {width}m. Đang tính giá...")
                price = update_excel_and_calculate(length, width)
                print(width, length)

                dispatcher.utter_message(text=f"Dưới đây là tính toán sơ bộ cho dự án của bạn.\n")
                for i in range(len(price)):
                    stt = i + 1
                    text = price[i]
                    dispatcher.utter_message(text=f"{stt}. {text}\n")
            else:
                dispatcher.utter_message(text="Không tìm thấy thông tin lưu trữ. Bạn có thể gửi tôi hình ảnh bảng vẽ hoặc chiều dài chiều rộng(đơn vị m) của bản dự án, tôi sẽ giúp bạn tính toán chi phí.s")

        return []


# actions.py
# actions.py




class ActionProcessFallback(Action):
    def name(self) -> str:
        return "process_fallback"

    def run(self, dispatcher, tracker, domain):
        # Lấy tin nhắn cuối cùng của người dùng
        modified_message = tracker.get_slot("modified_message")
        print(modified_message)
        if modified_message:
            user_message=modified_message
            prompt = (
                "Hãy xác định xem khách hàng hỏi gì. Nếu về sản phẩm thì tất cả sản phẩm khách hàng đang hỏi hiện trong kho đã hết, hãy xin lỗi khách hàng thật ngắn gọn. Còn nếu khách hàng hỏi cái khác cũng hãy trả lời ngắn gọn thôi. ")
        else:
            prompt = (
                "Bạn là một kỹ sư xây dựng. Hãy trả lời ngắn gọn câu hỏi sau đây của user ")
            user_message = tracker.latest_message.get('text')
        print(prompt)
        print(user_message)
        # Kiểm tra nếu không có tin nhắn để gửi đến Gemini
        if not user_message:
            dispatcher.utter_message("Không thể xử lý yêu cầu.")
            return [UserUtteranceReverted()]

        # API URL và Key cho Gemini
        GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=AIzaSyAU3sW3KSfsezm4lvO24AIcuePgLe529rE"
        headers = {"Content-Type": "application/json"}


        data = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{prompt}\nUser: {user_message}"}
                    ]
                }
            ]
        }

        try:
            # Gửi request đến API Gemini
            response = requests.post(GEMINI_API_URL, headers=headers, json=data)
            response_data = response.json()
            print(response)
            # Lấy nội dung phản hồi từ Gemini
            gemini_reply = response_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")

            # Kiểm tra nếu không có phản hồi hợp lệ
            if not gemini_reply:
                dispatcher.utter_message("Xin lỗi, không có phản hồi từ hệ thống.")
                return [UserUtteranceReverted()]

            # Trả lời người dùng với phản hồi từ Gemini
            dispatcher.utter_message(gemini_reply)

        except Exception as e:
            dispatcher.utter_message(f"Lỗi khi xử lý yêu cầu: {str(e)}")
            return [UserUtteranceReverted()]

        # Hoàn thành hành động mà không lưu trạng thái tin nhắn hiện tại
        return [UserUtteranceReverted()]






# Giả sử bạn có dữ liệu sản phẩm như sau:
product_data = {
    "gạch": {
        "type": "Gạch ceramic",
        "price": "50,000 VND",
        "details": "Gạch ceramic có kích thước 20x20 cm, màu sắc đa dạng.",
        "available": True,
        "size": "20x20 cm",
        "material": "Gạch ceramic",
        "usage": "Dùng cho các công trình xây dựng, lát nền.",
        "colors": ["Trắng", "Xám", "Be"]
    },
    "Thép loại II": {
        "type": "Thép",
        "price": "500,000 VND",
        "details": "Thép loại II, đường kính 10mm, dài 6m, khả năng chịu tải cao.",
        "available": True,
        "size": "10mm x 6m",
        "material": "Thép hợp kim",
        "usage": "Dùng trong kết cấu công trình xây dựng, chịu lực tốt.",
        "colors": ["Bạc", "Đen"],
        "load_capacity": "Chịu tải lên đến 5 tấn"
    },
    "xà gồ": {
        "type": "Xà gồ thép",
        "price": "150,000 VND",
        "details": "Xà gồ thép dài 3m, chịu lực tốt, dùng cho kết cấu mái.",
        "available": True,
        "size": "3m",
        "material": "Thép mạ kẽm",
        "usage": "Dùng cho kết cấu mái.",
        "load_capacity": "Chịu tải trọng lên đến 10 tấn"

    },
    "bàn học sinh": {
        "type": "Bàn học sinh",
        "price": "1 triệu VND",
        "details": "Bàn học sinh gỗ tự nhiên, thiết kế tiện dụng.",
        "available": True,
        "size": "120x60x75 cm",
        "material": "Gỗ tự nhiên",
        "usage": "Dùng cho học sinh, thiết kế hiện đại.",
        "colors": ["Gỗ tự nhiên", "Trắng"],
        "specifications": "Chân bàn gỗ, mặt bàn phủ lớp sơn chống thấm."
    },
    "bàn làm việc": {
        "type": "Bàn làm việc",
        "price": "2 triệu VND",
        "details": "Bàn làm việc gỗ công nghiệp, thiết kế hiện đại.",
        "available": True
    },
    "cửa sắt": {
        "type": "Cửa sắt",
        "price": "2 triệu VND",
        "details": "Cửa sắt chắc chắn, thiết kế đẹp.",
        "available": True
    },
    "ghế sofa": {
        "type": "Ghế sofa",
        "price": "4 triệu VND",
        "details": "Ghế sofa da cao cấp, thoải mái, sang trọng.",
        "available": True
    },
    "bồn cầu": {
        "type": "Bồn cầu",
        "price": "3 triệu VND",
        "details": "Bồn cầu cao cấp, tiết kiệm nước, dễ vệ sinh.",
        "available": True
    },
    "máy lạnh": {
        "type": "Máy lạnh",
        "price": "5 triệu VND",
        "details": "Máy lạnh tiết kiệm điện, làm lạnh nhanh.",
        "available": True,
        "size": "Inverter 12000 BTU",
        "power": "12000 BTU",
        "energy_efficiency": "A++",
        "usage": "Dùng cho phòng khách, phòng ngủ.",
        "colors": ["Trắng"],
        "specifications": "Tiết kiệm điện, làm lạnh nhanh."
    }
}



class ActionSearchProduct(Action):
    def name(self) -> str:
        return "action_search_product"

    def run(self, dispatcher, tracker, domain):
        # Lấy thông tin từ các slot
        product_name = tracker.get_slot("product_name")
        product_type = tracker.get_slot("product_type")
        price_range = tracker.get_slot("price_range")
        print(product_name)
        print(product_type)
        print(price_range)

        # Khởi tạo vectorizer

        if price_range:
            data={}
            for name, product in product_data.items():
                min_price, max_price = self.parse_price_range(price_range)
                price = self.extract_price(product["price"])
                print(min_price,price,max_price)
                if min_price <= price <= max_price:
                    data[name] = product
            print(data)
            if data != {}:
                result=self.type_name(product_name, product_type, data)
                print("oke1")
                if result:
                    dispatcher.utter_message(text="\n".join(result))
                    print("oke2")
                else:
                    print("oke3")

                    result=[]
                    for name, product in data.items():
                        result.append(
                            f"Sản phẩm {name}: {product['type']}, {product['price']}, {product['details']}"
                        )
                    dispatcher.utter_message(text="\n".join(result))
                    print("oke4")
            else:
                user_message = tracker.latest_message['text']
                modified_message =  user_message
                return [SlotSet("modified_message", modified_message), FollowupAction("process_fallback")]

        else:
            user_message = tracker.latest_message['text']
            modified_message=+user_message
            return [SlotSet("modified_message", modified_message),FollowupAction("process_fallback")]

        # else:
        #     if price_range:
        #         dispatcher.utter_message(text=f"Không tìm thấy sản phẩm {product_type} {product_name} có giá {price_range}.")
        #     elif product_name or product_type:
        #         dispatcher.utter_message(text=f"Không tìm thấy sản phẩm {product_type} {product_name}.")
        #     else:
        #         dispatcher.utter_message(text="Vui lòng cung cấp tên sản phẩm hoặc loại sản phẩm.")

        return [SlotSet("product_name", None),SlotSet("modified_message", None), SlotSet("product_type", None), SlotSet("price_range", None)]

    def parse_price_range(self, price_range):
        """Chuyển đổi giá trị price_range thành giá trị min và max"""
        # Giả sử price_range có dạng "2 triệu" hoặc "1 triệu đến 3 triệu"
        price_range = price_range.lower()
        prices = price_range.split(" đến ")
        # prices = price_range.split(" từ ")
        # prices = price_range.split(" - ")

        min_price = self.extract_price(prices[0])
        max_price = self.extract_price(prices[-1]) if len(prices) > 1 else min_price

        return min_price, max_price
    def type_name(self,product_name,product_type,product_data):

        vectorizer = TfidfVectorizer()

        # Lấy tất cả các mô tả sản phẩm từ product_data
        product_descriptions = [product["details"] for product in product_data.values()]

        # Tạo ma trận TF-IDF từ các mô tả sản phẩm
        tfidf_matrix = vectorizer.fit_transform(product_descriptions)

        # Tìm kiếm sản phẩm dựa trên tên hoặc loại
        if product_name or product_type:
            # Mảng chứa các tên sản phẩm để tìm kiếm
            search_queries = []
            if product_name:
                search_queries.append(product_name)
            if product_type:
                search_queries.append(product_type)

            # Tạo ma trận TF-IDF cho các câu truy vấn tìm kiếm
            query_matrix = vectorizer.transform(search_queries)

            # Tính độ tương đồng cosine giữa câu truy vấn và các mô tả sản phẩm
            similarities = cosine_similarity(query_matrix, tfidf_matrix)
            print(similarities)
            # Tìm kiếm sản phẩm có độ tương đồng cao nhất
            best_match_index = np.argmax(similarities, axis=1)
            print(best_match_index)
            # Trả về kết quả tìm kiếm
            results = []
            for idx in best_match_index:
                product = list(product_data.values())[idx]
                results.append(
                    f"Sản phẩm {list(product_data.keys())[idx]}: {product['type']}, {product['price']}, {product['details']}"
                )
            return results
            # Hiển thị kết quả
            # if results:
            #     dispatcher.utter_message(text="\n".join(results))
            # else:
            #     dispatcher.utter_message(text="Không tìm thấy sản phẩm phù hợp.")
    def extract_price(self, price_str):
        """Chuyển đổi giá thành giá trị số"""
        # Loại bỏ các ký tự không phải là số và các từ như "triệu", "VND", ...
        price_str = price_str.lower()
        price_str = price_str.replace("triệu", "").replace("vnd", "").replace(" ", "").strip()

        try:
            # Chuyển chuỗi còn lại thành số thực và nhân với 1 triệu (đồng)
            return float(price_str) * 1000000  # Convert triệu to đồng
        except ValueError:
            # Nếu có lỗi khi chuyển đổi (chẳng hạn như chuỗi rỗng hoặc không phải số), trả về 0
            return 0.0


class ActionProductDetails(Action):
    def name(self) -> str:
        return "action_product_info"

    def run(self, dispatcher, tracker, domain):
        # Lấy thông tin từ slot
        product_name = tracker.get_slot("product_name")

        # Kiểm tra nếu sản phẩm có trong dữ liệu
        if product_name in product_data:
            details = product_data[product_name]
            response = f"Sản phẩm {product_name}:\n"

            # Trả lời về thông số sản phẩm
            if "size" in details:
                response += f"Kích thước: {details['size']}\n"
            if "price" in details:
                response += f"Giá: {details['price']}\n"
            if "material" in details:
                response += f"Chất liệu: {details['material']}\n"
            if "usage" in details:
                response += f"Ứng dụng: {details['usage']}\n"
            if "colors" in details:
                response += f"Màu sắc: {', '.join(details['colors'])}\n"
            if "load_capacity" in details:
                response += f"Tải trọng: {details['load_capacity']}\n"
            if "specifications" in details:
                response += f"Thông số kỹ thuật: {details['specifications']}\n"

            dispatcher.utter_message(text=response)
        else:
            dispatcher.utter_message(text="Xin lỗi, tôi không có thông tin chi tiết về sản phẩm này.")

        return []