from pdf2image import convert_from_path
import os

# Đường dẫn tới file PDF đầu vào
pdf_path = "VN_HánVăn_TiểuThuyết_TậpThành - 18.pdf"

# Thư mục lưu ảnh đầu ra
output_folder = "./output_tap_18/images"
os.makedirs(output_folder, exist_ok=True)

# Chuyển đổi PDF thành list các ảnh (mỗi trang là một ảnh)
images = convert_from_path(pdf_path, dpi=150)  # Có thể đổi dpi = 200 để nhẹ hơn

# Lưu từng trang thành file ảnh PNG
for i, image in enumerate(images):
    output_path = os.path.join(output_folder, f"page{i + 1}.png")
    image.save(output_path, "PNG")

print("Chuyển đổi hoàn tất!")
