import json
import csv
import os
import re
import pandas as pd

input_dir = "./output_paddle"
output_rows = []

# Các thành phần mặc định cho mã số
DOMAIN = "L"       # Văn học
SUBDOMAIN = "O"    # Mock
GENRE = "A"        # Mock
FILE_CODE = "023"  # Mock
CHAPTER = "004"    # Tập số 04


def generate_id(domain, subdomain, genre, file_code, chapter, page, box_index):
    """
    Tạo ID dạng DSG_fff.ccc.ppp.ss
    """
    return f"{domain}{subdomain}{genre}_{file_code}.{chapter}.{str(page).zfill(3)}.{str(box_index).zfill(2)}"


# Regex để lấy số trang từ tên file kiểu 'page5.json'
page_pattern = re.compile(r"page(\d+)_res\.json")

input_dir = "./output_paddle"

# Lọc và sắp xếp file theo số trang
json_files = sorted(
    [f for f in os.listdir(input_dir) if page_pattern.match(f)],
    key=lambda f: int(page_pattern.match(f).group(1))
)

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

    combined = list(zip(rec_polys, rec_texts))
    combined.sort(key=lambda item: (-item[0][0][0], -item[0][0][1]))  # x1 giảm dần, y1 giảm dần
    rec_polys, rec_texts = zip(*combined) if combined else ([], [])
    
    # Read from right to left
    for idx in range(len(rec_polys)):
    # for idx in range(len(rec_polys)):
        box = rec_polys[idx]
        text = rec_texts[idx]
        id_code = generate_id(DOMAIN, SUBDOMAIN, GENRE, FILE_CODE, CHAPTER, page_number, idx + 1)

        row = {
            "ID": id_code,
            "Image box": str(box),
            "Hán char": text,
            "Âm Hán Việt": "",
            "Nghĩa thuần Việt": "",
            "Uploaded Filename": filename.replace(".json", ".png")
        }
        output_rows.append(row)


# Xuất CSV
df = pd.DataFrame(output_rows)
df.to_excel("./output_ocr/output_ocr_raw.xlsx", index=False)
print(f"✅ Xuất {len(output_rows)} dòng vào file: output_ocr_raw.xlsx")


