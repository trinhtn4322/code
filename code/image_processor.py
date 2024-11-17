# image_processor.py

import os
import cv2
from sklearn.cluster import DBSCAN
import numpy as np
import shutil


def group_centers(centers, axis=0, threshold=50):
    """
    Nhóm các trung tâm dựa trên khoảng cách theo trục được chỉ định.

    Args:
        centers (list of tuples): Danh sách các trung tâm (x, y).
        axis (int): 0 cho trục x (dọc), 1 cho trục y (ngang).
        threshold (int): Ngưỡng khoảng cách để nhóm.

    Returns:
        list of lists: Danh sách các nhóm, mỗi nhóm là danh sách các chỉ số trong centers.
    """
    groups = []
    centers_sorted = sorted(enumerate(centers), key=lambda c: c[1][axis])
    group = []
    prev_value = None
    for idx, center in centers_sorted:
        value = center[axis]
        if prev_value is None or abs(value - prev_value) <= threshold:
            group.append(idx)
        else:
            groups.append(group)
            group = [idx]
        prev_value = value
    if group:
        groups.append(group)
    return groups


def select_sorted_vertical_groups(vertical_groups, centers, image_width):
    """
    Sắp xếp các nhóm dọc theo ưu tiên: bên trái nhất trước, sau đó bên phải.

    Args:
        vertical_groups (list of lists): Danh sách các nhóm dọc.
        centers (list of tuples): Danh sách các trung tâm (x, y).
        image_width (int): Chiều rộng của hình ảnh.

    Returns:
        list of lists: Các nhóm dọc đã được sắp xếp theo ưu tiên.
    """
    # Tính trung bình x của mỗi nhóm dọc
    groups_with_avg_x = [(g, sum(centers[idx][0] for idx in g) / len(g)) for g in vertical_groups]

    # Sắp xếp các nhóm theo trung bình x từ nhỏ đến lớn (từ trái sang phải)
    groups_with_avg_x_sorted = sorted(groups_with_avg_x, key=lambda x: x[1])

    # Trả về danh sách các nhóm đã sắp xếp theo ưu tiên
    sorted_vertical_groups = [g for g, avg_x in groups_with_avg_x_sorted]
    return sorted_vertical_groups


def select_sorted_horizontal_groups(horizontal_groups, centers, image_height):
    """
    Sắp xếp các nhóm ngang theo ưu tiên: nhóm nằm dưới nhất trước, sau đó nhóm nằm trên.

    Args:
        horizontal_groups (list of lists): Danh sách các nhóm ngang.
        centers (list of tuples): Danh sách các trung tâm (x, y).
        image_height (int): Chiều cao của hình ảnh.

    Returns:
        list of lists: Các nhóm ngang đã được sắp xếp theo ưu tiên.
    """
    # Tính trung bình y của mỗi nhóm ngang
    groups_with_avg_y = [(g, sum(centers[idx][1] for idx in g) / len(g)) for g in horizontal_groups]

    # Sắp xếp các nhóm theo trung bình y từ lớn đến nhỏ (từ dưới lên trên)
    groups_with_avg_y_sorted = sorted(groups_with_avg_y, key=lambda x: x[1], reverse=True)

    # Trả về danh sách các nhóm đã sắp xếp theo ưu tiên
    sorted_horizontal_groups = [g for g, avg_y in groups_with_avg_y_sorted]
    return sorted_horizontal_groups


