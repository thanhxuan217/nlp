import re
import numpy as np
import hanzidentifier


def is_chinese(text):
    return hanzidentifier.has_chinese(text)

def is_page_number(text):
    # Loại nếu chỉ toàn số hoặc dạng "第X页"
    return re.fullmatch(r'\d+', text)

def is_normal_box(box, max_width=300, max_height=300, min_width=15, min_height=15, aspect_lo=0.8, aspect_hi=1.2):
    """
    Kiểm tra xem box có hợp lệ hay không.

    Điều kiện hợp lệ:
        - 4 điểm (tọa độ) hợp lệ
        - Góc vuông ~90 độ
        - Không quá to (cả width và height)
        - Không quá nhỏ (tránh nhiễu)
        - Không gần vuông (loại bỏ ký tự không phải chữ Hán-Nôm)

    Args:
        box (list): List 4 điểm [[x1, y1], ..., [x4, y4]]
        max_width (int): chiều rộng tối đa
        max_height (int): chiều cao tối đa
        min_width (int): chiều rộng tối thiểu
        min_height (int): chiều cao tối thiểu
        aspect_lo (float): ngưỡng dưới aspect ratio để loại box gần vuông
        aspect_hi (float): ngưỡng trên aspect ratio để loại box gần vuông

    Returns:
        bool: True nếu hợp lệ, False nếu loại bỏ
    """
    box = np.array(box)
    if box.shape != (4, 2):
        return False

    # Kiểm tra góc gần vuông
    vecs = [box[(i + 1) % 4] - box[i] for i in range(4)]
    angles = []
    for i in range(4):
        v1 = vecs[i]
        v2 = vecs[(i + 1) % 4]
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        angle = np.arccos(np.clip(cos_angle, -1, 1)) * 180 / np.pi
        angles.append(angle)
    if not all(75 < a < 105 for a in angles):
        return False

    # Tính width, height, aspect ratio
    x_coords = box[:, 0]
    y_coords = box[:, 1]
    width = max(x_coords) - min(x_coords)
    height = max(y_coords) - min(y_coords)
    aspect_ratio = height / (width + 1e-6)

    # Loại nếu quá to toàn diện
    if width > max_width and height > max_height:
        return False

    # Loại nếu quá nhỏ
    if width < min_width or height < min_height:
        return False

    # Loại nếu gần vuông (nghi nhiễu)
    if aspect_lo < aspect_ratio < aspect_hi:
        return False

    return True


def clean_ocr_data(rec_polys, rec_texts, rec_scores):
    filtered_polys = []
    filtered_texts = []
    filtered_scores = []
    for poly, text, score in zip(rec_polys, rec_texts, rec_scores):
        remove = False
        if not is_chinese(text):
            print(f"Loại do không phải chữ Hán: {text}")
            remove = True
        elif is_page_number(text):
            print(f"Loại do là số trang: {text}")
            remove = True
        elif not is_normal_box(poly):
            print(f"Loại do box bất thường: {text} - {poly}")
            remove = True
        elif score < 0.2:
            print(f"Loại do box score quá thấp: {text} - {poly} - {score}")
            remove = True
        if not remove:
            filtered_polys.append(poly)
            filtered_texts.append(text)
            filtered_scores.append(score)
    return filtered_polys, filtered_texts, filtered_scores
