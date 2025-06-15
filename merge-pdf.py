from PIL import Image
import os

def images_to_pdf(image_folder, output_pdf_path="output.pdf"):
    # Lấy danh sách ảnh và sắp xếp theo số thứ tự trong tên (page_1.jpg, page_2.jpg, ...)
    image_files = sorted(
        [f for f in os.listdir(image_folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))],
        key=lambda f: int(f.split("_")[1].split(".")[0])
    )

    if not image_files:
        print("❌ Không tìm thấy ảnh hợp lệ.")
        return

    # Chuyển tất cả ảnh sang RGB
    image_paths = [os.path.join(image_folder, f) for f in image_files]
    images = [Image.open(p).convert("RGB") for p in image_paths]

    # Trang đầu tiên + phần còn lại
    first_image = images[0]
    remaining_images = images[1:]

    # Tạo PDF: mỗi hình 1 trang
    first_image.save(output_pdf_path, save_all=True, append_images=remaining_images)
    print(f"✅ Đã tạo PDF với {len(images)} trang: {output_pdf_path}")

# Thực thi
images_to_pdf("downloaded_images", "sachbaovn_pages.pdf")
