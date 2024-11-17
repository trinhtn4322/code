# detect_yolo.py

import os
from ultralytics import YOLO

def get_detections(image_path, model_path='model/best.pt', confidence_threshold=0.7):
    """
    Perform YOLO detection on a single image and return the results as a dictionary.
    
    Parameters:
    - image_path: Path to the image file.
    - model_path: Path to the YOLO model weights.
    - confidence_threshold: Confidence threshold to consider detections valid.
    
    Returns:
    - detections_dict: Dictionary mapping the image filename to its list of detections.
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"The image file {image_path} does not exist.")
    
    # Load the YOLO model
    model = YOLO(model_path)
    # model.to('cuda')  # Uncomment if you want to use GPU
    
    image_file = os.path.basename(image_path)
    detections_dict = {}
    
    # Perform detection on the image
    results = model(image_path)
    
    # Process results to match the desired format
    detections = []
    for result in results:
        for det in result.boxes:
            confidence = float(det.conf)
            
            # Only add detections with confidence above the threshold
            if confidence > confidence_threshold:
                label = result.names[int(det.cls)]
                # Get original image dimensions
                orig_width, orig_height = result.orig_shape[1], result.orig_shape[0]
                x_min = float(det.xyxy[0][0])
                y_min = float(det.xyxy[0][1])
                x_max = float(det.xyxy[0][2])
                y_max = float(det.xyxy[0][3])
                
                # Convert bbox to a list of absolute coordinates
                bbox = [
                    [int(x_min), int(y_min)],
                    [int(x_max), int(y_min)],
                    [int(x_max), int(y_max)],
                    [int(x_min), int(y_max)]
                ]
                
                detections.append({
                    "label": label,       # Keep 'label' for image_processor.py
                    "confidence": confidence,
                    "text": "A",          # Add default 'text' as "A"
                    "bbox": bbox          # Bbox as absolute coordinates
                })
    
    if detections:
        detections_dict[image_file] = detections

    return detections_dict 

# If you still want to run detect_yolo.py independently, keep this section unchanged
if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) != 2:
        print("Usage: python detect_yolo.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    try:
        detections = get_detections(image_path)
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)

    # Optionally, save the results to JSON (not required as per current requirements)
    output_folder = 'outsource/json'
    os.makedirs(output_folder, exist_ok=True)

    for image_file, dets in detections.items():
        json_filename = os.path.splitext(image_file)[0] + '.json'
        json_filepath = os.path.join(output_folder, json_filename)
        with open(json_filepath, 'w') as f:
            json.dump(dets, f, indent=4)

    print(f"Detection completed. JSON file is saved in {output_folder}")
