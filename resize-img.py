from PIL import Image
import os

# Danh sách đường dẫn ảnh
image_paths = [f"./output_tap_18/images/page{i}.png" for i in range(1, 365)]

# Kích thước mới
new_size = (800, 1000)  # width, height (bạn có thể chỉnh lại)

# Thư mục lưu ảnh đã resize (có thể là "./resized" hoặc ghi đè gốc)
output_dir = "./output_tap_18/resized_imgs"
os.makedirs(output_dir, exist_ok=True)

# Resize và lưu lại
for path in image_paths:
    with Image.open(path) as img:
        resized = img.resize(new_size, Image.Resampling.LANCZOS)
        filename = os.path.basename(path)
        output_path = os.path.join(output_dir, filename)
        resized.save(output_path)

print("Hoàn tất resize ảnh.")
