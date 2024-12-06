import yaml

# Đọc tập tin YAML
def count_stories(yaml_file):
    with open(yaml_file, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)

    # Kiểm tra cấu trúc dữ liệu YAML và đếm số lượng stories
    if 'stories' in data:
        return len(data['stories'])
    else:
        return 0

# Đường dẫn đến tập tin YAML
yaml_file = 'stories.yml'

# Đếm số lượng stories
story_count = count_stories(yaml_file)

print(f'Số lượng stories trong tập tin YAML là: {story_count}')
