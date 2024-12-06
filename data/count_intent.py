def count_intent_examples(yaml_file):
    import yaml

    # Đọc file YAML
    with open(yaml_file, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)

    intent_counts = {}
    for intent_data in data.get('nlu', []):
        # Kiểm tra khóa 'intent' và 'examples'
        if 'intent' not in intent_data or 'examples' not in intent_data:
            print(f"Invalid data format: {intent_data}")
            continue

        # Đếm số lượng ví dụ
        intent = intent_data['intent']
        examples = intent_data['examples']
        # Tách ví dụ dựa trên định dạng chuẩn YAML
        example_lines = examples.strip().split('\n')
        intent_counts[intent] = len(example_lines)

    return intent_counts


# Gọi hàm với file YAML
yaml_file = 'nlu.yml'
intent_counts = count_intent_examples(yaml_file)

# In kết quả
for intent, count in intent_counts.items():
    print(f"Intent: {intent}, Examples: {count}")