def crop_image_custom(image, crop_x_min, crop_y_min, crop_width, crop_height):
    """
    Cắt hình ảnh với các giới hạn được xác định, đảm bảo không vượt quá biên hình ảnh.

    Args:
        image (numpy.ndarray): Hình ảnh gốc.
        crop_x_min (int): Tọa độ x tối thiểu của vùng cắt.
        crop_y_min (int): Tọa độ y tối thiểu của vùng cắt.
        crop_width (int): Chiều rộng vùng cắt.
        crop_height (int): Chiều cao vùng cắt.

    Returns:
        numpy.ndarray: Hình ảnh đã cắt.
    """
    x_min = max(crop_x_min, 0)
    y_min = max(crop_y_min, 0)
    x_max = min(crop_x_min + crop_width, image.shape[1])
    y_max = min(crop_y_min + crop_height, image.shape[0])

    # Điều chỉnh nếu vùng cắt nhỏ hơn kích thước yêu cầu
    if x_max - x_min < crop_width:
        if x_min == 0:
            x_max = min(crop_width, image.shape[1])
        elif x_max == image.shape[1]:
            x_min = max(image.shape[1] - crop_width, 0)

    if y_max - y_min < crop_height:
        if y_min == 0:
            y_max = min(crop_height, image.shape[0])
        elif y_max == image.shape[0]:
            y_min = max(image.shape[0] - crop_height, 0)

    x_min = int(x_min)
    y_min = int(y_min)
    x_max = int(x_max)
    y_max = int(y_max)

    cropped_image = image[y_min:y_max, x_min:x_max]
    return cropped_image


def count_bboxes_in_crop(bboxes, crop_x_min, crop_y_min, crop_width, crop_height):
    """
    Đếm số bounding boxes nằm trong vùng cắt.

    Args:
        bboxes (list of tuples): Danh sách bounding boxes (x_min, y_min, x_max, y_max).
        crop_x_min (int): Tọa độ x tối thiểu của vùng cắt.
        crop_y_min (int): Tọa độ y tối thiểu của vùng cắt.
        crop_width (int): Chiều rộng vùng cắt.
        crop_height (int): Chiều cao vùng cắt.

    Returns:
        int: Số bounding boxes trong vùng cắt.
    """
    count = 0
    crop_x_max = crop_x_min + crop_width
    crop_y_max = crop_y_min + crop_height
    for bbox in bboxes:
        x_min, y_min, x_max, y_max = bbox  # Unpack đúng cách
        # Kiểm tra xem bounding box có giao với vùng cắt hay không
        if (x_min < crop_x_max and x_max > crop_x_min and
                y_min < crop_y_max and y_max > crop_y_min):
            count += 1
    return count


def determine_horizontal_crop_direction(group_centers, image_height):
    """
    Xác định hướng cắt ngang dựa trên vị trí trung bình y của nhóm trục ngang.

    Args:
        group_centers (list of tuples): Danh sách các trung tâm trong nhóm ngang được chọn.
        image_height (int): Chiều cao của hình ảnh.

    Returns:
        str: 'bottom_up' hoặc 'top_down'.
    """
    avg_y = sum([center[1] for center in group_centers]) / len(group_centers)
    return 'bottom_up' if avg_y > image_height / 2 else 'top_down'


def determine_vertical_crop_direction(group_centers, image_width):
    """
    Xác định hướng cắt dọc dựa trên vị trí trung bình x của nhóm trục dọc.

    Args:
        group_centers (list of tuples): Danh sách các trung tâm trong nhóm trục dọc được chọn.
        image_width (int): Chiều rộng của hình ảnh.

    Returns:
        str: 'left_to_right' hoặc 'right_to_left'.
    """
    avg_x = sum([center[0] for center in group_centers]) / len(group_centers)
    return 'left_to_right' if avg_x < image_width / 2 else 'right_to_left'


