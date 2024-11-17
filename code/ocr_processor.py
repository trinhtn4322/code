# ocr_processor.py

import os
import cv2
import json
import numpy as np
from google.cloud import vision

def detect_text_ocr(image):
    """
    Phát hiện văn bản trong hình ảnh đã cắt sử dụng Google Cloud Vision API.

    Parameters:
    - image: Mảng Numpy của hình ảnh đã cắt ở định dạng BGR.

    Returns:
    - List các dictionary chứa 'text' và 'bbox' cho mỗi văn bản được phát hiện.
    """
    client = vision.ImageAnnotatorClient()

    # Chuyển đổi hình ảnh từ OpenCV (BGR) sang RGB và mã hóa thành PNG
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    success, encoded_image = cv2.imencode('.png', image_rgb)
    if not success:
        print("Không thể mã hóa hình ảnh để thực hiện OCR.")
        return []

    content = encoded_image.tobytes()

    vision_image = vision.Image(content=content)

    response = client.text_detection(image=vision_image)
    texts = response.text_annotations

    ocr_results = []

    if not texts:
        print("Không phát hiện văn bản trong hình ảnh này.")
        return ocr_results

    # Phần tử đầu tiên chứa toàn bộ văn bản được phát hiện
    # Các phần tử tiếp theo là từng từ hoặc dòng riêng lẻ
    for text in texts[1:]:  # Bỏ qua phần tử đầu tiên
        bbox = []
        vertices = text.bounding_poly.vertices
        for vertex in vertices:
            bbox.append([vertex.x, vertex.y])
        ocr_results.append({
            "text": text.description.strip(),
            "bbox": bbox
        })

    if response.error.message:
        raise Exception(
            f"{response.error.message}\nĐể biết thêm thông tin về các thông báo lỗi, kiểm tra: "
            "https://cloud.google.com/apis/design/errors"
        )

    return ocr_results

def save_bbox_info_json(image_url, combined_detections, image_width, image_height):
    """
    Xử lý kết quả phát hiện YOLO và OCR và trả về dưới dạng JSON thay vì lưu file.

    Parameters:
    - image_url: URL của hình ảnh gốc.
    - combined_detections: List các dictionary chứa 'text' và 'bbox' từ YOLO và OCR.
    - image_width: Chiều rộng của hình ảnh gốc.
    - image_height: Chiều cao của hình ảnh gốc.

    Returns:
    - JSON chứa tên hình ảnh và các cặp 'text' và 'bbox'.
    """
    # Lọc các detections để chỉ giữ 'text' và 'bbox'
    filtered_detections = []
    for det in combined_detections:
        # Chỉ giữ 'text' và 'bbox'
        text = det.get("text", "")
        bbox = det.get("bbox", [])

        # Chuyển đổi bbox sang tọa độ tương đối
        relative_bbox = []
        for point in bbox:
            x_rel = point[0] / image_width
            y_rel = point[1] / image_height
            relative_bbox.append([x_rel, y_rel])

        filtered_det = {
            "text": text,
            "bbox": relative_bbox
        }
        filtered_detections.append(filtered_det)

    json_data = { "data":{
        "image": image_url,
        "json": filtered_detections
    }}
    return json_data

