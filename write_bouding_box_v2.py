import json
import os
import re
import cv2
import numpy as np
import pandas as pd
import ast

df = pd.read_excel("output_ocr/output_ocr_raw.xlsx")  # Đổi tên file cho phù hợp

def parse_image_box(x):
    try:
        return json.loads(x)
    except Exception:
        return ast.literal_eval(x)

df['Image box'] = df['Image box'].apply(parse_image_box)
df_grouped = df.groupby('Uploaded Filename')['Image box'].agg(list).reset_index()
print(df_grouped)

def get_box_color(box_index):
    """Tạo màu khác nhau cho mỗi box"""
    colors = [
        (139, 0, 0),     # Dark Red
        (0, 100, 0),     # Dark Green
        (0, 0, 139),     # Dark Blue
        (128, 0, 128),   # Purple
        (128, 128, 0),   # Olive
        (139, 69, 19),   # Saddle Brown
        (165, 42, 42),   # Brown
        (184, 134, 11),  # Dark Goldenrod
        (72, 61, 139),   # Dark Slate Blue
        (0, 128, 128),   # Teal
        (205, 92, 92),   # Indian Red
        (70, 130, 180),  # Steel Blue
        (46, 139, 87),   # Sea Green
        (210, 105, 30),  # Chocolate
        (233, 150, 122), # Dark Salmon
        (112, 128, 144), # Slate Gray
        (95, 158, 160),  # Cadet Blue
        (143, 188, 143), # Dark Sea Green
        (160, 82, 45),   # Sienna
        (128, 0, 0),     # Maroon
    ]
    return colors[box_index % len(colors)]

def check_text_overlap(text_pos, existing_positions, min_distance=50):
    """Kiểm tra xem vị trí text có bị trùng với các vị trí đã có không"""
    text_x, text_y = text_pos
    for existing_x, existing_y in existing_positions:
        distance = np.sqrt((text_x - existing_x)**2 + (text_y - existing_y)**2)
        if distance < min_distance:
            return True
    return False

def find_non_overlapping_position(poly, box_index, existing_positions, image_shape, attempt=0):
    """Tìm vị trí không bị trùng cho text"""
    # Lấy bounding box của polygon
    x_coords = [point[0] for point in poly]
    y_coords = [point[1] for point in poly]
    
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)
    center_x, center_y = (min_x + max_x) // 2, (min_y + max_y) // 2
    
    # Danh sách các vị trí ưu tiên để thử
    positions_to_try = [
        (center_x, min_y - 20),           # Trên giữa
        (center_x, max_y + 30),           # Dưới giữa
        (min_x - 30, center_y),           # Trái giữa
        (max_x + 30, center_y),           # Phải giữa
        (min_x - 30, min_y - 20),         # Trên trái
        (max_x + 30, min_y - 20),         # Trên phải
        (min_x - 30, max_y + 30),         # Dưới trái
        (max_x + 30, max_y + 30),         # Dưới phải
        (center_x - 50, min_y - 40),      # Xa hơn - trên trái
        (center_x + 50, min_y - 40),      # Xa hơn - trên phải
        (center_x - 50, max_y + 50),      # Xa hơn - dưới trái
        (center_x + 50, max_y + 50),      # Xa hơn - dưới phải
    ]
    
    for pos in positions_to_try:
        text_x, text_y = pos
        
        # Đảm bảo không vượt ra ngoài ảnh
        text_x = max(30, min(text_x, image_shape[1] - 50))
        text_y = max(30, min(text_y, image_shape[0] - 30))
        
        # Kiểm tra trùng lặp
        if not check_text_overlap((text_x, text_y), existing_positions):
            return text_x, text_y
    
    # Nếu không tìm được vị trí không trùng, dùng vị trí random
    import random
    for _ in range(10):
        text_x = random.randint(50, image_shape[1] - 100)
        text_y = random.randint(50, image_shape[0] - 50)
        if not check_text_overlap((text_x, text_y), existing_positions):
            return text_x, text_y
    
    # Cuối cùng, dùng vị trí mặc định với offset
    return center_x + (attempt * 20), min_y - 20 - (attempt * 15)

def draw_arrow(image, start_point, end_point, color, thickness=2):
    """Vẽ mũi tên từ start_point đến end_point"""
    # Vẽ đường thẳng
    cv2.line(image, start_point, end_point, color, thickness)
    
    # Tính toán góc cho mũi tên
    angle = np.arctan2(end_point[1] - start_point[1], end_point[0] - start_point[0])
    
    # Độ dài và góc của mũi tên
    arrow_length = 10
    arrow_angle = np.pi / 6  # 30 độ
    
    # Tính toán điểm mũi tên
    arrow_p1 = (
        int(end_point[0] - arrow_length * np.cos(angle - arrow_angle)),
        int(end_point[1] - arrow_length * np.sin(angle - arrow_angle))
    )
    arrow_p2 = (
        int(end_point[0] - arrow_length * np.cos(angle + arrow_angle)),
        int(end_point[1] - arrow_length * np.sin(angle + arrow_angle))
    )
    
    # Vẽ mũi tên
    cv2.line(image, end_point, arrow_p1, color, thickness)
    cv2.line(image, end_point, arrow_p2, color, thickness)

