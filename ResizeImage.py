import os
from PIL import Image

def resize_image(image_path, max_size=1200, output_file=None):
    with Image.open(image_path) as img:
        width, height = img.size
        total_size = width + height

        if total_size > max_size:
            scale_factor = max_size / total_size
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            img = img.resize((new_width, new_height), Image.LANCZOS)
            img.save(image_path)
            print(f"Resized image '{image_path}' to {new_width}x{new_height}")

            if output_file:
                output_file.write(f"{os.path.basename(image_path)}\n")
        else:
            print(f"Image '{image_path}' does not need resizing.")

def process_images_in_directory(directory_path, output_txt_path):
    with open(output_txt_path, 'w') as output_file:
        for filename in os.listdir(directory_path):
            if filename.lower().endswith(('png', 'jpg', 'jpeg', 'bmp', 'gif')):
                image_path = os.path.join(directory_path, filename)
                resize_image(image_path, output_file=output_file)

# Thay đường dẫn bằng thư mục chứa hình ảnh và file txt của bạn
directory_path = './output_tap_18/images'
output_txt_path = './resized_output.txt'

process_images_in_directory(directory_path, output_txt_path)