def convert_all_images(detections_dict, image_folder, final_output_folder,
                       fixed_width_crop=500, fixed_height_crop=750, padding=100,
                       group_threshold_vertical=50, group_threshold_horizontal=50,  # Điều chỉnh ngưỡng phân nhóm
                       prefer_left=True, prefer_bottom=True):  # prefer_bottom=True để ưu tiên nhóm ngang nằm dưới
    """
    Xử lý tất cả các hình ảnh: phát hiện trục, nhóm trục, chọn nhóm ưu tiên, và cắt ảnh.

    Args:
        detections_dict (dict): Từ điển chứa các detections cho mỗi hình ảnh.
        image_folder (str): Thư mục chứa hình ảnh gốc.
        final_output_folder (str): Thư mục lưu các ảnh đã cắt và các thông tin liên quan.
        fixed_width_crop (int): Chiều rộng cố định cho vùng cắt dọc.
        fixed_height_crop (int): Chiều cao cố định cho vùng cắt ngang.
        padding (int): Khoảng đệm cho vùng cắt.
        group_threshold_vertical (int): Ngưỡng phân nhóm cho trục dọc.
        group_threshold_horizontal (int): Ngưỡng phân nhóm cho trục ngang.
        prefer_left (bool): Ưu tiên chọn nhóm trục dọc bên trái nhất nếu có nhiều nhóm.
        prefer_bottom (bool): Ưu tiên chọn nhóm trục ngang nằm dưới nhất nếu có nhiều nhóm.

    Returns:
        list: Danh sách các thông tin về các ảnh đã cắt.
    """
    os.makedirs(final_output_folder, exist_ok=True)
    image_crop_folder = os.path.join(final_output_folder, "image_crop")
    if os.path.exists(image_crop_folder):
        try:
            shutil.rmtree(image_crop_folder)
            print(f"Đã xóa thư mục: {image_crop_folder}")
        except Exception as e:
            print(f"Lỗi khi xóa thư mục: {e}")
    else:
        print("Thư mục không tồn tại.")
    os.makedirs(image_crop_folder, exist_ok=True)

    cropped_images = []
    skipped_images = []
    MIN_BBOX_IN_CROP = 1

    for image_file, detections in detections_dict.items():
        image_path = os.path.join(image_folder, image_file)
        image = cv2.imread(image_path)
        if image is None:
            print(f"[ERROR] Không thể tải hình ảnh từ {image_path}. Bỏ qua.")
            skipped_images.append(image_file)
            continue

        bboxes_scaled = []
        centers = []
        for item in detections:
            bbox = item['bbox']
            if len(bbox) < 3:
                print(f"[WARNING] Bounding box không hợp lệ trong {image_file}: {bbox}. Bỏ qua bbox này.")
                continue
            x_min, y_min = bbox[0]
            x_max, y_max = bbox[2]
            bboxes_scaled.append((int(x_min), int(y_min), int(x_max), int(y_max)))
            x_center = (x_min + x_max) / 2
            y_center = (y_min + y_max) / 2
            centers.append((int(x_center), int(y_center)))

        # Nhóm các bounding boxes theo dọc và ngang
        vertical_groups = group_centers(centers, axis=0, threshold=group_threshold_vertical)
        horizontal_groups = group_centers(centers, axis=1, threshold=group_threshold_horizontal)

        print(f"[DEBUG] {image_file}: Số nhóm dọc = {len(vertical_groups)}, Số nhóm ngang = {len(horizontal_groups)}")

        # Kiểm tra điều kiện hợp lệ: có ít nhất 1 nhóm dọc và 1 nhóm ngang
        if len(vertical_groups) < 1 or len(horizontal_groups) < 1:
            print(f"[INFO] Ảnh {image_file} thiếu ít nhất một nhóm trục dọc hoặc nhóm trục ngang. Bỏ qua.")
            skipped_images.append(image_file)
            continue

        image_width = image.shape[1]
        image_height = image.shape[0]

        # Sắp xếp các nhóm dọc theo ưu tiên
        sorted_vertical_groups = select_sorted_vertical_groups(vertical_groups, centers, image_width)
        print(f"[DEBUG] {image_file}: Các nhóm dọc đã sắp xếp theo ưu tiên: {sorted_vertical_groups}")

        # Sắp xếp các nhóm ngang theo ưu tiên
        sorted_horizontal_groups = select_sorted_horizontal_groups(horizontal_groups, centers, image_height)
        print(f"[DEBUG] {image_file}: Các nhóm ngang đã sắp xếp theo ưu tiên: {sorted_horizontal_groups}")

        # Khởi tạo danh sách tạm để lưu thông tin cắt theo dọc và ngang
        vertical_crops = []
        horizontal_crops = []
        crop_counter = 1

        # Xử lý nhóm dọc theo ưu tiên
        for group in sorted_vertical_groups:
            if vertical_crops:
                break  # Đã có crop dọc, không cần xử lý thêm
            print(f"[DEBUG] {image_file}: Xử lý nhóm dọc {group}")
            vertical_centers = [centers[idx] for idx in group]
            vertical_centers_sorted = sorted(vertical_centers, key=lambda c: c[1])  # Sắp xếp theo y từ trên xuống dưới
            vertical_crop_direction = determine_vertical_crop_direction(vertical_centers, image_width)
            print(f"[DEBUG] {image_file}: Hướng cắt dọc = {vertical_crop_direction}")

            for i in range(len(vertical_centers_sorted) - 1):
                print(f"--------------{image_file} vertical --------------")
                print("thông số")
                pt1 = vertical_centers_sorted[i]
                pt2 = vertical_centers_sorted[i + 1]
                distance_y = abs(pt2[1] - pt1[1])
                print(pt1, pt2)
                print(distance_y)

                crop_height = distance_y + padding
                crop_width = fixed_width_crop
                if vertical_crop_direction == 'left_to_right':
                    crop_x_min = min(pt1[0], pt2[0]) - (padding // 2)
                else:
                    crop_x_min = max(pt1[0], pt2[0]) - fixed_width_crop + (padding // 2)
                crop_y_min = min(pt1[1], pt2[1]) - (padding // 2)

                bbox_count = count_bboxes_in_crop(bboxes_scaled, crop_x_min, crop_y_min, crop_width, crop_height)
                print(f"[DEBUG] {image_file}: Số bbox trong vùng cắt dọc = {bbox_count}")
                if bbox_count < MIN_BBOX_IN_CROP:
                    print(f"[DEBUG] {image_file}: Vùng cắt dọc không đủ bbox. Bỏ qua.")
                    continue

                cropped_image = crop_image_custom(image, crop_x_min, crop_y_min, crop_width, crop_height)
                actual_width = cropped_image.shape[1]
                actual_height = cropped_image.shape[0]

                # Kiểm tra tỉ lệ khung hình
                if (actual_width / actual_height > 7) or (actual_height / actual_width > 7):
                    print(
                        f"[DEBUG] {image_file}: Vùng cắt dọc {image_file} có tỉ lệ {actual_width}:{actual_height} không hợp lệ. Bỏ crop này.")
                    continue

                filename = f"{os.path.splitext(image_file)[0]}_vertical_crop_{crop_counter}.png"
                save_path = os.path.join(image_crop_folder, filename)
                cv2.imwrite(save_path, cropped_image)
                crop_info = {
                    "filename": filename,
                    "original_image": image_file,
                    "x_offset": int(crop_x_min),
                    "y_offset": int(crop_y_min),
                    "crop_width": actual_width,
                    "crop_height": actual_height
                }
                vertical_crops.append(crop_info)
                print(f"[INFO] {image_file}: Đã lưu cắt dọc {filename}")
                crop_counter += 1

        # Xử lý nhóm ngang theo ưu tiên
        for group in sorted_horizontal_groups:
            if horizontal_crops:
                break  # Đã có crop ngang, không cần xử lý thêm
            print(f"[DEBUG] {image_file}: Xử lý nhóm ngang {group}")
            horizontal_centers = [centers[idx] for idx in group]
            horizontal_centers_sorted = sorted(horizontal_centers,
                                               key=lambda c: c[0])  # Sắp xếp theo x từ trái sang phải
            horizontal_crop_direction = determine_horizontal_crop_direction(horizontal_centers, image_height)
            print(f"[DEBUG] {image_file}: Hướng cắt ngang = {horizontal_crop_direction}")

            for i in range(len(horizontal_centers_sorted) - 1):
                print(f"--------------{image_file} horizontal--------------")
                print("thông số")
                pt1 = horizontal_centers_sorted[i]
                pt2 = horizontal_centers_sorted[i + 1]
                distance_x = abs(pt2[0] - pt1[0])
                print(pt1, pt2)
                print(distance_x)

                crop_width = distance_x + padding
                crop_height = fixed_height_crop
                crop_x_min = min(pt1[0], pt2[0]) - (padding // 2)
                if horizontal_crop_direction == 'bottom_up':
                    crop_y_min = max(pt1[1], pt2[1]) - crop_height + (padding // 2)
                else:
                    crop_y_min = min(pt1[1], pt2[1]) - (padding // 2)

                bbox_count = count_bboxes_in_crop(bboxes_scaled, crop_x_min, crop_y_min, crop_width, crop_height)
                print(f"[DEBUG] {image_file}: Số bbox trong vùng cắt ngang = {bbox_count}")
                if bbox_count < MIN_BBOX_IN_CROP:
                    print(f"[DEBUG] {image_file}: Vùng cắt ngang không đủ bbox. Bỏ qua.")
                    continue

                cropped_image = crop_image_custom(image, crop_x_min, crop_y_min, crop_width, crop_height)
                actual_width = cropped_image.shape[1]
                actual_height = cropped_image.shape[0]

                # Kiểm tra tỉ lệ khung hình
                if (actual_width / actual_height > 7) or (actual_height / actual_width > 7):
                    print(
                        f"[DEBUG] {image_file}: Vùng cắt ngang {filename} có tỉ lệ {actual_width}:{actual_height} không hợp lệ. Bỏ crop này.")
                    continue

                filename = f"{os.path.splitext(image_file)[0]}_horizontal_crop_{crop_counter}.png"
                save_path = os.path.join(image_crop_folder, filename)
                cv2.imwrite(save_path, cropped_image)
                crop_info = {
                    "filename": filename,
                    "original_image": image_file,
                    "x_offset": int(crop_x_min),
                    "y_offset": int(crop_y_min),
                    "crop_width": actual_width,
                    "crop_height": actual_height
                }
                horizontal_crops.append(crop_info)
                print(f"[INFO] {image_file}: Đã lưu cắt ngang {filename}")
                crop_counter += 1

        # Kiểm tra nếu đã có ít nhất một crop dọc và một crop ngang
        vertical_has_valid_crop = len(vertical_crops) > 0
        horizontal_has_valid_crop = len(horizontal_crops) > 0

        if vertical_has_valid_crop and horizontal_has_valid_crop:
            cropped_images.extend(vertical_crops)
            cropped_images.extend(horizontal_crops)
            print(
                f"[INFO] Đã lưu {len(vertical_crops)} cắt dọc và {len(horizontal_crops)} cắt ngang từ hình ảnh {image_file}.")
        else:
            # Nếu một trong hai hướng thiếu crop hợp lệ, bỏ qua hình ảnh
            if vertical_groups and not vertical_has_valid_crop:
                print(f"[INFO] Vùng cắt dọc trong hình ảnh {image_file} không đủ bbox. Bỏ qua hình ảnh.")
            if horizontal_groups and not horizontal_has_valid_crop:
                print(f"[INFO] Vùng cắt ngang trong hình ảnh {image_file} không đủ bbox. Bỏ qua hình ảnh.")
            skipped_images.append(image_file)
            # Xóa các file cắt đã lưu tạm thời nếu có
            for crop in vertical_crops + horizontal_crops:
                crop_path = os.path.join(image_crop_folder, crop["filename"])
                if os.path.exists(crop_path):
                    os.remove(crop_path)

    # Báo cáo các hình ảnh bị bỏ qua
    if skipped_images:
        print("\n################## Các hình ảnh bị bỏ qua ##################")
        for img in skipped_images:
            print(f"- {img}")
    else:
        print("\nKhông có hình ảnh nào bị bỏ qua.")

    return cropped_images
