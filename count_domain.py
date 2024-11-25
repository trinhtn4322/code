import yaml

# Đọc file YAML
with open("domain.yml", 'r', encoding='utf-8') as file:
    data = yaml.safe_load(file)

# Hàm đếm số lượng response cho từng loại
def count_responses(responses_data):
    counts = {}
    cc=0
    for intent, responses in responses_data.items():
        counts[intent] = len(responses)
        cc+=len(responses)
    return counts,cc

# Đếm số lượng responses
response_counts,cc = count_responses(data['responses'])

# In kết quả ra màn hình
for intent, count in response_counts.items():
    print(f"{intent}: {count} response(s)")

print('cc',cc)