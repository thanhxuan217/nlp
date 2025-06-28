import os
from paddleocr import PaddleOCR

# Khởi tạo PaddleOCR
ocr = PaddleOCR(
    lang="ch",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    device="gpu"
)

# Thư mục chứa ảnh đầu vào và thư mục lưu đầu ra
input_folder = "./output_tap_18/resized_imgs"  # Đúng theo ảnh bạn cung cấp
output_dir = "./output_tap_18/output_paddle"
os.makedirs(output_dir, exist_ok=True)

# Duyệt qua các ảnh trong thư mục
for filename in sorted(os.listdir(input_folder)):
    if filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
        input_path = os.path.join(input_folder, filename)
        print(f"🔍 Processing: {input_path}")

        # Dự đoán OCR
        result = ocr.predict(input=input_path)

        for res in result:
            res.print()
            # res.save_to_img("./output_tap_18/output_paddle")
            res.save_to_json("./output_tap_18/output_paddle")

print("✅ Hoàn tất xử lý toàn bộ ảnh!")
