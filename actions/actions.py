import json
import unicodedata
from rasa_sdk.forms import FormValidationAction
import sqlite3
from rasa_sdk import Action, Tracker
from typing import Any, Text, Dict, List
# from OCR import ocr
from Layoutlm import layout
from calculator import update_excel_and_calculate
import re
import requests
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import UserUtteranceReverted
from rasa_sdk import Action
# ----------------
import sqlite3

def check_value_exists(user_id, field, value):
    """
    Kiểm tra xem giá trị (value) của một trường (field) có tồn tại cho user_id trong bảng slot_info không.
    """
    conn = sqlite3.connect('slots.db')
    cursor = conn.cursor()

    # Dựng câu truy vấn động dựa trên tên trường, giá trị và user_id
    query = f"SELECT COUNT(1) FROM slot_info WHERE user_id = ? AND {field} = ?"
    cursor.execute(query, (user_id, value))
    result = cursor.fetchone()

    conn.close()

    # Nếu kết quả > 0, nghĩa là giá trị đã tồn tại cho user_id đó
    if result[0] > 0:
        print(f"Giá trị '{value}' đã tồn tại trong trường '{field}' cho user_id '{user_id}'.")
        return True
    else:
        print(f"Giá trị '{value}' chưa tồn tại trong trường '{field}' cho user_id '{user_id}'.")
        return False


