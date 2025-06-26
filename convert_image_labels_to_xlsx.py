import json
import pandas as pd
import os

from utils.sort_poly import sort_rec_texts_polys

# --- Thông tin mặc định ---
# Các thành phần mặc định cho mã số
# ID = LSE_001
DOMAIN = "L"       # Văn học
SUBDOMAIN = "S"    
GENRE = "E"        
FILE_CODE = "001"  
CHAPTER = "004"    # Tập số 04
BOOK_NAME = "VN_HanVan_TieuThuyet_TapThanh_04_ThanhXuan"

def generate_id(domain, subdomain, genre, file_code, chapter, page, box_index):
    return f"{domain}{subdomain}{genre}_{file_code}.{chapter}.{str(page).zfill(3)}.{str(box_index).zfill(2)}"

def extract_page_number(image_path):
    # Lấy số trang từ tên file, ví dụ: ..._page004.png
    basename = os.path.basename(image_path)
    parts = basename.split('_page')
    if len(parts) > 1:
        page_str = parts[1].split('.')[0]
        return int(page_str)
    return 0

def generate_filename(book_name, page_number):
    page_str = f"{page_number:03d}"
    return f"{book_name}_page{page_str}.png"

# Đọc dữ liệu từ file /images_label/Label.txt
with open('./images_label/Label.txt', 'r', encoding='utf-8') as f:
    data = f.readlines()

rows = []
seen = set()
for line in data:
    line = line.strip()
    if not line:
        continue
    image_path, json_str = line.split('\t', 1)
    page_number = extract_page_number(image_path)
    image_name = generate_filename(BOOK_NAME, page_number)
    try:
        label_list = json.loads(json_str) # label for each page

    except Exception as e:
        print(f"Lỗi parse JSON dòng: {line[:50]}...: {e}")
        continue

    rec_texts = [item["transcription"] for item in label_list]
    rec_polys = [item["points"] for item in label_list]
    rec_scores = [0 for item in label_list]

    sorted_texts, sorted_polys, sorted_scores = sort_rec_texts_polys(rec_texts, rec_polys, rec_scores)
    
    box_count = 1  # Đếm số box hợp lệ trên trang

    # Read from right to left
    for idx in range(len(rec_texts)):
        box = sorted_polys[idx]
        text = sorted_texts[idx]
        key = (str(box), text)
        if key in seen:
            continue
        seen.add(key)

        id_code = generate_id(DOMAIN, SUBDOMAIN, GENRE, FILE_CODE, CHAPTER, page_number, box_count)

        row = {
            "ID": id_code,
            "Image box": str(box),
            "Hán char": text,
            "Image Name": generate_filename(BOOK_NAME, page_number)
        }
        rows.append(row)
        box_count += 1


df = pd.DataFrame(rows)
os.makedirs("./output_paddle_ocr_label", exist_ok=True)
df.to_excel("./output_paddle_ocr_label/output.xlsx", index=False)
print("✅ Đã xuất file ./output_paddle_ocr_label/output.xlsx")