# def save_bbox_info_json(image_url,image_name, combined_detections, output_ocr_folder, image_width, image_height):
#     """
#     Lưu kết quả phát hiện YOLO và OCR vào file JSON được đặt tên theo hình ảnh gốc.
#     Loại bỏ các khóa 'label' và 'confidence' và chỉ lưu 'text' và 'bbox' với bbox là tọa độ tương đối.
#
#     Parameters:
#     - image_name: Tên file hình ảnh gốc.
#     - combined_detections: List các dictionary chứa 'text' và 'bbox' từ YOLO và OCR.
#     - output_ocr_folder: Thư mục để lưu các file JSON.
#     - image_width: Chiều rộng của hình ảnh gốc.
#     - image_height: Chiều cao của hình ảnh gốc.
#     """
#     # Lọc các detections để chỉ giữ 'text' và 'bbox'
#     filtered_detections = []
#     for det in combined_detections:
#         # Chỉ giữ 'text' và 'bbox'
#         text = det.get("text", "")
#         bbox = det.get("bbox", [])
#
#         # Chuyển đổi bbox sang tọa độ tương đối
#         relative_bbox = []
#         for point in bbox:
#             x_rel = point[0] / image_width
#             y_rel = point[1] / image_height
#             relative_bbox.append([x_rel, y_rel])
#
#         filtered_det = {
#             "text": text,
#             "bbox": relative_bbox
#         }
#         filtered_detections.append(filtered_det)
#
#     json_data = { "data":{
#         "image": image_url,
#         "json": filtered_detections
#     }}
#
#     json_filename = os.path.splitext(image_name)[0] + '.json'
#     json_path = os.path.join(output_ocr_folder, json_filename)
#
#     with open(json_path, 'w', encoding='utf-8') as f:
#         json.dump(json_data, f, ensure_ascii=False, indent=4)
#
#     print(f"Đã lưu kết quả OCR và YOLO vào {json_path}")
def compute_iou(bbox1, bbox2):
    """
    Tính Intersection over Union (IoU) giữa hai bounding boxes.

    Parameters:
    - bbox1, bbox2: List các tọa độ [x, y] cho bốn đỉnh của bounding box.

    Returns:
    - Giá trị IoU.
    """
    # Chuyển đổi thành mảng numpy
    bbox1 = np.array(bbox1)
    bbox2 = np.array(bbox2)

    # Lấy tọa độ min và max cho các bounding box theo trục
    x1_min, y1_min = np.min(bbox1, axis=0)
    x1_max, y1_max = np.max(bbox1, axis=0)
    x2_min, y2_min = np.min(bbox2, axis=0)
    x2_max, y2_max = np.max(bbox2, axis=0)

    # Tính tọa độ giao nhau
    inter_min_x = max(x1_min, x2_min)
    inter_min_y = max(y1_min, y2_min)
    inter_max_x = min(x1_max, x2_max)
    inter_max_y = min(y1_max, y2_max)

    # Tính diện tích giao nhau
    inter_width = max(0, inter_max_x - inter_min_x)
    inter_height = max(0, inter_max_y - inter_min_y)
    inter_area = inter_width * inter_height

    # Tính diện tích của các bounding box
    area1 = (x1_max - x1_min) * (y1_max - y1_min)
    area2 = (x2_max - x2_min) * (y2_max - y2_min)

    # Tính IoU
    union_area = area1 + area2 - inter_area
    if union_area == 0:
        return 0
    iou = inter_area / union_area
    return iou

def non_max_suppression(combined_detections, iou_threshold=0.3):
    """
    Áp dụng Non-Maximum Suppression để loại bỏ các bounding boxes chồng lấp.

    Parameters:
    - combined_detections: List các dictionary chứa 'text' và 'bbox'.
    - iou_threshold: Ngưỡng IoU để coi các bounding boxes là chồng lấp.

    Returns:
    - List đã lọc các kết quả OCR và YOLO với các bounding boxes không chồng lấp.
    """
    if not combined_detections:
        return []

    # Sắp xếp kết quả theo diện tích của bounding box giảm dần
    sorted_results = sorted(
        combined_detections,
        key=lambda x: (x['bbox'][2][0] - x['bbox'][0][0]) * (x['bbox'][2][1] - x['bbox'][0][1]),
        reverse=True
    )

    keep = []
    while sorted_results:
        current = sorted_results.pop(0)
        keep.append(current)
        sorted_results = [
            item for item in sorted_results
            if compute_iou(current['bbox'], item['bbox']) < iou_threshold
        ]

    return keep
