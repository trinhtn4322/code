import yaml

def count_intent_examples(yaml_file):
    # Đọc dữ liệu từ file YAML
    with open(yaml_file, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)

    # Đếm số lượng ví dụ cho mỗi intent
    intent_counts = {}
    # Lặp qua tất cả các intent trong file
    for intent_data in data['nlu']:
        intent = intent_data['intent']
        examples = intent_data['examples'].strip().split('\n')
        intent_counts[intent] = len(examples)
        print(len(examples))
    return intent_counts

# Thay 'your_file.yml' bằng đường dẫn tới file YAML của bạn
yaml_file = 'data/nlu.yml'
intent_counts = count_intent_examples(yaml_file)

# In ra kết quả
for intent, count in intent_counts.items():
    print(f"Intent: {intent}, Examples: {count}")
