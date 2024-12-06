import yaml
import os

def remove_utter_prefix_from_stories(file_path):
    # Kiểm tra xem file có tồn tại không
    if not os.path.exists(file_path):
        print(f"File {file_path} không tồn tại.")
        return

    # Đọc file YAML
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)

    # Hàm thay thế 'utter_' trong các entries của stories
    def remove_utter_from_entries(entries):
        # Nếu entries là danh sách (list), duyệt qua từng mục
        if isinstance(entries, list):
            for i, entry in enumerate(entries):
                # Nếu phần tử là một từ khóa action, xóa tiền tố 'utter_'
                if isinstance(entry, str):
                    entries[i] = entry.replace('utter_', '')
                # Nếu phần tử là một dictionary (trường hợp của stories), gọi đệ quy
                elif isinstance(entry, dict):
                    for key, value in entry.items():
                        # Nếu là một danh sách, tiếp tục xử lý đệ quy
                        if isinstance(value, list):
                            entries[i][key] = remove_utter_from_entries(value)
        return entries

    # Thay thế 'utter_' trong phần 'stories'
    if "stories" in data:
        data["stories"] = remove_utter_from_entries(data["stories"])

    # Lưu lại file đã sửa
    with open(file_path, 'w', encoding='utf-8') as file:
        yaml.dump(data, file, allow_unicode=True)

    print(f"Đã xóa tiền tố 'utter_' trong file {file_path}.")

# Đường dẫn tới file stories.yml
stories_file = 'stories.yml'

# Gọi hàm để xử lý file
remove_utter_prefix_from_stories(stories_file)
