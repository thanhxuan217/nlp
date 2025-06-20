import json
import csv
import os
import re
import pandas as pd
from utils.sort_poly import sort_rec_texts_polys

input_dir = "output_paddle"
output_rows = []

# Các thành phần mặc định cho mã số
DOMAIN = "L"       # Văn học
SUBDOMAIN = "O"    # Mock
GENRE = "A"        # Mock
FILE_CODE = "023"  # Mock
CHAPTER = "004"    # Tập số 04
BOOK_NAME = "VN_HanVan_TieuThuyet_TapThanh_04_ThanhXuan"


def generate_id(domain, subdomain, genre, file_code, chapter, page, box_index):
    """
    Tạo ID dạng DSG_fff.ccc.ppp.ss
    """
    return f"{domain}{subdomain}{genre}_{file_code}.{chapter}.{str(page).zfill(3)}.{str(box_index).zfill(2)}"


# Regex để lấy số trang từ tên file kiểu 'page5.json'
page_pattern = re.compile(r"page(\d+)_res\.json")

# Lọc và sắp xếp file theo số trang
json_files = sorted(
    [f for f in os.listdir(input_dir) if page_pattern.match(f)],
    key=lambda f: int(page_pattern.match(f).group(1))
)

def generate_filename(book_name, page_number):
    # Định dạng số trang về 3 chữ số, ví dụ: 1 -> 001
    page_str = f"{page_number:03d}"
    # Ghép tên file
    filename = f"{book_name}_page{page_str}.png"
    return filename

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
    rec_texts = data.get("rec_texts", [])
    rec_scores = data.get("rec_scores", [])

    sorted_texts, sorted_polys, sorted_scores = sort_rec_texts_polys(rec_texts, rec_polys, rec_scores)
    
    # Read from right to left
    for idx in range(len(rec_polys)):
    # for idx in range(len(rec_polys)):
        box = sorted_polys[idx]
        text = sorted_texts[idx]
        score = sorted_scores[idx]

        id_code = generate_id(DOMAIN, SUBDOMAIN, GENRE, FILE_CODE, CHAPTER, page_number, idx + 1)


        row = {
            "ID": id_code,
            "Image box": str(box),
            "Hán char": text,
            "Score": score,
            "Âm Hán Việt": "",
            "Nghĩa thuần Việt": "",
            "Image Name": generate_filename(BOOK_NAME, page_number)
        }
        output_rows.append(row)


# Xuất CSV
df = pd.DataFrame(output_rows)
df.to_excel("output_ocr/output_ocr_raw_2.xlsx", index=False)
print(f"✅ Xuất {len(output_rows)} dòng vào file: output_ocr_raw_2.xlsx")


