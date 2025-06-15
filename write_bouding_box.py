import json
import os
import re
import cv2
import numpy as np

input_dir = "./output_paddle"

# Regex để lấy số trang từ tên file kiểu 'page5.json'
page_pattern = re.compile(r"page(\d+)_res\.json")

# Lọc và sắp xếp file theo số trang
json_files = sorted(
    [f for f in os.listdir(input_dir) if page_pattern.match(f)],
    key=lambda f: int(page_pattern.match(f).group(1))
)

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

def find_best_text_position(poly, box_index, all_polys, image_shape):
    """Tìm vị trí tốt nhất để đặt text - ưu tiên trên/dưới cho các box gần nhau"""
    # Lấy bounding box của polygon hiện tại
    x_coords = [point[0] for point in poly]
    y_coords = [point[1] for point in poly]
    
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)
    center_x, center_y = (min_x + max_x) // 2, (min_y + max_y) // 2
    
    # Tìm các box gần nhau (trong bán kính 100 pixel)
    nearby_boxes = []
    for i, other_poly in enumerate(all_polys):
        if i != box_index:
            other_x_coords = [point[0] for point in other_poly]
            other_y_coords = [point[1] for point in other_poly]
            other_center_x = (min(other_x_coords) + max(other_x_coords)) // 2
            other_center_y = (min(other_y_coords) + max(other_y_coords)) // 2
            
            distance = np.sqrt((center_x - other_center_x)**2 + (center_y - other_center_y)**2)
            if distance < 100:  # Khoảng cách ngưỡng để coi là "gần nhau"
                nearby_boxes.append((i, other_center_y))
    
    # Xác định vị trí text dựa trên các box gần nhau
    if nearby_boxes:
        # Sắp xếp các box gần theo tọa độ Y
        nearby_boxes.sort(key=lambda x: x[1])
        
        # Tìm vị trí của box hiện tại trong danh sách
        current_rank = 0
        for idx, (other_box_idx, other_y) in enumerate(nearby_boxes):
            if other_y < center_y:
                current_rank += 1
        
        # Quyết định vị trí text dựa trên thứ hạng
        if current_rank % 2 == 0:  # Box chẵn -> text ở trên
            text_x, text_y = center_x, min_y - 15
        else:  # Box lẻ -> text ở dưới
            text_x, text_y = center_x, max_y + 25
    else:
        # Nếu không có box nào gần, dùng vị trí mặc định (trên)
        text_x, text_y = center_x, min_y - 15
    
    # Đảm bảo không vượt ra ngoài ảnh
    text_x = max(10, min(text_x, image_shape[1] - 150))
    text_y = max(20, min(text_y, image_shape[0] - 20))
    
    return text_x, text_y

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
for filename in json_files:
    page_number = int(page_pattern.match(filename).group(1))

    with open(input_dir + "/" + filename, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print(f"❌ Lỗi khi đọc file JSON: {filename}")
            continue
        
    rec_polys = data.get("rec_polys", [])

    # Đọc ảnh gốc
    original_image = cv2.imread("./resized_img/page"+ str(page_number) +".png")
    if original_image is None:
        print(f"❌ Không thể đọc ảnh: page{page_number}.png")
        continue
    
    # Tạo ảnh với bounding boxes
    bbox_image = original_image.copy()
    
    print(f"📄 Xử lý trang {page_number} với {len(rec_polys)} bounding boxes")
    
    # VERSION 1: CLEAN - Chỉ hiển thị số box
    for i, poly in enumerate(rec_polys):
        # Lấy màu riêng cho mỗi box
        box_color = get_box_color(i)
        
        # Vẽ bounding box với màu riêng
        pts = np.array(poly, np.int32).reshape((-1,1,2))
        cv2.polylines(bbox_image, [pts], isClosed=True, color=box_color, thickness=2)
        
        # Vẽ các góc với màu tương ứng nhưng đậm hơn
        # for j, (x, y) in enumerate(poly):
        #     # Làm đậm màu cho các góc
        #     corner_color = tuple(max(0, int(c * 0.7)) for c in box_color)
        #     cv2.circle(bbox_image, (x, y), 4, corner_color, -1)
        #     cv2.circle(bbox_image, (x, y), 4, (255,255,255), 1)  # Viền trắng
        
        # Sử dụng thuật toán mới để xác định vị trí text
        text_x, text_y = find_best_text_position(poly, i, rec_polys, bbox_image.shape)
        
        # Text với màu tương ứng
        cv2.putText(bbox_image, f"{i+1}", (text_x, text_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2, cv2.LINE_AA)
        cv2.putText(bbox_image, f"{i+1}", (text_x, text_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 1, cv2.LINE_AA)
    
    # Tạo ảnh ghép side-by-side
    combined_clean = create_side_by_side_image(original_image, bbox_image)
    cv2.imwrite("output_write_box/page"+ str(page_number) +"_sidebyside_clean.jpg", combined_clean)

# VERSION 2: DETAILED - Hiển thị đầy đủ tọa độ
print("\n🔄 Tạo version chi tiết...")

for filename in json_files:
    page_number = int(page_pattern.match(filename).group(1))

    with open(input_dir + "/" + filename, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            continue
        
    rec_polys = data.get("rec_polys", [])
    original_image = cv2.imread("./resized_img/page"+ str(page_number) +".png")
    if original_image is None:
        continue
    
    # Tạo ảnh với bounding boxes (có overlay mờ)
    bbox_image = original_image.copy()
    overlay = bbox_image.copy()
    cv2.rectangle(overlay, (0, 0), (bbox_image.shape[1], bbox_image.shape[0]), (0, 0, 0), -1)
    bbox_image = cv2.addWeighted(bbox_image, 0.7, overlay, 0.3, 0)
    
    box_num = len(rec_polys)

    for i, poly in enumerate(rec_polys):
        # Lấy màu riêng cho mỗi box
        box_color = get_box_color(i)
        
        # Vẽ bounding box với màu nổi bật hơn
        pts = np.array(poly, np.int32).reshape((-1,1,2))
        cv2.polylines(bbox_image, [pts], isClosed=True, color=box_color, thickness=3)
        
        # Vẽ các góc với màu tương ứng
        # for j, (x, y) in enumerate(poly):
        #     # Làm đậm màu cho các góc
        #     corner_color = tuple(max(0, int(c * 0.7)) for c in box_color)
        #     cv2.circle(bbox_image, (x, y), 6, corner_color, -1)
        #     cv2.circle(bbox_image, (x, y), 6, (255,255,255), 2)  # Viền trắng
        
        # Sử dụng thuật toán mới để xác định vị trí text
        text_x, text_y = find_best_text_position(poly, i, rec_polys, bbox_image.shape)
        
        # Hiển thị từng tọa độ trên từng dòng cho dễ đọc
        lines = [
            f"B{box_num}:",
            f"TL:({poly[0][0]},{poly[0][1]})",  # Top Left
            f"TR:({poly[1][0]},{poly[1][1]})",  # Top Right  
            f"BR:({poly[2][0]},{poly[2][1]})",  # Bottom Right
            f"BL:({poly[3][0]},{poly[3][1]})"   # Bottom Left
        ]

        box_num = box_num - 1
        
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
        
        # Vẽ từng dòng text
        for j, line in enumerate(lines):
            line_y = text_y + (j * line_height)
            cv2.putText(bbox_image, line, (text_x, line_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1, cv2.LINE_AA)
    
    # Tạo ảnh ghép side-by-side
    combined_detailed = create_side_by_side_image(original_image, bbox_image)
    cv2.imwrite("output_write_box/page"+ str(page_number) +"_sidebyside_detailed.jpg", combined_detailed)

print("✅ Hoàn thành! Kiểm tra:")
print("   - *_sidebyside_clean.jpg: Ảnh ghép với số box")
print("   - *_sidebyside_detailed.jpg: Ảnh ghép với tọa độ chi tiết")
print("   - Bên trái: Bounding boxes")
print("   - Bên phải: Ảnh gốc")