def draw_text_with_background(image, text, position, font_scale, color, bg_color, thickness=1):
    """Vẽ text với background"""
    text_x, text_y = position
    
    # Tính kích thước text
    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
    
    # Vẽ background
    padding = 4
    cv2.rectangle(image, 
                 (text_x - padding, text_y - text_size[1] - padding),
                 (text_x + text_size[0] + padding, text_y + padding),
                 bg_color, -1)
    
    # Vẽ viền background
    cv2.rectangle(image, 
                 (text_x - padding, text_y - text_size[1] - padding),
                 (text_x + text_size[0] + padding, text_y + padding),
                 color, 1)
    
    # Vẽ text
    cv2.putText(image, text, (text_x, text_y), 
               cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness + 1, cv2.LINE_AA)
    cv2.putText(image, text, (text_x, text_y), 
               cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)

def create_side_by_side_image(original_image, bbox_image):
    """Tạo ảnh ghép: bbox bên trái, original bên phải"""
    # Lấy kích thước
    h1, w1 = bbox_image.shape[:2]
    h2, w2 = original_image.shape[:2]
    
    # Tạo ảnh ghép với chiều cao bằng ảnh cao nhất
    max_height = max(h1, h2)
    combined_width = w1 + w2 + 20  # Thêm 20px khoảng cách
    
    # Tạo ảnh nền trắng
    combined_image = np.ones((max_height, combined_width, 3), dtype=np.uint8) * 255
    
    # Đặt bbox image bên trái (căn giữa theo chiều dọc)
    y_offset1 = (max_height - h1) // 2
    combined_image[y_offset1:y_offset1+h1, 0:w1] = bbox_image
    
    # Đặt original image bên phải (căn giữa theo chiều dọc)
    y_offset2 = (max_height - h2) // 2
    combined_image[y_offset2:y_offset2+h2, w1+20:w1+20+w2] = original_image
    
    # Vẽ đường phân cách
    cv2.line(combined_image, (w1+10, 0), (w1+10, max_height), (200, 200, 200), 1)
    
    return combined_image

# Lặp qua các file JSON
for idx, row in df_grouped.iterrows():
    filename = row['Uploaded Filename']
    match = re.match(r'page(\d+)_res\.png', filename)
    if not match:
        print(f"❌ Không nhận diện được số trang từ: {filename}")
        continue
    page_number = int(match.group(1))

    rec_polys = row['Image box']        

    # Đọc ảnh gốc
    original_image = cv2.imread("resized_img/page"+ str(page_number) +".png")
    if original_image is None:
        print(f"❌ Không thể đọc ảnh: page{page_number}.png")
        continue
    
    # Tạo ảnh với bounding boxes
    bbox_image = original_image.copy()
    
    print(f"📄 Xử lý trang {page_number} với {len(rec_polys)} bounding boxes")
    
    # VERSION 1: CLEAN - Chỉ hiển thị số box với mũi tên
    existing_text_positions = []
    
    for i, poly in enumerate(rec_polys):
        # Lấy màu riêng cho mỗi box
        box_color = get_box_color(i)
        
        # Vẽ bounding box với màu riêng
        pts = np.array(poly, np.int32).reshape((-1,1,2))
        cv2.polylines(bbox_image, [pts], isClosed=True, color=box_color, thickness=2)
        
        # Tìm vị trí text không bị trùng
        text_x, text_y = find_non_overlapping_position(poly, i, existing_text_positions, bbox_image.shape)
        existing_text_positions.append((text_x, text_y))
        
        # Tính center của box để vẽ mũi tên
        x_coords = [point[0] for point in poly]
        y_coords = [point[1] for point in poly]
        center_x = (min(x_coords) + max(x_coords)) // 2
        center_y = (min(y_coords) + max(y_coords)) // 2
        
        # Vẽ mũi tên từ text đến center của box
        arrow_color = tuple(max(0, int(c * 0.8)) for c in box_color)  # Màu đậm hơn một chút
        draw_arrow(bbox_image, (text_x + 15, text_y - 10), (center_x, center_y), arrow_color, 2)
        
        # Vẽ text với background
        text = f"{i+1}"
        bg_color = tuple(min(255, int(c * 0.3)) for c in box_color)  # Màu nhạt làm background
        draw_text_with_background(bbox_image, text, (text_x, text_y), 0.7, box_color, bg_color, 1)
    
    # Tạo ảnh ghép side-by-side
    combined_clean = create_side_by_side_image(original_image, bbox_image)
    cv2.imwrite("output_write_box/page"+ str(page_number) +"_sidebyside_clean.jpg", combined_clean)

