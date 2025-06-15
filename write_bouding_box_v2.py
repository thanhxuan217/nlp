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

def expand_image_if_needed(image, text_positions, margin=80):
    """Mở rộng ảnh nếu text nằm ngoài biên"""
    h, w = image.shape[:2]
    
    # Tìm vị trí text xa nhất
    min_x = min([pos[0] for pos in text_positions] + [0])
    max_x = max([pos[0] for pos in text_positions] + [w])
    min_y = min([pos[1] for pos in text_positions] + [0])
    max_y = max([pos[1] for pos in text_positions] + [h])
    
    # Tính toán padding cần thiết
    left_pad = max(0, margin - min_x)
    right_pad = max(0, max_x + margin - w)
    top_pad = max(0, margin - min_y)
    bottom_pad = max(0, max_y + margin - h)
    
    if left_pad > 0 or right_pad > 0 or top_pad > 0 or bottom_pad > 0:
        # Mở rộng ảnh
        expanded_image = cv2.copyMakeBorder(
            image, top_pad, bottom_pad, left_pad, right_pad,
            cv2.BORDER_CONSTANT, value=(255, 255, 255)
        )
        # Cập nhật lại tọa độ text
        updated_positions = [(x + left_pad, y + top_pad) for x, y in text_positions]
        return expanded_image, updated_positions, (left_pad, top_pad)
    
    return image, text_positions, (0, 0)

def point_in_polygon(point, polygon):
    """Kiểm tra xem điểm có nằm trong polygon không"""
    x, y = point
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside

def check_text_overlap(text_pos, existing_positions, min_distance=60):
    """Kiểm tra xem vị trí text có bị trùng với các vị trí đã có không"""
    text_x, text_y = text_pos
    for existing_x, existing_y in existing_positions:
        distance = np.sqrt((text_x - existing_x)**2 + (text_y - existing_y)**2)
        if distance < min_distance:
            return True
    return False

def is_position_inside_any_box(position, all_polygons):
    """Kiểm tra xem vị trí có nằm trong bất kỳ bounding box nào không"""
    for poly in all_polygons:
        if point_in_polygon(position, poly):
            return True
    return False

