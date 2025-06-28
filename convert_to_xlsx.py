import json
import csv
import os
import re
import pandas as pd
from utils.clean import clean_ocr_data
from utils.merge import group_boxes_by_vertical_column, merge_boxes
from utils.sort_poly import sort_rec_texts_polys

input_dir = "./output_tap_18/output_paddle"
output_dir = "./output_tap_18/xlsx"
output_rows = []

# Các thành phần mặc định cho mã số
DOMAIN = "L"       # Văn học
SUBDOMAIN = "S"    
GENRE = "E"        
FILE_CODE = "001"  
CHAPTER = "018"    # Tập số 18
#CHAPTER = "001"
BOOK_NAME = "VN_HanVan_TieuThuyet_TapThanh_18_ThanhXuan"
#BOOK_NAME = "VN_HánVăn_TiểuThuyết_TậpThành - 01"

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
    rec_scores = data.get("rec_scores", []) # Should be improve later

    # Clean data
    filtered_polys, filtered_texts, filtered_scores = clean_ocr_data(rec_polys, rec_texts, rec_scores)
    if not filtered_polys or not filtered_texts or not filtered_scores:
        continue
    
    groups = group_boxes_by_vertical_column(filtered_polys)
    boxes_merged = []
    for i, group in enumerate(groups):
        boxes_merged.append(merge_boxes(group))

    texts_merged = []
    score_merged = []

    for i, box in enumerate(boxes_merged):
        # for each box_merged, get all groups[i].
        # Init groupInx = i, rec_texts_group
        # Then loop the groups[i] and find group in rec_polys -> index -> rec_texts[index], rec_texts_group += rec_texts[index] + " "
        rec_texts_group = ""
        score_group = []
        for poly in groups[i]:
            if poly in filtered_polys:
                idx = filtered_polys.index(poly)
                rec_texts_group += filtered_texts[idx] + " "
                score_group.append(filtered_scores[idx])

        texts_merged.append(rec_texts_group.strip())
        average = sum(score_group) / len(score_group)
        score_merged.append(average)

    sorted_texts, sorted_polys, sorted_scores = sort_rec_texts_polys(texts_merged, boxes_merged, score_merged)
    
    # Read from right to left
    for idx in range(len(sorted_texts)):
        box = sorted_polys[idx]
        text = sorted_texts[idx]
        score = sorted_scores[idx]

        id_code = generate_id(DOMAIN, SUBDOMAIN, GENRE, FILE_CODE, CHAPTER, page_number, idx + 1)

        row = {
            "ID": id_code,
            "Image box": str(box),
            "Hán char": text,
            "Score": score,
            "Image Name": generate_filename(BOOK_NAME, page_number)
        }
        output_rows.append(row)


# Xuất CSV
df = pd.DataFrame(output_rows)
df.to_excel(output_dir + "/output_ocr_raw.xlsx", index=False)
print(f"✅ Xuất {len(output_rows)} dòng vào file: output_ocr_raw.xlsx")


