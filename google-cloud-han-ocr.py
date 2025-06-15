import os
import io
import json
from google.cloud import vision
from google.cloud.vision_v1 import types
import numpy as np

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "./auth.json"

# Khởi tạo client
client = vision.ImageAnnotatorClient()

def save_response_to_file(response, output_path='./output_google_vision/ocr_response.json'):
    from google.protobuf.json_format import MessageToDict
    response_dict = MessageToDict(response._pb)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(response_dict, f, ensure_ascii=False, indent=2)

def extract_boxes_from_response(response):
    document = response.full_text_annotation
    boxes = []

    if not document or not document.pages:
        print("⚠️ Không có dữ liệu text trong ảnh")
        return []

    for page in document.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    word_text = ''.join([s.text for s in word.symbols])
                    vertices = word.bounding_box.vertices
                    box_coords = []
                    for v in vertices:
                        box_coords.extend([v.x, v.y])
                    boxes.append({
                        'text': word_text,
                        'box_coords': box_coords
                    })
    return boxes

def merge_vertical_text(boxes, x_thresh=25):
    """
    Gom chữ theo chiều dọc (trên xuống dưới) rồi nối các cột từ trái sang phải.
    """
    for box in boxes:
        coords = np.array(box['box_coords']).reshape(-1, 2)
        center_x = np.mean(coords[:, 0])
        center_y = np.mean(coords[:, 1])
        box['center_x'] = center_x
        box['center_y'] = center_y

    # Gom nhóm theo cột (X gần nhau)
    columns = []
    for box in sorted(boxes, key=lambda b: b['center_x']):
        matched = False
        for col in columns:
            if abs(col[0]['center_x'] - box['center_x']) < x_thresh:
                col.append(box)
                matched = True
                break
        if not matched:
            columns.append([box])

    # Sắp chữ trong mỗi cột theo Y (top → bottom), rồi ghép lại
    merged_columns = []
    for col in columns:
        sorted_col = sorted(col, key=lambda b: b['center_y'])
        merged_text = ''.join([b['text'] for b in sorted_col])
        merged_columns.append(merged_text)

    return merged_columns

def ocr_vertical_image(image_path, output_text_path='./output_google_vision/ocr_result.txt'):
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    # Thêm language hint để ưu tiên OCR tiếng Hán
    image_context = vision.ImageContext(language_hints=["zh"])

    response = client.document_text_detection(image=image, image_context=image_context)

    # Lưu toàn bộ response (nếu cần debug)
    save_response_to_file(response, './output_google_vision/ocr_page4_response.json')

    boxes = extract_boxes_from_response(response)
    merged_text_lines = merge_vertical_text(boxes)

    # Ghi kết quả ra file
    with open(output_text_path, 'w', encoding='utf-8') as f:
        for line in merged_text_lines:
            f.write(line + '\n')

    print(f"✅ OCR hoàn tất! Đã lưu vào {output_text_path}")

# --- Chạy thử ---
if __name__ == '__main__':
    ocr_vertical_image('./resized_img/page4.png', './output_google_vision/page4_ocr_result.txt')

