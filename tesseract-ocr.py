import cv2
import pytesseract
from pytesseract import Output
import os

# Nếu bạn dùng Windows và Tesseract không có trong PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Đường dẫn ảnh đầu vào
image_path = "./resized_img/page4.png"

# Đọc ảnh bằng OpenCV
image = cv2.imread(image_path)

# OCR và lấy thông tin các bounding box
d = pytesseract.image_to_data(image, output_type=Output.DICT)

# Vẽ bounding box cho mỗi từ
n_boxes = len(d['text'])
for i in range(n_boxes):
    if int(d['conf'][i]) > 60:  # độ tin cậy > 60%
        (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(image, d['text'][i], (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

# Tạo thư mục lưu ảnh nếu chưa có
output_dir = "./output_tesseract"
os.makedirs(output_dir, exist_ok=True)

# Tên file lưu
output_path = os.path.join(output_dir, "page4_ocr.png")

# Lưu ảnh đã vẽ bounding box
cv2.imwrite(output_path, image)

print(f"Ảnh đã được lưu tại: {output_path}")