def gemini(prompt):

    # API URL và Key cho Gemini
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=AIzaSyBGVjVxovvjuG5Tko6kyufdevzykXVVNac"
    headers = {"Content-Type": "application/json"}

    data = {
        "contents": [
            {
                "parts": [
                    {"text": f"{prompt}"}
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

        # updated_text = updated_text + ":" + gemini_reply
        if not gemini_reply:
            dispatcher.utter_message("Xin lỗi, không có phản hồi từ hệ thống.")
            return gemini_reply
        else:
            try:
                input_text = gemini_reply.replace("```json", "").replace("```", "").strip()
                json_object = json.loads(input_text)
                if json_object:
                    return json_object
            except ValueError as e:
                return gemini_reply
    except ValueError as e:
        return None
def normalize_text( text: str) -> str:
    """
    Chuyển văn bản thành chữ thường và bỏ dấu.
    """
    text = text.lower()
    text = unicodedata.normalize('NFD', text)
    text = re.sub(r'[\u0300-\u036f]', '', text)
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text

def save_to_db(user_id, column, value):
    """
    Thêm hoặc cập nhật thông tin trong bảng slot_info dựa trên user_id.

    Args:
    - user_id (str): ID của người dùng, là khóa chính.
    - column (str): Tên cột muốn cập nhật.
    - value (str): Giá trị mới của cột.
    """
    conn = sqlite3.connect('slots.db')
    cursor = conn.cursor()

    # Kiểm tra nếu user_id đã tồn tại trong bảng
    cursor.execute("SELECT 1 FROM slot_info WHERE user_id = ?", (user_id,))
    exists = cursor.fetchone()

    if exists:
        # Nếu user_id đã tồn tại, cập nhật giá trị của cột được chỉ định
        cursor.execute(f"UPDATE slot_info SET {column} = ? WHERE user_id = ?", (value, user_id))
        print(f"Cập nhật: user_id {user_id}, {column} = {value}")
    else:
        # Nếu user_id chưa tồn tại, chèn một dòng mới với user_id và giá trị của cột được chỉ định
        cursor.execute(f"INSERT INTO slot_info (user_id, {column}) VALUES (?, ?)", (user_id, value))
        print(f"Thêm mới: user_id {user_id}, {column} = {value}")

    conn.commit()
    conn.close()

def delete_all_rows():
    """
    Xóa tất cả các dòng trong bảng slot_info.
    """
    conn = sqlite3.connect('slots.db')
    cursor = conn.cursor()

    # Xóa tất cả các dòng trong bảng slot_info
    cursor.execute("DELETE FROM slot_info")

    # Commit thay đổi và đóng kết nối
    conn.commit()
    conn.close()

def get_first_row_column_values( user_id):

    # Kết nối tới cơ sở dữ liệu
    conn = sqlite3.connect('slots.db')
    cursor = conn.cursor()

    try:
        # Lấy danh sách tên cột trong bảng
        cursor.execute('PRAGMA table_info(slot_info);')
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]

        # Truy vấn để lấy dòng dựa trên user_id
        cursor.execute('SELECT * FROM slot_info WHERE user_id = ?;', (user_id,))
        row = cursor.fetchone()

        # Dictionary lưu trữ tên cột và giá trị tương ứng
        column_values = {}

        if row:
            for i, value in enumerate(row):
                column_values[column_names[i]] = value

        return column_values if row else {'type': None, 'length': None, 'width': None, 'height': None, 'weight': None, 'address': None}
    finally:
        # Đóng kết nối
        conn.close()


def ask_next_slot(slot_name: Text, dispatcher: CollectingDispatcher):

    questions = {
        "type": "Bạn có thể cho tôi biết loại công trình bạn dự định xây dựng không?",
        "length": "Bạn dự tính sẽ xây dựng công trình với chiều dài của là bao nhiêu?(đơn vị m)",
        "width": "Chiều rộng công trình là bao nhiêu vậy?(đơn vị m)",
        "height": "Để tư vấn rõ hơn xin vui lòng cho biết, chiều cao công trình là bao nhiêu?(đơn vị tầng)",
        "address": "Công trình này sẽ được xây dựng ở địa chỉ nào, hiện nay công ty chúng tôi chỉ làm việc tại Việt Nam?",
        "weight": "Tải trọng của công trình này dự tính là bao nhiêu(tấn)?",
    }
    if slot_name is not None:
        question = questions.get(slot_name, f"Vui lòng cung cấp thông tin cho {slot_name}.")
        dispatcher.utter_message(text=question)
# -----------------
class ActionProcessImage(Action):
    def name(self) -> Text:
        return "process_image"


    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> List[Dict[Text, Any]]:
        # Lấy thông tin ảnh từ tin nhắn
        text = tracker.latest_message['text']
        user_id = tracker.sender_id
        print("Received text:", text)

        if text:
            try:
                if len(text) == 30:
                    url = "http://57.155.0.174:5000/upload"
                    img_url= "http://57.155.0.174:5000"
                else:
                    url="https://api.telegram.org/bot7596431038:AAHrfaqqbBvSdTscaFJ8oXegD9v5iJLfPfI"
                    img_url="https://api.telegram.org/file/bot7596431038:AAHrfaqqbBvSdTscaFJ8oXegD9v5iJLfPfI"
                # Giả sử `file_id` được lưu trữ trực tiếp trong `text`
                file_id = text
                # Gọi API Telegram để lấy thông tin file
                response = requests.get(
                    f"{url}/getFile?file_id={file_id}"
                )
                file_info = response.json()

                # Kiểm tra phản hồi từ API Telegram
                if file_info.get('ok'):
                    file_path = file_info['result']['file_path']
                    image_url = f"{img_url}/{file_path}"

                    # Tải ảnh về hoặc thông báo thành công
                    dispatcher.utter_message(text="Đã nhận được ảnh! Cảm ơn bạn đã gửi.")

                    # Tải ảnh về nếu cần xử lý
                    image_response = requests.get(image_url)
                    if image_response.status_code == 200:
                 
                        n = layout(user_id, image_url)
                        if n == 0:
                            dispatcher.utter_message(text="Có vẻ ảnh hoặc tài liệu của bạn chưa đảm bảo chất lượng. Hãy tham khảo chất lượng ảnh tại đây.")
                            active = tracker.get_slot("mode")

                            if active=="consult":
                                return [SlotSet("mode", "consult"),FollowupAction("send_consult")]
                            elif active=="calculate":
                                return [SlotSet("mode", "calculate"),FollowupAction("calculate_price")]
                        elif n==1:
                            dispatcher.utter_message(text="Tôi đã trích xuất thành công tài liệu của bạn. Bạn có thắc mắc gì về tài liệu này nào")
                        elif n == []:
                            dispatcher.utter_message(text="Có vẻ ảnh của bạn chưa đảm bảo chất lượng. Hãy tham khảo chất lượng ảnh tại đây.")
                        else:
                            x=n[0]
                            y=n[1]
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
                            active = tracker.get_slot("mode")
                            user_id = tracker.sender_id
                            save_to_db(user_id,"length",length)
                            save_to_db(user_id, "width", width)
                            if active=="consult":
                                return [SlotSet("mode", "consult"),FollowupAction("send_consult")]
                            elif active=="calculate":
                                return [SlotSet("mode","calculate"),FollowupAction("calculate_price")]
                            return [
                                SlotSet("width", width),
                                SlotSet("length", length),
                                SlotSet("area", area)
                            ]

                    else:
                        dispatcher.utter_message(text="Không thể tải ảnh về từ server.")
                else:
                    dispatcher.utter_message(text="Không thể lấy ảnh. Vui lòng thử lại.")
            except Exception as e:
                dispatcher.utter_message(text=f"Đã xảy ra lỗi khi xử lý ảnh: {e}")
        else:
            dispatcher.utter_message(text="Không có ảnh nào được gửi. Vui lòng gửi lại.")
        return []


class ActionCalculatePrice(FormValidationAction):
    def name(self) -> Text:
        return "calculate_price"
    def get_conver(self,dispatcher, tracker, domain, user_id):
        consult_started = False
        conversation_history = []
        next_slot=self.request_next_slot(dispatcher, tracker, domain, user_id)
        conversation_history.append(f"Thu thập thông tin:{next_slot}")
        latest_message=tracker.latest_message.get('text', '')
        confirmation_asked = tracker.get_slot("confirmation_asked")
        for event in tracker.events:
            # Kiểm tra xem consult_active có True không và bắt đầu ghi lại lịch sử cuộc trò chuyện
            if event.get("event") == "slot" and event.get("name") == "mode":
                if event.get("value") == "calculate":
                    consult_started = True
                    # conversation_history=[]
                    # conversation_history.append(f"Bot: Để tính chi phí bạn hãy cho tôi biết loại công trình là gì?")
                elif event.get("value") == None and confirmation_asked==False:
                    conversation_history=[]
                    conversation_history.append(f"Bot: Để tính chi phí bạn hãy cho tôi biết loại công trình là gì?")
                else:
                    consult_started = False
                    conversation_history = []

            # Ghi nhận các sự kiện của người dùng và bot khi consult_active là True
            if consult_started and event.get("event") in ["user", "bot"]:
                if event.get("event") == "user":
                    conversation_history.append(f"Người dùng: {event.get('text', '')}")
                elif event.get("event") == "bot":
                    conversation_history.append(f"Bot: {event.get('text', '')}")

        # Chuyển history thành chuỗi để in ra
        conversation_history_str = "\n".join(conversation_history)
        print("history", conversation_history_str)


        return conversation_history

    def validate(self,dispatcher, tracker, domain, user_id):
        conversation_history=self.get_conver(dispatcher, tracker, domain, user_id)
        if len(conversation_history) > 1:
            prompt = f"Lịch sử trò chuyện: {conversation_history}.Nếu lịch sử trống thì intent là inquire\ntrích xuất ra cho tôi ý định trong tin nhắn gần nhất của người dùng thông qua lịch sử bằng 1 trong 3 intent sau: Nếu người dùng không muốn tư vấn nửa:'stop',Nếu người dùng muốn tư vấn hay tính tiền: 'provide_information',Nếu người dùng muốn thay đổi thông tin: 'change_information', Nếu là các thắc mắc của người dùng thì: 'inquire'.Nếu là provide_information hoặc change thì xác định intent đó chứa entities nào và thông tin gì. Lưu ý thông tin phải lấy đúng của người dùng, Có thể viết lại cho đúng format câu hỏi, đúng chính tả, đúng viết hoa chứ không được đừng thay đổi ý nghĩa, Entities thì chỉ lấy 1 trong 4 entities:type(loại công trình), width(Chuyển thành số đơn vị m), length(Chuyển thành số đơn vị m), height(Chuyển thành số đơn vị tầng). Nếu không thuộc gì trong 4 cái đó thì entities là more.\n còn nếu là 'inquire' thì hãy đưa nó vào entities trong json). chỉ trả lời bằng file json theo cấu trúc 'intent':intent, 'entities':entity:thông tin của người dùng(chỉ chứ duy nhất 1 mình nó thôi), \nĐưa vào json tổng cộng 3 cái đó thôi, đừng giải thích bạn đang làm gì hay thêm context"
            confirmation_asked = tracker.get_slot("confirmation_asked")
            confirmation_change = tracker.get_slot("confirmation_change")

            if confirmation_asked == True:
                llm_response = {'intent': 'stop'}
            elif confirmation_change == True:
                change, consult = self.bef_submit(dispatcher, tracker, user_id)
                if change==False and consult==None:
                    return self.submit(dispatcher, tracker)
                else:
                    return [SlotSet("confirmation_change", change), SlotSet("mode", consult)]
            else:
                llm_response = gemini(prompt)
            if llm_response is None:
                return []
            intent = llm_response.get("intent")

            # Xử lý theo intent của AI response
            if intent == "stop":
                confirmation_asked = tracker.get_slot("confirmation_asked")
                if confirmation_asked == False:  # Nếu chưa hỏi xác nhận
                    dispatcher.utter_message(
                        text="Bạn có chắc chắn muốn dừng tư vấn không? Nếu bạn dừng tư vấn bây giờ tôi sẽ xóa hết thông tin.")
                    return [SlotSet("confirmation_asked", True)]
                else:
                    intent = tracker.latest_message['intent'].get('name')
                    confidence = tracker.latest_message['intent'].get('confidence', 0)
                    if intent == "affirm" and confidence > 0.8:
                        dispatcher.utter_message(text="Cảm ơn bạn, nếu cần gì thêm hãy báo cho tôi nhé!")
                        delete_all_rows()
                        return [SlotSet("confirmation_asked", False), SlotSet("mode", None),
                                SlotSet("type", None),
                                SlotSet("length", None), SlotSet("width", None), SlotSet("weight", None),
                                SlotSet("address", None), SlotSet("height", None)]
                    elif intent == "deny" and confidence > 0.8:
                        dispatcher.utter_message(text="Vậy bạn hãy cung cấp thông tin cho tôi nhé!")
                        return [SlotSet("confirmation_asked", False)]
                    else:
                        dispatcher.utter_message(text="Bạn có chắc chắn muốn dừng tư vấn không?")
                        return [SlotSet("confirmation_asked", True)]

            elif intent == "inquire":
                entities = llm_response.get('entities', {})
                for entity_key, entity_value in entities.items():
                    if entity_key in ['length', 'width', 'height', 'address', 'weight', 'more']:
                        entities = entity_value

                prompts = f"Bạn là một tư vấn viên trong ngành xây dựng nhà máy thép tiền chế, hãy giải đáp thắc mắc này 1 cách ngắn gọn nhưng vẫn lịch sự: {entities}. Có một số điều cần lưu ý, chiều dài và chiêuf rộng đơn vị mét, chiều cao đơn vị tầng, loại công trình là nhà xưởng, nhà thép, nhà thép tiền chế, vị trí là vị trí ở Việt Nam."
                inquire_response = gemini(prompts)
                dispatcher.utter_message(text=inquire_response)
                return []

            elif intent == "provide_information":
                entities = llm_response.get('entities', {})
                type_map = {
                    'type': ["nha xuong", "nha thep tole", "nha thep ton", "nha thep tien che", 'nha thep'],
                    'length': 'length',
                    'width': 'width',
                    'height': 'height',
                }

                # Duyệt qua tất cả các entity trong entities
                for entity, value in entities.items():
                    if entity in type_map:
                        # Nếu là 'type', kiểm tra giá trị có hợp lệ không
                        if entity == 'type':
                            normalized_value = normalize_text(value)
                            if normalized_value not in type_map[entity]:
                                dispatcher.utter_message(
                                    text=f"Xin lỗi, Hiện tại chúng tôi không phục vụ loại hình '{value}', chúng tôi chỉ phục vụ 1 trong các loại sau: nhà xưởng, nhà thép và nhà thép tôn."
                                )
                                return []

                        # Lưu vào cơ sở dữ liệu nếu giá trị hợp lệ
                        save_to_db(user_id, entity, value)

                # Có thể thêm một thông báo cho người dùng nếu đã cập nhật thành công
                dispatcher.utter_message(template="acc_affirm")
                return []

            elif intent == "change_information":
                entities = llm_response.get('entities', {})
                updated_slots = []
                for field, value in entities.items():
                    if field == 'more':
                        dispatcher.utter_message(
                            text=f"Không tìm thấy thông tin về: {value}. Vui lòng cho biết thêm thông tin!")
                    elif field == "type":
                        normalized_value = normalize_text(value)
                        if normalized_value not in ["nha xuong", "nha thep tole", "nha thep ton", "nha thep tien che", 'nha thep']:
                            dispatcher.utter_message(
                                        text=f"Xin lỗi, Hiện tại chúng tôi không phục vụ loại hình '{value}', chúng tôi chỉ phục vụ 1 trong các loại sau: nhà xưởng, nhà thép và nhà thép tôn."
                                    )
                    check=check_value_exists(user_id, field, value)
                    if check is True:
                        dispatcher.utter_message(
                            text=f"Bạn đã cung cấp cho tôi: {value} trước đây rồi!")

                    else:
                        save_to_db(user_id, field, value)
                        updated_slots.append(SlotSet(field, value))
                        dispatcher.utter_message(text=f"Thông tin đã được cập nhật cho: {value}.")
                return []
            return [SlotSet("mode","calculate")]
    def request_next_slot(self, dispatcher, tracker, domain,user_id):
        """
        Yêu cầu thông tin cho slot tiếp theo còn thiếu.
        """
        # Lấy thông tin cột và giá trị từ dòng đầu tiên trong bảng
        column_values = get_first_row_column_values(user_id)
        # Danh sách các slot yêu cầu
        required = ["type", "length", "width", "height", "type", "length", "width", "height","type", "length", "width", "height"]

        updated_slot_events = []
        all_slots_updated = True

        # Kiểm tra xem tất cả các slot có được cập nhật chưa
        for slot_name in required:
            if slot_name not in column_values or column_values[slot_name] is None:
                all_slots_updated = False
                break

        print(f"Tất cả các slot đã cập nhật: {all_slots_updated}")

        for slot in required:
            if slot not in column_values or column_values[slot] is None:
                print("slot còn sót:", slot)
                return slot
        return None


    def run(self, dispatcher, tracker, domain):
        current_mode = tracker.get_slot("mode")
        user_id = tracker.sender_id

        if current_mode == "consult":
            return [SlotSet("mode", "consult"), FollowupAction("send_consult")]
        elif current_mode == "calculate":
            intent = tracker.latest_message['intent'].get('name')
            confidence = tracker.latest_message['intent'].get('confidence', 0)
            if intent == "detect_encoded_string" and confidence > 0.8:
                return [FollowupAction("process_image"), SlotSet("mode", "calculate")]
            validation_events = self.validate(dispatcher, tracker, domain, user_id)
            next_slot = self.request_next_slot(dispatcher, tracker, domain, user_id)
            if validation_events:
                return validation_events
            ask_next_slot(next_slot, dispatcher)
        else:
            validation_events=self.validate(dispatcher, tracker, domain, user_id)
            next_slot = self.request_next_slot(dispatcher, tracker, domain, user_id)
            if next_slot=="type":
                dispatcher.utter_message(
                    text=f"Để tính chi phí, Trước hết hãy cho tôi biết bạn muốn xây dựng loại công trình gì (Hiện nay Công ty chúng tôi cung cấp 3 loại công trình:nhà xưởng, nhà thép, nhà thép tôn) \n")
                return [SlotSet("mode", "calculate")]
            else:
                if next_slot is not None:
                    ask_next_slot(next_slot, dispatcher)
                    return [SlotSet("mode","calculate")]
        if next_slot is None:
            change, calculate = self.bef_submit(dispatcher, tracker, user_id)
            if change == False and calculate == None:
                return self.submit(dispatcher, tracker)
            elif change == False and calculate == "calculate":
                return [FollowupAction("calculate_price")]
            else:
                return [SlotSet("confirmation_change", change), SlotSet("mode", calculate)]
            # # Nếu chưa có câu hỏi tiếp theo


    def cal(self, dispatcher: CollectingDispatcher, user_id):
        conn = sqlite3.connect('slots.db')
        cursor = conn.cursor()

        # Lấy dữ liệu từ bảng slot_info
        cursor.execute("SELECT type, length, width, height FROM slot_info WHERE user_id = ?", (user_id,))
        data = cursor.fetchone()

        if not data:
            return []
        # Gán giá trị từ cơ sở dữ liệu vào các biến
        category, length, width,height = data
        cate=category
        category=normalize_text(category)
        price = update_excel_and_calculate(category,length, width,height)
        dispatcher.utter_message(
            text=f"Dưới đây là tính toán sơ bộ cho dự án {cate} của bạn bao gồm Chiều dài: {length}m, Chiều rộng: {width}m , Chiều cao: {height} tầng\n")
        for i in range(len(price)):
            stt = i + 1
            text = price[i]
            dispatcher.utter_message(text=f"{stt}. {text}\n")
        conn.close()
    def bef_submit(self, dispatcher, tracker,user_id):
        column_values = get_first_row_column_values(user_id)
        slot_data = {}
        slot_type = {
                "Loại công trình": "type",
                "Chiều dài": "length",
                "Chiều rộng": "width",
                "Chiều cao": "height",
            }
        confirmation_change = tracker.get_slot("confirmation_change")
        if confirmation_change == False:
            dispatcher.utter_message(text="Tất cả thông tin của bạn đã được thu thập thành công.")
            # Kiểm tra và gửi thông tin nếu chưa xác nhận
            for name, slot_name in slot_type.items():
                value = column_values.get(slot_name)
                if value:
                    slot_data[slot_name] = value
                    dispatcher.utter_message(text=f"{name}: {value}")
            dispatcher.utter_message(
                text="Mời bạn xác nhận lại thông tin, bạn có muốn thay đổi thông tin không? Nếu không, chúng tôi sẽ bắt đầu tính tiền dựa trên thông tin này. Nếu có bạn sẽ phải điền lại thông tin từ đầu!")
            return True, "calculate"
        else:
            # Kiểm tra và xử lý xác nhận thay đổi
            intent = tracker.latest_message['intent'].get('name')
            confidence = tracker.latest_message['intent'].get('confidence', 0)
            if intent == "affirm" and confidence > 0.8:
                dispatcher.utter_message(text="Được vậy giờ tôi sẽ thu thập thông tin lại từ đầu")
                delete_all_rows()
                ask_next_slot('type', dispatcher)
                return False, "calculate"
            elif intent == "deny" and confidence > 0.8:
                dispatcher.utter_message(text="Vậy tôi sẽ bắt đầu tính tiền!")
                self.cal(dispatcher, user_id)
                dispatcher.utter_message(text="Bạn có muốn tôi giúp bạn tư vấn nhiều hơn về công trình này không?")
                # return self.submit(dispatcher, tracker)
                return False, None,
            else:
                dispatcher.utter_message(
                    text="Tôi không hiểu ý bạn, Bạn có muốn thay đổi gì không?")
                return True, "calculate"

    def submit(self, dispatcher, tracker):
        return [SlotSet("mode",None),SlotSet("confirmation_change",False) ,SlotSet("checkpoint",True)]


class ActionProcessFallback(Action):
    def name(self):
        return "process_fallback"

    def run(self, dispatcher, tracker, domain):
        active = tracker.get_slot("mode")
        if active=="consult":
            return [SlotSet("mode", "consult"),FollowupAction("send_consult")]
        elif active=="calculate":
            return [SlotSet("mode", "calculate"),FollowupAction("calculate_price")]
        else:
            user_id = tracker.sender_id
            question = tracker.latest_message.get('text', '')
            api_url = "https://61c0-2401-d800-d4b0-26e9-2922-904c-69f3-3f9.ngrok-free.app/process_question"
            data=[]
            data.append(question)
            # Dữ liệu cần gửi
            payload = {
                'user_id': user_id,
                'data': data
            }

            try:
                # Gửi dữ liệu tới API bằng phương thức POST
                headers = {'Content-Type': 'application/json'}

                # Gửi POST request đến API
                response = requests.post(api_url, data=json.dumps(payload), headers=headers)

                # Kiểm tra mã trạng thái phản hồi
                if response.status_code == 200:
                    response_data = response.json()

                    # Lấy message từ API (giả sử phản hồi là message)
                    message = response_data.get('context')
                    prompt_rag=f"Bạn là một kỹ sư xây dựng nhà thép tiền chế và bạn đang phải tư vấn cho khách hàng về vấn đề :{question}. Hãy dùng ngữ cảnh sau đây để trả lời 1 cách ngắn gọn nhất có thể. Ngữ cảnh: {message}"
                    ans=gemini(prompt_rag)
                    dispatcher.utter_message(text=ans)

            except requests.exceptions.RequestException as e:
                # Xử lý lỗi khi không thể kết nối API
                dispatcher.utter_message(text="Không thể kết nối đến API, vui lòng thử lại sau.")
                print(f"Lỗi kết nối API: {e}")
            return []
# ----------------------

class ActionBookFlow(FormValidationAction):
    def name(self) -> Text:
        return "book_consult"

    def check_missing_columns(self,user_id):
        """
        Kiểm tra các cột trong bảng slot_info đối với một user_id,
        nếu có bất kỳ cột nào bị thiếu giá trị, trả về False, nếu không trả về True.
        """
        conn = sqlite3.connect('slots.db')
        cursor = conn.cursor()

        # Truy vấn dữ liệu cho user_id cụ thể
        cursor.execute('''
        SELECT type, length, width, height, weight, address FROM slot_info WHERE user_id = ?
        ''', (user_id,))

        result = cursor.fetchone()
        conn.close()

        # Kiểm tra xem kết quả có bị thiếu giá trị nào không
        if result:
            # Nếu bất kỳ cột nào có giá trị None (missing), trả về False
            if None in result:
                print(f"User {user_id} has missing values in their record.")
                return False
            else:
                return True
        else:
            print(f"No record found for user {user_id}.")
            return False


    def run(self, dispatcher, tracker, domain):
        name = tracker.get_slot("name")
        phone = tracker.get_slot("phone")
        user_id = tracker.sender_id
        check=self.check_missing_columns(user_id)
        if check==False:
            return [SlotSet("mode", "consult"), FollowupAction("send_consult")]
        else:
            if not name or not phone:
                dispatcher.utter_message("Vui lòng cung cấp tên và số điện thoại của bạn để chúng tôi có thể tư vấn.")
                return []
            dispatcher.utter_message(
                f"Cảm ơn bạn, {name}! Chúng tôi đã nhận được thông tin số điện thoại của bạn: {phone}. Kỹ sư của chúng tôi sẽ sớm liên hệ với bạn.")
        return [SlotSet("book", False)]

class ActionConsultFlow(FormValidationAction):
    def name(self) -> Text:
        return "send_consult"

    def get_conver(self,dispatcher, tracker, domain, user_id):
        consult_started = False
        conversation_history = []
        next_slot=self.request_next_slot(dispatcher, tracker, domain, user_id)
        conversation_history.append(f"Thu thập thông tin:{next_slot}")
        latest_message=tracker.latest_message.get('text', '')
        confirmation_asked = tracker.get_slot("confirmation_asked")
        for event in tracker.events:
            if event.get("event") == "slot" and event.get("name") == "mode":
                if event.get("value") == "consult":
                    consult_started = True
                    # conversation_history=[]
                    # conversation_history.append(f"Bot: Để tính chi phí bạn hãy cho tôi biết loại công trình là gì?")
                elif event.get("value") == None and confirmation_asked==False:
                    conversation_history=[]
                    conversation_history.append(f"Bot: Để tư vấn bạn hãy cho tôi biết địa chỉ công trình ở đâu?")
                else:
                    consult_started = False
                    conversation_history = []

            # Ghi nhận các sự kiện của người dùng và bot khi consult_active là True
            if consult_started and event.get("event") in ["user", "bot"]:
                if event.get("event") == "user":
                    conversation_history.append(f"Người dùng: {event.get('text', '')}")
                elif event.get("event") == "bot":
                    conversation_history.append(f"Bot: {event.get('text', '')}")

        # Chuyển history thành chuỗi để in ra
        conversation_history_str = "\n".join(conversation_history)
        print("history", conversation_history_str)
        return conversation_history

    def validate(self,dispatcher, tracker, domain, user_id):
        conversation_history=self.get_conver(dispatcher, tracker, domain, user_id)
        if len(conversation_history)>1:
            prompt = f"Lịch sử trò chuyện: {conversation_history}.Nếu lịch sử trống thì intent là inquire\ntrích xuất ra cho tôi ý định trong tin nhắn gần nhất của người dùng thông qua lịch sử bằng 1 trong 3 intent sau: Nếu người dùng không muốn tư vấn nửa:'stop',Nếu người dùng muốn tư vấn hay tính tiền: 'provide_information',Nếu người dùng muốn thay đổi thông tin: 'change_information', Nếu là các thắc mắc của người dùng thì: 'inquire'..Nếu là provide_information hoặc change thì xác định intent đó chứa entities nào và thông tin gì. Lưu ý thông tin phải lấy đúng của người dùng, Có thể viết lại cho đúng format câu hỏi, đúng chính tả, đúng viết hoa chứ không được đừng thay đổi ý nghĩa, Entities thì chỉ lấy 1 trong 6 entities:type(loại công trình), width(Chuyển thành số đơn vị m), length(Chuyển thành số đơn vị m), height(Chuyển thành số đơn vị tầng), weight(Chuyển thành số đơn vị tấn), address(chữ). Nếu không thuộc gì trong 6 cái đó thì entities là more.\n còn nếu là 'inquire' thì hãy đưa nó vào entities trong json). chỉ trả lời bằng file json theo cấu trúc 'intent':intent, 'entities':entity:thông tin của người dùng(chỉ chứ duy nhất 1 mình nó thôi), \nĐưa vào json tổng cộng 3 cái đó thôi, đừng giải thích bạn đang làm gì hay thêm context"

            llm_response = gemini(prompt)

            if llm_response is None:
                dispatcher.utter_message(text="Xin lỗi, tôi không thể xử lý thông tin hiện tại. Hãy thử lại sau.")
                return []

            confirmation_asked = tracker.get_slot("confirmation_asked")
            confirmation_change = tracker.get_slot("confirmation_change")

            if confirmation_asked == True:
                llm_response = {'intent': 'stop'}
            elif confirmation_change == True:
                change, consult = self.bef_submit(dispatcher, tracker, user_id)
                if change == False and consult == None:
                    return self.submit(dispatcher, tracker)
                else:
                    return [SlotSet("confirmation_change", change), SlotSet("mode", consult)]

            intent = llm_response.get("intent")

            # Xử lý theo intent của AI response
            if intent == "stop":
                confirmation_asked = tracker.get_slot("confirmation_asked")
                if confirmation_asked == False:  # Nếu chưa hỏi xác nhận
                    dispatcher.utter_message(
                        text="Bạn có chắc chắn muốn dừng tư vấn không? Nếu bạn dừng tư vấn bây giờ tôi sẽ xóa hết thông tin.")
                    return [SlotSet("confirmation_asked", True)]
                else:
                    intent = tracker.latest_message['intent'].get('name')
                    confidence = tracker.latest_message['intent'].get('confidence', 0)
                    if intent == "affirm" and confidence > 0.8:
                        dispatcher.utter_message(text="Cảm ơn bạn, nếu cần gì thêm hãy báo cho tôi nhé!")
                        delete_all_rows()
                        return [SlotSet("confirmation_asked", False), SlotSet("mode", None),
                                SlotSet("type", None),
                                SlotSet("length", None), SlotSet("width", None), SlotSet("weight", None),
                                SlotSet("address", None), SlotSet("height", None)]
                    elif intent == "deny" and confidence > 0.8:
                        dispatcher.utter_message(text="Vậy bạn hãy cung cấp thông tin cho tôi nhé!")
                        return [SlotSet("confirmation_asked", False)]
                    else:
                        dispatcher.utter_message(text="Bạn có chắc chắn muốn dừng tư vấn không?")
                        return [SlotSet("confirmation_asked", True)]

            elif intent == "inquire":
                entities = llm_response.get('entities', {})
                for entity_key, entity_value in entities.items():
                    if entity_key in ['length', 'width', 'height', 'address', 'weight', 'more']:
                        entities = entity_value

                prompts = f"Bạn là một tư vấn viên trong ngành xây dựng nhà máy thép tiền chế, hãy giải đáp thắc mắc này 1 cách ngắn gọn nhưng vẫn lịch sự: {entities}. Có một số điều cần lưu ý, chiều dài và chiêuf rộng đơn vị mét, chiều cao đơn vị tầng, loại công trình là nhà xưởng, nhà thép, nhà thép tiền chế, vị trí là vị trí ở Việt Nam."
                inquire_response = gemini(prompts)
                dispatcher.utter_message(text=inquire_response)
                return []

            elif intent == "provide_information":
                entities = llm_response.get('entities', {})
                type_map = {
                    'type': ["nha xuong", "nha thep tole", "nha thep ton", "nha thep tien che", 'nha thep'],
                    'length': 'length',
                    'width': 'width',
                    'height': 'height',
                    'address':'address',
                    'weight':'weight'
                }

                # Duyệt qua tất cả các entity trong entities
                for entity, value in entities.items():
                    if entity in type_map:
                        # Nếu là 'type', kiểm tra giá trị có hợp lệ không
                        if entity == 'type':
                            normalized_value = normalize_text(value)
                            if normalized_value not in type_map[entity]:
                                dispatcher.utter_message(
                                    text=f"Xin lỗi, Hiện tại chúng tôi không phục vụ loại hình '{value}', chúng tôi chỉ phục vụ 1 trong các loại sau: nhà xưởng, nhà thép và nhà thép tôn."
                                )
                                return []

                        # Lưu vào cơ sở dữ liệu nếu giá trị hợp lệ
                        save_to_db(user_id, entity, value)

                # Có thể thêm một thông báo cho người dùng nếu đã cập nhật thành công
                dispatcher.utter_message(template="acc_affirm")
                return []

            elif intent == "change_information":
                entities = llm_response.get('entities', {})
                updated_slots = []
                for field, value in entities.items():
                    if field == 'more':
                        dispatcher.utter_message(
                            text=f"Không tìm thấy thông tin về: {value}. Vui lòng cho biết thêm thông tin!")
                    elif field == "type":
                        normalized_value = normalize_text(value)
                        if normalized_value not in ["nha xuong", "nha thep tole", "nha thep ton", "nha thep tien che",
                                                    'nha thep']:
                            dispatcher.utter_message(
                                text=f"Xin lỗi, Hiện tại chúng tôi không phục vụ loại hình '{value}', chúng tôi chỉ phục vụ 1 trong các loại sau: nhà xưởng, nhà thép và nhà thép tôn."
                            )
                    check = check_value_exists(user_id, field, value)
                    if check is True:
                        dispatcher.utter_message(
                            text=f"Bạn đã cung cấp cho tôi: {value} trước đây rồi!")

                    else:
                        save_to_db(user_id, field, value)
                        updated_slots.append(SlotSet(field, value))
                        dispatcher.utter_message(text=f"Thông tin đã được cập nhật cho: {value}.")
                return []
            return [SlotSet("mode", "consult")]

    def request_next_slot(self, dispatcher, tracker, domain,user_id):
        """
        Yêu cầu thông tin cho slot tiếp theo còn thiếu.
        """
        # Lấy thông tin cột và giá trị từ dòng đầu tiên trong bảng
        print("user id in slot",user_id)
        column_values = get_first_row_column_values(user_id)
        # Danh sách các slot yêu cầu
        required = ["type", "length", "width", "height", "address", "weight","type", "length", "width", "height", "address", "weight","type", "length", "width", "height", "address", "weight"]

        updated_slot_events = []
        all_slots_updated = True

        # Kiểm tra xem tất cả các slot có được cập nhật chưa
        for slot_name in required:
            if slot_name not in column_values or column_values[slot_name] is None:
                all_slots_updated = False
                break

        print(f"Tất cả các slot đã cập nhật: {all_slots_updated}")

        for slot in required:
            if slot not in column_values or column_values[slot] is None:
                print("slot còn sót:", slot)
                return slot
        return None

    import sqlite3

    def check_user_fields(self,user_id):
        conn = sqlite3.connect('slots.db')
        cursor = conn.cursor()

        # Truy vấn lấy giá trị các trường của user_id
        query = '''
        SELECT type, length, width, height 
        FROM slot_info 
        WHERE user_id = ?
        '''
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()

        conn.close()

        # Nếu không có kết quả, user_id không tồn tại
        if result is None:
            print(f"user_id '{user_id}' không tồn tại trong cơ sở dữ liệu.")
            return False

        # Kiểm tra từng trường có giá trị hay không
        type_value, length_value, width_value, height_value = result
        missing_fields = []
        if not type_value:
            missing_fields.append("type")
        if not length_value:
            missing_fields.append("length")
        if not width_value:
            missing_fields.append("width")
        if not height_value:
            missing_fields.append("height")

        # Đưa ra kết quả
        if missing_fields:
            print(f"user_id '{user_id}' thiếu các trường: {', '.join(missing_fields)}.")
            return False
        else:
            print(f"user_id '{user_id}' đã có đầy đủ các trường: type, length, width, height.")
            return True

    def run(self, dispatcher, tracker, domain):
        current_mode = tracker.get_slot("mode")
        user_id = tracker.sender_id
        check = self.check_user_fields(user_id)
        if check == False:
            return [SlotSet("mode", "calculate"), FollowupAction("calculate_price")]

        elif current_mode == "calculate":
            return [SlotSet("mode", "consult"), FollowupAction("send_consult")]
        elif current_mode == "consult":
            check=self.check_user_fields(user_id)
            if check == False:
                return [SlotSet("mode", "calculate"), FollowupAction("calculate_price")]
            intent = tracker.latest_message['intent'].get('name')
            confidence = tracker.latest_message['intent'].get('confidence', 0)
            if intent == "detect_encoded_string" and confidence > 0.8:
                return [FollowupAction("process_image"), SlotSet("mode", "consult")]
            validation_events = self.validate(dispatcher, tracker, domain, user_id)
            next_slot = self.request_next_slot(dispatcher, tracker, domain, user_id)
            if validation_events:
                return validation_events
            ask_next_slot(next_slot, dispatcher)
        else:
            validation_events = self.validate(dispatcher, tracker, domain, user_id)
            next_slot = self.request_next_slot(dispatcher, tracker, domain, user_id)
            print("slot con tiep:", next_slot)
            if next_slot == "type":
                dispatcher.utter_message(
                    text=f"Để tư vấn, Trước hết hãy cho tôi biết bạn muốn xây dựng loại công trình gì (Hiện nay Công ty chúng tôi cung cấp 3 loại công trình:nhà xưởng, nhà thép, nhà thép tôn) \n")
                return [SlotSet("mode", "consult")]
            else:
                if next_slot is not None:
                    ask_next_slot(next_slot, dispatcher)
                    return [SlotSet("mode", "consult")]
        if next_slot is None:
            change, consult = self.bef_submit(dispatcher, tracker, user_id)
            if change == False and consult == None:
                return self.submit(dispatcher, tracker)
            elif change == False and consult == "consult":
                return [FollowupAction("send_consult")]
            else:
                return [SlotSet("confirmation_change", change), SlotSet("mode", consult)]

    def get_construction_info(self,user_id):
        # Kết nối cơ sở dữ liệu
        conn = sqlite3.connect('slots.db')
        cursor = conn.cursor()

        # Lấy dữ liệu từ bảng slot_info
        cursor.execute("SELECT type, length, width, weight, address FROM slot_info WHERE user_id = ?", (user_id,))
        data = cursor.fetchone()

        if not data:
            return []

        # Gán giá trị từ cơ sở dữ liệu vào các biến
        type_construction, length, width, weight, address,  = data
        length = float(re.match(r"(\d+(\.\d+)?)(\s?[a-zA-Z]+)?", length).group(1))
        width = float(re.match(r"(\d+(\.\d+)?)(\s?[a-zA-Z]+)?", width).group(1))
        weight = float(re.match(r"(\d+(\.\d+)?)(\s?[a-zA-Z]+)?", weight).group(1))
        # Tính toán diện tích
        area = length * width
        if area < 10:
            area_str = f"{type_construction} bé hơn 10m²"
        elif 10 <= area <= 50:
            area_str = f"{type_construction} từ 10m² đến 50m²"
        elif 50 < area <= 100:
            area_str = f"{type_construction} từ 50m² đến 100m²"
        elif 100 < area <= 200:
            area_str = f"{type_construction} từ 100m² đến 200m²"
        elif 200 < area <= 500:
            area_str = f"{type_construction} từ 200m² đến 500m²"
        elif 500 < area <= 1000:
            area_str = f"{type_construction} từ 500m² đến 1000m²"
        elif 1000 < area <= 2000:
            area_str = f"{type_construction} từ 1000m² đến 2000m²"
        else:
            area_str = f"{type_construction} trên 2000m²"

        # Xác định trọng tải
        if weight < 10:
            weight_str = f"{type_construction} có trọng tải nhỏ 10 tấn"
        elif 10 <= weight < 50:
            weight_str = f"{type_construction} từ 10 tấn đến 50 tấn"
        elif 50 <= weight < 100:
            weight_str = f"{type_construction} từ 50 tấn đến 100 tấn"
        elif 100 <= weight < 200:
            weight_str = f"{type_construction} từ 100 tấn đến 200 tấn"
        elif 200 <= weight < 500:
            weight_str = f"{type_construction} từ 200 tấn đến 500 tấn"
        elif 500 <= weight < 1000:
            weight_str = f"{type_construction} từ 500 tấn đến 1000 tấn"
        elif 1000 <= weight < 2000:
            weight_str = f"{type_construction} từ 1000 tấn đến 2000 tấn"
        else:
            weight_str = f"{type_construction} trên 2000 tấn"

        # Tạo một danh sách chứa các thông tin
        result = [
            f"{area_str}",
            f"{weight_str}"
        ]
        # Nếu địa chỉ không phải None, thêm thông tin địa chỉ và khu vực vào danh sách kết quả
        if address:
            prompt=f"Hãy xác địa địa chỉ này: {address} Thuộc miền nào của Việt Nam ( Bắc Trung Nam), nếu không thuộc Việt Nam hãy trả về None. Trả lời ngắn gọi đừng giải thích ngữ cảnh hãy hay gì hết"
            region  = gemini(prompt)
            result.append(f"{type_construction} khu vực {region}")

        # Đóng kết nối cơ sở dữ liệu
        base=f"Công trình:{type_construction} có kích thước dài:{length}, dọc:{width}, tổng diện tích:{area}, chiệu được trọng tải:{weight}. Ở địa chỉ là {address}, thuộc khu vực {region}"

        conn.close()

        return result, base

    def send_data_to_api(self,user_id, data_list):
        url = "https://61c0-2401-d800-d4b0-26e9-2922-904c-69f3-3f9.ngrok-free.app/process_question"

        # Chuẩn bị dữ liệu gửi đi
        payload = {
            'user_id': user_id,
            'data': data_list
        }

        headers = {'Content-Type': 'application/json'}

        # Gửi POST request đến API
        response = requests.post(url, data=json.dumps(payload), headers=headers)

        # Kiểm tra mã trạng thái phản hồi
        if response.status_code == 200:
            response_data = response.json()
            # In ra user_id và context từ phản hồi
            user_id = response_data.get('user_id')
            context = response_data.get('context')

            # In thông tin trả về từ API
            print(f"User ID: {user_id}")
            print(f"Context: {context}")
            return context
        else:
            print(f"Error: {response.status_code} - {response.text}")

    def bef_submit(self, dispatcher, tracker,user_id):

        column_values = get_first_row_column_values(user_id)
        slot_data = {}
        slot_type = {
                "Loại công trình": "type",
                "Chiều dài": "length",
                "Chiều rộng": "width",
                "Chiều cao": "height",
                "Địa chỉ xây dựng": "address",
                "Tải trọng": "weight"
            }
        confirmation_change = tracker.get_slot("confirmation_change")
        if confirmation_change == False:
            dispatcher.utter_message(text="Tất cả thông tin của bạn đã được thu thập thành công.")
            # Kiểm tra và gửi thông tin nếu chưa xác nhận
            for name, slot_name in slot_type.items():
                value = column_values.get(slot_name)
                if value:
                    slot_data[slot_name] = value
                    dispatcher.utter_message(text=f"{name}: {value}")
            dispatcher.utter_message(
                text="Bạn có muốn xác nhận lại và thay đổi thông tin không? Nếu không, chúng tôi sẽ bắt đầu tư vấn dựa trên thông tin này. Nếu có bạn sẽ phải điền lại thông tin từ đầu!")
            return True, True
        else:
            # Kiểm tra và xử lý xác nhận thay đổi
            intent = tracker.latest_message['intent'].get('name')
            confidence = tracker.latest_message['intent'].get('confidence', 0)
            if intent == "affirm" and confidence > 0.8:
                dispatcher.utter_message(text="Được vậy giờ tôi sẽ thu thập thông tin lại từ đầu")
                delete_all_rows()
                ask_next_slot('type', dispatcher)
                return False, "consult"
            elif intent == "deny" and confidence > 0.8:
                dispatcher.utter_message(text="Vậy tôi sẽ bắt đầu tư vấn!")
                construction_info, base = self.get_construction_info(user_id)
                context=self.send_data_to_api(user_id, construction_info)
                prompt_consult=f"Bạn là một tư vấn viên và một kỹ sư xây dựng trong ngành nhà thép tiền chế, bạn hãy tư vấn cho khách hàng có thông tin:{base} dựa vào nội dung ngữ cảnh sau :{context}. Hãy tư vấn lịch sự và ngắn gọn thôi. Chỉ tư vấn chứ đừng hỏi hay chào mời hàng hóa gì hết. Lưu ý nếu địa chỉ ở ngoài Việt Nam thì đừng tư vấn về vị trí nhé. Công ty chúng ta chỉ phục vụ trong nước thôi"
                dispatcher.utter_message(
                    text=gemini(prompt_consult))
                dispatcher.utter_message(
                    text="Đây là những sản phẩm và dịch vụ công ty chúng tôi có thể tư vấn cho quý khách với mức giá hấp dẫn. QUý khách có muốn đặt lịch tư vấn với kĩ sư xây dựng của chúng tôi không ạ.")
                dispatcher.utter_message(
                    text="Ngoài tư vấn chúng tôi cũng có thể giúp quý khách tính toán chi phí xây dựng hoặc đọc diện tích của bản vẽ(nếu đủ tiêu chuẩn).")
                return False, None
            else:
                dispatcher.utter_message(
                    text="Tôi không hiểu ý bạn, Bạn có muốn thay đổi gì không?")
                return True, "consult"


    def submit(self, dispatcher, tracker):
        return [SlotSet("mode",None),SlotSet("confirmation_change",False),[SlotSet("book", True)] ,SlotSet("checkpoint",True)]


# --------------------------


# ---------------------
from rasa_sdk import Action
from rasa_sdk.events import SlotSet, FollowupAction, Form
from rasa_sdk.executor import CollectingDispatcher


class ActionGreet(Action):
    def name(self) -> str:
        return "acc_greet"

    def run(self, dispatcher, tracker, domain):

        active = tracker.get_slot("mode")
        if active == "consult":
            return [SlotSet("mode", "consult"), FollowupAction("send_consult")]
        elif active == "calculate":
            return [SlotSet("mode", "calculate"), FollowupAction("calculate_price")]
        else:
            dispatcher.utter_message(template="acc_greet")
            return []

class ActionBotIntroduction(Action):
    def name(self) -> str:
        return "acc_bot_introduction"

    def run(self, dispatcher, tracker, domain):

        active = tracker.get_slot("mode")

        if active == "consult":
            return [SlotSet("mode", "consult"), FollowupAction("send_consult")]
        elif active == "calculate":
            return [SlotSet("mode", "calculate"), FollowupAction("calculate_price")]

        else:
            dispatcher.utter_message(template="acc_bot_introduction")
            return []


class ActionBotCapabilities(Action):
    def name(self) -> str:
        return "acc_bot_capabilities"

    def run(self, dispatcher, tracker, domain):
        active = tracker.get_slot("mode")

        if active == "consult":
            return [SlotSet("mode", "consult"), FollowupAction("send_consult")]
        elif active == "calculate":
            return [SlotSet("mode", "calculate"), FollowupAction("calculate_price")]
        else:
            dispatcher.utter_message(template="acc_bot_capabilities")
            return []


class ActionSendImage(Action):
    def name(self) -> str:
        return "acc_send_image"

    def run(self, dispatcher, tracker, domain):
        print("Gọi 2 lần 12")
        active = tracker.get_slot("mode")

        if active == "consult":
            return [SlotSet("mode", "consult"), FollowupAction("send_consult")]
        elif active == "calculate":
            return [SlotSet("mode", "calculate"), FollowupAction("calculate_price")]
        else:
            dispatcher.utter_message(template="acc_send_image")
            return []


class ActionGoodbye(Action):
    def name(self) -> str:
        return "acc_goodbye"

    def run(self, dispatcher, tracker, domain):
        active = tracker.get_slot("mode")

        if active == "consult":
            return [SlotSet("mode", "consult"), FollowupAction("send_consult")]
        elif active == "calculate":
            return [SlotSet("mode", "calculate"), FollowupAction("calculate_price")]
        else:
            dispatcher.utter_message(template="acc_goodbye")
            return []


# Action Affirm
class ActionAffirm(Action):
    def name(self) -> str:
        return "acc_affirm"

    def run(self, dispatcher, tracker, domain):
        active = tracker.get_slot("mode")
        book = tracker.get_slot("book")
        checkpoint=tracker.get_slot("checkpoint")
        if book == True:
            return [SlotSet("book", False), FollowupAction("book_consult")]
        elif active == "consult" or checkpoint==True:
            return [SlotSet("checkpoint",False),SlotSet("mode", None), FollowupAction("send_consult")]
        elif active == "calculate":
            return [SlotSet("mode", "calculate"), FollowupAction("calculate_price")]
        else:

            dispatcher.utter_message(template="acc_affirm")
            return []


# Action Deny
class ActionDeny(Action):
    def name(self) -> str:
        return "acc_deny"

    def run(self, dispatcher, tracker, domain):
        active = tracker.get_slot("mode")
        checkpoint=tracker.get_slot("checkpoint")
        if active == "consult":
            return [SlotSet("checkpoint",False),SlotSet("mode", "consult"), FollowupAction("send_consult")]
        elif active == "calculate":
            return [SlotSet("mode", "calculate"), FollowupAction("calculate_price")]
        else:
            dispatcher.utter_message(template="acc_deny")
            if checkpoint == True:
                return[SlotSet("checkpoint",False)]
            else:
                return []


# Action Contact
class ActionContact(Action):
    def name(self) -> str:
        return "acc_contact"

    def run(self, dispatcher, tracker, domain):
        active = tracker.get_slot("mode")

        if active == "consult":
            return [SlotSet("mode", "consult"), FollowupAction("send_consult")]
        elif active == "calculate":
            return [SlotSet("mode", "calculate"), FollowupAction("calculate_price")]
        else:
            dispatcher.utter_message(template="acc_contact")
            return []


# Action Product Info
class ActionProductInfo(Action):
    def name(self) -> str:
        return "acc_bot_how_to_use"

    def run(self, dispatcher, tracker, domain):
        active = tracker.get_slot("mode")

        if active == "consult":
            return [SlotSet("mode", "consult"), FollowupAction("send_consult")]
        elif active == "calculate":
            return [SlotSet("mode", "calculate"), FollowupAction("calculate_price")]
        else:
            dispatcher.utter_message(template="acc_bot_how_to_use")
            return []


# Action Ask Product
class ActionAskProduct(Action):
    def name(self) -> str:
        return "acc_bot_limitations"

    def run(self, dispatcher, tracker, domain):
        active = tracker.get_slot("mode")

        if active == "consult":
            return [SlotSet("mode", "consult"), FollowupAction("send_consult")]
        elif active == "calculate":
            return [SlotSet("mode", "calculate"), FollowupAction("calculate_price")]
        else:
            dispatcher.utter_message(template="acc_bot_limitations")
            return []


class ActionAskProduct(Action):
    def name(self) -> str:
        return "acc_thanks"

    def run(self, dispatcher, tracker, domain):
        active = tracker.get_slot("mode")

        if active == "consult":
            return [SlotSet("mode", "consult"), FollowupAction("send_consult")]
        elif active == "calculate":
            return [SlotSet("mode", "calculate"), FollowupAction("calculate_price")]
        else:
            dispatcher.utter_message(template="acc_thanks")
            return []