# VERSION 2: DETAILED - Hiển thị đầy đủ tọa độ với mũi tên
print("\n🔄 Tạo version chi tiết...")

for idx, row in df_grouped.iterrows():
    filename = row['Uploaded Filename']
    match = re.match(r'page(\d+)_res\.png', filename)
    if not match:
        print(f"❌ Không nhận diện được số trang từ: {filename}")
        continue
    page_number = int(match.group(1))

    rec_polys = row['Image box']   

    original_image = cv2.imread("resized_img/page"+ str(page_number) +".png")
    if original_image is None:
        continue
    
    # Tạo ảnh với bounding boxes (có overlay mờ)
    bbox_image = original_image.copy()
    overlay = bbox_image.copy()
    cv2.rectangle(overlay, (0, 0), (bbox_image.shape[1], bbox_image.shape[0]), (0, 0, 0), -1)
    bbox_image = cv2.addWeighted(bbox_image, 0.7, overlay, 0.3, 0)
    
    existing_text_positions = []
    
    for i, poly in enumerate(rec_polys):
        # Lấy màu riêng cho mỗi box
        box_color = get_box_color(i)
        
        # Vẽ bounding box với màu nổi bật hơn
        pts = np.array(poly, np.int32).reshape((-1,1,2))
        cv2.polylines(bbox_image, [pts], isClosed=True, color=box_color, thickness=3)
        
        # Tìm vị trí text không bị trùng
        text_x, text_y = find_non_overlapping_position(poly, i, existing_text_positions, bbox_image.shape, attempt=i)
        existing_text_positions.append((text_x, text_y))
        
        # Tính center của box để vẽ mũi tên
        x_coords = [point[0] for point in poly]
        y_coords = [point[1] for point in poly]
        center_x = (min(x_coords) + max(x_coords)) // 2
        center_y = (min(y_coords) + max(y_coords)) // 2
        
        # Hiển thị từng tọa độ trên từng dòng cho dễ đọc
        lines = [
            f"B{i+1}:",
            f"TL:({poly[0][0]},{poly[0][1]})",  # Top Left
            f"TR:({poly[1][0]},{poly[1][1]})",  # Top Right  
            f"BR:({poly[2][0]},{poly[2][1]})",  # Bottom Right
            f"BL:({poly[3][0]},{poly[3][1]})"   # Bottom Left
        ]

        # Tính kích thước background cần thiết
        max_width = 0
        line_height = 15
        for line in lines:
            text_size = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]
            max_width = max(max_width, text_size[0])
        
        total_height = len(lines) * line_height
        
        # Vẽ background cho text với màu box nhạt
        bg_color = tuple(min(255, int(c * 0.3)) for c in box_color)
        cv2.rectangle(bbox_image, (text_x-2, text_y-12), 
                     (text_x+max_width+4, text_y+total_height-5), bg_color, -1)
        cv2.rectangle(bbox_image, (text_x-2, text_y-12), 
                     (text_x+max_width+4, text_y+total_height-5), box_color, 2)
        
        # Vẽ mũi tên từ góc text box đến center của polygon
        arrow_start_x = text_x + max_width + 4
        arrow_start_y = text_y + total_height // 2
        arrow_color = tuple(max(0, int(c * 0.9)) for c in box_color)
        draw_arrow(bbox_image, (arrow_start_x, arrow_start_y), (center_x, center_y), arrow_color, 2)
        
        # Vẽ từng dòng text
        for j, line in enumerate(lines):
            line_y = text_y + (j * line_height)
            cv2.putText(bbox_image, line, (text_x, line_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1, cv2.LINE_AA)
    
    # Tạo ảnh ghép side-by-side
    combined_detailed = create_side_by_side_image(original_image, bbox_image)
    cv2.imwrite("output_write_box/page"+ str(page_number) +"_sidebyside_detailed.jpg", combined_detailed)

print("✅ Hoàn thành! Kiểm tra:")
print("   - *_sidebyside_clean.jpg: Ảnh ghép với số box và mũi tên")
print("   - *_sidebyside_detailed.jpg: Ảnh ghép với tọa độ chi tiết và mũi tên")
print("   - Bên trái: Bounding boxes")
print("   - Bên phải: Ảnh gốc")
print("   - Các số thứ tự không còn bị trùng lên nhau")
print("   - Mũi tên chỉ từ số thứ tự đến box tương ứng")