def find_non_overlapping_position(poly, box_index, existing_positions, all_polygons, image_shape):
    """Tìm vị trí không bị trùng và không nằm trong box cho text"""
    # Lấy bounding box của polygon
    x_coords = [point[0] for point in poly]
    y_coords = [point[1] for point in poly]
    
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)
    center_x, center_y = (min_x + max_x) // 2, (min_y + max_y) // 2
    
    # Danh sách các vị trí ưu tiên để thử (xa hơn khỏi box)
    distances = [40, 60, 80, 100, 120]  # Các khoảng cách khác nhau
    
    for distance in distances:
        positions_to_try = [
            (center_x, min_y - distance),           # Trên giữa
            (center_x, max_y + distance),           # Dưới giữa
            (min_x - distance, center_y),           # Trái giữa
            (max_x + distance, center_y),           # Phải giữa
            (min_x - distance, min_y - distance),   # Trên trái
            (max_x + distance, min_y - distance),   # Trên phải
            (min_x - distance, max_y + distance),   # Dưới trái
            (max_x + distance, max_y + distance),   # Dưới phải
            # Thêm các vị trí diagonal
            (center_x - distance//2, min_y - distance),
            (center_x + distance//2, min_y - distance),
            (center_x - distance//2, max_y + distance),
            (center_x + distance//2, max_y + distance),
        ]
        
        for pos in positions_to_try:
            text_x, text_y = pos
            
            # Kiểm tra các điều kiện:
            # 1. Không trùng lặp với text khác
            # 2. Không nằm trong bất kỳ bounding box nào
            if (not check_text_overlap((text_x, text_y), existing_positions) and
                not is_position_inside_any_box((text_x, text_y), all_polygons)):
                return text_x, text_y
    
    # Nếu không tìm được vị trí tốt, dùng phương pháp spiral search
    for radius in range(50, 200, 20):
        for angle in range(0, 360, 30):
            angle_rad = np.radians(angle)
            text_x = center_x + radius * np.cos(angle_rad)
            text_y = center_y + radius * np.sin(angle_rad)
            
            if (not check_text_overlap((text_x, text_y), existing_positions) and
                not is_position_inside_any_box((text_x, text_y), all_polygons)):
                return int(text_x), int(text_y)
    
    # Cuối cùng, dùng vị trí mặc định với offset lớn
    return center_x, min_y - 100 - (box_index * 30)

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
    padding = 6
    cv2.rectangle(image, 
                 (text_x - padding, text_y - text_size[1] - padding),
                 (text_x + text_size[0] + padding, text_y + padding),
                 bg_color, -1)
    
    # Vẽ viền background
    cv2.rectangle(image, 
                 (text_x - padding, text_y - text_size[1] - padding),
                 (text_x + text_size[0] + padding, text_y + padding),
                 color, 2)
    
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

# Lặp qua các file
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
    
    print(f"📄 Xử lý trang {page_number} với {len(rec_polys)} bounding boxes")
    
    # VERSION 1: CLEAN - Chỉ hiển thị số box với mũi tên
    bbox_image = original_image.copy()
    existing_text_positions = []
    text_positions_for_expansion = []
    
    # Tìm tất cả vị trí text trước
    for i, poly in enumerate(rec_polys):
        text_x, text_y = find_non_overlapping_position(poly, i, existing_text_positions, rec_polys, bbox_image.shape)
        existing_text_positions.append((text_x, text_y))
        text_positions_for_expansion.append((text_x, text_y))
    
    # Mở rộng ảnh nếu cần và cập nhật tọa độ
    bbox_image, updated_text_positions, offset = expand_image_if_needed(bbox_image, text_positions_for_expansion)
    offset_x, offset_y = offset
    
    # Cập nhật tọa độ polygons nếu ảnh được mở rộng
    if offset_x > 0 or offset_y > 0:
        updated_polys = []
        for poly in rec_polys:
            updated_poly = [(x + offset_x, y + offset_y) for x, y in poly]
            updated_polys.append(updated_poly)
        rec_polys = updated_polys
    
    # Vẽ bounding boxes và text
    for i, poly in enumerate(rec_polys):
        # Lấy màu riêng cho mỗi box
        box_color = get_box_color(i)
        
        # Vẽ bounding box với màu riêng
        pts = np.array(poly, np.int32).reshape((-1,1,2))
        cv2.polylines(bbox_image, [pts], isClosed=True, color=box_color, thickness=2)
        
        # Lấy vị trí text đã cập nhật
        text_x, text_y = updated_text_positions[i]
        
        # Tìm góc gần nhất với text để vẽ mũi tên
        text_center_x, text_center_y = text_x + 15, text_y - 10
        
        # Tính khoảng cách từ text đến mỗi góc của box
        min_distance = float('inf')
        closest_corner = None
        
        for corner in poly:
            corner_x, corner_y = corner[0], corner[1]
            distance = np.sqrt((text_center_x - corner_x)**2 + (text_center_y - corner_y)**2)
            if distance < min_distance:
                min_distance = distance
                closest_corner = (corner_x, corner_y)
        
        # Vẽ mũi tên từ text đến góc gần nhất
        arrow_color = tuple(max(0, int(c * 0.8)) for c in box_color)
        draw_arrow(bbox_image, (text_center_x, text_center_y), closest_corner, arrow_color, 2)
        
        # Vẽ text với background
        text = f"{i+1}"
        bg_color = tuple(min(255, int(c * 0.3)) for c in box_color)
        draw_text_with_background(bbox_image, text, (text_x, text_y), 0.8, box_color, bg_color, 1)
    
    # Tạo ảnh ghép side-by-side
    combined_clean = create_side_by_side_image(original_image, bbox_image)
    cv2.imwrite("output_write_box/page"+ str(page_number) +"_sidebyside_clean.jpg", combined_clean)

# VERSION 2: DETAILED - Hiển thị đầy đủ tọa độ với mũi tên
print("\n🔄 Tạo version chi tiết...")

for idx, row in df_grouped.iterrows():
    filename = row['Uploaded Filename']
    match = re.match(r'page(\d+)_res\.png', filename)
    if not match:
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
    text_positions_for_expansion = []
    
    # Tìm tất cả vị trí text trước
    for i, poly in enumerate(rec_polys):
        text_x, text_y = find_non_overlapping_position(poly, i, existing_text_positions, rec_polys, bbox_image.shape)
        existing_text_positions.append((text_x, text_y))
        text_positions_for_expansion.append((text_x, text_y))
    
    # Mở rộng ảnh nếu cần
    bbox_image, updated_text_positions, offset = expand_image_if_needed(bbox_image, text_positions_for_expansion, margin=120)
    offset_x, offset_y = offset
    
    # Cập nhật tọa độ polygons
    if offset_x > 0 or offset_y > 0:
        updated_polys = []
        for poly in rec_polys:
            updated_poly = [(x + offset_x, y + offset_y) for x, y in poly]
            updated_polys.append(updated_poly)
        rec_polys = updated_polys
    
    for i, poly in enumerate(rec_polys):
        # Lấy màu riêng cho mỗi box
        box_color = get_box_color(i)
        
        # Vẽ bounding box với màu nổi bật hơn
        pts = np.array(poly, np.int32).reshape((-1,1,2))
        cv2.polylines(bbox_image, [pts], isClosed=True, color=box_color, thickness=3)
        
        # Lấy vị trí text đã cập nhật
        text_x, text_y = updated_text_positions[i]
        
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
        line_height = 16
        for line in lines:
            text_size = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]
            max_width = max(max_width, text_size[0])
        
        total_height = len(lines) * line_height
        
        # Vẽ background cho text với màu box nhạt
        bg_color = tuple(min(255, int(c * 0.3)) for c in box_color)
        cv2.rectangle(bbox_image, (text_x-4, text_y-12), 
                     (text_x+max_width+8, text_y+total_height-5), bg_color, -1)
        cv2.rectangle(bbox_image, (text_x-4, text_y-12), 
                     (text_x+max_width+8, text_y+total_height-5), box_color, 2)
        
        # Vẽ mũi tên từ góc text box đến center của polygon
        arrow_start_x = text_x + max_width + 8
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

print("✅ Hoàn thành! Các cải tiến:")
print("   - ✓ Số thứ tự không nằm trong bounding box")
print("   - ✓ Số thứ tự không đè lên nhau") 
print("   - ✓ Tự động mở rộng ảnh nếu số thứ tự nằm ngoài biên")
print("   - ✓ Sử dụng thuật toán spiral search để tìm vị trí tối ưu")
print("   - ✓ Kiểm tra collision với tất cả bounding boxes")
print("\nKiểm tra file:")
print("   - *_sidebyside_clean.jpg: Ảnh ghép với số box sạch sẽ")
print("   - *_sidebyside_detailed.jpg: Ảnh ghép với tọa độ chi tiết")
