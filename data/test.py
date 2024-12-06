from rasa.shared.nlu.training_data import TrainingData
from rasa.shared.nlu.training_data import Message
import rasa
from sklearn.model_selection import KFold
import os

# Tải dữ liệu huấn luyện từ file YAML hoặc JSON của bạn
training_data = TrainingData.from_yaml('data/nlu.yml')  # Hoặc 'data/nlu.json' nếu bạn sử dụng định dạng JSON

# Tạo KFold với 5 fold
kf = KFold(n_splits=5)

# Tạo danh sách các fold
splits = kf.split(training_data.training_examples)

for fold, (train_index, val_index) in enumerate(splits):
    # Lấy dữ liệu huấn luyện và kiểm tra cho fold hiện tại
    train_data = [training_data.training_examples[i] for i in train_index]
    val_data = [training_data.training_examples[i] for i in val_index]

    # Lưu lại dữ liệu cho fold vào các file tạm thời
    with open(f'data/fold_{fold}_train.yml', 'w') as f:
        rasa.shared.nlu.training_data.write_training_data(f, train_data)

    with open(f'data/fold_{fold}_val.yml', 'w') as f:
        rasa.shared.nlu.training_data.write_training_data(f, val_data)

    # Huấn luyện mô hình trên fold này
    os.system(f"rasa train nlu --data data/fold_{fold}_train.yml")

    # Kiểm tra mô hình trên fold validation
    os.system(f"rasa test nlu --data data/fold_{fold}_val.yml")
