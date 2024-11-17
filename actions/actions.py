
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Text, Dict, List
import requests
from OCR import ocr
from Layoutlm import layout
from rasa_sdk.events import SlotSet

class ActionProcessImage(Action):
    def name(self) -> Text:
        return "process_image"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> List[Dict[Text, Any]]:
        # Lấy thông tin ảnh từ tin nhắn
        text = tracker.latest_message['text']
        print("Received text:", text)

        if text:
            try:
                # Giả sử `file_id` được lưu trữ trực tiếp trong `text`
                file_id = text
                print('ok1')
                # Gọi API Telegram để lấy thông tin file
                response = requests.get(
                    f"https://api.telegram.org/bot7596431038:AAHrfaqqbBvSdTscaFJ8oXegD9v5iJLfPfI/getFile?file_id={file_id}"
                )
                print('ok2')
                file_info = response.json()

                # Kiểm tra phản hồi từ API Telegram
                print('ok3')
                if file_info.get('ok'):
                    file_path = file_info['result']['file_path']
                    image_url = f"https://api.telegram.org/file/bot7596431038:AAHrfaqqbBvSdTscaFJ8oXegD9v5iJLfPfI/{file_path}"

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

                            width, length = layout(n)

                            area = width * length
                            dispatcher.utter_message(text=f"Chiều dài: {length}m, Chiều rộng: {width}m, Diện tích: {area}m²")
                            return [
                                SlotSet("width", width),
                                SlotSet("length", length),
                                SlotSet("area", area)
                            ]

                    else:
                        dispatcher.utter_message(text="Không thể tải ảnh về từ server Telegram.")

                    # Trả về sự kiện thành công
                    return []
                else:
                    dispatcher.utter_message(text="Không thể lấy ảnh từ Telegram. Vui lòng thử lại.")
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
        thép=area*1.5
        gạch=area*1.6
        xi_măng=area*2
        đá=area*1.2
        if width and length and area:
            dispatcher.utter_message(
                text=f"Với các thông số kích thước: {length}m x chiều rộng {width}m tôi có thể ước tính giá tiền của công trình này nhu sau: \n"
                     f"Thép: {thép} VND.\n"
                     f"Gạch: {gạch} VND.\n"
                     f"Xi măng: {xi_măng} VND.\n"
                     f"Đá: {đá} VND.\n"
                     f"Tổng cộng:{thép+gạch+xi_măng+đá} VND. Đây chỉ là ước tính sơ bộ, bạn có thể liên hệ với chúng tôi qua số điện thoại 012345678 để được tư vấn kỹ hơn. Ngoài ra bạn cũng có thể tham khảo các loại chất liệu khác nhau cho công trình của bạn.")
        else:
            dispatcher.utter_message(text="Không tìm thấy thông tin lưu trữ.")

        return []


# actions.py
# actions.py

import requests
from rasa_sdk import Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import UserUtteranceReverted


class ActionProcessFallback(Action):
    def name(self) -> str:
        return "process_fallback"

    def run(self, dispatcher, tracker, domain):
        # Lấy tin nhắn cuối cùng của người dùng
        user_message = tracker.latest_message.get('text')

        # Kiểm tra nếu không có tin nhắn để gửi đến Gemini
        if not user_message:
            dispatcher.utter_message("Không thể xử lý yêu cầu.")
            return [UserUtteranceReverted()]

        # API URL và Key cho Gemini
        GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=AIzaSyAU3sW3KSfsezm4lvO24AIcuePgLe529rE"
        headers = {"Content-Type": "application/json"}
        prompt = (
            "Bạn là một kỹ sư xây dựng. Hãy trả lời ngắn gọn câu hỏi sau đây của user "
        )
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


from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

PRODUCTS = [
    {"name": "Gạch", "type": "gạch", "price": 2000000, "size": "120x60cm"},
    {"name": "Thép loại I", "type": "thép", "price": 1500000, "size": "N/A"},
    {"name": "Xà gồ gỗ", "type": "xà gồ", "price": 5000000, "size": "200x100x50cm"},
    {"name": "Thép loại II", "type": "thép", "price": 3000000, "size": "150x70x30cm"},
]

from rasa_sdk import Action
from rasa_sdk.events import SlotSet

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

        # Xử lý tìm kiếm theo các tiêu chí: product_name, product_type, và price_range
        results = []

        # Tìm kiếm sản phẩm theo tên
        if product_name:
            if product_name in product_data:
                product = product_data[product_name]
                if price_range:
                    print("ok2",price_range)

                    # min_price, max_price = self.parse_price_range(price_range)
                    # price = self.extract_price(product["price"])
                    # if min_price <= price <= max_price:
                    results.append(
                            f"Sản phẩm {product_name}: {product['type']}, {product['price']}, {product['details']}")
                else:
                    print("ok1")

                    results.append(
                        f"Sản phẩm {product_name}: {product['type']}, {product['price']}, {product['details']}")

        # Tìm kiếm sản phẩm theo loại (product_type) và price_range
        elif product_type:
            for name, product in product_data.items():
                if product_type in product["type"]:
                    if price_range:
                        min_price, max_price = self.parse_price_range(price_range)
                        price = self.extract_price(product["price"])
                        if min_price <= price <= max_price:
                            results.append(
                                f"Sản phẩm {name}: {product['type']}, {product['price']}, {product['details']}")
                    else:
                        results.append(f"Sản phẩm {name}: {product['type']}, {product['price']}, {product['details']}")

        # Trả lời người dùng
        print("ok", results)

        if results:
            dispatcher.utter_message(text="\n".join(results))
        else:
            dispatcher.utter_message(text=f"Không tìm thấy sản phẩm phù hợp với yêu cầu của bạn.{product_name}")

        return []

    def parse_price_range(self, price_range):
        """Chuyển đổi giá trị price_range thành giá trị min và max"""
        # Giả sử price_range có dạng "2 triệu" hoặc "1 triệu đến 3 triệu"
        price_range = price_range.lower()
        prices = price_range.split(" đến ")

        min_price = self.extract_price(prices[0])
        max_price = self.extract_price(prices[-1]) if len(prices) > 1 else min_price

        return min_price, max_price

    def extract_price(self, price_str):
        """Chuyển đổi giá thành giá trị số"""
        # Loại bỏ các ký tự không phải là số và các từ như "triệu", "VND", ...
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