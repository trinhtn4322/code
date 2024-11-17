import os
import cv2
from detect_yolo import get_detections
from image_processor import convert_all_images
from ocr_processor import detect_text_ocr, save_bbox_info_json, non_max_suppression
from my_timer import my_timer  # Ensure you have implemented this decorator

# Set up environment variable for Google Cloud Vision API
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'vision_key.json'

@my_timer
def main(image_path, image_url):
    """
    Main function to perform YOLO detection, image processing, OCR, and save results.
    """
    # Tạo đối tượng rỗng để trả về nếu không có kết quả
    empty_result = []

    # Define paths
    # image_path = "output_final/image/pdf_6_page5.png"
    final_output_folder = "output_final/crop"
    ocr_output_folder = "output_final/ocr"

    # Ensure the output directories exist
    os.makedirs(final_output_folder, exist_ok=True)
    os.makedirs(ocr_output_folder, exist_ok=True)

    print("[INFO] Starting YOLO detection...")
    # Perform YOLO detection
    try:
        detections = get_detections(image_path)
    except FileNotFoundError as e:
        print(e)
        return empty_result

    if not detections:
        print("No detections found. Exiting program.")
        return empty_result

    print("[INFO] YOLO detection completed.")
    print("[INFO] Starting image processing and cropping...")

    # Extract the image folder and image filename
    image_folder = os.path.dirname(image_path)
    image_file = os.path.basename(image_path)

    # Process detections and crop the image
    cropped_images = convert_all_images(
        detections_dict=detections,
        image_folder=image_folder,
        final_output_folder=final_output_folder,
        fixed_width_crop=500,
        fixed_height_crop=500,
        padding=100,
        group_threshold_horizontal=100,
        prefer_left=True,
        prefer_bottom=True
    )

    if not cropped_images:
        print("No cropped images to process for OCR.")
        return empty_result

    print(f"[INFO] Image processing completed. Found {len(cropped_images)} cropped images.")
    print(f"[INFO] Starting OCR processing on cropped images...")

    ocr_results_per_image = {}

    image_crop_folder = os.path.join(final_output_folder, "image_crop")

    for crop in cropped_images:
        cropped_filename = crop['filename']
        original_image = crop['original_image']
        x_offset, y_offset = crop['x_offset'], crop['y_offset']
        cropped_image_path = os.path.join(image_crop_folder, cropped_filename)

        if not os.path.exists(cropped_image_path):
            print(f"[ERROR] Cropped image file {cropped_filename} does not exist. Skipping OCR for this image.")
            continue

        cropped_image = cv2.imread(cropped_image_path)
        if cropped_image is None:
            print(f"[ERROR] Unable to load cropped image from {cropped_image_path}. Skipping OCR for this image.")
            continue

        try:
            ocr_results = detect_text_ocr(cropped_image)

            if not ocr_results:
                print(f"No text detected in crop {cropped_filename} of {original_image}.")
                continue

            filtered_ocr_results = []
            for result in ocr_results:
                text = result['text'].strip()

                if text == '0006':
                    text = '9000'
                if text == '0009':
                    text = '6000'
                if text.isdigit():
                    number = int(text)
                    if number > 50:
                        filtered_ocr_results.append({
                            "text": text,
                            "bbox": result['bbox']
                        })

            if not filtered_ocr_results:
                print(f"No numerical text >50 detected in crop {cropped_filename} of {original_image}.")
                continue

            for result in filtered_ocr_results:
                mapped_bbox = {
                    "text": result['text'],
                    "bbox": [
                        [
                            vertex[0] + x_offset,
                            vertex[1] + y_offset
                        ] for vertex in result['bbox']
                    ]
                }
                ocr_results_per_image.setdefault(original_image, []).append(mapped_bbox)

            print(f"OCR processed for crop {cropped_filename} of {original_image} with {len(filtered_ocr_results)} texts before NMS.")

        except Exception as e:
            print(f"Error processing OCR for crop {cropped_filename} of {original_image}: {e}")

    print(f"[INFO] Combining YOLO and OCR results, applying NMS, and saving to JSON files...")

    for original_image, ocr_detections in ocr_results_per_image.items():
        combined_detections = detections.get(original_image, []) + ocr_detections
        original_image_path = os.path.join(image_folder, original_image)
        original_image_cv = cv2.imread(original_image_path)
        if original_image_cv is None:
            print(f"[ERROR] Unable to load original image from {original_image_path}. Skipping saving results for this image.")
            continue
        image_height, image_width = original_image_cv.shape[:2]

        nms_filtered_results = non_max_suppression(combined_detections, iou_threshold=0.3)

        if not nms_filtered_results:
            print(f"No data after NMS for {original_image}.")
            continue
        else:
            return save_bbox_info_json(image_url, nms_filtered_results, image_width, image_height)
        # n=save_bbox_info_json(image_url, nms_filtered_results, image_width, image_height)
        # n=save_bbox_info_json(image_url,original_image, nms_filtered_results, ocr_output_folder, image_width, image_height)

    # def save_bbox_info_json(image_url, combined_detections, image_width, image_height):
    # if n != []:
    #     print("Process completed successfully.")
    #     return n
    # else:
    #     print("fail")
